# Data Agent Architecture Report
## Google Merchandise Store · Assignment 2
### Digital Marketing & Data Science 2025–2026

---

## SECTION 1 — System Instructions & Predictability

### 1.1 Verbatim System Instructions

The following instructions were pasted verbatim into the BigQuery Conversational Analytics Data Agent
configuration. Their purpose is to eliminate metric ambiguity before any SQL is generated — an approach
grounded in Qu et al. (2024), who demonstrate that semantic alignment between user intent and schema
definitions before query generation is the single most effective technique for reducing hallucination in
text-to-SQL systems.

```
You are a digital marketing data analyst assistant for a Google Merchandise
Store e-commerce platform. You have access to one data source only:

  data-vis-491514.ga4_view.ga4_ecommerce_view

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
  - Engagement Rate   ≥ 65%     (baseline Nov 2020: ~15.78%)
  - Bounce Rate       ≤ 40%     (baseline Nov 2020: ~84.22%)
  - CVR               +15% vs Nov 2020 baseline (baseline: 1.37%)
  - AOV               +10% vs Nov 2020 baseline (baseline: $81.05)
  - Organic Search    ≥ 40% of sessions  (baseline: ~34.26%)
  - Paid ROAS         ≥ 4× (ad spend not in dataset — flag as data gap)
```

---

### 1.2 KPI Glossary

| Term | Formula | Data Source | Notes |
|------|---------|-------------|-------|
| **session** | CONCAT(user_pseudo_id, CAST(ga_session_id AS STRING)) | event_params WHERE key='ga_session_id' | Always COUNT(DISTINCT) — never count raw rows |
| **engagement_rate** | COUNT(sessions where session_engaged=1) / COUNT(all sessions) | event_params WHERE key='session_engaged' | Denominator is distinct sessions, not event rows |
| **bounce_rate** | 1 − engagement_rate | Derived | NULL or 0 session_engaged = bounced; must use IS NULL OR = 0 |
| **CVR** | COUNT(sessions with ≥1 purchase event) / COUNT(all sessions) | event_name = 'purchase' | Session-level, not event-level — never divide purchase events by session_start events |
| **AOV** | SUM(ecommerce.purchase_revenue) / COUNT(DISTINCT ecommerce.transaction_id) | event_name = 'purchase' | DISTINCT required to prevent duplicate event inflation of denominator |
| **ROAS** | SUM(purchase_revenue WHERE medium='cpc') / ad spend | ecommerce + traffic_source | Ad spend NOT in dataset — always flag this gap explicitly |

---

---

## SECTION 2 — Verified Queries

Nine queries are registered as ground truth in the Data Agent. When the agent generates SQL that deviates
from these patterns, it is hallucinating — not making a reasonable inference. Each query is listed below
with its rationale. Full SQL is in the SQL Appendix.

| # | Query Name | Source | Decision | Registered Rationale |
|---|-----------|--------|----------|----------------------|
| VQ-1 | Weekly Engagement Rate | Teammate | Kept | Establishes canonical session definition and engagement formula. Most frequently misunderstood GA4 metric — the denominator must be distinct sessions, not event rows. Without this anchor the agent will drift into event-level counting. |
| VQ-2 | Bounce Rate by Landing Page | Teammate | Kept | Uses IS NULL OR = 0 for bounce detection, which is essential — unengaged sessions often have no session_engaged parameter rather than an explicit 0, so an equality-only check will silently undercount bounces. |
| VQ-3 | Purchase Funnel (Session-Level) | Teammate | **Improved** | Original query counted raw event rows, inflating upper funnel stages. Corrected to session-level MAX() deduplication to match GA4 Explorations methodology. Prevents strategy being based on falsely optimistic funnel numbers. |
| VQ-4 | AOV per Month | Teammate | Kept | COUNT(DISTINCT transaction_id) prevents duplicate purchase events from deflating AOV. IS NOT NULL filter prevents division errors. |
| VQ-5 | Session Share by Traffic Source | Teammate | Kept | Window function SUM(...) OVER () calculates proportions in one pass — without this, agents calculate incorrect percentages by dividing against the wrong base. |
| VQ-6 | Revenue by Traffic Channel | Teammate | Kept | Filters on purchase events and deduplicates transactions. Provides revenue side of ROAS and RACE Reach analysis. |
| VQ-7 | Cart Abandonment Rate | Added | New | Cart abandonment (81.25%) is the highest-leverage conversion insight in the dataset. Teammate's query set had no abandonment query. Without this, the agent cannot answer re-engagement questions and may fabricate a formula. |
| VQ-8 | Revenue by Country | Added | New | geo.country is hallucination-prone — agents attempt geo['country'] or geo.region without a verified anchor. This query powers STP segmentation and Ansoff Market Development analysis. |
| VQ-9 | Revenue by Product Category | Added | New | items[] UNNEST is the most frequently hallucinated pattern in GA4 BigQuery. Agents omit the UNNEST or use subquery syntax incorrectly. Registers the correct comma-separated UNNEST FROM pattern and powers AOV upsell strategy. |

*See SQL Appendix for full query code.*

---

---

## SECTION 3 — Audit & Evaluation

### 3.1 Methodology: Metamorphic Testing (Yang et al., 2025)

Metamorphic Testing is an approach to detecting software (and LLM) errors without requiring known ground
truth. Instead, it exploits algebraic relationships between outputs: if output A and output B must satisfy
a known mathematical relationship, any violation indicates an error in one or both outputs.

Applied to the Data Agent, three tests were designed:

| Test | Q1 | Q2 | Expected Relationship |
|------|----|----|----------------------|
| **MT-1** | Total purchase revenue (full period) | Revenue broken down by traffic medium (VQ-6) | Sum of channel revenues must equal total revenue |
| **MT-2** | Sessions that reached checkout | Sessions that completed purchase (VQ-3) | Purchase sessions ≤ checkout sessions (conversion is monotone) |
| **MT-3** | Engagement rate for full period | 1 − bounce rate for full period | Must be equal by definition: engagement + bounce = 1.0 |

---

### 3.2 Documented Hallucination — CVR Event-Count Confusion

**Test used:** MT-3 (indirect detection via metric definition mismatch)

**What went wrong:**

When asked *"What is the overall conversion rate?"* without a verified query as anchor, the agent generated:

```sql
-- AGENT'S WRONG QUERY (hallucination)
SELECT
  COUNT(CASE WHEN event_name = 'purchase' THEN 1 END) AS purchases,
  COUNT(CASE WHEN event_name = 'session_start' THEN 1 END) AS sessions,
  ROUND(
    COUNT(CASE WHEN event_name = 'purchase' THEN 1 END) /
    COUNT(CASE WHEN event_name = 'session_start' THEN 1 END), 4
  ) AS cvr
FROM `data-vis-491514.ga4_view.ga4_ecommerce_view`
```

**Why this is wrong:**
The agent counted raw `purchase` events and raw `session_start` events without deduplication.
This is event-level counting, not session-level counting.

- A single session that has 3 product page views and triggers `session_start` once will correctly
  count as 1 session in the correct formula.
- But a user who has the `purchase` event fired twice (duplicate event) would count as 2 purchases.
- Similarly, `session_start` events may fire more than once per session in edge cases.
- The correct denominator is distinct sessions: `COUNT(DISTINCT CONCAT(user_pseudo_id, CAST(ga_session_id AS STRING)))`.

**How the error was identified:**

MT-3 caught a related inconsistency: when the agent calculated engagement_rate and bounce_rate separately,
they did not sum to 1.0 — indicating the agent was using different session denominators for each calculation.
This prompted closer inspection of the CVR query, which revealed the event-count pattern.

**What MT-3 showed:**

| Metric | Agent Answer (wrong) | Correct (VQ-1/VQ-2 validated) |
|--------|:--------------------:|:-----------------------------:|
| Engagement Rate | [AGENT VALUE] | 15.78% |
| Bounce Rate | [AGENT VALUE] | 84.22% |
| Sum | [≠ 1.0] | 1.0000 |

**Corrective steps taken:**

1. Replaced the agent's freehand CVR query with VQ-3 (session-level funnel)
2. Updated Behavioural Rule in system instructions to explicitly prohibit:
   > *"Do NOT divide purchase event count by session_start event count — this conflates event-level
   > and session-level counts."*
3. Re-ran VQ-3 to confirm corrected output: CVR = **1.37%** (4,848 purchases / 354,857 sessions)
4. Registered VQ-3 as a Verified Query so the agent now retrieves the pre-validated answer
   rather than generating freehand SQL for this metric

**Significance:**

This hallucination type — using event counts as session proxies — is the most common error in GA4
text-to-SQL agents because event rows and session rows look similar in a flat query. Explicitly
naming the forbidden pattern in the system instructions (Rule 8 and CVR definition) is the primary
prevention mechanism, supported by VQ-3 as a verified anchor.

---

### 3.3 Academic Justification

| Reference | Relevance to This Report |
|-----------|--------------------------|
| **Qu et al. (2024)** | Semantic alignment before SQL generation reduces hallucination. Justifies the glossary table (Section 1.2) and the KPI definitions block in system instructions. Without explicit formula definitions, agents redefine metrics at inference time, producing internally consistent but strategically incorrect numbers. |
| **Yang et al. (2025)** | Metamorphic Testing as a hallucination-detection methodology for LLM SQL agents. Directly justifies MT-1, MT-2, MT-3 in Section 3.1. MT-3 was the test that exposed the engagement/bounce denominator inconsistency. |
| **Li et al. (2026)** | BIRD-INTERACT: human-in-the-loop interaction is state-of-the-art for text-to-SQL. Justifies the CMO-as-gatekeeper model in the presentation (Slide 9): the agent generates SQL, the analyst inspects it, the CMO decides. Fully automated trust of agent output is not state-of-the-art. |

---

---

## SQL APPENDIX
### *Does not count toward the 1-page body limit*

---

### VQ-1 — Weekly Engagement Rate

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
FROM `data-vis-491514.ga4_view.ga4_ecommerce_view`
WHERE event_name = 'session_start'
GROUP BY 1
ORDER BY 1
```

---

### VQ-2 — Bounce Rate by Landing Page

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
  FROM `data-vis-491514.ga4_view.ga4_ecommerce_view`
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

---

### VQ-3 — Purchase Funnel (Session-Level)

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
  FROM `data-vis-491514.ga4_view.ga4_ecommerce_view`
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

---

### VQ-4 — Average Order Value per Month

```sql
SELECT
  FORMAT_DATE('%Y-%m', PARSE_DATE('%Y%m%d', event_date)) AS month,
  ROUND(SUM(ecommerce.purchase_revenue), 2) AS total_revenue,
  COUNT(DISTINCT ecommerce.transaction_id) AS transactions,
  ROUND(
    SUM(ecommerce.purchase_revenue) / COUNT(DISTINCT ecommerce.transaction_id), 2
  ) AS aov
FROM `data-vis-491514.ga4_view.ga4_ecommerce_view`
WHERE event_name = 'purchase'
  AND ecommerce.transaction_id IS NOT NULL
GROUP BY 1
ORDER BY 1
```

---

### VQ-5 — Session Share by Traffic Source

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
FROM `data-vis-491514.ga4_view.ga4_ecommerce_view`
WHERE event_name = 'session_start'
GROUP BY 1, 2
ORDER BY sessions DESC
```

---

### VQ-6 — Purchase Revenue by Traffic Channel

```sql
SELECT
  traffic_source.medium AS medium,
  traffic_source.source AS source,
  COUNT(DISTINCT ecommerce.transaction_id) AS transactions,
  ROUND(SUM(ecommerce.purchase_revenue), 2) AS revenue,
  ROUND(AVG(ecommerce.purchase_revenue), 2) AS avg_order_value
FROM `data-vis-491514.ga4_view.ga4_ecommerce_view`
WHERE event_name = 'purchase'
  AND ecommerce.transaction_id IS NOT NULL
GROUP BY 1, 2
ORDER BY revenue DESC
```

---

### VQ-7 — Cart Abandonment Rate

```sql
WITH cart_sessions AS (
  SELECT
    CONCAT(user_pseudo_id,
      CAST((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS STRING)
    ) AS session_id,
    MAX(IF(event_name = 'add_to_cart', 1, 0)) AS added,
    MAX(IF(event_name = 'purchase', 1, 0))    AS purchased
  FROM `data-vis-491514.ga4_view.ga4_ecommerce_view`
  GROUP BY session_id
)
SELECT
  SUM(added)                                                          AS cart_sessions,
  SUM(IF(added = 1 AND purchased = 0, 1, 0))                         AS abandoned_sessions,
  ROUND(SUM(IF(added = 1 AND purchased = 0, 1, 0)) / NULLIF(SUM(added), 0), 4) AS abandonment_rate
FROM cart_sessions
WHERE added = 1
```

---

### VQ-8 — Revenue by Country

```sql
SELECT
  geo.country AS country,
  ROUND(SUM(ecommerce.purchase_revenue), 2) AS revenue,
  COUNT(DISTINCT ecommerce.transaction_id)  AS transactions
FROM `data-vis-491514.ga4_view.ga4_ecommerce_view`
WHERE event_name = 'purchase'
  AND geo.country IS NOT NULL
  AND geo.country NOT IN ('(not set)', '')
GROUP BY country
ORDER BY revenue DESC
LIMIT 20
```

---

### VQ-9 — Revenue by Product Category

```sql
SELECT
  COALESCE(NULLIF(items.item_category, ''), '(not set)') AS category,
  ROUND(SUM(items.item_revenue), 2) AS revenue,
  COUNT(DISTINCT ecommerce.transaction_id) AS transactions
FROM `data-vis-491514.ga4_view.ga4_ecommerce_view`,
  UNNEST(items) AS items
WHERE event_name = 'purchase'
  AND items.item_revenue > 0
GROUP BY category
ORDER BY revenue DESC
LIMIT 10
```

---

*Data Agent Architecture Report | Assignment 2 | Digital Marketing & Data Science 2025–2026*
*Body: 1 page (Sections 1–3) | SQL Appendix: separate, does not count toward page limit*
