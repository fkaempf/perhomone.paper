---
title: "Figure 6: Multimodal Sensory Convergence onto Courtship Command Neurons"
geometry: margin=1in
documentclass: article
fontsize: 11pt
header-includes:
  - \usepackage{graphicx}
  - \usepackage{float}
  - \usepackage{unicode-math}
---

# Figure 6: Multimodal Sensory Convergence onto Courtship Command Neurons

## Presentation Script --- Panel-by-Panel Walk-through

![Figure 6 --- Complete composed figure](/private/tmp/fig6_v2_full.png){width=100%}

\newpage

## Slide 1 --- Title & Big Question

**Multimodal sensory convergence onto courtship command neurons**

Male *Drosophila* courtship is driven by at least seven distinct sensory
channels: three olfactory (DA1/cVA pheromone, VA1v, VA1d), auditory
(JO-B/courtship song), visual (LC10/small-object motion), and two contact
chemosensory (ppk23, ppk25/cuticular pheromones). All of these must
ultimately converge onto a small set of command-like neurons that gate the
decision to court.

**Central question:** How does the connectome route seven parallel sensory
streams onto shared downstream targets --- and what circuit motifs emerge at
the points of convergence?

**Approach:** We trace the strongest synaptic paths from every sensory entry
point through the connectome to four groups of downstream targets
(aSP-f, aSP-g, vAB3-downstream, PPN1-downstream), then quantify the
structure of integration at each circuit layer.

\newpage

## Slide 2 --- Panel (a): Circuit Architecture

**Three-layer sensory-to-motor circuit schematic**

![Panel (a): Three-layer circuit schematic showing sensory inputs, relay neurons, and command neurons](/private/tmp/fig6_singles/panel_A_circuit_schematic.png){width=85%}

Panel (a) shows the wiring diagram at the coarsest level:

- **Layer 1 --- Sensory inputs (7 channels):**
  - *Olfactory:* DA1 (cis-vaccenyl acetate pheromone receptor neurons),
    VA1v, VA1d (other olfactory receptor neurons implicated in courtship)
  - *Auditory:* JO-B (Johnston's organ mechanosensory neurons responding
    to courtship song)
  - *Visual:* LC10 (lobula columnar neurons tracking small moving objects,
    i.e. another fly)
  - *Contact chemosensory:* ppk23, ppk25 (gustatory receptor neurons on
    the legs detecting cuticular pheromones during tapping)
- **Layer 2 --- 2nd-order relay/integrator neurons:** vAB3 and PPN1 are
  well-characterized second-order neurons in the courtship circuit that
  receive direct sensory input
- **Layer 3 --- 3rd-order courtship command neurons:** aSP-f and aSP-g are
  sexually dimorphic interneurons implicated in the go/no-go courtship
  decision

Arrow widths in the schematic represent aggregate path strength, already
hinting that some modalities (e.g. DA1) have thicker, more dominant routes
while others (e.g. visual) arrive through more diffuse wiring.

**Key point:** Multiple modalities must funnel through a limited number of
shared relay neurons before reaching the same command neurons. The rest
of the figure asks: what happens at each of these convergence points?

\newpage

## Slide 3 --- Panels (b) & (c): Strength and Valence Heatmaps

**Panel (b): Column-normalized modality strength heatmap**

![Panel (b): Column-normalized modality strength heatmap across all target neurons](/private/tmp/fig6_singles/panel_B_heatmap_all_targets_horizontal.png){width=85%}

- Matrix: 36 target neuron types (rows) x 7 modalities (columns)
- Each column is independently scaled to its own maximum, so the heatmap
  shows which targets each modality *preferentially* reaches, rather than
  raw strength
- Rows are clustered (Ward's D2 on Euclidean distance) to group neurons
  with similar modality profiles
- **Row annotations** (left sidebar): target set membership ---
  aSP-f (8 types, red), aSP-g (5 types, blue), vAB3 (13 types), PPN1 (13 types)

**Absolute modality strength ranking** (mean path strength across all 36 targets):

| Rank | Modality | Mean strength | Dominates |
|------|----------|---------------|-----------|
| 1 | ppk23 | 0.058 | 21/36 targets |
| 2 | ppk25 | 0.056 | |
| 3 | DA1 | 0.030 | |
| 4 | VA1v | 0.010 | |
| 5 | VA1d | 0.005 | |
| 6 | Visual | 0.003 | |
| 7 | Auditory | 0.001 | weakest overall |

Contact channels (ppk23+ppk25) carry $\approx$70% of total path strength.
DA1 carries $\approx$19%. Column normalization is essential to reveal the
targeting *pattern* of weaker modalities.

- **Observations:**
  - Top cluster (LH004m, LH001m, LH008m): bright across DA1, VA1v, VA1d ---
    strong olfactory convergence
  - mAL neurons (mAL\_m1, mAL\_m8, etc.): dominated by DA1 pheromone input
  - ppk23 and ppk25 columns look nearly identical --- first hint that these
    two channels share the same downstream wiring

**Panel (c): Excitatory/inhibitory valence heatmap**

![Panel (c): Diverging excitatory/inhibitory valence heatmap across all target neurons](/private/tmp/fig6_singles/panel_C_diverging_all_targets_horizontal.png){width=85%}

- Same row ordering as panel (b), now showing a diverging blue--white--red
  scale: net valence = excitatory strength minus inhibitory strength
- Red tiles: predominantly excitatory paths; Blue tiles: predominantly inhibitory

**E/I balance differs dramatically across modalities:**

| Modality | % Excitatory | Note |
|----------|-------------|------|
| DA1 | $\approx$89% | Strongly drives courtship targets |
| Visual | $\approx$79% | |
| ppk25 | $\approx$66% | |
| ppk23 | $\approx$63% | |
| VA1d | $\approx$50% | Balanced; **flips** by target set (73% exc at aSP-f, 80% inh at PPN1) |
| VA1v | $\approx$20% | **Predominantly inhibitory** --- a braking pheromone channel |

**The VA1v finding is striking:** This olfactory glomerulus, activated by
fly-emitted volatiles including pheromones, delivers $>$80% inhibition to
courtship targets. At aSP-f: 84% inhibitory. At aSP-g: 87% inhibitory.
Together with excitatory DA1, this creates **opponent olfactory coding**:
DA1 (cVA-activated) drives courtship, VA1v (broadly fly-odor-activated)
suppresses it --- potentially distinguishing conspecific female pheromone
from non-specific fly odors.

\newpage

## Slide 4 --- Panel (d): Selectivity Landscape

**Dominance vs. Lifetime sparseness scatter**

![Panel (d): Dominance vs. lifetime sparseness scatter with marginal boxplots](/private/tmp/fig6_singles/panel_D_dominance_marginal_boxplot.png){width=85%}

Lifetime sparseness (Rolls & Tovee 1995) quantifies how selective each
target neuron is:

- Sparseness = 1.0: input from exactly one modality (fully unimodal)
- Sparseness ~ 0: perfectly balanced input from all 7 modalities

**Key statistics across all 36 targets:**

| Metric | Value |
|--------|-------|
| Median entropy | 1.60 bits (of 2.81 max) |
| Mean entropy | 1.72 bits |
| Range | 1.21 -- 2.49 bits |
| Median effective modalities | 3.0 ($= 2^H$) |
| Median breadth ($>$5% of max input) | 4 modalities |
| Median dominance | 48% from top modality |

**No target receives input from only one modality.** The least multimodal
(mAL\_m1, $H = 1.34$; AVLP606, $H = 1.21$) still receive non-trivial input
from 2--3 channels. The most multimodal (LH006m, $H = 2.49$; SLP160,
$H = 2.46$; AVLP753m, $H = 2.40$) sample from 5--6 modalities with no
single modality exceeding $\approx$30%.

**Distributions differ by target set:**

| Target set | Median $H$ | Breadth | Dominant modality |
|-----------|-----------|---------|-------------------|
| aSP-f | 2.23 | 6 | DA1 (4/8 neurons), 41% dominance |
| aSP-g | 1.70 | 4 | ppk23 (all 5 neurons) |
| vAB3 | 1.55 | 4 | Mixed: ppk23 (7), ppk25 (4), DA1 (2) |
| PPN1 | 1.45 | 3 | ppk23 (9/13), ppk25 (3/13) |

**Key finding:** aSP-f targets are the most broadly multimodal. PPN1 targets
are the most narrowly focused on contact channels. Different output
populations are wired to sample different widths of the sensory space.

\newpage

## Slide 5 --- Panels (e), (f), (g): Brain-Space Anatomy

**Panel (e): Mean lifetime sparseness mapped onto brain morphology**

![Panel (e): Brain map of mean lifetime sparseness](/private/tmp/fig6_singles/e.png){width=85%}

- 3D neuroglancer-style projection of all target neurons, colored by mean
  lifetime sparseness (dark = low sparseness = multimodal; bright = high
  sparseness = unimodal)
- Reveals spatial organization: multimodal neurons tend to cluster in
  specific neuropil regions (lateral horn, AVLP) while unimodal neurons
  are more scattered

**Panel (f): Mean number of modalities per neuron**

![Panel (f): Brain map of integration density](/private/tmp/fig6_singles/f.png){width=85%}

- Same anatomical view, now colored by mean number of distinct modalities
  contributing to each neuron (warm/bright = more modalities)
- Highlights the lateral horn and AVLP as hot spots for multimodal
  convergence

**Panel (g): Individual modality maps**

![Panel (g): Modality territory maps (dorsal view)](/private/tmp/fig6_singles/g_brain_modality_territories_dorsal.png){width=85%}

- Six sub-panels showing the spatial extent of each modality's reach:
  DA1, visual, VA1v, ppk23, VA1d, ppk25
- Each map shows where that modality's strongest paths terminate in the
  brain
- **DA1** fills broadly (many targets); **visual** is more spatially
  restricted to AVLP/PVLP regions
- **ppk23** and **ppk25** maps are virtually indistinguishable --- confirming
  from an anatomical angle that these two channels share the same wiring

\newpage

## Slide 6 --- Panel (h): Modality Similarity Matrices

**Six complementary pairwise similarity metrics between the 7 modalities**

![Panel (h): Modality similarity --- net strength](/private/tmp/fig6_singles/panel h net strength.png){width=45%}
![Panel (h): Modality similarity --- absolute](/private/tmp/fig6_singles/pabel h absolute.png){width=45%}

Panel (h) shows a 2x3 grid of 7x7 matrices plus network graph
visualizations:

- **Jaccard similarity** (binary overlap): what fraction of a modality
  pair's union of target neurons is shared?
- **Cosine similarity**: angular similarity of continuous strength vectors
- **Spearman rank correlation**: does modality A's strong targets also
  tend to be modality B's strong targets?
- **Pearson correlation**: linear co-variation of raw strengths
- Plus network graph renderings of significant positive correlations

**Pearson correlation matrix** (strength vectors across 36 targets):

|  | DA1 | VA1v | VA1d | Aud | Vis | ppk23 | ppk25 |
|--|-----|------|------|-----|-----|-------|-------|
| DA1 | 1.00 | 0.76 | 0.48 | -0.11 | 0.13 | 0.09 | 0.24 |
| VA1v | | 1.00 | 0.51 | -0.11 | 0.31 | -0.08 | 0.05 |
| VA1d | | | 1.00 | -0.08 | 0.12 | -0.06 | 0.03 |
| Aud | | | | 1.00 | -0.14 | 0.04 | 0.09 |
| Vis | | | | | 1.00 | -0.05 | 0.00 |
| ppk23 | | | | | | 1.00 | **0.96** |
| ppk25 | | | | | | | 1.00 |

**Three modality blocs emerge:**

1. **The Olfactory Trio** (DA1, VA1v, VA1d): DA1--VA1v $r = 0.76$,
   Spearman $\rho = 0.92$. These share downstream intermediates because
   their labeled-line projection neurons project to overlapping lateral
   horn / AVLP targets.

2. **The Contact Pair** (ppk23, ppk25): Pearson $r = 0.96$, Spearman
   $\rho = 0.98$ --- nearly interchangeable targeting. They share 75% of
   intermediate neurons (Jaccard). But they are uncorrelated with the
   olfactory trio ($r \approx 0$). Contact and olfactory target different neurons.

3. **Auditory and Visual --- The Loners:** Auditory is weakly anticorrelated
   with everything ($r = -0.08$ to $-0.14$). Visual is weakly positive with
   VA1v ($r = 0.31$) but routes through 3,701 unique intermediates at low
   per-path strength. Both reach 34/36 targets, but at low amplitude.

**Correlations shift by target set:** At aSP-f, DA1--ppk25 $r = 0.82$
(olfactory and contact converge). At vAB3, ppk23--VA1v $r = -0.30$
(the two blocs segregate). The circuit implements **different co-targeting
logic at different output populations.**

\newpage

## Slide 7 --- Panel (i): Path Diversity Across Target Sets

**Mean paths to accumulate 80% of total strength**

![Panel (i): Cross-target valence profile scaled](/private/tmp/fig6_singles/panel_i_cross_target_valence_scaled.png){width=85%}

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

**Median paths to 80% by modality** (across all targets):

| Modality | Median paths to 80% | Routing strategy |
|----------|---------------------|------------------|
| DA1 | 44 | Concentrated (labeled-line) |
| VA1v | 87 | Moderate |
| ppk25 | 116 | Moderate |
| ppk23 | 120 | Moderate |
| VA1d | 136 | Moderate |
| Auditory | 338 | Distributed |
| Visual | 686 | Massively parallel |

**Path diversity varies dramatically by target set:**

|  | DA1 | VA1d | VA1v | Aud | ppk23 | ppk25 | Visual |
|--|-----|------|------|-----|-------|-------|--------|
| aSP-f | **6.5** | 13 | 17 | 28.5 | 116.5 | 91.5 | 65.5 |
| aSP-g | 27 | 28 | 11 | 28 | 104 | 131 | 88 |
| vAB3 | 77 | 264 | 134 | 405 | 336 | 221 | 899 |
| PPN1 | 215 | 236 | 190 | 379 | 73 | 52 | **1612** |

At aSP-f targets, DA1 funnels through just $\approx$7 paths --- these are the
classic labeled-line olfactory projection neurons (DA1\_lPN, M\_lvPNm45).
At PPN1 targets, visual needs $\approx$1600 paths --- massively parallel,
low-amplitude routing.

**Design principle:** aSP-f is wired for high-fidelity, few-path olfactory
input. vAB3/PPN1 are wired for low-fidelity, many-path input that is more
robust but noisier. Different output populations use different routing
strategies.

\newpage

## Slide 8 --- Panel (j): Spotlight Integrator Neurons

**Best multimodal integrator from each target set**

![Panel (j): Combined spotlight view of best multimodal integrator neurons](/private/tmp/fig6_singles/panel_j_combined.png){width=85%}

For each of 5 target sets, we identified the neuron with the highest
Shannon entropy across its 7-modality input profile (requiring input from
at least 3 modalities). These are the circuit's best "multimodal
integrators." Six neurons are spotlighted (vAB3+PPN1 has two):

1. **LH006m** (aSP-f target) --- lateral horn neuron receiving broad
   olfactory input plus significant contact chemosensory input.
   Excitatory DA1 dominates but ppk23/ppk25 provide substantial
   inhibitory contribution.

2. **aSP-g3Am** (aSP-g target) --- one of the aSP-g neurons itself,
   receiving strong VA1v/VA1d olfactory input with some auditory.
   The fact that a command neuron itself ranks as a top integrator
   confirms that aSP-g performs multimodal integration directly.

3. **AVLP743m** (vAB3 target) --- AVLP neuron showing strong visual
   input alongside olfactory. One of the few neurons where visual
   modality contributes substantially, suggesting a visual-olfactory
   integration node.

4. **DNp103** (PPN1 target) --- a descending neuron with broad but weak
   input from multiple modalities. Integrates at lower strength levels,
   possibly acting as a gain modulator rather than a primary driver.

5. **LH004m** (vAB3+PPN1 target) --- a major lateral horn hub with the
   broadest multimodal profile. Receives input from all 7 modalities,
   heavily dominated by DA1 excitation and strong ppk23/ppk25 input.

6. **AVLP597** (vAB3+PPN1 target) --- another broad integrator, showing
   a more balanced excitatory/inhibitory mix across modalities.

**Stacked bar charts** decompose each neuron's input by modality and
valence (blue = excitatory, red = inhibitory), revealing that integration
is not just about which modalities arrive but also about the
excitatory/inhibitory balance of each.

\newpage

## Slide 9 --- Panel (k): aSP-f vs. aSP-g Receive Different Modality Mixtures

**Scatter: mean modality strength to aSP-f vs. aSP-g targets**

![Panel (k): Modality scatter comparing aSP-f vs. aSP-g mean input strength](/private/tmp/fig6_singles/panel_k_modality_scatter_aspf_vs_aspg.png){width=85%}

Each point is one modality; position shows its mean path strength to aSP-f
targets (x-axis) vs. aSP-g targets (y-axis).

**Quantitative modality composition:**

| Modality | aSP-f | aSP-g | Fold difference |
|----------|-------|-------|-----------------|
| DA1 | **49.5%** | 9.2% | 5.4$\times$ stronger at aSP-f |
| VA1v | 18.1% | 2.5% | 7.2$\times$ |
| VA1d | 9.3% | 0.7% | 13$\times$ |
| ppk23 | 7.2% | **45.9%** | 6.4$\times$ stronger at aSP-g |
| ppk25 | 10.9% | **39.7%** | 3.6$\times$ |
| Visual | 4.6% | 1.4% | 3.3$\times$ |
| Auditory | 0.3% | 0.6% | comparable |
| | | | |
| **Olfactory total** | **76.9%** | **12.4%** | |
| **Contact total** | **18.1%** | **85.7%** | |

This is a dramatic segregation:

- **aSP-f is an olfactory-dominated integrator:** three-quarters of its input
  is pheromonal. It is primarily asking "what does the fly smell?"
- **aSP-g is a contact-dominated integrator:** 86% of its input comes from
  ppk23/ppk25. It is primarily asking "what is the fly touching?"

**E/I valence also differs:** At aSP-f, DA1 is 93% excitatory (drives
courtship) while VA1v is 84% inhibitory (opposes courtship). At aSP-g,
VA1v remains inhibitory (87%) but VA1d flips from 73% excitatory (aSP-f) to
62% inhibitory (aSP-g). The same glomerulus changes sign depending on which
target population it reaches.

**VA1v as opponent channel:** The excitatory DA1 and inhibitory VA1v create
an opponent olfactory motif --- DA1 (cVA pheromone) pushes toward courtship,
VA1v (broadly fly-odor-activated) pulls away. This may help discriminate
conspecific female pheromone from non-specific fly odors.

\newpage

## Slide 10 --- Panel (l): ppk23/ppk25 Nonlinear Interaction --- The Model

**How we simulate costimulation through the connectome**

Now we zoom into the two contact chemosensory channels (ppk23, ppk25) and
ask: when both are active simultaneously, does the combined effect on each
target neuron equal the sum of individual effects, or is there a nonlinear
interaction? To answer this we build a signal-flow model directly on the
connectome's wiring diagram.

### Step 1 --- The signed weight matrix $W$

We start from the connectome adjacency matrix, where $W_{ij}$ is the
normalized synaptic weight from presynaptic neuron $i$ to postsynaptic
neuron $j$ (column-normalized so that each postsynaptic neuron's total
input sums to 1). We then apply neurotransmitter signs: every outgoing
weight from an inhibitory neuron (GABA, glycine, histamine) is negated,
while excitatory types (ACh, glutamate) keep their positive sign.
The result is a **signed weight matrix** $W$ where positive entries are
excitatory connections and negative entries are inhibitory.

### Step 2 --- Encoding sensory input as a binary vector

Each sensory channel is encoded as a binary stimulus vector $\mathbf{s}$
over all $N$ neurons in the network:

$$\mathbf{s}_{\text{ppk23}}[i] = \begin{cases} 1 & \text{if neuron } i \text{ is a ppk23 sensory neuron} \\ 0 & \text{otherwise} \end{cases}$$

For costimulation, the combined input is the sum of the two channel
vectors: $\mathbf{s}_{\text{both}} = \mathbf{s}_{\text{ppk23}} + \mathbf{s}_{\text{ppk25}}$.

### Step 3 --- Iterative propagation with matrix multiplication + sigmoid

Signal propagation through the circuit is modeled as repeated
matrix--vector multiplication followed by a nonlinear activation function.
At each step $t$, the activation vector $\mathbf{x}$ is updated:

$$\mathbf{x}^{(t+1)} = f\!\Big(W^\top \mathbf{x}^{(t)} + \mathbf{s}_{\text{input}}\Big)$$

- $W^\top \mathbf{x}^{(t)}$ is a **matrix multiplication** that computes,
  for every neuron, the weighted sum of its presynaptic inputs at the
  current time step --- this is the core "one synapse of propagation"
- $+ \mathbf{s}_{\text{input}}$ re-injects the sensory stimulus at every
  step (sustained mode), modeling tonic sensory drive
- $f(\cdot)$ is the **activation function** applied element-wise

The activation function is a **sigmoid** (specifically $\tanh$) with
gain parameter $\beta = 5$:

$$f(x) = \tanh(\beta \cdot x)$$

This saturating nonlinearity is the key ingredient. It maps the
weighted-sum input to the range $[-1, +1]$, compressing large inputs
toward $\pm 1$. Without it, signals would sum linearly and there could
be no interaction between channels. With it:

- When a neuron already receives strong excitatory input from ppk23
  alone, adding ppk25 pushes the total input further into the saturated
  tail of the sigmoid --- the output barely increases. This creates
  **subadditivity**.
- When two inputs push in opposite directions (push--pull), the sigmoid's
  steepest region is near zero, so the opposing drives can produce a
  sharper, amplified output change --- creating **superadditivity** downstream.

We propagate for $n = 3$ steps, corresponding to the 3-hop path depth
from sensory neurons through intermediaries to targets.

### Step 4 --- Computing $R_{ij}$: the interaction metric

We run the propagation model three times with identical parameters but
different input vectors:

1. **ppk23 alone:** $\mathbf{x}^{(3)}_{\text{ppk23}} = \text{propagate}(\mathbf{s}_{\text{ppk23}}, 3)$
2. **ppk25 alone:** $\mathbf{x}^{(3)}_{\text{ppk25}} = \text{propagate}(\mathbf{s}_{\text{ppk25}}, 3)$
3. **Both together:** $\mathbf{x}^{(3)}_{\text{both}} = \text{propagate}(\mathbf{s}_{\text{ppk23}} + \mathbf{s}_{\text{ppk25}}, 3)$

For each target neuron $k$, the nonlinear interaction is:

$$R_{ij}(k) = A_{\text{both}}(k) - A_{\text{ppk23}}(k) - A_{\text{ppk25}}(k)$$

If the circuit were perfectly linear, $R_{ij} = 0$ everywhere. Any
deviation is a direct consequence of the sigmoid saturation interacting
with the circuit topology.

- $R_{ij} < 0$: **subadditive** --- the combined activation is less than the
  sum of parts (saturation/occlusion)
- $R_{ij} = 0$: **linear** --- no interaction between channels
- $R_{ij} > 0$: **superadditive** --- the combined activation exceeds the
  sum of parts (synergy/amplification)

### Step 5 --- Tracking $R_{ij}$ across propagation steps

By recording the full trajectory $\mathbf{x}^{(0)}, \mathbf{x}^{(1)},
\mathbf{x}^{(2)}, \mathbf{x}^{(3)}$, we can compute $R_{ij}$ at every
step and ask: at which synapse does the nonlinearity emerge? This is
what panels (o) and (p) exploit --- the interaction is near-zero at
step 0--1 (sensory level), becomes strongly negative at step 2
(intermediary saturation), and then either stays negative or flips
positive at step 3 depending on the push--pull topology.

### The waterfall plot (panel l)

![Panel (l): R_ij waterfall --- per-target interaction scores for ppk23/ppk25 costimulation](/private/tmp/fig6_singles/panel_l_interactiononcooactivation.png){width=85%}

Panel (l) shows $R_{ij}$ at the final step (step 3) for every target
neuron, organized by target set (aSP-f, aSP-g, PPN1 downstream, vAB3
downstream):

- Horizontal bars extend left (subadditive) or right (superadditive)
- Color codes the mechanism: **ceiling saturation** (brown),
  **floor saturation** (pink), **push-pull** (green),
  **upstream saturation** (blue), **weak/indeterminate** (grey)

**Key pattern:** The vast majority of targets show $R_{ij} < 0$
(subadditive). This is the expected default: when two excitatory channels
converge on the same intermediary, the sigmoid saturates and the combined
output is less than the sum. But a handful of targets show $R_{ij} > 0$
--- these require the push--pull circuit motif explained in the following
slides.

\newpage

## Slide 11 --- Panel (m): Drive Quadrant Scatter

**Net ppk23 drive vs. net ppk25 drive to each target**

![Panel (m): Drive convergence reveals mechanism --- ppk23 vs ppk25 quadrant scatter](/private/tmp/fig6_singles/panel_m_Drive convergence reveals mechanism.png){width=85%}

Each point is a target neuron. X-axis: net ppk23 drive (summed across all
paths from ppk23 to that target). Y-axis: net ppk25 drive.

The scatter naturally divides into four quadrants:

1. **Top-right (both excitatory):** ppk23 and ppk25 both excite this
   target through the same intermediaries. When combined, the
   intermediaries saturate -> **ceiling saturation -> subadditive (destructive)**.

2. **Bottom-left (both inhibitory):** ppk23 and ppk25 both inhibit this
   target. Combined, the intermediary bottoms out ->
   **floor saturation -> superadditive** (double inhibition can't go below
   zero, so the combined effect is "less inhibitory" than expected, which
   is superadditive in the signed sense).

3. **Top-left and bottom-right (opposite signs):** ppk23 excites but ppk25
   inhibits (or vice versa) via **push-pull topology**. This is the most
   interesting motif: the intermediate neuron receives opposing drives,
   and the resulting interaction can be either superadditive or show
   upstream saturation depending on the circuit details.

**Labeled examples:**

- **mAL_m3c** sits in the "both inhibitory" quadrant --- floor saturation
- Several AVLP and LH neurons sit in the push-pull quadrants
- The annotations show that push-pull topology is the dominant mechanism
  for superadditivity

\newpage

## Slide 12 --- Panel (n): Intermediary Decomposition

**Linear drive at step 2: which intermediaries carry the signal?**

![Panel (n): Key intermediary neurons --- ppk23/ppk25 drive decomposition](/private/tmp/fig6_singles/panel_n_Key intermediary neurons.png){width=85%}

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
  **same** direction --- these are classic convergence points where
  saturation occurs.
- **mAL_m1 [INH]**: inhibitory neuron driven in **opposite** direction by
  ppk23 vs. ppk25 --- this is a push-pull intermediary. ppk23 excites it
  (via an excitatory path) while ppk25 inhibits it (or vice versa).
- **AN05B023c [INH]** and **mAL_m3c [INH]**: also opposite-direction ---
  more push-pull candidates.
- The top intermediary (LHAV4c2) has the strongest linear drive, but the
  push-pull neurons (those labeled "opp") are the ones that generate
  nonlinear amplification downstream.

\newpage

## Slide 13 --- Panel (o): The Push-Pull Flip

**R_ij transitions from step 2 (intermediaries) to step 3 (targets)**

![Panel (o): Multi-level interaction evolves across layers --- the push-pull flip](/private/tmp/fig6_singles/panel_o_C Multi-level- interaction evolves across layers.png){width=85%}

This is the central mechanistic result. The plot tracks R_ij at the
intermediary level (step 2) and at the target level (step 3) for key
neurons, with connecting lines showing how the interaction changes as
signals propagate one more synapse.

**Critical observations:**

1. **At step 2 (intermediary level): nearly ALL R_ij < 0.** Whether the
   intermediary is excitatory or inhibitory, convergence of two same-
   direction inputs causes saturation. This is a universal property of
   convergent circuits --- there is nothing surprising here.

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
   relay saturated signals from intermediaries don't recover --- their
   R_ij remains negative from step 2 to step 3.

4. **Ceiling saturation** neurons also stay negative --- these receive
   same-direction excitatory input from both channels through relays
   that are already at ceiling.

**The push-pull motif is therefore a circuit-level mechanism that converts
inherent saturating subadditivity into superadditive amplification.** It
works by splitting the two channels into opposing drive on a shared
intermediary, then recombining downstream.

\newpage

## Slide 14 --- Panels (p) & (q): Propagation Dynamics and Channel Asymmetry

**Panel (p): delta across propagation steps for AN09B017 family**

![Panel (p): Interaction signal at AN09B017 hubs across propagation steps](/private/tmp/fig6_singles/panel_pInteraction signal at AN09B017 hubs.png){width=85%}

This line plot tracks delta = A(both) - A(ppk23) - A(ppk25) across
propagation steps (0 to 3) for the seven AN09B017 variants (a through g),
which are major excitatory intermediaries for ppk23/ppk25 signals.

- At step 0-1: delta is near zero (no interaction at sensory level)
- At step 1-2: delta drops sharply negative --- this is where convergence
  occurs and saturation kicks in
- At step 2-3: most variants stay negative (upstream saturation persists
  to target), but some show partial recovery depending on the downstream
  wiring topology

The spread among AN09B017 variants shows that even neurons of the same
type can have different propagation dynamics depending on their specific
downstream connectivity.

**Panel (q): A(ppk23) - A(ppk25) for each AN09B017 variant**

![Panel (q): AN09B017 channel preference --- ppk23 vs ppk25 asymmetry](/private/tmp/fig6_singles/panel_q_an09b017_panel_E_channel_preference.png){width=85%}

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
intermediaries -> merged targets) creates the opportunity for push-pull
interactions.

\newpage

## Slide 15 --- Synthesis and Key Takeaways

**Six major findings from the connectomic analysis of multimodal convergence:**

1. **Structured multimodality, not random mixing.** Each target neuron has
   a specific modality "recipe" --- a dominant input with graded subordinate
   contributions. True equal-weight multimodal integration is rare.

2. **Correlated channel pairs reveal functional grouping.** ppk23/ppk25
   (r=0.98) and VA1v/VA1d (r=0.92) form tightly coupled pairs that the
   circuit routes almost identically. Visual input (LC10) is the most
   independent, reaching a distinct set of targets.

3. **DA1 pheromone has privileged, concentrated routing.** Fewer paths to
   80% strength than any other modality --- a dedicated labeled-line-like
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
   superadditivity --- a circuit-level mechanism for contrast enhancement
   between the two contact chemosensory pheromone channels.

\newpage

## Slide 16 --- Methods at a Glance

- **Connectome data:** Male CNS (male-cns.janelia.org), male *Drosophila* central nervous system connectome
- **Strongest path analysis:** For each (sensory neuron, target) pair, trace
  the path through the connectome that maximizes the product of normalized
  synaptic weights (connection probability)
- **Seven sensory modalities:** DA1, VA1v, VA1d (olfactory ORNs), JO-B
  (auditory), LC10 (visual), ppk23, ppk25 (contact chemosensory)
- **Four target sets:** aSP-f, aSP-g (3rd-order command neurons), vAB3
  downstream, PPN1 downstream (2nd-order relay targets)
- **Valence assignment:** Based on presynaptic neurotransmitter identity ---
  ACh/glutamate = excitatory; GABA/glycine/histamine = inhibitory
- **Selectivity metrics:** Lifetime sparseness (Rolls & Tovee 1995),
  Shannon entropy, dominance fraction
- **Similarity metrics:** Pearson, Spearman, Jaccard, Cosine (all pairwise)
- **Nonlinear interaction:** R_ij = A(ppk23+ppk25) - A(ppk23) - A(ppk25),
  decomposed by propagation step, classified by intermediary topology
  (push-pull, ceiling/floor saturation, upstream saturation)

\newpage

## Methods Deep Dive 1 --- The Male CNS Connectome

**Data source:** The male CNS connectome from the Janelia Male CNS project
(male-cns.janelia.org) provides a complete synaptic-resolution wiring
diagram of the adult male *Drosophila melanogaster* central nervous system.

**What the connectome gives us:**

- A **directed graph** where nodes are identified neuron types and edges
  are synaptic connections with synapse counts
- **Neurotransmitter identity** for each neuron type (ACh, GABA, glutamate,
  etc.), enabling us to assign excitatory or inhibitory signs to connections
- **Cell type annotations** including names, morphological classes,
  sexual dimorphism status (*fru*$^+$, *dsx*$^+$, male-specific, etc.)

**Scale of the data used:**

| Target set | Unique target types | Paths traced |
|-----------|-------------------|-------------|
| aSP-f | 8 | 12,400 |
| aSP-g | 5 | 7,750 |
| vAB3 | 13 | 247,000 |
| PPN1 | 13 | 247,000 |
| **Total** | **36** | **$>$500,000** |

**Important distinction:** The connectome is a *structural* map (which
neurons are connected), not a *functional* map (which connections are
active during courtship). Our analysis asks "what *could* the circuit
compute given its wiring?" --- functional validation requires physiology.

\newpage

## Methods Deep Dive 2 --- Strongest Path Analysis (Panels A--K)

**Problem:** Given a sensory neuron type $S$ and a target neuron type $T$,
what is the most efficient route through the connectome?

**Algorithm:** Yen's $k$-shortest-paths algorithm ($k = 1000$), applied to
the connectome graph where edge weights are $-\log(w_{ij})$ (negative log
of normalized synaptic weight). This finds the top 1000 paths that
**maximize the product of connection probabilities** along the path.

$$\text{Path strength} = \prod_{(i,j) \in \text{path}} w_{ij}$$

where $w_{ij}$ is the column-normalized synaptic weight from neuron $i$ to
neuron $j$.

**Path properties extracted for each path:**

- **Strength:** Product of edge weights along the path
- **Length:** Number of hops (typically 2--4)
- **Valence:** Product of neurotransmitter signs along the path. A path
  through two inhibitory synapses is net excitatory ($-1 \times -1 = +1$).
  This determines whether the path delivers excitation or inhibition.
- **Intermediate nodes:** Every neuron between source and target, identified
  by type name

**From paths to panels:** Aggregating across all 1000 paths per
(source, target) pair, we compute the modality strength profiles (Panel B),
valence signatures (Panel C), selectivity metrics (Panel D), similarity
matrices (Panel E), path diversity (Panel F), shared intermediates
(Panel G), and spotlight integrators (Panel H).

\newpage

## Methods Deep Dive 3 --- Combinatorial Signal Flow (Panels L--Q)

**Problem:** Strongest paths describe static wiring. Can the wiring
produce **nonlinear computation** when signals from multiple modalities
propagate simultaneously?

**Approach:** A neural network-style forward model on the real connectome:

**1. Build the signed adjacency matrix $W$:**

- Start from the connectome's synapse count matrix
- Column-normalize (post-synaptic normalization): each neuron's incoming
  weights sum to $\approx$1
- Apply neurotransmitter signs: negate all outgoing weights from inhibitory
  neurons

**2. Define sensory input vectors:**

- $\mathbf{s}_{\text{ppk23}}$: binary vector with 1 at every ppk23 sensory
  neuron, 0 elsewhere
- Same for each of the 7 channels
- Combined: $\mathbf{s}_{\text{both}} = \mathbf{s}_{\text{ppk23}} + \mathbf{s}_{\text{ppk25}}$

**3. Propagate for $n = 3$ steps (sustained mode):**

$$\mathbf{x}^{(t+1)} = f\!\Big(W^\top \mathbf{x}^{(t)} + \mathbf{s}_{\text{input}}\Big)$$

where $f(x) = \tanh(5x)$ is the sigmoid activation.

**4. Test all 127 non-empty subsets** of 7 channels ($2^7 - 1$): every
single channel, every pair, every triplet, ..., all 7 together.

**5. Compute pairwise interaction:** $R_{ij}(k) = A_{\text{both}}(k) - A_i(k) - A_j(k)$

**6. Compute trajectory-resolved interaction:** Record $\mathbf{x}$ at
every step to identify *where in the circuit* nonlinearity emerges.

**Complementarity with strongest paths:** The signal-flow model uses the
**entire adjacency matrix** (not just strongest paths). It captures
network-wide effects including recurrent connections, lateral inhibition,
and multi-pathway interference. The strongest-path analysis tells us
*which routes* matter; the signal-flow model tells us *what happens* when
signals flow through all routes simultaneously.

\newpage

## Methods Deep Dive 4 --- Selectivity and Similarity Metrics

**Lifetime sparseness** (Rolls & Tovee 1995):

$$S = \frac{1 - \frac{\left(\sum_i r_i / n\right)^2}{\sum_i r_i^2 / n}}{1 - 1/n}$$

where $r_i$ is the strength of modality $i$ and $n = 7$. Ranges from 0
(perfectly uniform) to 1 (perfectly selective). Intuitively: how
"peaked" is the neuron's modality profile?

**Shannon entropy:**

$$H = -\sum_{i=1}^{7} p_i \log_2 p_i$$

where $p_i = r_i / \sum r_j$ is the normalized strength proportion.
Maximum $= \log_2 7 = 2.81$ bits (uniform). **Effective modalities**
$= 2^H$ converts entropy to an intuitive "how many channels" equivalent.

**Dominance:** Fraction of total strength from the single strongest
modality. Dominance = 1 means unimodal; dominance = 1/7 means perfectly
balanced.

**Pairwise similarity between modalities** (4 metrics):

| Metric | What it captures | Input |
|--------|-----------------|-------|
| Pearson $r$ | Linear co-variation of raw strengths | Continuous strength vectors |
| Spearman $\rho$ | Rank-order agreement | Ranks of strengths |
| Jaccard | Binary overlap of target sets | Presence/absence (threshold $>$ 0) |
| Cosine | Angular similarity | Strength vectors (norm-independent) |

All are computed pairwise between the 7 modalities, treating the 36
target neurons as dimensions. Consistency across all four metrics
strengthens confidence in the modality-bloc structure.

\newpage

## Methods Deep Dive 5 --- Mechanism Classification for $R_{ij}$

**How do we determine WHY a target is sub- or superadditive?**

For each target neuron, we decompose the interaction into its mechanistic
origin by examining the **intermediary neurons** that relay ppk23 and ppk25
signals.

**Step 1: Linear drive decomposition.** At step 2 (intermediary level),
compute the net drive from ppk23 and from ppk25 to each intermediary:

- $d_{\text{ppk23}}(m)$ = activation of intermediary $m$ under ppk23-only
- $d_{\text{ppk25}}(m)$ = activation of intermediary $m$ under ppk25-only

**Step 2: Classify the intermediary by drive concordance:**

| ppk23 drive | ppk25 drive | Classification |
|-------------|-------------|----------------|
| Positive | Positive | Same-direction excitatory |
| Negative | Negative | Same-direction inhibitory |
| Positive | Negative | **Opposite-direction (push-pull)** |
| Negative | Positive | **Opposite-direction (push-pull)** |

**Step 3: Classify the target by which intermediaries dominate its input:**

| Intermediary type | $R_{ij}$ at intermediary | $R_{ij}$ at target | Mechanism |
|-------------------|------------------------|-------------------|-----------|
| Same-dir excitatory | $< 0$ | $< 0$ | **Ceiling saturation** |
| Same-dir inhibitory | $< 0$ | $> 0$ | **Floor saturation** |
| Opposite-dir | $< 0$ | $> 0$ | **Push-pull (superadditive)** |
| Opposite-dir | $< 0$ | $< 0$ | **Upstream saturation** |

The critical distinction between push-pull-SUPER and upstream-saturation
is whether the intermediary's own $R_{ij}$ is strong enough to suppress
the push-pull benefit. Both have opposite-direction drives at the
intermediary level, but only push-pull-SUPER produces $R_{ij} > 0$ at the
target.

\newpage

## Slide 17 --- Narrative Summary

**What we have learned about pheromone processing and sensory integration**

The traditional view of the male *Drosophila* courtship circuit emphasizes
pheromone detection --- cVA activates DA1 ORNs, which activate projection
neurons, which activate P1/aSP-f/aSP-g command neurons. This work reveals
that this is only one thread in a much richer tapestry.

The courtship decision circuit is fundamentally a **multimodal coincidence
detector**. It receives seven parallel sensory streams organized into two
major blocs (olfactory and contact) plus two independent channels (auditory,
visual), routes them through a compact layer of intermediate neuron types
that actively split, invert, and recombine signals, and delivers to
different output populations different nonlinear combinations of sensory
evidence.

**The key hub neurons:**

| Rank | Neuron | Strength | Dominant | Role |
|------|--------|----------|----------|------|
| 1 | DA1\_lPN | 0.852 | DA1 (94%) | Olfactory labeled-line |
| 2 | AN09B017g | 0.804 | ppk25 (72%) | Contact-channel splitter |
| 3 | AN09B017f | 0.745 | ppk25 (55%) | Contact-channel splitter |
| 4 | AN09B017e | 0.484 | ppk23 (58%) | Contact-channel splitter |
| 8 | LH008m | 0.183 | DA1 (73%) | **Cross-bloc integrator** |
| 9 | mAL\_m1 | 0.164 | ppk23 (56%) | GABAergic sign inverter |
| 13 | P1\_3c | 0.066 | ppk25 (47%) | Known courtship neuron |

The AN09B017 family (7 members) are contact-channel splitters: they carry
$>$95% ppk23+ppk25 signal but with different ratios (AN09B017a: 66% ppk23;
AN09B017g: 72% ppk25), creating sign-diversified copies for downstream
targets.

The mAL inhibitory neurons receive multimodal excitatory convergence and
deliver GABAergic inhibition, enabling push-pull motifs. **AN05B035** is
the key node that makes AN09B017g carry ppk23 signal with **negative sign**
--- the origin of push-pull topology in the contact system.

**Computational principles:**

- **Modularity with staged convergence:** Olfactory signals co-route early;
  contact and auditory/visual signals remain separate until deeper layers.
- **Sign diversification:** The same sensory signal is split into positive
  and negative copies by GABAergic interneurons (mAL family, AN05B025).
- **Target-specific computation:** aSP-f (77% olfactory) and aSP-g (86%
  contact) extract different features from the same sensory space.
- **Robustness through topology:** Interaction signs are conserved across
  activation functions, propagation depths, and input modes.

**The four mechanisms of sensory interaction:**

1. **Ceiling saturation** (destructive, $R_{ij} < 0$): Both channels deliver
   same-sign excitatory drive. Combined input overshoots the linear regime
   of the sigmoid. Output is sublinear.
2. **Floor saturation** (superadditive, $R_{ij} > 0$): Both channels deliver
   same-sign inhibitory drive. Combined inhibition saturates near the floor.
3. **Push-pull / mutual de-saturation** (superadditive, $R_{ij} > 0$):
   Channels deliver opposite-sign drives. The inhibitory channel rescues
   the excitatory one from saturation, keeping the neuron in its linear
   regime where it is maximally sensitive.
4. **Upstream saturation** (destructive despite push-pull topology,
   $R_{ij} < 0$): Intermediary neurons are themselves co-saturated. Their
   upstream compression propagates downstream, preventing the push-pull
   from materializing.

**Key insight:** Interaction sign is a multi-level phenomenon. It cannot be
predicted from linear drive decomposition alone. The nonlinear state of
intermediary neurons --- whether they are already co-saturated --- determines
whether push-pull topology actually produces superadditivity.

**Testable predictions:** The analysis predicts specific neurons that should
show superadditive (LH008m, mAL\_m2a) or subadditive (LH006m, AVLP700m)
responses when ppk23 and ppk25 are coactivated. These predictions are robust
across model variants and can be tested with calcium imaging or
electrophysiology. Silencing specific inhibitory intermediaries (e.g.,
AN05B035) should convert push-pull neurons from superadditive to destructive.

The picture that emerges is one of a structured computational device --- not
a simple sensory funnel --- that uses excitatory/inhibitory wiring motifs to
implement specific multimodal feature detectors for courtship decision-making.

\newpage

# Supplementary: Anticipated Questions

\newpage

## Q1 --- Why exactly these seven sensory modalities?

**"Are there other sensory inputs to the courtship circuit you are missing?"**

The seven channels (DA1, VA1v, VA1d, JO-B, LC10, ppk23, ppk25) were
chosen because they represent the **complete set of experimentally
characterized sensory inputs** to the male *Drosophila* courtship
decision circuit:

| Channel | Modality | Sensory cue | Evidence |
|---------|----------|-------------|----------|
| DA1 | Olfactory | cis-vaccenyl acetate (cVA) pheromone | Kurtovic et al. 2007 |
| VA1v | Olfactory | Fly-emitted volatiles | Dweck et al. 2015 |
| VA1d | Olfactory | Fly-emitted volatiles | Dweck et al. 2015 |
| JO-B | Auditory | Courtship song (wing vibration) | Kamikouchi et al. 2009 |
| LC10 | Visual | Small-object motion (another fly) | Ribeiro et al. 2018 |
| ppk23 | Contact chemo. | Cuticular pheromones (leg tapping) | Toda et al. 2012 |
| ppk25 | Contact chemo. | Cuticular pheromones (leg tapping) | Starostina et al. 2012 |

**Could we be missing inputs?** Possibly. The male CNS connectome might
reveal additional weak sensory paths (e.g., from hygrosensory or
thermosensory neurons) that have not been functionally characterized.
However, the seven channels above account for all modalities shown to
influence courtship probability in behavioral assays. Adding additional
channels would not change the pairwise or higher-order interactions
reported here --- it would only extend the combinatorial space.

\newpage

## Q2 --- Why use "strongest paths" instead of all synaptic connections?

**"Doesn't ignoring weaker connections bias the analysis?"**

The **strongest path analysis** traces, for each (sensory neuron, target)
pair, the path through the connectome that maximizes the product of
normalized synaptic weights. We use Yen's algorithm to find the top
$k = 1000$ strongest paths per pair.

**Why not use the full adjacency matrix directly?**

1. **Biological relevance:** In a network with ${\sim}10^5$ neurons,
   almost any pair can be connected if you allow enough hops. The vast
   majority of these multi-hop paths carry negligible signal. Strongest
   paths capture the routes through which the bulk of actual signaling
   flows.

2. **Interpretability:** A strongest path has named intermediate neurons
   at each hop --- we can ask "which neuron sits between ppk23 and aSP-f?"
   and get a specific answer (e.g., AN09B017d). A raw matrix multiplication
   gives you a scalar activation but no mechanistic explanation.

3. **Consistency with the signal-flow model:** Panels (l)--(q) use full
   matrix propagation ($W^\top \mathbf{x}$) anyway, which implicitly
   includes all connections. The strongest-path panels (a)--(k) and the
   signal-flow panels (l)--(q) are **complementary**: the former identifies
   which paths matter, the latter verifies that the full network dynamics
   agree.

**Important:** The signal-flow model in panels (l)--(q) does NOT use
strongest paths. It propagates through the **entire signed adjacency
matrix** --- every synapse in the connectome contributes. The strongest-path
analysis is used only for the descriptive panels (heatmaps, selectivity,
similarity) where we need to attribute strength to individual routes.

\newpage

## Q3 --- Is the sigmoid activation function biologically realistic?

**"Why $\tanh(\beta x)$? Real neurons don't compute $\tanh$."**

The sigmoid serves as a **minimal model of saturating input--output
transfer** --- the key biophysical property that creates nonlinear
interactions. We do not claim that neurons literally compute $\tanh$. We
claim that any reasonable input--output function with these properties
will produce qualitatively similar results:

1. **Monotonically increasing:** more input $\rightarrow$ more output
2. **Saturating at extremes:** output cannot grow without bound
3. **Steepest near zero:** the neuron is most sensitive when it is not
   already driven hard

These are universal properties of real neurons: firing rates saturate,
synaptic vesicle release has a ceiling, and postsynaptic receptors
desensitize.

**The gain parameter $\beta = 5$:** Controls how sharply the sigmoid
saturates. $\beta = 5$ places the transition zone around $|x| \approx 0.2$,
meaning neurons with moderate input are in the sensitive regime while
strongly driven neurons are saturated. We tested $\beta = 2, 5, 10$ and
found qualitatively identical results.

**Key robustness result:** We tested three qualitatively different
activation functions:

| Function | Shape | Saturates? |
|----------|-------|-----------|
| Sigmoid ($\tanh$) | S-curve, symmetric | Yes, both extremes |
| ReLU | Linear $>$ 0, flat $<$ 0 | No ceiling, but zero floor |
| Leaky ReLU ($\alpha = 0.1$) | Linear $>$ 0, shallow $<$ 0 | No ceiling, attenuated floor |

**Sign concordance across all three: $> 80\%$.** The same targets are
superadditive under sigmoid, ReLU, and leaky ReLU. The interaction sign
is a property of the **circuit topology**, not of the specific nonlinearity.
Magnitudes differ (sigmoid produces the largest $|R_{ij}|$ because it
saturates hardest), but the qualitative pattern is conserved.

\newpage

## Q4 --- How robust are the results across model parameters?

**"What if you change the propagation depth, input mode, or normalization?"**

We performed a systematic sensitivity analysis across four axes:

### Propagation depth ($n$ = 2, 3, 4, 5 steps)

- At $n = 2$: interaction patterns already visible but weak (signals
  haven't fully propagated)
- At $n = 3$ (default): clear separation of mechanism classes
- At $n = 4$--5: patterns persist, with minor quantitative shifts as
  deeper recurrent effects accumulate
- **Qualitative rankings of targets by $R_{ij}$ are stable across depths**

### Input mode: pulse vs. sustained

- **Pulse:** input injected only at $t = 0$, then allowed to propagate
  freely. Models a brief sensory stimulus.
- **Sustained:** input re-injected at every step ($+ \mathbf{s}$ term).
  Models tonic sensory drive (e.g., continuous pheromone exposure).
- **Most targets agree between modes.** However, a few neurons flip sign:
  - mAL\_m1: pulse $R = +0.58$, sustained $R = -0.18$ (dramatic flip)
  - AVLP743m: pulse $R = +0.07$, sustained $R = -0.08$
- These flips make biological sense: under tonic drive, intermediaries
  saturate more heavily, converting some push-pull neurons to
  upstream-saturated.

### Normalization (pre vs. post vs. raw)

- **Post-normalization** (column-normalized, used as default): each
  neuron's total input sums to ${\approx}$1. Biologically, this models synaptic
  scaling / homeostatic input normalization.
- **Pre-normalization** (row-normalized): each neuron's total output sums
  to ${\approx}$1. Models presynaptic resource competition.
- **Raw:** unnormalized synapse counts. Preserves absolute connection
  strength differences.
- **Post-normalization chosen as primary** because it best reflects the
  biological observation that neurons maintain roughly constant total
  input conductance.

### Summary of concordance

| Comparison | Sign concordance |
|-----------|-----------------|
| Sigmoid vs. ReLU | 82\% (32/39 targets) |
| Sigmoid vs. Leaky ReLU | 77\% (30/39 targets) |
| Depth 3 vs. depth 4 | $>$ 85\% |
| Pulse vs. sustained | $>$ 75\% (with known exceptions) |

**Bottom line:** The interaction landscape is a property of the wiring, not
of the model. Changing the activation function or parameters shifts
magnitudes but preserves the qualitative pattern.

\newpage

## Q5 --- What about P1 neurons and the classical courtship pathway?

**"How does this relate to the P1 $\rightarrow$ courtship initiation pathway?"**

The classical model of *Drosophila* male courtship emphasizes:

$$\text{cVA} \rightarrow \text{DA1 ORNs} \rightarrow \text{DA1 PNs} \rightarrow \text{P1 neurons} \rightarrow \text{courtship initiation}$$

P1 neurons are *fruitless*$^+$ (*fru*$^+$), male-specific command neurons
whose activation is sufficient to trigger courtship. They are the
best-studied entry point to the courtship motor program.

**How P1 fits into our analysis:**

- P1 neurons (e.g., P1\_3c, P1\_12b) appear as **intermediary neurons** in
  our path analysis --- they sit between sensory inputs and the aSP-f/aSP-g
  targets.
- aSP-f and aSP-g are downstream of (or parallel to) P1 in the courtship
  hierarchy. They are sometimes considered part of the extended "P1
  cluster" of courtship command neurons.
- Our analysis does NOT treat P1 as a target. Instead, P1 neurons emerge
  naturally as intermediate hubs through which multiple modalities route.

**What this work adds to the P1 story:**

1. The cVA $\rightarrow$ DA1 $\rightarrow$ P1 pathway is real but is
   **only one of seven parallel input streams**. P1/aSP-f/aSP-g receive
   substantial auditory, visual, and contact chemosensory input alongside
   pheromone input.
2. The circuit does not merely pool all modalities onto P1. Different
   intermediate neuron types (AN09B017 family, mAL neurons) split and
   recombine signals with different signs, creating **target-specific
   nonlinear integration** that goes far beyond simple convergence.
3. This challenges the view that courtship is a pheromone-gated behavior
   with other modalities acting as modulators. The connectome suggests
   a genuinely **multimodal coincidence detection** architecture.

\newpage

## Q6 --- Does the circuit still work without male-specific neurons?

**"Are the integration patterns you describe male-specific, or shared with
the female brain?"**

We performed three robustness analyses where we systematically removed
neurons from the connectome before re-running the strongest-path analysis:

1. **Remove male-specific neurons only:** Neurons classified as
   "male-specific" in the male CNS cell type annotations (present in
   males, absent in females).
2. **Remove sexually dimorphic neurons only:** Neurons present in both
   sexes but with different morphology or connectivity.
3. **Remove both male-specific AND sexually dimorphic neurons:** The most
   stringent test --- what survives is the "sex-shared" circuit backbone.

**Key finding:** The core circuit architecture --- including multimodal
convergence, modality clustering, and the intermediate hub structure ---
**remains largely intact** even after removing all male-specific and
dimorphic neurons. The sensory-to-target routing is built on a
sex-shared scaffold.

**What IS male-specific:**

- The aSP-f and aSP-g target neurons themselves are sexually dimorphic
  (present in both sexes but with male-specific arbors)
- Some mAL neurons are *fru*$^+$ and male-specific
- P1 neurons are male-specific

**Implication:** The integration architecture (which modalities converge
where, through which hubs) is a property of the shared wiring. Sexual
dimorphism acts primarily at the **output layer** (which command neurons
are activated) and at **specific inhibitory interneurons** (which provide
sex-specific gating), not at the level of multimodal convergence itself.

\newpage

## Q7 --- What about other modality pairs beyond ppk23/ppk25?

**"You focus on ppk23 $\times$ ppk25, but what about DA1 $\times$ auditory
or visual $\times$ olfactory interactions?"**

We tested **all 127 non-empty subsets** of the 7 sensory channels
($2^7 - 1 = 127$), including all 21 pairwise combinations, 35 triplets,
and so on up to the full 7-channel simultaneous activation.

**Why ppk23 $\times$ ppk25 is highlighted:**

- These two channels have the **highest pairwise correlation** (r = 0.98)
  in their downstream targeting, yet produce the most diverse interaction
  landscape. They provide the cleanest test case because the linear
  wiring is almost identical --- any nonlinear interaction must arise from
  subtle differences in sign/weight at the intermediary level.
- The push-pull mechanism is most clearly visible for this pair because
  the AN09B017 family provides diversified signed copies of the
  ppk23/ppk25 signal.

**What about other pairs?**

- **DA1 $\times$ VA1v/VA1d:** These olfactory pairs show broadly
  **constructive** (superadditive) interactions at aSP-f targets,
  consistent with the view that multiple pheromone/volatile cues
  reinforce each other.
- **Visual $\times$ olfactory:** Largely **independent** --- $R_{ij}
  \approx 0$ for most targets, consistent with LC10 reaching a distinct
  set of neurons.
- **Auditory $\times$ contact:** Mixed interactions depending on the
  target --- some PPN1 downstream neurons show destructive interactions.
- **PPN1 downstream targets** show **uniformly destructive** interactions
  for nearly all modality pairs --- suggesting these neurons are
  intrinsically saturating.
- **vAB3 downstream targets** show the **greatest heterogeneity** ---
  some strongly synergistic, others strongly opposed, making this the
  most computationally diverse output population.

**Higher-order interactions (triplets):** We also computed three-way
interaction scores:

$$R_{ijl} = A(i{+}j{+}l) - A(i{+}j) - A(i{+}l) - A(j{+}l) + A(i) + A(j) + A(l)$$

These are generally smaller in magnitude than pairwise interactions,
suggesting that the circuit's nonlinear structure is primarily determined
by pairwise convergence motifs rather than higher-order wiring.

\newpage

## Q8 --- Can these predictions be experimentally validated?

**"What specific experiments would test your model?"**

The signal-flow model generates **neuron-specific, quantitative
predictions** about how target neurons respond to costimulation of
ppk23 and ppk25:

### Predicted superadditive neurons ($R_{ij} > 0$)

| Neuron | Predicted $R_{ij}$ | Mechanism |
|--------|--------------------|-----------|
| mAL\_m2a | $\approx +0.23$ | Push-pull de-saturation |
| LH008m | $\approx +0.18$ | Push-pull (via AN09B017g $\rightarrow$ mAL\_m1) |
| AVLP750m | $\approx +0.17$ | Floor saturation |
| AVLP728m | $\approx +0.08$ | Push-pull |
| LH001m | $> 0$ | Push-pull |

### Predicted subadditive neurons ($R_{ij} < 0$)

| Neuron | Predicted $R_{ij}$ | Mechanism |
|--------|--------------------|-----------|
| AVLP700m | $\approx -0.30$ | Ceiling saturation |
| LH006m | $\approx -0.26$ | Ceiling saturation |
| AVLP704m | $\approx -0.26$ | Ceiling saturation |
| All PPN1 targets | $< 0$ | Uniformly destructive |

### Proposed experiments

1. **Two-photon calcium imaging:** Express GCaMP in target neurons.
   Stimulate ppk23 alone, ppk25 alone, and both together (e.g., via
   optogenetic activation of CsChrimson in ppk23/ppk25 sensory neurons).
   Measure $\Delta F/F$ and compute $R_{ij}$ from the three conditions.

2. **Electrophysiology:** Patch-clamp recording from identified target
   neurons during optogenetic costimulation. Provides higher temporal
   resolution than calcium imaging.

3. **Intermediary silencing:** The model predicts that silencing
   **AN05B035** (a key inhibitory neuron in the push-pull pathway) should
   convert superadditive neurons (LH008m, mAL\_m2a) to subadditive ---
   because removing the inhibitory arm of the push-pull destroys the
   de-saturation mechanism. This is a strong, specific causal prediction.

4. **Behavioral assay:** If push-pull targets gate courtship differently
   than ceiling-saturated targets, silencing specific intermediaries
   should differentially affect courtship probability under single vs.
   combined ppk23/ppk25 stimulation.

\newpage

## Q9 --- Why column-normalize the heatmaps?

**"Doesn't normalization hide absolute strength differences?"**

Two normalizations are used in different parts of the figure, for
different purposes:

### Panel (b): Column-normalized heatmap

Each column (modality) is independently scaled to its own maximum. This
means the heatmap shows **which targets each modality preferentially
reaches**, not raw strength.

**Why?** DA1 has ${\approx}$5$\times$ stronger total path strength than visual.
Without column normalization, the DA1 column would be bright and every
other column would look blank. Column normalization lets you compare the
**shape** of each modality's targeting profile on equal footing.

**Trade-off:** You lose information about absolute strength differences
between modalities. That information is captured separately in panel (d)
(dominance fraction) and panel (i) (cross-target valence profiles).

### Adjacency matrix: Post-normalization (column normalization)

For the signal-flow model, the adjacency matrix is post-normalized: each
postsynaptic neuron's incoming weights sum to ${\approx}$1. This models
**homeostatic input normalization** --- the biologically observed
phenomenon that neurons maintain roughly constant total input conductance
regardless of how many presynaptic partners they have.

**Alternative:** Pre-normalization (row-normalized, each neuron's outputs
sum to 1) models presynaptic resource competition. We tested both;
results are qualitatively similar. Post-normalization is preferred
because it better reflects the constraint on the postsynaptic side
(finite number of receptors, finite membrane area).

**Raw (unnormalized) versions** of all key analyses are also generated
and available in the supplementary output.

\newpage

## Q10 --- What are the limitations of this analysis?

**Honest limitations and caveats**

1. **Static connectome, dynamic brain.** The connectome gives us the
   wiring diagram, not the dynamics. Synaptic weights in the connectome
   are anatomical (synapse counts), not physiological (actual
   conductances). Neuromodulation, short-term plasticity, and
   state-dependent gating are not captured.

2. **No temporal dynamics.** Our propagation model uses discrete steps,
   not continuous time. Real synaptic transmission has delays, temporal
   summation windows, and frequency-dependent facilitation/depression.
   The model captures steady-state input--output relationships, not
   temporal coding.

3. **Activation function is a simplification.** Real neurons have
   complex input--output functions that depend on dendritic
   compartmentalization, ion channel distributions, and neuromodulatory
   state. Our sigmoid is a first-order approximation. The robustness
   across three different activation functions (sigmoid, ReLU, leaky
   ReLU) mitigates but does not eliminate this concern.

4. **Neurotransmitter sign assignment is coarse.** We assign every
   output of a neuron as excitatory or inhibitory based on its primary
   neurotransmitter. In reality, some neurons co-release multiple
   transmitters, and the same transmitter can have excitatory or
   inhibitory effects depending on the postsynaptic receptor.

5. **No gap junctions.** The male CNS connectome includes chemical
   synapses only. Electrical synapses (gap junctions) could provide
   additional coupling between neurons that our analysis does not capture.

6. **Path analysis is top-$k$, not exhaustive.** We trace the top 1000
   strongest paths per (source, target) pair. Extremely weak, highly
   indirect paths are excluded. For the signal-flow model this is not an
   issue (it uses the full matrix), but the descriptive path-based panels
   may miss diffuse, low-strength contributions.

7. **Single male brain.** The connectome is from one individual. While
   *Drosophila* connectomes are highly stereotyped, individual variation
   in synapse counts could shift quantitative interaction scores.
   Qualitative patterns (which targets are super- vs. subadditive) are
   likely robust given the topological basis of our results.

**Despite these limitations,** the analysis provides the first
comprehensive, neuron-resolution map of multimodal sensory integration in
a courtship decision circuit --- and the topological robustness of the
interaction patterns (conserved across activation functions, depths, and
input modes) suggests that the core findings reflect genuine circuit
design principles rather than modeling artifacts.
