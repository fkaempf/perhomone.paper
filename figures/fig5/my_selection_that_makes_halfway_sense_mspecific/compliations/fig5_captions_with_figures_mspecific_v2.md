---
title: "Figure 5 (male-specific variant) v2"
subtitle: "Panel captions with figures, grouped by panel. Supplementary views marked (SUPP)."
geometry: margin=1in
header-includes:
  - \usepackage{graphicx}
  - \usepackage{float}
---

Analysis restricted to the 16 male-specific `mAL_m*` subtypes.

**Scenario channel mapping (corrected):**
`ppk23` = M cells (male contact pheromone 7-T);
`ppk25` = F cells (female contact pheromone 7,11-HD);
`DA1` = cVA volatile pheromone.

**Story arc:** A -> B -> K -> C -> E -> G -> F -> L -> D -> J -> I.

Panels are grouped by the main-figure letter; each group contains the main view(s) followed by any supplementary variants. Supplementary views are labeled **(SUPP)**.

\newpage

# A. mAL sensory input profiles

![](../single panels/panel_A_input_profiles_raw.pdf)

**(A) Male-specific mAL is not monolithic.** Hierarchically-clustered heatmap of net path-based sensory input strength across 7 channels for all 16 mAL_m subtypes: ppk23-biased (male-contact), ppk25-biased (female-contact), olfactory, and multimodal subgroups emerge within the male-only subset.

\newpage

![](../single panels/panel_A_input_profiles_raw_synapses.pdf)

**(A-SUPP) Panel A recomputed with widest-path raw synapse counts.** Cell = signed max path-bottleneck synapse count (exc - inh), picking the single widest path per valence. Controls for path-count and normalization artifacts in (A).

\newpage

# B. AN09B017 relay selectivity

![](../single panels/panel_B_an09b017_selectivity.pdf)

**(B) AN09B017 ascending neurons tile a ppk23/ppk25 selectivity spectrum.** Scatter of ppk23 vs ppk25 input per AN09B017 variant (a-g); b is most ppk23-biased (12.6x), g is most ppk25-biased (16x). Channel separation of male (M-cell) vs female (F-cell) contact pheromone begins in the ascending relay layer.

\newpage

![](../single panels/panel_B_selectivity_ratio.pdf)

**(B') Log2 ppk23/ppk25 ratio per AN09B017 variant.** Bar quantification of the selectivity spectrum from (B), variants ordered by ratio.

\newpage

# K. Relays to mAL

![](../single panels/panel_K_heatmap.pdf)

**(K) Relays route channels to specific mAL subsets.** Input-normalized connectivity of AN09B017a-g + AN05B035 to the 16 male-specific mAL_m subtypes, annotated by ppk23/ppk25 input bias and mAL dimorphism. Completes the labeled-line motif: M-cell (ppk23) -> AN09B017 subset -> specific mAL_m; F-cell (ppk25) -> different AN09B017 subset -> different mAL_m.

\newpage

![](../single panels/panel_K_heatmap_raw.pdf)

**(K-SUPP) Panel K recomputed with raw synapse counts.** AN09B017 + AN05B035 -> mAL raw counts. Complements the input-normalized (K).

\newpage

# C. Male-contact sign reversal

![](../single panels/panel_C_ppk23_sign_reversal.pdf)

**(C) Male contact (ppk23) signal excites some mAL subtypes and inhibits others.** Paired bars of ppk23 vs ppk25 net path strength per mAL_m subtype. All 16 receive positive ppk23 drive (peak mAL_m3c = 0.11); sign reversal at specific subtypes arises from the GABAergic ascending neuron AN05B035.

\newpage

![](../single panels/panel_C_ppk23_vs_ppk25_scatter.pdf)

**(C') ppk23 vs ppk25 per-subtype scatter.** Each point one mAL_m subtype; identifies which subtypes are driven by which channel.

\newpage

# E. E/I decomposition of ppk drive

![](../single panels/panel_E_valence_bars.pdf)

**(E) E/I balance determines polarity.** Stacked bars decomposing ppk23 and ppk25 input into excitatory (red) and inhibitory (blue) path components per mAL_m subtype. Every subtype carries both; sign reversal in (C) reflects which arm dominates, not absent excitation.

\newpage

![](../single panels/panel_E_ei_balance_scatter.pdf)

**(E') E/I balance scatter.** x = ppk23 E/I ratio, y = ppk25 E/I ratio per subtype. mean balance ppk23 = 0.314, ppk25 = 0.424. Small weight changes on the inhibitory arm could flip polarity.

\newpage

# G. Lateral mAL<->mAL architecture

![](../single panels/panel_G_lateral_heatmap.pdf)

**(G) Lateral mAL<->mAL connectivity (raw synapses).** Signed synapse-count heatmap among the 16 mAL_m subtypes; 125 edges, 76% GABAergic. Blue = inhibitory, red = excitatory.

\newpage

![](../single panels/panel_G_hub_analysis.pdf)

**(G') Lateral inhibition hubs.** mAL_m1 and mAL_m8 are dominant inhibitory outputs; mAL_m5b/c and mAL_m2b receive heaviest lateral inhibition. Drive magnitude does not predict inhibition received (rho = 0.32), so competition sharpens the code independently of input strength.

\newpage

![](../single panels/panel_G_lateral_heatmap_normed.pdf)

**(G-SUPP) Panel G recomputed with input-normalized weights.** mAL<->mAL signed input fractions. Complements the raw-synapse version in (G).

\newpage

# F. Three-scenario population signatures

![](../single panels/panel_F_parallel_coordinates.pdf)

**(F) Three pheromone encounters produce distinct population signatures (path-based).** For each mAL_m subtype (x-axis), three lines give summed path-based drive under Female (red, ppk25), cVA+male (purple, DA1+ppk23), cVA+female (orange, DA1+ppk25). mAL_m3c/3a/2a show the largest differential activation.

\newpage

![](../single panels/panel_F_sf_parallel_coordinates.pdf)

**(F') Same scenarios under the signal-flow model.** Iterative nonlinear propagation (tanh saturation + rectification). Same scenario-discriminators as (F), confirming the population signatures are not artifacts of the linear sum.

\newpage

# L. ppk selectivity: mAL and P1 in shared coordinates

![](../single panels/panel_L_mal_and_p1_ppk_selectivity.pdf)

**(L) Path-based combined.** x = ppk23 path drive (male contact), y = ppk25 path drive (female contact); mAL blue circles, P1 red triangles, `coord_fixed` y=x. Channel selectivity propagates mAL -> P1.

\newpage

![](../single panels/panel_L_mal_and_p1_sf_ppk_selectivity.pdf)

**(L') Same overlay under the signal-flow model.** x = ppk23 alone net input, y = ppk25 alone net input. Confirms the path-based picture under nonlinear propagation.

\newpage

![](../single panels/panel_L_mal_ppk_selectivity_supp.pdf)

**(L-SUPP-a) Panel L mAL only, path-based.** Subsumed by (L) but shown separately for clarity.

\newpage

![](../single panels/panel_L_mal_sf_ppk_selectivity_supp.pdf)

**(L-SUPP-b) Panel L mAL only, signal-flow.** Subsumed by (L').

\newpage

![](../single panels/panel_L_p1_ppk_selectivity_supp.pdf)

**(L-SUPP-c) Panel L P1 only, path-based.** Subsumed by (L).

\newpage

![](../single panels/panel_L_p1_sf_ppk_selectivity_supp.pdf)

**(L-SUPP-d) Panel L P1 only, signal-flow.** Subsumed by (L').

\newpage

# D. mAL -> P1 gating

![](../single panels/panel_D_mal_to_p1.pdf)

**(D) mAL delivers channel-specific P1 gating (raw synapses).** Biclustered signed synapse-count heatmap of mAL_m -> P1. Block-diagonal structure: mAL_m8 and m1 dominate P1 inhibition while mAL_m3a/b are net excitatory. Graded labeled-line gate.

\newpage

![](../single panels/panel_D_total_drive.pdf)

**(D') Total mAL drive per P1 subtype.** Stacked bars summing signed mAL_m -> P1 weights. Net drive inhibitory for most P1s, with a few at net zero / excitatory.

\newpage

![](../single panels/panel_D_mal_to_p1_normed.pdf)

**(D-SUPP) Panel D recomputed with input-normalized weights.** Each cell = fraction of the P1's total input, signed by mAL neurotransmitter. Complements the raw-synapse version in (D).

\newpage

# J. P1 per-scenario drive & cVA gain

![](../single panels/panel_J_cva_delta_scatter.pdf)

**(J) cVA gain per P1 courtship command neuron.** 45 P1 subtypes. x = Delta drive when cVA added to female contact `drive(DA1+ppk25) - drive(ppk25)`. y = same for male contact `drive(DA1+ppk23) - drive(ppk23)`. Dashed y = x is the linear prediction. Off-diagonal spread reveals context-dependent cVA sensitivity.

\newpage

![](../single panels/panel_J_per_p1_bars.pdf)

**(J') Predicted P1 drive under the three encounter scenarios.** Stacked bars per P1 subtype showing drive under Female (ppk25), cVA+male, cVA+female. Per-P1 distribution of inhibition vs excitation shifts with encounter type.

\newpage

# I. Two-model convergence and P1 generalization

![](../single panels/panel_I_combined.pdf)

**(I) Two models agree on the mAL population code.** 2x2 grid: three per-scenario scatters of path-based vs signal-flow mAL drive + the rectified-sigmoid activation function. Per-scenario Spearman rho printed; overall rho ~0.65, 75% sign agreement.

\newpage

![](../single panels/panel_I_mal_and_p1_spread_scatter.pdf)

**(I') Model agreement extends from mAL to P1.** Mean path-based vs mean signal-flow drive per subtype, both populations, point size = joint spread across scenarios. Scenario discriminability inherited from mAL is preserved at the P1 command-neuron layer.

\newpage

![](../single panels/panel_I_scenario_heatmap_supp.pdf)

**(I-SUPP-a) mAL 3-scenario signal-flow heatmap.** 3 scenarios x 16 mAL_m subtypes, blue/red diverging on signal-flow net input.

\newpage

![](../single panels/panel_I_p1_scenario_heatmap_supp.pdf)

**(I-SUPP-b) P1 3-scenario signal-flow heatmap.** 3 scenarios x 45 P1 subtypes.

\newpage

![](../single panels/panel_I_p1_combined_supp.pdf)

**(I-SUPP-c) P1 version of the Panel I 2x2 grid.** Path-based vs signal-flow P1 drive per scenario plus activation function inset.

\newpage

![](../single panels/panel_I_mal_scenario_spread_bar_supp.pdf)

**(I-SUPP-d) mAL scenario spread bar.** Per-mAL subtype spread (max-min) across scenarios, bar color = argmax scenario. Every scenario gets a legend swatch even if it never wins argmax at a subtype.

\newpage

![](../single panels/panel_I_mal_scenario_trajectories_supp.pdf)

**(I-SUPP-e) Top-15 most scenario-discriminating mAL subtypes.** Signal-flow drive trajectories across the three scenarios, one line per subtype.

\newpage

![](../single panels/panel_I_p1_scenario_spread_bar_supp.pdf)

**(I-SUPP-f) P1 scenario spread bar.** Per-P1 spread across scenarios, argmax-colored.

\newpage

![](../single panels/panel_I_p1_scenario_spread_scatter_supp.pdf)

**(I-SUPP-g) P1 mean-drive vs spread.** Each P1 subtype in (mean drive, spread) space, point size = spread, color = argmax.

\newpage

![](../single panels/panel_I_p1_scenario_trajectories_supp.pdf)

**(I-SUPP-h) Top-15 most scenario-discriminating P1 subtypes.** Signal-flow drive trajectories across the three scenarios.

\newpage

![](../single panels/panel_I_mal_cva_mvf_bar_supp.pdf)

**(I-SUPP-i) Focused mAL cVA+male vs cVA+female spread.** Isolates ppk25 vs ppk23 sensitivity under shared cVA background; bar height = `|drive(cVA+female) - drive(cVA+male)|`, color = which scenario is higher.

\newpage

**One-line figure caption.** The 16 male-specific mAL_m* subtypes encode pheromone encounter identity through differential relay routing (ppk23 / M-cell and ppk25 / F-cell), sign-reversing inhibition, and lateral competition, delivering channel-specific gating of P1 courtship command neurons that propagates the selectivity downstream.
