#!/usr/bin/env python3
"""
Circuit diagrams: for each target neuron in aspf, aspg, PPN1_downstream,
and vAB3_downstream, draw a schematic showing the key signal paths from
ppk23/ppk25 sensory neurons through intermediaries to the target,
making it visually clear why the neuron shows super-additive or
destructive integration.
"""

import json, sys, logging
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signal_flow import NetworkLoader, ChannelEncoder, SignalPropagator

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = Path(__file__).resolve().parent / "plots" / "circuit_diagrams"

TARGET_GROUPS = ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]
GROUP_SHORT = {
    "aspf": "aspf", "aspg": "aspg",
    "PPN1_downstream": "PPN1", "vAB3_downstream": "vAB3",
}

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 12, "axes.labelsize": 10,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight", "pdf.fonttype": 42,
})

# Colors
COL_EXC = "#2196F3"       # blue — excitatory arrow
COL_INH = "#E53935"       # red — inhibitory arrow
COL_PPK23 = "#FFC107"     # amber — ppk23 sensory pool
COL_PPK25 = "#8D6E63"     # brown — ppk25 sensory pool
COL_SUPER = "#E53935"     # red border for super target
COL_DESTR = "#1565C0"     # blue border for destructive target
COL_EXC_NODE = "#E3F2FD"  # light blue — excitatory interneuron fill
COL_INH_NODE = "#FFEBEE"  # light red — inhibitory interneuron fill


def save_fig(fig, name):
    (OUT_DIR / "png").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "pdf").mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / "png" / f"{name}.png")
    fig.savefig(OUT_DIR / "pdf" / f"{name}.pdf")
    logger.info("  Saved: %s", name)
    plt.close(fig)


def _draw_node(ax, xy, label, width, height, facecolor, edgecolor="black",
               lw=1.5, fontsize=8, fontweight="normal", zorder=3):
    """Draw a rounded box node."""
    x, y = xy
    box = FancyBboxPatch(
        (x - width / 2, y - height / 2), width, height,
        boxstyle="round,pad=0.02", facecolor=facecolor,
        edgecolor=edgecolor, lw=lw, zorder=zorder,
    )
    ax.add_patch(box)
    ax.text(x, y, label, ha="center", va="center", fontsize=fontsize,
            fontweight=fontweight, zorder=zorder + 1, clip_on=False)
    return box


def _draw_arrow(ax, xy_from, xy_to, color, lw=1.5, label=None,
                label_fontsize=6.5, label_offset=(0, 0), style="-|>",
                zorder=2, connectionstyle="arc3,rad=0.0", alpha=1.0,
                shrinkA=8, shrinkB=8):
    """Draw an arrow between two points."""
    arrow = FancyArrowPatch(
        xy_from, xy_to,
        arrowstyle=style, color=color, lw=lw,
        connectionstyle=connectionstyle,
        shrinkA=shrinkA, shrinkB=shrinkB,
        zorder=zorder, alpha=alpha,
        mutation_scale=12,
    )
    ax.add_patch(arrow)
    if label:
        mx = (xy_from[0] + xy_to[0]) / 2 + label_offset[0]
        my = (xy_from[1] + xy_to[1]) / 2 + label_offset[1]
        ax.text(mx, my, label, fontsize=label_fontsize, ha="center", va="center",
                color=color, zorder=zorder + 1,
                bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.85))


def select_key_presynaptic(df_pre_target, channel, top_n_min=3, frac_threshold=0.80):
    """Select top presynaptic neurons explaining ≥frac_threshold of total |effective| signal.
    Always include at least top_n_min."""
    col = f"effective_{channel}_to_target"
    df = df_pre_target.copy()
    df["abs_eff"] = df[col].abs()
    df = df.sort_values("abs_eff", ascending=False).reset_index(drop=True)
    total = df["abs_eff"].sum()
    if total < 1e-12:
        return df.head(top_n_min)
    df["cum_frac"] = df["abs_eff"].cumsum() / total
    n_needed = max(top_n_min, int((df["cum_frac"] <= frac_threshold).sum()) + 1)
    n_needed = min(n_needed, 6, len(df))
    return df.head(n_needed)


def build_circuit_data(target_name, grp, W_csc, W_unsigned_csc, x23, x25,
                       idx_to_type, type_to_idx, type_to_nt, type_to_inhib,
                       ppk23_types, ppk25_types, prop_sig, s_ppk23, s_ppk25):
    """Build the data needed for one circuit diagram."""
    t_idx = type_to_idx[target_name]

    # Get activations
    a23 = prop_sig.propagate(s_ppk23, 3, sustained=True)[t_idx]
    a25 = prop_sig.propagate(s_ppk25, 3, sustained=True)[t_idx]
    ab = prop_sig.propagate(s_ppk23 + s_ppk25, 3, sustained=True)[t_idx]
    rij = ab - a23 - a25
    cat = "super" if rij > 0 else "destructive"

    # Presynaptic partners
    col = W_csc[:, t_idx].toarray().ravel()
    pre_indices = np.nonzero(col)[0]

    pre_rows = []
    for pi in pre_indices:
        ptype = idx_to_type.get(pi, f"idx_{pi}")
        w = col[pi]
        d23 = x23[2][pi]
        d25 = x25[2][pi]
        eff23 = w * d23
        eff25 = w * d25
        if abs(eff23) < 1e-10 and abs(eff25) < 1e-10:
            continue
        pre_rows.append({
            "presynaptic": ptype, "pre_idx": pi,
            "weight_signed": w,
            "pre_nt": type_to_nt.get(ptype, "?"),
            "pre_is_inhibitory": type_to_inhib.get(ptype, False),
            "pre_drive_ppk23": d23, "pre_drive_ppk25": d25,
            "effective_ppk23_to_target": eff23,
            "effective_ppk25_to_target": eff25,
            "is_ppk23_sensory": ptype in ppk23_types,
            "is_ppk25_sensory": ptype in ppk25_types,
        })

    df_pre = pd.DataFrame(pre_rows)

    # Select key presynaptic neurons (union of top ppk23 and ppk25 contributors)
    key23 = select_key_presynaptic(df_pre, "ppk23")
    key25 = select_key_presynaptic(df_pre, "ppk25")
    key_names = set(key23["presynaptic"]).union(set(key25["presynaptic"]))
    df_key = df_pre[df_pre["presynaptic"].isin(key_names)].copy()

    # Sort by total absolute contribution
    df_key["abs_total"] = df_key["effective_ppk23_to_target"].abs() + df_key["effective_ppk25_to_target"].abs()
    df_key = df_key.sort_values("abs_total", ascending=False).reset_index(drop=True)

    # Limit to at most 8 intermediaries for readability
    df_key = df_key.head(8)

    # For each key presynaptic, find its top upstream source
    upstream = {}
    for _, row in df_key.iterrows():
        pi = int(row["pre_idx"])
        ptype = row["presynaptic"]
        col_p = W_csc[:, pi].toarray().ravel()
        pre_p = np.nonzero(col_p)[0]

        up_list = []
        for pp in pre_p:
            pp_type = idx_to_type.get(pp, "")
            pp_s1_23 = x23[1][pp]
            pp_s1_25 = x25[1][pp]
            pp_s0_23 = x23[0][pp]
            pp_s0_25 = x25[0][pp]
            pp_w = col_p[pp]
            is_s23 = pp_type in ppk23_types
            is_s25 = pp_type in ppk25_types

            # Use step1 signal, or step0 if it's a sensory neuron
            drive_23 = pp_s1_23 if abs(pp_s1_23) > 1e-9 else pp_s0_23
            drive_25 = pp_s1_25 if abs(pp_s1_25) > 1e-9 else pp_s0_25
            eff_23 = pp_w * drive_23
            eff_25 = pp_w * drive_25

            if abs(eff_23) > 1e-9 or abs(eff_25) > 1e-9:
                up_list.append({
                    "neuron": pp_type, "w": pp_w,
                    "eff_23": eff_23, "eff_25": eff_25,
                    "is_ppk23_sensory": is_s23, "is_ppk25_sensory": is_s25,
                    "is_inhibitory": type_to_inhib.get(pp_type, False),
                })

        up_list.sort(key=lambda x: abs(x["eff_23"]) + abs(x["eff_25"]), reverse=True)
        upstream[ptype] = up_list[:2]  # top 2 upstream per intermediary

    # Net drives
    net_23 = df_pre["effective_ppk23_to_target"].sum()
    net_25 = df_pre["effective_ppk25_to_target"].sum()

    return {
        "target": target_name, "group": grp, "category": cat,
        "a23": a23, "a25": a25, "a_both": ab, "rij": rij,
        "net_23": net_23, "net_25": net_25,
        "key_pre": df_key, "upstream": upstream,
    }


def draw_circuit(data):
    """Draw the circuit diagram for one target neuron."""
    target = data["target"]
    cat = data["category"]
    grp = data["group"]
    df_key = data["key_pre"]
    upstream = data["upstream"]

    n_inter = len(df_key)
    fig_h = max(7, 1.4 * n_inter + 3)
    fig, ax = plt.subplots(figsize=(26, fig_h))
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.12, 1.05)
    ax.axis("off")

    # Column x positions — spread wide
    x_sens = 0.06
    x_inter = 0.48
    x_target = 0.90

    # Sensory pool positions
    y_ppk23 = 0.78
    y_ppk25 = 0.30

    # Draw sensory pools
    _draw_node(ax, (x_sens, y_ppk23), "ppk23\nsensory",
               0.08, 0.09, COL_PPK23, lw=2, fontsize=10, fontweight="bold")
    _draw_node(ax, (x_sens, y_ppk25), "ppk25\nsensory",
               0.08, 0.09, COL_PPK25, lw=2, fontsize=10, fontweight="bold")

    # Draw target
    target_color = COL_SUPER if cat == "super" else COL_DESTR
    target_fill = "#FFEBEE" if cat == "super" else "#E3F2FD"
    cat_label = "SUPER" if cat == "super" else "DESTRUCTIVE"
    _draw_node(ax, (x_target, 0.54), f"{target}\n({grp})",
               0.08, 0.10, target_fill, edgecolor=target_color,
               lw=3, fontsize=11, fontweight="bold")

    # Draw intermediaries — spread vertically with more room
    if n_inter > 0:
        y_positions = np.linspace(0.94, 0.10, n_inter)
    else:
        y_positions = []

    inter_positions = {}
    for i, (_, row) in enumerate(df_key.iterrows()):
        y = y_positions[i]
        ptype = row["presynaptic"]
        is_inh = row["pre_is_inhibitory"]
        nt = row["pre_nt"]

        fill = COL_INH_NODE if is_inh else COL_EXC_NODE
        edge = COL_INH if is_inh else "#1565C0"
        tag = "INH" if is_inh else "EXC"
        nt_short = nt[:4] if isinstance(nt, str) else "?"

        label = f"{ptype}\n[{tag}, {nt_short}]"
        _draw_node(ax, (x_inter, y), label, 0.10, 0.055, fill,
                   edgecolor=edge, lw=1.2, fontsize=8)
        inter_positions[ptype] = (x_inter, y)

    # ── Arrows: sensory → intermediaries ──
    # Stagger label offsets to reduce overlap
    left_label_idx = 0
    for ptype, (ix, iy) in inter_positions.items():
        ups = upstream.get(ptype, [])
        row = df_key[df_key["presynaptic"] == ptype].iloc[0]
        d23 = row["pre_drive_ppk23"]
        d25 = row["pre_drive_ppk25"]

        # Stagger: alternate label offset left/right of midpoint
        stagger_x = -0.02 + 0.015 * (left_label_idx % 3)
        stagger_y = 0.012 * (1 if left_label_idx % 2 == 0 else -1)
        left_label_idx += 1

        if abs(d23) > 1e-8:
            up_23_label = ""
            for u in ups:
                if u["is_ppk23_sensory"] and abs(u["eff_23"]) > 1e-9:
                    up_23_label = f"via {u['neuron']} (w={u['w']:+.3f})"
                    break
                elif abs(u["eff_23"]) > 1e-9 and not u["is_ppk25_sensory"]:
                    inh_tag = " [INH]" if u["is_inhibitory"] else ""
                    up_23_label = f"via {u['neuron']}{inh_tag} (w={u['w']:+.3f})"
                    break

            arr_color = COL_EXC if d23 > 0 else COL_INH
            lw = min(3.5, max(0.8, abs(d23) * 25))
            rad = 0.12 if iy > y_ppk23 else (-0.12 if iy < y_ppk23 - 0.12 else 0.04)
            conn = f"arc3,rad={rad}"

            label_str = f"ppk23 drive={d23:+.4f}"
            if up_23_label:
                label_str = f"ppk23 {up_23_label}\ndrive={d23:+.4f}"

            _draw_arrow(ax, (x_sens + 0.04, y_ppk23), (ix - 0.05, iy),
                        arr_color, lw=lw,
                        label=label_str,
                        label_offset=(stagger_x, stagger_y),
                        connectionstyle=conn,
                        label_fontsize=6.5)

        if abs(d25) > 1e-8:
            up_25_label = ""
            for u in ups:
                if u["is_ppk25_sensory"] and abs(u["eff_25"]) > 1e-9:
                    up_25_label = f"via {u['neuron']} (w={u['w']:+.3f})"
                    break
                elif abs(u["eff_25"]) > 1e-9 and not u["is_ppk23_sensory"]:
                    inh_tag = " [INH]" if u["is_inhibitory"] else ""
                    up_25_label = f"via {u['neuron']}{inh_tag} (w={u['w']:+.3f})"
                    break

            arr_color = COL_EXC if d25 > 0 else COL_INH
            lw = min(3.5, max(0.8, abs(d25) * 25))
            rad = -0.12 if iy < y_ppk25 else (0.12 if iy > y_ppk25 + 0.12 else -0.04)
            conn = f"arc3,rad={rad}"

            label_str = f"ppk25 drive={d25:+.4f}"
            if up_25_label:
                label_str = f"ppk25 {up_25_label}\ndrive={d25:+.4f}"

            _draw_arrow(ax, (x_sens + 0.04, y_ppk25), (ix - 0.05, iy),
                        arr_color, lw=lw,
                        label=label_str,
                        label_offset=(stagger_x, -stagger_y),
                        connectionstyle=conn,
                        label_fontsize=6.5)

    # ── Arrows: intermediaries → target ──
    # Stagger right-side labels vertically
    right_idx = 0
    for ptype, (ix, iy) in inter_positions.items():
        row = df_key[df_key["presynaptic"] == ptype].iloc[0]
        w = row["weight_signed"]
        eff23 = row["effective_ppk23_to_target"]
        eff25 = row["effective_ppk25_to_target"]

        arr_color = COL_EXC if w > 0 else COL_INH
        lw = min(3.5, max(0.6, (abs(eff23) + abs(eff25)) * 500))

        label = f"weight={w:+.4f}\nppk23 eff={eff23:+.5f}\nppk25 eff={eff25:+.5f}"

        # Stagger radii to separate converging arrows
        base_rad = 0.02 * (right_idx - n_inter / 2)
        if abs(iy - 0.54) < 0.04:
            base_rad += 0.04
        conn = f"arc3,rad={base_rad}"
        right_idx += 1

        # Offset label along the arrow to avoid stacking
        frac = 0.3 + 0.05 * right_idx  # place labels at different positions
        lbl_x = ix + (x_target - ix) * frac
        lbl_y = iy + (0.54 - iy) * frac
        lbl_offset = (lbl_x - (ix + x_target) / 2, lbl_y - (iy + 0.54) / 2)

        _draw_arrow(ax, (ix + 0.05, iy), (x_target - 0.04, 0.54),
                    arr_color, lw=lw, label=label,
                    label_offset=(0.015, 0.008 * (right_idx - n_inter / 2)),
                    connectionstyle=conn,
                    label_fontsize=6.5)

    # ── Summary box ──
    net23 = data["net_23"]
    net25 = data["net_25"]
    same_sign = (net23 > 0 and net25 > 0) or (net23 < 0 and net25 < 0)
    sign_label = "SAME sign" if same_sign else "OPPOSITE sign"

    summary = (
        f"Net ppk23 drive: {net23:+.5f} ({'exc' if net23 > 0 else 'inh'})\n"
        f"Net ppk25 drive: {net25:+.5f} ({'exc' if net25 > 0 else 'inh'})\n"
        f"Drive signs: {sign_label}\n"
        f"─────────────────────────\n"
        f"A(ppk23) = {data['a23']:+.4f}\n"
        f"A(ppk25) = {data['a25']:+.4f}\n"
        f"A(both)  = {data['a_both']:+.4f}\n"
        f"R_ij     = {data['rij']:+.4f}  ({cat_label})\n"
    )
    # Determine mechanism based on drive signs AND category
    both_negative = (net23 < 0 and net25 < 0)
    both_positive = (net23 > 0 and net25 > 0)
    opposite = not same_sign

    if cat == "super" and opposite:
        summary += (
            f"─────────────────────────\n"
            f"Opposite-sign convergence\n"
            f"→ push-pull / de-saturation\n"
            f"→ combined > sum of singles"
        )
    elif cat == "super" and both_negative:
        summary += (
            f"─────────────────────────\n"
            f"Both drives inhibitory\n"
            f"→ floor saturation (sublinear\n"
            f"  inhibition): combined inh\n"
            f"  weaker than sum of singles"
        )
    elif cat == "destructive" and both_positive:
        summary += (
            f"─────────────────────────\n"
            f"Both drives excitatory\n"
            f"→ ceiling saturation: combined\n"
            f"  exc weaker than sum of singles"
        )
    elif cat == "destructive":
        summary += (
            f"─────────────────────────\n"
            f"Same-sign convergence\n"
            f"→ saturating nonlinearity\n"
            f"→ combined < sum of singles"
        )
    else:
        # super but both positive — unusual, just describe
        summary += (
            f"─────────────────────────\n"
            f"R_ij > 0 despite same-sign\n"
            f"→ network-level interaction"
        )

    box_color = "#FFEBEE" if cat == "super" else "#E3F2FD"
    ax.text(0.68, -0.04, summary, transform=ax.transAxes,
            fontsize=8, va="top", ha="center", family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc=box_color,
                      ec=target_color, lw=1.5, alpha=0.95))

    # Title
    ax.set_title(
        f"Circuit diagram: {target} ({grp}) — {cat_label}\n"
        f"R_ij(ppk23 × ppk25) = {data['rij']:+.4f}",
        fontsize=14, fontweight="bold", color=target_color, pad=15,
    )

    # ── Legend ──
    legend_text = (
        "LEGEND\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "ARROWS\n"
        "  Blue arrow = excitatory connection (w > 0)\n"
        "  Red arrow  = inhibitory connection (w < 0)\n"
        "  Thickness  = magnitude of contribution\n"
        "\n"
        "LEFT SIDE (sensory → intermediary)\n"
        "  drive = linear ppk23/ppk25 signal this\n"
        "    neuron carries at step 2 (2 hops from\n"
        "    sensory), computed WITHOUT activation fn.\n"
        "    Positive = excitatory path dominates.\n"
        "    Negative = inhibitory path dominates.\n"
        "  via = upstream neuron feeding the signal,\n"
        "    with its synaptic weight (w)\n"
        "\n"
        "RIGHT SIDE (intermediary → target)\n"
        "  weight = signed synaptic weight to target\n"
        "    (positive if EXC, negative if INH)\n"
        "  ppk23 eff = weight × drive(ppk23)\n"
        "    = effective ppk23 signal delivered to\n"
        "      target through this one synapse\n"
        "  ppk25 eff = same for ppk25\n"
        "\n"
        "NODES\n"
        "  Light blue box = excitatory neuron (EXC)\n"
        "  Light red box  = inhibitory neuron (INH)\n"
        "  [EXC, glut] = excitatory, glutamatergic\n"
        "  [INH, gaba] = inhibitory, GABAergic\n"
        "\n"
        "SUMMARY BOX\n"
        "  A(ppk23) = target activation, ppk23 only\n"
        "  A(ppk25) = target activation, ppk25 only\n"
        "  A(both)  = target activation, both active\n"
        "  R_ij = A(both) − A(ppk23) − A(ppk25)\n"
        "\n"
        "THREE MECHANISMS\n"
        "  Both exc → ceiling saturation → R_ij<0\n"
        "    (DESTRUCTIVE)\n"
        "  Both inh → floor saturation   → R_ij>0\n"
        "    (SUPER: sublinear inhibition)\n"
        "  Opposite → push-pull          → R_ij>0\n"
        "    (SUPER: mutual de-saturation)"
    )
    ax.text(0.01, -0.04, legend_text, transform=ax.transAxes,
            fontsize=7, va="top", ha="left", family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc="#F5F5F5",
                      ec="gray", lw=0.8, alpha=0.95))

    return fig


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Loading data...")
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

    W_csc = W.tocsc()
    W_unsigned_csc = W_unsigned.tocsc()
    Wt = W.T.tocsc()

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]

    ppk23_types = set(channels["ppk23"])
    ppk25_types = set(channels["ppk25"])

    # Linear pulse propagation
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

    # Sigmoid propagator for activation values
    prop_sig = SignalPropagator(W, "sigmoid_rectified", {"beta": 5.0})

    # Pre-compute combined activation for R_ij
    s_both = s_ppk23 + s_ppk25
    a23_all = prop_sig.propagate(s_ppk23, 3, sustained=True)
    a25_all = prop_sig.propagate(s_ppk25, 3, sustained=True)
    ab_all = prop_sig.propagate(s_both, 3, sustained=True)

    # Load targets
    targets = loader.load_targets()

    # Exclude sensory types from targets
    sensory_types = set()
    for ch_types in channels.values():
        sensory_types.update(ch_types)
    sensory_indices = set(encoder.get_indices(list(sensory_types)))

    total_count = 0
    for grp_name in TARGET_GROUPS:
        if grp_name not in targets:
            logger.warning("  Group '%s' not in targets.json, skipping", grp_name)
            continue
        grp_short = GROUP_SHORT.get(grp_name, grp_name)
        grp_dir = OUT_DIR / grp_short
        (grp_dir / "png").mkdir(parents=True, exist_ok=True)
        (grp_dir / "pdf").mkdir(parents=True, exist_ok=True)

        target_list = targets[grp_name]
        logger.info("Group %s: %d targets", grp_short, len(target_list))

        for target_name in target_list:
            if target_name not in type_to_idx:
                logger.warning("  %s not in matrix, skipping", target_name)
                continue
            t_idx = type_to_idx[target_name]
            if t_idx in sensory_indices:
                logger.info("  %s is sensory, skipping", target_name)
                continue

            # Compute R_ij to determine category
            rij = ab_all[t_idx] - a23_all[t_idx] - a25_all[t_idx]
            cat = "super" if rij > 0 else "destructive"

            logger.info("  Drawing %s (%s, %s, R_ij=%.4f)...",
                        target_name, grp_short, cat, rij)

            data = build_circuit_data(
                target_name, grp_short, W_csc, W_unsigned_csc, x23, x25,
                idx_to_type, type_to_idx, type_to_nt, type_to_inhib,
                ppk23_types, ppk25_types, prop_sig, s_ppk23, s_ppk25,
            )

            fig = draw_circuit(data)

            # Save in group subdirectory
            fname = f"circuit_{target_name}"
            fig.savefig(grp_dir / "png" / f"{fname}.png")
            fig.savefig(grp_dir / "pdf" / f"{fname}.pdf")
            logger.info("    Saved: %s/%s", grp_short, fname)
            plt.close(fig)
            total_count += 1

    logger.info("Done! %d circuit diagrams in %s", total_count, OUT_DIR)


if __name__ == "__main__":
    main()
