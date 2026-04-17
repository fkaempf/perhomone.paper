---
title: "Figure 5 (male-specific variant) v10"
subtitle: "16 male-specific mAL_m* subtypes; 12-panel story arc. Each figure + caption on one page; main panels bordered red, supps unbordered."
author: "Story arc: A -> B -> C -> M -> E -> K -> G -> F -> L -> D -> J -> I"
geometry: margin=0.75in
fontsize: 10pt
header-includes:
  - \usepackage{graphicx}
  - \usepackage{float}
  - \usepackage{xcolor}
  - \usepackage[export]{adjustbox}
  - \usepackage{titlesec}
  - \titleformat{\section}[display]{\vspace*{3.5cm}\centering\Huge\bfseries}{}{0em}{}
  - \titlespacing*{\section}{0pt}{0pt}{0.5cm}
  - \newcommand{\sectionbreak}{\clearpage}
  - \setlength{\parskip}{0.3em}
  - \setlength{\parindent}{0pt}
  - \setlength{\intextsep}{4pt plus 1pt minus 1pt}
  - \setlength{\textfloatsep}{4pt plus 1pt minus 1pt}
  - \newcommand{\mainpanel}[1]{\begin{figure}[H]\centering\adjustbox{cfbox=red 2pt 0pt,max width=\linewidth,max height=0.62\textheight,keepaspectratio}{\includegraphics{#1}}\end{figure}}
  - \newcommand{\suppfig}[1]{\begin{figure}[H]\centering\adjustbox{max width=\linewidth,max height=0.62\textheight,keepaspectratio}{\includegraphics{#1}}\end{figure}}
---

# A. mAL sensory input profiles

\mainpanel{../single panels/panel_A_input_profiles_raw.pdf}

*Terms used throughout this figure: mAL_m\* = the 16 male-specific mAL interneuron subtypes (this figure's subject); `ppk23` = male-contact-pheromone sensory channel (7-T / M cells, gustatory contact sensilla on legs); `ppk25` = female-contact-pheromone channel (7,11-HD / F cells); `DA1` = cVA volatile-pheromone olfactory channel. The 7 channels plotted in (A) are ppk23, ppk25, DA1 and four additional olfactory/sensory modalities (VA1v, VA1d, auditory, visual). "Path-based drive" denotes the net K-strongest-path strength (exc minus inh) used throughout this figure.*

**(A) Male-specific mAL is not monolithic.** Hierarchically-clustered heatmap of net path-based drive across 7 channels for all 16 mAL_m subtypes. Cell = `strength_exc - strength_inh` where each direction is the sum of path-strength products over the K-strongest cached paths. ppk23-biased (male-contact), ppk25-biased (female-contact), olfactory, and multimodal subgroups emerge within the male-only subset.

\clearpage

\suppfig{../single panels/panel_A_input_profiles_raw_synapses.pdf}

**(A-SUPP-1) Widest-path raw synapse counts.** Controls for the aggregation mechanics of (A). For each (modality, mAL) pair, compute the bottleneck (minimum raw synapse count along the path) for every cached path, pick the single widest per valence, and take excitatory minus inhibitory. Cell units are raw synapse counts. Answers "what is the best single pathway that the modality could use to reach this mAL, measured by the weakest edge's synapse count?"

\clearpage

\suppfig{../single panels/panel_A_input_profiles_max_flow.pdf}

**(A-SUPP-2) Max-flow with raw synapses.** Graph-theoretic generalization of (A-SUPP-1). Build the subgraph induced by all cached paths with raw synapse counts as edge capacities; connect a virtual super-source to every source sensillum of the modality with infinite capacity; compute max-flow from super-source to target mAL. Cell = exc max-flow - inh max-flow. Accounts for parallel routes and shared-edge bottlenecks that (A-SUPP-1) ignores. **Caveat:** standard max-flow does not penalize path length — a long weak chain contributes the same as a short strong one if their bottlenecks match.

\clearpage

\suppfig{../single panels/panel_A_input_profiles_max_flow_normed.pdf}

**(A-SUPP-3) Max-flow with input-normalized capacities.** Same max-flow procedure as (A-SUPP-2) but edge capacities are the input-normalized adjacency (fraction of the postsynaptic neuron's total input contributed by the presynaptic type) instead of raw synapse counts. Units match panel A's path-strength products, so this is the most direct max-flow comparator to (A).

\clearpage

\suppfig{../single panels/panel_A_input_profiles_topK_sum.pdf}

**(A-SUPP-4) Sum of top-10 widest bottlenecks per valence.** For each (modality, mAL, valence) triple, select the 10 paths with highest bottleneck and sum their bottleneck synapse counts; cell = exc sum - inh sum. Treats paths as parallel pipes carrying independent signals. Intermediate between the single-widest (A-SUPP-1) and the full max-flow (A-SUPP-2); risk of double-counting when paths share bottleneck edges.

\clearpage

\suppfig{../single panels/panel_A_input_profiles_topK_mean.pdf}

**(A-SUPP-5) Mean of top-10 widest bottlenecks per valence.** Same top-10 selection as (A-SUPP-4), but mean instead of sum. Represents "typical capacity of the strongest K routes" — deflates when many good routes exist and amplifies when only one or two strong routes dominate. Less noisy than the sum; arguably the information you want reflected if route redundancy matters.

\clearpage

# B. AN09B017 relay selectivity

\mainpanel{../single panels/panel_B_an09b017_selectivity.pdf}

**(B) AN09B017 ascending neurons tile a ppk23/ppk25 selectivity spectrum.** Scatter of ppk23 vs ppk25 input per AN09B017 variant (a-g; M-cell = ppk23 contact-sensilla, F-cell = ppk25 contact-sensilla). Variants span a broad ppk23-to-ppk25 bias range, with some strongly ppk23-preferring (AN09B017a receives the most ppk23 input per narrative) and others strongly ppk25-preferring (AN09B017g receives the most ppk25 input). Channel separation of male vs female contact pheromone begins in the ascending relay layer.

\clearpage

\mainpanel{../single panels/panel_B_an09_dominance_vs_ppk_asymmetry_v6.pdf}

**(B') AN09B017 input composition per mAL vs ppk asymmetry.** Each mAL_m subtype is drawn as a pie chart at position (x = ppk23 path-based drive minus ppk25 path-based drive, y = % of mAL's total input from all AN09B017 variants combined). Pie slices show the fraction contributed by each AN09B017 variant (a-g). Soft quadrant backgrounds label interpretation regions: top-right = male-contact-driven + strong AN09B017 input; top-left = female-contact-driven + strong AN09B017 input; bottom halves = weak AN09B017 involvement. Dashed guide lines mark `ppk23 - ppk25 = 0` (channel-balanced) and the median AN09B017 coupling.

\clearpage

\suppfig{../single panels/panel_B_selectivity_ratio.pdf}

**(B-SUPP) Log2 ppk23/ppk25 ratio per AN09B017 variant.** Bar quantification of the selectivity spectrum from (B), variants ordered by ratio. Positive bars = male-biased variants, negative = female-biased. Moved from main to supplementary in favor of the per-mAL pie-scatter (B').

\clearpage

# C. Male-contact sign reversal

\mainpanel{../single panels/panel_C_ppk23_sign_reversal.pdf}

**(C) Male contact (ppk23) signal excites some mAL subtypes and inhibits others.** Paired bars of ppk23 vs ppk25 path-based drive per mAL_m subtype. All 16 receive positive ppk23 drive (peak mAL_m3c ~ 0.11); sign reversal at specific subtypes arises from a GABAergic ascending neuron (AN05B035) whose morphology and pool identity are dissected in panel M.

\clearpage

\mainpanel{../single panels/panel_C_ppk23_vs_ppk25_scatter.pdf}

**(C') ppk23 vs ppk25 per-subtype scatter.** Each dot = one mAL_m subtype; x = ppk23 path-based drive (male contact), y = ppk25 path-based drive (female contact). Color = neurotransmitter identity. Dashed lines mark x = 0, y = 0; dotted line is the y = x diagonal. Subtypes below the diagonal are ppk23-dominant (male-contact-biased); above = ppk25-dominant (female-contact-biased); distance from origin = total ppk drive magnitude. Complements the paired-bar view in (C).

\clearpage

# M. GABA sign-inverter pool: mechanistic substrate of sign reversal

\mainpanel{../single panels/panel_M_morphology_AN05B035.pdf}

**(M) AN05B035 is the highest-throughput member of the GABA sign-inverter pool.** Skeleton morphology of AN05B035 (n=2 bodyids, 23513 and 517601), top contributor to an 11-member GABAergic sign-inverter (SI) pool (AN05B021, AN05B023a, AN05B023b, AN05B023c, AN05B023d, AN05B025, AN05B035, AN05B050_a, IN05B002, IN05B011a, IN05B011b; AN = ascending neuron, IN = intrinsic interneuron) that carries the GABAergic sign inversion from ppk23/ppk25 contact sensilla to mAL_m targets. Three-panel row: (1) inputs in T1 leg neuromere (dorsal view) where ppk23/ppk25 contact sensory input arrives, (2) inputs in the SEZ (frontal view), (3) outputs in the SEZ onto mAL_m (frontal view). Synapses are colour-coded by partner channel (ppk23-sensillum, ppk25-sensillum, ppk23/ppk25-biased relay or mAL_m target, other) so each channel reads off independently. The other 10 pool members carry the same motif at lower throughput. Mechanistic substrate of the sign reversal summarised in panels C and E.

\clearpage

\mainpanel{../single panels/panel_M_si_channel_scatter.pdf}

**(M') Per-SI ppk23 vs ppk25 input strength.** Each point is one of the 11 GABA SI pool members; x and y are summed top-50 path-based strengths from ppk23 and ppk25 contact-sensilla sensory neurons (gustatory ORNs on leg sensilla) onto that SI as endpoint. Channels are tightly coupled at the pool level (n=11, Pearson r=0.879, p=0.000369; Spearman rho=0.555, p=0.0767; OLS log-log slope=0.890, R^2=0.772), but individual SIs split their bias: 8/11 are ppk23-biased (below y=x) and 3/11 are ppk25-biased (above). Points near the diagonal are channel-symmetric 'dual-channel' sign-inverters that can route inhibition from either contact-pheromone context onto mAL_m. Complemented by the channel-agnostic downstream view in (M-SUPP-c).

\clearpage

\mainpanel{../single panels/panel_M_si_vs_other_contribution.pdf}

**(M'') SI-traversing vs non-SI partition of ORN -> mAL_m drive.** For each (channel, mAL_m) pair the top-50 strongest ORN -> mAL_m paths are partitioned by whether any interior node is a member of the 11-member GABA SI pool; stacked bars give SI-traversing vs non-SI totals. At the channel level, 22.1% of total ppk23 drive (raw SI strength 0.351) and 19.5% of total ppk25 drive (raw SI strength 0.273) route through the SI pool. Top-5 (channel, mAL_m) pairs by SI fraction: mAL_m1 ppk25 (29.4%), mAL_m10 ppk23 (29.1%), mAL_m1 ppk23 (28.8%), mAL_m2b ppk23 (28.7%), mAL_m5a ppk25 (28.4%); lowest is mAL_m3b ppk25 (7.1%). Direct readout of which mAL_m subtypes are most inhibition-routed, pairing with (C) and (E) to pinpoint targets at risk of sign reversal.

\clearpage

\suppfig{../single panels/panel_M_example_traces_supp.pdf}

**(M-SUPP-a) Example ppk23 -> mAL_m path traces spanning the E/I range.** Top-10 strongest ppk23 -> mAL paths drawn for three mAL_m subtypes spanning the ppk23 E/I extremes (E/I balance index `(exc - inh) / (exc + inh)`, range [-1, +1]; see (E')): mAL_m10 (most ppk23-inhibited, E/I=+0.04, SI fraction 29%), mAL_m8 (balanced, E/I=+0.12, SI fraction 23%) and mAL_m3b (most ppk23-excited, E/I=+0.40, SI fraction 13%). Red edges = paths not traversing the 11-member GABA SI pool; blue edges = paths routed through at least one SI. Edge width scales with path strength, node size with top-10 path overlap. The inhibited subtype is dominated by blue SI edges, the excited subtype by red direct / AN09B017 routes, the balanced case mixes both.

\clearpage

\suppfig{../single panels/panel_M_example_traces_ppk25_supp.pdf}

**(M-SUPP-b) Example ppk25 -> mAL_m path traces (F-cell counterpart).** Same top-10 trace format as (M-SUPP-a) but for ppk25, with three mAL_m spanning the ppk25 E/I range: mAL_m1 (most ppk25-inhibited, E/I=+0.39, SI fraction 29%), mAL_m2b (balanced, E/I=+0.43, SI fraction 19%) and mAL_m3b (most ppk25-excited, E/I=+0.67, SI fraction 7%). The 11-member GABA SI pool sits on the sign-inverting route for both pheromone channels; channel-specific SI routing across mAL_m targets produces the ppk23 vs ppk25 E/I asymmetries in panels C and E.

\clearpage

\suppfig{../single panels/panel_M_mal_by_si_input_supp.pdf}

**(M-SUPP-c) mAL_m subtypes ordered by GABA SI-pool input.** 16 male-specific mAL_m subtypes ranked by total SI-driven path strength, stacked by SI pool member identity. Bars come from a top-50 path computation with the SI as source and mAL_m as target, so the ORN -> SI prefix is dropped and bar height reflects each SI's downstream reach. Top targets: mAL_m1 (0.177), mAL_m5a (0.173), mAL_m2a (0.122). Channel-agnostic complement to (M'), which attributes channel bias on the input side.

\clearpage

# E. E/I decomposition of ppk drive

\mainpanel{../single panels/panel_E_valence_bars.pdf}

**(E) E/I balance determines polarity.** Stacked bars decomposing ppk23 and ppk25 input into excitatory (red) and inhibitory (blue) path components per mAL_m subtype. Every subtype carries both; sign reversal in (C) reflects which arm dominates, not absent excitation.

\clearpage

\mainpanel{../single panels/panel_E_ei_balance_scatter.pdf}

**(E') E/I balance scatter.** Each mAL_m subtype plotted by ppk23 (x) and ppk25 (y) E/I balance index = `(exc - inh) / (exc + inh)`, range [-1, +1]. All 16 male-specific subtypes are net excitatory on both channels (mean balance ppk23 = 0.314, ppk25 = 0.424); ppk25 is systematically less inhibition-weighted than ppk23, consistent with AN05B035 relaying ppk23 specifically. mAL_m5a (ppk23 balance 0.04) sits one modest weight change from flipping into ppk23 inhibition.

\clearpage

# K. Relays to mAL

\mainpanel{../single panels/panel_K_heatmap.pdf}

**(K) Relays route channels to specific mAL subsets.** Input-normalized connectivity of AN09B017a-g + AN05B035 to the 16 male-specific mAL_m subtypes, rows annotated by relay ppk23/ppk25 bias, columns by mAL dimorphism. Completes the labeled-line motif: M-cell (ppk23) -> AN09B017 subset -> specific mAL_m; F-cell (ppk25) -> different AN09B017 subset -> different mAL_m.

\clearpage

\suppfig{../single panels/panel_K_heatmap_raw.pdf}

**(K-SUPP) Raw synapse count variant of (K).** Same rows and columns, but cell = raw synapse count from the raw (non-normalized) adjacency matrix instead of input-normalized fraction. Useful for seeing which relay-to-mAL connections carry many synapses in absolute terms; large cells correspond to anatomically prominent connections.

\clearpage

# G. Lateral mAL<->mAL architecture

\mainpanel{../single panels/panel_G_lateral_heatmap.pdf}

**(G) Lateral mAL<->mAL connectivity (raw synapses).** Signed synapse-count heatmap among the 16 mAL_m subtypes; 125 edges, 76% GABAergic. Rows = presynaptic mAL, columns = postsynaptic mAL. Blue = GABAergic (inhibitory), red = non-GABA (excitatory) presynaptic contribution.

\clearpage

\mainpanel{../single panels/panel_G_hub_analysis.pdf}

**(G') Lateral inhibition hubs.** Per-subtype ranking of inhibitory output and input. mAL_m1, mAL_m5a and mAL_m4 are the dominant inhibitory outputs (top-3 by summed inhibitory output); mAL_m5b, mAL_m5c and mAL_m2b receive the heaviest lateral inhibition. Drive magnitude does not predict inhibition received (Spearman rho = 0.32), so lateral competition sharpens the code independently of input strength.

\clearpage

\suppfig{../single panels/panel_G_lateral_heatmap_normed.pdf}

**(G-SUPP) Input-normalized variant of (G).** Same topology as (G) but cells now represent the fraction of each postsynaptic mAL's total input coming from each presynaptic mAL (signed by presynaptic NT). Reveals which postsynaptic mAL subtypes are DOMINATED by lateral input (high row-fraction to any mAL) vs those that receive mostly non-mAL input.

\clearpage

# F. Three-scenario population signatures

\mainpanel{../single panels/panel_F_parallel_coordinates.pdf}

**(F) Three pheromone encounters produce distinct population signatures (path-based drive).** For each mAL_m subtype (x-axis), three lines give summed path-based drive under Female (red, ppk25), cVA+male (purple, DA1+ppk23), cVA+female (orange, DA1+ppk25). Several mAL_m subtypes show pronounced differential activation across the three scenarios; the top-3 ppk25-gainers (cVA+female vs cVA+male) per narrative are mAL_m2a, mAL_m2b and mAL_m3b.

\clearpage

\mainpanel{../single panels/panel_F_sf_parallel_coordinates.pdf}

**(F') Same scenarios under the signal-flow model.** Iterative nonlinear propagation with rectified-tanh activation `max(0, tanh(beta*x))` (beta = 5; see (I)) applied to each scenario's channel activation. Same scenario-discriminators as (F), confirming the population signatures are not artifacts of the linear sum.

\clearpage

# L. ppk selectivity: mAL and P1 in shared coordinates

\mainpanel{../single panels/panel_L_mal_and_p1_ppk_selectivity.pdf}

**(L) Channel selectivity propagates from mAL to P1 (path-based).** x = ppk23 path-based drive (male contact), y = ppk25 path-based drive (female contact). P1 = male-courtship command neurons downstream of mAL. Overlays both layers in one coordinate system: 16 mAL_m subtypes (blue circles) and 45 P1 subtypes (red triangles), equal aspect with y=x diagonal overlaid. Directly shows how channel selectivity propagates from the mAL layer to the downstream P1 courtship command neurons. Per-layer breakouts in (L-SUPP-a..d).

\clearpage

\mainpanel{../single panels/panel_L_mal_and_p1_sf_ppk_selectivity.pdf}

**(L') Same overlay under the signal-flow model.** x = ppk23 alone signal-flow net input, y = ppk25 alone signal-flow net input. Confirms the path-based picture under nonlinear iterative propagation; ppk selectivity is preserved at both mAL and P1 layers.

\clearpage

\suppfig{../single panels/panel_L_mal_ppk_selectivity_supp.pdf}

**(L-SUPP-a) Panel L mAL-only, path-based.** Path-based ppk23 vs ppk25 drive scatter for the 16 male-specific mAL subtypes only, each point labeled by subtype name. Subsumed by (L) but shown standalone to see the mAL layer's positioning without the P1 overlay compressing the axis range.

\clearpage

\suppfig{../single panels/panel_L_mal_sf_ppk_selectivity_supp.pdf}

**(L-SUPP-b) Panel L mAL-only, signal-flow.** Same 16 mAL subtypes as (L-SUPP-a), but both axes use the signal-flow net input (iterative nonlinear propagation): x = mAL drive under ppk23 alone, y = mAL drive under ppk25 alone. Reveals where each subtype sits under the iterative nonlinear model without P1 points.

\clearpage

\suppfig{../single panels/panel_L_p1_ppk_selectivity_supp.pdf}

**(L-SUPP-c) Panel L P1-only, path-based.** Path-based ppk23 vs ppk25 drive for all 45 P1 subtypes. P1 drive = mAL channel activations propagated through signed mAL -> P1 connectivity, with GABAergic mAL contributing negatively. Each point is one P1 subtype.

\clearpage

\suppfig{../single panels/panel_L_p1_sf_ppk_selectivity_supp.pdf}

**(L-SUPP-d) Panel L P1-only, signal-flow.** Same 45 P1 subtypes as (L-SUPP-c), using signal-flow net input (iterative nonlinear model) for both axes. Shows ppk selectivity structure at the P1 layer under the iterative nonlinear model — directly validates the path-based P1 picture in (L-SUPP-c).

\clearpage

# D. mAL -> P1 gating

\mainpanel{../single panels/panel_D_mal_to_p1.pdf}

**(D) mAL delivers channel-specific P1 gating (raw synapses).** Biclustered signed synapse-count heatmap of mAL_m -> P1 (P1 = male-courtship command neurons downstream of mAL). Sign applied by presynaptic NT (GABAergic = negative). Block-diagonal structure: mAL_m1 is the dominant inhibitory hub (strongest single connection mAL_m1 -> P1_3c at 723 synapses per narrative) while mAL_m3a/b are net excitatory. Graded labeled-line gate rather than a binary switch.

\clearpage

\mainpanel{../single panels/panel_D_total_drive.pdf}

**(D') Total mAL drive per P1 subtype.** Stacked bars summing signed mAL_m -> P1 weights across all mAL sources per P1. Net drive is inhibitory for most P1s, with a handful at near-zero or net-excitatory drive.

\clearpage

\suppfig{../single panels/panel_D_mal_to_p1_normed.pdf}

**(D-SUPP) Input-normalized variant of (D).** Same mAL x P1 structure as (D), but each cell now = fraction of the postsynaptic P1 neuron's total input contributed by that mAL type (signed by NT). Controls for differences in P1 total synapse count across subtypes, making connection strength directly comparable across P1s.

\clearpage

# J. P1 per-scenario drive & cVA gain

\mainpanel{../single panels/panel_J_cva_delta_scatter.pdf}

**(J) cVA gain per P1 courtship command neuron.** 45 P1 subtypes. x = Delta drive when cVA is added to female contact `drive(DA1+ppk25) - drive(ppk25)`. y = same for male contact `drive(DA1+ppk23) - drive(ppk23)`. Dashed y = x is the linear prediction. Off-diagonal spread reveals P1s whose cVA sensitivity depends on the context pheromone.

\clearpage

\mainpanel{../single panels/panel_J_per_p1_bars.pdf}

**(J') Predicted P1 drive under the three encounter scenarios.** For each of 45 P1 subtypes (x-axis), three stacked bars give predicted drive under Female (ppk25), cVA+male (DA1+ppk23), cVA+female (DA1+ppk25); drive derived by propagating each scenario's mAL channel activation through signed mAL -> P1 connectivity. Per-P1 inhibition-vs-excitation distribution shifts with encounter type.

\clearpage

# I. Two-model convergence and P1 generalization

\mainpanel{../single panels/panel_I_combined.pdf}

**(I) Two models agree on the mAL population code.** 2x2 grid: three per-scenario scatters of path-based (x) vs signal-flow (y) mAL drive, one facet per scenario, with y=x diagonal overlaid and Spearman rho printed per facet. Fourth tile: the rectified-tanh activation function `max(0, tanh(beta*x))` with `beta = 5`, used in the signal-flow iterations. Overall rho ~0.65 across all 48 subtype-scenario pairs (16 mAL x 3 scenarios), 75% sign agreement.

\clearpage

\mainpanel{../single panels/panel_I_mal_and_p1_spread_scatter.pdf}

**(I') Model agreement extends from mAL to P1.** For each mAL (blue circles) and P1 (red triangles) subtype, plot mean path-based drive (x) vs mean signal-flow drive (y), averaged across the three scenarios. Point size = joint spread across scenarios `sqrt(var_path + var_sf)` — a per-subtype measure of how much the scenario condition matters. Both populations cluster near the y=x diagonal at mean level, and the scenario-discriminating subtypes in both populations are the ones with large points.

\clearpage

\suppfig{../single panels/panel_I_scenario_heatmap_supp.pdf}

**(I-SUPP-a) mAL 3-scenario signal-flow heatmap.** 3 scenarios (rows) x 16 mAL_m subtypes (columns), cells = signal-flow net input (iterative nonlinear model), blue-white-red diverging. Columns clustered by response similarity. A direct table view of the data summarized as trajectories in (F') and (I); identifies which specific mAL subtypes are strongly activated or inhibited by each encounter.

\clearpage

\suppfig{../single panels/panel_I_p1_scenario_heatmap_supp.pdf}

**(I-SUPP-b) P1 3-scenario signal-flow heatmap.** Same format as (I-SUPP-a) but for 45 P1 subtypes. Reveals which P1 command neurons are excited or suppressed by each encounter type; clusters highlight P1 groups with shared response profiles.

\clearpage

\suppfig{../single panels/panel_I_p1_combined_supp.pdf}

**(I-SUPP-c) P1 version of the Panel I 2x2 grid.** Mirrors main (I) but at the P1 layer. Three per-scenario scatters of path-based vs signal-flow P1 drive with Spearman rho per facet, plus the activation function inset. Shows that the two-model agreement demonstrated at mAL (in the main panel) carries through to downstream P1 courtship command neurons.

\clearpage

\suppfig{../single panels/panel_I_mal_scenario_spread_bar_supp.pdf}

**(I-SUPP-d) mAL scenario spread bar.** One bar per mAL_m subtype, height = max - min drive across the 3 scenarios (signal-flow net input). Bar color = which scenario gives the highest drive (argmax). Sorted left-to-right by spread, so the most scenario-discriminating mAL_m subtypes are at the left. Legend includes all 3 scenarios even when one never wins argmax.

\clearpage

\suppfig{../single panels/panel_I_mal_scenario_trajectories_supp.pdf}

**(I-SUPP-e) Top-15 most scenario-discriminating mAL subtypes.** For the 15 mAL_m with largest spread, plot drive under Female -> cVA+male -> cVA+female as a connected line (one line per subtype, labeled). Shows the direction of scenario-induced shifts: subtypes with positive slopes gain drive when DA1 is added, those with flipping signs cross zero between scenarios.

\clearpage

\suppfig{../single panels/panel_I_p1_scenario_spread_bar_supp.pdf}

**(I-SUPP-f) P1 scenario spread bar.** Same metric and format as (I-SUPP-d) but for all 45 P1 subtypes. Identifies which P1 courtship command neurons shift most across encounter types, and which scenario each is tuned to.

\clearpage

\suppfig{../single panels/panel_I_p1_scenario_spread_scatter_supp.pdf}

**(I-SUPP-g) P1 mean-drive vs spread.** Each P1 subtype plotted at (mean drive across scenarios, spread across scenarios); point size = spread; color = argmax scenario. Separates "strongly active but scenario-insensitive" P1s (high x, low y) from "strongly context-sensitive" P1s (high y). Complements the bar view in (I-SUPP-f).

\clearpage

\suppfig{../single panels/panel_I_p1_scenario_trajectories_supp.pdf}

**(I-SUPP-h) Top-15 most scenario-discriminating P1 subtypes.** Same format as (I-SUPP-e) but for the top 15 P1 subtypes by spread. Labels at the rightmost scenario.

\clearpage

\suppfig{../single panels/panel_I_mal_cva_mvf_bar_supp.pdf}

**(I-SUPP-i) Focused mAL cVA+male vs cVA+female spread.** Restricts the spread analysis to the two cVA-containing scenarios (cVA+male = DA1+ppk23; cVA+female = DA1+ppk25). Bar height = `|drive(DA1+ppk25) - drive(DA1+ppk23)|` per mAL_m subtype. Isolates "how much F-cell (ppk25) input matters when cVA is present" from all other scenario-level differences. Bar color = which of the two scenarios gives the higher drive.

\clearpage

**One-line figure caption.** The 16 male-specific mAL_m* subtypes encode pheromone encounter identity through differential relay routing (ppk23 / M-cell and ppk25 / F-cell), sign-reversing inhibition via the GABAergic AN05B035-led SI pool, and lateral competition, delivering channel-specific gating of P1 courtship command neurons that propagates the selectivity downstream (A -> B -> C -> M -> E -> K -> G -> F -> L -> D -> J -> I).
