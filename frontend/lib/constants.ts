export const API_BASE = "https://donerick-air-quality.hf.space";

export const COLORS = {
  teal:    "#00E5B4",
  coral:   "#FB923C",
  indigo:  "#6366F1",
  violet:  "#8B5CF6",
  amber:   "#F59E0B",
  danger:  "#EF4444",
  muted:   "#8896B0",
  border:  "#1A2438",
  surface: "#0E1420",
  bg:      "#080C14",
};

export const AQI_COLORS: Record<string, string> = {
  Bon:     "#0D9488",
  Moyen:   "#F59E0B",
  Mauvais: "#EF4444",
};

export const OMS_THRESHOLDS: Record<string, number> = {
  pm2_5:            12,
  PM10:             40,
  ozone:            100,
  nitrogen_dioxide: 10,
};

export interface PollutantMeta {
  label: string;
  unit: string;
  color: string;
  max: number;
}

export const POLLUTANT_META: Record<string, PollutantMeta> = {
  pm2_5:            { label: "PM2.5",   unit: "μg/m³", color: COLORS.coral,  max: 55 },
  pm10:             { label: "PM10",    unit: "μg/m³", color: COLORS.amber,  max: 300 },
  carbon_dioxide:   { label: "CO₂",     unit: "ppm", color: COLORS.indigo, max: 400-4200 },
  carbon_monoxide:  { label: "CO",      unit: "mg/m³", color: COLORS.violet, max: 4 },
  ozone:            { label: "Ozone O₃",unit: "μg/m³", color: COLORS.teal,   max: 200 },
  nitrogen_dioxide: { label: "NO₂",     unit: "μg/m³", color: COLORS.muted,  max: 100 },
  sulphur_dioxide:  { label: "SO₂",     unit: "μg/m³", color: COLORS.amber,  max: 40 },
  methane:          { label: "Méthane", unit: "ppm", color: COLORS.indigo, max: 5 },
};

export const CORR_SHORT: Record<string, string> = {
  pm10:             "PM10",
  pm2_5:            "PM2.5",
  carbon_monoxide:  "CO",
  carbon_dioxide:   "CO₂",
  sulphur_dioxide:  "SO₂",
  ozone:            "O₃",
  nitrogen_dioxide: "NO₂",
  methane:          "CH₄",
  european_aqi:     "AQI",
};

export const POLL_COLS = [
  "pm2_5","pm10","carbon_monoxide","carbon_dioxide",
  "sulphur_dioxide","ozone","nitrogen_dioxide","methane","european_aqi",
];

export const NAV_ITEMS = [
  { id: "overview",      label: "Overview",      icon: "" },
  { id: "timeseries",    label: "Séries Temporelles",  icon: "" },
  { id: "distributions", label: "Distributions",       icon: "" },
  { id: "correlations",  label: "Corrélations",         icon: "" },
  { id: "peaks",         label: "Pics & Épisodes",     icon: "" },
  { id: "ml",            label: "Analyses ML",          icon: "" },
] as const;