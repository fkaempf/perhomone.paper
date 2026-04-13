#!/usr/bin/env python3
"""
Publication-quality 4-panel summary figure for ppk23 x ppk25 interaction analysis.

Narrative flow:
  Panel A: The phenomenon — R_ij across all targets (coactivation result)
  Panel B: The linear prediction — drive convergence scatter reveals circuit motifs
  Panel C: The multi-level story — R_ij at step 2 vs step 3 (super neurons flip)
  Panel D: The resolution — upstream saturation explains why push-pull fails

Usage:
    cd ppk_interaction_investigation
    ../.venv/bin/python figure_summary.py
"""

import sys
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signal_flow import NetworkLoader, ChannelEncoder, SignalPropagator

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = Path(__file__).resolve().parent / "plots" / "summary_figure"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

TARGET_GROUPS = ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]
GROUP_SHORT = {"aspf": "aSP-f", "aspg": "aSP-g",
               "PPN1_downstream": "PPN1 dwn", "vAB3_downstream": "vAB3 dwn"}

MECH_COLORS = {
    "ceiling saturation": "#2166AC",       # blue — both exc, destructive
    "floor saturation": "#F4A582",         # orange — both inh, super
    "push-pull": "#B2182B",                # red — opposite sign, super
    "upstream saturation": "#7B68AE",      # muted purple — opposite sign but intermediaries co-saturated
    "weak/indeterminate": "#BDBDBD",       # gray — drives too small to classify
    "other": "#999999",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Data
# ═══════════════════════════════════════════════════════════════════════════════

def load_and_compute():
    """Load network, compute R_ij, drives, step-wise trajectories, and intermediary decomposition."""
    loader = NetworkLoader(str(DATA_DIR))
    W_unsigned = loader.load_adjacency_matrix("post")
    type_names = loader.load_type_names()
    channels = loader.load_channels()
    nt_map = loader.load_neurotransmitter_mapping()
    W = loader.sign_matrix(W_unsigned, type_names)

    encoder = ChannelEncoder(type_names)
    enc = encoder.encode_all(channels)
    type_to_idx = encoder.type_to_idx
    idx_to_type = dict(zip(type_names["index"], type_names["type"]))
    type_to_nt = dict(zip(nt_map["type"], nt_map["consensus_nt"]))
    type_to_inhib = dict(zip(nt_map["type"], nt_map["is_inhibitory"]))

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]

    # Linear propagation (for drive decomposition)
    Wt = W.T.tocsc()
    x23 = [s_ppk23.copy()]
    x25 = [s_ppk25.copy()]
    x = s_ppk23.copy()
    for _ in range(4):
        x = Wt.dot(x)
        x23.append(x.copy())
    x = s_ppk25.copy()
    for _ in range(4):
        x = Wt.dot(x)
        x25.append(x.copy())

    # Step-by-step sigmoid propagation (for Panel C)
    prop = SignalPropagator(W, "sigmoid_rectified", {"beta": 5.0})
    step_data = {}
    for n_steps in [2, 3]:
        a23_s = prop.propagate(s_ppk23, n_steps, sustained=True)
        a25_s = prop.propagate(s_ppk25, n_steps, sustained=True)
        ab_s = prop.propagate(s_ppk23 + s_ppk25, n_steps, sustained=True)
        step_data[n_steps] = (a23_s, a25_s, ab_s)

    # Final (3-step) activations
    a23, a25, ab = step_data[3]

    targets = loader.load_targets()
    W_csc = W.tocsc()

    # ── Per-target data ──
    target_rows = []
    inter_influence = {}

    for group in TARGET_GROUPS:
        if group not in targets:
            continue
        for t in targets[group]:
            if t not in type_to_idx:
                continue
            t_idx = type_to_idx[t]
            r_ij = ab[t_idx] - a23[t_idx] - a25[t_idx]

            # Step-wise R_ij
            a23_s2, a25_s2, ab_s2 = step_data[2]
            r_ij_s2 = ab_s2[t_idx] - a23_s2[t_idx] - a25_s2[t_idx]

            col = W_csc[:, t_idx].toarray().ravel()
            pre_indices = np.nonzero(col)[0]
            net_ppk23 = sum(col[pi] * x23[2][pi] for pi in pre_indices)
            net_ppk25 = sum(col[pi] * x25[2][pi] for pi in pre_indices)

            # Intermediary decomposition: what fraction of interaction comes from
            # presynaptic neurons that are themselves destructive?
            total_destr_contrib = 0.0
            total_super_contrib = 0.0
            for pi in pre_indices:
                w = col[pi]
                # Intermediary's own R_ij at step 2
                pre_rij = ab_s2[pi] - a23_s2[pi] - a25_s2[pi]
                # Intermediary's delta (nonlinear activation diff)
                delta_pre = ab_s2[pi] - a23_s2[pi] - a25_s2[pi]
                # How this intermediary contributes to target R_ij:
                # via weight * (activation_both - activation_23 - activation_25)
                delivery = w * delta_pre
                if delta_pre < 0:
                    total_destr_contrib += abs(delivery)
                else:
                    total_super_contrib += abs(delivery)

            total_contrib = total_destr_contrib + total_super_contrib
            frac_destr = total_destr_contrib / total_contrib if total_contrib > 0 else 0.5

            target_rows.append({
                "target": t, "group": group, "t_idx": t_idx,
                "R_ij": r_ij,
                "R_ij_step2": r_ij_s2,
                "net_ppk23_drive": net_ppk23,
                "net_ppk25_drive": net_ppk25,
                "A_ppk23": a23[t_idx], "A_ppk25": a25[t_idx], "A_both": ab[t_idx],
                "frac_destr_intermediaries": frac_destr,
            })

            for pi in pre_indices:
                w = col[pi]
                eff23 = abs(w * x23[2][pi])
                eff25 = abs(w * x25[2][pi])
                if eff23 + eff25 < 1e-10:
                    continue
                if pi not in inter_influence:
                    inter_influence[pi] = 0.0
                inter_influence[pi] += eff23 + eff25

    df_targets = pd.DataFrame(target_rows)
    df_targets["mechanism"] = df_targets.apply(_classify_mechanism, axis=1)

    # ── Key intermediaries ──
    ranked = sorted(inter_influence.items(), key=lambda x: x[1], reverse=True)
    inter_rows = []
    for pi, influence in ranked[:20]:
        ptype = idx_to_type.get(pi, f"idx_{pi}")
        is_inh = type_to_inhib.get(ptype, False)
        nt = type_to_nt.get(ptype, "?")
        d23 = x23[2][pi]
        d25 = x25[2][pi]
        inter_rows.append({
            "neuron": ptype, "idx": pi,
            "ppk23_drive": d23, "ppk25_drive": d25,
            "is_inhibitory": is_inh, "nt": nt,
            "total_influence": influence,
            "sign_relationship": "opposite" if (d23 * d25 < 0) else "same",
        })

    df_inter = pd.DataFrame(inter_rows)
    logger.info("Computed data for %d targets, %d key intermediaries",
                len(df_targets), len(df_inter))
    return df_targets, df_inter


def _classify_mechanism(row):
    d23 = row["net_ppk23_drive"]
    d25 = row["net_ppk25_drive"]
    r = row["R_ij"]

    drive_mag = max(abs(d23), abs(d25))
    if drive_mag < 0.002:
        return "weak/indeterminate"

    both_pos = d23 > 0 and d25 > 0
    both_neg = d23 < 0 and d25 < 0
    mixed = not both_pos and not both_neg
    if both_pos and r < 0:
        return "ceiling saturation"
    elif both_neg and r > 0:
        return "floor saturation"
    elif mixed and r > 0:
        return "push-pull"
    elif mixed and r < 0:
        return "upstream saturation"
    else:
        return "other"


# ═══════════════════════════════════════════════════════════════════════════════
# Panel A: R_ij dot plot (the phenomenon)
# ═══════════════════════════════════════════════════════════════════════════════

def draw_panel_A(ax, df):
    """Lollipop chart of R_ij per target, grouped by target class."""
    group_order = TARGET_GROUPS
    sorted_rows = []
    group_boundaries = []
    y_pos = 0

    for group in group_order:
        sub = df[df["group"] == group].sort_values("R_ij", ascending=True)
        if sub.empty:
            continue
        group_boundaries.append((y_pos, y_pos + len(sub) - 1, group))
        for _, row in sub.iterrows():
            sorted_rows.append((y_pos, row))
            y_pos += 1
        y_pos += 1

    for y, row in sorted_rows:
        mech = row["mechanism"]
        color = MECH_COLORS.get(mech, "#999999")
        ax.plot([0, row["R_ij"]], [y, y], color=color, lw=1.2, solid_capstyle="round")
        ax.plot(row["R_ij"], y, "o", color=color, markersize=5,
                markeredgecolor="0.2", markeredgewidth=0.4, zorder=3)

    ax.set_yticks([y for y, _ in sorted_rows])
    ax.set_yticklabels([row["target"] for _, row in sorted_rows], fontsize=5.5)

    ax.autoscale_view()

    xmax = ax.get_xlim()[1]
    x_label = xmax + (xmax - ax.get_xlim()[0]) * 0.03
    for start_y, end_y, group in group_boundaries:
        mid_y = (start_y + end_y) / 2
        ax.text(x_label, mid_y, GROUP_SHORT[group],
                fontsize=6.5, fontweight="bold", va="center", ha="left",
                color="0.3", clip_on=False)
        if start_y > 0:
            ax.axhline(start_y - 0.5, color="0.8", lw=0.5)

    ax.axvline(0, color="0.4", lw=0.7, ls="--", zorder=1)
    ax.invert_yaxis()

    handles = [
        mpatches.Patch(color=MECH_COLORS["ceiling saturation"], label="Ceiling sat."),
        mpatches.Patch(color=MECH_COLORS["floor saturation"], label="Floor sat."),
        mpatches.Patch(color=MECH_COLORS["push-pull"], label="Push-pull"),
        mpatches.Patch(color=MECH_COLORS["upstream saturation"], label="Upstream sat."),
        mpatches.Patch(color=MECH_COLORS["weak/indeterminate"], label="Weak/indet."),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=5.5,
              framealpha=0.85, edgecolor="none")

    ax.set_xlabel("$R_{ij}$ = A(both) $-$ A(ppk23) $-$ A(ppk25)")
    ax.set_title("A  Interaction upon coactivation", fontweight="bold", loc="left")


# ═══════════════════════════════════════════════════════════════════════════════
# Panel B: Drive scatter (the linear prediction)
# ═══════════════════════════════════════════════════════════════════════════════

def draw_panel_B(ax, df):
    """Scatter: net ppk23 vs ppk25 drive, colored by R_ij, annotated by mechanism."""
    vmin = np.percentile(df["R_ij"], 10)
    vmax = np.percentile(df["R_ij"], 90)
    vmin = min(vmin, -0.05)
    vmax = max(vmax, 0.05)
    norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
    cmap = plt.cm.RdBu_r

    group_markers = {"aspf": "o", "aspg": "s",
                     "PPN1_downstream": "^", "vAB3_downstream": "D"}
    group_labels = {"aspf": "aSP-f", "aspg": "aSP-g",
                    "PPN1_downstream": "PPN1 dwn", "vAB3_downstream": "vAB3 dwn"}

    ax.axhline(0, color="0.5", lw=0.7, ls="--", zorder=1)
    ax.axvline(0, color="0.5", lw=0.7, ls="--", zorder=1)

    for group, marker in group_markers.items():
        sub = df[df["group"] == group]
        if sub.empty:
            continue
        ax.scatter(sub["net_ppk23_drive"], sub["net_ppk25_drive"],
                   c=sub["R_ij"], cmap=cmap, norm=norm,
                   marker=marker, s=55, edgecolor="0.2", linewidth=0.5,
                   zorder=3, label=group_labels[group])

    from adjustText import adjust_text
    texts = []
    for _, row in df.iterrows():
        texts.append(ax.text(row["net_ppk23_drive"], row["net_ppk25_drive"],
                             row["target"], fontsize=4, ha="center", va="center",
                             alpha=0.8, zorder=5))
    try:
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle="-", color="0.5", lw=0.3),
                    force_points=(0.5, 0.5), expand=(1.3, 1.3))
    except Exception:
        for t in texts:
            t.set_position((t.get_position()[0], t.get_position()[1] + 0.0005))

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.82, pad=0.02)
    cbar.set_label("$R_{ij}$", fontsize=9)
    cbar.ax.tick_params(labelsize=7)

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    px = (xlim[1] - xlim[0]) * 0.04
    py = (ylim[1] - ylim[0]) * 0.04

    ax.text(xlim[1] - px, ylim[1] - py,
            "both excitatory\nceiling sat. $\\rightarrow$ DESTR.",
            ha="right", va="top", fontsize=6, fontstyle="italic",
            color="#2166AC", alpha=0.9,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.7))
    ax.text(xlim[0] + px, ylim[0] + py,
            "both inhibitory\nfloor sat. $\\rightarrow$ SUPER",
            ha="left", va="bottom", fontsize=6, fontstyle="italic",
            color="#B2182B", alpha=0.9,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.7))
    ax.text(xlim[0] + px, ylim[1] - py,
            "opposite drives\n$\\rightarrow$ SUPER or destr.?",
            ha="left", va="top", fontsize=6, fontstyle="italic",
            color="#6A3D9A", alpha=0.9,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.7))
    ax.text(xlim[1] - px, ylim[0] + py,
            "opposite drives\n$\\rightarrow$ SUPER or destr.?",
            ha="right", va="bottom", fontsize=6, fontstyle="italic",
            color="#6A3D9A", alpha=0.9,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.7))

    legend_handles = [Line2D([0], [0], marker=m, color="none", markerfacecolor="0.5",
                             markeredgecolor="0.2", markersize=5, label=group_labels[g])
                      for g, m in group_markers.items()]
    ax.legend(handles=legend_handles, loc="upper left", fontsize=5.5,
              framealpha=0.85, edgecolor="none", handletextpad=0.3)

    ax.set_xlabel("Net ppk23 drive to target")
    ax.set_ylabel("Net ppk25 drive to target")
    ax.set_title("B  Linear drive predicts some, not all", fontweight="bold", loc="left")


# ═══════════════════════════════════════════════════════════════════════════════
# Panel C: Step-by-step R_ij trajectory (the multi-level story)
# ═══════════════════════════════════════════════════════════════════════════════

def draw_panel_C(ax, df):
    """Slope chart: R_ij at step 2 → step 3, showing super neurons flip positive."""
    # Color by mechanism
    for _, row in df.iterrows():
        mech = row["mechanism"]
        color = MECH_COLORS.get(mech, "#BDBDBD")
        alpha = 0.25  # default: faint
        lw = 0.8

        # Highlight push-pull and upstream saturation
        if mech in ("push-pull", "upstream saturation"):
            alpha = 0.85
            lw = 1.8
        elif mech == "ceiling saturation":
            alpha = 0.15
            lw = 0.6

        ax.plot([2, 3], [row["R_ij_step2"], row["R_ij"]],
                color=color, alpha=alpha, lw=lw, solid_capstyle="round", zorder=2)
        ax.plot(3, row["R_ij"], "o", color=color, alpha=min(alpha + 0.1, 1.0),
                markersize=4, markeredgecolor="0.3", markeredgewidth=0.3, zorder=3)

    # Label the highlighted neurons
    labeled = df[df["mechanism"].isin(["push-pull", "upstream saturation"])].copy()
    for _, row in labeled.iterrows():
        mech = row["mechanism"]
        color = MECH_COLORS.get(mech, "#999")
        # Label at step 3
        offset_x = 0.08
        ha = "left"
        ax.annotate(row["target"], xy=(3, row["R_ij"]),
                    xytext=(3 + offset_x, row["R_ij"]),
                    fontsize=5.5, color=color, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color=color, lw=0.4),
                    va="center", ha=ha, zorder=4)

    ax.axhline(0, color="0.3", lw=1.0, ls="-", zorder=1)
    ax.set_xticks([2, 3])
    ax.set_xticklabels(["Step 2\n(intermediaries)", "Step 3\n(targets)"], fontsize=9)
    ax.set_ylabel("$R_{ij}$")
    ax.set_xlim(1.7, 3.9)

    # Annotations explaining the key insight
    # Arrow region: "all destructive here"
    y_mid_s2 = df["R_ij_step2"].median()
    ax.annotate("Nearly all $R_{ij} < 0$\nat intermediary level",
                xy=(2, y_mid_s2), xytext=(1.78, y_mid_s2 * 0.6),
                fontsize=7, color="0.3", fontstyle="italic",
                ha="center", va="center",
                arrowprops=dict(arrowstyle="->", color="0.5", lw=0.8))

    # "super neurons flip" annotation
    super_at_3 = df[df["mechanism"] == "push-pull"]["R_ij"]
    if not super_at_3.empty:
        y_super = super_at_3.mean()
        ax.annotate("Push-pull\nneurons flip\n$R_{ij} > 0$",
                    xy=(3, y_super), xytext=(3.45, y_super + 0.05),
                    fontsize=7, color=MECH_COLORS["push-pull"], fontweight="bold",
                    ha="center", va="bottom",
                    arrowprops=dict(arrowstyle="->", color=MECH_COLORS["push-pull"], lw=1.0))

    # "upstream sat stays negative"
    upsat_at_3 = df[df["mechanism"] == "upstream saturation"]["R_ij"]
    if not upsat_at_3.empty:
        y_upsat = upsat_at_3.median()
        ax.annotate("Upstream sat.\nstays $R_{ij} < 0$",
                    xy=(3, y_upsat), xytext=(3.45, y_upsat - 0.05),
                    fontsize=7, color=MECH_COLORS["upstream saturation"], fontweight="bold",
                    ha="center", va="top",
                    arrowprops=dict(arrowstyle="->", color=MECH_COLORS["upstream saturation"], lw=1.0))

    handles = [
        Line2D([0], [0], color=MECH_COLORS["push-pull"], lw=2, label="Push-pull (SUPER)"),
        Line2D([0], [0], color=MECH_COLORS["upstream saturation"], lw=2, label="Upstream sat. (DESTR.)"),
        Line2D([0], [0], color=MECH_COLORS["ceiling saturation"], lw=1, alpha=0.3, label="Ceiling sat."),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=6,
              framealpha=0.85, edgecolor="none")

    ax.set_title("C  Multi-level: interaction evolves across layers", fontweight="bold", loc="left")


# ═══════════════════════════════════════════════════════════════════════════════
# Panel D: Upstream saturation (the resolution)
# ═══════════════════════════════════════════════════════════════════════════════

def draw_panel_D(ax, df):
    """Horizontal bar chart: % signal from destructive intermediaries, for push-pull
    and upstream-saturation targets. Shows what determines whether push-pull works."""
    # Select only the neurons with opposite-sign drives (push-pull topology)
    df_pp = df[df["mechanism"].isin(["push-pull", "upstream saturation"])].copy()
    df_pp = df_pp.sort_values("R_ij", ascending=True).reset_index(drop=True)

    if df_pp.empty:
        ax.text(0.5, 0.5, "No push-pull topology neurons", transform=ax.transAxes,
                ha="center", va="center")
        return

    n = len(df_pp)
    y = np.arange(n)

    # Bar: fraction from destructive intermediaries
    colors = [MECH_COLORS.get(m, "#999") for m in df_pp["mechanism"]]
    bars = ax.barh(y, df_pp["frac_destr_intermediaries"] * 100, height=0.6,
                   color=colors, edgecolor="0.3", linewidth=0.4, zorder=2)

    # 50% reference line
    ax.axvline(50, color="0.4", lw=0.8, ls=":", zorder=1)
    ax.text(50, n + 0.3, "50%", ha="center", va="bottom", fontsize=7, color="0.4")

    # Y-axis labels: neuron name + R_ij
    labels = [f"{row['target']}  ($R$={row['R_ij']:+.2f})" for _, row in df_pp.iterrows()]
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7)

    # Color y-tick labels by mechanism
    for i, (_, row) in enumerate(df_pp.iterrows()):
        color = MECH_COLORS.get(row["mechanism"], "#999")
        ax.get_yticklabels()[i].set_color(color)
        ax.get_yticklabels()[i].set_fontweight("bold")

    # Value labels on bars
    for i, (_, row) in enumerate(df_pp.iterrows()):
        val = row["frac_destr_intermediaries"] * 100
        ax.text(val + 1.5, y[i], f"{val:.0f}%", va="center", ha="left",
                fontsize=6.5, fontweight="bold", color="0.3")

    ax.set_xlabel("% of interaction signal from destructive intermediaries")
    ax.set_xlim(0, 105)

    # Explanatory text box
    ax.text(0.98, 0.05,
            "Push-pull topology alone\n"
            "does not guarantee SUPER.\n"
            "If intermediaries are already\n"
            "co-saturated ($R_{pre} < 0$),\n"
            "the target inherits their\n"
            "destructive interaction.",
            transform=ax.transAxes, fontsize=7,
            ha="right", va="bottom",
            bbox=dict(boxstyle="round,pad=0.4", fc="#F5F0FF", ec="#7B68AE",
                      lw=0.8, alpha=0.9))

    handles = [
        mpatches.Patch(color=MECH_COLORS["push-pull"], label="Push-pull → SUPER"),
        mpatches.Patch(color=MECH_COLORS["upstream saturation"], label="Upstream sat. → DESTR."),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=6.5,
              framealpha=0.85, edgecolor="none")

    ax.set_title("D  Why push-pull sometimes fails", fontweight="bold", loc="left")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    (OUT_DIR / "png").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "pdf").mkdir(parents=True, exist_ok=True)

    logger.info("Loading data and computing...")
    df_targets, df_inter = load_and_compute()

    logger.info("Mechanism counts:\n%s", df_targets["mechanism"].value_counts().to_string())

    # ── Build 2x2 figure ──
    fig = plt.figure(figsize=(17, 14))
    gs = fig.add_gridspec(2, 2,
                          width_ratios=[0.85, 1.0],
                          height_ratios=[1.0, 0.7],
                          left=0.07, right=0.96, top=0.93, bottom=0.05,
                          wspace=0.35, hspace=0.35)

    # Panel A (top-left)
    ax_A = fig.add_subplot(gs[0, 0])
    draw_panel_A(ax_A, df_targets)

    # Panel B (top-right)
    ax_B = fig.add_subplot(gs[0, 1])
    draw_panel_B(ax_B, df_targets)

    # Panel C (bottom-left)
    ax_C = fig.add_subplot(gs[1, 0])
    draw_panel_C(ax_C, df_targets)

    # Panel D (bottom-right)
    ax_D = fig.add_subplot(gs[1, 1])
    draw_panel_D(ax_D, df_targets)

    fig.suptitle(
        "ppk23 $\\times$ ppk25 interaction: multi-level saturation determines integration mode",
        fontsize=14, fontweight="bold", y=0.97,
    )

    fig.savefig(OUT_DIR / "png" / "summary_4panel.png", dpi=300)
    fig.savefig(OUT_DIR / "pdf" / "summary_4panel.pdf")
    plt.close(fig)
    logger.info("Saved to %s", OUT_DIR)


if __name__ == "__main__":
    main()
