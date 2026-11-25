# ScaleBridge: design skeleton


**One line:** AI-native re-engineering of approvals, procurement and audit compliance for India's best-funded urban and housing bodies (BMC, MHADA, CIDCO, MMRDA, SRA), starting with a one-district pilot in Maharashtra, plus an audit-intelligence layer built only on published CAG reports.

---

## 0. Principles (borrowed from how Scale says it deploys for governments)
1. **Evaluation first:** every module ships with a gold test set and a pass bar before any pilot.
2. **People make the final call** on permits, approvals, payments and audit replies. AI prepares, checks, flags and drafts.
3. **The agency owns its data and assets;** sovereign/on-prem deployable (no public-cloud dependency for sensitive data).
4. **Public or synthetic data only in this repo.** No inspection reports, draft paras or auditee records (they are not public).

## 1. The problem (with evidence)
| Area | What's broken | Evidence |
|---|---|---|
| Approvals | ~8,000 redevelopment proposals/year at BMC, ~60% rejected on technical grounds; NOCs from many agencies; a single NOC portal outage (NOCAS, aviation) stalled 500+ proposals for ~2 months | FPJ 29 May 2026; FPJ 2 Nov 2026 |
| Procurement | CAG special audit of BMC (2023): 20 works (Rs 214 cr) awarded without tender; 64 works (Rs 4,756 cr) without contracts; Rs 3,539 cr unauditable (records not produced) | CAG, tabled 25 Mar 2023 |
| Compliance after approval | MHADA: 40 of 43 developers owe Rs 261 cr on transit tenements; SRA: excess TDR ~Rs 35.8 cr, Rs 18.5 cr undue benefit | CAG via press, 2025–26 |
| Funds and audit follow-up | UDD: Rs 11,040 cr of utilisation certificates pending (highest of any dept), Rs 7,970 cr idle; 2,408 IRs with 10,340 observations unresolved (Jun 2023) | CAG State Finances 2024-25; FPJ 31 Mar 2026 |

**What already exists (we build around it, not against it):** BMC's CivitTwin (AI pre-scrutiny of building plans, May 2026); BPMS statewide permits; MahaTenders e-procurement; CAG's in-house CAG-LLM, CDMA analytics and 16 startup AI projects; UDD's study group on AI/GIS audit of civic works (Jul 2026).

## 2. Modules
### M1. Approvals: NOC orchestration & compliance agent (post-pre-scrutiny)
- Ingests an application (BPMS-style), identifies required NOCs, tracks each agency's clock against Right to Public Services timelines, drafts deficiency letters, predicts stuck files.
- Post-approval: checks plinth/occupancy-stage submissions and developer obligations (e.g. transit rent, rehab units) against approval conditions.
- Scale analogue: Building Permits Automation, Business License Automation.

### M2. Procurement integrity copilot
- Reads tender documents, bids and work orders; flags red patterns CAG keeps finding: no-tender/nomination awards, missing contracts, split works below e-tender thresholds, abnormal cost escalation, repeat-bidder rings, mismatched rates.
- Drafts the evaluation note for the committee (human decides).
- Scale analogue: RFQ Evaluation, Document Contract Extraction.

### M3. Audit-readiness copilot (auditee side)
- For the agency, not the auditor: organises evidence, drafts replies to audit observations and inspection-report paras, tracks compliance until settled; aims at the IR backlog.
- Scale analogue: Legal Department Agent (review → draft → expert approves, feedback loop).

### M4. Audit intelligence on published CAG reports (public-data demo)
- Retrieval over published CAG reports (2,754 on cag.gov.in) for Maharashtra urban/housing bodies: leakage taxonomy, recurring-pattern mining across years and bodies, "what did CAG say about X" with citations.
- Positioned as a **complement** to CAG-LLM / CDMA and a public-accountability tool, and as a reference for the CAG's May 2026 call for a Sovereign AI Platform.

## 3. Prototype scope (v0.1, buildable in ~5–7 days)
| Build | Data | Output |
|---|---|---|
| M4 RAG app over ~20–40 published CAG reports (Maharashtra urban/housing + BMC special audit) | Public PDFs | Cited Q&A + leakage-pattern table |
| M2 red-flag engine on a synthetic tender dataset seeded with CAG-documented patterns | Synthetic | Flag list + evaluation-committee note |
| M1 NOC tracker demo on synthetic applications | Synthetic | Status board, delay prediction, draft deficiency letter |
| Eval harness | Gold Q&A (50) + labelled flags (100) | Accuracy, citation precision, false-flag rate |
Stack: Python, Claude API (or open model for sovereign mode), local vector store, simple web UI (Streamlit). No real citizen data.

## 4. Evaluation
- **M4:** 50 gold questions from published reports; metrics: answer accuracy, citation precision, hallucination rate.
- **M2:** 100 synthetic tenders with known injected red flags; precision/recall, false-alarm cost.
- **M1:** delay-prediction accuracy on synthetic timelines; deficiency-letter completeness vs checklist.
- Language: English + Marathi (pilot reality); Arabic as the Gulf extension (Section 7).

## 5. One-district pilot plan
- **Candidates:** Thane / Kalyan-Dombivli / Navi Mumbai, Pune, Nashik (BPMS-online councils; outside MCGM).
- **Entry point:** UDD study group on AI/GIS audit of civic works (GR 29 Jul 2026) + your Maharashtra network; Directorate of Municipal Administration.
- **Shape:** 12 weeks, one module (M2 or M1), read-only access, shadow mode (AI runs alongside humans, no decisions), weekly metrics; exit criteria agreed upfront.
- **Success metrics:** approval cycle time, % first-time-right applications, red flags caught pre-award, audit replies on time.

## 6. Go-to-market
- **Buyers:** Municipal Commissioner (economic + political owner), UDD Principal Secretary, MahaIT (tech), Chief Auditor / vigilance; for M4: CAG IT/CDMA, legislators' committees, civil society.
- **Route:** pilot via MoU / innovation challenge → GeM or tender for scale-up; CAG Sovereign AI EOI as a parallel track.
- **Pricing logic:** fixed-fee pilot → per-module subscription per body → state-wide platform licence.
- **Land → expand:** one district → state UDD (all councils) → MHADA/SRA/CIDCO → other states.
- **Risks:** procurement cycles, data access, political sensitivity of "leakage" findings, CAG's in-house build; mitigations in `gtm/`.

## 7. Why Scale (and the Gulf)
- Scale already sells Building Permits Automation, RFQ Evaluation, Contract Extraction and Legal agents to governments, and its Qatar work (MCIT; Ministry of Justice "Shoor", Nov 2026) shows the national-partnership → ministry-app pattern.
- PRAMAAN shows (a) the same playbook in a new, very large market, (b) a procurement and audit depth Scale's catalogue doesn't show yet, (c) evaluation-first delivery.
- **Gulf transfer:** same modules for Dubai Municipality / Abu Dhabi DMT permits, government procurement, and supreme audit institutions (UAE Accountability Authority, Qatar State Audit Bureau), with Arabic evaluation sets.

## 8. Repo layout
```
README.md            pitch, problem, demo GIF, results, why Scale
docs/problem.md      evidence table with sources
docs/bpr_maps.md     as-is vs to-be process maps (approvals, procurement, audit reply)
solution/m1_approvals/  m2_procurement/  m3_audit_readiness/  m4_cag_rag/
eval/                gold sets, harness, results.md
gtm/                 buyer map, pilot plan, pricing, 90-day plan, risks
data/                public reports (links + loader), synthetic generators
corpus/              research extracts (Scale, India)
```

## 9. Guardrails
- Only published CAG reports; nothing from your CAG service years that isn't public.
- Name institutions only via published findings; avoid naming individuals.
- Synthetic data clearly labelled.

## 10. Decisions made
1. Name: **ScaleBridge**.
2. Lead module for the demo: **M4, audit intelligence over published CAG reports** (v0.1 built; see `eval/results.md`).
3. Pilot: **Mumbai**, embedding with BMC and related departments.
4. Procurement module (M2) reuses generic design principles from tender-pipeline experience (`docs/design_principles.md`).
