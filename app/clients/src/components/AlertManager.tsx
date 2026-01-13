/**
 * Alert management component
 */
import React, { useEffect, useState } from 'react';
import { apiClient } from '../utils/api';
import type { Alert } from '../utils/api';

export const AlertManager: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [newAlert, setNewAlert] = useState({
    symbol: '',
    condition: 'zscore >',
    threshold: 2.0,
  });

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchAlerts = async () => {
    try {
      const alertsData = await apiClient.getAlerts();
      setAlerts(alertsData);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient.createAlert(newAlert.symbol, newAlert.condition, newAlert.threshold);
      setNewAlert({ symbol: '', condition: 'zscore >', threshold: 2.0 });
      setShowForm(false);
      fetchAlerts();
    } catch (error) {
      console.error('Error creating alert:', error);
      alert('Error creating alert');
    }
  };

  const handleDeleteAlert = async (alertId: string) => {
    if (!confirm('Are you sure you want to delete this alert?')) return;
    try {
      await apiClient.deleteAlert(alertId);
      fetchAlerts();
    } catch (error) {
      console.error('Error deleting alert:', error);
      alert('Error deleting alert');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-full">Loading...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Alerts</h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {showForm ? 'Cancel' : 'New Alert'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreateAlert} className="mb-4 p-4 bg-gray-50 rounded">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Symbol</label>
              <input
                type="text"
                value={newAlert.symbol}
                onChange={(e) => setNewAlert({ ...newAlert, symbol: e.target.value.toUpperCase() })}
                className="w-full px-3 py-2 border rounded"
                placeholder="BTCUSDT"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Condition</label>
              <select
                value={newAlert.condition}
                onChange={(e) => setNewAlert({ ...newAlert, condition: e.target.value })}
                className="w-full px-3 py-2 border rounded"
              >
                <option value="zscore >">Z-Score &gt;</option>
                <option value="zscore <">Z-Score &lt;</option>
                <option value="price >">Price &gt;</option>
                <option value="price <">Price &lt;</option>
                <option value="spread >">Spread &gt;</option>
                <option value="spread <">Spread &lt;</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Threshold</label>
              <input
                type="number"
                step="0.01"
                value={newAlert.threshold}
                onChange={(e) => setNewAlert({ ...newAlert, threshold: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border rounded"
                required
              />
            </div>
          </div>
          <button
            type="submit"
            className="mt-4 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          >
            Create Alert
          </button>
        </form>
      )}

      <div className="space-y-2">
        {alerts.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No alerts configured</p>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-4 border rounded flex justify-between items-center ${
                alert.triggered ? 'bg-red-50 border-red-300' : 'bg-gray-50'
              }`}
            >
              <div>
                <p className="font-medium">
                  {alert.symbol} {alert.condition} {alert.threshold}
                </p>
                {alert.triggered && (
                  <p className="text-sm text-red-600">Triggered!</p>
                )}
                {alert.last_triggered && (
                  <p className="text-xs text-gray-500">
                    Last triggered: {new Date(alert.last_triggered).toLocaleString()}
                  </p>
                )}
              </div>
              <button
                onClick={() => handleDeleteAlert(alert.id)}
                className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};


