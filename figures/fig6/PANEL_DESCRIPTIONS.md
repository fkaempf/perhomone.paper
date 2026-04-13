# Figure 6: Multimodal Sensory Integration -- Panel Descriptions

**Targets:** aSP-f and aSP-g neuron subtypes (3rd-order courtship command neurons)
**Sources:** 7 sensory modalities (DA1, VA1v, VA1d, auditory, visual, ppk23, ppk25)
**Method:** 50 strongest paths (Yen's algorithm) from each modality's sensory neurons to each target type

---

## Panel A: Circuit Schematic

**File:** `panel_A.Rmd`
**Plot type:** Programmatic ggplot diagram (boxes + arrows)

A wiring diagram showing the logic of the analysis. Three columns represent circuit layers:

1. **Left (sensory inputs):** 7 colored boxes for each modality (DA1, VA1v, VA1d, JO-B, LC10, ppk23, ppk25), grouped by sensory type (olfactory, auditory, visual, contact) with bracket annotations.
2. **Middle (2nd-order relay neurons):** vAB3 and PPN1 boxes (grey).
3. **Right (3rd-order targets):** aSP-f and aSP-g boxes (grey).

Arrows connect all sensory nodes to all relay nodes, and all relay nodes to all targets, illustrating the convergence/divergence topology. This panel sets up the conceptual framework for the quantitative panels that follow.

**Output:** `panel_A_circuit_schematic.png/pdf`

---

## Panel B: Modality Composition Heatmap

**File:** `panel_B.Rmd`
**Plot type:** Clustered heatmap (pheatmap)

Shows how strongly each sensory modality's paths reach each target neuron.

- **Rows:** Target neuron types (aSP-f and aSP-g subtypes). Hierarchically clustered (Ward.D2, euclidean distance) to group neurons with similar modality input profiles.
- **Columns:** 7 sensory modalities in fixed order.
- **Cell color:** Total path strength (sum of 50 strongest paths), column-normalized so each modality's maximum = 1. This normalization makes cross-modality comparison fair despite differing absolute strengths.
- **Row annotation:** Colored sidebar indicating target set membership (aSP-f = red, aSP-g = blue).
- **Column annotation:** Colored sidebar grouping modalities (olfactory, auditory, visual, contact).
- **Color scale:** Viridis (dark = low, yellow = high).

**Key question answered:** Which target neurons receive broad multimodal input vs. unimodal input? Do aSP-f and aSP-g subtypes cluster separately by their modality profiles?

Also includes an **extended version** adding vAB3 and PPN1 downstream targets for a broader view.

Exports the row dendrogram order to `panel_B_row_order.rds` for Panel C consistency.

**Output:** `panel_B_heatmap_aspf_aspg.png/pdf`, `panel_B_heatmap_all_targets.png/pdf`

### Panel B variant: vAB3 & PPN1 downstream targets

**File:** `panel_B_vab3_ppn1.Rmd`

Standalone heatmap focusing on the downstream targets of vAB3 and PPN1 (the neurons they project onto). These targets were defined in `strongest.path.closer.evaluation.Rmd` as the top 10 downstream partners of each ascending neuron (plus 3 shared partners). The 1000 paths per modality are filtered to top 50 per (end, modality) pair to match the aspf/aspg analysis scale.

- **Row annotation:** vAB3 (green) vs PPN1 (orange) target set.
- Same column-normalization and clustering as main Panel B.

**Output:** `panel_B_heatmap_vab3_ppn1_top50.png/pdf`

---

## Panel C: Excitatory/Inhibitory Valence Heatmap

**File:** `panel_C.Rmd`
**Plot type:** Paired heatmaps + diverging heatmap (pheatmap)

Separates path strength by valence (excitatory vs. inhibitory) to reveal whether modalities provide excitatory drive, inhibitory suppression, or mixed input to each target.

**Approach 1 (side-by-side):**
- Two separate heatmaps: excitatory (white-to-red scale) and inhibitory (white-to-blue scale).
- Both column-normalized independently.
- Same row/column annotations as Panel B.
- Uses Panel B's row ordering if available, otherwise clusters independently.

**Approach 2 (diverging):**
- Single heatmap of net valence (excitatory - inhibitory).
- Symmetrically scaled to [-1, 1] using a blue-white-red diverging palette.
- Red = excitatory dominant, blue = inhibitory dominant, white = balanced.

**Summary statistics:** Reports per-modality and per-neuron excitatory/inhibitory balance.

**Key question answered:** Are some modalities predominantly excitatory or inhibitory? Do specific neurons receive opposing valence from different modalities?

**Output:** `panel_C_excitatory.png/pdf`, `panel_C_inhibitory.png/pdf`, `panel_C_diverging_valence.png/pdf`

---

## Panel D: Shannon Entropy / Multimodality Score

**File:** `panel_D.Rmd`
**Plot type:** Bar charts, boxplots, scatter plots

Quantifies how multimodal each target neuron is using information-theoretic measures.

**Metrics per neuron:**
- **Shannon entropy** H = -sum(p_i * log2(p_i)) over modality strength proportions. Maximum = log2(7) ~ 2.807 bits for perfectly uniform input from all 7 modalities. Minimum = 0 for purely unimodal input.
- **Breadth:** Number of modalities with non-zero path strength.
- **Dominance:** Fraction of total strength from the single strongest modality (1 = unimodal, 1/7 = perfectly uniform).
- **Dominant modality:** Which modality contributes most.

**Plots:**
1. Ranked bar chart: neurons on x-axis sorted by descending entropy, bars colored by dominant modality.
2. Faceted version: same but split by target set (aSP-f vs aSP-g).
3. Boxplot: entropy distribution comparison between aSP-f and aSP-g.
4. Scatter: breadth vs. entropy with labeled top-15 neurons.
5. Valence-split: separate entropy for excitatory-only and inhibitory-only paths.
6. Dominance vs. entropy scatter.

**Key question answered:** Which neurons are the strongest multimodal integrators? Is multimodality a property of specific neuron types or broadly distributed?

**Output:** `panel_D_entropy_bar.png/pdf`, `panel_D_entropy_faceted.png/pdf`, `panel_D_entropy_boxplot.png/pdf`, `panel_D_breadth_vs_entropy.png/pdf`, plus valence variants

---

## Panel E: Pairwise Modality Co-occurrence and Correlation

**File:** `panel_E.Rmd`
**Plot type:** Correlation heatmaps, network graphs (pheatmap, ggraph)

Examines which modalities tend to converge on the same target neurons.

**Analyses:**
1. **Pearson correlation matrix** (7x7): How correlated are modality strength profiles across all target neurons? High correlation = two modalities tend to reach the same neurons with similar relative strengths.
2. **Spearman correlation matrix:** Rank-based version, robust to outliers.
3. **Co-targeting heatmap:** Binary threshold (5% of modality max), counts how many target neurons are reached by each pair of modalities.
4. **Jaccard similarity:** Normalized co-targeting that accounts for marginal frequencies.
5. **Correlation network:** Modalities as nodes in a circular graph layout, edges colored by positive (red) / negative (blue) correlation, width proportional to |r|.
6. **Thresholded network:** Same but only showing |r| > 0.1 with labeled edges.
7. **Valence-split versions:** All above repeated for excitatory-only and inhibitory-only paths.

**Key question answered:** Do modalities travel together to the same targets, or are pathways independent? Which modality pairs are most/least correlated?

**Output:** `panel_E_pearson_heatmap.png/pdf`, `panel_E_spearman_heatmap.png/pdf`, `panel_E_cotarget_heatmap.png/pdf`, `panel_E_cotarget_jaccard.png/pdf`, `panel_E_correlation_network.png/pdf`, plus valence variants

---

## Panel F: Path Diversity (Concentrated vs. Distributed Routes)

**File:** `panel_F.Rmd`
**Plot type:** Dot plots, cumulative curves, bar charts

Measures whether modality input arrives through a few dominant paths or many distributed routes.

**Key metric: paths_to_80pct** -- the minimum number of paths needed to capture 80% of total strength for each target-modality pair. Low = concentrated (a few strong paths dominate). High = distributed (many paths contribute).

**Plots:**
1. Dot plot: individual target neurons as jittered points, diamond-shaped median per modality.
2. Cumulative strength curves: for selected high-breadth targets, shows how quickly cumulative strength rises as paths are added (steep = concentrated).
3. Summary bar chart: mean paths_to_80pct per modality with SE error bars.
4. Valence-split: grouped bar chart and faceted dot plot comparing excitatory vs. inhibitory path diversity.

**Key question answered:** Are some modalities "funneled" through a few critical paths while others take diverse routes? Does this differ between excitatory and inhibitory pathways?

**Output:** `panel_F_dot_paths_to_80pct.png/pdf`, `panel_F_cumulative_curves.png/pdf`, `panel_F_bar_paths_to_80pct.png/pdf`, plus valence variants

---

## Panel G: Shared Intermediate Nodes (Hidden Hubs)

**File:** `panel_G.Rmd`
**Plot type:** Ranked dot plots, heatmaps, lollipop charts

Identifies neurons that appear as intermediates in paths from multiple modalities -- potential sites of multimodal integration that aren't the start or end of paths.

**Method:**
1. Parse each path string ("A -> B -> C -> D"), extract intermediate nodes (B, C).
2. Exclude sensory neurons (ORN_DA1, JO-B, LC10, ppk types).
3. For each intermediate: count distinct modalities, sum path strength, look up neurotransmitter.
4. Annotate known courtship circuit types (mAL, P1, pC1, pC2, vAB3, PPN1, etc.).

**Plots:**
1. Ranked dot plot: top 40 intermediates by modality count, color = log10(total strength), shape = known courtship neuron.
2. Heatmap: top 30 intermediates (rows) x 7 modalities (columns), log10 strength, row annotation by neuron class.
3. Modality count histogram: how many intermediates are hit by 1, 2, ... 7 modalities.
4. Effective modality count: 2^(Shannon entropy) as a continuous measure vs. discrete count.
5. Top 15 lollipop chart: publication-ready, labeled, sized by total strength, colored by neuron class.

**Key question answered:** Where are the "hidden hubs" of multimodal integration? Are they known courtship neurons or novel candidates?

**Output:** `panel_G_ranked_intermediates.png/pdf`, `panel_G_heatmap_intermediates.png/pdf`, `panel_G_modality_count_distribution.png/pdf`, `panel_G_effective_modalities.png/pdf`, `panel_G_top15_hubs.png/pdf`

---

## Panel H: Spotlight Examples (Radar Plots for Top Integrators)

**File:** `panel_H.Rmd`
**Plot type:** Radar/spider plots, stacked bar charts

Detailed per-neuron profiles for the top multimodal integrators, combining data-driven selection with literature-validated candidates.

**Neuron selection:**
1. Compute entropy for all target neurons.
2. Select top 4 by entropy (requiring input from 3+ modalities).
3. Also search for known types (AL-AST1, LH008, LH002, aSP-f/aSP-g subtypes).
4. Look up synonyms from mba.

**Plots per spotlight neuron:**
1. Individual radar: normalized strength across 7 modality axes, modality-colored points, entropy annotation, synonym subtitle.
2. Valence radar: excitatory (solid blue polygon) and inhibitory (dashed red polygon) overlaid.
3. Stacked bar: absolute strength breakdown by modality and valence.
4. Proportional stacked bar: normalized to 100%.

**Combined panel:** Three-row layout (total radars, valence radars, stacked bars).

**Key question answered:** What do the modality input profiles of the top integrators look like in detail? Is input balanced or skewed?

**Output:** `panel_H_radar_individual.png/pdf`, `panel_H_radar_valence.png/pdf`, `panel_H_stacked_bar.png/pdf`, `panel_H_stacked_bar_proportional.png/pdf`, `panel_H_combined.png/pdf`

---

## Panel I: aSP-f vs. aSP-g Modality Profile Comparison

**File:** `panel_I.Rmd`
**Plot type:** Grouped bars, tornado chart, radar, heatmap, boxplot, scatter

Direct comparison of modality input profiles between the two major target neuron classes.

**Plots:**
1. Grouped bar chart: 7 modalities on x-axis, paired bars (aSP-f blue, aSP-g red) with SE error bars.
2. Butterfly/tornado chart: back-to-back horizontal bars (aSP-f right, aSP-g left).
3. Radar overlay: two semi-transparent polygons on a single polar plot.
4. Heatmap: both groups stacked vertically with gap, Ward.D2 clustering within each group.
5. Entropy boxplot: with Wilcoxon rank-sum test p-value.
6. Modality scatter: each modality as a labeled point (x = aSP-f mean, y = aSP-g mean), identity line shows enrichment direction.
7. Valence-split versions of all above.

**Key question answered:** Do aSP-f and aSP-g receive different modality mixes? Which modalities are enriched in one vs. the other? Does this differ for excitatory vs. inhibitory input?

**Output:** `panel_I_paired_bar.png/pdf`, `panel_I_butterfly.png/pdf`, `panel_I_radar_overlay.png/pdf`, `panel_I_heatmap_grouped.png/pdf`, `panel_I_entropy_boxplot.png/pdf`, `panel_I_modality_scatter.png/pdf`, plus valence variants
