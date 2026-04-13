"""
Combinatorial Signal Flow Analysis for Drosophila Male CNS Connectome.

Core module: network loading, channel encoding, signal propagation,
combinatorial screening, and interaction score computation.
"""

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.io import mmread
from scipy.spatial.distance import squareform, pdist
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
import json
import itertools
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Activation functions
# =============================================================================

def relu(x: np.ndarray, **kwargs) -> np.ndarray:
    """Threshold-linear (ReLU) activation."""
    return np.maximum(x, 0.0)


def sigmoid(x: np.ndarray, beta: float = 5.0, **kwargs) -> np.ndarray:
    """Sigmoidal activation with gain parameter beta."""
    z = np.clip(beta * x, -500, 500)  # prevent overflow
    return np.tanh(z)  # tanh variant — saturates for large |x|


def sigmoid_rectified(x: np.ndarray, beta: float = 5.0, **kwargs) -> np.ndarray:
    """Rectified sigmoid: max(0, tanh(beta*x)).

    Firing rates cannot be negative — this clips the tanh output at zero.
    """
    z = np.clip(beta * x, -500, 500)
    return np.maximum(np.tanh(z), 0.0)


def leaky_relu(x: np.ndarray, alpha: float = 0.1, **kwargs) -> np.ndarray:
    """Leaky ReLU: excitatory signal passes fully, inhibitory at reduced strength.

    Biologically: inhibition propagates but at attenuated efficacy (alpha=10%).
    Unlike ReLU (which blocks all inhibition) and sigmoid (which compresses
    everything symmetrically), leaky ReLU preserves the sign asymmetry between
    excitation and inhibition.
    """
    return np.where(x > 0, x, alpha * x)


def linear(x: np.ndarray, **kwargs) -> np.ndarray:
    """Identity activation (no nonlinearity)."""
    return x


ACTIVATIONS = {
    "relu": relu,
    "sigmoid": sigmoid,
    "sigmoid_rectified": sigmoid_rectified,
    "leaky_relu": leaky_relu,
    "linear": linear,
}


# =============================================================================
# Data loading
# =============================================================================

class NetworkLoader:
    """Loads sparse adjacency matrices and metadata from R-exported data."""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def load_adjacency_matrix(self, normalization: str = "post") -> sparse.csc_matrix:
        """
        Load sparse adjacency matrix.

        Parameters
        ----------
        normalization : {'post', 'pre', 'raw'}
            post = column-normalized (each neuron's inputs sum to ~1)
            pre  = row-normalized (each neuron's outputs sum to ~1)
            raw  = unnormalized synapse counts
        """
        if normalization not in ("post", "pre", "raw"):
            raise ValueError(f"normalization must be 'post', 'pre', or 'raw', got '{normalization}'")

        mtx_path = self.data_dir / f"adj_matrix_{normalization}.mtx"
        if not mtx_path.exists():
            raise FileNotFoundError(f"Matrix file not found: {mtx_path}")

        W = mmread(str(mtx_path)).tocsc()
        logger.info("Loaded %s matrix: %d x %d, %d non-zeros",
                     normalization, W.shape[0], W.shape[1], W.nnz)
        return W

    def load_type_names(self) -> pd.DataFrame:
        """Load type name mapping (index -> type)."""
        df = pd.read_csv(self.data_dir / "type_names.csv")
        return df

    def load_channels(self) -> Dict[str, List[str]]:
        """Load sensory channel definitions."""
        with open(self.data_dir / "channels.json") as f:
            channels = json.load(f)
        # Ensure all values are lists
        for k, v in channels.items():
            if isinstance(v, str):
                channels[k] = [v]
        return channels

    def load_targets(self) -> Dict[str, List[str]]:
        """Load target neuron set definitions."""
        with open(self.data_dir / "targets.json") as f:
            targets = json.load(f)
        for k, v in targets.items():
            if isinstance(v, str):
                targets[k] = [v]
        return targets

    def load_neurotransmitter_mapping(self) -> pd.DataFrame:
        """Load type -> neurotransmitter -> is_inhibitory mapping."""
        return pd.read_csv(self.data_dir / "neurotransmitter_mapping.csv")

    def load_colors(self) -> dict:
        """Load full color palette (modality colors, order, groups, target colors)."""
        with open(self.data_dir / "modality_colors.json") as f:
            return json.load(f)

    def sign_matrix(self, W: sparse.csc_matrix,
                    type_names: pd.DataFrame) -> sparse.csc_matrix:
        """
        Apply neurotransmitter signs: negate outgoing weights of inhibitory types.

        Inhibitory neurotransmitters (GABA, glycine, histamine) get sign -1,
        excitatory get +1. W[pre, post] is multiplied row-wise by the sign
        of the presynaptic type.
        """
        nt_map = self.load_neurotransmitter_mapping()
        type_to_inhib = dict(zip(nt_map["type"], nt_map["is_inhibitory"]))

        signs = np.ones(W.shape[0], dtype=np.float64)
        n_inhib = 0
        for _, row in type_names.iterrows():
            idx = row["index"]
            t = row["type"]
            if type_to_inhib.get(t, False):
                signs[idx] = -1.0
                n_inhib += 1

        logger.info("Signing matrix: %d inhibitory / %d total types",
                     n_inhib, len(type_names))

        # Multiply each row by its sign (pre-synaptic type determines sign)
        # diag(signs) @ W
        sign_diag = sparse.diags(signs, format="csc")
        W_signed = sign_diag.dot(W)

        return W_signed.tocsc()


# =============================================================================
# Channel encoding
# =============================================================================

class ChannelEncoder:
    """Encodes sensory channels as binary input vectors over the type space."""

    def __init__(self, type_names: pd.DataFrame):
        self.type_to_idx = dict(zip(type_names["type"], type_names["index"]))
        self.idx_to_type = dict(zip(type_names["index"], type_names["type"]))
        self.n = len(type_names)

    def encode(self, type_list: List[str]) -> np.ndarray:
        """Create binary vector with 1s at positions matching type_list."""
        s = np.zeros(self.n, dtype=np.float64)
        missing = []
        for t in type_list:
            if t in self.type_to_idx:
                s[self.type_to_idx[t]] = 1.0
            else:
                missing.append(t)
        if missing:
            warnings.warn(f"{len(missing)} types not in matrix: {missing[:5]}")
        return s

    def encode_all(self, channels: Dict[str, List[str]]) -> Dict[str, np.ndarray]:
        """Encode all channels. Returns dict of channel_name -> binary vector."""
        return {name: self.encode(types) for name, types in channels.items()}

    def get_indices(self, type_list: List[str]) -> List[int]:
        """Get matrix indices for a list of types (skipping missing)."""
        return [self.type_to_idx[t] for t in type_list if t in self.type_to_idx]


# =============================================================================
# Signal propagation
# =============================================================================

class SignalPropagator:
    """Iterative signal propagation through a sparse directed network."""

    def __init__(self, W: sparse.csc_matrix,
                 nonlinearity: str = "relu",
                 activation_params: Optional[dict] = None):
        """
        Parameters
        ----------
        W : sparse matrix
            Adjacency matrix. Convention: W[pre, post] = weight.
            For forward propagation we compute W.T @ x so that signal flows
            from presynaptic sources to postsynaptic targets.
        nonlinearity : str
            One of 'relu', 'sigmoid', 'linear'.
        activation_params : dict, optional
            Extra kwargs passed to the activation function (e.g. beta for sigmoid).
        """
        # W[pre, post] -> to propagate forward, we need x_post = sum_pre W[pre,post] * x_pre
        # That's W.T @ x (columns of W are postsynaptic neurons)
        # But actually: if W is stored as (pre x post), then W.T[post, pre] and
        # W.T @ x sums over pre for each post. That's correct.
        self.Wt = W.T.tocsc()
        self.n = W.shape[0]

        if nonlinearity not in ACTIVATIONS:
            raise ValueError(f"Unknown nonlinearity '{nonlinearity}'. "
                             f"Choose from {list(ACTIVATIONS.keys())}")
        self.activation_fn = ACTIVATIONS[nonlinearity]
        self.activation_params = activation_params or {}

    def propagate(self, s0: np.ndarray, n_steps: int,
                  sustained: bool = False) -> np.ndarray:
        """
        Propagate signal for n_steps iterations.

        sustained=False (pulse):     x(t+1) = f(W.T @ x(t))
        sustained=True  (clamped):   x(t+1) = f(W.T @ x(t) + s0)

        Returns (final_activation, final_net_input) tuple.
        """
        x = s0.copy().astype(np.float64)
        net_input = x.copy()
        for _ in range(n_steps):
            net_input = self.Wt.dot(x)
            if sustained:
                net_input = net_input + s0
            x = self.activation_fn(net_input, **self.activation_params)
        return x, net_input

    def propagate_trajectory(self, s0: np.ndarray, n_steps: int,
                             sustained: bool = False) -> np.ndarray:
        """Same as propagate but returns full trajectory (n_steps+1 x N)."""
        x = s0.copy().astype(np.float64)
        trajectory = np.zeros((n_steps + 1, self.n))
        trajectory[0] = x
        for t in range(n_steps):
            net_input = self.Wt.dot(x)
            if sustained:
                net_input = net_input + s0
            x = self.activation_fn(net_input, **self.activation_params)
            trajectory[t + 1] = x
        return trajectory


# =============================================================================
# Combinatorial screen
# =============================================================================

def generate_combinations(channel_names: List[str],
                          max_order: int = 7) -> Dict[str, List[str]]:
    """
    Generate all channel combinations up to max_order.

    For 7 channels: 7 singles + 21 pairs + 35 triplets + ... + 1 all.
    """
    combos = {}

    for k in range(1, min(max_order, len(channel_names)) + 1):
        for group in itertools.combinations(channel_names, k):
            name = "+".join(group)
            combos[name] = list(group)

    return combos


class CombinatorialScreen:
    """Runs combinatorial stimulation protocol across all channel combinations."""

    def __init__(self,
                 W: sparse.csc_matrix,
                 encoded_channels: Dict[str, np.ndarray],
                 target_indices: Dict[str, List[int]],
                 type_names: pd.DataFrame):
        self.W = W
        self.encoded_channels = encoded_channels
        self.target_indices = target_indices
        self.type_names = type_names
        self.idx_to_type = dict(zip(type_names["index"], type_names["type"]))

    def run(self,
            n_steps: int = 3,
            nonlinearity: str = "relu",
            activation_params: Optional[dict] = None,
            max_combination_order: int = 7,
            sustained: bool = False) -> pd.DataFrame:
        """
        Run full combinatorial screen.

        sustained: if True, input is re-injected at every propagation step.

        Returns DataFrame with one row per (combination, target_group, target_type).
        """
        channel_names = list(self.encoded_channels.keys())
        combos = generate_combinations(channel_names, max_combination_order)

        propagator = SignalPropagator(self.W, nonlinearity, activation_params)

        rows = []
        for combo_name, combo_channels in combos.items():
            # Sum input vectors for this combination
            s0 = np.sum([self.encoded_channels[ch] for ch in combo_channels], axis=0)

            # Propagate
            x_final, net_input = propagator.propagate(s0, n_steps, sustained=sustained)

            # Read out at targets
            for tg_name, tg_indices in self.target_indices.items():
                for idx in tg_indices:
                    rows.append({
                        "combination": combo_name,
                        "channels": ",".join(combo_channels),
                        "n_channels": len(combo_channels),
                        "target_group": tg_name,
                        "target_type": self.idx_to_type.get(idx, f"idx_{idx}"),
                        "target_idx": idx,
                        "activation": x_final[idx],
                        "net_input": net_input[idx],
                    })

        df = pd.DataFrame(rows)
        logger.info("Screen complete: %d combinations x %d targets = %d measurements",
                     len(combos),
                     sum(len(v) for v in self.target_indices.values()),
                     len(df))
        return df


# =============================================================================
# Interaction analysis
# =============================================================================

class InteractionAnalyzer:
    """Computes pairwise, triplet, and total interaction scores."""

    def __init__(self, results: pd.DataFrame):
        """
        Parameters
        ----------
        results : pd.DataFrame
            Output from CombinatorialScreen.run()
        """
        self.results = results
        # Build lookup: (combination, target_group, target_type) -> activation
        self._lookup = {}
        for _, row in results.iterrows():
            key = (row["combination"], row["target_group"], row["target_type"])
            self._lookup[key] = row["activation"]

    def _get_activation(self, combo: str, tg: str, tt: str) -> float:
        return self._lookup.get((combo, tg, tt), 0.0)

    def compute_pairwise_interactions(self) -> pd.DataFrame:
        """
        R_ij(k) = A(i+j, k) - A(i, k) - A(j, k)

        Positive = synergy, negative = opposition, zero = independence.
        """
        pairs = self.results[self.results["n_channels"] == 2].copy()

        rows = []
        for _, row in pairs.iterrows():
            ch1, ch2 = row["channels"].split(",")
            tg = row["target_group"]
            tt = row["target_type"]

            A_i = self._get_activation(ch1, tg, tt)
            A_j = self._get_activation(ch2, tg, tt)
            A_ij = row["activation"]
            R_ij = A_ij - A_i - A_j

            rows.append({
                "target_group": tg,
                "target_type": tt,
                "ch1": ch1,
                "ch2": ch2,
                "A_ch1": A_i,
                "A_ch2": A_j,
                "A_pair": A_ij,
                "R_ij": R_ij,
            })

        return pd.DataFrame(rows)

    def compute_triplet_interactions(self) -> pd.DataFrame:
        """
        R_ijl(k) = A(i+j+l) - A(i+j) - A(i+l) - A(j+l) + A(i) + A(j) + A(l)

        Three-way interaction beyond pairwise.
        """
        triplets = self.results[self.results["n_channels"] == 3].copy()

        rows = []
        for _, row in triplets.iterrows():
            chs = row["channels"].split(",")
            ch1, ch2, ch3 = chs[0], chs[1], chs[2]
            tg = row["target_group"]
            tt = row["target_type"]

            A_ijl = row["activation"]
            A_ij = self._get_activation(f"{ch1}+{ch2}", tg, tt)
            A_il = self._get_activation(f"{ch1}+{ch3}", tg, tt)
            A_jl = self._get_activation(f"{ch2}+{ch3}", tg, tt)
            A_i = self._get_activation(ch1, tg, tt)
            A_j = self._get_activation(ch2, tg, tt)
            A_l = self._get_activation(ch3, tg, tt)

            R_ijl = A_ijl - A_ij - A_il - A_jl + A_i + A_j + A_l

            rows.append({
                "target_group": tg,
                "target_type": tt,
                "ch1": ch1,
                "ch2": ch2,
                "ch3": ch3,
                "A_triplet": A_ijl,
                "R_ijl": R_ijl,
            })

        return pd.DataFrame(rows)

    def compute_total_interaction(self) -> pd.DataFrame:
        """
        R_all(k) = A(all, k) - sum_i A(i, k)

        Total deviation from linear summation when all channels active.
        """
        singles = self.results[self.results["n_channels"] == 1]
        max_n = self.results["n_channels"].max()
        all_comb = self.results[self.results["n_channels"] == max_n]

        # Sum of singles per (target_group, target_type)
        singles_sum = (singles.groupby(["target_group", "target_type"])["activation"]
                       .sum().reset_index().rename(columns={"activation": "sum_singles"}))

        merged = all_comb[["target_group", "target_type", "activation"]].merge(
            singles_sum, on=["target_group", "target_type"], how="left"
        )
        merged["R_all"] = merged["activation"] - merged["sum_singles"]

        return merged.rename(columns={"activation": "A_all"})

    def compute_integration_metrics(self, pairwise: pd.DataFrame) -> pd.DataFrame:
        """
        Per-target integration score and channel breadth.

        integration_score = mean of positive R_ij values
        channel_breadth   = number of single channels producing above-threshold activation
        """
        # Integration score from pairwise
        integration = (pairwise.groupby(["target_group", "target_type"])
                       .agg(
                           mean_synergy=("R_ij", lambda x: x[x > 0].mean() if (x > 0).any() else 0.0),
                           mean_opposition=("R_ij", lambda x: x[x < 0].mean() if (x < 0).any() else 0.0),
                           sum_R_ij=("R_ij", "sum"),
                           sum_positive_R_ij=("R_ij", lambda x: x[x > 0].sum()),
                           sum_negative_R_ij=("R_ij", lambda x: x[x < 0].sum()),
                           n_synergistic=("R_ij", lambda x: (x > 0).sum()),
                           n_opposing=("R_ij", lambda x: (x < 0).sum()),
                           mean_abs_interaction=("R_ij", lambda x: x.abs().mean()),
                       )
                       .reset_index())

        # Channel breadth from singles
        singles = self.results[self.results["n_channels"] == 1]
        threshold = singles["activation"].median() * 0.1  # 10% of median activation
        breadth = (singles[singles["activation"] > threshold]
                   .groupby(["target_group", "target_type"])
                   .size().reset_index(name="channel_breadth"))

        merged = integration.merge(breadth, on=["target_group", "target_type"], how="left")
        merged["channel_breadth"] = merged["channel_breadth"].fillna(0).astype(int)

        # Total activation: activation when all channels are on simultaneously
        all_ch = self.results[self.results["n_channels"] == self.results["n_channels"].max()]
        if len(all_ch) > 0:
            total_act = (all_ch.groupby(["target_group", "target_type"])["activation"]
                         .first().reset_index(name="total_activation"))
            merged = merged.merge(total_act, on=["target_group", "target_type"], how="left")
            merged["total_activation"] = merged["total_activation"].fillna(0.0)
        else:
            merged["total_activation"] = 0.0

        return merged


# =============================================================================
# Sensitivity analysis
# =============================================================================

def sensitivity_analysis(
    W_dict: Dict[str, sparse.csc_matrix],
    encoded_channels: Dict[str, np.ndarray],
    target_indices: Dict[str, List[int]],
    type_names: pd.DataFrame,
    param_grid: dict,
    sustained: bool = False,
) -> pd.DataFrame:
    """
    Sweep across normalizations, propagation steps, and nonlinearities.

    Parameters
    ----------
    W_dict : dict
        {'post': W_post, 'pre': W_pre, 'raw': W_raw}
    param_grid : dict
        Keys: 'normalizations', 'n_steps', 'nonlinearities', 'activation_params'
    sustained : bool
        If True, re-inject input at each propagation step.
    """
    all_dfs = []

    normalizations = param_grid.get("normalizations", ["post"])
    steps_list = param_grid.get("n_steps", [3])
    nonlinearities = param_grid.get("nonlinearities", ["relu"])
    act_params_map = param_grid.get("activation_params", {})

    total = len(normalizations) * len(steps_list) * len(nonlinearities)
    i = 0

    for norm in normalizations:
        if norm not in W_dict:
            logger.warning("Normalization '%s' not in W_dict, skipping", norm)
            continue
        W = W_dict[norm]

        for n_steps in steps_list:
            for nonlin in nonlinearities:
                i += 1
                logger.info("Sensitivity %d/%d: norm=%s, steps=%d, nonlin=%s",
                            i, total, norm, n_steps, nonlin)

                act_params = act_params_map.get(nonlin)
                screen = CombinatorialScreen(
                    W, encoded_channels, target_indices, type_names
                )
                # Only run singles + pairs + all-together (skip triplets for speed)
                df = screen.run(
                    n_steps=n_steps,
                    nonlinearity=nonlin,
                    activation_params=act_params,
                    max_combination_order=2,  # singles + pairs only for sensitivity
                    sustained=sustained,
                )
                df["normalization"] = norm
                df["n_steps"] = n_steps
                df["nonlinearity"] = nonlin
                all_dfs.append(df)

    # Also add all-channels-together for each param combo
    # (max_combination_order=2 doesn't include the all-7 combo,
    #  but the full run_analysis.py handles that separately)

    return pd.concat(all_dfs, ignore_index=True)
