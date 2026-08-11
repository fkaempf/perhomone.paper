# Panel M Synthesis: Can we identify courtship-vs-aggression P1 subtypes?

## 1. Question
Given the MCNS v0.9 male connectome and our scenario-decoder (Female encounter
= ppk23+ppk25; cVA+male = DA1+ppk23; cVA+female = DA1+ppk23+ppk25), can we
partition the 45 annotated P1 subtypes (148 cells) into courtship-biased and
aggression-biased sub-populations, cross-validated against auxiliary genetic,
morphological, and wiring evidence?

## 2. Evidence summary by source

- **Agent 1 -- fru/dsx & metadata.** 45 P1 types, 148 cells. 142 cells carry
  fru_dsx labels (dsx_high / dsx_low / coexpress_high / coexpress_low / fru).
  Keyword scan over metadata flags 19/45 types as "courtship-suggesting"; **0
  types carry an aggression keyword**. Absence is an annotation gap, not a
  biological claim. (`agent01_findings.txt`, `p1_metadata_curated.csv`.)
- **Agent 2 -- downstream DNs.** Input-normalised weights onto curated
  courtship-DN (pIP10, DNa01, DNp24, vPR*) vs aggression-DN (aIPg*, aSP*, pC1x,
  aDT8) sets. Courtship output is diffuse but absolutely largest at P1_14a
  (0.029), P1_5b, P1_7b, P1_19, P1_7a. Aggression-DN coupling is numerically
  stronger per subtype: P1_9a (0.167), P1_18b (0.166), P1_7a, P1_4a, P1_7b.
  Most pure-courtship-asymmetric: P1_8a, P1_13a, P1_14b, P1_14a, P1_19.
  (`agent02_findings.txt`, `p1_dn_courtship_vs_aggression.csv`.)
- **Agent 3 -- aggression-circuit candidates.** 716 MCNS neurons match
  aggression tokens (pC1, aIPg, aDT8, Tk, dsx+). Direct type-level edges P1 ->
  aggression candidates exist but are sparse and low-weight: P1_9a -> aIPg_m1/m2
  (w=0.1), P1_4a -> aIPg5, P1_18a -> pC1x_d, P1_18b -> pC1x_b/d, P1_14a ->
  pC1x_c. (`agent03_findings.txt`, `p1_to_aggression_type_edges.csv`.)
- **Agent 4 -- input clustering.** Ward k=3 over mAL-subtype signed drive
  yields: cluster 1 (n=9, mALD3 / visual-inh; P1_9a/b, P1_10a/d, P1_13c,
  P1_15a, P1_17a/b, P1_8c); cluster 2 (n=29, mAL_m8 / ppk23-inh; contact-
  pheromone dominant pool); cluster 3 (n=3, mAL_m3b / ppk25-exc; P1_13a/b,
  P1_14b). 4 subtypes lack detectable mAL input. Average silhouette 0.440.
- **Agent 5 -- DECODER ANALYSIS: NOT PRODUCED.** No findings file written.
- **Agent 6 -- published nomenclature.** The only in-repo map is the mba
  `synonyms` field. All P1_* -> "pC1" (Lee/Rideout/Nojima); many also
  "pMP-e/pMP4". Anderson P1a/b/c and Auer pC1a-d cannot be assigned from
  metadata alone. dsx_high P1s are tagged as "fru+dsx courtship command".
- **Agent 7 -- lateral P1<->P1 architecture: FINDINGS NOT WRITTEN.** Only
  `p1_lateral_matrix.csv` exists; inspection shows the subtype-subtype
  matrix is essentially zero at type level (extremely sparse lateral
  coupling at this aggregation).
- **Agent 8 -- statistical discriminability: NOT PRODUCED.**
- **Agent 9 -- group-level test.** 20 P1 groups vs 3 scenarios. argmax
  distribution: cVA+female 14, cVA+male 4, Female encounter 2. Wilcoxon
  aggression-like vs courtship-like: all p > 0.1. K-means k=2 fails to
  recover a clean courtship/aggression split; drive vectors collapse onto a
  single contact-amplitude axis. cVA+male-argmax groups (P1_1, P1_9, P1_17,
  P1_2a/2) are tentative aggression candidates only.

## 3. Final classification table

| P1 subtype(s) | Assignment | Confidence | Evidence chain |
|---|---|---|---|
| P1_8a, P1_13a, P1_14b, P1_19 | Courtship (canonical) | High | Agent 2 courtship-asymmetry; Agent 1 fru_dsx (P1_19 dsx_high); Agent 6 pC1 |
| P1_10a-d, P1_11a/b, P1_12b, P1_13b/c, P1_18a/b | Courtship (dsx_high pC1 command) | Medium-High | Agents 1+6 converge; Agent 4 mixed mAL profiles |
| P1_14a, P1_5b, P1_7a/b | Mixed / integrator | Medium | Strong courtship-DN output (Ag2) AND strong aggression-DN output; Ag3 direct pC1x/aIPg edges |
| P1_9a/b, P1_17a/b, P1_1, P1_2a/2 | Aggression-biased (candidate) | Low-Medium | Ag9 cVA+male argmax; Ag3 direct aIPg_m1/m2 (P1_9a); Ag2 P1_9a top aggression-asym |
| P1_4a | Aggression-biased (candidate) | Low-Medium | Ag2 aggression-asym; Ag3 P1_4a -> aIPg5 direct edge |
| P1_3a-c, P1_15-16, P1_2b/c, P1_6a/b, P1_8b/c | Unresolved | Low | Conflicting or sparse evidence |

## 4. Proposed Panel M layout

- **M-A.** Summary heatmap: 45 P1 subtypes x 3 scenarios (Female, cVA+male,
  cVA+female) net drive (from `p1_group_drive_table.csv`), rows sorted by
  cVA+male bias, annotated with fru_dsx class.
- **M-B.** Dot plot of courtship-DN vs aggression-DN input-normalised weight
  per P1 subtype (source: `p1_dn_courtship_vs_aggression.csv`). Diagonal =
  mixed; off-diagonal labels the committed subtypes.
- **M-C.** Input-pattern dendrogram (k=3 clusters, `p1_input_dendrogram.png`)
  coloured by fru_dsx class, highlighting the contact- vs visual-/olfactory-
  driven partitions.
- **M-D.** Direct P1 -> aggression-circuit edges (top edges from Ag3) drawn
  on a bipartite ball-and-stick diagram; highlight P1_9a -> aIPg_m1/m2 and
  P1_4a -> aIPg5.
- **M-E.** Final classification call-out table (Section 3) overlaid on the
  scenario-decoder schematic from Panel L.

## 5. Limitations and next steps

- Five of nine agents (5, 7 partially, 8) did not emit findings, so
  decoder-level discriminability, lateral P1<->P1 architecture, and formal
  statistical tests are incomplete in this synthesis.
- MCNS `synonyms` do not propagate Anderson P1a/b/c or Auer pC1a-d labels;
  morphology-based split-GAL4 light-microscopy registration is required to
  firm up the published-name map.
- No P1 type carries an explicit aggression annotation in MCNS v0.9; all
  aggression assignments here are inferred from downstream connectivity or
  scenario argmax and should be treated as hypothesis-generating.
- Statistical power at the group level is too low (n=20 groups, n=4
  aggression-like): Wilcoxon p > 0.1 across all scenarios. Bootstrapped or
  cell-level permutation tests on the full 148-cell pool would help.
- **Needed to firm up:** in-vivo calcium imaging of candidate P1 types
  (especially P1_9a, P1_4a, P1_18b) during male- vs female-stimulus
  scenarios; genetic labelling (split-GAL4) for dsx vs fru-only P1 clades;
  optogenetic activation phenotypes to adjudicate mixed P1_14a / P1_7a/b.
