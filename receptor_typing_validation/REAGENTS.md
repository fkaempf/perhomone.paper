# Reagents for the t-GRASP receptor test

Searched directly against Bloomington (logged-in session) on 2026-08-11, and independently
confirmed by a second pass over BDSC + FlyBase. Stock numbers were read off stock records.

## Go/no-go: solved

GRNs are presynaptic, the connectome target is postsynaptic, so the two GRASP halves need two
different binary systems. Both ppk drivers exist **only as GAL4** — so the target must be LexA.
`R56C09-lexA` exists, and BDSC stocks the t-GRASP pair in the required orientation.

| Reagent | Exists | Stock | Chr / site | Source |
|---|---|---|---|---|
| ppk23-GAL4 `2.695` | yes | BDSC 93026 | chr 2 | Thistle 2012; used in Kallman 2015 |
| ppk25-GAL4 | yes | BDSC 93028 | chr 2 **and** chr 3 | Starostina 2012 |
| R56C09-lexA | yes | BDSC 53584 | chr 2, attP40 | Pfeiffer 2013; the PPN1-LexA of Kallman 2015 |
| UAS-pre + LexAop-post t-GRASP | yes | **BDSC 79040** | chr 3, attP2 + VK00027 | Shearin 2018, pre-recombined |
| R56C09-GAL4 | yes | BDSC 39145 | chr 3, attP2 | **collides with t-GRASP** |
| ppk23-LexA | exists, unstocked | none | not reported | Pool 2014 (Dickson) — request from Dickson or Scott |
| ppk25-LexA | **does not exist** | — | — | — |
| ppk23/ppk25-QF, -QF2 | **do not exist** | — | — | no MiMIC/CRIMIC either, so no Trojan route |

Full t-GRASP set (all six permutations, all chr 3): BDSC 79037–79042. 79040 is the one with
`20XUAS-pre-t-GRASP` + `13XLexAop2-post-t-GRASP`.

## Traps

**Do not use vGlut-LexA as an F-cell proxy.** Because ppk25-LexA does not exist, Kallman/Scott
used `vGlut-LexA` / `vGlut-QF2` to stand in for the F-cell population. For this experiment that
is circular — "glutamate implies ppk25+" is precisely the neurotransmitter prediction under
test. The entire point is to drive off the receptor promoter.

**Segregate ppk25-GAL4.** BDSC 93028 carries insertions on chr 2 *and* chr 3. The chr 3 copy
collides with t-GRASP. It also creates a dosage confound: two copies of ppk25-GAL4 against one
copy of ppk23-GAL4 differ in driver strength between exactly the two arms whose ratio is the
readout. Cross the chr 3 copy away.

**R56C09-GAL4 is out** — attP2 is occupied by the LexAop half. Independent second reason to use
the LexA version.

**VT063311 / VT063314 lines are not ppk23 drivers.** They are Vienna Tiles that happen to overlap
the ppk23 locus, imaged in brain rather than leg/wing GRNs. Do not assume they equal ppk23
expression.

## Crossing scheme

No recombination needed on chr 2 — ppk-GAL4 and R56C09-lexA sit *in trans*, one per homolog, and
both express.

Build once (~6–8 weeks at 25 °C):

```
G0   BDSC 93026  w; ppk23-GAL4 ; TM2/TM6B
   × BDSC 79040  y w; Sp/CyO ; LexAop-post-tG, UAS-pre-tG
F1   score CyO, Tb
     w; ppk23-GAL4 / CyO ; LexAop-post-tG, UAS-pre-tG / TM6B
F2   sib cross, select non-CyO non-Tb
STOCK A   w; ppk23-GAL4 ; LexAop-post-tG, UAS-pre-tG
```

Stock A′ = the same with ppk25-GAL4 (chr 2 insertion only).

Then per target, one cross, no selection (~2–3 weeks):

```
STOCK A ♀  ×  target-LexA ♂
F1 males   w/Y ; ppk-GAL4 / target-lexA ; LexAop-post-tG, UAS-pre-tG / +
```

Experimental animals must be **male** — ppk23 T1 midline crossing is male-specific and
*fru*-dependent, and every connectome prediction comes from the male CNS.

## Critical path

Not the genetics. **Driver lines for the targets.**

Only R56C09 has a confirmed LexA driver, and that is the reference arm — the one that cannot
discriminate (R₀ = 0.408, 1.5-fold). AN05B023b/c and the other 13 discriminating targets need
LexA lines that do not yet exist.

Route: NeuronBridge colour-depth MIP search from the EM body → existing Gen1 LexA if one matches
→ otherwise a split-LexA build. Body IDs are in `SHORTLIST.md`.

## Useful

BDSC has a JSON search endpoint that avoids the form entirely:
`bdsc.indiana.edu/Home/GetSearchResults` and `/Home/GetDetails/<id>`.

---

# Lab stock check (flomington)

Matched by `R/04_lab_stock_match.py` against the newest local flomington snapshot,
`backups/20260720-141305/stocks.json` (660 stocks, 20 July 2026). Live data is in the flomington
Supabase instance — this is a local snapshot, so re-check before ordering.
`complete_lab_stocks.xlsx` (March) is stale; do not use it.

## Every core reagent is already in the lab

| Need | Lab stock | Where | Keeper |
|---|---|---|---|
| ppk23-GAL4 (BDSC 93026) | "PPK23 - Gal4" ×2; "BDSC 93026 ppk23-Gal4" | 25inc | Flo, Bella |
| ppk25-GAL4 (BDSC 93028) | "ppk25-GAL4" ×2 | 18 | Flo |
| R56C09-lexA (BDSC 53584) | "Kallman PPN1 LexA" ×2 | 18 | Flo |
| R56C09-GAL4 (BDSC 39145) | "Kallman PPN1 Gal4" ×2 | 18 | Flo |
| t-GRASP UAS-pre + LexAop-post (BDSC 79040) | "BDSC 79040" ×2 | 18 | Flo |
| t-GRASP LexAop-pre + UAS-post (BDSC 79039) | "BDSC 79039" ×2 | 18 | Flo |
| Gr32a-GAL4 | "Gr32a Gal4" ×2 | — | — |

**Nothing needs ordering for the core experiment.**

## ppk23-LexA — the one no stock centre has, the lab has it

`#4785e783` / `#661b6f47`, Bella, 25inc:
```
;ppk23-LexA/Cyo; 22B10-Gal4/Tm3, ser
Lab ID GJ1472 · Janelia ID DG78 · Chr 2,3 · IRB 26 · Verified 2026-05-06
made with ppk23-LexA from Barry Dickson lab
```
Note it arrives carrying `22B10-GAL4` on chr 3, which must be crossed away — chr 3 is where the
t-GRASP pair lives.

## Split-GAL4 lines in the lab that hit shortlist targets

| Janelia line | Labels | Relevance |
|---|---|---|
| **SS103018** | **AN13B002** | a shortlist target — R₀ = 0.849, 5.6× |
| SS103089, SS104905, SS104909, SS105464 | vAB3 candidates | vAB3 = the AN09B017 group (a–g), which holds the LgLG5/6/7/8 isolators |
| SS104240, SS104309, SS03049 | mAL | downstream node in the paper |
| SS45434 ×5 | AVLP743m | adjacent project |

## The consequence — and the remaining blocker

Having both t-GRASP orientations (79039 *and* 79040) plus ppk23 in *both* GAL4 and LexA looks
like it unlocks the split-GAL4 targets. It does not, and the reason is worth stating precisely:

- The readout is the ratio ppk25-arm / ppk23-arm at the **same** target with the **same** reporter
  configuration. Only then does the unknown efficiency factor `k` cancel.
- **ppk25 exists only as GAL4.** So the ppk25 arm forces GAL4 on the driver side, which forces the
  target onto LexA.
- The only target LexA in the lab is **R56C09-lexA** — the reference arm, which cannot
  discriminate (R₀ = 0.408, 1.5×).
- Running the ppk23 arm through ppk23-LexA → split-GAL4 target and the ppk25 arm through
  ppk25-GAL4 → LexA target puts the two arms in different reporter configurations, so `k` does
  not cancel and the ratio is meaningless.

**The single blocking reagent is ppk25-LexA.** It does not exist anywhere. Making it converts
every split-GAL4 target in the lab — starting with SS103018 / AN13B002 — into a usable
discriminating arm.

Still missing: Ir52a / Ir52b (the WG1/WG2 arm) — 0 hits.
