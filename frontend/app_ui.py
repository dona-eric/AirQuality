"""
dashboard_streamlit.py
======================
Dashboard Streamlit — EDA Qualité d'Air Cotonou
Données : Open-Meteo Air Quality API — Sept 2025 → Mars 2026
Fusion : visualisations EDA + prévisions IA 24h
"""

import logging
import pathlib
import warnings
from streamlit_option_menu import option_menu
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots
from sklearn.ensemble import IsolationForest

warnings.filterwarnings("ignore")

# =========================
# 0. CONFIG PAGE
# ==========================
st.set_page_config(
    page_title="Indice de la Qualité de l'Air à Cotonou: Pollution d'Air PM2.5, PM10 en temps réel",
    page_icon=":material/dashboard:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===============================
# 0b. CSS GLOBAL
# ===============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    padding: "40px 10%";
}

/* Sidebar */
.main { background-color: #41757C; }

.main-content {
    padding-bottom: 100px;}

/* Sidebar Style */
[data-testid="stSidebar"] {
    background-color: #0A0F1E !important;
    border-right: 1px solid rgba(99,102,241,0.18) !important;
}
[data-testid="stSidebar"] * { color: #94A3B8 !important; }
.sidebar-title { 
    font-size: 22px; font-weight: 800; 
    background: linear-gradient(135deg, #60A5FA, #3B82F6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
            
/* Style de la bannière principale */
.main-banner {
    background-color: #262730;
    background-image: url('https://www.transparenttextures.com/patterns/black-thread-light.png');
    border-radius: 15px;
    padding: 30px;
    color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 30px;
    border: 1px solid #3e404b;
}
            
/* KPI cards */
.kpi-card {
    background-color: #a4c9ec86;
    border-radius: 12px;
    padding: 20px;
    border-bottom: 5px solid #e0e0e0; /* Bordure colorée en bas */
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    white-space: wrap;
}
            
.card-title { color: #566F91; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.card-value { color: #0F172B; font-size: 28px; font-weight: 800; margin: 5px 0; }
.card-subtitle { color: #293A32; font-size: 12px; }

/* Section headers */
.section-container {
    display: flex;
    align-items: center;
    margin-top: 40px;
    margin-bottom: 20px;
}
.section-title {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-right: 15px;
    color: #11172D;
    white-space: nowrap;
    
}

/* Insight bullets */
.insight-box {
    background: #F0EDE6;
    border-radius: 12px;
    padding: 20px 24px;
}
.insight-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 10px;
    font-size: 13px;
    line-height: 1.6;
}

/* Plotly chart container */
.stPlotlyChart { border-radius: 12px; overflow: hidden; }

/* Alert banners */
.alert-bad {
    background: #FEF2F2;
    border-left: 4px solid #EF4444;
    border-radius: 8px;
    padding: 12px 16px;
    color: #991B1B;
    font-size: 13px;
}
.alert-good {
    background: #ECFDF5;
    border-left: 4px solid #10B981;
    border-radius: 8px;
    padding: 12px 16px;
    color: #065F46;
    font-size: 13px;
}

/* Hide Streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
footer-container {
    margin-top: 100px;
    padding: 40px 0 20px 0;
    border-top: 1px solid #7CB550;
}
            

.footer-wrapper {
        width: 100%;
        background-color: #FFFFFF;
        border-top: 1px solid #E2E8F0;
        padding: 30px 0;
        margin-top: 50px;
        color: #64748B;
    }
.footer-badge {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    background: #7CB550;
    color: #64748B;
    border: 1px solid #E2E8F0;
    margin-right: 10px;
}
.footer-text {
    font-size: 12px;
    color: #94A3B8;
    }
</style>
""", unsafe_allow_html=True)

# =====================================
# 1. PALETTE & CONSTANTES

C = {
    "primary":   "#0A0F1E",
    "secondary": "#64748B",
    "accent":    "#6366F1",      # indigo
    "violet":    "#8B5CF6",
    "bg":        "#F8FAFC",
    "card":      "#FFFFFF",
    "border":    "rgba(99,102,241,0.12)",
    "success":   "#0D9488",
    "warning":   "#F59E0B",
    "danger":    "#EF4444",
    "coral":     "#FB923C",
    "teal":      "#0D9488",
    "amber":     "#F59E0B",
    "blue":      "#6366F1",
}

AQI_COLORS = {"Bon": "#0b7d79", "Moyen": "#f39c12", "Mauvais": "#ff0000"}
OMS = {"pm2_5": 12, "pm10": 40, "ozone": 100, "nitrogen_dioxide": 10}
TEMPLATE = "plotly_white"

POLL_COLS = [
    "pm2_5", "pm10", "carbon_monoxide", "carbon_dioxide",
    "sulphur_dioxide", "ozone", "nitrogen_dioxide", "methane", "european_aqi",
]
CORR_COLS = POLL_COLS
CORR_SHORT = {
    "pm10": "PM10", "pm2_5": "PM2.5", "carbon_monoxide": "CO",
    "carbon_dioxide": "CO2", "sulphur_dioxide": "SO2",
    "ozone": "O3", "nitrogen_dioxide": "NO2", "methane": "CH4", "european_aqi": "AQI",
}
POLLUANT_META = {
    "pm2_5":            ("PM2.5 (μg/m³)",   C["coral"],     0,   55),
    "pm10":             ("PM10 (μg/m³)",     C["teal"],      0,  150),
    "carbon_dioxide":   ("CO2 (μg/m³)",      C["card"],      0,  100),
    "carbon_monoxide":  ("CO (μg/m³)",       C["blue"],      0,  400),
    "ozone":            ("Ozone O₃ (μg/m³)", C["teal"],      0,  180),
    "nitrogen_dioxide": ("NO₂ (μg/m³)",      C["secondary"], 0,   15),
    "sulphur_dioxide":  ("SO₂ (μg/m³)",      C["amber"],     0,    5),
    "methane":          ("Méthane (μg/m³)",   C["accent"],    0, 2000),
}

CARD_STYLE = {
    "background": C["card"],
    "border": f"1px solid {C['border']}",
    "borderRadius": "12px",
    "padding": "20px",
    "boxShadow": "0 1px 3px 0 rgba(0,0,0,0.1)",
}


# 2.========================= CHARGEMENT DONNÉES (mis en cache) ===========================


@st.cache_data(show_spinner="Chargement des données air…")

def load_data():
    CSV_PATH = pathlib.Path("data/raw/hourly_quality_air_data.csv")
    df_raw = pd.read_csv(CSV_PATH)
    df_raw["date"] = pd.to_datetime(df_raw["date"], utc=True)
    df = df_raw.sort_values("date").reset_index(drop=True)

    df["hour"]      = df["date"].dt.hour
    df["month"]     = df["date"].dt.month
    df["dayofweek"] = df["date"].dt.dayofweek
    df["date_str"]  = df["date"].dt.strftime("%Y-%m-%d")
    df["month_str"] = df["date"].dt.strftime("%b %Y")
    df["pm_ratio"]  = (df["pm2_5"] / df["pm10"].replace(0, np.nan)).round(3)
    df["saison"]    = df["month"].apply(
        lambda m: "Harmattan (Déc-Fév)" if m in [12, 1, 2] else "Saison pluvieuse (Mar+)"
    )
    return df

df=load_data()

# Coordonnées approximatives de Cotonou
LAT_COTONOU = 6.3654
LON_COTONOU = 2.4505

# Ajout de coordonnées si elles n'existent pas (simulation pour l'exemple)
if 'lat' not in df.columns:
    df['lat'] = LAT_COTONOU
    df['lon'] = LON_COTONOU

# AQI label
def aqi_label(val):
    if val <= 12:   return "Bon"
    elif val <= 35.5: return "Moyen"
    else:           return "Mauvais"

df["aqi_level"] = df["pm2_5"].apply(lambda x: aqi_label(x))

    # Anomalies IsolationForest
ANOMALY_COLS = ["pm2_5", "pm10", "ozone", "nitrogen_dioxide"]
X_iso = df[ANOMALY_COLS].dropna()
iso = IsolationForest(contamination=0.05, random_state=42)
pred = iso.fit_predict(X_iso)
df.loc[X_iso.index, "anomaly"] = (pred == -1).astype(int)
df["anomaly"] = df["anomaly"].fillna(0).astype(int)



@st.cache_data(show_spinner=False)
def compute_aggregates(df):
    daily = df.groupby("date_str")[POLL_COLS].mean().round(3).reset_index()

    hourly = df.groupby("hour")[POLL_COLS].mean().round(3).reset_index()
    monthly = df.groupby("month")[POLL_COLS].mean().round(2).reset_index()
    monthly["month_label"] = monthly["month"].map({
        9: "Sept 2025", 10: "Oct 2025", 11: "Nov 2025",
        12: "Déc 2025", 1: "Jan 2026", 2: "Fév 2026", 3: "Mar 2026"
    })
    corr = df[[c for c in CORR_COLS if df[c].notna().any()]].corr().round(3)
    peaks = (
        df[df["european_aqi"] > 60]
        .groupby("date_str")["european_aqi"].max()
        .sort_values(ascending=False)
        .reset_index()
        .head(15)
    )
    return daily, hourly, monthly, corr, peaks


# ==================================
# 3. APPEL API PRÉDICTION
# ==================================
def fetch_prediction(api_url: str):
    try:
        r = requests.post(f"{api_url}/predict", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def fetch_history(api_url: str):
    try:
        r = requests.get(f"{api_url}/history", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


# =============================
# 4. FIGURES
# =============================

def fig_oms_gauges(pm2_5_mean, pm_10_mean, O3_mean, no2_mean) -> go.Figure:
    polluants = [
        ("PM2.5", pm2_5_mean, OMS["pm2_5"],          C["coral"]),
        ("PM10",  pm_10_mean, OMS["pm10"],            C["amber"]),
        ("Ozone", O3_mean,    OMS["ozone"],            C["teal"]),
        ("NO₂",   no2_mean,   OMS["nitrogen_dioxide"], C["blue"]),
    ]
    fig = make_subplots(rows=1, cols=4,
                        specs=[[{"type": "indicator"}] * 4],
                        subplot_titles=[p[0] for p in polluants])
    for i, (label, val, seuil, color) in enumerate(polluants, 1):
        pct = val / seuil
        g_color = C["danger"] if pct > 1 else (C["amber"] if pct > 0.75 else C["teal"])
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=val,
            delta={"reference": seuil,
                   "increasing": {"color": C["danger"]},
                   "decreasing": {"color": C["teal"]},
                   "suffix": " μg/m³"},
            number={"suffix": " μg/m³", "font": {"size": 18}},
            gauge={
                "axis": {"range": [0, seuil * 2.5], "tickwidth": 1},
                "bar":  {"color": g_color, "thickness": 0.3},
                "bgcolor": "white", "borderwidth": 0,
                "steps": [
                    {"range": [0, seuil * 0.75],    "color": C["teal"]},
                    {"range": [seuil * 0.75, seuil], "color": C["amber"]},
                    {"range": [seuil, seuil * 2.5],  "color": C["danger"]},
                ],
                "threshold": {"line": {"color": C["danger"], "width": 3},
                              "thickness": 0.85, "value": seuil},
            },
            title={"text": f"Seuil OMS : {seuil} μg/m³",
                   "font": {"size": 11, "color": C["secondary"]}},
        ), row=1, col=i)
    fig.update_layout(template=TEMPLATE, height=300,
                      margin=dict(l=20, r=20, t=40, b=10))
    return fig


def fig_aqi_distribution(df) -> go.Figure:
    counts = df["aqi_level"].value_counts()
    ordre  = ["Bon", "Moyen", "Mauvais"]
    labels = [l for l in ordre if l in counts.index]
    values = [counts[l] for l in labels]
    colors = [AQI_COLORS[l] for l in labels]

    fig = make_subplots(rows=1, cols=2,
                        specs=[[{"type": "pie"}, {"type": "bar"}]],
                        subplot_titles=["Répartition des heures", "Nombre d'heures par niveau"])
    fig.add_trace(go.Pie(labels=labels, values=values,
                         marker=dict(colors=colors),
                         textinfo="percent+label",
                         hovertemplate="%{label}<br><b>%{value} h</b> (%{percent})<extra></extra>",
                         hole=0.35), row=1, col=1)
    fig.add_trace(go.Bar(x=labels, y=values, marker_color=colors,
                         text=values, textposition="outside",
                         hovertemplate="%{x}<br><b>%{y} h</b><extra></extra>"), row=1, col=2)
    fig.update_layout(template=TEMPLATE, height=320,
                      margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
    return fig


def fig_monthly_evolution(monthly) -> go.Figure:
    fig = go.Figure()
    for col, color, label in [
        ("pm2_5",           C["coral"],     "PM2.5"),
        ("pm10",            C["amber"],     "PM10"),
        ("sulphur_dioxide", C["card"],      "SO2"),
        ("nitrogen_dioxide",C["accent"],    "NO2"),
        ("carbon_dioxide",  C["blue"],      "CO2"),
        ("ozone",           C["teal"],      "O₃"),
    ]:
        fig.add_trace(go.Bar(
            x=monthly["month_label"], y=monthly[col], name=label,
            marker_color=color,
            text=monthly[col].round(1), textposition="outside",
            hovertemplate="%{x}<br><b>%{y:.1f}</b><extra>" + label + "</extra>",
        ))
    fig.update_layout(
        template=TEMPLATE, height=320, barmode="stack",
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=1.08),
        yaxis=dict(title="Valeur moyenne"),
        xaxis=dict(categoryorder="array", categoryarray=[
            "Sept 2025", "Oct 2025", "Nov 2025", "Déc 2025",
            "Jan 2026", "Fév 2026", "Mar 2026"]),
    )
    return fig


def fig_hourly_pollutants(hourly) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=["PM2.5 (μg/m³)", "PM10 (μg/m³)", "CO2 (μg/m³)",
                        "Ozone O₃ (μg/m³)", "SO2 (μg/m³)", "NO₂ (μg/m³)"],
        vertical_spacing=0.25, horizontal_spacing=0.08,
    )
    for row, col, col_name, color in [
        (1, 1, "pm2_5",           C["coral"]),
        (1, 2, "pm10",            C["amber"]),
        (1, 3, "ozone",           C["teal"]),
        (2, 1, "sulphur_dioxide", C["secondary"]),
        (2, 2, "carbon_dioxide",  C["accent"]),
        (2, 3, "nitrogen_dioxide",C["blue"]),
    ]:
        fig.add_trace(go.Scatter(
            x=hourly["hour"], y=hourly[col_name],
            mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(size=5, color=color),
            fill="tozeroy", fillcolor=color,
            showlegend=False,
            hovertemplate=f"%{{x}}h → <b>%{{y:.1f}}</b><extra></extra>",
        ), row=row, col=col)
    fig.update_xaxes(title_text="Heure", tickvals=list(range(0, 24, 3)))
    fig.update_layout(template=TEMPLATE, height=400,
                      margin=dict(l=10, r=10, t=35, b=10))
    return fig


def fig_timeseries_anomalies(daily, df, polluant="pm2_5") -> go.Figure:
    label, color, ymin, ymax = POLLUANT_META[polluant]
    roll7 = daily[polluant].rolling(7, min_periods=1).mean()
    daily_anom = df.groupby("date_str")["anomaly"].max().reset_index()
    merged = daily.merge(daily_anom, on="date_str", how="left")
    anom_days = merged[merged["anomaly"] == 1]

    fig = go.Figure()
    if polluant == "pm2_5":
        for lo, hi, lcolor, lbl in [
            (0, 12, C["teal"],  "Bon (OMS)"),
            (12, 35.5, C["amber"], "Moyen"),
            (35.5, 60, C["coral"], "Mauvais"),
        ]:
            fig.add_hrect(y0=lo, y1=hi, fillcolor=lcolor, line_width=0,
                          annotation_text=lbl, annotation_position="left",
                          annotation_font_size=10)
        fig.add_hline(y=15, line=dict(color=C["danger"], dash="dash", width=1),
                      annotation_text="Seuil OMS 24h (15)", annotation_font_size=10)

    fig.add_trace(go.Scatter(
        x=daily["date_str"], y=daily[polluant],
        mode="lines", name=label,
        line=dict(color=color, width=1.5),
        fill="tozeroy", fillcolor=color,
        hovertemplate="%{x}<br><b>%{y:.1f} μg/m³</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=daily["date_str"], y=roll7,
        mode="lines", name="Moy. mobile 7j",
        line=dict(color=color, width=2.5, dash="dot"),
        hovertemplate="Moy 7j : %{y:.1f}<extra></extra>",
    ))
    if not anom_days.empty:
        fig.add_trace(go.Scatter(
            x=anom_days["date_str"], y=anom_days[polluant],
            mode="markers", name="Anomalie",
            marker=dict(color=C["danger"], size=9, symbol="x",
                        line=dict(color="white", width=1.5)),
            hovertemplate="⚠ Anomalie<br>%{x}<br><b>%{y:.1f}</b><extra></extra>",
        ))
    fig.update_layout(template=TEMPLATE, height=340,
                      margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation="h", y=1.1),
                      hovermode="x unified",
                      yaxis=dict(title=label))
    return fig


def fig_streamgraph(df) -> go.Figure:
    df_r = df[["date_str", "pm2_5", "pm10", "ozone"]].copy()
    df_r["pm2_5_r"] = df_r["pm2_5"].rolling(24, min_periods=1).mean().round(2)
    df_r["pm10_r"]  = df_r["pm10"].rolling(24, min_periods=1).mean().round(2)
    df_r["o3_r"]    = df_r["ozone"].rolling(24, min_periods=1).mean().round(2)
    daily_r = df_r.groupby("date_str").agg(
        pm2_5_r=("pm2_5_r", "mean"),
        pm10_r=("pm10_r", "mean"),
        o3_r=("o3_r", "mean"),
    ).round(2).reset_index()

    fig = go.Figure()
    for col, label, color in [
        ("pm2_5_r", "PM2.5", C["coral"]),
        ("pm10_r",  "PM10",  C["amber"]),
        ("o3_r",    "O₃",    C["teal"]),
    ]:
        fig.add_trace(go.Scatter(
            x=daily_r["date_str"], y=daily_r[col],
            mode="lines", name=label, stackgroup="one",
            line=dict(color=color, width=0.5), fillcolor=color,
            hovertemplate=f"{label} : %{{y:.1f}}<extra></extra>",
        ))
    fig.add_vrect(x0="2025-12-19", x1="2026-02-28",
                  fillcolor=C["amber"], line_width=0,
                  annotation_text="Harmattan", annotation_position="top left",
                  annotation_font_size=11)
    fig.update_layout(template=TEMPLATE, height=300,
                      margin=dict(l=10, r=10, t=10, b=10),
                      hovermode="x unified",
                      legend=dict(orientation="h", y=1.08),
                      yaxis=dict(title="Concentration μg/m³ (empilée)"))
    return fig


def fig_hour_day_heatmap(df) -> go.Figure:
    pivot = df.pivot_table(index="dayofweek", columns="hour",
                           values="pm2_5", aggfunc="mean")
    days = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=list(range(24)), y=days,
        colorscale="YlOrRd", colorbar=dict(title="PM2.5"),
    ))
    fig.update_layout(template=TEMPLATE, height=320,
                      xaxis_title="Heure", yaxis_title="Jour",
                      margin=dict(l=10, r=10, t=10, b=10))
    return fig


def fig_monthly_boxplot(df) -> go.Figure:
    fig = px.box(df, x="month_str", y="pm2_5", color="month_str")
    fig.update_layout(template=TEMPLATE, showlegend=False, height=320,
                      margin=dict(l=10, r=10, t=10, b=10))
    return fig


def fig_pm_scatter(df) -> go.Figure:
    subset = df[["pm2_5", "pm10", "european_aqi", "hour", "aqi_level"]].dropna()
    sample = subset.sample(min(2000, len(subset)), random_state=42)
    fig = px.density_contour(sample, x="pm10", y="pm2_5", color="aqi_level")
    fig.add_trace(go.Scatter(
        x=sample["pm10"], y=sample["pm2_5"],
        mode="markers", marker=dict(size=3, opacity=0.3, color=C["amber"]),
        showlegend=False,
    ))
    z = np.polyfit(sample["pm10"], sample["pm2_5"], 1)
    p = np.poly1d(z)
    x_range = np.linspace(sample["pm10"].min(), sample["pm10"].max(), 50)
    fig.add_trace(go.Scatter(
        x=x_range, y=p(x_range), mode="lines",
        line=dict(color=C["danger"], dash="dash", width=2),
        name=f"Régression (y={z[0]:.2f}x+{z[1]:.2f})",
    ))
    fig.update_layout(template=TEMPLATE, height=350,
                      margin=dict(l=10, r=10, t=10, b=10))
    return fig


def fig_correlation_heatmap(corr) -> go.Figure:
    available = [c for c in CORR_COLS if c in corr.columns]
    labels = [CORR_SHORT[c] for c in available]
    z = corr.loc[available, available].values
    text = [[f"{v:.2f}" for v in row] for row in z]
    fig = go.Figure(go.Heatmap(
        z=z, x=labels, y=labels,
        text=text, texttemplate="%{text}", textfont=dict(size=11),
        colorscale=[[0, "blue"], [0.5, "red"], [1.0, "rgb(0,0,255)"]],
        zmid=0, zmin=-1, zmax=1,
        colorbar=dict(title="r", thickness=12, len=0.8),
        hovertemplate="%{y} / %{x}<br><b>r = %{z:.3f}</b><extra></extra>",
    ))
    fig.update_layout(template=TEMPLATE, height=360,
                      margin=dict(l=10, r=10, t=10, b=10),
                      yaxis=dict(autorange="reversed"))
    return fig


def fig_distribution_interactive(df, variable="pm2_5") -> go.Figure:
    meta = POLLUANT_META.get(variable, (variable, C["border"], 0, 200))
    label, color, _, _ = meta
    vals = df[variable].dropna()
    fig = make_subplots(rows=2, cols=1, row_heights=[0.75, 0.25],
                        vertical_spacing=0.04, shared_xaxes=True)
    fig.add_trace(go.Histogram(
        x=vals, nbinsx=50, marker_color=color,
        hovertemplate="Plage : %{x}<br>Fréq. : %{y}<extra></extra>",
        name=label,
    ), row=1, col=1)
    fig.add_trace(go.Box(
        x=vals, boxmean="sd", marker_color=color,
        line_color=color, showlegend=False,
    ), row=2, col=1)
    oms_seuils = {
        "pm2_5": [(12, "OMS 24h", C["amber"]), (25, "UE 24h", C["coral"])],
        "pm10":  [(35.5, "OMS 24h", C["amber"]), (50, "UE 24h", C["coral"])],
        "ozone": [(100, "OMS 8h", C["amber"])],
    }
    for lo, lbl, lcolor in oms_seuils.get(variable, []):
        fig.add_vline(x=lo, line=dict(color=lcolor, dash="dash", width=1.5),
                      annotation_text=lbl, annotation_font_size=10,
                      annotation_position="top right")
    fig.update_layout(template=TEMPLATE, height=320,
                      margin=dict(l=10, r=10, t=10, b=10),
                      showlegend=False, bargap=0.05,
                      xaxis2=dict(title=label),
                      yaxis=dict(title="Fréquence"))
    return fig


def fig_polluants_relation(df, variable="pm10") -> go.Figure:
    label = CORR_SHORT.get(variable, variable)
    subset = df[["pm2_5", variable, "aqi_level"]].dropna()
    fig = px.scatter(subset, x=variable, y="pm2_5", color="aqi_level",
                     opacity=0.65, render_mode="webgl",
                     marginal_x="histogram", marginal_y="histogram",
                     color_discrete_map=AQI_COLORS)
    fig.update_layout(template=TEMPLATE, height=350,
                      margin=dict(l=10, r=10, t=10, b=10),
                      xaxis_title=label, yaxis_title="PM2.5")
    return fig


def fig_peaks_bar(peaks) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=peaks["date_str"], y=peaks["european_aqi"],
        marker=dict(
            color=peaks["european_aqi"],
            colorscale=[[0, C["amber"]], [0.5, C["coral"]], [1.0, C["danger"]]],
            colorbar=dict(title="AQI", thickness=10),
        ),
        text=peaks["european_aqi"].round(1), textposition="outside",
        hovertemplate="%{x}<br><b>AQI max : %{y:.1f}</b><extra></extra>",
    ))
    fig.add_hline(y=60, line=dict(color=C["danger"], dash="dash", width=1.5),
                  annotation_text="Seuil 'Très mauvais' (60)", annotation_font_size=10)
    fig.update_layout(template=TEMPLATE, height=300,
                      margin=dict(l=10, r=10, t=10, b=10),
                      xaxis=dict(tickangle=-35),
                      yaxis=dict(title="AQI max journalier", range=[0, 95]),
                      showlegend=False)
    return fig


def fig_episodes_pollution(df) -> go.Figure:
    df_aqi = df[["date_str", "date", "european_aqi"]].dropna().copy()
    df_aqi["bad"] = (df_aqi["european_aqi"] > 60).astype(int)
    df_aqi["episode"] = (df_aqi["bad"].diff() != 0).cumsum()
    episodes = []
    for ep_id, grp in df_aqi[df_aqi["bad"] == 1].groupby("episode"):
        if len(grp) >= 6:
            episodes.append({
                "debut": grp["date_str"].iloc[0],
                "fin":   grp["date_str"].iloc[-1],
                "duree": len(grp),
                "aqi_max": grp["european_aqi"].max().round(1),
                "aqi_moy": grp["european_aqi"].mean().round(1),
            })
    if not episodes:
        return go.Figure()
    ep_df = pd.DataFrame(episodes).sort_values("debut")
    fig = go.Figure()
    for _, row in ep_df.iterrows():
        ep_color = C["coral"] if row["aqi_max"] > 70 else C["amber"]
        fig.add_trace(go.Bar(
            x=[row["duree"]],
            y=[f"{row['debut']} → {row['fin']}"],
            orientation="h",
            marker=dict(color=row["aqi_max"],
                        colorscale=[[0, C["amber"]], [0.5, C["coral"]], [1.0, C["danger"]]],
                        cmin=60, cmax=82),
            text=f"  {row['duree']}h · AQI max {row['aqi_max']}",
            textposition="inside", insidetextanchor="start",
            textfont=dict(color="white", size=11),
            hovertemplate=(
                f"<b>Épisode du {row['debut']} au {row['fin']}</b><br>"
                f"Durée : {row['duree']}h<br>"
                f"AQI max : {row['aqi_max']}<br>"
                f"AQI moy : {row['aqi_moy']}<extra></extra>"
            ),
            showlegend=False,
        ))
    fig.update_layout(
        template=TEMPLATE,
        height=max(200, len(ep_df) * 55 + 60),
        margin=dict(l=10, r=10, t=10, b=10),
        barmode="overlay",
        xaxis=dict(title="Durée (heures)"),
        yaxis=dict(title="", autorange="reversed"),
    )
    return fig


def fig_map_cotonou(polluant="pm2_5"):
    label, color, _, _ = POLLUANT_META[polluant]
    
    # On prend les dernières données connues pour la carte
    latest_data = df.tail(100) # Ou un agrégat par zone si tu as plusieurs capteurs

    fig = px.scatter_mapbox(
        latest_data,
        lat="lat",
        lon="lon",
        size=polluant,          # La taille de la bulle dépend de la concentration
        color=polluant,         # La couleur aussi
        color_continuous_scale="Reds",
        size_max=30,
        zoom=11,
        mapbox_style="carto-positron", # Style de carte épuré (SaaS style)
        title=f"Distribution spatiale : {label}"
    )
    
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# =================================
# 5. HELPERS UI

def render_kpi(title, value, subtitle, color):
    st.markdown(f"""
        <div class="kpi-card" style="border-bottom-color: {color};">
            <div class="card-title">{title}</div>
            <div class="card-value">{value}</div>
            <div class="card-subtitle">{subtitle}</div>
            <div class="p-bar"><div class="p-fill" style="background-color: {color};"></div></div>
        </div>
    """, unsafe_allow_html=True)

def section_title(text: str):
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin: 40px 0 20px 0;">
            <div style="font-size: 13px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 1.5px; white-space: nowrap; margin-right: 15px;">
                {text}
            </div>
            <div style="flex-grow: 1; height: 1px; background: #E2E8F0;"></div>
        </div>
    """, unsafe_allow_html=True)

# ==========================6. SIDEBAR ==============================

with st.sidebar:
    st.markdown('<p class="sidebar-title">AQI Cotonou</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:12px; color:#94A3B8; margin-top:-10px;">Surveillance & IA</p>', unsafe_allow_html=True)
    st.divider()

    # Navigation avec icônes
    selected_page = option_menu(
        menu_title=None,
        options=["Vue d'ensemble", "Séries Temporelles", "Distributions", "Matrice Corrélations", "Pics & Evolutions", "Analyses ML"],
        icons=["grid-full", "graph-up", "bar-chart-steps", "patch-check", "lightning-charge", "cpu"],
        menu_icon="cast",
        default_index=0,
        styles={
        "container": {"padding": "0!important",},
        "icon": {"color": "#60A5FA", "font-size": "18px"}, 
        "nav-link": {
            "font-size": "14px", 
            "text-align": "left", 
            "margin": "5px", 
            "color": "#94A3B8",
            "font-family": "'Inter', sans-serif"
        },
        "nav-link-selected": {
            "background-color": "#1E293B", 
            "color": "#4F6B75", 
            "font-weight": "600",
            "border-left": "4px solid #3B82F6" # 
        },
    }
    )

    st.divider()
    with st.expander("Paramètres API"):
        api_url = st.text_input("URL", "http://127.0.0.1:8000")
        if st.button("Rafraîchir les données", use_container_width=True, width="stretch"):
            st.cache_data.clear()
            st.rerun()

# =========================== 7. CHARGEMENT ================================

try:
    daily, hourly, monthly, corr_matrix, peaks = compute_aggregates(df)
except FileNotFoundError:
    st.error("Fichier `data/raw/hourly_quality_air_data.csv` introuvable.")
    st.info("Lancez d'abord votre ETL pour générer le fichier de données.")
    st.stop()

# Stats globales
pm2_5_mean  = df["pm2_5"].mean().round(2)
pm_10_mean  = df["pm10"].mean().round(2)
pm2_5_p95   = df["pm2_5"].quantile(0.95).round(2)
O3_mean     = df["ozone"].mean().round(2)
no2_mean    = df["nitrogen_dioxide"].mean().round(2)
AQI         = df["european_aqi"].mean().round(2)
aqi_counts  = df["aqi_level"].value_counts()
n_anomalies = int(df["anomaly"].sum())
bon_pct     = (aqi_counts.get("Bon", 0) / len(df) * 100).round(1)
moyen_pct   = (aqi_counts.get("Moyen", 0) / len(df) * 100).round(1)

mauvais_pct = (aqi_counts.get("Mauvais", 0) / len(df) * 100).round(1)

if AQI <= 50:   aqi_global_label, aqi_global_color = "Bon",    C["teal"]
elif AQI <= 100: aqi_global_label, aqi_global_color = "Modéré", C["amber"]
else:            aqi_global_label, aqi_global_color = "Mauvais",C["danger"]

#===================== 8. EN-TÊTE ================================

st.markdown("""
<div class="main-banner">
    <div>
        <span style="font-size: 40px; font-weight: bold; color: #4285F4;">AQI</span>
        <span style="margin-left: 20px; color: #bdc1c6;">Niveau de pollution de l'air PM2.5, PM10 en temps réel à Cotonou, Bénin</span>
        <h2 style="color: white; margin-top: 5px;">Surveillance des Données de la Qualité d'Air</h2>
    </div>
    <div style="background: #3e404b; padding: 10px; border-radius: 50%;">
        <span style="color: white; font-size: 24px;">↗</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════
#  PAGE : VUE D'ENSEMBLE
# ══════════════════════════════════════════
if selected_page == "Vue d'ensemble":

    # — Prévision IA
    # section_title("🤖 PRÉVISION IA À 24H")
    pred = fetch_prediction(api_url)

    if pred:
        c1, c2, c3 = st.columns(3)
        with c1:
            render_kpi("PM2.5 Actuel", f"{pred['current_pm25']} µg/m³", "Valeur actuelle", color="#EF4444")
        with c2:
            delta_sign = "↑" if pred.get("delta", 0) > 0 else "↓"
            render_kpi("Prévision J+1", f"{pred['predicted_pm25']} µg/m³",
                       f"{delta_sign} {abs(pred.get('delta', 0))} µg/m³ vs actuel", color="#3B82F6")
        with c3:
            render_kpi("Status", pred.get("aqi_label", "—"),
                       pred.get("conseil", ""), color="#10B981")

        if "Mauvais" in str(pred.get("aqi_label", "")):
            st.markdown(
                '<div class="alert-bad">⚠️ Pic de pollution prévu. '
                'Pensez à limiter vos trajets en Zémidjan demain.</div>',
                unsafe_allow_html=True
            )
        elif "Bon" in str(pred.get("aqi_label", "")):
            st.markdown(
                '<div class="alert-good">✅ L\'air sera de bonne qualité. '
                'Idéal pour une sortie sur la Route des Pêches !</div>',
                unsafe_allow_html=True
            )

        # Historique 7 jours
        hist = fetch_history(api_url)
        if hist:
            st.markdown("##### Historique 7 derniers jours")
            df_hist = pd.DataFrame({"Date": hist["dates"], "PM2.5 (µg/m³)": hist["values"]})
            fig_h = px.line(df_hist, x="Date", y="PM2.5 (µg/m³)",
                            markers=True, line_shape="spline")
            fig_h.add_hline(y=15, line_dash="dash", line_color="green",
                            annotation_text="Limite OMS")
            fig_h.update_layout(template=TEMPLATE, height=260,
                                 margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_h, use_container_width=True)
    else:
        st.info("💡 API non disponible. Lancez `python main.py` pour activer les prévisions.")


    # — KPIs EDA
    section_title("📊 INDICATEURS CLÉS — PÉRIODE COMPLÈTE")
    c1, c2, c3, c4 = st.columns(4)
    with c1: render_kpi("AQI Moyen", str(AQI), aqi_global_label, aqi_global_color)
    with c2: render_kpi("PM2.5 Moyen", f"{pm2_5_mean} μg/m³", f"P95 : {pm2_5_p95}", "#EF4444")
    with c3: render_kpi("PM10 Moyen", f"{pm_10_mean} μg/m³", "Données 24h", "#F59E0B")
    with c4: render_kpi("Anomalies", f"{n_anomalies} h", "IsolationForest 5%", "#EF4444")

    c1, c2, c3, c4 = st.columns(4)
    with c1: render_kpi("Ozone moyen", f"{O3_mean} μg/m³", "", color="#14B8A6")
    with c2: render_kpi("Rapport PM2.5/PM10", f"{df['pm_ratio'].mean().round(2)}",
                 "Source mixte biomasse/poussière", "#8B5CF6")
    with c3: render_kpi("Heures Mauvais", f"{mauvais_pct}%", "AQI > 35.5", "#EF4444")
    with c4:
        dominant = "Mauvais" if mauvais_pct > 50 else ("Modéré" if moyen_pct > 50 else "Bon")
        render_kpi("Niveau dominant", dominant,
            f"Mauvais {mauvais_pct}% · Modéré {moyen_pct}% · Bon {bon_pct}%", "#10B981")

    # --- Jauges OMS ---
    section_title("⚖️ DÉPASSEMENTS DES SEUILS OMS")
    st.markdown('<p style="color: #94A3B8; font-size: 13px; margin-top: -15px;">Rouge = dépassement du seuil OMS · Valeurs moyennes sur la période</p>', unsafe_allow_html=True)

    # Conteneur blanc pour le graphique
    with st.container():
        st.plotly_chart(fig_oms_gauges(pm2_5_mean, pm_10_mean, O3_mean, no2_mean),
                        use_container_width=True)


    # --- AQI Distribution + Mensuel ---
    section_title("📊 RÉPARTITION AQI & TENDANCE MENSUELLE")

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown('<p style="font-weight: 600; color: #1E293B; font-size: 14px;">Répartition des niveaux AQI</p>', unsafe_allow_html=True)
        st.plotly_chart(fig_aqi_distribution(df), use_container_width=True)

    with c2:
        st.markdown('<p style="font-weight: 600; color: #1E293B; font-size: 14px;">Évolution mensuelle comparative</p>', unsafe_allow_html=True)
        st.plotly_chart(fig_monthly_evolution(monthly), use_container_width=True)


    # --- Profil horaire ---
    section_title("⏰ PROFIL HORAIRE MOYEN — CYCLE JOURNALIER")
    st.markdown('<p style="color: #94A3B8; font-size: 13px; margin-top: -15px;">Analyse cyclique des 6 indicateurs clés sur 24 heures</p>', unsafe_allow_html=True)

    st.plotly_chart(fig_hourly_pollutants(hourly), use_container_width=True)


    # --- Stream graph ---
    section_title("🌊 ÉVOLUTION MULTI-POLLUANTS ROLLING 24H")
    st.markdown('<p style="color: #94A3B8; font-size: 13px; margin-top: -15px;">Contribution cumulée PM2.5 + PM10 + O₃ · Focus zone Harmattan</p>', unsafe_allow_html=True)

    with st.container():
        st.plotly_chart(fig_streamgraph(df), use_container_width=True)

    # --- SECTION CARTOGRAPHIE ---
    section_title("🌍 CARTOGRAPHIE TEMPS RÉEL")

    col_map_1, col_map_2 = st.columns([1, 3])

    with col_map_1:
        st.markdown('<p style="color: #94A3B8; font-size: 13px; margin-top: -15px;">Focus Géographique</p>', unsafe_allow_html=True)
        map_poll_choice = st.selectbox(
            "Choisir le polluant à cartographier :",
            options=["pm2_5", "pm10", "ozone", "nitrogen_dioxide"],
            format_func=lambda x: POLLUANT_META[x][0]
        )
        st.info("Les données sont actuellement centrées sur la station de référence du Littoral.")

    with col_map_2:
        # Conteneur blanc pour la carte
        st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
        st.plotly_chart(fig_map_cotonou(map_poll_choice), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════
#  PAGE : SÉRIES TEMPORELLES
# ══════════════════════════════════════════
elif selected_page == "Séries Temporelles":
    section_title(" SÉRIE TEMPORELLE + ANOMALIES DÉTECTÉES")
    poll_choice = st.selectbox(
        "Polluant",
        options=list(POLLUANT_META.keys()),
        format_func=lambda k: POLLUANT_META[k][0],
        index=0,
    )
    st.plotly_chart(fig_timeseries_anomalies(daily, df, poll_choice),
                    use_container_width=True, width="stretch")


    section_title(" ANALYSE TEMPORELLE AVANCÉE")
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Cycle pollution : heure vs jour de la semaine")
        st.plotly_chart(fig_hour_day_heatmap(df), use_container_width=True, width="stretch")
    with c2:
        st.caption("Distribution mensuelle PM2.5")
        st.plotly_chart(fig_monthly_boxplot(df), use_container_width=True, width="stretch")


# ══════════════════════════════════════════
#  PAGE : DISTRIBUTIONS
# ══════════════════════════════════════════
elif selected_page == "Distributions":
    section_title("📊 DISTRIBUTION DES POLLUANTS")
    c1, c2 = st.columns(2)
    with c1:
        dist_poll = st.selectbox(
            "Distribution de",
            options=list(POLLUANT_META.keys()),
            format_func=lambda k: POLLUANT_META[k][0],
            index=0,
            key="dist_sel",
        )
        st.plotly_chart(fig_distribution_interactive(df, dist_poll),
                        use_container_width=True, width="stretch")
    with c2:
        rel_poll = st.selectbox(
            "Relation PM2.5 vs",
            options=[k for k in POLLUANT_META.keys() if k != "pm2_5"],
            format_func=lambda k: POLLUANT_META[k][0],
            index=0,
            key="rel_sel",
        )
        st.plotly_chart(fig_polluants_relation(df, rel_poll),
                        use_container_width=True, width="stretch")


# ══════════════════════════════════════════
#  PAGE : CORRÉLATIONS
# ══════════════════════════════════════════
elif selected_page == "Matrice Corrélations":
    section_title("🔗 RELATIONS & CORRÉLATIONS")
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Densité & Régression PM2.5 vs PM10")
        st.plotly_chart(fig_pm_scatter(df), use_container_width=True, width="stretch")
    with c2:
        st.caption("Matrice de corrélation des polluants")
        st.plotly_chart(fig_correlation_heatmap(corr_matrix), use_container_width=True, width="stretch")


# ══════════════════════════════════════════
#  PAGE : ÉPISODES & PICS
# ══════════════════════════════════════════
elif selected_page == "Pics & Evolutions":
    section_title("📅 ÉPISODES DE POLLUTION PROLONGÉS (AQI > 60 pendant ≥ 6h)")
    st.plotly_chart(fig_episodes_pollution(df), use_container_width=True, width="stretch")

    st.divider()
    section_title("🏆 TOP 15 JOURS LES PLUS POLLUÉS")
    st.caption("AQI maximum journalier — 15 pires jours de la période")
    st.plotly_chart(fig_peaks_bar(peaks), use_container_width=True, width="stretch")


# ══════════════════════════════════════════
#  PAGE : INSIGHTS ML
# ══════════════════════════════════════════
elif selected_page == "Analyses ML":
    section_title("🤖 INSIGHTS POUR LE MODÈLE ML")
    insights = [
        (C["coral"],   "PM2.5 / PM10 : corrélation 0.92 — très colinéaires. Créer le ratio PM2.5/PM10 (= 0.44 en moyenne) comme feature de source de pollution plutôt que garder les deux bruts."),
        (C["card"],    "AQI corrèle fortement avec PM2.5 (0.84) et PM10 (0.80) → ce sont les drivers principaux de l'indice à Cotonou. Le modèle doit absolument intégrer ces deux polluants."),
        (C["teal"],    "Ozone corrèle avec PM (0.57) et SO₂ (0.63) → pollution photochimique. L'ozone monte en journée (pic 13-14h), créer un lag O₃ de 6h pour capturer cet effet."),
        (C["amber"],   "Tendance mensuelle claire : AQI moyen = 49 en Jan, 46 en Fév, 31 en Mar. La saison sèche (Harmattan) est nettement plus polluée. Variable 'month' essentielle."),
        (C["blue"],    "Cycle journalier fort sur PM et AQI : pic nocturne 0h-6h (accumulation), creux en milieu de journée (dispersion thermique). Lags 1h, 6h, 24h sont critiques."),
        (C["danger"],  "572 heures en zone 'Très mauvais' (AQI > 60), dont 38h 'Dangereux' (> 80) — principalement jan-fév. Ces pics correspondent à l'Harmattan du Sahara."),
    ]
    for color, text in insights:
        cols = st.columns([0.02, 0.98])
        with cols[0]:
            st.markdown(f'<div style="color:{color};font-size:20px;margin-top:4px">●</div>',
                        unsafe_allow_html=True)
        with cols[1]:
            st.markdown(
                f'<div style="font-size:13px;line-height:1.7;padding:8px 0;'
                f'border-bottom:1px solid #E2E8F0">{text}</div>',
                unsafe_allow_html=True
            )

    section_title("📋 STATISTIQUES RÉSUMÉES")
    resume = pd.DataFrame({
        "Indicateur": ["PM2.5 Moyen", "PM10 Moyen", "Ozone Moyen", "NO₂ Moyen",
                       "AQI Moyen", "Heures 'Bon'", "Heures 'Moyen'", "Heures 'Mauvais'",
                       "Anomalies détectées"],
        "Valeur": [f"{pm2_5_mean} μg/m³", f"{pm_10_mean} μg/m³",
                   f"{O3_mean} μg/m³", f"{no2_mean} μg/m³",
                   str(AQI), f"{bon_pct}%", f"{moyen_pct}%", f"{mauvais_pct}%",
                   f"{n_anomalies} h"],
        "Seuil OMS": ["12 μg/m³", "40 μg/m³", "100 μg/m³", "10 μg/m³",
                      "50", "—", "—", "—", "—"],
        "Statut": [
            "OK" if pm2_5_mean <= 12 else "Dépassé",
            "OK" if pm_10_mean <= 40 else "Dépassé",
            "OK" if O3_mean <= 100 else " Dépassé",
            "OK" if no2_mean <= 10 else "Dépassé",
            "OK" if AQI <= 50 else "Élevé",
            "—", "—", "—", "—",
        ],
    })
    st.dataframe(resume, use_container_width=True, width="stretch", hide_index=True)

#=============================
# FOOTER
# ============================
from datetime import datetime
st.markdown('<div style="margin-top: 100px;"></div>', unsafe_allow_html=True)
# Ligne 2 : Copyright et Sources

with st.container():
    col_left, col_right = st.columns([0.7, 0.3])
    with col_left:
        st.markdown(f"""
                    <p style="margin-bottom: 8px;">
                        <span class="footer-badge">📡 Live Status</span>
                        <span class="footer-badge" style="margin-left:8px;">🤖 ML Guard</span>
                    </p>
                    <p style="font-size: 13px; color: #64748B; line-height: 1.6;">
                        © {datetime.now().year} — <b>Système de Surveillance Qualité de l'Air</b><br>
                        Données agrégées via <i>Open-Météo API</i> & <i>OpenAQ</i>.<br>
                        Analyses basées sur les seuils directeurs de l'OMS.
                    </p>
                """, unsafe_allow_html=True)
    with col_right:
        st.markdown(f"""
                    <div style="text-align: right;">
                        <p style="font-size: 12px; color: #94A3B8; margin-bottom: 4px;">Dernière synchronisation</p>
                        <p style="color: #3B82F6; font-size: 16px; font-weight: 700; margin: 0;">
                            {datetime.now().strftime('%d %b %Y')}
                        </p>
                        <p style="color: #3B82F6; font-size: 14px; font-weight: 500; margin: 0;">
                            {datetime.now().strftime('%H:%M:%S')}
                        </p>
                    </div>
                """, unsafe_allow_html=True)