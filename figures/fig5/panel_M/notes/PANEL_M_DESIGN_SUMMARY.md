# Panel M design synthesis — AN05B035 sign-inverter

## Candidate figures built (all in `panel_M/pdf/`)

- **CE1 stacked bar** — % ppk23 input per mAL routed via AN05B035 vs non-AN05B035 relays. Clear, easy to read at a glance. Descriptive only.
- **CE2 correlation scatter** — AN05B035 input fraction vs ppk23 E/I balance. **R² = 0.423, p = 0.0064, slope = −2.71 (n=16).** Directly quantifies the mechanistic claim.
- **CE3 3-layer bipartite network** — sensilla → relays → mAL. Visually rich but edge-dense.
- **CE4 path counts (2×2)** — per-mAL counts, total strength, mean strength, median hops through/bypassing AN05B035. Descriptive table-like.
- **CE5 counterfactual** — real vs "remove AN05B035" E/I balance, paired arrows. **Mean shift +0.11 toward excitation across all 16 subtypes; 11.9% of ppk23 paths involve AN05B035.** Strong causal-looking narrative.
- **CE6 Sankey** — flow diagram sensilla/relay/target. Pretty but cluttered; relies on pre-aggregated flow, harder to cite specific numbers.
- **CE7 heatmap + bar** — AN05B035→mAL raw synapses aligned with ppk23 E/I bar. Compact, correlation visible by eye.
- **CE8 pie grid** — 4×4 pies of per-mAL relay composition. Visually dense, hard to compare across subtypes.
- **CE9 example traces** — 3 mAL subtypes with their top-10 ppk23 paths drawn. Concrete but anecdotal.
- **CE10 schematic neuron-centric** — my first pass: AN05B035 as a circle with I/O edges colored by sex-bias. Replaced by:
- **M_an05b035_morphology** — **actual neuron skeleton** from MCNS v0.9 (both bodyids 23513 & 517601, ~5.9k nodes each) rendered as 2D XY and XZ projections, with ~14.6k real pre + post synapse locations plotted as points and colored by partner sex-bias. Includes Neuroglancer URL for 3D inspection.

## Ranked recommendation for the main-figure slot between C and E

1. **(M) Morphology + synapse sex-bias** — the real neuron. Best one-shot "here is the inhibitor, here is what it sees and who it writes to" view. Keeps the biology visible.
2. **(M') CE2 correlation scatter** (alternate main, or main if the morphology isn't preferred) — the only figure that gives a testable quantitative prediction with p-value.
3. **(M-SUPP)**: CE5 counterfactual (strongest mechanistic complement), CE1 stacked bar (cleanest descriptive view), CE7 heatmap (alignment with E/I balance), CE3 bipartite (optional overview).

## Proposed (M) caption

**(M) AN05B035 is the GABAergic sign-inverter in the ppk23 → mAL pathway.** Skeletons of the two AN05B035 neurons (bodyids 23513, 517601; MCNS v0.9) shown in XY and XZ projections (dark grey). Synapse locations are overlaid as points: the "input" panels mark where AN05B035 is postsynaptic (~14 k sites), colored by the presynaptic partner's ppk23/ppk25 input bias (red = male-contact-driven source, blue = female, grey = balanced/non-pheromonal); the "output" panels mark where AN05B035 is presynaptic, colored by the postsynaptic target's ppk23 − ppk25 drive. AN05B035 collects predominantly male-leaning input and projects onto male-contact-driven mAL subtypes; because AN05B035 is GABAergic, this pathway delivers the sign-inverted ppk23 signal that produces the Panel C polarity reversal.

## Open questions

- Bias metric uses direct 1-hop adj.matrix contributions, not K-strongest path strength — could be expanded.
- Neurons marked "Roughly traced" — skeleton detail might be incomplete.
- Recommend pairing (M) with CE2 correlation as (M') to carry quantitative weight.
