# Dashboard Implementations — Status

All 5 implementations approved and built. See `app.py` for full code.

---

## Implementation 1 — Sessions by Country (World Map) ✓
**Chart:** Choropleth world map, colour gradient (light → dark blue) by session count.
**Section:** Traffic Sources

---

## Implementation 2 — Daily Revenue + Sessions (Dual-Axis) ✓
**Chart:** Dual-axis line chart — revenue (solid, left axis) + sessions (dotted, right axis) at daily granularity.
**Section:** Sales Trends

---

## Implementation 3 — Top Product Categories by Revenue ✓
**Chart:** Donut chart + horizontal bar chart side-by-side.
**Section:** Sales Trends

---

## Implementation 4 — Page-Level Bounce Rate Table ✓
**Chart:** Styled table — Page Path | Sessions | Bounced Sessions | Bounce Rate (%) | Engaged Sessions.
Bounce Rate colour-coded: green < 50%, amber 50–70%, red ≥ 70%.
Ranked by session volume (most traffic first).
**Section:** Website Performance

---

## Implementation 5 — Customer Journey Flow (Sankey) ✓
**Chart:** Sankey diagram — page-to-page transitions across first 4 steps (steps 1→2, 2→3, 3→4).
Top 8 pages shown by name; all others grouped as "(other pages)".
**Section:** Customer Journey

---

## Notes

- All data from `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`, Nov 2020 – Jan 2021.
- All queries are cached (1 hour TTL) — BigQuery is only hit once per session.
- Bounce rate = sessions that landed on a page and had `session_engaged = 0` (< 10s active, < 2 pageviews, no conversion).
- Customer journey uses LEAD() window function to compute next-page transitions without a self-join.
