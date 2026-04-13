# fig5 Directory Reorganization Plan

**Goal.** Move `fig5/` (and eventually siblings) under a single top-level `figures/` parent so the repo root stops growing one folder per figure. Target layout (A):

```
pheromone.paper/
  figures/
    fig5/        (current fig5/, unchanged internal structure)
    fig6/        (current fig6/)
    fig6_bella_targets/
  feather/
  R/
  combinatorial_signal_flow/
  ...
```

**Why target A (not per-panel B).** Target A requires ~17 path edits and preserves the `plots/`, `plots_mspecific/`, `selection/` sub-tree that `render_all.R`, `render_mspecific.R`, and the helper functions (`panel_plot_dir`, `save_panel_narrative`) depend on. Target B would require restructuring those helpers too (~25–30 edits) with no payoff beyond aesthetics. If B is later desired, it can be layered on top.

**Scope.** This plan covers `fig5/` only. Moving `fig6/` and `fig6_bella_targets/` follows the identical template — append a copy of phases 2–5 for each.

---

## Phase 0 — Audit recap (already complete)

Five parallel Explore agents already inventoried every filesystem reference in `fig5/`. Results:

- **All paths are absolute or built via `file.path()` from `project_root`/`fig5_dir` in `setup.R`.** No `../`, no `here::here()`, no `setwd()`, no YAML `output_dir`, no `knitr::opts_chunk$set(fig.path=...)`.
- **Single source of truth:** `fig5/setup.R` lines 9–10 define `project_root` and `fig5_dir`. Everything downstream constructs paths from those.
- **External reads (stay put):** `feather/strongest.paths/*.feather`, `R/{utils,data_processing,path_analysis,visualization,neuroglancer}.R`, `combinatorial_signal_flow/plots/sigmoid_rectified/{screen_results,pairwise_interactions}.csv`. All reached via `project_root`, outside fig5.
- **No cross-panel file dependencies.** `panel_A.Rmd:137` writes `panel_A_row_order.rds` to `fig5_dir/` root; no other panel reads it.

**Exact references to update (17 total):**

| # | File | Line | Current |
|---|------|------|---------|
| 1 | `fig5/setup.R` | 9 | `project_root <- "/Users/fkampf/Documents/pheromone.paper"` (unchanged — correct) |
| 2 | `fig5/setup.R` | 10 | `fig5_dir <- file.path(project_root, "fig5")` → `file.path(project_root, "figures", "fig5")` |
| 3 | `fig5/setup_mspecific.R` | 5 | `source("/Users/.../fig5/setup.R")` → `.../figures/fig5/setup.R` |
| 4 | `fig5/render_all.R` | 9 | `fig5_dir <- "/Users/.../fig5"` → `.../figures/fig5` |
| 5 | `fig5/render_mspecific.R` | 11 | same |
| 6 | `fig5/render_mspecific.R` | 23 | regex that substitutes source() — already uses `fig5_dir` variable, no change needed once line 11 is fixed |
| 7–18 | `fig5/panel_{A..L}.Rmd` | 8 | `source("/Users/.../fig5/setup.R")` → `.../figures/fig5/setup.R` (12 panels) |

Full audit tables are in the session transcript (2026-04-13).

---

## Phase 1 — Create `figures/` and move `fig5/`

**Goal.** Physically relocate the directory. Do this with `git mv` to preserve history.

**Commands:**

```bash
cd /Users/fkampf/Documents/pheromone.paper
mkdir figures
git mv fig5 figures/fig5
```

**Verification:**

```bash
ls figures/fig5/setup.R        # must exist
git status | head              # should show renames, not add+delete
```

**Anti-pattern guard.** Do NOT use plain `mv` — that loses rename tracking. Do NOT delete and recreate.

**Do not yet touch** `fig6/` or `fig6_bella_targets/` — this plan only covers `fig5`. A follow-up plan with the same steps handles those.

---

## Phase 2 — Update `setup.R` and `setup_mspecific.R`

**Goal.** Re-anchor `fig5_dir` to the new location.

**Edit 1 — `figures/fig5/setup.R` line 10:**

```r
# before
fig5_dir <- file.path(project_root, "fig5")
# after
fig5_dir <- file.path(project_root, "figures", "fig5")
```

`project_root` on line 9 stays `/Users/fkampf/Documents/pheromone.paper` — it is the repo root, which did not move.

**Edit 2 — `figures/fig5/setup_mspecific.R` line 5:**

```r
# before
source("/Users/fkampf/Documents/pheromone.paper/fig5/setup.R")
# after
source("/Users/fkampf/Documents/pheromone.paper/figures/fig5/setup.R")
```

**Verification:**

```bash
cd /Users/fkampf/Documents/pheromone.paper
Rscript -e 'source("figures/fig5/setup.R"); cat("fig5_dir =", fig5_dir, "\n")'
# expect: fig5_dir = /Users/fkampf/Documents/pheromone.paper/figures/fig5
```

**Anti-pattern guard.** Do NOT switch to `here::here()` — the codebase does not use it elsewhere and introducing one pattern here would be inconsistent. Do NOT move `project_root` — it's already correct.

---

## Phase 3 — Update `render_all.R` and `render_mspecific.R`

**Goal.** Point the renderers at the new fig5 location.

**Edit 1 — `figures/fig5/render_all.R` line 9:**

```r
fig5_dir <- "/Users/fkampf/Documents/pheromone.paper/figures/fig5"
```

**Edit 2 — `figures/fig5/render_mspecific.R` line 11:** same replacement.

Line 23's `sprintf('source("%s/setup_mspecific.R")', fig5_dir)` will absorb the new value automatically — no edit.

**Verification:** dry-run the render script, skipping the actual knit, to confirm it finds the panel Rmds:

```bash
cd /Users/fkampf/Documents/pheromone.paper/figures/fig5
Rscript -e '
  fig5_dir <- "/Users/fkampf/Documents/pheromone.paper/figures/fig5"
  panels <- c("panel_A.Rmd","panel_B.Rmd","panel_C.Rmd","panel_D.Rmd",
              "panel_E.Rmd","panel_F.Rmd","panel_G.Rmd","panel_H.Rmd",
              "panel_I.Rmd","panel_J.Rmd","panel_K.Rmd","panel_L.Rmd")
  for (p in panels) stopifnot(file.exists(file.path(fig5_dir, p)))
  cat("all 12 panels found\n")
'
```

---

## Phase 4 — Update `source()` in all 12 panel Rmds

**Goal.** Fix the hardcoded `source(".../fig5/setup.R")` on line 8 of every panel.

**Mechanical edit.** Same change in every panel file:

```r
# before (line 8)
source("/Users/fkampf/Documents/pheromone.paper/fig5/setup.R")
# after
source("/Users/fkampf/Documents/pheromone.paper/figures/fig5/setup.R")
```

Apply to all 12: `panel_A.Rmd` through `panel_L.Rmd` under `figures/fig5/`.

**Recommended method.** One sed invocation, reviewed before running:

```bash
cd /Users/fkampf/Documents/pheromone.paper/figures/fig5
# dry-run preview
grep -n 'source.*pheromone.paper/fig5/setup.R' panel_*.Rmd
# apply
sed -i '' 's|pheromone.paper/fig5/setup.R|pheromone.paper/figures/fig5/setup.R|g' panel_*.Rmd
# confirm
grep -n 'source.*setup.R' panel_*.Rmd
```

**Verification:** every panel's line 8 should now reference `figures/fig5/setup.R`, and `grep -rn "pheromone.paper/fig5/" figures/fig5/` should return zero hits (old path fully gone).

**Anti-pattern guard.** Do NOT replace with a relative `source("setup.R")`. The panels are often knit with `rmarkdown::render` which sets knit_root_dir — a relative path would silently break under render_mspecific.R (which knits from a temp dir).

---

## Phase 5 — Canary render (one panel end-to-end)

**Goal.** Prove the pipeline still works before re-rendering everything.

Pick Panel A (simplest, writes the `panel_A_row_order.rds` side-effect we want to confirm lands in the right place):

```bash
cd /Users/fkampf/Documents/pheromone.paper/figures/fig5
Rscript -e 'rmarkdown::render("panel_A.Rmd", output_dir="html")'
```

**Verification checklist:**

- [ ] `figures/fig5/html/panel_A.html` exists and is non-empty
- [ ] `figures/fig5/plots/panel_A/png/panel_A_input_profiles_raw.png` exists (new, since last run)
- [ ] `figures/fig5/plots/panel_A/pdf/panel_A_input_profiles_raw.pdf` exists
- [ ] `figures/fig5/panel_A_row_order.rds` exists (side-effect from line 137)
- [ ] `figures/fig5/plots/panel_A/panel_A_narrative.txt` exists
- [ ] No errors about missing files from `feather/strongest.paths/` or `R/` sources

If any check fails, stop and diagnose — do not proceed to full render.

---

## Phase 6 — Full render via `render_all.R`

**Goal.** Regenerate all 12 panels into the new layout and confirm `selection/` copies still work.

```bash
cd /Users/fkampf/Documents/pheromone.paper/figures/fig5
Rscript render_all.R
```

**Verification:**

```bash
ls figures/fig5/html/                              # 12 html files (A–L)
ls figures/fig5/plots/ | sort                      # 12 panel directories
ls figures/fig5/selection/*.pdf | wc -l            # > 0, curated PDFs
```

Then (optional) confirm the mspecific variant still works:

```bash
Rscript render_mspecific.R
ls figures/fig5/plots_mspecific/ | sort            # 11 panel dirs (no H)
```

**Anti-pattern guard.** Do NOT compare byte-identical output — timestamps, cairo font hinting, and RNG-seeded layouts produce bit-level differences. Visual spot-check a few PDFs instead.

---

## Phase 7 — Final verification sweep

**Goal.** Prove no dangling references to the old path remain anywhere in the repo.

```bash
cd /Users/fkampf/Documents/pheromone.paper
# Should return zero results:
grep -rn 'pheromone.paper/fig5' --include='*.R' --include='*.Rmd' .
grep -rn '"fig5"' --include='*.R' --include='*.Rmd' . | grep -v figures/fig5
```

If either grep returns hits, inspect each — they may be:
- Comments or narrative text (fine, but update for clarity)
- Code in `fig5_bella_targets/` (out of scope for this plan — leave as-is)
- Something missed — add an edit and re-verify

---

## Phase 8 — Commit

```bash
git status    # review: renames + 16 file modifications
git add -A
git commit -m "refactor: move fig5/ under figures/ parent directory"
```

**Anti-pattern guard.** Do NOT `git add .` blindly — the untracked files (`claude_research/`, `fig5/` stragglers from prior sessions, `fig5_dynamic_decision_design.txt`) may or may not belong in this commit. Stage explicitly.

---

## Out of scope (follow-up plans)

- **Move `fig6/` and `fig6_bella_targets/`.** Same template, ~1 hour each. Defer until fig5 is verified working.
- **Per-panel subdir reorg (target B).** Not recommended — see "Why target A" above.
- **Renaming `plots_mspecific/` → `plots/mspecific/`.** Possible cleanup, but independent of this move.
