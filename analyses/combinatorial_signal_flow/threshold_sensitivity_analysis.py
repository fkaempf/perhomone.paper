#!/usr/bin/env python3
"""
Firing Threshold Sensitivity Analysis
======================================

Quantitative analysis of adding a firing threshold to the neural circuit model.

Current activation: sigmoid_rectified = max(0, tanh(5x))
Proposed:           max(0, tanh(5*(x - theta))) for various theta values

This script measures:
  1. How many neurons have non-zero activation at step 3
  2. What fraction of signal at key target neurons is preserved vs lost
  3. Whether interaction scores R_ij change qualitatively
  4. Distribution of pre-threshold activations (what % fall below each theta)
"""

import sys
import logging
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from signal_flow import (
    NetworkLoader, ChannelEncoder, SignalPropagator,
    ACTIVATIONS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

NONLINEARITY = "sigmoid_rectified"
ACT_PARAMS = {"beta": 5.0}
N_STEPS = 3
SUSTAINED = True
NORMALIZATION = "post"

THETA_VALUES = [0.0, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1]

TARGET_GROUPS_OF_INTEREST = ["aspf", "aspg", "PPN1_downstream", "vAB3_downstream"]

# Focal neurons from the investigation script
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
        "super": [],
    },
}


# =============================================================================
# Custom activation with threshold
# =============================================================================

def sigmoid_rectified_threshold(x: np.ndarray, beta: float = 5.0,
                                 theta: float = 0.0, **kwargs) -> np.ndarray:
    """Rectified sigmoid with firing threshold: max(0, tanh(beta*(x - theta))).

    When theta=0 this is identical to the standard sigmoid_rectified.
    """
    z = np.clip(beta * (x - theta), -500, 500)
    return np.maximum(np.tanh(z), 0.0)


class ThresholdPropagator:
    """Signal propagator that uses a threshold-shifted activation."""

    def __init__(self, W, theta=0.0, beta=5.0):
        self.Wt = W.T.tocsc()
        self.n = W.shape[0]
        self.theta = theta
        self.beta = beta

    def propagate(self, s0, n_steps, sustained=False):
        x = s0.copy().astype(np.float64)
        for _ in range(n_steps):
            x = self.Wt.dot(x)
            if sustained:
                x = x + s0
            x = sigmoid_rectified_threshold(x, beta=self.beta, theta=self.theta)
        return x

    def propagate_trajectory(self, s0, n_steps, sustained=False):
        x = s0.copy().astype(np.float64)
        trajectory = np.zeros((n_steps + 1, self.n))
        trajectory[0] = x
        for t in range(n_steps):
            x = self.Wt.dot(x)
            if sustained:
                x = x + s0
            # Store pre-threshold activation for analysis
            x = sigmoid_rectified_threshold(x, beta=self.beta, theta=self.theta)
            trajectory[t + 1] = x
        return trajectory

    def propagate_with_prethreshold(self, s0, n_steps, sustained=False):
        """Propagate and also return pre-threshold values at each step."""
        x = s0.copy().astype(np.float64)
        pre_threshold_values = []
        for _ in range(n_steps):
            raw = self.Wt.dot(x)
            if sustained:
                raw = raw + s0
            pre_threshold_values.append(raw.copy())
            x = sigmoid_rectified_threshold(raw, beta=self.beta, theta=self.theta)
        return x, pre_threshold_values


# =============================================================================
# Load data
# =============================================================================

def load_data():
    """Load network, channels, targets."""
    loader = NetworkLoader(str(DATA_DIR))
    W_unsigned = loader.load_adjacency_matrix(NORMALIZATION)
    type_names = loader.load_type_names()
    channels = loader.load_channels()
    targets = loader.load_targets()
    nt_map = loader.load_neurotransmitter_mapping()

    W = loader.sign_matrix(W_unsigned, type_names)

    encoder = ChannelEncoder(type_names)
    encoded_channels = encoder.encode_all(channels)

    # Build target indices
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
        "type_names": type_names,
        "channels": channels,
        "targets": targets,
        "nt_map": nt_map,
        "encoder": encoder,
        "encoded_channels": encoded_channels,
        "target_indices": target_indices,
    }


# =============================================================================
# Analysis functions
# =============================================================================

def analyse_activation_sparsity(data):
    """For each theta, count how many neurons have non-zero activation at step 3."""
    print("\n" + "="*80)
    print("SECTION 1: ACTIVATION SPARSITY — Non-zero neurons at step 3")
    print("="*80)

    W = data["W"]
    enc = data["encoded_channels"]

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    n_total = W.shape[0]

    print(f"\nNetwork size: {n_total} neurons")
    print(f"Propagation: {N_STEPS} steps, sustained={SUSTAINED}")
    print(f"{'theta':>8}  {'ppk23_nz':>10}  {'ppk25_nz':>10}  {'both_nz':>10}  "
          f"{'ppk23_%':>8}  {'ppk25_%':>8}  {'both_%':>8}")
    print("-" * 80)

    results = []
    for theta in THETA_VALUES:
        prop = ThresholdPropagator(W, theta=theta, beta=5.0)

        x_23 = prop.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
        x_25 = prop.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
        x_both = prop.propagate(s_both, N_STEPS, sustained=SUSTAINED)

        nz_23 = np.count_nonzero(x_23 > 1e-10)
        nz_25 = np.count_nonzero(x_25 > 1e-10)
        nz_both = np.count_nonzero(x_both > 1e-10)

        print(f"{theta:>8.3f}  {nz_23:>10d}  {nz_25:>10d}  {nz_both:>10d}  "
              f"{100*nz_23/n_total:>7.1f}%  {100*nz_25/n_total:>7.1f}%  "
              f"{100*nz_both/n_total:>7.1f}%")

        results.append({
            "theta": theta,
            "nz_ppk23": nz_23,
            "nz_ppk25": nz_25,
            "nz_both": nz_both,
            "pct_ppk23": 100 * nz_23 / n_total,
            "pct_ppk25": 100 * nz_25 / n_total,
            "pct_both": 100 * nz_both / n_total,
        })

    return pd.DataFrame(results)


def analyse_prethreshold_distribution(data):
    """Analyse the distribution of pre-threshold (but post-sigmoid) activations."""
    print("\n" + "="*80)
    print("SECTION 2: PRE-THRESHOLD ACTIVATION DISTRIBUTION")
    print("="*80)
    print("What fraction of activations fall below each theta value?")
    print("(These are the raw inputs to the activation function at each step,")
    print(" i.e., the values x before applying max(0, tanh(5*(x - theta))))")

    W = data["W"]
    enc = data["encoded_channels"]

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    # Use theta=0 propagator to get pre-threshold values
    # We need the RAW input to the activation function (before tanh)
    # i.e., x_raw = W.T @ x_prev (+ s0 if sustained)
    prop = ThresholdPropagator(W, theta=0.0, beta=5.0)

    for label, s0 in [("ppk23", s_ppk23), ("ppk25", s_ppk25), ("both", s_both)]:
        _, pre_thresh = prop.propagate_with_prethreshold(s0, N_STEPS, sustained=SUSTAINED)

        print(f"\n--- Signal: {label} ---")
        for step_idx, raw_vals in enumerate(pre_thresh):
            step_num = step_idx + 1
            # Only look at neurons that receive any input (raw != 0 or very small)
            active_mask = np.abs(raw_vals) > 1e-15
            active_vals = raw_vals[active_mask]
            positive_vals = active_vals[active_vals > 0]

            print(f"\n  Step {step_num}: {len(active_vals)} neurons receive non-zero input, "
                  f"{len(positive_vals)} have positive input")

            if len(positive_vals) > 0:
                percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
                pvals = np.percentile(positive_vals, percentiles)
                print(f"  Positive input distribution (percentiles):")
                for p, v in zip(percentiles, pvals):
                    print(f"    P{p:>2d} = {v:.6f}")

                print(f"\n  Fraction of POSITIVE inputs below each theta:")
                for theta in THETA_VALUES[1:]:  # skip 0
                    frac_below = np.mean(positive_vals < theta)
                    n_below = np.sum(positive_vals < theta)
                    print(f"    theta={theta:.3f}: {100*frac_below:.1f}% ({n_below}/{len(positive_vals)} neurons)")

            # Also show the negative input distribution
            negative_vals = active_vals[active_vals < 0]
            if len(negative_vals) > 0:
                print(f"\n  Negative inputs: {len(negative_vals)} neurons "
                      f"(range [{negative_vals.min():.6f}, {negative_vals.max():.6f}])")
                print(f"  (These are already zeroed by the rectification, theta does not affect them)")


def analyse_target_signal_preservation(data):
    """For each theta, what fraction of signal at key targets is preserved?"""
    print("\n" + "="*80)
    print("SECTION 3: SIGNAL PRESERVATION AT KEY TARGETS")
    print("="*80)

    W = data["W"]
    enc = data["encoded_channels"]
    encoder = data["encoder"]
    targets = data["targets"]

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    # First get baseline (theta=0) activations
    prop_base = ThresholdPropagator(W, theta=0.0, beta=5.0)
    x_both_base = prop_base.propagate(s_both, N_STEPS, sustained=SUSTAINED)
    x_23_base = prop_base.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
    x_25_base = prop_base.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)

    # Print baseline activations at target groups
    print("\nBaseline activations (theta=0) at target groups:")
    for tg in TARGET_GROUPS_OF_INTEREST:
        if tg not in targets:
            continue
        print(f"\n  {tg}:")
        for t in targets[tg]:
            if t not in encoder.type_to_idx:
                continue
            idx = encoder.type_to_idx[t]
            a23 = x_23_base[idx]
            a25 = x_25_base[idx]
            ab = x_both_base[idx]
            r = ab - a23 - a25
            print(f"    {t:>20s}: A(ppk23)={a23:.6f}  A(ppk25)={a25:.6f}  "
                  f"A(both)={ab:.6f}  R_ij={r:+.6f}")

    # Now for each theta, compute preservation
    print("\n\nSignal preservation ratio A(theta)/A(baseline) for combined (ppk23+ppk25):")
    print(f"{'neuron':>20s}", end="")
    for theta in THETA_VALUES:
        print(f"  {'theta='+str(theta):>12s}", end="")
    print()
    print("-" * (20 + 14 * len(THETA_VALUES)))

    all_results = []
    activations_by_theta = {}

    for theta in THETA_VALUES:
        prop = ThresholdPropagator(W, theta=theta, beta=5.0)
        x_both = prop.propagate(s_both, N_STEPS, sustained=SUSTAINED)
        x_23 = prop.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
        x_25 = prop.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
        activations_by_theta[theta] = (x_23, x_25, x_both)

    for tg in TARGET_GROUPS_OF_INTEREST:
        if tg not in targets:
            continue
        print(f"\n  --- {tg} ---")
        for t in targets[tg]:
            if t not in encoder.type_to_idx:
                continue
            idx = encoder.type_to_idx[t]
            base_val = x_both_base[idx]

            print(f"  {t:>20s}", end="")
            for theta in THETA_VALUES:
                x_23, x_25, x_both = activations_by_theta[theta]
                val = x_both[idx]
                if base_val > 1e-10:
                    ratio = val / base_val
                    print(f"  {ratio:>12.4f}", end="")
                else:
                    print(f"  {'N/A':>12s}", end="")

                all_results.append({
                    "target_group": tg,
                    "target_type": t,
                    "theta": theta,
                    "A_both": val,
                    "A_both_baseline": base_val,
                    "preservation_ratio": val / base_val if base_val > 1e-10 else np.nan,
                    "A_ppk23": x_23[idx],
                    "A_ppk25": x_25[idx],
                })
            print()

    # Summary: mean preservation per target group
    df = pd.DataFrame(all_results)
    print("\n\nMean preservation ratio by target group:")
    print(f"{'group':>20s}", end="")
    for theta in THETA_VALUES:
        print(f"  {'theta='+str(theta):>12s}", end="")
    print()
    print("-" * (20 + 14 * len(THETA_VALUES)))
    for tg in TARGET_GROUPS_OF_INTEREST:
        df_tg = df[df["target_group"] == tg]
        print(f"  {tg:>20s}", end="")
        for theta in THETA_VALUES:
            mean_ratio = df_tg[df_tg["theta"] == theta]["preservation_ratio"].mean()
            print(f"  {mean_ratio:>12.4f}", end="")
        print()

    return df


def analyse_interaction_scores(data):
    """For each theta, compute R_ij = A(both) - A(ppk23) - A(ppk25) at targets."""
    print("\n" + "="*80)
    print("SECTION 4: INTERACTION SCORES R_ij UNDER THRESHOLD")
    print("="*80)

    W = data["W"]
    enc = data["encoded_channels"]
    encoder = data["encoder"]
    targets = data["targets"]

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    # Collect all focal neurons
    focal_list = []
    for tg, groups in FOCAL_NEURONS.items():
        for cat, neurons in groups.items():
            for n in neurons:
                if n in encoder.type_to_idx:
                    focal_list.append((n, tg, cat, encoder.type_to_idx[n]))

    # Print R_ij for focal neurons across theta values
    print(f"\n{'neuron':>20s} {'group':>12s} {'cat':>6s}", end="")
    for theta in THETA_VALUES:
        print(f"  {'theta='+str(theta):>12s}", end="")
    print()
    print("-" * (42 + 14 * len(THETA_VALUES)))

    all_results = []

    for theta in THETA_VALUES:
        prop = ThresholdPropagator(W, theta=theta, beta=5.0)
        x_23 = prop.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
        x_25 = prop.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
        x_both = prop.propagate(s_both, N_STEPS, sustained=SUSTAINED)

        for n, tg, cat, idx in focal_list:
            r_ij = x_both[idx] - x_23[idx] - x_25[idx]
            all_results.append({
                "theta": theta,
                "neuron": n,
                "group": tg,
                "category": cat,
                "A_ppk23": x_23[idx],
                "A_ppk25": x_25[idx],
                "A_both": x_both[idx],
                "R_ij": r_ij,
            })

    df = pd.DataFrame(all_results)

    # Print focal neuron table
    for n, tg, cat, idx in focal_list:
        df_n = df[df["neuron"] == n]
        r_vals = df_n.sort_values("theta")["R_ij"].values
        print(f"  {n:>20s} {tg:>12s} {cat:>6s}", end="")
        for r in r_vals:
            print(f"  {r:>+12.6f}", end="")
        print()

    # Check for qualitative changes (sign flips)
    print("\n\nQUALITATIVE CHANGES — Sign flips in R_ij:")
    print("-" * 60)
    baseline = df[df["theta"] == 0.0]
    any_flip = False
    for n, tg, cat, idx in focal_list:
        r_base = baseline[baseline["neuron"] == n]["R_ij"].values[0]
        base_sign = "+" if r_base > 0 else ("-" if r_base < 0 else "0")

        for theta in THETA_VALUES[1:]:
            r_theta = df[(df["neuron"] == n) & (df["theta"] == theta)]["R_ij"].values[0]
            theta_sign = "+" if r_theta > 0 else ("-" if r_theta < 0 else "0")

            if base_sign != theta_sign and base_sign != "0" and theta_sign != "0":
                print(f"  SIGN FLIP: {n} ({cat}): R_ij goes from {r_base:+.6f} to "
                      f"{r_theta:+.6f} at theta={theta}")
                any_flip = True

    if not any_flip:
        print("  No sign flips detected in any focal neuron across all theta values.")

    # Also compute R_ij for ALL neurons in each target group
    print("\n\nALL TARGET NEURONS — R_ij summary by group and theta:")
    print("-" * 80)

    all_target_results = []
    for theta in THETA_VALUES:
        prop = ThresholdPropagator(W, theta=theta, beta=5.0)
        x_23 = prop.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
        x_25 = prop.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
        x_both = prop.propagate(s_both, N_STEPS, sustained=SUSTAINED)

        for tg in TARGET_GROUPS_OF_INTEREST:
            if tg not in targets:
                continue
            for t in targets[tg]:
                if t not in encoder.type_to_idx:
                    continue
                idx = encoder.type_to_idx[t]
                r_ij = x_both[idx] - x_23[idx] - x_25[idx]
                all_target_results.append({
                    "theta": theta,
                    "target_group": tg,
                    "target_type": t,
                    "R_ij": r_ij,
                    "A_both": x_both[idx],
                })

    df_all = pd.DataFrame(all_target_results)

    print(f"\n{'group':>20s}  {'metric':>12s}", end="")
    for theta in THETA_VALUES:
        print(f"  {'theta='+str(theta):>12s}", end="")
    print()
    print("-" * (36 + 14 * len(THETA_VALUES)))

    for tg in TARGET_GROUPS_OF_INTEREST:
        df_tg = df_all[df_all["target_group"] == tg]

        # Mean R_ij
        print(f"  {tg:>20s}  {'mean R_ij':>12s}", end="")
        for theta in THETA_VALUES:
            m = df_tg[df_tg["theta"] == theta]["R_ij"].mean()
            print(f"  {m:>+12.6f}", end="")
        print()

        # Fraction with positive R_ij (synergistic)
        print(f"  {'':>20s}  {'frac R>0':>12s}", end="")
        for theta in THETA_VALUES:
            vals = df_tg[df_tg["theta"] == theta]["R_ij"]
            frac = (vals > 0).mean()
            print(f"  {frac:>12.3f}", end="")
        print()

        # Fraction with negative R_ij (destructive)
        print(f"  {'':>20s}  {'frac R<0':>12s}", end="")
        for theta in THETA_VALUES:
            vals = df_tg[df_tg["theta"] == theta]["R_ij"]
            frac = (vals < 0).mean()
            print(f"  {frac:>12.3f}", end="")
        print()

        # Number of neurons with R_ij that is effectively zero
        print(f"  {'':>20s}  {'frac ~0':>12s}", end="")
        for theta in THETA_VALUES:
            vals = df_tg[df_tg["theta"] == theta]["R_ij"]
            frac = (vals.abs() < 1e-6).mean()
            print(f"  {frac:>12.3f}", end="")
        print()
        print()

    return df, df_all


def analyse_overall_network_impact(data):
    """Summary statistics of threshold impact on the whole network."""
    print("\n" + "="*80)
    print("SECTION 5: OVERALL NETWORK IMPACT")
    print("="*80)

    W = data["W"]
    enc = data["encoded_channels"]

    s_both = enc["ppk23"] + enc["ppk25"]
    n_total = W.shape[0]

    print(f"\nTotal activation magnitude across entire network (ppk23+ppk25 combined):")
    print(f"{'theta':>8}  {'sum_act':>12}  {'mean_act':>12}  {'max_act':>12}  "
          f"{'median_nz':>12}  {'nz_count':>10}  {'sum_ratio':>10}")
    print("-" * 85)

    base_sum = None
    for theta in THETA_VALUES:
        prop = ThresholdPropagator(W, theta=theta, beta=5.0)
        x = prop.propagate(s_both, N_STEPS, sustained=SUSTAINED)

        s = x.sum()
        nz = np.count_nonzero(x > 1e-10)
        nz_vals = x[x > 1e-10]

        if base_sum is None:
            base_sum = s

        ratio = s / base_sum if base_sum > 0 else 0
        median_nz = np.median(nz_vals) if len(nz_vals) > 0 else 0

        print(f"{theta:>8.3f}  {s:>12.4f}  {s/n_total:>12.6f}  {x.max():>12.6f}  "
              f"{median_nz:>12.6f}  {nz:>10d}  {ratio:>10.4f}")

    # Also for individual channels
    for ch_name, s0 in [("ppk23", enc["ppk23"]), ("ppk25", enc["ppk25"])]:
        print(f"\n{ch_name} alone:")
        print(f"{'theta':>8}  {'sum_act':>12}  {'nz_count':>10}  {'sum_ratio':>10}")
        print("-" * 50)
        base_sum_ch = None
        for theta in THETA_VALUES:
            prop = ThresholdPropagator(W, theta=theta, beta=5.0)
            x = prop.propagate(s0, N_STEPS, sustained=SUSTAINED)
            s = x.sum()
            nz = np.count_nonzero(x > 1e-10)
            if base_sum_ch is None:
                base_sum_ch = s
            ratio = s / base_sum_ch if base_sum_ch > 0 else 0
            print(f"{theta:>8.3f}  {s:>12.4f}  {nz:>10d}  {ratio:>10.4f}")


def analyse_step_by_step_threshold_effect(data):
    """Look at where the threshold bites: step 1, 2, or 3."""
    print("\n" + "="*80)
    print("SECTION 6: STEP-BY-STEP THRESHOLD IMPACT")
    print("="*80)
    print("At which propagation step does the threshold have the most impact?")

    W = data["W"]
    enc = data["encoded_channels"]

    s_both = enc["ppk23"] + enc["ppk25"]

    for theta in [0.0, 0.01, 0.05, 0.1]:
        prop = ThresholdPropagator(W, theta=theta, beta=5.0)
        traj = prop.propagate_trajectory(s_both, N_STEPS, sustained=SUSTAINED)

        print(f"\n  theta={theta:.3f}:")
        for step in range(N_STEPS + 1):
            x = traj[step]
            nz = np.count_nonzero(x > 1e-10)
            s = x.sum()
            mx = x.max()
            print(f"    Step {step}: {nz:>6d} active neurons, "
                  f"sum={s:>10.4f}, max={mx:>.6f}")


def analyse_sensitivity_of_rij_magnitude(data):
    """How does absolute magnitude of R_ij change with theta? Expressed as percentage of baseline."""
    print("\n" + "="*80)
    print("SECTION 7: R_ij MAGNITUDE SENSITIVITY")
    print("="*80)
    print("How does |R_ij| change with theta, as % of baseline |R_ij|?")

    W = data["W"]
    enc = data["encoded_channels"]
    encoder = data["encoder"]

    s_ppk23 = enc["ppk23"]
    s_ppk25 = enc["ppk25"]
    s_both = s_ppk23 + s_ppk25

    # Collect focal neurons
    focal_list = []
    for tg, groups in FOCAL_NEURONS.items():
        for cat, neurons in groups.items():
            for n in neurons:
                if n in encoder.type_to_idx:
                    focal_list.append((n, tg, cat, encoder.type_to_idx[n]))

    # Get baseline R_ij
    prop_base = ThresholdPropagator(W, theta=0.0, beta=5.0)
    x_23_base = prop_base.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
    x_25_base = prop_base.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
    x_both_base = prop_base.propagate(s_both, N_STEPS, sustained=SUSTAINED)

    print(f"\n{'neuron':>20s} {'cat':>6s} {'R_ij_base':>12s}", end="")
    for theta in THETA_VALUES[1:]:
        print(f"  {'%_at_'+str(theta):>12s}", end="")
    print()
    print("-" * (42 + 14 * len(THETA_VALUES[1:])))

    for n, tg, cat, idx in focal_list:
        r_base = x_both_base[idx] - x_23_base[idx] - x_25_base[idx]
        print(f"  {n:>20s} {cat:>6s} {r_base:>+12.6f}", end="")

        for theta in THETA_VALUES[1:]:
            prop = ThresholdPropagator(W, theta=theta, beta=5.0)
            x_23 = prop.propagate(s_ppk23, N_STEPS, sustained=SUSTAINED)
            x_25 = prop.propagate(s_ppk25, N_STEPS, sustained=SUSTAINED)
            x_both = prop.propagate(s_both, N_STEPS, sustained=SUSTAINED)

            r_theta = x_both[idx] - x_23[idx] - x_25[idx]
            if abs(r_base) > 1e-10:
                pct = 100 * r_theta / r_base
                print(f"  {pct:>+11.1f}%", end="")
            else:
                print(f"  {'N/A':>12s}", end="")
        print()


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("="*80)
    print("FIRING THRESHOLD SENSITIVITY ANALYSIS")
    print("="*80)
    print(f"Activation: max(0, tanh(5*(x - theta)))")
    print(f"Theta values: {THETA_VALUES}")
    print(f"Propagation: {N_STEPS} steps, sustained={SUSTAINED}, norm={NORMALIZATION}")

    data = load_data()
    logger.info("Data loaded: %d neurons", data["W"].shape[0])

    # Run all analyses
    df_sparsity = analyse_activation_sparsity(data)
    analyse_prethreshold_distribution(data)
    df_preservation = analyse_target_signal_preservation(data)
    df_rij, df_rij_all = analyse_interaction_scores(data)
    analyse_overall_network_impact(data)
    analyse_step_by_step_threshold_effect(data)
    analyse_sensitivity_of_rij_magnitude(data)

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
