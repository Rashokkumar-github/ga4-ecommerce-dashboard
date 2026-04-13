# Assignment 2 — Planning Document
## Strategic Marketing Plan & Data Agent
**Digital Marketing & Data Science 2025–2026**

---

## Overview

Two deliverables:

1. **Strategic Marketing Plan** — PDF presentation, max 10 slides, visuals-first
2. **Data Agent Architecture Report** — 1-page PDF + SQL appendix

Data source for the agent: `project-7c815de1-c0a4-4f10-a46.DMDS_GA4_samle.events`
Period: November 2020 – January 2021

---
## Part 1 — Data Agent Design

### System Instructions (verbatim, for BigQuery Conversational Analytics Agent)

```
You are a digital marketing data analyst assistant for a Google Merchandise
Store e-commerce platform. You have access to one data source only:

  project-7c815de1-c0a4-4f10-a46.DMDS_GA4_samle.events

This table contains Google Analytics 4 event-level data from November 2020
to January 2021.

────────────────────────────────────────────────────────────────
SCHEMA RULES — NON-NEGOTIABLE
────────────────────────────────────────────────────────────────
1. Never invent or assume column names. The only top-level fields
   you may reference are those in the official GA4 BigQuery export
   schema: event_date, event_timestamp, event_name, event_params[],
   user_pseudo_id, user_properties[], device{}, geo{}, app_info{},
   traffic_source{}, ecommerce{}, items[].

2. event_params and items are REPEATED RECORD fields. Always access
   them using UNNEST() or a subquery:
     (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
   Never reference event_params.key or items.item_name directly.

3. ecommerce fields (purchase_revenue, transaction_id, etc.) are
   nested structs, not arrays. Access them as ecommerce.purchase_revenue,
   ecommerce.transaction_id — no UNNEST required.

4. traffic_source is a struct. Use traffic_source.medium and
   traffic_source.source. Never use "channel" as a field name — it
   does not exist in the schema.

────────────────────────────────────────────────────────────────
KPI DEFINITIONS — USE THESE EXACTLY, NEVER REDEFINE
────────────────────────────────────────────────────────────────
A "session" is defined as a unique combination of:
  user_pseudo_id + ga_session_id (from event_params WHERE key = 'ga_session_id')

engagement_rate
  = COUNT(sessions where session_engaged = 1) / COUNT(all sessions)
  Numerator: sessions where the event_param key='session_engaged' int_value = 1
  Never use raw event counts as the denominator.

bounce_rate
  = 1 − engagement_rate
  = COUNT(sessions where session_engaged IS NULL OR = 0) / COUNT(all sessions)

conversion_rate (CVR)
  = COUNT(sessions that contain at least one 'purchase' event)
    / COUNT(all sessions)
  Do NOT divide purchase event count by session_start event count —
  this conflates event-level and session-level counts.

average_order_value (AOV)
  = SUM(ecommerce.purchase_revenue)
    / COUNT(DISTINCT ecommerce.transaction_id)
  Always filter WHERE event_name = 'purchase'
  Always filter WHERE ecommerce.transaction_id IS NOT NULL

ROAS (Paid Channel)
  = SUM(ecommerce.purchase_revenue WHERE traffic_source.medium = 'cpc')
    / estimated ad spend
  Note: estimated ad spend is not in the dataset. Flag this explicitly
  when asked for ROAS; do not fabricate a denominator.

organic_search_share
  = sessions WHERE traffic_source.medium = 'organic' / total sessions

────────────────────────────────────────────────────────────────
BEHAVIOURAL RULES
────────────────────────────────────────────────────────────────
5. If a question is ambiguous (e.g. "revenue" could mean item-level
   items.item_revenue or transaction-level ecommerce.purchase_revenue),
   ask for clarification before generating SQL. Default to
   ecommerce.purchase_revenue for transaction revenue questions.

6. Always filter by event_name when the question is about a specific
   user action (e.g. WHERE event_name = 'purchase', 'add_to_cart',
   'session_start', etc.).

7. Never aggregate without a GROUP BY. Never use SELECT * in a
   final answer — always name the columns explicitly.

8. When counting sessions, always use COUNT(DISTINCT) with the
   composite key: CONCAT(user_pseudo_id, CAST(ga_session_id AS STRING)).
   Never count raw rows as sessions.

9. When the user asks about "top" results, always include an ORDER BY
   and a LIMIT clause. Default LIMIT is 10 unless specified otherwise.

10. If you are unsure whether a column, field, or metric exists in the
    schema, say so explicitly and ask the user rather than guessing.
    Hallucinating a column name will produce a query error and wastes
    the user's time.

────────────────────────────────────────────────────────────────
KPI TARGETS (from Measurement Framework — Assignment 1)
────────────────────────────────────────────────────────────────
Always compare results against these targets when reporting on performance:
  - Engagement Rate   ≥ 65%     (baseline Nov 2020: ~52%)
  - Bounce Rate       ≤ 40%     (baseline Nov 2020: ~48%)
  - CVR               +15% vs Nov 2020 baseline
  - AOV               +10% vs Nov 2020 baseline
  - Organic Search    ≥ 40% of sessions  (baseline: ~28%)
  - Paid ROAS         ≥ 4×               (Q1 2021 actual: 3.4×)
```

---

### Verified Queries

These are the queries registered in the agent as ground truth. Each one defines exactly how a core business metric must be calculated. If the agent deviates from these patterns, it is hallucinating.

---

#### VQ-1 — Weekly Engagement Rate
*Source: teammate query, kept as-is.*

```sql
SELECT
  DATE_TRUNC(PARSE_DATE('%Y%m%d', event_date), WEEK) AS week,
  COUNTIF(
    (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'session_engaged') = 1
  ) AS engaged_sessions,
  COUNT(DISTINCT CONCAT(user_pseudo_id,
    CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
  )) AS total_sessions,
  ROUND(
    COUNTIF((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'session_engaged') = 1)
    / COUNT(DISTINCT CONCAT(user_pseudo_id,
        CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
    )), 4
  ) AS engagement_rate
FROM `project-7c815de1-c0a4-4f10-a46.DMDS_GA4_samle.events`
WHERE event_name = 'session_start'
GROUP BY 1
ORDER BY 1
```

**Why this query:** It establishes the canonical session definition (user_pseudo_id + ga_session_id) and the exact engagement_rate formula (engaged sessions / total sessions) so the agent cannot drift into counting raw events instead of deduplicated sessions. This is the most frequently misunderstood metric in GA4. Without this anchor, the agent will almost certainly hallucinate the denominator.

---

#### VQ-2 — Bounce Rate by Landing Page
*Source: teammate query, kept as-is.*

```sql
WITH sessions AS (
  SELECT
    (SELECT value.string_value FROM UNNEST(event_params)
      WHERE key = 'page_location') AS landing_page,
    CONCAT(user_pseudo_id,
      CAST((SELECT value.int_value FROM UNNEST(event_params)
        WHERE key = 'ga_session_id') AS STRING)
    ) AS session_id,
    MAX(
      (SELECT value.int_value FROM UNNEST(event_params)
        WHERE key = 'session_engaged')
    ) AS is_engaged
  FROM `project-7c815de1-c0a4-4f10-a46.DMDS_GA4_samle.events`
  WHERE event_name = 'session_start'
  GROUP BY 1, 2
)
SELECT
  landing_page,
  COUNT(session_id) AS total_sessions,
  COUNTIF(is_engaged IS NULL OR is_engaged = 0) AS bounced_sessions,
  ROUND(
    COUNTIF(is_engaged IS NULL OR is_engaged = 0) / COUNT(session_id), 4
  ) AS bounce_rate
FROM sessions
GROUP BY 1
ORDER BY total_sessions DESC
LIMIT 20
```

**Why this query:** Bounce rate is KPI 2 and one of the most strategically important levers in the plan (landing page UX improvements are the primary tactic). The `IS NULL OR = 0` pattern is essential — without it the agent will undercount bounces because unengaged sessions often have no `session_engaged` parameter at all rather than an explicit 0.

---

#### VQ-3 — Purchase Funnel (Session-Level)
*Source: teammate query improved to session-level deduplication.*

The teammate's original query counts raw event rows, which inflates each funnel stage (a user who views 5 products in one session counts as 5 view_item events). The correct approach deduplicates at session level, matching how GA4 reports funnel data.

```sql
WITH session_funnel AS (
  SELECT
    CONCAT(user_pseudo_id,
      CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
    ) AS session_id,
    MAX(IF(event_name = 'session_start', 1, 0))    AS had_session,
    MAX(IF(event_name = 'view_item', 1, 0))         AS viewed_item,
    MAX(IF(event_name = 'add_to_cart', 1, 0))       AS added_to_cart,
    MAX(IF(event_name = 'begin_checkout', 1, 0))    AS began_checkout,
    MAX(IF(event_name = 'purchase', 1, 0))          AS purchased
  FROM `project-7c815de1-c0a4-4f10-a46.DMDS_GA4_samle.events`
  GROUP BY session_id
)
SELECT
  SUM(had_session)    AS sessions,
  SUM(viewed_item)    AS product_views,
  SUM(added_to_cart)  AS add_to_cart,
  SUM(began_checkout) AS begin_checkout,
  SUM(purchased)      AS purchases,
  ROUND(SUM(purchased) / NULLIF(SUM(had_session), 0), 4) AS cvr
FROM session_funnel
```

**Why this query (and why we improved it):** The funnel is the core evidence for the CVR strategy (+15% target). Event-level counting artificially inflates the top of the funnel, making drop-off rates look better than they are and misleading strategy. Session-level MAX() deduplication is what GA4 Explorations actually use, so this aligns agent output with what the CMO sees in the GA4 interface. We chose this over the teammate's version specifically to prevent the agent from reporting a flattering but incorrect picture.

---

#### VQ-4 — Average Order Value per Month
*Source: teammate query, kept as-is — well structured.*

```sql
SELECT
  FORMAT_DATE('%Y-%m', PARSE_DATE('%Y%m%d', event_date)) AS month,
  ROUND(SUM(ecommerce.purchase_revenue), 2) AS total_revenue,
  COUNT(DISTINCT ecommerce.transaction_id) AS transactions,
  ROUND(
    SUM(ecommerce.purchase_revenue) / COUNT(DISTINCT ecommerce.transaction_id), 2
  ) AS aov
FROM `project-7c815de1-c0a4-4f10-a46.DMDS_GA4_samle.events`
WHERE event_name = 'purchase'
  AND ecommerce.transaction_id IS NOT NULL
GROUP BY 1
ORDER BY 1
```

**Why this query:** AOV is KPI 4 and the primary lever for the Ansoff product development strategy (upsell/cross-sell). Using `COUNT(DISTINCT ecommerce.transaction_id)` is critical — without DISTINCT, any duplicate purchase events in GA4 will deflate AOV by inflating the denominator. The `IS NOT NULL` filter prevents division errors on malformed events.

---

#### VQ-5 — Session Share by Traffic Source
*Source: teammate query, kept as-is.*

```sql
SELECT
  traffic_source.medium AS medium,
  traffic_source.source AS source,
  COUNT(DISTINCT CONCAT(user_pseudo_id,
    CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
  )) AS sessions,
  ROUND(
    COUNT(DISTINCT CONCAT(user_pseudo_id,
      CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
    )) / SUM(COUNT(DISTINCT CONCAT(user_pseudo_id,
      CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
    ))) OVER (), 4
  ) AS session_share
FROM `project-7c815de1-c0a4-4f10-a46.DMDS_GA4_samle.events`
WHERE event_name = 'session_start'
GROUP BY 1, 2
ORDER BY sessions DESC
```

**Why this query:** This is the evidence base for KPI 5 (Organic Search ≥ 40%) and the SWOT weakness finding (organic only ~28% of sessions). The window function `SUM(...) OVER ()` gives proportions in a single pass — without this anchor the agent tends to calculate incorrect percentages by dividing against the wrong base.

---

#### VQ-6 — Purchase Revenue by Traffic Channel
*Source: teammate query, kept as-is.*

```sql
SELECT
  traffic_source.medium AS medium,
  traffic_source.source AS source,
  COUNT(DISTINCT ecommerce.transaction_id) AS transactions,
  ROUND(SUM(ecommerce.purchase_revenue), 2) AS revenue,
  ROUND(AVG(ecommerce.purchase_revenue), 2) AS avg_order_value
FROM `project-7c815de1-c0a4-4f10-a46.DMDS_GA4_samle.events`
WHERE event_name = 'purchase'
  AND ecommerce.transaction_id IS NOT NULL
GROUP BY 1, 2
ORDER BY revenue DESC
```

**Why this query:** This is the revenue side of KPI 6 (Paid ROAS ≥ 4×) and the RACE Reach analysis. Knowing which channels generate revenue (not just traffic) changes strategy entirely — a channel with 30% of sessions but 5% of revenue is a trap. We kept this because it correctly filters on `purchase` events and deduplicates transactions.

---

#### VQ-7 — Cart Abandonment Rate *(added — not in teammate's set)*

```sql
WITH cart_sessions AS (
  SELECT
    CONCAT(user_pseudo_id,
      CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
    ) AS session_id,
    MAX(IF(event_name = 'add_to_cart', 1, 0)) AS added,
    MAX(IF(event_name = 'purchase', 1, 0))    AS purchased
  FROM `project-7c815de1-c0a4-4f10-a46.DMDS_GA4_samle.events`
  GROUP BY session_id
)
SELECT
  SUM(added)                                                          AS cart_sessions,
  SUM(IF(added = 1 AND purchased = 0, 1, 0))                         AS abandoned_sessions,
  ROUND(SUM(IF(added = 1 AND purchased = 0, 1, 0)) / NULLIF(SUM(added), 0), 4) AS abandonment_rate
FROM cart_sessions
WHERE added = 1
```

**Why this query:** Cart abandonment is the single highest-leverage conversion optimisation insight in the dataset and sits at the core of the RACE Convert strategy. The teammate's query set had no way to quantify the re-engagement opportunity. Without this query as a verified anchor, the agent will either refuse to answer abandonment questions or fabricate a formula — we need this defined explicitly.

---

#### VQ-8 — Revenue by Country *(added — not in teammate's set)*

```sql
SELECT
  geo.country AS country,
  ROUND(SUM(ecommerce.purchase_revenue), 2) AS revenue,
  COUNT(DISTINCT ecommerce.transaction_id)  AS transactions
FROM `project-7c815de1-c0a4-4f10-a46.DMDS_GA4_samle.events`
WHERE event_name = 'purchase'
  AND geo.country IS NOT NULL
  AND geo.country NOT IN ('(not set)', '')
GROUP BY country
ORDER BY revenue DESC
LIMIT 20
```

**Why this query:** Geographic revenue distribution is the evidence base for the STP segmentation slide and the Ansoff Market Development quadrant (which countries to expand into). `geo.country` is a deeply nested field — without this as a verified query, the agent frequently attempts `geo['country']` or `geo.region` and generates broken SQL.

---

#### VQ-9 — Revenue by Product Category *(added — not in teammate's set)*

```sql
SELECT
  COALESCE(NULLIF(items.item_category, ''), '(not set)') AS category,
  ROUND(SUM(items.item_revenue), 2) AS revenue,
  COUNT(DISTINCT ecommerce.transaction_id) AS transactions
FROM `project-7c815de1-c0a4-4f10-a46.DMDS_GA4_samle.events`,
  UNNEST(items) AS items
WHERE event_name = 'purchase'
  AND items.item_revenue > 0
GROUP BY category
ORDER BY revenue DESC
LIMIT 10
```

**Why this query:** The `items` array is the most hallucination-prone field in GA4 BigQuery schema — agents almost always get the UNNEST syntax wrong. Registering this as a verified query teaches the agent the correct pattern (comma-separated UNNEST in the FROM clause, not a subquery). It also powers the product category strategy in the AOV upsell recommendation.

---

### Query Decisions Summary

| # | Source | Decision | Reason |
|---|--------|----------|--------|
| VQ-1 | Teammate | **Kept as-is** | Correct session-level engagement logic |
| VQ-2 | Teammate | **Kept as-is** | Handles NULL bounce correctly |
| VQ-3 | Teammate | **Improved** | Switched to session-level deduplication — original inflated funnel |
| VQ-4 | Teammate | **Kept as-is** | Correct DISTINCT transaction deduplication |
| VQ-5 | Teammate | **Kept as-is** | Window function share calculation is correct |
| VQ-6 | Teammate | **Kept as-is** | Correct revenue attribution pattern |
| VQ-7 | Added | **New** | Cart abandonment = critical gap in teammate set |
| VQ-8 | Added | **New** | Geography needed for STP + Ansoff; geo.country is hallucination-prone |
| VQ-9 | Added | **New** | items[] UNNEST pattern is most frequently hallucinated; needed for AOV strategy |

---

### Audit & Evaluation Plan

**Methodology: Metamorphic Testing (Yang et al., 2025)**

Ask two mathematically related questions. The answers must satisfy a known relationship. Discrepancy = hallucination.

| Test | Q1 | Q2 | Expected Relationship |
|------|----|----|----------------------|
| MT-1 | Total purchase revenue (full period) | Revenue broken down by traffic medium | Sum of Q2 must equal Q1 |
| MT-2 | Total sessions that reached checkout | Total sessions that purchased | Q2 must be ≤ Q1 |
| MT-3 | Engagement rate for full period | 1 − bounce rate for full period | Must be equal (by definition) |

**Most likely hallucination to catch and document:**
The agent will almost certainly count `session_start` events as sessions without the `DISTINCT user_pseudo_id + ga_session_id` deduplication. This inflates session count and deflates engagement rate and CVR. Catch it by comparing VQ-3's CVR output against the agent's freehand answer. Document the discrepancy, show the corrected query, and explain how the system instructions were updated.

---

## Part 2 — Strategic Marketing Plan (10 Slides)

### Slide Structure

**Slide 1 — Situation & Brief**
- Business objective from Measurement Framework: grow revenue 20%, reduce CAC
- KPI scorecard snapshot: engagement 52%, bounce 48%, CVR (baseline), AOV (baseline), organic 28%, ROAS 3.4×
- Framing: what the data tells us before strategy begins

**Slide 2 — SOSTAC® Spine**
- Situation → Objectives → Strategy → Tactics → Action → Control
- Map each SOSTAC stage to a KPI and a later slide
- This slide is the structural backbone — reference it in every subsequent slide

**Slide 3 — Market Analysis: Porter's Five Forces**
- Supplier power: Google ecosystem dependency (low leverage)
- Buyer power: High — price-sensitive merch shoppers, many alternatives
- Threat of substitutes: Amazon, direct brand stores, resellers
- Competitive rivalry: SEO/SEM arms race in branded merch
- New entrants: Low barrier
- **Data tie-in:** Organic search only 28% = over-reliance on paid = margin exposed to rivalry

**Slide 4 — Internal Review: McKinsey 7S**
- Strategy: data-driven revenue growth
- Structure: CMO + data science team
- Systems: GA4 → BigQuery → Dashboard → Data Agent
- Style: analytics-first decision-making
- Staff: data science + marketing split
- Skills: SQL, BigQuery, GA4, Looker
- Shared Values: evidence over intuition
- **Gap identified:** organic search skills, conversion optimisation depth

**Slide 5 — SWOT Analysis (Digital Channel)**
- Strengths: active paid channel (ROAS 3.4×), existing engaged audience segment
- Weaknesses: bounce rate 48% (above 40% target), organic 28% (below 40% target)
- Opportunities: 12pp SEO gap to close, AOV uplift via upsell programme (planned Q2–Q3)
- Threats: rising CPCs if ROAS falls below 4×, mobile conversion gap (device breakdown)

**Slide 6 — STP: Segmentation, Targeting, Positioning**
- Segmentation: Geographic (top-revenue countries from VQ-8), Device (desktop vs mobile from dashboard), Behavioural (funnel stage: browsers / cart-adders / abandoners)
- Targeting: High-intent desktop users in US and top 5 revenue markets
- Positioning: Data-validated premium brand; justify AOV premium via UX trust signals

**Slide 7 — Ansoff Matrix: Where to Grow**
- Market Penetration (primary): CVR +15% and bounce ≤40% in existing markets via funnel and landing page optimisation
- Market Development: Expand to top underperforming countries from VQ-8 (high sessions, low revenue)
- Product Development: AOV +10% via cross-sell / upsell (existing users, new product bundles from VQ-9 top categories)
- Diversification: Not recommended — focus resources on penetration first

**Slide 8 — RACE Framework: How to Execute**
- Reach: SEO roadmap (organic 28% → 40%); paid maintained at ROAS ≥4×
- Act: Landing page UX audit targeting worst bounce rate pages from VQ-2; content relevance improvements
- Convert: Funnel optimisation at the three highest drop-off steps (from VQ-3); cart abandonment recovery email flow (from VQ-7)
- Engage: Upsell/cross-sell email campaigns targeting top categories (VQ-9); retargeting for abandoners

**Slide 9 — Data Agent: Insights & Validation**
- Show 3–4 agent conversation screenshots
- For each: Agent query → Agent answer → Your SQL validation → Confirmed or Challenged
- Must include at least one instance where agent was wrong (hallucinated metric or column)
- Show your correction and updated query

**Slide 10 — Roadmap & Control**
- Q1–Q4 2021 action plan mapped to 6 KPIs
- Measurement Framework as the ongoing control mechanism
- Data Agent as the CMO's self-service analytics interface
- Final visual: KPI dashboard with target vs. projected trajectory

---

### Framework Coverage Map

| Framework | Slide | Primary Data Evidence |
|-----------|-------|-----------------------|
| SOSTAC® | 2 | KPI structure from Measurement Framework |
| Porter's Five Forces | 3 | Organic 28% = paid dependency risk |
| McKinsey 7S | 4 | Systems gap: organic + CRO skills |
| Digital Channel SWOT | 5 | All 6 KPIs mapped to quadrants |
| STP | 6 | VQ-8 country revenue, device breakdown |
| Ansoff's Matrix | 7 | CVR + bounce (penetration); VQ-8 (development) |
| RACE Framework | 8 | VQ-2, VQ-3, VQ-7, VQ-9 |
| Business Model Canvas | 1 or 2 | Value proposition, channels, revenue streams |

---

## Part 3 — Data Agent Architecture Report (1-Pager)

Structure for the 1-page document:

```
┌─────────────────────────────────────────────────────────────────────┐
│ SECTION 1: System Instructions & Predictability                     │
│  • Verbatim system instructions (paste from above)                  │
│  • Glossary table: 6 terms (session, engagement_rate, bounce_rate,  │
│    CVR, AOV, ROAS) with exact formulas                             │
│                                                                      │
│ SECTION 2: Verified Queries (reference SQL appendix)                │
│  • VQ-1 through VQ-9 listed by name                                │
│  • 1–2 sentence rationale per query (from above)                    │
│  • "See SQL Appendix, pages X–Y"                                    │
│                                                                      │
│ SECTION 3: Audit & Evaluation                                       │
│  • Metamorphic Test that caught the hallucination                   │
│  • Screenshot of agent's wrong query / wrong number                 │
│  • Explanation of error (event-count vs session-count confusion)    │
│  • Corrective steps: updated system instructions + re-registered VQ │
└─────────────────────────────────────────────────────────────────────┘
```

SQL Appendix: paste VQ-1 through VQ-9 in full. Does not count toward page limit.

---

## Academic References to Cite

| Reference | Where to Cite |
|-----------|---------------|
| Qu et al. (2024) — semantic alignment before SQL generation | Section 1 of architecture report; justifies glossary terms + system instructions |
| Yang et al. (2025) — Metamorphic Testing for hallucination detection | Section 3 of architecture report; justifies MT-1, MT-2, MT-3 audit tests |
| Li et al. (2026) — BIRD-INTERACT, human-in-the-loop is state of the art | Slide 9 of presentation; justifies your role as gatekeeper, not passive user |

---

## Technical Setup Checklist (Pre-Work)

- [ ] Create BigQuery VIEW in `data-vis-491514` project:
  ```sql
  CREATE OR REPLACE VIEW `data-vis-491514.ga4_view.ga4_ecommerce_view` AS
  SELECT * FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
  ```
- [ ] Enable Conversational Analytics API in Google Cloud Console
- [ ] Create Data Agent in BigQuery Studio pointing at the view
- [ ] Paste system instructions (verbatim from Part 1) into agent configuration
- [ ] Register VQ-1 through VQ-9 as Verified Queries in the agent
- [ ] Add glossary terms to agent data context
- [ ] Run Metamorphic Tests MT-1, MT-2, MT-3 and document at least one failure
- [ ] Screenshot agent conversation showing a caught hallucination

---

*Generated: April 2026 | Assignment 2 | Digital Marketing & Data Science 2025–2026*
