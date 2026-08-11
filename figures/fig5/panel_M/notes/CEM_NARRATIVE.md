# Panels C, E, M — The Corrected Dual-Channel Sign-Inverter Story

## 1. Overview — AN05B035 is a dual-channel GABAergic inverter

The original Figure 5 narrative framed AN05B035 as the ppk23-specific sign
inverter that rerouted male-cuticular signals onto an inhibitory relay. A full
re-audit of the direct sensillum-to-relay connectivity shows this framing was
incomplete. AN05B035 receives direct input from BOTH contact-pheromone
channels: approximately **1833 synapses from ppk23 sensory neurons** and
**1088 synapses from ppk25 sensory neurons** onto the two AN05B035 cells
(bodyids 517601, 23513). The path-level accounting is similarly balanced —
**2622 ppk23-rooted paths** and **2603 ppk25-rooted paths** through the
AN05B035 bottleneck — essentially one-to-one. Because AN05B035 is GABAergic,
*both* channels acquire a disynaptic inhibitory route via this single relay.
The correct claim is therefore: AN05B035 is a dual-channel inverter that
imposes a GABAergic shadow on both male and female contact-pheromone signals,
and the asymmetry seen downstream at mAL reflects how much of each channel's
drive the downstream subtype reads out through this shared relay — not that
the relay is ppk23-selective.

## 2. Panel C — why the visible sign flip lives on ppk23

Panel C plots paired net path strength (ppk23 vs ppk25) across the
male-specific mAL_m subtypes and colours each subtype by its E/I quadrant.
The sign reversal — subtypes whose ppk23 drive tips below zero while ppk25
stays positive — is read off the ppk23 axis because that is where the
inhibitory-dominant and excitatory-dominant routes separate cleanly in the
male-specific subset. ppk25 net drive stays net-positive across almost all
mAL_m subtypes, which is why panel C does not *visualize* a ppk25 sign flip.
That visual absence does not mean ppk25 escapes the inverter: it means that
for ppk25 the excitatory bypass routes (direct + AN09B017-a..e-mediated) are
strong enough to outweigh the AN05B035 inhibitory contribution at the net
level. The inhibitory component from AN05B035 is still present in ppk25 — it
just loses the arithmetic. Panel C should now be read as "where the ppk23
balance crosses zero," not "where AN05B035 acts."

## 3. Panel E — E/I decomposition with AN05B035 attribution

Panel E decomposes each mAL_m subtype's net path strength into its
excitatory and inhibitory components (panel_E_valence_bars.pdf) and plots
the per-subtype E/I ratios for ppk23 vs ppk25
(panel_E_ei_balance_scatter.pdf). The new
**panel_M_E_inhibition_attribution.pdf** adds the crucial next layer:
within each subtype's inhibitory bar, the fraction attributable to paths
traversing AN05B035 is separated from inhibition contributed by other
relays. For ppk23, AN05B035 dominates the inhibitory budget — counterfactual
removal of AN05B035 paths shifts the mean ppk23 E/I balance by **+0.110**
toward excitation, with 15/16 subtypes pushed positive. For ppk25, AN05B035
contributes a measurable but smaller fraction of total inhibition because
additional inhibitory relays also feed the ppk25 branch; AN05B035 is a
component, not the sole author, of ppk25 inhibition.

## 4. Panel M — morphology makes the dual-channel readout concrete

Panel M shows the AN05B035 skeleton with every input and output synapse
colour-coded by the partner cell type's ppk23/ppk25 bias (red = ppk23-driven,
blue = ppk25-driven, grey = balanced). The dendrite carries interleaved red
and blue input synapses — direct visual evidence that the two channels
converge on the same GABAergic neuron — and the axon projects the merged,
sign-inverted signal onto downstream partners. Panel M is the anatomical
substrate behind the path counts in the overview and the attribution split
in panel E.

## 5. Revised one-line claim for main text

"AN05B035 is a GABAergic ascending neuron that receives direct input from
both the ppk23 and ppk25 contact-pheromone channels (approx. 1833 and 1088
sensillum synapses, 2622 vs 2603 paths) and imposes a sign-inverting
inhibitory shadow on both, with the net behavioural readout at mAL
determined by how much of each channel a given subtype draws through the
inverter versus around it."

---

## Executive summary (~150 words)

AN05B035 was originally cast as the ppk23-specific GABAergic sign inverter,
but direct synapse and path accounting show it is a **dual-channel** relay:
about 1833 ppk23 and 1088 ppk25 sensillum synapses, and 2622 vs 2603
pheromone-rooted paths — effectively balanced. Because AN05B035 is
GABAergic, both male (ppk23) and female (ppk25) contact-pheromone signals
acquire an inhibitory route through it. Panel C displays a visible sign
reversal only on ppk23 because the ppk25 excitatory bypass outweighs its
AN05B035 inhibition at the net level, not because ppk25 escapes the relay.
Panel E, augmented by the new attribution plot, confirms AN05B035 dominates
ppk23 inhibition but contributes only a share of ppk25 inhibition, which
has additional relays. Panel M anatomically grounds the story by showing
both ppk23- and ppk25-biased inputs converging on the same dendrite. The
revised claim: AN05B035 inverts both channels; mAL polarity depends on
through-versus-around routing.
