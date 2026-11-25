# M4 evaluation results: v0.1 (25 Nov 2026)

Corpus: 15 published CAG reports on Maharashtra (state finances, compliance audits, local bodies, urban local bodies under the 74th Amendment, CIDCO, MMRDA monorail, slum improvement, PSUs), 146 PDFs, **5,592 page-anchored passages**. 8 files are scanned images and are queued for OCR, not guessed.

| Set | Questions | hit@5 | hit@3 | fact recall@5 | not-found accuracy |
|---|---|---|---|---|---|
| Development (`gold.jsonl`) | 18 lookups + 4 not-found | 18/18 (100%) | 18/18 | 22/22 | 4/4 |
| Held-out (`heldout.jsonl`, run once, no tuning) | 9 lookups + 2 not-found | 9/9 (100%) | – | 9/9 | 2/2 |

**What changed during development (from 83% to 100% hit@5):** keep one passage per page; IDF-weighted answerability gate (NOT FOUND when distinctive query terms are missing); light stemming ("recover" vs "recovered"); gold labels widened where a second report is an equally valid source.

## Honest limitations
1. **Self-authored questions.** Both sets were written by the builder while reading source passages, so wording overlaps with the reports. Real users phrase differently. Next: an independent set written by former audit officers who have not seen the passages.
2. **Generative mode not yet measured.** Claude-written answers with mandatory citations are implemented; citation validity will be scored once API credentials are configured (`python eval/run_eval.py --llm`).
3. **Tagger precision not yet measured.** The leakage tagger is rule-based and transparent, but can fire on headings or passing mentions. Next: 100 hand-labelled passages to measure precision and recall per tag.
4. **Coverage gaps.** The 2023 CAG special audit of BMC was tabled in the state legislature and is not on cag.gov.in; it is not in the corpus yet. 8 scanned PDFs need OCR. Marathi pages are indexed, but there is no Marathi query expansion yet.
