"""
meteo_eda_dashboard.py
======================
Dashboard interactif Dash + Plotly pour l'EDA des données météo.
Données : Open-Meteo Forecast API — Cotonou, Bénin — Jan-Mars 2026
"""
import logging
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pathlib
import dash
from dash import dcc, html, Input, Output, callback


logging.basicConfig(level=logging.INFO, 
                            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                            handlers=[logging.FileHandler('app.log'),logging.StreamHandler()
                                      ])

logging.info("TABLEAU DE BOARD POUR DONNÉES MÉTÉOROLOGIQUES À COTONOU")
# 1. CHARGEMENT & PRÉPARATION DES DONNÉES


CSV_PATH = pathlib.Path("data/raw/hourly_meteo_data.csv")

if CSV_PATH.exists:
    df_raw = pd.read_csv(CSV_PATH)
    logging.info("Données météorologiques chargés avec succès")

    logging.info("Etape 1: Extraction des features de la date")
    df_raw["date"] = pd.to_datetime(df_raw["date"], utc=True)

    df = df_raw.dropna(subset=["temperature_2m"]).copy()
    df = df.sort_values("date").reset_index(drop=True)

    # Features dérivées utiles pour l'EDA
    df["hour"]      = df["date"].dt.hour
    df["dayofweek"] = df["date"].dt.dayofweek
    df["month"]     = df["date"].dt.month
    df["date_local"]= df["date"].dt.tz_convert("Africa/Porto-Novo")
else:
    logging.error(f"{CSV_PATH} doesn't exist")

# Agrégation journalière
daily = (
    df.set_index("date").resample("D").agg(
        temp_mean=("temperature_2m",       "mean"),
        temp_min= ("temperature_2m",       "min"),
        temp_max= ("temperature_2m",       "max"),
        hum_mean= ("relative_humidity_2m", "mean"),
        precip=   ("precipitation",        "sum"),
        wind_mean=("wind_speed_80m",       "mean"),
        pressure= ("surface_pressure",     "mean"),
        apptemp=  ("apparent_temperature", "mean"),
    ).round(3).reset_index()
)

# Profil horaire moyen
hourly_profile = (df.groupby("hour").agg(
        temp=   ("temperature_2m",       "mean"),
        hum=    ("relative_humidity_2m", "mean"),
        wind=   ("wind_speed_80m",       "mean"),
        apptemp=("apparent_temperature", "mean"),
        precip= ("precipitation",        "mean"),
    )
    .round(2)
    .reset_index()
)

# Matrice de corrélation
CORR_COLS = [
    "temperature_2m", "relative_humidity_2m", "precipitation",
    "surface_pressure", "apparent_temperature", "wind_speed_80m",
    "temperature_80m", "soil_temperature_18cm", "soil_moisture_3_to_9cm"
    ]
corr_cols_present = [c for c in CORR_COLS if c in df.columns]
corr_matrix = df[corr_cols_present].dropna().corr().round(3)
corr_labels_short = {
    "temperature_2m":         "temp 2m",
    "relative_humidity_2m":   "humidité",
    "precipitation":          "précip",
    "surface_pressure":       "pression",
    "apparent_temperature":   "ressenti",
    "wind_speed_80m":         "vent 80m",
    "temperature_80m":        "temp 80m",
    "soil_temperature_18cm":  "sol temp",
    "soil_moisture_3_to_9cm": "sol hum",
}
corr_display = [corr_labels_short.get(c, c) for c in corr_cols_present]

# 2. PALETTE DE COULEURS

COLORS = {
    "coral":  "#ff0000",
    "blue":   "#006eff",
    "teal":   "#0db3d4",
    "amber":  "#ff0000",
    "purple": "#3ebcc7",
    "gray":   "#888780",
    "bg":     "#f8f7f3",
    "card":   "#ffffff",
    "border": "#e8e6df",
    "text":   "#1a1a18",
    "text2":  "#5f5e5a",
}

PLOTLY_TEMPLATE = "plotly_white"

# 3. FIGURES PLOTLY

def fig_timeseries(variable: str) -> go.Figure:
    """Série temporelle journalière pour la variable choisie."""
    meta = {
        "temp_mean": ("Température moyenne (°C)",  COLORS["coral"],  "°C"),
        "hum_mean":  ("Humidité moyenne (%)",       COLORS["blue"],   "%"),
        "wind_mean": ("Vent moyen à 80m (km/h)",    COLORS["teal"],   "km/h"),
        "pressure":  ("Pression de surface (hPa)",  COLORS["purple"], "hPa"),
        "precip":    ("Précipitations cumulées (mm)", COLORS["blue"],  "mm"),
        "soil_temperature_18cm": ("Température du Sol à 18cm", COLORS['amber'], "°C")
    }
    label, color, unit = meta[variable]

    fig_time_series = go.Figure()

    # Bande min-max pour la température
    if variable == "temp_mean" and "temp_min" in daily.columns:
        fig_time_series.add_trace(go.Scatter(
            x=pd.concat([daily["date"], daily["date"][::-1]]),
            y=pd.concat([daily["temp_max"], daily["temp_min"][::-1]]),
            fill="toself",
            fillcolor=color,
            line=dict(color="rgba(0,0,0,0)"),
            name="Min-Max",
            hoverinfo="skip",
        ))

    fig_time_series.add_trace(go.Scatter(
        x=daily["date"],
        y=daily[variable],
        mode="lines",
        line=dict(color=color, width=2),
        name=label,
        hovertemplate=f"%{{x|%d %b}}<br><b>%{{y:.1f}} {unit}</b><extra></extra>",
    ))

    # Moyenne mobile 7j
    rolling = daily[variable].rolling(7, min_periods=1).mean()
    fig_time_series.add_trace(go.Scatter(
        x=daily["date"],
        y=rolling,
        mode="lines",
        line=dict(color=color, width=1.5, dash="dot"),
        name="Moy. mobile 7j",
        hovertemplate=f"Moy 7j : %{{y:.1f}} {unit}<extra></extra>",
    ))

    fig_time_series.update_layout(
        template=PLOTLY_TEMPLATE,
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=1.08, x=0),
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor="#d9ceab"),
        yaxis=dict(showgrid=True, gridcolor="#eeece6", title=unit),
    )
    return fig_timeseries


def fig_hourly_profile() -> go.Figure:
    """Profil horaire moyen : température + humidité sur axes doubles."""
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

    fig2.add_trace(go.Scatter(
        x=hourly_profile["hour"],
        y=hourly_profile["temp"],
        mode="lines+markers",
        name="Temp (°C)",
        line=dict(color=COLORS["coral"], width=2.5),
        marker=dict(size=5),
        hovertemplate="<b>%{y:.1f}°C</b><extra>Température</extra>",
    ), secondary_y=False)

    fig2.add_trace(go.Scatter(
        x=hourly_profile["hour"],
        y=hourly_profile["hum"],
        mode="lines+markers",
        name="Humidité (%)",
        line=dict(color=COLORS["blue"], width=2.5),
        marker=dict(size=5),
        hovertemplate="<b>%{y:.1f}%</b><extra>Humidité</extra>",
    ), secondary_y=True)

    fig2.add_trace(go.Scatter(
        x=hourly_profile["hour"],
        y=hourly_profile["wind"],
        mode="lines",
        name="Vent (km/h)",
        line=dict(color=COLORS["teal"], width=1.5, dash="dash"),
        hovertemplate="<b>%{y:.1f} km/h</b><extra>Vent</extra>",
    ), secondary_y=False)

    fig2.update_xaxes(title_text="Heure (UTC)", tickvals=list(range(0, 24, 2)))
    fig2.update_yaxes(title_text="Temp / Vent", secondary_y=False, gridcolor="#eeece6")
    fig2.update_yaxes(title_text="Humidité (%)", secondary_y=True, showgrid=False)
    fig2.update_layout(
        template=PLOTLY_TEMPLATE,
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=1.08),
        hovermode="x unified",
    )
    return fig2


def fig_distribution(variable: str) -> go.Figure:
    """Histogramme + courbe KDE pour une variable."""
    meta = {
        "temperature_2m":       ("Température 2m(°C)",        COLORS["coral"]),
        "temperature_80m":      ("Température 80m(°C)",      COLORS['amber']),
        "relative_humidity_2m": ("Humidité relative (%)",   COLORS["blue"]),
        "wind_speed_80m":       ("Vitesse du vent (km/h)",  COLORS["teal"]),
        "surface_pressure":     ("Pression (hPa)",          COLORS["purple"]),
        "precipitation":        ("Précipitations (mm)",     COLORS["text2"]),
        "soil_temperature_18cm": ("Température du Sol à 18cm", COLORS['card'])
    }
    label, color = meta.get(variable, (variable, COLORS["gray"]))
    vals = df[variable].dropna()

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=vals,
        nbinsx=40,
        name=label,
        marker_color=color,
        marker_line=dict(color=color, width=0.5),
        hovertemplate="Plage : %{x}<br>Fréquence : %{y}<extra></extra>",
    ))

    # Ligne médiane
    median = vals.median()
    fig.add_vline(
        x=median,
        line=dict(color=color, dash="dash", width=1.5),
        annotation_text=f"Médiane : {median:.2f}",
        annotation_position="top right",
        annotation_font_size=11,
    )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        bargap=0.05,
        xaxis=dict(title=label),
        yaxis=dict(title="Fréquence", gridcolor="#eeece6"),
    )
    return fig


def fig_correlation_heatmap() -> go.Figure:
    """Heatmap de corrélation annotée."""
    z = corr_matrix.values
    text = [[f"{v:.2f}" for v in row] for row in z]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=corr_display,
        y=corr_display,
        text=text,
        texttemplate="%{text}",
        textfont=dict(size=11),
        colorscale=[[0, 'green'], [0.5, 'red'], [1.0, 'rgb(0, 0, 255)']],
        zmid=0,
        zmin=-1, zmax=1,
        colorbar=dict(title="r", thickness=12, len=0.8),
        hovertemplate="%{y} / %{x}<br><b>r = %{z:.3f}</b><extra></extra>",
    ))

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=360,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(side="bottom", tickangle=-30),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def fig_scatter_temp_hum() -> go.Figure:
    """Scatter temperature vs humidité, colorié par heure."""
    sample = df[["temperature_2m", "relative_humidity_2m", "hour",
                 "precipitation", "apparent_temperature", "temperature_80m",
                 "soil_temperature_18cm"]].dropna()

    fig = px.scatter(
        sample,
        x="temperature_2m",
        y="relative_humidity_2m",
        color="hour",
        color_continuous_scale="RdYlBu_r",
        labels={
            "temperature_2m":       "Température sur 2m (°C)",
            "temperature_80m":       "Température sur 80m(°C)",
            "relative_humidity_2m": "Humidité (%)",
            "hour":                 "Heure",
        },
        opacity=0.5,
        hover_data={"apparent_temperature": ":.1f", "precipitation": ":.2f"},
    )
    fig.update_traces(marker=dict(size=4))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_colorbar=dict(title="Heure", thickness=12, len=0.8),
    )
    return fig


def fig_wind_rose() -> go.Figure:
    """Rose des vents à partir de wind_direction_80m et wind_speed_80m."""
    wd = df["wind_direction_80m"].dropna()
    ws = df["wind_speed_80m"].dropna()

    # Aligne les index
    valid = df[["wind_direction_80m", "wind_speed_80m"]].dropna()
    directions = valid["wind_direction_80m"].values
    speeds     = valid["wind_speed_80m"].values

    # Découpe en 16 secteurs
    n_sectors = 16
    sector_size = 360 / n_sectors
    sectors = [f"{int(i * sector_size)}°" for i in range(n_sectors)]
    speed_bins  = [0, 5, 10, 15, 20, 50]
    speed_labels= ["0-5", "5-10", "10-15", "15-20", ">20"]
    speed_colors= [COLORS["teal"], COLORS["blue"], COLORS["amber"],
                   COLORS["coral"], COLORS["purple"]]

    fig = go.Figure()
    for i, (lo, hi) in enumerate(zip(speed_bins[:-1], speed_bins[1:])):
        mask = (speeds >= lo) & (speeds < hi)
        d_bin = directions[mask]
        counts = np.zeros(n_sectors)
        for angle in d_bin:
            idx = int((angle % 360) / sector_size) % n_sectors
            counts[idx] += 1
        fig.add_trace(go.Barpolar(
            r=counts,
            theta=sectors,
            name=f"{speed_labels[i]} km/h",
            marker_color=speed_colors[i],
            opacity=0.85,
        ))

    fig.update_layout(
        template="plotly_white",
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        polar=dict(
            radialaxis=dict(showticklabels=False, ticks=""),
            angularaxis=dict(direction="clockwise", rotation=90),
        ),
        legend=dict(orientation="h", y=-0.08, font=dict(size=11)),
    )
    return fig


def fig_boxplot_by_hour() -> go.Figure:
    """Boxplot de la température par heure de la journée."""
    fig = go.Figure()
    for h in range(24):
        vals = df[df["hour"] == h]["temperature_2m"].dropna()
        fig.add_trace(go.Box(
            y=vals,
            name=str(h),
            marker_color=COLORS["coral"],
            line_color=COLORS["coral"],
            showlegend=False,
            boxmean="sd",
        ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title="Heure de la journée"),
        yaxis=dict(title="Température (°C)", gridcolor="#eeece6"),
    )
    return fig


def fig_precipitation_bar() -> go.Figure:
    """Barres de précipitations journalières, colorié par intensité."""
    rainy = daily[daily["precip"] > 0.0].copy()
    rainy["color"] = rainy["precip"].apply(
        lambda x: COLORS["blue"] if x < 1 else (COLORS["teal"] if x < 3 else COLORS["coral"])
    )
    fig = go.Figure(go.Bar(
        x=rainy["date"],
        y=rainy["precip"],
        marker_color=rainy["color"],
        hovertemplate="%{x|%d %b}<br><b>%{y:.1f} mm</b><extra></extra>",
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title="Date"),
        yaxis=dict(title="mm", gridcolor="#eeece6"),
        showlegend=False,
    )
    return fig


# ──────────────────────────────────────────────
# 4. LAYOUT DASH
# ──────────────────────────────────────────────

CARD_STYLE = {
    "background": COLORS["card"],
    "border":     f"0.5px solid {COLORS['border']}",
    "borderRadius": "12px",
    "padding":    "16px",
    "marginBottom": "12px",
}

def kpi_card(label, value, sub=None, color=COLORS["text"]):
    return html.Div([
        html.Div(label, style={"fontSize": "11px", "color": COLORS["text2"], "marginBottom": "4px"}),
        html.Div(value, style={"fontSize": "22px", "fontWeight": "500", "color": color, "lineHeight": "1"}),
        html.Div(sub or "", style={"fontSize": "11px", "color": "#9c9a92", "marginTop": "3px"}),
    ], style={
        "background": "#f0ede6",
        "borderRadius": "10px",
        "padding": "12px 14px",
        "flex": "1",
    })


app = dash.Dash(
    __name__,
    title="EDA Météo — Cotonou",
    suppress_callback_exceptions=True,
)

app.layout = html.Div(
    style={"fontFamily": "system-ui, -apple-system, sans-serif",
           "background": COLORS["bg"], "minHeight": "100vh",
           "padding": "24px", "color": COLORS["text"]},
    children=[

        # ── En-tête ──────────────────────────────
        html.H1("EDA — Données Météo Cotonou, Bénin",
                style={"fontSize": "20px", "fontWeight": "500", "marginBottom": "4px"}),
        html.P("Open-Meteo Forecast API · Janv – Mars 2026 · Résolution horaire",
               style={"fontSize": "13px", "color": COLORS["text2"], "marginBottom": "16px"}),

        html.Div(
            "⚠  518 lignes vides (19 déc → 18 jan) — coordonnées Berlin dans le script original. "
            "1 858 lignes valides sur 2 376. Corriger latitude=6.37, longitude=2.42 pour Cotonou.",
            style={
                "background": "#fdf3e3", "border": "0.5px solid #e8a020",
                "borderRadius": "8px", "padding": "9px 14px",
                "fontSize": "12px", "color": "#7a4f10", "marginBottom": "16px",
            }
        ),

        # ── KPIs ─────────────────────────────────
        html.Div([
            kpi_card("Temp. moyenne",  "29.3°C",   "min 24.1 · max 36.7", COLORS["coral"]),
            kpi_card("Humidité moy.",  "77.3%",    "min 27 · max 97",     COLORS["blue"]),
            kpi_card("Précip. totales","49.6 mm",  "sur 78 jours valides"),
            kpi_card("Vent moyen",     "15.9 km/h","à 80m d'altitude",    COLORS["teal"]),
            kpi_card("Période",        "Jan→Mar 26","78 jours valides"),
            kpi_card("Lignes valides", "1 858",    "sur 2 376 total"),
        ], style={"display": "flex", "gap": "10px", "marginBottom": "20px", "flexWrap": "wrap"}),

        # ── Série temporelle ─────────────────────
        html.Div("ÉVOLUTION JOURNALIÈRE", style={
            "fontSize": "11px", "fontWeight": "500", "color": "#9c9a92",
            "letterSpacing": ".07em", "marginBottom": "8px"
        }),
        html.Div([
            html.Div([
                dcc.RadioItems(
                    id="ts-variable",
                    options=[
                        {"label": "  Température",  "value": "temp_mean"},
                        {"label": "  Humidité",     "value": "hum_mean"},
                        {"label": "  Vent",         "value": "wind_mean"},
                        {"label": "  Pression",     "value": "pressure"},
                        {"label": "  Précipitations","value": "precip"},
                    ],
                    value="temp_mean",
                    inline=True,
                    style={"fontSize": "13px", "marginBottom": "10px"},
                    inputStyle={"marginRight": "4px", "marginLeft": "12px"},
                ),
                dcc.Graph(id="ts-chart", config={"displayModeBar": False}),
            ])
        ], style=CARD_STYLE),

        # ── Profil horaire + distribution ────────
        html.Div("PROFIL HORAIRE & DISTRIBUTION", style={
            "fontSize": "11px", "fontWeight": "500", "color": "#9c9a92",
            "letterSpacing": ".07em", "marginBottom": "8px"
        }),
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.P("Profil horaire moyen",
                               style={"fontSize": "12px", "fontWeight": "500",
                                      "color": COLORS["text2"], "marginBottom": "8px"}),
                        dcc.Graph(figure=fig_hourly_profile(), config={"displayModeBar": False}),
                    ], style={**CARD_STYLE, "flex": "1"}),

                    html.Div([
                        html.P("Distribution horaire — Température par heure",
                               style={"fontSize": "12px", "fontWeight": "500",
                                      "color": COLORS["text2"], "marginBottom": "8px"}),
                        dcc.Graph(figure=fig_boxplot_by_hour(), config={"displayModeBar": False}),
                    ], style={**CARD_STYLE, "flex": "1"}),
                ], style={"display": "flex", "gap": "12px"}),
            ])
        ]),

        # ── Histogrammes ─────────────────────────
        html.Div("DISTRIBUTIONS", style={
            "fontSize": "11px", "fontWeight": "500", "color": "#9c9a92",
            "letterSpacing": ".07em", "marginBottom": "8px"
        }),
        html.Div([
            html.Div([
                html.P("Variable à analyser :",
                       style={"fontSize": "12px", "color": COLORS["text2"], "marginBottom": "8px"}),
                dcc.Dropdown(
                    id="hist-variable",
                    options=[
                        {"label": "Température (°C)",       "value": "temperature_2m"},
                        {"label": "Humidité relative (%)",  "value": "relative_humidity_2m"},
                        {"label": "Vitesse du vent (km/h)", "value": "wind_speed_80m"},
                        {"label": "Pression (hPa)",         "value": "surface_pressure"},
                        {"label": "Précipitations (mm)",    "value": "precipitation"},
                    ],
                    value="temperature_2m",
                    clearable=False,
                    style={"fontSize": "13px", "marginBottom": "10px", "width": "300px"},
                ),
                dcc.Graph(id="hist-chart", config={"displayModeBar": False}),
            ])
        ], style=CARD_STYLE),

        # ── Précipitations + Rose des vents ──────
        html.Div("PRÉCIPITATIONS & VENT", style={
            "fontSize": "11px", "fontWeight": "500", "color": "#9c9a92",
            "letterSpacing": ".07em", "marginBottom": "8px"
        }),
        html.Div([
            html.Div([
                html.Div([
                    html.P("Précipitations journalières (mm)",
                           style={"fontSize": "12px", "fontWeight": "500",
                                  "color": COLORS["text2"], "marginBottom": "8px"}),
                    dcc.Graph(figure=fig_precipitation_bar(), config={"displayModeBar": False}),
                ], style={**CARD_STYLE, "flex": "2"}),

                html.Div([
                    html.P("Rose des vents à 80m",
                           style={"fontSize": "12px", "fontWeight": "500",
                                  "color": COLORS["text2"], "marginBottom": "8px"}),
                    dcc.Graph(figure=fig_wind_rose(), config={"displayModeBar": False}),
                ], style={**CARD_STYLE, "flex": "1"}),
            ], style={"display": "flex", "gap": "12px"}),
        ]),

        # ── Scatter temp vs humidité ──────────────
        html.Div("RELATIONS ENTRE VARIABLES", style={
            "fontSize": "11px", "fontWeight": "500", "color": "#9c9a92",
            "letterSpacing": ".07em", "marginBottom": "8px"
        }),
        html.Div([
            html.Div([
                html.Div([
                    html.P("Température vs Humidité (colorié par heure)",
                           style={"fontSize": "12px", "fontWeight": "500",
                                  "color": COLORS["text2"], "marginBottom": "8px"}),
                    dcc.Graph(figure=fig_scatter_temp_hum(), config={"displayModeBar": False}),
                ], style={**CARD_STYLE, "flex": "1"}),

                html.Div([
                    html.P("Matrice de corrélation — toutes variables",
                           style={"fontSize": "12px", "fontWeight": "500",
                                  "color": COLORS["text2"], "marginBottom": "8px"}),
                    dcc.Graph(figure=fig_correlation_heatmap(), config={"displayModeBar": False}),
                ], style={**CARD_STYLE, "flex": "1"}),
            ], style={"display": "flex", "gap": "12px"}),
        ]),

        # ── Insights ─────────────────────────────
        html.Div("INSIGHTS POUR LE MODÈLE ML", style={
            "fontSize": "11px", "fontWeight": "500", "color": "#9c9a92",
            "letterSpacing": ".07em", "marginBottom": "8px"
        }),
        html.Div([
            *[
                html.Div([
                    html.Span("●", style={"color": color, "marginRight": "8px", "fontSize": "16px"}),
                    html.Span(text, style={"fontSize": "13px", "lineHeight": "1.6"}),
                ], style={"display": "flex", "alignItems": "flex-start", "marginBottom": "10px"})
                for color, text in [
                    (COLORS["coral"],  "Temp / Ressenti : corrélation 0.97 — quasi redondants. Créer un écart (ressenti - réelle) comme feature plutôt que garder les deux."),
                    (COLORS["blue"],   "Temp / Humidité : corrélation -0.79 — relation inverse forte typique du tropique. Feature d'interaction temp × humidité pertinente."),
                    (COLORS["teal"],   "Cycle journalier très marqué : minimum à 6h (~26.7°C), maximum à 13-14h (~32.1°C). Encodage cyclique de l'heure (sin/cos) indispensable."),
                    (COLORS["amber"],  "Tendance saisonnière nette : humidité croissante de 65% (janv) vers 88% (mars). Entrée progressive en saison pluvieuse → feature month + rolling 7j."),
                    (COLORS["purple"], "Pression chute avant les pluies (corr = -0.23). La variation de pression sur 3h sera un bon prédicteur de pluie imminente."),
                    (COLORS["gray"],   "Vent dominant du SW (195-228°) — alizés du Golfe de Guinée. Direction stable : ajouter sin/cos du vent comme feature directionnelle."),
                ]
            ]
        ], style={**CARD_STYLE, "background": "#f0ede6", "border": "none"}),

    ]
)

# ──────────────────────────────────────────────
# 5. CALLBACKS
# ──────────────────────────────────────────────

@callback(Output("ts-chart", "figure"), Input("ts-variable", "value"))
def update_timeseries(variable):
    return fig_timeseries(variable)


@callback(Output("hist-chart", "figure"), Input("hist-variable", "value"))
def update_histogram(variable):
    return fig_distribution(variable)


# ──────────────────────────────────────────────
# 6. LANCEMENT
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  Dashboard EDA — Météo Cotonou")
    print("  http://127.0.0.1:8050")
    print("="*55 + "\n")
    app.run(debug=True, host="127.0.0.1",
             port=8050, 
             dev_tools_hot_reload=True, 
             dev_tools_hot_reload_interval=2)