"""
Aqua Harvest interactive dashboard (2012–2026).
Run:  streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ------------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Aqua Harvest Dashboard",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# DATA
# ------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.DataFrame({
        "YEAR": [2012, 2013, 2014, 2015, 2016, 2017, 2018,
                 2019, 2020, 2021, 2022, 2023, 2024, 2025],
        "AQUA_HARVEST": [64.7, 81.4, 19, 20.5, 66.2, 192.4, 718,
                         585, 608, 526, 405, 2.1, 13.7, 37.8],
    })
    return df

history = load_data()

# 2026 operational inputs
YTD_2026       = 93.0
YTD_MONTHS     = 8
PROJECTED_2026 = 212.0
CAGES_ACTIVE   = 10

# ------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------
st.sidebar.title("🐟 Controls")
st.sidebar.markdown("---")

st.sidebar.subheader("2026 Inputs")
projected_2026 = st.sidebar.slider(
    "Full-year 2026 projection (t)",
    min_value=50, max_value=400, value=212, step=5,
)
ytd_2026 = st.sidebar.slider(
    "YTD Aug 2026 harvest (t)",
    min_value=0, max_value=200, value=93, step=1,
)
cages = st.sidebar.slider("Cages in operation", 1, 40, 10)

st.sidebar.markdown("---")
st.sidebar.subheader("Chart Options")
show_forecast  = st.sidebar.checkbox("Show 2026 projection", value=True)
show_rolling   = st.sidebar.checkbox("Show 3-yr rolling avg", value=True)
log_scale      = st.sidebar.checkbox("Log scale (y-axis)", value=False)

# ------------------------------------------------------------------
# HEADER + KPI ROW
# ------------------------------------------------------------------
st.title("🐟 Aqua Harvest Dashboard")
st.caption("Historical production 2012–2025 · Forecast & plan for 2026")

col1, col2, col3, col4 = st.columns(4)

peak_val  = history["AQUA_HARVEST"].max()
peak_year = int(history.loc[history["AQUA_HARVEST"].idxmax(), "YEAR"])
last_val  = history["AQUA_HARVEST"].iloc[-1]

col1.metric("Peak harvest",  f"{peak_val:,.0f} t", f"{peak_year}")
col2.metric("2025 actual",   f"{last_val:,.1f} t",
            f"{last_val - history['AQUA_HARVEST'].iloc[-2]:+.1f} t YoY")
col3.metric("2026 YTD (Aug)", f"{ytd_2026:,.0f} t",
            f"{ytd_2026 / YTD_MONTHS:.1f} t/month")
col4.metric("2026 projection", f"{projected_2026:,.0f} t",
            f"{projected_2026 - last_val:+.1f} t vs 2025")

st.markdown("---")

# ------------------------------------------------------------------
# CHART 1 — MAIN TREND (bar + line overlay)
# ------------------------------------------------------------------
st.subheader("📈 Production Trend")

df_plot = history.copy()
if show_forecast:
    df_plot.loc[len(df_plot)] = {"YEAR": 2026,
                                 "AQUA_HARVEST": projected_2026}

fig1 = go.Figure()

# Bars for actual
hist_mask = df_plot["YEAR"] <= 2025
fig1.add_trace(go.Bar(
    x=df_plot.loc[hist_mask, "YEAR"],
    y=df_plot.loc[hist_mask, "AQUA_HARVEST"],
    name="Actual harvest",
    marker_color="#4C9F70",
    text=[f"{v:,.0f}" for v in df_plot.loc[hist_mask, "AQUA_HARVEST"]],
    textposition="outside",
))

# Projected bar
if show_forecast:
    fig1.add_trace(go.Bar(
        x=[2026], y=[projected_2026],
        name="2026 projection",
        marker_color="#E4572E",
        marker_pattern_shape="/",
        text=[f"{projected_2026:,.0f}"],
        textposition="outside",
    ))
    # YTD marker
    fig1.add_trace(go.Scatter(
        x=[2026], y=[ytd_2026],
        mode="markers+text",
        marker=dict(symbol="diamond", size=14, color="#1B4965"),
        text=[f"YTD: {ytd_2026:.0f} t"],
        textposition="bottom center",
        name="YTD Aug 2026",
    ))

# Rolling average
if show_rolling:
    rolling = history.set_index("YEAR")["AQUA_HARVEST"] \
                     .rolling(3, center=True).mean()
    fig1.add_trace(go.Scatter(
        x=history["YEAR"], y=rolling,
        mode="lines+markers",
        name="3-yr rolling avg",
        line=dict(color="#8FB8DE", width=2, dash="dot"),
        marker=dict(size=6),
    ))

fig1.update_layout(
    height=460,
    xaxis_title="Year",
    yaxis_title="Harvest (tonnes)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1),
    bargap=0.25,
)
if log_scale:
    fig1.update_yaxes(type="log")

st.plotly_chart(fig1, use_container_width=True)

# ------------------------------------------------------------------
# ROW: SCENARIO CHART + COMPOSITION
# ------------------------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    st.subheader("🎯 2026 Scenarios")
    last_year = history["AQUA_HARVEST"].iloc[-1]
    prev_year = history["AQUA_HARVEST"].iloc[-2]
    scenarios = {
        "Naive (carry-forward)":     last_year,
        "Linear (2024→2025 trend)":  last_year + (last_year - prev_year),
        "YTD extrapolation":         ytd_2026 / YTD_MONTHS * 12,
        "Operational plan":          projected_2026,
    }
    sdf = pd.DataFrame({
        "Scenario": list(scenarios.keys()),
        "Tonnes":   list(scenarios.values()),
    })
    color_map = {
        "Naive (carry-forward)":    "#B0B0B0",
        "Linear (2024→2025 trend)": "#8FB8DE",
        "YTD extrapolation":        "#4C9F70",
        "Operational plan":         "#E4572E",
    }
    fig2 = px.bar(
        sdf, x="Tonnes", y="Scenario", orientation="h",
        color="Scenario", color_discrete_map=color_map,
        text="Tonnes",
    )
    fig2.update_traces(texttemplate="%{text:.1f} t",
                       textposition="outside")
    fig2.update_layout(height=340, showlegend=False,
                       margin=dict(l=10, r=40, t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

with c2:
    st.subheader("📊 Monthly Pace Required")
    avg_monthly   = ytd_2026 / YTD_MONTHS
    remaining     = 12 - YTD_MONTHS
    needed_pace   = (projected_2026 - ytd_2026) / remaining

    pace_df = pd.DataFrame({
        "Metric": ["Current pace (Jan–Aug)",
                   "Required pace (Sep–Dec)"],
        "t/month": [avg_monthly, needed_pace],
    })
    fig3 = go.Figure(go.Bar(
        x=pace_df["Metric"], y=pace_df["t/month"],
        marker_color=["#4C9F70", "#E4572E"],
        text=[f"{v:.1f} t/mo" for v in pace_df["t/month"]],
        textposition="outside",
    ))
    fig3.update_layout(height=340, yaxis_title="Tonnes / month",
                       margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig3, use_container_width=True)

# ------------------------------------------------------------------
# CHART — YEAR-OVER-YEAR CHANGE
# ------------------------------------------------------------------
st.subheader("📉 Year-over-Year Change")

yoy = history.copy()
yoy["YoY_%"] = yoy["AQUA_HARVEST"].pct_change() * 100
yoy = yoy.dropna()

colors = ["#E4572E" if v < 0 else "#4C9F70" for v in yoy["YoY_%"]]
fig4 = go.Figure(go.Bar(
    x=yoy["YEAR"], y=yoy["YoY_%"],
    marker_color=colors,
    text=[f"{v:+.0f}%" for v in yoy["YoY_%"]],
    textposition="outside",
))
fig4.add_hline(y=0, line_dash="dash", line_color="grey")
fig4.update_layout(height=360, xaxis_title="Year",
                   yaxis_title="YoY change (%)",
                   margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig4, use_container_width=True)

# ------------------------------------------------------------------
# DATA TABLE + DOWNLOAD
# ------------------------------------------------------------------
st.subheader("📋 Data Table")
table = history.copy()
if show_forecast:
    table.loc[len(table)] = {"YEAR": 2026, "AQUA_HARVEST": projected_2026}
table["Note"] = ""
table.loc[table["YEAR"] == 2023, "Note"] = "⚠️ Crash year"
table.loc[table["YEAR"] == 2018, "Note"] = "🏆 Peak year"
table.loc[table["YEAR"] == 2026, "Note"] = "🔮 Projection"

st.dataframe(table, use_container_width=True, hide_index=True)

st.download_button(
    "⬇️ Download CSV",
    data=table.to_csv(index=False).encode("utf-8"),
    file_name="aqua_harvest_2012_2026.csv",
    mime="text/csv",
)

st.markdown("---")
st.caption("Built with Streamlit · Plotly · Pandas")