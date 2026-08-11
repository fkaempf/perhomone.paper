# Figure 5 — claim census and slimming proposal

**Date:** 2026-08-10. Read-only audit. Nothing deleted, nothing rendered.
**Inputs:** 43 top-level `.Rmd` + 20 in `panel_M/rmd/` = 63 notebooks; 14 per-panel
narratives; `my_selection_that_makes_halfway_sense/figure_5_narrative.txt`;
`panel_M/notes/PANEL_M_DESIGN_SUMMARY.md`.

---

## 1. Distinct claims (15)

Every notebook in fig5 asserts one of these. Notebook count per claim in brackets.

| # | Claim | Panels asserting it |
|---|---|---|
| 1 | mAL is heterogeneous across 7 sensory channels — not one cell type | A [8 variants] |
| 2 | AN09B017 relay tiles a ppk23↔ppk25 selectivity spectrum (input side) | B [8] |
| 3 | The same relays are output-specific onto mAL | K [2] |
| 4 | AN05B102 is a second, cholinergic relay family doing the same job | N, N' [2] |
| 5 | ppk23 arrives net-*inhibitory* at a subset of mAL — sign reversal | C |
| 6 | The reversal is carried by an 11-cell GABA sign-inverter pool (AN05B035 + siblings) | panel_M [20] |
| 7 | Net drive decomposes into separable excitatory / inhibitory components | E |
| 8 | mAL↔mAL lateral inhibition network (157 edges, 75% GABA) | G |
| 9 | Male-specific mAL subtypes carry 7.5× ppk drive and 23× P1 output | H |
| 10 | Three encounter scenarios produce distinct population signatures | F |
| 11 | Path model and signal-flow model agree (ρ = 0.63) | I [10] |
| 12 | mAL→P1 output is channel-specific (22/37 → 41/45) | D |
| 13 | ppk23-inhibited vs ppk23-excited mAL groups wire differently to P1 | J [3] |
| 14 | mAL and P1 both show graded ppk23-vs-ppk25 selectivity | L [3] |
| 15 | cVA's effect on P1 is context-dependent (nonlinear) | J_cva_delta |

**63 notebooks, 15 claims.** The ratio is the problem, not the claims.

---

## 2. The redundancy groups

### Group α — same quantity, four views (claims 1, 5, 7, 14)
A, C, E, L all plot *net path strength per mAL subtype for ppk23/ppk25*.
- A = that quantity as a 7-channel heatmap
- C-right = ppk23 vs ppk25 scatter
- L-first = ppk23 vs ppk25 scatter (**near-duplicate of C-right**)
- E = the same net value split into its exc/inh addends — narrative says so verbatim:
  *"the NET strength equals excitatory minus inhibitory — i.e. what Panel A and Panel C display."*

→ One main panel carries the quantity; the rest are re-cuts.

### Group β — relay layer, three panels (claims 2, 3, 4)
B (relay input) + K (relay output) + N (second family). N exists *only* because B and K
scoped to AN09B017 — its own narrative says this. One input-vs-output panel covering both
families replaces all three.

### Group γ — mAL→P1, three panels (claims 12, 13, 14)
D is the full mAL→P1 weight matrix. J is that same matrix re-split by ppk23 response group.
L-third is P1 ppk drive under signal flow. J is a re-slice of D.

### Group δ — panel M, 20 notebooks for one claim (claim 6)
Already triaged in `PANEL_M_DESIGN_SUMMARY.md`: main = morphology + synapse sex-bias;
alternate = CE2 correlation (R² = 0.423, p = 0.0064); supp = CE5 counterfactual, CE1, CE7.
**That ranking is already the cut** — ~14 of the 20 have no slot.

### Group ε — methods cross-check (claim 11)
I plus 9 `panel_I_*` variants. A model-agreement check is supplementary by nature.

---

## 3. The decision underneath all of it

`panel_A_max_flow.Rmd`, `panel_A_max_flow_normed.Rmd`, `panel_A_raw_path_bottleneck.Rmd`,
`panel_A_topK_widest.Rmd` are **four competing definitions of the core path metric**, not four
panels. A, C, E, F, L, I all consume that metric.

**Nothing else can be cut safely until one metric is chosen**, because "is this panel
redundant" changes depending on which number the figure reports. `panel_A_supp.Rmd`
(path-count confound), `panel_A_supp_level1.Rmd` (collapsed intermediates), and
`panel_A_supp_real_merge.Rmd` are the checks that should decide it.

This is the single highest-leverage thing to settle first.

---

## 4. Proposed slim Fig 5 — 7 main panels

Order follows the thesis in `my_selection_that_makes_halfway_sense`, with β/γ merged.

| Slot | Content | From | Role |
|---|---|---|---|
| A | mAL × 7-channel input heatmap | A (one metric) | the puzzle |
| B | Relay selectivity: input vs output, AN09B017 **and** AN05B102 | B + K + N merged | where diversity is made |
| C | ppk23 sign reversal at mAL | C (bars; drop duplicate scatter) | the surprise |
| D | AN05B035 morphology + synapse sex-bias | panel_M main | the mechanism |
| E | Male-specific vs shared: ppk in, P1 out | H | dimorphism — the paper's theme |
| F | Three encounter signatures | F | population code |
| G | mAL→P1 output specificity | D | the output |

**Supplement:** E (E/I decomposition), G (lateral inhibition), I (model agreement),
J (response-group × P1), L (selectivity scatters), J_cva_delta (cVA nonlinearity),
panel_M CE1/CE2/CE5/CE7, `panel_A_supp*` (metric justification).

**No slot:** the remaining ~14 panel_M variants, `panel_B_supp_v1–v6`, most `panel_I_*`,
`panel_K_heatmap_raw`, `panel_J_heatmap_raw`, `panel_supp_variants`, `panel_N_prime`,
`plots_mspecific/` if it is not declared a supplementary figure.

15 claims → 7 main + ~10 supp. Every claim still lands somewhere.

---

## 5. Fig 5 / Fig 6 collisions — resolve before touching Fig 6

Three claims are currently made twice, once per figure:

| Claim | Fig 5 | Fig 6 |
|---|---|---|
| E/I architecture of sensory convergence | E (E/I decomposition) | C (valence heatmap) |
| Male-specific vs shared output populations | H (dimorphism) | I (aSP-f vs aSP-g) |
| Multi-channel combination effects | F (3 encounter scenarios) | L–O (127-combination screen) |

Fig 6's 127-combination interaction screen strictly generalizes Fig 5's three hand-picked
scenarios. Either Fig 5's F becomes the illustrative special case of Fig 6's framework and
says so, or one of them goes.

---

## 6. Open questions for the author

1. Which path metric — max-flow, max-flow normed, raw bottleneck, or top-K widest?
2. Is `plots_mspecific/` a supplementary figure, a replacement, or a dead end?
3. Does F survive as its own panel, or fold into Fig 6's interaction framework?
4. Merged relay panel (B+K+N): keep both relay families in the main figure, or AN05B102 to supp?
