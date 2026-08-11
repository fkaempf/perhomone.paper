#!/usr/bin/env python3
"""Match the t-GRASP reagent worklist against the lab stock inventory (flomington).

Primary source: the newest local flomington snapshot (backups/<ts>/stocks.json), which carries
janelia_line / source_id / flybase_id and so can be matched on stock number and line name, not
just genotype text. Falls back to complete_lab_stocks.xlsx.

NOTE: live data lives in the flomington Supabase instance; this reads a local snapshot only.
"""
import json, re, glob, os, sys

FLOM = "/Users/fkampf/Documents/flomington"
OUT  = "/Users/fkampf/Documents/pheromone.paper/receptor_typing_validation/data"

def newest_snapshot():
    snaps = sorted(glob.glob(f"{FLOM}/backups/*/stocks.json"))
    return snaps[-1] if snaps else None

# what the experiment needs -> how to recognise it
WORKLIST = [
    ("ppk23-GAL4",        "core", r"ppk23", "BDSC 93026 - GAL4 arm, labels M+F"),
    ("ppk25-GAL4",        "core", r"ppk25", "BDSC 93028 - GAL4 arm, F family only"),
    ("R56C09 (any)",      "core", r"56c09", "BDSC 53584 lexA / 39145 GAL4 - PPN1 arm"),
    ("t-GRASP",           "core", r"t-?grasp|pre-?t-?grasp|post-?t-?grasp", "BDSC 79040"),
    ("GRASP / spGFP",     "core", r"\bgrasp\b|spgfp|sp-?gfp1-?10|spgfp11|cd4-?spgfp", "any GRASP reporter"),
    ("Ir52a / Ir52b",     "opt",  r"ir52", "WG1/WG2 Ir52 arm"),
    ("Gr32a",             "opt",  r"gr32a", "Wang 2011 aggression channel"),
    ("mAL split-GAL4",    "have", r"\bmal\b", "downstream node, already in the paper"),
    ("fru",               "have", r"\bfru\b|fruitless", "male-specific circuit"),
    ("LexAop reporters",  "have", r"lexaop|lexa[\s\-_]?op", "LexA-side reporters in stock"),
    ("LexA drivers",      "have", r"lexa", "LexA drivers in stock"),
    ("QUAS / QF",         "have", r"quas|\bqf2?\b", "third binary system"),
    ("vGlut",             "warn", r"vglut", "do NOT use as an F-cell proxy - circular"),
]

BDSC_NEEDED = {"93026":"ppk23-GAL4","93028":"ppk25-GAL4","53584":"R56C09-lexA",
               "79040":"UAS-pre + LexAop-post t-GRASP","39145":"R56C09-GAL4 (blocked, attP2)"}

def load():
    snap = newest_snapshot()
    if snap:
        rows = json.load(open(snap))
        src  = f"flomington snapshot {os.path.basename(os.path.dirname(snap))}"
        recs = [{
            "id": str(r.get("id","")), "name": r.get("name") or "",
            "genotype": r.get("genotype") or "", "janelia": r.get("janelia_line") or "",
            "source": r.get("source") or "", "source_id": str(r.get("source_id") or ""),
            "flybase": r.get("flybase_id") or "", "loc": r.get("location") or "",
            "keeper": r.get("maintainer") or "", "notes": r.get("notes") or "",
            "cat": r.get("category") or "",
        } for r in rows]
        return recs, src
    import openpyxl
    ws = openpyxl.load_workbook(f"{FLOM}/complete_lab_stocks.xlsx", read_only=True,
                                data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True)); h = [str(x or "") for x in rows[0]]
    recs = [{"id":str(r[h.index('UniqueStockID')] or ""),"name":"",
             "genotype":str(r[h.index('Genotype')] or "").strip('"'),
             "janelia":"","source":"","source_id":"","flybase":"","loc":"","keeper":"",
             "notes":str(r[h.index('Comments')] or ""),"cat":""}
            for r in rows[1:] if r and r[h.index('Genotype')]]
    return recs, "complete_lab_stocks.xlsx (STALE - Mar 2026)"

def blob(r):
    return " ".join([r["name"], r["genotype"], r["janelia"], r["notes"], r["cat"]])

def main():
    recs, src = load()
    print(f"source: {src}")
    print(f"stocks: {len(recs)}\n")

    print("=" * 78)
    print("BDSC STOCKS THE EXPERIMENT NEEDS - do we already have them?")
    print("=" * 78)
    have_ids = {r["source_id"] for r in recs if r["source_id"]}
    for num, what in BDSC_NEEDED.items():
        hits = [r for r in recs if r["source_id"] == num or num in blob(r)]
        mark = "IN LAB " if hits else "ORDER  "
        print(f"[{mark}] BDSC {num:<7} {what}")
        for r in hits[:3]:
            print(f"           #{r['id'][:8]} {r['name'][:40]} | {r['loc']} | {r['keeper']}")
    print()

    print("=" * 78)
    print("REAGENT CLASSES")
    print("=" * 78)
    summary = {}
    for label, kind, pat, why in WORKLIST:
        rx = re.compile(pat, re.I)
        hits = [r for r in recs if rx.search(blob(r))]
        summary[label] = len(hits)
        mark = {"core":"ORDER  ","opt":"ORDER  ","have":"IN LAB ","warn":"AVOID  "}[kind]
        if hits and kind in ("core","opt"): mark = "IN LAB "
        if not hits and kind == "have":     mark = "MISSING"
        print(f"[{mark}] {label:<20} {len(hits):>3}  -- {why}")
        for r in hits[:6]:
            tag = f" [{r['source']} {r['source_id']}]" if r["source_id"] else ""
            jl  = f" <{r['janelia']}>" if r["janelia"] else ""
            print(f"           #{r['id'][:8]} {(r['name'] or r['genotype'])[:62]}{jl}{tag}")
        if len(hits) > 6: print(f"           ... {len(hits)-6} more")
        print()

    os.makedirs(OUT, exist_ok=True)
    json.dump({"source": src, "n_stocks": len(recs), "counts": summary},
              open(f"{OUT}/lab_stock_match.json", "w"), indent=1)
    print(f"written: {OUT}/lab_stock_match.json")

if __name__ == "__main__":
    main()
