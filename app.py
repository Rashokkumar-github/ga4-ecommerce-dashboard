import os
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import urlparse

st.set_page_config(page_title="GA4 E-Commerce Dashboard", layout="wide", page_icon="◆")

CREDENTIALS_FILE = "service-account.json"
PROJECT_ID       = "data-vis-491514"
TABLE            = "`bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`"
DATE_FROM        = "20201101"
DATE_TO          = "20210131"

# ── Palette ───────────────────────────────────────────────────────────────────
GOLD   = "#C8973A"
BLUE   = "#3D7EF5"
GREEN  = "#1DB97E"
RED    = "#E84040"
VIOLET = "#9B6FE8"

COLORS = {
    "primary": BLUE,
    "success": GREEN,
    "warning": GOLD,
    "danger":  RED,
    "purple":  VIOLET,
}

GOLD_SCALE = [[0, "#0E0D1A"], [0.5, "#7B5718"], [1, "#C8973A"]]
BLUE_SCALE = [[0, "#0E0D1A"], [0.5, "#1A3A8A"], [1, "#3D7EF5"]]

# ── Design system ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;1,400&family=IBM+Plex+Mono:wght@300;400;500&family=Barlow+Condensed:wght@400;500;600;700&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg:      #06060F;
    --surface: #0C0C1E;
    --border:  #181830;
    --subtle:  #11112A;
    --gold:    #C8973A;
    --blue:    #3D7EF5;
    --green:   #1DB97E;
    --red:     #E84040;
    --violet:  #9B6FE8;
    --text:    #DDD8F0;
    --muted:   #4A4A70;
    --dim:     #2A2A4A;
}

/* ── Page ── */
.stApp {
    background: var(--bg) !important;
    background-image:
        radial-gradient(ellipse at 12% 35%, rgba(61,126,245,0.05) 0%, transparent 55%),
        radial-gradient(ellipse at 88% 12%, rgba(200,151,58,0.05) 0%, transparent 55%),
        radial-gradient(ellipse at 50% 90%, rgba(155,110,232,0.03) 0%, transparent 55%);
}
.block-container {
    padding: 0 2.5rem 5rem !important;
    max-width: 1440px !important;
}

/* ── Dashboard header ── */
.dash-header {
    padding: 2.5rem 0 2rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0;
}
.dash-eyebrow {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.4em;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 10px;
}
.dash-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 3.4rem;
    font-weight: 400;
    letter-spacing: -0.03em;
    line-height: 1;
    margin: 0 0 14px;
    background: linear-gradient(130deg, #DDD8F0 0%, #9090B8 55%, #C8973A 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.dash-meta {
    font-family: 'DM Sans', sans-serif;
    font-size: 12px;
    font-weight: 300;
    color: var(--muted);
    letter-spacing: 0.04em;
}
.dash-meta span {
    color: var(--dim);
    margin: 0 8px;
}

/* ── Hide Streamlit native headers ── */
h1, h2, h3 { display: none !important; }

/* ── Section breaks ── */
.section-break {
    display: flex;
    align-items: center;
    gap: 16px;
    margin: 3.5rem 0 1.75rem;
}
.section-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    font-weight: 400;
    color: var(--gold);
    letter-spacing: 0.12em;
    opacity: 0.75;
    flex-shrink: 0;
}
.section-name {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    color: var(--text);
    flex-shrink: 0;
}
.section-rule {
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, var(--border) 0%, transparent 100%);
}

/* ── KPI strip ── */
.kpi-strip {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    border-radius: 4px;
    overflow: hidden;
    margin: 2rem 0 0;
}
.kpi-card {
    background: var(--surface);
    padding: 22px 20px 20px;
    position: relative;
    transition: background 0.2s ease;
}
.kpi-card:hover { background: #10102A; }
.kpi-bar {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.kpi-label {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 14px;
}
.kpi-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem;
    font-weight: 300;
    line-height: 1;
    letter-spacing: -0.03em;
}

/* ── Chart label ── */
.chart-label {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--muted);
    padding-left: 10px;
    border-left: 2px solid var(--gold);
    margin-bottom: 12px;
    line-height: 1.4;
}

/* ── Caption ── */
[data-testid="stCaptionContainer"] p,
.stCaption p, .stCaption {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11.5px !important;
    color: var(--muted) !important;
    line-height: 1.65 !important;
    margin-top: 10px !important;
    font-weight: 300 !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrameResizable"],
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    overflow: hidden !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-color: var(--gold) transparent transparent transparent !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--dim); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
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
            st.secrets["gcp_service_account"], scopes=scopes)
    elif os.path.exists(CREDENTIALS_FILE):
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=scopes)
    else:
        st.error(
            "**No credentials found.** Add your service account key to Streamlit Cloud via "
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
      FORMAT_DATE('%b %Y', month) AS month_label, month,
      COUNT(*) AS total_sessions,
      SUM(is_engaged) AS engaged_sessions,
      ROUND(100 * SUM(is_engaged) / COUNT(*), 1) AS engagement_rate
    FROM sessions GROUP BY month, month_label ORDER BY month
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
      FORMAT_DATE('%b %Y', month) AS month_label, month,
      COUNT(*) AS total_sessions,
      SUM(has_purchase) AS purchase_sessions,
      ROUND(100 * SUM(has_purchase) / COUNT(*), 2) AS conversion_rate
    FROM sessions GROUP BY month, month_label ORDER BY month
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
    GROUP BY device ORDER BY sessions DESC
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
    GROUP BY channel ORDER BY revenue DESC LIMIT 10
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
    GROUP BY month, month_label ORDER BY month
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
    SELECT SUM(viewed) AS view_item, SUM(added) AS add_to_cart,
           SUM(checked_out) AS begin_checkout, SUM(purchased) AS purchase
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
    SELECT SUM(added) AS cart_sessions,
           SUM(IF(added = 1 AND purchased = 0, 1, 0)) AS abandoned,
           ROUND(100 * SUM(IF(added = 1 AND purchased = 0, 1, 0)) / NULLIF(SUM(added), 0), 1) AS abandonment_rate
    FROM cart WHERE added = 1
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
      AND geo.country IS NOT NULL AND geo.country NOT IN ('(not set)', '')
    GROUP BY country ORDER BY sessions DESC
    """

def sql_revenue_by_country():
    return f"""
    SELECT
      geo.country AS country,
      ROUND(SUM(ecommerce.purchase_revenue), 2) AS revenue
    FROM {TABLE}
    WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      AND event_name = 'purchase'
      AND geo.country IS NOT NULL AND geo.country NOT IN ('(not set)', '')
    GROUP BY country ORDER BY revenue DESC
    """

def sql_daily_revenue_sessions():
    return f"""
    WITH daily_sessions AS (
      SELECT PARSE_DATE('%Y%m%d', event_date) AS date,
        COUNT(DISTINCT CONCAT(user_pseudo_id, CAST(
          (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
        AS STRING))) AS sessions
      FROM {TABLE} WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}' GROUP BY date
    ),
    daily_revenue AS (
      SELECT PARSE_DATE('%Y%m%d', event_date) AS date,
             ROUND(SUM(ecommerce.purchase_revenue), 2) AS revenue
      FROM {TABLE}
      WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}' AND event_name = 'purchase'
      GROUP BY date
    )
    SELECT s.date, s.sessions, COALESCE(r.revenue, 0) AS revenue
    FROM daily_sessions s LEFT JOIN daily_revenue r ON s.date = r.date ORDER BY s.date
    """

def sql_category_revenue():
    return f"""
    SELECT
      COALESCE(NULLIF(items.item_category, ''), '(not set)') AS category,
      ROUND(SUM(items.item_revenue), 2) AS revenue
    FROM {TABLE}, UNNEST(items) AS items
    WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      AND event_name = 'purchase' AND items.item_revenue > 0
    GROUP BY category ORDER BY revenue DESC LIMIT 10
    """

def sql_page_bounce_rate():
    return f"""
    WITH page_events AS (
      SELECT user_pseudo_id,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page_location,
        event_timestamp
      FROM {TABLE}
      WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}' AND event_name = 'page_view'
    ),
    sessions AS (
      SELECT user_pseudo_id,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
        MAX((SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'session_engaged')) AS is_engaged
      FROM {TABLE} WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}'
      GROUP BY user_pseudo_id, session_id HAVING session_id IS NOT NULL
    ),
    landing_pages AS (
      SELECT user_pseudo_id, session_id, page_location,
        ROW_NUMBER() OVER (PARTITION BY user_pseudo_id, session_id ORDER BY event_timestamp) AS rn
      FROM page_events WHERE page_location IS NOT NULL AND session_id IS NOT NULL
    ),
    first_pages AS (SELECT user_pseudo_id, session_id, page_location FROM landing_pages WHERE rn = 1)
    SELECT fp.page_location AS page, COUNT(*) AS sessions,
      SUM(IF(s.is_engaged = 0 OR s.is_engaged IS NULL, 1, 0)) AS bounced,
      ROUND(100 * SUM(IF(s.is_engaged = 0 OR s.is_engaged IS NULL, 1, 0)) / COUNT(*), 1) AS bounce_rate,
      COUNT(*) - SUM(IF(s.is_engaged = 0 OR s.is_engaged IS NULL, 1, 0)) AS engaged_sessions
    FROM first_pages fp
    JOIN sessions s ON fp.user_pseudo_id = s.user_pseudo_id AND fp.session_id = s.session_id
    GROUP BY page HAVING sessions >= 20 ORDER BY sessions DESC LIMIT 20
    """

def sql_customer_journey():
    return f"""
    WITH page_events AS (
      SELECT user_pseudo_id,
        (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id') AS session_id,
        (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page_location,
        event_timestamp
      FROM {TABLE}
      WHERE _TABLE_SUFFIX BETWEEN '{DATE_FROM}' AND '{DATE_TO}' AND event_name = 'page_view'
    ),
    ranked AS (
      SELECT user_pseudo_id, session_id, page_location,
        ROW_NUMBER() OVER (PARTITION BY user_pseudo_id, session_id ORDER BY event_timestamp) AS step
      FROM page_events WHERE page_location IS NOT NULL AND session_id IS NOT NULL
    ),
    transitions AS (
      SELECT page_location AS from_page,
        LEAD(page_location) OVER (PARTITION BY user_pseudo_id, session_id ORDER BY step) AS to_page,
        step AS from_step
      FROM ranked
    )
    SELECT from_page, to_page, from_step, COUNT(*) AS transitions
    FROM transitions WHERE from_step <= 3 AND to_page IS NOT NULL
    GROUP BY from_page, to_page, from_step ORDER BY transitions DESC LIMIT 100
    """


# ── Load data ──────────────────────────────────────────────────────────────────

with st.spinner("Loading dashboard…"):
    df_eng         = q(sql_engagement())
    df_conv        = q(sql_conversion())
    df_device      = q(sql_device_sessions())
    df_rev         = q(sql_revenue_by_channel())
    df_aov         = q(sql_aov())
    df_fun         = q(sql_funnel())
    df_cart        = q(sql_cart_abandonment())
    df_country     = q(sql_sessions_by_country())
    df_rev_country = q(sql_revenue_by_country())
    df_daily       = q(sql_daily_revenue_sessions())
    df_cat         = q(sql_category_revenue())
    df_bounce      = q(sql_page_bounce_rate())
    df_journey     = q(sql_customer_journey())


# ── Shared chart defaults ─────────────────────────────────────────────────────

_CHART_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#4A4A70", size=12),
)
_DEFAULT_MARGIN = dict(t=10, b=0, l=0, r=0)
_AXIS_STYLE = dict(showgrid=False, zeroline=False, showline=False,
                   tickfont=dict(family="IBM Plex Mono, monospace", size=11, color="#4A4A70"))
_GRID_AXIS  = dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)",
                   zeroline=False, showline=False,
                   tickfont=dict(family="IBM Plex Mono, monospace", size=11, color="#4A4A70"))


# ── UI helpers ────────────────────────────────────────────────────────────────

def section_break(num: int, title: str):
    st.markdown(f"""
    <div class="section-break">
        <span class="section-num">{num:02d}</span>
        <span class="section-name">{title}</span>
        <div class="section-rule"></div>
    </div>""", unsafe_allow_html=True)

def chart_label(text: str):
    st.markdown(f'<div class="chart-label">{text}</div>', unsafe_allow_html=True)

def kpi_card(col, label: str, value: str, color: str = BLUE):
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-bar" style="background:{color}"></div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{color}">{value}</div>
    </div>""", unsafe_allow_html=True)

def choropleth(df, col, color_scale, label):
    fig = px.choropleth(
        df, locations="country", locationmode="country names",
        color=col, color_continuous_scale=color_scale, labels={col: label},
    )
    fig.update_layout(
        geo=dict(
            showframe=False, showcoastlines=True, coastlinecolor="#1A1A30",
            bgcolor="rgba(0,0,0,0)", landcolor="#0E0E1C",
            oceancolor="#06060F", showocean=True,
            lakecolor="#06060F", showlakes=True,
            projection_type="natural earth",
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#4A4A70"),
        coloraxis_colorbar=dict(
            title=dict(text=label, font=dict(color="#4A4A70", size=11)),
            tickfont=dict(color="#4A4A70", family="IBM Plex Mono, monospace", size=10),
            thickness=10, len=0.6,
        ),
        margin=dict(t=20, b=10, l=0, r=0),
        height=370,
    )
    return fig

def clean_path(url):
    try:
        path = urlparse(url).path.rstrip("/")
        return path if path else "/"
    except Exception:
        return url[:60]


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="dash-header">
    <div class="dash-eyebrow">Analytics Intelligence</div>
    <div class="dash-title">GA4 E-Commerce</div>
    <div class="dash-meta">
        Google Merchandise Store
        <span>·</span>
        Nov 2020 – Jan 2021
        <span>·</span>
        BigQuery Public Dataset
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# KPI STRIP
# ══════════════════════════════════════════════════════════════════════════════

overall_engagement = round(df_eng["engaged_sessions"].sum() / df_eng["total_sessions"].sum() * 100, 1)
overall_conversion = round(df_conv["purchase_sessions"].sum() / df_conv["total_sessions"].sum() * 100, 2)
total_revenue      = df_aov["total_revenue"].sum()
overall_aov        = round(total_revenue / df_aov["transactions"].sum(), 2)
abandonment_rate   = float(df_cart["abandonment_rate"].iloc[0])

st.markdown('<div class="kpi-strip">', unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns(5)
kpi_card(col1, "Engagement Rate",     f"{overall_engagement}%",  BLUE)
kpi_card(col2, "Purchase Conv. Rate", f"{overall_conversion}%",  GREEN)
kpi_card(col3, "Total Revenue",       f"${total_revenue:,.0f}",  GOLD)
kpi_card(col4, "Avg. Order Value",    f"${overall_aov:,.2f}",    VIOLET)
kpi_card(col5, "Cart Abandonment",    f"{abandonment_rate}%",    RED)
st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 01  AUDIENCE & TRAFFIC
# ══════════════════════════════════════════════════════════════════════════════

section_break(1, "Audience & Traffic")

col_l, col_r = st.columns(2)

with col_l:
    chart_label("Sessions by Country")
    st.plotly_chart(
        choropleth(df_country, "sessions", BLUE_SCALE, "Sessions"),
        use_container_width=True,
    )
    st.caption("Session volume by country across Nov 2020 – Jan 2021. Identifies markets driving the most traffic.")

with col_r:
    chart_label("Revenue by Country")
    st.plotly_chart(
        choropleth(df_rev_country, "revenue", GOLD_SCALE, "Revenue (USD)"),
        use_container_width=True,
    )
    st.caption("Purchase revenue by country. Reveals which markets convert traffic into commercial value.")

col_l, col_r = st.columns(2)

with col_l:
    chart_label("Sessions by Device Type")
    fig = px.bar(
        df_device.sort_values("sessions"), x="sessions", y="device",
        orientation="h", text="sessions",
        labels={"sessions": "Sessions", "device": ""},
        color_discrete_sequence=[BLUE],
    )
    fig.update_traces(
        texttemplate="%{text:,}", textposition="outside",
        textfont=dict(family="IBM Plex Mono, monospace", size=11, color="#4A4A70"),
        marker_line_width=0,
    )
    fig.update_layout(**_CHART_LAYOUT, margin=_DEFAULT_MARGIN,
                      xaxis=_AXIS_STYLE, yaxis=_AXIS_STYLE)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Unique sessions by device category. Desktop dominance shapes responsive design priorities.")

with col_r:
    chart_label("Revenue by Traffic Channel")
    fig = px.bar(
        df_rev.sort_values("revenue"), x="revenue", y="channel",
        orientation="h", text="revenue",
        labels={"revenue": "Revenue (USD)", "channel": ""},
        color="revenue", color_continuous_scale=GOLD_SCALE,
    )
    fig.update_traces(
        texttemplate="$%{text:,.0f}", textposition="outside",
        textfont=dict(family="IBM Plex Mono, monospace", size=11, color="#4A4A70"),
        marker_line_width=0,
    )
    fig.update_layout(coloraxis_showscale=False, **_CHART_LAYOUT, margin=_DEFAULT_MARGIN,
                      xaxis=_AXIS_STYLE, yaxis=_AXIS_STYLE)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Total purchase revenue attributed to each traffic source/medium across the full period.")


# ══════════════════════════════════════════════════════════════════════════════
# 02  ENGAGEMENT & CONVERSION
# ══════════════════════════════════════════════════════════════════════════════

section_break(2, "Engagement & Conversion")

col_l, col_r = st.columns(2)

with col_l:
    chart_label("Engagement Rate by Month")
    fig = px.bar(
        df_eng, x="month_label", y="engagement_rate",
        text="engagement_rate",
        labels={"month_label": "", "engagement_rate": "Engagement Rate (%)"},
        color_discrete_sequence=[BLUE],
    )
    fig.update_traces(
        texttemplate="%{text}%", textposition="outside",
        textfont=dict(family="IBM Plex Mono, monospace", size=11, color="#4A4A70"),
        marker_line_width=0,
    )
    fig.update_layout(yaxis_range=[0, 100], **_CHART_LAYOUT, margin=_DEFAULT_MARGIN,
                      xaxis=_AXIS_STYLE, yaxis={**_GRID_AXIS, "range": [0, 100]})
    st.plotly_chart(fig, use_container_width=True)
    st.caption("% of sessions where the user was engaged (10s+ active, 2+ pageviews, or a conversion event).")

with col_r:
    chart_label("Purchase Conversion Rate by Month")
    fig = px.bar(
        df_conv, x="month_label", y="conversion_rate",
        text="conversion_rate",
        labels={"month_label": "", "conversion_rate": "Conversion Rate (%)"},
        color_discrete_sequence=[GREEN],
    )
    fig.update_traces(
        texttemplate="%{text}%", textposition="outside",
        textfont=dict(family="IBM Plex Mono, monospace", size=11, color="#4A4A70"),
        marker_line_width=0,
    )
    fig.update_layout(**_CHART_LAYOUT, margin=_DEFAULT_MARGIN,
                      xaxis=_AXIS_STYLE, yaxis=_GRID_AXIS)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("% of sessions that resulted in at least one purchase event.")

chart_label("Purchase Conversion Funnel")
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
    textfont=dict(family="IBM Plex Mono, monospace", size=12),
    marker=dict(color=[BLUE, GOLD, "#E07820", RED]),
    connector=dict(line=dict(color="rgba(255,255,255,0.04)", width=1)),
))
fig.update_layout(**_CHART_LAYOUT, margin=_DEFAULT_MARGIN)
st.plotly_chart(fig, use_container_width=True)
st.caption(f"Drop-off at each step of the purchase journey. Cart abandonment rate: **{abandonment_rate}%** of sessions that added to cart did not complete a purchase.")


# ══════════════════════════════════════════════════════════════════════════════
# 03  REVENUE & SALES
# ══════════════════════════════════════════════════════════════════════════════

section_break(3, "Revenue & Sales")

col_l, col_r = st.columns(2)

with col_l:
    chart_label("Revenue & Transactions by Month")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_aov["month_label"], y=df_aov["total_revenue"],
        name="Revenue", marker_color=GOLD, marker_line_width=0, yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=df_aov["month_label"], y=df_aov["transactions"],
        name="Transactions", mode="lines+markers",
        line=dict(color=BLUE, width=2),
        marker=dict(size=7, color=BLUE, line=dict(width=1.5, color="#06060F")),
        yaxis="y2",
    ))
    fig.update_layout(
        yaxis=dict(title="Revenue (USD)", showgrid=False, zeroline=False,
                   tickfont=dict(family="IBM Plex Mono, monospace", size=10, color="#4A4A70"),
                   tickprefix="$"),
        yaxis2=dict(title="Transactions", overlaying="y", side="right", showgrid=False,
                    zeroline=False,
                    tickfont=dict(family="IBM Plex Mono, monospace", size=10, color="#4A4A70")),
        legend=dict(orientation="h", y=1.12, font=dict(size=11)),
        **_CHART_LAYOUT,
        margin=dict(t=30, b=0, l=0, r=0),
        xaxis=_AXIS_STYLE,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Monthly revenue (bars) and transaction volume (line) — dual axis reveals scale and trend simultaneously.")

with col_r:
    chart_label("Average Order Value by Month")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_aov["month_label"], y=df_aov["aov"],
        mode="lines+markers+text", text=df_aov["aov"],
        texttemplate="$%{text:,.2f}", textposition="top center",
        textfont=dict(family="IBM Plex Mono, monospace", size=11, color="#4A4A70"),
        line=dict(color=VIOLET, width=2.5),
        marker=dict(size=9, color=VIOLET, line=dict(width=2, color="#06060F")),
        fill="tozeroy", fillcolor="rgba(155,110,232,0.06)",
    ))
    fig.update_layout(
        yaxis={**_GRID_AXIS, "title": "AOV (USD)", "tickprefix": "$"},
        xaxis=_AXIS_STYLE,
        **_CHART_LAYOUT,
        margin=dict(t=30, b=0, l=0, r=0),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Total revenue divided by transactions — shows how purchase value shifts during the holiday season.")

chart_label("Daily Revenue vs. Sessions")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_daily["date"], y=df_daily["revenue"],
    name="Revenue (USD)", mode="lines",
    line=dict(color=GOLD, width=1.8),
    fill="tozeroy", fillcolor="rgba(200,151,58,0.08)",
    yaxis="y1",
))
fig.add_trace(go.Scatter(
    x=df_daily["date"], y=df_daily["sessions"],
    name="Sessions", mode="lines",
    line=dict(color=BLUE, width=1.5, dash="dot"),
    yaxis="y2",
))
fig.update_layout(
    yaxis=dict(title="Revenue (USD)", showgrid=False, zeroline=False, tickprefix="$",
               tickfont=dict(family="IBM Plex Mono, monospace", size=10, color="#4A4A70")),
    yaxis2=dict(title="Sessions", overlaying="y", side="right", showgrid=False, zeroline=False,
                tickfont=dict(family="IBM Plex Mono, monospace", size=10, color="#4A4A70")),
    legend=dict(orientation="h", y=1.08, font=dict(size=11)),
    xaxis={**_AXIS_STYLE, "title": ""},
    **_CHART_LAYOUT,
    margin=dict(t=30, b=0, l=0, r=0),
    height=340,
)
st.plotly_chart(fig, use_container_width=True)
st.caption("Daily revenue (solid gold) alongside daily sessions (dotted blue). Reveals whether traffic spikes translate into proportional revenue gains.")

chart_label("Revenue by Product Category")
fig = px.bar(
    df_cat.sort_values("revenue"), x="revenue", y="category",
    orientation="h", text="revenue",
    labels={"revenue": "Revenue (USD)", "category": ""},
    color="revenue", color_continuous_scale=GOLD_SCALE,
)
fig.update_traces(
    texttemplate="$%{text:,.0f}", textposition="outside",
    textfont=dict(family="IBM Plex Mono, monospace", size=11, color="#4A4A70"),
    marker_line_width=0,
)
fig.update_layout(coloraxis_showscale=False, **_CHART_LAYOUT,
                  margin=_DEFAULT_MARGIN, height=340,
                  xaxis=_AXIS_STYLE, yaxis=_AXIS_STYLE)
st.plotly_chart(fig, use_container_width=True)
st.caption("Total purchase revenue by product category — identifies highest-value lines for budget allocation and promotional strategy.")


# ══════════════════════════════════════════════════════════════════════════════
# 04  WEBSITE PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════

section_break(4, "Website Performance")

chart_label("Landing Page Bounce Rate")
st.caption("Bounce rate = % of sessions that landed on this page and were **not engaged** (< 10s, < 2 pageviews, no conversion). Focus on high-traffic rows with high bounce rates.")

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
        return "color: #E84040; font-weight: 500"
    elif val >= 50:
        return "color: #C8973A; font-weight: 500"
    return "color: #1DB97E; font-weight: 500"

styled = (
    df_bounce_display
    .style
    .map(color_bounce_rate, subset=["Bounce Rate (%)"])
    .format({
        "Sessions": "{:,}",
        "Bounced Sessions": "{:,}",
        "Engaged Sessions": "{:,}",
        "Bounce Rate (%)": "{:.1f}%",
    })
)
st.dataframe(styled, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# 05  CUSTOMER JOURNEY
# ══════════════════════════════════════════════════════════════════════════════

section_break(5, "Customer Journey")

chart_label("Page Navigation Flow — Steps 1 → 4")
st.caption("Where visitors go across their first four page views. Band width = session volume. Top 8 pages shown; all others grouped as '(other pages)'.")

all_pages_series = pd.concat([df_journey["from_page"], df_journey["to_page"]])
top_pages_set    = set(all_pages_series.value_counts().head(8).index)

def map_page(url):
    if url in top_pages_set:
        p = clean_path(url)
        return p if p else "/"
    return "(other pages)"

df_j = df_journey.copy()
df_j["from_clean"] = df_j["from_page"].map(map_page)
df_j["to_clean"]   = df_j["to_page"].map(map_page)

df_agg_j = (
    df_j.groupby(["from_clean", "to_clean", "from_step"], as_index=False)["transitions"].sum()
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

node_colors = [VIOLET if lbl == "(other pages)" else BLUE for lbl in labels]

fig = go.Figure(go.Sankey(
    arrangement="snap",
    node=dict(
        pad=24, thickness=16,
        label=labels, color=node_colors,
        line=dict(width=0),
    ),
    link=dict(
        source=srcs, target=tgts, value=vals,
        color="rgba(61,126,245,0.12)",
    ),
))
fig.update_layout(
    **_CHART_LAYOUT,
    height=520,
    margin=dict(t=10, b=10, l=10, r=10),
)
st.plotly_chart(fig, use_container_width=True)
