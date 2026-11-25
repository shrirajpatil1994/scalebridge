# Design principles for the M2 procurement-integrity copilot (and shared by all modules)

Generic engineering patterns adapted from the author's experience building a government-tender pipeline. No code or proprietary content is reused.

1. **Staged, auditable chain.** Normalise documents → typed extraction → rule checks → evidence-anchored brief → deterministic routing. Each stage writes its own artifact.
2. **Quote-substring guard.** Every extracted item carries a verbatim quote, a document and a page. Items whose quote is not found in the source text are dropped. If more than half are dropped, the run aborts (likely a scanned or broken PDF).
3. **No fabrication.** Every flag cites document, page and quote. Missing evidence shows as a visible NOT FOUND item, never an inference.
4. **Deterministic final gate.** Routing (flag / clarify / clear) is decided by rules, not by the LLM. First match wins.
5. **Humans decide.** The system never approves, rejects, awards or sends anything. Confidence is capped at "likely" until a person confirms.
6. **Fail closed.** No evaluation note is produced if evidence extraction was thin or unverifiable.
7. **Ground truth is a verified rulebook.** Procurement rules and thresholds (e.g. state e-tender limits, delegation of powers) are encoded as versioned rules with their source.
8. **Canonical keys and dedupe.** Tender and work-order numbers are the keys; near matches go to a human.
9. **Award vs tender reconciliation.** Awards with no matching tender, contracts missing for paid works, and works split below thresholds are surfaced as flags.
10. **Source health.** Data sources are classified as healthy, silent (returns nothing) or broken. Partial data fails loudly.
11. **Pre-release scan of every note.** No placeholders, no unsupported claims, no accusatory language: flags describe patterns and cite evidence; conclusions are for auditors.
12. **Dry-run by default, append-only audit log, cost caps per run, originals never edited.**
