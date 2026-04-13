#!/usr/bin/env python3
"""
Circuit diagrams with per-step activation trajectories.

Same layout as circuit_diagrams_detailed.py but every node shows a
mini-heatmap of its activation at each propagation step (0 → 3) under
three conditions (ppk23-only, ppk25-only, both) plus the interaction
delta = A(both) - A(ppk23) - A(ppk25).
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
import matplotlib.colors as mcolors
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from signal_flow import NetworkLoader, ChannelEncoder, SignalPropagator

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)-8s  %(message)s",
                    datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = Path(__file__).resolve().parent / "plots" / "circuit_diagrams_trajectory"

TARGET_GROUPS = ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]
GROUP_SHORT = {
    "aspf": "aspf", "aspg": "aspg",
    "PPN1_downstream": "PPN1", "vAB3_downstream": "vAB3",
}

N_STEPS = 3  # must match the analysis convention

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 12, "axes.labelsize": 10,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "pdf.fonttype": 42,
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
COL_SENSORY_23 = "#FFF8E1"
COL_SENSORY_25 = "#EFEBE9"

# Diverging colormap for mini-heatmaps (blue → white → red)
TRAJ_CMAP = plt.cm.RdBu_r


def _draw_mini_heatmap(ax, cx, cy, width, height, traj_data, n_steps,
                       vmax=None, fontsize=4.5, highlight_cells=None):
    """
    Draw a small heatmap inside a node.

    traj_data : dict with keys 'ppk23', 'ppk25', 'both', 'delta',
                each a 1-D array of length n_steps+1.
    highlight_cells : set of (row, col) tuples to draw with bold yellow border
                      (used to mark sensory input cells: s0=1.0).
    """
    rows_order = ["ppk23", "ppk25", "both", "delta"]
    row_labels = ["23", "25", "B", "Δ"]
    n_cols = n_steps + 1
    n_rows = len(rows_order)

    if highlight_cells is None:
        highlight_cells = set()

    # Build the 2-D data matrix
    mat = np.zeros((n_rows, n_cols))
    for ri, key in enumerate(rows_order):
        vals = traj_data.get(key, np.zeros(n_cols))
        mat[ri, :len(vals)] = vals[:n_cols]

    if vmax is None:
        vmax = max(np.abs(mat).max(), 1e-6)

    cell_w = width / n_cols
    cell_h = height / n_rows

    # Starting corner (top-left)
    x0 = cx - width / 2
    y0 = cy + height / 2  # top

    norm = mcolors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

    for ri in range(n_rows):
        for ci in range(n_cols):
            val = mat[ri, ci]
            color = TRAJ_CMAP(norm(val))
            is_hl = (ri, ci) in highlight_cells
            rect = plt.Rectangle(
                (x0 + ci * cell_w, y0 - (ri + 1) * cell_h),
                cell_w, cell_h,
                facecolor=color,
                edgecolor="#FFD600" if is_hl else "gray",
                lw=1.8 if is_hl else 0.3,
                zorder=5,
            )
            ax.add_patch(rect)
            # Value label
            text_color = "white" if abs(val) > 0.6 * vmax else "black"
            ax.text(x0 + (ci + 0.5) * cell_w,
                    y0 - (ri + 0.5) * cell_h,
                    f"{val:+.2f}" if abs(val) >= 0.005 else "0",
                    ha="center", va="center", fontsize=fontsize,
                    color=text_color, zorder=6, clip_on=False)

    # Row labels (left side)
    for ri, lbl in enumerate(row_labels):
        ax.text(x0 - 0.003, y0 - (ri + 0.5) * cell_h,
                lbl, ha="right", va="center", fontsize=fontsize,
                color="gray", zorder=6, clip_on=False)

    # Column headers (step numbers)
    for ci in range(n_cols):
        ax.text(x0 + (ci + 0.5) * cell_w, y0 + 0.003,
                f"s{ci}", ha="center", va="bottom", fontsize=fontsize - 0.5,
                color="gray", zorder=6, clip_on=False)


def _draw_sigmoid_inset(ax, cx, cy, width, height, traj_data, beta=5.0,
                        step=None):
    """
    Draw a small tanh(beta*z) curve with 3 operating-point markers
    (ppk23, ppk25, both) at a single propagation step.

    step : which propagation step to show (default: last).
    """
    n_steps = len(traj_data.get("ppk23", [0])) - 1
    if step is None:
        step = n_steps  # use final step

    # Background
    rect = plt.Rectangle((cx - width / 2, cy - height / 2), width, height,
                          facecolor="white", edgecolor="gray", lw=0.4,
                          zorder=4, alpha=0.9)
    ax.add_patch(rect)

    # Draw rectified sigmoid curve: max(0, tanh(beta * z))
    z_max = 0.6  # beyond this the sigmoid is essentially flat
    zz = np.linspace(-z_max, z_max, 80)
    yy = np.maximum(np.tanh(beta * zz), 0.0)

    def _map(z_val, y_val):
        """Map function space → data coords within the inset."""
        px = cx - width / 2 + (z_val + z_max) / (2 * z_max) * width
        py = cy - height / 2 + (y_val + 1.0) / 2.0 * height
        return px, py

    # Curve
    curve_x = [_map(z, y)[0] for z, y in zip(zz, yy)]
    curve_y = [_map(z, y)[1] for z, y in zip(zz, yy)]
    ax.plot(curve_x, curve_y, color="gray", lw=0.8, zorder=5, alpha=0.5)

    # Zero crosshairs
    zx0, zy0 = _map(0, -1)
    zx1, zy1 = _map(0, 1)
    ax.plot([zx0, zx1], [zy0, zy1], color="gray", lw=0.3, ls=":", zorder=5, alpha=0.3)
    hx0, hy0 = _map(-z_max, 0)
    hx1, hy1 = _map(z_max, 0)
    ax.plot([hx0, hx1], [hy0, hy1], color="gray", lw=0.3, ls=":", zorder=5, alpha=0.3)

    # 3 markers: ppk23, ppk25, both — at the chosen step
    markers = [
        ("ppk23", "pre_ppk23", "#FFC107", "o"),
        ("ppk25", "pre_ppk25", "#8D6E63", "s"),
        ("both",  "pre_both",  "#7B1FA2", "D"),
    ]
    for cond, pre_key, color, marker in markers:
        post = traj_data.get(cond)
        pre = traj_data.get(pre_key)
        if post is None or pre is None:
            continue
        if step >= len(post):
            continue
        z = pre[step]
        a = post[step]
        if np.isnan(z):
            continue
        z_cl = np.clip(z, -z_max, z_max)
        a_cl = np.clip(a, -1.0, 1.0)
        px, py = _map(z_cl, a_cl)
        ax.plot(px, py, marker, color=color, markersize=5,
                zorder=7, markeredgecolor="black", markeredgewidth=0.4,
                alpha=0.7)

    # Tiny label
    ax.text(cx, cy + height / 2 + 0.002, f"σ(z) s{step}", ha="center",
            va="bottom", fontsize=3.5, color="gray", zorder=6)


def _draw_node_with_traj(ax, xy, name_label, width, height,
                         facecolor, edgecolor="black", lw=1.5,
                         fontsize=8, fontweight="normal", zorder=3,
                         traj_data=None, n_steps=3, vmax=None,
                         highlight_cells=None, sigmoid_step=None):
    """
    Draw a node box with name at top, mini-heatmap on left, sigmoid inset on right.

    highlight_cells : set of (row, col) for bold yellow borders on input cells.
    sigmoid_step : which propagation step to show on the sigmoid (default: last).
                   Use the step matching the node's column: 0=sensory, 1=step1, etc.
    """
    x, y = xy
    box = FancyBboxPatch(
        (x - width / 2, y - height / 2), width, height,
        boxstyle="round,pad=0.01", facecolor=facecolor,
        edgecolor=edgecolor, lw=lw, zorder=zorder,
    )
    ax.add_patch(box)

    if traj_data is not None:
        # Name at top of box
        ax.text(x, y + height / 2 - 0.012, name_label,
                ha="center", va="top", fontsize=fontsize,
                fontweight=fontweight, zorder=zorder + 1, clip_on=False)

        # Split lower area: heatmap (left 58%) + sigmoid inset (right 36%)
        inner_w = width * 0.92
        hm_width = inner_w * 0.58
        sig_width = inner_w * 0.36
        gap = inner_w * 0.06

        inner_left = x - inner_w / 2
        hm_cx = inner_left + hm_width / 2
        sig_cx = inner_left + hm_width + gap + sig_width / 2

        hm_height = height * 0.55
        hm_cy = y - height * 0.12

        _draw_mini_heatmap(ax, hm_cx, hm_cy, hm_width, hm_height,
                           traj_data, n_steps, vmax=vmax,
                           highlight_cells=highlight_cells)

        # Sigmoid operating-point inset (same vertical region as heatmap)
        has_pre = "pre_ppk23" in traj_data
        if has_pre:
            _draw_sigmoid_inset(ax, sig_cx, hm_cy, sig_width, hm_height,
                                traj_data, step=sigmoid_step)
    else:
        ax.text(x, y, name_label, ha="center", va="center",
                fontsize=fontsize, fontweight=fontweight,
                zorder=zorder + 1, clip_on=False)
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
        zorder=zorder, alpha=alpha, mutation_scale=10,
    )
    ax.add_patch(arrow)
    if label:
        mx = (xy_from[0] + xy_to[0]) / 2 + label_offset[0]
        my = (xy_from[1] + xy_to[1]) / 2 + label_offset[1]
        ax.text(mx, my, label, fontsize=label_fontsize,
                ha="center", va="center", color=color, zorder=zorder + 1,
                bbox=dict(boxstyle="round,pad=0.08", fc="white",
                          ec="none", alpha=0.85))


# ═══════════════════════════════════════════════════════════════════
# Data building
# ═══════════════════════════════════════════════════════════════════

def build_trajectory_data(target_name, grp, W_csc, x23_lin, x25_lin,
                          idx_to_type, type_to_idx, type_to_nt, type_to_inhib,
                          ppk23_types, ppk25_types, prop_sig, s_ppk23, s_ppk25):
    """Build multi-hop path data with full activation trajectories."""
    t_idx = type_to_idx[target_name]

    # ── Full trajectories (shape: n_steps+1 x N) ──
    traj_23 = prop_sig.propagate_trajectory(s_ppk23, N_STEPS, sustained=True)
    traj_25 = prop_sig.propagate_trajectory(s_ppk25, N_STEPS, sustained=True)
    traj_both = prop_sig.propagate_trajectory(s_ppk23 + s_ppk25, N_STEPS, sustained=True)
    traj_delta = traj_both - traj_23 - traj_25  # interaction at each step

    # ── Pre-activation trajectories (input to sigmoid, before nonlinearity) ──
    # At step 0: raw input (no sigmoid applied). Steps 1+: z = W.T @ x(t) + s0.
    def _pre_traj(s0):
        x = s0.copy().astype(np.float64)
        n = len(s0)
        pre = np.full((N_STEPS + 1, n), np.nan)
        pre[0] = s0  # step 0 is raw input, no sigmoid
        for t in range(N_STEPS):
            z = prop_sig.Wt.dot(x) + s0  # sustained
            pre[t + 1] = z
            x = prop_sig.activation_fn(z, **prop_sig.activation_params)
        return pre

    pre_23 = _pre_traj(s_ppk23)
    pre_25 = _pre_traj(s_ppk25)
    pre_both = _pre_traj(s_ppk23 + s_ppk25)

    # Target final activations
    a23 = traj_23[-1, t_idx]
    a25 = traj_25[-1, t_idx]
    ab = traj_both[-1, t_idx]
    rij = ab - a23 - a25
    cat = "super" if rij > 0 else "destructive"

    # R_ij trajectory at the target
    rij_traj = traj_delta[:, t_idx]

    def _node_traj(idx):
        """Extract per-step activation + pre-activation for one neuron."""
        return {
            "ppk23": traj_23[:, idx],
            "ppk25": traj_25[:, idx],
            "both":  traj_both[:, idx],
            "delta": traj_delta[:, idx],
            "pre_ppk23": pre_23[:, idx],
            "pre_ppk25": pre_25[:, idx],
            "pre_both":  pre_both[:, idx],
        }

    # ── Step 2 neurons (presynaptic to target) ──
    col_t = W_csc[:, t_idx].toarray().ravel()
    pre_t_indices = np.nonzero(col_t)[0]

    step2_rows = []
    for pi in pre_t_indices:
        ptype = idx_to_type.get(pi, f"idx_{pi}")
        w = col_t[pi]
        d23 = x23_lin[2][pi]
        d25 = x25_lin[2][pi]
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
            "traj": _node_traj(pi),
        })

    df_s2 = pd.DataFrame(step2_rows)
    if len(df_s2) == 0:
        return None

    df_s2["abs_total"] = df_s2["eff_23"].abs() + df_s2["eff_25"].abs()
    df_s2 = df_s2.sort_values("abs_total", ascending=False)

    total_sig = df_s2["abs_total"].sum()
    if total_sig > 1e-12:
        df_s2["cum_frac"] = df_s2["abs_total"].cumsum() / total_sig
        n_need = max(3, int((df_s2["cum_frac"] <= 0.80).sum()) + 1)
    else:
        n_need = 3
    n_need = min(n_need, 6, len(df_s2))
    df_s2 = df_s2.head(n_need).reset_index(drop=True)

    # ── Step 1 neurons (presynaptic to each step 2 neuron) ──
    step1_neurons = {}
    edges_s1_to_s2 = []

    for _, s2_row in df_s2.iterrows():
        s2_name = s2_row["neuron"]
        s2_idx = int(s2_row["idx"])

        col_s2 = W_csc[:, s2_idx].toarray().ravel()
        pre_s2 = np.nonzero(col_s2)[0]

        s1_contribs = []
        for pp in pre_s2:
            pp_type = idx_to_type.get(pp, f"idx_{pp}")
            pp_w = col_s2[pp]
            pp_d23_s1 = x23_lin[1][pp]
            pp_d25_s1 = x25_lin[1][pp]
            pp_d23_s0 = x23_lin[0][pp]
            pp_d25_s0 = x25_lin[0][pp]

            is_s23 = pp_type in ppk23_types
            is_s25 = pp_type in ppk25_types

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
                    "traj": _node_traj(pp),
                })

        s1_contribs.sort(key=lambda x: abs(x["eff23"]) + abs(x["eff25"]),
                         reverse=True)
        for s1c in s1_contribs[:2]:
            s1_name = s1c["neuron"]
            if s1_name not in step1_neurons:
                step1_neurons[s1_name] = s1c
            edges_s1_to_s2.append({
                "s1": s1_name, "s2": s2_name,
                "w": s1c["w"], "eff23": s1c["eff23"], "eff25": s1c["eff25"],
            })

    # ── Sensory connections to step 1 ──
    edges_sens_to_s1 = []
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

    for s1_name, s1_info in step1_neurons.items():
        if s1_info["is_ppk23_sensory"]:
            edges_sens_to_s1.append({
                "sensory": s1_name, "channel": "ppk23",
                "s1": s1_name, "w": None,
            })
        if s1_info["is_ppk25_sensory"]:
            edges_sens_to_s1.append({
                "sensory": s1_name, "channel": "ppk25",
                "s1": s1_name, "w": None,
            })

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

    # Global vmax for consistent color scale across all nodes in this diagram
    all_vals = []
    for _, row in df_s2.iterrows():
        for key in ("ppk23", "ppk25", "both", "delta"):
            all_vals.extend(row["traj"][key])
    for s1_info in step1_neurons.values():
        for key in ("ppk23", "ppk25", "both", "delta"):
            all_vals.extend(s1_info["traj"][key])
    target_traj = _node_traj(t_idx)
    for key in ("ppk23", "ppk25", "both", "delta"):
        all_vals.extend(target_traj[key])
    global_vmax = max(np.abs(all_vals).max(), 1e-4)

    # Sensory pool trajectories (average across all sensory neurons in each channel)
    ppk23_indices = [type_to_idx[t] for t in ppk23_types if t in type_to_idx]
    ppk25_indices = [type_to_idx[t] for t in ppk25_types if t in type_to_idx]

    def _pool_traj(indices):
        """Average trajectory across a pool of neurons."""
        z = N_STEPS + 1
        if not indices:
            return {"ppk23": np.zeros(z), "ppk25": np.zeros(z),
                    "both": np.zeros(z), "delta": np.zeros(z),
                    "pre_ppk23": np.full(z, np.nan), "pre_ppk25": np.full(z, np.nan),
                    "pre_both": np.full(z, np.nan)}
        return {
            "ppk23": traj_23[:, indices].mean(axis=1),
            "ppk25": traj_25[:, indices].mean(axis=1),
            "both":  traj_both[:, indices].mean(axis=1),
            "delta": traj_delta[:, indices].mean(axis=1),
            "pre_ppk23": pre_23[:, indices].mean(axis=1),
            "pre_ppk25": pre_25[:, indices].mean(axis=1),
            "pre_both":  pre_both[:, indices].mean(axis=1),
        }

    sens23_traj = _pool_traj(ppk23_indices)
    sens25_traj = _pool_traj(ppk25_indices)

    # Include sensory values in global vmax
    for t in (sens23_traj, sens25_traj):
        for key in ("ppk23", "ppk25", "both", "delta"):
            all_vals.extend(t[key])
    global_vmax = max(np.abs(all_vals).max(), 1e-4)

    net_23 = col_t[pre_t_indices] @ np.array([x23_lin[2][i] for i in pre_t_indices])
    net_25 = col_t[pre_t_indices] @ np.array([x25_lin[2][i] for i in pre_t_indices])

    return {
        "target": target_name, "group": grp, "category": cat,
        "a23": a23, "a25": a25, "a_both": ab, "rij": rij,
        "rij_traj": rij_traj,
        "target_traj": target_traj,
        "sens23_traj": sens23_traj,
        "sens25_traj": sens25_traj,
        "net_23": net_23, "net_25": net_25,
        "step2": df_s2,
        "step1": step1_neurons,
        "edges_s1_s2": edges_s1_to_s2,
        "sens_agg": sens_agg,
        "global_vmax": global_vmax,
    }


# ═══════════════════════════════════════════════════════════════════
# Drawing
# ═══════════════════════════════════════════════════════════════════

def draw_trajectory_circuit(data):
    """Draw the circuit diagram with per-step activation heatmaps."""
    target = data["target"]
    cat = data["category"]
    grp = data["group"]
    df_s2 = data["step2"]
    step1 = data["step1"]
    edges_s1_s2 = data["edges_s1_s2"]
    sens_agg = data["sens_agg"]
    gvmax = data["global_vmax"]

    n_s2 = len(df_s2)
    n_s1 = len(step1)
    n_rows = max(n_s2, n_s1, 4)

    # Wide figure — extra horizontal space for arrows between columns
    fig_h = max(10, 1.4 * n_rows + 5)
    fig, ax = plt.subplots(figsize=(52, fig_h))
    ax.set_xlim(-0.02, 1.02)
    y_top = 1.02
    y_bot = -0.02
    ax.set_ylim(y_bot - 0.22, y_top + 0.03)
    ax.axis("off")

    # Column positions — equally spaced
    x_sens = 0.125
    x_s1 = 0.375
    x_s2 = 0.625
    x_target = 0.875

    # Node dimensions — wide enough for heatmap + sigmoid inset
    node_w = 0.16
    node_h = 0.09
    tgt_w = 0.16
    tgt_h = 0.11

    # ── Column headers ──
    ax.text(x_sens, y_top + 0.02, "Sensory\n(step 0)", ha="center",
            fontsize=9, fontweight="bold", color="gray")
    ax.text(x_s1, y_top + 0.02, "Step 1\n(1-hop from sensory)", ha="center",
            fontsize=9, fontweight="bold", color="gray")
    ax.text(x_s2, y_top + 0.02, "Step 2\n(presynaptic to target)", ha="center",
            fontsize=9, fontweight="bold", color="gray")
    ax.text(x_target, y_top + 0.02, "Target\n(step 3)", ha="center",
            fontsize=9, fontweight="bold", color="gray")

    # ── Sensory pools ──
    # Highlight s0 cells: ppk23 row (0) and both row (2) for ppk23 pool,
    # ppk25 row (1) and both row (2) for ppk25 pool — these are the
    # input cells where the sensory neurons broadcast 1.0 from step 0.
    y_ppk23 = 0.72
    y_ppk25 = 0.28
    _draw_node_with_traj(ax, (x_sens, y_ppk23), "ppk23 sensory",
                         node_w, node_h, COL_PPK23, lw=2, fontsize=8,
                         fontweight="bold",
                         traj_data=data["sens23_traj"], n_steps=N_STEPS,
                         vmax=gvmax,
                         highlight_cells={(0, 0), (2, 0)}, sigmoid_step=1)
    _draw_node_with_traj(ax, (x_sens, y_ppk25), "ppk25 sensory",
                         node_w, node_h, COL_PPK25, lw=2, fontsize=8,
                         fontweight="bold",
                         traj_data=data["sens25_traj"], n_steps=N_STEPS,
                         vmax=gvmax,
                         highlight_cells={(1, 0), (2, 0)}, sigmoid_step=1)

    # ── Target ──
    target_color = COL_SUPER if cat == "super" else COL_DESTR
    target_fill = "#FFEBEE" if cat == "super" else "#E3F2FD"
    cat_label = "SUPER" if cat == "super" else "DESTRUCTIVE"
    _draw_node_with_traj(ax, (x_target, 0.50), f"{target}\n({grp})",
                         tgt_w, tgt_h, target_fill, edgecolor=target_color,
                         lw=3, fontsize=10, fontweight="bold",
                         traj_data=data["target_traj"], n_steps=N_STEPS,
                         vmax=gvmax, sigmoid_step=3)

    # ── Step 1 neurons ──
    s1_names = list(step1.keys())
    s1_ys = np.linspace(0.92, 0.08, n_s1) if n_s1 > 0 else []
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

        sens_mark = ""
        hl_cells = None
        if info.get("is_ppk23_sensory"):
            fill = COL_SENSORY_23
            sens_mark = " (ppk23 s.)"
            # This neuron broadcasts 1.0 from step 0 under ppk23 & both
            hl_cells = {(0, 0), (2, 0)}
        elif info.get("is_ppk25_sensory"):
            fill = COL_SENSORY_25
            sens_mark = " (ppk25 s.)"
            # This neuron broadcasts 1.0 from step 0 under ppk25 & both
            hl_cells = {(1, 0), (2, 0)}

        label = f"{s1_name} [{tag},{nt_short}]{sens_mark}"
        _draw_node_with_traj(ax, (x_s1, y), label, node_w, node_h, fill,
                             edgecolor=edge, lw=1.0, fontsize=6.5,
                             traj_data=info["traj"], n_steps=N_STEPS,
                             vmax=gvmax, highlight_cells=hl_cells,
                             sigmoid_step=1)
        s1_pos[s1_name] = (x_s1, y)

    # ── Step 2 neurons ──
    s2_ys = np.linspace(0.92, 0.08, n_s2) if n_s2 > 0 else []
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

        label = f"{name} [{tag},{nt_short}]"
        _draw_node_with_traj(ax, (x_s2, y), label, node_w, node_h, fill,
                             edgecolor=edge, lw=1.0, fontsize=6.5,
                             traj_data=row["traj"], n_steps=N_STEPS,
                             vmax=gvmax, sigmoid_step=2)
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
            arr_color = COL_PPK23 if ch == "ppk23" else COL_PPK25
            _draw_arrow(ax, (sx + node_w / 2 + 0.01, sy),
                        (tx - node_w / 2 - 0.01, ty),
                        arr_color, lw=1.5, style="-|>",
                        label=f"{ch} (IS sensory)", label_fontsize=6,
                        connectionstyle=f"arc3,rad={0.05 if ty > sy else -0.05}")
        elif abs(agg["total_w"]) > 1e-10:
            n_sens = len(agg["sensory_list"])
            arr_color = COL_EXC if agg["total_w"] > 0 else COL_INH
            lw = min(3.0, max(0.6, abs(agg["total_w"]) * 4))
            rad = 0.08 if ty > sy else (-0.08 if ty < sy else 0.02)
            label_str = f"{ch} (n={n_sens})\nw={agg['total_w']:+.3f}"
            _draw_arrow(ax, (sx + node_w / 2 + 0.01, sy),
                        (tx - node_w / 2 - 0.01, ty),
                        arr_color, lw=lw, label=label_str,
                        label_fontsize=6, connectionstyle=f"arc3,rad={rad}")

    # ── Arrows: step 1 → step 2 ──
    s1s2_edges = {}
    for e in edges_s1_s2:
        key = (e["s1"], e["s2"])
        if key not in s1s2_edges:
            s1s2_edges[key] = e

    for (s1_name, s2_name), e in s1s2_edges.items():
        if s1_name not in s1_pos or s2_name not in s2_pos:
            continue
        sx, sy = s1_pos[s1_name]
        tx, ty = s2_pos[s2_name]
        arr_color = COL_EXC if e["w"] > 0 else COL_INH
        lw = min(3.0, max(0.5, (abs(e["eff23"]) + abs(e["eff25"])) * 80))
        rad = 0.06 if abs(ty - sy) < 0.03 else 0.0
        _draw_arrow(ax, (sx + node_w / 2 + 0.01, sy),
                    (tx - node_w / 2 - 0.01, ty),
                    arr_color, lw=lw, label=f"w={e['w']:+.3f}",
                    label_fontsize=6,
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
        rad = 0.04 if abs(sy - 0.50) < 0.04 else 0.0
        label = f"w={w:+.4f}"
        _draw_arrow(ax, (sx + node_w / 2 + 0.01, sy),
                    (x_target - tgt_w / 2 - 0.01, 0.50),
                    arr_color, lw=lw, label=label,
                    label_fontsize=6,
                    connectionstyle=f"arc3,rad={rad}")

    # ── Summary box with R_ij trajectory ──
    net23 = data["net_23"]
    net25 = data["net_25"]
    same_sign = (net23 > 0 and net25 > 0) or (net23 < 0 and net25 < 0)
    sign_label = "SAME sign" if same_sign else "OPPOSITE sign"

    rij_traj = data["rij_traj"]
    rij_str = "  ".join([f"s{i}={rij_traj[i]:+.4f}" for i in range(len(rij_traj))])

    summary = (
        f"A(ppk23) = {data['a23']:+.4f}    A(ppk25) = {data['a25']:+.4f}\n"
        f"A(both)  = {data['a_both']:+.4f}    R_ij = {data['rij']:+.4f} ({cat_label})\n"
        f"────────────────────────────\n"
        f"R_ij trajectory:  {rij_str}\n"
        f"────────────────────────────\n"
        f"Net drives: ppk23={net23:+.5f} ppk25={net25:+.5f} ({sign_label})\n"
    )
    both_negative = (net23 < 0 and net25 < 0)
    both_positive = (net23 > 0 and net25 > 0)
    opposite = not same_sign

    if cat == "super" and opposite:
        summary += "Mechanism: push-pull / de-saturation"
    elif cat == "super" and both_negative:
        summary += "Mechanism: floor saturation (sublinear inhibition)"
    elif cat == "destructive" and both_positive:
        summary += "Mechanism: ceiling saturation (sublinear excitation)"
    elif cat == "destructive":
        summary += "Mechanism: saturating nonlinearity"
    else:
        summary += "Mechanism: network-level interaction"

    box_color = "#FFEBEE" if cat == "super" else "#E3F2FD"
    ax.text(0.72, y_bot - 0.04, summary, transform=ax.transAxes,
            fontsize=8, va="top", ha="center", family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", fc=box_color,
                      ec=target_color, lw=1.5, alpha=0.95))

    # ── Legend ──
    legend_text = (
        "LEGEND\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "NODE HEATMAPS (left, 4 rows × 4 cols)\n"
        "  Rows: 23=ppk23, 25=ppk25,\n"
        "    B=both, Δ=interaction\n"
        "  Cols: s0, s1, s2, s3 = steps\n"
        "  Color: blue=neg, white=0, red=pos\n"
        "  Yellow border = sensory input (s0=1.0)\n"
        "\n"
        "SIGMOID INSET σ(z) (right of heatmap)\n"
        "  Gray curve = max(0, tanh(5z))\n"
        "  Dots = operating point (pre→post)\n"
        "    Amber = ppk23, Brown = ppk25,\n"
        "    Purple = both\n"
        "  Dot size: s1=small, s2=med, s3=large\n"
        "  Near midline = linear regime\n"
        "  Near edges = saturated regime\n"
        "\n"
        "ARROWS\n"
        "  Blue = excitatory (+weight)\n"
        "  Red  = inhibitory (-weight)\n"
        "  Thickness ∝ |contribution|\n"
        "\n"
        "NODES\n"
        "  Light blue = EXC neuron\n"
        "  Light red  = INH neuron\n"
        "  Amber/brown = sensory\n"
    )
    ax.text(0.01, y_bot - 0.04, legend_text, transform=ax.transAxes,
            fontsize=7, va="top", ha="left", family="monospace",
            bbox=dict(boxstyle="round,pad=0.3", fc="#F5F5F5",
                      ec="gray", lw=0.6, alpha=0.95))

    # ── Colorbar ──
    sm = plt.cm.ScalarMappable(cmap=TRAJ_CMAP,
                                norm=mcolors.TwoSlopeNorm(vmin=-gvmax, vcenter=0, vmax=gvmax))
    sm.set_array([])
    cbar_ax = fig.add_axes([0.35, 0.01, 0.15, 0.012])
    cb = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cb.set_label("Activation", fontsize=7)
    cb.ax.tick_params(labelsize=6)

    # ── Title ──
    ax.set_title(
        f"Circuit trajectory: {target} ({grp}) — {cat_label}\n"
        f"R_ij(ppk23 × ppk25) = {data['rij']:+.4f}    "
        f"(steps 0→{N_STEPS}, rectified sigmoid β=5, sustained)",
        fontsize=13, fontweight="bold", color=target_color, pad=18,
    )

    return fig


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

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

    # Linear pulse propagation (for drive decomposition)
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

            data = build_trajectory_data(
                target_name, grp_short, W_csc, x23, x25,
                idx_to_type, type_to_idx, type_to_nt, type_to_inhib,
                ppk23_types, ppk25_types, prop_sig, s_ppk23, s_ppk25,
            )
            if data is None:
                logger.warning("  %s: no step 2 neurons, skipping", target_name)
                continue

            fig = draw_trajectory_circuit(data)
            fname = f"circuit_trajectory_{target_name}"
            fig.savefig(grp_dir / "png" / f"{fname}.png")
            fig.savefig(grp_dir / "pdf" / f"{fname}.pdf")
            logger.info("    Saved: %s/%s", grp_short, fname)
            plt.close(fig)
            total_count += 1

    logger.info("Done! %d trajectory diagrams in %s", total_count, OUT_DIR)


if __name__ == "__main__":
    main()
