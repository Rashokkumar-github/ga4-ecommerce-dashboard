# Assignment 1 — Planning Document
**Digital Marketing and Data Science (2025-2026)**

> **Solo work** — group of 4 on paper, so the requirement is **minimum 5 visualizations**.

---

## 1. What We're Planning to Do

We're building two deliverables for a fictional CMO of an e-commerce company:

### Deliverable 1 — Measurement Framework (PDF, 1 page)
A structured blueprint that maps:
- **Business Objective(s)** → **KPIs** → **GA4 Metrics**

It justifies *why* each KPI was chosen, *how* each is calculated, and *which* visualization type is most appropriate per KPI. The PDF must include a public link to the dashboard.

### Deliverable 2 — Interactive Dashboard (Looker Studio)
A publicly shareable, interactive dashboard covering three areas:
1. **General website performance** — how engaged are visitors?
2. **Sales trends** — how is revenue and conversion evolving over time?
3. **Traffic sources** — where are visitors coming from, and which channels drive the most value?

**Data source:** `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
This is Google's obfuscated GA4 export from the Google Merchandise Store, covering **Nov 1, 2020 – Jan 31, 2021** (includes holiday shopping season).

**Toolchain:** BigQuery (SQL) → Looker Studio (visualization)

---

## 2. How We're Planning to Go About It

### Phase 0 — Setup (do this first, nothing else is possible without it)

**Step 1: Create a Google Cloud project**
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Sign in with a Google account
3. Click "Select a project" → "New Project" → give it any name (e.g. `dmds-assignment1`)
4. Enable the **BigQuery API** (it's usually on by default for new projects)
5. The free tier gives you 1 TB of query processing/month — more than enough

**Step 2: Access the sample dataset in BigQuery**
1. In BigQuery, click "+ Add Data" → "Pin a project" → type `bigquery-public-data`
2. Navigate to `ga4_obfuscated_sample_ecommerce` → you should see `events_YYYYMMDD` tables
3. Alternatively, click the **"direct link"** in your assignment PDF — it will open BigQuery with the dataset already loaded
4. Run a quick sanity-check query:
```sql
SELECT event_name, COUNT(*) as event_count
FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
GROUP BY event_name
ORDER BY event_count DESC
LIMIT 20
```

**Step 3: Set up Looker Studio**
1. Go to [lookerstudio.google.com](https://lookerstudio.google.com) — sign in with the same Google account
2. Create a blank report → Add data → choose **BigQuery** as the connector
3. You can connect either via a saved BigQuery table/view, or via a **custom SQL query** (recommended for this project — gives you full control)
4. Note: Looker Studio is free; no Google Cloud billing needed for the visualization layer itself

---

### Phase 1 — Data Exploration (BigQuery)
Before designing anything, we explore the dataset to understand what's actually in it:
- Run schema discovery queries to enumerate all `event_names` and `event_params` keys
- Validate which events exist: `page_view`, `session_start`, `purchase`, `add_to_cart`, `begin_checkout`, `view_item`, etc.
- Check coverage of key fields: `traffic_source`, `geo`, `device.category`, `ecommerce.*`
- Note: many fields require `UNNEST(event_params)` to access; sessions must be reconstructed from events

Key SQL patterns to master:
```sql
-- Accessing a nested event param (e.g. session_id)
UNNEST(event_params) AS ep WHERE ep.key = 'session_id'

-- Date filtering (efficient, avoids full table scan)
WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'

-- Revenue from purchase events
SUM(ecommerce.purchase_revenue)
```

### Phase 2 — Measurement Framework Design
Define the business objective, then derive SMART KPIs from it.

**Proposed Business Objective:**
> Maximize revenue from the e-commerce website by improving visitor engagement, increasing purchase conversion, and identifying the highest-value traffic channels.

**Proposed KPIs (minimum 3):**

| # | KPI | SMART breakdown | GA4 Metrics Used |
|---|-----|-----------------|------------------|
| 1 | **Engagement Rate** | % of sessions that are "engaged" (10s+ or 2+ pageviews or conversion) — track monthly | `engaged_sessions / total_sessions` via `session_start` + `engagement_time_msec` events |
| 2 | **Purchase Conversion Rate** | % of sessions resulting in a purchase — compare across the 3-month period | `COUNT(DISTINCT purchase sessions) / COUNT(DISTINCT all sessions)` |
| 3 | **Revenue by Traffic Channel** | Total purchase revenue attributed to each traffic source/medium — ranked monthly | `ecommerce.purchase_revenue` grouped by `traffic_source.source / medium` |
| 4 | **Average Order Value (AOV)** | Total revenue divided by number of transactions — track monthly trend | `SUM(purchase_revenue) / COUNT(DISTINCT transaction_id)` |
| 5 | **Cart Abandonment Rate** | % of users who add to cart but don't purchase | `(add_to_cart events - purchase events) / add_to_cart events` |

*Since this is a group-of-4 submission done solo, all 5 KPIs above are in scope — one visualization per KPI, minimum.*

### Phase 3 — Dashboard Design & Build (Looker Studio)
Connect Looker Studio to BigQuery via a custom SQL query (or native connector). Design follows a clear **visual hierarchy**:

**Suggested layout:**

```
┌──────────────────────────────────────────────────────┐
│  FILTERS: Date Range | Traffic Source | Device Type  │
├────────────────┬─────────────────┬───────────────────┤
│  KPI Scorecard │  KPI Scorecard  │   KPI Scorecard   │
│  (Engagement)  │  (Conv. Rate)   │   (Revenue)       │
├────────────────┴─────────────────┴───────────────────┤
│  Revenue & Sessions over Time (line chart, dual axis)│
├──────────────────────┬───────────────────────────────┤
│  Traffic Source      │  Top Products / Categories    │
│  Breakdown           │  by Revenue (bar chart)       │
│  (pie / bar chart)   │                               │
└──────────────────────┴───────────────────────────────┘
```

**Visualization selection rationale (chart chooser principles):**
- Time trends → **Line chart**
- Part-to-whole (channels) → **Pie or stacked bar**
- Rankings (products, pages) → **Horizontal bar chart**
- Single-number KPIs → **Scorecard/KPI card**
- Geographic breakdown → **Geo map** (bonus, if time allows)

Each visualization gets a 2–3 sentence plain-English description targeted at the CMO.

### Phase 4 — Measurement Framework PDF
Design a clean 1-page PDF (Canva, Figma, or Google Slides → export) showing:
- Business objective at the top
- KPIs in the middle layer with SMART justification
- Metrics at the bottom layer showing how they feed each KPI
- Paste the public Looker Studio link

### Phase 5 — Review & Submit
- Verify the Looker Studio dashboard is publicly accessible (no login required)
- Test all interactive filters work
- Proofread CMO-facing descriptions for jargon
- Export final PDF with dashboard link embedded

---

## 3. Things to Keep in Mind

### Data limitations
- The dataset is **obfuscated** — some values are `<Other>` or `NULL`. This is expected and should be noted if it affects a KPI.
- Date range is fixed: **Nov 2020 – Jan 2021** only. All "trends" are within this 3-month window — avoid language implying longer historical context.
- Sessions are **not pre-built** in GA4 BigQuery exports. We reconstruct sessions using `session_id` from `event_params`, grouped by `user_pseudo_id`. This requires careful SQL.
- `user_pseudo_id` is the only reliable user identifier (not `user_id`, which is often NULL in this dataset).

### BigQuery cost management
- Always filter by `_TABLE_SUFFIX` (date range) to avoid scanning all tables unnecessarily.
- Preview queries in BigQuery before running to check estimated data processed.
- The 1 TB free tier should be more than sufficient for this dataset, but wildcard queries without date filters can be expensive.

### Visualization principles
- Dashboard is for **marketing decision-makers**, not data engineers. Avoid SQL jargon in descriptions.
- Use consistent color coding (e.g., one color per traffic channel, consistent across charts).
- Interactivity is required — at minimum: date range filter + one categorical filter (e.g., traffic source or device type).
- Visual hierarchy matters: most important KPIs at the top, supporting detail below.

### Measurement framework quality
- KPIs must be **SMART**: Specific, Measurable, Achievable, Relevant, Time-bound. Generic KPIs like "improve engagement" will lose marks — specify a target and timeframe.
- The framework should justify *why* each KPI matters to a CMO, not just what it is.
- 1 page maximum — keep it visually clean, not text-heavy.

### Working solo
- You're covering all three skill areas yourself: SQL/data, visualization design, and business framing.
- Work sequentially: get the SQL right first, then design the dashboard, then write the measurement framework. Trying to do all three simultaneously is the main risk.
- The measurement framework is easier to write *after* the dashboard exists — you can justify choices you've already made rather than speculating.

---

## 4. Remaining Questions

1. **What's the submission deadline?** This determines how aggressively to scope each phase.

2. **Does your professor have strong opinions on visualization types or specific KPIs?** Some courses expect you to demonstrate particular chart types (e.g., funnel charts) or analytical methods.

3. **Should the measurement framework PDF be diagram-heavy or table-heavy?** A Canva-style hierarchy diagram looks clean but takes longer to design — a well-formatted table in Google Slides is faster and can still look sharp.

4. **Any preference on the business objective framing?** The proposed one (maximize revenue via engagement + conversion + channel optimization) covers all three required focus areas. Happy to reframe around a different angle if you have one in mind.

5. **Is there a grading rubric beyond the PDF?** If the professor shared additional marking criteria (SQL complexity, visual design quality, number of filters, etc.), those would change priorities.

6. **Have you looked at the "example GA4 dashboard in Looker Studio" link in the assignment PDF?** It's worth checking before we finalize the layout — it may give implicit hints about what the professor expects to see.
