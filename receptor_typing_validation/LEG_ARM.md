# The leg arm — target selection

male-cns:v1.0, unthresholded. `R/06_final_targets.R` → `R/07_perbody_leg.R`.

**Framing correction.** Earlier versions of this analysis optimised for the *wing* types, on the
argument that WG3/WG4 are foundational and the leg assignments were propagated from them. That is
right as epistemics and wrong as a deliverable. The paper is about **contact chemosensation** —
foreleg tapping — so what has to be correct is the **leg** assignment. The wing matters only as
the historical entry point for the typing argument.

Targets are therefore scored on `R_leg`, renormalised **within the leg types only**
(LgLG1a, LgLG1b, LgLG5–8), which is what a leg-compartment readout actually measures.

## The channel that matters: LgLG1a vs LgLG1b

The leg "M" and "F" cells. Opposed, 100%-leg targets:

| side | target | loading | R_leg | fold | leg syn |
|---|---|---:|---:|---:|---:|
| LgLG1b | **DNpe029** | 0.93 | 0.935 | 14.4× | 772 |
| LgLG1b | IN23B025 | 0.91 | 0.928 | 13.0× | 405 |
| LgLG1b | IN23B020 | 0.87 | 0.899 | 8.9× | 662 |
| LgLG1b | AN17A024 | 0.87 | 0.896 | 8.7× | 473 |
| LgLG1a | **IN17A013** | 0.87 | 0.129 | 6.7× | 1711 |
| LgLG1a | IN07B010 | 0.85 | 0.149 | 5.7× | 429 |
| LgLG1a | IN01B065 | 0.81 | 0.153 | 5.5× | 1847 |
| LgLG1a | AN17A013 | 0.80 | 0.174 | 4.7× | 3401 |

## The male-specific bilateral T1 types: LgLG5–8

| type | best isolator | loading | R_leg |
|---|---|---:|---:|
| LgLG6 | **AN09B017b** | 0.89 | 0.090 |
| LgLG8 | **AN09B017g** | 0.73 | 0.896 |
| LgLG5 | AN09B017f | 0.56 | 0.569 |
| LgLG7 | AN09B017e | 0.56 | 0.380 |

LgLG5 and LgLG7 have no clean isolator and may not be resolvable by this design.

## Per-body robustness

A type whose R is carried by one body is useless here: a driver labels the whole type, so the
signal dilutes toward the type mean. Every leg candidate was checked body by body.

| target | bodies | with input | pooled R | drop-largest | SD |
|---|---:|---:|---:|---:|---:|
| AN09B017b | 2 | 2 | 0.090 | 0.084 | **0.008** |
| AN05B023c | 2 | 2 | 0.934 | 0.928 | **0.008** |
| AN05B023b | 2 | 2 | 0.091 | 0.082 | 0.013 |
| IN17A013 | 2 | 2 | 0.129 | 0.116 | 0.016 |
| AN17A013 | 4 | 4 | 0.174 | 0.164 | 0.017 |
| IN07B010 | 2 | 2 | 0.149 | 0.184 | 0.037 |
| DNpe029 | 4 | 4 | 0.935 | 0.925 | 0.043 |
| IN23B025 | 6 | 6 | 0.928 | 0.946 | 0.043 |
| IN23B020 | 7 | 7 | 0.899 | 0.910 | 0.050 |
| AN17A024 | 6 | 6 | 0.896 | 0.894 | 0.050 |
| AN09B017g | 2 | 2 | 0.896 | 0.942 | 0.060 |
| IN01B065 | 20 | 20 | 0.153 | 0.142 | 0.070 |
| AN09B017c | 2 | 2 | 0.181 | 0.238 | 0.080 |

**Every body of every leg candidate receives ppk input.** No dilution, no one-body artifacts.

### The wing targets fail exactly this test

Found by the independent crosscheck (`wf_8bdc3de4-906`), which reproduced all 22 R values to
within 0.00045 by two independent methods and then broke them down per body:

- **INXXX044** — 8 bodies, per-body R spans 0.071 → 1.000, SD 0.41. One body (800660) carries
  638 of 863 synapses. Drop it and R collapses to 0.431, **inverting the prediction**. Not a
  coherent type for a GRASP readout. **Do not use.**
- **AN01B004** — 6 bodies in three instance groups; the `(28192)` pair receives **zero** ppk
  input, 170 of 178 synapses come from the `(57382)` pair. A type-level driver will not
  reproduce R = 0.966. **Do not use.**
- **AN17A003** — R is bilaterally consistent (L 0.973, R 0.996, SD 0.015), so the 57× is real.
  But only 2 of its 6 bodies receive meaningful ppk input, so a type-level driver labels six
  neurons of which two carry the signal. Usable, with that dilution priced in.
- AN05B096 — 4 bodies, 2 receive input. Same caveat.

So the targets that looked strongest on fold alone are the ones that fail per-body scrutiny,
while the leg targets — the ones the biology needs — are the robust ones.

## Recommended pairs

1. **AN09B017g (0.896) vs AN09B017b (0.090)** — opposed, 2 bodies each, all receiving input,
   ~1000–2000 leg synapses. Tests the LgLG8 / LgLG6 assignment. **The lab holds four vAB3
   candidate split-GAL4 lines** (SS103089, SS104905, SS104909, SS105464) and vAB3 is the
   AN09B017 group, so this is the only pair with reagents plausibly already in hand.
2. **AN05B023c (0.934) vs AN05B023b (0.091)** — the cleanest pair in the dataset (SD 0.008 and
   0.013, thousands of synapses each). No driver at Bloomington or in the lab.
3. **DNpe029 (0.935) vs IN17A013 (0.129)** — tests the LgLG1b / LgLG1a assignment directly,
   which is the channel the paper is actually about. No driver known.

## The gate on option 1

AN09B017 members span R_leg 0.090 (b) to 0.896 (g). If a vAB3 split-GAL4 labels the **group**
rather than one member, R averages toward ~0.35 and the contrast dies. MCFO on the four lab lines
resolves which member each labels. That is the cheapest next step in the whole project and uses
reagents already in the freezer.
