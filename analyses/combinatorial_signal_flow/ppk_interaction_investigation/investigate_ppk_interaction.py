#!/usr/bin/env python3
"""
PPK23 × PPK25 Interaction Investigation
========================================

Why do some neurons show DESTRUCTIVE integration (R_ij < 0) and others
SUPER-ADDITIVE integration (R_ij > 0) when PPK23 and PPK25 are coactivated?

Key examples:
  aSP-f:  LH006m  → destructive (R_ij ≈ -0.26)
          LH008m  → super       (R_ij ≈ +0.18)
  aSP-g:  AVLP700m, AVLP704m → destructive (R_ij ≈ -0.30, -0.26)
          AVLP750m → super       (R_ij ≈ +0.17)
  PPN1 downstream: uniformly destructive
  vAB3 downstream: mostly destructive, except AVLP728m (+0.08), mAL_m2a (+0.23)

This script investigates the mechanistic basis through:
  1. Step-by-step trajectory analysis
  2. Pathway decomposition (which intermediates contribute to R_ij)
  3. Systematic ablation of intermediate neurons
  4. Direct connectivity analysis (excitatory vs inhibitory inputs)
  5. Shared-pathway overlap analysis
  6. Saturation analysis (how much activation headroom exists)

Usage:
  cd combinatorial_signal_flow
  python ppk_interaction_investigation/investigate_ppk_interaction.py
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
from matplotlib.patches import Patch
from matplotlib.gridspec import GridSpec
import seaborn as sns
from scipy import sparse
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signal_flow import (
    NetworkLoader, ChannelEncoder, SignalPropagator,
    ACTIVATIONS, sigmoid,
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
OUT_DIR = Path(__file__).resolve().parent / "plots"

NONLINEARITY = "sigmoid_rectified"
ACT_PARAMS = {"beta": 5.0}
N_STEPS = 3
SUSTAINED = True
NORMALIZATION = "post"

# Neurons of interest — synergistic vs destructive exemplars
FOCAL_NEURONS = {
    "aspf": {
        "destructive": ["LH006m", "LH003m", "LH002m"],
        "super": ["LH008m", "LH001m"],
    },
    "aspg": {
        "destructive": ["AVLP700m", "AVLP704m"],
        "super": ["AVLP750m"],
    },
    "vAB3_downstream": {
        "destructive": ["mAL_m3c", "mAL_m3b", "FLA001m"],
        "super": ["mAL_m2a", "AVLP728m"],
    },
    "PPN1_downstream": {
        "destructive": ["AVLP606", "CB1119,CB1989", "AVLP508"],
        "super": [],  # none — all destructive
    },
}

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


def save_fig(fig, name, subdir="summary", description=None):
    """Save figure as PNG + PDF."""
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


# =============================================================================
# 1. LOAD DATA
# =============================================================================

def load_everything():
    """Load network, channels, targets, and build propagator."""
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

    # Build target indices (excluding sensory neurons)
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
        "W": W,
        "W_unsigned": W_unsigned,
        "type_names": type_names,
        "channels": channels,
        "targets": targets,
        "palette": palette,
        "nt_map": nt_map,
        "encoder": encoder,
        "encoded_channels": encoded_channels,
        "target_indices": target_indices,
    }


# =============================================================================
# 2. TRAJECTORY ANALYSIS — Where does divergence happen?
# =============================================================================

def analyse_trajectories(data):
    """
    For each focal neuron, track activation at every propagation step
    for ppk23-alone, ppk25-alone, and ppk23+ppk25-together.
    Plot the trajectory and the step-wise R_ij.
    """
    logger.info("=" * 60)
    logger.info("TRAJECTORY ANALYSIS")
    logger.info("=" * 60)

    W = data["W"]
    encoder = data["encoder"]
    enc = data["encoded_channels"]

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    propagator = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)

    traj_23 = propagator.propagate_trajectory(s_ppk23, N_STEPS, sustained=SUSTAINED)
    traj_25 = propagator.propagate_trajectory(s_ppk25, N_STEPS, sustained=SUSTAINED)
    traj_both = propagator.propagate_trajectory(s_both, N_STEPS, sustained=SUSTAINED)

    # Collect all focal neurons
    all_focal = {}
    for tg, groups in FOCAL_NEURONS.items():
        for category, neurons in groups.items():
            for neuron in neurons:
                if neuron in encoder.type_to_idx:
                    idx = encoder.type_to_idx[neuron]
                    all_focal[neuron] = {
                        "idx": idx,
                        "group": tg,
                        "category": category,
                    }

    if not all_focal:
        logger.warning("No focal neurons found in type_names!")
        return

    # ── Per-neuron trajectory plots ──
    steps = np.arange(N_STEPS + 1)

    for neuron, info in all_focal.items():
        idx = info["idx"]
        a23 = traj_23[:, idx]
        a25 = traj_25[:, idx]
        aboth = traj_both[:, idx]
        r_ij = aboth - a23 - a25  # step-wise R_ij

        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

        # Left: activation trajectories
        ax = axes[0]
        ax.plot(steps, a23, "o-", color="#FFD92F", label="ppk23 alone", lw=2, ms=7)
        ax.plot(steps, a25, "s-", color="#E5C494", label="ppk25 alone", lw=2, ms=7)
        ax.plot(steps, a23 + a25, "^--", color="gray", label="ppk23+ppk25 (linear sum)", lw=1.5, ms=6, alpha=0.6)
        ax.plot(steps, aboth, "D-", color="#E41A1C" if info["category"] == "super" else "#377EB8",
                label="ppk23+ppk25 (actual)", lw=2.5, ms=8)
        ax.set_xlabel("Propagation step")
        ax.set_ylabel("Activation")
        ax.set_title(f"{neuron} ({info['group']})")
        ax.legend(fontsize=8)
        ax.axhline(0, color="black", lw=0.5, ls=":")
        ax.set_xticks(steps)

        # Right: step-wise R_ij
        ax = axes[1]
        color = "#E41A1C" if info["category"] == "super" else "#377EB8"
        ax.bar(steps, r_ij, color=color, alpha=0.8, edgecolor="black", lw=0.5)
        ax.set_xlabel("Propagation step")
        ax.set_ylabel("R_ij = A(both) − A(ppk23) − A(ppk25)")
        ax.set_title(f"Step-wise interaction ({info['category']})")
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(steps)

        # Add final R_ij annotation
        final_r = r_ij[-1]
        ax.annotate(f"final R_ij = {final_r:.4f}",
                     xy=(N_STEPS, final_r), fontsize=9, fontweight="bold",
                     ha="center", va="bottom" if final_r > 0 else "top")

        fig.suptitle(f"PPK23 × PPK25 trajectory: {neuron} — {info['category'].upper()} integration",
                     fontsize=13, fontweight="bold")
        fig.tight_layout()
        save_fig(fig, f"trajectory_{neuron}", "trajectory",
                 description=f"Step-by-step activation trajectory for {neuron} ({info['group']}). "
                 f"Shows ppk23-alone, ppk25-alone, their linear sum, and actual combined activation. "
                 f"Right panel shows step-wise R_ij (deviation from linearity). "
                 f"Category: {info['category']} integration.")

    # ── Summary panel: all focal neurons side by side ──
    n_neurons = len(all_focal)
    fig, axes = plt.subplots(2, max(n_neurons, 1), figsize=(3.5 * n_neurons, 8),
                              squeeze=False)
    for col, (neuron, info) in enumerate(all_focal.items()):
        idx = info["idx"]
        a23 = traj_23[:, idx]
        a25 = traj_25[:, idx]
        aboth = traj_both[:, idx]
        r_ij = aboth - a23 - a25

        ax = axes[0, col]
        ax.plot(steps, a23, "o-", color="#FFD92F", lw=1.5, ms=5)
        ax.plot(steps, a25, "s-", color="#E5C494", lw=1.5, ms=5)
        ax.plot(steps, a23 + a25, "^--", color="gray", lw=1, ms=4, alpha=0.5)
        color = "#E41A1C" if info["category"] == "super" else "#377EB8"
        ax.plot(steps, aboth, "D-", color=color, lw=2, ms=6)
        ax.set_title(f"{neuron}\n({info['category']})", fontsize=9,
                     color=color, fontweight="bold")
        ax.axhline(0, color="black", lw=0.3)
        ax.set_xticks(steps)
        if col == 0:
            ax.set_ylabel("Activation")

        ax = axes[1, col]
        ax.bar(steps, r_ij, color=color, alpha=0.8, edgecolor="black", lw=0.3)
        ax.axhline(0, color="black", lw=0.5)
        ax.set_xlabel("Step")
        ax.set_xticks(steps)
        if col == 0:
            ax.set_ylabel("R_ij")
        ax.text(0.95, 0.95, f"R={r_ij[-1]:.3f}", transform=ax.transAxes,
                ha="right", va="top", fontsize=8, fontweight="bold")

    fig.suptitle("PPK23 × PPK25 interaction trajectories — all focal neurons",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "trajectory_summary_all", "trajectory",
             description="Summary of step-by-step trajectories for all focal neurons.")


# =============================================================================
# 3. PATHWAY DECOMPOSITION — Which intermediates drive R_ij?
# =============================================================================

def analyse_pathway_decomposition(data):
    """
    Decompose: after step 1, which intermediate neurons are most different
    between the 'actual combined' vs 'linear sum' condition?
    These are the neurons responsible for the nonlinear interaction.
    """
    logger.info("=" * 60)
    logger.info("PATHWAY DECOMPOSITION")
    logger.info("=" * 60)

    W = data["W"]
    encoder = data["encoder"]
    enc = data["encoded_channels"]
    type_names = data["type_names"]
    nt_map = data["nt_map"]

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    propagator = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)

    traj_23 = propagator.propagate_trajectory(s_ppk23, N_STEPS, sustained=SUSTAINED)
    traj_25 = propagator.propagate_trajectory(s_ppk25, N_STEPS, sustained=SUSTAINED)
    traj_both = propagator.propagate_trajectory(s_both, N_STEPS, sustained=SUSTAINED)

    idx_to_type = dict(zip(type_names["index"], type_names["type"]))
    type_to_nt = dict(zip(nt_map["type"], nt_map["consensus_nt"]))
    type_to_inhib = dict(zip(nt_map["type"], nt_map["is_inhibitory"]))

    # For each step, compute the "interaction vector" across ALL neurons
    # delta[t] = x_both[t] - x_23[t] - x_25[t]
    # This shows WHERE in the network the nonlinearity accumulates
    for step in range(1, N_STEPS + 1):
        delta = traj_both[step] - traj_23[step] - traj_25[step]

        # Find top positive and top negative delta neurons
        top_k = 30
        top_pos_idx = np.argsort(delta)[-top_k:][::-1]
        top_neg_idx = np.argsort(delta)[:top_k]

        rows = []
        for idx in np.concatenate([top_pos_idx, top_neg_idx]):
            t = idx_to_type.get(idx, f"idx_{idx}")
            rows.append({
                "type": t,
                "index": idx,
                "delta": delta[idx],
                "a_both": traj_both[step, idx],
                "a_23": traj_23[step, idx],
                "a_25": traj_25[step, idx],
                "linear_sum": traj_23[step, idx] + traj_25[step, idx],
                "nt": type_to_nt.get(t, "unknown"),
                "is_inhibitory": type_to_inhib.get(t, False),
            })
        df = pd.DataFrame(rows).drop_duplicates("type")
        df.to_csv(OUT_DIR / "pathway_decomposition" / f"intermediate_delta_step{step}.csv", index=False)
        logger.info("  Step %d: top delta neurons saved (%d)", step, len(df))

        # ── Plot: top intermediate neurons with largest |delta| ──
        df_sorted = df.sort_values("delta")
        fig, ax = plt.subplots(figsize=(10, max(6, len(df_sorted) * 0.25)))
        colors = ["#E41A1C" if d > 0 else "#377EB8" for d in df_sorted["delta"]]
        bars = ax.barh(range(len(df_sorted)), df_sorted["delta"], color=colors,
                       edgecolor="black", lw=0.3)
        ax.set_yticks(range(len(df_sorted)))
        labels = []
        for _, r in df_sorted.iterrows():
            nt_label = f" [{r['nt']}" + (" INH" if r["is_inhibitory"] else " EXC") + "]"
            labels.append(r["type"] + nt_label)
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_xlabel("δ = A(both) − A(ppk23) − A(ppk25)")
        ax.set_title(f"Intermediate neurons with largest interaction signal — Step {step}")
        ax.axvline(0, color="black", lw=0.8)
        fig.tight_layout()
        save_fig(fig, f"intermediate_delta_step{step}", "pathway_decomposition",
                 description=f"Neurons with largest deviation from linear summation at step {step}. "
                 f"Red = supralinear (more activation than expected), Blue = sublinear.")

    # ── Pathway tracing: For focal neurons, trace which intermediates
    #    connect ppk23/ppk25 inputs to the target ──
    Wt = W.T.tocsc()  # post x pre
    W_csc = W.tocsc()  # pre x post

    all_focal = []
    for tg, groups in FOCAL_NEURONS.items():
        for cat, neurons in groups.items():
            for n in neurons:
                if n in encoder.type_to_idx:
                    all_focal.append((n, tg, cat, encoder.type_to_idx[n]))

    ppk23_idx = encoder.get_indices(data["channels"]["ppk23"])
    ppk25_idx = encoder.get_indices(data["channels"]["ppk25"])

    rows_connectivity = []
    for neuron, tg, cat, target_idx in all_focal:
        # Get 1-hop presynaptic partners of this target
        # W[pre, post] → column target_idx gives all presynaptic weights
        col = W_csc[:, target_idx].toarray().ravel()
        pre_indices = np.nonzero(col)[0]

        for pre_idx in pre_indices:
            pre_type = idx_to_type.get(pre_idx, f"idx_{pre_idx}")
            weight = col[pre_idx]

            # How much does this presynaptic neuron get activated by ppk23 vs ppk25?
            a23_pre = traj_23[N_STEPS - 1, pre_idx]  # activation 1 step before final
            a25_pre = traj_25[N_STEPS - 1, pre_idx]
            aboth_pre = traj_both[N_STEPS - 1, pre_idx]

            rows_connectivity.append({
                "target": neuron,
                "target_group": tg,
                "target_category": cat,
                "presynaptic": pre_type,
                "pre_idx": pre_idx,
                "weight": weight,
                "nt": type_to_nt.get(pre_type, "unknown"),
                "is_inhibitory": type_to_inhib.get(pre_type, False),
                "pre_a_ppk23": a23_pre,
                "pre_a_ppk25": a25_pre,
                "pre_a_both": aboth_pre,
                "pre_delta": aboth_pre - a23_pre - a25_pre,
                "contribution_23": weight * a23_pre,
                "contribution_25": weight * a25_pre,
                "contribution_both": weight * aboth_pre,
                "contribution_delta": weight * (aboth_pre - a23_pre - a25_pre),
            })

    if rows_connectivity:
        df_conn = pd.DataFrame(rows_connectivity)
        df_conn.to_csv(OUT_DIR / "pathway_decomposition" / "presynaptic_contributions.csv", index=False)

        # ── Plot: for each focal neuron, show top contributing presynaptic neurons ──
        for neuron, tg, cat, _ in all_focal:
            df_n = df_conn[df_conn["target"] == neuron].copy()
            if df_n.empty:
                continue

            # Sort by absolute contribution_delta
            df_n["abs_delta"] = df_n["contribution_delta"].abs()
            df_n = df_n.nlargest(25, "abs_delta")
            df_n = df_n.sort_values("contribution_delta")

            fig, ax = plt.subplots(figsize=(10, max(5, len(df_n) * 0.3)))
            colors = []
            for _, r in df_n.iterrows():
                if r["contribution_delta"] > 0:
                    colors.append("#E41A1C")  # synergistic contribution
                else:
                    colors.append("#377EB8")  # antagonistic contribution
            ax.barh(range(len(df_n)), df_n["contribution_delta"], color=colors,
                    edgecolor="black", lw=0.3)
            labels = []
            for _, r in df_n.iterrows():
                nt_tag = " [INH]" if r["is_inhibitory"] else " [EXC]"
                w_tag = f" (w={r['weight']:.3f})"
                labels.append(r["presynaptic"] + nt_tag + w_tag)
            ax.set_yticks(range(len(df_n)))
            ax.set_yticklabels(labels, fontsize=7)
            ax.set_xlabel("Contribution to R_ij\n(weight × δ_presynaptic)")
            ax.set_title(f"Presynaptic contributions to {neuron} ({cat} integration)\n"
                         f"Target group: {tg}")
            ax.axvline(0, color="black", lw=0.8)
            fig.tight_layout()
            save_fig(fig, f"presynaptic_{neuron}", "pathway_decomposition",
                     description=f"Top 25 presynaptic neurons contributing to R_ij at {neuron}. "
                     f"Contribution = synaptic weight × δ (deviation from linearity in presynaptic activity). "
                     f"Red = synergistic, Blue = antagonistic contribution.")


# =============================================================================
# 4. ABLATION ANALYSIS — Remove intermediates and see how R_ij changes
# =============================================================================

def analyse_ablations(data):
    """
    Systematically ablate (zero out) rows/columns of intermediate neurons
    and recompute R_ij for ppk23×ppk25 at focal targets.
    Identifies which intermediates are necessary for the interaction.
    """
    logger.info("=" * 60)
    logger.info("ABLATION ANALYSIS")
    logger.info("=" * 60)

    W = data["W"]
    encoder = data["encoder"]
    enc = data["encoded_channels"]
    type_names = data["type_names"]
    nt_map = data["nt_map"]
    idx_to_type = dict(zip(type_names["index"], type_names["type"]))
    type_to_nt = dict(zip(nt_map["type"], nt_map["consensus_nt"]))
    type_to_inhib = dict(zip(nt_map["type"], nt_map["is_inhibitory"]))

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    # Baseline R_ij
    prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
    x_23 = prop.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
    x_25 = prop.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
    x_both = prop.propagate(s_both, N_STEPS, sustained=SUSTAINED)

    all_focal = []
    for tg, groups in FOCAL_NEURONS.items():
        for cat, neurons in groups.items():
            for n in neurons:
                if n in encoder.type_to_idx:
                    idx = encoder.type_to_idx[n]
                    r_ij_baseline = x_both[idx] - x_23[idx] - x_25[idx]
                    all_focal.append({
                        "neuron": n, "group": tg, "category": cat,
                        "idx": idx, "R_ij_baseline": r_ij_baseline,
                    })

    logger.info("  Baseline R_ij values:")
    for f in all_focal:
        logger.info("    %s (%s): R_ij = %.4f", f["neuron"], f["category"], f["R_ij_baseline"])

    # Identify candidate neurons to ablate:
    # Use the step-1 delta to find neurons with large interaction signals
    traj_both = prop.propagate_trajectory(s_both, N_STEPS, sustained=SUSTAINED)
    traj_23 = prop.propagate_trajectory(s_ppk23, N_STEPS, sustained=SUSTAINED)
    traj_25 = prop.propagate_trajectory(s_ppk25, N_STEPS, sustained=SUSTAINED)

    # Candidates: neurons with large |delta| at any step
    max_abs_delta = np.zeros(W.shape[0])
    for step in range(1, N_STEPS + 1):
        delta = np.abs(traj_both[step] - traj_23[step] - traj_25[step])
        max_abs_delta = np.maximum(max_abs_delta, delta)

    # Exclude sensory neurons and target neurons themselves
    sensory_types = set()
    for ch_types in data["channels"].values():
        sensory_types.update(ch_types)
    sensory_idx = set(encoder.get_indices(list(sensory_types)))
    target_idx = set(f["idx"] for f in all_focal)

    candidate_mask = np.ones(W.shape[0], dtype=bool)
    for i in sensory_idx | target_idx:
        candidate_mask[i] = False

    max_abs_delta[~candidate_mask] = 0
    top_candidates = np.argsort(max_abs_delta)[-50:][::-1]  # top 50

    logger.info("  Ablating top %d intermediate neurons...", len(top_candidates))

    ablation_rows = []
    W_lil = W.tolil()  # for efficient row/col manipulation

    for abl_idx in top_candidates:
        abl_type = idx_to_type.get(abl_idx, f"idx_{abl_idx}")

        # Create ablated matrix: zero out row AND column for this neuron
        W_abl = W_lil.copy()
        W_abl[abl_idx, :] = 0  # no output
        W_abl[:, abl_idx] = 0  # no input
        W_abl_csc = W_abl.tocsc()

        prop_abl = SignalPropagator(W_abl_csc, NONLINEARITY, ACT_PARAMS)
        x_23_abl = prop_abl.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
        x_25_abl = prop_abl.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
        x_both_abl = prop_abl.propagate(s_both, N_STEPS, sustained=SUSTAINED)

        for f in all_focal:
            tidx = f["idx"]
            r_ij_abl = x_both_abl[tidx] - x_23_abl[tidx] - x_25_abl[tidx]
            delta_r = r_ij_abl - f["R_ij_baseline"]

            ablation_rows.append({
                "ablated_neuron": abl_type,
                "ablated_idx": abl_idx,
                "ablated_nt": type_to_nt.get(abl_type, "unknown"),
                "ablated_is_inhibitory": type_to_inhib.get(abl_type, False),
                "target_neuron": f["neuron"],
                "target_group": f["group"],
                "target_category": f["category"],
                "R_ij_baseline": f["R_ij_baseline"],
                "R_ij_ablated": r_ij_abl,
                "delta_R_ij": delta_r,
                "pct_change": (delta_r / abs(f["R_ij_baseline"])) * 100 if f["R_ij_baseline"] != 0 else 0,
            })

    df_abl = pd.DataFrame(ablation_rows)
    df_abl.to_csv(OUT_DIR / "ablation" / "ablation_results.csv", index=False)
    logger.info("  Ablation results: %d rows saved", len(df_abl))

    # ── Plot: per focal neuron, which ablations have largest effect? ──
    for f in all_focal:
        neuron = f["neuron"]
        df_n = df_abl[df_abl["target_neuron"] == neuron].copy()
        df_n["abs_delta"] = df_n["delta_R_ij"].abs()
        df_top = df_n.nlargest(20, "abs_delta").sort_values("delta_R_ij")

        if df_top.empty:
            continue

        fig, ax = plt.subplots(figsize=(10, max(5, len(df_top) * 0.3)))
        colors = []
        for _, r in df_top.iterrows():
            # If ablation makes R_ij more positive → the ablated neuron was causing opposition
            # If ablation makes R_ij more negative → the ablated neuron was causing synergy
            if r["delta_R_ij"] > 0:
                colors.append("#E41A1C")  # ablation increases R_ij
            else:
                colors.append("#377EB8")  # ablation decreases R_ij
        ax.barh(range(len(df_top)), df_top["delta_R_ij"], color=colors,
                edgecolor="black", lw=0.3)
        labels = []
        for _, r in df_top.iterrows():
            nt_tag = " [INH]" if r["ablated_is_inhibitory"] else " [EXC]"
            labels.append(r["ablated_neuron"] + nt_tag)
        ax.set_yticks(range(len(df_top)))
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_xlabel("ΔR_ij (ablated − baseline)")
        ax.set_title(f"Ablation effects on {neuron} ({f['category']})\n"
                     f"Baseline R_ij = {f['R_ij_baseline']:.4f}")
        ax.axvline(0, color="black", lw=0.8)
        fig.tight_layout()
        save_fig(fig, f"ablation_{neuron}", "ablation",
                 description=f"Effect of ablating individual intermediate neurons on R_ij at {neuron}. "
                 f"Red: ablation increases R_ij (removes opposition). "
                 f"Blue: ablation decreases R_ij (removes synergy). "
                 f"Baseline R_ij = {f['R_ij_baseline']:.4f}.")

    # ── Summary heatmap: ablation effect matrix (neurons × ablated) ──
    focal_names = [f["neuron"] for f in all_focal]
    # Pick top 20 most impactful ablations overall
    overall_impact = df_abl.groupby("ablated_neuron")["delta_R_ij"].apply(
        lambda x: x.abs().max()
    ).nlargest(20)
    top_ablated = overall_impact.index.tolist()

    mat = np.zeros((len(focal_names), len(top_ablated)))
    for i, fn in enumerate(focal_names):
        for j, abl in enumerate(top_ablated):
            row = df_abl[(df_abl["target_neuron"] == fn) & (df_abl["ablated_neuron"] == abl)]
            if len(row) > 0:
                mat[i, j] = row.iloc[0]["delta_R_ij"]

    vmax = max(abs(mat.min()), abs(mat.max())) or 1e-6
    fig, ax = plt.subplots(figsize=(max(8, len(top_ablated) * 0.6), max(4, len(focal_names) * 0.5)))
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(top_ablated)))
    ax.set_xticklabels(top_ablated, rotation=60, ha="right", fontsize=7)
    ax.set_yticks(range(len(focal_names)))

    # Color-code y labels by category
    for i, f in enumerate(all_focal):
        color = "#E41A1C" if f["category"] == "super" else "#377EB8"
        ax.get_yticklabels()[i] if ax.get_yticklabels() else None
    ylabels = [f"{f['neuron']} ({f['category'][0].upper()})" for f in all_focal]
    ax.set_yticklabels(ylabels, fontsize=8)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("ΔR_ij (ablated − baseline)")
    ax.set_title("Ablation effect matrix: PPK23 × PPK25 interaction")
    ax.set_xlabel("Ablated intermediate neuron")
    ax.set_ylabel("Target neuron")
    fig.tight_layout()
    save_fig(fig, "ablation_heatmap", "ablation",
             description="Heatmap showing the effect of ablating each intermediate neuron (columns) "
             "on the PPK23×PPK25 interaction R_ij at each focal target (rows). "
             "Red = ablation increases R_ij (removes opposition), Blue = decreases (removes synergy).")


# =============================================================================
# 5. CONNECTIVITY ANALYSIS — Direct wiring explains integration mode?
# =============================================================================

def analyse_connectivity(data):
    """
    For each focal neuron, analyze:
    1. Excitatory vs inhibitory input balance from ppk23 vs ppk25 pathways
    2. Shared vs unique presynaptic partners
    3. Weight distributions
    """
    logger.info("=" * 60)
    logger.info("CONNECTIVITY ANALYSIS")
    logger.info("=" * 60)

    W = data["W"]
    W_unsigned = data["W_unsigned"]
    encoder = data["encoder"]
    type_names = data["type_names"]
    nt_map = data["nt_map"]
    enc = data["encoded_channels"]

    idx_to_type = dict(zip(type_names["index"], type_names["type"]))
    type_to_nt = dict(zip(nt_map["type"], nt_map["consensus_nt"]))
    type_to_inhib = dict(zip(nt_map["type"], nt_map["is_inhibitory"]))

    ppk23_idx = set(encoder.get_indices(data["channels"]["ppk23"]))
    ppk25_idx = set(encoder.get_indices(data["channels"]["ppk25"]))

    propagator = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    # Get trajectories to understand intermediate activations
    traj_23 = propagator.propagate_trajectory(s_ppk23, N_STEPS, sustained=SUSTAINED)
    traj_25 = propagator.propagate_trajectory(s_ppk25, N_STEPS, sustained=SUSTAINED)
    traj_both = propagator.propagate_trajectory(s_both, N_STEPS, sustained=SUSTAINED)

    W_csc = W.tocsc()
    W_unsigned_csc = W_unsigned.tocsc()

    all_focal = []
    for tg, groups in FOCAL_NEURONS.items():
        for cat, neurons in groups.items():
            for n in neurons:
                if n in encoder.type_to_idx:
                    all_focal.append((n, tg, cat, encoder.type_to_idx[n]))

    # ── Analysis 1: Input balance at each step ──
    balance_rows = []
    for neuron, tg, cat, target_idx in all_focal:
        col_signed = W_csc[:, target_idx].toarray().ravel()
        col_raw = W_unsigned_csc[:, target_idx].toarray().ravel()

        pre_indices = np.nonzero(col_raw)[0]

        total_exc_23 = 0
        total_inh_23 = 0
        total_exc_25 = 0
        total_inh_25 = 0
        total_exc_shared = 0
        total_inh_shared = 0
        n_shared = 0
        n_unique_23 = 0
        n_unique_25 = 0

        for pre_idx in pre_indices:
            pre_type = idx_to_type.get(pre_idx, "")
            is_inhib = type_to_inhib.get(pre_type, False)
            w = col_signed[pre_idx]

            # How much is this presynaptic neuron driven by ppk23 vs ppk25?
            # Use step N_STEPS-1 activation (one step before reaching target)
            a23 = traj_23[N_STEPS - 1, pre_idx] if N_STEPS >= 1 else 0
            a25 = traj_25[N_STEPS - 1, pre_idx] if N_STEPS >= 1 else 0

            driven_by_23 = abs(a23) > 1e-6
            driven_by_25 = abs(a25) > 1e-6

            if driven_by_23 and driven_by_25:
                n_shared += 1
                if is_inhib:
                    total_inh_shared += abs(w)
                else:
                    total_exc_shared += abs(w)
            elif driven_by_23:
                n_unique_23 += 1
            elif driven_by_25:
                n_unique_25 += 1

            if driven_by_23:
                if is_inhib:
                    total_inh_23 += abs(w) * abs(a23)
                else:
                    total_exc_23 += abs(w) * abs(a23)

            if driven_by_25:
                if is_inhib:
                    total_inh_25 += abs(w) * abs(a25)
                else:
                    total_exc_25 += abs(w) * abs(a25)

        balance_rows.append({
            "neuron": neuron,
            "group": tg,
            "category": cat,
            "n_presynaptic": len(pre_indices),
            "n_shared": n_shared,
            "n_unique_23": n_unique_23,
            "n_unique_25": n_unique_25,
            "exc_input_ppk23": total_exc_23,
            "inh_input_ppk23": total_inh_23,
            "exc_input_ppk25": total_exc_25,
            "inh_input_ppk25": total_inh_25,
            "exc_shared": total_exc_shared,
            "inh_shared": total_inh_shared,
            "ei_ratio_23": total_exc_23 / max(total_inh_23, 1e-10),
            "ei_ratio_25": total_exc_25 / max(total_inh_25, 1e-10),
        })

    df_balance = pd.DataFrame(balance_rows)
    df_balance.to_csv(OUT_DIR / "connectivity" / "input_balance.csv", index=False)

    # ── Plot: E/I balance comparison ──
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))

    # Panel A: Shared vs unique presynaptic partners
    ax = axes[0]
    x = np.arange(len(df_balance))
    width = 0.25
    ax.bar(x - width, df_balance["n_unique_23"], width, label="Unique ppk23", color="#FFD92F")
    ax.bar(x, df_balance["n_shared"], width, label="Shared", color="#808080")
    ax.bar(x + width, df_balance["n_unique_25"], width, label="Unique ppk25", color="#E5C494")
    ax.set_xticks(x)
    ax.set_xticklabels(df_balance["neuron"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("# presynaptic partners")
    ax.set_title("Shared vs unique inputs")
    ax.legend(fontsize=8)
    # Mark super vs destructive
    for i, row in df_balance.iterrows():
        color = "#E41A1C" if row["category"] == "super" else "#377EB8"
        ax.get_xticklabels()[i].set_color(color)

    # Panel B: E/I ratio for ppk23 vs ppk25
    ax = axes[1]
    super_mask = df_balance["category"] == "super"
    destr_mask = df_balance["category"] == "destructive"
    ax.scatter(df_balance.loc[super_mask, "ei_ratio_23"],
               df_balance.loc[super_mask, "ei_ratio_25"],
               c="#E41A1C", s=100, label="Super", edgecolor="black", zorder=3)
    ax.scatter(df_balance.loc[destr_mask, "ei_ratio_23"],
               df_balance.loc[destr_mask, "ei_ratio_25"],
               c="#377EB8", s=100, label="Destructive", edgecolor="black", zorder=3)
    for _, row in df_balance.iterrows():
        ax.annotate(row["neuron"], (row["ei_ratio_23"], row["ei_ratio_25"]),
                    fontsize=7, ha="left", va="bottom")
    ax.set_xlabel("E/I ratio (ppk23 pathway)")
    ax.set_ylabel("E/I ratio (ppk25 pathway)")
    ax.set_title("Excitation/Inhibition balance")
    ax.plot([0, ax.get_xlim()[1]], [0, ax.get_xlim()[1]], "k--", alpha=0.3)
    ax.legend(fontsize=8)

    # Panel C: Shared inhibitory input weight
    ax = axes[2]
    colors = ["#E41A1C" if c == "super" else "#377EB8" for c in df_balance["category"]]
    ax.bar(range(len(df_balance)), df_balance["inh_shared"], color=colors,
           edgecolor="black", lw=0.5)
    ax.set_xticks(range(len(df_balance)))
    ax.set_xticklabels(df_balance["neuron"], rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("Shared inhibitory input weight")
    ax.set_title("Shared inhibitory convergence\n(higher → more destructive potential)")

    fig.suptitle("Connectivity analysis: PPK23 × PPK25 pathways to focal neurons",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "connectivity_balance", "connectivity",
             description="Three-panel connectivity analysis. "
             "A: Number of shared vs unique presynaptic partners from ppk23/ppk25 pathways. "
             "B: Excitatory/Inhibitory ratio comparison. "
             "C: Shared inhibitory input weight (higher = more destructive potential).")


# =============================================================================
# 6. SATURATION ANALYSIS — Is it just sigmoid saturation?
# =============================================================================

def analyse_saturation(data):
    """
    Test whether destructive integration is simply due to activation saturation:
    neurons that are already near tanh(1)=0.76 from single channels saturate
    when both are active, while low-activation neurons have headroom.
    """
    logger.info("=" * 60)
    logger.info("SATURATION ANALYSIS")
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

    # Also run with linear activation to see "true linear sum"
    prop_linear = SignalPropagator(W, "linear", {})
    x_23_lin = prop_linear.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
    x_25_lin = prop_linear.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
    x_both_lin = prop_linear.propagate(s_both, N_STEPS, sustained=SUSTAINED)

    rows = []
    for tg in ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]:
        if tg not in targets:
            continue
        for t in targets[tg]:
            if t not in encoder.type_to_idx:
                continue
            idx = encoder.type_to_idx[t]
            a23 = x_23[idx]
            a25 = x_25[idx]
            aboth = x_both[idx]
            r_ij = aboth - a23 - a25

            # Linear R_ij (should be ~0 if propagation is truly linear)
            r_ij_lin = x_both_lin[idx] - x_23_lin[idx] - x_25_lin[idx]

            # Max single-channel activation
            max_single = max(abs(a23), abs(a25))
            # Sum of singles
            sum_singles = a23 + a25

            rows.append({
                "target_group": tg,
                "target_type": t,
                "A_ppk23": a23,
                "A_ppk25": a25,
                "A_both": aboth,
                "R_ij": r_ij,
                "R_ij_linear": r_ij_lin,
                "max_single": max_single,
                "sum_singles": sum_singles,
                "headroom": 1.0 - max_single,  # distance from saturation
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "summary" / "saturation_analysis.csv", index=False)

    # ── Plot: R_ij vs max single-channel activation ──
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

    group_colors = {
        "aspf": "#E41A1C",
        "aspg": "#377EB8",
        "PPN1_downstream": "#FF7F00",
        "vAB3_downstream": "#4DAF4A",
    }

    # Panel A: R_ij vs max single activation
    ax = axes[0]
    for tg, color in group_colors.items():
        mask = df["target_group"] == tg
        ax.scatter(df.loc[mask, "max_single"], df.loc[mask, "R_ij"],
                   c=color, s=60, label=tg, edgecolor="black", lw=0.5, alpha=0.8)
        for _, r in df[mask].iterrows():
            ax.annotate(r["target_type"], (r["max_single"], r["R_ij"]),
                        fontsize=5, alpha=0.7)
    ax.set_xlabel("Max single-channel activation |A(ppk23)| or |A(ppk25)|")
    ax.set_ylabel("R_ij (ppk23 × ppk25)")
    ax.set_title("R_ij vs activation level")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.legend(fontsize=7)

    # Panel B: R_ij vs headroom (1 - max_single)
    ax = axes[1]
    for tg, color in group_colors.items():
        mask = df["target_group"] == tg
        ax.scatter(df.loc[mask, "headroom"], df.loc[mask, "R_ij"],
                   c=color, s=60, label=tg, edgecolor="black", lw=0.5, alpha=0.8)
        for _, r in df[mask].iterrows():
            ax.annotate(r["target_type"], (r["headroom"], r["R_ij"]),
                        fontsize=5, alpha=0.7)
    ax.set_xlabel("Activation headroom (1 − max single)")
    ax.set_ylabel("R_ij")
    ax.set_title("R_ij vs headroom\n(saturation hypothesis)")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.legend(fontsize=7)

    # Panel C: Nonlinear R_ij vs Linear R_ij
    ax = axes[2]
    for tg, color in group_colors.items():
        mask = df["target_group"] == tg
        ax.scatter(df.loc[mask, "R_ij_linear"], df.loc[mask, "R_ij"],
                   c=color, s=60, label=tg, edgecolor="black", lw=0.5, alpha=0.8)
        for _, r in df[mask].iterrows():
            ax.annotate(r["target_type"], (r["R_ij_linear"], r["R_ij"]),
                        fontsize=5, alpha=0.7)
    ax.set_xlabel("R_ij (linear activation)")
    ax.set_ylabel("R_ij (sigmoid activation)")
    ax.set_title("Linear vs nonlinear interaction")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.axvline(0, color="black", lw=0.5, ls=":")
    lim = max(abs(ax.get_xlim()[0]), abs(ax.get_xlim()[1]),
              abs(ax.get_ylim()[0]), abs(ax.get_ylim()[1]))
    ax.plot([-lim, lim], [-lim, lim], "k--", alpha=0.3)
    ax.legend(fontsize=7)

    fig.suptitle("Saturation analysis: Is destructive integration just activation ceiling?",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "saturation_analysis", "summary",
             description="Three-panel analysis testing whether R_ij is driven by sigmoid saturation. "
             "A: R_ij vs max single-channel activation. B: R_ij vs headroom (distance from saturation). "
             "C: Comparing R_ij under linear vs sigmoid activation.")


# =============================================================================
# 7. NONLINEARITY SWEEP — Does the effect persist across activation functions?
# =============================================================================

def analyse_nonlinearity_sweep(data):
    """
    Compute R_ij under different activation functions and parameters
    to test robustness and understand mechanism.
    """
    logger.info("=" * 60)
    logger.info("NONLINEARITY SWEEP")
    logger.info("=" * 60)

    W = data["W"]
    encoder = data["encoder"]
    enc = data["encoded_channels"]
    targets = data["targets"]

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    configs = [
        ("linear", {}),
        ("relu", {}),
        ("sigmoid_rectified_b1", {"beta": 1.0}),
        ("sigmoid_rectified_b2", {"beta": 2.0}),
        ("sigmoid_rectified_b5", {"beta": 5.0}),
        ("sigmoid_rectified_b10", {"beta": 10.0}),
        ("sigmoid_rectified_b20", {"beta": 20.0}),
        ("leaky_relu_01", {"alpha": 0.1}),
        ("leaky_relu_05", {"alpha": 0.5}),
    ]

    all_rows = []
    for name, params in configs:
        if name.startswith("sigmoid_rectified"):
            nonlin = "sigmoid_rectified"
        elif name.startswith("leaky_relu"):
            nonlin = "leaky_relu"
        else:
            nonlin = name

        prop = SignalPropagator(W, nonlin, params)
        x_23 = prop.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
        x_25 = prop.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
        x_both = prop.propagate(s_both, N_STEPS, sustained=SUSTAINED)

        for tg in ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]:
            if tg not in targets:
                continue
            for t in targets[tg]:
                if t not in encoder.type_to_idx:
                    continue
                idx = encoder.type_to_idx[t]
                all_rows.append({
                    "config": name,
                    "target_group": tg,
                    "target_type": t,
                    "A_ppk23": x_23[idx],
                    "A_ppk25": x_25[idx],
                    "A_both": x_both[idx],
                    "R_ij": x_both[idx] - x_23[idx] - x_25[idx],
                })

    df = pd.DataFrame(all_rows)
    df.to_csv(OUT_DIR / "summary" / "nonlinearity_sweep.csv", index=False)

    # ── Plot: R_ij across nonlinearities for focal neurons ──
    focal_list = []
    for tg, groups in FOCAL_NEURONS.items():
        for cat, neurons in groups.items():
            for n in neurons:
                focal_list.append((n, tg, cat))

    config_names = [c[0] for c in configs]
    n_focal = len(focal_list)

    fig, ax = plt.subplots(figsize=(14, max(5, n_focal * 0.4)))
    mat = np.zeros((n_focal, len(config_names)))
    for i, (neuron, tg, cat) in enumerate(focal_list):
        for j, cn in enumerate(config_names):
            row = df[(df["target_type"] == neuron) & (df["config"] == cn)]
            if len(row) > 0:
                mat[i, j] = row.iloc[0]["R_ij"]

    vmax = max(abs(mat.min()), abs(mat.max())) or 1e-6
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(config_names)))
    ax.set_xticklabels(config_names, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(n_focal))
    ylabels = [f"{n} ({c[0].upper()})" for n, _, c in focal_list]
    ax.set_yticklabels(ylabels, fontsize=8)

    # Annotate
    for i in range(n_focal):
        for j in range(len(config_names)):
            ax.text(j, i, f"{mat[i, j]:.3f}", ha="center", va="center", fontsize=6)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("R_ij")
    ax.set_title("PPK23 × PPK25 interaction across activation functions")
    ax.set_xlabel("Activation function / parameters")
    ax.set_ylabel("Target neuron")
    fig.tight_layout()
    save_fig(fig, "nonlinearity_sweep", "summary",
             description="R_ij for ppk23×ppk25 across different activation functions and parameters. "
             "Tests whether super/destructive classification is robust to model choices.")


# =============================================================================
# 8. PROPAGATION STEPS SWEEP — Sensitivity to path length
# =============================================================================

def analyse_steps_sweep(data):
    """
    Sweep n_steps from 1 to 6 and see how R_ij evolves.
    This reveals whether the interaction is a direct or polysynaptic effect.
    """
    logger.info("=" * 60)
    logger.info("PROPAGATION STEPS SWEEP")
    logger.info("=" * 60)

    W = data["W"]
    encoder = data["encoder"]
    enc = data["encoded_channels"]
    targets = data["targets"]

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    all_rows = []
    for n_steps in range(1, 7):
        prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
        x_23 = prop.propagate(s_ppk23, n_steps, sustained=SUSTAINED)
        x_25 = prop.propagate(s_ppk25, n_steps, sustained=SUSTAINED)
        x_both = prop.propagate(s_both, n_steps, sustained=SUSTAINED)

        for tg in ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]:
            if tg not in targets:
                continue
            for t in targets[tg]:
                if t not in encoder.type_to_idx:
                    continue
                idx = encoder.type_to_idx[t]
                all_rows.append({
                    "n_steps": n_steps,
                    "target_group": tg,
                    "target_type": t,
                    "R_ij": x_both[idx] - x_23[idx] - x_25[idx],
                })

    df = pd.DataFrame(all_rows)
    df.to_csv(OUT_DIR / "summary" / "steps_sweep.csv", index=False)

    # Plot: line plots for focal neurons
    focal_list = []
    for tg, groups in FOCAL_NEURONS.items():
        for cat, neurons in groups.items():
            for n in neurons:
                focal_list.append((n, tg, cat))

    fig, ax = plt.subplots(figsize=(10, 6))
    for neuron, tg, cat in focal_list:
        df_n = df[df["target_type"] == neuron]
        if df_n.empty:
            continue
        color = "#E41A1C" if cat == "super" else "#377EB8"
        ls = "-" if cat == "super" else "--"
        ax.plot(df_n["n_steps"], df_n["R_ij"], f"o{ls}", color=color,
                label=f"{neuron} ({cat})", lw=1.5, ms=5)

    ax.set_xlabel("Number of propagation steps")
    ax.set_ylabel("R_ij (ppk23 × ppk25)")
    ax.set_title("PPK23 × PPK25 interaction vs propagation depth")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.legend(fontsize=7, ncol=2, loc="best")
    ax.set_xticks(range(1, 7))
    fig.tight_layout()
    save_fig(fig, "steps_sweep", "summary",
             description="R_ij for ppk23×ppk25 as a function of propagation steps (1-6). "
             "Red/solid = super integration, Blue/dashed = destructive. "
             "Reveals whether interaction emerges at specific pathway depths.")


# =============================================================================
# 9. COMPREHENSIVE SUMMARY — All R_ij for all neurons across target groups
# =============================================================================

def analyse_comprehensive_summary(data):
    """
    Create a comprehensive summary of ppk23×ppk25 R_ij across ALL target neurons
    in all four groups, highlighting the super vs destructive pattern.
    """
    logger.info("=" * 60)
    logger.info("COMPREHENSIVE SUMMARY")
    logger.info("=" * 60)

    W = data["W"]
    encoder = data["encoder"]
    enc = data["encoded_channels"]
    targets = data["targets"]
    nt_map = data["nt_map"]
    type_to_nt = dict(zip(nt_map["type"], nt_map["consensus_nt"]))
    type_to_inhib = dict(zip(nt_map["type"], nt_map["is_inhibitory"]))

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
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
            rows.append({
                "target_group": tg,
                "target_type": t,
                "A_ppk23": x_23[idx],
                "A_ppk25": x_25[idx],
                "A_both": x_both[idx],
                "R_ij": x_both[idx] - x_23[idx] - x_25[idx],
                "nt": type_to_nt.get(t, "unknown"),
                "is_inhibitory": type_to_inhib.get(t, False),
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "summary" / "ppk23_ppk25_Rij_all_targets.csv", index=False)

    # ── Plot: Waterfall plot of R_ij sorted within each group ──
    group_colors = {
        "aspf": "#E41A1C",
        "aspg": "#377EB8",
        "PPN1_downstream": "#FF7F00",
        "vAB3_downstream": "#4DAF4A",
    }

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    for ax, tg in zip(axes.ravel(), ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]):
        df_tg = df[df["target_group"] == tg].sort_values("R_ij")
        if df_tg.empty:
            continue
        colors = ["#E41A1C" if r > 0 else "#377EB8" for r in df_tg["R_ij"]]
        bars = ax.barh(range(len(df_tg)), df_tg["R_ij"], color=colors,
                       edgecolor="black", lw=0.5)
        labels = []
        for _, r in df_tg.iterrows():
            nt_tag = f" [{r['nt']}" + (" INH" if r["is_inhibitory"] else " EXC") + "]"
            labels.append(r["target_type"] + nt_tag)
        ax.set_yticks(range(len(df_tg)))
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("R_ij (ppk23 × ppk25)")
        ax.set_title(f"{tg}", fontweight="bold", color=group_colors[tg])
        ax.axvline(0, color="black", lw=0.8)

    fig.suptitle("PPK23 × PPK25 interaction across all target neurons",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "ppk23_ppk25_Rij_waterfall", "summary",
             description="Waterfall plots of R_ij for ppk23×ppk25 across all neurons in each target group. "
             "Red = super-additive (synergy), Blue = sub-additive (destructive). "
             "Sorted from most destructive to most synergistic within each group.")

    # ── Plot: R_ij vs A(ppk23)/A(ppk25) ratio ──
    df["ratio_23_25"] = df["A_ppk23"] / df["A_ppk25"].replace(0, np.nan)
    df_plot = df.dropna(subset=["ratio_23_25"])

    fig, ax = plt.subplots(figsize=(10, 7))
    for tg, color in group_colors.items():
        mask = df_plot["target_group"] == tg
        ax.scatter(df_plot.loc[mask, "ratio_23_25"], df_plot.loc[mask, "R_ij"],
                   c=color, s=80, label=tg, edgecolor="black", lw=0.5, alpha=0.8)
        for _, r in df_plot[mask].iterrows():
            ax.annotate(r["target_type"], (r["ratio_23_25"], r["R_ij"]),
                        fontsize=6, alpha=0.7)
    ax.set_xlabel("A(ppk23) / A(ppk25)")
    ax.set_ylabel("R_ij")
    ax.set_title("Does channel selectivity predict interaction mode?")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.axvline(1, color="gray", lw=0.5, ls=":", alpha=0.5)
    ax.legend(fontsize=8)
    fig.tight_layout()
    save_fig(fig, "ppk23_ppk25_selectivity_vs_Rij", "summary",
             description="Scatter of R_ij vs the ratio A(ppk23)/A(ppk25) for each target neuron. "
             "Tests whether neurons that respond more symmetrically to both channels show "
             "different interaction patterns.")

    # ── Plot: sign of individual channels vs R_ij ──
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ax = axes[0]
    for tg, color in group_colors.items():
        mask = df["target_group"] == tg
        ax.scatter(df.loc[mask, "A_ppk23"], df.loc[mask, "R_ij"],
                   c=color, s=60, label=tg, edgecolor="black", lw=0.5, alpha=0.8)
    ax.set_xlabel("A(ppk23)")
    ax.set_ylabel("R_ij")
    ax.set_title("PPK23 response vs interaction")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.axvline(0, color="black", lw=0.5, ls=":")
    ax.legend(fontsize=7)

    ax = axes[1]
    for tg, color in group_colors.items():
        mask = df["target_group"] == tg
        ax.scatter(df.loc[mask, "A_ppk25"], df.loc[mask, "R_ij"],
                   c=color, s=60, label=tg, edgecolor="black", lw=0.5, alpha=0.8)
    ax.set_xlabel("A(ppk25)")
    ax.set_ylabel("R_ij")
    ax.set_title("PPK25 response vs interaction")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.axvline(0, color="black", lw=0.5, ls=":")
    ax.legend(fontsize=7)

    fig.suptitle("Single-channel activation vs pairwise interaction", fontsize=13, fontweight="bold")
    fig.tight_layout()
    save_fig(fig, "ppk23_ppk25_activation_vs_Rij", "summary",
             description="R_ij vs individual channel activations. "
             "Tests whether high single-channel responders show more destructive interaction (saturation).")


# =============================================================================
# 10. SIGN-FLIPPING EXPERIMENT — What if PPK23 or PPK25 inputs were inhibitory?
# =============================================================================

def analyse_sign_manipulation(data):
    """
    Counterfactual: What happens to R_ij if we flip the sign of
    ppk23 or ppk25 channel neurons (make them inhibitory)?
    This tests whether the interaction depends on the excitatory nature of the inputs.
    """
    logger.info("=" * 60)
    logger.info("SIGN MANIPULATION")
    logger.info("=" * 60)

    W = data["W"]
    encoder = data["encoder"]
    enc = data["encoded_channels"]
    targets = data["targets"]

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]

    ppk23_indices = encoder.get_indices(data["channels"]["ppk23"])
    ppk25_indices = encoder.get_indices(data["channels"]["ppk25"])

    configs = {
        "baseline": (s_ppk23, s_ppk25),
        "ppk23_inhibitory": (-s_ppk23, s_ppk25),
        "ppk25_inhibitory": (s_ppk23, -s_ppk25),
        "both_inhibitory": (-s_ppk23, -s_ppk25),
        "ppk23_half": (0.5 * s_ppk23, s_ppk25),
        "ppk25_half": (s_ppk23, 0.5 * s_ppk25),
        "ppk23_double": (2.0 * s_ppk23, s_ppk25),
        "ppk25_double": (s_ppk23, 2.0 * s_ppk25),
    }

    all_rows = []
    for config_name, (s1, s2) in configs.items():
        s_combined = s1 + s2

        prop = SignalPropagator(W, NONLINEARITY, ACT_PARAMS)
        x_1 = prop.propagate(s1, N_STEPS, sustained=SUSTAINED)
        x_2 = prop.propagate(s2, N_STEPS, sustained=SUSTAINED)
        x_both = prop.propagate(s_combined, N_STEPS, sustained=SUSTAINED)

        for tg in ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]:
            if tg not in targets:
                continue
            for t in targets[tg]:
                if t not in encoder.type_to_idx:
                    continue
                idx = encoder.type_to_idx[t]
                all_rows.append({
                    "config": config_name,
                    "target_group": tg,
                    "target_type": t,
                    "A_ch1": x_1[idx],
                    "A_ch2": x_2[idx],
                    "A_both": x_both[idx],
                    "R_ij": x_both[idx] - x_1[idx] - x_2[idx],
                })

    df = pd.DataFrame(all_rows)
    df.to_csv(OUT_DIR / "summary" / "sign_manipulation.csv", index=False)

    # ── Plot: heatmap of R_ij across manipulations for focal neurons ──
    focal_list = []
    for tg, groups in FOCAL_NEURONS.items():
        for cat, neurons in groups.items():
            for n in neurons:
                focal_list.append((n, tg, cat))

    config_names = list(configs.keys())
    mat = np.zeros((len(focal_list), len(config_names)))
    for i, (neuron, tg, cat) in enumerate(focal_list):
        for j, cn in enumerate(config_names):
            row = df[(df["target_type"] == neuron) & (df["config"] == cn)]
            if len(row) > 0:
                mat[i, j] = row.iloc[0]["R_ij"]

    vmax = max(abs(mat.min()), abs(mat.max())) or 1e-6
    fig, ax = plt.subplots(figsize=(14, max(5, len(focal_list) * 0.4)))
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(len(config_names)))
    ax.set_xticklabels(config_names, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(focal_list)))
    ylabels = [f"{n} ({c[0].upper()})" for n, _, c in focal_list]
    ax.set_yticklabels(ylabels, fontsize=8)

    for i in range(len(focal_list)):
        for j in range(len(config_names)):
            ax.text(j, i, f"{mat[i, j]:.3f}", ha="center", va="center", fontsize=6)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("R_ij")
    ax.set_title("PPK23 × PPK25 interaction under input manipulations")
    fig.tight_layout()
    save_fig(fig, "sign_manipulation", "summary",
             description="R_ij under different input manipulations: sign-flipping, halving, doubling. "
             "Tests whether the interaction mode depends on input sign and magnitude.")


# =============================================================================
# MAIN
# =============================================================================

def main():
    logger.info("=" * 70)
    logger.info("PPK23 × PPK25 INTERACTION INVESTIGATION")
    logger.info("=" * 70)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    data = load_everything()
    logger.info("Data loaded successfully.")

    # Run all analyses
    analyse_trajectories(data)
    analyse_pathway_decomposition(data)
    analyse_ablations(data)
    analyse_connectivity(data)
    analyse_saturation(data)
    analyse_nonlinearity_sweep(data)
    analyse_steps_sweep(data)
    analyse_comprehensive_summary(data)
    analyse_sign_manipulation(data)

    logger.info("=" * 70)
    logger.info("INVESTIGATION COMPLETE")
    logger.info("All results saved to: %s", OUT_DIR)
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
