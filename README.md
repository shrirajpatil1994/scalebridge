# ScaleBridge

**AI-native re-engineering of approvals, procurement and audit compliance for India's best-funded urban and housing bodies, starting with Mumbai.**

India's urban bodies spend enormous sums through processes that are fragmented, paper-heavy and slow by design. The Brihanmumbai Municipal Corporation alone budgets over ₹80,000 crore a year (FY27), yet a 2023 special audit by the Comptroller & Auditor General (CAG) found ₹214 crore of works awarded without tender and ₹4,756 crore of works executed without contracts. Across Maharashtra's Urban Development Department, ₹11,040 crore of utilisation certificates were pending in 2024-25. The audit trail exists, but no intelligence sits on top of it.

ScaleBridge is a set of AI modules that sit on top of existing systems (BPMS, MahaTenders, CivitTwin, the CAG's report archive) and make approvals faster, procurement cleaner and audit follow-up continuous, with **humans making every final decision**.

> **Start here: [`docs/IMPACT.md`](docs/IMPACT.md)**: 126 transaction-level audit findings citing ₹3,627 crore, mapped by leakage pattern, with page-level sources.
>
> Status: **v0.1 (private)**. Module M4 (audit intelligence over published CAG reports) is working. M1–M3 are specified in [`SKELETON.md`](SKELETON.md).

---

## Modules

| | Module | What it does | Status |
|---|---|---|---|
| **M4** | **Audit intelligence (CAG reports)** | Cited Q&A and leakage-pattern mining across published CAG reports on Maharashtra urban, housing and infrastructure bodies | **v0.1 working** |
| M2 | Procurement integrity copilot | Reads tenders, bids and work orders; flags patterns CAG keeps finding (no-tender awards, missing contracts, split works, escalation); drafts the evaluation-committee note | Designed ([`docs/design_principles.md`](docs/design_principles.md)) |
| M1 | Approvals: NOC orchestration & post-approval compliance | Tracks every NOC against statutory timelines, drafts deficiency letters, checks developer obligations after approval | Specified |
| M3 | Audit-readiness copilot (auditee side) | Organises evidence and drafts replies to audit observations so inspection-report paras get settled | Specified |

## M4 quick start

```bash
pip install -r requirements.txt          # only needed for --llm mode
python scripts/build_manifest.py         # downloads published CAG reports (public PDFs)
python -m scalebridge.cli ingest         # PDF -> page-level chunks + local index
python -m scalebridge.cli ask "Which works were awarded without inviting tenders?"
python -m scalebridge.cli ask "What did audit find on CIDCO infrastructure contracts?" --llm
python -m scalebridge.cli patterns       # leakage taxonomy across all reports
python eval/run_eval.py                  # retrieval evaluation against the gold set
```

**How it works**
1. **Ingest:** published CAG PDFs → page-level text → ~220-word chunks that keep report and page.
2. **Retrieve:** local BM25 search with an audit-vocabulary expansion (tender ↔ nomination, recovery ↔ dues, idle ↔ unutilised). Runs fully offline, so it can be deployed on a government's own servers.
3. **Tag:** a transparent rule-based leakage taxonomy (no-tender award, contract gaps, cost escalation, short recovery, idle funds, undue benefit, unfruitful expenditure, records not produced, quality control). Each tag carries the exact matched phrase as evidence.
4. **Answer:** extractive by default; with `--llm`, Claude writes an answer in which **every sentence must cite a passage**. Uncited sentences are flagged; if the passages don't answer the question, the required reply is "NOT FOUND IN THE PROVIDED REPORTS".

## Evaluation first

See [`eval/`](eval/). The gold set pairs questions with the report, page and verbatim facts that must be retrieved, plus "not found" questions that must not produce confident answers. Metrics: hit@k, fact recall@k, not-found accuracy and, with `--llm`, citation validity.

## Principles

- **People make the final call** on permits, payments, awards and audit replies. AI prepares, checks, flags and drafts.
- **Evidence or nothing:** every output cites document and page; missing evidence is shown as NOT FOUND, never guessed.
- **The agency owns its data;** the core runs offline and on-premises.
- **Public data only in this repository:** published CAG reports and synthetic data. No inspection reports, draft paragraphs or auditee records.

## Pilot: Mumbai

Entry through BMC and related departments, alongside the Urban Development Department's study group on AI and GIS-based audit of civic works (set up July 2026). Twelve weeks, one module, shadow mode first (AI runs alongside staff, no decisions), with success metrics agreed up front. See [`gtm/`](gtm/).

## Why this matters beyond India

The same modules apply to municipal permitting and supreme audit institutions in the Gulf (Dubai and Abu Dhabi permitting, the UAE Accountability Authority, Qatar's State Audit Bureau), with Arabic evaluation sets.

## About

Built by Shriraj Patil: former Audit Officer at the Comptroller & Auditor General of India, co-founder of an RBI-regulated lender, Chief of Staff at an AI company selling to governments.
