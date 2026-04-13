# Repo Root Cleanup Plan

**Goal.** Collapse the remaining analysis-folder clutter at the repo root into a single `analyses/` parent (mirroring the `figures/` move already done). Normalize dotted folder names to underscores.

**Target layout:**

```
pheromone.paper/
  analyses/
    aspf_as_targets.Rmd                      (already here)
    aspg_as_targets.Rmd                      (already here)
    combinatorial_signal_flow/               (moved from root)
    inherited_connectivity/                  (renamed, moved)
    robustness_and_nulls/                    (renamed, moved)
    strongest_path/                          (renamed, moved)
    strongest_path_closer_evaluation/        (renamed, moved)
  figures/                                   (done in prior commits)
  feather/                                   (stays — data cache)
  R/                                         (stays — shared utilities)
  claude_research/                           (stays)
  install_packages.R                         (stays — project setup)
  pheromone.paper.Rproj                      (stays — must be at root for RStudio)
  .gitignore
```

**What's being removed from root:** 5 analysis directories, consolidated under `analyses/`.

---

## Phase 0 — Audit (already scoped)

Tracked content + references inventory:

| Folder | Tracked files | External references |
|---|---|---|
| `combinatorial_signal_flow/` | ~10 | `figures/fig5/setup.R:456`, `combinatorial_signal_flow/export_for_python.R:16` |
| `inherited.connectivity/` | 1 (`intherited.connectivity.Rmd`) | none in R/Rmd |
| `robustness.and.nulls/` | 1 (`rewiring.Rmd`) | none in R/Rmd |
| `strongest.path/` | 6 Rmds | mentioned in `figures/fig6/PANEL_DESCRIPTIONS.md` (narrative text only) |
| `strongest.path.closer.evaluation/` | 15 files (has own `R/`, `plots/`) | mentioned in `figures/fig6/PANEL_DESCRIPTIONS.md` (narrative text only) |

**Only two executable references need rewriting** (both in R code):
1. `figures/fig5/setup.R:456` — `file.path(project_root, "combinatorial_signal_flow", ...)`
2. `combinatorial_signal_flow/export_for_python.R:16` — `file.path(project_root, "combinatorial_signal_flow", "data")`

**Narrative references in `.md`** can stay factually correct or be updated — not load-bearing for code.

**Not audited yet but LOW RISK:** internal references within the moved folders themselves (e.g., an Rmd inside `strongest.path/` that hardcodes its own folder name). A grep pass in Phase 2 catches those.

---

## Phase 1 — Move + rename folders

**Goal.** Relocate under `analyses/` and normalize dot-separated names to underscore_separated (consistent with the rest of the repo).

```bash
cd /Users/fkampf/Documents/pheromone.paper

# Tracked folder — use git mv
git mv combinatorial_signal_flow analyses/combinatorial_signal_flow

# Dotted-name folders: rename AND move in one git mv per folder
git mv inherited.connectivity analyses/inherited_connectivity
git mv robustness.and.nulls analyses/robustness_and_nulls
git mv strongest.path analyses/strongest_path
git mv strongest.path.closer.evaluation analyses/strongest_path_closer_evaluation
```

**Anti-pattern guard.**
- If `git mv` fails with "source directory is empty", there are untracked files blocking the move — investigate before using plain `mv`. Same pattern as the fig5/fig6 reorgs.
- If `git mv` fails with "bad source" errors, there are stale deletions tracked — run `git status --short <folder>/ | grep "^ D"` and `git rm` each before retrying.
- Do NOT rename the `strongest.paths/` subdir inside `feather/` — that's a data cache, its name is the canonical filename prefix inside feather files.

**Verification:**
```bash
ls analyses/    # 2 Rmds + 5 directories
ls combinatorial_signal_flow inherited.connectivity robustness.and.nulls strongest.path strongest.path.closer.evaluation 2>&1 | grep -c "No such"
# expect: 5
```

---

## Phase 2 — Update the two executable path references

**Edit 1 — `figures/fig5/setup.R:456`:**

```r
# before
sf_plots_dir <- file.path(project_root, "combinatorial_signal_flow", "plots", "sigmoid_rectified")
# after
sf_plots_dir <- file.path(project_root, "analyses", "combinatorial_signal_flow", "plots", "sigmoid_rectified")
```

**Edit 2 — `analyses/combinatorial_signal_flow/export_for_python.R:16`:**

```r
# before
export_dir <- file.path(project_root, "combinatorial_signal_flow", "data")
# after
export_dir <- file.path(project_root, "analyses", "combinatorial_signal_flow", "data")
```

**Then a sweep for anything missed (internal references inside the moved folders):**

```bash
cd /Users/fkampf/Documents/pheromone.paper
grep -rn --include='*.R' --include='*.Rmd' \
  -E '(inherited\.connectivity|robustness\.and\.nulls|strongest\.path[^s]|combinatorial_signal_flow)' \
  analyses/ figures/
```

Any hit that isn't (a) `feather/strongest.paths/` (different folder, trailing `s`, not moved) or (b) the two Edits above — triage and fix.

**Anti-pattern guard.** Do NOT rewrite `strongest.paths` (plural, inside `feather/`). That folder did NOT move. The regex above uses `strongest\.path[^s]` to exclude it.

---

## Phase 3 — Verify setup scripts still source

```bash
cd figures/fig5 && Rscript -e 'source("setup.R"); cat("OK:", sf_plots_dir, "\n")' | tail -2
# expect path ending in /analyses/combinatorial_signal_flow/plots/sigmoid_rectified
```

fig6 setups don't reference these folders, so no re-check needed there.

---

## Phase 4 — Update narrative mentions (non-load-bearing)

`figures/fig6/PANEL_DESCRIPTIONS.md:52` references `strongest.path.closer.evaluation.Rmd` by name. Rename the mention to match new path (`analyses/strongest_path_closer_evaluation/strongest.path.closer.evaluation.Rmd`) OR just leave — it's prose. Choose based on how authoritative that doc is meant to be.

**Recommended:** update the prose to the new path so future readers can find the file.

---

## Phase 5 — Gitignore hygiene

Add to `.gitignore` if not already excluded:

```
# Claude auto-generated
claude.context/
.claude/

# Session junk
.Rhistory
```

Verify with:
```bash
git check-ignore -v claude.context .Rhistory .claude
```

Remove `.Rhistory` from working tree if present (harmless junk):
```bash
rm -f .Rhistory
```

**Anti-pattern guard.** Do NOT `git rm` `claude_research/` — that's the deliberate persistent research folder (not claude-mem auto-output).

---

## Phase 6 — Stage + commit

```bash
git status --short | head -40    # review
git add -A analyses/ figures/
git add .gitignore               # if Phase 5 touched it
git commit -m "refactor: consolidate analyses under analyses/; normalize names"
```

**Anti-pattern guard.** Don't use `git add -A` at repo root without path filters — it would include unrelated working-tree changes in `figures/fig5/plots/` runs, stale Rproj files, etc.

---

## Phase 7 — Final root check

```bash
ls /Users/fkampf/Documents/pheromone.paper
```

Expected:
```
analyses  claude_research  feather  figures  install_packages.R
pheromone.paper.Rproj  R
```

(Plus dotfiles: `.gitignore`, `.claude/` if gitignored but present, etc.)

If any item other than the above appears, it's either (a) legitimately infrastructure missed by this plan, or (b) should be moved.

---

## Out of scope

- **Reorganizing inside `analyses/` folders.** Each analysis directory has its own internal structure — don't touch it in this pass.
- **Consolidating shared `R/` utilities.** Already at root, already referenced via `project_root/R/*.R` from every figure's setup.R. Works.
- **Moving `feather/`.** It's the data cache, referenced from every fig setup.R as `project_root/feather/`. Changing it is a separate larger change.
- **Cleaning up unrelated working-tree modifications** (e.g., the `M combinatorial_signal_flow/*.py` entries from prior sessions). Those are unrelated edits — address in their own commit, not here.
