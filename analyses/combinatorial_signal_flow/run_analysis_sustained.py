#!/usr/bin/env python3
"""
Combinatorial Signal Flow Analysis — Sustained Input Variant

Same as run_analysis.py but with sustained (clamped) input injection:
  x(t+1) = f(W.T @ x(t) + s0)

The sensory input is re-injected at every propagation step, modelling
continuous sensory stimulation (e.g. persistent pheromone exposure)
rather than a single pulse.

Usage:
  python run_analysis_sustained.py
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from signal_flow import (
    NetworkLoader,
    ChannelEncoder,
    CombinatorialScreen,
    InteractionAnalyzer,
    sensitivity_analysis,
)
from visualization import (
    plot_interaction_heatmap,
    plot_interaction_heatmaps_per_type,
    plot_summary_interaction_heatmap,
    plot_target_clustermap,
    plot_target_clustering_summary,
    plot_channel_clustermap,
    plot_integrator_scatter,
    plot_integrator_scatter_activation,
    plot_integrator_scatter_synergy,
    plot_integrator_scatter_opposition,
    plot_interaction_profile_per_group,
    plot_interaction_profile_per_group_biclustered,
    plot_all_channels_bar,
    plot_pairwise_vs_total,
    plot_sensitivity_grid,
    plot_interaction_forest,
    plot_signal_identity_interactions,
    plot_activation_profiles,
    plot_interaction_forest_clustered,
    plot_signal_identity_interactions_clustered,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent

CONFIG = {
    "data_dir": str(BASE_DIR / "data"),
    "output_dir": str(BASE_DIR / "plots_sustained"),

    "normalization": "post",
    "n_steps": 3,

    "nonlinearities": ["relu", "sigmoid_rectified", "leaky_relu"],
    "activation_params": {
        "sigmoid_rectified": {"beta": 5.0},
        "leaky_relu": {"alpha": 0.1},
    },

    "target_groups": None,
    "max_combination_order": 7,

    "run_sensitivity": True,
    "sensitivity_params": {
        "normalizations": ["post", "pre", "raw"],
        "n_steps": [2, 3, 4, 5],
        "nonlinearities": ["relu", "sigmoid_rectified", "leaky_relu"],
        "activation_params": {
            "sigmoid_rectified": {"beta": 5.0},
            "leaky_relu": {"alpha": 0.1},
        },
    },
}


def run_single_nonlinearity(nonlinearity, act_params, W, encoded_channels,
                            target_indices, type_names, encoder, channel_order,
                            modality_colors, target_colors, output_dir,
                            curated_map, targets, results_collector):
    """Run screen + interactions + plots for one nonlinearity (sustained input)."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("Running nonlinearity: %s (sustained input)", nonlinearity)
    logger.info("=" * 60)

    screen = CombinatorialScreen(W, encoded_channels, target_indices, type_names)
    results = screen.run(
        n_steps=CONFIG["n_steps"],
        nonlinearity=nonlinearity,
        activation_params=act_params,
        max_combination_order=CONFIG["max_combination_order"],
        sustained=True,
    )
    results.to_csv(output_dir / "screen_results.csv", index=False)
    logger.info("  %d measurements saved", len(results))

    results_tagged = results.copy()
    results_tagged["nonlinearity"] = nonlinearity
    results_collector.append(results_tagged)

    logger.info("Computing interaction scores...")
    analyzer = InteractionAnalyzer(results)

    pairwise = analyzer.compute_pairwise_interactions()
    pairwise.to_csv(output_dir / "pairwise_interactions.csv", index=False)
    logger.info("  Pairwise: %d rows", len(pairwise))

    triplets = analyzer.compute_triplet_interactions()
    if len(triplets) > 0:
        triplets.to_csv(output_dir / "triplet_interactions.csv", index=False)
        logger.info("  Triplets: %d rows", len(triplets))

    total = analyzer.compute_total_interaction()
    total.to_csv(output_dir / "total_interaction.csv", index=False)
    logger.info("  Total interaction: %d rows", len(total))

    metrics = analyzer.compute_integration_metrics(pairwise)
    metrics.to_csv(output_dir / "integration_metrics.csv", index=False)

    logger.info("Generating plots for %s...", nonlinearity)

    # Subdirectories
    d_heatmaps = output_dir / "heatmaps"
    d_profiles = output_dir / "profiles"
    d_clustering = output_dir / "clustering"
    d_scatter = output_dir / "scatter"
    d_forest = output_dir / "forest"
    d_signal = output_dir / "signal_identity"

    # --- heatmaps/ ---
    for tg in target_indices:
        plot_interaction_heatmap(
            pairwise, tg, channel_order, modality_colors,
            save_path=str(d_heatmaps / f"interaction_heatmap_{tg}"),
        )
    for tg in target_indices:
        plot_interaction_heatmaps_per_type(
            pairwise, tg, channel_order, modality_colors,
            type_order=targets.get(tg),
            curated_types=curated_map.get(tg),
            save_path=str(d_heatmaps / f"interaction_heatmap_{tg}_per_type"),
        )
    plot_summary_interaction_heatmap(
        pairwise, channel_order, modality_colors,
        target_groups=list(target_indices.keys()),
        save_path=str(d_heatmaps / "interaction_heatmap_summary"),
    )

    # --- clustering/ ---
    plot_target_clustermap(
        pairwise, channel_order, target_colors,
        save_path=str(d_clustering / "target_clustering"),
    )
    plot_target_clustering_summary(
        pairwise, channel_order, target_colors,
        save_path=str(d_clustering / "target_clustering_summary"),
    )
    plot_channel_clustermap(
        pairwise, channel_order, modality_colors,
        save_path=str(d_clustering / "channel_clustering"),
    )
    plot_activation_profiles(
        results, channel_order, modality_colors, target_colors,
        save_path=str(d_clustering / "activation_profiles"),
    )

    # --- profiles/ ---
    d_prof_raw = d_profiles / "raw"
    d_prof_colnorm = d_profiles / "colnorm"
    d_prof_rownorm = d_profiles / "rownorm"

    for tg in target_indices:
        # Raw
        plot_interaction_profile_per_group(
            pairwise, channel_order, target_colors, tg,
            type_order=targets.get(tg),
            save_path=str(d_prof_raw / f"interaction_profile_{tg}"),
        )
        plot_interaction_profile_per_group_biclustered(
            pairwise, channel_order, target_colors, tg,
            save_path=str(d_prof_raw / f"interaction_profile_{tg}_biclustered"),
        )
        # Column-normalized
        plot_interaction_profile_per_group(
            pairwise, channel_order, target_colors, tg,
            type_order=targets.get(tg), normalize="cols",
            save_path=str(d_prof_colnorm / f"interaction_profile_{tg}"),
        )
        plot_interaction_profile_per_group_biclustered(
            pairwise, channel_order, target_colors, tg,
            normalize="cols",
            save_path=str(d_prof_colnorm / f"interaction_profile_{tg}_biclustered"),
        )
        # Row-normalized
        plot_interaction_profile_per_group(
            pairwise, channel_order, target_colors, tg,
            type_order=targets.get(tg), normalize="rows",
            save_path=str(d_prof_rownorm / f"interaction_profile_{tg}"),
        )
        plot_interaction_profile_per_group_biclustered(
            pairwise, channel_order, target_colors, tg,
            normalize="rows",
            save_path=str(d_prof_rownorm / f"interaction_profile_{tg}_biclustered"),
        )

    # --- scatter/ ---
    plot_integrator_scatter(
        metrics, target_colors,
        save_path=str(d_scatter / "integrator_scatter"),
    )
    plot_integrator_scatter_activation(
        metrics, target_colors,
        save_path=str(d_scatter / "integrator_scatter_activation"),
    )
    plot_integrator_scatter_synergy(
        metrics, target_colors,
        save_path=str(d_scatter / "integrator_scatter_synergy"),
    )
    plot_integrator_scatter_opposition(
        metrics, target_colors,
        save_path=str(d_scatter / "integrator_scatter_opposition"),
    )
    plot_all_channels_bar(
        total, target_colors,
        save_path=str(d_scatter / "all_channels_bar"),
    )
    plot_pairwise_vs_total(
        pairwise, total, target_colors,
        save_path=str(d_scatter / "pairwise_vs_total"),
    )

    # --- forest/ ---
    plot_interaction_forest(
        pairwise, channel_order, modality_colors, target_colors,
        save_path=str(d_forest / "interaction_forest"),
    )
    plot_interaction_forest_clustered(
        pairwise, channel_order, modality_colors, target_colors,
        save_path=str(d_forest / "interaction_forest_clustered"),
    )

    # --- signal_identity/ ---
    plot_signal_identity_interactions(
        pairwise, channel_order, target_colors,
        save_path=str(d_signal / "signal_identity_interactions"),
    )
    plot_signal_identity_interactions_clustered(
        pairwise, channel_order, target_colors,
        save_path=str(d_signal / "signal_identity_clustered"),
    )

    return results, pairwise


def main():
    root_output = Path(CONFIG["output_dir"])
    root_output.mkdir(parents=True, exist_ok=True)

    logger.info("Loading network data...")
    loader = NetworkLoader(CONFIG["data_dir"])

    W_unsigned = loader.load_adjacency_matrix(CONFIG["normalization"])
    type_names = loader.load_type_names()
    channels = loader.load_channels()
    targets = loader.load_targets()
    palette = loader.load_colors()

    modality_colors = palette["colors"]
    channel_order = palette["order"]
    target_colors = palette.get("target_colors", {})

    logger.info("  Matrix: %d x %d  (%d non-zeros)",
                W_unsigned.shape[0], W_unsigned.shape[1], W_unsigned.nnz)

    W = loader.sign_matrix(W_unsigned, type_names)
    logger.info("  Channels: %s", list(channels.keys()))
    logger.info("  Target groups: %s", list(targets.keys()))

    logger.info("Encoding channels as input vectors...")
    encoder = ChannelEncoder(type_names)
    encoded_channels = encoder.encode_all(channels)

    for ch, vec in encoded_channels.items():
        logger.info("  %s: %d types active", ch, int(vec.sum()))

    logger.info("Mapping targets to matrix indices...")
    target_indices = {}
    requested_groups = CONFIG["target_groups"] or list(targets.keys())

    sensory_types = set()
    for ch_types in channels.values():
        sensory_types.update(ch_types)
    sensory_indices = set(encoder.get_indices(list(sensory_types)))
    logger.info("  %d sensory types (%d in matrix) will be excluded from targets",
                len(sensory_types), len(sensory_indices))

    for tg_name in requested_groups:
        if tg_name not in targets:
            logger.warning("  Target group '%s' not in targets.json, skipping", tg_name)
            continue
        indices = encoder.get_indices(targets[tg_name])
        n_before = len(indices)
        indices = [i for i in indices if i not in sensory_indices]
        if n_before != len(indices):
            logger.info("  %s: removed %d sensory neurons from targets",
                        tg_name, n_before - len(indices))
        if not indices:
            logger.warning("  %s: 0 types found in matrix, skipping", tg_name)
            continue
        target_indices[tg_name] = indices
        logger.info("  %s: %d types mapped", tg_name, len(indices))

    if not target_indices:
        logger.error("No valid target groups. Check targets.json and type_names.csv.")
        sys.exit(1)

    curated_map = {}
    for tg in target_indices:
        if tg.endswith("_all"):
            base = tg.removesuffix("_all")
            if base in target_indices:
                base_types = {encoder.idx_to_type[i] for i in target_indices[base]}
                curated_map[tg] = base_types

    results_collector = []

    for nonlin in CONFIG["nonlinearities"]:
        act_params = CONFIG["activation_params"].get(nonlin)
        nonlin_dir = root_output / nonlin

        run_single_nonlinearity(
            nonlin, act_params, W, encoded_channels,
            target_indices, type_names, encoder, channel_order,
            modality_colors, target_colors, nonlin_dir,
            curated_map, targets, results_collector,
        )

    if CONFIG["run_sensitivity"]:
        logger.info("Running sensitivity analysis (sustained)...")

        W_dict = {}
        for norm in CONFIG["sensitivity_params"]["normalizations"]:
            try:
                W_raw = loader.load_adjacency_matrix(norm)
                W_dict[norm] = loader.sign_matrix(W_raw, type_names)
            except FileNotFoundError:
                logger.warning("  Matrix for '%s' not found, skipping", norm)

        if W_dict:
            sens_results = sensitivity_analysis(
                W_dict, encoded_channels, target_indices, type_names,
                CONFIG["sensitivity_params"],
                sustained=True,
            )
            sens_results.to_csv(root_output / "sensitivity_results.csv", index=False)

            sens_analyzer = InteractionAnalyzer(sens_results)
            sens_pairwise = sens_analyzer.compute_pairwise_interactions()
            sens_pairwise.to_csv(root_output / "sensitivity_pairwise.csv", index=False)

            ref_pairwise = pd.read_csv(root_output / "relu" / "pairwise_interactions.csv")
            plot_sensitivity_grid(
                sens_results, channel_order, ref_pairwise,
                save_path=str(root_output / "sensitivity_grid"),
            )
            logger.info("  Sensitivity analysis complete")

    logger.info("Sustained analysis complete! Results in: %s", root_output)
    for nonlin in CONFIG["nonlinearities"]:
        logger.info("  %s/ — screen, interactions, plots", nonlin)


if __name__ == "__main__":
    main()
