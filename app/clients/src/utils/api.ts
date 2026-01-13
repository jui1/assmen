/**
 * API client for backend communication
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8010';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface TickData {
  timestamp: string;
  symbol: string;
  price: number;
  quantity: number;
}

export interface OHLCData {
  timestamp: string;
  symbol: string;
  timeframe: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface PriceStats {
  mean: number;
  std: number;
  min: number;
  max: number;
  median: number;
  current: number;
  change: number;
  change_pct: number;
}

export interface HedgeRatio {
  hedge_ratio: number;
  intercept: number;
  r_squared?: number;
  symbol1: string;
  symbol2: string;
  method?: string;
  window?: number;
}

export interface SpreadData {
  timestamp: string;
  spread: number;
  close_1: number;
  close_2: number;
}

export interface ZScoreData {
  timestamp: string;
  zscore: number;
  spread: number;
}

export interface ADFTestResult {
  adf_statistic: number;
  p_value: number;
  critical_values: Record<string, number>;
  is_stationary: boolean;
  lags_used: number;
  n_obs: number;
}

export interface CorrelationData {
  timestamp: string;
  rolling_corr: number;
  close_1: number;
  close_2: number;
}

export interface Alert {
  id: string;
  symbol: string;
  condition: string;
  threshold: number;
  enabled: boolean;
  triggered?: boolean;
  last_triggered?: string;
}

export const apiClient = {
  // Symbols
  getSymbols: async () => {
    const response = await api.get('/symbols');
    return response.data.symbols as string[];
  },

  // Data
  getTicks: async (
    symbol: string,
    startTime?: string,
    endTime?: string,
    limit = 1000
  ) => {
    const params: any = { symbol, limit };
    if (startTime) params.start_time = startTime;
    if (endTime) params.end_time = endTime;
    const response = await api.get('/data/ticks', { params });
    return response.data.data as TickData[];
  },

  getOHLC: async (
    symbol: string,
    timeframe = '1m',
    startTime?: string,
    endTime?: string
  ) => {
    const params: any = { symbol, timeframe };
    if (startTime) params.start_time = startTime;
    if (endTime) params.end_time = endTime;
    const response = await api.get('/data/ohlc', { params });
    return response.data.data as OHLCData[];
  },

  // Analytics
  getPriceStats: async (symbol: string, timeframe = '1m') => {
    const response = await api.get('/analytics/price-stats', {
      params: { symbol, timeframe },
    });
    return response.data as PriceStats;
  },

  getHedgeRatio: async (
    symbol1: string,
    symbol2: string,
    timeframe = '1m',
    method = 'ols',
    window = 100
  ) => {
    const response = await api.get('/analytics/hedge-ratio', {
      params: { symbol1, symbol2, timeframe, method, window },
    });
    return response.data as HedgeRatio;
  },

  getSpread: async (
    symbol1: string,
    symbol2: string,
    timeframe = '1m',
    hedgeRatio?: number
  ) => {
    const params: any = { symbol1, symbol2, timeframe };
    if (hedgeRatio) params.hedge_ratio = hedgeRatio;
    const response = await api.get('/analytics/spread', { params });
    return response.data.data as SpreadData[];
  },

  getZScore: async (
    symbol1: string,
    symbol2: string,
    timeframe = '1m',
    window = 20
  ) => {
    const response = await api.get('/analytics/zscore', {
      params: { symbol1, symbol2, timeframe, window },
    });
    return response.data.data as ZScoreData[];
  },

  getADFTest: async (symbol1: string, symbol2: string, timeframe = '1m') => {
    const response = await api.get('/analytics/adf-test', {
      params: { symbol1, symbol2, timeframe },
    });
    return response.data as ADFTestResult;
  },

  getCorrelation: async (
    symbol1: string,
    symbol2: string,
    timeframe = '1m',
    window = 20
  ) => {
    const response = await api.get('/analytics/correlation', {
      params: { symbol1, symbol2, timeframe, window },
    });
    return response.data.data as CorrelationData[];
  },

  getCorrelationMatrix: async (
    symbols: string[],
    timeframe = '1m',
    window = 100
  ) => {
    const response = await api.get('/analytics/correlation-matrix', {
      params: { symbols: symbols.join(','), timeframe, window },
    });
    return response.data.data as Record<string, Record<string, number>>;
  },

  getBacktest: async (
    symbol1: string,
    symbol2: string,
    timeframe = '1m',
    entryZ = 2.0,
    exitZ = 0.0,
    window = 20
  ) => {
    const response = await api.get('/analytics/backtest', {
      params: {
        symbol1,
        symbol2,
        timeframe,
        entry_z: entryZ,
        exit_z: exitZ,
        window,
      },
    });
    return response.data;
  },

  getLiquidity: async (symbol: string, timeframe = '1m') => {
    const response = await api.get('/analytics/liquidity', {
      params: { symbol, timeframe },
    });
    return response.data;
  },

  getTimeSeriesStats: async (symbol: string, timeframe = '1m', window = 60) => {
    const response = await api.get('/analytics/time-series-stats', {
      params: { symbol, timeframe, window },
    });
    return response.data.data as Array<
      PriceStats & { timestamp: string; price: number; volume: number }
    >;
  },

  // Alerts
  getAlerts: async () => {
    const response = await api.get('/alerts');
    return response.data.alerts as Alert[];
  },

  createAlert: async (symbol: string, condition: string, threshold: number) => {
    const response = await api.post('/alerts', null, {
      params: { symbol, condition, threshold },
    });
    return response.data;
  },

  deleteAlert: async (alertId: string) => {
    const response = await api.delete(`/alerts/${alertId}`);
    return response.data;
  },

  // Export
  exportCSV: async (
    symbol: string,
    timeframe = '1m',
    startTime?: string,
    endTime?: string
  ) => {
    const params: any = { symbol, timeframe };
    if (startTime) params.start_time = startTime;
    if (endTime) params.end_time = endTime;
    const response = await api.get('/export/csv', {
      params,
      responseType: 'blob',
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${symbol}_${timeframe}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  },

  // Subscribe to symbols (handled automatically on backend startup)
  subscribeSymbols: async (symbols: string[]) => {
    // Note: Symbol subscription is handled automatically on backend startup
    // This endpoint is kept for future use
    return { message: 'Symbol subscription handled on backend startup' };
  },
};

export default apiClient;

// Explicit type exports for better module resolution
export type {
  OHLCData,
  TickData,
  PriceStats,
  HedgeRatio,
  SpreadData,
  ZScoreData,
  ADFTestResult,
  CorrelationData,
  Alert,
};
