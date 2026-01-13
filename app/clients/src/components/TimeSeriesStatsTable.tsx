/**
 * Time-series statistics table component
 */
import React, { useEffect, useState } from 'react';
import { apiClient } from '../utils/api';

interface TimeSeriesStatsTableProps {
  symbol: string;
  timeframe: string;
  window: number;
}

export const TimeSeriesStatsTable: React.FC<TimeSeriesStatsTableProps> = ({
  symbol,
  timeframe,
  window,
}) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const fetchData = async () => {
      if (!mounted) return;

      try {
        const statsData = await apiClient.getTimeSeriesStats(
          symbol,
          timeframe,
          window
        );
        if (mounted) {
          setData((prevData) => {
            if (JSON.stringify(prevData) !== JSON.stringify(statsData)) {
              return statsData;
            }
            return prevData;
          });
          setLoading(false);
        }
      } catch (error) {
        console.error('Error fetching time-series stats:', error);
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
  }, [symbol, timeframe, window]);

  const handleExport = () => {
    if (data.length === 0) return;

    const csv = [
      [
        'Timestamp',
        'Price',
        'Volume',
        'Mean',
        'Std',
        'Min',
        'Max',
        'Median',
        'Change',
        'Change %',
      ],
      ...data.map((row) => [
        row.timestamp,
        row.price?.toFixed(4) || '',
        row.volume?.toFixed(4) || '',
        row.mean?.toFixed(4) || '',
        row.std?.toFixed(4) || '',
        row.min?.toFixed(4) || '',
        row.max?.toFixed(4) || '',
        row.median?.toFixed(4) || '',
        row.change?.toFixed(4) || '',
        row.change_pct?.toFixed(2) || '',
      ]),
    ]
      .map((row) => row.join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute(
      'download',
      `${symbol}_timeseries_stats_${timeframe}.csv`
    );
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

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

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Time-Series Statistics</h3>
        <button
          onClick={handleExport}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          Export CSV
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Timestamp
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Price
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Volume
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Mean
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Std
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Min
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Max
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Median
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Change
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Change %
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data
              .slice(-50)
              .reverse()
              .map((row, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm">
                    {new Date(row.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {row.price?.toFixed(4) || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {row.volume?.toFixed(4) || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {row.mean?.toFixed(4) || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {row.std?.toFixed(4) || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {row.min?.toFixed(4) || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {row.max?.toFixed(4) || '-'}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {row.median?.toFixed(4) || '-'}
                  </td>
                  <td
                    className={`px-4 py-3 text-sm ${
                      row.change >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {row.change?.toFixed(4) || '-'}
                  </td>
                  <td
                    className={`px-4 py-3 text-sm ${
                      row.change_pct >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {row.change_pct?.toFixed(2) || '-'}%
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
