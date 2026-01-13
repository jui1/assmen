/**
 * Spread chart component
 */
import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { apiClient } from '../utils/api';
import type { SpreadData } from '../utils/api';

interface SpreadChartProps {
  symbol1: string;
  symbol2: string;
  timeframe: string;
  hedgeRatio?: number;
  height?: number;
}

export const SpreadChart: React.FC<SpreadChartProps> = React.memo(
  ({ symbol1, symbol2, timeframe, hedgeRatio, height = 400 }) => {
    const [data, setData] = useState<SpreadData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      let mounted = true;

      const fetchData = async () => {
        if (!mounted) return;

        try {
          const spreadData = await apiClient.getSpread(
            symbol1,
            symbol2,
            timeframe,
            hedgeRatio
          );
          if (mounted) {
            setData((prevData) => {
              if (JSON.stringify(prevData) !== JSON.stringify(spreadData)) {
                return spreadData;
              }
              return prevData;
            });
            setLoading(false);
          }
        } catch (error) {
          console.error('Error fetching spread data:', error);
          if (mounted) {
            setLoading(false);
          }
        }
      };

      fetchData();
      // Reduce polling frequency
      const pollInterval =
        timeframe === '1s' ? 5000 : timeframe === '1m' ? 30000 : 60000;
      const interval = setInterval(fetchData, pollInterval);

      return () => {
        mounted = false;
        clearInterval(interval);
      };
    }, [symbol1, symbol2, timeframe, hedgeRatio]);

    if (loading && data.length === 0) {
      return (
        <div className="flex items-center justify-center h-full">
          Loading...
        </div>
      );
    }

    if (data.length === 0) {
      return (
        <div className="flex items-center justify-center h-full">
          No data available
        </div>
      );
    }

    const timestamps = data.map((d) => new Date(d.timestamp));
    const spreads = data.map((d) => d.spread);

    return (
      <Plot
        data={[
          {
            x: timestamps,
            y: spreads,
            type: 'scatter',
            mode: 'lines',
            name: 'Spread',
            line: { color: '#10b981' },
          },
          {
            x: timestamps,
            y: new Array(timestamps.length).fill(0),
            type: 'scatter',
            mode: 'lines',
            name: 'Zero Line',
            line: { color: '#ef4444', dash: 'dash' },
          },
        ]}
        layout={{
          width: undefined,
          height: height,
          title: { text: `Spread: ${symbol1} - ${symbol2} (${timeframe})` },
          xaxis: { title: 'Time' },
          yaxis: { title: 'Spread' },
          hovermode: 'x unified',
          showlegend: true,
        }}
        config={{
          displayModeBar: true,
          displaylogo: false,
        }}
        style={{ width: '100%' }}
      />
    );
  }
);
