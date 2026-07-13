#!/usr/bin/env python3
"""Multi-model cross-validation for the Evidence-Integrity Benchmark.

Removes single-author bias: instead of trusting one person's gold labels, run
several independent models as judges, then measure how much they AGREE. Where
models converge = defensible consensus ground truth. Where they split = the
genuinely hard items (your v0.2 targets).

Usage:
    python3 crossval.py benchmark_v0.2.jsonl ModelA=preds_a.json ModelB=preds_b.json ModelC=preds_c.json

Reports two agreement views:
  - FULL   : exact 5-way verdict agreement (strict).
  - SAFETY : the only line that ships a false claim -- SUPPORTS vs not-SUPPORTS.
    Models can disagree on the *shade* of "not supported" (PARTIAL vs UNSUPPORTED
    vs CONTRADICTS) without any of them wrongly greenlighting a claim. Safety
    agreement is what matters for an assurance tool.
"""
import json, sys, itertools
from collections import Counter

def load_jsonl(p): return [json.loads(l) for l in open(p) if l.strip()]

def main(bench_path, model_args):
    bench = load_jsonl(bench_path)
    ids = [it["id"] for it in bench]
    gold = {it["id"]: it["gold_verdict"] for it in bench}
    models = {}
    for a in model_args:
        label, path = a.split("=", 1)
        models[label] = json.load(open(path))
    names = list(models)
    n = len(bench)

    def binm(v): return "SUPPORTS" if v == "SUPPORTS" else "NOT"

    # consensus (majority; tie -> SPLIT)
    consensus = {}
    split_items = []
    for id_ in ids:
        votes = Counter(models[m].get(id_, "?") for m in names)
        top, c = votes.most_common(1)[0]
        if c > len(names)/2:
            consensus[id_] = top
        else:
            consensus[id_] = "SPLIT"; split_items.append(id_)

    # agreement stats
    def pair_agree(a, b, fn):
        return sum(fn(models[a].get(i)) == fn(models[b].get(i)) for i in ids)/n
    pairs = list(itertools.combinations(names, 2))
    full_pair = {p: pair_agree(*p, fn=lambda v: v) for p in pairs}
    safe_pair = {p: pair_agree(*p, fn=binm) for p in pairs}
    unanim_full = sum(len({models[m].get(i) for m in names}) == 1 for i in ids)/n
    unanim_safe = sum(len({binm(models[m].get(i)) for m in names}) == 1 for i in ids)/n

    print("="*70)
    print(f"  models: {', '.join(names)}   items: {n}")
    print("-"*70)
    print("  AGREEMENT")
    print(f"    exact 5-way, unanimous:      {unanim_full:.0%} of items")
    print(f"    SAFETY (grounded/not), unanimous: {unanim_safe:.0%} of items   <-- the one that matters")
    if pairs:
        print("    pairwise:")
        for p in pairs:
            print(f"      {p[0]} vs {p[1]:<10} full {full_pair[p]:.0%}   safety {safe_pair[p]:.0%}")
    print("-"*70)
    # overclaim of each model vs consensus (where consensus is a clear non-SUPPORTS)
    print("  OVERCLAIM vs consensus (model says SUPPORTS where consensus says otherwise):")
    for m in names:
        oc = [i for i in ids if consensus[i] not in ("SUPPORTS","SPLIT") and models[m].get(i)=="SUPPORTS"]
        denom = [i for i in ids if consensus[i] not in ("SUPPORTS","SPLIT")]
        print(f"    {m:<10} {len(oc)}/{len(denom)} = {len(oc)/max(1,len(denom)):.0%}")
    print("-"*70)
    print(f"  HARD CASES (models split — no majority): {len(split_items)}")
    for i in split_items:
        fam = next(it['attack_family'] for it in bench if it['id']==i)
        calls = "  ".join(f"{m}={models[m].get(i)}" for m in names)
        print(f"    {i} [{fam}]  {calls}")
    print("-"*70)
    # where the authored gold diverges from model consensus (which of MY labels are idiosyncratic)
    div = [i for i in ids if consensus[i] not in ("SPLIT",) and consensus[i] != gold[i]]
    print(f"  AUTHORED-GOLD vs CONSENSUS mismatches (candidate label fixes): {len(div)}")
    for i in div:
        print(f"    {i}  gold={gold[i]}  consensus={consensus[i]}")
    print("="*70)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    main(sys.argv[1], sys.argv[2:])
