/**
 * Correlation heatmap component
 */
import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { apiClient } from '../utils/api';

interface CorrelationHeatmapProps {
  symbols: string[];
  timeframe: string;
  window: number;
  height?: number;
}

export const CorrelationHeatmap: React.FC<CorrelationHeatmapProps> = ({
  symbols,
  timeframe,
  window,
  height = 500,
}) => {
  const [data, setData] = useState<Record<string, Record<string, number>>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const fetchData = async () => {
      if (!mounted || symbols.length < 2) {
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const matrix = await apiClient.getCorrelationMatrix(
          symbols,
          timeframe,
          window
        );
        if (mounted) {
          setData((prevData) => {
            if (JSON.stringify(prevData) !== JSON.stringify(matrix)) {
              return matrix;
            }
            return prevData;
          });
          setLoading(false);
        }
      } catch (error) {
        console.error('Error fetching correlation matrix:', error);
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchData();
    // Update every 30 seconds instead of every minute
    const interval = setInterval(fetchData, 30000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [symbols, timeframe, window]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">Loading...</div>
    );
  }

  if (Object.keys(data).length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        No data available
      </div>
    );
  }

  // Convert to matrix format for Plotly
  const matrixData: number[][] = [];
  const labels = Object.keys(data);

  for (const symbol1 of labels) {
    const row: number[] = [];
    for (const symbol2 of labels) {
      row.push(data[symbol1]?.[symbol2] ?? 0);
    }
    matrixData.push(row);
  }

  return (
    <Plot
      data={[
        {
          z: matrixData,
          x: labels,
          y: labels,
          type: 'heatmap',
          colorscale: 'RdBu',
          zmid: 0,
          zmin: -1,
          zmax: 1,
          text: matrixData.map((row) => row.map((val) => val.toFixed(3))),
          texttemplate: '%{text}',
          textfont: { size: 10 },
        },
      ]}
      layout={{
        width: undefined,
        height: height,
        title: { text: `Correlation Heatmap (Window: ${window})` },
        xaxis: { title: 'Symbol' },
        yaxis: { title: 'Symbol' },
      }}
      config={{
        displayModeBar: true,
        displaylogo: false,
      }}
      style={{ width: '100%' }}
    />
  );
};
