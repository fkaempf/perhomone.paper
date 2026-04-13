#!/usr/bin/env python3
"""
Pulse vs Sustained Propagation: Systematic Comparison of R_ij Values
=====================================================================

Compares R_ij = A(both) - A(ppk23) - A(ppk25) for ALL 39 target neurons
under two propagation modes:
  PULSE:     x(t+1) = f(W.T @ x(t)),           input injected only at t=0
  SUSTAINED: x(t+1) = f(W.T @ x(t) + s0),      input re-injected every step

Key questions:
  1. How correlated are pulse and sustained R_ij across targets?
  2. Which neurons flip sign between modes (mode-sensitive)?
  3. Are the flips robust across beta values (beta=2, 5, 10)?

Usage:
  cd combinatorial_signal_flow/ppk_interaction_investigation
  ../.venv/bin/python pulse_vs_sustained.py
"""

import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

# Add parent to path for signal_flow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signal_flow import NetworkLoader, ChannelEncoder, SignalPropagator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = Path(__file__).resolve().parent / "plots" / "pulse_vs_sustained"

N_STEPS = 3
NORMALIZATION = "post"

# Target groups to include (the "core" groups, not the _all expansions)
TARGET_GROUPS = ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]

# Beta values to test
BETAS = [2.0, 5.0, 10.0]

# Publication-quality defaults
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

GROUP_COLORS = {
    "aspf": "#E41A1C",
    "aspg": "#377EB8",
    "PPN1_downstream": "#FF7F00",
    "vAB3_downstream": "#4DAF4A",
}

GROUP_MARKERS = {
    "aspf": "o",
    "aspg": "s",
    "PPN1_downstream": "^",
    "vAB3_downstream": "D",
}


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


def compute_rij_all_targets(W, encoder, encoded_channels, targets, beta, n_steps):
    """
    Compute R_ij for ppk23 x ppk25 at all targets in both pulse and sustained mode.

    Returns a DataFrame with columns:
        target_group, target_type, R_ij_pulse, R_ij_sustained,
        A_ppk23_pulse, A_ppk25_pulse, A_both_pulse,
        A_ppk23_sustained, A_ppk25_sustained, A_both_sustained
    """
    s_ppk23 = encoded_channels["ppk23"]
    s_ppk25 = encoded_channels["ppk25"]
    s_both = s_ppk23 + s_ppk25

    act_params = {"beta": beta}

    # Pulse propagation
    prop_pulse = SignalPropagator(W, "sigmoid_rectified", act_params)
    x23_pulse = prop_pulse.propagate(s_ppk23, n_steps, sustained=False)
    x25_pulse = prop_pulse.propagate(s_ppk25, n_steps, sustained=False)
    xboth_pulse = prop_pulse.propagate(s_both, n_steps, sustained=False)

    # Sustained propagation
    prop_sust = SignalPropagator(W, "sigmoid_rectified", act_params)
    x23_sust = prop_sust.propagate(s_ppk23, n_steps, sustained=True)
    x25_sust = prop_sust.propagate(s_ppk25, n_steps, sustained=True)
    xboth_sust = prop_sust.propagate(s_both, n_steps, sustained=True)

    rows = []
    for tg in TARGET_GROUPS:
        if tg not in targets:
            continue
        for t in targets[tg]:
            if t not in encoder.type_to_idx:
                continue
            idx = encoder.type_to_idx[t]

            a23_p = x23_pulse[idx]
            a25_p = x25_pulse[idx]
            ab_p = xboth_pulse[idx]
            r_pulse = ab_p - a23_p - a25_p

            a23_s = x23_sust[idx]
            a25_s = x25_sust[idx]
            ab_s = xboth_sust[idx]
            r_sust = ab_s - a23_s - a25_s

            rows.append({
                "target_group": tg,
                "target_type": t,
                "A_ppk23_pulse": a23_p,
                "A_ppk25_pulse": a25_p,
                "A_both_pulse": ab_p,
                "R_ij_pulse": r_pulse,
                "A_ppk23_sustained": a23_s,
                "A_ppk25_sustained": a25_s,
                "A_both_sustained": ab_s,
                "R_ij_sustained": r_sust,
            })

    return pd.DataFrame(rows)


def plot_scatter(df, beta, ax=None, standalone=True):
    """
    Scatter plot: x = pulse R_ij, y = sustained R_ij.
    Identity line, highlights sign-flippers, labels all points.
    Returns the axis.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 10))
    else:
        fig = ax.get_figure()

    rp = df["R_ij_pulse"].values
    rs = df["R_ij_sustained"].values

    # Compute limits
    all_vals = np.concatenate([rp, rs])
    pad = max(abs(all_vals.max()), abs(all_vals.min())) * 0.15
    lim = max(abs(all_vals.max()), abs(all_vals.min())) + pad

    # Identity line
    ax.plot([-lim, lim], [-lim, lim], "k--", alpha=0.3, lw=1, label="identity")
    # Zero lines
    ax.axhline(0, color="gray", lw=0.5, ls=":")
    ax.axvline(0, color="gray", lw=0.5, ls=":")

    # Shade quadrants where sign flips occur (Q2 and Q4)
    ax.fill_between([-lim, 0], [0, 0], [lim, lim], alpha=0.04, color="red",
                    label="sign flip region")
    ax.fill_between([0, lim], [-lim, -lim], [0, 0], alpha=0.04, color="red")

    # Identify sign-flippers
    sign_flip = (rp * rs) < 0  # different sign

    # Plot non-flippers
    for tg in TARGET_GROUPS:
        mask = (df["target_group"] == tg).values
        mask_noflip = mask & ~sign_flip
        mask_flip = mask & sign_flip

        if mask_noflip.any():
            ax.scatter(rp[mask_noflip], rs[mask_noflip],
                       c=GROUP_COLORS[tg], marker=GROUP_MARKERS[tg],
                       s=60, edgecolor="black", lw=0.5, alpha=0.8,
                       label=tg, zorder=3)
        if mask_flip.any():
            ax.scatter(rp[mask_flip], rs[mask_flip],
                       c=GROUP_COLORS[tg], marker=GROUP_MARKERS[tg],
                       s=120, edgecolor="red", lw=2.0, alpha=1.0,
                       zorder=4)

    # Label all points
    for i, row in df.iterrows():
        fontweight = "bold" if sign_flip[i] else "normal"
        color = "red" if sign_flip[i] else "black"
        ax.annotate(
            row["target_type"],
            (row["R_ij_pulse"], row["R_ij_sustained"]),
            fontsize=6, fontweight=fontweight, color=color,
            ha="left", va="bottom",
            xytext=(3, 3), textcoords="offset points",
        )

    # Correlation
    r_pearson, p_pearson = pearsonr(rp, rs)
    r_spearman, p_spearman = spearmanr(rp, rs)
    n_flips = sign_flip.sum()
    n_total = len(df)

    corr_text = (
        f"Pearson r = {r_pearson:.3f} (p = {p_pearson:.2e})\n"
        f"Spearman rho = {r_spearman:.3f} (p = {p_spearman:.2e})\n"
        f"Sign flips: {n_flips}/{n_total}"
    )
    ax.text(0.03, 0.97, corr_text, transform=ax.transAxes,
            fontsize=8, va="top", ha="left",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9))

    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.set_xlabel("R_ij (PULSE mode)")
    ax.set_ylabel("R_ij (SUSTAINED mode)")
    ax.set_title(f"Pulse vs Sustained R_ij -- beta={beta:.0f}, {N_STEPS} steps")
    ax.legend(fontsize=7, loc="lower right")

    return fig, ax, r_pearson, r_spearman, n_flips


def main():
    logger.info("=" * 70)
    logger.info("PULSE vs SUSTAINED: Systematic R_ij comparison")
    logger.info("=" * 70)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load data ──
    loader = NetworkLoader(str(DATA_DIR))
    W_unsigned = loader.load_adjacency_matrix(NORMALIZATION)
    type_names = loader.load_type_names()
    channels = loader.load_channels()
    targets = loader.load_targets()
    W = loader.sign_matrix(W_unsigned, type_names)

    encoder = ChannelEncoder(type_names)
    encoded_channels = encoder.encode_all(channels)

    logger.info("Data loaded. Matrix: %d x %d", W.shape[0], W.shape[1])

    # ── Compute R_ij for all betas ──
    all_dfs = {}
    for beta in BETAS:
        logger.info("Computing R_ij for beta=%.1f ...", beta)
        df = compute_rij_all_targets(W, encoder, encoded_channels, targets, beta, N_STEPS)
        all_dfs[beta] = df
        df.to_csv(OUT_DIR / f"rij_pulse_vs_sustained_beta{beta:.0f}.csv", index=False)
        logger.info("  %d targets computed", len(df))

    # ══════════════════════════════════════════════════════════════════════
    # 1. MAIN SCATTER: beta=5 (reference)
    # ══════════════════════════════════════════════════════════════════════
    df5 = all_dfs[5.0]
    fig, ax = plt.subplots(figsize=(11, 11))
    _, _, r_pear_5, r_spear_5, nflip_5 = plot_scatter(df5, beta=5.0, ax=ax)
    save_fig(fig, "pulse_vs_sustained_beta5",
             description="Scatter plot of R_ij (ppk23 x ppk25) under pulse vs sustained propagation "
             f"for all {len(df5)} target neurons at beta=5. "
             f"Pearson r={r_pear_5:.3f}, Spearman rho={r_spear_5:.3f}. "
             f"{nflip_5} neurons flip sign between modes (highlighted with red edges).")

    # ══════════════════════════════════════════════════════════════════════
    # 2. MULTI-BETA PANEL: beta=2, 5, 10
    # ══════════════════════════════════════════════════════════════════════
    fig, axes = plt.subplots(1, 3, figsize=(30, 10))
    for ax, beta in zip(axes, BETAS):
        df_b = all_dfs[beta]
        plot_scatter(df_b, beta=beta, ax=ax, standalone=False)

    fig.suptitle("Pulse vs Sustained R_ij across beta values (sigmoid gain parameter)",
                 fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    save_fig(fig, "pulse_vs_sustained_multi_beta",
             description="Three-panel scatter comparing pulse vs sustained R_ij at beta=2, 5, 10. "
             "Tests whether sign-flipping neurons are consistent across nonlinearity strengths.")

    # ══════════════════════════════════════════════════════════════════════
    # 3. SIGN-FLIP TABLE (all betas)
    # ══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("SIGN-FLIPPING NEURONS: R_ij changes sign between pulse and sustained modes")
    print("=" * 90)

    flip_summary_rows = []
    for beta in BETAS:
        df_b = all_dfs[beta]
        rp = df_b["R_ij_pulse"].values
        rs = df_b["R_ij_sustained"].values
        flips = (rp * rs) < 0

        r_pear, _ = pearsonr(rp, rs)
        r_spear, _ = spearmanr(rp, rs)

        print(f"\n--- beta = {beta:.0f}  |  Pearson r = {r_pear:.3f}  |  "
              f"Spearman rho = {r_spear:.3f}  |  {flips.sum()}/{len(df_b)} flips ---")
        print(f"{'Neuron':<20s} {'Group':<22s} {'R_pulse':>10s} {'R_sust':>10s} "
              f"{'Sign_P':>8s} {'Sign_S':>8s} {'|Delta|':>10s}")
        print("-" * 90)

        for i, row in df_b.iterrows():
            if flips[i]:
                sign_p = "+" if row["R_ij_pulse"] > 0 else "-"
                sign_s = "+" if row["R_ij_sustained"] > 0 else "-"
                delta = abs(row["R_ij_sustained"] - row["R_ij_pulse"])
                print(f"{row['target_type']:<20s} {row['target_group']:<22s} "
                      f"{row['R_ij_pulse']:>10.4f} {row['R_ij_sustained']:>10.4f} "
                      f"{sign_p:>8s} {sign_s:>8s} {delta:>10.4f}")
                flip_summary_rows.append({
                    "beta": beta,
                    "target_type": row["target_type"],
                    "target_group": row["target_group"],
                    "R_ij_pulse": row["R_ij_pulse"],
                    "R_ij_sustained": row["R_ij_sustained"],
                })

    # ══════════════════════════════════════════════════════════════════════
    # 4. IDENTIFY ROBUST vs MODE-SENSITIVE NEURONS
    # ══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("COMPREHENSIVE TABLE: All targets at beta=5 (reference)")
    print("=" * 90)

    df5_sorted = df5.sort_values(["target_group", "R_ij_pulse"])
    rp5 = df5["R_ij_pulse"].values
    rs5 = df5["R_ij_sustained"].values
    flips5 = (rp5 * rs5) < 0

    print(f"\n{'Neuron':<20s} {'Group':<22s} {'R_pulse':>10s} {'R_sust':>10s} "
          f"{'Agree?':>8s} {'Category':>12s}")
    print("-" * 90)

    for _, row in df5_sorted.iterrows():
        rp_val = row["R_ij_pulse"]
        rs_val = row["R_ij_sustained"]
        agree = "YES" if (rp_val * rs_val) >= 0 else "FLIP"

        if rp_val > 0 and rs_val > 0:
            cat = "synergy"
        elif rp_val < 0 and rs_val < 0:
            cat = "opposition"
        elif abs(rp_val) < 0.01 and abs(rs_val) < 0.01:
            cat = "~zero"
        else:
            cat = "MODE-DEP"

        print(f"{row['target_type']:<20s} {row['target_group']:<22s} "
              f"{rp_val:>10.4f} {rs_val:>10.4f} "
              f"{agree:>8s} {cat:>12s}")

    # ══════════════════════════════════════════════════════════════════════
    # 5. BETA-DEPENDENCE OF SIGN FLIPS
    # ══════════════════════════════════════════════════════════════════════
    # For each neuron, check if it flips at ALL betas or only some
    if flip_summary_rows:
        df_flips = pd.DataFrame(flip_summary_rows)
        flip_counts = df_flips.groupby("target_type")["beta"].count().reset_index()
        flip_counts.columns = ["target_type", "n_betas_flipping"]

        print("\n" + "=" * 90)
        print("BETA-DEPENDENCE OF SIGN FLIPS")
        print("=" * 90)
        print(f"\n{'Neuron':<20s} {'Flips at N betas':>20s} {'Beta values':>30s}")
        print("-" * 70)
        for _, row in flip_counts.iterrows():
            neuron = row["target_type"]
            n = int(row["n_betas_flipping"])
            betas_str = ", ".join(
                [f"{b:.0f}" for b in sorted(
                    df_flips[df_flips["target_type"] == neuron]["beta"].values
                )]
            )
            robustness = "ROBUST FLIP" if n == len(BETAS) else "BETA-DEPENDENT"
            print(f"{neuron:<20s} {n:>20d}   betas: {betas_str:<20s}  ({robustness})")

    # ══════════════════════════════════════════════════════════════════════
    # 6. DIVERGENCE BAR CHART: |R_sustained - R_pulse| for all neurons
    # ══════════════════════════════════════════════════════════════════════
    df5_div = df5.copy()
    df5_div["delta_R"] = df5_div["R_ij_sustained"] - df5_div["R_ij_pulse"]
    df5_div = df5_div.sort_values("delta_R")

    fig, ax = plt.subplots(figsize=(10, max(8, len(df5_div) * 0.28)))

    rp_vals = df5_div["R_ij_pulse"].values
    rs_vals = df5_div["R_ij_sustained"].values
    flips_sorted = (rp_vals * rs_vals) < 0

    colors = []
    for i, row in df5_div.iterrows():
        if flips_sorted[list(df5_div.index).index(i)]:
            colors.append("red")
        else:
            colors.append(GROUP_COLORS.get(row["target_group"], "gray"))

    y_pos = np.arange(len(df5_div))
    ax.barh(y_pos, df5_div["delta_R"], color=colors, edgecolor="black", lw=0.4)
    ax.set_yticks(y_pos)
    labels = [f"{row['target_type']} ({row['target_group']})" for _, row in df5_div.iterrows()]
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("R_ij(sustained) - R_ij(pulse)")
    ax.set_title("Divergence between propagation modes (beta=5)\nRed = sign-flipping neurons")
    ax.axvline(0, color="black", lw=0.8)
    fig.tight_layout()
    save_fig(fig, "divergence_bar_beta5",
             description="Bar chart showing R_ij(sustained) - R_ij(pulse) for each neuron at beta=5. "
             "Red bars indicate neurons where R_ij flips sign between modes.")

    # ══════════════════════════════════════════════════════════════════════
    # 7. HEATMAP: R_ij across betas for both modes
    # ══════════════════════════════════════════════════════════════════════
    # Build matrix: rows = neurons, columns = (beta, mode) pairs
    col_labels = []
    for beta in BETAS:
        col_labels.append(f"Pulse b={beta:.0f}")
        col_labels.append(f"Sust b={beta:.0f}")

    # Use consistent neuron order (sorted by group, then by R_ij_pulse at beta=5)
    df5_order = df5.sort_values(["target_group", "R_ij_pulse"])
    neuron_order = df5_order["target_type"].tolist()
    group_order = df5_order["target_group"].tolist()

    mat = np.zeros((len(neuron_order), len(col_labels)))
    for j, beta in enumerate(BETAS):
        df_b = all_dfs[beta]
        for i, neuron in enumerate(neuron_order):
            row = df_b[df_b["target_type"] == neuron]
            if len(row) > 0:
                mat[i, 2*j] = row.iloc[0]["R_ij_pulse"]
                mat[i, 2*j+1] = row.iloc[0]["R_ij_sustained"]

    vmax = max(abs(mat.min()), abs(mat.max())) or 1e-6
    fig, ax = plt.subplots(figsize=(12, max(8, len(neuron_order) * 0.3)))
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")

    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(neuron_order)))

    # Color-code y labels by group
    ylabels = []
    for neuron, grp in zip(neuron_order, group_order):
        ylabels.append(neuron)
    ax.set_yticklabels(ylabels, fontsize=8)
    for i, grp in enumerate(group_order):
        ax.get_yticklabels()[i].set_color(GROUP_COLORS.get(grp, "black"))

    # Add vertical lines separating beta blocks
    for j in range(1, len(BETAS)):
        ax.axvline(2*j - 0.5, color="black", lw=1.5)

    # Annotate cells
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            val = mat[i, j]
            textcolor = "white" if abs(val) > vmax * 0.6 else "black"
            ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                    fontsize=5.5, color=textcolor)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("R_ij (ppk23 x ppk25)")
    ax.set_title("R_ij across propagation modes and beta values", fontsize=13, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "rij_heatmap_all_betas",
             description="Heatmap of R_ij for all targets across pulse/sustained modes "
             "and beta=2,5,10. Allows visual comparison of sign consistency.")

    # ══════════════════════════════════════════════════════════════════════
    # 8. SUMMARY STATISTICS
    # ══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("SUMMARY STATISTICS")
    print("=" * 90)

    for beta in BETAS:
        df_b = all_dfs[beta]
        rp = df_b["R_ij_pulse"].values
        rs = df_b["R_ij_sustained"].values
        flips = (rp * rs) < 0

        r_pear, p_pear = pearsonr(rp, rs)
        r_spear, p_spear = spearmanr(rp, rs)

        # Count robust categories
        n_both_neg = ((rp < 0) & (rs < 0)).sum()
        n_both_pos = ((rp > 0) & (rs > 0)).sum()
        n_flip_neg_to_pos = ((rp < 0) & (rs > 0)).sum()
        n_flip_pos_to_neg = ((rp > 0) & (rs < 0)).sum()
        n_both_zero = ((np.abs(rp) < 1e-4) | (np.abs(rs) < 1e-4)).sum()

        print(f"\nbeta = {beta:.0f}:")
        print(f"  Pearson r  = {r_pear:.4f}  (p = {p_pear:.2e})")
        print(f"  Spearman   = {r_spear:.4f}  (p = {p_spear:.2e})")
        print(f"  Both negative (robust opposition):  {n_both_neg}")
        print(f"  Both positive (robust synergy):     {n_both_pos}")
        print(f"  Flip neg->pos (pulse opp, sust syn): {n_flip_neg_to_pos}")
        print(f"  Flip pos->neg (pulse syn, sust opp): {n_flip_pos_to_neg}")
        print(f"  Near-zero in either mode:            {n_both_zero}")

    # ══════════════════════════════════════════════════════════════════════
    # DONE
    # ══════════════════════════════════════════════════════════════════════
    logger.info("=" * 70)
    logger.info("ANALYSIS COMPLETE")
    logger.info("All results saved to: %s", OUT_DIR)
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
