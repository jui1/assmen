/**
 * Correlation chart component
 */
import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { apiClient } from '../utils/api';
import type { CorrelationData } from '../utils/api';

interface CorrelationChartProps {
  symbol1: string;
  symbol2: string;
  timeframe: string;
  window: number;
  height?: number;
}

export const CorrelationChart: React.FC<CorrelationChartProps> = ({
  symbol1,
  symbol2,
  timeframe,
  window,
  height = 400,
}) => {
  const [data, setData] = useState<CorrelationData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const fetchData = async () => {
      if (!mounted) return;

      try {
        const corrData = await apiClient.getCorrelation(
          symbol1,
          symbol2,
          timeframe,
          window
        );
        if (mounted) {
          setData((prevData) => {
            if (JSON.stringify(prevData) !== JSON.stringify(corrData)) {
              return corrData;
            }
            return prevData;
          });
          setLoading(false);
        }
      } catch (error) {
        console.error('Error fetching correlation data:', error);
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
  }, [symbol1, symbol2, timeframe, window]);

  if (loading && data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">Loading...</div>
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
  const correlations = data.map((d) => d.rolling_corr);

  return (
    <Plot
      data={[
        {
          x: timestamps,
          y: correlations,
          type: 'scatter',
          mode: 'lines',
          name: 'Rolling Correlation',
          line: { color: '#f59e0b' },
        },
      ]}
      layout={{
        width: undefined,
        height: height,
        title: {
          text: `Rolling Correlation: ${symbol1} vs ${symbol2} (Window: ${window})`,
        },
        xaxis: { title: 'Time' },
        yaxis: { title: 'Correlation', range: [-1, 1] },
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
};
