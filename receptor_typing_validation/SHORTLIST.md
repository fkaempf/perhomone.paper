# GRASP target shortlist — receptor-type inference

Generated 2026-08-11 by `R/01_design_matrix.R` → `R/02_select_targets.R` → `R/03_shortlist.R`.
Source: `feather/connectivity.feather` (mCNS `male-cns:v0.9`), nerve suffixes collapsed.

## The inverse problem

`x_i ∈ {0,1}` = "sensory type *i* is ppk25+". `C[i,j]` = synapse count from type *i* onto
target *j*. A GRASP experiment at target *j* measures

```
R_j = Σ_i x_i·C[i,j] / Σ_i C[i,j]
```

with an unknown common scale factor `k` (differing GRASP efficiency between the ppk23 and
ppk25 drivers). `k` cancels in ratios between targets, so ≥2 targets are required and a
reference target is needed.

Eight unknown types: WG3, WG4, LgLG1a, LgLG1b, LgLG5, LgLG6, LgLG7, LgLG8.

Current assignment (H0, from `figures/fig5/setup.R:269-274`):
ppk25+ = {WG3, LgLG1b, LgLG5, LgLG8}; ppk25− = {WG4, LgLG1a, LgLG6, LgLG7}.

## Identifiability

Greedy D-optimal selection over all targets with ≥500 ppk-family synapses:

| # | target | ppk syn | log-det |
|---|---|---:|---:|
| 1 | IN01B065 | 1246 | −96.85 |
| 2 | AN09B017b | 1034 | −83.18 |
| 3 | INXXX044 | 642 | −69.54 |
| 4 | AN09B017g | 1788 | −56.19 |
| 5 | IN11A022 | 1540 | −42.87 |
| 6 | AN05B023c | 5631 | −30.01 |
| 7 | AN09B017e | 827 | −17.20 |
| 8 | AN09B017f | 1217 | −4.52 |

**Rank 8 of 8. Condition number 2.5.** All eight types are individually identifiable — the
wing→leg co-clustering propagation does not have to be assumed.

## Core targets for the M/F swap

`R_H0` = predicted ppk25+ fraction under the current assignment; `R_H1` = under a global swap.

| target | ppk syn | R_H0 | R_H1 | fold | notes |
|---|---:|---:|---:|---:|---|
| **AN05B023c** | 5631 | 0.992 | 0.008 | **121×** | GABA, A6 |
| **AN05B023b** | 12066 | 0.054 | 0.946 | **17×** | GABA, A2 |
| IN01B065 | 1246 | 0.051 | 0.949 | 18× | GABA, 20 bodies, T2/T3/A1 |
| IN05B002 | 19190 | 0.139 | 0.861 | 6.2× | GABA, T1, highest signal |
| ANXXX093 | 7259 | 0.850 | 0.150 | 5.7× | ACh, A6, unnamed |
| AN13B002 | 6477 | 0.849 | 0.151 | 5.6× | GABA, A1, **"Dandelion" (Shiu 2022)** |
| IN11A022 | 1540 | 0.195 | 0.805 | 4.1× | ACh, T2 |
| IN11A020 | 3163 | 0.222 | 0.778 | 3.5× | |
| AN05B102a | 27083 | 0.408 | 0.592 | **1.5×** | **= PPN1 (R56C09). Not diagnostic.** |

## Best isolator per type

| type | target | loading | ppk syn | R if ppk25+ | R if not | Δ |
|---|---|---:|---:|---:|---:|---:|
| WG3 | INXXX044 | 0.908 | 642 | 0.908 | 0.000 | **0.908** |
| WG4 | IN11A022 | 0.805 | 1540 | 1.000 | 0.195 | 0.805 |
| LgLG1a | IN01B065 | 0.932 | 1246 | 0.983 | 0.051 | **0.932** |
| LgLG1b | AN05B023c | 0.620 | 5631 | 0.992 | 0.372 | 0.620 |
| LgLG5 | AN09B017f | 0.571 | 1217 | 0.571 | 0.000 | 0.571 |
| LgLG6 | AN09B017b | 0.926 | 1034 | 1.000 | 0.074 | **0.926** |
| LgLG7 | AN09B017e | 0.618 | 827 | 0.979 | 0.362 | 0.618 |
| LgLG8 | AN09B017g | 0.781 | 1788 | 0.941 | 0.160 | 0.781 |

`AN09B017e` and `AN09B017f` carry the synonym **"Yu 2010: vAB3"** — a named neuron with
existing reagents. Worth checking first.

## Wing / leg decoupling ★

Some targets receive input from wing types only, others from leg types only. This is what
breaks the co-clustering propagation.

| target | ppk syn | wing frac | leg frac | R_H0 |
|---|---:|---:|---:|---:|
| **INXXX044** | 642 | **1.000** | 0.000 | 0.908 |
| **IN11A022** | 1540 | **1.000** | 0.000 | 0.195 |
| IN11A020 | 3163 | 0.970 | 0.030 | 0.222 |
| IN01B065 | 1246 | 0.000 | **1.000** | 0.051 |
| AN09B017b | 1034 | 0.000 | 1.000 | 0.074 |
| IN17A013 | 1652 | 0.000 | 1.000 | 0.105 |
| AN17A013 | 3274 | 0.000 | 1.000 | 0.157 |
| AN09B017g | 1788 | 0.000 | 1.000 | 0.941 |

`INXXX044` (R=0.908) and `IN11A022` (R=0.195) are pure-wing and lie on opposite sides.
Together they determine the **wing** assignment with no leg contamination. `IN01B065` (0.051)
and `AN09B017g` (0.941) do the same for the **leg** assignment.

## Recommended minimal sets

- **2 targets, maximal power:** AN05B023b + AN05B023c (17× and 121×)
- **4 targets, wing and leg decoupled:** INXXX044 + IN11A022 (wing) + IN01B065 + AN09B017g (leg)
- **8 targets, full identifiability:** the D-optimal set above
- **Reference/positive control in every case:** AN05B102a (PPN1, R56C09) — 27083 ppk synapses,
  both drivers guaranteed to give signal, expected R ≈ 0.41

## Caveats

- `C` is unthresholded connectome synapse count. GRASP puncta are not synapses 1:1; only
  ratios across targets are interpretable.
- Driver lines for most of these are unknown. `AN09B017e/f` (vAB3) and `AN13B002` (Dandelion)
  are the only ones with published names.
- `INXXX044` and `ANXXX093` are unnamed types — driver hunt required.
- `IN01B065` has 20 bodies and `INXXX044` 8; multi-body types make puncta attribution harder
  than 2-body types.
