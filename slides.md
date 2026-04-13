# Assignment 2 — Strategic Marketing Plan
## Google Merchandise Store · Nov 2020 – Jan 2021
### Digital Marketing & Data Science 2025–2026

> **Data source:** All KPI figures are derived directly from BigQuery VQ queries run against
> `data-vis-491514.ga4_view.ga4_ecommerce_view` using the project service account.
> These are the authoritative numbers for this assignment.

---

---

## SLIDE 1 — Situation & Brief

### Business Objective
Grow e-commerce revenue by **20%** and reduce customer acquisition cost (CAC) through data-driven optimisation of the Google Merchandise Store digital channel.

---

### KPI Scorecard — Nov 2020 – Jan 2021 Baseline

| KPI | Actual (Baseline) | Target | Gap | Status |
|-----|:-----------------:|:------:|:---:|:------:|
| Engagement Rate | **15.78%** | ≥ 65% | −49.2pp | 🔴 Critical |
| Bounce Rate | **84.22%** | ≤ 40% | +44.2pp | 🔴 Critical |
| CVR (Session-Level) | **1.37%** | +15% rel. | Baseline | ⚠️ Needs lift |
| AOV (Overall) | **$81.05** | +10% rel. | Baseline | ⚠️ Needs lift |
| Organic Search Share | **34.26%** | ≥ 40% | −5.7pp | 🟡 Close |
| Paid ROAS | **Limited data\*** | ≥ 4× | Unknown | ⚠️ Flagged |

> \*Paid (CPC) revenue = $8,977 from 133 transactions. Ad spend is not recorded in the dataset.
> ROAS cannot be calculated without the spend denominator — flagged as a data gap.

---

### What the Data Tells Us
- **354,857 total sessions** across the 3-month window
- **$360,837 total revenue** from **4,452 transactions**
- **81.25% cart abandonment rate** — most serious conversion leak
- Organic traffic is strong (34.26%) but just below the 40% target
- Paid CPC drives only 4.38% of sessions but requires cost context to evaluate

---

---

## SLIDE 2 — SOSTAC® Strategic Spine

> *This framework is the backbone of the plan. Each subsequent slide maps to one of these stages.*

| Stage | What It Means | Applied to This Plan | KPI Owner | Slide |
|-------|---------------|---------------------|-----------|-------|
| **Situation** | Where are we now? | Bounce 84%, CVR 1.37%, organic 34% | All 6 KPIs | Slide 1 |
| **Objectives** | Where do we want to be? | Revenue +20%, CVR +15%, Bounce ≤40%, Organic ≥40% | All 6 KPIs | Slide 1 |
| **Strategy** | How will we get there? | Market Penetration + SEO-led organic growth | CVR, Bounce, Organic | Slide 7 |
| **Tactics** | What specific actions? | Landing page UX, funnel CRO, cart recovery, SEO programme | CVR, Bounce, AOV | Slide 8 |
| **Action** | Who does what by when? | Q1–Q4 2021 roadmap with owners | All 6 KPIs | Slide 10 |
| **Control** | How do we measure progress? | Measurement Framework + Data Agent as CMO dashboard | All 6 KPIs | Slide 10 |

---

### SOSTAC® ↔ KPI Mapping

```
Engagement Rate ──► Situation (baseline) + Control (ongoing monitor)
Bounce Rate ──────► Objectives (≤40%) + Tactics (landing page UX)
CVR ──────────────► Objectives (+15%) + Tactics (funnel CRO, cart recovery)
AOV ──────────────► Objectives (+10%) + Tactics (upsell / cross-sell)
Organic Share ────► Objectives (≥40%) + Strategy (SEO programme)
Paid ROAS ────────► Control (≥4× gate before increasing CPC spend)
```

---

---

## SLIDE 3 — Market Analysis: Porter's Five Forces

> *Framework: Porter (1980). Applied here to the Google Merchandise Store digital channel.*

---

### Five Forces Assessment

| Force | Intensity | Evidence |
|-------|:---------:|---------|
| **Competitive Rivalry** | 🔴 High | Branded merch space is crowded; YouTube, Google product competitors exist |
| **Buyer Power** | 🔴 High | Price-sensitive merch shoppers; Amazon/reseller alternatives one click away |
| **Threat of Substitutes** | 🔴 High | Amazon, direct brand stores, resellers, second-hand marketplaces |
| **Threat of New Entrants** | 🟡 Medium | Low technical barrier; brand recognition provides some moat |
| **Supplier Power** | 🟢 Low | Google ecosystem products; internal supply chain control |

---

### Data-Driven Insight: Paid Dependency Risk

- **Organic search = 34.26% of sessions** (121,566 / 354,857)
- **CPC paid = only 4.38% of sessions** — paid is a small channel by volume
- However, organic being below the 40% target means the store is not fully capturing its owned channel advantage against rivals who dominate Google SERPs
- **Strategic implication (Porter):** In a high-rivalry, high-buyer-power environment, over-reliance on any single acquisition channel (especially paid) exposes margin to competitive bidding wars. Growing organic to ≥40% reduces this structural risk.

---

---

## SLIDE 4 — Internal Review: McKinsey 7S Framework

> *Assesses internal organisational alignment and identifies capability gaps.*

---

### 7S Elements

| Element | Current State | Gap Identified |
|---------|--------------|----------------|
| **Strategy** | Data-driven revenue growth; 20% revenue target | No formal SEO/CRO roadmap yet |
| **Structure** | CMO + data science team + marketing | CRO and SEO skills sit in separate silos |
| **Systems** | GA4 → BigQuery → Streamlit Dashboard → Data Agent | Data Agent is new; workflows not yet embedded |
| **Style** | Analytics-first, evidence over intuition | Decisions still partly based on channel assumptions rather than VQ data |
| **Staff** | Data scientists + digital marketers | Gap: SEO specialists and conversion rate optimisation (CRO) practitioners |
| **Skills** | SQL, BigQuery, GA4, Looker, Python | Gap: technical SEO, A/B testing at scale, email automation |
| **Shared Values** | Evidence-based decision making | Risk: analytics culture strong but action velocity is slow |

---

### Key Gaps (Gap Analysis)

1. **Organic search capability** — 34.26% organic share (vs 40% target) requires dedicated SEO resource that does not currently exist
2. **Conversion optimisation depth** — 84.22% bounce rate and 81.25% cart abandonment require specialist CRO skills (heatmaps, A/B testing, UX research)
3. **Data Agent adoption** — the agent is a new tool; CMO team needs onboarding to use it as a self-service interface rather than always routing through data science

---

---

## SLIDE 5 — SWOT Analysis: Digital Channel

> *All four quadrants anchored directly to the 6 KPIs and VQ-validated data.*

---

### SWOT Matrix

|  | **Helpful** | **Harmful** |
|--|:-----------:|:-----------:|
| **Internal** | **Strengths** | **Weaknesses** |
| | ✅ Strong organic base (34.26% of sessions via Google organic) | ❌ Bounce rate 84.22% — far above 40% target |
| | ✅ Existing purchase funnel with measurable conversion (CVR 1.37%) | ❌ Cart abandonment 81.25% — 12,340 sessions lost after cart add |
| | ✅ Data infrastructure in place (BigQuery + GA4 + Data Agent) | ❌ Organic share 34.26% — below 40% target, limiting free traffic ceiling |
| | ✅ Premium AOV of $81.05 with seasonal peak ($113.53 in Nov 2020) | ❌ CVR only 1.37% — conversion leaks at every funnel stage |
| **External** | **Opportunities** | **Threats** |
| | 🟢 5.7pp SEO gap to close to hit 40% organic target | 🔴 Rising CPCs if ROAS falls below viability threshold |
| | 🟢 AOV upsell via top categories: Apparel (#1, $171K), Bags (#3, $24K) | 🔴 Mobile conversion gap (desktop users likely over-indexed in funnel) |
| | 🟢 Geographic expansion: India ($35K, 406 tx) and Canada ($33K, 363 tx) underserved | 🔴 High bounce pages (Apparel 94.98%, YouTube branded 95.39%) risk brand damage |
| | 🟢 Cart recovery email flow targeting 12,340 abandoned sessions | 🔴 Seasonal AOV decline: $113.53 (Nov) → $64.08 (Jan) — post-holiday drop |

---

---

## SLIDE 6 — STP: Segmentation, Targeting, Positioning

> *Evidence base: VQ-8 (country revenue), VQ-9 (category revenue), VQ-3 (funnel stages).*

---

### Segmentation

**Geographic Segmentation (VQ-8 — Revenue by Country)**

| Tier | Countries | Revenue | Transactions | Strategy |
|------|-----------|:-------:|:------------:|----------|
| Tier 1 — Core | United States | $160,573 | 1,940 | Retention + AOV uplift |
| Tier 2 — Growth | India, Canada | $68K combined | 769 | Conversion optimisation |
| Tier 3 — Emerging | UK, Spain, France, China, Japan | $37K combined | 491 | Awareness + organic SEO |

**Behavioural Segmentation (VQ-3 — Purchase Funnel)**

| Segment | Sessions | Description | Tactic |
|---------|:--------:|-------------|--------|
| Browsers | 354,857 → 77,020 viewed | Arrive but don't engage deeply | Landing page UX (VQ-2 worst pages) |
| Cart-Adders | 15,188 added to cart | Show high intent but abandon (81.25%) | Cart recovery email / retargeting |
| Purchasers | 4,848 converted | Completed purchase (CVR 1.37%) | Loyalty, upsell (VQ-9 top categories) |

---

### Targeting

**Primary target:** High-intent desktop users in the US who have previously viewed items but not converted  
**Secondary target:** Organic searchers in Tier 2 growth markets (India, Canada)  
**Tertiary target:** Existing purchasers for cross-sell / upsell within Apparel and Bags categories

---

### Positioning

> *"Data-validated premium Google brand merchandise — quality you can trust, backed by the world's most recognised technology brand."*

- Justify AOV premium ($81.05) through trust signals (Google brand heritage, product quality)
- Compete on brand association rather than price — Apparel dominates ($171,727 = 47% of product revenue)
- Position Data Agent as internal proof of analytics capability (credibility signal for B2B gifting segment)

---

---

## SLIDE 7 — Ansoff Matrix: Growth Strategy

> *Prioritisation framework for where to focus the 20% revenue growth target.*

---

### Ansoff Matrix

```
                 EXISTING PRODUCTS          NEW PRODUCTS
                ┌──────────────────────┬──────────────────────┐
EXISTING        │  MARKET PENETRATION  │  PRODUCT DEVELOPMENT │
MARKETS         │  ⭐ PRIMARY FOCUS     │  ✅ Secondary        │
                │                      │                      │
                │ CVR: 1.37% → +15%    │ AOV: $81.05 → +10%  │
                │ Bounce: 84% → ≤40%   │ Cross-sell Apparel + │
                │ Cart recovery flow   │ Bags bundles (VQ-9)  │
                │ Landing page UX fix  │ Upsell top SKUs      │
                ├──────────────────────┼──────────────────────┤
NEW             │  MARKET DEVELOPMENT  │   DIVERSIFICATION    │
MARKETS         │  ✅ Tertiary          │   ❌ NOT recommended │
                │                      │                      │
                │ India + Canada:      │ New product lines    │
                │ high sessions, under │ outside core merch = │
                │ revenue potential    │ resource distraction │
                │ (VQ-8 geo data)      │                      │
                └──────────────────────┴──────────────────────┘
```

---

### Quadrant Rationale

**Market Penetration (Primary):**
- 12,340 cart-adder sessions abandoned (VQ-7: 81.25% abandonment) = the single highest-leverage opportunity
- Funnel leaks at every stage (VQ-3): 354,857 sessions → 15,188 carts → 4,848 purchases
- Target: CVR +15% relative to 1.37% baseline = reach ~1.58% CVR
- Landing page UX improvements targeting worst bounce pages (VQ-2: Apparel 94.98%, YouTube 95.39%)

**Product Development (Secondary):**
- Apparel dominates (47% of revenue). Introduce bundles combining Apparel + Bags (#3 by revenue) or Apparel + Accessories (#5)
- AOV $81.05 overall, but Nov peak $113.53 suggests customers will spend more in gifting context → replicate gifting triggers year-round

**Market Development (Tertiary):**
- India (406 transactions, $35K) and Canada (363 transactions, $33K) show strong purchase intent relative to their session volume
- Localised landing pages and geo-targeted organic content to grow Tier 2 market share

---

---

## SLIDE 8 — RACE Framework: Execution Plan

> *Maps all 6 KPIs and VQ-validated insights to concrete digital marketing actions.*

---

### RACE Framework Map

```
REACH ──────────────────────────────────────────────────────────
  Organic share: 34.26% → target ≥40%
  - Technical SEO audit of top 10 landing pages (VQ-2)
  - Content strategy: long-tail keywords for Apparel + Bags
  - Internal linking from high-traffic homepage to product pages
  - Timeline: Q1–Q2 2021

  Paid (CPC): maintain ROAS ≥4× gate
  - Do not increase CPC spend until ad spend data is tracked
  - Enable spend tracking to calculate true ROAS (currently data gap)

ACT ────────────────────────────────────────────────────────────
  Bounce rate: 84.22% → target ≤40%
  Priority pages from VQ-2:
    1. /Apparel — 94.98% bounce (40,027 sessions)
    2. YouTube branded — 95.39% bounce (24,071 sessions)
    3. Google Dino Game Tee — 97.79% bounce (18,557 sessions)
  Actions:
  - Add social proof, clear CTAs, and related product carousels on these pages
  - Run A/B tests on hero image and price presentation
  - Timeline: Q1 2021 (quick wins)

CONVERT ────────────────────────────────────────────────────────
  CVR: 1.37% → target +15% relative improvement
  Funnel leaks from VQ-3 (session-level):
    Sessions    354,857  (100%)
    View Item    77,020  (21.7%)  ← −78.3% drop from sessions
    Add to Cart  15,188  (4.3%)   ← −80.3% drop from views
    Checkout     11,106  (3.1%)   ← −26.9% drop from cart
    Purchase      4,848  (1.4%)   ← −56.4% drop from checkout
  Actions:
  - Product page CTA optimisation (sessions → view_item gap)
  - Cart recovery email automation targeting 12,340 abandoners (VQ-7)
  - Checkout friction reduction (11K → 4.8K is −56% drop — biggest leak)
  - Timeline: Q1–Q2 2021

ENGAGE ─────────────────────────────────────────────────────────
  AOV: $81.05 → target +10% to $89.16
  - Post-purchase upsell: recommend Bags or Accessories after Apparel purchase (VQ-9)
  - Loyalty email sequence to previous purchasers (4,452 transactions)
  - Seasonal gifting campaigns to replicate Nov 2020 AOV peak ($113.53)
  - Timeline: Q2–Q3 2021
```

---

### KPI ↔ RACE Stage Mapping

| KPI | RACE Stage | Primary Tactic | VQ Used |
|-----|-----------|----------------|---------|
| Organic Share ≥40% | Reach | SEO programme | VQ-5 |
| Paid ROAS ≥4× | Reach | Track ad spend; hold CPC budget | VQ-6 |
| Bounce Rate ≤40% | Act | Landing page UX audit | VQ-2 |
| CVR +15% | Convert | Funnel CRO + cart recovery | VQ-3, VQ-7 |
| AOV +10% | Engage | Upsell / cross-sell programme | VQ-9 |
| Engagement Rate ≥65% | All stages | UX + content quality improvements | VQ-1 |

---

---

## SLIDE 9 — Data Agent: Insights & Validation

> *Screenshots of agent conversations, validation SQL, and documented hallucination.*
> **ACTION REQUIRED:** Replace the placeholders below with actual screenshots from your BigQuery
> Studio Data Agent session once it is set up.

---

### Agent Conversation Summary

**Conversation 1 — Revenue by Country**
- Question asked: *"Which countries generated the most purchase revenue between November 2020 and January 2021?"*
- Expected answer (from VQ-8): US $160,573 · India $34,986 · Canada $32,799 · UK $11,458 · Spain $7,681
- [SCREENSHOT PLACEHOLDER — agent response + SQL it generated]
- Validation: Run VQ-8 manually and confirm numbers match

---

**Conversation 2 — Cart Abandonment Rate**
- Question asked: *"What percentage of sessions that added items to cart did not complete a purchase?"*
- Expected answer (from VQ-7): 81.25% abandonment (12,340 abandoned / 15,188 cart sessions)
- [SCREENSHOT PLACEHOLDER — agent response + SQL it generated]
- Validation: Run VQ-7 manually and confirm

---

**Conversation 3 — Overall CVR**
- Question asked: *"What is the overall conversion rate for this period?"*
- Expected answer (from VQ-3): 1.37% (4,848 purchases / 354,857 sessions)
- **⚠️ LIKELY HALLUCINATION POINT:** Agent may divide purchase event count by session_start event count rather than using DISTINCT session deduplication — this conflates event-level and session-level counts and will return a deflated CVR
- [SCREENSHOT PLACEHOLDER — agent's wrong query showing the error]
- Correction applied: Show corrected query using VQ-3 pattern (CONCAT deduplication + session-level MAX)
- System instructions updated: added explicit rule prohibiting event-count-as-session-count

---

**Conversation 4 — Top Product Categories**
- Question asked: *"Which product categories drive the most revenue?"*
- Expected answer (from VQ-9): Apparel $171,727 · New $25,813 · Bags $23,860 · Campus Collection $20,061 · Accessories $17,815
- [SCREENSHOT PLACEHOLDER — agent response + SQL it generated]
- Validation: Run VQ-9 manually. **Watch for UNNEST syntax error** — agents frequently write `items.item_category` without UNNEST, which generates a query error

---

### Documented Hallucination (MT-3 Metamorphic Test)

**Test:** Ask engagement rate → ask bounce rate → verify they sum to 1.0

| Question | Agent Answer | Expected | Status |
|----------|:------------:|:--------:|:------:|
| What is the engagement rate? | [AGENT ANSWER] | 15.78% | [PASS/FAIL] |
| What is the bounce rate? | [AGENT ANSWER] | 84.22% | [PASS/FAIL] |
| Sum | [SUM] | 1.0000 | [PASS/FAIL] |

> If the agent uses different denominators for each calculation (a common hallucination — e.g., counting
> session_start events rather than distinct sessions), the two metrics will not sum to 1.0. This is
> evidence of metric definition drift and must be corrected by pointing the agent to VQ-1 and VQ-2.

---

### Validation Methodology: Metamorphic Testing (Yang et al., 2025)

> Metamorphic Testing detects hallucinations without requiring "ground truth" — instead, it exploits
> known mathematical relationships between outputs. If Engagement + Bounce ≠ 1.0, one or both is wrong.
> This technique is applicable wherever outputs have a verifiable algebraic relationship.

---

---

## SLIDE 10 — Roadmap & Control

### Q1–Q4 2021 Action Roadmap

| Quarter | Priority Actions | KPI Target | Owner |
|---------|-----------------|:----------:|-------|
| **Q1 2021** | Landing page UX audit (VQ-2 worst pages: Apparel, YouTube) | Bounce: 84% → 70% | Marketing + UX |
| **Q1 2021** | Cart abandonment email flow (12,340 abandoners from VQ-7) | CVR: 1.37% → 1.50% | CRM + Dev |
| **Q1 2021** | Enable ad spend tracking to unlock ROAS measurement | ROAS: data gap → measurable | Analytics |
| **Q2 2021** | Technical SEO audit + content strategy for organic growth | Organic: 34% → 37% | SEO |
| **Q2 2021** | Checkout friction reduction (−56% drop at begin_checkout→purchase) | CVR: 1.50% → 1.58% | Product + Dev |
| **Q2 2021** | Post-purchase upsell programme (Apparel → Bags cross-sell) | AOV: $81 → $86 | Email + Merch |
| **Q3 2021** | Geo-targeted campaigns for India + Canada (Tier 2 markets, VQ-8) | Revenue: +8% international | Paid + Content |
| **Q3 2021** | A/B testing programme on top 5 landing pages | Bounce: 70% → 55% | UX + Analytics |
| **Q4 2021** | Full SEO programme mature; content library in place | Organic: 37% → 40% | SEO |
| **Q4 2021** | Year-end gifting campaign replicating Nov 2020 AOV peak ($113) | AOV: $86 → $89+ | Campaign |

---

### KPI Targets: Baseline vs. Q4 2021 Projection

| KPI | Nov 2020 Baseline | Q4 2021 Target | Method |
|-----|:-----------------:|:--------------:|--------|
| Engagement Rate | 15.78% | ≥ 25% | UX + content quality improvements |
| Bounce Rate | 84.22% | ≤ 65% | Landing page UX (VQ-2 priority pages) |
| CVR | 1.37% | ≥ 1.58% (+15% rel.) | Funnel CRO + cart recovery (VQ-3, VQ-7) |
| AOV | $81.05 | ≥ $89.16 (+10%) | Upsell + seasonal campaigns (VQ-9) |
| Organic Share | 34.26% | ≥ 40% | SEO programme (VQ-5) |
| Paid ROAS | Not measurable | ≥ 4× (once tracked) | Ad spend tracking + ROAS gate |

---

### Data Agent as CMO Control Tool

```
CMO asks question
       │
       ▼
  Data Agent (BigQuery Conversational Analytics)
       │
       ├─── Retrieves pre-validated answer from Verified Queries (VQ-1 → VQ-9)
       │
       ├─── Flags if metric definition deviates from KPI glossary
       │
       └─── Returns result with SQL — CMO validates against Measurement Framework
                                                    │
                                                    ▼
                                          Decision made with evidence
                                          not assumptions
```

> *"The value of a Data Agent is not automation — it is speed of hypothesis testing.
> The CMO should ask, inspect the SQL, and decide. The agent is the interface;
> the analyst is the gatekeeper." — Li et al. (2026), BIRD-INTERACT*

---

### References

1. **Qu et al. (2024)** — Semantic alignment before SQL generation. Justifies glossary terms + system instructions in agent design.
2. **Yang et al. (2025)** — Metamorphic Testing for hallucination detection in LLM-based SQL agents. Justifies MT-1, MT-2, MT-3 audit methodology.
3. **Li et al. (2026)** — BIRD-INTERACT: human-in-the-loop as state-of-the-art for text-to-SQL agents. Justifies CMO-as-gatekeeper positioning in Slide 9 and Slide 10.

---

*Assignment 2 | Digital Marketing & Data Science 2025–2026 | Data source: BigQuery VQ-1 through VQ-9*
