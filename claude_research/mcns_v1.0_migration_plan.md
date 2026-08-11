# maleCNS v0.9 -> v1.0 migration plan

Surveyed 2026-08-11. Read-only audit; nothing was changed.

# maleCNS v0.9 → v1.0 migration plan

## 1. VERDICT

**No — this cannot be done as a global find-and-replace, and the reason is *not* what you expect.** Body IDs turned out to be the *safe* part: all 10 named v0.9 body IDs in the codebase (200336, 801269, 18430, 18696, 11431, 12286, 17103, 17335, 13341, 13693) resolve in v1.0 with **identical type, instance, somaSide and status**, and the only body ID literal in executable code — `12286` at `/Users/fkampf/Documents/pheromone.paper/analyses/an_investigation/R/_paths.R:65` — is still `AN05B102a_R`. A sweep of every 5–9-digit literal in `.R`/`.Rmd` found 19 real body IDs and **all 19 keep their v0.9 type in v1.0**.

What breaks instead, loudly:

1. **`P1_*` no longer exists in v1.0.** The whole family was renamed to `pC1_*` (v0.9: 45 `P1_*` types / 148 bodies, 4 `pC1*` types; v1.0: **zero** `P1_*`, 49 `pC1*` types / 156 bodies). Every `grepl("^P1_", type)` returns an empty set on v1.0 — silently, with no error. I grepped: **7 live regex/label sites** plus a `"P1_all"` target group and ~16 archived files (listed in §3).
2. **`LgLG7` and `LgLG8` swapped identity.** Body 817057 was `LgLG8_R` in v0.9 and is `LgLG7_R` in v1.0; body 819781 went the other way. Counts are unchanged (14/14), so nothing looks wrong — the neuron behind the name is simply different. `LgLG3a` + `LgLG3b` also merged into one `LgLG3`, and five `SNch*` types were reclassified into `LgLG*`.
3. **`f3969:master` in the neuroglancer URL is a moving branch pointer, not a pin — and it already points at v1.0.** So your *currently published* v0.9-ID scenes are already being rendered against the v1.0 segmentation, and they will silently follow master to whatever Janelia commits next. This is fixable (exact v1.0 URL in §3) but it is a semantic change, not a string swap: there is no `v0.9` substring in that URL to replace.
4. **The dataset selector that actually governs half your queries has no `v0.9` string to replace.** `mcns_body_annotations()`, `mcns_connection_table()`, `cf_ids(malecns=…)` and `read_mcns_meshes()` all resolve through `getOption("malecns.dataset")`, whose default is baked into `malecns:::.onLoad`. Editing `MCNS_DATASET` / `neuprint_login(dataset=)` does **nothing** for those calls. An `options(malecns.dataset = "male-cns:v1.0")` line must be *added* in ~12 places.
5. **The caches are authoritative and version-blind.** `feather/mba.feather` (18 MB), `feather/connectivity.feather` (617 MB), `adj.matrix*.rds`, `graph.general.rds` and ~95 `strongest.paths/*.feather` are all read under `file.exists()` / `force_recompute = FALSE` guards with no version stamp. Change every dataset string in the repo and **not one number in any figure changes** until these are rebuilt.
6. **`receptor_type` materially degraded.** Non-NA count 979 → 752; `putative_IR52a` was **deleted wholesale** (252 bodies → 0), and all 97 WG2 bodies now carry no `receptor_type` at all. Any channel definition built from that column changes meaning.

Connectivity itself is essentially frozen (spot-checks: body 11431 → 10604 partners / weight 24370 in *both*; body 200336 → 4210 / 8119 in *both*), and mAL is completely untouched (37 types / 159 bodies in both, zero type changes). So the migration is *tractable* — it is just not a sweep.

---

## 2. SAFE EDITS

Pure `"male-cns:v0.9"` → `"male-cns:v1.0"` string swaps, executable code:

| File | Line |
|---|---|
| `/Users/fkampf/Documents/pheromone.paper/analyses/an_investigation/R/_paths.R` | 18 |
| `/Users/fkampf/Documents/pheromone.paper/figures/fig5/setup.R` | 88 |
| `/Users/fkampf/Documents/pheromone.paper/figures/fig6/panel_brain_maps.Rmd` | 188, 745 |
| `/Users/fkampf/Documents/pheromone.paper/analyses/inherited_connectivity/intherited.connectivity.Rmd` | 51 (live); 28, 29 (commented) |
| `/Users/fkampf/Documents/pheromone.paper/analyses/strongest_path/mcns.circuit.construction.strongest.path.Rmd` | 24, 25 (commented) |
| `/Users/fkampf/Documents/AVLP743m_connectomics/R/_paths.R` | 13 |
| `/Users/fkampf/Documents/AVLP743m_connectomics/R/02_fetch_input_synapses.R` | 5, 24, 33 |
| `/Users/fkampf/Documents/AVLP743m_connectomics/R/03_annotate_input_synapses.R` | 5, 42 |
| `/Users/fkampf/Documents/AVLP743m_connectomics/R/04_input_synapse_map.R` | 5 |
| `/Users/fkampf/Documents/AVLP743m_connectomics/R/06_axon_dendrite.R` | 13, 32 |

Generated-page provenance strings (swap so the page stops asserting v0.9):

| File | Line |
|---|---|
| `/Users/fkampf/Documents/pheromone.paper/analyses/an_investigation/R/03_neuroglancer_scenes.R` | 571 (better: interpolate `MCNS_DATASET`) |
| `/Users/fkampf/Documents/AVLP743m_connectomics/R/09_neuroglancer_scenes.R` | 258 |
| `/Users/fkampf/Documents/pheromone.paper/figures/fig5/panel_M/rmd/M_an05b035_morphology.Rmd` | 241, 325 |

Prose / documentation swaps (no runtime effect):

`analyses/an_investigation/README.md:4` · `figures/fig5/panel_M/notes/MORPHOLOGY_DATA_NOTES.md:11,12,67` · `figures/fig5/panel_M_p1_classification_archive/agent01_extract.R:150`, `agent02_analysis.R:224`, `PANEL_M_SYNTHESIS.md:4`

**Additions, not swaps** — these `neuprint_login()` calls pass *no* `dataset=` and currently float to the server default. They need `dataset = "male-cns:v1.0"` inserted:

`figures/fig6/setup.R:91` · `figures/fig6_bella_targets/setup.R:92` · `figures/fig6_bella_targets/compute_paths.R:31` · `analyses/aspf_as_targets.Rmd:71` · `analyses/aspg_as_targets.Rmd:71` · `analyses/strongest_path_closer_evaluation/strongest.path.closer.evaluation.Rmd:71`

Explicitly **not** to change: `MCNS_SERVER` (same host for both), `em_url = "precomputed://gs://cns-full-clahe"` (same grayscale volume), the two `flyem-cns-roi-7c971aa…` shell meshes, the camera coordinates at `_paths.R:66,68` and `neuroglancer.R:121,129`, and the `colorSeed` values — all confirmed version-independent or confirmed false positives.

---

## 3. UNSAFE

### 3a. `P1_*` → `pC1_*` (silent empty results)

v1.0 has zero `P1_*` types. Live sites found by grep:

- `figures/fig6/panel_G.Rmd:75` — `"P1" = "^P1_"`
- `figures/fig6/panel_K.Rmd:85` — `"P1" = "^P1_"`
- `figures/fig6_bella_targets/panel_G.Rmd:77` — `"P1" = "^P1_"`
- `figures/fig6_bella_targets/panel_K.Rmd:85` — `"P1" = "^P1_"`
- `figures/fig5/setup.R:490, 495` — `filter(target_group == "P1_all", …)`
- `figures/fig6_bella_targets/panel_H.Rmd:73, 101` — literal `"P1_3"` pattern
- `figures/fig6_bella_targets/compute_paths.R:63` and `panel_A.Rmd:84` — literal `"P1_3c"`
- `analyses/combinatorial_signal_flow/data/targets.json` — `"P1_all"` key
- Archive (`figures/fig5/panel_M_p1_classification_archive/`): `agent01_extract.R:22`, `agent04_analysis.R:66,248`, `agent07_p1_lateral.R:23`, `agent02_analysis.R:226`, plus ~16 `p1_*.csv` outputs
- `figures/fig5/rmd/panel_I_p1_decoder.Rmd` (15 `P1_` occurrences — I did not audit which are regexes vs labels)

**What breaks:** filters return zero rows; a "P1" facet/legend entry renders empty; `target_group == "P1_all"` yields nothing. No error anywhere.
**What it takes:** decide whether the paper adopts `pC1_*` nomenclature or keeps saying "P1" in prose while filtering on `pC1_`. That is a naming decision, not a mechanical edit. Whichever way, every site above needs a per-site read — `P1_3c` may or may not have a 1:1 `pC1_3c` counterpart, which is **UNKNOWN** (the probe enumerated counts, not the name-by-name mapping). v1.0 ships an `old_type` annotation column that can be used to build the mapping authoritatively.

### 3b. `LgLG7` / `LgLG8` swap, `LgLG3a`+`LgLG3b` merge, `SNch` → `LgLG` reclassification

**What breaks:** anything keyed by these type names — `analyses/combinatorial_signal_flow/data/channels.json`, the `adj_matrix_*.mtx` + `type_names.csv` pair, and any `LgLG7`/`LgLG8` mention in captions — silently refers to a different neuron. Counts stay the same (14/14), so no sanity check fires. Body-level detail: 817057 LgLG8→LgLG7, 819781 LgLG7→LgLG8, 819165 LgLG7→LgLG6, 825461/820407/843529/828914 LgLG1b→LgLG1a, 821097/846186 SNch05→LgLG1b, 864655 SNch06→LgLG2.
**What it takes:** re-derive channel membership from v1.0 annotations and diff against the published channel lists before regenerating anything; if any figure names LgLG7 or LgLG8 individually, that claim has to be re-checked, not relabelled. WG1–WG4 are byte-identical (same counts, same body ID sets) so the WG side is safe.

### 3c. `receptor_type` degradation

`putative_IR52a` is gone (252 → 0 bodies); all 97 WG2 bodies now have `NA`. Sites: `R/data_processing.R:34,39,84,95,96`; `analyses/strongest_path_closer_evaluation/R/data_processing.R:34,39`; `analyses/combinatorial_signal_flow/export_for_python.R:75,76`.
**What breaks:** the ppk23/ppk25-derived channel definitions shift slightly (269 vs 264, 257 vs 258 bodies) and any IR52a-derived set becomes empty. `export_for_python.R` warns about types missing from the adjacency matrix but **not** about an empty channel.
**What it takes:** given the standing distrust of the receptor call (`receptor_typing_validation/PLAN.md`), this should be a deliberate re-derivation, not a silent follow-along. Add an assertion that each channel is non-empty.

### 3d. Neuroglancer segmentation source

`f3969:master` is a branch head. Live-probed: `GET /api/repo/f3969/info` → the only childless node on the unnamed (master) branch is V142 `4b2087c0fbe046bfaf0d60bc970e3e5d`, note `tag "v1.0"` — and `GET /api/dbmeta/datasets` confirms neuprint's `male-cns:v1.0` names that same uuid. So **master == v1.0 today**, and v0.9 = `79f9a4cb54b0463cad8615b26bf8f137` (V128).

Exact replacements (both must move together or you get v1.0 geometry with mismatched labels):

```
dvid://https://emdata6-novran.janelia.org/4b2087c0fbe046bfaf0d60bc970e3e5d/segmentation?dvid-service=https://ngsupport-bmcp5imp6q-uk.a.run.app
precomputed://https://ngsupport-bmcp5imp6q-uk.a.run.app/neuronjson_segment_properties/emdata6-novran.janelia.org/4b2087c0fbe046bfaf0d60bc970e3e5d/segmentation_annotations/type/group
```

Verified: `/api/node/4b2087…/segmentation/info` → 200, byte-comparable to master, VoxelSize `[8,8,8]`; the `.ngmesh` subsource returns an identically-sized payload at the pinned uuid; the sidecar `…/info` returns 200 / 3890902 bytes with an id set **exactly equal** to master's (165025 ids). Note `f3969:v1.0` is **403** — there is no such branch; use the bare uuid.

Files: `pheromone.paper/R/neuroglancer.R:10,42` · `analyses/strongest_path_closer_evaluation/R/neuroglancer.R:10,42` (byte-identical copy) · `analyses/strongest_path_closer_evaluation/strongest.path.closer.evaluation.Rmd:3859,3891` **and** `4065,4133` (a second inline copy that shadows the first at runtime — both must be edited) · comment at `analyses/an_investigation/R/03_neuroglancer_scenes.R:7`. Also present in the four untracked `.Rmd.backup/.cleaned/.final.bak/.fixed.bak2` copies — recommend deleting rather than migrating.

### 3e. The hidden `malecns.dataset` option

No `v0.9` literal exists to replace; `malecns:::.onLoad` sets it. Confirmed sufficient by probe: with only `options(malecns.dataset=…)` changed in one session, `mcns_body_annotations()` returned 211239×42 vs 211271×50 rows, and body 825461 came back `LgLG1b`/`unclear`/`putative_ppk25` under v0.9 vs `LgLG1a`/`acetylcholine`/`putative_ppk23` under v1.0. `choose_mcns()` special-cases the literal `"male-cns:v0.9"` and otherwise delegates to `malevnc::choose_flyem_dataset()`, which resolves `male-cns:v1.0` to the correct uuid.

**Add `options(malecns.dataset = "male-cns:v1.0")` before every `choose_mcns()` / first `mcns_*` call:** `figures/fig5/setup.R:89` · `figures/fig6/setup.R:92` · `figures/fig6_bella_targets/setup.R:93` · `figures/fig6_bella_targets/compute_paths.R:32` · `analyses/strongest_path/mcns.strongest.path.hierarchical.Rmd:65` · `remove.dimorphism.Rmd:68` · `remove.dimorphism.and.specific.Rmd:69` · `remove.sex.specific.Rmd:70` · `analyses/robustness_and_nulls/rewiring.Rmd:64` · `analyses/strongest_path_closer_evaluation/strongest.path.closer.evaluation.Rmd:97` · `analyses/aspf_as_targets.Rmd:94` · `analyses/aspg_as_targets.Rmd:94` · `pheromone.paper/R/data_processing.R` (no `choose_mcns()` at all, yet calls `mcns_body_annotations()` at L29/L125) · `analyses/inherited_connectivity/intherited.connectivity.Rmd:54,55` and `analyses/strongest_path/mcns.circuit.construction.strongest.path.Rmd:47,48,73` (also no `choose_mcns()`) · `AVLP743m_connectomics/R/09_neuroglancer_scenes.R:148`. Precedent already in the tree: `receptor_typing_validation/R/05_design_matrix_v1.R:2`.

### 3f. `choose_mcns_dataset("cns")` escape hatch

`analyses/strongest_path/mcns.strongest.path.hierarchical.Rmd:2103-2106` switches globally to the `cns` dataset to render meshes ("V9 snapshot doesn't work"), never reverts, so every later chunk — including `neuprint_get_synapses` at 2183 and 2411 — runs against `cns`. Re-test whether the workaround is still needed on v1.0; if not, delete it. If kept, it must be scoped and reverted.

### 3g. Hard-coded census assertions and derived literals

`AVLP743m_connectomics/R/12_an09b017_mal_convergence.R:36` — `stopifnot(nrow(fam) == 14, n_distinct(fam$type) == 7)`. **This one passes:** AN09B017a–g are 2 bodies each in both versions = 14 bodies / 7 types. It is the only place a version change would hard-fail, so leave it in as a canary. Related literals in the same file that are v0.9 results in text: header comment L10-13 ("159 bodies, 37 types" for mAL — mAL is unchanged, so still true), L161 `p < 1e-300`, L193-194 mAL target names.

### 3h. `as.integer(bodyid)` 32-bit downcast

`R/data_processing.R:147,165` and the same pattern in five `strongest_path*` notebooks. v0.9 max body ID is 1,571,679,990 — 73% of the int32 ceiling. **Whether any v1.0 body ID exceeds 2^31 is UNKNOWN** (the probe pulled the full v1.0 annotation table but did not report its max body ID). Check it before the first recompute; if it overflows, joins drop rows with only a coercion warning.

### 3i. ROI-derived type suffixes and the T1 laterality check

v1.0 adds 100+ ROI synapse-count node properties (AL glomeruli, MB compartments, CX/INP/PENP/SNP super-ROIs). The `" _ADMN"/" _ProLN"/" _MesoLN"/" _MetaLN"` suffixes are minted locally in `R/data_processing.R` (~L65) from `neuprint_get_roiInfo`, validated by a hard stop at `an_investigation/R/02_annotate_input_synapses.R:28`, and consumed by the `bare_type()` regex at `_paths.R:106`. `03_neuroglancer_scenes.R:234` depends on the literal ROI names `LegNp(T1)(L).post` / `LegNp(T1)(R).post` — if renamed, `z()` returns 0 and `contra` becomes NA/0 rather than erroring. **Whether these specific ROI names survive in v1.0 is UNKNOWN** — verify before regenerating `mba.feather`.

### 3j. Missing regeneration code

`AVLP743m_connectomics/data/raw/AVLP743m_skeletons.rds` is read by seven scripts and **produced by none**. A fetch (`neuprint_read_neurons` / `mcns_read_neurons`) has to be written as part of the migration. Consumers index `skels[[as.character(bid)]]`; most return `NULL` silently on a miss, but `10_export_for_navis.R:15` has no guard and will error.

### 3k. Frozen shortlinks

`https://is.gd/QWEo9C` appears in three files (`figures/fig5/panel_M/M_an05b035_neuroglancer_url.txt`, `plots_mspecific/panel_M/panel_M_morphology_v2_neuroglancer_url.txt`, and the `data/` copy) and `analyses/strongest_path_closer_evaluation/full_url.txt` holds a percent-encoded scene with `f3969:master` and body IDs 13693/13341 baked in. These cannot be re-pointed by editing code — they must be regenerated, and any already circulated externally are unrecoverable.

---

## 4. CACHES TO REGENERATE

Nothing below is version-stamped; every one is read under `file.exists()` or `force_recompute = FALSE`. **The dataset edits are inert until these are rebuilt.**

**Tier 1 — the root of everything**

| Artifact | Size / date | Rebuild | Cost |
|---|---|---|---|
| `pheromone.paper/feather/mba.feather` | 18 MB, 7 Dec 2025 | `options(malecns.dataset="male-cns:v1.0")` then `load_mba(force_recompute = TRUE)` (`R/data_processing.R:20-77`) | ~15 s for the `mcns_body_annotations()` pull (211k rows, measured), plus the `neuprint_get_roiInfo` suffix pass — cost UNKNOWN |
| `pheromone.paper/feather/connectivity.feather` | **617 MB**, 7 Dec 2025 | `load_connectivity(force_recompute = TRUE)` → `cf_partners(cf_ids(malecns = <211k ids>))` | Large; not measured — **UNKNOWN**, budget hours |

**Tier 2 — derived from Tier 1**

`feather/adj.matrix.rds` (6.0 MB, 6 Jan 2026) · `adj.matrix.pre.rds` (9.2 MB) · `adj.matrix.raw.rds` (3.8 MB) · `graph.general.rds` (12.5 MB) — all via `load_all_data(cache_dir=…, force_recompute = TRUE)`. Cheap once connectivity exists (in-memory matrix/graph construction).
`feather/target.PPN1.rds`, `feather/target.vAB3.rds` — from `cf_partner_summary(cf_ids(malecns=…))`.

**Tier 3 — path caches (delete, they have no version in the filename)**

`feather/strongest.paths/` — 95 files, Oct 2025 – Apr 2026, incl. `bella_target_groups.rds`, `bella_targets_list.rds`. `feather/strongest.paths.merged/` (13 Apr 2026). Written by `fig5/setup.R:294,368`, `fig6/setup.R:155,169-175`, `fig6_bella_targets/{setup.R:173, compute_paths.R:203,241,243}`, `fig5/panel_M/compute_si_paths.R:14`, `fig5/rmd/panel_A_supp_real_merge.Rmd:103`, `panel_A_supp_level1.Rmd:150`. The fig5 validity check at `setup.R:317-326` compares only the *target set*, not the version — a v0.9 cache passes. **Wipe the directories**; the reload guards will recompute.

**Tier 4 — figure-local**

`figures/fig5/panel_M/cache/meshes/` — 22 `.rds` files named by bare body ID (`17492, 18324, 18430, 18627, 18696, 23513, 27346, 38322, 46466, 59387, 100234, 114184, 200336, 517601, 520195, 800035, 800040, 800320, 801269, 805770, 807376, 910810`), 16 Apr. `panel_M_morphology_v2.Rmd:265` does `if (file.exists(f)) return(readRDS(f))` with **no dataset in the key** — a colliding v1.0 ID renders the wrong mesh with no warning. Delete the directory.
`feather/brain_map_synapses.feather` — 22.8 MB, 13 Feb 2026, fetched with the explicit `dataset="male-cns:v0.9"` at `panel_brain_maps.Rmd:188`; guard at :158 only checks for a `type` column. Delete.
Type-name-keyed row orders (low risk, regenerate for consistency): `fig5/panel_A_row_order.rds`, `fig6/panel_B_row_order.rds`, `panel_B_all_row_order.rds`, `fig6_bella_targets/panel_B_row_order.rds`, `panel_M_mal_sort_order.rds`, `an_investigation/data/derived/sn_an_heatmap_col_order.txt` (already orphaned — nothing reads or writes it).

**Tier 5 — `an_investigation/`** (delete then rerun `01 → 02 → 03`, and `04`)

`data/raw/{an05b023bc,an05b102,an09b017}_input_synapses.feather` (584 KB / 1.57 MB / 623 KB) — `01…R:26` short-circuits on existence, so these **must** be deleted or nothing refetches. `data/derived/*_input_synapses_annotated.feather`, `*_synonyms.rds`, `*_t1_bilaterality.rds` (body-ID-keyed — joins to NA and prints "-" rather than failing), `*_neuroglancer_scenes.csv`. `an05b023_neuroglancer_scenes.csv` is an orphan from before the case rename — delete, don't migrate. `Rplots.pdf` and `plots/sn_an_heatmap*.{pdf,png}` are v0.9 outputs. `04_SN_AN_connections.html` needs re-knitting, not editing.

**Tier 6 — `AVLP743m_connectomics/`** (delete `data/raw/*` and `data/derived/*`, rerun `02 → 12`)

`AVLP743m_input_synapses.feather`, `AVLP743m_output_synapses.feather`, `roi_meshes.rds` (9.6 MB), `AVLP743m_output_partner_meta.feather`, `AN09B017_mal_connections.feather`, `AVLP743m_top_partners.rds`, plus 25+ derived products and 26 `data/derived/report_parts/*.md` feeding four top-level markdown reports. `AVLP743m_skeletons.rds` has **no rebuild path** (§3j). `data/navis_export/` writes per-body-ID SWCs without cleanup.

**Tier 7 — Python bridge** (`analyses/combinatorial_signal_flow/`)

`export_for_python.R` is the only R↔Python link; the Python tree never touches neuprint and has **zero hardcoded body IDs** (entirely type-name based). Regenerate `data/adj_matrix_{post,pre,raw}.mtx`, `type_names.csv`, `channels.json`, `targets.json`, `neurotransmitter_mapping.csv` **together** — the `.mtx` index ordering and `type_names.csv` must match or every channel index silently points at the wrong type. `modality_colors.json` needs nothing. `ppk_interaction_investigation/INVESTIGATION_RESULTS.txt` is a committed v0.9 result artifact with numeric weights baked in.

**Highest-risk consumer:** `analyses/strongest_path/target.set.sensitivity.Rmd` never calls `choose_mcns` or `neuprint` at all — it is a pure cache reader with `must_exist()` hard stops. It will keep emitting v0.9 results forever with zero warning.

---

## 5. PUBLISHED ARTEFACTS AT RISK

`~/Documents/AVLP743m_connectomics/website/ng/` holds **72 `*.json` scenes** plus `an05b023bc/`, `an05b102/`, `an09b017/` menu pages from `an_investigation/03_neuroglancer_scenes.R`, and **78 more** from `AVLP743m_connectomics/09_neuroglancer_scenes.R` (`avlp743m/`, `receptor-typing/`). Every filename embeds a v0.9 body ID (`AN05B023b_200336.json`, `AN05B102d_16505.json`, `AN09B017a_17103.json`, …) and every `segments` list holds v0.9 IDs.

What is actually happening right now: because the scenes point at `f3969:master`, **they are already rendering v0.9-derived IDs against the v1.0 segmentation**. The mismatch the brief worries about is present today; migrating the analysis to v1.0 *fixes* it rather than causing it.

Whether that is currently doing damage: measured drift between the two release nodes over a random 400-body sample of the 165007 shared typed IDs — 398 identical voxel counts, 2 changed (14106: 1253502563 → 1260985494; 907472: 556577381 → 546757501), 0 missing, i.e. ~0.5% silent drift. Seven typed bodies exist in v0.9 and **not** in v1.0 (`206751, 435077, 518041, 527138, 86009, 898405, 945500`) — body 86009 (GNG493) returns HTTP 404 at the v1.0 node, so a scene listing it renders nothing at all. **Whether any of those seven, or any of the drifted bodies, appear in your published scene list is UNKNOWN** — the probe sampled randomly rather than over your concrete ID lists. That check is one query and should be run.

Three further consequences:

- The menu pages hardcode "Clio-NG scenes for the male CNS (male-cns:v0.9)" (`03_neuroglancer_scenes.R:571`, `09_neuroglancer_scenes.R:258`). Post-migration they will assert v0.9 while showing v1.0 data unless those strings are fixed.
- **Reruns do not delete old files.** New v1.0-named JSONs land *alongside* the v0.9-named ones, so the stale scenes stay live on floriankaempf.com indefinitely. The `ng/` directory must be cleaned explicitly.
- The `is.gd` shortlinks (§3k) and `full_url.txt` are frozen. They will follow `master` wherever it goes and cannot be patched. If any is in a submitted manuscript it must be regenerated and the manuscript updated.
- `AVLP743m_connectomics/python/build_hull_meshes.py` output (`https://floriankaempf.com/ng/meshes` + `DERIVED/hull_meshes.csv`) is built from v0.9 synapse positions and must be rebuilt with the rest.

---

## 6. RECOMMENDED ORDER

**Phase 0 — decide, before touching anything**

1. **The `P1_` → `pC1_` nomenclature call.** This is a paper-level naming decision (does the manuscript say P1 or pC1?), not a migration mechanic. Build the authoritative old→new mapping from the v1.0 `old_type` column first.
2. **Whether `receptor_type` still underpins the channel definitions at all**, given the standing distrust of that annotation. Losing `putative_IR52a` entirely is a reason to revisit, not a reason to silently follow.
3. **Whether the `LgLG7`/`LgLG8` swap touches any figure claim.** If a figure names either type individually, the underlying claim must be re-checked.

Keep all three out of the sweep.

**Phase 1 — pin, don't rebuild (cheap, reversible)**

4. Apply the §2 string swaps and the six `dataset=` additions.
5. Add `options(malecns.dataset = "male-cns:v1.0")` at the 16 sites in §3e. Verify with `getOption("malecns.dataset")` in a fresh session after sourcing each `setup.R`.
6. Pin the neuroglancer uuid in the four live locations (§3d) — including the **second** inline copy at `Rmd:4065,4133` that shadows the first. Delete the four untracked `.bak/.cleaned` notebook copies rather than editing them.
7. Verify `f3969:master` still equals `4b2087c0fbe0…` at the moment you pin, so the pin is a no-op for currently rendered geometry.

**Phase 2 — verify before spending compute**

8. Check `max(bodyid)` in the v1.0 annotation table against 2147483647 (§3h). If it overflows, fix the `as.integer()` downcasts *before* any recompute.
9. Check that `LegNp(T1)(L).post` / `(R).post` and the ADMN/ProLN/MesoLN/MetaLN nerve ROIs still exist under v1.0 (§3i).
10. Run the drift check over your actual published scene ID lists (§5) — cheap, and it tells you whether the live site is currently wrong.
11. Confirm the four `FOCUS` type names (`DA1_lPN`, `M_lvPNm45`, `AN09B017f`, `AN05B102d`) still exist. All four are attested in v1.0 by the probe for the AN types; `DA1_lPN` and `M_lvPNm45` are **UNKNOWN**.

**Phase 3 — rebuild caches, root-first**

12. `mba.feather` → verify the nerve suffixes and the `bare_type()` regex still match, and that the `02_annotate_input_synapses.R:28` hard stop passes.
13. `connectivity.feather` → `adj.matrix*.rds` → `graph.general.rds` → `target.*.rds`.
14. Wipe `feather/strongest.paths/`, `feather/strongest.paths.merged/`, `feather/brain_map_synapses.feather`, `figures/fig5/panel_M/cache/meshes/`.
15. Wipe and rerun `an_investigation/` (01→02→03, then 04) and `AVLP743m_connectomics/` (02→12), writing `AVLP743m_skeletons.rds` fetch code first.
16. Regenerate the `combinatorial_signal_flow/data/` export as one atomic set.

**Phase 4 — republish**

17. Clean `website/ng/` of the v0.9-named scenes *before* writing the new ones, then regenerate scenes, hull meshes, shortlinks and menu pages.
18. Re-knit every `.html`/narrative artifact; do not hand-edit numbers in `README.md`, the panel narratives, or the `fig5_captions_*_v14.md` compilation — those must fall out of a rerun.

**Deliberately excluded from the sweep:** the `panel_M_p1_classification_archive/` findings (their `v0.9` claims about which DN types exist are *substantive negative results* that must be re-derived, not relabelled), `caption_audit_v8.md` (an audit trail that should keep quoting the v0.9 IDs as historical record), and `choose_mcns_dataset("cns")` at `mcns.strongest.path.hierarchical.Rmd:2104` (a workaround that needs re-testing on its own).