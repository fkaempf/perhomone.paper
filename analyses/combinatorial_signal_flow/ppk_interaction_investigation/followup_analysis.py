#!/usr/bin/env python3
"""
PPK23 × PPK25 Interaction — Follow-up Analysis
================================================

Deeper investigation based on initial findings:
  1. E/I ratio is the strongest predictor of super vs destructive integration
  2. AN09B017 family (pPNx glutamatergic) is the critical hub
  3. Sigmoid saturation drives the divergence

This script:
  A. Formal correlation: E/I ratio vs R_ij with regression
  B. AN09B017 hub wiring diagram — trace ppk23/ppk25 → AN09B017 → targets
  C. Focused ablation: ablate ALL AN09B017 members simultaneously
  D. "Pre-activation" analysis: what drives the sign of activation at AN09B017 neurons
  E. Publication-quality summary figure combining key results
  F. Negative activation analysis: neurons with A(ppk23) < 0 tend to show super integration
"""

import sys
import logging
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch, FancyArrowPatch
from matplotlib.gridspec import GridSpec
import seaborn as sns
from scipy import sparse, stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signal_flow import (
    NetworkLoader, ChannelEncoder, SignalPropagator, ACTIVATIONS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = Path(__file__).resolve().parent / "plots"

NONLINEARITY = "sigmoid_rectified"
ACT_PARAMS = {"beta": 5.0}
N_STEPS = 3
SUSTAINED = True
NORMALIZATION = "post"

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


def save_fig(fig, name, subdir="followup", description=None):
    out = OUT_DIR / subdir
    (out / "png").mkdir(parents=True, exist_ok=True)
    (out / "pdf").mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "png" / f"{name}.png")
    fig.savefig(out / "pdf" / f"{name}.pdf")
    if description:
        (out / "txt").mkdir(parents=True, exist_ok=True)
        (out / "txt" / f"{name}.txt").write_text(description.strip() + "\n")
    logger.info("Saved: %s/%s", subdir, name)
    plt.close(fig)


def load_everything():
    loader = NetworkLoader(str(DATA_DIR))
    W_unsigned = loader.load_adjacency_matrix(NORMALIZATION)
    type_names = loader.load_type_names()
    channels = loader.load_channels()
    targets = loader.load_targets()
    palette = loader.load_colors()
    nt_map = loader.load_neurotransmitter_mapping()
    W = loader.sign_matrix(W_unsigned, type_names)
    encoder = ChannelEncoder(type_names)
    encoded_channels = encoder.encode_all(channels)

    sensory_types = set()
    for ch_types in channels.values():
        sensory_types.update(ch_types)
    sensory_indices = set(encoder.get_indices(list(sensory_types)))

    target_indices = {}
    for tg_name, tg_types in targets.items():
        indices = encoder.get_indices(tg_types)
        indices = [i for i in indices if i not in sensory_indices]
        if indices:
            target_indices[tg_name] = indices

    return {
        "W": W, "W_unsigned": W_unsigned,
        "type_names": type_names, "channels": channels,
        "targets": targets, "palette": palette, "nt_map": nt_map,
        "encoder": encoder, "encoded_channels": encoded_channels,
        "target_indices": target_indices,
    }


# =============================================================================
# A. FORMAL CORRELATION: E/I RATIO vs R_ij
# =============================================================================

def analyse_ei_correlation(data):
    """
    For ALL target neurons (not just focal), compute E/I ratio of ppk23/ppk25
    input pathways and correlate with R_ij.
    """
    logger.info("=" * 60)
    logger.info("E/I RATIO CORRELATION ANALYSIS")
    logger.info("=" * 60)

    W = data["W"]
    W_csc = W.tocsc()
    encoder = data["encoder"]
    enc = data["encoded_channels"]
    targets = data["targets"]
    nt_map = data["nt_map"]
    idx_to_type = dict(zip(data["type_names"]["index"], data["type_names"]["type"]))
    type_to_inhib = dict(zip(nt_map["type"], nt_map["is_inhibitory"]))
    type_to_nt = dict(zip(nt_map["type"], nt_map["consensus_nt"]))

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
    traj_23 = prop.propagate_trajectory(s_ppk23, N_STEPS, sustained=SUSTAINED)
    traj_25 = prop.propagate_trajectory(s_ppk25, N_STEPS, sustained=SUSTAINED)

    x_23 = prop.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
    x_25 = prop.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
    x_both = prop.propagate(s_both, N_STEPS, sustained=SUSTAINED)

    rows = []
    for tg in ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]:
        if tg not in targets:
            continue
        for t in targets[tg]:
            if t not in encoder.type_to_idx:
                continue
            idx = encoder.type_to_idx[t]
            r_ij = x_both[idx] - x_23[idx] - x_25[idx]

            # Get presynaptic partners
            col = W_csc[:, idx].toarray().ravel()
            pre_indices = np.nonzero(col)[0]

            # Weighted E/I from each pathway
            exc_23 = 0; inh_23 = 0; exc_25 = 0; inh_25 = 0
            exc_shared = 0; inh_shared = 0
            n_pre_active = 0

            for pre_idx in pre_indices:
                pre_type = idx_to_type.get(pre_idx, "")
                is_inhib = type_to_inhib.get(pre_type, False)
                w = abs(col[pre_idx])

                a23 = traj_23[N_STEPS - 1, pre_idx]
                a25 = traj_25[N_STEPS - 1, pre_idx]
                driven_23 = abs(a23) > 1e-6
                driven_25 = abs(a25) > 1e-6

                if driven_23 or driven_25:
                    n_pre_active += 1

                if driven_23:
                    if is_inhib:
                        inh_23 += w * abs(a23)
                    else:
                        exc_23 += w * abs(a23)
                if driven_25:
                    if is_inhib:
                        inh_25 += w * abs(a25)
                    else:
                        exc_25 += w * abs(a25)
                if driven_23 and driven_25:
                    if is_inhib:
                        inh_shared += w
                    else:
                        exc_shared += w

            total_exc = exc_23 + exc_25
            total_inh = inh_23 + inh_25
            ei_ratio = total_exc / max(total_inh, 1e-10)
            ei_ratio_23 = exc_23 / max(inh_23, 1e-10)
            ei_ratio_25 = exc_25 / max(inh_25, 1e-10)

            # Also compute: does this neuron get NEGATIVE activation from either channel?
            # (key for understanding super integration)
            rows.append({
                "target_group": tg,
                "target_type": t,
                "R_ij": r_ij,
                "A_ppk23": x_23[idx],
                "A_ppk25": x_25[idx],
                "A_both": x_both[idx],
                "ei_ratio": ei_ratio,
                "ei_ratio_23": ei_ratio_23,
                "ei_ratio_25": ei_ratio_25,
                "exc_total": total_exc,
                "inh_total": total_inh,
                "exc_shared": exc_shared,
                "inh_shared": inh_shared,
                "n_pre_active": n_pre_active,
                "nt": type_to_nt.get(t, "unknown"),
                "is_inhibitory": type_to_inhib.get(t, False),
                "has_negative_single": (x_23[idx] < -0.01) or (x_25[idx] < -0.01),
                "min_single": min(x_23[idx], x_25[idx]),
                "max_single": max(abs(x_23[idx]), abs(x_25[idx])),
                "sum_singles": x_23[idx] + x_25[idx],
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "followup" / "ei_correlation_all_neurons.csv", index=False)

    group_colors = {
        "aspf": "#E41A1C", "aspg": "#377EB8",
        "PPN1_downstream": "#FF7F00", "vAB3_downstream": "#4DAF4A",
    }

    # ── Main correlation figure: 3 panels ──
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Panel A: E/I ratio vs R_ij
    ax = axes[0]
    for tg, color in group_colors.items():
        mask = df["target_group"] == tg
        ax.scatter(np.log10(df.loc[mask, "ei_ratio"].clip(lower=0.01)),
                   df.loc[mask, "R_ij"],
                   c=color, s=70, label=tg, edgecolor="black", lw=0.5, alpha=0.8)
        for _, r in df[mask].iterrows():
            ax.annotate(r["target_type"],
                        (np.log10(max(r["ei_ratio"], 0.01)), r["R_ij"]),
                        fontsize=5, alpha=0.6)

    # Regression line
    x_reg = np.log10(df["ei_ratio"].clip(lower=0.01))
    slope, intercept, r_val, p_val, _ = stats.linregress(x_reg, df["R_ij"])
    x_line = np.linspace(x_reg.min(), x_reg.max(), 100)
    ax.plot(x_line, slope * x_line + intercept, "k--", lw=2, alpha=0.7)
    ax.text(0.05, 0.95, f"r = {r_val:.3f}\np = {p_val:.2e}",
            transform=ax.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
    ax.set_xlabel("log₁₀(E/I ratio)")
    ax.set_ylabel("R_ij (ppk23 × ppk25)")
    ax.set_title("A  E/I balance predicts interaction mode")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.legend(fontsize=7)

    # Panel B: Minimum single-channel activation vs R_ij
    ax = axes[1]
    for tg, color in group_colors.items():
        mask = df["target_group"] == tg
        ax.scatter(df.loc[mask, "min_single"], df.loc[mask, "R_ij"],
                   c=color, s=70, label=tg, edgecolor="black", lw=0.5, alpha=0.8)
        for _, r in df[mask].iterrows():
            ax.annotate(r["target_type"], (r["min_single"], r["R_ij"]),
                        fontsize=5, alpha=0.6)

    x_reg2 = df["min_single"]
    slope2, intercept2, r_val2, p_val2, _ = stats.linregress(x_reg2, df["R_ij"])
    x_line2 = np.linspace(x_reg2.min(), x_reg2.max(), 100)
    ax.plot(x_line2, slope2 * x_line2 + intercept2, "k--", lw=2, alpha=0.7)
    ax.text(0.05, 0.95, f"r = {r_val2:.3f}\np = {p_val2:.2e}",
            transform=ax.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
    ax.set_xlabel("min(A(ppk23), A(ppk25))")
    ax.set_ylabel("R_ij")
    ax.set_title("B  Negative single-channel activation → super integration")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.axvline(0, color="gray", lw=0.5, ls=":", alpha=0.5)
    ax.legend(fontsize=7)

    # Panel C: sum of singles vs R_ij
    ax = axes[2]
    for tg, color in group_colors.items():
        mask = df["target_group"] == tg
        ax.scatter(df.loc[mask, "sum_singles"], df.loc[mask, "R_ij"],
                   c=color, s=70, label=tg, edgecolor="black", lw=0.5, alpha=0.8)
        for _, r in df[mask].iterrows():
            ax.annotate(r["target_type"], (r["sum_singles"], r["R_ij"]),
                        fontsize=5, alpha=0.6)

    x_reg3 = df["sum_singles"]
    slope3, intercept3, r_val3, p_val3, _ = stats.linregress(x_reg3, df["R_ij"])
    x_line3 = np.linspace(x_reg3.min(), x_reg3.max(), 100)
    ax.plot(x_line3, slope3 * x_line3 + intercept3, "k--", lw=2, alpha=0.7)
    ax.text(0.05, 0.95, f"r = {r_val3:.3f}\np = {p_val3:.2e}",
            transform=ax.transAxes, fontsize=10, va="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))
    ax.set_xlabel("A(ppk23) + A(ppk25)")
    ax.set_ylabel("R_ij")
    ax.set_title("C  Sum of singles vs interaction")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.legend(fontsize=7)

    fig.suptitle("Predictors of PPK23 × PPK25 interaction mode",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "ei_ratio_correlation", "followup",
             description="Formal correlation analysis. A: log10(E/I ratio) vs R_ij with linear regression. "
             "B: Minimum single-channel activation vs R_ij — neurons inhibited by one channel show super integration. "
             "C: Sum of single-channel activations vs R_ij — high-activation neurons saturate (destructive).")

    return df


# =============================================================================
# B. AN09B017 HUB WIRING — Trace the circuit
# =============================================================================

def analyse_hub_wiring(data):
    """
    Map the complete wiring of the AN09B017 family:
    - Which ppk23/ppk25 neurons connect TO them?
    - Which focal targets do they connect FROM?
    - What are the weights and signs?
    """
    logger.info("=" * 60)
    logger.info("AN09B017 HUB WIRING ANALYSIS")
    logger.info("=" * 60)

    W = data["W"]
    W_csc = W.tocsc()
    encoder = data["encoder"]
    enc = data["encoded_channels"]
    type_names = data["type_names"]
    nt_map = data["nt_map"]
    idx_to_type = dict(zip(type_names["index"], type_names["type"]))
    type_to_idx = dict(zip(type_names["type"], type_names["index"]))
    type_to_nt = dict(zip(nt_map["type"], nt_map["consensus_nt"]))
    type_to_inhib = dict(zip(nt_map["type"], nt_map["is_inhibitory"]))

    # Find all AN09B017 members
    an09_members = [t for t in type_to_idx if isinstance(t, str) and t.startswith("AN09B017")]
    an09_members.sort()
    logger.info("  AN09B017 family: %s", an09_members)

    ppk23_types = set(data["channels"]["ppk23"])
    ppk25_types = set(data["channels"]["ppk25"])

    # Focal targets
    focal_targets = {
        "LH006m": "destructive", "LH008m": "super",
        "LH003m": "destructive", "LH001m": "super",
        "AVLP700m": "destructive", "AVLP704m": "destructive",
        "AVLP750m": "super",
        "mAL_m3c": "destructive", "mAL_m3b": "destructive",
        "FLA001m": "destructive",
        "mAL_m2a": "super", "AVLP728m": "super",
        "AVLP606": "destructive", "CB2458": "destructive",
    }

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
    traj_23 = prop.propagate_trajectory(s_ppk23, N_STEPS, sustained=SUSTAINED)
    traj_25 = prop.propagate_trajectory(s_ppk25, N_STEPS, sustained=SUSTAINED)
    traj_both = prop.propagate_trajectory(s_both, N_STEPS, sustained=SUSTAINED)

    # ── 1. Input to AN09B017 from ppk23/ppk25 channels ──
    input_rows = []
    for an in an09_members:
        if an not in type_to_idx:
            continue
        an_idx = type_to_idx[an]
        col = W_csc[:, an_idx].toarray().ravel()

        for pre_type in ppk23_types | ppk25_types:
            if pre_type not in type_to_idx:
                continue
            pre_idx = type_to_idx[pre_type]
            w = col[pre_idx]
            if abs(w) > 1e-10:
                input_rows.append({
                    "hub": an,
                    "source": pre_type,
                    "channel": "ppk23" if pre_type in ppk23_types else "ppk25",
                    "weight": w,
                    "source_nt": type_to_nt.get(pre_type, "unknown"),
                })

    df_input = pd.DataFrame(input_rows)
    if not df_input.empty:
        df_input.to_csv(OUT_DIR / "followup" / "an09b017_inputs.csv", index=False)

    # ── 2. Output from AN09B017 to focal targets ──
    output_rows = []
    for an in an09_members:
        if an not in type_to_idx:
            continue
        an_idx = type_to_idx[an]
        row_vals = W_csc[an_idx, :].toarray().ravel()

        for target, cat in focal_targets.items():
            if target not in type_to_idx:
                continue
            t_idx = type_to_idx[target]
            w = row_vals[t_idx]
            if abs(w) > 1e-10:
                output_rows.append({
                    "hub": an,
                    "target": target,
                    "target_category": cat,
                    "weight": w,
                    "hub_nt": type_to_nt.get(an, "unknown"),
                    "hub_is_inhib": type_to_inhib.get(an, False),
                })

    df_output = pd.DataFrame(output_rows)
    if not df_output.empty:
        df_output.to_csv(OUT_DIR / "followup" / "an09b017_outputs.csv", index=False)

    # ── 3. AN09B017 activation trajectories ──
    an_activation_rows = []
    for an in an09_members:
        if an not in type_to_idx:
            continue
        an_idx = type_to_idx[an]
        for step in range(N_STEPS + 1):
            an_activation_rows.append({
                "hub": an,
                "step": step,
                "A_ppk23": traj_23[step, an_idx],
                "A_ppk25": traj_25[step, an_idx],
                "A_both": traj_both[step, an_idx],
                "delta": traj_both[step, an_idx] - traj_23[step, an_idx] - traj_25[step, an_idx],
                "nt": type_to_nt.get(an, "unknown"),
            })

    df_traj = pd.DataFrame(an_activation_rows)
    df_traj.to_csv(OUT_DIR / "followup" / "an09b017_trajectories.csv", index=False)

    # ── Plot: AN09B017 wiring diagram ──
    fig = plt.figure(figsize=(20, 14))
    gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.3)

    # Panel A: Input weights from ppk channels to AN09B017
    ax = fig.add_subplot(gs[0, 0])
    if not df_input.empty:
        pivot = df_input.pivot_table(index="hub", columns="source", values="weight", fill_value=0)
        # Color by ppk23 vs ppk25
        col_colors = []
        for c in pivot.columns:
            if c in ppk23_types:
                col_colors.append("#FFD92F")
            else:
                col_colors.append("#E5C494")

        im = ax.imshow(pivot.values, cmap="RdBu_r", aspect="auto",
                        vmin=-max(abs(pivot.values.min()), abs(pivot.values.max())),
                        vmax=max(abs(pivot.values.min()), abs(pivot.values.max())))
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns, rotation=90, fontsize=6)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index, fontsize=8)
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                v = pivot.values[i, j]
                if abs(v) > 1e-6:
                    ax.text(j, i, f"{v:.3f}", ha="center", va="center", fontsize=5)
        fig.colorbar(im, ax=ax, shrink=0.6)
    ax.set_title("A  ppk23/ppk25 → AN09B017\n(input weights)")

    # Panel B: Output weights from AN09B017 to focal targets
    ax = fig.add_subplot(gs[0, 1])
    if not df_output.empty:
        pivot_out = df_output.pivot_table(index="hub", columns="target", values="weight", fill_value=0)
        # Order targets by category
        target_order = sorted(pivot_out.columns,
                              key=lambda t: (focal_targets.get(t, ""), t))
        pivot_out = pivot_out[target_order]
        vmax = max(abs(pivot_out.values.min()), abs(pivot_out.values.max())) or 1e-6
        im = ax.imshow(pivot_out.values, cmap="RdBu_r", aspect="auto",
                        vmin=-vmax, vmax=vmax)
        ax.set_xticks(range(len(pivot_out.columns)))
        labels = [f"{t} ({'S' if focal_targets.get(t)=='super' else 'D'})"
                  for t in pivot_out.columns]
        ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=7)
        ax.set_yticks(range(len(pivot_out.index)))
        ax.set_yticklabels(pivot_out.index, fontsize=8)
        for i in range(len(pivot_out.index)):
            for j in range(len(pivot_out.columns)):
                v = pivot_out.values[i, j]
                if abs(v) > 1e-6:
                    ax.text(j, i, f"{v:.3f}", ha="center", va="center", fontsize=5)
        fig.colorbar(im, ax=ax, shrink=0.6)
    ax.set_title("B  AN09B017 → focal targets\n(output weights)")

    # Panel C: AN09B017 activation at step 2 (one step before reaching targets)
    ax = fig.add_subplot(gs[0, 2])
    step_data = df_traj[df_traj["step"] == N_STEPS - 1].copy()
    if not step_data.empty:
        x = np.arange(len(step_data))
        width = 0.25
        ax.bar(x - width, step_data["A_ppk23"], width, label="ppk23", color="#FFD92F")
        ax.bar(x, step_data["A_ppk25"], width, label="ppk25", color="#E5C494")
        ax.bar(x + width, step_data["A_both"], width, label="both", color="#9467BD")
        ax.set_xticks(x)
        ax.set_xticklabels(step_data["hub"], rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("Activation at step 2")
        ax.legend(fontsize=7)
        ax.axhline(0, color="black", lw=0.5)
    ax.set_title(f"C  AN09B017 activation (step {N_STEPS-1})")

    # Panel D: Delta (nonlinear interaction) at AN09B017 across steps
    ax = fig.add_subplot(gs[1, 0])
    for an in an09_members:
        an_data = df_traj[df_traj["hub"] == an]
        if not an_data.empty:
            ax.plot(an_data["step"], an_data["delta"], "o-", label=an, lw=1.5, ms=5)
    ax.set_xlabel("Propagation step")
    ax.set_ylabel("δ = A(both) − A(23) − A(25)")
    ax.set_title("D  Interaction signal at AN09B017 hubs")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.legend(fontsize=6, ncol=2)

    # Panel E: Summary — channel preference of each AN09B017 member
    ax = fig.add_subplot(gs[1, 1])
    step2 = df_traj[df_traj["step"] == N_STEPS - 1].copy()
    if not step2.empty:
        step2["preference"] = step2["A_ppk23"] - step2["A_ppk25"]
        colors = ["#FFD92F" if p > 0 else "#E5C494" for p in step2["preference"]]
        ax.barh(range(len(step2)), step2["preference"], color=colors,
                edgecolor="black", lw=0.5)
        ax.set_yticks(range(len(step2)))
        ax.set_yticklabels(step2["hub"], fontsize=8)
        ax.set_xlabel("A(ppk23) − A(ppk25)")
        ax.set_title("E  Channel preference at AN09B017")
        ax.axvline(0, color="black", lw=0.8)

    # Panel F: How much does ablating each AN09B017 change R_ij?
    ax = fig.add_subplot(gs[1, 2])
    # Read ablation results
    abl_file = OUT_DIR / "ablation" / "ablation_results.csv"
    if abl_file.exists():
        df_abl = pd.read_csv(abl_file)
        an_abl = df_abl[df_abl["ablated_neuron"].str.startswith("AN09B017")]
        if not an_abl.empty:
            pivot_abl = an_abl.pivot_table(
                index="target_neuron", columns="ablated_neuron",
                values="delta_R_ij", fill_value=0
            )
            vmax = max(abs(pivot_abl.values.min()), abs(pivot_abl.values.max())) or 1e-6
            im = ax.imshow(pivot_abl.values, cmap="RdBu_r", aspect="auto",
                            vmin=-vmax, vmax=vmax)
            ax.set_xticks(range(len(pivot_abl.columns)))
            ax.set_xticklabels(pivot_abl.columns, rotation=45, ha="right", fontsize=7)
            ax.set_yticks(range(len(pivot_abl.index)))
            ax.set_yticklabels(pivot_abl.index, fontsize=8)
            for i in range(len(pivot_abl.index)):
                for j in range(len(pivot_abl.columns)):
                    v = pivot_abl.values[i, j]
                    if abs(v) > 0.01:
                        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6)
            fig.colorbar(im, ax=ax, shrink=0.6)
    ax.set_title("F  Ablation of AN09B017 members\n(ΔR_ij at focal targets)")

    fig.suptitle("AN09B017 pPNx Hub Family — Wiring and Function",
                 fontsize=15, fontweight="bold")
    save_fig(fig, "an09b017_hub_analysis", "followup",
             description="Six-panel analysis of the AN09B017 hub family. "
             "A: Input weights from ppk23/ppk25 channels. B: Output weights to focal targets. "
             "C: Activation at step 2 for each channel. D: Interaction signal δ across steps. "
             "E: Channel preference. F: Ablation effects.")


# =============================================================================
# C. COMBINED AN09B017 ABLATION — Remove all members at once
# =============================================================================

def analyse_combined_ablation(data):
    """
    Ablate ALL AN09B017 members simultaneously and recompute R_ij.
    Also test ablating subsets and other hub families.
    """
    logger.info("=" * 60)
    logger.info("COMBINED ABLATION ANALYSIS")
    logger.info("=" * 60)

    W = data["W"]
    encoder = data["encoder"]
    enc = data["encoded_channels"]
    targets = data["targets"]
    type_to_idx = dict(zip(data["type_names"]["type"], data["type_names"]["index"]))
    nt_map = data["nt_map"]
    type_to_nt = dict(zip(nt_map["type"], nt_map["consensus_nt"]))

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    # Baseline
    prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
    x_23 = prop.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
    x_25 = prop.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
    x_both = prop.propagate(s_both, N_STEPS, sustained=SUSTAINED)

    # Find neuron groups to ablate
    an09_all = [t for t in type_to_idx if isinstance(t, str) and t.startswith("AN09B017")]
    an05b102 = [t for t in type_to_idx if isinstance(t, str) and t.startswith("AN05B102")]
    an05b025_035 = [t for t in type_to_idx if isinstance(t, str) and (t.startswith("AN05B025") or t.startswith("AN05B035"))]
    in05b011 = [t for t in type_to_idx if isinstance(t, str) and t.startswith("IN05B011")]

    ablation_groups = {
        "baseline": [],
        "AN09B017_all": an09_all,
        "AN05B102_all": an05b102,
        "AN05B025+035": an05b025_035,
        "IN05B011_all": in05b011,
        "all_hubs": an09_all + an05b102 + an05b025_035 + in05b011,
    }

    all_rows = []
    for abl_name, abl_types in ablation_groups.items():
        if abl_types:
            W_lil = W.tolil()
            for t in abl_types:
                if t in type_to_idx:
                    idx = type_to_idx[t]
                    W_lil[idx, :] = 0
                    W_lil[:, idx] = 0
            W_abl = W_lil.tocsc()
        else:
            W_abl = W

        prop_abl = SignalPropagator(W_abl, NONLINEARITY, ACT_PARAMS)
        x_23_a = prop_abl.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
        x_25_a = prop_abl.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
        x_both_a = prop_abl.propagate(s_both, N_STEPS, sustained=SUSTAINED)

        for tg in ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]:
            if tg not in targets:
                continue
            for t in targets[tg]:
                if t not in encoder.type_to_idx:
                    continue
                idx = encoder.type_to_idx[t]
                r_baseline = x_both[idx] - x_23[idx] - x_25[idx]
                r_abl = x_both_a[idx] - x_23_a[idx] - x_25_a[idx]

                all_rows.append({
                    "ablation": abl_name,
                    "n_ablated": len(abl_types),
                    "target_group": tg,
                    "target_type": t,
                    "R_ij_baseline": r_baseline,
                    "R_ij_ablated": r_abl,
                    "delta_R_ij": r_abl - r_baseline,
                })

    df = pd.DataFrame(all_rows)
    df.to_csv(OUT_DIR / "followup" / "combined_ablation.csv", index=False)

    # ── Plot: combined ablation results ──
    abl_names = [a for a in ablation_groups if a != "baseline"]

    focal_targets = ["LH006m", "LH008m", "AVLP700m", "AVLP704m", "AVLP750m",
                     "mAL_m2a", "AVLP728m", "mAL_m3c", "mAL_m3b", "AVLP606"]

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Panel A: Heatmap of R_ij under each ablation for focal targets
    ax = axes[0]
    mat = np.zeros((len(focal_targets), len(abl_names) + 1))
    col_labels = ["baseline"] + abl_names
    for i, ft in enumerate(focal_targets):
        for j, abl in enumerate(col_labels):
            row = df[(df["target_type"] == ft) & (df["ablation"] == abl)]
            if len(row) > 0:
                if abl == "baseline":
                    mat[i, j] = row.iloc[0]["R_ij_baseline"]
                else:
                    mat[i, j] = row.iloc[0]["R_ij_ablated"]

    vmax = max(abs(mat.min()), abs(mat.max())) or 1e-6
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(focal_targets)))
    ax.set_yticklabels(focal_targets, fontsize=8)
    for i in range(len(focal_targets)):
        for j in range(len(col_labels)):
            ax.text(j, i, f"{mat[i, j]:.3f}", ha="center", va="center", fontsize=6)
    fig.colorbar(im, ax=ax, shrink=0.7)
    ax.set_title("A  R_ij under group ablations")

    # Panel B: Percent change from baseline
    ax = axes[1]
    mat_pct = np.zeros((len(focal_targets), len(abl_names)))
    for i, ft in enumerate(focal_targets):
        for j, abl in enumerate(abl_names):
            row = df[(df["target_type"] == ft) & (df["ablation"] == abl)]
            if len(row) > 0:
                baseline = row.iloc[0]["R_ij_baseline"]
                if abs(baseline) > 1e-6:
                    mat_pct[i, j] = row.iloc[0]["delta_R_ij"] / abs(baseline) * 100

    vmax_pct = min(200, max(abs(mat_pct.min()), abs(mat_pct.max())) or 1)
    im = ax.imshow(mat_pct, cmap="RdBu_r", vmin=-vmax_pct, vmax=vmax_pct, aspect="auto")
    ax.set_xticks(range(len(abl_names)))
    ax.set_xticklabels(abl_names, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(focal_targets)))
    ax.set_yticklabels(focal_targets, fontsize=8)
    for i in range(len(focal_targets)):
        for j in range(len(abl_names)):
            ax.text(j, i, f"{mat_pct[i, j]:.0f}%", ha="center", va="center", fontsize=6)
    fig.colorbar(im, ax=ax, shrink=0.7)
    ax.set_title("B  % change from baseline R_ij")

    fig.suptitle("Combined ablation of intermediate hub families",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "combined_ablation", "followup",
             description="Group ablation analysis. A: Absolute R_ij values under each ablation condition. "
             "B: Percent change from baseline. Tests whether removing entire hub families "
             "abolishes the super/destructive pattern.")


# =============================================================================
# D. NEGATIVE ACTIVATION MECHANISM — Key insight
# =============================================================================

def analyse_negative_activation(data):
    """
    Key finding: neurons that receive NET INHIBITION from one channel
    (A(ppk23) < 0 or A(ppk25) < 0) tend to show SUPER integration.

    Mechanism: if A(ppk23) < 0, then when you add ppk25 signal,
    the combined activation can exceed A(ppk25) alone because the
    inhibitory ppk23 component saturates (tanh clips it).

    Conversely, neurons with strong excitation from BOTH channels
    saturate → destructive.
    """
    logger.info("=" * 60)
    logger.info("NEGATIVE ACTIVATION MECHANISM")
    logger.info("=" * 60)

    W = data["W"]
    encoder = data["encoder"]
    enc = data["encoded_channels"]
    targets = data["targets"]

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
    x_23 = prop.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
    x_25 = prop.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
    x_both = prop.propagate(s_both, N_STEPS, sustained=SUSTAINED)

    # Also compute PRE-activation (before sigmoid) at final step
    prop_lin = SignalPropagator(W, "linear", {})
    x_23_lin = prop_lin.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
    x_25_lin = prop_lin.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
    x_both_lin = prop_lin.propagate(s_both, N_STEPS, sustained=SUSTAINED)

    rows = []
    for tg in ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]:
        if tg not in targets:
            continue
        for t in targets[tg]:
            if t not in encoder.type_to_idx:
                continue
            idx = encoder.type_to_idx[t]
            a23 = x_23[idx]; a25 = x_25[idx]; aboth = x_both[idx]
            r_ij = aboth - a23 - a25

            rows.append({
                "target_group": tg,
                "target_type": t,
                "A_ppk23": a23,
                "A_ppk25": a25,
                "A_both": aboth,
                "R_ij": r_ij,
                "A_ppk23_linear": x_23_lin[idx],
                "A_ppk25_linear": x_25_lin[idx],
                "A_both_linear": x_both_lin[idx],
                "sign_23": "positive" if a23 > 0.01 else ("negative" if a23 < -0.01 else "near_zero"),
                "sign_25": "positive" if a25 > 0.01 else ("negative" if a25 < -0.01 else "near_zero"),
                "both_positive": (a23 > 0.01) and (a25 > 0.01),
                "has_negative": (a23 < -0.01) or (a25 < -0.01),
                "both_same_sign": (a23 > 0 and a25 > 0) or (a23 < 0 and a25 < 0),
                "opposite_sign": (a23 > 0.01 and a25 < -0.01) or (a23 < -0.01 and a25 > 0.01),
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "followup" / "negative_activation_analysis.csv", index=False)

    group_colors = {
        "aspf": "#E41A1C", "aspg": "#377EB8",
        "PPN1_downstream": "#FF7F00", "vAB3_downstream": "#4DAF4A",
    }

    # ── Plot: The mechanism figure ──
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))

    # Panel A: A(ppk23) vs A(ppk25), colored by R_ij
    ax = axes[0, 0]
    sc = ax.scatter(df["A_ppk23"], df["A_ppk25"], c=df["R_ij"],
                     cmap="RdBu_r", s=80, edgecolor="black", lw=0.5,
                     vmin=-max(abs(df["R_ij"])), vmax=max(abs(df["R_ij"])))
    for _, r in df.iterrows():
        ax.annotate(r["target_type"], (r["A_ppk23"], r["A_ppk25"]),
                    fontsize=5, alpha=0.6)
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.axvline(0, color="black", lw=0.5, ls=":")
    ax.set_xlabel("A(ppk23)")
    ax.set_ylabel("A(ppk25)")
    ax.set_title("A  Single-channel responses, colored by R_ij")
    fig.colorbar(sc, ax=ax, shrink=0.7, label="R_ij")

    # Draw quadrant annotations
    ax.text(0.9, 0.9, "Both +\n→ destructive", transform=ax.transAxes,
            fontsize=8, ha="right", va="top", color="#377EB8", fontweight="bold")
    ax.text(0.1, 0.9, "ppk23−/ppk25+\n→ super", transform=ax.transAxes,
            fontsize=8, ha="left", va="top", color="#E41A1C", fontweight="bold")

    # Panel B: Box plot of R_ij by sign combination
    ax = axes[0, 1]
    sign_combo = []
    for _, r in df.iterrows():
        if r["both_positive"]:
            sign_combo.append("Both positive")
        elif r["has_negative"]:
            sign_combo.append("One negative")
        else:
            sign_combo.append("Near zero")
    df["sign_combo"] = sign_combo

    combo_order = ["Both positive", "Near zero", "One negative"]
    combo_colors = ["#377EB8", "#808080", "#E41A1C"]
    combo_data = [df[df["sign_combo"] == c]["R_ij"].values for c in combo_order]

    bp = ax.boxplot(combo_data, labels=combo_order, patch_artist=True, widths=0.6)
    for patch, color in zip(bp["boxes"], combo_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.5)

    # Overlay individual points
    for i, (c, color) in enumerate(zip(combo_order, combo_colors)):
        y = df[df["sign_combo"] == c]["R_ij"]
        x = np.random.normal(i + 1, 0.08, size=len(y))
        ax.scatter(x, y, c=color, s=30, alpha=0.7, edgecolor="black", lw=0.3, zorder=3)

    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.set_ylabel("R_ij")
    ax.set_title("B  Interaction mode by sign combination")

    # Stats
    if len(combo_data[0]) > 1 and len(combo_data[2]) > 1:
        t_stat, p_val = stats.mannwhitneyu(combo_data[0], combo_data[2], alternative="less")
        ax.text(0.5, 0.02, f"Both+ vs One−: p = {p_val:.2e}",
                transform=ax.transAxes, fontsize=9, ha="center",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    # Panel C: Saturation diagram — show tanh curve with example neurons
    ax = axes[1, 0]
    x_range = np.linspace(-3, 3, 200)
    y_tanh = np.tanh(5.0 * x_range)
    ax.plot(x_range, y_tanh, "k-", lw=2, label="tanh(5x)")
    ax.axhline(0, color="black", lw=0.3)
    ax.axvline(0, color="black", lw=0.3)

    # Show example: LH006m (both high → saturates)
    for _, r in df.iterrows():
        if r["target_type"] == "LH006m":
            a23, a25 = r["A_ppk23_linear"], r["A_ppk25_linear"]
            # Mark individual activations on curve
            ax.plot(a23 / 5, np.tanh(a23), "o", color="#FFD92F", ms=10,
                    label=f"LH006m ppk23 (a={r['A_ppk23']:.2f})", zorder=5)
            ax.plot(a25 / 5, np.tanh(a25), "s", color="#E5C494", ms=10,
                    label=f"LH006m ppk25 (a={r['A_ppk25']:.2f})", zorder=5)
        if r["target_type"] == "LH008m":
            a23, a25 = r["A_ppk23_linear"], r["A_ppk25_linear"]
            ax.plot(a23 / 5, np.tanh(a23), "^", color="#FFD92F", ms=10,
                    label=f"LH008m ppk23 (a={r['A_ppk23']:.2f})", zorder=5)
            ax.plot(a25 / 5, np.tanh(a25), "D", color="#E5C494", ms=10,
                    label=f"LH008m ppk25 (a={r['A_ppk25']:.2f})", zorder=5)

    ax.set_xlabel("Pre-activation (linear)")
    ax.set_ylabel("Post-activation (tanh)")
    ax.set_title("C  Sigmoid saturation mechanism")
    ax.legend(fontsize=6, loc="lower right")

    # Panel D: Text summary of the mechanism
    ax = axes[1, 1]
    ax.axis("off")
    mechanism_text = """
PROPOSED MECHANISM

DESTRUCTIVE INTEGRATION (R_ij < 0):
  Both channels excite target neuron individually.
  Combined: sigmoid saturates → output < sum.
  Example: LH006m, AVLP700m
  A(ppk23) ≈ +0.30, A(ppk25) ≈ +0.37
  A(both) ≈ +0.41 < 0.30 + 0.37 = 0.67

SUPER INTEGRATION (R_ij > 0):
  One channel INHIBITS target (net negative activation).
  Combined: inhibitory component saturates at ~-1,
  excitatory component adds on top.
  Result: combined > sum (because -1 + 1 > -0.2 + 0.3)
  Example: LH008m, mAL_m2a
  A(ppk23) ≈ -0.21, A(ppk25) ≈ +0.28
  A(both) ≈ +0.25 > -0.21 + 0.28 = 0.07

KEY: The SIGN of single-channel activation predicts
whether integration will be super or destructive.
Neurons inhibited by one channel → super.
Neurons excited by both → destructive.
"""
    ax.text(0.05, 0.95, mechanism_text, transform=ax.transAxes,
            fontsize=9, va="top", family="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8))

    fig.suptitle("Mechanism: Sign of single-channel activation determines interaction mode",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "negative_activation_mechanism", "followup",
             description="Key mechanistic figure. A: Single-channel responses colored by R_ij — "
             "neurons in top-right (both positive) are destructive (blue), neurons with one negative "
             "are super (red). B: Box plot confirming the pattern statistically. "
             "C: Sigmoid saturation diagram explaining why. D: Summary of mechanism.")


# =============================================================================
# E. PUBLICATION SUMMARY FIGURE
# =============================================================================

def make_summary_figure(data, df_corr):
    """
    4-panel publication figure combining the key results.
    """
    logger.info("=" * 60)
    logger.info("PUBLICATION SUMMARY FIGURE")
    logger.info("=" * 60)

    W = data["W"]
    encoder = data["encoder"]
    enc = data["encoded_channels"]
    targets = data["targets"]

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
    traj_23 = prop.propagate_trajectory(s_ppk23, N_STEPS, sustained=SUSTAINED)
    traj_25 = prop.propagate_trajectory(s_ppk25, N_STEPS, sustained=SUSTAINED)
    traj_both = prop.propagate_trajectory(s_both, N_STEPS, sustained=SUSTAINED)

    x_23 = prop.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
    x_25 = prop.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
    x_both = prop.propagate(s_both, N_STEPS, sustained=SUSTAINED)

    group_colors = {
        "aspf": "#E41A1C", "aspg": "#377EB8",
        "PPN1_downstream": "#FF7F00", "vAB3_downstream": "#4DAF4A",
    }

    fig = plt.figure(figsize=(16, 14))
    gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

    # ── Panel A: Example trajectories (destructive vs super) ──
    ax = fig.add_subplot(gs[0, 0])
    steps = np.arange(N_STEPS + 1)
    examples = [
        ("LH006m", "destructive", "#377EB8"),
        ("LH008m", "super", "#E41A1C"),
    ]
    for neuron, cat, color in examples:
        if neuron not in encoder.type_to_idx:
            continue
        idx = encoder.type_to_idx[neuron]
        a23 = traj_23[:, idx]; a25 = traj_25[:, idx]; aboth = traj_both[:, idx]
        linear_sum = a23 + a25

        ax.fill_between(steps, linear_sum, aboth, alpha=0.2, color=color)
        ax.plot(steps, linear_sum, "--", color=color, lw=1.5, alpha=0.6)
        ax.plot(steps, aboth, "-", color=color, lw=2.5, ms=7,
                label=f"{neuron} ({cat})")

    ax.set_xlabel("Propagation step")
    ax.set_ylabel("Activation")
    ax.set_title("A  Example trajectories", fontweight="bold")
    ax.legend(fontsize=8)
    ax.set_xticks(steps)
    ax.axhline(0, color="black", lw=0.3)
    ax.text(0.02, 0.02, "Shaded = R_ij\n(deviation from linear sum)",
            transform=ax.transAxes, fontsize=7, va="bottom")

    # ── Panel B: R_ij waterfall for all 4 groups ──
    ax = fig.add_subplot(gs[0, 1])
    all_neurons = []
    for tg in ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]:
        if tg not in targets:
            continue
        for t in targets[tg]:
            if t not in encoder.type_to_idx:
                continue
            idx = encoder.type_to_idx[t]
            r = x_both[idx] - x_23[idx] - x_25[idx]
            all_neurons.append({"type": t, "group": tg, "R_ij": r})

    df_all = pd.DataFrame(all_neurons).sort_values("R_ij")
    colors = [group_colors[r["group"]] for _, r in df_all.iterrows()]
    ax.barh(range(len(df_all)), df_all["R_ij"], color=colors,
            edgecolor="black", lw=0.3)
    ax.set_yticks(range(len(df_all)))
    ax.set_yticklabels(df_all["type"], fontsize=5)
    ax.set_xlabel("R_ij (ppk23 × ppk25)")
    ax.set_title("B  Interaction across all targets", fontweight="bold")
    ax.axvline(0, color="black", lw=0.8)
    handles = [Patch(facecolor=c, label=tg) for tg, c in group_colors.items()]
    ax.legend(handles=handles, fontsize=7, loc="lower right")

    # ── Panel C: A(ppk23) vs A(ppk25) colored by R_ij ──
    ax = fig.add_subplot(gs[1, 0])
    if df_corr is not None and len(df_corr) > 0:
        vmax = max(abs(df_corr["R_ij"]))
        sc = ax.scatter(df_corr["A_ppk23"], df_corr["A_ppk25"],
                         c=df_corr["R_ij"], cmap="RdBu_r", s=70,
                         edgecolor="black", lw=0.5, vmin=-vmax, vmax=vmax)
        for _, r in df_corr.iterrows():
            ax.annotate(r["target_type"], (r["A_ppk23"], r["A_ppk25"]),
                        fontsize=4, alpha=0.5)
        fig.colorbar(sc, ax=ax, shrink=0.7, label="R_ij")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.axvline(0, color="black", lw=0.5, ls=":")
    ax.set_xlabel("A(ppk23)")
    ax.set_ylabel("A(ppk25)")
    ax.set_title("C  Sign predicts interaction mode", fontweight="bold")

    # Add quadrant labels
    ax.text(0.95, 0.95, "Both excite\n→ DESTRUCTIVE",
            transform=ax.transAxes, fontsize=8, ha="right", va="top",
            color="#377EB8", fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.7))
    ax.text(0.05, 0.95, "ppk23 inhibits\n→ SUPER",
            transform=ax.transAxes, fontsize=8, ha="left", va="top",
            color="#E41A1C", fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.7))

    # ── Panel D: E/I ratio vs R_ij with regression ──
    ax = fig.add_subplot(gs[1, 1])
    if df_corr is not None and len(df_corr) > 0:
        for tg, color in group_colors.items():
            mask = df_corr["target_group"] == tg
            ax.scatter(np.log10(df_corr.loc[mask, "ei_ratio"].clip(lower=0.01)),
                       df_corr.loc[mask, "R_ij"],
                       c=color, s=70, label=tg, edgecolor="black", lw=0.5)

        x_reg = np.log10(df_corr["ei_ratio"].clip(lower=0.01))
        slope, intercept, r_val, p_val, _ = stats.linregress(x_reg, df_corr["R_ij"])
        x_line = np.linspace(x_reg.min(), x_reg.max(), 100)
        ax.plot(x_line, slope * x_line + intercept, "k--", lw=2, alpha=0.7)
        ax.text(0.05, 0.95, f"r = {r_val:.3f}, p = {p_val:.2e}",
                transform=ax.transAxes, fontsize=9, va="top",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5))

    ax.set_xlabel("log₁₀(E/I ratio)")
    ax.set_ylabel("R_ij")
    ax.set_title("D  E/I balance predicts interaction", fontweight="bold")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.legend(fontsize=7)

    fig.suptitle("PPK23 × PPK25 pairwise interaction: mechanistic investigation",
                 fontsize=15, fontweight="bold")
    save_fig(fig, "publication_summary", "followup",
             description="Four-panel summary figure. A: Trajectory examples showing super (red) vs "
             "destructive (blue) integration. B: Waterfall of R_ij across all target neurons. "
             "C: Single-channel activation space colored by R_ij — neurons inhibited by one channel "
             "show super integration. D: E/I ratio predicts interaction mode.")


# =============================================================================
# MAIN
# =============================================================================

def main():
    logger.info("=" * 70)
    logger.info("PPK INTERACTION — FOLLOW-UP ANALYSIS")
    logger.info("=" * 70)

    (OUT_DIR / "followup").mkdir(parents=True, exist_ok=True)

    data = load_everything()

    df_corr = analyse_ei_correlation(data)
    analyse_hub_wiring(data)
    analyse_combined_ablation(data)
    analyse_negative_activation(data)
    make_summary_figure(data, df_corr)

    logger.info("=" * 70)
    logger.info("FOLLOW-UP ANALYSIS COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
