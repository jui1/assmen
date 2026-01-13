/**
 * Statistics widget component
 */
import React, { useEffect, useState } from 'react';
import { apiClient } from '../utils/api';
import type { PriceStats } from '../utils/api';

interface StatsWidgetProps {
  symbol: string;
  timeframe: string;
}

export const StatsWidget: React.FC<StatsWidgetProps> = React.memo(
  ({ symbol, timeframe }) => {
    const [stats, setStats] = useState<PriceStats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      let mounted = true;

      const fetchStats = async () => {
        if (!mounted) return;

        try {
          const statsData = await apiClient.getPriceStats(symbol, timeframe);
          if (mounted) {
            setStats(statsData);
            setLoading(false);
          }
        } catch (error) {
          console.error('Error fetching stats:', error);
          if (mounted) {
            setLoading(false);
          }
        }
      };

      fetchStats();
      // Reduce polling frequency - update every 5 seconds instead of 1
      const interval = setInterval(fetchStats, 5000);

      return () => {
        mounted = false;
        clearInterval(interval);
      };
    }, [symbol, timeframe]);

    if (loading || !stats) {
      return (
        <div className="flex items-center justify-center h-full">
          Loading...
        </div>
      );
    }

    // Safe access with fallbacks
    const current = stats.current ?? 0;
    const change = stats.change ?? 0;
    const changePct = stats.change_pct ?? 0;
    const mean = stats.mean ?? 0;
    const std = stats.std ?? 0;
    const min = stats.min ?? 0;
    const max = stats.max ?? 0;
    const median = stats.median ?? 0;

    const changeColor = change >= 0 ? 'text-green-600' : 'text-red-600';

    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">{symbol} Statistics</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Current Price</p>
            <p className="text-xl font-bold">{current.toFixed(4)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Change</p>
            <p className={`text-xl font-bold ${changeColor}`}>
              {change >= 0 ? '+' : ''}
              {change.toFixed(4)} ({changePct.toFixed(2)}%)
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Mean</p>
            <p className="text-lg">{mean.toFixed(4)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Std Dev</p>
            <p className="text-lg">{std.toFixed(4)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Min</p>
            <p className="text-lg">{min.toFixed(4)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Max</p>
            <p className="text-lg">{max.toFixed(4)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Median</p>
            <p className="text-lg">{median.toFixed(4)}</p>
          </div>
        </div>
      </div>
    );
  }
);
