/**
 * Main dashboard page
 */
import React, { useState, useEffect } from 'react';
import { PriceChart } from '../components/PriceChart';
import { SpreadChart } from '../components/SpreadChart';
import { ZScoreChart } from '../components/ZScoreChart';
import { CorrelationChart } from '../components/CorrelationChart';
import { CorrelationHeatmap } from '../components/CorrelationHeatmap';
import { StatsWidget } from '../components/StatsWidget';
import { AlertManager } from '../components/AlertManager';
import { TimeSeriesStatsTable } from '../components/TimeSeriesStatsTable';
import { apiClient } from '../utils/api';
import { useWebSocket } from '../hooks/useWebSocket';

export const Home: React.FC = () => {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedSymbol2, setSelectedSymbol2] = useState('ETHUSDT');
  const [timeframe, setTimeframe] = useState('1m');
  const [rollingWindow, setRollingWindow] = useState(20);
  const [regressionMethod, setRegressionMethod] = useState('ols');
  const [hedgeRatio, setHedgeRatio] = useState<number | undefined>(undefined);
  const [showADFTest, setShowADFTest] = useState(false);
  const [adfResult, setAdfResult] = useState<any>(null);
  const [backtestResult, setBacktestResult] = useState<any>(null);
  const [selectedSymbolsForHeatmap, setSelectedSymbolsForHeatmap] = useState<
    string[]
  >(['BTCUSDT', 'ETHUSDT', 'BNBUSDT']);
  const { isConnected, latestData } = useWebSocket();

  useEffect(() => {
    const fetchSymbols = async () => {
      try {
        const syms = await apiClient.getSymbols();
        setSymbols(syms);
        if (syms.length > 0 && !selectedSymbol) {
          setSelectedSymbol(syms[0]);
        }
        if (syms.length > 1 && !selectedSymbol2) {
          setSelectedSymbol2(syms[1]);
        }
      } catch (error) {
        console.error('Error fetching symbols:', error);
      }
    };

    fetchSymbols();
  }, []);

  useEffect(() => {
    const fetchHedgeRatio = async () => {
      try {
        const result = await apiClient.getHedgeRatio(
          selectedSymbol,
          selectedSymbol2,
          timeframe,
          regressionMethod,
          100
        );
        if (result.hedge_ratio) {
          setHedgeRatio(result.hedge_ratio);
        }
      } catch (error) {
        console.error('Error fetching hedge ratio:', error);
      }
    };

    if (selectedSymbol && selectedSymbol2) {
      fetchHedgeRatio();
    }
  }, [selectedSymbol, selectedSymbol2, timeframe, regressionMethod]);

  const handleADFTest = async () => {
    try {
      const result = await apiClient.getADFTest(
        selectedSymbol,
        selectedSymbol2,
        timeframe
      );
      setAdfResult(result);
      setShowADFTest(true);
    } catch (error) {
      console.error('Error running ADF test:', error);
      alert('Error running ADF test');
    }
  };

  const handleBacktest = async () => {
    try {
      const result = await apiClient.getBacktest(
        selectedSymbol,
        selectedSymbol2,
        timeframe,
        2.0,
        0.0,
        rollingWindow
      );
      setBacktestResult(result);
    } catch (error) {
      console.error('Error running backtest:', error);
      alert('Error running backtest');
    }
  };

  const handleExportData = async () => {
    try {
      await apiClient.exportCSV(selectedSymbol, timeframe);
    } catch (error) {
      console.error('Error exporting data:', error);
      alert('Error exporting data');
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Trading Analytics Dashboard
              </h1>
              <p className="text-gray-600 mt-1">
                Real-time market data analysis and visualization
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div
                className={`px-4 py-2 rounded ${
                  isConnected
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {isConnected ? '● Connected' : '● Disconnected'}
              </div>
              <button
                onClick={handleExportData}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Export Data
              </button>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Controls</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Symbol 1</label>
              <select
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                className="w-full px-3 py-2 border rounded"
              >
                {symbols.map((sym) => (
                  <option key={sym} value={sym}>
                    {sym}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Symbol 2</label>
              <select
                value={selectedSymbol2}
                onChange={(e) => setSelectedSymbol2(e.target.value)}
                className="w-full px-3 py-2 border rounded"
              >
                {symbols.map((sym) => (
                  <option key={sym} value={sym}>
                    {sym}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Timeframe
              </label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full px-3 py-2 border rounded"
              >
                <option value="1s">1 Second</option>
                <option value="1m">1 Minute</option>
                <option value="5m">5 Minutes</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Rolling Window
              </label>
              <input
                type="number"
                value={rollingWindow}
                onChange={(e) => setRollingWindow(parseInt(e.target.value))}
                className="w-full px-3 py-2 border rounded"
                min="5"
                max="200"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Regression Method
              </label>
              <select
                value={regressionMethod}
                onChange={(e) => setRegressionMethod(e.target.value)}
                className="w-full px-3 py-2 border rounded"
              >
                <option value="ols">OLS</option>
                <option value="kalman">Kalman Filter</option>
                <option value="huber">Huber</option>
                <option value="theilsen">Theil-Sen</option>
              </select>
            </div>
            <div className="flex items-end gap-2">
              <button
                onClick={handleADFTest}
                className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
              >
                ADF Test
              </button>
              <button
                onClick={handleBacktest}
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
              >
                Backtest
              </button>
            </div>
          </div>
        </div>

        {/* ADF Test Result Modal */}
        {showADFTest && adfResult && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md">
              <h3 className="text-xl font-semibold mb-4">ADF Test Results</h3>
              <div className="space-y-2">
                <p>
                  <strong>ADF Statistic:</strong>{' '}
                  {adfResult.adf_statistic?.toFixed(4)}
                </p>
                <p>
                  <strong>P-Value:</strong> {adfResult.p_value?.toFixed(4)}
                </p>
                <p>
                  <strong>Is Stationary:</strong>{' '}
                  {adfResult.is_stationary ? 'Yes' : 'No'}
                </p>
                <p>
                  <strong>Lags Used:</strong> {adfResult.lags_used}
                </p>
                <p>
                  <strong>Observations:</strong> {adfResult.n_obs}
                </p>
                <div className="mt-4">
                  <strong>Critical Values:</strong>
                  <ul className="list-disc list-inside ml-4">
                    {Object.entries(adfResult.critical_values || {}).map(
                      ([key, value]) => (
                        <li key={key}>
                          {key}: {(value as number).toFixed(4)}
                        </li>
                      )
                    )}
                  </ul>
                </div>
              </div>
              <button
                onClick={() => setShowADFTest(false)}
                className="mt-4 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Close
              </button>
            </div>
          </div>
        )}

        {/* Backtest Result */}
        {backtestResult && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="text-xl font-semibold mb-4">Backtest Results</h3>
            <div className="grid grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Total Trades</p>
                <p className="text-2xl font-bold">
                  {backtestResult.total_trades || 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Total P&L</p>
                <p
                  className={`text-2xl font-bold ${
                    (backtestResult.total_pnl || 0) >= 0
                      ? 'text-green-600'
                      : 'text-red-600'
                  }`}
                >
                  {(backtestResult.total_pnl || 0).toFixed(4)}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Winning Trades</p>
                <p className="text-2xl font-bold">
                  {backtestResult.winning_trades || 0}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Win Rate</p>
                <p className="text-2xl font-bold">
                  {((backtestResult.win_rate || 0) * 100).toFixed(2)}%
                </p>
              </div>
            </div>
            <button
              onClick={() => setBacktestResult(null)}
              className="mt-4 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Close
            </button>
          </div>
        )}

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Price Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <PriceChart symbol={selectedSymbol} timeframe={timeframe} />
          </div>

          {/* Stats Widget */}
          <div>
            <StatsWidget symbol={selectedSymbol} timeframe={timeframe} />
          </div>
        </div>

        {/* Pair Analytics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Spread Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <SpreadChart
              symbol1={selectedSymbol}
              symbol2={selectedSymbol2}
              timeframe={timeframe}
              hedgeRatio={hedgeRatio}
            />
          </div>

          {/* Z-Score Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <ZScoreChart
              symbol1={selectedSymbol}
              symbol2={selectedSymbol2}
              timeframe={timeframe}
              window={rollingWindow}
            />
          </div>
        </div>

        {/* Correlation Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Rolling Correlation */}
          <div className="bg-white rounded-lg shadow p-6">
            <CorrelationChart
              symbol1={selectedSymbol}
              symbol2={selectedSymbol2}
              timeframe={timeframe}
              window={rollingWindow}
            />
          </div>

          {/* Correlation Heatmap */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">
                Symbols for Heatmap (comma-separated)
              </label>
              <input
                type="text"
                value={selectedSymbolsForHeatmap.join(',')}
                onChange={(e) =>
                  setSelectedSymbolsForHeatmap(
                    e.target.value.split(',').map((s) => s.trim().toUpperCase())
                  )
                }
                className="w-full px-3 py-2 border rounded"
                placeholder="BTCUSDT,ETHUSDT,BNBUSDT"
              />
            </div>
            <CorrelationHeatmap
              symbols={selectedSymbolsForHeatmap}
              timeframe={timeframe}
              window={100}
            />
          </div>
        </div>

        {/* Time Series Stats Table */}
        <div className="mb-6">
          <TimeSeriesStatsTable
            symbol={selectedSymbol}
            timeframe={timeframe}
            window={60}
          />
        </div>

        {/* Alerts */}
        <div className="mb-6">
          <AlertManager />
        </div>
      </div>
    </div>
  );
};
