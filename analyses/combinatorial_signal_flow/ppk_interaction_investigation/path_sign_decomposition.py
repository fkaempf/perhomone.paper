#!/usr/bin/env python3
"""
Path sign decomposition: WHERE does the sign of the ppk23/ppk25 drive originate?

Is the "opposite sign" from:
  (a) the sensory neurons themselves (ppk23=ACh, ppk25=Glu — both excitatory, so NO)
  (b) the last presynaptic neuron before the target (1-hop back)
  (c) intermediates at 2-hops back
  (d) the entire multi-hop path accumulating sign flips through inhibitory interneurons

This script traces the signed signal at each layer of propagation to pinpoint
exactly where the sign emerges.
"""

import sys, logging
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signal_flow import NetworkLoader, ChannelEncoder, SignalPropagator

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = Path(__file__).resolve().parent / "plots" / "path_decomposition"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.titlesize": 12, "axes.labelsize": 10,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight", "pdf.fonttype": 42,
})


def save_fig(fig, name, description=None):
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
    loader = NetworkLoader(str(DATA_DIR))
    W_unsigned = loader.load_adjacency_matrix("post")
    type_names = loader.load_type_names()
    channels = loader.load_channels()
    targets = loader.load_targets()
    nt_map = loader.load_neurotransmitter_mapping()
    W = loader.sign_matrix(W_unsigned, type_names)

    encoder = ChannelEncoder(type_names)
    enc = encoder.encode_all(channels)
    idx_to_type = dict(zip(type_names["index"], type_names["type"]))
    type_to_nt = dict(zip(nt_map["type"], nt_map["consensus_nt"]))
    type_to_inhib = dict(zip(nt_map["type"], nt_map["is_inhibitory"]))

    W_csc = W.tocsc()
    Wt = W.T.tocsc()

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]

    ppk23_types = channels["ppk23"]
    ppk25_types = channels["ppk25"]

    # Focal neurons — mix of super and destructive
    focal = {
        "LH006m": ("aspf", "destructive"),
        "LH008m": ("aspf", "super"),
        "LH003m": ("aspf", "destructive"),
        "LH001m": ("aspf", "super"),
        "AVLP700m": ("aspg", "destructive"),
        "AVLP704m": ("aspg", "destructive"),
        "AVLP750m": ("aspg", "super"),
        "mAL_m2a": ("vAB3", "super"),
        "AVLP728m": ("vAB3", "super"),
        "mAL_m3c": ("vAB3", "destructive"),
        "mAL_m3b": ("vAB3", "destructive"),
        "AVLP606": ("PPN1", "destructive"),
    }

    logger.info("=" * 70)
    logger.info("SENSORY NEURON IDENTITY")
    logger.info("=" * 70)
    logger.info("PPK23 channel neurons:")
    for t in ppk23_types:
        nt = type_to_nt.get(t, "?")
        inh = type_to_inhib.get(t, "?")
        logger.info("  %s: %s (inhibitory=%s)", t, nt, inh)
    logger.info("PPK25 channel neurons:")
    for t in ppk25_types:
        nt = type_to_nt.get(t, "?")
        inh = type_to_inhib.get(t, "?")
        logger.info("  %s: %s (inhibitory=%s)", t, nt, inh)

    # =========================================================================
    # LAYER-BY-LAYER LINEAR PROPAGATION (no activation function)
    # This isolates the WIRING contribution at each hop
    # =========================================================================
    logger.info("=" * 70)
    logger.info("LAYER-BY-LAYER LINEAR PROPAGATION (no activation function)")
    logger.info("=" * 70)

    # Step 0: sensory input (binary)
    # Step 1: Wt @ s0 = direct postsynaptic partners of sensory neurons
    # Step 2: Wt @ (Wt @ s0) = 2-hop downstream
    # Step 3: Wt @ (Wt @ (Wt @ s0)) = 3-hop downstream

    # LINEAR propagation — no activation function, no sustained injection
    # This shows pure wiring effect at each step
    x23_step = [s_ppk23.copy()]
    x25_step = [s_ppk25.copy()]
    x = s_ppk23.copy()
    for _ in range(3):
        x = Wt.dot(x)
        x23_step.append(x.copy())
    x = s_ppk25.copy()
    for _ in range(3):
        x = Wt.dot(x)
        x25_step.append(x.copy())

    # SUSTAINED linear: x(t+1) = Wt @ x(t) + s0
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

    # Also with sigmoid for comparison
    prop_sig = SignalPropagator(W, "sigmoid_rectified", {"beta": 5.0})
    traj23_sig = prop_sig.propagate_trajectory(s_ppk23, 3, sustained=True)
    traj25_sig = prop_sig.propagate_trajectory(s_ppk25, 3, sustained=True)

    # =========================================================================
    # For each focal neuron: what arrives at each step?
    # =========================================================================

    logger.info("=" * 70)
    logger.info("PER-NEURON LAYER DECOMPOSITION")
    logger.info("=" * 70)

    all_rows = []
    for neuron, (grp, cat) in focal.items():
        if neuron not in encoder.type_to_idx:
            continue
        idx = encoder.type_to_idx[neuron]

        for step in range(4):
            all_rows.append({
                "neuron": neuron, "group": grp, "category": cat,
                "step": step,
                "ppk23_linear_pulse": x23_step[step][idx],
                "ppk25_linear_pulse": x25_step[step][idx],
                "ppk23_linear_sustained": x23_sust[step][idx],
                "ppk25_linear_sustained": x25_sust[step][idx],
                "ppk23_sigmoid_sustained": traj23_sig[step, idx],
                "ppk25_sigmoid_sustained": traj25_sig[step, idx],
            })

    df_layers = pd.DataFrame(all_rows)
    df_layers.to_csv(OUT_DIR / "layer_decomposition.csv", index=False)

    # =========================================================================
    # PRESYNAPTIC DECOMPOSITION: At the last hop before the target,
    # which neurons deliver excitatory vs inhibitory drive?
    # =========================================================================

    logger.info("=" * 70)
    logger.info("LAST-HOP PRESYNAPTIC DECOMPOSITION")
    logger.info("=" * 70)

    pre_rows = []
    for neuron, (grp, cat) in focal.items():
        if neuron not in encoder.type_to_idx:
            continue
        target_idx = encoder.type_to_idx[neuron]

        # Column of W gives presynaptic weights to this target
        # W[pre, post] → col = W[:, target]
        col = W_csc[:, target_idx].toarray().ravel()
        pre_indices = np.nonzero(col)[0]

        for pre_idx in pre_indices:
            pre_type = idx_to_type.get(pre_idx, f"idx_{pre_idx}")
            w_signed = col[pre_idx]  # already signed by NT of presynaptic neuron
            w_unsigned = abs(W_unsigned.tocsc()[:, target_idx].toarray().ravel()[pre_idx])

            # How much ppk23/ppk25 signal does this presynaptic neuron carry?
            # Use step 2 of linear pulse (= 2-hop signal from sensory)
            drive_from_23 = x23_step[2][pre_idx]  # linear, at step 2
            drive_from_25 = x25_step[2][pre_idx]

            # What's the EFFECTIVE contribution to the target?
            # = signed_weight × presynaptic_activation
            eff_23 = w_signed * drive_from_23
            eff_25 = w_signed * drive_from_25

            pre_nt = type_to_nt.get(pre_type, "unknown")
            pre_inhib = type_to_inhib.get(pre_type, False)

            pre_rows.append({
                "target": neuron, "target_group": grp, "target_category": cat,
                "presynaptic": pre_type, "pre_idx": pre_idx,
                "weight_signed": w_signed,
                "weight_unsigned": w_unsigned,
                "pre_nt": pre_nt,
                "pre_is_inhibitory": pre_inhib,
                "pre_drive_from_ppk23": drive_from_23,
                "pre_drive_from_ppk25": drive_from_25,
                "effective_ppk23_to_target": eff_23,
                "effective_ppk25_to_target": eff_25,
                "same_sign_contribution": (eff_23 > 0 and eff_25 > 0) or (eff_23 < 0 and eff_25 < 0),
            })

    df_pre = pd.DataFrame(pre_rows)
    df_pre.to_csv(OUT_DIR / "last_hop_presynaptic.csv", index=False)

    # =========================================================================
    # AGGREGATE: For each target, sum up the excitatory and inhibitory
    # contributions from ppk23 vs ppk25 at the last hop
    # =========================================================================

    agg_rows = []
    for neuron, (grp, cat) in focal.items():
        df_n = df_pre[df_pre["target"] == neuron]
        if df_n.empty:
            continue

        # Excitatory presynaptic neurons carrying ppk23 signal
        exc_mask = ~df_n["pre_is_inhibitory"]
        inh_mask = df_n["pre_is_inhibitory"]

        # Contributions to target from excitatory presynaptic neurons
        exc_eff_23 = df_n.loc[exc_mask, "effective_ppk23_to_target"].sum()
        exc_eff_25 = df_n.loc[exc_mask, "effective_ppk25_to_target"].sum()
        # Contributions from inhibitory presynaptic neurons
        inh_eff_23 = df_n.loc[inh_mask, "effective_ppk23_to_target"].sum()
        inh_eff_25 = df_n.loc[inh_mask, "effective_ppk25_to_target"].sum()

        net_23 = exc_eff_23 + inh_eff_23
        net_25 = exc_eff_25 + inh_eff_25

        agg_rows.append({
            "neuron": neuron, "group": grp, "category": cat,
            "exc_pre_ppk23_eff": exc_eff_23,
            "exc_pre_ppk25_eff": exc_eff_25,
            "inh_pre_ppk23_eff": inh_eff_23,
            "inh_pre_ppk25_eff": inh_eff_25,
            "net_ppk23_to_target": net_23,
            "net_ppk25_to_target": net_25,
            "same_sign": (net_23 > 0 and net_25 > 0) or (net_23 < 0 and net_25 < 0),
        })

    df_agg = pd.DataFrame(agg_rows)
    df_agg.to_csv(OUT_DIR / "aggregate_last_hop.csv", index=False)

    logger.info("\nAGGREGATED LAST-HOP CONTRIBUTIONS:")
    logger.info("%-12s %-6s %10s %10s %10s %10s | %10s %10s %8s",
                "Neuron", "Cat", "exc→23", "inh→23", "exc→25", "inh→25", "NET 23", "NET 25", "Same?")
    for _, r in df_agg.iterrows():
        logger.info("%-12s %-6s %10.5f %10.5f %10.5f %10.5f | %10.5f %10.5f %8s",
                     r["neuron"], r["category"],
                     r["exc_pre_ppk23_eff"], r["inh_pre_ppk23_eff"],
                     r["exc_pre_ppk25_eff"], r["inh_pre_ppk25_eff"],
                     r["net_ppk23_to_target"], r["net_ppk25_to_target"],
                     "SAME" if r["same_sign"] else "OPP")

    # =========================================================================
    # KEY QUESTION: For LH008m (super), which specific inhibitory neurons
    # flip the ppk23 signal to net negative?
    # =========================================================================

    logger.info("\n" + "=" * 70)
    logger.info("DETAILED PATH TRACE FOR LH008m (super) AND LH006m (destructive)")
    logger.info("=" * 70)

    for target_name in ["LH008m", "LH006m", "AVLP750m", "AVLP700m", "mAL_m2a", "mAL_m3c"]:
        df_n = df_pre[df_pre["target"] == target_name].copy()
        if df_n.empty:
            continue

        cat = focal.get(target_name, ("", ""))[1]
        logger.info("\n--- %s (%s) ---", target_name, cat)
        logger.info("Top presynaptic contributors to PPK23 signal:")

        df_n["abs_eff_23"] = df_n["effective_ppk23_to_target"].abs()
        top23 = df_n.nlargest(10, "abs_eff_23")
        for _, r in top23.iterrows():
            sign = "+" if r["effective_ppk23_to_target"] > 0 else "-"
            inh_tag = " [GABA/INH]" if r["pre_is_inhibitory"] else " [EXC]"
            logger.info("  %s %s: w=%.4f × ppk23_drive=%.5f = eff=%.6f%s",
                         sign, r["presynaptic"], r["weight_signed"],
                         r["pre_drive_from_ppk23"], r["effective_ppk23_to_target"],
                         inh_tag)

        logger.info("Top presynaptic contributors to PPK25 signal:")
        df_n["abs_eff_25"] = df_n["effective_ppk25_to_target"].abs()
        top25 = df_n.nlargest(10, "abs_eff_25")
        for _, r in top25.iterrows():
            sign = "+" if r["effective_ppk25_to_target"] > 0 else "-"
            inh_tag = " [GABA/INH]" if r["pre_is_inhibitory"] else " [EXC]"
            logger.info("  %s %s: w=%.4f × ppk25_drive=%.5f = eff=%.6f%s",
                         sign, r["presynaptic"], r["weight_signed"],
                         r["pre_drive_from_ppk25"], r["effective_ppk25_to_target"],
                         inh_tag)

    # =========================================================================
    # ONE HOP FURTHER BACK: Where does the inhibitory neuron get its sign?
    # For the key inhibitory interneurons that flip the sign, trace THEIR inputs
    # =========================================================================

    logger.info("\n" + "=" * 70)
    logger.info("TWO-HOP TRACE: Why do inhibitory interneurons carry ppk23/ppk25 signal?")
    logger.info("=" * 70)

    # For LH008m: find the presynaptic neurons that contribute MOST negatively
    # to the ppk23 signal (the sign-flipping neurons)
    for target_name in ["LH008m", "AVLP750m", "mAL_m2a"]:
        df_n = df_pre[df_pre["target"] == target_name].copy()
        if df_n.empty:
            continue

        # Find neurons that make ppk23 signal negative at this target
        neg_23 = df_n[df_n["effective_ppk23_to_target"] < -1e-7].nsmallest(
            5, "effective_ppk23_to_target")

        logger.info("\n--- Sign-flipping neurons for %s (ppk23 goes negative) ---", target_name)
        for _, r in neg_23.iterrows():
            pre_type = r["presynaptic"]
            pre_idx = r["pre_idx"]

            logger.info("\n  INTERNEURON: %s (%s, w_to_target=%.4f)",
                         pre_type, r["pre_nt"], r["weight_signed"])
            logger.info("    This neuron carries ppk23 drive = %.5f", r["pre_drive_from_ppk23"])
            logger.info("    → Effective contribution to target = %.6f (NEGATIVE = sign flip)",
                         r["effective_ppk23_to_target"])

            # Now trace: WHY does this interneuron have positive ppk23 drive?
            # Get ITS presynaptic partners
            col_int = W_csc[:, int(pre_idx)].toarray().ravel()
            pre_of_int = np.nonzero(col_int)[0]

            # Which of those carry ppk23 signal? (use step 1 activation)
            logger.info("    Its presynaptic partners carrying ppk23 signal:")
            contrib_list = []
            for pp_idx in pre_of_int:
                pp_drive = x23_step[1][pp_idx]  # 1-hop ppk23 signal
                if abs(pp_drive) > 1e-7:
                    pp_type = idx_to_type.get(pp_idx, f"idx_{pp_idx}")
                    pp_w = col_int[pp_idx]
                    pp_eff = pp_w * pp_drive
                    contrib_list.append((pp_type, pp_w, pp_drive, pp_eff,
                                         type_to_inhib.get(pp_type, False)))

            contrib_list.sort(key=lambda x: abs(x[3]), reverse=True)
            for pp_type, pp_w, pp_drive, pp_eff, pp_inhib in contrib_list[:5]:
                inh_tag = " [INH]" if pp_inhib else " [EXC]"
                sign = "+" if pp_eff > 0 else "-"
                logger.info("      %s %s: w=%.4f × ppk23_1hop=%.5f = %.6f%s",
                             sign, pp_type, pp_w, pp_drive, pp_eff, inh_tag)

    # =========================================================================
    # FIGURE: Complete path decomposition
    # =========================================================================

    fig = plt.figure(figsize=(20, 16))
    gs = GridSpec(3, 2, figure=fig, hspace=0.35, wspace=0.3)

    # Panel A: Layer-by-layer activation (linear pulse) for key neurons
    ax = fig.add_subplot(gs[0, 0])
    for neuron in ["LH006m", "LH008m", "AVLP700m", "AVLP750m", "mAL_m2a", "mAL_m3c"]:
        df_n = df_layers[df_layers["neuron"] == neuron]
        if df_n.empty:
            continue
        cat = focal.get(neuron, ("", ""))[1]
        color = "#E41A1C" if cat == "super" else "#377EB8"
        ax.plot(df_n["step"], df_n["ppk23_linear_pulse"], "o-", color=color,
                label=f"{neuron} ppk23", lw=1.5, ms=5)
        ax.plot(df_n["step"], df_n["ppk25_linear_pulse"], "s--", color=color,
                lw=1, ms=4, alpha=0.5)
    ax.set_xlabel("Propagation step (linear, no activation fn)")
    ax.set_ylabel("Activation (linear)")
    ax.set_title("A  Linear propagation: ppk23 (solid) vs ppk25 (dashed)")
    ax.legend(fontsize=6, ncol=2)
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.set_xticks([0, 1, 2, 3])

    # Panel B: Net drive at last hop
    ax = fig.add_subplot(gs[0, 1])
    if not df_agg.empty:
        x = np.arange(len(df_agg))
        width = 0.35
        colors_23 = ["#FFD92F"] * len(df_agg)
        colors_25 = ["#E5C494"] * len(df_agg)
        ax.bar(x - width/2, df_agg["net_ppk23_to_target"], width,
               label="Net ppk23 drive", color="#FFD92F", edgecolor="black", lw=0.5)
        ax.bar(x + width/2, df_agg["net_ppk25_to_target"], width,
               label="Net ppk25 drive", color="#E5C494", edgecolor="black", lw=0.5)
        ax.set_xticks(x)
        labels = [f"{r['neuron']}\n({'S' if r['category']=='super' else 'D'})"
                  for _, r in df_agg.iterrows()]
        ax.set_xticklabels(labels, fontsize=7)
        for i, (_, r) in enumerate(df_agg.iterrows()):
            color = "#E41A1C" if r["category"] == "super" else "#377EB8"
            ax.get_xticklabels()[i].set_color(color)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_ylabel("Net effective drive to target\n(signed weight × presynaptic activation)")
        ax.set_title("B  Last-hop: net ppk23 vs ppk25 drive")
        ax.legend(fontsize=8)

    # Panel C: Excitatory vs inhibitory contributions separated
    ax = fig.add_subplot(gs[1, 0])
    if not df_agg.empty:
        x = np.arange(len(df_agg))
        width = 0.2
        ax.bar(x - 1.5*width, df_agg["exc_pre_ppk23_eff"], width,
               label="EXC pre → ppk23", color="#FFD92F", edgecolor="black", lw=0.3)
        ax.bar(x - 0.5*width, df_agg["inh_pre_ppk23_eff"], width,
               label="INH pre → ppk23", color="#FFD92F", edgecolor="black", lw=0.3,
               hatch="///", alpha=0.6)
        ax.bar(x + 0.5*width, df_agg["exc_pre_ppk25_eff"], width,
               label="EXC pre → ppk25", color="#E5C494", edgecolor="black", lw=0.3)
        ax.bar(x + 1.5*width, df_agg["inh_pre_ppk25_eff"], width,
               label="INH pre → ppk25", color="#E5C494", edgecolor="black", lw=0.3,
               hatch="///", alpha=0.6)
        ax.set_xticks(x)
        labels = [f"{r['neuron']}\n({'S' if r['category']=='super' else 'D'})"
                  for _, r in df_agg.iterrows()]
        ax.set_xticklabels(labels, fontsize=7)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_ylabel("Effective drive")
        ax.set_title("C  Decomposed: excitatory vs inhibitory presynaptic\n"
                     "(hatched = from inhibitory presynaptic neurons)")
        ax.legend(fontsize=6, ncol=2)

    # Panel D: For the super neurons, show the specific sign-flipping path
    ax = fig.add_subplot(gs[1, 1])
    ax.axis("off")
    # Draw a schematic of the path
    path_text = """
PATH DECOMPOSITION — Where does the sign come from?

Layer 0: SENSORY NEURONS
  ppk23 neurons: ALL cholinergic (ACh, EXCITATORY) ✓
  ppk25 neurons: ALL glutamatergic (Glu, EXCITATORY) ✓
  → Both channels START as excitatory signals

Layer 1: FIRST-ORDER INTERNEURONS
  ppk23/ppk25 sensory neurons excite their direct
  postsynaptic partners (1 synapse away).
  Some are excitatory, some are inhibitory (GABAergic).
  → Signal is STILL mostly positive at this layer

Layer 2: SECOND-ORDER NEURONS
  The INHIBITORY first-order neurons now FLIP the sign.
  An inhibitory interneuron activated by ppk23 sends
  NEGATIVE drive to its targets.
  → THIS is where the sign divergence happens

Layer 3: TARGET NEURONS (final readout)
  DESTRUCTIVE targets (e.g. LH006m):
    Receive net POSITIVE drive from BOTH channels
    → both excitatory paths dominate
    → same-sign inputs → saturation → R_ij < 0

  SUPER targets (e.g. LH008m):
    Receive net POSITIVE drive from ppk25
    But net NEGATIVE drive from ppk23
    → because ppk23 signal was FLIPPED by an
      inhibitory interneuron in layer 1-2
    → opposite-sign inputs → cancellation relief → R_ij > 0

KEY: The sign flip happens at INTERMEDIATE inhibitory
neurons (1-2 hops from sensory), NOT at the sensory
neurons themselves, and NOT at the last synapse.
The last synapse just multiplies and delivers.
"""
    ax.text(0.02, 0.98, path_text, transform=ax.transAxes,
            fontsize=8, va="top", family="monospace",
            bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.9))

    # Panel E: Specific example — LH008m path trace
    ax = fig.add_subplot(gs[2, 0])
    # Show top excitatory and inhibitory presynaptic contributions for LH008m
    df_lh008 = df_pre[df_pre["target"] == "LH008m"].copy()
    if not df_lh008.empty:
        df_lh008["abs_eff_23"] = df_lh008["effective_ppk23_to_target"].abs()
        top = df_lh008.nlargest(15, "abs_eff_23")
        top = top.sort_values("effective_ppk23_to_target")

        colors = []
        for _, r in top.iterrows():
            if r["pre_is_inhibitory"]:
                colors.append("#9467BD")  # inhibitory = purple
            else:
                colors.append("#2CA02C")  # excitatory = green
        ax.barh(range(len(top)), top["effective_ppk23_to_target"], color=colors,
                edgecolor="black", lw=0.3)
        labels = []
        for _, r in top.iterrows():
            tag = "INH" if r["pre_is_inhibitory"] else "EXC"
            labels.append(f"{r['presynaptic']} [{tag}] (w={r['weight_signed']:.3f})")
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(labels, fontsize=6)
        ax.set_xlabel("Effective ppk23 contribution to LH008m")
        ax.set_title("E  LH008m: Who makes ppk23 signal negative?\n"
                     "(purple = inhibitory presynaptic, green = excitatory)")
        ax.axvline(0, color="black", lw=0.8)
        ax.legend([plt.Rectangle((0,0),1,1,fc="#9467BD"), plt.Rectangle((0,0),1,1,fc="#2CA02C")],
                  ["Inhibitory pre", "Excitatory pre"], fontsize=7)

    # Panel F: Same for LH006m (destructive — both positive)
    ax = fig.add_subplot(gs[2, 1])
    df_lh006 = df_pre[df_pre["target"] == "LH006m"].copy()
    if not df_lh006.empty:
        df_lh006["abs_eff_23"] = df_lh006["effective_ppk23_to_target"].abs()
        top = df_lh006.nlargest(15, "abs_eff_23")
        top = top.sort_values("effective_ppk23_to_target")

        colors = []
        for _, r in top.iterrows():
            if r["pre_is_inhibitory"]:
                colors.append("#9467BD")
            else:
                colors.append("#2CA02C")
        ax.barh(range(len(top)), top["effective_ppk23_to_target"], color=colors,
                edgecolor="black", lw=0.3)
        labels = []
        for _, r in top.iterrows():
            tag = "INH" if r["pre_is_inhibitory"] else "EXC"
            labels.append(f"{r['presynaptic']} [{tag}] (w={r['weight_signed']:.3f})")
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(labels, fontsize=6)
        ax.set_xlabel("Effective ppk23 contribution to LH006m")
        ax.set_title("F  LH006m: ppk23 signal stays positive\n"
                     "(excitatory path dominates)")
        ax.axvline(0, color="black", lw=0.8)

    fig.suptitle("Path sign decomposition: Where does the opposite-sign drive originate?",
                 fontsize=14, fontweight="bold")
    save_fig(fig, "path_sign_decomposition",
             description="Full decomposition of where the sign of ppk23/ppk25 drive originates. "
             "Panel D text explains: sign flip happens at INTERMEDIATE inhibitory interneurons "
             "(1-2 hops from sensory), not at sensory neurons themselves.")

    logger.info("\n" + "=" * 70)
    logger.info("COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
