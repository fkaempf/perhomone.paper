# AN05B023 connectomics

Where the contact-pheromone sensory input lands on AN05B023b and AN05B023c.
Male CNS dataset `male-cns:v0.9`. Structure and methods follow
`~/Documents/AVLP743m_connectomics`.

Four target bodies: AN05B023b `200336` (L), `801269` (R); AN05B023c `18430` (L),
`18696` (R). All four are GABAergic ascending neurons, hemilineage 05B.
28,250 input synapses in total.

## Layout

```
R/          analysis scripts, numbered by run order
  _paths.R    shared paths, focus types, palette; sourced by every script
data/raw/       fetched from neuprint and cached
data/derived/   produced by these scripts
```

Scenes are written into the fkaempf.github.io checkout that lives at
`~/Documents/AVLP743m_connectomics/website/ng/`, prefixed `AN05B023*` so they sit
alongside the AVLP743m scenes without colliding.

## Pipeline

| Script | Produces |
| --- | --- |
| `R/01_fetch_input_synapses.R` | input synapse locations for the four bodies |
| `R/02_annotate_input_synapses.R` | presynaptic type per synapse, suffix variants collapsed |
| `R/03_neuroglancer_scenes.R` | 4 per-body Clio-NG scenes + overview + menu page |

## Findings

**The two cells split the sensory input almost cleanly between them.** Synapse
counts, unthresholded:

| target | LgLG1a | WG4 | LgLG1b | WG3 |
| --- | ---: | ---: | ---: | ---: |
| AN05B023b | **6744** | **4346** | 589 | 398 |
| AN05B023c | 246 | 185 | **3545** | **2154** |

AN05B023b is a LgLG1a/WG4 cell, AN05B023c a LgLG1b/WG3 cell, roughly 10-fold in
both directions. The pattern holds independently in the left and right body of
each type, so it is not a lateralisation artifact. These four types are 55-72%
of all input synapses on any given body.

**All of it is in the nerve cord.** Every one of the sensory synapses is VNC, and
the neuropil follows the type: wing types (WG3, WG4; ADMN nerve) land in `Ov`,
leg types (LgLG1a, LgLG1b) in `LegNp(T1-T3)`. So within one cell the wing and leg
input occupy different neuropils.

**The non-sensory input differs between the two.** AN05B023b's largest non-sensory
input is `IN05B002` (499 syn). AN05B023c instead receives `IN05B011a` (988),
`IN05B011b` (373), and 464 synapses from AN05B023b itself - a direct link from
the LgLG1a/WG4 cell onto the LgLG1b/WG3 one. AN05B023c also has a small brain-side
input in AVLP that AN05B023b essentially lacks.

## Naming

Types are named as the connectome names them: `WG3`, `WG4`, `LgLG1a`, `LgLG1b`.
The ppk23/ppk25 receptor assignment is a light-level call from Fig 1 of the
pheromone paper and is deliberately not used here, in layer names, colours or
figures.

The nerve-suffix variants (`WG3 _ADMN`, `LgLG1a _MesoLN`, ...) exist only in the
local `mba.feather`; they are minted in `pheromone.paper/R/data_processing.R`
around line 65 from `neuprint_get_roiInfo`, and note the space before the
underscore. The neuprint server's own `type` is always the bare name. All four
focus types are therefore collapsed with `bare_type()` before any filter.

This matters: `WG3` bare is 135 synapses while `WG3 _ADMN` is 2417, so a plain
`partner_type == "WG3"` filter renders 5% of the layer, silently, with a full
legend and exit code 0.

## Caveats

- `partner_type` is NA for 4,991 of the 28,250 input synapses (partners absent
  from `mba`). They fall into the grey "other inputs" layer. Any percentage using
  all input synapses as the denominator carries them; the per-type counts above
  do not.
- The per-body focus share (55-72%) uses every input synapse as the denominator.
  A type-level connection table gives a higher figure (84.6% / 67.4%) because it
  excludes unassigned partners. Do not mix the two conventions in one caption.
- Counts here are unthresholded. The cached `adj.matrix.raw.rds` in
  pheromone.paper applies a 5-synapse type-pair threshold and runs slightly
  lower; do not mix cached and live numbers in one figure.
- `projectionOrientation` in the scenes is still the brain-view quaternion
  inherited from `make_mcns_scene()`. It frames the VNC acceptably but was not
  chosen for it.

## Interactive scenes

Menu page at `website/ng/an05b023/index.html`, scenes at
`https://clio-ng.janelia.org/#!https://floriankaempf.com/ng/AN05B023*.json`.

Not published yet - the files are written into the website checkout but not
committed or pushed. To publish:

```
cd ~/Documents/AVLP743m_connectomics/website
git add -A ng && git commit -m "..." && git push
```

GitHub Pages takes about a minute. The scenes only load once they are public:
Clio-NG fetches the JSON over HTTPS, so a local file cannot be previewed.
