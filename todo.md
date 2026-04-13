# Assignment 2 — To-Do List

> Tracks all tasks from `planning.md`. Work through these in order — each phase depends on the one before it.

---

## Phase 1 — BigQuery Setup

- [ ] Create a BigQuery VIEW in the `data-vis-491514` project that flattens the public dataset into a single queryable table:
  ```sql
  CREATE OR REPLACE VIEW `data-vis-491514.ga4_view.ga4_ecommerce_view` AS
  SELECT * FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
  ```
- [ ] Verify the VIEW works by running a quick `SELECT COUNT(*) FROM <view>` and confirming row count is reasonable
- [ ] Enable the **Conversational Analytics API** in Google Cloud Console (APIs & Services → Enable APIs)

---

## Phase 2 — Build the Data Agent

- [ ] Open BigQuery Studio and create a new **Data Agent**
- [ ] Point the agent at the VIEW created in Phase 1 (not the raw public tables)
- [ ] Paste the **system instructions** from `planning.md` Part 1 verbatim into the agent configuration
- [ ] Add the **glossary terms** (session, engagement_rate, bounce_rate, CVR, AOV, ROAS) into the agent's data context
- [ ] Register **VQ-1 through VQ-9** as Verified Queries in the agent:
  - [ ] VQ-1 — Weekly Engagement Rate
  - [ ] VQ-2 — Bounce Rate by Landing Page
  - [ ] VQ-3 — Purchase Funnel (session-level, improved version)
  - [ ] VQ-4 — Average Order Value per Month
  - [ ] VQ-5 — Session Share by Traffic Source
  - [ ] VQ-6 — Purchase Revenue by Traffic Channel
  - [ ] VQ-7 — Cart Abandonment Rate
  - [ ] VQ-8 — Revenue by Country
  - [ ] VQ-9 — Revenue by Product Category

---

## Phase 3 — Agent Conversations & Validation

- [ ] Run **Metamorphic Test MT-1**: ask total revenue, then ask revenue by channel — confirm the sum matches
- [ ] Run **Metamorphic Test MT-2**: ask sessions that reached checkout, then sessions that purchased — confirm purchase ≤ checkout
- [ ] Run **Metamorphic Test MT-3**: ask engagement rate, then bounce rate — confirm they sum to 1
- [ ] **Catch and document at least one hallucination** from the agent (most likely: event-count vs session-count confusion in CVR). Screenshot the wrong query/output, then correct it and update the system instructions if needed
- [ ] Have the agent answer at least 3–4 strategic questions that feed into the 10 slides (e.g. top revenue countries, top product categories, worst bounce rate pages, channel revenue split)
- [ ] For each agent answer: **validate with your own SQL** — confirm the numbers match the dashboard from Assignment 1

---

## Phase 4 — Strategic Marketing Plan (Slides)

- [ ] Slide 1 — Situation & Brief: paste KPI scorecard snapshot (engagement 52%, bounce 48%, organic 28%, ROAS 3.4×)
- [ ] Slide 2 — SOSTAC® spine mapped to all 6 KPIs
- [ ] Slide 3 — Porter's Five Forces with organic search data point (28% = paid dependency risk)
- [ ] Slide 4 — McKinsey 7S internal review, gap analysis
- [ ] Slide 5 — SWOT (all 6 KPIs mapped to quadrants)
- [ ] Slide 6 — STP: country revenue (VQ-8), device breakdown, funnel behavioural segments
- [ ] Slide 7 — Ansoff Matrix: penetration (CVR/bounce), development (country gaps), product (AOV upsell via VQ-9)
- [ ] Slide 8 — RACE Framework mapped to all 6 KPIs and verified queries
- [ ] Slide 9 — Data Agent conversation screenshots: 3–4 insights, at least one correction documented
- [ ] Slide 10 — Q1–Q4 2021 roadmap + KPI targets + Data Agent as CMO tool
- [ ] Export presentation to PDF and confirm it is ≤ 10 slides

---

## Phase 5 — Data Agent Architecture Report (1-Pager)

- [ ] Section 1: paste verbatim system instructions + glossary table (6 terms)
- [ ] Section 2: list VQ-1 through VQ-9 by name with 1–2 sentence rationale each; reference SQL appendix
- [ ] Section 3: document the hallucination caught in Phase 3 — what went wrong, how you identified it (Metamorphic Testing), what corrective steps you took
- [ ] Write SQL Appendix with all 9 verified queries in full (does not count toward page limit)
- [ ] Export to PDF — confirm body is ≤ 1 page, appendix is separate

---

## Phase 6 — Final Checks

- [ ] All slide data points cross-referenced against Assignment 1 dashboard
- [ ] All 3 academic references cited in the report (Qu 2024, Yang 2025, Li 2026)
- [ ] Agent conversation screenshots are legible and show both the question and the generated SQL
- [ ] At least one hallucination documented with before/after correction
- [ ] Both PDFs named clearly and submitted together

---

*Based on `planning.md` · Last updated: April 2026*
