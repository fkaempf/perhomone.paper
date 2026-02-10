# Figure 6 (Bella's Targets): Multimodal Sensory Integration -- Panel Descriptions

**Targets:** Third-order neurons downstream of M cells, F cells, and IR-expressing cells (from Bella's figure)
**Sources:** 7 sensory modalities (DA1, VA1v, VA1d, auditory, visual, ppk23, ppk25)
**Method:** 50 strongest paths (Yen's algorithm) from each modality's sensory neurons to each target type

## Target Neuron Groups

| Group | Label | Color | Neuron Types |
|-------|-------|-------|-------------|
| M_downstream | M cells | Red (#E41A1C) | mAL_m1, mAL_m5a-c, mAL_m8, mAL_m3c, AVLP494m, SIP105m, AVLP711m, IN05B002, mAL_m6, SIP119m, VES206m, mAL_m5b |
| F_downstream | F cells | Blue (#377EB8) | mAL_m1, mAL_m2b, AVLP743m, AVLP597, P1_3c, IN05B002, IN23B006/7/9/56, IN11A020 |
| IR_downstream | IR cells | Green (#4DAF4A) | IN05B022, LH004m, AVLP743m, mAL_m1, LH007m, DNd02 |

Note: Some neurons (e.g., mAL_m1, IN05B002, AVLP743m) appear in multiple groups.

## How to Run

```r
# Step 1: Compute paths (first time only, ~10-30 min, results cached)
source("compute_paths.R")

# Step 2: Render all panels
source("render_all.R")
```

---

## Panel A: Circuit Schematic

**File:** `panel_A.Rmd`
**Plot type:** Programmatic ggplot diagram (boxes + arrows)

A wiring diagram showing 7 sensory modalities converging on Bella's three target groups. Two-column layout:

1. **Left (sensory inputs):** 7 colored boxes for each modality, grouped by sensory type (olfactory, auditory, visual, contact) with bracket annotations.
2. **Right (3rd-order targets):** 3 large colored boxes: "M cells downstream" (red), "F cells downstream" (blue), "IR cells downstream" (green), with representative neuron type names beneath each box.

Arrows connect all sensory inputs directly to all target groups (no relay intermediary column, since Bella's targets are defined differently from the vAB3/PPN1 relay structure).

**Difference from original:** Removed middle relay column (vAB3/PPN1); replaced aSP-f/aSP-g targets with 3 target groups; added representative neuron labels.

**Output:** `panel_A_circuit_schematic_bella.png/pdf`

---

## Panel B: Modality Composition Heatmap

**File:** `panel_B.Rmd`
**Plot type:** Clustered heatmap (pheatmap)

Same structure as original: rows = target neurons, columns = 7 modalities, color = column-normalized path strength (viridis scale).

- **Row annotation:** Target group membership (M_downstream = red, F_downstream = blue, IR_downstream = green) instead of aSP-f/aSP-g.
- **No extended version** (no vAB3/PPN1 data in this variant).
- Exports row order to `panel_B_row_order.rds`.

**Key question answered:** Do the three target groups (M, F, IR downstream) show distinct modality input profiles? Which neurons within each group are multimodal?

**Output:** `panel_B_heatmap_bella.png/pdf`

---

## Panel C: Excitatory/Inhibitory Valence Heatmap

**File:** `panel_C.Rmd`
**Plot type:** Paired heatmaps + diverging heatmap (pheatmap)

Same two approaches as original:
1. **Side-by-side:** Excitatory (white-to-red) and inhibitory (white-to-blue) heatmaps.
2. **Diverging:** Net valence (exc - inh) with blue-white-red scale.

Row annotations use Bella's 3 target groups. Loads Panel B row ordering for consistency.

**Difference from original:** Target group colors are M/F/IR instead of aSP-f/aSP-g.

**Output:** `panel_C_excitatory_bella.png/pdf`, `panel_C_inhibitory_bella.png/pdf`, `panel_C_diverging_valence_bella.png/pdf`

---

## Panel D: Shannon Entropy / Multimodality Score

**File:** `panel_D.Rmd`
**Plot type:** Bar charts, boxplots, scatter plots

Same entropy metrics as original (Shannon entropy, breadth, dominance, dominant modality).

**Difference from original:**
- Faceted by 3 groups (M cells, F cells, IR cells) instead of 2.
- Boxplot compares entropy across 3 groups with target_set_colors.
- Target set assignment from paths.bella target_set column.

**Key question answered:** Which of Bella's target neurons are the strongest multimodal integrators? Do M, F, and IR downstream neurons differ in their multimodality?

**Output:** `panel_D_entropy_bar_bella.png/pdf`, `panel_D_entropy_faceted_bella.png/pdf`, `panel_D_entropy_boxplot_bella.png/pdf`, `panel_D_breadth_vs_entropy_bella.png/pdf`, plus valence variants

---

## Panel E: Pairwise Modality Co-occurrence and Correlation

**File:** `panel_E.Rmd`
**Plot type:** Correlation heatmaps, network graphs (pheatmap, ggraph)

Same analyses as original: Pearson/Spearman correlation, co-targeting, Jaccard similarity, network visualization. All computed over Bella's target neuron set.

**Difference from original:** Different target neuron population may reveal different modality co-occurrence patterns.

**Key question answered:** Among Bella's targets, which modalities converge on the same neurons?

**Output:** `panel_E_pearson_heatmap_bella.png/pdf`, `panel_E_spearman_heatmap_bella.png/pdf`, `panel_E_cotarget_heatmap_bella.png/pdf`, `panel_E_cotarget_jaccard_bella.png/pdf`, `panel_E_correlation_network_bella.png/pdf`, plus valence variants

---

## Panel F: Path Diversity (Concentrated vs. Distributed Routes)

**File:** `panel_F.Rmd`
**Plot type:** Dot plots, cumulative curves, bar charts

Same paths_to_80pct analysis as original.

**Difference from original:** Added Section 8 splitting path diversity by target group (M/F/IR), producing a faceted bar chart showing whether path diversity patterns differ across Bella's three target groups.

**Output:** `panel_F_dot_paths_to_80pct_bella.png/pdf`, `panel_F_cumulative_curves_bella.png/pdf`, `panel_F_bar_paths_to_80pct_bella.png/pdf`, plus valence and target-group variants

---

## Panel G: Shared Intermediate Nodes (Hidden Hubs)

**File:** `panel_G.Rmd`
**Plot type:** Ranked dot plots, heatmaps, lollipop charts

Same intermediate node analysis as original.

**Difference from original:**
- Annotation pass also flags intermediates that are members of Bella's target groups (M_downstream, F_downstream, IR_downstream).
- Heatmap and lollipop chart color scales extended with target_set_colors.
- Hub table includes `is_bella_target` flag and `bella_group` column.

**Key question answered:** Which neurons serve as shared pathway hubs across modalities when targeting Bella's neurons? Are any of Bella's targets themselves hubs for other targets?

**Output:** `panel_G_ranked_intermediates_bella.png/pdf`, `panel_G_heatmap_intermediates_bella.png/pdf`, `panel_G_modality_count_distribution_bella.png/pdf`, `panel_G_effective_modalities_bella.png/pdf`, `panel_G_top15_hubs_bella.png/pdf`

---

## Panel H: Spotlight Examples (Radar Plots for Top Integrators)

**File:** `panel_H.Rmd`
**Plot type:** Radar/spider plots, stacked bar charts

Same structure as original but adapted for Bella's targets.

**Difference from original:**
- Known neuron search looks for Bella's types (mAL, AVLP494, P1_3, LH004, pC1, pC2) instead of AL-AST1, LH008, LH002.
- Each spotlight neuron's subtitle shows which target group(s) it belongs to.
- Annotation table includes "Target group(s)" column.

**Output:** `panel_H_bella_radar_individual.png/pdf`, `panel_H_bella_radar_valence.png/pdf`, `panel_H_bella_stacked_bar.png/pdf`, `panel_H_bella_stacked_bar_proportional.png/pdf`, `panel_H_bella_combined.png/pdf`

---

## Panel I: M vs. F vs. IR Downstream Comparison

**File:** `panel_I.Rmd`
**Plot type:** Grouped bars, faceted tornado, radar, heatmap, boxplot, scatter

**This is the most significantly changed panel.** Instead of a 2-way comparison (aSP-f vs aSP-g), this is a **3-way comparison** of modality input profiles across Bella's three target groups.

**Plots:**
1. **Grouped bar chart:** 7 modalities on x-axis, 3 bars per modality (M=red, F=blue, IR=green) with SE error bars.
2. **Faceted tornado chart:** Horizontal bars faceted by target group (adapted from butterfly chart since 3 groups can't go back-to-back).
3. **Radar overlay:** 3 semi-transparent polygons (M, F, IR) on a single polar plot.
4. **Heatmap:** 3 groups stacked vertically with gaps between, Ward.D2 clustering within each group.
5. **Entropy boxplot:** 3 groups with all 3 pairwise Wilcoxon test p-values annotated.
6. **Modality scatter:** 3 facets showing pairwise comparisons (M vs F, M vs IR, F vs IR) with identity lines.
7. **Valence-split versions:** Grouped bar, radar, entropy boxplot, and scatter all repeated for excitatory-only and inhibitory-only.

**Key question answered:** Do M, F, and IR downstream neurons receive different sensory modality mixes? Which modalities are enriched for each pathway?

**Output:** `panel_I_bella_paired_bar.png/pdf`, `panel_I_bella_tornado.png/pdf`, `panel_I_bella_radar_overlay.png/pdf`, `panel_I_bella_heatmap_grouped.png/pdf`, `panel_I_bella_entropy_boxplot.png/pdf`, `panel_I_bella_modality_scatter.png/pdf`, plus valence variants and composite
