# Figure 6: Multimodal Sensory Convergence onto Courtship Command Neurons

## Presentation Script — Panel-by-Panel Walk-through

---

## Slide 1 — Title & Big Question

**Multimodal sensory convergence onto courtship command neurons**

Male *Drosophila* courtship is driven by at least seven distinct sensory
channels: three olfactory (DA1/cVA pheromone, VA1v, VA1d), auditory
(JO-B/courtship song), visual (LC10/small-object motion), and two contact
chemosensory (ppk23, ppk25/cuticular pheromones). All of these must
ultimately converge onto a small set of command-like neurons that gate the
decision to court.

**Central question:** How does the connectome route seven parallel sensory
streams onto shared downstream targets — and what circuit motifs emerge at
the points of convergence?

**Approach:** We trace the strongest synaptic paths from every sensory entry
point through the connectome to four groups of downstream targets
(aSP-f, aSP-g, vAB3-downstream, PPN1-downstream), then quantify the
structure of integration at each circuit layer.

---

## Slide 2 — Panel (a): Circuit Architecture

**Three-layer sensory-to-motor circuit schematic**

Panel (a) shows the wiring diagram at the coarsest level:

- **Layer 1 — Sensory inputs (7 channels):**
  - *Olfactory:* DA1 (cis-vaccenyl acetate pheromone receptor neurons),
    VA1v, VA1d (other olfactory receptor neurons implicated in courtship)
  - *Auditory:* JO-B (Johnston's organ mechanosensory neurons responding
    to courtship song)
  - *Visual:* LC10 (lobula columnar neurons tracking small moving objects,
    i.e. another fly)
  - *Contact chemosensory:* ppk23, ppk25 (gustatory receptor neurons on
    the legs detecting cuticular pheromones during tapping)
- **Layer 2 — 2nd-order relay/integrator neurons:** vAB3 and PPN1 are
  well-characterized second-order neurons in the courtship circuit that
  receive direct sensory input
- **Layer 3 — 3rd-order courtship command neurons:** aSP-f and aSP-g are
  sexually dimorphic interneurons implicated in the go/no-go courtship
  decision

Arrow widths in the schematic represent aggregate path strength, already
hinting that some modalities (e.g. DA1) have thicker, more dominant routes
while others (e.g. visual) arrive through more diffuse wiring.

**Key point:** Multiple modalities must funnel through a limited number of
shared relay neurons before reaching the same command neurons. The rest
of the figure asks: what happens at each of these convergence points?

---

## Slide 3 — Panels (b) & (c): Strength and Valence Heatmaps

**Panel (b): Column-normalized modality strength heatmap**

- Matrix: ~36 target neuron types (rows) x 7 modalities (columns)
- Each column is independently scaled to its own maximum, so the heatmap
  shows which targets each modality *preferentially* reaches, rather than
  raw strength
- Rows are clustered (Ward's D2 on Euclidean distance) to group neurons
  with similar modality profiles
- **Row annotations** (left sidebar): target set membership —
  aSP-f (red), aSP-g (blue), vAB3-target, PPN1-target
- **Observations:**
  - Top cluster (LH004m, LH001m, LH008m): bright across DA1, VA1v, VA1d —
    strong olfactory convergence
  - mAL neurons (mAL_m1, mAL_m8, etc.): dominated by DA1 pheromone input
  - Bottom cluster (AVLP488, CB2458, DNp103, AVLP753m, SLP160): weaker
    olfactory input, relatively more auditory/visual contribution
  - ppk23 and ppk25 columns look nearly identical — first hint that these
    two channels share the same downstream wiring

**Panel (c): Excitatory/inhibitory valence heatmap**

- Same row ordering as panel (b), now showing a diverging blue–white–red
  scale: net valence = excitatory strength minus inhibitory strength
- Red tiles: modality reaches that target predominantly through excitatory
  paths; Blue tiles: predominantly inhibitory paths
- **Key patterns:**
  - DA1 column is overwhelmingly red (excitatory) for the top aSP-f/aSP-g
    cluster, but mixed or blue for some lower targets
  - ppk23/ppk25 show complex valence patterns — some targets get excitatory
    contact input, others get inhibitory, revealing that the same pheromone
    signal is being split into push and pull components at this circuit layer

---

## Slide 4 — Panel (d): Selectivity Landscape

**Dominance vs. Lifetime sparseness scatter**

Lifetime sparseness (Rolls & Tovee 1995) quantifies how selective each
target neuron is:
- Sparseness = 1.0: input from exactly one modality (fully unimodal)
- Sparseness ~ 0: perfectly balanced input from all 7 modalities

X-axis: **Dominance** = fraction of total strength contributed by the
single strongest modality. Y-axis: **Lifetime sparseness**.

- Points are **colored** by dominant modality (DA1 = green, ppk23/ppk25 =
  pink/brown, VA1d = orange, visual = purple)
- Points are **shaped** by target set (aSP-f, aSP-g, vAB3-target,
  PPN1-target, vAB3+PPN1 combined)
- Every neuron is individually labeled

**Key findings:**
- Most neurons sit at intermediate sparseness (0.4–0.8) — they are
  multimodal, but not uniformly so. They have a dominant modality with
  subordinate contributions from others
- A handful of neurons approach sparseness ~ 1.0 (top-right corner):
  these are essentially unimodal (typically DA1-dominated)
- The spread is wide within each target set — aSP-f and aSP-g targets
  individually span a range from moderately multimodal to fairly selective
- **Boxplots** (right side) compare sparseness distributions across target
  sets, showing that vAB3 and PPN1 downstream targets have slightly
  different selectivity profiles

---

## Slide 5 — Panels (e), (f), (g): Brain-Space Anatomy

**Panel (e): Mean lifetime sparseness mapped onto brain morphology**

- 3D neuroglancer-style projection of all target neurons, colored by mean
  lifetime sparseness (dark = low sparseness = multimodal; bright = high
  sparseness = unimodal)
- Reveals spatial organization: multimodal neurons tend to cluster in
  specific neuropil regions (lateral horn, AVLP) while unimodal neurons
  are more scattered

**Panel (f): Mean number of modalities per neuron**

- Same anatomical view, now colored by mean number of distinct modalities
  contributing to each neuron (warm/bright = more modalities)
- Highlights the lateral horn and AVLP as hot spots for multimodal
  convergence

**Panel (g): Individual modality maps**

- Six sub-panels showing the spatial extent of each modality's reach:
  DA1, visual, VA1v, ppk23, VA1d, ppk25
- Each map shows where that modality's strongest paths terminate in the
  brain
- **DA1** fills broadly (many targets); **visual** is more spatially
  restricted to AVLP/PVLP regions
- **ppk23** and **ppk25** maps are virtually indistinguishable — confirming
  from an anatomical angle that these two channels share the same wiring

---

## Slide 6 — Panel (h): Modality Similarity Matrices

**Six complementary pairwise similarity metrics between the 7 modalities**

Panel (h) shows a 2x3 grid of 7x7 matrices plus network graph
visualizations:

- **Jaccard similarity** (binary overlap): what fraction of a modality
  pair's union of target neurons is shared?
- **Cosine similarity**: angular similarity of continuous strength vectors
- **Spearman rank correlation**: does modality A's strong targets also
  tend to be modality B's strong targets?
- **Pearson correlation**: linear co-variation of raw strengths
- Plus network graph renderings of significant positive correlations

**Consistent findings across all metrics:**

1. **ppk23 ↔ ppk25: r = 0.96–0.98** — by far the most correlated pair.
   These two contact chemosensory channels converge on a nearly identical
   set of downstream neurons with nearly identical strength profiles.
   Functionally, the circuit treats them almost as a single channel at
   this level.

2. **VA1v ↔ VA1d: r = 0.81–0.92** — the two sister olfactory channels
   also share strong downstream overlap, though less perfectly than
   ppk23/ppk25.

3. **VA1v/VA1d ↔ auditory: r = 0.85–0.92** — auditory input is
   positively correlated with these olfactory channels, suggesting they
   converge onto many of the same targets.

4. **Visual is the outlier:** negative or near-zero correlation with DA1
   (r = -0.65 Pearson) and most other modalities. Visual input reaches a
   largely distinct set of downstream neurons. This makes biological sense:
   LC10 visual motion detection may engage a different behavioral sub-
   circuit than pheromone-driven pathways.

5. **DA1 (cVA pheromone) is partially independent:** moderate positive
   correlation with VA1v (r = 0.38) but anticorrelated with VA1d and
   visual, suggesting DA1 has its own dedicated downstream targets (the
   mAL neurons) that other modalities do not share.

**Network graphs** make this clustering visually intuitive: olfactory +
auditory form one dense cluster, ppk23/ppk25 form a tightly linked pair,
and visual is isolated.

---

## Slide 7 — Panel (i): Path Diversity Across Target Sets

**Mean paths to accumulate 80% of total strength**

For each (target neuron, modality) pair, we ask: how many of the strongest
paths are needed before 80% of total path strength is accounted for?

- **Few paths to 80%** = routing is concentrated through one or two dominant
  pathways (stereotyped, low redundancy)
- **Many paths to 80%** = routing is distributed across many parallel
  pathways (redundant, fault-tolerant)

The bar chart shows this metric across all 7 modalities, grouped by 5
target sets (aSP-f, aSP-g, vAB3, PPN1, vAB3+PPN1) x 2 valences
(excitatory light bars, inhibitory dark bars) = **10 bars per modality**.
Individual data points (jittered dots) show per-neuron values.

**Key findings:**

- **DA1** has the fewest paths to 80% — pheromone information travels
  through a small number of very strong, dedicated pathways (e.g., the
  DA1→mAL relay). This is a stereotyped, channel-like routing.
- **Visual** and **auditory** require more paths — their information is
  distributed across many weaker parallel routes. This may reflect
  more distributed, population-level encoding.
- **Excitatory paths** are generally more concentrated than inhibitory
  paths across all modalities — excitation travels through fewer,
  stronger connections while inhibition is more diffuse.
- **vAB3+PPN1 targets** show intermediate diversity — consistent with
  their position as relay neurons that aggregate from many inputs.
- The large spread of individual dots (especially for auditory, visual)
  indicates substantial heterogeneity: some target neurons receive very
  concentrated input from a modality, while others receive it through
  many distributed routes.

---

## Slide 8 — Panel (j): Spotlight Integrator Neurons

**Best multimodal integrator from each target set**

For each of 5 target sets, we identified the neuron with the highest
Shannon entropy across its 7-modality input profile (requiring input from
at least 3 modalities). These are the circuit's best "multimodal
integrators." Six neurons are spotlighted (vAB3+PPN1 has two):

1. **LH006m** (aSP-f target) — lateral horn neuron receiving broad
   olfactory input plus significant contact chemosensory input.
   Excitatory DA1 dominates but ppk23/ppk25 provide substantial
   inhibitory contribution.

2. **aSP-g3Am** (aSP-g target) — one of the aSP-g neurons itself,
   receiving strong VA1v/VA1d olfactory input with some auditory.
   The fact that a command neuron itself ranks as a top integrator
   confirms that aSP-g performs multimodal integration directly.

3. **AVLP743m** (vAB3 target) — AVLP neuron showing strong visual
   input alongside olfactory. One of the few neurons where visual
   modality contributes substantially, suggesting a visual-olfactory
   integration node.

4. **DNp103** (PPN1 target) — a descending neuron with broad but weak
   input from multiple modalities. Integrates at lower strength levels,
   possibly acting as a gain modulator rather than a primary driver.

5. **LH004m** (vAB3+PPN1 target) — a major lateral horn hub with the
   broadest multimodal profile. Receives input from all 7 modalities,
   heavily dominated by DA1 excitation and strong ppk23/ppk25 input.

6. **AVLP597** (vAB3+PPN1 target) — another broad integrator, showing
   a more balanced excitatory/inhibitory mix across modalities.

**Stacked bar charts** decompose each neuron's input by modality and
valence (blue = excitatory, red = inhibitory), revealing that integration
is not just about which modalities arrive but also about the
excitatory/inhibitory balance of each.

---

## Slide 9 — Panel (k): aSP-f vs. aSP-g Receive Different Modality Mixtures

**Scatter: mean modality strength to aSP-f vs. aSP-g targets**

Each point is one modality; position shows its mean path strength to aSP-f
targets (x-axis) vs. aSP-g targets (y-axis).

**Key observations:**

- If both command neuron populations received identical input, all points
  would fall on the diagonal. They do not.
- **DA1** (cVA pheromone): sits distinctly — relatively stronger to aSP-f
  targets, reflecting the known DA1 → mAL → aSP-f dedicated pathway
- **VA1v and VA1d**: strong to both, but proportionally stronger to aSP-g
- **Auditory**: moderate strength, roughly similar to both sets
- **Visual**: weak to both, but slightly more to aSP-g
- **ppk23/ppk25**: cluster together (as always), with moderate strength
  to both sets

**Implication:** aSP-f and aSP-g, despite being at the same circuit layer
and both gating courtship behavior, receive quantitatively distinct
sensory mixtures. aSP-f is more heavily pheromone-driven (DA1-weighted),
while aSP-g integrates a broader mix of olfactory and auditory cues.
This suggests they may encode different confidence signals or different
aspects of the courtship decision.

---

## Slide 10 — Panel (l): ppk23/ppk25 Nonlinear Interaction Overview

**R_ij waterfall: per-target deviation from linear additivity**

Now we zoom into the two contact chemosensory channels (ppk23, ppk25) and
ask: when both are active simultaneously, does the combined effect on each
target neuron equal the sum of individual effects, or is there a nonlinear
interaction?

**Definition:** R_ij = A(ppk23+ppk25 combined) - A(ppk23 alone) - A(ppk25 alone)
- R_ij < 0: **subadditive** (less than the sum — saturation/occlusion)
- R_ij = 0: **linear** (no interaction)
- R_ij > 0: **superadditive** (more than the sum — synergy/amplification)

Panel (l) shows R_ij for every target neuron, organized by target set
(aSP-f, aSP-g, PPN1 downstream, vAB3 downstream):

- Horizontal bars extend left (subadditive) or right (superadditive)
- Color codes the mechanism: **ceiling saturation** (brown),
  **floor saturation** (pink), **push-pull** (green),
  **upstream saturation** (blue), **weak/indeterminate** (grey)

**Key pattern:** The vast majority of targets show R_ij < 0 (subadditive).
This makes sense: when two excitatory channels converge on the same
intermediate neuron, that intermediate saturates, so the combined effect is
less than the sum. But a handful of targets show R_ij > 0 — these are the
interesting exceptions that require explanation.

---

## Slide 11 — Panel (m): Drive Quadrant Scatter

**Net ppk23 drive vs. net ppk25 drive to each target**

Each point is a target neuron. X-axis: net ppk23 drive (summed across all
paths from ppk23 to that target). Y-axis: net ppk25 drive.

The scatter naturally divides into four quadrants:

1. **Top-right (both excitatory):** ppk23 and ppk25 both excite this
   target through the same intermediaries. When combined, the
   intermediaries saturate → **ceiling saturation → subadditive (destructive)**.

2. **Bottom-left (both inhibitory):** ppk23 and ppk25 both inhibit this
   target. Combined, the intermediary bottoms out →
   **floor saturation → superadditive** (double inhibition can't go below
   zero, so the combined effect is "less inhibitory" than expected, which
   is superadditive in the signed sense).

3. **Top-left and bottom-right (opposite signs):** ppk23 excites but ppk25
   inhibits (or vice versa) via **push-pull topology**. This is the most
   interesting motif: the intermediate neuron receives opposing drives,
   and the resulting interaction can be either superadditive or show
   upstream saturation depending on the circuit details.

**Labeled examples:**
- **mAL_m3c** sits in the "both inhibitory" quadrant — floor saturation
- Several AVLP and LH neurons sit in the push-pull quadrants
- The annotations show that push-pull topology is the dominant mechanism
  for superadditivity

---

## Slide 12 — Panel (n): Intermediary Decomposition

**Linear drive at step 2: which intermediaries carry the signal?**

This horizontal bar chart shows the 15 strongest intermediary neurons
(step 2 in the path), decomposing each into ppk23 drive (gold) and ppk25
drive (brown). Each bar is labeled with its neurotransmitter type
([EXC] or [INH]) and whether ppk23 and ppk25 drive it in the **same** or
**opposite** direction.

**Key observations:**

- **LHAV4c2 [INH]** and **mAL_m5c [INH]**: inhibitory neurons driven in
  the same direction by both channels. These contribute to floor/ceiling
  saturation.
- **AN09B017 variants [EXC]**: a family of excitatory neurons (AN09B017d,
  e, f, g) that are major relays for ppk23/ppk25. All driven in the
  **same** direction — these are classic convergence points where
  saturation occurs.
- **mAL_m1 [INH]**: inhibitory neuron driven in **opposite** direction by
  ppk23 vs. ppk25 — this is a push-pull intermediary. ppk23 excites it
  (via an excitatory path) while ppk25 inhibits it (or vice versa).
- **AN05B023c [INH]** and **mAL_m3c [INH]**: also opposite-direction —
  more push-pull candidates.
- The top intermediary (LHAV4c2) has the strongest linear drive, but the
  push-pull neurons (those labeled "opp") are the ones that generate
  nonlinear amplification downstream.

---

## Slide 13 — Panel (o): The Push-Pull Flip

**R_ij transitions from step 2 (intermediaries) to step 3 (targets)**

This is the central mechanistic result. The plot tracks R_ij at the
intermediary level (step 2) and at the target level (step 3) for key
neurons, with connecting lines showing how the interaction changes as
signals propagate one more synapse.

**Critical observations:**

1. **At step 2 (intermediary level): nearly ALL R_ij < 0.** Whether the
   intermediary is excitatory or inhibitory, convergence of two same-
   direction inputs causes saturation. This is a universal property of
   convergent circuits — there is nothing surprising here.

2. **At step 3 (target level): push-pull neurons FLIP to R_ij > 0.**
   The neurons labeled "Push-pull (SUPER)" show a dramatic sign change
   from negative at the intermediary to positive at the target.

   **Why?** The push-pull intermediary receives ppk23 and ppk25 in
   opposite directions. At the intermediary level, each individual
   channel's drive partially cancels the other, creating subadditivity.
   But when this push-pull intermediary's output is combined with the
   direct excitatory relay at the target, the push-pull provides a
   sharpened contrast signal that amplifies beyond linear summation.

3. **Upstream saturation neurons stay R_ij < 0.** Neurons that simply
   relay saturated signals from intermediaries don't recover — their
   R_ij remains negative from step 2 to step 3.

4. **Ceiling saturation** neurons also stay negative — these receive
   same-direction excitatory input from both channels through relays
   that are already at ceiling.

**The push-pull motif is therefore a circuit-level mechanism that converts
inherent saturating subadditivity into superadditive amplification.** It
works by splitting the two channels into opposing drive on a shared
intermediary, then recombining downstream.

---

## Slide 14 — Panels (p) & (q): Propagation Dynamics and Channel Asymmetry

**Panel (p): delta across propagation steps for AN09B017 family**

This line plot tracks delta = A(both) - A(ppk23) - A(ppk25) across
propagation steps (0 to 3) for the seven AN09B017 variants (a through g),
which are major excitatory intermediaries for ppk23/ppk25 signals.

- At step 0-1: delta is near zero (no interaction at sensory level)
- At step 1-2: delta drops sharply negative — this is where convergence
  occurs and saturation kicks in
- At step 2-3: most variants stay negative (upstream saturation persists
  to target), but some show partial recovery depending on the downstream
  wiring topology

The spread among AN09B017 variants shows that even neurons of the same
type can have different propagation dynamics depending on their specific
downstream connectivity.

**Panel (q): A(ppk23) - A(ppk25) for each AN09B017 variant**

This horizontal bar chart shows the **asymmetry** between ppk23 and ppk25
input strength for each AN09B017 variant:

- **AN09B017g**: strongly ppk25-biased (large positive bar)
- **AN09B017f**: moderately ppk25-biased
- **AN09B017a**: ppk23-biased (negative bar)
- Others show varying degrees of asymmetry

**Key insight:** Even though ppk23 and ppk25 have near-identical downstream
target profiles (r = 0.96-0.98 at the population level), individual
intermediary neurons can show marked ppk23 vs. ppk25 preference. The
circuit maintains channel identity at the intermediary level while merging
the channels at the target level. This two-stage architecture (separate
intermediaries → merged targets) creates the opportunity for push-pull
interactions.

---

## Slide 15 — Synthesis and Key Takeaways

**Six major findings from the connectomic analysis of multimodal convergence:**

1. **Structured multimodality, not random mixing.** Each target neuron has
   a specific modality "recipe" — a dominant input with graded subordinate
   contributions. True equal-weight multimodal integration is rare.

2. **Correlated channel pairs reveal functional grouping.** ppk23/ppk25
   (r=0.98) and VA1v/VA1d (r=0.92) form tightly coupled pairs that the
   circuit routes almost identically. Visual input (LC10) is the most
   independent, reaching a distinct set of targets.

3. **DA1 pheromone has privileged, concentrated routing.** Fewer paths to
   80% strength than any other modality — a dedicated labeled-line-like
   channel amid a multimodal convergence circuit.

4. **aSP-f and aSP-g encode different sensory mixtures.** aSP-f is more
   DA1/pheromone-weighted; aSP-g integrates a broader olfactory+auditory
   mix. Same circuit layer, different integration profiles.

5. **Hidden integration hubs at the intermediate layer** serve as
   multimodal crossroads, distinct from high-throughput single-modality
   relays. These are the true sites of sensory fusion.

6. **Push-pull circuit motifs enable nonlinear amplification.** The
   ppk23/ppk25 channels interact through push-pull intermediaries that
   convert ubiquitous saturating subadditivity into target-level
   superadditivity — a circuit-level mechanism for contrast enhancement
   between the two contact chemosensory pheromone channels.

---

## Slide 16 — Methods at a Glance

- **Connectome data:** Male CNS (male-cns.janelia.org), male *Drosophila* central nervous system connectome
- **Strongest path analysis:** For each (sensory neuron, target) pair, trace
  the path through the connectome that maximizes the product of normalized
  synaptic weights (connection probability)
- **Seven sensory modalities:** DA1, VA1v, VA1d (olfactory ORNs), JO-B
  (auditory), LC10 (visual), ppk23, ppk25 (contact chemosensory)
- **Four target sets:** aSP-f, aSP-g (3rd-order command neurons), vAB3
  downstream, PPN1 downstream (2nd-order relay targets)
- **Valence assignment:** Based on presynaptic neurotransmitter identity —
  ACh/glutamate = excitatory; GABA/glycine/histamine = inhibitory
- **Selectivity metrics:** Lifetime sparseness (Rolls & Tovee 1995),
  Shannon entropy, dominance fraction
- **Similarity metrics:** Pearson, Spearman, Jaccard, Cosine (all pairwise)
- **Nonlinear interaction:** R_ij = A(ppk23+ppk25) - A(ppk23) - A(ppk25),
  decomposed by propagation step, classified by intermediary topology
  (push-pull, ceiling/floor saturation, upstream saturation)
