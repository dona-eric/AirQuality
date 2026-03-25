"""
air_quality_eda_dashboard.py
=============================
Dashboard interactif Dash + Plotly — EDA Qualité d'air Cotonou
Données : Open-Meteo Air Quality API — Déc 2025 → Mars 2026

"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pathlib
import dash
from dash import dcc, html, Input, Output, callback

# 1. CHARGEMENT & PRÉPARATION

CSV_PATH = pathlib.Path("data/raw/hourly_quality_air_data.csv")

df_raw = pd.read_csv(CSV_PATH)
df_raw["date"] = pd.to_datetime(df_raw["date"], utc=True)
df = df_raw.sort_values("date").reset_index(drop=True)

df["hour"]      = df["date"].dt.hour
df["month"]     = df["date"].dt.month
df["dayofweek"] = df["date"].dt.dayofweek
df["date_str"]  = df["date"].dt.strftime("%Y-%m-%d")
df["month_str"] = df["date"].dt.strftime("%b %Y")

# Ratio PM2.5 / PM10 — signature de la source de pollution
df["pm_ratio"] = (df["pm2_5"] / df["pm10"].replace(0, np.nan)).round(3)

# Niveau qualitatif AQI (normes européennes)
def aqi_label(val):
    if val <= 12:      return "Bon"
    elif val <= 35.5:    return "Moyen"
    else:               return "Mauvais"

AQI_COLORS = {
    "Bon":           "#1cb6b1",
    "Moyen":         "#f39c12",
    "Mauvais":       "#ff0000",
}

df["aqi_level"] = df["pm2_5"].apply(aqi_label)

# calcul stattistiques des PM et AQI selon les nrmes OMS
pm2_5_mean = df['pm2_5'].mean().round(2)
pm_10_mean = df['pm10'].mean().round(2)
pm2_5_p95 = df['pm2_5'].quantile(0.95).round(2)
O3_mean = df_raw['ozone'].mean().round(2)

aqi_level_counts = df["aqi_level"].value_counts()
bon_pct = (aqi_level_counts.get("Bon", 0) / len(df) * 100).round(1)
moyen_pct = (aqi_level_counts.get("Moyen", 0) / len(df) * 100).round(1)
mauvais_pct = (aqi_level_counts.get("Mauvais", 0) / len(df) * 100).round(1)

hours_mauvais = (df["pm2_5"] > 35.5).sum()
hours_moyen = ((df["pm2_5"] > 12) & (df["pm2_5"] <= 35.5)).sum()
hours_bon = (df["pm2_5"] <= 12).sum()

# selon les normes internationales ,lindice de la qualité de l'air se calcule par la formule suivantes

"""
AQI = (valeur_polluant_brute / norme_qualite_air)*50

"""

"""Etant donné qu'à cotonou le polluant le plus frequent est PM2.5 alors je tiens compte"""

AQI = df['european_aqi'].mean().round(2)


# Agrégation journalière
POLL_COLS = ["pm2_5","pm10","carbon_monoxide","carbon_dioxide",
             "sulphur_dioxide","ozone","nitrogen_dioxide",
             "formaldehyde","methane","european_aqi","european_aqi_pm2_5"]

daily = (
    df.groupby("date_str")[POLL_COLS]
    .mean()
    .round(3)
    .reset_index()
)
daily["aqi_level"] = daily["pm2_5"].apply(aqi_label)

# Profil horaire moyen
hourly_profile = (
    df.groupby("hour")[POLL_COLS]
    .mean()
    .round(3)
    .reset_index()
)

# Statistiques mensuelles
monthly = (
    df.groupby("month")[POLL_COLS]
    .mean()
    .round(2)
    .reset_index()
)
monthly["month_label"] = monthly["month"].map(
    {9: "Sept 2025", 10: "Oct 2025", 11: "Nov 2025",12:"Déc 2025", 1:"Jan 2026", 2:"Fév 2026", 3:"Mar 2026"}
)

# Matrice corrélation
CORR_COLS = [
    "pm10", "pm2_5", "carbon_monoxide", "sulphur_dioxide",
    "ozone", "nitrogen_dioxide", "formaldehyde", "european_aqi"
]

available_corr_cols = [c for c in CORR_COLS if df[c].notna().any()]
corr_matrix = df[available_corr_cols].corr().round(3)
corr_short = {
    "pm10": "PM10",
    "pm2_5": "PM2.5",
    "carbon_monoxide": "CO",
    "sulphur_dioxide": "SO2",
    "ozone": "O3",
    "nitrogen_dioxide": "NO2",
    "formaldehyde": "CH2O",
    "european_aqi": "AQI",
}
corr_labels = [corr_short[c] for c in available_corr_cols]

# Pics de pollution AQI > 60
peaks = (
    df[df["european_aqi"] > 60]
    .groupby("date_str")["european_aqi"]
    .max()
    .sort_values(ascending=False)
    .reset_index()
    .head(15)
)

# 2. PALETTE & STYLES

C = {
    "coral":  "#FF6B6B", "blue":   "#4ECDC4",
    "teal":   "#45B7AA", "amber":  "#FFB84D",
    "purple": "#9D84B7", "gray":   "#8E92A9",
    "green":  "#6BCB77", "red":    "#FF6B6B",
    "bg":     "#F5F7FA", "card":   "#FFFFFF",
    "border": "#E0E4E8", "text":   "#2C3E50",
    "text2":  "#7F8C8D", "accent": "#FF6B6B",
}

if AQI <= 50:
    aqi_label = "Bon"
    aqi_color = C["green"]
elif AQI <= 100:
    aqi_label = "Modéré"
    aqi_color = C["amber"]
else:
    aqi_label = "Mauvais"
    aqi_color = C["red"]

POLLUANT_META = {
    "pm2_5":           ("PM2.5 (μg/m³)",        C["coral"],  0,  55),
    "pm10":            ("PM10 (μg/m³)",          C["amber"],  0, 150),
    "european_aqi":    ("AQI Européen",          C["purple"], 0, 100),
    "carbon_monoxide": ("CO (μg/m³)",            C["blue"],   0, 400),
    "ozone":           ("Ozone O₃ (μg/m³)",      C["teal"],   0, 180),
    "nitrogen_dioxide":("NO₂ (μg/m³)",           C["gray"],   0,  15),
    "sulphur_dioxide": ("SO₂ (μg/m³)",           C["amber"],  0,   5),
    "formaldehyde":    ("Formaldéhyde (μg/m³)",  C["purple"], 0,  30),
    "methane":         ("Méthane (μg/m³)",        C["blue"],   0,2000),
}

TEMPLATE = "plotly_white"
CARD_STYLE = {
    "background": C["card"],
    "border": f"1px solid {C['border']}",
    "borderRadius": "16px",
    "padding": "24px",
    "marginBottom": "20px",
    "boxShadow": "0 4px 12px rgba(0,0,0,0.08)",
    "transition": "all 0.3s ease",
}

# =====================3. FIGURES=========================

def fig_aqi_timeseries(polluant: str = "european_aqi") -> go.Figure:

    """Série temporelle journalière d'un polluant avec seuils OMS."""
    label, color, ymin, ymax = POLLUANT_META[polluant]
    roll7 = daily[polluant].rolling(7, min_periods=1).mean()

    fig = go.Figure()

    # Zone de fond colorée selon niveau AQI (uniquement pour AQI)
    if polluant in ["pm2_5", "european_aqi"]:
        zones = [
            (0,  12, C["teal"], "Bon"),
            (12, 35.5, C["amber"], "Moyen"),
            (35.5, 100, C["coral"], "Mauvais"),
            ]
        for lo, hi, lvl_color, lvl_label in zones:
            fig.add_hrect(y0=lo, y1=hi,
                          fillcolor=lvl_color, line_width=0,
                          annotation_text=lvl_label,
                          annotation_position="left",
                          annotation_font_size=10,
                          annotation_font_color=C["text2"])

    fig.add_trace(go.Scatter(
        x=daily["date_str"], y=daily[polluant],
        mode="lines",
        line=dict(color=color, width=1.5),
        name=label,
        hovertemplate="%{x}<br><b>%{y:.1f}</b><extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=daily["date_str"], y=roll7,
        mode="lines",
        line=dict(color=color, width=2, dash="dot"),
        name="Moy. mobile 7j",
        hovertemplate="Moy 7j : %{y:.1f}<extra></extra>",
    ))

    fig.update_layout(
        template=TEMPLATE, height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=1.08),
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor="#eeece6"),
        yaxis=dict(showgrid=True, gridcolor="#eeece6",
                   title=label, range=[ymin, None]),
    )
    return fig


def fig_aqi_distribution() -> go.Figure:
    """Camembert des niveaux AQI + barres de comptage."""
    counts = df["aqi_level"].value_counts()
    ordre  = ["Bon","Moyen","Mauvais"]
    labels = [l for l in ordre if l in counts.index]
    values = [counts[l] for l in labels]
    colors = [AQI_COLORS[l] for l in labels]

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "bar"}]],
        subplot_titles=["Répartition des heures", "Nombre d'heures par niveau"],
    )

    fig.add_trace(go.Pie(
        labels=labels, values=values,
        marker=dict(colors=colors),
        textinfo="percent+label",
        hovertemplate="%{label}<br><b>%{value} heures</b> (%{percent})<extra></extra>",
        hole=0.35,
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        text=values, textposition="outside",
        hovertemplate="%{x}<br><b>%{y} heures</b><extra></extra>",
    ), row=1, col=2)

    fig.update_layout(
        template=TEMPLATE, height=320,
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=False,
    )
    return fig


def fig_hourly_pollutants() -> go.Figure:
    """Profil horaire des 4 polluants principaux."""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["PM2.5 (μg/m³)", "PM10 (μg/m³)",
                         "Ozone O₃ (μg/m³)", "AQI Européen"],
        vertical_spacing=0.14, horizontal_spacing=0.08,
    )

    for (row, col, col_name, color) in [
        (1, 1, "pm2_5",        C["coral"]),
        (1, 2, "pm10",         C["amber"]),
        (2, 1, "ozone",        C["teal"]),
        (2, 2, "european_aqi", C["purple"]),
    ]:
        fig.add_trace(go.Scatter(
            x=hourly_profile["hour"],
            y=hourly_profile[col_name],
            mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(size=5, color=color),
            fill="tozeroy",
            fillcolor=color,
            showlegend=False,
            hovertemplate=f"%{{x}}h → <b>%{{y:.1f}}</b><extra></extra>",
        ), row=row, col=col)

    fig.update_xaxes(title_text="Heure", tickvals=list(range(0,24,3)))
    fig.update_layout(
        template=TEMPLATE, height=380,
        margin=dict(l=10, r=10, t=35, b=10),
    )
    return fig


def fig_monthly_evolution() -> go.Figure:
    """Évolution mensuelle des polluants principaux."""
    fig = go.Figure()

    for col, color, label in [
        ("pm2_5",        C["coral"],  "PM2.5"),
        ("pm10",         C["amber"],  "PM10"),
        ("european_aqi", C["purple"], "AQI"),
        ("ozone",        C["teal"],   "O₃"),
    ]:
        fig.add_trace(go.Bar(
            x=monthly["month_label"],
            y=monthly[col],
            name=label,
            marker_color=color,
            text=monthly[col].round(1),
            textposition="outside",
            hovertemplate="%{x}<br><b>%{y:.1f}</b><extra>" + label + "</extra>",
        ))

    fig.update_layout(
        template=TEMPLATE, height=320,
        barmode="stack",
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=1.08),
        yaxis=dict(title="Valeur moyenne", gridcolor="#eeece6"),
        xaxis=dict(categoryorder="array",
                   categoryarray=["Sept 2025", "Oct 2025", "Nov 2025","Déc 2025","Jan 2026","Fév 2026","Mar 2026"]),
    )
    return fig


def fig_pm_scatter() -> go.Figure:
    """Scatter PM2.5 vs PM10 colorié par AQI, avec ligne de régression."""
    subset = df[["pm2_5", "pm10", "european_aqi", "hour", "aqi_level"]].dropna(
        subset=["pm2_5", "pm10", "european_aqi"]
    )

    sample = subset.sample(min(2000, len(subset)), random_state=42)

    fig = px.density_contour(
        sample, 
        x="pm10", 
        y="pm2_5",
        color="aqi_level",
        # title="Relation PM2.5 vs PM10 (densité)",
    )

    fig.add_trace(go.Scatter(
        x=sample["pm10"],
        y=sample["pm2_5"],
        mode="markers",
        marker=dict(size=3, opacity=0.3, color=C["gray"]),
        showlegend=False
    ))

    # Ligne de tendance réelle (régression)
    z = np.polyfit(sample["pm10"], sample["pm2_5"], 1)
    p = np.poly1d(z)


    # Ligne PM2.5 = 0.44 × PM10 (ratio moyen observé)
    x_range = np.linspace(sample["pm10"].min(), sample["pm10"].max(), 50)
    fig.add_trace(go.Scatter(
        x=x_range, y=p(x_range),
        mode="lines",
        line=dict(color=C["red"], dash="dash", width=2),
        name=f"Régression (y={z[0]:.2f}x+{z[1]:.2f})",
        hoverinfo="skip",
    ))

    fig.update_traces(marker=dict(size=4), selector=dict(mode="markers"))
    fig.update_layout(
        template=TEMPLATE, height=350,
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_colorbar=dict(title="AQI", thickness=12, len=0.8),
    )
    return fig


#======================= RELATION DE PM2.5 AVEC LES AUTRES POLLUANTS===============

def fig_polluants(variable: str) -> go.Figure:
    """relation entre PM2.5 avec les autres polluants"""


    label = corr_short.get(variable, variable)
    subset = df[['pm2_5', variable]].dropna()

    # Nuage de points pour visualiser la relation entre deux variables continues
    fig = px.scatter(
        subset,
        x=variable,
        y="pm2_5",
        color=df['aqi_level'],
        opacity=0.65,
        render_mode="webgl",  # plus fluide quand beaucoup de points
        marginal_x="histogram",
        marginal_y="histogram",
    )
    
    fig.update_layout(
        template=TEMPLATE, height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=True,
        xaxis_title=label,
        yaxis_title="PM2.5",
        )

    return fig
#=======================HEATMAP GLOABLE=======================

def fig_correlation_heatmap() -> go.Figure:
    """Heatmap de corrélation des polluants."""
    available_corr_cols = [c for c in CORR_COLS if df[c].notna().any()]
    corr = df[available_corr_cols].corr().round(3)
    labels = [corr_short[c] for c in available_corr_cols]
    z    = corr_matrix.values
    text = [[f"{v:.2f}" for v in row] for row in z]

    fig = go.Figure(go.Heatmap(
        z=z, x=labels, y=labels,
        text=text, texttemplate="%{text}",
        textfont=dict(size=11),
        colorscale=[[0, 'blue'], [0.5, 'green'], [1.0, 'rgb(0, 0, 255)'],
        ],
        zmid=0, zmin=-1, zmax=1,
        colorbar=dict(title="correlation", thickness=12, len=0.8),
        hovertemplate="%{y} / %{x}<br><b>r = %{z:.3f}</b><extra></extra>",
    ))
    fig.update_layout(
        template=TEMPLATE, height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(side="bottom"),
        yaxis=dict(autorange="reversed"),
    )
    return fig
#==================== HEATMAP JOUR * HEURE====================
def fig_hour_day_heatmap() -> go.Figure:
    pivot = df.pivot_table(
        index="dayofweek",
        columns="hour",
        values="pm2_5",
        aggfunc="mean"
    )

    days = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=list(range(24)),
        y=days,
        colorscale="YlOrRd",
        colorbar=dict(title="PM2.5"),
    ))

    fig.update_layout(
        template=TEMPLATE,
        title="Cycle pollution : heure vs jour",
        xaxis_title="Heure",
        yaxis_title="Jour",
        height=350
    )

    return fig

#======================= TP 15 JOURS AVEC AQI ÉLÉVÉ================
def fig_peaks_bar() -> go.Figure:
    """Top 15 jours avec AQI le plus élevé."""
    fig = go.Figure(go.Bar(
        x=peaks["date_str"],
        y=peaks["european_aqi"],
        marker=dict(
            color=peaks["european_aqi"],
            colorscale=[[0, C["amber"]], [0.5, C["coral"]], [1.0, C["red"]]],
            colorbar=dict(title="AQI", thickness=10),
        ),
        text=peaks["european_aqi"].round(1),
        textposition="outside",
        hovertemplate="%{x}<br><b>AQI max : %{y:.1f}</b><extra></extra>",
    ))

    # Seuil "Très mauvais"
    fig.add_hline(y=60, line=dict(color=C["red"], dash="dash", width=1.5),
                  annotation_text="Seuil 'Très mauvais' (60)",
                  annotation_font_size=10)

    fig.update_layout(
        template=TEMPLATE, height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(tickangle=-35),
        yaxis=dict(title="AQI max journalier", gridcolor="#e6d8ae", range=[0, 95]),
        showlegend=False,
    )
    return fig

### =================================== DISTRIBUTION DE PM2.5 PAR MOIS==================
def fig_monthly_boxplot() -> go.Figure:
    fig = px.box(
        df,
        x="month_str",
        y="pm2_5",
        color="month_str",
        title="Distribution PM2.5 par mois"
    )

    fig.update_layout(
        template=TEMPLATE,
        showlegend=False,
        height=350
    )

    return fig


####================================== DISTRIBUTION INTERACTIVE======================
def fig_distribution_interactive(variable: str = "pm2_5") -> go.Figure:
    """Histogramme + box plot en subplot pour une variable."""
    meta = POLLUANT_META.get(variable, (variable, C["gray"], 0, 200))
    label, color, _, _ = meta
    vals = df[variable].dropna()

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.04,
        shared_xaxes=True,
    )

    fig.add_trace(go.Histogram(
        x=vals, nbinsx=50,
        marker_color=color,
        marker_line=dict(color=color, width=0.5),
        hovertemplate="Plage : %{x}<br>Fréquence : %{y}<extra></extra>",
        name=label,
    ), row=1, col=1)

    fig.add_trace(go.Box(
        x=vals, boxmean="sd",
        marker_color=color,
        line_color=color,
        fillcolor=color ,
        showlegend=False,
        hovertemplate=f"<b>%{{x:.1f}}</b><extra>{label}</extra>",
    ), row=2, col=1)

    # Lignes de référence OMS
    oms_seuils = {
        "pm2_5": [(12, "OMS 24h", C["amber"]), (25, "UE 24h", C["coral"])],
        "pm10":  [(35.5, "OMS 24h", C["amber"]), (50, "UE 24h", C["coral"])],
        "ozone": [(100, "OMS 8h", C["amber"])],
    }
    for lo, lbl, lcolor in oms_seuils.get(variable, []):
        fig.add_vline(x=lo, line=dict(color=lcolor, dash="dash", width=1.5),
                      annotation_text=lbl, annotation_font_size=10,
                      annotation_position="top right")

    fig.update_layout(
        template=TEMPLATE, height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        bargap=0.05,
        xaxis2=dict(title=label),
        yaxis=dict(title="Fréquence", gridcolor="#d1c9b4"),
    )
    return fig


# 4. LAYOUT DASH

def kpi_card(label, value, sub=None, color=None):
    return html.Div([
        html.Div(label, style={"fontSize":"12px","color":C["text2"],"marginBottom":"8px","fontWeight":"600","letterSpacing":"0.5px","textTransform":"uppercase"}),
        html.Div(value, style={"fontSize":"28px","fontWeight":"700",
                               "color": color or C["text"], "lineHeight":"1","marginBottom":"8px"}),
        html.Div(sub or "", style={"fontSize":"11px","color":C["text2"],"marginTop":"0px","fontWeight":"400"}),
    ], style={"background":C["card"],"border":f"3px solid {color or C['text2']}","borderRadius":"14px","padding":"18px 16px","flex":"1","boxShadow":"0 2px 8px rgba(0,0,0,0.06)","borderLeft":f"4px solid {color or C['text2']}"})

def section(title):
    return html.Div([
        html.Span("▸", style={"color":C["accent"],"marginRight":"8px","fontSize":"14px"}),
        html.Span(title, style={"fontWeight":"700","color":C["text"]}),
    ], style={
        "fontSize":"14px","fontWeight":"700","color":C["text"],
        "letterSpacing":"0.5px","marginBottom":"16px","marginTop":"28px",
        "display":"flex","alignItems":"center","paddingBottom":"12px",
        "borderBottom":f"2px solid {C['border']}",
    })

app = dash.Dash(__name__, title="Indice de la Qualité d'Air à Cotonou", suppress_callback_exceptions=True)

app.layout = html.Div(
    style={"fontFamily":"system-ui,-apple-system,sans-serif",
           "background":C["bg"],"minHeight":"100vh",
           "padding":"24px","color":C["text"]},
    children=[

        # En-tête
        html.H1("Qualité de l'Air · Pollution d'Air · Littoral-Cotonou, Bénin",
                style={"fontSize":"42px","fontWeight":"800","marginBottom":"12px","color":C["text"],"backgroundImage":f"linear-gradient(135deg, {C['coral']}, {C['purple']})","backgroundClip":"text","-webkit-backgroundClip":"text","-webkit-textFillColor":"transparent","letterSpacing":"-0.5px"}),
        html.P("Niveau de pollution de l'air PM2.5, PM10 à Cotonou · Déc 2025 - Mar 2026",
               style={"fontSize":"15px","color":C["text2"],"marginBottom":"28px","fontWeight":"500","letterSpacing":"0.3px"}),

        #  KPIs 
        html.Div([
            kpi_card("AQI",  f"{AQI}", aqi_label, aqi_color),
            kpi_card("PM2.5 moyen",      f"{pm2_5_mean} μg/m³", f"P95 = {pm2_5_p95}", C["blue"]),
            kpi_card("Niveau dominant",  
                     "Mauvais" if mauvais_pct > 50 else ("Modéré" if moyen_pct > 50 else "Bon"),
                     f"Mauvais {mauvais_pct}% · Modéré {moyen_pct}% · Bon {bon_pct}%", C["purple"]),
            kpi_card("PM10 moyen",       f"{pm_10_mean} μg/m³", None, C["amber"]),
            kpi_card("Ozone moyen",      f"{O3_mean} μg/m³", None, C["teal"]),
            kpi_card("Rapport PM2.5/PM10", f"{df['pm_ratio'].mean().round(2)}", "Source mixte biomasse/poussière", C["green"]),
        ], style={"display":"flex","gap":"14px","marginBottom":"28px","flexWrap":"wrap"}),

        #  Série temporelle interactive
        section("ÉVOLUTION TEMPORELLE"),
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id="ts-poll",
                    options=[{"label": v[0], "value": k}
                             for k,v in POLLUANT_META.items()],
                    value="pm2_5",
                    clearable=False,
                    style={"fontSize":"13px","width":"280px","marginBottom":"10px"},
                ),
                dcc.Graph(id="ts-chart", config={"displayModeBar": False}),
            ])
        ], style=CARD_STYLE),



        # Distribution AQI + Mensuel
        section("DISTRIBUTION AQI & TENDANCE MENSUELLE"),
        html.Div([
            html.Div([
                html.Div([
                    html.P("📊 Répartition des niveaux AQI — toute la période",
                           style={"fontSize":"14px","fontWeight":"600",
                                  "color":C["text"],"marginBottom":"12px","letterSpacing":"0.3px"}),
                    dcc.Graph(figure=fig_aqi_distribution(),
                              config={"displayModeBar":False}),
                ], style={**CARD_STYLE,"flex":"1.2"}),

                html.Div([
                    html.P("📈 Évolution mensuelle — comparaison polluants",
                           style={"fontSize":"14px","fontWeight":"600",
                                  "color":C["text"],"marginBottom":"12px","letterSpacing":"0.3px"}),
                    dcc.Graph(figure=fig_monthly_evolution(),
                              config={"displayModeBar":False}),
                ], style={**CARD_STYLE,"flex":"1"}),
            ], style={"display":"flex","gap":"16px"}),
        ]),

        # Profil horaire 
        section("PROFIL HORAIRE MOYEN - CYCLE JOURNALIER"),
        html.Div([
            html.P("⏰ Profil horaire moyen des 4 indicateurs clés",
                   style={"fontSize":"14px","fontWeight":"600",
                          "color":C["text"],"marginBottom":"12px","letterSpacing":"1.3px"}),
            dcc.Graph(figure=fig_hourly_pollutants(),
                      config={"displayModeBar":False}),
        ], style=CARD_STYLE),

        section("ANALYSE TEMPORELLE AVANCÉE"),
        html.Div([
            html.Div([
                html.P("Structure de la Pollution Journalière",
                        style={"fontSize":"14px","fontWeight":"600",
                                "color":C["text"],"marginBottom":"12px"}),
                dcc.Graph(figure=fig_hour_day_heatmap(),
                        config={"displayModeBar":False}),
                    ], style={**CARD_STYLE,"flex":"1"}),

            html.Div([
                html.P("Distribution Mensuelle",
                    style={"fontSize":"14px","fontWeight":"600",
                            "color":C["text"],"marginBottom":"12px"}),
                dcc.Graph(figure=fig_monthly_boxplot(),
                    config={"displayModeBar":False}),
                ], style={**CARD_STYLE,"flex":"1"}),
            ], style={"display":"flex","gap":"16px"}),

        # Distribution interactive 
        section("DISTRIBUTION DES POLLUANTS"),
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id="dist-poll",
                    options=[{"label": v[0], "value": k}
                            for k,v in POLLUANT_META.items()],
                    value="pm2_5",
                    clearable=False,
                    style={"fontSize":"13px","width":"320px","marginBottom":"16px","padding":"8px"},
                ),
                dcc.Graph(id="dist-chart", config={"displayModeBar":False}),
            ], style={**CARD_STYLE, "flex":"1 1 360px", "minWidth":"320px"}),

            html.Div([
                html.P("Analyse des relations entre PM2.5 et les autres polluants", 
                       style={"fontSize": "13px", "color": C['text']}),
                dcc.Dropdown(
                    id="rel-variable",
                    # on retire PM2.5 pour éviter la comparaison d'une variable avec elle‑même
                    options=[{"label": v[0], "value": k}
                             for k, v in POLLUANT_META.items() if k != "pm2_5"],
                    value="pm10",
                    clearable=False,
                ),
                dcc.Graph(id="rel-chart", config={"displayModeBar":False})
            ], style={**CARD_STYLE, "flex":"1 1 360px", "minWidth":"320px"})
        ], style={"display":"flex","gap":"16px","flexWrap":"wrap"}),

        #  Scatter PM + Corrélation 
        section("RELATIONS DENSITÉ ENTRE PM2.5 vs PM10"),
        html.Div([
            html.Div([
                html.Div([
                    html.P("Rélation de densité et Régression entre PM2.5 vs PM10",
                           style={"fontSize":"12px","fontWeight":"500",
                                  "color":C["text2"],"marginBottom":"8px"}),
                    dcc.Graph(figure=fig_pm_scatter(),
                              config={"displayModeBar":False}),
                ], style={**CARD_STYLE,"flex":"1"}),

                html.Div([
                    html.P("Matrice de corrélation des polluants",
                           style={"fontSize":"12px","fontWeight":"500",
                                  "color":C["text2"],"marginBottom":"8px"}),
                    dcc.Graph(figure=fig_correlation_heatmap(),
                              config={"displayModeBar":False}),
                ], style={**CARD_STYLE,"flex":"1"}),
            ], style={"display":"flex","gap":"12px"}),
        ]),


        #  Pics de pollution 
        section("JOURS LES PLUS POLLUÉS — TOP 15"),
        html.Div([
            html.P("AQI maximum journalier — 15 pires jours de la période",
                   style={"fontSize":"12px","fontWeight":"500",
                          "color":C["text2"],"marginBottom":"8px"}),
            dcc.Graph(figure=fig_peaks_bar(), config={"displayModeBar":False}),
        ], style=CARD_STYLE),

        #  Insights ML 
        section("INSIGHTS POUR LE MODÈLE ML"),
        html.Div([
            *[
                html.Div([
                    html.Span("●", style={"color":color,"marginRight":"8px",
                                          "fontSize":"16px","flexShrink":"0"}),
                    html.Span(text, style={"fontSize":"13px","lineHeight":"1.6"}),
                ], style={"display":"flex","alignItems":"flex-start","marginBottom":"10px"})
                for color, text in [
                    (C["coral"],  "PM2.5 / PM10 : corrélation 0.92 — très colinéaires. Créer le ratio PM2.5/PM10 (= 0.44 en moyenne) comme feature de source de pollution plutôt que garder les deux bruts."),
                    (C["purple"], "AQI corrèle fortement avec PM2.5 (0.84) et PM10 (0.80) → ce sont les drivers principaux de l'indice à Cotonou. Le modèle doit absolument intégrer ces deux polluants."),
                    (C["teal"],   "Ozone corrèle avec PM (0.57) et SO₂ (0.63) → pollution photochimique. L'ozone monte en journée (pic 13-14h), créer un lag O₃ de 6h pour capturer cet effet."),
                    (C["amber"],  "Tendance mensuelle claire : AQI moyen = 49 en Jan, 46 en Fév, 31 en Mar. La saison sèche (Harmattan) est nettement plus polluée. Variable 'month' essentielle."),
                    (C["blue"],   "Cycle journalier fort sur PM et AQI : pic nocturne 0h-6h (accumulation), creux en milieu de journée (dispersion thermique). Lags 1h, 6h, 24h sont critiques."),
                    (C["red"],    "572 heures en zone 'Très mauvais' (AQI > 60), dont 38h 'Dangereux' (> 80) — principalement jan-fév. Ces pics correspondent à l'Harmattan du Sahara. Détecter comme anomalies avec IsolationForest."),
                ]
            ]
        ], style={**CARD_STYLE,"background":"#f0ede6","border":"none"}),
    ]
)


# 5. CALLBACKS

@callback(Output("ts-chart","figure"), Input("ts-poll","value"))
def update_ts(pollutant):
    return fig_aqi_timeseries(pollutant)

@callback(Output("dist-chart","figure"), Input("dist-poll","value"))
def update_dist(variable):
    return fig_distribution_interactive(variable)

@callback(Output('rel-chart', "figure"), Input("rel-variable", "value"))
def update_matrix(variable):
    return fig_polluants(variable)

# 6. LANCEMENT

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  Dashboard EDA — Qualité d'air Cotonou")
    print("  http://127.0.0.1:8051")
    print("="*55 + "\n")
    app.run(debug=True, host="127.0.0.1", port=8051)
