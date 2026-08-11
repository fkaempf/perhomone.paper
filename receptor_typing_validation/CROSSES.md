# Crossing schemes — t-GRASP receptor test

All stocks below are **already in the lab** (flomington snapshot 20 July 2026) unless marked
ORDER. Genotypes are copied from the stock records; verify against the vial before setting up.

Balancer logic is written out but **not checked by a fly geneticist** — treat as a draft to
correct, not a protocol to follow blind.

Legend: `tG` = t-GRASP. `pre` = spGFP11 half (presynaptic, goes in the **GRN** driver).
`post` = spGFP1-10 half (postsynaptic, goes in the **target** driver).

---

## Reagents in hand

| Role | Stock | Genotype as recorded | Keeper |
|---|---|---|---|
| GRN driver, both families | BDSC 93026 | `w[1118]; P{ppk23-Gal4.2.695}2; TM2/TM6B` | Flo, Bella |
| GRN driver, ppk25+ only | BDSC 93028 | `w[1118]; P{ppk25-GAL4.S}2; P{ppk25-GAL4.S}3` | Flo |
| GRN driver, LexA | GJ1472 (Dickson DG78) | `;ppk23-LexA/CyO; 22B10-Gal4/TM3, Ser` | Bella |
| Target driver, LexA | BDSC 53584 | `w[1118]; P{GMR56C09-lexA}attP40` | Flo |
| Target driver, GAL4 | BDSC 39145 | `w[1118]; P{GMR56C09-GAL4}attP2` | Flo |
| Reporter, UAS-pre + LexAop-post | BDSC 79040 | `y w; wg[Sp-1]/CyO, Dfd-EYFP; 13XLexAop2-post-tG[attP2] 20XUAS-pre-tG[VK00027]` | Flo |
| Reporter, LexAop-pre + UAS-post | BDSC 79039 | `y w; wg[Sp-1]/CyO, Dfd-EYFP; 20XUAS-post-tG[attP2] 13XLexAop2-pre-tG[VK00027]` | Flo |
| Target split-GAL4 | SS103018 | AN13B002 | — |
| Target split-GAL4 | SS103089/104905/104909/105464 | vAB3 candidates (AN09B017 group) | — |

Both t-GRASP halves sit on **chr 3**. Everything else that matters is on **chr 2**, except
R56C09-GAL4 (attP2, chr 3 — collides) and the second ppk25-GAL4 insertion (chr 3 — collides).

---

## Cross 0 — clean the ppk23-LexA stock

Removes `22B10-GAL4`, which sits on chr 3 where the t-GRASP pair must go.

```
G0   w ; ppk23-LexA / CyO ; 22B10-GAL4 / TM3, Ser        (GJ1472, Bella)
   × w ; Sp / CyO ; TM2 / TM6B                            (any double balancer)

F1   select  CyO , Sp-negative , Ser-POSITIVE
     Ser+ means the chr 3 inherited from GJ1472 is TM3,Ser — i.e. NOT 22B10-GAL4.
     CyO with no Sp means chr 2 is ppk23-LexA / CyO (CyO/CyO is lethal).

     w ; ppk23-LexA / CyO ; TM3, Ser / TM2 or TM6B

F2   sib cross, keep as a balanced stock
     w ; ppk23-LexA / CyO ; TM3, Ser / TM6B
```

Ser is dominant, so **no PCR is needed** — this is scoreable by eye in one generation.
Keep the original GJ1472 vial untouched.

Open: is `ppk23-LexA` homozygous viable? It is maintained over CyO, which may be convenience or
may be necessity. Worth testing while Cross 0 runs.

---

## Route A — ppk-GAL4 drives the GRNs, target is LexA

This is the route that can produce the **ratio**, because both arms use the same reporter
configuration. It is the only route for which ppk25 exists.

### Cross A1 — build Stock A (ppk23 arm)

```
G0   w ; ppk23-GAL4 ; TM2 / TM6B                                        (BDSC 93026)
   × y w ; Sp / CyO, Dfd-EYFP ; LexAop-post-tG , UAS-pre-tG             (BDSC 79040)

F1   select CyO , Tb
     w ; ppk23-GAL4 / CyO ; LexAop-post-tG, UAS-pre-tG / TM6B

F2   sib cross, select non-CyO non-Tb
STOCK A   w ; ppk23-GAL4 ; LexAop-post-tG , UAS-pre-tG
```

### Cross A2 — build Stock A′ (ppk25 arm), segregating away the chr 3 insertion

BDSC 93028 carries `ppk25-GAL4` on **both** chr 2 and chr 3. The chr 3 copy collides with the
t-GRASP pair, and two copies vs one would differ in driver strength between exactly the two arms
whose ratio is the readout.

```
G0   w ; ppk25-GAL4 }2 ; ppk25-GAL4 }3                                  (BDSC 93028)
   × w ; Sp / CyO ; TM2 / TM6B

F1   select CyO , Tb  →  w ; ppk25-GAL4 / CyO ; ppk25-GAL4 / TM6B
F2   cross to the double balancer again; recover  w ; ppk25-GAL4 / CyO ; TM2 / TM6B
     i.e. chr 3 now carries only balancers.
     VERIFY the chr 3 insertion is gone — both copies are w+ marked, so eye colour will not
     distinguish them. PCR or a UAS-reporter expression check is needed here.

F3 × BDSC 79040, as in Cross A1
STOCK A'   w ; ppk25-GAL4 ; LexAop-post-tG , UAS-pre-tG
```

Cross A2 is the one place PCR is genuinely required.

### Cross A3 — the experiment, repeated per target

```
STOCK A (or A') ♀  ×  w ; R56C09-lexA[attP40] ; +  ♂                    (BDSC 53584)

F1 males   w / Y ; ppk-GAL4 / R56C09-lexA[attP40] ; LexAop-post-tG, UAS-pre-tG / +
```

ppk-GAL4 and R56C09-lexA sit **in trans**, one per homolog of chr 2. Both express; no
recombination is needed. If Stock A and BDSC 53584 are each homozygous for their chr 2 element,
**every F1 male is the experimental genotype** and no selection is required.

Score males only — ppk23 T1 midline crossing is male-specific and *fru*-dependent, and every
connectome prediction comes from the male CNS.

---

## Route B — ppk23-LexA drives the GRNs, target is split-GAL4

Unlocks the split-GAL4 targets already in the lab (SS103018 / AN13B002, the vAB3 candidates).

```
G0   w ; ppk23-LexA / CyO ; TM3, Ser / TM6B                             (Cross 0 output)
   × y w ; Sp / CyO, Dfd-EYFP ; UAS-post-tG , LexAop-pre-tG             (BDSC 79039)

F1   select CyO , Tb
F2   sib cross, select non-CyO non-Tb
STOCK B   w ; ppk23-LexA ; UAS-post-tG , LexAop-pre-tG

Experiment
STOCK B ♀  ×  split-GAL4 target ♂     (SS103018 = AN13B002, etc.)
F1 males   w / Y ; ppk23-LexA / SS-AD ; UAS-post-tG, LexAop-pre-tG / SS-DBD
```

Note the split-GAL4 hemidrivers are typically AD on chr 2 (attP40) and DBD on chr 3 (attP2).
**attP2 is occupied by the t-GRASP post half in BDSC 79039** — so this needs checking per line,
and may not be buildable at all for lines whose DBD is at attP2.

### Route B does not give the ratio

Route B measures only the **ppk23 arm** (both families). The ppk25 arm requires ppk25-GAL4,
which forces the target onto LexA — Route A. Running one arm through Route A and the other
through Route B puts them in different reporter configurations, so the unknown efficiency factor
`k` does not cancel and the ratio is meaningless.

**The single reagent that unlocks Route B properly is `ppk25-LexA`, which exists nowhere.**
Making it converts every split-GAL4 target in the lab into a usable discriminating arm.

Route B is still worth running on its own as a qualitative test: does the ppk23 population
contact AN13B002 at all, as the connectome says it does?

---

## Controls

| Control | Genotype | Answers |
|---|---|---|
| pre half alone | Stock A × `w1118` | reconstitution requires both halves |
| post half alone | `w1118` × 53584, with reporter | same |
| known-zero target | ppk driver × a LexA line the connectome says receives no ppk input | proximity artifact rate |
| reference arm | Route A on R56C09/PPN1 | reagents work; the denominator for every ratio |
| driver-swap | ppk23 vs ppk25 arm at the *same* target | the readout itself |

---

## Timeline

| Step | Generations | Weeks at 25 °C |
|---|---|---|
| Cross 0 | 2 | 4–5 |
| Stock A | 2 | 4–5 |
| Stock A′ (incl. PCR verify) | 3 | 7–9 |
| Each experiment | 1 | 2–3 |

Stocks A and A′ are built once and reused for every target.
