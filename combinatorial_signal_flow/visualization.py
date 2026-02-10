"""
Visualization functions for combinatorial signal flow analysis.

Produces interaction heatmaps, clustermaps, integrator scatter plots,
sensitivity grids, and summary bar plots. Colour palette matches
the existing fig6/ R outputs.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import seaborn as sns
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

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
    "pdf.fonttype": 42,  # editable text in PDFs
})


def _save(fig: plt.Figure, path: Optional[str], close: bool = True,
          description: Optional[str] = None):
    """Save figure as PNG + PDF in separate subdirectories, with optional .txt description."""
    if path is None:
        return
    p = Path(path)
    png_dir = p.parent / "png"
    pdf_dir = p.parent / "pdf"
    png_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_dir / (p.stem + ".png"))
    fig.savefig(pdf_dir / (p.stem + ".pdf"))
    if description:
        txt_dir = p.parent / "txt"
        txt_dir.mkdir(parents=True, exist_ok=True)
        (txt_dir / (p.stem + ".txt")).write_text(description.strip() + "\n")
    logger.info("Saved: %s (.png + .pdf)", p.stem)
    if close:
        plt.close(fig)


def _build_interaction_matrix(interactions: pd.DataFrame,
                              channel_order: List[str],
                              target_filter: Optional[str] = None,
                              ) -> np.ndarray:
    """
    Pivot pairwise interactions into a symmetric 7x7 matrix.

    If target_filter is given, restrict to that target_group first,
    then average R_ij across all target neurons in the group.
    """
    df = interactions.copy()
    if target_filter is not None:
        df = df[df["target_group"] == target_filter]

    # Average R_ij across target neurons for each channel pair
    avg = df.groupby(["ch1", "ch2"])["R_ij"].mean().reset_index()

    n = len(channel_order)
    mat = np.zeros((n, n))
    ch_idx = {ch: i for i, ch in enumerate(channel_order)}

    for _, row in avg.iterrows():
        i = ch_idx.get(row["ch1"])
        j = ch_idx.get(row["ch2"])
        if i is not None and j is not None:
            mat[i, j] = row["R_ij"]
            mat[j, i] = row["R_ij"]  # symmetric

    return mat


# =============================================================================
# A. Interaction heatmaps (7 x 7)
# =============================================================================

def plot_interaction_heatmap(interactions: pd.DataFrame,
                             target_group: str,
                             channel_order: List[str],
                             modality_colors: Dict[str, str],
                             save_path: Optional[str] = None,
                             ) -> plt.Figure:
    """
    7x7 heatmap of mean pairwise interaction scores for one target group.
    Blue = opposition, white = independence, red = synergy.
    """
    mat = _build_interaction_matrix(interactions, channel_order, target_group)

    vmax = max(abs(mat.min()), abs(mat.max())) or 1e-6
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="equal")

    ax.set_xticks(range(len(channel_order)))
    ax.set_yticks(range(len(channel_order)))
    ax.set_xticklabels(channel_order, rotation=45, ha="right")
    ax.set_yticklabels(channel_order)

    # Annotate cells
    for i in range(len(channel_order)):
        for j in range(len(channel_order)):
            if i != j:
                ax.text(j, i, f"{mat[i, j]:.2e}", ha="center", va="center", fontsize=6)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("R_ij (synergy ↔ opposition)")
    ax.set_title(f"Pairwise interactions: {target_group}")
    fig.tight_layout()
    _save(fig, save_path, description=f"""\
Pairwise interaction heatmap for target group: {target_group}

Each cell shows R_ij = A(i+j) - A(i) - A(j), the pairwise interaction score
between two sensory channels (rows/columns), averaged across all target neurons
in this group. R_ij measures deviation from linear additivity:
  - Red (R_ij > 0): synergy — combined stimulation exceeds sum of individual effects
  - Blue (R_ij < 0): opposition — combined stimulation is less than sum (interference)
  - White (R_ij ~ 0): independence — channels do not interact at these targets

The matrix is symmetric. Diagonal is empty (self-interaction undefined).
Values are computed after propagating signal through the signed connectome
(inhibitory neurotransmitter types have negative weights).

______________________________

Pairwise interaction heatmap for {target_group} target neurons. Each cell shows the mean interaction score R_ij = A(i+j) − A(i) − A(j) between two sensory channels, averaged across all neuron types in the {target_group} population. Red indicates synergy (supralinear combination), blue indicates opposition (sublinear combination), and white indicates independence (linear additivity). Signal was propagated through the signed type-level connectome, where inhibitory neurotransmitter identities (GABA, glutamate, acetylcholine) determine edge sign.
""")
    return fig


def plot_interaction_heatmaps_per_type(interactions: pd.DataFrame,
                                       target_group: str,
                                       channel_order: List[str],
                                       modality_colors: Dict[str, str],
                                       type_order: Optional[List[str]] = None,
                                       curated_types: Optional[set] = None,
                                       save_path: Optional[str] = None,
                                       max_cols: int = 6,
                                       ) -> Optional[plt.Figure]:
    """
    One 7x7 heatmap per individual target type within a target group.

    type_order: ordered list of type names (e.g. from targets.json, which
                preserves the descending-weight order from the R analysis).
    Types in curated_types are highlighted with * and bold title.
    For groups with many types, splits across multiple pages/files.
    """
    df = interactions[interactions["target_group"] == target_group]
    available = set(df["target_type"].unique())
    if not available:
        logger.warning("No target types found for group '%s'", target_group)
        return None

    curated_types = curated_types or set()

    # Use provided order (from targets.json / RDS), fall back to alphabetical
    if type_order is not None:
        types = [t for t in type_order if t in available]
        remaining = sorted(available - set(types))
        types = types + remaining
    else:
        types = sorted(available)

    n = len(channel_order)
    ch_idx = {ch: i for i, ch in enumerate(channel_order)}

    # Build per-type matrices
    type_mats = {}
    for tt in types:
        tt_df = df[df["target_type"] == tt]
        mat = np.zeros((n, n))
        for _, row in tt_df.iterrows():
            i = ch_idx.get(row["ch1"])
            j = ch_idx.get(row["ch2"])
            if i is not None and j is not None:
                mat[i, j] = row["R_ij"]
                mat[j, i] = row["R_ij"]
        type_mats[tt] = mat

    # Global color scale across all subtypes in this group
    all_vals = np.concatenate([m.ravel() for m in type_mats.values()])
    vmax = max(abs(all_vals.min()), abs(all_vals.max())) or 1e-6

    # Paginate if many subtypes
    page_size = max_cols * max_cols  # e.g. 36 per page
    pages = [types[i:i + page_size] for i in range(0, len(types), page_size)]

    for page_idx, page_types in enumerate(pages):
        n_types = len(page_types)
        ncols = min(n_types, max_cols)
        nrows = (n_types + ncols - 1) // ncols
        fig, axes = plt.subplots(nrows, ncols,
                                 figsize=(3.2 * ncols, 3.0 * nrows),
                                 squeeze=False)

        for idx, tt in enumerate(page_types):
            r, c = divmod(idx, ncols)
            ax = axes[r][c]
            mat = type_mats[tt]
            ax.imshow(mat, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="equal")
            ax.set_xticks(range(n))
            ax.set_yticks(range(n))
            ax.set_xticklabels(channel_order, rotation=90, fontsize=5)
            ax.set_yticklabels(channel_order, fontsize=5)

            is_curated = tt in curated_types
            label = f"* {tt}" if is_curated else tt
            weight = "bold" if is_curated else "normal"
            ax.set_title(label, fontsize=7, fontweight=weight, pad=2)

        # Hide empty subplots
        for idx in range(n_types, nrows * ncols):
            r, c = divmod(idx, ncols)
            axes[r][c].set_visible(False)

        # Shared colorbar
        cbar_ax = fig.add_axes([0.92, 0.15, 0.015, 0.7])
        sm = plt.cm.ScalarMappable(cmap="RdBu_r",
                                   norm=mcolors.Normalize(vmin=-vmax, vmax=vmax))
        fig.colorbar(sm, cax=cbar_ax, label="R_ij")

        suffix = f"_p{page_idx + 1}" if len(pages) > 1 else ""
        fig.suptitle(f"Pairwise interactions per type: {target_group}{suffix}",
                     fontsize=11)
        fig.subplots_adjust(right=0.90, hspace=0.5, wspace=0.35)

        desc = f"""\
Per-type pairwise interaction heatmaps for target group: {target_group} (page {page_idx + 1})

Each subplot is one individual target neuron type. Each shows a 7x7 R_ij matrix
of pairwise channel interactions at THAT SPECIFIC type (not averaged).
R_ij = A(i+j) - A(i) - A(j): red = synergy, blue = opposition, white = independent.

Types are ordered by descending downstream synaptic weight (from the R analysis).
Types marked with * and bold title belong to the curated top-13 subset
(top 10 by weight + 3 shared between PPN1 and vAB3).
All panels share the same color scale for direct comparison.

______________________________

Per-type pairwise interaction matrices for {target_group} neurons. Each panel shows the 7×7 interaction matrix R_ij for an individual neuron type, ordered by descending downstream synaptic weight. Asterisks mark the curated top-13 subset. A shared colour scale (red = synergy, blue = opposition) enables direct comparison of interaction structure across types within this population.
"""
        if save_path:
            _save(fig, f"{save_path}{suffix}", description=desc)
        else:
            plt.close(fig)

    return None  # multiple figs possible; all saved directly


def plot_summary_interaction_heatmap(interactions: pd.DataFrame,
                                     channel_order: List[str],
                                     modality_colors: Dict[str, str],
                                     target_groups: Optional[List[str]] = None,
                                     save_path: Optional[str] = None,
                                     ) -> plt.Figure:
    """
    Summary heatmaps: one per target group + one overall average.
    """
    if target_groups is None:
        target_groups = sorted(interactions["target_group"].unique())

    n_panels = len(target_groups) + 1  # +1 for overall
    fig, axes = plt.subplots(1, n_panels, figsize=(5 * n_panels, 5))
    if n_panels == 1:
        axes = [axes]

    all_mats = []
    for idx, tg in enumerate(target_groups):
        mat = _build_interaction_matrix(interactions, channel_order, tg)
        all_mats.append(mat)
        vmax = max(abs(mat.min()), abs(mat.max())) or 1e-6
        im = axes[idx].imshow(mat, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
        axes[idx].set_xticks(range(len(channel_order)))
        axes[idx].set_yticks(range(len(channel_order)))
        axes[idx].set_xticklabels(channel_order, rotation=45, ha="right", fontsize=7)
        axes[idx].set_yticklabels(channel_order, fontsize=7)
        axes[idx].set_title(tg, fontsize=10)
        fig.colorbar(im, ax=axes[idx], shrink=0.7)

    # Overall average
    overall = np.mean(all_mats, axis=0)
    vmax = max(abs(overall.min()), abs(overall.max())) or 1e-6
    im = axes[-1].imshow(overall, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    axes[-1].set_xticks(range(len(channel_order)))
    axes[-1].set_yticks(range(len(channel_order)))
    axes[-1].set_xticklabels(channel_order, rotation=45, ha="right", fontsize=7)
    axes[-1].set_yticklabels(channel_order, fontsize=7)
    axes[-1].set_title("All targets (mean)", fontsize=10)
    fig.colorbar(im, ax=axes[-1], shrink=0.7)

    fig.suptitle("Pairwise interaction scores by target population", fontsize=12)
    fig.tight_layout()
    _save(fig, save_path, description="""\
Summary pairwise interaction heatmap across all target populations.

Each panel shows a 7x7 matrix of mean R_ij values for one target group,
plus a final panel averaging across all groups. This allows comparison of
which channel pairs synergise or oppose at different downstream populations.

R_ij = A(i+j) - A(i) - A(j): red = synergy, blue = opposition.
Each panel has its own color scale (symmetric around zero).

______________________________

Summary of pairwise channel interactions across target populations. Each panel displays the mean R_ij matrix for one target group, with a final panel showing the grand mean. Red indicates synergistic channel pairs (supralinear integration), blue indicates opposing pairs (sublinear). Comparison across panels reveals population-specific differences in multisensory integration structure.
""")
    return fig


# =============================================================================
# B. Target neuron clustering
# =============================================================================

def plot_target_clustermap(interactions: pd.DataFrame,
                           channel_order: List[str],
                           target_colors: Dict[str, str],
                           save_path: Optional[str] = None,
                           ) -> plt.Figure:
    """
    Cluster target neurons by their 21-dim interaction profile vector.
    Uses cosine distance + Ward linkage. Annotated by target population.
    """
    # Deduplicate: same type can appear in multiple target groups
    interactions = interactions.copy()
    interactions["_priority"] = interactions["target_group"].apply(
        lambda g: 1 if g.endswith("_all") else 0)
    interactions = (interactions.sort_values(["target_type", "_priority"])
                                .drop_duplicates(subset=["target_type", "ch1", "ch2"], keep="first")
                                .drop(columns="_priority"))

    # Pivot: each target neuron gets a row, each pair a column
    interactions["pair"] = interactions["ch1"] + "+" + interactions["ch2"]

    feature_df = interactions.pivot_table(
        index=["target_group", "target_type"],
        columns="pair",
        values="R_ij",
        aggfunc="mean",
    ).fillna(0.0)

    if feature_df.shape[0] < 2:
        logger.warning("Not enough targets for clustering (need >= 2)")
        return plt.figure()

    # Compute distances
    X = feature_df.values
    dist = pdist(X, metric="cosine")
    dist = np.nan_to_num(dist, nan=1.0)
    Z = linkage(dist, method="ward")

    # Row colours by target group
    groups = feature_df.index.get_level_values("target_group")
    row_colors = [target_colors.get(g, "#999999") for g in groups]

    # Labels
    labels = [f"{tt} ({tg})" for tg, tt in feature_df.index]

    g = sns.clustermap(
        feature_df,
        row_linkage=Z,
        col_cluster=True,
        row_colors=row_colors,
        cmap="RdBu_r",
        center=0,
        figsize=(max(10, feature_df.shape[1] * 0.5), max(8, feature_df.shape[0] * 0.25)),
        yticklabels=labels,
        xticklabels=True,
        cbar_kws={"label": "R_ij"},
    )
    g.ax_heatmap.set_xlabel("Channel pair")
    g.ax_heatmap.set_ylabel("")
    g.fig.suptitle("Target neurons clustered by interaction profile", y=1.02)

    # Legend
    handles = [Patch(facecolor=c, label=g_name) for g_name, c in target_colors.items()]
    g.ax_heatmap.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.15, 1.0),
                        title="Target group", fontsize=7)

    _save(g.fig, save_path, close=True, description="""\
Target neuron clustering by interaction profile.

Each target neuron (row) is represented by a 21-dimensional vector of R_ij
values (one per channel pair). Neurons are clustered using cosine distance
and Ward linkage. The color strip on the left indicates target group membership.

This reveals which target neurons have similar patterns of multisensory
integration — i.e., which neurons respond similarly to channel combinations,
regardless of which target group they were assigned to.
Columns = channel pairs (e.g. DA1+VA1v). Red = synergy, blue = opposition.

______________________________

Hierarchical clustering of target neuron types by their pairwise interaction profiles. Each row represents one neuron type characterised by a 21-dimensional vector of R_ij scores (one per channel pair). Clustering uses cosine distance with Ward linkage. The colour strip indicates target group membership. Neurons that cluster together share similar patterns of multisensory integration regardless of their anatomical classification.
""")
    return g.fig


def plot_target_clustering_summary(interactions: pd.DataFrame,
                                    channel_order: List[str],
                                    target_colors: Dict[str, str],
                                    save_path: Optional[str] = None,
                                    k: int = 10,
                                    ) -> plt.Figure:
    """
    Cluster-averaged interaction profiles.

    1. Cluster targets by their R_ij profile (cosine distance, Ward linkage)
    2. Cut into k clusters
    3. Average interaction profiles within each cluster
    4. Show a clean heatmap of cluster means + composition bar + member list
    """
    # --- Deduplicate ---
    interactions = interactions.copy()
    interactions["_priority"] = interactions["target_group"].apply(
        lambda g: 1 if g.endswith("_all") else 0)
    interactions = (interactions.sort_values(["target_type", "_priority"])
                                .drop_duplicates(subset=["target_type", "ch1", "ch2"], keep="first")
                                .drop(columns="_priority"))

    interactions["pair"] = interactions["ch1"] + "+" + interactions["ch2"]

    feature_df = interactions.pivot_table(
        index=["target_group", "target_type"],
        columns="pair",
        values="R_ij",
        aggfunc="mean",
    ).fillna(0.0)

    if feature_df.shape[0] < 3:
        logger.warning("Not enough targets for cluster summary (need >= 3)")
        return plt.figure()

    X = feature_df.values
    dist = pdist(X, metric="cosine")
    dist = np.nan_to_num(dist, nan=1.0)
    Z = linkage(dist, method="ward")

    # Clamp k to available targets
    k = min(k, feature_df.shape[0] - 1)
    logger.info("Target clustering summary: k=%d clusters", k)

    labels = fcluster(Z, t=k, criterion="maxclust")
    feature_df["cluster"] = labels

    groups = feature_df.index.get_level_values("target_group")
    types = feature_df.index.get_level_values("target_type")
    pair_cols = [c for c in feature_df.columns if c != "cluster"]

    # --- Compute cluster means ---
    cluster_means = feature_df.groupby("cluster")[pair_cols].mean()

    # --- Cluster composition: count per target group ---
    comp_rows = []
    member_lists = {}
    for c in sorted(feature_df["cluster"].unique()):
        mask = feature_df["cluster"] == c
        c_groups = groups[mask]
        c_types = types[mask]
        member_lists[c] = list(c_types)
        row = {"cluster": c, "n": int(mask.sum())}
        for tg in target_colors:
            row[tg] = int((c_groups == tg).sum())
        comp_rows.append(row)
    comp_df = pd.DataFrame(comp_rows).set_index("cluster")

    # --- Figure: 3 panels ---
    fig = plt.figure(figsize=(max(10, len(pair_cols) * 0.55), 3 + k * 1.2))
    gs = fig.add_gridspec(1, 3, width_ratios=[5, 1.5, 3], wspace=0.4)

    # Panel 1: cluster-mean interaction heatmap
    ax_heat = fig.add_subplot(gs[0])
    vmax = max(abs(cluster_means.values.min()), abs(cluster_means.values.max())) or 1e-6
    im = ax_heat.imshow(cluster_means.values, cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                        aspect="auto")
    ax_heat.set_xticks(range(len(pair_cols)))
    ax_heat.set_xticklabels(pair_cols, rotation=90, fontsize=7)
    ax_heat.set_yticks(range(k))
    ax_heat.set_yticklabels([f"C{c} (n={comp_df.loc[c, 'n']})"
                             for c in cluster_means.index], fontsize=9)
    ax_heat.set_title("Mean interaction profile per cluster", fontsize=10)
    fig.colorbar(im, ax=ax_heat, shrink=0.6, label="mean R_ij")

    # Panel 2: stacked bar of target group composition
    ax_comp = fig.add_subplot(gs[1])
    bottom = np.zeros(k)
    tg_names = [tg for tg in target_colors if tg in comp_df.columns]
    for tg in tg_names:
        vals = comp_df[tg].values
        ax_comp.barh(range(k), vals, left=bottom,
                     color=target_colors.get(tg, "#999999"), label=tg, height=0.7)
        bottom += vals
    ax_comp.set_yticks(range(k))
    ax_comp.set_yticklabels([f"C{c}" for c in cluster_means.index], fontsize=9)
    ax_comp.set_xlabel("# types", fontsize=8)
    ax_comp.set_title("Composition", fontsize=10)
    ax_comp.legend(fontsize=5, loc="lower right", title="Group", title_fontsize=6)

    # Panel 3: member type list
    ax_text = fig.add_subplot(gs[2])
    ax_text.axis("off")
    text_lines = []
    for c in sorted(member_lists.keys()):
        members = member_lists[c]
        if len(members) > 12:
            shown = ", ".join(members[:12]) + f", ... (+{len(members) - 12})"
        else:
            shown = ", ".join(members)
        text_lines.append(f"C{c}: {shown}")
    ax_text.text(0, 1.0, "\n".join(text_lines),
                 transform=ax_text.transAxes, fontsize=6,
                 verticalalignment="top", fontfamily="monospace")
    ax_text.set_title("Cluster members", fontsize=10)

    fig.suptitle(f"Target neuron clusters (k={k})", fontsize=12, y=1.02)

    _save(fig, save_path, description=f"""\
Target neuron clustering summary (k={k} clusters).

Targets were clustered by their 21-dimensional pairwise interaction profile
(R_ij for each of 21 channel pairs) using cosine distance and Ward linkage.
The dendrogram is cut at k={k} clusters.

Left panel: mean R_ij profile per cluster. Each row is one cluster, each
column is a channel pair. Red = synergy, blue = opposition.

Middle panel: cluster composition — stacked bar showing how many neurons
from each target group (aspf, aspg, PPN1_downstream, etc.) fall in each cluster.

Right panel: list of neuron type names in each cluster.

This summarises the interaction landscape: neurons in the same cluster
respond similarly to channel combinations, suggesting shared integration logic.

______________________________

Cluster-averaged interaction profiles of target neurons (k={k}). Target types were clustered by their 21-dimensional R_ij vectors using cosine distance and Ward linkage. Left: mean interaction profile per cluster (red = synergy, blue = opposition). Centre: cluster composition showing the number of neurons from each target group. Right: neuron type names per cluster. Clusters group neurons with shared multisensory integration logic.
""")
    return fig


def plot_interaction_profile_per_group(interactions: pd.DataFrame,
                                       channel_order: List[str],
                                       target_colors: Dict[str, str],
                                       target_group: str,
                                       type_order: Optional[List[str]] = None,
                                       normalize: Optional[str] = None,
                                       save_path: Optional[str] = None,
                                       ) -> plt.Figure:
    """
    Per-neuron interaction profile heatmap for a single target group.

    Each row is one neuron type, each column is one of 21 channel pairs.
    normalize: None (raw), "cols" (per channel pair), or "rows" (per neuron).
    """
    df = interactions.copy()
    df = df[df["target_group"] == target_group]

    if len(df) == 0:
        logger.warning("No data for target group '%s'", target_group)
        return plt.figure()

    df["pair"] = df["ch1"] + "+" + df["ch2"]

    feature_df = df.pivot_table(
        index="target_type",
        columns="pair",
        values="R_ij",
        aggfunc="mean",
    ).fillna(0.0)

    # Order columns by channel_order
    pair_order = []
    for i, c1 in enumerate(channel_order):
        for c2 in channel_order[i + 1:]:
            pair_order.append(f"{c1}+{c2}")
    pair_cols = [p for p in pair_order if p in feature_df.columns]
    feature_df = feature_df[pair_cols]

    if normalize == "cols":
        col_max = feature_df.abs().max(axis=0)
        col_max[col_max == 0] = 1.0
        feature_df = feature_df / col_max
    elif normalize == "rows":
        row_max = feature_df.abs().max(axis=1)
        row_max[row_max == 0] = 1.0
        feature_df = feature_df.div(row_max, axis=0)

    n_types = len(feature_df)

    vmax = max(abs(feature_df.values.min()), abs(feature_df.values.max())) or 1e-6

    cbar_label = {"cols": "R_ij (col-normalized)", "rows": "R_ij (row-normalized)"}.get(
        normalize, "R_ij")

    g = sns.clustermap(
        feature_df,
        row_cluster=True if n_types >= 3 else False,
        col_cluster=False,
        cmap="RdBu_r",
        vmin=-vmax,
        vmax=vmax,
        figsize=(max(10, len(pair_cols) * 0.55), max(4, n_types * 0.35)),
        yticklabels=True,
        xticklabels=True,
        method="ward",
        metric="euclidean",
        cbar_kws={"label": cbar_label},
    )
    g.ax_heatmap.set_xlabel("Channel pair")
    g.ax_heatmap.set_ylabel("Target neuron type")
    g.ax_heatmap.tick_params(axis="y", labelsize=8)
    g.ax_heatmap.tick_params(axis="x", labelsize=7)

    norm_labels = {"cols": " (column-normalized)", "rows": " (row-normalized)"}
    norm_label = norm_labels.get(normalize, "")
    tg_color = target_colors.get(target_group, "black")
    g.fig.suptitle(f"{target_group} — pairwise interaction profiles{norm_label}",
                   fontsize=11, color=tg_color, y=1.02)

    norm_descs = {
        "cols": ("Values are column-normalized: each channel pair is divided by its\n"
                 "max absolute R_ij, so all columns range [-1, 1]. This emphasises\n"
                 "the relative pattern across neurons rather than absolute magnitude."),
        "rows": ("Values are row-normalized: each neuron's R_ij values are divided by\n"
                 "its max absolute R_ij, so all rows range [-1, 1]. This emphasises\n"
                 "the relative interaction pattern of each neuron across channel pairs."),
    }
    norm_desc = norm_descs.get(normalize, "Values show raw R_ij (not normalized).")

    norm_legend = {
        "cols": "Values are normalized per column (divided by max |R_ij|) to highlight relative patterns across neurons.",
        "rows": "Values are normalized per row (divided by max |R_ij|) to highlight each neuron's relative interaction pattern.",
    }
    norm_leg = norm_legend.get(normalize, "Cell values show raw R_ij.")

    fig = g.fig
    _save(fig, save_path, description=f"""\
Per-neuron pairwise interaction profile for {target_group}{norm_label}.

Each row is one neuron type in the {target_group} population. Each column is
one of 21 channel pairs. Red = synergy, blue = opposition.
{norm_desc}

Rows are hierarchically clustered (Euclidean distance, Ward linkage) to group
neurons with similar interaction profiles. Columns (channel pairs) are kept
in a fixed order matching the channel ordering.

______________________________

Pairwise interaction profiles for individual {target_group} neurons{norm_label}, hierarchically clustered. Each row represents one neuron type; each column represents one of 21 sensory channel pairs. {norm_leg} Red = synergy, blue = opposition. Rows are clustered by Euclidean distance with Ward linkage.
""")
    return fig


def plot_interaction_profile_per_group_biclustered(
        interactions: pd.DataFrame,
        channel_order: List[str],
        target_colors: Dict[str, str],
        target_group: str,
        normalize: Optional[str] = None,
        save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Same as plot_interaction_profile_per_group but with both rows AND columns
    clustered (biclustering). normalize: None, "cols", or "rows".
    """
    df = interactions.copy()
    df = df[df["target_group"] == target_group]

    if len(df) == 0:
        logger.warning("No data for target group '%s'", target_group)
        return plt.figure()

    df["pair"] = df["ch1"] + "+" + df["ch2"]

    feature_df = df.pivot_table(
        index="target_type",
        columns="pair",
        values="R_ij",
        aggfunc="mean",
    ).fillna(0.0)

    # Keep all available pair columns
    pair_order = []
    for i, c1 in enumerate(channel_order):
        for c2 in channel_order[i + 1:]:
            pair_order.append(f"{c1}+{c2}")
    pair_cols = [p for p in pair_order if p in feature_df.columns]
    feature_df = feature_df[pair_cols]

    if normalize == "cols":
        col_max = feature_df.abs().max(axis=0)
        col_max[col_max == 0] = 1.0
        feature_df = feature_df / col_max
    elif normalize == "rows":
        row_max = feature_df.abs().max(axis=1)
        row_max[row_max == 0] = 1.0
        feature_df = feature_df.div(row_max, axis=0)

    n_types = len(feature_df)
    vmax = max(abs(feature_df.values.min()), abs(feature_df.values.max())) or 1e-6

    cbar_label = {"cols": "R_ij (col-normalized)", "rows": "R_ij (row-normalized)"}.get(
        normalize, "R_ij")

    g = sns.clustermap(
        feature_df,
        row_cluster=True if n_types >= 3 else False,
        col_cluster=True if len(pair_cols) >= 3 else False,
        cmap="RdBu_r",
        vmin=-vmax,
        vmax=vmax,
        figsize=(max(10, len(pair_cols) * 0.55), max(4, n_types * 0.35)),
        yticklabels=True,
        xticklabels=True,
        method="ward",
        metric="euclidean",
        cbar_kws={"label": cbar_label},
    )
    g.ax_heatmap.set_xlabel("Channel pair")
    g.ax_heatmap.set_ylabel("Target neuron type")
    g.ax_heatmap.tick_params(axis="y", labelsize=8)
    g.ax_heatmap.tick_params(axis="x", labelsize=7)

    norm_labels = {"cols": " (column-normalized)", "rows": " (row-normalized)"}
    norm_label = norm_labels.get(normalize, "")
    tg_color = target_colors.get(target_group, "black")
    g.fig.suptitle(f"{target_group} — interaction profiles (biclustered){norm_label}",
                   fontsize=11, color=tg_color, y=1.02)

    norm_descs = {
        "cols": "Values are column-normalized (each pair divided by max |R_ij|, range [-1, 1]).",
        "rows": "Values are row-normalized (each neuron divided by max |R_ij|, range [-1, 1]).",
    }
    norm_desc = norm_descs.get(normalize, "Values show raw R_ij.")

    norm_legend = {
        "cols": "Values are normalized per column to highlight relative patterns across neurons.",
        "rows": "Values are normalized per row to highlight each neuron's relative interaction pattern.",
    }
    norm_leg = norm_legend.get(normalize, "Cell values show raw R_ij.")

    fig = g.fig
    _save(fig, save_path, description=f"""\
Biclustered pairwise interaction profile for {target_group}{norm_label}.

Each row is one neuron type, each column is one channel pair. Both rows and
columns are hierarchically clustered (Euclidean distance, Ward linkage).
{norm_desc}

Row clustering groups neurons with similar interaction profiles.
Column clustering groups channel pairs that tend to co-occur in synergy or
opposition across neurons — revealing correlated input pathways.

Red = synergy, blue = opposition.

______________________________

Biclustered pairwise interaction profiles for {target_group} neurons{norm_label}. Rows (neuron types) and columns (channel pairs) are both hierarchically clustered (Euclidean distance, Ward linkage). {norm_leg} Row dendrograms group neurons with similar integration patterns; column dendrograms reveal channel pairs with correlated interaction effects.
""")
    return fig


# =============================================================================
# C. Input channel clustering
# =============================================================================

def plot_channel_clustermap(interactions: pd.DataFrame,
                            channel_order: List[str],
                            modality_colors: Dict[str, str],
                            save_path: Optional[str] = None,
                            ) -> plt.Figure:
    """
    Cluster input channels by which targets they synergise/oppose at.
    Feature vector per channel = R_ij values with all other channels at all targets.
    """
    interactions = interactions.copy()

    # Deduplicate types appearing in multiple groups
    interactions["_priority"] = interactions["target_group"].apply(
        lambda g: 1 if g.endswith("_all") else 0)
    interactions = (interactions.sort_values(["target_type", "_priority"])
                                .drop_duplicates(subset=["target_type", "ch1", "ch2"], keep="first")
                                .drop(columns="_priority"))

    # Build feature matrix: one row per channel
    # For each channel, collect all R_ij involving that channel across all targets
    features = {}
    for ch in channel_order:
        mask = (interactions["ch1"] == ch) | (interactions["ch2"] == ch)
        subset = interactions[mask].copy()
        subset["partner"] = subset.apply(
            lambda r: r["ch2"] if r["ch1"] == ch else r["ch1"], axis=1
        )
        subset["key"] = subset["partner"] + "_" + subset["target_group"] + "_" + subset["target_type"]
        vec = subset.set_index("key")["R_ij"]
        features[ch] = vec

    feature_df = pd.DataFrame(features).fillna(0).T

    if feature_df.shape[0] < 2:
        return plt.figure()

    col_colors = [modality_colors.get(ch, "#999999") for ch in feature_df.index]

    g = sns.clustermap(
        feature_df,
        row_colors=col_colors,
        cmap="RdBu_r",
        center=0,
        figsize=(12, 5),
        yticklabels=True,
        xticklabels=False,
        cbar_kws={"label": "R_ij"},
    )
    g.fig.suptitle("Input channels clustered by interaction profile", y=1.02)
    _save(g.fig, save_path, close=True, description="""\
Input channel clustering by interaction profile.

Each sensory channel (row) is represented by a vector of R_ij values with
all other channels across all target neurons. Channels are clustered to
reveal which sensory modalities have similar interaction patterns.

For example, if DA1 and VA1v cluster together, they synergise/oppose with
the same partners at the same targets — suggesting shared integration pathways.
The color strip indicates sensory modality group.

______________________________

Hierarchical clustering of sensory input channels by their interaction profiles across target neurons. Each channel is represented by its R_ij values with all other channels at all targets. Channels that cluster together produce similar interaction patterns, suggesting convergence onto shared integration pathways in the connectome.
""")
    return g.fig


# =============================================================================
# D. Integrator identification
# =============================================================================

def plot_integrator_scatter(metrics: pd.DataFrame,
                            target_colors: Dict[str, str],
                            save_path: Optional[str] = None,
                            ) -> plt.Figure:
    """
    Scatter: integration score vs channel breadth, colored by target group.
    Labels top integrators.
    """
    # Deduplicate types appearing in multiple groups
    metrics = metrics.copy()
    metrics["_priority"] = metrics["target_group"].apply(lambda g: 1 if g.endswith("_all") else 0)
    metrics = (metrics.sort_values(["target_type", "_priority"])
                      .drop_duplicates(subset="target_type", keep="first")
                      .drop(columns="_priority"))

    fig, ax = plt.subplots(figsize=(8, 6))

    for tg in metrics["target_group"].unique():
        sub = metrics[metrics["target_group"] == tg]
        color = target_colors.get(tg, "#999999")
        ax.scatter(sub["channel_breadth"], sub["mean_synergy"],
                   c=color, label=tg, alpha=0.7, s=40, edgecolors="white", linewidths=0.5)

    # Label top 20 integrators; top 10 in red, 11-20 in black
    top20 = metrics.nlargest(20, "mean_synergy")
    for rank, (_, row) in enumerate(top20.iterrows()):
        color = "#E41A1C" if rank < 10 else "#333333"
        weight = "bold" if rank < 10 else "normal"
        ax.annotate(row["target_type"],
                    (row["channel_breadth"], row["mean_synergy"]),
                    fontsize=6, alpha=0.9, color=color, fontweight=weight,
                    xytext=(4, 4), textcoords="offset points")

    ax.set_xlabel("Channel breadth (# channels with above-threshold activation)")
    ax.set_ylabel("Integration score (mean positive R_ij)")
    ax.set_title("Integrator neuron identification")
    ax.legend(title="Target group", fontsize=8)
    fig.tight_layout()
    _save(fig, save_path, description="""\
Integrator neuron identification scatter plot.

Each point is one target neuron type. X-axis = channel breadth (number of
single channels that produce above-threshold activation at this target).
Y-axis = integration score (mean of positive R_ij values at this target).

Neurons in the upper-right are "integrators": they receive input from many
channels AND those channels synergise (positive R_ij). The top 10 integrators
are labelled. Colors indicate target group membership.

Channel breadth threshold = 10% of median single-channel activation.

______________________________

Identification of multisensory integrator neurons. Each point represents one target neuron type; x-axis shows channel breadth (number of sensory channels producing above-threshold activation), y-axis shows integration score (mean positive R_ij). Neurons in the upper right receive convergent input from many channels that interact synergistically. Top 10 labelled in red, 11–20 in black. Colours indicate target group.
""")
    return fig


def plot_integrator_scatter_activation(metrics: pd.DataFrame,
                                       target_colors: Dict[str, str],
                                       save_path: Optional[str] = None,
                                       ) -> plt.Figure:
    """
    Scatter: sum R_ij vs total activation (all channels on),
    colored by target group. Labels top neurons.
    """
    metrics = metrics.copy()
    metrics["_priority"] = metrics["target_group"].apply(lambda g: 1 if g.endswith("_all") else 0)
    metrics = (metrics.sort_values(["target_type", "_priority"])
                      .drop_duplicates(subset="target_type", keep="first")
                      .drop(columns="_priority"))

    fig, ax = plt.subplots(figsize=(8, 6))

    for tg in metrics["target_group"].unique():
        sub = metrics[metrics["target_group"] == tg]
        color = target_colors.get(tg, "#999999")
        ax.scatter(sub["total_activation"], sub["sum_R_ij"],
                   c=color, label=tg, alpha=0.7, s=40, edgecolors="white", linewidths=0.5)

    # Label top 20 by absolute sum R_ij; top 10 in red, 11-20 in black
    top20 = metrics.reindex(metrics["sum_R_ij"].abs().nlargest(20).index)
    for rank, (_, row) in enumerate(top20.iterrows()):
        color = "#E41A1C" if rank < 10 else "#333333"
        weight = "bold" if rank < 10 else "normal"
        ax.annotate(row["target_type"],
                    (row["total_activation"], row["sum_R_ij"]),
                    fontsize=6, alpha=0.9, color=color, fontweight=weight,
                    xytext=(4, 4), textcoords="offset points")

    ax.axhline(0, color="black", linewidth=0.5, linestyle="-")
    ax.set_xlabel("Total activation (all 7 channels on)")
    ax.set_ylabel("Sum R_ij (net pairwise interaction)")
    ax.set_title("Net interaction vs total activation")
    ax.legend(title="Target group", fontsize=8)
    fig.tight_layout()
    _save(fig, save_path, description="""\
Net interaction vs total activation scatter plot.

Each point is one target neuron type. X-axis = total activation when all
7 channels are stimulated simultaneously. Y-axis = sum of all 21 pairwise
R_ij values at this target (net interaction: positive = net synergy,
negative = net opposition).

Upper-right: strongly driven AND net synergistic (channels amplify each other).
Lower-right: strongly driven but net opposing (channels cancel each other).
Upper-left: weakly driven but synergistic (amplification without base drive).
Near y=0: channels are approximately additive at this target.

Top 10 by |sum R_ij| labelled in bold red, 11-20 in black.

______________________________

Net pairwise interaction versus total activation for target neurons. X-axis: activation when all seven sensory channels are stimulated simultaneously. Y-axis: sum of all 21 pairwise R_ij scores (positive = net synergy, negative = net opposition). Neurons in the upper right are both strongly driven and net synergistic. The horizontal line marks linear additivity (sum R_ij = 0). Top 10 neurons by |sum R_ij| labelled in red, 11–20 in black.
""")
    return fig


def plot_integrator_scatter_synergy(metrics: pd.DataFrame,
                                    target_colors: Dict[str, str],
                                    save_path: Optional[str] = None,
                                    ) -> plt.Figure:
    """
    Scatter: sum positive R_ij vs mean positive R_ij,
    colored by target group. Shows synergistic interaction landscape.
    """
    metrics = metrics.copy()
    metrics["_priority"] = metrics["target_group"].apply(lambda g: 1 if g.endswith("_all") else 0)
    metrics = (metrics.sort_values(["target_type", "_priority"])
                      .drop_duplicates(subset="target_type", keep="first")
                      .drop(columns="_priority"))

    fig, ax = plt.subplots(figsize=(8, 6))

    for tg in metrics["target_group"].unique():
        sub = metrics[metrics["target_group"] == tg]
        color = target_colors.get(tg, "#999999")
        ax.scatter(sub["mean_synergy"], sub["sum_positive_R_ij"],
                   c=color, label=tg, alpha=0.7, s=40, edgecolors="white", linewidths=0.5)

    # Label top 20 by sum_positive_R_ij; top 10 in red, 11-20 in black
    top20 = metrics.nlargest(20, "sum_positive_R_ij")
    for rank, (_, row) in enumerate(top20.iterrows()):
        color = "#E41A1C" if rank < 10 else "#333333"
        weight = "bold" if rank < 10 else "normal"
        ax.annotate(row["target_type"],
                    (row["mean_synergy"], row["sum_positive_R_ij"]),
                    fontsize=6, alpha=0.9, color=color, fontweight=weight,
                    xytext=(4, 4), textcoords="offset points")

    ax.set_xlabel("Mean positive R_ij (average synergy strength)")
    ax.set_ylabel("Sum positive R_ij (total synergy)")
    ax.set_title("Synergistic interactions: strength vs total")
    ax.legend(title="Target group", fontsize=8)
    fig.tight_layout()
    _save(fig, save_path, description="""\
Synergistic interaction scatter plot.

Each point is one target neuron type. X-axis = mean positive R_ij (average
strength of synergistic channel pairs at this target). Y-axis = sum of all
positive R_ij values (total synergy budget).

Upper-right: many strong synergistic pairs (broad, strong synergy).
Lower-left: few or weak synergies.
High x, low y: a few very strong synergies but not many pairs.
Low x, high y: many weak synergies that add up.

Top 10 by sum positive R_ij labelled in bold red, 11-20 in black.

______________________________

Synergistic interaction landscape across target neurons. X-axis: mean positive R_ij (average synergy strength per channel pair). Y-axis: sum of all positive R_ij values (total synergy budget). Neurons in the upper right have both strong and numerous synergistic channel interactions. Top 10 labelled in red, 11–20 in black. Colours indicate target group.
""")
    return fig


def plot_integrator_scatter_opposition(metrics: pd.DataFrame,
                                       target_colors: Dict[str, str],
                                       save_path: Optional[str] = None,
                                       ) -> plt.Figure:
    """
    Scatter: sum negative R_ij vs mean negative R_ij,
    colored by target group. Shows opposing interaction landscape.
    """
    metrics = metrics.copy()
    metrics["_priority"] = metrics["target_group"].apply(lambda g: 1 if g.endswith("_all") else 0)
    metrics = (metrics.sort_values(["target_type", "_priority"])
                      .drop_duplicates(subset="target_type", keep="first")
                      .drop(columns="_priority"))

    fig, ax = plt.subplots(figsize=(8, 6))

    for tg in metrics["target_group"].unique():
        sub = metrics[metrics["target_group"] == tg]
        color = target_colors.get(tg, "#999999")
        ax.scatter(sub["mean_opposition"], sub["sum_negative_R_ij"],
                   c=color, label=tg, alpha=0.7, s=40, edgecolors="white", linewidths=0.5)

    # Label top 20 by most negative sum; top 10 in red, 11-20 in black
    top20 = metrics.nsmallest(20, "sum_negative_R_ij")
    for rank, (_, row) in enumerate(top20.iterrows()):
        color = "#E41A1C" if rank < 10 else "#333333"
        weight = "bold" if rank < 10 else "normal"
        ax.annotate(row["target_type"],
                    (row["mean_opposition"], row["sum_negative_R_ij"]),
                    fontsize=6, alpha=0.9, color=color, fontweight=weight,
                    xytext=(4, 4), textcoords="offset points")

    ax.set_xlabel("Mean negative R_ij (average opposition strength)")
    ax.set_ylabel("Sum negative R_ij (total opposition)")
    ax.set_title("Opposing interactions: strength vs total")
    ax.legend(title="Target group", fontsize=8)
    fig.tight_layout()
    _save(fig, save_path, description="""\
Opposing interaction scatter plot.

Each point is one target neuron type. X-axis = mean negative R_ij (average
strength of opposing/destructive channel pairs at this target). Y-axis = sum
of all negative R_ij values (total opposition budget).

Lower-left: many strong opposing pairs (broad, strong interference).
Upper-right (near zero): few or weak opposing interactions.
Very negative x, near-zero y: a few very strong opposing pairs but not many.
Near-zero x, very negative y: many weak opposing pairs that accumulate.

Top 10 by most negative sum labelled in bold red, 11-20 in black.

______________________________

Opposing interaction landscape across target neurons. X-axis: mean negative R_ij (average opposition strength per channel pair). Y-axis: sum of all negative R_ij values (total opposition budget). Neurons in the lower left have both strong and numerous destructive channel interactions. Top 10 labelled in red, 11–20 in black. Colours indicate target group.
""")
    return fig


# =============================================================================
# E. All-channels-together summary
# =============================================================================

def plot_all_channels_bar(total_interaction: pd.DataFrame,
                          target_colors: Dict[str, str],
                          save_path: Optional[str] = None,
                          ) -> plt.Figure:
    """
    Bar plot of R_all per target neuron, coloured by target group.
    """
    df = total_interaction.sort_values("R_all", ascending=False).copy()

    # Deduplicate: same type can appear in multiple target groups (e.g. _all
    # variants or shared between PPN1/vAB3). Prefer the more specific group
    # (non-_all over _all).
    df["_priority"] = df["target_group"].apply(lambda g: 1 if g.endswith("_all") else 0)
    df = (df.sort_values(["target_type", "_priority"])
            .drop_duplicates(subset="target_type", keep="first")
            .drop(columns="_priority")
            .sort_values("R_all", ascending=False))

    fig, ax = plt.subplots(figsize=(max(10, len(df) * 0.3), 6))

    colors = [target_colors.get(tg, "#999999") for tg in df["target_group"]]
    bars = ax.bar(range(len(df)), df["R_all"], color=colors, edgecolor="white", linewidth=0.3)

    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df["target_type"], rotation=90, fontsize=6)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_ylabel("R_all (total interaction score)")
    ax.set_title("All channels combined: deviation from linear summation")

    handles = [Patch(facecolor=c, label=g) for g, c in target_colors.items()]
    ax.legend(handles=handles, fontsize=7, title="Target group")
    fig.tight_layout()
    _save(fig, save_path, description="""\
All-channels-together bar plot.

Each bar is one target neuron type, showing R_all = A(all) - sum(A(i)):
the total interaction score when all 7 channels are stimulated simultaneously.
R_all measures how much the all-channels response deviates from the sum of
individual channel responses.

Positive R_all = overall supralinear integration (the neuron responds more
to everything together than the sum of parts).
Negative R_all = overall sublinear / suppressive interaction.

Bars are sorted by R_all descending. Colors indicate target group.

______________________________

Total interaction score R_all per target neuron when all seven sensory channels are active simultaneously. R_all = A(all) − Σ A(i) measures the deviation of the combined response from the linear sum of individual channel responses. Positive values indicate supralinear integration; negative values indicate suppressive interactions. Bars sorted by descending R_all, coloured by target group.
""")
    return fig


def plot_pairwise_vs_total(pairwise: pd.DataFrame,
                           total: pd.DataFrame,
                           target_colors: Dict[str, str],
                           save_path: Optional[str] = None,
                           ) -> plt.Figure:
    """
    Scatter: sum of pairwise R_ij vs R_all.
    Tests how much interaction is pairwise-explainable vs higher-order.
    """
    sum_pairwise = (pairwise.groupby(["target_group", "target_type"])["R_ij"]
                    .sum().reset_index().rename(columns={"R_ij": "sum_R_ij"}))

    merged = total.merge(sum_pairwise, on=["target_group", "target_type"], how="left")
    merged["sum_R_ij"] = merged["sum_R_ij"].fillna(0)

    # Deduplicate types appearing in multiple groups
    merged["_priority"] = merged["target_group"].apply(lambda g: 1 if g.endswith("_all") else 0)
    merged = (merged.sort_values(["target_type", "_priority"])
                    .drop_duplicates(subset="target_type", keep="first")
                    .drop(columns="_priority"))

    fig, ax = plt.subplots(figsize=(7, 7))

    for tg in merged["target_group"].unique():
        sub = merged[merged["target_group"] == tg]
        color = target_colors.get(tg, "#999999")
        ax.scatter(sub["sum_R_ij"], sub["R_all"], c=color, label=tg, alpha=0.7, s=40)

    # Identity line
    lims = [min(ax.get_xlim()[0], ax.get_ylim()[0]),
            max(ax.get_xlim()[1], ax.get_ylim()[1])]
    ax.plot(lims, lims, "k--", alpha=0.3, linewidth=1)

    # Label points furthest from the diagonal (largest higher-order effects)
    merged["_residual"] = (merged["R_all"] - merged["sum_R_ij"]).abs()
    outliers = merged.nlargest(15, "_residual")
    for _, row in outliers.iterrows():
        ax.annotate(row["target_type"],
                    (row["sum_R_ij"], row["R_all"]),
                    fontsize=5, alpha=0.8,
                    xytext=(4, 4), textcoords="offset points")

    ax.set_xlabel("Sum of pairwise R_ij")
    ax.set_ylabel("R_all (total interaction)")
    ax.set_title("Pairwise-explainable vs higher-order interactions")
    ax.legend(title="Target group", fontsize=8)
    fig.tight_layout()
    _save(fig, save_path, description="""\
Pairwise vs total interaction scatter plot.

Each point is one target neuron type. X-axis = sum of all pairwise R_ij.
Y-axis = R_all (total interaction when all 7 channels active).

Points on the dashed diagonal: total interaction is fully explained by
the sum of pairwise interactions (no higher-order effects).
Points above the line: higher-order interactions add extra synergy.
Points below the line: higher-order interactions are suppressive.

This tests whether pairwise channel interactions are sufficient to predict
multisensory integration, or whether genuine higher-order (3-way+) effects exist.

______________________________

Pairwise versus total interaction at each target neuron. X-axis: sum of all 21 pairwise interaction scores Σ R_ij. Y-axis: total interaction R_all when all channels are active. Points on the dashed diagonal indicate that pairwise interactions fully account for the total; deviations reveal higher-order (≥3-way) interaction effects. Labelled points have the largest residuals from the diagonal. Colours indicate target group.
""")
    return fig


# =============================================================================
# F. Sensitivity analysis plots
# =============================================================================

def plot_sensitivity_grid(sensitivity_results: pd.DataFrame,
                          channel_order: List[str],
                          reference_pairwise: pd.DataFrame,
                          save_path: Optional[str] = None,
                          ) -> plt.Figure:
    """
    Faceted heatmaps: top synergistic channel pair at each
    (normalization x n_steps x nonlinearity) combination.
    Shows stability of key findings across parameter choices.
    """
    # For each parameter combo, compute pairwise interactions and find top pair
    combos = sensitivity_results.groupby(["normalization", "n_steps", "nonlinearity"])

    rows = []
    for (norm, steps, nonlin), group in combos:
        from signal_flow import InteractionAnalyzer
        analyzer = InteractionAnalyzer(group)
        pw = analyzer.compute_pairwise_interactions()
        if len(pw) == 0:
            continue

        # Mean R_ij per channel pair (across all targets)
        pair_means = pw.groupby(["ch1", "ch2"])["R_ij"].mean().reset_index()

        for _, p in pair_means.iterrows():
            rows.append({
                "normalization": norm,
                "n_steps": steps,
                "nonlinearity": nonlin,
                "ch1": p["ch1"],
                "ch2": p["ch2"],
                "mean_R_ij": p["R_ij"],
            })

    if not rows:
        logger.warning("No sensitivity data to plot")
        return plt.figure()

    sens_df = pd.DataFrame(rows)

    # Plot: facet by channel pair, x=n_steps, y=normalization, color=mean_R_ij
    # Pick top 6 most variable pairs
    pair_var = (sens_df.groupby(["ch1", "ch2"])["mean_R_ij"]
                .std().nlargest(6).reset_index())
    top_pairs = list(zip(pair_var["ch1"], pair_var["ch2"]))

    n_pairs = len(top_pairs)
    n_nonlin = sens_df["nonlinearity"].nunique()

    fig, axes = plt.subplots(n_pairs, n_nonlin,
                             figsize=(4 * n_nonlin, 3 * n_pairs),
                             squeeze=False)

    nonlinearities = sorted(sens_df["nonlinearity"].unique())

    for i, (c1, c2) in enumerate(top_pairs):
        for j, nonlin in enumerate(nonlinearities):
            sub = sens_df[(sens_df["ch1"] == c1) &
                          (sens_df["ch2"] == c2) &
                          (sens_df["nonlinearity"] == nonlin)]

            if len(sub) == 0:
                axes[i, j].set_visible(False)
                continue

            pivot = sub.pivot_table(index="normalization", columns="n_steps",
                                    values="mean_R_ij")
            vmax = max(abs(pivot.values.min()), abs(pivot.values.max())) or 1e-6

            sns.heatmap(pivot, ax=axes[i, j], cmap="RdBu_r", center=0,
                        vmin=-vmax, vmax=vmax, annot=True, fmt=".1e",
                        annot_kws={"fontsize": 6})

            if i == 0:
                axes[i, j].set_title(nonlin, fontsize=10)
            if j == 0:
                axes[i, j].set_ylabel(f"{c1} + {c2}", fontsize=9)
            else:
                axes[i, j].set_ylabel("")

    fig.suptitle("Sensitivity: mean R_ij across parameter space", fontsize=13, y=1.01)
    fig.tight_layout()
    _save(fig, save_path, description="""\
Sensitivity analysis grid.

Shows how the top 6 most variable channel pairs' mean R_ij values change
across the parameter space: normalization (post/pre/raw) x n_steps (2-5)
x nonlinearity (relu/sigmoid/softplus).

Each subplot row is one channel pair. Each column is one nonlinearity.
Within each subplot, rows = normalization, columns = n_steps.
Red = synergy, blue = opposition. This reveals whether key interaction
findings are robust to parameter choices or sensitive to specific settings.

______________________________

Sensitivity of key pairwise interactions to analysis parameters. Each row shows one channel pair (top 6 most variable); columns correspond to nonlinearities (ReLU, sigmoid, leaky ReLU). Within each cell, the heatmap spans normalisation methods (rows) and propagation steps (columns). Consistent colours across conditions indicate robust interactions; variable colours indicate parameter-sensitive findings.
""")
    return fig


def plot_interaction_forest(interactions: pd.DataFrame,
                            channel_order: List[str],
                            modality_colors: Dict[str, str],
                            target_colors: Dict[str, str],
                            save_path: Optional[str] = None,
                            ) -> plt.Figure:
    """
    Forest plot: mean R_ij ± SEM per channel pair, faceted by target group.
    Shows which interactions are synergistic, destructive, or neutral.
    """
    interactions = interactions.copy()

    # Deduplicate
    interactions["_priority"] = interactions["target_group"].apply(
        lambda g: 1 if g.endswith("_all") else 0)
    interactions = (interactions.sort_values(["target_type", "_priority"])
                                .drop_duplicates(subset=["target_type", "ch1", "ch2"], keep="first")
                                .drop(columns="_priority"))

    interactions["pair"] = interactions["ch1"] + "+" + interactions["ch2"]

    # Order pairs by channel_order
    pair_order = []
    for i, c1 in enumerate(channel_order):
        for c2 in channel_order[i+1:]:
            pair_order.append(f"{c1}+{c2}")

    target_groups = sorted(interactions["target_group"].unique(),
                           key=lambda g: (g.endswith("_all"), g))

    n_groups = len(target_groups)
    fig, axes = plt.subplots(1, n_groups, figsize=(5 * n_groups, 8),
                             sharey=True, sharex=True, squeeze=False)

    # Track global x range for shared axis
    global_xmin, global_xmax = 0.0, 0.0

    for col, tg in enumerate(target_groups):
        ax = axes[0][col]
        sub = interactions[interactions["target_group"] == tg]

        stats = (sub.groupby("pair")["R_ij"]
                 .agg(["mean", "sem", "count", "std"])
                 .reindex(pair_order)
                 .dropna())

        y_pos = list(range(len(stats)))
        means = stats["mean"].values
        sems = stats["sem"].values

        # Update global range (mean ± 2 SEM)
        if len(means) > 0:
            lo = (means - 2 * sems).min()
            hi = (means + 2 * sems).max()
            global_xmin = min(global_xmin, lo)
            global_xmax = max(global_xmax, hi)

        # Color by sign: synergistic (red), destructive (blue), neutral (grey)
        colors = []
        markers = []
        for m, s in zip(means, sems):
            if s > 0 and abs(m) > 2 * s:  # "significant" at ~2 SEM
                colors.append("#E41A1C" if m > 0 else "#377EB8")
                markers.append("D")
            else:
                colors.append("#999999")
                markers.append("o")

        # Plot error bars
        ax.axvline(0, color="black", linewidth=0.5, linestyle="-")

        for i, (y, m, sem, c, mk) in enumerate(zip(y_pos, means, sems, colors, markers)):
            ax.errorbar(m, y, xerr=2*sem, fmt="none", ecolor=c, elinewidth=1, capsize=2)
            ax.scatter(m, y, c=c, marker=mk, s=30, zorder=5, edgecolors="white", linewidths=0.3)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(stats.index, fontsize=7)
        ax.set_title(tg, fontsize=10, color=target_colors.get(tg, "black"))
        ax.set_xlabel("mean R_ij", fontsize=8)
        ax.invert_yaxis()

        # Light grid
        ax.grid(axis="x", alpha=0.2)

    # Set shared x limits with a small margin
    margin = (global_xmax - global_xmin) * 0.05 or 1e-6
    for ax in axes.flat:
        ax.set_xlim(global_xmin - margin, global_xmax + margin)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="D", color="w", markerfacecolor="#E41A1C",
               markersize=7, label="Synergistic (|mean| > 2 SEM)"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor="#377EB8",
               markersize=7, label="Destructive (|mean| > 2 SEM)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#999999",
               markersize=7, label="Not significant"),
    ]
    axes[0][0].legend(handles=legend_elements, loc="lower left", fontsize=7)

    fig.suptitle("Interaction significance: synergistic vs destructive vs neutral",
                 fontsize=12)
    fig.tight_layout()
    _save(fig, save_path, description="""\
Interaction forest plot: synergistic vs destructive channel pairs per target group.

Each panel is one target group. Each row is a channel pair (21 total).
Points show mean R_ij across all target neurons in that group, with
error bars = 2x SEM (approximate 95% confidence interval).

Red diamonds: significant synergy (mean R_ij > 0 and |mean| > 2 SEM).
  These channel pairs produce MORE activation together than individually.
Blue diamonds: significant opposition (mean R_ij < 0 and |mean| > 2 SEM).
  These channel pairs INTERFERE when combined.
Grey circles: not significant (effect indistinguishable from zero).
  These channels are effectively independent at these targets.

The vertical black line marks R_ij = 0 (linear additivity / independence).

______________________________

Forest plot of pairwise channel interactions per target population. Each panel corresponds to one target group; each row is one of 21 channel pairs. Points and error bars show the mean R_ij ± 2 SEM across neurons in that group. Red diamonds indicate significant synergy (mean > 0, |mean| > 2 SEM), blue diamonds indicate significant opposition, and grey circles indicate non-significant interactions. The vertical line at zero marks linear additivity.
""")
    return fig


# =============================================================================
# H. Signal identity interaction plot
# =============================================================================

# Biological signal identity of each channel
SIGNAL_IDENTITY = {
    "ppk25":    "female",
    "ppk23":    "male",
    "DA1":      "male",
    "visual":   "both",
    "auditory":  "both",
    "VA1v":     "neutral",
    "VA1d":     "neutral",
}

SIGNAL_CATEGORIES = ["female", "male", "both", "neutral"]
SIGNAL_COLORS = {
    "female":  "#E41A1C",
    "male":    "#377EB8",
    "both":    "#984EA3",
    "neutral": "#999999",
}


def plot_signal_identity_interactions(interactions: pd.DataFrame,
                                      channel_order: List[str],
                                      target_colors: Dict[str, str],
                                      save_path: Optional[str] = None,
                                      ) -> plt.Figure:
    """
    Collapse channel interactions into biological signal categories
    (female / male / both / neutral) and show category-level interactions
    per target group.

    Two panels per target group:
      - Left: 4x4 category interaction heatmap (mean R_ij between categories)
      - Right: bar chart of category-pair R_ij with SEM error bars
    """
    interactions = interactions.copy()

    # Deduplicate
    interactions["_priority"] = interactions["target_group"].apply(
        lambda g: 1 if g.endswith("_all") else 0)
    interactions = (interactions.sort_values(["target_type", "_priority"])
                                .drop_duplicates(subset=["target_type", "ch1", "ch2"], keep="first")
                                .drop(columns="_priority"))

    # Map channels to signal categories
    interactions["sig1"] = interactions["ch1"].map(SIGNAL_IDENTITY)
    interactions["sig2"] = interactions["ch2"].map(SIGNAL_IDENTITY)

    # Canonical order for category pairs (avoid double-counting)
    def cat_pair(s1, s2):
        idx1 = SIGNAL_CATEGORIES.index(s1) if s1 in SIGNAL_CATEGORIES else 99
        idx2 = SIGNAL_CATEGORIES.index(s2) if s2 in SIGNAL_CATEGORIES else 99
        if idx1 <= idx2:
            return f"{s1} × {s2}"
        return f"{s2} × {s1}"

    interactions["cat_pair"] = interactions.apply(
        lambda r: cat_pair(r["sig1"], r["sig2"]), axis=1)

    target_groups = sorted(interactions["target_group"].unique(),
                           key=lambda g: (g.endswith("_all"), g))

    # --- Figure: heatmaps + bar charts ---
    n_groups = len(target_groups)
    fig, axes = plt.subplots(2, n_groups,
                             figsize=(4.5 * n_groups, 10),
                             squeeze=False)

    # Unique category pairs in canonical order
    cat_pairs_ordered = []
    for i, c1 in enumerate(SIGNAL_CATEGORIES):
        for c2 in SIGNAL_CATEGORIES[i:]:
            cat_pairs_ordered.append(f"{c1} × {c2}")

    # First pass: compute all matrices and bar stats to find global scales
    n_cat = len(SIGNAL_CATEGORIES)
    all_mats = []
    all_bar_stats = []

    for tg in target_groups:
        sub = interactions[interactions["target_group"] == tg]

        mat = np.zeros((n_cat, n_cat))
        cat_stats = sub.groupby(["sig1", "sig2"])["R_ij"].mean()
        for (s1, s2), val in cat_stats.items():
            i = SIGNAL_CATEGORIES.index(s1) if s1 in SIGNAL_CATEGORIES else None
            j = SIGNAL_CATEGORIES.index(s2) if s2 in SIGNAL_CATEGORIES else None
            if i is not None and j is not None:
                mat[i, j] = val
                mat[j, i] = val
        all_mats.append(mat)

        bar_stats = (sub.groupby("cat_pair")["R_ij"]
                     .agg(["mean", "sem"])
                     .reindex(cat_pairs_ordered)
                     .dropna())
        all_bar_stats.append(bar_stats)

    # Global heatmap colour scale
    global_vmax = max(abs(m).max() for m in all_mats) or 1e-6

    # Global bar y-axis limits
    bar_ymin, bar_ymax = 0.0, 0.0
    for bs in all_bar_stats:
        if len(bs) > 0:
            lo = (bs["mean"] - 2 * bs["sem"]).min()
            hi = (bs["mean"] + 2 * bs["sem"]).max()
            bar_ymin = min(bar_ymin, lo)
            bar_ymax = max(bar_ymax, hi)
    bar_margin = (bar_ymax - bar_ymin) * 0.05 or 1e-6

    # Second pass: plot
    for col, tg in enumerate(target_groups):
        mat = all_mats[col]
        bar_stats = all_bar_stats[col]

        # --- Top: 4x4 heatmap ---
        ax_heat = axes[0][col]
        im = ax_heat.imshow(mat, cmap="RdBu_r", vmin=-global_vmax, vmax=global_vmax,
                            aspect="equal")
        ax_heat.set_xticks(range(n_cat))
        ax_heat.set_yticks(range(n_cat))
        ax_heat.set_xticklabels(SIGNAL_CATEGORIES, rotation=45, ha="right", fontsize=9)
        ax_heat.set_yticklabels(SIGNAL_CATEGORIES, fontsize=9)

        # Annotate
        for i in range(n_cat):
            for j in range(n_cat):
                ax_heat.text(j, i, f"{mat[i, j]:.2e}", ha="center", va="center", fontsize=7)

        fig.colorbar(im, ax=ax_heat, shrink=0.7)
        ax_heat.set_title(tg, fontsize=10, color=target_colors.get(tg, "black"))

        # --- Bottom: bar chart of category pairs ---
        ax_bar = axes[1][col]
        x = range(len(bar_stats))
        means = bar_stats["mean"].values
        sems = bar_stats["sem"].values

        bar_colors = []
        for cp in bar_stats.index:
            parts = cp.split(" × ")
            if parts[0] == parts[1]:
                bar_colors.append(SIGNAL_COLORS.get(parts[0], "#999999"))
            elif "female" in parts and "male" in parts:
                bar_colors.append("#FF7F00")  # cross-sex = orange
            else:
                bar_colors.append("#AAAAAA")

        ax_bar.bar(x, means, yerr=2*sems, color=bar_colors,
                   edgecolor="white", linewidth=0.5, capsize=3, error_kw={"linewidth": 1})
        ax_bar.set_xticks(x)
        ax_bar.set_xticklabels(bar_stats.index, rotation=60, ha="right", fontsize=7)
        ax_bar.axhline(0, color="black", linewidth=0.5)
        ax_bar.set_ylabel("mean R_ij", fontsize=8)
        ax_bar.set_ylim(bar_ymin - bar_margin, bar_ymax + bar_margin)

    axes[0][0].set_ylabel("Signal category", fontsize=9)

    fig.suptitle("Interactions by biological signal identity\n"
                 "(female=ppk25 | male=ppk23,DA1 | both=visual,auditory | neutral=VA1v,VA1d)",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    _save(fig, save_path, description="""\
Signal identity interaction plot.

Channels are grouped by biological signal identity:
  - female: ppk25 (female contact pheromone)
  - male: ppk23, DA1 (male-specific signals)
  - both: visual (LC10), auditory (JO-B) (sex-nonspecific)
  - neutral: VA1v, VA1d (general olfactory, not sex-specific)

Top row: 4x4 heatmap of mean R_ij between signal categories per target group.
  Red = synergy (e.g. female × male signals enhance each other at this target).
  Blue = opposition (signals interfere).

Bottom row: bar chart of each category pair's mean R_ij (± 2 SEM).
  Orange bars highlight female × male cross-sex interactions.

Key biological question answered:
  - Do female + male signals synergize at courtship command neurons (aSP-f/g)?
  - Do same-sex signals show redundancy (opposition) or reinforcement (synergy)?
  - Are neutral channels truly independent of sex-specific signals?

______________________________

Interactions between sensory channels grouped by biological signal identity. Channels are classified as female (ppk25), male (ppk23, DA1), both-sex (visual, auditory), or neutral (VA1v, VA1d). Top row: 4×4 heatmaps of mean R_ij between signal categories per target group, with a shared colour scale (red = synergy, blue = opposition). Bottom row: bar charts of each category pair's mean R_ij ± 2 SEM. Orange bars highlight female × male cross-sex interactions.
""")
    return fig


def plot_activation_profiles(results: pd.DataFrame,
                             channel_order: List[str],
                             modality_colors: Dict[str, str],
                             target_colors: Dict[str, str],
                             save_path: Optional[str] = None,
                             ) -> plt.Figure:
    """
    Heatmap of single-channel activation at each target neuron.
    Rows = target neurons, columns = channels. Like a radar plot in matrix form.
    """
    singles = results[results["n_channels"] == 1].copy()

    # Deduplicate types appearing in multiple groups
    singles["_priority"] = singles["target_group"].apply(
        lambda g: 1 if g.endswith("_all") else 0)
    singles = (singles.sort_values(["target_type", "_priority"])
                      .drop_duplicates(subset=["target_type", "combination"], keep="first")
                      .drop(columns="_priority"))

    # Pivot: rows=target, cols=channel
    pivot = singles.pivot_table(
        index=["target_group", "target_type"],
        columns="combination",
        values="activation",
        aggfunc="mean",
    ).fillna(0)

    # Reorder columns
    pivot = pivot[[ch for ch in channel_order if ch in pivot.columns]]

    # Normalize per column (like the R heatmaps)
    col_max = pivot.max(axis=0)
    col_max[col_max == 0] = 1
    pivot_norm = pivot / col_max

    # Row colours
    groups = pivot_norm.index.get_level_values("target_group")
    row_colors = [target_colors.get(g, "#999999") for g in groups]

    labels = [f"{tt}" for _, tt in pivot_norm.index]

    g = sns.clustermap(
        pivot_norm,
        row_colors=row_colors,
        col_cluster=False,
        cmap="viridis",
        figsize=(8, max(6, len(pivot_norm) * 0.2)),
        yticklabels=labels,
        xticklabels=True,
        cbar_kws={"label": "Activation (col-normalized)"},
        method="ward",
    )
    g.fig.suptitle("Single-channel activation profiles", y=1.02)

    handles = [Patch(facecolor=c, label=g_name) for g_name, c in target_colors.items()]
    g.ax_heatmap.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.15, 1.0),
                        title="Target group", fontsize=7)

    _save(g.fig, save_path, close=True, description="""\
Single-channel activation profile heatmap.

Each row is one target neuron type, each column is one sensory channel.
Values show the activation at each target when only that single channel
is stimulated (no combinations). Values are column-normalized (divided by
each channel's max activation) to allow visual comparison across channels
with different absolute magnitudes.

Rows are clustered (Ward linkage) to group target neurons with similar
activation profiles. Color strip = target group. This reveals which targets
are reached by which channels, independent of interaction effects.

______________________________

Single-channel activation profiles across target neurons. Each row is one neuron type, each column is one sensory channel stimulated alone. Values are column-normalised to the channel maximum. Rows are hierarchically clustered (Ward linkage) to group targets with similar sensory tuning. The colour strip indicates target group membership. This reveals the baseline sensory selectivity of each target independent of channel interactions.
""")
    return g.fig


# =============================================================================
# CLUSTER-LEVEL VARIANTS
# =============================================================================

def _cluster_targets(interactions: pd.DataFrame, k: int = 10):
    """
    Cluster target neurons by their 21-dim pairwise interaction profile.

    Returns (interactions_with_cluster, cluster_info) where:
      - interactions_with_cluster: original df + 'cluster' column
      - cluster_info: dict of cluster_id -> {'members': [...], 'groups': [...]}
    """
    df = interactions.copy()

    # Deduplicate
    df["_priority"] = df["target_group"].apply(
        lambda g: 1 if g.endswith("_all") else 0)
    df = (df.sort_values(["target_type", "_priority"])
            .drop_duplicates(subset=["target_type", "ch1", "ch2"], keep="first")
            .drop(columns="_priority"))

    df["pair"] = df["ch1"] + "+" + df["ch2"]

    feature_df = df.pivot_table(
        index=["target_group", "target_type"],
        columns="pair",
        values="R_ij",
        aggfunc="mean",
    ).fillna(0.0)

    if feature_df.shape[0] < 3:
        logger.warning("Not enough targets for clustering (need >= 3)")
        return df, {}

    X = feature_df.values
    dist = pdist(X, metric="cosine")
    dist = np.nan_to_num(dist, nan=1.0)
    Z = linkage(dist, method="ward")

    k = min(k, feature_df.shape[0] - 1)
    labels = fcluster(Z, t=k, criterion="maxclust")

    # Map (target_group, target_type) -> cluster
    cluster_map = {}
    for (tg, tt), cl in zip(feature_df.index, labels):
        cluster_map[(tg, tt)] = int(cl)

    df["cluster"] = df.apply(
        lambda r: cluster_map.get((r["target_group"], r["target_type"]), -1),
        axis=1,
    )
    df = df[df["cluster"] > 0]

    # Cluster info
    cluster_info = {}
    for cl in sorted(set(labels)):
        mask = labels == cl
        members = feature_df.index[mask]
        cluster_info[int(cl)] = {
            "members": [tt for _, tt in members],
            "groups": [tg for tg, _ in members],
            "n": int(mask.sum()),
        }

    return df, cluster_info


def plot_interaction_forest_clustered(interactions: pd.DataFrame,
                                      channel_order: List[str],
                                      modality_colors: Dict[str, str],
                                      target_colors: Dict[str, str],
                                      k: int = 10,
                                      save_path: Optional[str] = None,
                                      ) -> plt.Figure:
    """
    Forest plot of mean R_ij ± SEM per channel pair, faceted by cluster (k=10).
    Same layout as plot_interaction_forest but clusters replace target groups.
    """
    df, cluster_info = _cluster_targets(interactions, k=k)
    if not cluster_info:
        return plt.figure()

    df["pair"] = df["ch1"] + "+" + df["ch2"]

    pair_order = []
    for i, c1 in enumerate(channel_order):
        for c2 in channel_order[i + 1:]:
            pair_order.append(f"{c1}+{c2}")

    clusters = sorted(cluster_info.keys())
    n_clusters = len(clusters)

    # Use up to 2 rows if many clusters
    n_cols = min(n_clusters, 5)
    n_rows = (n_clusters + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols,
                             figsize=(5 * n_cols, 8 * n_rows),
                             sharey=True, sharex=True, squeeze=False)

    # Assign cluster colours based on dominant target group
    from collections import Counter
    cluster_colors = {}
    for cl, info in cluster_info.items():
        group_counts = Counter(info["groups"])
        dominant = group_counts.most_common(1)[0][0]
        cluster_colors[cl] = target_colors.get(dominant, "#999999")

    # Track global x range for shared axis
    global_xmin, global_xmax = 0.0, 0.0

    for idx, cl in enumerate(clusters):
        row, col = divmod(idx, n_cols)
        ax = axes[row][col]
        sub = df[df["cluster"] == cl]

        stats = (sub.groupby("pair")["R_ij"]
                 .agg(["mean", "sem", "count"])
                 .reindex(pair_order)
                 .dropna())

        y_pos = list(range(len(stats)))
        means = stats["mean"].values
        sems = stats["sem"].values

        # Update global range
        if len(means) > 0:
            lo = (means - 2 * sems).min()
            hi = (means + 2 * sems).max()
            global_xmin = min(global_xmin, lo)
            global_xmax = max(global_xmax, hi)

        colors = []
        markers = []
        for m, s in zip(means, sems):
            if s > 0 and abs(m) > 2 * s:
                colors.append("#E41A1C" if m > 0 else "#377EB8")
                markers.append("D")
            else:
                colors.append("#999999")
                markers.append("o")

        ax.axvline(0, color="black", linewidth=0.5, linestyle="-")

        for i, (y, m, sem, c, mk) in enumerate(zip(y_pos, means, sems, colors, markers)):
            ax.errorbar(m, y, xerr=2 * sem, fmt="none", ecolor=c, elinewidth=1, capsize=2)
            ax.scatter(m, y, c=c, marker=mk, s=30, zorder=5,
                       edgecolors="white", linewidths=0.3)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(stats.index, fontsize=7)
        info = cluster_info[cl]
        members_short = ", ".join(info["members"][:5])
        if info["n"] > 5:
            members_short += f", +{info['n'] - 5}"
        ax.set_title(f"Cluster {cl} (n={info['n']})\n{members_short}",
                     fontsize=8, color=cluster_colors[cl])
        ax.set_xlabel("mean R_ij", fontsize=8)
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=0.2)

    # Set shared x limits with a small margin
    margin = (global_xmax - global_xmin) * 0.05 or 1e-6
    for ax in axes.flat:
        if ax.get_visible():
            ax.set_xlim(global_xmin - margin, global_xmax + margin)

    # Hide unused axes
    for idx in range(n_clusters, n_rows * n_cols):
        row, col = divmod(idx, n_cols)
        axes[row][col].set_visible(False)

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="D", color="w", markerfacecolor="#E41A1C",
               markersize=7, label="Synergistic (|mean| > 2 SEM)"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor="#377EB8",
               markersize=7, label="Destructive (|mean| > 2 SEM)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#999999",
               markersize=7, label="Not significant"),
    ]
    axes[0][0].legend(handles=legend_elements, loc="lower left", fontsize=7)

    fig.suptitle(f"Interaction forest by target cluster (k={k})", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    _save(fig, save_path, description=f"""\
Interaction forest plot by target neuron cluster (k={k}).

Target neurons are first clustered by their 21-dim pairwise interaction profile
(cosine distance, Ward linkage, cut into {k} clusters). Each panel then shows
the mean R_ij ± 2 SEM for each channel pair within that cluster.

Red diamonds: significant synergy (mean > 0, |mean| > 2 SEM).
Blue diamonds: significant opposition (mean < 0, |mean| > 2 SEM).
Grey circles: not significant.

Panel titles list the cluster ID, member count, and first few member types.
Panel color reflects the dominant target group in that cluster.

This reveals whether neurons with similar integration profiles show
consistent synergy/opposition patterns at specific channel pairs.

______________________________

Forest plot of pairwise channel interactions per target neuron cluster (k={k}). Targets were first clustered by their R_ij profiles (cosine distance, Ward linkage). Each panel shows the mean R_ij ± 2 SEM for all 21 channel pairs within one cluster. Red diamonds: significant synergy; blue diamonds: significant opposition; grey circles: non-significant. Panel colours reflect the dominant target group. Shared x-axis enables direct comparison of effect sizes across clusters.
""")
    return fig


def plot_signal_identity_interactions_clustered(
        interactions: pd.DataFrame,
        channel_order: List[str],
        target_colors: Dict[str, str],
        k: int = 10,
        save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Signal identity interaction plot faceted by cluster instead of target group.

    Two panels per cluster:
      - Top: 4x4 category interaction heatmap
      - Bottom: bar chart of category-pair R_ij with SEM error bars
    """
    df, cluster_info = _cluster_targets(interactions, k=k)
    if not cluster_info:
        return plt.figure()

    # Map channels to signal categories
    df["sig1"] = df["ch1"].map(SIGNAL_IDENTITY)
    df["sig2"] = df["ch2"].map(SIGNAL_IDENTITY)

    def cat_pair(s1, s2):
        idx1 = SIGNAL_CATEGORIES.index(s1) if s1 in SIGNAL_CATEGORIES else 99
        idx2 = SIGNAL_CATEGORIES.index(s2) if s2 in SIGNAL_CATEGORIES else 99
        if idx1 <= idx2:
            return f"{s1} × {s2}"
        return f"{s2} × {s1}"

    df["cat_pair"] = df.apply(lambda r: cat_pair(r["sig1"], r["sig2"]), axis=1)

    cat_pairs_ordered = []
    for i, c1 in enumerate(SIGNAL_CATEGORIES):
        for c2 in SIGNAL_CATEGORIES[i:]:
            cat_pairs_ordered.append(f"{c1} × {c2}")

    clusters = sorted(cluster_info.keys())
    n_clusters = len(clusters)

    # Assign cluster colours based on dominant target group
    from collections import Counter
    cluster_colors = {}
    for cl, info in cluster_info.items():
        group_counts = Counter(info["groups"])
        dominant = group_counts.most_common(1)[0][0]
        cluster_colors[cl] = target_colors.get(dominant, "#999999")

    # Layout: up to 5 cols
    n_cols = min(n_clusters, 5)
    n_rows_grid = (n_clusters + n_cols - 1) // n_cols

    fig, axes = plt.subplots(2 * n_rows_grid, n_cols,
                             figsize=(4.5 * n_cols, 10 * n_rows_grid),
                             squeeze=False)

    # First pass: compute all matrices and bar stats for global scales
    n_cat = len(SIGNAL_CATEGORIES)
    all_mats = []
    all_bar_stats = []

    for cl in clusters:
        sub = df[df["cluster"] == cl]

        mat = np.zeros((n_cat, n_cat))
        cat_stats = sub.groupby(["sig1", "sig2"])["R_ij"].mean()
        for (s1, s2), val in cat_stats.items():
            i = SIGNAL_CATEGORIES.index(s1) if s1 in SIGNAL_CATEGORIES else None
            j = SIGNAL_CATEGORIES.index(s2) if s2 in SIGNAL_CATEGORIES else None
            if i is not None and j is not None:
                mat[i, j] = val
                mat[j, i] = val
        all_mats.append(mat)

        bar_stats = (sub.groupby("cat_pair")["R_ij"]
                     .agg(["mean", "sem"])
                     .reindex(cat_pairs_ordered)
                     .dropna())
        all_bar_stats.append(bar_stats)

    # Global heatmap colour scale
    global_vmax = max(abs(m).max() for m in all_mats) or 1e-6

    # Global bar y-axis limits
    bar_ymin, bar_ymax = 0.0, 0.0
    for bs in all_bar_stats:
        if len(bs) > 0:
            lo = (bs["mean"] - 2 * bs["sem"]).min()
            hi = (bs["mean"] + 2 * bs["sem"]).max()
            bar_ymin = min(bar_ymin, lo)
            bar_ymax = max(bar_ymax, hi)
    bar_margin = (bar_ymax - bar_ymin) * 0.05 or 1e-6

    # Second pass: plot
    for idx, cl in enumerate(clusters):
        grid_row, col = divmod(idx, n_cols)
        ax_heat = axes[2 * grid_row][col]
        ax_bar = axes[2 * grid_row + 1][col]

        mat = all_mats[idx]
        bar_stats = all_bar_stats[idx]
        info = cluster_info[cl]

        # --- Heatmap ---
        im = ax_heat.imshow(mat, cmap="RdBu_r", vmin=-global_vmax, vmax=global_vmax,
                            aspect="equal")
        ax_heat.set_xticks(range(n_cat))
        ax_heat.set_yticks(range(n_cat))
        ax_heat.set_xticklabels(SIGNAL_CATEGORIES, rotation=45, ha="right", fontsize=9)
        ax_heat.set_yticklabels(SIGNAL_CATEGORIES, fontsize=9)

        for i in range(n_cat):
            for j in range(n_cat):
                ax_heat.text(j, i, f"{mat[i, j]:.2e}", ha="center", va="center", fontsize=7)

        fig.colorbar(im, ax=ax_heat, shrink=0.7)
        members_short = ", ".join(info["members"][:4])
        if info["n"] > 4:
            members_short += f", +{info['n'] - 4}"
        ax_heat.set_title(f"Cluster {cl} (n={info['n']})\n{members_short}",
                          fontsize=8, color=cluster_colors[cl])

        # --- Bar chart ---
        x = range(len(bar_stats))
        means = bar_stats["mean"].values
        sems = bar_stats["sem"].values

        bar_colors = []
        for cp in bar_stats.index:
            parts = cp.split(" × ")
            if parts[0] == parts[1]:
                bar_colors.append(SIGNAL_COLORS.get(parts[0], "#999999"))
            elif "female" in parts and "male" in parts:
                bar_colors.append("#FF7F00")
            else:
                bar_colors.append("#AAAAAA")

        ax_bar.bar(x, means, yerr=2 * sems, color=bar_colors,
                   edgecolor="white", linewidth=0.5, capsize=3,
                   error_kw={"linewidth": 1})
        ax_bar.set_xticks(x)
        ax_bar.set_xticklabels(bar_stats.index, rotation=60, ha="right", fontsize=7)
        ax_bar.axhline(0, color="black", linewidth=0.5)
        ax_bar.set_ylabel("mean R_ij", fontsize=8)
        ax_bar.set_ylim(bar_ymin - bar_margin, bar_ymax + bar_margin)

    # Hide unused axes
    for idx in range(n_clusters, n_rows_grid * n_cols):
        grid_row, col = divmod(idx, n_cols)
        axes[2 * grid_row][col].set_visible(False)
        axes[2 * grid_row + 1][col].set_visible(False)

    fig.suptitle(
        f"Signal identity interactions by cluster (k={k})\n"
        "(female=ppk25 | male=ppk23,DA1 | both=visual,auditory | neutral=VA1v,VA1d)",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    _save(fig, save_path, description=f"""\
Signal identity interaction plot by target neuron cluster (k={k}).

Target neurons are clustered by their pairwise interaction profile
(cosine distance, Ward linkage). Each cluster gets its own panel pair.

Channels are grouped by biological signal identity:
  - female: ppk25
  - male: ppk23, DA1
  - both: visual, auditory
  - neutral: VA1v, VA1d

Top: 4x4 heatmap of mean R_ij between signal categories within the cluster.
Bottom: bar chart of each category pair's mean R_ij (± 2 SEM).

This shows whether different clusters of target neurons have distinct
patterns of sex-signal integration — e.g. some clusters may show
female×male synergy while others show opposition.

______________________________

Signal identity interactions per target neuron cluster (k={k}). Channels are classified as female (ppk25), male (ppk23, DA1), both-sex (visual, auditory), or neutral (VA1v, VA1d). Targets are first clustered by R_ij profile. Each cluster pair shows a 4×4 category heatmap (shared colour scale; red = synergy, blue = opposition) and a bar chart of category-pair mean R_ij ± 2 SEM (shared y-axis). This reveals cluster-specific patterns of sex-signal integration.
""")
    return fig
