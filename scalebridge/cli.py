"""ScaleBridge CLI.

  python -m scalebridge.cli ingest                 # PDFs -> chunks index
  python -m scalebridge.cli ask "question" [--llm] # cited answer
  python -m scalebridge.cli patterns [--top 15]    # leakage-pattern table across all reports
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict

from . import ingest
from .answer import extractive, generative
from .retrieve import load_index
from .taxonomy import TAXONOMY, amounts, tag


def patterns(top: int) -> None:
    idx = load_index()
    by_tag: dict[str, Counter] = defaultdict(Counter)
    examples: dict[str, list] = defaultdict(list)
    for d in idx.docs:
        for t in tag(d["text"]):
            by_tag[t["tag"]][d["report_title"][:70]] += 1
            if len(examples[t["tag"]]) < 3:
                examples[t["tag"]].append(f'{d["report_title"][:60]} p.{d["page"]}: "{t["evidence"]}" {", ".join(amounts(d["text"])[:2])}')
    print(f"{'Pattern':<58} {'Passages':>8} {'Reports':>8}")
    for key in sorted(by_tag, key=lambda k: -sum(by_tag[k].values())):
        print(f"{TAXONOMY[key]['label'][:58]:<58} {sum(by_tag[key].values()):>8} {len(by_tag[key]):>8}")
        for ex in examples[key][:2]:
            print(f"    e.g. {ex}")


def main() -> None:
    ap = argparse.ArgumentParser(prog="scalebridge")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ingest")
    a = sub.add_parser("ask"); a.add_argument("question"); a.add_argument("--llm", action="store_true"); a.add_argument("--json", action="store_true")
    p = sub.add_parser("patterns"); p.add_argument("--top", type=int, default=15)
    args = ap.parse_args()
    if args.cmd == "ingest":
        ingest.build()
    elif args.cmd == "ask":
        ans = generative(args.question) if args.llm else extractive(args.question)
        if args.json:
            print(json.dumps(ans.__dict__, ensure_ascii=False, indent=1)); return
        print(f"\nQ: {ans.question}\nMode: {ans.mode}\n\n{ans.text}\n")
        print("Sources:")
        for p_ in ans.passages:
            print(f"  [{p_['n']}] {p_['report_title'][:100]} | file {p_['file']} | page {p_['page']}")
        if ans.uncited_sentences:
            print("\nWARNING: sentences without a valid citation:")
            for s in ans.uncited_sentences: print("  -", s)
    elif args.cmd == "patterns":
        patterns(args.top)


if __name__ == "__main__":
    main()
