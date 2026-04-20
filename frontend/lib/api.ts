import { API_BASE, POLL_COLS } from "./constants";
import type { AirRecord, DataResponse, DailyRow, HourlyRow, PredictionResponse, HistoryResponse,} from "./types";
import { apiCache } from "./cache";

// ── Raw fetch helpers 
export async function fetchPrediction(): Promise<PredictionResponse | null> {
  return apiCache.getOrFetch("prediction", async () => {
    try {
      const res = await fetch(`${API_BASE}/predict`, {
        method: "POST",
      });
      if (!res.ok) return null;
      return res.json();
    } catch {
      return null;
    }
  }, apiCache.getTTL("prediction"));
}

export async function fetchHistory(): Promise<HistoryResponse | null> {
  return apiCache.getOrFetch("history", async () => {
    try {
      const res = await fetch(`${API_BASE}/history`);
      if (!res.ok) return null;
      return res.json();
    } catch {
      return null;
    }
  }, apiCache.getTTL("history"));
}

export async function fetchAllData(): Promise<DataResponse | null> {
  return apiCache.getOrFetch("data", async () => {
    try {
      const res = await fetch(`${API_BASE}/data`);
      if (!res.ok) return null;
      return res.json();
    } catch {
      return null;
    }
  }, apiCache.getTTL("data"));
}

// ── Data transformation helpers ──────────────────────────────

export function getAqiLabel(val: number): string {
  if (val <= 12)   return "Bon";
  if (val <= 35.5) return "Moyen";
  return "Mauvais";
}

/** Group hourly records by date and compute daily averages */
export function aggregateDaily(records: AirRecord[]): DailyRow[] {
  const byDate = new Map<string, AirRecord[]>();
  for (const r of records) {
    const d = r.date.slice(0, 10);
    if (!byDate.has(d)) byDate.set(d, []);
    byDate.get(d)!.push(r);
  }
  const rows: DailyRow[] = [];
  byDate.forEach((group, date) => {
    const row: DailyRow = { date } as DailyRow;
    for (const col of POLL_COLS) {
      const vals = group
        .map((r) => r[col])
        .filter((v) => v != null && !isNaN(v));

      row[col] = vals.length
        ? +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(3)
        : 0;
    }
    rows.push(row);
  });
  return rows.sort((a, b) => a.date.localeCompare(b.date));
}

/** Group by hour (0-23) and compute averages */
export function aggregateHourly(records: AirRecord[]): HourlyRow[] {
  const byHour: Record<number, AirRecord[]> = {};
  for (let h = 0; h < 24; h++) byHour[h] = [];
  for (const r of records) {
    const h = new Date(r.date).getUTCHours();
    byHour[h].push(r);
  }
  return Array.from({ length: 24 }, (_, h) => {
    const group = byHour[h];
    const avg = (col: string) => {
      const vals = group.map((r) => r[col] as number).filter((v) => v != null && !isNaN(v));
      return vals.length ? +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(3) : 0;
    };
    return {
      hour: h,
      pm2_5:            avg("pm2_5"),
      pm10:             avg("pm10"),
      ozone:            avg("ozone"),
      sulphur_dioxide:  avg("sulphur_dioxide"),
      carbon_dioxide:   avg("carbon_dioxide"),
      nitrogen_dioxide: avg("nitrogen_dioxide"),
    };
  });
}

/** Compute Pearson correlation matrix (with caching) */
const correlationCache = new Map<string, number[][]>();

export function computeCorrelation(records: AirRecord[], cols: string[]): number[][] {
  // Generate cache key from records length and column names
  const cacheKey = `${records.length}-${cols.join(",")}`;
  
  if (correlationCache.has(cacheKey)) {
    return correlationCache.get(cacheKey)!;
  }

  const n = cols.length;
  const mat: number[][] = Array.from({ length: n }, () => Array(n).fill(0));
  const arrays = cols.map((c) =>
    records.map((r) => r[c] as number).filter((v) => !isNaN(v))
  );
  for (let i = 0; i < n; i++) {
    for (let j = i; j < n; j++) {
      const xi = arrays[i];
      const xj = arrays[j];
      const len = Math.min(xi.length, xj.length);
      const mx = xi.slice(0, len).reduce((a, b) => a + b, 0) / len;
      const my = xj.slice(0, len).reduce((a, b) => a + b, 0) / len;
      let num = 0, di = 0, dj = 0;
      for (let k = 0; k < len; k++) {
        const a = xi[k] - mx, b = xj[k] - my;
        num += a * b; di += a * a; dj += b * b;
      }
      const val = di && dj ? +(num / Math.sqrt(di * dj)).toFixed(3) : (i === j ? 1 : 0);
      mat[i][j] = val;
      mat[j][i] = val; // Symmetric
    }
  }
  
  // Cache result (keep max 5 results)
  if (correlationCache.size > 5) correlationCache.clear();
  correlationCache.set(cacheKey, mat);
  
  return mat;
}