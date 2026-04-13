#!/usr/bin/env python3
"""
Extract individual panels as standalone publication-ready figures.

Outputs all panels to plots/output/png/ and plots/output/pdf/
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path

BASE = Path(__file__).resolve().parent
PLOT_DIR = BASE / "plots"
OUT = PLOT_DIR / "output"
(OUT / "png").mkdir(parents=True, exist_ok=True)
(OUT / "pdf").mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 13, "axes.labelsize": 11,
    "xtick.labelsize": 9, "ytick.labelsize": 9,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "pdf.fonttype": 42,
})

FOCAL_NEURONS = {
    "aspf": {"destructive": ["LH006m", "LH003m", "LH002m"], "super": ["LH008m", "LH001m"]},
    "aspg": {"destructive": ["AVLP700m", "AVLP704m"], "super": ["AVLP750m"]},
    "vAB3_downstream": {"destructive": ["mAL_m3c", "mAL_m3b", "FLA001m"], "super": ["mAL_m2a", "AVLP728m"]},
    "PPN1_downstream": {"destructive": ["AVLP606", "CB1119,CB1989", "AVLP508"], "super": []},
}


def save(fig, name):
    fig.savefig(OUT / "png" / f"{name}.png")
    fig.savefig(OUT / "pdf" / f"{name}.pdf")
    print(f"  Saved: {name}")
    plt.close(fig)


def focal_list():
    rows = []
    for tg, groups in FOCAL_NEURONS.items():
        for cat, neurons in groups.items():
            for n in neurons:
                rows.append((n, tg, cat))
    return rows


# =========================================================================
# 1. Steps sweep (R_ij vs propagation depth)
# =========================================================================
def panel_steps_sweep():
    print("Panel: steps_sweep")
    df = pd.read_csv(PLOT_DIR / "summary" / "steps_sweep.csv")
    fl = focal_list()

    fig, ax = plt.subplots(figsize=(10, 6))
    for neuron, tg, cat in fl:
        df_n = df[df["target_type"] == neuron]
        if df_n.empty:
            continue
        color = "#E41A1C" if cat == "super" else "#377EB8"
        ls = "-" if cat == "super" else "--"
        ax.plot(df_n["n_steps"], df_n["R_ij"], f"o{ls}", color=color,
                label=f"{neuron} ({cat})", lw=1.5, ms=5)

    ax.set_xlabel("Number of propagation steps")
    ax.set_ylabel(r"$R_{ij}$ (ppk23 × ppk25)")
    ax.set_title("PPK23 × PPK25 interaction vs propagation depth")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.legend(fontsize=6, ncol=3, loc="upper center",
              bbox_to_anchor=(0.5, -0.12), framealpha=0.9)
    ax.set_xticks(range(1, 7))
    fig.subplots_adjust(bottom=0.25)
    save(fig, "steps_sweep")


# =========================================================================
# 2. AN09B017 panel D — Interaction signal δ at hubs across steps
# =========================================================================
def panel_an09b017_D():
    print("Panel: an09b017_panel_D")
    df_traj = pd.read_csv(PLOT_DIR / "followup" / "an09b017_trajectories.csv")
    an09_members = df_traj["hub"].unique()

    fig, ax = plt.subplots(figsize=(7, 5))
    for an in an09_members:
        an_data = df_traj[df_traj["hub"] == an]
        if not an_data.empty:
            ax.plot(an_data["step"], an_data["delta"], "o-", label=an, lw=1.5, ms=5)
    ax.set_xlabel("Propagation step")
    ax.set_ylabel("δ = A(both) − A(ppk23) − A(ppk25)")
    ax.set_title("Interaction signal at AN09B017 hubs")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    save(fig, "an09b017_panel_D_interaction_signal")


# =========================================================================
# 3. AN09B017 panel E — Channel preference
# =========================================================================
def panel_an09b017_E():
    print("Panel: an09b017_panel_E")
    df_traj = pd.read_csv(PLOT_DIR / "followup" / "an09b017_trajectories.csv")

    # Use step 2 (N_STEPS - 1 = 2 when N_STEPS=3)
    step2 = df_traj[df_traj["step"] == 2].copy()
    if step2.empty:
        step2 = df_traj[df_traj["step"] == df_traj["step"].max()].copy()

    step2["preference"] = step2["A_ppk23"] - step2["A_ppk25"]
    colors = ["#FFD92F" if p > 0 else "#E5C494" for p in step2["preference"]]

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.barh(range(len(step2)), step2["preference"], color=colors,
            edgecolor="black", lw=0.5)
    ax.set_yticks(range(len(step2)))
    ax.set_yticklabels(step2["hub"], fontsize=9)
    ax.set_xlabel("A(ppk23) − A(ppk25)")
    ax.set_title("Channel preference at AN09B017")
    ax.axvline(0, color="black", lw=0.8)
    fig.tight_layout()
    save(fig, "an09b017_panel_E_channel_preference")


# =========================================================================
# 4. Deep trace panel A — R_ij vs sigmoid steepness
# =========================================================================
def panel_deep_trace_A():
    print("Panel: deep_trace_panel_A")
    df_rij = pd.read_csv(PLOT_DIR / "deep_trace" / "rij_across_nonlinearities.csv")

    focal_targets = {}
    for tg, groups in FOCAL_NEURONS.items():
        for cat, neurons in groups.items():
            for n in neurons:
                focal_targets[n] = (tg, cat)

    sig_data = df_rij[df_rij["nonlinearity"] == "sigmoid_rectified"]

    fig, ax = plt.subplots(figsize=(8, 6))
    for name in focal_targets:
        grp, cat = focal_targets[name]
        color = "#E41A1C" if cat == "super" else "#377EB8"
        ls = "-" if cat == "super" else "--"
        data = sig_data[sig_data["neuron"] == name].sort_values("beta")
        if len(data) > 0:
            ax.plot(data["beta"], data["R_ij"], f"o{ls}", color=color, lw=1.5,
                    ms=4, label=f"{name} ({cat[:3]})")
    ax.set_xlabel("Sigmoid β (steepness)")
    ax.set_ylabel(r"$R_{ij}$ (interaction score)")
    ax.set_title(r"$R_{ij}$ vs sigmoid steepness" + "\nSign is stable, magnitude scales with β")
    ax.axhline(0, color="black", lw=0.8, ls=":")
    ax.set_xscale("log")
    ax.legend(fontsize=5.5, ncol=2, loc="lower left",
              bbox_to_anchor=(0.0, 0.0), framealpha=0.85)
    fig.tight_layout()
    save(fig, "deep_trace_panel_A_rij_vs_beta")


# =========================================================================
# 5. Deep trace panel E — Sigmoid saturation schematic
# =========================================================================
def panel_deep_trace_E():
    print("Panel: deep_trace_panel_E")

    fig, ax = plt.subplots(figsize=(8, 6))
    x_range = np.linspace(-3, 3, 200)
    y_range = np.tanh(2.0 * x_range)
    ax.plot(x_range, y_range, "k-", lw=2.5)
    ax.set_xlabel("Total input (linear drive)")
    ax.set_ylabel("Output (after activation)")
    ax.set_title("Why saturation reveals circuit structure")

    # Same-sign case (destructive)
    x1, x2 = 0.8, 1.0
    x_both = x1 + x2
    y1 = np.tanh(2 * x1); y2 = np.tanh(2 * x2); yb = np.tanh(2 * x_both)
    ax.axvline(x1, color="#377EB8", ls="--", alpha=0.5, lw=0.8)
    ax.axvline(x2, color="#377EB8", ls=":", alpha=0.5, lw=0.8)
    ax.axvline(x_both, color="#377EB8", ls="-", alpha=0.7, lw=1.5)
    ax.annotate("ppk23", (x1, -0.1), color="#377EB8", fontsize=9, ha="center")
    ax.annotate("ppk25", (x2, -0.2), color="#377EB8", fontsize=9, ha="center")
    ax.annotate(f"both\nA(both)={yb:.2f} < {y1:.2f}+{y2:.2f}={y1+y2:.2f}\n"
                r"$R_{ij}$ < 0 (DESTRUCTIVE)",
                (x_both, yb), xytext=(2.2, 0.5), fontsize=8, color="#377EB8",
                arrowprops=dict(arrowstyle="->", color="#377EB8"),
                bbox=dict(boxstyle="round", facecolor="#E0E0FF", alpha=0.8))

    # Opposite-sign case (super)
    x1o, x2o = -0.5, 1.2
    x_botho = x1o + x2o
    y1o = np.tanh(2 * x1o); y2o = np.tanh(2 * x2o); ybo = np.tanh(2 * x_botho)
    ax.plot([x1o], [y1o], "o", color="#E41A1C", ms=8, zorder=5)
    ax.plot([x2o], [y2o], "s", color="#E41A1C", ms=8, zorder=5)
    ax.plot([x_botho], [ybo], "D", color="#E41A1C", ms=8, zorder=5)
    ax.annotate("ppk23\n(negative!)", (x1o, y1o), xytext=(-2.8, -0.3),
                fontsize=8, color="#E41A1C",
                arrowprops=dict(arrowstyle="->", color="#E41A1C"))
    ax.annotate("ppk25", (x2o, y2o), xytext=(1.5, 0.0), fontsize=8, color="#E41A1C",
                arrowprops=dict(arrowstyle="->", color="#E41A1C"))
    ax.annotate(f"both: ppk23 cancels ppk25\n" + r"$R_{ij}$ > 0 (SUPER)",
                (x_botho, ybo), xytext=(-2.5, 0.7), fontsize=8, color="#E41A1C",
                arrowprops=dict(arrowstyle="->", color="#E41A1C"),
                bbox=dict(boxstyle="round", facecolor="#FFE0E0", alpha=0.8))

    ax.axhline(0, color="gray", lw=0.5)
    ax.axvline(0, color="gray", lw=0.5)
    fig.tight_layout()
    save(fig, "deep_trace_panel_E_sigmoid_schematic")


# =========================================================================
# 6. Beta titration — sustained mode
# =========================================================================
def panel_beta_titration_sustained():
    print("Panel: beta_titration_sustained")
    df = pd.read_csv(PLOT_DIR / "artifact_analysis" / "test2_beta_titration.csv")

    focal = ["LH006m", "LH008m", "AVLP700m", "AVLP750m", "mAL_m2a", "AVLP728m",
             "mAL_m3c", "AVLP606", "LH003m", "AVLP704m"]

    fig, ax = plt.subplots(figsize=(8, 6))
    for neuron in focal:
        sub = df[(df["type"] == neuron) & (df["mode"] == "sustained")]
        if sub.empty:
            continue
        ref = sub[sub["beta"] == 5.0]
        color = "#E41A1C" if (len(ref) > 0 and ref.iloc[0]["R_ij"] > 0) else "#377EB8"
        ls = "-" if (len(ref) > 0 and ref.iloc[0]["R_ij"] > 0) else "--"
        ax.plot(sub["beta"], sub["R_ij"], f"o{ls}", color=color,
                label=neuron, lw=1.5, ms=4)
    ax.set_xlabel("Beta (sigmoid steepness)")
    ax.set_ylabel(r"$R_{ij}$")
    ax.set_title("Beta titration — SUSTAINED mode")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.set_xscale("log")
    ax.legend(fontsize=6, ncol=2, loc="lower left",
              bbox_to_anchor=(0.0, 0.0), framealpha=0.85)
    fig.tight_layout()
    save(fig, "beta_titration_sustained")


# =========================================================================
# 7. Beta titration — pulse mode
# =========================================================================
def panel_beta_titration_pulse():
    print("Panel: beta_titration_pulse")
    df = pd.read_csv(PLOT_DIR / "artifact_analysis" / "test2_beta_titration.csv")

    focal = ["LH006m", "LH008m", "AVLP700m", "AVLP750m", "mAL_m2a", "AVLP728m",
             "mAL_m3c", "AVLP606", "LH003m", "AVLP704m"]

    fig, ax = plt.subplots(figsize=(8, 6))
    for neuron in focal:
        sub = df[(df["type"] == neuron) & (df["mode"] == "pulse")]
        if sub.empty:
            continue
        ref = sub[sub["beta"] == 5.0]
        color = "#E41A1C" if (len(ref) > 0 and ref.iloc[0]["R_ij"] > 0) else "#377EB8"
        ls = "-" if (len(ref) > 0 and ref.iloc[0]["R_ij"] > 0) else "--"
        ax.plot(sub["beta"], sub["R_ij"], f"o{ls}", color=color,
                label=neuron, lw=1.5, ms=4)
    ax.set_xlabel("Beta (sigmoid steepness)")
    ax.set_ylabel(r"$R_{ij}$")
    ax.set_title("Beta titration — PULSE mode")
    ax.axhline(0, color="black", lw=0.5, ls=":")
    ax.set_xscale("log")
    ax.legend(fontsize=6, ncol=2, loc="lower left",
              bbox_to_anchor=(0.0, 0.0), framealpha=0.85)
    fig.tight_layout()
    save(fig, "beta_titration_pulse")


# =========================================================================
# 8. Sigmoid shape panel (from enhanced beta titration)
# =========================================================================
def panel_sigmoid_shapes():
    print("Panel: sigmoid_shapes")

    fig, ax = plt.subplots(figsize=(8, 6))
    x = np.linspace(-2.5, 2.5, 500)
    show_betas = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
    cmap = plt.cm.magma_r
    norm = mcolors.LogNorm(vmin=0.08, vmax=25)

    for beta in show_betas:
        y = np.tanh(beta * x)
        c = cmap(norm(beta))
        lw = 2.5 if beta == 5.0 else 1.4
        ax.plot(x, y, color=c, lw=lw, label=f"β = {beta}")

    ax.plot(x, x, color="gray", lw=0.8, ls=":", alpha=0.5, label="y = x (linear)")

    ax.annotate("near-linear\n(R_ij ≈ 0)", xy=(1.5, np.tanh(0.1 * 1.5)),
                xytext=(2.0, 0.35), fontsize=9, color="gray",
                arrowprops=dict(arrowstyle="->", color="gray", lw=0.8), ha="center")
    ax.annotate("saturating\n(R_ij diverges)", xy=(0.5, np.tanh(20.0 * 0.5)),
                xytext=(-1.5, 0.65), fontsize=9, color=cmap(norm(20.0)),
                arrowprops=dict(arrowstyle="->", color=cmap(norm(20.0)), lw=0.8), ha="center")

    ax.axvspan(0.1, 1.0, alpha=0.06, color="orange", zorder=0)
    ax.text(0.55, -0.85, "typical\noperating\nrange", fontsize=8, ha="center",
            color="darkorange", style="italic")

    ax.set_xlabel("Pre-sigmoid input (x)")
    ax.set_ylabel("f(x) = tanh(β · x)")
    ax.set_title("Activation function shape across β")
    ax.set_ylim(-1.05, 1.05)
    ax.axhline(0, color="black", lw=0.3)
    ax.axvline(0, color="black", lw=0.3)
    ax.legend(fontsize=7, loc="lower right", ncol=2)
    fig.tight_layout()
    save(fig, "sigmoid_shapes")


# =========================================================================
# 9. Ceiling saturation schematic (from enhanced beta titration panel D)
# =========================================================================
def panel_ceiling_saturation_schematic():
    print("Panel: ceiling_saturation_schematic")

    fig, ax = plt.subplots(figsize=(8, 6))
    beta_demo = 5.0
    a_vals = np.linspace(0, 1.5, 200)
    b_val = 0.5

    f_a = np.tanh(beta_demo * a_vals)
    f_b = np.tanh(beta_demo * b_val)
    f_ab = np.tanh(beta_demo * (a_vals + b_val))
    linear_sum = f_a + f_b

    ax.plot(a_vals, linear_sum, color="#377EB8", lw=2.5, label="f(a) + f(b)  [linear prediction]")
    ax.plot(a_vals, f_ab, color="#E41A1C", lw=2.5, label="f(a + b)  [actual combined]")
    ax.fill_between(a_vals, f_ab, linear_sum,
                     where=linear_sum > f_ab,
                     alpha=0.15, color="#377EB8", label="Destructive gap (ceiling sat.)")

    a_op = 0.6
    ax.annotate(r"$R_{ij}$ < 0" + "\n(destructive)",
                xy=(a_op, np.tanh(beta_demo * (a_op + b_val))),
                xytext=(a_op + 0.35, 0.4), fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#377EB8", lw=0.8),
                color="#377EB8", ha="center")

    ax.set_xlabel(f"Input a (with b = {b_val} fixed, β = {beta_demo})")
    ax.set_ylabel("Output activation")
    ax.set_title("Why saturation creates destructive interaction")
    ax.set_ylim(-0.05, 2.1)
    ax.axhline(1.0, color="gray", lw=0.5, ls=":", alpha=0.5)
    ax.text(1.4, 1.03, "tanh ceiling", fontsize=8, color="gray", ha="right")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    save(fig, "ceiling_saturation_schematic")


# =========================================================================
# MAIN
# =========================================================================
if __name__ == "__main__":
    print(f"Extracting panels to {OUT}/")
    panel_steps_sweep()
    panel_an09b017_D()
    panel_an09b017_E()
    panel_deep_trace_A()
    panel_deep_trace_E()
    panel_beta_titration_sustained()
    panel_beta_titration_pulse()
    panel_sigmoid_shapes()
    panel_ceiling_saturation_schematic()
    print(f"\nDone! All panels in {OUT}/")
