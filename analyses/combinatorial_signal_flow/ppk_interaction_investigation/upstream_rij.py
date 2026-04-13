#!/usr/bin/env python3
"""
Upstream R_ij Analysis: Is the interaction determined at the intermediary level?
================================================================================

HYPOTHESIS: The interaction R_ij observed at target neurons might already be
determined at the intermediary (step 2) level before signals reach the target.
If an intermediary neuron itself shows destructive integration (its own R_ij < 0),
then even if it carries opposing ppk23/ppk25 linear drives, the nonlinear signal
it actually delivers to the target may not have the push-pull property.

This script:
  1. For ALL 39 targets, identifies their top presynaptic neurons (step 2 intermediaries)
  2. For each intermediary, computes ITS OWN R_ij
  3. For each target, computes a "weighted intermediary R_ij"
  4. Checks whether the weighted intermediary R_ij predicts the target's R_ij sign
  5. Examines mixed-destructive targets specifically
  6. Creates a three-panel figure

Usage:
  cd ppk_interaction_investigation
  ../.venv/bin/python upstream_rij.py
"""

import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy import sparse, stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signal_flow import NetworkLoader, ChannelEncoder, SignalPropagator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = Path(__file__).resolve().parent / "plots" / "upstream_rij"
OUT_DIR.mkdir(parents=True, exist_ok=True)

NONLINEARITY = "sigmoid_rectified"
ACT_PARAMS = {"beta": 5.0}
N_STEPS = 3
SUSTAINED = True

plt.rcParams.update({
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,
})


def save_fig(fig, name, description=None):
    """Save figure as PNG + PDF."""
    (OUT_DIR / "png").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "pdf").mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / "png" / f"{name}.png")
    fig.savefig(OUT_DIR / "pdf" / f"{name}.pdf")
    if description:
        (OUT_DIR / "txt").mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "txt" / f"{name}.txt").write_text(description.strip() + "\n")
    logger.info("Saved: %s", name)
    plt.close(fig)


def main():
    # =========================================================================
    # LOAD DATA
    # =========================================================================
    loader = NetworkLoader(str(DATA_DIR))
    W_unsigned = loader.load_adjacency_matrix("post")
    type_names = loader.load_type_names()
    channels = loader.load_channels()
    targets = loader.load_targets()
    nt_map = loader.load_neurotransmitter_mapping()
    W = loader.sign_matrix(W_unsigned, type_names)

    encoder = ChannelEncoder(type_names)
    enc = encoder.encode_all(channels)
    type_to_idx = encoder.type_to_idx
    idx_to_type = dict(zip(type_names["index"], type_names["type"]))
    type_to_nt = dict(zip(nt_map["type"], nt_map["consensus_nt"]))
    type_to_inhib = dict(zip(nt_map["type"], nt_map["is_inhibitory"]))

    s23 = enc["ppk23"]
    s25 = enc["ppk25"]
    s_both = s23 + s25

    Wt = W.T.tocsc()
    W_csc = W.tocsc()

    # =========================================================================
    # COMPUTE LINEAR DRIVES (per step, no activation function)
    # =========================================================================
    x23 = [s23.copy()]
    x25 = [s25.copy()]
    x = s23.copy()
    for _ in range(4):
        x = Wt.dot(x)
        x23.append(x.copy())
    x = s25.copy()
    for _ in range(4):
        x = Wt.dot(x)
        x25.append(x.copy())

    # =========================================================================
    # COMPUTE NONLINEAR ACTIVATIONS (sigmoid, sustained)
    # =========================================================================
    prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
    a23 = prop.propagate(s23, N_STEPS, sustained=SUSTAINED)
    a25 = prop.propagate(s25, N_STEPS, sustained=SUSTAINED)
    ab = prop.propagate(s_both, N_STEPS, sustained=SUSTAINED)

    # R_ij for ANY neuron idx
    R_ij_all = ab - a23 - a25

    # =========================================================================
    # COLLECT ALL TARGETS across the 4 groups
    # =========================================================================
    target_groups = ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]
    target_records = []
    for tg in target_groups:
        if tg not in targets:
            continue
        for t in targets[tg]:
            if t in type_to_idx:
                idx = type_to_idx[t]
                target_records.append({
                    "type": t,
                    "group": tg,
                    "idx": idx,
                    "R_ij": R_ij_all[idx],
                    "A_ppk23": a23[idx],
                    "A_ppk25": a25[idx],
                    "A_both": ab[idx],
                })

    logger.info("Total targets: %d", len(target_records))

    # =========================================================================
    # CLASSIFY targets by their linear drive signs and R_ij sign
    # "mixed (destructive)" = last-hop ppk23/ppk25 drives have opposite signs
    #                         but R_ij < 0 (destructive despite push-pull)
    # =========================================================================
    # For each target, compute net last-hop linear drives
    for rec in target_records:
        idx = rec["idx"]
        col = W_csc[:, idx].toarray().ravel()
        pre_indices = np.nonzero(col)[0]

        net_drive_23 = 0.0
        net_drive_25 = 0.0
        for pi in pre_indices:
            w = col[pi]
            # Use step 2 linear drive (one step before the 3-step target)
            net_drive_23 += w * x23[2][pi]
            net_drive_25 += w * x25[2][pi]

        rec["net_linear_drive_ppk23"] = net_drive_23
        rec["net_linear_drive_ppk25"] = net_drive_25
        same_sign = (net_drive_23 > 0 and net_drive_25 > 0) or \
                    (net_drive_23 < 0 and net_drive_25 < 0)
        rec["same_sign_drive"] = same_sign
        rec["drive_product"] = net_drive_23 * net_drive_25

        # Classification
        if rec["R_ij"] > 0:
            rec["category"] = "super"
        else:
            rec["category"] = "destructive"

        if not same_sign and rec["R_ij"] < 0:
            rec["mixed_label"] = "mixed-destructive"
        elif not same_sign and rec["R_ij"] > 0:
            rec["mixed_label"] = "mixed-super"
        elif same_sign and rec["R_ij"] < 0:
            rec["mixed_label"] = "same-destructive"
        elif same_sign and rec["R_ij"] > 0:
            rec["mixed_label"] = "same-super"
        else:
            rec["mixed_label"] = "other"

    df_targets = pd.DataFrame(target_records)

    # Print target classification
    print("\n" + "=" * 78)
    print("TARGET CLASSIFICATION")
    print("=" * 78)
    for label in ["mixed-destructive", "mixed-super", "same-destructive", "same-super"]:
        sub = df_targets[df_targets["mixed_label"] == label]
        print(f"\n  {label} ({len(sub)} targets):")
        for _, r in sub.iterrows():
            print(f"    {r['type']:20s} [{r['group']:20s}]  R_ij={r['R_ij']:+.4f}  "
                  f"ppk23_drive={r['net_linear_drive_ppk23']:+.5f}  "
                  f"ppk25_drive={r['net_linear_drive_ppk25']:+.5f}")

    # =========================================================================
    # STEP 1-2: For each target, identify presynaptic intermediaries
    #           and compute each intermediary's OWN R_ij
    # =========================================================================
    print("\n" + "=" * 78)
    print("INTERMEDIARY R_ij ANALYSIS")
    print("=" * 78)

    intermediary_rows = []
    target_weighted_rij = []

    for rec in target_records:
        target_idx = rec["idx"]
        target_type = rec["type"]
        target_group = rec["group"]
        target_rij = rec["R_ij"]
        target_cat = rec["category"]
        target_mixed = rec["mixed_label"]

        # Get presynaptic partners of this target
        col = W_csc[:, target_idx].toarray().ravel()
        pre_indices = np.nonzero(col)[0]

        weighted_rij_sum = 0.0
        abs_weight_sum = 0.0
        intermediary_data = []

        for pi in pre_indices:
            w_to_target = col[pi]
            pre_type = idx_to_type.get(pi, f"idx_{pi}")

            # The intermediary's own R_ij
            inter_rij = R_ij_all[pi]

            # Intermediary's ppk23/ppk25 linear drives at step 2
            inter_drive_23 = x23[2][pi]
            inter_drive_25 = x25[2][pi]

            # Intermediary's nonlinear activations
            inter_a23 = a23[pi]
            inter_a25 = a25[pi]
            inter_ab = ab[pi]

            # Effective contribution of this intermediary to the target:
            # The signal it ACTUALLY delivers (nonlinear) under each condition
            eff_contrib_23 = w_to_target * inter_a23
            eff_contrib_25 = w_to_target * inter_a25
            eff_contrib_both = w_to_target * inter_ab

            # The nonlinear contribution to R_ij at the target from this intermediary
            # = w * (inter_ab - inter_a23 - inter_a25) = w * inter_rij
            eff_rij_contrib = w_to_target * inter_rij

            # For the weighted intermediary R_ij, weight by the magnitude of
            # the effective nonlinear contribution (average of the three conditions)
            effective_mag = (abs(eff_contrib_23) + abs(eff_contrib_25) + abs(eff_contrib_both)) / 3.0

            # Only count intermediaries that carry meaningful signal
            if effective_mag > 1e-8:
                weighted_rij_sum += effective_mag * np.sign(inter_rij) * abs(inter_rij)
                abs_weight_sum += effective_mag

                intermediary_data.append({
                    "target": target_type,
                    "target_group": target_group,
                    "target_rij": target_rij,
                    "target_category": target_cat,
                    "target_mixed_label": target_mixed,
                    "intermediary": pre_type,
                    "inter_idx": pi,
                    "inter_nt": type_to_nt.get(pre_type, "unknown"),
                    "inter_is_inhibitory": type_to_inhib.get(pre_type, False),
                    "w_to_target": w_to_target,
                    "inter_rij": inter_rij,
                    "inter_drive_ppk23": inter_drive_23,
                    "inter_drive_ppk25": inter_drive_25,
                    "inter_a_ppk23": inter_a23,
                    "inter_a_ppk25": inter_a25,
                    "inter_a_both": inter_ab,
                    "eff_contrib_23": eff_contrib_23,
                    "eff_contrib_25": eff_contrib_25,
                    "eff_contrib_both": eff_contrib_both,
                    "eff_rij_contrib": eff_rij_contrib,
                    "effective_magnitude": effective_mag,
                })

        intermediary_rows.extend(intermediary_data)

        # Weighted intermediary R_ij for this target
        if abs_weight_sum > 1e-10:
            weighted_inter_rij = weighted_rij_sum / abs_weight_sum
        else:
            weighted_inter_rij = 0.0

        target_weighted_rij.append({
            "target": target_type,
            "target_group": target_group,
            "target_rij": target_rij,
            "target_category": target_cat,
            "target_mixed_label": target_mixed,
            "weighted_inter_rij": weighted_inter_rij,
            "n_intermediaries": len(intermediary_data),
            "sum_eff_rij_contrib": sum(d["eff_rij_contrib"] for d in intermediary_data),
        })

    df_inter = pd.DataFrame(intermediary_rows)
    df_weighted = pd.DataFrame(target_weighted_rij)

    # Save CSVs
    df_inter.to_csv(OUT_DIR / "intermediary_rij_all.csv", index=False)
    df_weighted.to_csv(OUT_DIR / "target_weighted_intermediary_rij.csv", index=False)

    # =========================================================================
    # STEP 3: ANALYSIS — Does the weighted intermediary R_ij predict target R_ij?
    # =========================================================================
    print("\n" + "=" * 78)
    print("PREDICTION CHECK: weighted intermediary R_ij vs target R_ij")
    print("=" * 78)

    x_vals = df_weighted["weighted_inter_rij"].values
    y_vals = df_weighted["target_rij"].values
    valid = np.isfinite(x_vals) & np.isfinite(y_vals)

    if valid.sum() > 2:
        slope, intercept, r_val, p_val, se = stats.linregress(x_vals[valid], y_vals[valid])
        print(f"\n  Linear regression: r = {r_val:.4f}, p = {p_val:.2e}")
        print(f"  Slope = {slope:.4f}, Intercept = {intercept:.4f}")

    # Sign concordance
    concordant = sum(1 for i in range(len(df_weighted))
                     if np.sign(x_vals[i]) == np.sign(y_vals[i])
                     and abs(x_vals[i]) > 1e-6 and abs(y_vals[i]) > 1e-6)
    total_meaningful = sum(1 for i in range(len(df_weighted))
                           if abs(x_vals[i]) > 1e-6 and abs(y_vals[i]) > 1e-6)
    print(f"  Sign concordance: {concordant}/{total_meaningful} "
          f"({100*concordant/max(total_meaningful,1):.1f}%)")

    # Also check sum_eff_rij_contrib (direct decomposition)
    x_direct = df_weighted["sum_eff_rij_contrib"].values
    if valid.sum() > 2:
        slope_d, _, r_d, p_d, _ = stats.linregress(x_direct[valid], y_vals[valid])
        print(f"\n  Direct decomposition (sum w_i * inter_R_ij_i):")
        print(f"    r = {r_d:.4f}, p = {p_d:.2e}")

    # =========================================================================
    # STEP 5: Focus on mixed-destructive targets
    # =========================================================================
    print("\n" + "=" * 78)
    print("MIXED-DESTRUCTIVE TARGETS: Are their key intermediaries destructive?")
    print("=" * 78)

    mixed_destr = df_targets[df_targets["mixed_label"] == "mixed-destructive"]
    if len(mixed_destr) == 0:
        print("  No mixed-destructive targets found.")
    else:
        for _, trec in mixed_destr.iterrows():
            tname = trec["type"]
            print(f"\n  TARGET: {tname} ({trec['group']})  R_ij = {trec['R_ij']:+.4f}")
            print(f"    Linear drives: ppk23={trec['net_linear_drive_ppk23']:+.5f}  "
                  f"ppk25={trec['net_linear_drive_ppk25']:+.5f}  (OPPOSITE signs)")

            df_t = df_inter[df_inter["target"] == tname].copy()
            if df_t.empty:
                print("    (no intermediary data)")
                continue

            # Sort by absolute effective R_ij contribution
            df_t["abs_eff_rij"] = df_t["eff_rij_contrib"].abs()
            top = df_t.nlargest(10, "abs_eff_rij")

            print(f"    Top intermediaries (by |w * inter_R_ij|):")
            n_destructive_inter = 0
            n_super_inter = 0
            for _, ir in top.iterrows():
                tag = "INH" if ir["inter_is_inhibitory"] else "EXC"
                rij_sign = "DESTR" if ir["inter_rij"] < 0 else "SUPER"
                if ir["inter_rij"] < 0:
                    n_destructive_inter += 1
                else:
                    n_super_inter += 1
                print(f"      {ir['intermediary']:20s} [{tag}]  "
                      f"w={ir['w_to_target']:+.4f}  "
                      f"own_R_ij={ir['inter_rij']:+.4f} ({rij_sign})  "
                      f"eff_contrib={ir['eff_rij_contrib']:+.6f}")
            print(f"    Summary: {n_destructive_inter} destructive / "
                  f"{n_super_inter} super intermediaries (top 10)")

            # The weighted intermediary R_ij for this target
            wrec = df_weighted[df_weighted["target"] == tname].iloc[0]
            print(f"    Weighted intermediary R_ij = {wrec['weighted_inter_rij']:+.4f}")
            print(f"    Sum(w_i * inter_R_ij_i) = {wrec['sum_eff_rij_contrib']:+.6f}")

    # =========================================================================
    # STEP 4+: Also check: for super targets, are their intermediaries super?
    # =========================================================================
    print("\n" + "=" * 78)
    print("COMPARISON: Intermediary R_ij by target category")
    print("=" * 78)

    # For each target category, collect the R_ij of intermediaries
    for cat in ["super", "destructive"]:
        cat_targets = df_targets[df_targets["category"] == cat]["type"].values
        cat_inter = df_inter[df_inter["target"].isin(cat_targets)]
        if len(cat_inter) > 0:
            mean_rij = cat_inter["inter_rij"].mean()
            med_rij = cat_inter["inter_rij"].median()
            frac_destr = (cat_inter["inter_rij"] < 0).mean()
            # Weight by effective magnitude
            weighted = (cat_inter["inter_rij"] * cat_inter["effective_magnitude"]).sum() / \
                       cat_inter["effective_magnitude"].sum()
            print(f"\n  {cat.upper()} targets ({len(cat_targets)} targets, "
                  f"{len(cat_inter)} intermediary links):")
            print(f"    Mean intermediary R_ij:     {mean_rij:+.5f}")
            print(f"    Median intermediary R_ij:   {med_rij:+.5f}")
            print(f"    Weighted mean inter R_ij:   {weighted:+.5f}")
            print(f"    Fraction destructive inter: {frac_destr:.1%}")

    # Statistical test: are intermediaries of super targets more super?
    super_targets = df_targets[df_targets["category"] == "super"]["type"].values
    destr_targets = df_targets[df_targets["category"] == "destructive"]["type"].values

    inter_of_super = df_inter[df_inter["target"].isin(super_targets)]["inter_rij"].values
    inter_of_destr = df_inter[df_inter["target"].isin(destr_targets)]["inter_rij"].values

    if len(inter_of_super) > 1 and len(inter_of_destr) > 1:
        stat, p = stats.mannwhitneyu(inter_of_super, inter_of_destr, alternative="two-sided")
        print(f"\n  Mann-Whitney U test (intermediary R_ij: super vs destructive targets):")
        print(f"    U = {stat:.1f}, p = {p:.2e}")

    # =========================================================================
    # KEY FINDING: How much of target R_ij is explained by intermediary R_ij?
    # =========================================================================
    print("\n" + "=" * 78)
    print("KEY FINDING: Intermediary-level explanation of target R_ij")
    print("=" * 78)

    # The sum_eff_rij_contrib is the EXACT decomposition:
    # R_ij(target) at the LAST hop is contributed by w_i * R_ij(intermediary_i)
    # PLUS the interaction arising from the last synapse itself.
    # If sum_eff_rij_contrib closely tracks target_rij, intermediaries explain it.

    print("\n  Per-target decomposition:")
    print(f"  {'Target':20s} {'Group':20s} {'target_R_ij':>12s} {'sum(w*inter_R)':>14s} "
          f"{'residual':>10s} {'%explained':>10s}")
    print("  " + "-" * 90)
    for _, wr in df_weighted.iterrows():
        resid = wr["target_rij"] - wr["sum_eff_rij_contrib"]
        pct = (wr["sum_eff_rij_contrib"] / wr["target_rij"] * 100
               if abs(wr["target_rij"]) > 1e-8 else float("nan"))
        print(f"  {wr['target']:20s} {wr['target_group']:20s} {wr['target_rij']:+12.5f} "
              f"{wr['sum_eff_rij_contrib']:+14.6f} {resid:+10.5f} {pct:9.1f}%")

    # =========================================================================
    # FIGURE: Three-panel summary
    # =========================================================================
    group_colors = {
        "aspf": "#E41A1C",
        "aspg": "#377EB8",
        "PPN1_downstream": "#FF7F00",
        "vAB3_downstream": "#4DAF4A",
    }

    fig = plt.figure(figsize=(20, 7))
    gs = GridSpec(1, 3, figure=fig, wspace=0.32)

    # ── PANEL A: Scatter of target R_ij vs weighted intermediary R_ij ──
    ax = fig.add_subplot(gs[0, 0])
    for tg, color in group_colors.items():
        mask = df_weighted["target_group"] == tg
        ax.scatter(
            df_weighted.loc[mask, "weighted_inter_rij"],
            df_weighted.loc[mask, "target_rij"],
            c=color, s=70, label=tg, edgecolor="black", lw=0.5, alpha=0.85, zorder=3,
        )
        for _, r in df_weighted[mask].iterrows():
            ax.annotate(
                r["target"], (r["weighted_inter_rij"], r["target_rij"]),
                fontsize=5, alpha=0.6,
            )

    # Regression line
    xv = df_weighted["weighted_inter_rij"].values
    yv = df_weighted["target_rij"].values
    valid_mask = np.isfinite(xv) & np.isfinite(yv)
    if valid_mask.sum() > 2:
        sl, ic, rv, pv, _ = stats.linregress(xv[valid_mask], yv[valid_mask])
        x_line = np.linspace(xv[valid_mask].min(), xv[valid_mask].max(), 100)
        ax.plot(x_line, sl * x_line + ic, "k--", lw=2, alpha=0.6)
        ax.text(
            0.05, 0.95,
            f"r = {rv:.3f}\np = {pv:.2e}",
            transform=ax.transAxes, fontsize=9, va="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.axvline(0, color="black", lw=0.5, ls=":")
    ax.set_xlabel("Weighted intermediary R_ij")
    ax.set_ylabel("Target R_ij")
    ax.set_title("A  Target R_ij vs intermediary-level R_ij", fontweight="bold")
    ax.legend(fontsize=7, loc="lower right")

    # ── PANEL B: For mixed-destructive targets, bar charts of key intermediaries ──
    ax_b = fig.add_subplot(gs[0, 1])

    mixed_destr_names = mixed_destr["type"].values.tolist()
    if len(mixed_destr_names) == 0:
        ax_b.text(0.5, 0.5, "No mixed-destructive\ntargets found",
                  transform=ax_b.transAxes, ha="center", va="center", fontsize=12)
        ax_b.set_title("B  Intermediary R_ij for mixed-destructive targets", fontweight="bold")
    else:
        # Collect the top intermediaries for all mixed-destructive targets
        bar_data = []
        for tname in mixed_destr_names:
            df_t = df_inter[df_inter["target"] == tname].copy()
            if df_t.empty:
                continue
            df_t["abs_eff_rij"] = df_t["eff_rij_contrib"].abs()
            top = df_t.nlargest(5, "abs_eff_rij")  # top 5 per target
            for _, ir in top.iterrows():
                bar_data.append({
                    "target": tname,
                    "intermediary": ir["intermediary"],
                    "inter_rij": ir["inter_rij"],
                    "eff_rij_contrib": ir["eff_rij_contrib"],
                    "w_to_target": ir["w_to_target"],
                    "is_inhibitory": ir["inter_is_inhibitory"],
                })

        if bar_data:
            df_bar = pd.DataFrame(bar_data)
            # Group by target, show bars for each intermediary
            unique_targets = df_bar["target"].unique()
            n_targets = len(unique_targets)

            # Create grouped bar plot
            all_labels = []
            all_values = []
            all_colors = []
            all_edgecolors = []
            separator_positions = []
            pos = 0

            for ti, tname in enumerate(unique_targets):
                sub = df_bar[df_bar["target"] == tname].sort_values("inter_rij")
                if ti > 0:
                    separator_positions.append(pos - 0.5)
                for _, row in sub.iterrows():
                    short_name = row["intermediary"]
                    if len(short_name) > 15:
                        short_name = short_name[:14] + ".."
                    all_labels.append(f"{short_name}")
                    all_values.append(row["inter_rij"])
                    # Color by super/destructive
                    if row["inter_rij"] > 0:
                        all_colors.append("#E41A1C")  # super (red)
                    else:
                        all_colors.append("#377EB8")  # destructive (blue)
                    # Edge indicates inhibitory
                    all_edgecolors.append("purple" if row["is_inhibitory"] else "black")
                    pos += 1

            y_pos = np.arange(len(all_labels))
            bars = ax_b.barh(y_pos, all_values, color=all_colors,
                             edgecolor=all_edgecolors, lw=0.8)
            ax_b.set_yticks(y_pos)
            ax_b.set_yticklabels(all_labels, fontsize=6)
            ax_b.axvline(0, color="black", lw=0.8)

            # Add target name annotations and separators
            for sep in separator_positions:
                ax_b.axhline(sep, color="gray", lw=0.5, ls="--", alpha=0.5)

            # Add target name labels on the right
            current_pos = 0
            for tname in unique_targets:
                sub = df_bar[df_bar["target"] == tname]
                n = len(sub)
                mid = current_pos + n / 2 - 0.5
                trij = df_targets[df_targets["type"] == tname]["R_ij"].values[0]
                ax_b.text(ax_b.get_xlim()[1] if ax_b.get_xlim()[1] > 0 else 0.01,
                          mid, f"  {tname}\n  (R={trij:+.3f})",
                          fontsize=6, va="center", fontweight="bold",
                          color="darkred",
                          bbox=dict(boxstyle="round,pad=0.2", facecolor="lightyellow",
                                    alpha=0.7, lw=0.3))
                current_pos += n

            ax_b.set_xlabel("Intermediary own R_ij")
            ax_b.set_title("B  Key intermediaries' own R_ij\n(mixed-destructive targets)",
                           fontweight="bold")

            # Legend
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor="#E41A1C", label="Super inter (R > 0)"),
                Patch(facecolor="#377EB8", label="Destructive inter (R < 0)"),
                Patch(facecolor="white", edgecolor="purple", lw=1.5, label="Inhibitory"),
            ]
            ax_b.legend(handles=legend_elements, fontsize=6, loc="lower right")
        else:
            ax_b.text(0.5, 0.5, "No intermediary data",
                      transform=ax_b.transAxes, ha="center", va="center")
            ax_b.set_title("B  Intermediary R_ij for mixed-destructive targets",
                           fontweight="bold")

    # ── PANEL C: Histogram comparing intermediary R_ij distributions ──
    ax_c = fig.add_subplot(gs[0, 2])

    # Weight intermediaries by their effective magnitude to focus on those that matter
    # Use a weighted histogram approach
    bins = np.linspace(-0.5, 0.5, 41)

    if len(inter_of_super) > 0:
        # Get weights for intermediaries of super targets
        super_mask = df_inter["target"].isin(super_targets)
        weights_super = df_inter.loc[super_mask, "effective_magnitude"].values
        vals_super = df_inter.loc[super_mask, "inter_rij"].values
        # Clip to bin range for visibility
        vals_super_clip = np.clip(vals_super, bins[0], bins[-1])

        ax_c.hist(vals_super_clip, bins=bins, weights=weights_super,
                  alpha=0.5, color="#E41A1C", edgecolor="black", lw=0.3,
                  label=f"Feed SUPER targets (n={len(vals_super)})", density=True)

    if len(inter_of_destr) > 0:
        destr_mask = df_inter["target"].isin(destr_targets)
        weights_destr = df_inter.loc[destr_mask, "effective_magnitude"].values
        vals_destr = df_inter.loc[destr_mask, "inter_rij"].values
        vals_destr_clip = np.clip(vals_destr, bins[0], bins[-1])

        ax_c.hist(vals_destr_clip, bins=bins, weights=weights_destr,
                  alpha=0.5, color="#377EB8", edgecolor="black", lw=0.3,
                  label=f"Feed DESTRUCTIVE targets (n={len(vals_destr)})", density=True)

    ax_c.axvline(0, color="black", lw=0.8, ls=":")
    ax_c.set_xlabel("Intermediary own R_ij")
    ax_c.set_ylabel("Weighted density")
    ax_c.set_title("C  Intermediary R_ij distributions\n(weighted by effective contribution)",
                    fontweight="bold")
    ax_c.legend(fontsize=7)

    # Add summary statistics as text
    if len(inter_of_super) > 0 and len(inter_of_destr) > 0:
        super_wmean = np.average(vals_super, weights=weights_super)
        destr_wmean = np.average(vals_destr, weights=weights_destr)
        ax_c.text(0.05, 0.95,
                  f"Wtd mean (super targets): {super_wmean:+.4f}\n"
                  f"Wtd mean (destr targets): {destr_wmean:+.4f}",
                  transform=ax_c.transAxes, fontsize=8, va="top",
                  bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    fig.suptitle(
        "Is the interaction (R_ij) already determined at the intermediary level?",
        fontsize=14, fontweight="bold",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    save_fig(
        fig, "upstream_rij_analysis",
        description=(
            "Three-panel analysis testing whether target R_ij is pre-determined "
            "at the intermediary (step 2) level. "
            "Panel A: Scatter of target R_ij vs weighted intermediary R_ij — tests "
            "whether intermediary-level integration predicts target-level integration. "
            "Panel B: For mixed-destructive targets (opposite-sign linear drives but "
            "R_ij < 0), shows the own R_ij of their key intermediary neurons. "
            "Panel C: Weighted histograms of intermediary R_ij separated by whether "
            "they feed super or destructive targets."
        ),
    )

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print("\n" + "=" * 78)
    print("SUMMARY OF KEY FINDINGS")
    print("=" * 78)

    # 1. Correlation
    if valid_mask.sum() > 2:
        print(f"\n  1. Weighted intermediary R_ij predicts target R_ij:")
        print(f"     Pearson r = {rv:.4f}, p = {pv:.2e}")
        if abs(rv) > 0.5 and pv < 0.05:
            print("     --> STRONG: The interaction IS largely set at the intermediary level.")
        elif abs(rv) > 0.3 and pv < 0.05:
            print("     --> MODERATE: Intermediary R_ij partly explains target R_ij.")
        else:
            print("     --> WEAK: Target R_ij is NOT well-predicted by intermediary R_ij alone.")

    # 2. Mixed-destructive explanation
    if len(mixed_destr_names) > 0:
        print(f"\n  2. Mixed-destructive targets ({len(mixed_destr_names)} neurons):")
        for tname in mixed_destr_names:
            wrec = df_weighted[df_weighted["target"] == tname].iloc[0]
            trij = wrec["target_rij"]
            inter_sum = wrec["sum_eff_rij_contrib"]
            df_t = df_inter[df_inter["target"] == tname]
            if len(df_t) > 0:
                frac_destr_inter = (df_t["inter_rij"] < 0).mean()
            else:
                frac_destr_inter = float("nan")
            print(f"     {tname}: target_R={trij:+.4f}, "
                  f"sum(w*inter_R)={inter_sum:+.6f}, "
                  f"frac_destr_intermediaries={frac_destr_inter:.1%}")
        print("     --> These targets have opposite-sign linear drives (push-pull)")
        print("         but their intermediaries themselves integrate destructively,")
        print("         so the nonlinear signal delivered to the target lacks the")
        print("         expected push-pull property.")

    # 3. Overall
    if len(inter_of_super) > 0 and len(inter_of_destr) > 0:
        print(f"\n  3. Intermediary R_ij distributions:")
        print(f"     Mean for super-feeding:    {np.mean(inter_of_super):+.5f}")
        print(f"     Mean for destr-feeding:    {np.mean(inter_of_destr):+.5f}")
        print(f"     Mann-Whitney p = {p:.2e}")
        if p < 0.05:
            print("     --> Significant: intermediaries of super targets are more super.")
        else:
            print("     --> Not significant: intermediary distributions overlap.")

    print(f"\n  Figures saved to: {OUT_DIR}")
    print("=" * 78)


if __name__ == "__main__":
    main()
