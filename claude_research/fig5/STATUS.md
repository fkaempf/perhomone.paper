# Figure 5 — Status & Handoff

**Last updated:** 2026-04-13. Three commits this day: `2ca5139`, `7c4edd7`, `4d0169e`.

## Where things live

```
figures/fig5/
  setup.R                    ← single source of truth for paths + data
  setup_mspecific.R          ← inherits setup.R, restricts to male-specific mAL_m* subset
  render_all.R               ← knits A–L → html/; copies curated PDFs → selection/
  render_mspecific.R         ← renders A–G, I–L (skips H) → plots_mspecific/
  panel_A.Rmd ... panel_L.Rmd  (12 panels, all complete, no TODOs)
  plots/                     ← per-panel png + pdf + narrative.txt
  plots_mspecific/           ← same, male-specific variant
  selection/                 ← curated "best" PDFs per panel
  html/                      ← rendered notebooks (12/12)
  panel_A_row_order.rds      ← saved by panel_A for downstream consumption (unused today)
  fig5_dynamic_decision_design.txt   ← design doc #1 (dynamic decision story)
  fig5_gain_landscape_design.txt     ← design doc #2 (gain-landscape story)
```

All paths inside Rmds source via absolute `source(".../figures/fig5/setup.R")`. No `here::here`, no relative paths, no YAML `output_dir`. `setup.R` defines `project_root`, `fig5_dir`, `feather_dir`, `paths_dir`, `sf_plots_dir` — everything downstream composes from those.

## Panel inventory (all complete, all rendered to HTML)

| # | Panel | Topic |
|---|---|---|
| A | mAL input profiles | Clustered heatmap across 7 sensory channels |
| B | AN09B017 relay selectivity | Bipartite scatter, ppk23/25 → mAL via ascending variants |
| C | ppk23 sign reversal | Paired bars + scatter showing AN05B035 GABAergic flip |
| D | mAL→P1 output specificity | Biclustered heatmap + drive bars |
| E | ppk23/25 E/I decomposition | Stacked bars + E/I balance scatter |
| F | Scenario responses | Parallel coords + heatmap for 3 encounter scenarios |
| G | mAL↔mAL lateral inhibition | Signed heatmap + hub bars |
| H | Sexual dimorphism of ppk→mAL→P1 | Boxplots + Wilcoxon |
| I | Path-based vs signal-flow agreement | Per-scenario Spearman + sign-agreement |
| J | ppk23 response group vs P1 connectivity | Heatmap + Wilcoxon + scenario bars |
| K | AN09B017 subtype targeting on mAL | Heatmap + output entropy |
| L | mAL ppk23 vs ppk25 selectivity | Path- and signal-flow scatters |

## Narrative (per the two design docs)

**Dynamic Decision Design:** sequential sensory input gates P1 courtship decisions through transient mAL GABAergic inhibition — the moment-to-moment story.

**Gain Landscape Design:** mAL is the evolutionarily favored tuning knob for selectivity — the cross-species story.

Together: which subtypes do what (A–G), how dimorphism and models cross-check (H–I), and how the circuit's output wiring maps back to pheromone channel (J–L).

## What's reliably working

- `Rscript render_all.R` from `figures/fig5/` rebuilds all 12 HTMLs and the 12 curated PDFs in `selection/`.
- `Rscript render_mspecific.R` rebuilds the 11 male-specific variants.
- Canary verified this session — panel A end-to-end, then full render_all — both clean.

## What's open

**No analytical TODOs in the Rmds themselves** — all panels execute, all narratives are written.

Likely next work (in rough priority order):

1. **Figure layout in `figures/fig5/fig5.afpub`.** No Affinity Publisher file exists yet (unlike fig6). Someone needs to pull the right `selection/*.pdf` outputs into a multi-panel layout. This is the biggest missing piece.

2. **Panel ordering / story structure.** Currently 12 panels labeled A–L by creation order. A real figure probably wants fewer, in story order:
   - Intro pair: input profiles (A) + outcome (L or D?)
   - Mechanism pair: ppk23 sign flip (B→C)
   - Decomposition (E) + lateral (G)
   - Dimorphism validation (H)
   - Model cross-check (I)
   - Output (J, D)
   The two design docs have explicit panel-order proposals — compare what's in the docs vs what rendered, cut/merge/promote.

3. **Narrative tightening.** Each Rmd has a block-level narrative. Once the panel set is final, harvest those into a single figure-level caption + legend. `my_selection_that_makes_halfway_sense/figure_5_narrative.txt` is a draft attempt.

4. **Statistical reporting.** Panel H has Wilcoxon tests, Panel I has Spearman. Check that effect sizes + n + exact p (not just stars) are in every caption that reports a test.

5. **Male-specific variant decision.** `plots_mspecific/` exists in parallel. Is it a supplementary figure? A replacement for fig5 in some contexts? A dead-end exploration? Decide before final figure assembly.

6. **Panel A row_order.rds is written but never read.** Either downstream panels should inherit the clustering order (so rows align across heatmaps), or the save can be deleted.

## Useful commands

```bash
cd figures/fig5
Rscript -e 'source("setup.R")'               # sanity check: loads data, no render
Rscript -e 'rmarkdown::render("panel_X.Rmd", output_dir="html")'   # single-panel render
Rscript render_all.R                         # full rebuild (~5–15 min)
Rscript render_mspecific.R                   # male-specific variant
```

## Gotchas for next instance

- **fig5/ was never git-tracked before this session's commits.** Binary artifacts (`*.rds`, `*.pdf`, `*.png`, `*.html`, `*.feather`) are gitignored repo-wide — don't try to commit regenerated plots, they'll be silently rejected.
- **`feather/strongest.paths/`** (trailing `s`) is the cache dir, lives at `project_root/feather/`. NOT to be confused with `analyses/strongest_path/` (no `s`) which is a separate analysis workspace.
- **Paths are absolute.** Do not convert to `here::here()` — `render_mspecific.R` knits from a temp dir and would break relative sources.
- **project_root is hardcoded** to `/Users/fkampf/Documents/pheromone.paper` in every setup.R. Works for this machine; anyone cloning will need to patch.

## Reference docs

- `claude_research/fig5/reorg_plan.md` — the directory reorg plan executed this session
- `claude_research/root_cleanup_plan.md` — repo-root cleanup executed this session
- `figures/fig5/fig5_dynamic_decision_design.txt` — story design #1
- `figures/fig5/fig5_gain_landscape_design.txt` — story design #2
