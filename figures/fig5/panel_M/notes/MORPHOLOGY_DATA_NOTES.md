# Panel M AN05B035 morphology — data notes

## Status

Real skeleton + synapse data fetched successfully. No fabrication was needed.

## Data sources

| Item | Source | Function |
|------|--------|----------|
| Skeleton | neuprint `male-cns:v0.9` | `neuprintr::neuprint_read_skeletons(ids, heal=TRUE)` |
| Synapse locations + partner bodyids | neuprint `male-cns:v0.9` | `neuprintr::neuprint_get_synapses(ids)` |
| Partner bodyid -> cell type | `feather/mba.feather` (loaded by `setup.R`) | `mba$type[mba$bodyid == partner]` |
| Partner type ppk23/ppk25 drive | `adj.matrix` from `load_all_data` | sum of rows for `channel_neurons$ppk23` / `channel_neurons$ppk25` |

## AN05B035 bodyids

Two bodyids in `mba` (one per hemisphere, both `Prelim Roughly traced`):

- `517601`  (AN05B035_R)
- `23513`   (AN05B035_L)

Both are fetched and rendered together.

## ppk23/ppk25 bias metric

For every cell type in the connectome:

```
drive_ppk23 = sum over src_types in channel_neurons$ppk23 of adj.matrix[src_type, target_type]
drive_ppk25 = sum over src_types in channel_neurons$ppk25 of adj.matrix[src_type, target_type]
bias        = (drive_ppk23 - drive_ppk25) / (drive_ppk23 + drive_ppk25)
```

Bias classes used for colouring:

- `ppk23 (male)`   : bias >=  0.2  -> red  (#D62728)
- `ppk25 (female)` : bias <= -0.2  -> blue (#1F77B4)
- `balanced`       : |bias| < 0.2  -> mid-grey (#9E9E9E)
- `neither` / NA   : no detectable ppk23/ppk25 drive -> light grey (#DADADA)

This is a **direct, one-hop** drive metric. A more graph-theoretic option
would be to use strongest-path strengths (as in `mal_paths`) but those
only cover mAL targets, not the full set of AN05B035 partners.

## View choices

- **Top row**: XY projection (frontal view, y-axis flipped to match EM voxel convention).
- **Bottom row**: XZ projection (dorsal view).
- Each view is faceted into `input` (AN05B035 postsynaptic, `prepost==1`) and
  `output` (AN05B035 presynaptic, `prepost==0`).

## Subsampling

Synapses are capped at 3500 per IO class for scatter readability
(AN05B035 has ~14k synapses per hemisphere). Full table saved to
`panel_M/M_an05b035_synapse_table.csv`.

## Neuroglancer URL

A short Clio-NG URL is also written to
`panel_M/M_an05b035_neuroglancer_url.txt` (via `mcns_shortlink`) for
interactive 3D inspection in the browser.

## Dependencies

- `neuprintr` — configured via `neuprint_login("https://neuprint-cns.janelia.org", "male-cns:v0.9")` already done in `setup.R`.
- `nat`       — for skeleton parsing.
- `rgl`       — only required to avoid load warnings; all plotting is 2D ggplot, no 3D window needed.
- `malecns`   — provides `choose_mcns()` dataset selection.

## If neuprint access is lost

The Rmd has a built-in fallback branch: it prints "data unavailable", writes
the Neuroglancer URL to `M_an05b035_neuroglancer_url.txt`, and still saves a
placeholder PDF. Users would then need to either:

1. Re-authenticate to neuprint (`neuprintr::neuprint_login(...)` with an API
   token in `~/.Renviron`), or
2. Inspect the neuron manually via the Neuroglancer shortlink.
