"""Leakage taxonomy for audit findings, and a transparent rule-based tagger (v0.1).

Rules are explicit and reviewable; an LLM tagger can be layered on later but never
replaces the citation requirement. Tags describe *patterns reported by CAG*,
not conclusions about individuals.
"""
from __future__ import annotations

import re

TAXONOMY: dict[str, dict] = {
    "no_tender_award": {
        "label": "Work awarded without tender / on nomination",
        "patterns": [r"without (inviting )?tender", r"on nomination basis", r"without competitive bidding", r"without calling (for )?tenders"],
    },
    "contract_gaps": {
        "label": "Missing or defective contract / agreement",
        "patterns": [r"without (executing|entering into) (an |any )?(agreement|contract)", r"no (formal )?(agreement|contract) (was|had been) (executed|signed)", r"agreement was not executed"],
    },
    "cost_escalation": {
        "label": "Cost overrun / escalation / time overrun",
        "patterns": [r"cost (overrun|escalation)", r"time overrun", r"revised (cost|estimate)", r"price variation"],
    },
    "short_recovery": {
        "label": "Short / non-recovery of dues",
        "patterns": [r"short recovery", r"non[- ]recovery", r"not recovered", r"(dues|arrears) of ₹?\s?[\d,\.]+ (crore|lakh)", r"outstanding (dues|recover)"],
    },
    "idle_funds": {
        "label": "Idle / unutilised / parked funds; pending utilisation certificates",
        "patterns": [r"unutilised", r"unspent", r"remained idle", r"utilisation certificates? (were )?(pending|not (been )?(submitted|received))", r"parked (in|funds)"],
    },
    "undue_benefit": {
        "label": "Undue benefit / excess payment to contractor or developer",
        "patterns": [r"undue (benefit|favour)", r"excess payment", r"irregular payment", r"inadmissible payment", r"excess (TDR|FSI)"],
    },
    "unfruitful_expenditure": {
        "label": "Unfruitful / infructuous / avoidable expenditure",
        "patterns": [r"unfruitful", r"infructuous", r"avoidable expenditure", r"wasteful expenditure", r"idle (assets?|investment)"],
    },
    "records_not_produced": {
        "label": "Records not produced / not auditable",
        "patterns": [r"records? (were |was )?not (produced|made available|furnished)", r"could not be (verified|audited)"],
    },
    "quality_control": {
        "label": "Quality control / third-party inspection lapses",
        "patterns": [r"third[- ]party (quality|inspection|audit)", r"quality (control|assurance) (was|were) not", r"substandard"],
    },
}

_COMPILED = {k: [re.compile(p, re.I) for p in v["patterns"]] for k, v in TAXONOMY.items()}
AMOUNT = re.compile(r"[₹`]\s?([\d,]+(?:\.\d+)?)\s?(crore|lakh)|Rs\.?\s?([\d,]+(?:\.\d+)?)\s?(crore|lakh)", re.I)


def is_toc_like(text: str) -> bool:
    """Tables of contents / index pages: many numbers, few sentences. Not findings."""
    digits = sum(c.isdigit() for c in text)
    return digits / max(1, len(text)) > 0.12 or text.count(". ") < 2


def tag(text: str) -> list[dict]:
    """Return tags with the exact matched phrase (evidence) for each hit."""
    if is_toc_like(text):
        return []
    hits = []
    for key, regs in _COMPILED.items():
        for r in regs:
            m = r.search(text)
            if m:
                hits.append({"tag": key, "label": TAXONOMY[key]["label"], "evidence": m.group(0)})
                break
    return hits


def amounts(text: str) -> list[str]:
    out = []
    for m in AMOUNT.finditer(text):
        num, unit = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        out.append(f"₹{num} {unit.lower()}")
    return out
