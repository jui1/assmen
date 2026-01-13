/**
 * Price chart component using Plotly
 */
import React, { useEffect, useState, useMemo, useCallback } from 'react';
import Plot from 'react-plotly.js';
import { apiClient } from '../utils/api';
import type { OHLCData } from '../utils/api';

interface PriceChartProps {
  symbol: string;
  timeframe: string;
  height?: number;
}

export const PriceChart: React.FC<PriceChartProps> = React.memo(
  ({ symbol, timeframe, height = 400 }) => {
    const [data, setData] = useState<OHLCData[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchData = useCallback(async () => {
      try {
        const ohlcData = await apiClient.getOHLC(symbol, timeframe);
        setData((prevData) => {
          // Only update if data actually changed
          if (JSON.stringify(prevData) !== JSON.stringify(ohlcData)) {
            return ohlcData;
          }
          return prevData;
        });
      } catch (error) {
        console.error('Error fetching price data:', error);
      } finally {
        setLoading(false);
      }
    }, [symbol, timeframe]);

    useEffect(() => {
      let mounted = true;

      const loadData = async () => {
        setLoading(true);
        await fetchData();
      };

      loadData();

      // Reduce polling frequency based on timeframe
      const pollInterval =
        timeframe === '1s' ? 5000 : timeframe === '1m' ? 30000 : 60000;
      const interval = setInterval(() => {
        if (mounted) {
          fetchData();
        }
      }, pollInterval);

      return () => {
        mounted = false;
        clearInterval(interval);
      };
    }, [fetchData, timeframe]);

    // All hooks must be called before any conditional returns
    const plotData = useMemo(() => {
      if (data.length === 0) return [];

      const timestamps = data.map((d) => new Date(d.timestamp));
      const closes = data.map((d) => d.close);

      return [
        {
          x: timestamps,
          y: closes,
          type: 'scatter' as const,
          mode: 'lines' as const,
          name: 'Price',
          line: { color: '#3b82f6' },
        },
      ];
    }, [data]);

    const layout = useMemo(
      () => ({
        width: undefined as number | undefined,
        height: height,
        title: { text: `${symbol} Price Chart (${timeframe})` },
        xaxis: { title: 'Time' },
        yaxis: { title: 'Price' },
        hovermode: 'x unified' as const,
        showlegend: true,
      }),
      [symbol, timeframe, height]
    );

    const config = useMemo(
      () => ({
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d'],
      }),
      []
    );

    // Early returns after all hooks
    if (loading && data.length === 0) {
      return (
        <div className="flex items-center justify-center h-full">
          Loading...
        </div>
      );
    }

    if (data.length === 0 || plotData.length === 0) {
      return (
        <div className="flex items-center justify-center h-full">
          No data available
        </div>
      );
    }

    return (
      <Plot
        data={plotData}
        layout={layout}
        config={config}
        style={{ width: '100%' }}
      />
    );
  }
);
