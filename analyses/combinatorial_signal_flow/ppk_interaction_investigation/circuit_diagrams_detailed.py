#!/usr/bin/env python3
"""
Detailed circuit diagrams — shows EVERY intermediate hop explicitly:

  sensory (step 0) → step 1 neurons → step 2 neurons → target (step 3)

This is the expanded version of circuit_diagrams.py, which collapses
step 1 and step 2 into a single intermediary column.
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
OUT_DIR = Path(__file__).resolve().parent / "plots" / "circuit_diagrams_detailed"

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
COL_EXC = "#2196F3"
COL_INH = "#E53935"
COL_PPK23 = "#FFC107"
COL_PPK25 = "#8D6E63"
COL_SUPER = "#E53935"
COL_DESTR = "#1565C0"
COL_EXC_NODE = "#E3F2FD"
COL_INH_NODE = "#FFEBEE"
COL_SENSORY_23 = "#FFF8E1"  # individual ppk23 sensory neuron
COL_SENSORY_25 = "#EFEBE9"  # individual ppk25 sensory neuron


def _draw_node(ax, xy, label, width, height, facecolor, edgecolor="black",
               lw=1.5, fontsize=8, fontweight="normal", zorder=3):
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
                label_fontsize=6, label_offset=(0, 0), style="-|>",
                zorder=2, connectionstyle="arc3,rad=0.0", alpha=1.0,
                shrinkA=6, shrinkB=6):
    arrow = FancyArrowPatch(
        xy_from, xy_to,
        arrowstyle=style, color=color, lw=lw,
        connectionstyle=connectionstyle,
        shrinkA=shrinkA, shrinkB=shrinkB,
        zorder=zorder, alpha=alpha,
        mutation_scale=10,
    )
    ax.add_patch(arrow)
    if label:
        mx = (xy_from[0] + xy_to[0]) / 2 + label_offset[0]
        my = (xy_from[1] + xy_to[1]) / 2 + label_offset[1]
        ax.text(mx, my, label, fontsize=label_fontsize, ha="center", va="center",
                color=color, zorder=zorder + 1,
                bbox=dict(boxstyle="round,pad=0.08", fc="white", ec="none", alpha=0.85))


def build_detailed_data(target_name, grp, W_csc, x23, x25,
                        idx_to_type, type_to_idx, type_to_nt, type_to_inhib,
                        ppk23_types, ppk25_types, prop_sig, s_ppk23, s_ppk25):
    """Build multi-hop path data for one target."""
    t_idx = type_to_idx[target_name]

    # Activations
    a23 = prop_sig.propagate(s_ppk23, 3, sustained=True)[t_idx]
    a25 = prop_sig.propagate(s_ppk25, 3, sustained=True)[t_idx]
    ab = prop_sig.propagate(s_ppk23 + s_ppk25, 3, sustained=True)[t_idx]
    rij = ab - a23 - a25
    cat = "super" if rij > 0 else "destructive"

    # ── Step 2 neurons (presynaptic to target) ──
    col_t = W_csc[:, t_idx].toarray().ravel()
    pre_t_indices = np.nonzero(col_t)[0]

    step2_rows = []
    for pi in pre_t_indices:
        ptype = idx_to_type.get(pi, f"idx_{pi}")
        w = col_t[pi]
        d23 = x23[2][pi]
        d25 = x25[2][pi]
        eff23 = w * d23
        eff25 = w * d25
        if abs(eff23) < 1e-10 and abs(eff25) < 1e-10:
            continue
        step2_rows.append({
            "neuron": ptype, "idx": pi, "w_to_target": w,
            "drive_23": d23, "drive_25": d25,
            "eff_23": eff23, "eff_25": eff25,
            "nt": type_to_nt.get(ptype, "?"),
            "is_inh": type_to_inhib.get(ptype, False),
        })

    df_s2 = pd.DataFrame(step2_rows)
    df_s2["abs_total"] = df_s2["eff_23"].abs() + df_s2["eff_25"].abs()
    df_s2 = df_s2.sort_values("abs_total", ascending=False)

    # Select top step 2 neurons: enough for ~80% of signal, min 3, max 6
    total_sig = df_s2["abs_total"].sum()
    if total_sig > 1e-12:
        df_s2["cum_frac"] = df_s2["abs_total"].cumsum() / total_sig
        n_need = max(3, int((df_s2["cum_frac"] <= 0.80).sum()) + 1)
    else:
        n_need = 3
    n_need = min(n_need, 6, len(df_s2))
    df_s2 = df_s2.head(n_need).reset_index(drop=True)

    # ── Step 1 neurons (presynaptic to each step 2 neuron) ──
    # For each step 2 neuron, find the top step 1 contributors of ppk23/ppk25
    step1_neurons = {}  # neuron_name → {info}
    edges_s1_to_s2 = []  # (step1_name, step2_name, w, eff23, eff25)

    for _, s2_row in df_s2.iterrows():
        s2_name = s2_row["neuron"]
        s2_idx = int(s2_row["idx"])

        col_s2 = W_csc[:, s2_idx].toarray().ravel()
        pre_s2 = np.nonzero(col_s2)[0]

        s1_contribs = []
        for pp in pre_s2:
            pp_type = idx_to_type.get(pp, f"idx_{pp}")
            pp_w = col_s2[pp]
            # Step 1 signal: ppk23/ppk25 at 1 hop from sensory
            pp_d23_s1 = x23[1][pp]
            pp_d25_s1 = x25[1][pp]
            # Also check if it's a sensory neuron (step 0)
            pp_d23_s0 = x23[0][pp]
            pp_d25_s0 = x25[0][pp]

            is_s23 = pp_type in ppk23_types
            is_s25 = pp_type in ppk25_types

            # Use step 1 signal, or step 0 if sensory
            d23 = pp_d23_s1 if abs(pp_d23_s1) > 1e-9 else pp_d23_s0
            d25 = pp_d25_s1 if abs(pp_d25_s1) > 1e-9 else pp_d25_s0
            eff23 = pp_w * d23
            eff25 = pp_w * d25

            if abs(eff23) > 1e-9 or abs(eff25) > 1e-9:
                s1_contribs.append({
                    "neuron": pp_type, "idx": pp, "w": pp_w,
                    "d23": d23, "d25": d25,
                    "eff23": eff23, "eff25": eff25,
                    "is_ppk23_sensory": is_s23,
                    "is_ppk25_sensory": is_s25,
                    "nt": type_to_nt.get(pp_type, "?"),
                    "is_inh": type_to_inhib.get(pp_type, False),
                })

        # Sort by total contribution and pick top 2 per step2 neuron
        s1_contribs.sort(key=lambda x: abs(x["eff23"]) + abs(x["eff25"]), reverse=True)
        for s1c in s1_contribs[:2]:
            s1_name = s1c["neuron"]
            if s1_name not in step1_neurons:
                step1_neurons[s1_name] = s1c
            edges_s1_to_s2.append({
                "s1": s1_name, "s2": s2_name,
                "w": s1c["w"], "eff23": s1c["eff23"], "eff25": s1c["eff25"],
            })

    # ── Sensory connections to step 1 neurons ──
    # Which sensory neurons connect to which step 1 neurons?
    edges_sens_to_s1 = []  # (sensory_type, step1_name, w)
    all_sensory = ppk23_types | ppk25_types

    for s1_name, s1_info in step1_neurons.items():
        s1_idx = int(s1_info["idx"])
        col_s1 = W_csc[:, s1_idx].toarray().ravel()

        for sens_type in all_sensory:
            if sens_type not in type_to_idx:
                continue
            sens_idx = type_to_idx[sens_type]
            w = col_s1[sens_idx]
            if abs(w) > 1e-10:
                ch = "ppk23" if sens_type in ppk23_types else "ppk25"
                edges_sens_to_s1.append({
                    "sensory": sens_type, "channel": ch,
                    "s1": s1_name, "w": w,
                })

    # Also check if step 1 neurons ARE sensory neurons
    for s1_name, s1_info in step1_neurons.items():
        if s1_info["is_ppk23_sensory"]:
            edges_sens_to_s1.append({
                "sensory": s1_name, "channel": "ppk23",
                "s1": s1_name, "w": None,  # it IS the sensory neuron
            })
        if s1_info["is_ppk25_sensory"]:
            edges_sens_to_s1.append({
                "sensory": s1_name, "channel": "ppk25",
                "s1": s1_name, "w": None,
            })

    # Aggregate sensory edges: group by (channel, s1), sum weights
    sens_agg = {}
    for e in edges_sens_to_s1:
        key = (e["channel"], e["s1"])
        if key not in sens_agg:
            sens_agg[key] = {"channel": e["channel"], "s1": e["s1"],
                             "sensory_list": [], "total_w": 0.0, "is_self": False}
        if e["w"] is None:
            sens_agg[key]["is_self"] = True
        else:
            sens_agg[key]["sensory_list"].append(e["sensory"])
            sens_agg[key]["total_w"] += e["w"]

    # Net drives
    net_23 = col_t[pre_t_indices] @ np.array([x23[2][i] for i in pre_t_indices])
    net_25 = col_t[pre_t_indices] @ np.array([x25[2][i] for i in pre_t_indices])

    return {
        "target": target_name, "group": grp, "category": cat,
        "a23": a23, "a25": a25, "a_both": ab, "rij": rij,
        "net_23": net_23, "net_25": net_25,
        "step2": df_s2,
        "step1": step1_neurons,
        "edges_s1_s2": edges_s1_to_s2,
        "sens_agg": sens_agg,
    }


def draw_detailed_circuit(data):
    """Draw the detailed multi-hop circuit diagram."""
    target = data["target"]
    cat = data["category"]
    grp = data["group"]
    df_s2 = data["step2"]
    step1 = data["step1"]
    edges_s1_s2 = data["edges_s1_s2"]
    sens_agg = data["sens_agg"]

    n_s2 = len(df_s2)
    n_s1 = len(step1)
    n_rows = max(n_s2, n_s1, 4)

    fig_h = max(8, 1.1 * n_rows + 4)
    fig, ax = plt.subplots(figsize=(28, fig_h))
    ax.set_xlim(-0.02, 1.02)
    y_top = 1.02
    y_bot = -0.02
    ax.set_ylim(y_bot - 0.18, y_top)
    ax.axis("off")

    # Column positions — spread wide
    x_sens = 0.05
    x_s1 = 0.27
    x_s2 = 0.55
    x_target = 0.92

    # ── Column headers ──
    ax.text(x_sens, y_top + 0.01, "Sensory\n(step 0)", ha="center", fontsize=8,
            fontweight="bold", color="gray")
    ax.text(x_s1, y_top + 0.01, "Step 1\n(1-hop from sensory)", ha="center", fontsize=8,
            fontweight="bold", color="gray")
    ax.text(x_s2, y_top + 0.01, "Step 2\n(presynaptic to target)", ha="center", fontsize=8,
            fontweight="bold", color="gray")
    ax.text(x_target, y_top + 0.01, "Target\n(step 3)", ha="center", fontsize=8,
            fontweight="bold", color="gray")

    # ── Sensory pools ──
    y_ppk23 = 0.72
    y_ppk25 = 0.28
    _draw_node(ax, (x_sens, y_ppk23), "ppk23\nsensory",
               0.08, 0.09, COL_PPK23, lw=2, fontsize=9, fontweight="bold")
    _draw_node(ax, (x_sens, y_ppk25), "ppk25\nsensory",
               0.08, 0.09, COL_PPK25, lw=2, fontsize=9, fontweight="bold")

    # ── Target ──
    target_color = COL_SUPER if cat == "super" else COL_DESTR
    target_fill = "#FFEBEE" if cat == "super" else "#E3F2FD"
    cat_label = "SUPER" if cat == "super" else "DESTRUCTIVE"
    _draw_node(ax, (x_target, 0.50), f"{target}\n({grp})",
               0.08, 0.10, target_fill, edgecolor=target_color,
               lw=3, fontsize=10, fontweight="bold")

    # ── Step 1 neurons ──
    s1_names = list(step1.keys())
    if n_s1 > 0:
        s1_ys = np.linspace(0.90, 0.10, n_s1)
    else:
        s1_ys = []
    s1_pos = {}
    for i, s1_name in enumerate(s1_names):
        y = s1_ys[i]
        info = step1[s1_name]
        is_inh = info["is_inh"]
        nt = info["nt"]
        fill = COL_INH_NODE if is_inh else COL_EXC_NODE
        edge = COL_INH if is_inh else "#1565C0"
        tag = "INH" if is_inh else "EXC"
        nt_short = nt[:4] if isinstance(nt, str) else "?"

        # Mark if it's a sensory neuron
        sens_mark = ""
        if info.get("is_ppk23_sensory"):
            fill = COL_SENSORY_23
            sens_mark = "\n(ppk23 sens.)"
        elif info.get("is_ppk25_sensory"):
            fill = COL_SENSORY_25
            sens_mark = "\n(ppk25 sens.)"

        label = f"{s1_name}\n[{tag}, {nt_short}]{sens_mark}"
        _draw_node(ax, (x_s1, y), label, 0.12, 0.06, fill,
                   edgecolor=edge, lw=1.0, fontsize=7)
        s1_pos[s1_name] = (x_s1, y)

    # ── Step 2 neurons ──
    if n_s2 > 0:
        s2_ys = np.linspace(0.90, 0.10, n_s2)
    else:
        s2_ys = []
    s2_pos = {}
    for i, (_, row) in enumerate(df_s2.iterrows()):
        y = s2_ys[i]
        name = row["neuron"]
        is_inh = row["is_inh"]
        nt = row["nt"]
        fill = COL_INH_NODE if is_inh else COL_EXC_NODE
        edge = COL_INH if is_inh else "#1565C0"
        tag = "INH" if is_inh else "EXC"
        nt_short = nt[:4] if isinstance(nt, str) else "?"

        label = f"{name}\n[{tag}, {nt_short}]"
        _draw_node(ax, (x_s2, y), label, 0.12, 0.06, fill,
                   edgecolor=edge, lw=1.0, fontsize=7)
        s2_pos[name] = (x_s2, y)

    # ── Arrows: sensory → step 1 ──
    for key, agg in sens_agg.items():
        ch = agg["channel"]
        s1_name = agg["s1"]
        if s1_name not in s1_pos:
            continue

        sx, sy = (x_sens, y_ppk23) if ch == "ppk23" else (x_sens, y_ppk25)
        tx, ty = s1_pos[s1_name]

        if agg["is_self"]:
            # Step 1 neuron IS the sensory neuron — draw a special dashed arrow
            arr_color = COL_PPK23 if ch == "ppk23" else COL_PPK25
            _draw_arrow(ax, (sx + 0.05, sy), (tx - 0.07, ty),
                        arr_color, lw=1.5, style="-|>",
                        label=f"{ch}\n(IS sensory)",
                        label_fontsize=6.5, label_offset=(0, 0.005),
                        connectionstyle=f"arc3,rad={0.05 if ty > sy else -0.05}")
        elif abs(agg["total_w"]) > 1e-10:
            n_sens = len(agg["sensory_list"])
            arr_color = COL_EXC if agg["total_w"] > 0 else COL_INH
            lw = min(3.0, max(0.6, abs(agg["total_w"]) * 4))
            rad = 0.08 if ty > sy else (-0.08 if ty < sy else 0.02)
            top_sens = agg["sensory_list"][0] if agg["sensory_list"] else ""
            label_str = f"{ch} ({n_sens} neurons)\nw_sum={agg['total_w']:+.3f}"
            if n_sens == 1:
                label_str = f"{ch}: {top_sens}\nw={agg['total_w']:+.3f}"
            _draw_arrow(ax, (sx + 0.05, sy), (tx - 0.07, ty),
                        arr_color, lw=lw,
                        label=label_str,
                        label_fontsize=6.5, label_offset=(0, 0.005),
                        connectionstyle=f"arc3,rad={rad}")

    # ── Arrows: step 1 → step 2 ──
    # Group edges by (s1, s2) pair
    s1s2_edges = {}
    for e in edges_s1_s2:
        key = (e["s1"], e["s2"])
        if key not in s1s2_edges:
            s1s2_edges[key] = e
        # if duplicate, keep first (they should be same)

    for (s1_name, s2_name), e in s1s2_edges.items():
        if s1_name not in s1_pos or s2_name not in s2_pos:
            continue

        sx, sy = s1_pos[s1_name]
        tx, ty = s2_pos[s2_name]

        arr_color = COL_EXC if e["w"] > 0 else COL_INH
        lw = min(3.0, max(0.5, (abs(e["eff23"]) + abs(e["eff25"])) * 80))
        rad = 0.0
        dy = ty - sy
        if abs(dy) < 0.03:
            rad = 0.06

        label = f"w={e['w']:+.3f}"
        _draw_arrow(ax, (sx + 0.07, sy), (tx - 0.07, ty),
                    arr_color, lw=lw,
                    label=label,
                    label_fontsize=6.5, label_offset=(0, 0.005),
                    connectionstyle=f"arc3,rad={rad}")

    # ── Arrows: step 2 → target ──
    for _, row in df_s2.iterrows():
        s2_name = row["neuron"]
        if s2_name not in s2_pos:
            continue

        sx, sy = s2_pos[s2_name]
        w = row["w_to_target"]
        eff23 = row["eff_23"]
        eff25 = row["eff_25"]

        arr_color = COL_EXC if w > 0 else COL_INH
        lw = min(3.5, max(0.6, (abs(eff23) + abs(eff25)) * 400))
        rad = 0.0
        if abs(sy - 0.50) < 0.04:
            rad = 0.04

        label = (f"weight={w:+.4f}\n"
                 f"ppk23 eff={eff23:+.5f}\n"
                 f"ppk25 eff={eff25:+.5f}")
        _draw_arrow(ax, (sx + 0.07, sy), (x_target - 0.055, 0.50),
                    arr_color, lw=lw,
                    label=label,
                    label_fontsize=6.5, label_offset=(0.01, 0),
                    connectionstyle=f"arc3,rad={rad}")

    # ── Drive annotations on step 2 nodes ──
    for _, row in df_s2.iterrows():
        name = row["neuron"]
        if name not in s2_pos:
            continue
        sx, sy = s2_pos[name]
        d23 = row["drive_23"]
        d25 = row["drive_25"]
        c23 = COL_INH if d23 < 0 else COL_EXC
        c25 = COL_INH if d25 < 0 else COL_EXC
        ax.text(sx + 0.065, sy + 0.020,
                f"ppk23 drive={d23:+.4f}", fontsize=6, color=c23,
                ha="left", style="italic")
        ax.text(sx + 0.065, sy - 0.003,
                f"ppk25 drive={d25:+.4f}", fontsize=6, color=c25,
                ha="left", style="italic")

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
        summary += (
            f"─────────────────────────\n"
            f"R_ij > 0 despite same-sign\n"
            f"→ network-level interaction"
        )

    box_color = "#FFEBEE" if cat == "super" else "#E3F2FD"
    ax.text(0.72, y_bot - 0.02, summary, transform=ax.transAxes,
            fontsize=8, va="top", ha="center", family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc=box_color,
                      ec=target_color, lw=1.5, alpha=0.95))

    # ── Legend ──
    legend_text = (
        "LEGEND\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "ARROWS\n"
        "  Blue = excitatory connection (positive weight)\n"
        "  Red  = inhibitory connection (negative weight)\n"
        "  Thickness proportional to |contribution|\n"
        "\n"
        "ARROW LABELS\n"
        "  Sensory → Step 1:\n"
        "    w or w_sum = synaptic weight(s) from sensory\n"
        "    neurons to this step 1 neuron\n"
        "  Step 1 → Step 2:\n"
        "    w = synaptic weight between these neurons\n"
        "  Step 2 → Target:\n"
        "    weight = synaptic weight to the target\n"
        "    ppk23 eff = weight × ppk23 drive\n"
        "      = effective ppk23 signal this synapse\n"
        "        delivers to the target\n"
        "    ppk25 eff = same for ppk25\n"
        "\n"
        "NODE ANNOTATIONS (next to step 2 nodes)\n"
        "  ppk23 drive = how much ppk23 signal this\n"
        "    neuron carries (linear, 2 hops from sensory)\n"
        "  ppk25 drive = same for ppk25\n"
        "\n"
        "NODES\n"
        "  Light blue = excitatory neuron (EXC)\n"
        "  Light red  = inhibitory neuron (INH)\n"
        "  Amber/brown = sensory neuron\n"
        "  [EXC, glut] = excitatory, glutamatergic\n"
        "  [INH, gaba] = inhibitory, GABAergic\n"
        "\n"
        "SUMMARY BOX\n"
        "  A(ppk23)  = target response, ppk23 only\n"
        "  A(ppk25)  = target response, ppk25 only\n"
        "  A(both)   = target response, both active\n"
        "  R_ij      = A(both) − A(ppk23) − A(ppk25)\n"
        "\n"
        "THREE MECHANISMS\n"
        "  Both exc → ceiling sat. → R_ij<0 (DESTR.)\n"
        "  Both inh → floor sat.   → R_ij>0 (SUPER)\n"
        "  Opposite → push-pull    → R_ij>0 (SUPER)"
    )
    ax.text(0.01, y_bot - 0.02, legend_text, transform=ax.transAxes,
            fontsize=7, va="top", ha="left", family="monospace",
            bbox=dict(boxstyle="round,pad=0.3", fc="#F5F5F5",
                      ec="gray", lw=0.6, alpha=0.95))

    # ── Title ──
    ax.set_title(
        f"Detailed circuit: {target} ({grp}) — {cat_label}\n"
        f"R_ij(ppk23 × ppk25) = {data['rij']:+.4f}",
        fontsize=13, fontweight="bold", color=target_color, pad=15,
    )

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

    prop_sig = SignalPropagator(W, "sigmoid_rectified", {"beta": 5.0})
    targets = loader.load_targets()

    sensory_types = set()
    for ch_types in channels.values():
        sensory_types.update(ch_types)
    sensory_indices = set(encoder.get_indices(list(sensory_types)))

    total_count = 0
    for grp_name in TARGET_GROUPS:
        if grp_name not in targets:
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

            logger.info("  Drawing %s ...", target_name)

            data = build_detailed_data(
                target_name, grp_short, W_csc, x23, x25,
                idx_to_type, type_to_idx, type_to_nt, type_to_inhib,
                ppk23_types, ppk25_types, prop_sig, s_ppk23, s_ppk25,
            )

            fig = draw_detailed_circuit(data)
            fname = f"circuit_detailed_{target_name}"
            fig.savefig(grp_dir / "png" / f"{fname}.png")
            fig.savefig(grp_dir / "pdf" / f"{fname}.pdf")
            logger.info("    Saved: %s/%s", grp_short, fname)
            plt.close(fig)
            total_count += 1

    logger.info("Done! %d detailed circuit diagrams in %s", total_count, OUT_DIR)


if __name__ == "__main__":
    main()
