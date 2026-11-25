"""Answer questions over published CAG reports with mandatory citations.

Two modes:
- extractive (default, no API needed): top passages + leakage tags, each with report and page.
- generative (Claude): a written answer where every sentence must cite a passage [n];
  sentences without a valid citation are flagged, and "not found" is the required
  answer when the passages don't support one.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .retrieve import BM25, load_index
from .taxonomy import amounts, tag

MODEL = "claude-opus-5-5"

SYSTEM = """You answer questions about Indian government audit findings using ONLY the numbered passages provided,
which are extracts from published reports of the Comptroller and Auditor General of India (CAG).

Rules:
- Every sentence that states a fact must end with one or more citations like [2] or [1][3], pointing to the passages used.
- Use only facts in the passages. Do not add outside knowledge, estimates or assumptions.
- If the passages do not answer the question, reply exactly: NOT FOUND IN THE PROVIDED REPORTS.
- Report amounts, years and entity names exactly as written in the passages.
- Describe what the audit reported; do not accuse individuals or draw conclusions beyond the report.
- Be concise: at most 8 sentences, then a one-line "Patterns:" list of leakage types seen."""


@dataclass
class Answer:
    question: str
    mode: str
    text: str
    passages: list[dict] = field(default_factory=list)
    uncited_sentences: list[str] = field(default_factory=list)


def best_sentence(text: str, question: str) -> str:
    """The sentence in a passage sharing most terms with the question (evidence snippet)."""
    from .retrieve import tokens
    q = set(tokens(question))
    sents = re.split(r"(?<=[.;])\s+", text)
    best = max(sents, key=lambda s: (len(q & set(tokens(s))), len(s) > 40))
    return best.strip()[:320]


def _passages(index: BM25, question: str, k: int) -> list[dict]:
    out, seen = [], set()
    for score, d in index.search(question, k=k * 3):
        key = (d["file"], d["page"])
        if key in seen:
            continue  # overlapping chunks from the same page: keep the best one
        seen.add(key)
        n = len(out) + 1
        if n > k:
            break
        out.append({
            "n": n, "evidence": best_sentence(d["text"], question), "score": round(score, 2), "report_id": d["report_id"], "report_title": d["report_title"],
            "file": d["file"], "page": d["page"], "text": d["text"],
            "tags": tag(d["text"].replace("` ", "₹ ")), "amounts": amounts(d["text"])[:5],
        })
    return out


def _cite_check(text: str, n_max: int) -> list[str]:
    if text.strip().startswith("NOT FOUND"):
        return []
    body = text.split("Patterns:")[0]
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if len(s.strip()) > 20]
    bad = []
    for s in sents:
        cites = [int(c) for c in re.findall(r"\[(\d+)\]", s)]
        if not cites or any(c < 1 or c > n_max for c in cites):
            bad.append(s)
    return bad


def _answerable(index: BM25, question: str) -> bool:
    from .retrieve import ANSWERABLE_MIN, coverage
    top = index.search(question, k=3)
    return bool(top) and max(coverage(index, question, d) for _, d in top) >= ANSWERABLE_MIN


def extractive(question: str, index: BM25 | None = None, k: int = 6) -> Answer:
    index = index or load_index()
    ps = _passages(index, question, k)
    if not ps or not _answerable(index, question):
        return Answer(question, "extractive", "NOT FOUND IN THE PROVIDED REPORTS.", [])
    lines = []
    for p in ps:
        tags = ", ".join(t["label"] for t in p["tags"]) or "no pattern tagged"
        lines.append(f"[{p['n']}] {p['report_title'][:80]} (p.{p['page']})\n    \"{p['evidence']}\"\n    Pattern: {tags}. {', '.join(p['amounts'][:3])}")
    return Answer(question, "extractive", "\n".join(lines), ps)


def generative(question: str, index: BM25 | None = None, k: int = 8) -> Answer:
    """Claude-written answer; falls back to extractive if the API is unavailable."""
    index = index or load_index()
    ps = _passages(index, question, k)
    if not ps or not _answerable(index, question):
        return Answer(question, "generative", "NOT FOUND IN THE PROVIDED REPORTS.", [])
    try:
        import anthropic
        client = anthropic.Anthropic()
        context = "\n\n".join(f"[{p['n']}] Source: {p['report_title']} (page {p['page']})\n{p['text']}" for p in ps)
        resp = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SYSTEM,
            messages=[{"role": "user", "content": f"Passages:\n\n{context}\n\nQuestion: {question}"}],
        )
        if resp.stop_reason == "refusal":
            return Answer(question, "generative", "The model declined this request; showing cited passages instead.\n"
                          + extractive(question, index).text, ps)
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        return Answer(question, "generative", text, ps, _cite_check(text, len(ps)))
    except Exception as e:  # no credentials, network, or API error: never fabricate, fall back
        ans = extractive(question, index)
        ans.text = f"(Generative mode unavailable: {type(e).__name__}. Showing cited passages.)\n" + ans.text
        return ans
