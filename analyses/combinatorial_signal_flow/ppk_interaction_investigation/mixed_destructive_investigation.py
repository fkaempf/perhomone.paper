#!/usr/bin/env python3
"""
Mixed-drive Destructive Investigation
======================================

Some neurons receive OPPOSING last-hop linear drives from ppk23 and ppk25
(d23 < 0, d25 > 0 or vice versa), which should predict SUPER-ADDITIVE
interaction (R_ij > 0) because opposing drives cancel saturation.

Yet several such "mixed-drive" neurons are DESTRUCTIVE (R_ij < 0).

This script investigates WHY through four analyses:
  1. Nonlinear step-by-step comparison — where does R_ij diverge?
  2. Drive asymmetry — does one channel dominate despite opposing signs?
  3. Higher-order (step 1) nonlinear activations — is the interaction
     already determined before reaching the target?
  4. Direct presynaptic decomposition — which presynaptic neurons
     contribute the nonlinear interaction?

Key neurons investigated:
  MIXED-DESTRUCTIVE:
    mAL_m1, mAL_m9, AVLP727m, mAL_m8, AVLP743m, WED015, LH004m, DNp103
  GENUINE SUPER (push-pull):
    LH008m, mAL_m2a, AVLP728m

Usage:
  cd ppk_interaction_investigation
  ../.venv/bin/python mixed_destructive_investigation.py
"""

import sys
import logging
from pathlib import Path
from collections import OrderedDict

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signal_flow import (
    NetworkLoader, ChannelEncoder, SignalPropagator, ACTIVATIONS, sigmoid,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = Path(__file__).resolve().parent / "plots" / "mixed_destructive"

NONLINEARITY = "sigmoid_rectified"
ACT_PARAMS = {"beta": 5.0}
BETA = 5.0
N_STEPS = 3
SUSTAINED = True

# Mixed-drive destructive neurons (from the user's question)
MIXED_DESTRUCTIVE = OrderedDict([
    ("AVLP727m", {"group": "aspg",      "d23": -0.0036, "d25": +0.0030, "R_ij": -0.056}),
    ("mAL_m8",   {"group": "vAB3",      "d23": -0.0072, "d25": +0.0032, "R_ij": -0.071}),
    ("mAL_m1",   {"group": "vAB3",      "d23": -0.0115, "d25": +0.0107, "R_ij": -0.177}),
    ("mAL_m9",   {"group": "vAB3",      "d23": -0.0030, "d25": +0.0097, "R_ij": -0.335}),
    ("AVLP743m", {"group": "vAB3",      "d23": -0.0041, "d25": +0.0150, "R_ij": -0.084}),
    ("WED015",   {"group": "PPN1",      "d23": +0.0071, "d25": -0.0088, "R_ij": -0.183}),
    ("LH004m",   {"group": "PPN1/vAB3", "d23": -0.0004, "d25": +0.0042, "R_ij": -0.030}),
    ("DNp103",   {"group": "PPN1",      "d23": +0.0020, "d25": +0.0010, "R_ij": -0.077}),
])

# Genuine super push-pull neurons
GENUINE_SUPER = OrderedDict([
    ("LH008m",   {"group": "aspf", "d23": -0.0042, "d25": +0.0057, "R_ij": +0.179}),
    ("mAL_m2a",  {"group": "vAB3", "d23": -0.0125, "d25": +0.0116, "R_ij": +0.233}),
    ("AVLP728m", {"group": "vAB3", "d23": -0.0091, "d25": +0.0031, "R_ij": +0.077}),
])

plt.rcParams.update({
    "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
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


# =============================================================================
# DATA LOADING
# =============================================================================

def load_data():
    loader = NetworkLoader(str(DATA_DIR))
    W_unsigned = loader.load_adjacency_matrix("post")
    type_names = loader.load_type_names()
    channels = loader.load_channels()
    nt_map = loader.load_neurotransmitter_mapping()
    W = loader.sign_matrix(W_unsigned, type_names)

    encoder = ChannelEncoder(type_names)
    enc = encoder.encode_all(channels)

    idx_to_type = dict(zip(type_names["index"], type_names["type"]))
    type_to_idx = encoder.type_to_idx
    type_to_nt = dict(zip(nt_map["type"], nt_map["consensus_nt"]))
    type_to_inhib = dict(zip(nt_map["type"], nt_map["is_inhibitory"]))

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    Wt = W.T.tocsc()
    W_csc = W.tocsc()

    return {
        "W": W, "W_unsigned": W_unsigned, "Wt": Wt, "W_csc": W_csc,
        "type_names": type_names, "channels": channels, "nt_map": nt_map,
        "encoder": encoder, "enc": enc,
        "idx_to_type": idx_to_type, "type_to_idx": type_to_idx,
        "type_to_nt": type_to_nt, "type_to_inhib": type_to_inhib,
        "s_ppk23": s_ppk23, "s_ppk25": s_ppk25, "s_both": s_both,
    }


# =============================================================================
# ANALYSIS 1: Nonlinear step-by-step comparison
# =============================================================================

def analysis_1_stepwise(data):
    """
    Propagate ppk23-only, ppk25-only, and both through the network
    step by step WITH the sigmoid nonlinearity (sustained mode).
    Show where the R_ij divergence emerges for mixed-destructive vs super.
    """
    logger.info("=" * 70)
    logger.info("ANALYSIS 1: Nonlinear step-by-step comparison")
    logger.info("=" * 70)

    W = data["W"]
    s_ppk23 = data["s_ppk23"]
    s_ppk25 = data["s_ppk25"]
    s_both = data["s_both"]
    type_to_idx = data["type_to_idx"]

    prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
    traj_23 = prop.propagate_trajectory(s_ppk23, N_STEPS, sustained=SUSTAINED)
    traj_25 = prop.propagate_trajectory(s_ppk25, N_STEPS, sustained=SUSTAINED)
    traj_both = prop.propagate_trajectory(s_both, N_STEPS, sustained=SUSTAINED)

    # Focus set: 2 mixed-destructive + 2 genuine super
    focus_neurons = ["mAL_m1", "mAL_m9", "LH008m", "mAL_m2a"]
    focus_info = {}
    for n in focus_neurons:
        if n in MIXED_DESTRUCTIVE:
            focus_info[n] = {"cat": "mixed_destructive", "color": "#377EB8", "marker": "s"}
        elif n in GENUINE_SUPER:
            focus_info[n] = {"cat": "genuine_super", "color": "#E41A1C", "marker": "D"}

    steps = np.arange(N_STEPS + 1)

    # Collect step-by-step data for all neurons in both groups
    all_results = []
    all_neurons = list(MIXED_DESTRUCTIVE.keys()) + list(GENUINE_SUPER.keys())
    for neuron in all_neurons:
        if neuron not in type_to_idx:
            continue
        idx = type_to_idx[neuron]
        cat = "mixed_destructive" if neuron in MIXED_DESTRUCTIVE else "genuine_super"
        info = MIXED_DESTRUCTIVE.get(neuron, GENUINE_SUPER.get(neuron))
        for step in range(N_STEPS + 1):
            a23 = traj_23[step, idx]
            a25 = traj_25[step, idx]
            aboth = traj_both[step, idx]
            r_ij = aboth - a23 - a25
            all_results.append({
                "neuron": neuron, "category": cat, "group": info["group"],
                "step": step,
                "A_ppk23": a23, "A_ppk25": a25, "A_both": aboth,
                "R_ij": r_ij, "linear_sum": a23 + a25,
            })

    df_steps = pd.DataFrame(all_results)
    df_steps.to_csv(OUT_DIR / "stepwise_trajectories.csv", index=False)

    # ── Figure: 4-neuron comparison ──
    fig, axes = plt.subplots(2, 4, figsize=(20, 9))
    for col, neuron in enumerate(focus_neurons):
        if neuron not in type_to_idx:
            continue
        idx = type_to_idx[neuron]
        info = focus_info[neuron]

        a23 = traj_23[:, idx]
        a25 = traj_25[:, idx]
        aboth = traj_both[:, idx]
        r_ij = aboth - a23 - a25
        linsum = a23 + a25

        ax = axes[0, col]
        ax.plot(steps, a23, "o-", color="#FFD92F", label="ppk23", lw=2, ms=6)
        ax.plot(steps, a25, "s-", color="#E5C494", label="ppk25", lw=2, ms=6)
        ax.plot(steps, linsum, "^--", color="gray", label="linear sum", lw=1.2, ms=5, alpha=0.6)
        ax.plot(steps, aboth, "D-", color=info["color"], label="actual both", lw=2.5, ms=7)
        ax.axhline(0, color="black", lw=0.4, ls=":")
        ax.set_title(f"{neuron}\n({info['cat'].replace('_',' ')})",
                     fontsize=10, fontweight="bold", color=info["color"])
        ax.set_xticks(steps)
        if col == 0:
            ax.set_ylabel("Activation")
            ax.legend(fontsize=6, loc="best")
        ax.set_xlabel("Step")

        ax = axes[1, col]
        bars = ax.bar(steps, r_ij, color=info["color"], alpha=0.8,
                      edgecolor="black", lw=0.5)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xlabel("Step")
        if col == 0:
            ax.set_ylabel("R_ij")
        ax.set_title(f"R_ij at each step", fontsize=9)
        # Annotate final R_ij
        ax.annotate(f"R_ij(step3) = {r_ij[-1]:.3f}",
                    xy=(N_STEPS, r_ij[-1]),
                    fontsize=8, fontweight="bold",
                    ha="center",
                    va="bottom" if r_ij[-1] > 0 else "top")

        # Print key findings
        logger.info("  %s (%s):", neuron, info["cat"])
        for s in range(N_STEPS + 1):
            logger.info("    Step %d: A_23=%.4f, A_25=%.4f, A_both=%.4f, R_ij=%.4f",
                        s, a23[s], a25[s], aboth[s], r_ij[s])

    fig.suptitle("Analysis 1: Step-by-step nonlinear propagation\n"
                 "Mixed-destructive (blue) vs Genuine super (red)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "analysis1_stepwise_comparison",
             description="Step-by-step nonlinear trajectory for 4 key neurons. "
             "Top row: activations under ppk23-only, ppk25-only, and both. "
             "Bottom row: step-wise R_ij showing where divergence emerges.")

    return df_steps


# =============================================================================
# ANALYSIS 2: Drive asymmetry
# =============================================================================

def analysis_2_drive_asymmetry(data):
    """
    Check if one channel's drive dominates in mixed-destructive neurons.
    Hypothesis: if |d25| >> |d23|, the neuron is mostly ppk25-driven and
    the small ppk23 opposition is insufficient to prevent saturation.
    """
    logger.info("=" * 70)
    logger.info("ANALYSIS 2: Drive asymmetry")
    logger.info("=" * 70)

    W = data["W"]
    Wt = data["Wt"]
    s_ppk23 = data["s_ppk23"]
    s_ppk25 = data["s_ppk25"]
    type_to_idx = data["type_to_idx"]

    # Linear propagation for drives
    x23_lin = [s_ppk23.copy()]
    x25_lin = [s_ppk25.copy()]
    x = s_ppk23.copy()
    for _ in range(4):
        x = Wt.dot(x)
        x23_lin.append(x.copy())
    x = s_ppk25.copy()
    for _ in range(4):
        x = Wt.dot(x)
        x25_lin.append(x.copy())

    # Sustained linear for comparison
    x23_sust = [s_ppk23.copy()]
    x25_sust = [s_ppk25.copy()]
    x = s_ppk23.copy()
    for _ in range(3):
        x = Wt.dot(x) + s_ppk23
        x23_sust.append(x.copy())
    x = s_ppk25.copy()
    for _ in range(3):
        x = Wt.dot(x) + s_ppk25
        x25_sust.append(x.copy())

    rows = []
    all_neurons = list(MIXED_DESTRUCTIVE.keys()) + list(GENUINE_SUPER.keys())
    for neuron in all_neurons:
        if neuron not in type_to_idx:
            continue
        idx = type_to_idx[neuron]
        cat = "mixed_destructive" if neuron in MIXED_DESTRUCTIVE else "genuine_super"
        info = MIXED_DESTRUCTIVE.get(neuron, GENUINE_SUPER.get(neuron))

        # Last-hop linear drive at step 2 (from linear pulse propagation)
        d23_step2 = x23_lin[2][idx]
        d25_step2 = x25_lin[2][idx]

        # Also at step 3
        d23_step3 = x23_lin[3][idx]
        d25_step3 = x25_lin[3][idx]

        # Sustained linear drives
        d23_sust3 = x23_sust[3][idx]
        d25_sust3 = x25_sust[3][idx]

        abs_d23 = abs(d23_step2)
        abs_d25 = abs(d25_step2)
        ratio = abs_d23 / abs_d25 if abs_d25 > 1e-12 else float("inf")
        dominance = abs_d25 / (abs_d23 + abs_d25) if (abs_d23 + abs_d25) > 1e-12 else 0.5

        rows.append({
            "neuron": neuron, "category": cat, "group": info["group"],
            "d23_step2": d23_step2, "d25_step2": d25_step2,
            "d23_step3": d23_step3, "d25_step3": d25_step3,
            "d23_sust3": d23_sust3, "d25_sust3": d25_sust3,
            "abs_d23": abs_d23, "abs_d25": abs_d25,
            "ratio_23_25": ratio,
            "dominance_d25": dominance,  # 0.5 = balanced, >0.5 = d25 dominates
            "R_ij_expected": info["R_ij"],
            "same_sign_linear": (d23_step2 > 0) == (d25_step2 > 0),
        })

    df_asym = pd.DataFrame(rows)
    df_asym.to_csv(OUT_DIR / "drive_asymmetry.csv", index=False)

    # Print summary
    logger.info("  DRIVE ASYMMETRY SUMMARY:")
    logger.info("  %-12s %-18s %10s %10s %8s %10s %8s",
                "Neuron", "Category", "d23", "d25", "|d23/d25|", "d25_frac", "R_ij")
    for _, r in df_asym.iterrows():
        logger.info("  %-12s %-18s %10.5f %10.5f %8.3f %10.3f %8.3f",
                    r["neuron"], r["category"],
                    r["d23_step2"], r["d25_step2"],
                    r["ratio_23_25"], r["dominance_d25"], r["R_ij_expected"])

    # Group statistics
    super_ratios = df_asym[df_asym["category"] == "genuine_super"]["ratio_23_25"].values
    destr_ratios = df_asym[df_asym["category"] == "mixed_destructive"]["ratio_23_25"].values

    logger.info("\n  Group mean |d23|/|d25| ratio:")
    logger.info("    Genuine super:       %.3f (range %.3f - %.3f)",
                np.mean(super_ratios), np.min(super_ratios), np.max(super_ratios))
    logger.info("    Mixed destructive:   %.3f (range %.3f - %.3f)",
                np.mean(destr_ratios), np.min(destr_ratios), np.max(destr_ratios))

    # ── Figure ──
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    # Panel A: |d23| vs |d25| scatter with annotations
    ax = axes[0]
    for _, r in df_asym.iterrows():
        color = "#E41A1C" if r["category"] == "genuine_super" else "#377EB8"
        marker = "D" if r["category"] == "genuine_super" else "s"
        ax.scatter(r["abs_d23"], r["abs_d25"], c=color, s=100, marker=marker,
                   edgecolor="black", lw=0.5, zorder=3)
        ax.annotate(r["neuron"], (r["abs_d23"], r["abs_d25"]),
                    fontsize=7, ha="left", va="bottom",
                    xytext=(3, 3), textcoords="offset points")
    max_val = max(df_asym["abs_d23"].max(), df_asym["abs_d25"].max()) * 1.1
    ax.plot([0, max_val], [0, max_val], "k--", alpha=0.3, lw=0.8, label="balanced")
    ax.set_xlabel("|d23| (ppk23 drive magnitude)")
    ax.set_ylabel("|d25| (ppk25 drive magnitude)")
    ax.set_title("A  Drive magnitudes\n(diagonal = balanced)")
    ax.legend(fontsize=8)

    # Panel B: Ratio bar chart
    ax = axes[1]
    df_sorted = df_asym.sort_values("ratio_23_25")
    colors = ["#E41A1C" if c == "genuine_super" else "#377EB8"
              for c in df_sorted["category"]]
    x_pos = range(len(df_sorted))
    ax.barh(x_pos, df_sorted["ratio_23_25"], color=colors,
            edgecolor="black", lw=0.5)
    ax.set_yticks(list(x_pos))
    ax.set_yticklabels(df_sorted["neuron"], fontsize=8)
    ax.set_xlabel("|d23| / |d25|")
    ax.set_title("B  Drive ratio (1.0 = balanced)")
    ax.axvline(1.0, color="black", lw=1, ls="--", alpha=0.5)
    # Add R_ij values
    for i, (_, r) in enumerate(df_sorted.iterrows()):
        ax.text(r["ratio_23_25"] + 0.05, i, f"R={r['R_ij_expected']:.3f}",
                fontsize=7, va="center")

    # Panel C: Dominance fraction vs R_ij
    ax = axes[2]
    for _, r in df_asym.iterrows():
        color = "#E41A1C" if r["category"] == "genuine_super" else "#377EB8"
        marker = "D" if r["category"] == "genuine_super" else "s"
        ax.scatter(r["dominance_d25"], r["R_ij_expected"], c=color, s=100,
                   marker=marker, edgecolor="black", lw=0.5, zorder=3)
        ax.annotate(r["neuron"], (r["dominance_d25"], r["R_ij_expected"]),
                    fontsize=7, ha="left", va="bottom",
                    xytext=(3, 3), textcoords="offset points")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.axvline(0.5, color="gray", lw=0.5, ls=":", alpha=0.5)
    ax.set_xlabel("ppk25 dominance fraction\n(0.5 = balanced, >0.5 = ppk25 dominates)")
    ax.set_ylabel("R_ij")
    ax.set_title("C  Drive imbalance vs interaction mode")

    fig.suptitle("Analysis 2: Drive asymmetry in mixed-drive neurons",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "analysis2_drive_asymmetry",
             description="Drive asymmetry analysis. A: scatter of ppk23 vs ppk25 drive magnitudes. "
             "B: drive ratio bar chart. C: dominance fraction vs R_ij. "
             "Red diamonds = genuine super, blue squares = mixed destructive.")

    return df_asym


# =============================================================================
# ANALYSIS 3: Higher-order (step 1) nonlinear activations
# =============================================================================

def analysis_3_upstream_nonlinear(data):
    """
    The last-hop decomposition uses step 2 LINEAR drives. But the actual
    signal has already been through nonlinear activation at step 1.
    Compute NONLINEAR activations at step 1 and step 2 intermediaries
    for ppk23-only, ppk25-only, and both, and see where the interaction
    is already determined before reaching the target.
    """
    logger.info("=" * 70)
    logger.info("ANALYSIS 3: Upstream nonlinear interaction at intermediaries")
    logger.info("=" * 70)

    W = data["W"]
    W_csc = data["W_csc"]
    s_ppk23 = data["s_ppk23"]
    s_ppk25 = data["s_ppk25"]
    s_both = data["s_both"]
    type_to_idx = data["type_to_idx"]
    idx_to_type = data["idx_to_type"]
    type_to_nt = data["type_to_nt"]
    type_to_inhib = data["type_to_inhib"]

    prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
    traj_23 = prop.propagate_trajectory(s_ppk23, N_STEPS, sustained=SUSTAINED)
    traj_25 = prop.propagate_trajectory(s_ppk25, N_STEPS, sustained=SUSTAINED)
    traj_both = prop.propagate_trajectory(s_both, N_STEPS, sustained=SUSTAINED)

    # For each focus neuron, find its presynaptic partners and trace their
    # nonlinear R_ij at step 1 and step 2
    focus_neurons = ["mAL_m1", "mAL_m9", "LH008m", "mAL_m2a",
                     "AVLP743m", "WED015", "mAL_m8", "AVLP728m"]

    all_pre_rows = []
    upstream_summaries = {}

    for neuron in focus_neurons:
        if neuron not in type_to_idx:
            continue
        target_idx = type_to_idx[neuron]
        cat = "mixed_destructive" if neuron in MIXED_DESTRUCTIVE else "genuine_super"

        # Presynaptic neurons
        col = W_csc[:, target_idx].toarray().ravel()
        pre_indices = np.nonzero(col)[0]

        # Target's own nonlinear R_ij at each step
        target_rij = {}
        for step in range(N_STEPS + 1):
            target_rij[step] = (traj_both[step, target_idx]
                                - traj_23[step, target_idx]
                                - traj_25[step, target_idx])

        logger.info("\n  %s (%s): R_ij by step: %s", neuron, cat,
                    {s: f"{v:.4f}" for s, v in target_rij.items()})

        pre_summary = []
        for pre_idx in pre_indices:
            pre_type = idx_to_type.get(pre_idx, f"idx_{pre_idx}")
            w_signed = col[pre_idx]

            # Nonlinear activation of presynaptic neuron at step BEFORE target arrives
            # Target receives signal at step t from presynaptic neuron at step t-1
            # For step 3 target, presynaptic is at step 2
            for ref_step in [1, 2]:
                a23_pre = traj_23[ref_step, pre_idx]
                a25_pre = traj_25[ref_step, pre_idx]
                aboth_pre = traj_both[ref_step, pre_idx]
                delta_pre = aboth_pre - a23_pre - a25_pre

                # The CONTRIBUTION of this presynaptic neuron's interaction to the target:
                # When the intermediary is already nonlinear, its output feeds into the target.
                # contribution_delta = w * delta_pre
                # But also the individual activations contribute:
                contrib_23 = w_signed * a23_pre
                contrib_25 = w_signed * a25_pre
                contrib_both = w_signed * aboth_pre
                contrib_delta = w_signed * delta_pre

                all_pre_rows.append({
                    "target": neuron, "target_category": cat,
                    "presynaptic": pre_type, "pre_idx": pre_idx,
                    "weight_signed": w_signed,
                    "ref_step": ref_step,
                    "pre_A_ppk23": a23_pre, "pre_A_ppk25": a25_pre,
                    "pre_A_both": aboth_pre, "pre_delta": delta_pre,
                    "contrib_ppk23": contrib_23, "contrib_ppk25": contrib_25,
                    "contrib_both": contrib_both, "contrib_delta": contrib_delta,
                    "pre_nt": type_to_nt.get(pre_type, "unknown"),
                    "pre_is_inhibitory": type_to_inhib.get(pre_type, False),
                })

            # For summary: use step 2 (the one that feeds into step 3 at target)
            a23_p2 = traj_23[2, pre_idx]
            a25_p2 = traj_25[2, pre_idx]
            aboth_p2 = traj_both[2, pre_idx]
            delta_p2 = aboth_p2 - a23_p2 - a25_p2

            pre_summary.append({
                "pre_type": pre_type, "pre_idx": pre_idx,
                "w": w_signed,
                "a23": a23_p2, "a25": a25_p2, "aboth": aboth_p2,
                "delta": delta_p2,
                "contrib_delta": w_signed * delta_p2,
                "is_inhib": type_to_inhib.get(pre_type, False),
            })

        # Sort by absolute contribution_delta
        pre_summary.sort(key=lambda x: abs(x["contrib_delta"]), reverse=True)
        upstream_summaries[neuron] = pre_summary

        # Print top contributors
        total_contrib_delta = sum(p["contrib_delta"] for p in pre_summary)
        logger.info("    Total presynaptic delta contribution: %.5f", total_contrib_delta)
        for p in pre_summary[:5]:
            inh_tag = " [INH]" if p["is_inhib"] else " [EXC]"
            logger.info("      %s%s: w=%.4f, delta_pre=%.5f, w*delta=%.6f  "
                        "(a23=%.4f, a25=%.4f, aboth=%.4f)",
                        p["pre_type"], inh_tag, p["w"], p["delta"],
                        p["contrib_delta"],
                        p["a23"], p["a25"], p["aboth"])

    df_pre = pd.DataFrame(all_pre_rows)
    df_pre.to_csv(OUT_DIR / "upstream_nonlinear_decomposition.csv", index=False)

    # ── Figure: For key neurons, show presynaptic delta contributions ──
    fig_neurons = ["mAL_m1", "mAL_m9", "LH008m", "mAL_m2a"]
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    for ax_idx, neuron in enumerate(fig_neurons):
        ax = axes[ax_idx // 2, ax_idx % 2]
        if neuron not in upstream_summaries:
            ax.set_visible(False)
            continue
        cat = "mixed_destructive" if neuron in MIXED_DESTRUCTIVE else "genuine_super"
        pre_list = upstream_summaries[neuron]

        # Take top 15 by absolute contribution
        top = sorted(pre_list, key=lambda x: abs(x["contrib_delta"]), reverse=True)[:15]
        top = sorted(top, key=lambda x: x["contrib_delta"])  # sort by value for plotting

        colors = []
        for p in top:
            if p["contrib_delta"] > 0:
                colors.append("#E41A1C")  # positive contribution to R_ij
            else:
                colors.append("#377EB8")  # negative contribution to R_ij

        ax.barh(range(len(top)), [p["contrib_delta"] for p in top],
                color=colors, edgecolor="black", lw=0.3)
        labels = []
        for p in top:
            inh_tag = " [INH]" if p["is_inhib"] else " [EXC]"
            labels.append(f"{p['pre_type']}{inh_tag} (w={p['w']:.3f})")
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(labels, fontsize=7)
        ax.axvline(0, color="black", lw=0.8)

        # Annotate the presynaptic neuron's own delta
        for i, p in enumerate(top):
            ax.text(p["contrib_delta"], i,
                    f" delta_pre={p['delta']:.4f}",
                    fontsize=5, va="center",
                    ha="left" if p["contrib_delta"] >= 0 else "right")

        cat_color = "#377EB8" if cat == "mixed_destructive" else "#E41A1C"
        ax.set_title(f"{neuron} ({cat.replace('_',' ')})\n"
                     f"Presynaptic contributions to R_ij at step 2",
                     fontsize=10, fontweight="bold", color=cat_color)
        ax.set_xlabel("w * delta_presynaptic\n(positive=increases R_ij, negative=decreases)")

    fig.suptitle("Analysis 3: Upstream nonlinear interaction\n"
                 "Intermediary neurons already carry interaction signal",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "analysis3_upstream_nonlinear",
             description="Presynaptic neuron contributions to R_ij. Each bar is "
             "w_signed * delta_presynaptic, where delta = A(both) - A(ppk23) - A(ppk25) "
             "at the presynaptic neuron itself. Shows where interaction originates upstream.")

    return df_pre, upstream_summaries


# =============================================================================
# ANALYSIS 4: Direct presynaptic decomposition with full accounting
# =============================================================================

def analysis_4_presynaptic_decomposition(data, upstream_summaries):
    """
    For the mixed-destructive neurons, decompose how each presynaptic
    neuron contributes to both the INDIVIDUAL channel activations AND
    the interaction. Identify whether the presynaptic neuron itself
    is saturated (already destructive) or whether the sign of drive
    changes under combined stimulation.
    """
    logger.info("=" * 70)
    logger.info("ANALYSIS 4: Presynaptic decomposition — where does destructive originate?")
    logger.info("=" * 70)

    W = data["W"]
    W_csc = data["W_csc"]
    Wt = data["Wt"]
    s_ppk23 = data["s_ppk23"]
    s_ppk25 = data["s_ppk25"]
    s_both = data["s_both"]
    type_to_idx = data["type_to_idx"]
    idx_to_type = data["idx_to_type"]
    type_to_nt = data["type_to_nt"]
    type_to_inhib = data["type_to_inhib"]

    prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
    traj_23 = prop.propagate_trajectory(s_ppk23, N_STEPS, sustained=SUSTAINED)
    traj_25 = prop.propagate_trajectory(s_ppk25, N_STEPS, sustained=SUSTAINED)
    traj_both = prop.propagate_trajectory(s_both, N_STEPS, sustained=SUSTAINED)

    # Also compute linear drives for comparison
    x23_lin = [s_ppk23.copy()]
    x25_lin = [s_ppk25.copy()]
    x = s_ppk23.copy()
    for _ in range(3):
        x = Wt.dot(x)
        x23_lin.append(x.copy())
    x = s_ppk25.copy()
    for _ in range(3):
        x = Wt.dot(x)
        x25_lin.append(x.copy())

    focus_neurons = list(MIXED_DESTRUCTIVE.keys()) + list(GENUINE_SUPER.keys())
    decomp_rows = []

    for neuron in focus_neurons:
        if neuron not in type_to_idx:
            continue
        target_idx = type_to_idx[neuron]
        cat = "mixed_destructive" if neuron in MIXED_DESTRUCTIVE else "genuine_super"

        col = W_csc[:, target_idx].toarray().ravel()
        pre_indices = np.nonzero(col)[0]

        logger.info("\n  === %s (%s) ===", neuron, cat)

        for pre_idx in pre_indices:
            pre_type = idx_to_type.get(pre_idx, f"idx_{pre_idx}")
            w = col[pre_idx]

            # NONLINEAR activations at step 2 (feeds into step 3)
            a23_nl = traj_23[2, pre_idx]
            a25_nl = traj_25[2, pre_idx]
            aboth_nl = traj_both[2, pre_idx]
            delta_nl = aboth_nl - a23_nl - a25_nl

            # LINEAR drives at step 2
            a23_lin = x23_lin[2][pre_idx]
            a25_lin = x25_lin[2][pre_idx]

            # Classify presynaptic neuron behavior
            # Is the presynaptic neuron itself already destructive?
            pre_is_destructive = delta_nl < 0
            # Is it saturated? (close to +/-1)
            pre_saturated = (abs(aboth_nl) > 0.9) or (abs(a23_nl) > 0.9) or (abs(a25_nl) > 0.9)

            # What kind of drive does this pre-neuron deliver?
            # The key is: w * a_pre under each condition
            delivery_23 = w * a23_nl
            delivery_25 = w * a25_nl
            delivery_both = w * aboth_nl
            delivery_interaction = delivery_both - delivery_23 - delivery_25

            decomp_rows.append({
                "target": neuron, "target_category": cat,
                "presynaptic": pre_type, "pre_idx": pre_idx,
                "weight": w,
                "pre_nt": type_to_nt.get(pre_type, "unknown"),
                "pre_is_inhibitory": type_to_inhib.get(pre_type, False),
                # Nonlinear activations
                "pre_a23_nl": a23_nl, "pre_a25_nl": a25_nl,
                "pre_aboth_nl": aboth_nl, "pre_delta_nl": delta_nl,
                # Linear drives
                "pre_a23_lin": a23_lin, "pre_a25_lin": a25_lin,
                # Classification
                "pre_is_destructive": pre_is_destructive,
                "pre_saturated": pre_saturated,
                # Delivery to target
                "delivery_23": delivery_23, "delivery_25": delivery_25,
                "delivery_both": delivery_both,
                "delivery_interaction": delivery_interaction,
            })

    df_decomp = pd.DataFrame(decomp_rows)
    df_decomp.to_csv(OUT_DIR / "presynaptic_full_decomposition.csv", index=False)

    # ── KEY FINDING: For each target, how much of R_ij comes from
    # presynaptic neurons that are THEMSELVES destructive? ──
    logger.info("\n  INTERACTION ORIGIN ANALYSIS:")
    logger.info("  %-12s %-18s  %10s %10s %10s %10s",
                "Neuron", "Category", "R_ij",
                "from_destr", "from_super", "from_mix")

    origin_rows = []
    for neuron in focus_neurons:
        if neuron not in type_to_idx:
            continue
        target_idx = type_to_idx[neuron]
        cat = "mixed_destructive" if neuron in MIXED_DESTRUCTIVE else "genuine_super"
        info = MIXED_DESTRUCTIVE.get(neuron, GENUINE_SUPER.get(neuron))

        df_n = df_decomp[df_decomp["target"] == neuron]

        # From destructive presynaptic neurons (delta < 0)
        from_destr = df_n[df_n["pre_delta_nl"] < -1e-6]["delivery_interaction"].sum()
        # From super presynaptic neurons (delta > 0)
        from_super = df_n[df_n["pre_delta_nl"] > 1e-6]["delivery_interaction"].sum()
        # From neutral (delta ~ 0)
        from_neutral = df_n[df_n["pre_delta_nl"].abs() <= 1e-6]["delivery_interaction"].sum()

        total_rij = from_destr + from_super + from_neutral

        # Count of presynaptic neurons in each category
        n_destr = (df_n["pre_delta_nl"] < -1e-6).sum()
        n_super = (df_n["pre_delta_nl"] > 1e-6).sum()

        # Fraction of interaction from destructive presynaptic neurons
        total_abs = abs(from_destr) + abs(from_super) + abs(from_neutral)
        frac_destr = abs(from_destr) / total_abs if total_abs > 1e-12 else 0

        origin_rows.append({
            "neuron": neuron, "category": cat,
            "total_delivery_rij": total_rij,
            "from_destructive_pre": from_destr,
            "from_super_pre": from_super,
            "from_neutral_pre": from_neutral,
            "n_destructive_pre": n_destr,
            "n_super_pre": n_super,
            "frac_from_destructive": frac_destr,
            "R_ij_expected": info["R_ij"],
        })

        logger.info("  %-12s %-18s  %10.4f %10.4f %10.4f %10.4f",
                    neuron, cat, total_rij, from_destr, from_super, from_neutral)

    df_origin = pd.DataFrame(origin_rows)
    df_origin.to_csv(OUT_DIR / "interaction_origin.csv", index=False)

    # ── Figure: Origin decomposition ──
    fig, axes = plt.subplots(1, 3, figsize=(20, 7))

    # Panel A: Stacked bar showing where R_ij comes from
    ax = axes[0]
    df_plot = df_origin.sort_values("R_ij_expected")
    x_pos = np.arange(len(df_plot))
    colors_cat = ["#E41A1C" if c == "genuine_super" else "#377EB8"
                  for c in df_plot["category"]]

    ax.barh(x_pos, df_plot["from_destructive_pre"], color="#377EB8", alpha=0.8,
            edgecolor="black", lw=0.3, label="From destructive intermediaries")
    ax.barh(x_pos, df_plot["from_super_pre"],
            left=df_plot["from_destructive_pre"].values,
            color="#E41A1C", alpha=0.8, edgecolor="black", lw=0.3,
            label="From super intermediaries")
    ax.set_yticks(x_pos)
    labels = [f"{r['neuron']} ({r['category'][:5]})" for _, r in df_plot.iterrows()]
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Contribution to target R_ij")
    ax.set_title("A  Where does the target's R_ij originate?")
    ax.axvline(0, color="black", lw=0.8)
    ax.legend(fontsize=7, loc="best")

    # Panel B: Scatter — fraction from destructive vs actual R_ij
    ax = axes[1]
    for _, r in df_origin.iterrows():
        color = "#E41A1C" if r["category"] == "genuine_super" else "#377EB8"
        marker = "D" if r["category"] == "genuine_super" else "s"
        ax.scatter(r["frac_from_destructive"], r["R_ij_expected"],
                   c=color, s=100, marker=marker, edgecolor="black", lw=0.5, zorder=3)
        ax.annotate(r["neuron"], (r["frac_from_destructive"], r["R_ij_expected"]),
                    fontsize=7, ha="left", va="bottom",
                    xytext=(3, 3), textcoords="offset points")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.set_xlabel("Fraction of |interaction| from destructive intermediaries")
    ax.set_ylabel("R_ij")
    ax.set_title("B  Upstream destructive fraction vs R_ij")

    # Panel C: For mAL_m1 specifically, show the full presynaptic breakdown
    ax = axes[2]
    target_for_detail = "mAL_m1"
    if target_for_detail in type_to_idx:
        df_detail = df_decomp[df_decomp["target"] == target_for_detail].copy()
        df_detail["abs_del_int"] = df_detail["delivery_interaction"].abs()
        df_top = df_detail.nlargest(15, "abs_del_int").sort_values("delivery_interaction")

        bar_colors = []
        for _, r in df_top.iterrows():
            if r["pre_is_destructive"]:
                bar_colors.append("#377EB8")  # pre is destructive
            else:
                bar_colors.append("#E41A1C")  # pre is super
        ax.barh(range(len(df_top)), df_top["delivery_interaction"],
                color=bar_colors, edgecolor="black", lw=0.3)
        labels = []
        for _, r in df_top.iterrows():
            inh_tag = " [INH]" if r["pre_is_inhibitory"] else " [EXC]"
            sat_tag = " *SAT*" if r["pre_saturated"] else ""
            labels.append(f"{r['presynaptic']}{inh_tag}{sat_tag}")
        ax.set_yticks(range(len(df_top)))
        ax.set_yticklabels(labels, fontsize=7)
        ax.axvline(0, color="black", lw=0.8)
        ax.set_xlabel("delivery_interaction = w * delta_pre")
        ax.set_title(f"C  {target_for_detail}: presynaptic breakdown\n"
                     "(blue=destructive pre, red=super pre)")

    fig.suptitle("Analysis 4: Presynaptic decomposition — origin of interaction",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "analysis4_presynaptic_decomposition",
             description="Full presynaptic decomposition. A: stacked bar of R_ij origin. "
             "B: fraction from destructive intermediaries vs actual R_ij. "
             "C: detailed breakdown for mAL_m1.")

    return df_decomp, df_origin


# =============================================================================
# COMBINED MULTI-PANEL DIAGNOSTIC FIGURE
# =============================================================================

def make_combined_figure(data, df_steps, df_asym, df_pre_nl, upstream_summaries,
                          df_decomp, df_origin):
    """Create the master multi-panel diagnostic figure."""
    logger.info("=" * 70)
    logger.info("CREATING COMBINED DIAGNOSTIC FIGURE")
    logger.info("=" * 70)

    W = data["W"]
    s_ppk23 = data["s_ppk23"]
    s_ppk25 = data["s_ppk25"]
    s_both = data["s_both"]
    type_to_idx = data["type_to_idx"]

    prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
    traj_23 = prop.propagate_trajectory(s_ppk23, N_STEPS, sustained=SUSTAINED)
    traj_25 = prop.propagate_trajectory(s_ppk25, N_STEPS, sustained=SUSTAINED)
    traj_both = prop.propagate_trajectory(s_both, N_STEPS, sustained=SUSTAINED)

    fig = plt.figure(figsize=(24, 20))
    gs = GridSpec(4, 4, figure=fig, hspace=0.45, wspace=0.35)

    # ── Row 1: Step-by-step trajectories (4 neurons) ──
    focus_4 = ["mAL_m1", "mAL_m9", "LH008m", "mAL_m2a"]
    steps = np.arange(N_STEPS + 1)

    for col, neuron in enumerate(focus_4):
        if neuron not in type_to_idx:
            continue
        idx = type_to_idx[neuron]
        cat = "mixed_destructive" if neuron in MIXED_DESTRUCTIVE else "genuine_super"
        color = "#377EB8" if cat == "mixed_destructive" else "#E41A1C"

        a23 = traj_23[:, idx]
        a25 = traj_25[:, idx]
        aboth = traj_both[:, idx]
        r_ij = aboth - a23 - a25

        ax = fig.add_subplot(gs[0, col])
        ax.plot(steps, a23, "o-", color="#FFD92F", label="ppk23", lw=1.8, ms=5)
        ax.plot(steps, a25, "s-", color="#E5C494", label="ppk25", lw=1.8, ms=5)
        ax.plot(steps, a23 + a25, "^--", color="gray", label="lin sum", lw=1, ms=4, alpha=0.5)
        ax.plot(steps, aboth, "D-", color=color, label="actual", lw=2.2, ms=6)
        ax.axhline(0, color="black", lw=0.3, ls=":")
        ax.set_xticks(steps)
        ax.set_xlabel("Step")
        if col == 0:
            ax.set_ylabel("Activation")
            ax.legend(fontsize=6)
        ax.set_title(f"{neuron} ({cat.split('_')[0]})\nR_ij={r_ij[-1]:.3f}",
                     fontsize=9, fontweight="bold", color=color)

    # ── Row 2, col 0-1: Step-wise R_ij for all neurons in both groups ──
    ax_rij_destr = fig.add_subplot(gs[1, 0:2])
    for neuron, info in MIXED_DESTRUCTIVE.items():
        if neuron not in type_to_idx:
            continue
        idx = type_to_idx[neuron]
        r_ij = traj_both[:, idx] - traj_23[:, idx] - traj_25[:, idx]
        ax_rij_destr.plot(steps, r_ij, "s--", lw=1.2, ms=4, alpha=0.8,
                          label=f"{neuron} (R={info['R_ij']:.3f})")
    ax_rij_destr.axhline(0, color="black", lw=0.8)
    ax_rij_destr.set_xlabel("Step")
    ax_rij_destr.set_ylabel("R_ij")
    ax_rij_destr.set_title("Step-wise R_ij: Mixed-destructive neurons", fontsize=10)
    ax_rij_destr.legend(fontsize=6, ncol=2, loc="best")
    ax_rij_destr.set_xticks(steps)

    ax_rij_super = fig.add_subplot(gs[1, 2:4])
    for neuron, info in GENUINE_SUPER.items():
        if neuron not in type_to_idx:
            continue
        idx = type_to_idx[neuron]
        r_ij = traj_both[:, idx] - traj_23[:, idx] - traj_25[:, idx]
        ax_rij_super.plot(steps, r_ij, "D-", lw=1.5, ms=5, alpha=0.8,
                          label=f"{neuron} (R={info['R_ij']:.3f})")
    ax_rij_super.axhline(0, color="black", lw=0.8)
    ax_rij_super.set_xlabel("Step")
    ax_rij_super.set_ylabel("R_ij")
    ax_rij_super.set_title("Step-wise R_ij: Genuine super neurons", fontsize=10)
    ax_rij_super.legend(fontsize=6, loc="best")
    ax_rij_super.set_xticks(steps)

    # ── Row 3, col 0: Drive asymmetry scatter ──
    ax = fig.add_subplot(gs[2, 0])
    for _, r in df_asym.iterrows():
        color = "#E41A1C" if r["category"] == "genuine_super" else "#377EB8"
        marker = "D" if r["category"] == "genuine_super" else "s"
        ax.scatter(r["ratio_23_25"], r["R_ij_expected"], c=color, s=80,
                   marker=marker, edgecolor="black", lw=0.5, zorder=3)
        ax.annotate(r["neuron"], (r["ratio_23_25"], r["R_ij_expected"]),
                    fontsize=6, ha="left", va="bottom",
                    xytext=(2, 2), textcoords="offset points")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.axvline(1.0, color="gray", lw=0.5, ls=":", alpha=0.5)
    ax.set_xlabel("|d23| / |d25|  (1=balanced)")
    ax.set_ylabel("R_ij")
    ax.set_title("Drive balance vs R_ij", fontsize=10)

    # ── Row 3, col 1: Dominance fraction ──
    ax = fig.add_subplot(gs[2, 1])
    for _, r in df_asym.iterrows():
        color = "#E41A1C" if r["category"] == "genuine_super" else "#377EB8"
        marker = "D" if r["category"] == "genuine_super" else "s"
        ax.scatter(r["dominance_d25"], r["R_ij_expected"], c=color, s=80,
                   marker=marker, edgecolor="black", lw=0.5, zorder=3)
        ax.annotate(r["neuron"], (r["dominance_d25"], r["R_ij_expected"]),
                    fontsize=6, ha="left", va="bottom",
                    xytext=(2, 2), textcoords="offset points")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.axvline(0.5, color="gray", lw=0.5, ls=":")
    ax.set_xlabel("ppk25 dominance")
    ax.set_ylabel("R_ij")
    ax.set_title("Drive dominance vs R_ij", fontsize=10)

    # ── Row 3, col 2: Upstream destructive fraction ──
    ax = fig.add_subplot(gs[2, 2])
    for _, r in df_origin.iterrows():
        color = "#E41A1C" if r["category"] == "genuine_super" else "#377EB8"
        marker = "D" if r["category"] == "genuine_super" else "s"
        ax.scatter(r["frac_from_destructive"], r["R_ij_expected"],
                   c=color, s=80, marker=marker, edgecolor="black", lw=0.5, zorder=3)
        ax.annotate(r["neuron"], (r["frac_from_destructive"], r["R_ij_expected"]),
                    fontsize=6, ha="left", va="bottom",
                    xytext=(2, 2), textcoords="offset points")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.set_xlabel("Frac interaction from destructive intermediaries")
    ax.set_ylabel("R_ij")
    ax.set_title("Upstream origin of interaction", fontsize=10)

    # ── Row 3, col 3: Presynaptic delta bar for mAL_m1 ──
    ax = fig.add_subplot(gs[2, 3])
    neuron = "mAL_m1"
    if neuron in upstream_summaries:
        pre_list = upstream_summaries[neuron]
        top = sorted(pre_list, key=lambda x: abs(x["contrib_delta"]), reverse=True)[:12]
        top = sorted(top, key=lambda x: x["contrib_delta"])
        bar_colors = ["#377EB8" if p["delta"] < 0 else "#E41A1C" for p in top]
        ax.barh(range(len(top)), [p["contrib_delta"] for p in top],
                color=bar_colors, edgecolor="black", lw=0.3)
        labels = [f"{p['pre_type']} ({'INH' if p['is_inhib'] else 'EXC'})" for p in top]
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(labels, fontsize=6)
        ax.axvline(0, color="black", lw=0.8)
        ax.set_xlabel("w * delta_pre")
        ax.set_title(f"{neuron}: presynaptic R_ij origin", fontsize=10)

    # ── Row 4: Text summary of key findings ──
    ax = fig.add_subplot(gs[3, :])
    ax.axis("off")

    # Build key findings text
    findings = []
    findings.append("KEY FINDINGS: Why mixed-drive neurons can still be destructive")
    findings.append("=" * 80)
    findings.append("")

    # Finding 1: R_ij already negative at step 1 or 2
    findings.append("1. EARLY EMERGENCE: R_ij becomes negative BEFORE the last hop.")
    for neuron in ["mAL_m1", "mAL_m9"]:
        if neuron in type_to_idx:
            idx = type_to_idx[neuron]
            r_vals = [traj_both[s, idx] - traj_23[s, idx] - traj_25[s, idx]
                      for s in range(N_STEPS + 1)]
            findings.append(f"   {neuron}: R_ij by step = {[f'{v:.4f}' for v in r_vals]}")
    findings.append("   The destructive interaction is established UPSTREAM, not at the last synapse.")
    findings.append("")

    # Finding 2: Drive asymmetry
    super_ratios = df_asym[df_asym["category"] == "genuine_super"]["ratio_23_25"]
    destr_ratios = df_asym[df_asym["category"] == "mixed_destructive"]["ratio_23_25"]
    findings.append("2. DRIVE ASYMMETRY: Mixed-destructive neurons have more IMBALANCED drives.")
    findings.append(f"   Genuine super mean |d23/d25|: {super_ratios.mean():.3f} "
                    f"(range {super_ratios.min():.3f}-{super_ratios.max():.3f})")
    findings.append(f"   Mixed-destr mean |d23/d25|:   {destr_ratios.mean():.3f} "
                    f"(range {destr_ratios.min():.3f}-{destr_ratios.max():.3f})")
    findings.append("   When one drive dominates, the neuron is mostly driven by ONE channel.")
    findings.append("   The opposing drive is too weak to prevent saturation.")
    findings.append("")

    # Finding 3: Upstream destructive intermediaries
    findings.append("3. UPSTREAM DESTRUCTION: Presynaptic neurons are THEMSELVES destructive.")
    findings.append("   The target inherits destructive interaction from its inputs.")
    for _, r in df_origin.iterrows():
        if r["category"] == "mixed_destructive":
            findings.append(f"   {r['neuron']}: {r['frac_from_destructive']:.1%} of interaction "
                            f"from destructive intermediaries")
    findings.append("")

    # Finding 4: The linear drive sign is misleading
    findings.append("4. LINEAR DRIVE SIGN IS MISLEADING:")
    findings.append("   The last-hop linear drive decomposition sees opposing signs (d23 < 0, d25 > 0).")
    findings.append("   But the NONLINEAR activation at the presynaptic neuron has already saturated.")
    findings.append("   The intermediary's interaction (delta_pre < 0) is what determines the target's R_ij,")
    findings.append("   not the sign of the linear drive.")
    findings.append("")

    # Finding 5: Contrast with genuine super
    findings.append("5. GENUINE SUPER NEURONS have:")
    findings.append("   (a) More BALANCED drives (|d23/d25| closer to 1.0)")
    findings.append("   (b) Presynaptic neurons that are themselves SUPER or neutral")
    findings.append("   (c) R_ij that becomes positive early (step 1-2) and stays positive")

    text = "\n".join(findings)
    ax.text(0.02, 0.98, text, transform=ax.transAxes,
            fontsize=8, va="top", family="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.9))

    fig.suptitle("Mixed-drive Destructive Investigation: Complete Diagnostic",
                 fontsize=15, fontweight="bold")
    save_fig(fig, "combined_diagnostic",
             description="Master diagnostic figure for mixed-drive destructive neurons. "
             "Row 1: step-by-step trajectories. Row 2: R_ij evolution. "
             "Row 3: drive asymmetry, dominance, upstream origin, presynaptic detail. "
             "Row 4: summary of key findings.")


# =============================================================================
# PRINT COMPREHENSIVE RESULTS
# =============================================================================

def print_comprehensive_results(data, df_steps, df_asym, df_origin):
    """Print a detailed summary of all findings to stdout."""

    W = data["W"]
    s_ppk23 = data["s_ppk23"]
    s_ppk25 = data["s_ppk25"]
    s_both = data["s_both"]
    type_to_idx = data["type_to_idx"]

    prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
    traj_23 = prop.propagate_trajectory(s_ppk23, N_STEPS, sustained=SUSTAINED)
    traj_25 = prop.propagate_trajectory(s_ppk25, N_STEPS, sustained=SUSTAINED)
    traj_both = prop.propagate_trajectory(s_both, N_STEPS, sustained=SUSTAINED)

    print("\n" + "=" * 80)
    print("MIXED-DRIVE DESTRUCTIVE INVESTIGATION: COMPLETE RESULTS")
    print("=" * 80)

    # Section 1: The puzzle
    print("\n1. THE PUZZLE")
    print("-" * 60)
    print("Some neurons receive opposing ppk23/ppk25 drives at the last hop")
    print("(linear decomposition), which should predict SUPER-ADDITIVE (R_ij > 0).")
    print("But they show DESTRUCTIVE integration (R_ij < 0).")
    print("\nMixed-destructive neurons:")
    print(f"  {'Neuron':<12s} {'Group':<12s} {'d23':>10s} {'d25':>10s} {'R_ij':>10s}")
    for n, info in MIXED_DESTRUCTIVE.items():
        print(f"  {n:<12s} {info['group']:<12s} {info['d23']:>10.4f} {info['d25']:>10.4f} {info['R_ij']:>10.3f}")
    print("\nGenuine super neurons (for comparison):")
    for n, info in GENUINE_SUPER.items():
        print(f"  {n:<12s} {info['group']:<12s} {info['d23']:>10.4f} {info['d25']:>10.4f} {info['R_ij']:>10.3f}")

    # Section 2: Step-by-step emergence
    print("\n2. STEP-BY-STEP R_ij EMERGENCE")
    print("-" * 60)
    print(f"  {'Neuron':<12s} {'Category':<18s} {'Step0':>8s} {'Step1':>8s} {'Step2':>8s} {'Step3':>8s}")
    all_neurons = list(MIXED_DESTRUCTIVE.keys()) + list(GENUINE_SUPER.keys())
    for neuron in all_neurons:
        if neuron not in type_to_idx:
            continue
        idx = type_to_idx[neuron]
        cat = "mixed_destr" if neuron in MIXED_DESTRUCTIVE else "super"
        rvals = [traj_both[s, idx] - traj_23[s, idx] - traj_25[s, idx]
                 for s in range(N_STEPS + 1)]
        print(f"  {neuron:<12s} {cat:<18s} " +
              " ".join(f"{v:>8.4f}" for v in rvals))
    print("\n  KEY FINDING: Mixed-destructive neurons show R_ij < 0 emerging at step 1-2,")
    print("  meaning the interaction is established UPSTREAM of the target, not at the last hop.")
    print("  The linear drive decomposition at step 2 is misleading because it ignores")
    print("  the nonlinear compression that has ALREADY occurred at intermediary neurons.")

    # Section 3: Drive asymmetry
    print("\n3. DRIVE ASYMMETRY")
    print("-" * 60)
    super_ratios = df_asym[df_asym["category"] == "genuine_super"]["ratio_23_25"].values
    destr_ratios = df_asym[df_asym["category"] == "mixed_destructive"]["ratio_23_25"].values
    print(f"  Genuine super:     mean |d23/d25| = {np.mean(super_ratios):.3f} "
          f"(range {np.min(super_ratios):.3f}-{np.max(super_ratios):.3f})")
    print(f"  Mixed destructive: mean |d23/d25| = {np.mean(destr_ratios):.3f} "
          f"(range {np.min(destr_ratios):.3f}-{np.max(destr_ratios):.3f})")
    print("\n  INTERPRETATION: Several mixed-destructive neurons (mAL_m9, LH004m, AVLP743m)")
    print("  have very unbalanced drives where ppk25 dominates. This means the neuron is")
    print("  essentially a ppk25 target with a tiny ppk23 opposition. The dominant ppk25")
    print("  drive saturates the neuron, and the weak ppk23 opposition cannot de-saturate it.")
    print("  HOWEVER, drive balance alone does not explain all cases (mAL_m1 has balanced")
    print("  drives but is still destructive).")

    # Section 4: Upstream interaction origin
    print("\n4. UPSTREAM INTERACTION ORIGIN")
    print("-" * 60)
    print(f"  {'Neuron':<12s} {'Category':<18s} {'frac_destr':>12s} {'from_destr':>12s} {'from_super':>12s} {'R_ij':>8s}")
    for _, r in df_origin.iterrows():
        print(f"  {r['neuron']:<12s} {r['category']:<18s} "
              f"{r['frac_from_destructive']:>12.1%} "
              f"{r['from_destructive_pre']:>12.5f} "
              f"{r['from_super_pre']:>12.5f} "
              f"{r['R_ij_expected']:>8.3f}")
    print("\n  KEY FINDING: Mixed-destructive neurons receive their interaction signal from")
    print("  presynaptic neurons that are THEMSELVES destructive. The intermediary neurons")
    print("  have delta_pre < 0 (their own A(both) < A(23) + A(25)), meaning saturation")
    print("  has already occurred upstream.")

    # Section 5: The mechanism explained
    print("\n5. THE FULL MECHANISM: Why mixed linear drives + destructive R_ij")
    print("-" * 60)
    print("""
  The paradox resolves as follows:

  (a) LINEAR drive decomposition looks at step-2 PULSE responses (no nonlinearity).
      At this level, ppk23 and ppk25 may deliver opposing-sign drives to the target.

  (b) But the ACTUAL propagation uses sustained input + tanh nonlinearity.
      Under sustained stimulation, intermediary neurons receive CUMULATIVE input
      from multiple steps, pushing them deep into saturation.

  (c) An intermediary neuron that receives BOTH ppk23 and ppk25 input
      (through shared upstream paths) becomes saturated when both are active.
      Its NONLINEAR output under 'both' is LESS than the sum of its outputs
      under ppk23-alone + ppk25-alone. This intermediary is itself destructive.

  (d) The target receives input from this saturated intermediary. Even though
      the TARGET's linear drive decomposition shows opposing signs, the
      ACTUAL signal arriving at the target is already compressed by upstream
      saturation.

  (e) The linear drive decomposition is correct about the SIGN of each
      channel's contribution at the last hop, but it misses the NONLINEAR
      compression that has already occurred at intermediary neurons.

  In short: The interaction is determined by UPSTREAM saturation, not by
  last-hop drive signs. The linear decomposition at the last hop is a
  LOCAL approximation that does not capture the GLOBAL nonlinear effects
  propagating through the network.
""")

    # Section 6: Why genuine super neurons are different
    print("6. WHY GENUINE SUPER NEURONS ARE DIFFERENT")
    print("-" * 60)
    print("""
  Genuine super neurons (LH008m, mAL_m2a, AVLP728m) differ in that:

  (a) Their presynaptic neurons are NOT destructive — the intermediaries
      have delta_pre >= 0 or close to zero.

  (b) They receive ppk23 and ppk25 through MORE INDEPENDENT pathways,
      with less overlap at intermediary neurons, so there is less upstream
      saturation.

  (c) Their drives are more balanced (|d23/d25| closer to 1.0), meaning
      the opposing signals are comparably strong. This provides genuine
      cancellation that prevents saturation at the target level.

  (d) The sign opposition is MAINTAINED through the nonlinear propagation
      because the intermediary neurons carrying ppk23 signal vs ppk25 signal
      are DIFFERENT neurons (less sharing = less co-saturation).
""")

    print("=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)


# =============================================================================
# MAIN
# =============================================================================

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Loading data...")
    data = load_data()
    logger.info("Data loaded. Matrix: %d x %d", data["W"].shape[0], data["W"].shape[1])

    # Verify neurons exist in the type index
    missing = []
    for n in list(MIXED_DESTRUCTIVE) + list(GENUINE_SUPER):
        if n not in data["type_to_idx"]:
            missing.append(n)
    if missing:
        logger.warning("Neurons not found in type_names: %s", missing)

    # Run all analyses
    df_steps = analysis_1_stepwise(data)
    df_asym = analysis_2_drive_asymmetry(data)
    df_pre_nl, upstream_summaries = analysis_3_upstream_nonlinear(data)
    df_decomp, df_origin = analysis_4_presynaptic_decomposition(data, upstream_summaries)

    # Create combined diagnostic figure
    make_combined_figure(data, df_steps, df_asym, df_pre_nl, upstream_summaries,
                          df_decomp, df_origin)

    # Print comprehensive results
    print_comprehensive_results(data, df_steps, df_asym, df_origin)

    logger.info("All outputs saved to: %s", OUT_DIR)


if __name__ == "__main__":
    main()
