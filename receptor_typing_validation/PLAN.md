# Receptor typing: independent validation — actionable list

Status: ideas backlog, 2026-08-11. Not yet executed.

**Core problem.** Billy's receptor assignment (WG3 = ppk23+/ppk25+, WG4 = ppk23+/ppk25−,
WG1 = Ir52a+/Ir52b+, plus LgLG propagation) was derived from **downstream partner identity**
(PPN1 for WG3, mAL for WG4) plus NT prediction plus qualitative morphology. The paper's thesis
is about **valence logic downstream of those receptor types**. You cannot validate downstream
circuit logic with labels inferred from downstream circuit logic. Every task below is scored on
whether it is **independent** of that evidence.

**Current assignment as encoded** (`figures/fig5/setup.R:269-274`):

| Label in code | Meaning | Types |
|---|---|---|
| `ppk23` | ppk23+/ppk25− ("M" cells) | WG4, LgLG1a, LgLG6, LgLG7 |
| `ppk25` | ppk23+/ppk25+ ("F" cells) | WG3, LgLG1b, LgLG5, LgLG8 |
| — | Ir52a+/Ir52b+ | WG1 |
| — | unassigned | WG2 |

---

## Tier -1 — the decisive experiment: t-GRASP double dissociation ★

Everything below this section is a computational proxy. **This is the only test that touches the
actual molecule**, and the connectome hands us a target pair that makes it binary.

### The target: AN05B023b vs AN05B023c

Sensory input, from `analyses/an_investigation/data/derived/an05b023bc_input_synapses_annotated.feather`:

| target | LgLG1a | WG4 | LgLG1b | WG3 | "F"-family fraction |
|---|---:|---:|---:|---:|---:|
| AN05B023b | 6744 | 4346 | 589 | 398 | **0.08** |
| AN05B023c | 246 | 185 | 3545 | 2154 | **0.93** |

~11-fold double dissociation, holds independently in left and right bodies.

### The discriminating driver is ppk25, not ppk23

ppk25+ ⊂ ppk23+. A ppk23 driver labels M *and* F cells and hits both ANs hard. ppk25 labels F only:

- **Billy right** → ppk25 t-GRASP strong on AN05B023**c**, near-zero on **b**
- **Billy wrong (WG3↔WG4 swapped)** → strong on **b**, near-zero on **c**

Binary. Same driver, two targets, one imaging session — cancels the absolute-puncta-count
artifact that makes GRASP unquantitative.

### Free second readout: wing vs leg in the same animal

Wing types land in `Ov` (z ≈ 85,000), leg types in `LegNp(T1-T3)` (z ≈ 99,000). Score puncta by
neuropil: Ov puncta test WG3/WG4, LegNp puncta test LgLG1a/1b. Two independent answers, one
experiment.

### Third arm: AN05B102d tests the Ir52 channel

| target | WG1 | LgLG2 | LgLG1a | LgLG1b | WG3 | WG4 |
|---|---:|---:|---:|---:|---:|---:|
| AN05B102d | 2327 | 2296 | 67 | 140 | 170 | 22 |

~95% WG1/LgLG2, near-zero ppk. Cleanest single-channel target in the dataset. Ir52a and Ir52b
t-GRASP onto AN05B102d tests WG1's assignment and, if Luo 2024 is right that Ir52a and Ir52b are
separate populations, should give different puncta distributions — which would also fill the
abandoned WG2 slot (see 1.6).

### PPN1 / R56C09 is NOT the target — it is the positive control

R56C09 = PPN1 = AN05B102a (`analyses/an_investigation/R/_paths.R:54-58`), the Kallman 2015 line.
Two disqualifying problems as a *test* target:

1. **Not discriminating.** Input is LgLG1a 7951, WG4 8138, LgLG1b 5397, WG3 5701 — F-fraction
   0.41. Predicted ppk25/ppk23 ratio is 0.41 (Billy right) vs 0.59 (swapped): 1.4×, well inside
   GRASP noise.
2. **Circular.** PPN1 ← ppk23+/ppk25+ functional connectivity (Kallman 2015) is constraint C3,
   one of the three things Billy used to make the call.
3. **No spatial rescue.** Checked: WG3 and WG4 centroids on PPN1 differ by 12 units out of
   85,000 (medians x,y,z — WG3 51734/59442/84922, WG4 52036/59492/84910); LgLG1a/1b likewise.
   The only split is wing vs leg, not M vs F.

**Do use it as the positive control.** Robust puncta validates the protocol before committing to
the real target, and it validates puncta-by-neuropil scoring since PPN1 receives both Ov and
LegNp input.

### Stocks in hand

| Stock | System | Chr |
|---|---|---|
| `GMR56C09-GAL4 attP2` | GAL4 | 3 |
| `GMR56C09-lexA attP40` | LexA | 2 |
| `ppk23-Gal4.2.695` | GAL4 | 2 |
| `ppk25-GAL4.S` | GAL4 | 2 **and 3** |
| t-GRASP **A**: `20XUAS-post-tGRASP`attP2 `13XLexAop2-pre-tGRASP`VK00027 | both halves | 3 |
| t-GRASP **B**: `13XLexAop2-post-tGRASP`attP2 `20XUAS-pre-tGRASP`VK00027 | both halves | 3 |

**Use Stock B.** GRNs are presynaptic and the AN is postsynaptic, so with ppk drivers in GAL4 and
R56C09 in LexA you need **pre on the GAL4 side** — that is Stock B. Keep Stock A for later: once
ppk-LexA exists it becomes the correct orientation for any AN driver in GAL4.

**`GMR56C09-GAL4` is unusable** — it sits at attP2 and both reporter stocks put a transgene at
attP2. Same landing site, cannot coexist. R56C09-LexA only.

**No recombination is required.** ppk-GAL4(2) and R56C09-LexA(attP40, 2) sit on homologous
chromosomes; trans-heterozygous expresses fine. Same for ppk25-GAL4.S(3) versus the chr3
reporters, which also gives two GAL4 copies.

```
# Tester stock, ~3 generations, reusable for every future GAL4
   w ; R56C09-LexA(attP40) ; +                                  [homozygous]
 x y w ; wg[Sp-1]/CyO,Dfd-EYFP ; LexAop-post-tGRASP attP2, UAS-pre-tGRASP VK00027   [Stock B]
   -> select CyO non-Sp; rebalance chr2, homozygose chr3
   S1 = w ; R56C09-LexA(attP40)/CyO ; LexAop-post-tGRASP, UAS-pre-tGRASP

# Test crosses, one generation each
   S1 x w ; ppk25-GAL4.S(2) ; ppk25-GAL4.S(3)
      -> non-CyO:  w ; R56C09-LexA / ppk25-GAL4(2) ; reporters / ppk25-GAL4(3)
   S1 x w ; ppk23-Gal4.2.695(2) ; TM2/TM6B
      -> non-CyO non-TM:  w ; R56C09-LexA / ppk23-GAL4(2) ; reporters / +
```

Swap the AN05B023 LexA line into S1 when it exists and the pipeline is already built.

### PPN1 as quantitative calibration, not just a positive control

Both ppk arms are now essentially free, so run them and measure the **ratio**, which the
connectome predicts sharply:

| | ppk25-family | ppk23-family (all) | predicted ratio |
|---|---:|---:|---:|
| PPN1 whole | 11,098 | 27,187 | **0.41** |
| PPN1 Ov (wing) | 5,701 | 13,839 | **0.41** |
| PPN1 LegNp (leg) | 5,397 | 13,348 | **0.40** |

A measured ratio near 0.41 demonstrates that t-GRASP puncta track connectome synapse counts
quantitatively **in this system** — the licence needed for anyone to accept the 0.08-vs-0.93
result on AN05B023. A ratio nowhere near 0.41 means GRASP is non-quantitative here; skip to the
functional (Chrimson/GCaMP) version.

**Check the MCFO first:** does R56C09 label only AN05B102a, or also b/c/d? Predicted ratios differ
per cell (a 0.41, b 0.36, c 0.27, d 0.78). If several are labelled and morphologically separable,
that is four calibration points in one animal — a regression of puncta against connectome synapse
count. If not separable, it is a confound and the prediction must be weighted by which cells the
line actually hits.

### To order, priority order

1. **A driver for AN05B023b or AN05B023c** — now the only real bottleneck. Bodyids b = 200336 (L),
   801269 (R); c = 18430 (L), 18696 (R). GABAergic, hemilineage 05B, ascending. Route: NBLAST
   the EM skeletons against FlyLight Gen1 GAL4 and the split-GAL4 collections; the Janelia VNC
   split-GAL4 collection is indexed by hemilineage, so 05B should be covered. A **LexA** version
   drops straight into S1; a GAL4 version needs Stock A plus a ppk-LexA.
2. **ppk23-LexA and ppk25-LexA** — strategic. Moving the ppk side to LexA once makes every future
   AN driver in GAL4 usable (with Stock A). Likely source: Scott lab (Kallman/Thistle).
3. **Ir52a and Ir52b drivers** for the AN05B102d arm.

t-GRASP reporters are no longer needed — both orientations are already in hand.

### Controls

- Half-reporter-only in each genotype (no reconstitution).
- Apposition false-positive control: a connectome-predicted-zero pair with overlapping arbors.
- Positive control: ppk × R56C09-LexA (see above).
- Males only — dimorphic circuit, and the bilateral T1 GRNs are male-specific.
- n ≈ 10–15 VNCs per genotype, automated puncta segmentation, counted blind to genotype.
- **Pre-register the prediction.** Table the connectome numbers before running flies. On a
  contested assignment a pre-stated direction is worth a great deal at review.

### Stronger confirmation if affordable

CsChrimson in ppk25 cells + GCaMP in AN05B023b vs c. Functional rather than anatomical, and
Kallman 2015 established the method in this exact system. t-GRASP is apposition-biased even in
its targeted form. Do GRASP first, functional as confirmation.

---

## Tier 0 — draft errors, fix regardless (minutes)

### 0.1 WG4 ↔ LgLG1a, not LgLG1b
Results text says WG3 co-clusters with LgLG1b, then two sentences later says WG4 co-clusters
with LgLG1b. `setup.R:269` has WG4 → LgLG1a. Typo in the load-bearing sentence. Fix in
manuscript + Methods (same sentence is duplicated verbatim in Methods and Billy's draft).

### 0.2 WG1 vs WG2 swap
Results: "relative positioning of **WG1** with respect to WG3 and WG4". Methods: "relative
positioning of **WG2** with reference to WG3 and WG4". Otherwise verbatim-identical paragraph.
Decide which, fix both.

### 0.3 Audit `set_ppk25_glutamate = TRUE`
`setup.R:95` overrides NT for the ppk25 group. Document exactly what it does and why, or a
reviewer will read it as circular data massaging. Check `R/data_processing.R`.

---

## Tier 1 — cheap, fully independent, do first

Each of these uses **zero downstream connectivity**. If any fails, the assignment is dead and
you want to know now.

### 1.1 Bristle-slot test (strongest single anatomical test)
**Claim to test:** WG1–4 are the 4 co-housed neurons of each wing-margin taste bristle
(molecular partition), not 4 spatial groups (topographic partition).

**Arithmetic already supports it:** 4 types × ~48/side ≈ 192/side; ~40–48 margin bristles ×
4 chemosensory neurons/bristle = same number. Total 385 ≈ 2 × 192.

**Steps**
1. Pull all ADMN sensory axons in mCNS, get entry-point coordinates where the axon crosses
   the ADMN nerve boundary (or first skeleton node inside the VNC).
2. Cluster entry points into fascicles/bundles — expect ~48 tight groups per side.
3. Cross-tabulate: group × WG type.

**Decision rule**
- Every group contains exactly one WG1, one WG2, one WG3, one WG4 → per-bristle-slot
  partition, i.e. molecular. Assignment framework is sound; go find *which* label goes where.
- Groups are homogeneous (all WG3, all WG4, …) → partition is positional. Receptor mapping is
  unfounded and must be dropped.
- Mixed/no structure → inconclusive, entry-point resolution too coarse.

**Cost:** low, EM geometry only. **Independence:** total.

### 1.2 Calibrate the NT classifier on sensory neurons
**Claim to test:** "glutamate ⇒ ppk23+/ppk25+" is the single point of failure for the whole
assignment, and it assumes the NT predictor works on sensory axons. Predictor was trained
largely on central neurons; GRN axons may be out of distribution.

**Steps**
1. Assemble GRNs of *known* NT from literature: Gr64f sugar (ACh), Gr66a bitter (ACh),
   ppk28 water, bristle mechanosensory (ACh).
2. Pull their predicted NT + prediction confidence from `mba`.
3. Report accuracy and confidence distribution **restricted to sensory neurons**.
4. Separately: for WG1–4 and each LgLG type, report the *distribution* of per-neuron NT calls
   and confidences, not just the argmax label.

**Decision rule** — if sensory-neuron accuracy is poor, or WG3's glutamate call is 55% weak
rather than 95% confident, the NT leg of the argument cannot carry the assignment. Say so.

**Cost:** low. **Independence:** total.

### 1.3 Count matching against light microscopy
**Claim to test:** ppk25+ cells are a subset of ppk23+ cells, so the numbers must add up.

Predictions:
- `|WG3|` = N(ppk25-GAL4 wing cells)
- `|WG3| + |WG4|` = N(ppk23-GAL4 wing cells)
- `|WG1|` (+ `|WG2|` if 1.6 holds) = N(Ir52a/Ir52b wing cells)
- Same arithmetic per leg segment for LgLG types, using T1/T2/T3 counts.

**Steps** — pull counts per type per entry nerve from mCNS (Fig 1C already plots this; make it
a quantitative test rather than a picture). Get LM counts from He 2019, Thistle 2012,
Toda 2012, Luo 2024, plus your own/Bella's images.

**Decision rule** — a 2× mismatch kills the mapping. Falsifiable arithmetic.

**Cost:** low. **Independence:** total.

### 1.4 Clustering stability / robustness
**Claim to test:** the wing↔leg 1:1 pairing that carries the LgLG assignments is stable.

**Steps** — resample neurons and synapses; vary distance (euclidean vs cosine), linkage (ward
vs average vs complete), input transform (raw counts / normalised / binary / sqrt). Count how
often WG3 pairs with LgLG1b vs LgLG1a across the ensemble.

Add a null model: given 4 wing groups and N leg groups, what is the chance of a 1:1 matching
this clean?

**Decision rule** — if the pairing flips under reasonable perturbation, the LgLG assignments
are unsupported and only the wing types can be labelled.

**Cost:** low. **Independence:** partial — same evidence channel, but tests whether that
channel is even reliable.

### 1.5 Measure the "hole"
"A small hole in the axonal terminals is present" is currently an eyeball claim used to link
WG3/WG4 to ppk23+ GAL4 images. Make it a number: terminal mesh topology (genus), or a 2D
density projection with automated void detection, with a per-neuron score. Compare all WG and
LgLG types so the reader sees WG3/WG4 stand out (or don't).

**Cost:** low-medium. **Independence:** total.

### 1.6 WG1 *and* WG2 = Ir52a and Ir52b, separately
**Claim to test:** the draft treats "Ir52a+/Ir52b+" as one co-expressing type and then abandons
WG2. Luo, Talross & Carlson 2024 indicate Ir52a and Ir52b label largely distinct neurons with
different projections (both reaching vAB3). If so, WG2 is not a mystery — it's the other half.

**Steps** — compare WG1 vs WG2 axon terminal position along the anterior–posterior margin axis
against He 2019 Ir52a images and Luo 2024 Ir52a/Ir52b anatomy; check whether both reach vAB3;
compare NT and counts.

**Decision rule** — if WG1 and WG2 both reach vAB3 with distinct terminals, assign Ir52a and
Ir52b separately and close the gap in the partition.

**Cost:** low. **Independence:** high (uses published anatomy, not your connectivity clusters).

### 1.7 Is one of WG1–4 mechanosensory?
Taste bristles house chemosensory neurons **plus one mechanosensory** neuron. If a WG type is
actually the bristle mechanoreceptor, its receptor assignment is meaningless and it contaminates
the valence analysis. Check terminal depth/layer, overlap with known bristle-mechano VNC
interneuron targets, and whether it responds to the bristle-slot test differently.

**Cost:** low. **Independence:** high.

---

## Tier 2 — held-out prediction tests (break the circularity properly)

### 2.1 cVA convergence test ★ best evidence-per-hour
**Logic:** M cells respond to 7-T **and cVA** (Thistle 2012; the manuscript states this).
Volatile cVA arrives via Or67d → DA1. So the true M-cell contact type must show the strongest
downstream convergence with DA1 of any contact type. **This was not used to make Billy's call
— genuinely held out.**

**Steps** — you already have DA1/VA1v/VA1d channels wired up (`setup.R:123`). Compute
downstream-target overlap (and shared-path weight) for each contact type × each volatile
channel. Rank.

**Decision rule** — WG4/LgLG1a (current "M") should top the DA1 convergence ranking. If WG3
tops it instead, the assignment is swapped.

**Cost:** low, existing machinery. **Independence:** high.

### 2.2 Sexual dimorphism as discriminator
**Logic:** ppk23+ leg GRN midline crossing in T1 is male-specific and *fru*-dependent
(Mellert 2010). Independent of any connectivity clustering.

**Steps** — compare mCNS (male) leg GRNs against FANC and/or BANC (female) leg GRNs. Identify
which types have the bilateral T1 projection in male and lack it in female. Also compare
per-type counts across sexes — ppk23+ number is dimorphic.

**Decision rule** — types with male-only midline crossing are the *fru*+ ppk23+ populations.
Note the draft already assigns bilateral types LgLG5–8 by NT alone; this test is a real check
on that.

**Cost:** medium (cross-dataset). **Independence:** total.

### 2.3 Wing-margin topographic map
**Logic:** He 2019 shows Ir52a restricted to the anterior wing margin. If axon entry order along
the ADMN preserves margin position, you can read receptor identity off position directly.

**Steps** — order axon entry points along the nerve, test for a monotonic map to margin
position (use bristle groups from 1.1), then compare the WG1/WG2 distribution to published
Ir52a/ppk23 co-expression images.

**Cost:** medium. **Independence:** total.

### 2.4 Cross-connectome replication (BANC / FANC)
Two more independent specimens and independent segmentation+proofreading pipelines. Does the
4-type wing partition reproduce? Does the wing↔leg 1:1 pairing reproduce? Sex differs, so treat
dimorphic features (2.2) as signal rather than noise.

**Cost:** medium-high. **Independence:** high.

### 2.5 Multi-hop retyping (coconatfly PR #59)
**Caveat first:** multi-hop *deepens* the downstream-connectivity channel. It makes the
assignment more robust, **not more independent**. Do not use it to break circularity.

**Valid uses**
- Test whether the wing↔leg pairing survives at 2-hop and 3-hop (complements 1.4).
- One-hop VNC partner identity is heavily shaped by axon terminal position — neighbouring
  axons contact the same local interneurons. Multi-hop reaches through topography to
  functionally-defined targets (mAL, P1, pC1, PPN1) where the literature gives ground truth.

**Cost:** medium. **Independence:** low — label it honestly.

---

## Tier 3 — the framework: assignment as constrained model selection

### 3.1 Enumerate and score all permutations
Replace the narrative with a posterior. The space is small — 4 wing types × 3–4 candidate
labels. Enumerate every permutation, score each against a constraint set, report the ranking.

**Constraint set** (each independently sourced):

| # | Constraint | Source | Currently used by Billy? |
|---|---|---|---|
| C1 | M channel → mAL (GABA) → inhibits P1 | Kallman 2015; Clowney 2015 | **yes** |
| C2 | F channel net-excites P1 | Thistle 2012; Kallman 2015 | no |
| C3 | PPN1 downstream of ppk23+/ppk25+ | Kallman 2015 | **yes** |
| C4 | Gr32a/7-T channel reaches aggression nodes (pC1) | Wang 2011 | no |
| C5 | Gustatory dominant to olfactory | Wang 2011 | no |
| C6 | cVA detected by taste as well as smell | Thistle 2012 | no |
| C7 | Ir52a ≠ Ir52b cells, distinct projections, both → vAB3 | Luo 2024 | no |
| C8 | ppk23+ T1 midline crossing male-specific, *fru*-dependent | Mellert 2010 | partly |
| C9 | Glutamate in ppk23+/ppk25+ | Kallman 2015 | **yes** |

**Method** — fit on {C1, C3, C9} (Billy's evidence), test on {C2, C4, C5, C6, C7, C8}. Report
how many held-out constraints each permutation satisfies.

**Why this is publishable either way** — "permutation X is excluded by held-out constraints" is
a result. A ranked posterior is more defensible than a narrative, and it makes the confidence
tiers in Tier 4 quantitative rather than vibes.

**Cost:** medium, but mostly reuses 1.x and 2.x outputs.

---

## Tier 4 — manuscript framing (do this whatever the analysis says)

### 4.1 Keep the paper on connectome type names
Already started — `analyses/an_investigation/R/_paths.R:64` says the receptor call is "a
light-level call from Fig 1 and is not used here". Extend that discipline to Figs 5/6 and the
text. Real type names: WG3, WG4, LgLG1a, LgLG1b, LgLG5–8. Receptor identity becomes a labelled
overlay, not the load-bearing wall.

### 4.2 Evidence table with confidence tiers
Supplementary table: rows = cell types, columns = evidence channels (NT, morphology, counts,
bristle slot, dimorphism, topography, downstream, cross-connectome), entries =
supports / contradicts / neutral / untested, plus an overall confidence tier. Reviewers cannot
kill the paper by killing one channel.

### 4.3 Swap robustness pass
Force the WG3↔WG4 swap, rerun every Fig 5 / Fig 6 downstream conclusion, report which survive.
Turns a trust problem into a robustness statement. Cheap and it pre-empts the obvious attack.

---

## Tier 5 — the angle Greg is pointing at

The four papers Greg sent all have the same shape: **a complete channel inventory (receptor /
neuron / ligand / behaviour) plus a rule for how channels interact.** Not a mechanism for one
cell.

- Wang & Anderson 2010, Nature 463:227 — cVA → Or67d OSN → aggression.
  [10.1038/nature08678](https://doi.org/10.1038/nature08678)
- Wang et al. 2011, Nat Neurosci 14:757 — 7-T/Gr32a and cVA/Or67d are **hierarchical**,
  gustatory dominant to olfactory; one pheromone drives aggression and courtship-suppression via
  *independent* mechanisms. [10.1038/nn.2800](https://doi.org/10.1038/nn.2800)
- Dweck et al. 2015, PNAS 112:E2829 — Or47b/Or88a deorphanized (methyl laurate/myristate/
  palmitate); two dedicated lines to higher brain; Or47b = male copulation advantage, Or88a =
  attraction in both sexes. [10.1073/pnas.1504527112](https://doi.org/10.1073/pnas.1504527112)
- van der Goes van Naters & Carlson 2007, Curr Biol 17:606 — **Table 1**, systematic sensillum ×
  fly-odour response matrix. [10.1016/j.cub.2007.02.043](https://doi.org/10.1016/j.cub.2007.02.043)

(Metadata retrieved from PubMed.)

### 5.1 Part 1 — the connectome Table 1
Build the connectome-side analogue of van der Goes van Naters Table 1. Rows = every pheromone
channel. Columns = ligand (literature), receptor + confidence tier, entry nerve, first-order
target, ascending route, brain convergence node, sex-specificity.

Volatile side is solid: Or67d/DA1 (Kurtovic 2007; Wang 2010), Or47b/VA1v and Or88a/VA1d
(Dweck 2015) all have ligand *and* behaviour nailed down. Contact side gets explicit confidence
tiers. The asymmetry is honest and visible, and it justifies Tier 4.1.

### 5.2 Part 2 — the hierarchy rule ★ the actual headline
Wang 2011's hierarchy (gustatory dominant to olfactory) is the most connectome-testable claim in
that literature and **nobody has the anatomical substrate.**

Predictions to test:
- Contact channels reach P1/pC1 with shorter path length and/or higher weight than volatile
  channels.
- Contact touches the volatile pathway with inhibitory sign, upstream of the decision node.
- mAL is GABAergic and receives both.

**Your existing Fig 5 result — mAL subtypes preferentially relaying multimodal sensory
information — is already the substrate of the Wang hierarchy.** Reframing it that way moves it
from descriptive to explanatory.

**Why this is the safe headline:** the hierarchy rule does not depend on which contact type is
which. "Contact dominates volatile at mAL" survives a WG3↔WG4 swap (4.3 proves it). Billy's
assignment becomes an annotation on a table rather than the foundation of the paper.

### 5.3 Optional — name channels by tuning, not receptor gene
"male-pheromone channel" / "female-pheromone channel" / "Ir52 channel". Functional class is what
the paper's argument actually needs; the gene name is what a single reviewer can kill.

---

## Suggested order

1. Tier 0 (minutes)
2. 1.2 NT calibration, 1.3 counts, 1.4 stability — all cheap, any failure changes everything
3. 1.1 bristle-slot test — highest information
4. 2.1 cVA convergence — best evidence-per-hour of the held-out tests
5. 1.6, 1.7, 1.5
6. 2.2 dimorphism, 2.3 topography
7. 3.1 permutation scoring, assembled from the above
8. 2.4 cross-connectome only if 1.x/2.x leave real ambiguity
9. Tier 4 + Tier 5 framing in parallel with all of it
