import os
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import urlparse

st.set_page_config(page_title="GA4 E-Commerce Dashboard", layout="wide", page_icon="📊")

CREDENTIALS_FILE = "service-account.json"
PROJECT_ID = "data-vis-491514"
TABLE = "`bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`"
DATE_FROM = "20201101"
DATE_TO = "20210131"

COLORS = {
    "primary": "#4F8EF7",
    "success": "#2ECC71",
    "warning": "#F39C12",
    "danger": "#E74C3C",
    "purple": "#9B59B6",
    "channels": px.colors.qualitative.Plotly,
}

st.markdown("""
<style>
    .metric-card {
        background: #1E1E2E;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid #2A2A3E;
    }
    .metric-label { color: #888; font-size: 13px; margin-bottom: 4px; }
    .metric-value { color: #fff; font-size: 28px; font-weight: 700; }
    .metric-delta { font-size: 12px; margin-top: 4px; }
    .section-title { color: #ccc; font-size: 13px; font-weight: 600;
                     text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0; }
</style>
""", unsafe_allow_html=True)


# ── BigQuery helpers ───────────────────────────────────────────────────────────

@st.cache_resource
def get_client():
    scopes = ["https://www.googleapis.com/auth/bigquery"]
    try:
        has_secrets = "gcp_service_account" in st.secrets
    except Exception:
        has_secrets = False

    if has_secrets:
        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes,
        )
    elif os.path.exists(CREDENTIALS_FILE):
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=scopes,
        )
    else:
        st.error(
            "**No credentials found.** "
            "Add your service account key to Streamlit Cloud via "
            "**App Settings → Secrets** using the format in `.streamlit/secrets.toml.example`."
        )
        st.stop()
    return bigquery.Client(credentials=creds, project=PROJECT_ID)


@st.cache_data(ttl=3600, show_spinner=False)
def q(sql: str) -> pd.DataFrame:
    return get_client().query(sql).to_dataframe()


# ── SQL queries ────────────────────────────────────────────────────────────────

def sql_engagement():
    return f"""
    WITH sessions AS (
      SELECT
        DATE_TRUNC(PARSE_DATE('%Y%m%d', event_date), MONTH) AS month,
        user_pseudo_id,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
        MAX((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'session_engaged')) AS is_engaged
      FROM {TABLE}
      WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      GROUP BY month, user_pseudo_id, session_id
    )
    SELECT
      FORMAT_DATE('%b %Y', month) AS month_label,
      month,
      COUNT(*) AS total_sessions,
      SUM(is_engaged) AS engaged_sessions,
      ROUND(100 * SUM(is_engaged) / COUNT(*), 1) AS engagement_rate
    FROM sessions
    GROUP BY month, month_label
    ORDER BY month
    """

def sql_conversion():
    return f"""
    WITH sessions AS (
      SELECT
        DATE_TRUNC(PARSE_DATE('%Y%m%d', event_date), MONTH) AS month,
        user_pseudo_id,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
        MAX(IF(event_name = 'purchase', 1, 0)) AS has_purchase
      FROM {TABLE}
      WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      GROUP BY month, user_pseudo_id, session_id
    )
    SELECT
      FORMAT_DATE('%b %Y', month) AS month_label,
      month,
      COUNT(*) AS total_sessions,
      SUM(has_purchase) AS purchase_sessions,
      ROUND(100 * SUM(has_purchase) / COUNT(*), 2) AS conversion_rate
    FROM sessions
    GROUP BY month, month_label
    ORDER BY month
    """

def sql_device_sessions():
    return f"""
    SELECT
      device.category AS device,
      COUNT(DISTINCT CONCAT(user_pseudo_id, CAST(
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
      AS STRING))) AS sessions
    FROM {TABLE}
    WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
    GROUP BY device
    ORDER BY sessions DESC
    """

def sql_revenue_by_channel():
    return f"""
    SELECT
      COALESCE(NULLIF(traffic_source.medium, ''), '(none)') AS channel,
      ROUND(SUM(ecommerce.purchase_revenue), 2) AS revenue,
      COUNT(DISTINCT ecommerce.transaction_id) AS transactions
    FROM {TABLE}
    WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      AND event_name = 'purchase'
    GROUP BY channel
    ORDER BY revenue DESC
    LIMIT 10
    """

def sql_aov():
    return f"""
    SELECT
      FORMAT_DATE('%b %Y', DATE_TRUNC(PARSE_DATE('%Y%m%d', event_date), MONTH)) AS month_label,
      DATE_TRUNC(PARSE_DATE('%Y%m%d', event_date), MONTH) AS month,
      ROUND(SUM(ecommerce.purchase_revenue), 2) AS total_revenue,
      COUNT(DISTINCT ecommerce.transaction_id) AS transactions,
      ROUND(SUM(ecommerce.purchase_revenue) / COUNT(DISTINCT ecommerce.transaction_id), 2) AS aov
    FROM {TABLE}
    WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      AND event_name = 'purchase'
    GROUP BY month, month_label
    ORDER BY month
    """

def sql_funnel():
    return f"""
    WITH steps AS (
      SELECT
        user_pseudo_id,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
        MAX(IF(event_name = 'view_item', 1, 0))       AS viewed,
        MAX(IF(event_name = 'add_to_cart', 1, 0))     AS added,
        MAX(IF(event_name = 'begin_checkout', 1, 0))  AS checked_out,
        MAX(IF(event_name = 'purchase', 1, 0))        AS purchased
      FROM {TABLE}
      WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      GROUP BY user_pseudo_id, session_id
    )
    SELECT
      SUM(viewed)      AS view_item,
      SUM(added)       AS add_to_cart,
      SUM(checked_out) AS begin_checkout,
      SUM(purchased)   AS purchase
    FROM steps
    """

def sql_cart_abandonment():
    return f"""
    WITH cart AS (
      SELECT
        user_pseudo_id,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
        MAX(IF(event_name = 'add_to_cart', 1, 0)) AS added,
        MAX(IF(event_name = 'purchase', 1, 0))    AS purchased
      FROM {TABLE}
      WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      GROUP BY user_pseudo_id, session_id
    )
    SELECT
      SUM(added) AS cart_sessions,
      SUM(IF(added = 1 AND purchased = 0, 1, 0)) AS abandoned,
      ROUND(100 * SUM(IF(added = 1 AND purchased = 0, 1, 0)) / NULLIF(SUM(added), 0), 1) AS abandonment_rate
    FROM cart
    WHERE added = 1
    """

def sql_sessions_by_country():
    return f"""
    SELECT
      geo.country AS country,
      COUNT(DISTINCT CONCAT(user_pseudo_id, CAST(
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
      AS STRING))) AS sessions
    FROM {TABLE}
    WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      AND geo.country IS NOT NULL
      AND geo.country NOT IN ('(not set)', '')
    GROUP BY country
    ORDER BY sessions DESC
    """

def sql_revenue_by_country():
    return f"""
    SELECT
      geo.country AS country,
      ROUND(SUM(ecommerce.purchase_revenue), 2) AS revenue
    FROM {TABLE}
    WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      AND event_name = 'purchase'
      AND geo.country IS NOT NULL
      AND geo.country NOT IN ('(not set)', '')
    GROUP BY country
    ORDER BY revenue DESC
    """

def sql_daily_revenue_sessions():
    return f"""
    WITH daily_sessions AS (
      SELECT
        PARSE_DATE('%Y%m%d', event_date) AS date,
        COUNT(DISTINCT CONCAT(user_pseudo_id, CAST(
          (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
        AS STRING))) AS sessions
      FROM {TABLE}
      WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      GROUP BY date
    ),
    daily_revenue AS (
      SELECT
        PARSE_DATE('%Y%m%d', event_date) AS date,
        ROUND(SUM(ecommerce.purchase_revenue), 2) AS revenue
      FROM {TABLE}
      WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
        AND event_name = 'purchase'
      GROUP BY date
    )
    SELECT
      s.date,
      s.sessions,
      COALESCE(r.revenue, 0) AS revenue
    FROM daily_sessions s
    LEFT JOIN daily_revenue r ON s.date = r.date
    ORDER BY s.date
    """

def sql_category_revenue():
    return f"""
    SELECT
      COALESCE(NULLIF(items.item_category, ''), '(not set)') AS category,
      ROUND(SUM(items.item_revenue), 2) AS revenue
    FROM {TABLE},
    UNNEST(items) AS items
    WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      AND event_name = 'purchase'
      AND items.item_revenue > 0
    GROUP BY category
    ORDER BY revenue DESC
    LIMIT 10
    """

def sql_page_bounce_rate():
    return f"""
    WITH page_events AS (
      SELECT
        user_pseudo_id,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page_location,
        event_timestamp
      FROM {TABLE}
      WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
        AND event_name = 'page_view'
    ),
    sessions AS (
      SELECT
        user_pseudo_id,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
        MAX((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'session_engaged')) AS is_engaged
      FROM {TABLE}
      WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      GROUP BY user_pseudo_id, session_id
      HAVING session_id IS NOT NULL
    ),
    landing_pages AS (
      SELECT
        user_pseudo_id,
        session_id,
        page_location,
        ROW_NUMBER() OVER (PARTITION BY user_pseudo_id, session_id ORDER BY event_timestamp) AS rn
      FROM page_events
      WHERE page_location IS NOT NULL AND session_id IS NOT NULL
    ),
    first_pages AS (
      SELECT user_pseudo_id, session_id, page_location
      FROM landing_pages WHERE rn = 1
    )
    SELECT
      fp.page_location AS page,
      COUNT(*) AS sessions,
      SUM(IF(s.is_engaged = 0 OR s.is_engaged IS NULL, 1, 0)) AS bounced,
      ROUND(100 * SUM(IF(s.is_engaged = 0 OR s.is_engaged IS NULL, 1, 0)) / COUNT(*), 1) AS bounce_rate,
      COUNT(*) - SUM(IF(s.is_engaged = 0 OR s.is_engaged IS NULL, 1, 0)) AS engaged_sessions
    FROM first_pages fp
    JOIN sessions s ON fp.user_pseudo_id = s.user_pseudo_id AND fp.session_id = s.session_id
    GROUP BY page
    HAVING sessions >= 20
    ORDER BY sessions DESC
    LIMIT 20
    """

def sql_customer_journey():
    return f"""
    WITH page_events AS (
      SELECT
        user_pseudo_id,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page_location,
        event_timestamp
      FROM {TABLE}
      WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
        AND event_name = 'page_view'
    ),
    ranked AS (
      SELECT
        user_pseudo_id,
        session_id,
        page_location,
        ROW_NUMBER() OVER (PARTITION BY user_pseudo_id, session_id ORDER BY event_timestamp) AS step
      FROM page_events
      WHERE page_location IS NOT NULL AND session_id IS NOT NULL
    ),
    transitions AS (
      SELECT
        page_location AS from_page,
        LEAD(page_location) OVER (PARTITION BY user_pseudo_id, session_id ORDER BY step) AS to_page,
        step AS from_step
      FROM ranked
    )
    SELECT
      from_page,
      to_page,
      from_step,
      COUNT(*) AS transitions
    FROM transitions
    WHERE from_step <= 3
      AND to_page IS NOT NULL
    GROUP BY from_page, to_page, from_step
    ORDER BY transitions DESC
    LIMIT 100
    """


# ── Load data ──────────────────────────────────────────────────────────────────

with st.spinner("Loading dashboard data from BigQuery..."):
    df_eng        = q(sql_engagement())
    df_conv       = q(sql_conversion())
    df_device     = q(sql_device_sessions())
    df_rev        = q(sql_revenue_by_channel())
    df_aov        = q(sql_aov())
    df_fun        = q(sql_funnel())
    df_cart       = q(sql_cart_abandonment())
    df_country    = q(sql_sessions_by_country())
    df_rev_country = q(sql_revenue_by_country())
    df_daily      = q(sql_daily_revenue_sessions())
    df_cat        = q(sql_category_revenue())
    df_bounce     = q(sql_page_bounce_rate())
    df_journey    = q(sql_customer_journey())


# ── Shared layout helpers ──────────────────────────────────────────────────────

_CHART_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#ccc",
    margin=dict(t=10, b=0),
)

def kpi_card(col, label, value, color="#4F8EF7"):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:{color}">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def choropleth(df, col, color_scale, label, title):
    fig = px.choropleth(
        df,
        locations="country",
        locationmode="country names",
        color=col,
        color_continuous_scale=color_scale,
        labels={col: label},
    )
    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#444",
            bgcolor="rgba(0,0,0,0)",
            landcolor="#1E1E2E",
            oceancolor="#12121F",
            showocean=True,
            lakecolor="#12121F",
            showlakes=True,
            projection_type="natural earth",
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#ccc",
        coloraxis_colorbar=dict(
            title=dict(text=label, font=dict(color="#ccc")),
            tickfont=dict(color="#ccc"),
        ),
        margin=dict(t=30, b=10, l=0, r=0),
        height=380,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════

st.title("GA4 E-Commerce Dashboard")
st.caption("Google Merchandise Store · Nov 2020 – Jan 2021 · Data via BigQuery")
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# 1. KPI SCORECARDS
# ══════════════════════════════════════════════════════════════════════════════

overall_engagement = round(df_eng["engaged_sessions"].sum() / df_eng["total_sessions"].sum() * 100, 1)
overall_conversion = round(df_conv["purchase_sessions"].sum() / df_conv["total_sessions"].sum() * 100, 2)
total_revenue      = df_aov["total_revenue"].sum()
overall_aov        = round(total_revenue / df_aov["transactions"].sum(), 2)
abandonment_rate   = float(df_cart["abandonment_rate"].iloc[0])

col1, col2, col3, col4, col5 = st.columns(5)
kpi_card(col1, "Engagement Rate",     f"{overall_engagement}%",  COLORS["primary"])
kpi_card(col2, "Purchase Conv. Rate", f"{overall_conversion}%",  COLORS["success"])
kpi_card(col3, "Total Revenue",       f"${total_revenue:,.0f}",  COLORS["warning"])
kpi_card(col4, "Avg. Order Value",    f"${overall_aov:,.2f}",    COLORS["purple"])
kpi_card(col5, "Cart Abandonment",    f"{abandonment_rate}%",    COLORS["danger"])


# ══════════════════════════════════════════════════════════════════════════════
# 2. AUDIENCE & TRAFFIC
# ══════════════════════════════════════════════════════════════════════════════

st.divider()
st.header("Audience & Traffic")

# ── Row 1: Sessions by Country | Revenue by Country ───────────────────────────

col_l, col_r = st.columns(2)

with col_l:
    st.markdown('<p class="section-title">Sessions by Country</p>', unsafe_allow_html=True)
    st.plotly_chart(
        choropleth(df_country, "sessions", "Blues", "Sessions", "Sessions by Country"),
        use_container_width=True,
    )
    st.caption("Session volume by country. Darker blue = more sessions.")

with col_r:
    st.markdown('<p class="section-title">Revenue by Country</p>', unsafe_allow_html=True)
    st.plotly_chart(
        choropleth(df_rev_country, "revenue", "Greens", "Revenue (USD)", "Revenue by Country"),
        use_container_width=True,
    )
    st.caption("Purchase revenue by country. Identifies which markets contribute most to revenue.")

# ── Row 2: Sessions by Device | Revenue by Channel ───────────────────────────

col_l, col_r = st.columns(2)

with col_l:
    st.markdown('<p class="section-title">Sessions by Device Type</p>', unsafe_allow_html=True)
    fig = px.bar(
        df_device.sort_values("sessions"), x="sessions", y="device",
        orientation="h", text="sessions",
        labels={"sessions": "Sessions", "device": ""},
        color_discrete_sequence=[COLORS["primary"]],
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(**_CHART_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Unique sessions broken down by device category across the full period.")

with col_r:
    st.markdown('<p class="section-title">Revenue by Traffic Channel</p>', unsafe_allow_html=True)
    fig = px.bar(
        df_rev.sort_values("revenue"), x="revenue", y="channel",
        orientation="h", text="revenue",
        labels={"revenue": "Revenue (USD)", "channel": ""},
        color="revenue", color_continuous_scale="Blues",
    )
    fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
    fig.update_layout(coloraxis_showscale=False, **_CHART_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Total purchase revenue attributed to each traffic source/medium across the full period.")


# ══════════════════════════════════════════════════════════════════════════════
# 3. ENGAGEMENT & CONVERSION
# ══════════════════════════════════════════════════════════════════════════════

st.divider()
st.header("Engagement & Conversion")

# ── Row: Engagement Rate | Conversion Rate ────────────────────────────────────

col_l, col_r = st.columns(2)

with col_l:
    st.markdown('<p class="section-title">Engagement Rate by Month</p>', unsafe_allow_html=True)
    fig = px.bar(
        df_eng, x="month_label", y="engagement_rate",
        text="engagement_rate",
        labels={"month_label": "", "engagement_rate": "Engagement Rate (%)"},
        color_discrete_sequence=[COLORS["primary"]],
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(yaxis_range=[0, 100], **_CHART_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("% of sessions where the user was engaged (10s+ active, 2+ pageviews, or a conversion event).")

with col_r:
    st.markdown('<p class="section-title">Purchase Conversion Rate by Month</p>', unsafe_allow_html=True)
    fig = px.bar(
        df_conv, x="month_label", y="conversion_rate",
        text="conversion_rate",
        labels={"month_label": "", "conversion_rate": "Conversion Rate (%)"},
        color_discrete_sequence=[COLORS["success"]],
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(**_CHART_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("% of sessions that resulted in at least one purchase event.")

# ── Full width: Conversion Funnel ─────────────────────────────────────────────

st.markdown('<p class="section-title">Purchase Conversion Funnel</p>', unsafe_allow_html=True)
funnel_labels = ["View Item", "Add to Cart", "Begin Checkout", "Purchase"]
funnel_values = [
    int(df_fun["view_item"].iloc[0]),
    int(df_fun["add_to_cart"].iloc[0]),
    int(df_fun["begin_checkout"].iloc[0]),
    int(df_fun["purchase"].iloc[0]),
]
fig = go.Figure(go.Funnel(
    y=funnel_labels, x=funnel_values,
    textinfo="value+percent initial",
    marker=dict(color=["#4F8EF7", "#F39C12", "#E67E22", "#E74C3C"]),
))
fig.update_layout(**_CHART_LAYOUT, margin=dict(t=10, b=0))
st.plotly_chart(fig, use_container_width=True)
st.caption(f"Drop-off at each step of the purchase journey. Cart abandonment rate: **{abandonment_rate}%** of sessions that added to cart did not complete a purchase.")


# ══════════════════════════════════════════════════════════════════════════════
# 4. REVENUE & SALES
# ══════════════════════════════════════════════════════════════════════════════

st.divider()
st.header("Revenue & Sales")

# ── Row: Revenue + Transactions | AOV Trend ───────────────────────────────────

col_l, col_r = st.columns(2)

with col_l:
    st.markdown('<p class="section-title">Revenue & Transactions by Month</p>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_aov["month_label"], y=df_aov["total_revenue"],
        name="Revenue (USD)", marker_color=COLORS["warning"], yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=df_aov["month_label"], y=df_aov["transactions"],
        name="Transactions", mode="lines+markers",
        line=dict(color=COLORS["primary"], width=2),
        marker=dict(size=8), yaxis="y2",
    ))
    fig.update_layout(
        yaxis=dict(title="Revenue (USD)", showgrid=False),
        yaxis2=dict(title="Transactions", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.1),
        **_CHART_LAYOUT,
        margin=dict(t=30, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Monthly revenue and transaction volume — dual axis to show both scale and trend simultaneously.")

with col_r:
    st.markdown('<p class="section-title">Average Order Value by Month</p>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_aov["month_label"], y=df_aov["aov"],
        mode="lines+markers+text", text=df_aov["aov"],
        texttemplate="$%{text:,.2f}", textposition="top center",
        line=dict(color=COLORS["purple"], width=3),
        marker=dict(size=10),
    ))
    fig.update_layout(yaxis_title="AOV (USD)", xaxis_title="", **_CHART_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Total revenue divided by number of transactions — shows how purchase value shifts during the holiday season.")

# ── Full width: Daily Revenue vs Sessions ─────────────────────────────────────

st.markdown('<p class="section-title">Daily Revenue vs. Sessions</p>', unsafe_allow_html=True)
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_daily["date"], y=df_daily["revenue"],
    name="Revenue (USD)", mode="lines",
    line=dict(color=COLORS["warning"], width=2),
    fill="tozeroy", fillcolor="rgba(243,156,18,0.1)",
    yaxis="y1",
))
fig.add_trace(go.Scatter(
    x=df_daily["date"], y=df_daily["sessions"],
    name="Sessions", mode="lines",
    line=dict(color=COLORS["primary"], width=2, dash="dot"),
    yaxis="y2",
))
fig.update_layout(
    yaxis=dict(title="Revenue (USD)", showgrid=False, tickprefix="$"),
    yaxis2=dict(title="Sessions", overlaying="y", side="right", showgrid=False),
    legend=dict(orientation="h", y=1.08),
    xaxis=dict(title="", showgrid=False),
    **_CHART_LAYOUT,
    margin=dict(t=30, b=0),
    height=360,
)
st.plotly_chart(fig, use_container_width=True)
st.caption("Daily revenue (solid, left axis) alongside daily sessions (dotted, right axis). Reveals whether traffic spikes translate into proportional revenue gains.")

# ── Full width: Revenue by Product Category ───────────────────────────────────

st.markdown('<p class="section-title">Revenue by Product Category</p>', unsafe_allow_html=True)
fig = px.bar(
    df_cat.sort_values("revenue"), x="revenue", y="category",
    orientation="h", text="revenue",
    labels={"revenue": "Revenue (USD)", "category": ""},
    color="revenue", color_continuous_scale="Blues",
)
fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
fig.update_layout(coloraxis_showscale=False, **_CHART_LAYOUT, height=360)
st.plotly_chart(fig, use_container_width=True)
st.caption("Total purchase revenue broken down by product category. Identifies which categories are most profitable — informs budget allocation and promotional strategy.")


# ══════════════════════════════════════════════════════════════════════════════
# 5. WEBSITE PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════

st.divider()
st.header("Website Performance")

# ── Landing Page Bounce Rate Table ────────────────────────────────────────────

st.markdown('<p class="section-title">Landing Page Bounce Rate</p>', unsafe_allow_html=True)
st.caption("Bounce rate = % of sessions that landed on this page and were **not engaged** (< 10s, < 2 pageviews, no conversion). Sorted by session volume — focus on high-traffic rows with high bounce rates.")

def clean_path(url):
    try:
        path = urlparse(url).path.rstrip("/")
        return path if path else "/"
    except Exception:
        return url[:60]

df_bounce_display = df_bounce.copy()
df_bounce_display["page"] = df_bounce_display["page"].apply(clean_path)
df_bounce_display = df_bounce_display.rename(columns={
    "page": "Page Path",
    "sessions": "Sessions",
    "bounced": "Bounced Sessions",
    "bounce_rate": "Bounce Rate (%)",
    "engaged_sessions": "Engaged Sessions",
})

def color_bounce_rate(val):
    if val >= 70:
        return "color: #E74C3C; font-weight: bold"
    elif val >= 50:
        return "color: #F39C12; font-weight: bold"
    else:
        return "color: #2ECC71; font-weight: bold"

styled = (
    df_bounce_display
    .style
    .applymap(color_bounce_rate, subset=["Bounce Rate (%)"])
    .format({"Sessions": "{:,}", "Bounced Sessions": "{:,}", "Engaged Sessions": "{:,}", "Bounce Rate (%)": "{:.1f}%"})
)
st.dataframe(styled, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# 6. CUSTOMER JOURNEY
# ══════════════════════════════════════════════════════════════════════════════

st.divider()
st.header("Customer Journey")

# ── Page Navigation Flow Sankey ───────────────────────────────────────────────

st.markdown('<p class="section-title">Page Navigation Flow (Steps 1 → 4)</p>', unsafe_allow_html=True)
st.caption("Shows where visitors go across their first four page views. Each band's width represents the number of sessions that followed that path. Top 8 pages shown; all others grouped as '(other pages)'.")

all_pages_series = pd.concat([df_journey["from_page"], df_journey["to_page"]])
top_pages_set = set(all_pages_series.value_counts().head(8).index)

def map_page(url):
    if url in top_pages_set:
        p = clean_path(url)
        return p if p else "/"
    return "(other pages)"

df_j = df_journey.copy()
df_j["from_clean"] = df_j["from_page"].map(map_page)
df_j["to_clean"]   = df_j["to_page"].map(map_page)

df_agg_j = (
    df_j
    .groupby(["from_clean", "to_clean", "from_step"], as_index=False)["transitions"]
    .sum()
)

node_map: dict = {}

def get_node(page: str, step: int) -> int:
    key = (page, step)
    if key not in node_map:
        node_map[key] = len(node_map)
    return node_map[key]

srcs, tgts, vals = [], [], []
for _, row in df_agg_j.iterrows():
    step = int(row["from_step"])
    srcs.append(get_node(row["from_clean"], step))
    tgts.append(get_node(row["to_clean"], step + 1))
    vals.append(int(row["transitions"]))

labels = [""] * len(node_map)
for (page, _step), idx in node_map.items():
    labels[idx] = page

node_colors = [
    "#9B59B6" if lbl == "(other pages)" else "#4F8EF7"
    for lbl in labels
]

fig = go.Figure(go.Sankey(
    arrangement="snap",
    node=dict(pad=20, thickness=18, label=labels, color=node_colors),
    link=dict(source=srcs, target=tgts, value=vals, color="rgba(79,142,247,0.2)"),
))
fig.update_layout(
    **_CHART_LAYOUT,
    font_size=12,
    height=520,
    margin=dict(t=10, b=10, l=10, r=10),
)
st.plotly_chart(fig, use_container_width=True)
