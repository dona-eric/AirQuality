export interface AirRecord {
  date: string;
  pm2_5: number;
  pm10: number;
  carbon_monoxide: number;
  carbon_dioxide: number;
  sulphur_dioxide: number;
  ozone: number;
  nitrogen_dioxide: number;
  methane: number;
  european_aqi: number;
  european_aqi_pm2_5: number;
  lat?: number;
  lon?: number;
  [key: string]: number | string | null | undefined;
}

export interface DataResponse {
  count: number;
  last_update: string;
  records: AirRecord[];
}

export interface PredictionResponse {
  date_prevision: string;
  current_pm25: number;
  predicted_pm25: number;
  delta: number;
  aqi_label: string;
  conseil: string;
}

export interface HistoryResponse {
  dates: string[];
  values: number[];
}

export type PageId =
  | "overview"
  | "timeseries"
  | "distributions"
  | "correlations"
  | "peaks"
  | "ml";

export interface DailyRow {
  date: string;
  pm2_5: number;
  pm10: number;
  carbon_monoxide: number;
  carbon_dioxide: number;
  sulphur_dioxide: number;
  ozone: number;
  nitrogen_dioxide: number;
  methane: number;
  european_aqi: number;
}

export interface HourlyRow {
  hour: number;
  pm2_5: number;
  pm10: number;
  ozone: number;
  sulphur_dioxide: number;
  carbon_dioxide: number;
  nitrogen_dioxide: number;
}