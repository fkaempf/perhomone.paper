# Crossing scheme — adversarial review synthesis

Workflow `wf_6a789d35-7c9`, 11 agents, 2026-08-11. Verbatim synthesis output.

**Correction applied after this ran:** the synthesis states neither ppk-LexA is
orderable. The lab holds `ppk23-LexA` from the Dickson lab (GJ1472 / Janelia DG78,
Bella, 25inc) — see REAGENTS.md. Only `ppk25-LexA` must be built.

---

# t-GRASP validation of the ppk25 receptor assignment — recommended plan

*Synthesis of three crossing schemes and four adversarial reviews. Senior-scientist call, 2026-08-11.*

---

## 1. VERDICT

**Yes, with changes — but not the experiment as designed, and not first.** All three proposed schemes are built on a between-target contrast (AN05B023c vs IN01B065) that is provably blind to the hypothesis the team actually holds: the reviewers are correct that the live alternatives are not "global swap" but "wing call right / leg propagation wrong" (H2) and "wing call wrong / leg right" (H3), and against H3 the proposed primary contrast has a predicted separation of ~1.6-fold against a detection floor of ~2-fold. That objection is fatal and it changes the plan. However, the fix is already sitting in the repo's own `receptor_typing_validation/PLAN.md`: **AN05B023b vs AN05B023c, scored separately in Ov and LegNp**. That configuration yields two statistics — a wing statistic and a leg statistic — each of which is a *within-compartment, between-target* ratio-of-ratios in which the driver-efficiency constant *k* cancels **exactly** (same GRN population, same compartment, same two drivers), and each of which **flips sign** between the two relevant hypotheses with ~2.1 log₁₀ units of separation. This simultaneously answers the "H1 is a straw man" objection, the "compartment contrast does not cancel k" objection, and the "zero-inflation" objection (the smallest predicted true signal is ~400 synapses on a 2-cell arbor, not ~3 synapses on a 20-cell arbor). What does **not** survive review is the eight-type identification: rank-8 / κ=2.5 D-optimality is invalid once *k* and the saturation exponent γ are unknown, and it must be deleted from all documents. And one objection is genuinely upstream of everything: the denominator of R_j assumes that the ppk drivers label exactly the eight assigned types and nothing else — 417 GRN cells in five types have no receptor call at all, and four of the eight assigned types have no molecular support for being ppk23⁺. **That must be measured before the GRASP is interpretable, it is cheaper than the GRASP, and if it succeeds it partly answers the question outright.** Hence: driver-mapping first, GRASP second, and the two run in parallel because the GRASP reagents take 12 weeks to build regardless.

---

## 2. THE RECOMMENDED SCHEME

### 2.0 The design in one paragraph

Two targets (**AN05B023b**, **AN05B023c**), two GRN drivers (**ppk23**, **ppk25**), two neuropil compartments (**Ov**, **LegNp T1–T3**), scored within animal inside an anti-ICAM5 mask. Four genotypes, eight measurement cells, one block per animal-quartet. From the repo's own input table (`an05b023bc_input_synapses_annotated.feather`):

| | LgLG1a | WG4 | LgLG1b | WG3 |
|---|---:|---:|---:|---:|
| AN05B023b | 6744 | 4346 | 589 | 398 |
| AN05B023c | 246 | 185 | 3545 | 2154 |

Predicted ppk25⁺ fraction per (target × compartment), under the four hypotheses (H0 = published; H1 = global swap; H2 = leg swapped only; H3 = wing swapped only):

| | R(Ov) H0 | R(Ov) swapped | R(Leg) H0 | R(Leg) swapped |
|---|---:|---:|---:|---:|
| AN05B023b | 0.084 | 0.916 | 0.080 | 0.920 |
| AN05B023c | 0.921 | 0.079 | 0.935 | 0.065 |

**The two estimators:**

```
W = [log Y(ppk25, c, Ov)  − log Y(ppk23, c, Ov) ]
  − [log Y(ppk25, b, Ov)  − log Y(ppk23, b, Ov) ]        →  log10(R_c,Ov / R_b,Ov)

L = [log Y(ppk25, c, Leg) − log Y(ppk23, c, Leg)]
  − [log Y(ppk25, b, Leg) − log Y(ppk23, b, Leg)]        →  log10(R_c,Leg / R_b,Leg)
```

| statistic | wing call right | wing call wrong |
|---|---:|---:|
| **W** | **+1.04** | **−1.06** |

| statistic | leg call right | leg call wrong |
|---|---:|---:|
| **L** | **+1.07** | **−1.15** |

`sign(W)` and `sign(L)` are **two independent binary readouts** whose pair maps one-to-one onto {H0, H1, H2, H3}. `k_Ov` cancels inside W; `k_Leg` cancels inside L; the two are never compared to each other. This is the single change that rescues the project, and it is not in any of the three submitted designs.

*(Note: I computed these from the four dominant types only. Gate 0 must recompute with the full ROI-resolved C matrix including LgLG5–8; the method reviewer's ROI-resolved figures were larger, i.e. more favourable. I quote the conservative version.)*

### 2.1 Final genotypes

**Architecture: GRN driver = LexA, target = split-GAL4, pre-half = LexAop, post-half = UAS.** This is forced — the target drivers for AN05B023b/c exist only as split-GAL4, so the GRN drivers must be LexA, and neither ppk-LexA is orderable.

**Experimental male, ppk25 arm:**
```
w[1118] P{ppk25-LexA::p65}su(Hw)attP8 / Y ;
  P{20XUAS-post-t-GRASP}VK00037 / P{y[+t7.7] w[+mC]=SS<n>-p65ADZp}attP40 ;
  PBac{13XLexAop2-pre-t-GRASP}VK00027 / P{y[+t7.7] w[+mC]=SS<n>-ZpGAL4DBD}attP2
```

**Experimental male, ppk23 arm:** identical, `P{ppk23-LexA::p65}su(Hw)attP8` on the X.

Chromosome allocation, one copy of everything, nothing recombined in the final cross:

| Chr | element | site | cytology |
|---|---|---|---|
| X | ppk23- **or** ppk25-LexA::p65 | su(Hw)attP8 | X:8E10 |
| 2 | 20XUAS-post-t-GRASP (**new integration**) | VK00037 | 2L 22A3 |
| 2 | SS line p65ADZp | attP40 | 2L 25C6 |
| 3 | 13XLexAop2-pre-t-GRASP | VK00027 | 3R 89E11 |
| 3 | SS line ZpGAL4DBD | attP2 | 3L 68A4 |

**Why UAS-post is re-integrated at VK00037 and not left at attP2.** The *pragmatic* review is right that attP2⊗attP2 in trans is genetically legal — but the *genetics* reviewer is right that it is scientifically unsafe. Mellert & Truman 2012 (*Genetics* 191:1129) showed transvection between transgenes paired at attP2 in larval VNC, specifically that GAL4 bound to a UAS array in trans to a functional promoter drives pairing-dependent trans-activation. That would express the post half — and therefore the ICAM5 mask — outside the split pattern, by a target-specific amount, aliasing directly onto the between-target contrast that carries all the information. One injection removes it. This is the *only* new transgene the architecture strictly needs; the two ppk-LexA constructs are needed because the reagent does not exist.

**Honest statement about *k*.** I do **not** claim that building both LexA drivers at the same landing site makes *k* a matched constant — the genetics reviewer is correct that `ppk23-LexA` (2.695 kb enhancer fragment, `pBPLexA::p65Uw`) and `ppk25-LexA` (Starostina genomic gene-fusion, start codon mutated) are different construct classes and *k* remains unknown. The design does not need *k* to be known or matched: W and L cancel it exactly. We measure it anyway (see §3, Control 4) to put an informative prior on it and to bound *k_Ov/k_Leg* for the exploratory analyses.

### 2.2 Stable reagent stocks to build first

Build once; every subsequent target costs **one cross with zero marker selection**.

```
P23:  w[1118] P{ppk23-LexA::p65}su(Hw)attP8 ; P{20XUAS-post-t-GRASP}VK00037 ; PBac{13XLexAop2-pre-t-GRASP}VK00027
P25:  w[1118] P{ppk25-LexA::p65}su(Hw)attP8 ; P{20XUAS-post-t-GRASP}VK00037 ; PBac{13XLexAop2-pre-t-GRASP}VK00027
```
Both homozygous on X, II and III; no GAL4 present so UAS-post is silent; self-propagating.

Control platforms (they are assembly intermediates — balance and keep them, they cost nothing):
```
P25-ΔPre     w ppk25-LexA[attP8] ; UAS-post[VK37] ; +
P25-ΔPost    w ppk25-LexA[attP8] ; +              ; LexAop-pre[VK27]
P23-ΔPre / P23-ΔPost   as above
P-ΔDriver    w[1118]              ; UAS-post[VK37] ; LexAop-pre[VK27]
```

Both platforms must be built in **one** isogenic `w[1118]` host and backcrossed ≥5 generations together, so the two X chromosomes are isogenic except for the transgene. This is the only defence against the genetics reviewer's objection 7 (X provenance differs between arms), and here it is unavoidable-by-design because the driver *is* the X.

### 2.3 Generation-by-generation crosses

**Build A — separate `LexAop-pre`@VK00027 from `UAS-post`@attP2** (skip entirely if Stowers supplies singles; ask in week 0). attP2 = 3L 68A4, VK00027 = 3R 89E11 — opposite arms, recombinants common.

| Gen | Cross | Select | Note |
|---|---|---|---|
| G0 | ♀ BDSC 79039 × ♂ `w1118` | F1 ♀ **Sb⁻ Tb⁻ Sp⁻** | `; +/CyO or +/+ ; [post,pre]/+` — recombination in these females |
| G1 | ♀ G0 × ♂ `w; TM3, Sb Ser / TM6B, Tb Hu` | — | **not MKRS** — MKRS is not a balancer and gives no protection at 89E11 (genetics reviewer obj. 11, correct) |
| G2 | single ♂ `chr3*/TM6B` (**Hu⁺ Sb⁻**) × ♀ `w; TM3,Sb/TM6B,Tb Hu` | ≥24 independent single-male lines | |
| G3 | — | **PCR**: `13XLexAop2→cac` junction (+), `20XUAS→Icam5` junction (−) | both elements are `w+`; eye colour is useless |

→ `w; ; PBac{13XLexAop2-pre-t-GRASP}VK00027 / TM6B`. **3 generations ≈ 6 weeks.**

**Build B — platform assembly (identical for P23 and P25).** Inputs: **A** = `w; UAS-post[VK37]/CyO` (from injection); **B** = Build A output; **C** = `w ppk-LexA[attP8]` (from injection, X); **D** = `w; Sp/CyO; TM3,Sb/TM6B,Tb Hu`.

| Gen | Cross | Select on |
|---|---|---|
| G1 | ♀ **A** × ♂ **D** | ♂ **Cy, Sb, Sp⁻, Hu⁻** → `w; post/CyO; TM3,Sb/+` |
| G2 | ♂ G1 × ♀ **B** | ♂ **Cy, Hu⁻ Tb⁻, Sb** → `w; post/CyO; pre/TM3,Sb` (the only non-TM6B maternal third is `pre`) |
| G3 | ♂ G2 × ♀ **C** (X-homozygous) | **Cy, Sb**; all F3 carry the X driver |
| G4 | G3 sib intercross | ♂ **Cy, Sb**; PCR-verify the X transgene — do **not** score mini-white (genetics obj. 12, correct: an X-linked mini-white is invisible against 2 segregating autosomal `w+` transgenes) |
| G5 | intercross | **non-Cy, non-Sb** = `post/post ; pre/pre` |
| G6 | expand + verify | PCR all three elements; test-cross to `13XLexAop2-myr::GFP` and `20XUAS-myr::GFP` |

**6 generations ≈ 12 weeks**, both platforms in parallel.

**The experimental cross — one generation, no marker selection.**
```
G0   ♀ P23  (or P25), 10 virgins   ×   ♂ SS<n>  w; AD[attP40]; DBD[attP2],  5 males
     25.0 ± 0.5 °C, 60% RH, 12:12 LD, ≤60 larvae/vial
F1   collect MALES within 8 h of eclosion, group-house 10/vial, age 5–7 d, dissect ZT2–6
     → every F1 male is the genotype in §2.1. Nothing to score. No mis-genotyping possible.
```

**Track 1 (driver mapping) crosses** — trivial, run from week 1:
```
T1a  ♂ BDSC 93026 (ppk23-GAL4) × ♀ UAS-myr::GFP        → soma counts, wing margin + T1–T3 legs
T1b  ♂ BDSC 93028 (ppk25-GAL4) × ♀ UAS-myr::GFP        → same
T1c  hs-FLP; MCFO × ppk23-GAL4  and  × ppk25-GAL4      → single GRN axons, VNC, registered to mCNS
T1d  (week ~16, after injections) ppk23-LexA > LexAop-tdTom  +  ppk25-GAL4 > UAS-myr::GFP
     → subset relation, cell-by-cell; and per-compartment terminal-volume coverage ratio
```

### 2.4 Timeline (2 weeks/generation, 25 °C)

| Week | Critical path | Parallel |
|---|---|---|
| **0** | **GATE 0** — the whole computational package (§8). Design and order the 3 constructs. Order all stocks. Send the five emails (§7). Search the Janelia GMR-**lexA** catalogue for any fragment hitting AN05B023b/c/AN13B002/IN05B002 — a hit would remove one or two injections. | — |
| 1–4 | Clone + sequence-verify; submit to injection (BestGene/GenetiVision) | **Track 1a/1b**: ppk23- and ppk25-GAL4 > myr::GFP. Count GFP⁺ somata per wing margin and per foreleg. Compare with mCNS cell counts of the assigned 8-type set. |
| 4–10 | Injection → transformants → balancing (outsourced) | **Build A** (3 gens). **Track 1c**: MCFO on both drivers, register to JRC2018_VNC_MALE, match single axons to mCNS type skeletons. Request SS lines from Janelia. |
| 10–12 | Transformants in hand, homozygosed | **GATE 1 decision** (§6). Pilot Phase-1 assay development on `ppk23-GAL4 × R56C09-lexA × BDSC 79040` — antibodies, segmentation, background *b_j*, **and the σ pilot at n = 20**. |
| 12–24 | **Build B**, both platforms, 6 gens | **GATE 2**: ppk-LexA vs ppk-GAL4 concordance (Track 1d). Characterise SS02541 / SS90856 / SS29574 in-house by MCFO; **recompute R over the actually-labelled cell set**. |
| 24–26 | Experimental crosses P23/P25 × SS lines; age 5–7 d | Pre-register on OSF (frozen script, frozen segmentation parameters, predicted signs of W and L) |
| 26–34 | Primary data: 15 blocks × 4 genotypes = 60 VNCs, plus controls (~35) | Dose and temperature arms; age arm (3 d vs 10 d) |
| 34–38 | Analysis, unblinding, replication cohort with second SS line per target | |

**First interpretable Track-1 data: week 6. GATE 1 decision: week 12. Primary GRASP answer: week 34 (~8 months).** With realistic contingency, 10 months. Note that weeks 0–24 contain *no GRASP data collection at all* — they are covered by Track 1, which is the arm most likely to make the GRASP unnecessary.

### 2.5 Target order and the decision rule

**Target 1 and 2 are run together, not sequentially. They are the experiment.**

1. **AN05B023c** — SS02541 (Omnibus, rank 1, 1299 px, near-clean), with **SS90856** (published Drivers collection, more likely orderable) as the replication line. Wing 2339 / leg 3791 ppk synapses — both compartments well-populated. `C[j,i] = 0` (no reverse edge), so the reciprocal-polarity control is a true zero here.
2. **AN05B023b** — SS29574 (Omnibus). Wing 4744 / leg 7333. Hemilineage-matched, transmitter-matched (both GABAergic 05B), 2 bodies each, 70–92% of total input is ppk — so both the saturation exponent γ and the additive background *b* are matched between the two targets by construction, which is what the transfer-function objection demands.
3. **AN05B102a / PPN1 via SS40650 or R56C09-LexA** — assay development and the σ pilot only. **Pre-register that it yields no hypothesis inference**: with one driver pattern and pooled scoring, *k* does not cancel and the information content about H0/H1/H2/H3 is exactly zero (stats reviewer obj. 12, correct). Its value is σ, *b_j*, antibody validation, and testing whether per-arbor ICAM5 segmentation works.

**Demoted, with reasons:**
- **IN01B065** — 14 of 17 bodies have R = 0.000; the ppk25 arm's true signal is ~64 synapses over 20 cells (~3/cell), at or below any plausible floor; and it gives poor separation against H3. Not a primary target.
- **INXXX044** — **drop entirely.** Its two homologous cells give R = 0.104 and 0.981 (L/R split 0.342 vs 0.981 on a 7.8:1 synapse imbalance, i.e. almost certainly incomplete reconstruction on the left), and only 1.0% of its total input is ppk. The prediction spans the entire hypothesis space.
- **IN05B002** — 17,708 reverse synapses (target → ppk GRNs), 48% of the ppk↔IN05B002 traffic. Reverse-polarity contamination is not hypothetical there, and it breaks the reciprocal control.
- **AN09B017a–g** — vAB3 is the whole family (FBbt_00110852); family bleed is structural; pooled R ≈ 0.45 vs 0.55.
- **AN13B002** — no driver exists (Shiu 2022 report Dandelion returned no split matches). Also 16,003 synapses from *unassigned* GRN types vs 6,477 from assigned ones.

**Decision rule for continuing past the primary pair.** Compute `sign(W)` and `sign(L)` with their permutation CIs. If both are unambiguous, **stop and write it up** — you have independently tested the wing call and the leg call, which is the entire question. Add further targets only if (a) one of W or L is ambiguous (|estimate| < 2×SE), in which case add a second target pair loading on the ambiguous compartment, or (b) a reviewer demands replication, in which case use the second SS line per target, not a new target.

---

## 3. CONTROLS THAT SURVIVED REVIEW

| # | Control | Genotype / manipulation | Objection it answers |
|---|---|---|---|
| **1** | **Driver mapping (Track 1)** — soma counts on wing margin and foreleg for both drivers vs mCNS cell counts of the assigned 8-type set; MCFO single-axon type-matching | 93026/93028 × myr::GFP; MCFO | **Method obj. 3 (FATAL): the denominator of R_j is untested.** 417 GRN cells in five types have no receptor call; four assigned types (LgLG5–8) have no molecular support. If ppk23-GAL4 labels ~2× the predicted cell number, the denominator is wrong and the GRASP is uninterpretable. **This is a gate, not a control.** |
| **2** | **Half-only controls, per target, per batch** — P25-ΔPre, P25-ΔPost, P-ΔDriver, and platform × **empty split** (`p65ADZp`attP40 / `ZpGAL4DBD`attP2) | 4 crosses | **Stats obj. 5 (SERIOUS): "sign survives monotone saturation" is false with target-dependent additive background.** *b_j* must be a free per-target parameter estimated from the matched no-driver control **at that same target in the same block**, not pooled. Admissibility criterion: `b̂_j / f̂(1)_j < 0.1`, pre-registered. |
| **3** | **Zero-ppk VNC compartment, within animal, within cell** — abdominal ganglion / mVAC, verified `C = 0` from mCNS for AN05B023b/c | free | **Method obj. 10 (SERIOUS): the brain arbor is NOT a clean negative.** ppk23-GAL4 labels labellar GRNs → SEZ; ppk25-GAL4 labels antennal ORNs → VA1v/VL2a. The two arms have *different* brain floors. Use a VNC compartment instead. |
| **4** | **Two-colour driver coverage** — ppk23-LexA > tdTom + ppk25-GAL4 > GFP, same animal, per compartment; report the ratio-of-ratios (ppk25/ppk23 in Ov ÷ ppk25/ppk23 in LegNp) | Track 1d | Directly estimates **k_Ov/k_Leg**, and tests the genetic premise ppk25⁺ ⊂ ppk23⁺ cell by cell. Answers **stats obj. 2** and **genetics obj. 4** — but note the primary estimators W and L do not need it; this is an informative prior for the exploratory model and a hard test of GATE 2. |
| **5** | **Dose titration** — 1× vs 2× t-GRASP copy number, *and* 21/25/29 °C rearing, at AN05B023c | 2 extra crosses | **Method obj. 11 / inference obj. 3 (SERIOUS): saturation exponent γ.** Shearin attributes every observed t-GRASP false positive to driver strength. If W and L are invariant across a 2× dose change, signal is not overexpression-driven and γ is near 1. If they move, only the sign is reportable, and γ is measured, not assumed. **This is also where γ comes from for the power recalculation.** |
| **6** | **Reciprocal polarity** — swap in a `20XUAS-pre` / `13XLexAop2-post` configuration at AN05B023c | 1 cross | Shearin's strongest structural control. **Run it at AN05B023c specifically, where `C[j,i] = 0`**, not at IN05B002 where the reverse edge is 48% of traffic (method obj. 7). |
| **7** | **Age arm — 3 d vs 10 d adults** | free (collect both) | **Method obj. 6 (SERIOUS): GRASP integrates from the pupa, the connectome is a 5-d adult, and the reporter is built from a Neurexin-1β domain + mouse ICAM5 ectodomain — i.e. a synaptogenic adhesion system held together irreversibly for ten days.** If 3 d ≈ 10 d, integration is dominated by the pre-adult window and `tub-GAL80ts` gating of the split-GAL4 (post half) becomes mandatory before publication. If signal grows with age, the adult contribution dominates. Cheap, decisive, zero genetics. |
| **8** | **Balanced complete blocks** — every block = one animal of each of the 4 genotypes, dissected the same day, stained in the same tube, imaged in the same session, randomised acquisition order, barcoded before scoring | procedural | **Stats obj. 8 (SERIOUS): the pragmatic design protects δ_j (within-target) and leaves Δ (between-target) exposed.** W and L are between-target, so the block must contain both targets. Non-negotiable. Plus a frozen reference VNC and a TetraSpeck bead check per session (>10% drift ⇒ discard session). |
| **9** | **In-house MCFO on every SS line, and recomputation of R over the labelled set** | 3 crosses | **Method obj. 8 / inference obj. 11 (SERIOUS): per-body R dispersion and driver bleed.** Both AN05B023b and c are 2-body types with tight per-body R (0.989/0.994 for c), which is why they were chosen — but the driver must be shown to label them and not their 05B siblings. |
| **10** | **Blinding + pre-registration** — predicted signs of W and L, one primary metric, one normalisation, one alpha-spending function, frozen analysis script deposited before unblinding | procedural | **Stats obj. 9 (SERIOUS): optional stopping and 32–128 versions of "the primary statistic".** Replace the "stop at n=6 if it looks good" rule with an O'Brien–Fleming boundary; report median-unbiased estimates if stopped early; label everything else exploratory. |

**Controls I am cutting, and why.** The zero-ppk-*synapse target* driver (rather than compartment) is cut — no verified line exists, and Control 3 substitutes for it at zero cost. Female cohorts are cut (genetics obj. 15 is right that they are not dose-matched and the comparison is confounded).

---

## 4. READOUT AND STATISTICS

**Tissue.** VNC only for scoring; brain retained on the sample to verify the split-GAL4 pattern in the same animal, but **not used as a negative control** (Control 3). Fix 4% PFA 25 min RT, Janelia FlyLight IHC protocol verbatim, DPX mounting after ethanol/xylene clearing (refractive-index-matched and intensity-stable; PBS/Vectashield are neither).

**Four channels, four host species:**

| Channel | Antibody | Reports |
|---|---|---|
| AF488 | rabbit anti-GFP ABfinity, ThermoFisher **G10362** — *catalogue number is an inference from Shearin's text; confirm with Stowers* | **reconstituted GFP = the signal** |
| AF568 | rat anti-HA 3F10 (Roche 11867431001) | pre-half in GRN terminals; per-animal QC covariate |
| AF647 | goat anti-ICAM5/TLN (Bio-Techne AF1173) | post-half = **the target mask** |
| AF405 | mouse nc82 (DSHB) | Brp; registration + coincidence QC |

Sigma **G6539** (mouse, GFP-20) is the better-attested reconstituted-GFP antibody but clashes with nc82; validate **both** against the half-only controls in-house before the pre-registration locks, and do not present either as "the safe default" (method obj. 14, correct).

**Imaging.** 63×/1.4 oil, Nyquist, 0.19–0.25 µm z-step, fixed laser/gain/pinhole/zoom, single antibody lot, single oil lot, TetraSpeck bead slide at session start and end. 40× survey stack for registration.

**Registration and compartments.** Register to **JRC2018_VNC_MALE** (CMTK/ANTs, natverse `nat.templatebrains`), apply the Court et al. 2020 VNC neuropil atlas. Score **Ov**, **LegNp T1**, **LegNp T2**, **LegNp T3** (pooled as "LegNp" for L; T1 ipsi/contra split reported separately as a free male-specific positive control), and the zero-ppk compartment.

**Segmentation.** Target mask from the **anti-ICAM5 channel** — not from the GFP channel. This is the one provably well-behaved element of the estimator: the post half is driven by the same split-GAL4 at the same copy number in both arms, so mask volume, dendritic surface, imaging depth and local background divide out **exactly** within a target. Threshold, 3D clean-up, intersect with atlas compartment. GRASP channel: deconvolve with the measured PSF, rolling-ball background subtraction, 3D DoG (σ₁ 0.25, σ₂ 0.60 µm), threshold = mean + 5 SD of the matched half-only control **for that target, that block**.

**Primary quantity: integrated intensity inside mask ∩ compartment, per µm³ of mask.** Measured within-arbor synapse spacing on these two cells is 156–263 nm — at or below the confocal resolution limit — so a "punctum" has unknown multiplicity, and counting is a *compressive, biased* estimator that shrinks the effect. Puncta count is secondary and pre-registered; the two must agree in sign.

**Do NOT normalise the signal by the anti-HA channel as the primary estimator.** HA density is proportional to driven GRN terminal abundance, which differs between arms *because that difference is the signal*. HA enters as a covariate and as a pre-registered sensitivity analysis only. (The pragmatic design is right here and the rigorous design is wrong.)

**The model.** Not a t-test on log ratios. The stats reviewer is right that a difference of logs is undefined when the low-R arm can hit the floor, and that fitting γ once under H0 and reusing it is circular. Fit:

```
N_{a,j,d,c} ~ NegBinomial(μ, φ)
μ = V_mask · [ b_{j,c} + A_{j,c} · q^γ ]
q = 1                                        for d = ppk23
q = k_c · R_{j,c}(x)                         for d = ppk25
log A_{j,c} = α_{j,c} + u_block + u_animal
```
- `x` — marginalised over the full lattice of binary assignments; **the primary output is a posterior over hypotheses, not a p-value on one contrast.**
- `γ` — one global saturation exponent, lognormal prior, **profiled separately under each candidate x** (never fitted under H0 and reused).
- `k_c` — one per compartment group (Ov, LegNp), with an informative prior from Control 4.
- `b_{j,c}` — free per-target per-compartment background with a strong prior from the matched half-only control in the same block.
- `C[i,j,c]` — **not a constant.** Dirichlet prior on input composition, concentration calibrated so that connections <10 synapses or <1% of input are treated as non-conserved (Schlegel et al. 2024). This propagates the n=1-connectome uncertainty the reviewers correctly flagged.

**Frequentist backstop, reported alongside:** W and L as block-wise contrasts, tested by exact permutation of driver labels within block. Two-sided α = 0.025 each (Bonferroni over the two statistics). Report `sign(W), sign(L)` and the implied hypothesis.

**Primary claim, stated model-lightly so it survives graded x:** *"the wing-derived ppk25⁺ synaptic fraction is higher in AN05B023c than in AN05B023b"* (and the same for leg). That statement is true or false regardless of whether x is binary, and it is exactly what the receptor assignment predicts.

**Deleted from all documents:** "rank 8 of 8", "condition number 2.5", "all eight types individually identifiable", "121-fold". The first three are invalid once k and γ are unknown (D-optimality assumes a linear, homoscedastic, continuous-parameter model; all three assumptions fail). "121-fold" is the ratio of a number near 1 to R = 0.008, which is eight synapses in a thousand — inside the false-positive rate of automated synapse prediction. Report low-R predictions as **upper bounds**, not point estimates.

**Sample size.** No power calculation until σ is measured. **σ pilot: n = 20, single arm, one target, full pipeline, week 10–12.** An n = 6 pilot does not estimate σ — the 95% CI on σ̂ at 5 df spans [0.62σ, 2.45σ], a 15-fold range in implied n.

Provisional planning number, and the tolerance it buys: W is a within-block contrast of four measurements, so `Var(W̄) = 4σ_w²/n`. Predicted `|E[W]| = 2.4` natural-log units (half the 4.8-unit sign-flip separation).

| σ_w (ln) | CV | SE(W̄) at n = 15 | z | power |
|---|---|---|---|---|
| 0.5 | 65% | 0.258 | 9.3 | >0.999 |
| 1.0 | 170% | 0.516 | 4.7 | >0.99 |
| 1.5 | 320% | 0.775 | 3.1 | 0.88 |
| 2.0 | — | 1.03 | 2.3 | 0.63 |

**n = 15 per genotype (15 blocks, 60 VNCs) tolerates σ_w up to ~1.5 ln units.** The design is powered by the size of the sign flip, not by an assumed σ — which is the correct answer to the "your σ is invented" objection. The binding constraint is compression: at γ = 0.25 the effect shrinks to 0.6 ln units and n = 15 gives z ≈ 2.3 at σ_w = 0.5. **So γ, not σ, sets the sample size, and γ comes from Control 5.** Re-power by simulation from the model above after the σ pilot and the dose arm. Budget +20% attrition. Controls at n = 8. Replication cohort at n = 12 with the second SS line per target, second experimenter, separate batch.

Total: ~60 primary + ~35 control + ~48 replication + ~20 pilot ≈ **165 VNCs**, not the 300–315 in the submitted designs.

---

## 5. SURVIVING RISKS

| # | Risk | P | Impact | Mitigation |
|---|---|---|---|---|
| 1 | **The ppk drivers label GRN types outside the assigned eight** (WG2, LgLG2/3a/3b/4 — 417 cells), or **LgLG5–8 are not ppk23⁺ at all**. Zhang et al. 2023 resolve only four GRN classes per leg bristle, two of them *fru*⁺/ppk23⁺, and LgLG1a/1b already fill both slots. | **0.35** | Denominator of R_j is wrong; W and L still interpretable as descriptive statements but the mapping to x is broken | **Track 1, weeks 1–10.** Soma-count arithmetic alone is decisive: if ppk23-GAL4 labels ~2× the assigned-set cell count, the denominator is contaminated. This risk is why Track 1 runs first. |
| 2 | **`ppk25-LexA::p65` does not reproduce `ppk25-GAL4`.** Different transactivator, different site; BDSC's own note is that lexA patterns are "generally a subset" of matched GAL4 patterns. | 0.30 | Phase 2 not comparable to anything; both arms suspect | **GATE 2** (Control 4), quantitative, cell-by-cell, before any GRASP. Abandon ppk-LexA if it labels <80% of ppk25-GAL4 cells; fall back to split-LexA (`Zip⁻-LexA::DBD`, Ting et al. 2011, FBto0000161) which keeps ppk-GAL4 on the GRN side — at one construct per target. |
| 3 | **Saturation compresses W and L** (small γ). Split-GFP is irreversible and integrates over life. | 0.30 | Sign survives (this compresses, it does not invert, provided *b* is controlled — Control 2); magnitude and the exploratory inversion die | Ordinal claim is primary; γ measured in Control 5; re-power on measured γ. |
| 4 | **Split lines are not type-specific.** Omnibus Broad lines carry an explicit "may contain inconsistencies" warning; SS02541 and SS29574 are Omnibus. SS90856 is from the published Drivers collection and is the safer replication line. | 0.25 | R must be recomputed over the labelled set; if the recomputed R lands near 0.5, the line is useless | Control 9; two independent lines per target; drop any line whose recomputed R is within 0.15 of 0.5. |
| 5 | **Developmental / synaptogenic integration.** Both halves are on from pupal life; pre-t-GRASP carries a Neurexin-1β domain and post carries the mouse ICAM5 ectodomain — an adhesion system, not a passive dye. | 0.25 | Estimand becomes lifetime-integrated contact, not adult C[i,j]; and the ppk23 arm has ~2× as many neurexin-bearing terminals | **Control 7 (age arm) is the diagnostic.** Contingency: recombine `tub-GAL80ts` onto the platform X with ppk-LexA (PCR-screened) to gate the *post* half via the split-GAL4 — adds 4 weeks and one recombination, only if the age arm demands it. |
| 6 | **Apposition-driven false positives.** 13–15% of non-partner ppk active zones lie within 500 nm of genuine ppk25⁺ inputs on AN05B023c; VNC neurite diameters are 0.2–1 µm. No numerical false-positive rate has ever been published for any GRASP variant. | 0.20 | Compresses W and L toward zero by pulling R̂ toward the local membrane fraction (~0.5); at φ = 0.3 a 19.5-fold contrast becomes 4.5-fold | Bounded and non-inverting. Controls 2, 3, 5, 6. t-GRASP is structurally protected (Cac tail confines pre to AZs) but Shearin's lamina test was 8/9, and the miss was real. |
| 7 | **Batch × arm interaction over an 8-month run**, or independent drift of the two platform stocks. | 0.20 | Directly aliases onto W and L | Control 8 (block contains all four genotypes); frozen reference VNC per session; both platforms backcrossed together into one isogenic host; re-verify platforms by PCR every ~10 generations. |
| 8 | **Transvection**, if UAS-post is left at attP2 in trans to the DBD. | 0.15 *(0.60 if not fixed)* | Target-specific ectopic post-half expression, inside the ICAM5 mask, aliasing onto the between-target contrast | Already fixed by re-integrating at VK00037. Same objection blocks using `Ir52a-LexA-VP16`@attP2 (BDSC 60692) in trans to a 13XLexAop2 array at attP2. |
| 9 | **Connectome uncertainty.** n = 1 male, machine-predicted synapses; L/R replicates disagree by up to 0.12 on AN13B002 and 0.64 on INXXX044. | 0.15 | Predictions are intervals, not points | AN05B023b/c are the *best-behaved* targets on this axis (c: L/R agree to 0.005; per-body R 0.989/0.994) — that is part of why they were chosen. Dirichlet prior propagates the rest. |
| 10 | **Anti-ICAM5 fails in whole-mount VNC.** | 0.10 | Lose the mask, lose the exact within-target cancellation | Fall back to atlas-ROI-only scoring using the anti-HA neuropil outline; costs specificity, not validity of W/L. |

**Risks I am demoting from the submitted designs.** "ppk25-GAL4 wing-margin expression is undocumented" was ranked #1 or #3 in all three designs at 25–30%. It is documented: Starostina et al. 2012 (*J. Neurosci.* 32:11879) state that *ppk25-Gal4* "is expressed in wings, but not in the labellum." Run the check anyway as part of Track 1a, but do not budget it as a project-killer. Likewise, "*k* does not cancel" is demoted because W and L are constructed so that it does — that objection killed the *minimal* design, not this one.

---

## 6. KILL CRITERIA

| Gate | Week | Kill / redirect condition |
|---|---|---|
| **GATE 0** (computational, free) | 0 | If the ROI-resolved recomputation shows `|W_predicted|` or `|L_predicted|` < 0.6 log₁₀ (4-fold) for the AN05B023b/c pair, **do not run this experiment** — no other target pair in the shortlist is better and none is buildable. |
| **GATE 0b** | 0 | If `C[j,i]` (target → ppk GRN) is > 5% of `C[i,j]` for AN05B023b or c, that target's forward signal is polarity-contaminated. Drop it and re-select. |
| **GATE 1 — driver mapping** | 10–12 | If ppk23-GAL4 labels **>1.3× or <0.7×** the connectome cell count of the assigned 8-type set on the wing margin or foreleg, the denominator of R_j is not the assigned set. **Stop the GRASP build.** Redirect all effort to HCR-FISH / MCFO type-assignment, which measures x directly. |
| **GATE 1b — σ pilot** | 12 | If σ̂_w > 2.0 natural-log units at n = 20, n = 15 gives <65% power even at γ = 1. Either re-power (n scales as σ²) or stop — at σ_w = 2.5 the required n exceeds 40/cell and the project is not worth it. |
| **GATE 1c — assay floor** | 12 | If the ppk23 arm at AN05B102a (27,083 ppk synapses) does not give strong, unambiguous signal above the half-only control, the assay does not work. Stop. |
| **GATE 2 — ppk-LexA concordance** | 20–24 | If ppk25-LexA labels <80% of ppk25-GAL4 cells, or if ppk25-LexA⁺ cells are not a subset of ppk23-LexA⁺ cells, switch to split-LexA or stop. |
| **GATE 3 — driver specificity** | 20–24 | If in-house MCFO shows either SS line labels a set whose recomputed R is within 0.15 of 0.5, that target is dead. If both are dead, stop — there is no substitute pair. |
| **GATE 4 — dose invariance** | 30 | If W or L moves by more than 0.5 log₁₀ between 1× and 2× t-GRASP copy number, signal is overexpression-driven. Report sign only, delete every magnitude claim, and do not attempt the GRASP-vs-EM calibration. |
| **GATE 5 — background** | ongoing | If `b̂_j / f̂(1)_j > 0.1` at either target, the sign of W or L is not protected (background can flip it). Drop that target. |

---

## 7. REAGENT ORDER LIST

### Confirmed (verified BDSC / FlyBase records)

| Stock | Genotype | Role |
|---|---|---|
| **BDSC 79039** | `y1 w*; wg[Sp-1]/CyO, P{Dfd-EYFP}2; P{20XUAS-post-t-GRASP}attP2 PBac{13XLexAop2-pre-t-GRASP}VK00027/TM6C, Sb1 Tb1` | source of `LexAop-pre`@VK00027 (Build A) |
| **BDSC 79040** | `y1 w*; wg[Sp-1]/CyO, P{Dfd-EYFP}2; P{13XLexAop2-post-t-GRASP}attP2 PBac{20XUAS-pre-t-GRASP}VK00027` | Phase-1 pilot (ppk-GAL4 × R56C09-lexA) |
| **BDSC 93026** | `w1118; P{ppk23-Gal4.2.695}2; TM2/TM6B` | Track 1 driver mapping; Phase-1 pilot |
| **BDSC 93028** | `w1118; P{ppk25-GAL4.S}2; P{ppk25-GAL4.S}3` | Track 1 driver mapping. **Note: homozygous at both loci — 2 GAL4 copies.** Fine for Track 1 (single-driver imaging); would be a fatal 2× dose asymmetry if used in a two-arm GRASP comparison |
| **BDSC 53584** | `w1118; P{GMR56C09-lexA}attP40` | Phase-1 pilot target (PPN1) |
| **BDSC 39145** | `w1118; P{GMR56C09-GAL4}attP2` | R56C09 pattern characterisation |
| **BDSC 32203** | `w*; P{13XLexAop2-mCD8::GFP}attP2` | LexA driver validation |
| **BDSC 60692** | `w*; wg[Sp-1]/CyO; P{Ir52a-LexA-VP16}attP2 PBac{...}VK00005/TM3` | WG1/Ir52a channel — **flagged: attP2, transvection risk in trans to LexAop arrays** |
| Sigma **G6539** | mouse anti-GFP clone GFP-20 | reconstituted GFP (validate in-house) |
| Roche **11867431001** | rat anti-HA 3F10 | pre-half |
| Bio-Techne **AF1173** | goat anti-ICAM5/TLN | post-half = mask |
| DSHB **nc82** | mouse anti-Brp | registration, coincidence QC |

### UNCONFIRMED — verify before ordering

| Item | Status |
|---|---|
| ThermoFisher **G10362** (rabbit ABfinity anti-GFP) | Catalogue number is an *inference* from Shearin's text ("rabbit anti-GFP Tag Abfinity"). Confirm with Stowers. |
| `w; Sp/CyO; TM3,Sb Ser/TM6B, Tb Hu` double balancer | Several exist at BDSC; number not verified. |
| `UAS-myr::GFP`, `13XLexAop2-myr::tdTomato` reporters | Numbers not verified. |
| `hs-FLP; MCFO-1` (or MCFO-3/5) | Numbers not verified. Needed for Track 1c. |
| `tub-GAL80ts` (chr X or chr 2 insertion) | Numbers not verified. Contingency only (Risk 5). |
| Empty split-GAL4 `P{BPp65ADZpUw}attP40; P{BPZpGAL4DBDUw}attP2` | Hampel/Meissner; may be Janelia-only. |
| **VK00037** cytology (2L 22A3) | Inferred from landing-site tables; confirm before designing the injection. |
| Whether **SS02541, SS29574, SS90856, SS57949** are at BDSC | Omnibus Broad lines are usually **not** at BDSC; SS90856 is from the published Drivers collection and is most likely orderable. |
| Whether any **Janelia GMR-lexA** exists for a fragment hitting AN05B023b/c | **10-minute manual check on bdsc.indiana.edu. A hit removes two injections and 12 weeks.** Do this in week 0. |

### To be made (3 injections, outsourced, week 0–10)

1. `P{ppk23-LexA::p65}su(Hw)attP8` — Thistle 2.695 kb fragment in `pBPLexA::p65Uw`.
2. `P{ppk25-LexA::p65}su(Hw)attP8` — Starostina architecture (5 kb upstream + 2 kb downstream genomic, LexA::p65 ORF inserted after the ppk25 start codon, **start codon mutated**). Do **not** shortcut this into a Gen1 enhancer plasmid.
3. `P{20XUAS-post-t-GRASP}VK00037` — re-integration, required to avoid attP2 transvection.

### Emails, week 0 (rate-limiting)

- **Kristin Scott** — a chr-2-only `ppk25-GAL4` segregant; the ppk23/ppk25 plasmids; **and the definitive answer to whether the `P{ppk25-GAL4.S}` ATG is mutated.** If it is intact, ppk25-GAL4 animals are Ppk25 overexpressors in the very neurons being counted, and no ratio cancels that.
- **Steve Stowers** — single (un-recombined) t-GRASP transgenes; the `pJFRC-20XUAS-post-t-GRASP` attB plasmid (removes Build A and one injection design step); the exact ThermoFisher antibody catalogue number.
- **Barry Dickson** — `P{ppk23-lexA.D}` and **its chromosome**. Useful as an independent cross-check; do not build on it.
- **Marin / Jefferis** — PPN1 = AN05B023a–d or AN05B102a? FlyBase/VFB (Marin 2024 MANC, Berg 2025 male CNS) say the former; the repo says the latter. One answer changes the pilot's interpretation.
- **flylight@janelia.hhmi.org** — SS02541, SS29574, SS90856, SS57949.

---

## 8. OPEN QUESTIONS, RANKED BY HOW MUCH THEY CHANGE THE PLAN

1. **What do ppk23-GAL4 and ppk25-GAL4 actually label, in connectome terms?** Everything downstream assumes the denominator of R_j runs over exactly the eight assigned types. Five GRN types (417 cells) have no receptor call, and four of the eight assigned types (LgLG5–8) rest on connectome inference alone. **If Track 1 answers this cleanly it partly answers the receptor question directly and the GRASP becomes confirmatory rather than primary.** If it cannot answer it, the GRASP was never interpretable. This is the single highest-leverage question and it is answerable in six weeks with two crosses.

2. **Are WG3 and WG4 (and LgLG1a vs LgLG1b) morphologically separable at light-microscope resolution?** This is a connectome query you can run today, and it decides whether Track 1 yields x_i directly or only a coverage ratio. The repo's own KS D ≈ 0.1–0.26 for LgLG1a/1b terminal positions suggests the leg pair is *not* separable; the wing pair is untested. If WG3/WG4 are separable, MCFO plus registration measures the wing call directly, with no GRASP, no k, no γ, no background, and n = hundreds of axons rather than fifteen animals.

3. **Is the `P{ppk25-GAL4.S}` start codon mutated?** If not, one arm of every GRASP experiment is a Ppk25-overexpressing animal and the other is not — a biological asymmetry in the presynaptic neurons themselves, which no ratio cancels. Get the construct map from the Pikielny lab before ordering anything.

4. **What does GATE 0 return for W and L on the ROI-resolved matrix including LgLG5–8?** My hand-computation from the four dominant types gives ±1.04 and ±1.07 log₁₀. The method reviewer's ROI-resolved figure for the related compartment ratio was substantially larger. Either is fine; but if the full recomputation drops either below 0.6 log₁₀, the experiment should not be run.

5. **Do any Janelia GMR-lexA lines hit AN05B023b or AN05B023c?** A hit collapses the plan from 3 injections + 9 generations of stock building to a Phase-1 architecture with off-the-shelf reagents, and moves the answer from week 34 to roughly week 18.

6. **Is the mCNS neurotransmitter prediction really as reported** — that WG3/LgLG1b/LgLG8 are "unclear", LgLG5 is glutamatergic, and every other GRN type including all unassigned ones is confidently cholinergic? If so, combined with Zhang et al. 2023's independent finding that the ppk25⁺ leg GRN is the VGlut⁺ one, that is a genuinely non-circular molecular line of evidence that already makes H1 (global swap) improbable. It does not touch H2 or H3 — which is precisely why the wing/leg decoupling in W and L is the right experiment — but it should be stated up front, because a 34-week project powered mainly against H1 would be powered against a hypothesis that is already close to dead.

7. **Does the team want an answer about x, or an answer about the paper's thesis?** If the deliverable is "the valence logic downstream of these types is real", then W and L answer it: they test whether the wing assignment and the leg assignment each survive an independent measurement, which is the load-bearing claim. If the deliverable is "we identified ppk25 status for eight connectome types", **the GRASP cannot deliver that at any n** — the identification claim is not recoverable once k, γ and per-type reporter weights are unknown, and it should be removed from the grant and the paper now rather than after the data come in.
