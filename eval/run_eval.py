"""Evaluation harness for M4 (CAG report retrieval + answering).

Gold set: eval/gold.jsonl, one object per line:
  {"id": "q01", "question": "...", "report_id": "117101", "pages": [34, 35],
   "facts": ["exact phrase or amount that must be retrieved"], "type": "lookup|pattern|not_found"}

Metrics
- hit@k: a top-k passage comes from the gold report and one of the gold pages (+/-1 page).
- fact_recall@k: share of gold facts that appear verbatim in the top-k passages.
- not_found accuracy: for questions with no answer in the corpus, the system must not
  return a confident passage (top score below threshold) - generative mode must say NOT FOUND.
- citation_validity (only with --llm): share of answer sentences carrying a valid [n] citation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scalebridge.answer import generative  # noqa: E402
from scalebridge.retrieve import ANSWERABLE_MIN, coverage, load_index  # noqa: E402

GOLD = Path(__file__).with_name("gold.jsonl")


def norm(s: str) -> str:
    return " ".join(s.lower().replace(",", "").split())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--gold", default=str(GOLD))
    ap.add_argument("--llm", action="store_true", help="also score generated answers (spends API tokens)")
    args = ap.parse_args()
    idx = load_index()
    gold = [json.loads(l) for l in Path(args.gold).read_text().splitlines() if l.strip()]
    rows, hits, facts_hit, facts_total, nf_ok, nf_total, cite_ok, cite_total = [], 0, 0, 0, 0, 0, 0, 0
    for g in gold:
        res = idx.search(g["question"], k=args.k)
        if g.get("type") == "not_found":
            nf_total += 1
            cov = max((coverage(idx, g["question"], d) for _, d in res[:3]), default=0.0)
            ok = cov < ANSWERABLE_MIN
            nf_ok += ok
            rows.append((g["id"], "not_found", "PASS" if ok else "FAIL", f"coverage {cov:.2f}"))
            continue
        pages = set(g.get("pages", []))
        # hit = a top-k passage from the gold report that is on a gold page (+/-1) OR contains a gold fact
        ok_reports = set(g.get("report_ids", [g["report_id"]]))
        hit = any(d["report_id"] in ok_reports and ((not pages or any(abs(d["page"] - p) <= 1 for p in pages))
                  or any(norm(f) in norm(d["text"]) for f in g.get("facts", []))) for _, d in res)
        cov = max((coverage(idx, g["question"], d) for _, d in res[:3]), default=0.0)
        if cov < ANSWERABLE_MIN:
            hit = False  # the system would have said NOT FOUND
        hits += hit
        blob = norm(" ".join(d["text"] for _, d in res))
        fh = sum(norm(f) in blob for f in g.get("facts", []))
        facts_hit += fh; facts_total += len(g.get("facts", []))
        note = ""
        if args.llm:
            ans = generative(g["question"], idx)
            body = ans.text.split("Patterns:")[0]
            n_sent = max(1, body.count(". ") + 1)
            cite_total += n_sent; cite_ok += n_sent - len(ans.uncited_sentences)
            note = f"uncited={len(ans.uncited_sentences)}"
        rows.append((g["id"], g.get("type", "lookup"), "HIT" if hit else "MISS", f"facts {fh}/{len(g.get('facts', []))} {note}"))
    n = len(gold) - nf_total
    print(f"{'id':<6}{'type':<11}{'result':<7}detail")
    for r in rows:
        print(f"{r[0]:<6}{r[1]:<11}{r[2]:<7}{r[3]}")
    print(f"\nhit@{args.k}: {hits}/{n} = {hits / max(1, n):.0%}")
    print(f"fact_recall@{args.k}: {facts_hit}/{facts_total} = {facts_hit / max(1, facts_total):.0%}")
    if nf_total:
        print(f"not_found accuracy: {nf_ok}/{nf_total}")
    if args.llm:
        print(f"citation_validity: {cite_ok}/{cite_total} = {cite_ok / max(1, cite_total):.0%}")


if __name__ == "__main__":
    main()
