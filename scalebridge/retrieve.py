"""Local BM25 retrieval over CAG report chunks. No external services: sovereign-friendly."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data" / "index"

STOP = set("""a an the of and or to in on for by with from at as is are was were be been being this that these those
it its into than then there their which who whom whose what when where why how not no nor but if so such
under over per also may shall should would could will can has have had do does did""".split())

# Light query expansion with audit vocabulary (Indian public finance terms).
SYNONYMS = {
    "tender": ["tendering", "e-tender", "bids", "bidding", "nomination"],
    "contract": ["agreement", "work order", "contractor"],
    "leakage": ["loss", "excess", "irregular", "unfruitful", "infructuous", "undue"],
    "delay": ["delayed", "time overrun", "pending", "non-completion"],
    "escalation": ["cost overrun", "price variation", "revised estimate"],
    "recovery": ["short recovery", "non-recovery", "dues", "outstanding"],
    "idle": ["unutilised", "unspent", "parked", "blocked"],
    "housing": ["mhada", "slum", "sra", "tenements", "rehabilitation"],
    "bmc": ["brihanmumbai", "mcgm", "municipal corporation"],
}


def stem(t: str) -> str:
    """Very light English stemming so 'recovered'/'recovery'/'recover' and 'tenders'/'tender' meet."""
    if t[0].isdigit() or len(t) <= 4:
        return t
    for suf in ("ations", "ation", "ings", "ing", "ies", "ied", "ery", "ed", "es", "s"):
        if t.endswith(suf) and len(t) - len(suf) >= 4:
            return t[: -len(suf)] + ("y" if suf in ("ies", "ied") else "")
    return t


def tokens(text: str) -> list[str]:
    return [stem(t) for t in re.findall(r"[a-z0-9][a-z0-9\-\.]*", text.lower()) if t not in STOP and len(t) > 1]


class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs: list[dict] = []
        self.tf: list[Counter] = []
        self.df: Counter = Counter()
        self.avgdl = 0.0

    def fit(self, docs: list[dict]) -> "BM25":
        self.docs = docs
        for d in docs:
            c = Counter(tokens(d["text"] + " " + d.get("report_title", "")))
            self.tf.append(c)
            self.df.update(c.keys())
        self.avgdl = sum(sum(c.values()) for c in self.tf) / max(1, len(self.tf))
        return self

    def score(self, q: list[str], i: int) -> float:
        tf, dl, n, s = self.tf[i], sum(self.tf[i].values()), len(self.docs), 0.0
        for t in q:
            if t not in tf:
                continue
            idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
            s += idf * tf[t] * (self.k1 + 1) / (tf[t] + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s

    def search(self, query: str, k: int = 8) -> list[tuple[float, dict]]:
        q = tokens(query)
        for t in list(q):
            for key, alts in SYNONYMS.items():
                if t.startswith(key):
                    q += tokens(" ".join(alts))
        scored = [(self.score(q, i), d) for i, d in enumerate(self.docs)]
        scored = [x for x in scored if x[0] > 0]
        scored.sort(key=lambda x: -x[0])
        return scored[:k]


def coverage(index: "BM25", query: str, doc: dict) -> float:
    """IDF-weighted share of the query's distinctive terms present in the passage.
    Terms absent from the whole corpus count fully against coverage. Used to say NOT FOUND
    instead of returning the 'least bad' passage."""
    n = len(index.docs)
    q = list(dict.fromkeys(tokens(query)))
    if not q:
        return 0.0
    dt = set(tokens(doc["text"] + " " + doc.get("report_title", "")))
    def idf(t: str) -> float:
        return math.log(1 + (n - index.df.get(t, 0) + 0.5) / (index.df.get(t, 0) + 0.5))
    total = sum(idf(t) for t in q)
    return sum(idf(t) for t in q if t in dt) / total if total else 0.0


ANSWERABLE_MIN = 0.5


def load_index() -> BM25:
    docs = [json.loads(l) for l in (INDEX / "chunks.jsonl").read_text().splitlines() if l.strip()]
    return BM25().fit(docs)
