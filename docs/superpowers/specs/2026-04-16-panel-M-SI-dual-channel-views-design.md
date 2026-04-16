# Panel M — SI-centric dual-channel views

Two new Panel M figures that take the GABA sign-inverter (SI) pool as the
unit of analysis instead of mAL_m subtypes.

## Context

The SI pool is defined in `figures/fig5/setup_mspecific.R` as
`gaba_sign_inverter_types` — 11 types: `AN05B021`, `AN05B023a`-`d`,
`AN05B025`, `AN05B035`, `AN05B050_a`, `IN05B002`, `IN05B011a`,
`IN05B011b`. Existing Panel M figures quantify ppk23/ppk25 drive onto
the 16 mAL_m subtypes (`mal_paths` cache, endpoint = mAL_m). These two
new figures flip the question:

1. **Plot 1** — how much ppk23 vs ppk25 input each SI receives (SI as
   the path endpoint, not a relay).
2. **Plot 2** — which mAL_m subtypes receive the most SI drive, and
   which SI carries it (mAL_m as endpoint, but strength recalculated
   from the SI downwards rather than from the ORN).

Both plug into the existing panel_M palette and plots_mspecific output
tree.

## Data — two new strongest-path caches

Use `find_k_strongest_paths_yen` (same function that produces
`mal_paths`), same `n_paths = 50`, writing into
`feather/strongest.paths/`:

| Cache                                                      | starts                           | targets                   |
| ---------------------------------------------------------- | -------------------------------- | ------------------------- |
| `strongest.50.paths.ppk23.2.gaba_si_pool.feather`          | `channel_neurons[["ppk23"]]`     | `gaba_sign_inverter_types`|
| `strongest.50.paths.ppk25.2.gaba_si_pool.feather`          | `channel_neurons[["ppk25"]]`     | `gaba_sign_inverter_types`|
| `strongest.50.paths.gaba_si_pool.2.mAL_all.feather`        | `gaba_sign_inverter_types`       | `mal_subtypes` (mAL_m)    |

The first two feed Plot 1. The third feeds Plot 2. Loader logic mirrors
`load_mal_modality_paths` / `compute_and_cache_mal_paths` in
`figures/fig5/setup.R` — reuse the same helpers, passing the new
`target_name` string (`"gaba_si_pool"`) and source set.

Each cache is a tidy data frame with at least: `start`, `end`, `path`,
`strength`, `valence` (and `modality` for the ppk23/25 caches).

## Plot 1 — SI pool: ppk23 vs ppk25 input scatter

**File**: `figures/fig5/panel_M/rmd/panel_M_si_channel_scatter.Rmd`
**Output**: `figures/fig5/plots_mspecific/panel_M/{pdf,png}/panel_M_si_channel_scatter.{pdf,png}`

**Per-SI aggregation**
```
df_si <- bind_rows(
  ppk23 = sum(strength) by end   # from ppk23-to-SI cache
  ppk25 = sum(strength) by end   # from ppk25-to-SI cache
) %>% pivot_wider(names_from = modality, values_from = strength)
```
One row per SI pool member (n = 11).

**Plot**
- `ggplot(df_si, aes(x = ppk23, y = ppk25))`
- `geom_abline(slope = 1, intercept = 0, linetype = "dashed", color = "grey60")` (y = x reference)
- `geom_point(size = 3.6, color = panel_M_palette["gaba_si"])`
- `ggrepel::geom_text_repel(aes(label = end), ...)` — same repel settings as `panel_M_dual_channel_correlation.Rmd`
- `scale_x_log10()`, `scale_y_log10()` — AN05B035 dominates on a linear axis
- Equal-range expansion so the diagonal is visually 45°
- `theme_pub(base_size = 14)`; title/subtitle handled by panel
  conventions in `setup_mspecific.R`

**Stats annotation (NPC corner, same pattern as existing Panel M)**
- Pearson r + p and Spearman rho + p, computed on `log10(ppk23)` vs
  `log10(ppk25)` (matches the log-log visual).
- OLS slope with 95 % CI from `lm(log10(ppk25) ~ log10(ppk23))`.
- n = 11, and counts of SIs above vs below the diagonal as a quick
  "channel bias" summary: `sum(ppk25 > ppk23)` / `sum(ppk25 < ppk23)`.
- SIs with `strength == 0` on either channel are offset by a small
  pseudocount (`0.5 * min_positive_strength`) before log-transform so
  they appear on-axis rather than being silently dropped.

**Reading**: points on the diagonal = channel-symmetric SIs; points
off-diagonal = channel-biased SIs. Expected: AN05B035 sits top-right
(high on both); a few SIs likely lean ppk23-only vs ppk25-only —
that's the biological signal.

## Plot 2 — mAL_m ordered by SI input, stacked by SI, recalculated from SI

**File**: `figures/fig5/panel_M/rmd/panel_M_mal_by_si_input.Rmd`
**Output**: `figures/fig5/plots_mspecific/panel_M/{pdf,png}/panel_M_mal_by_si_input.{pdf,png}`

**Per-(mAL_m, SI) aggregation — "recalculated from SI"**

Use the `strongest.50.paths.gaba_si_pool.2.mAL_all.feather` cache
(paths whose *start* is an SI, *end* is an mAL_m). This is the
re-calculation: strength is the multiplicative path weight *starting
from the SI*, not from an ORN, so the ORN→SI prefix is excluded by
construction.

```
df_bar <- si_to_mal_paths %>%
  filter(end %in% mal_subtypes) %>%
  group_by(end, start) %>%              # end = mAL_m, start = SI
  summarise(strength = sum(strength), .groups = "drop") %>%
  rename(mal = end, si = start)
```

**Ordering**: mAL_m ordered descending by `sum(strength)` across all
SIs.

**Plot (stacked bar, B3)**
- `ggplot(df_bar, aes(x = reorder(mal, -total), y = strength, fill = si))`
- `geom_col(position = "stack")`
- Fill palette: 11-color categorical palette for SI identities, built
  as `viridis::turbo(11, begin = 0.05, end = 0.95)`, ordered by
  mean per-SI contribution across mAL_m (largest first). Then
  overwrite the AN05B035 slot with `panel_M_palette["gaba_si"]` so it
  reads continuous with other Panel M figures. Cache the resulting
  named vector so both the bar fill and the legend pick it up.
- `theme_pub(base_size = 14)`, x-axis labels rotated 30° (already in
  `theme_pub`), y-axis label "SI→mAL_m path strength (recalculated
  from SI)"
- Legend on the right, ordered by SI contribution to the top-ranked
  mAL_m so the dominant SI sits at the top of the legend.

**Companion readout (small, below the bar)**: a 2-row annotation
strip showing, per mAL_m, which channel-marker (ppk23-biased /
ppk25-biased / symmetric) each dominant SI carries, using Plot 1's
classification. This keeps Plot 2 tied back to Plot 1. Optional — can
defer if it clutters.

## Narrative / captions

Write `panel_M_si_channel_scatter_narrative.txt` and
`panel_M_mal_by_si_input_narrative.txt` into
`plots_mspecific/panel_M/data/` following the same structure as
existing Panel M narratives (DESIGN / STATISTICS / INTERPRETATION
sections, plus `panel_M_pool_caption`).

## Testing / verification

Both Rmds must:
- Source `figures/fig5/setup_mspecific.R`.
- Re-render cleanly via the existing `render_all.R` pattern (or stand
  alone).
- Produce a PDF that is non-empty (file size > 5 KB) and reflects the
  11-SI pool size (Plot 1) / 16-mAL_m rows (Plot 2).
- Assert: the three new feather caches exist after first run, and
  `nrow > 0`.

No mocks; integration-style rendering against real cached graph data.

## Out of scope

- Normalising by the number of ORN starts per channel (ppk23 and ppk25
  have different ORN counts). If channel imbalance becomes an
  interpretation blocker, add a second Plot-1 variant divided by
  `length(channel_neurons[[mod]])` — but default is raw sum, matching
  `mal_paths`-era panels.
- Significance testing on Plot 2 bar ordering; it's a ranking, not a
  statistical claim.
- Channel-split version of Plot 2 (ppk23 vs ppk25). Could be a follow-up
  if the panel needs it; current spec keeps Plot 2 channel-agnostic
  because "recalculated from SI" drops the ORN prefix anyway.
