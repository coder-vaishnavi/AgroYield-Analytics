"""
AgroYield Analytics
Indian Crop Yield & Climate Impact Intelligence Dashboard
Author: Vaishnavi
Program: IBM SkillsBuild Data Analytics with AI Academic Internship Program
"""

import os
import glob
import warnings
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AgroYield Analytics",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* Main background */
.main { background-color: #f8f9fa; }
/* KPI card */
.kpi-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-left: 4px solid #1e3a5f;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.kpi-value { font-size: 1.7rem; font-weight: 700; color: #1e3a5f; margin: 0; }
.kpi-label { font-size: 0.82rem; color: #57606a; margin: 0; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-delta { font-size: 0.8rem; color: #28a745; margin: 0; }
/* Section headings */
.section-header {
    font-size: 1.1rem; font-weight: 700;
    color: #1e3a5f;
    border-bottom: 2px solid #e07b22;
    padding-bottom: 4px; margin-bottom: 12px; margin-top: 20px;
}
/* Risk / Opportunity / Action cards */
.risk-card {
    background: #fff5f5; border: 1px solid #f5c6c6;
    border-left: 4px solid #dc3545;
    border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;
}
.opp-card {
    background: #f0fff4; border: 1px solid #b2dfdb;
    border-left: 4px solid #28a745;
    border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;
}
.action-card {
    background: #f0f4ff; border: 1px solid #c3cfe2;
    border-left: 4px solid #3b5bdb;
    border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;
}
.insight-card {
    background: #fffbea; border: 1px solid #f6e05e;
    border-left: 4px solid #e07b22;
    border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;
}
.badge-risk   { color: #dc3545; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; }
.badge-opp    { color: #28a745; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; }
.badge-action { color: #3b5bdb; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; }
.badge-insight{ color: #e07b22; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; }
/* Sidebar title */
.sidebar-title { font-size: 1.1rem; font-weight: 800; color: #1e3a5f; letter-spacing: 0.08em; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPER – KPI CARD
# ─────────────────────────────────────────────
def kpi_card(label, value, delta=None):
    delta_html = f'<p class="kpi-delta">{delta}</p>' if delta else ""
    st.markdown(
        f'<div class="kpi-card">'
        f'<p class="kpi-label">{label}</p>'
        f'<p class="kpi-value">{value}</p>'
        f'{delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

def section_header(text):
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)

def risk_card(title, body):
    st.markdown(
        f'<div class="risk-card"><span class="badge-risk">⚠ Potential Risk Indicator</span>'
        f'<br><strong>{title}</strong><br><small>{body}</small></div>',
        unsafe_allow_html=True,
    )

def opp_card(title, body):
    st.markdown(
        f'<div class="opp-card"><span class="badge-opp">✔ Opportunity</span>'
        f'<br><strong>{title}</strong><br><small>{body}</small></div>',
        unsafe_allow_html=True,
    )

def action_card(title, body):
    st.markdown(
        f'<div class="action-card"><span class="badge-action">→ Recommended Action</span>'
        f'<br><strong>{title}</strong><br><small>{body}</small></div>',
        unsafe_allow_html=True,
    )

def insight_card(title, body):
    st.markdown(
        f'<div class="insight-card"><span class="badge-insight">💡 Insight</span>'
        f'<br><strong>{title}</strong><br><small>{body}</small></div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# DATA LOADING & PROCESSING
# ─────────────────────────────────────────────

CROPS_DIR = os.path.join("data", "Crops")
RAINFALL_PATH = os.path.join("data", "rainfall.csv")
TEMPERATURE_PATH = os.path.join("data", "temperature.csv")
MASTER_PATH = os.path.join("data", "agroyield_master.csv")


@st.cache_data(show_spinner=False)
def load_single_crop(filepath: str) -> pd.DataFrame:
    """Load one crop CSV, extract crop name, return long-form DataFrame."""
    try:
        df = pd.read_csv(filepath, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(filepath, encoding="latin-1")

    # Standardise column names
    df.columns = [c.strip() for c in df.columns]
    rename_map = {}
    for col in df.columns:
        cl = col.lower()
        if "element" in cl and "code" not in cl:
            rename_map[col] = "Element"
        elif "item" in cl and "code" not in cl and "fao" not in cl.lower():
            rename_map[col] = "Item"
        elif col.lower() in ("year",) or ("year" in cl and "code" not in cl):
            rename_map[col] = "Year"
        elif col.lower() == "unit":
            rename_map[col] = "Unit"
        elif col.lower() == "value":
            rename_map[col] = "Value"
    df.rename(columns=rename_map, inplace=True)

    # Keep only required columns (flexible fallback)
    required = ["Element", "Year", "Value", "Unit"]
    for r in required:
        if r not in df.columns:
            return pd.DataFrame()

    # Derive crop name from Item column or filename
    if "Item" in df.columns:
        crop_name = df["Item"].dropna().iloc[0] if not df["Item"].dropna().empty else \
                    os.path.splitext(os.path.basename(filepath))[0].title()
    else:
        crop_name = os.path.splitext(os.path.basename(filepath))[0].title()

    df = df[required + ["Item"] if "Item" in df.columns else required].copy()
    df["Crop"] = crop_name
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_all_crops() -> pd.DataFrame:
    """Automatically discover and load all crop CSVs from CROPS_DIR."""
    pattern = os.path.join(CROPS_DIR, "*.csv")
    files = glob.glob(pattern)
    if not files:
        return pd.DataFrame()

    frames = []
    for fp in sorted(files):
        f = load_single_crop(fp)
        if not f.empty:
            frames.append(f)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)

    # Normalise Element values
    combined["Element"] = combined["Element"].str.strip()
    element_map = {
        "Area harvested": "Area harvested",
        "Production":     "Production",
        "Yield":          "Yield",
    }
    combined = combined[combined["Element"].isin(element_map.keys())].copy()
    combined["Element"] = combined["Element"].map(element_map)
    return combined


@st.cache_data(show_spinner=False)
def pivot_crop_data(long_df: pd.DataFrame) -> pd.DataFrame:
    """Pivot long-form crop data into wide-form: one row per (Crop, Year)."""
    if long_df.empty:
        return pd.DataFrame()

    # Aggregate duplicates (some crops may have multiple entries per year/element)
    agg = long_df.groupby(["Crop", "Year", "Element"])["Value"].mean().reset_index()

    wide = agg.pivot_table(index=["Crop", "Year"], columns="Element", values="Value").reset_index()
    wide.columns.name = None

    # Rename to clean column names
    col_map = {
        "Area harvested": "Area_Harvested",
        "Production":     "Production",
        "Yield":          "Yield_hg_per_ha",
    }
    wide.rename(columns=col_map, inplace=True)

    # Convert Yield from hg/ha to tonnes/ha
    if "Yield_hg_per_ha" in wide.columns:
        wide["Yield"] = wide["Yield_hg_per_ha"] / 10000
    else:
        wide["Yield"] = np.nan

    # Ensure year is integer
    wide["Year"] = wide["Year"].astype(int)
    wide = wide.sort_values(["Crop", "Year"]).reset_index(drop=True)
    return wide


@st.cache_data(show_spinner=False)
def load_rainfall() -> pd.DataFrame:
    """Load rainfall.csv and standardise column names."""
    try:
        df = pd.read_csv(RAINFALL_PATH, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(RAINFALL_PATH, encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    # Rename YEAR column
    for col in df.columns:
        if col.upper() == "YEAR":
            df.rename(columns={col: "Year"}, inplace=True)
            break
    if "ANN" in df.columns:
        df.rename(columns={"ANN": "Annual_Rainfall"}, inplace=True)
    elif "ANNUAL" in df.columns:
        df.rename(columns={"ANNUAL": "Annual_Rainfall"}, inplace=True)
    # Seasonal rainfall columns
    seasonal_map = {
        "Jan-Feb":  "RF_Jan_Feb",
        "Mar-May":  "RF_Mar_May",
        "Jun-Sep":  "RF_Jun_Sep",
        "Oct-Dec":  "RF_Oct_Dec",
        "JAN-FEB":  "RF_Jan_Feb",
        "MAR-MAY":  "RF_Mar_May",
        "JUN-SEP":  "RF_Jun_Sep",
        "OCT-DEC":  "RF_Oct_Dec",
    }
    df.rename(columns={k: v for k, v in seasonal_map.items() if k in df.columns}, inplace=True)

    # Monthly columns (JAN–DEC)
    month_map = {
        "JAN": "RF_Jan", "FEB": "RF_Feb", "MAR": "RF_Mar",
        "APR": "RF_Apr", "MAY": "RF_May", "JUN": "RF_Jun",
        "JUL": "RF_Jul", "AUG": "RF_Aug", "SEP": "RF_Sep",
        "OCT": "RF_Oct", "NOV": "RF_Nov", "DEC": "RF_Dec",
    }
    df.rename(columns={k: v for k, v in month_map.items() if k in df.columns}, inplace=True)

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["Year"])
    return df


@st.cache_data(show_spinner=False)
def load_temperature() -> pd.DataFrame:
    """Load temperature.csv and standardise column names."""
    try:
        df = pd.read_csv(TEMPERATURE_PATH, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(TEMPERATURE_PATH, encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    for col in df.columns:
        if col.upper() == "YEAR":
            df.rename(columns={col: "Year"}, inplace=True)
            break
    if "ANNUAL" in df.columns:
        df.rename(columns={"ANNUAL": "Annual_Temperature"}, inplace=True)
    seasonal_map = {
        "JAN-FEB":  "Temp_Jan_Feb",
        "MAR-MAY":  "Temp_Mar_May",
        "JUN-SEP":  "Temp_Jun_Sep",
        "OCT-DEC":  "Temp_Oct_Dec",
    }
    df.rename(columns={k: v for k, v in seasonal_map.items() if k in df.columns}, inplace=True)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["Year"])
    return df


@st.cache_data(show_spinner=False)
def build_master(crop_wide: pd.DataFrame, rainfall: pd.DataFrame, temperature: pd.DataFrame) -> pd.DataFrame:
    """Merge crop data with rainfall and temperature on Year."""
    if crop_wide.empty:
        return pd.DataFrame()
    master = crop_wide.copy()
    master["Year"] = master["Year"].astype(int)

    if not rainfall.empty:
        rain = rainfall.copy()
        rain["Year"] = rain["Year"].astype(int)
        master = master.merge(rain, on="Year", how="left")

    if not temperature.empty:
        temp = temperature.copy()
        temp["Year"] = temp["Year"].astype(int)
        master = master.merge(temp, on="Year", how="left")

    # Save master CSV
    try:
        master.to_csv(MASTER_PATH, index=False)
    except Exception:
        pass
    return master


# ─────────────────────────────────────────────
# LOAD DATA (cached at startup)
# ─────────────────────────────────────────────
with st.spinner("Loading AgroYield Analytics data…"):
    _long      = load_all_crops()
    _crop_wide = pivot_crop_data(_long)
    _rainfall  = load_rainfall()
    _temp      = load_temperature()
    _master    = build_master(_crop_wide, _rainfall, _temp)

DATA_OK = not _master.empty


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="sidebar-title">🌾 AGROYIELD ANALYTICS</p>', unsafe_allow_html=True)
    st.caption("Indian Crop Yield & Climate Impact Intelligence")
    st.divider()

    page = st.radio(
        "Navigation",
        [
            "1 · Executive Overview",
            "2 · Crop Analysis",
            "3 · Climate Analysis",
            "4 · Yield & Climate Drivers",
            "5 · Risk • Opportunity • Action",
            "6 · Data Explorer",
            "7 · Methodology",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("**Filters**")

    all_years = sorted(_master["Year"].dropna().unique().tolist()) if DATA_OK else [1961, 2018]
    year_min, year_max = int(min(all_years)), int(max(all_years))
    year_range = st.slider("Year Range", year_min, year_max, (year_min, year_max))

    all_crops = sorted(_master["Crop"].dropna().unique().tolist()) if DATA_OK else []
    selected_crops = st.multiselect("Crop(s)", all_crops, default=all_crops[:5] if len(all_crops) >= 5 else all_crops)

    metric_options = ["Production", "Yield", "Area_Harvested"]
    selected_metric = st.selectbox("Primary Metric", metric_options)

    st.divider()
    st.caption("IBM SkillsBuild · BharatCares × AICTE · Vaishnavi")


# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────
def get_filtered(df: pd.DataFrame, crops=None, yr_range=None) -> pd.DataFrame:
    """Return dataframe filtered by year range and optional crop list."""
    if df.empty:
        return df
    out = df.copy()
    if yr_range:
        out = out[(out["Year"] >= yr_range[0]) & (out["Year"] <= yr_range[1])]
    if crops:
        out = out[out["Crop"].isin(crops)]
    return out


filt_master = get_filtered(_master, selected_crops, year_range) if DATA_OK else pd.DataFrame()
all_filt    = get_filtered(_master, None, year_range) if DATA_OK else pd.DataFrame()


# ─────────────────────────────────────────────
# CHART THEME
# ─────────────────────────────────────────────
COLORS = px.colors.qualitative.Bold
PLOTLY_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="#f8f9fa",
    font=dict(family="Segoe UI, system-ui, sans-serif", size=12, color="#1f2328"),
    title_font=dict(size=14, color="#1e3a5f", family="Segoe UI, system-ui, sans-serif"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=20, t=50, b=40),
)

def apply_theme(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_xaxes(gridcolor="#e5e7eb", zeroline=False)
    fig.update_yaxes(gridcolor="#e5e7eb", zeroline=False)
    return fig


# ─────────────────────────────────────────────
# UTILITY ANALYTICS
# ─────────────────────────────────────────────
def safe_pct_change(series: pd.Series) -> float:
    """Compute first-to-last percentage change, guarding division by zero."""
    s = series.dropna()
    if len(s) < 2 or s.iloc[0] == 0:
        return np.nan
    return ((s.iloc[-1] - s.iloc[0]) / abs(s.iloc[0])) * 100

def cv(series: pd.Series) -> float:
    """Coefficient of variation (%)."""
    s = series.dropna()
    if len(s) < 2 or s.mean() == 0:
        return np.nan
    return (s.std() / s.mean()) * 100

def trend_slope(series: pd.Series, years: pd.Series) -> float:
    """Simple linear regression slope using numpy polyfit."""
    s = series.dropna()
    y = years[series.notna()]
    if len(s) < 3:
        return np.nan
    try:
        slope, _ = np.polyfit(y, s, 1)
        return slope
    except Exception:
        return np.nan


# ══════════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE OVERVIEW
# ══════════════════════════════════════════════════════════════════
def page_executive_overview():
    st.title("🌾 AgroYield Analytics")
    st.markdown(
        "<h4 style='color:#57606a;margin-top:-12px;'>Indian Crop Yield & Climate Impact Intelligence</h4>",
        unsafe_allow_html=True,
    )
    st.caption(f"Data period: {year_range[0]}–{year_range[1]}  |  Crops selected: {len(selected_crops)}")

    if not DATA_OK or all_filt.empty:
        st.warning("No data available. Please check the data directory.")
        return

    # ── KPIs ──────────────────────────────────────────────────────
    section_header("What Is Happening? — Key Performance Indicators")
    k1, k2, k3, k4, k5, k6 = st.columns(6)

    total_prod  = all_filt["Production"].sum(skipna=True)
    avg_yield   = all_filt["Yield"].mean(skipna=True)
    total_area  = all_filt["Area_Harvested"].sum(skipna=True)
    n_crops     = all_filt["Crop"].nunique()
    avg_rain    = all_filt["Annual_Rainfall"].mean(skipna=True) if "Annual_Rainfall" in all_filt.columns else np.nan
    avg_temp    = all_filt["Annual_Temperature"].mean(skipna=True) if "Annual_Temperature" in all_filt.columns else np.nan

    def fmt_large(v):
        if np.isnan(v): return "N/A"
        if v >= 1e12:  return f"{v/1e12:.2f} T"
        if v >= 1e9:   return f"{v/1e9:.2f} B"
        if v >= 1e6:   return f"{v/1e6:.2f} M"
        return f"{v:,.0f}"

    with k1: kpi_card("Total Production (tonnes)", fmt_large(total_prod))
    with k2: kpi_card("Avg Yield (t/ha)", f"{avg_yield:.3f}" if not np.isnan(avg_yield) else "N/A")
    with k3: kpi_card("Total Area Harvested (ha)", fmt_large(total_area))
    with k4: kpi_card("Crop Types", str(n_crops))
    with k5: kpi_card("Avg Annual Rainfall (mm)", f"{avg_rain:.0f}" if not np.isnan(avg_rain) else "N/A")
    with k6: kpi_card("Avg Annual Temp (°C)", f"{avg_temp:.1f}" if not np.isnan(avg_temp) else "N/A")

    # ── Production Trend ──────────────────────────────────────────
    section_header("Production & Yield Trends")
    trend_df = all_filt.groupby("Year").agg(
        Total_Production=("Production", "sum"),
        Avg_Yield=("Yield", "mean"),
        Total_Area=("Area_Harvested", "sum"),
    ).reset_index()

    c1, c2 = st.columns(2)
    with c1:
        fig = px.area(trend_df, x="Year", y="Total_Production",
                      title="Total Agricultural Production (tonnes) Over Time",
                      labels={"Total_Production": "Production (tonnes)", "Year": "Year"})
        fig.update_traces(fillcolor="rgba(30,58,95,0.15)", line_color="#1e3a5f")
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    with c2:
        fig2 = px.line(trend_df, x="Year", y="Avg_Yield",
                       title="Average Crop Yield (t/ha) Over Time",
                       labels={"Avg_Yield": "Avg Yield (t/ha)", "Year": "Year"})
        fig2.update_traces(line_color="#e07b22", line_width=2.5)
        st.plotly_chart(apply_theme(fig2), use_container_width=True)

    fig3 = px.bar(trend_df, x="Year", y="Total_Area",
                  title="Total Area Harvested (ha) Over Time",
                  labels={"Total_Area": "Area (ha)", "Year": "Year"})
    fig3.update_traces(marker_color="#3b5bdb", opacity=0.75)
    st.plotly_chart(apply_theme(fig3), use_container_width=True)

    # ── Top Performers ─────────────────────────────────────────────
    section_header("Top Performers")
    crop_summary = all_filt.groupby("Crop").agg(
        Total_Production=("Production", "sum"),
        Avg_Yield=("Yield", "mean"),
        Total_Area=("Area_Harvested", "sum"),
    ).dropna(subset=["Total_Production"]).sort_values("Total_Production", ascending=False).reset_index()

    c1, c2, c3 = st.columns(3)
    with c1:
        top_prod = crop_summary.head(10)
        fig = px.bar(top_prod, x="Total_Production", y="Crop", orientation="h",
                     title="Top 10 Crops by Production",
                     labels={"Total_Production": "Production (tonnes)", "Crop": ""})
        fig.update_traces(marker_color="#1e3a5f")
        fig.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    with c2:
        top_yield = crop_summary.dropna(subset=["Avg_Yield"]).sort_values("Avg_Yield", ascending=False).head(10)
        fig = px.bar(top_yield, x="Avg_Yield", y="Crop", orientation="h",
                     title="Top 10 Crops by Average Yield (t/ha)",
                     labels={"Avg_Yield": "Avg Yield (t/ha)", "Crop": ""})
        fig.update_traces(marker_color="#e07b22")
        fig.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    with c3:
        # Growth rate per crop
        growth_rows = []
        for crop, grp in all_filt.groupby("Crop"):
            pct = safe_pct_change(grp.sort_values("Year")["Production"])
            if not np.isnan(pct):
                growth_rows.append({"Crop": crop, "Growth_pct": pct})
        if growth_rows:
            growth_df = pd.DataFrame(growth_rows).sort_values("Growth_pct", ascending=False).head(10)
            fig = px.bar(growth_df, x="Growth_pct", y="Crop", orientation="h",
                         title="Top 10 Crops by Production Growth (%)",
                         labels={"Growth_pct": "Growth (%)", "Crop": ""})
            fig.update_traces(marker_color="#28a745")
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(apply_theme(fig), use_container_width=True)

    # ── Key Insights ──────────────────────────────────────────────
    section_header("Key Insights")
    # Derive insights dynamically
    top_crop_name = crop_summary["Crop"].iloc[0] if not crop_summary.empty else "N/A"
    top_crop_prod = crop_summary["Total_Production"].iloc[0] if not crop_summary.empty else 0

    slope_prod = trend_slope(trend_df["Total_Production"], trend_df["Year"])
    slope_yield = trend_slope(trend_df["Avg_Yield"], trend_df["Year"])

    rain_cv_val = cv(_rainfall["Annual_Rainfall"]) if not _rainfall.empty and "Annual_Rainfall" in _rainfall.columns else np.nan
    temp_trend  = trend_slope(_temp["Annual_Temperature"], _temp["Year"]) if not _temp.empty and "Annual_Temperature" in _temp.columns else np.nan

    i1, i2 = st.columns(2)
    with i1:
        insight_card(
            f"{top_crop_name} is the dominant production crop",
            f"Cumulative production of {fmt_large(top_crop_prod)} tonnes over {year_range[0]}–{year_range[1]}."
        )
        direction = "upward" if (not np.isnan(slope_prod) and slope_prod > 0) else "downward"
        insight_card(
            f"Overall production shows an {direction} historical trend",
            f"Linear trend slope: {slope_prod:,.0f} tonnes/year." if not np.isnan(slope_prod) else "Insufficient data."
        )
    with i2:
        if not np.isnan(slope_yield):
            yd = "improving" if slope_yield > 0 else "declining"
            insight_card(
                f"Average crop yield is historically {yd}",
                f"Trend slope: {slope_yield:.5f} t/ha per year across the selected period."
            )
        if not np.isnan(rain_cv_val):
            insight_card(
                "Rainfall variability is analytically notable",
                f"Coefficient of variation of annual rainfall: {rain_cv_val:.1f}%. High variability may be associated with year-to-year yield fluctuations."
            )


# ══════════════════════════════════════════════════════════════════
# PAGE 2 — CROP ANALYSIS
# ══════════════════════════════════════════════════════════════════
def page_crop_analysis():
    st.title("🌿 Crop & Production Analysis")
    st.caption("Understanding agricultural production and crop productivity trends across India.")

    if not DATA_OK or filt_master.empty:
        st.warning("No data available for selected filters.")
        return

    # ── Crop summary table ─────────────────────────────────────────
    section_header("Crop Comparison Table")
    rows = []
    for crop, grp in filt_master.groupby("Crop"):
        grp_s = grp.sort_values("Year")
        rows.append({
            "Crop":           crop,
            "Total Production (t)":  grp_s["Production"].sum(skipna=True),
            "Avg Yield (t/ha)":      grp_s["Yield"].mean(skipna=True),
            "Avg Area (ha)":         grp_s["Area_Harvested"].mean(skipna=True),
            "Production Growth (%)": safe_pct_change(grp_s["Production"]),
            "Yield Growth (%)":      safe_pct_change(grp_s["Yield"]),
        })
    summary_df = pd.DataFrame(rows)
    if not summary_df.empty:
        summary_df = summary_df.sort_values("Total Production (t)", ascending=False)
        # Categorical tags
        median_yield = summary_df["Avg Yield (t/ha)"].median()
        def categorise(row):
            pg = row.get("Production Growth (%)", np.nan)
            yg = row.get("Yield Growth (%)", np.nan)
            y  = row.get("Avg Yield (t/ha)", np.nan)
            if not np.isnan(yg) and yg > 20:
                return "Growing Productivity"
            if not np.isnan(yg) and yg < -20:
                return "Declining Productivity"
            if not np.isnan(y) and y > median_yield:
                return "High Yield"
            return "Stable / Mixed"
        summary_df["Category"] = summary_df.apply(categorise, axis=1)
        for col in ["Total Production (t)", "Avg Yield (t/ha)", "Avg Area (ha)", "Production Growth (%)", "Yield Growth (%)"]:
            summary_df[col] = summary_df[col].round(2)
        st.dataframe(summary_df, use_container_width=True, height=300)

    # ── Charts ─────────────────────────────────────────────────────
    section_header("Production by Crop")
    prod_by_crop = filt_master.groupby("Crop")["Production"].sum().dropna().sort_values(ascending=False).reset_index()
    fig = px.bar(prod_by_crop, x="Crop", y="Production",
                 title="Total Production by Crop",
                 labels={"Production": "Production (tonnes)", "Crop": "Crop"},
                 color="Production", color_continuous_scale="Blues")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(apply_theme(fig), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        yield_by_crop = filt_master.groupby("Crop")["Yield"].mean().dropna().sort_values(ascending=False).reset_index()
        fig = px.bar(yield_by_crop, x="Yield", y="Crop", orientation="h",
                     title="Average Yield by Crop (t/ha)",
                     labels={"Yield": "Avg Yield (t/ha)", "Crop": ""},
                     color="Yield", color_continuous_scale="Oranges")
        fig.update_layout(height=500, yaxis=dict(autorange="reversed"))
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    with c2:
        area_by_crop = filt_master.groupby("Crop")["Area_Harvested"].mean().dropna().sort_values(ascending=False).reset_index()
        fig = px.bar(area_by_crop, x="Area_Harvested", y="Crop", orientation="h",
                     title="Average Area Harvested by Crop (ha)",
                     labels={"Area_Harvested": "Avg Area (ha)", "Crop": ""},
                     color="Area_Harvested", color_continuous_scale="Greens")
        fig.update_layout(height=500, yaxis=dict(autorange="reversed"))
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    # ── Trend Lines ────────────────────────────────────────────────
    section_header("Production & Yield Trends (Selected Crops)")
    if not filt_master.empty:
        prod_trend = filt_master.groupby(["Year", "Crop"])["Production"].sum().reset_index()
        fig = px.line(prod_trend, x="Year", y="Production", color="Crop",
                      title="Production Trend by Crop Over Time",
                      labels={"Production": "Production (tonnes)"})
        st.plotly_chart(apply_theme(fig), use_container_width=True)

        yield_trend = filt_master.groupby(["Year", "Crop"])["Yield"].mean().reset_index()
        fig = px.line(yield_trend, x="Year", y="Yield", color="Crop",
                      title="Yield Trend by Crop Over Time (t/ha)",
                      labels={"Yield": "Yield (t/ha)"})
        st.plotly_chart(apply_theme(fig), use_container_width=True)

    # ── Category Breakdown ─────────────────────────────────────────
    if not summary_df.empty and "Category" in summary_df.columns:
        section_header("Analytical Category Breakdown")
        cat_counts = summary_df["Category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        cat_color_map = {
            "Growing Productivity": "#28a745",
            "Declining Productivity": "#dc3545",
            "High Yield": "#e07b22",
            "Stable / Mixed": "#3b5bdb",
        }
        fig = px.pie(cat_counts, names="Category", values="Count",
                     title="Crops by Analytical Category",
                     color="Category", color_discrete_map=cat_color_map)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(apply_theme(fig), use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 3 — CLIMATE ANALYSIS
# ══════════════════════════════════════════════════════════════════
def page_climate_analysis():
    st.title("🌦 Climate & Weather Analysis")
    st.caption("Historical rainfall and temperature patterns over India (1961–2018).")

    if _rainfall.empty and _temp.empty:
        st.warning("Climate data files not found.")
        return

    # Filter climate by year range
    def filt_climate(df):
        return df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]

    rain_f = filt_climate(_rainfall) if not _rainfall.empty else pd.DataFrame()
    temp_f = filt_climate(_temp)     if not _temp.empty     else pd.DataFrame()

    # ── KPIs ──────────────────────────────────────────────────────
    section_header("Climate KPIs")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    if not rain_f.empty and "Annual_Rainfall" in rain_f.columns:
        rf = rain_f["Annual_Rainfall"].dropna()
        max_rf_yr = int(rain_f.loc[rain_f["Annual_Rainfall"].idxmax(), "Year"])
        min_rf_yr = int(rain_f.loc[rain_f["Annual_Rainfall"].idxmin(), "Year"])
        with c1: kpi_card("Avg Annual Rainfall", f"{rf.mean():.0f} mm")
        with c2: kpi_card("Highest Rainfall Year", f"{max_rf_yr} ({rf.max():.0f} mm)")
        with c3: kpi_card("Lowest Rainfall Year",  f"{min_rf_yr} ({rf.min():.0f} mm)")
        with c4: kpi_card("Rainfall Variability (CV)", f"{cv(rf):.1f}%")
    if not temp_f.empty and "Annual_Temperature" in temp_f.columns:
        tp = temp_f["Annual_Temperature"].dropna()
        max_tp_yr = int(temp_f.loc[temp_f["Annual_Temperature"].idxmax(), "Year"])
        min_tp_yr = int(temp_f.loc[temp_f["Annual_Temperature"].idxmin(), "Year"])
        with c5: kpi_card("Highest Temp Year", f"{max_tp_yr} ({tp.max():.2f} °C)")
        with c6: kpi_card("Avg Annual Temp", f"{tp.mean():.2f} °C")

    # ── Annual Rainfall Trend ──────────────────────────────────────
    if not rain_f.empty and "Annual_Rainfall" in rain_f.columns:
        section_header("Annual Rainfall Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=rain_f["Year"], y=rain_f["Annual_Rainfall"],
                                 mode="lines+markers", name="Annual Rainfall",
                                 line=dict(color="#1e3a5f", width=2),
                                 marker=dict(size=4)))
        # Add 10-year rolling average
        roll = rain_f.set_index("Year")["Annual_Rainfall"].rolling(10, min_periods=5).mean().reset_index()
        fig.add_trace(go.Scatter(x=roll["Year"], y=roll["Annual_Rainfall"],
                                 mode="lines", name="10-Year Rolling Avg",
                                 line=dict(color="#e07b22", width=2, dash="dash")))
        fig.update_layout(title="Annual Rainfall (mm) with 10-Year Rolling Average",
                          xaxis_title="Year", yaxis_title="Rainfall (mm)")
        st.plotly_chart(apply_theme(fig), use_container_width=True)

        # Monthly rainfall bar chart (average over selected period)
        month_cols = [c for c in rain_f.columns if c.startswith("RF_") and not any(s in c for s in ["Jan_Feb", "Mar_May", "Jun_Sep", "Oct_Dec"])]
        if month_cols:
            section_header("Average Monthly Rainfall Distribution")
            monthly_avg = rain_f[month_cols].mean()
            month_labels = [c.replace("RF_", "") for c in month_cols]
            fig = px.bar(x=month_labels, y=monthly_avg.values,
                         labels={"x": "Month", "y": "Avg Rainfall (mm)"},
                         title="Average Monthly Rainfall Distribution")
            fig.update_traces(marker_color="#3b5bdb")
            st.plotly_chart(apply_theme(fig), use_container_width=True)

        # Seasonal rainfall
        seasonal_cols = [c for c in rain_f.columns if c in ("RF_Jan_Feb", "RF_Mar_May", "RF_Jun_Sep", "RF_Oct_Dec")]
        if seasonal_cols:
            section_header("Seasonal Rainfall Trends")
            sea_df = rain_f[["Year"] + seasonal_cols].melt("Year", var_name="Season", value_name="Rainfall")
            sea_df["Season"] = sea_df["Season"].str.replace("RF_", "").str.replace("_", "–")
            fig = px.line(sea_df, x="Year", y="Rainfall", color="Season",
                          title="Seasonal Rainfall Over Time",
                          labels={"Rainfall": "Rainfall (mm)"})
            st.plotly_chart(apply_theme(fig), use_container_width=True)

    # ── Temperature Trend ─────────────────────────────────────────
    if not temp_f.empty and "Annual_Temperature" in temp_f.columns:
        section_header("Annual Temperature Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=temp_f["Year"], y=temp_f["Annual_Temperature"],
                                 mode="lines+markers", name="Annual Temp",
                                 line=dict(color="#dc3545", width=2),
                                 marker=dict(size=4)))
        roll_t = temp_f.set_index("Year")["Annual_Temperature"].rolling(10, min_periods=5).mean().reset_index()
        fig.add_trace(go.Scatter(x=roll_t["Year"], y=roll_t["Annual_Temperature"],
                                 mode="lines", name="10-Year Rolling Avg",
                                 line=dict(color="#e07b22", width=2, dash="dash")))
        fig.update_layout(title="Annual Mean Temperature (°C) with 10-Year Rolling Average",
                          xaxis_title="Year", yaxis_title="Temperature (°C)")
        st.plotly_chart(apply_theme(fig), use_container_width=True)

        # Seasonal temperature
        temp_seasonal = [c for c in temp_f.columns if c in ("Temp_Jan_Feb", "Temp_Mar_May", "Temp_Jun_Sep", "Temp_Oct_Dec")]
        if temp_seasonal:
            section_header("Seasonal Temperature Trends")
            ts_df = temp_f[["Year"] + temp_seasonal].melt("Year", var_name="Season", value_name="Temperature")
            ts_df["Season"] = ts_df["Season"].str.replace("Temp_", "").str.replace("_", "–")
            fig = px.line(ts_df, x="Year", y="Temperature", color="Season",
                          title="Seasonal Mean Temperature (°C) Over Time",
                          labels={"Temperature": "Temperature (°C)"})
            st.plotly_chart(apply_theme(fig), use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 4 — YIELD & CLIMATE DRIVERS
# ══════════════════════════════════════════════════════════════════
def page_yield_climate_drivers():
    st.title("📊 Yield & Climate Drivers")
    st.markdown(
        "<p style='color:#57606a;'>This page explores <strong>historical associations</strong> between climate variables and crop yield. "
        "Correlation does not imply causation. All relationships are analytical indicators based on historical data.</p>",
        unsafe_allow_html=True,
    )

    if not DATA_OK or _master.empty:
        st.warning("No data available.")
        return

    # Crop selector for detailed view
    driver_crops = sorted(_master["Crop"].dropna().unique().tolist())
    sel_crop = st.selectbox("Select Crop for Detailed Analysis", driver_crops, key="driver_crop")

    crop_df = _master[_master["Crop"] == sel_crop].copy()
    crop_df = crop_df[(crop_df["Year"] >= year_range[0]) & (crop_df["Year"] <= year_range[1])]

    if crop_df.empty:
        st.warning(f"No data for {sel_crop} in the selected year range.")
        return

    has_rain  = "Annual_Rainfall" in crop_df.columns and crop_df["Annual_Rainfall"].notna().sum() > 5
    has_temp  = "Annual_Temperature" in crop_df.columns and crop_df["Annual_Temperature"].notna().sum() > 5

    # ── Correlation values ─────────────────────────────────────────
    corr_rain = corr_temp = np.nan
    if has_rain:
        valid = crop_df[["Yield", "Annual_Rainfall"]].dropna()
        if len(valid) >= 5:
            corr_rain = valid["Yield"].corr(valid["Annual_Rainfall"])
    if has_temp:
        valid = crop_df[["Yield", "Annual_Temperature"]].dropna()
        if len(valid) >= 5:
            corr_temp = valid["Yield"].corr(valid["Annual_Temperature"])

    section_header(f"Climate–Yield Association: {sel_crop}")
    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_card("Pearson Corr: Rainfall–Yield",
                       f"{corr_rain:.3f}" if not np.isnan(corr_rain) else "N/A")
    with k2: kpi_card("Pearson Corr: Temp–Yield",
                       f"{corr_temp:.3f}" if not np.isnan(corr_temp) else "N/A")
    with k3:
        avg_y = crop_df["Yield"].mean()
        kpi_card("Avg Yield (t/ha)", f"{avg_y:.3f}" if not np.isnan(avg_y) else "N/A")
    with k4:
        cv_y = cv(crop_df["Yield"])
        kpi_card("Yield Variability (CV %)", f"{cv_y:.1f}%" if not np.isnan(cv_y) else "N/A")

    # Interpret correlation
    def interpret_corr(r, var_name, crop):
        if np.isnan(r):
            return f"Insufficient data to calculate correlation between {var_name} and yield for {crop}."
        dir_str = "positive" if r > 0 else "negative"
        mag = abs(r)
        if mag > 0.5: strength = "moderate-to-strong"
        elif mag > 0.25: strength = "weak-to-moderate"
        else: strength = "weak"
        return (f"{crop} shows a {strength} {dir_str} historical association between {var_name} and yield "
                f"(r = {r:.3f}). This is an analytical indicator based on historical data and does not imply a causal relationship.")

    st.info(interpret_corr(corr_rain, "Annual Rainfall", sel_crop))
    st.info(interpret_corr(corr_temp, "Annual Temperature", sel_crop))

    c1, c2 = st.columns(2)
    if has_rain:
        with c1:
            fig = px.scatter(crop_df, x="Annual_Rainfall", y="Yield", trendline="ols",
                             title=f"Rainfall vs Yield: {sel_crop}",
                             labels={"Annual_Rainfall": "Annual Rainfall (mm)", "Yield": "Yield (t/ha)"},
                             hover_data=["Year"])
            fig.update_traces(marker_color="#1e3a5f", selector=dict(mode="markers"))
            fig.update_traces(line_color="#e07b22", selector=dict(mode="lines"))
            st.plotly_chart(apply_theme(fig), use_container_width=True)

    if has_temp:
        with c2:
            fig = px.scatter(crop_df, x="Annual_Temperature", y="Yield", trendline="ols",
                             title=f"Temperature vs Yield: {sel_crop}",
                             labels={"Annual_Temperature": "Annual Temperature (°C)", "Yield": "Yield (t/ha)"},
                             hover_data=["Year"])
            fig.update_traces(marker_color="#dc3545", selector=dict(mode="markers"))
            fig.update_traces(line_color="#3b5bdb", selector=dict(mode="lines"))
            st.plotly_chart(apply_theme(fig), use_container_width=True)

    # Combined time-series view
    section_header(f"Year-by-Year: Rainfall, Temperature, Yield — {sel_crop}")
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        subplot_titles=("Yield (t/ha)", "Annual Rainfall (mm)", "Annual Temperature (°C)"),
                        vertical_spacing=0.08)
    fig.add_trace(go.Scatter(x=crop_df["Year"], y=crop_df["Yield"],
                             mode="lines+markers", name="Yield", line=dict(color="#1e3a5f")), row=1, col=1)
    if has_rain:
        fig.add_trace(go.Scatter(x=crop_df["Year"], y=crop_df["Annual_Rainfall"],
                                 mode="lines", name="Rainfall", line=dict(color="#3b5bdb")), row=2, col=1)
    if has_temp:
        fig.add_trace(go.Scatter(x=crop_df["Year"], y=crop_df["Annual_Temperature"],
                                 mode="lines", name="Temperature", line=dict(color="#dc3545")), row=3, col=1)
    fig.update_layout(height=550, title_text=f"Yield–Climate Time Series: {sel_crop}",
                      **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("legend",)})
    st.plotly_chart(fig, use_container_width=True)

    # ── Correlation Matrix across selected crops ───────────────────
    section_header("Correlation Matrix — Selected Crops")
    corr_rows = []
    for crop in (selected_crops if selected_crops else driver_crops[:10]):
        cd = _master[(_master["Crop"] == crop) & (_master["Year"] >= year_range[0]) & (_master["Year"] <= year_range[1])]
        if cd.empty: continue
        row = {"Crop": crop}
        if "Annual_Rainfall" in cd.columns:
            v = cd[["Yield", "Annual_Rainfall"]].dropna()
            row["Corr_Rainfall_Yield"] = v["Yield"].corr(v["Annual_Rainfall"]) if len(v) >= 5 else np.nan
        if "Annual_Temperature" in cd.columns:
            v = cd[["Yield", "Annual_Temperature"]].dropna()
            row["Corr_Temp_Yield"] = v["Yield"].corr(v["Annual_Temperature"]) if len(v) >= 5 else np.nan
        corr_rows.append(row)

    if corr_rows:
        corr_df = pd.DataFrame(corr_rows).set_index("Crop")
        numeric_corr = corr_df.select_dtypes(include=[np.number])
        if not numeric_corr.empty:
            fig = px.imshow(numeric_corr, text_auto=".2f",
                            title="Correlation Heatmap: Climate Variables vs Yield by Crop",
                            color_continuous_scale="RdBu", zmin=-1, zmax=1,
                            labels={"color": "Pearson r"})
            fig.update_layout(height=max(300, 30 * len(corr_rows)))
            st.plotly_chart(apply_theme(fig), use_container_width=True)
        st.caption("Note: All correlations shown are historical associations. They do not imply causation.")


# ══════════════════════════════════════════════════════════════════
# PAGE 5 — RISK • OPPORTUNITY • ACTION
# ══════════════════════════════════════════════════════════════════
def page_risk_opportunity_action():
    st.title("⚠ Risk • ✔ Opportunity • → Action")
    st.caption("Data-driven analytical indicators derived from historical patterns — not predictions or guarantees.")

    if not DATA_OK or _master.empty:
        st.warning("No data available.")
        return

    # Compute crop-level stats across the full master dataset
    crop_stats = []
    for crop, grp in _master.groupby("Crop"):
        grp_s = grp.sort_values("Year")
        yield_series = grp_s["Yield"].dropna()
        prod_series  = grp_s["Production"].dropna()
        crop_stats.append({
            "Crop":            crop,
            "yield_cv":        cv(yield_series),
            "yield_slope":     trend_slope(yield_series, grp_s.loc[yield_series.index, "Year"]),
            "prod_pct":        safe_pct_change(prod_series),
            "yield_pct":       safe_pct_change(yield_series),
            "corr_rain":       yield_series.corr(grp_s.loc[yield_series.index, "Annual_Rainfall"]) if "Annual_Rainfall" in grp.columns and grp["Annual_Rainfall"].notna().sum() > 5 else np.nan,
        })
    stats_df = pd.DataFrame(crop_stats)

    # ── Single-crop detail ─────────────────────────────────────────
    roa_crops = sorted(_master["Crop"].dropna().unique().tolist())
    roa_crop = st.selectbox("Select Crop for Detailed Risk/Opportunity Analysis", roa_crops, key="roa_crop")
    row = stats_df[stats_df["Crop"] == roa_crop].iloc[0] if not stats_df[stats_df["Crop"] == roa_crop].empty else None

    tab_risk, tab_opp, tab_action = st.tabs(["⚠ Risk Indicators", "✔ Opportunities", "→ Actions"])

    with tab_risk:
        section_header(f"Potential Risk Indicators — {roa_crop}")
        risk_found = False
        if row is not None:
            if not np.isnan(row["yield_slope"]) and row["yield_slope"] < 0:
                risk_card("Declining Yield Trend",
                          f"Historical yield of {roa_crop} shows a negative trend slope ({row['yield_slope']:.5f} t/ha/year). Sustained decline may indicate agronomic or environmental stress.")
                risk_found = True
            if not np.isnan(row["yield_cv"]) and row["yield_cv"] > 25:
                risk_card("High Yield Variability",
                          f"Coefficient of variation of yield: {row['yield_cv']:.1f}%. Higher variability is historically associated with inconsistent production seasons.")
                risk_found = True
            if not np.isnan(row["prod_pct"]) and row["prod_pct"] < -20:
                risk_card("Significant Production Decline",
                          f"Production change over the selected period: {row['prod_pct']:.1f}%. This warrants further investigation into area, yield, and market factors.")
                risk_found = True
            if not np.isnan(row["corr_rain"]) and row["corr_rain"] < -0.3:
                risk_card("Negative Rainfall–Yield Association",
                          f"Historical correlation between rainfall and yield for {roa_crop}: {row['corr_rain']:.3f}. Higher rainfall is historically associated with lower yield. Possible flood/waterlogging effects or reverse causality.")
                risk_found = True
        # Rainfall variability
        if not _rainfall.empty and "Annual_Rainfall" in _rainfall.columns:
            rf_cv = cv(_rainfall["Annual_Rainfall"])
            if not np.isnan(rf_cv) and rf_cv > 10:
                risk_card("Rainfall Variability",
                          f"Annual rainfall coefficient of variation: {rf_cv:.1f}%. High inter-annual variability is a key analytical indicator of production uncertainty.")
                risk_found = True
        if not risk_found:
            st.success(f"No major risk indicators identified for {roa_crop} based on historical data patterns.")

        # Portfolio-level risks
        section_header("Portfolio-Level Risk Overview")
        declining = stats_df[stats_df["yield_slope"] < 0].shape[0]
        high_var  = stats_df[stats_df["yield_cv"]  > 25].shape[0]
        n_total   = len(stats_df)
        c1, c2, c3 = st.columns(3)
        with c1: kpi_card("Crops with Declining Yield Trend", f"{declining} / {n_total}")
        with c2: kpi_card("Crops with High Yield Variability (CV>25%)", f"{high_var} / {n_total}")
        with c3:
            declining_prod = stats_df[stats_df["prod_pct"] < -20].shape[0]
            kpi_card("Crops with Declining Production (>20%)", f"{declining_prod} / {n_total}")

    with tab_opp:
        section_header(f"Opportunities — {roa_crop}")
        opp_found = False
        if row is not None:
            if not np.isnan(row["yield_slope"]) and row["yield_slope"] > 0:
                opp_card("Improving Yield Trend",
                         f"{roa_crop} shows a positive historical yield trend (+{row['yield_slope']:.5f} t/ha/year). Continued investment in productivity could sustain this trajectory.")
                opp_found = True
            if not np.isnan(row["prod_pct"]) and row["prod_pct"] > 20:
                opp_card("Growing Production",
                         f"Production has grown by {row['prod_pct']:.1f}% over the selected period — indicating expanding agricultural output.")
                opp_found = True
            if not np.isnan(row["yield_cv"]) and row["yield_cv"] < 15:
                opp_card("Stable Productivity",
                         f"Yield coefficient of variation: {row['yield_cv']:.1f}%. Low variability indicates consistently stable production — a positive signal for planning.")
                opp_found = True
            if not np.isnan(row["corr_rain"]) and row["corr_rain"] > 0.3:
                opp_card("Positive Rainfall–Yield Association",
                         f"Historical correlation between rainfall and yield: {row['corr_rain']:.3f}. Years with higher rainfall tend to be historically associated with higher yield for {roa_crop}.")
                opp_found = True
        # Best-performing crops
        section_header("Top Growing Crops by Yield Trend")
        top_growing = stats_df[stats_df["yield_slope"] > 0].sort_values("yield_slope", ascending=False).head(10)
        if not top_growing.empty:
            fig = px.bar(top_growing, x="yield_slope", y="Crop", orientation="h",
                         title="Crops with Highest Positive Yield Trend Slope (t/ha/year)",
                         labels={"yield_slope": "Yield Trend Slope (t/ha/yr)", "Crop": ""})
            fig.update_traces(marker_color="#28a745")
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(apply_theme(fig), use_container_width=True)
        if not opp_found:
            st.info(f"Limited positive signals identified for {roa_crop} in the selected period based on available data.")

    with tab_action:
        section_header("Data-Driven Analytical Actions")
        actions = [
            ("Monitor Crops with Declining Yield Trends",
             f"{stats_df[stats_df['yield_slope'] < 0].shape[0]} crops show historically declining yield trends. Prioritise monitoring with additional regional, soil, and irrigation data."),
            ("Investigate Anomalous Production Years",
             "Identify years with unusually low or high production per crop. Cross-reference with rainfall, temperature, and pest/disease records for root-cause analysis."),
            ("Analyse Climate Conditions During High-Yield Periods",
             "Filter years where yield exceeded the historical 75th percentile for each crop and compare rainfall and temperature distributions."),
            ("Compare Crop Performance Under Different Rainfall Ranges",
             "Segment historical data by rainfall quartile and compare yield distributions. This can reveal crops that are more or less sensitive to precipitation levels."),
            ("Investigate Crops with High Climate Sensitivity",
             f"Focus analytical attention on crops with strong historical rainfall–yield correlations. These may require more detailed climate risk modelling."),
            ("Expand Dataset for Deeper Analysis",
             "Incorporate regional disaggregation, irrigation coverage, soil type, fertiliser use, and MSP data for more robust analytical conclusions."),
            ("Benchmark Against National Averages",
             "Compare district- or state-level productivity data against national averages to identify high-performing and underperforming regions."),
        ]
        for title, body in actions:
            action_card(title, body)

        section_header("BI Storytelling — End-to-End Analytical Chain")
        st.markdown("""
| Level | Question | Indicator |
|-------|----------|-----------|
| **Fact** | What is happening? | Production & yield KPIs |
| **Insight** | How is it changing? | Historical trend slopes |
| **Risk** | What could require attention? | Declining trends, high variability |
| **Opportunity** | What shows positive signals? | Growing productivity, stable yields |
| **Action** | What should be investigated next? | Targeted analytical actions above |
""")


# ══════════════════════════════════════════════════════════════════
# PAGE 6 — DATA EXPLORER
# ══════════════════════════════════════════════════════════════════
def page_data_explorer():
    st.title("🔍 Data Explorer")
    st.caption("Explore, filter, search, and download the AgroYield master dataset.")

    if not DATA_OK or _master.empty:
        st.warning("No data available.")
        return

    # Filters
    c1, c2 = st.columns(2)
    with c1:
        exp_crops = st.multiselect("Filter by Crop", sorted(_master["Crop"].dropna().unique().tolist()),
                                   default=[], key="exp_crops")
    with c2:
        exp_years = st.slider("Filter by Year",
                              int(_master["Year"].min()), int(_master["Year"].max()),
                              (int(_master["Year"].min()), int(_master["Year"].max())), key="exp_years")

    explore_df = _master.copy()
    if exp_crops:
        explore_df = explore_df[explore_df["Crop"].isin(exp_crops)]
    explore_df = explore_df[(explore_df["Year"] >= exp_years[0]) & (explore_df["Year"] <= exp_years[1])]

    # Column selection
    all_cols = list(explore_df.columns)
    sel_cols = st.multiselect("Select Columns to Display", all_cols, default=all_cols[:8])
    if sel_cols:
        explore_df = explore_df[sel_cols]

    # Search
    search_term = st.text_input("🔎 Search (crop name or year)", "")
    if search_term:
        mask = explore_df.apply(lambda col: col.astype(str).str.contains(search_term, case=False, na=False)).any(axis=1)
        explore_df = explore_df[mask]

    st.write(f"**{len(explore_df):,} records** matching current filters")
    st.dataframe(explore_df.reset_index(drop=True), use_container_width=True, height=400)

    # Download
    csv_bytes = explore_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇ Download Filtered Data as CSV",
        data=csv_bytes,
        file_name="agroyield_filtered.csv",
        mime="text/csv",
    )

    # ── Data Quality Section ───────────────────────────────────────
    section_header("Data Quality Summary")
    dq1, dq2, dq3, dq4 = st.columns(4)
    with dq1:
        kpi_card("Crop Files Loaded",  str(len(glob.glob(os.path.join(CROPS_DIR, "*.csv")))))
    with dq2:
        kpi_card("Unique Crop Types",  str(_master["Crop"].nunique()))
    with dq3:
        kpi_card("Total Records", f"{len(_master):,}")
    with dq4:
        yr_range_data = f"{int(_master['Year'].min())}–{int(_master['Year'].max())}"
        kpi_card("Year Range", yr_range_data)

    dq5, dq6, dq7, dq8 = st.columns(4)
    total_cells = _master.shape[0] * _master.shape[1]
    missing_cells = _master.isnull().sum().sum()
    with dq5: kpi_card("Missing Values (total cells)", f"{missing_cells:,}")
    with dq6: kpi_card("Data Completeness", f"{100 - (missing_cells/total_cells*100):.1f}%")
    with dq7: kpi_card("Duplicate Rows", str(_master.duplicated().sum()))
    with dq8: kpi_card("Columns in Master Dataset", str(_master.shape[1]))

    section_header("Missing Value Distribution")
    miss = _master.isnull().sum().reset_index()
    miss.columns = ["Column", "Missing"]
    miss = miss[miss["Missing"] > 0].sort_values("Missing", ascending=False)
    if not miss.empty:
        fig = px.bar(miss, x="Column", y="Missing", title="Missing Values per Column",
                     labels={"Missing": "Count", "Column": "Column"})
        fig.update_traces(marker_color="#dc3545")
        st.plotly_chart(apply_theme(fig), use_container_width=True)
    else:
        st.success("No missing values detected in the master dataset.")


# ══════════════════════════════════════════════════════════════════
# PAGE 7 — METHODOLOGY
# ══════════════════════════════════════════════════════════════════
def page_methodology():
    st.title("📋 Methodology")
    st.caption("How raw agricultural data is transformed into analytical intelligence.")

    st.markdown("""
## Data Analytics Pipeline

```
RAW AGRICULTURAL DATA (49 crop CSV files + rainfall.csv + temperature.csv)
        ↓
DATA LOADING & COLLECTION
  • Automatic discovery of all CSV files using glob patterns
  • Encoding-safe loading (UTF-8 with BOM, Latin-1 fallback)
        ↓
DATA CLEANING
  • Standardise column names (strip whitespace, normalise casing)
  • Remove irrelevant metadata columns (Domain, Area Code, Flag, etc.)
  • Convert Value and Year to numeric; drop non-parseable rows
  • Remove duplicate records
        ↓
DATA TRANSFORMATION
  • Filter Element column to: Area harvested, Production, Yield
  • Pivot long-form data (one row per Crop–Year–Element) to wide form
    (one row per Crop–Year with Area_Harvested, Production, Yield columns)
  • Yield Unit Conversion: hg/ha → tonnes/ha
    (Yield_t_ha = Yield_hg_ha ÷ 10,000)
        ↓
DATA INTEGRATION
  • Merge agricultural data with rainfall.csv on Year (left join)
  • Merge result with temperature.csv on Year (left join)
  • Save combined master dataset: data/agroyield_master.csv
        ↓
EXPLORATORY DATA ANALYSIS (EDA)
  • Distribution of production by crop and year
  • Area harvested trends
  • Yield trend analysis per crop
  • Rainfall distribution and variability
  • Temperature distribution and variability
        ↓
STATISTICAL ANALYSIS
  • Mean, Median, Standard Deviation for all key metrics
  • Percentage change (first year to last year per crop)
  • Pearson Correlation: Annual Rainfall ↔ Yield (per crop)
  • Pearson Correlation: Annual Temperature ↔ Yield (per crop)
  • Coefficient of Variation (CV%) = (std / mean) × 100
  • Linear trend slope via numpy.polyfit (degree 1)
  • Rolling averages (10-year window) for climate smoothing
        ↓
VISUALISATION
  • Interactive Plotly charts: line, bar, scatter, area, heatmap
  • Multi-panel subplot charts for combined time-series
  • Plotly OLS trendlines for scatter analyses
        ↓
INSIGHTS
  • KPI calculation from actual data (no hard-coded values)
  • Crop categorisation: Growing Productivity / Declining / High Yield / Stable
  • Top performers: production, yield, growth rate
        ↓
RISK / OPPORTUNITY IDENTIFICATION
  • Risk: negative yield trend, high CV%, declining production, negative rainfall correlation
  • Opportunity: positive yield trend, stable CV%, growing production, positive rainfall correlation
        ↓
ANALYTICAL ACTIONS
  • Data-driven investigation recommendations
  • Cross-referencing approach suggestions
  • Dataset expansion guidance
```

---

## Key Processing Decisions

| Step | Approach | Reason |
|------|----------|--------|
| Yield unit | Divide hg/ha by 10,000 | Convert to tonnes/ha for interpretability |
| Crop name | Extracted from `Item` column or filename | Automated, no manual mapping |
| Element pivoting | `pivot_table` on Crop × Year | Converts 3 rows per year into 1 analytical row |
| Climate merge | Left join on `Year` | Preserve all crop records even if climate data is missing |
| Correlation | Pearson r | Standard linear association measure for continuous variables |
| Trend | `numpy.polyfit(degree=1)` | Linear trend slope in original units per year |
| Caching | `@st.cache_data` | Prevent reloading all 49 files on every user interaction |

---

## Statistical Methods

| Method | Formula | Use Case |
|--------|---------|----------|
| Mean | Σx / n | Average production, yield, area |
| Standard Deviation | √(Σ(x-μ)²/n) | Spread of yield or rainfall |
| CV% | (σ/μ) × 100 | Relative variability independent of units |
| Pearson Correlation | cov(X,Y) / (σ_X · σ_Y) | Association between two continuous variables |
| Percentage Change | ((last − first) / |first|) × 100 | Growth over analysis period |
| Trend Slope | Linear regression coefficient | Direction and magnitude of historical trend |
| Rolling Average | Moving mean over 10-year window | Smooths inter-annual climate noise |

---

## Important Caveats

> **Correlation ≠ Causation.** All statistical relationships reported in this dashboard are historical associations  
> derived from national-level aggregated data. Actual agricultural outcomes are influenced by many  
> additional factors including soil quality, irrigation, fertiliser use, pest/disease pressure,  
> farming practices, government policy, and local climate patterns not captured in this dataset.

> All insights and indicators are labelled as *analytical* or *potential* — they are starting points  
> for investigation, not definitive conclusions.

---

## Dataset Reference

- **Source:** Indian Agriculture & Climate Dataset (FAOSTAT-based, 1961–2018)  
- **Kaggle:** [Indian Agriculture Dataset](https://www.kaggle.com/datasets/pyatakov/india-agriculture-crop-production)  
- **Crops:** 49 crop CSV files  
- **Climate:** rainfall.csv (monthly + seasonal + annual), temperature.csv (seasonal + annual)  
- **Period:** 1961–2018 (58 years)

---

## Technologies

| Technology | Version | Role |
|-----------|---------|------|
| Python | ≥ 3.9 | Core programming language |
| Streamlit | ≥ 1.32 | Interactive web dashboard framework |
| Pandas | ≥ 2.0 | Data loading, cleaning, transformation |
| NumPy | ≥ 1.24 | Numerical computation, trend slopes |
| Plotly | ≥ 5.18 | Interactive visualisations |

""")


# ══════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════════════
if page.startswith("1"):
    page_executive_overview()
elif page.startswith("2"):
    page_crop_analysis()
elif page.startswith("3"):
    page_climate_analysis()
elif page.startswith("4"):
    page_yield_climate_drivers()
elif page.startswith("5"):
    page_risk_opportunity_action()
elif page.startswith("6"):
    page_data_explorer()
elif page.startswith("7"):
    page_methodology()
