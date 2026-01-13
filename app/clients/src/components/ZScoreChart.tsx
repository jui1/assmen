/**
 * Z-Score chart component
 */
import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { apiClient } from '../utils/api';
import type { ZScoreData } from '../utils/api';

interface ZScoreChartProps {
  symbol1: string;
  symbol2: string;
  timeframe: string;
  window: number;
  height?: number;
}

export const ZScoreChart: React.FC<ZScoreChartProps> = React.memo(
  ({ symbol1, symbol2, timeframe, window, height = 400 }) => {
    const [data, setData] = useState<ZScoreData[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      let mounted = true;

      const fetchData = async () => {
        if (!mounted) return;

        try {
          const zscoreData = await apiClient.getZScore(
            symbol1,
            symbol2,
            timeframe,
            window
          );
          if (mounted) {
            setData((prevData) => {
              // Only update if data changed
              if (JSON.stringify(prevData) !== JSON.stringify(zscoreData)) {
                return zscoreData;
              }
              return prevData;
            });
            setLoading(false);
          }
        } catch (error) {
          console.error('Error fetching z-score data:', error);
          if (mounted) {
            setLoading(false);
          }
        }
      };

      fetchData();
      // Update every 2 seconds instead of 500ms to reduce API calls
      const interval = setInterval(fetchData, 2000);

      return () => {
        mounted = false;
        clearInterval(interval);
      };
    }, [symbol1, symbol2, timeframe, window]);

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
    const zscores = data.map((d) => d.zscore);

    return (
      <Plot
        data={[
          {
            x: timestamps,
            y: zscores,
            type: 'scatter',
            mode: 'lines',
            name: 'Z-Score',
            line: { color: '#8b5cf6' },
          },
          {
            x: timestamps,
            y: new Array(timestamps.length).fill(2),
            type: 'scatter',
            mode: 'lines',
            name: '+2σ',
            line: { color: '#ef4444', dash: 'dash' },
          },
          {
            x: timestamps,
            y: new Array(timestamps.length).fill(-2),
            type: 'scatter',
            mode: 'lines',
            name: '-2σ',
            line: { color: '#ef4444', dash: 'dash' },
          },
          {
            x: timestamps,
            y: new Array(timestamps.length).fill(0),
            type: 'scatter',
            mode: 'lines',
            name: 'Zero',
            line: { color: '#6b7280', dash: 'dot' },
          },
        ]}
        layout={{
          width: undefined,
          height: height,
          title: {
            text: `Z-Score: ${symbol1} vs ${symbol2} (Window: ${window})`,
          },
          xaxis: { title: 'Time' },
          yaxis: { title: 'Z-Score' },
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
