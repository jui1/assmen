# Quick Start Guide

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## Step 1: Backend Setup

```bash
cd app/server
pip install -r requirements.txt
python main.py
```

The backend will start on http://localhost:8000

## Step 2: Frontend Setup

In a new terminal:

```bash
cd app/clients
npm install
npm run dev
```

The frontend will start on http://localhost:5173

## Step 3: Access the Application

Open http://localhost:5173 in your browser.

## What to Expect

1. **Initial Data Collection**: The backend automatically starts collecting data from Binance for BTCUSDT, ETHUSDT, and BNBUSDT. It may take a few seconds to accumulate enough data for analytics.

2. **Real-time Updates**:

   - Price charts update based on selected timeframe
   - Z-score updates every 500ms for real-time monitoring
   - Statistics widgets update every second

3. **Analytics Availability**:

   - Basic price stats: Available immediately
   - Spread/Z-score: Available after a few data points
   - Correlation: Requires more data points
   - ADF test: Requires sufficient data
   - Backtest: Requires historical data

4. **Controls**:

   - Select different symbols from dropdowns
   - Change timeframe (1s, 1m, 5m)
   - Adjust rolling window
   - Choose regression method
   - Run ADF test and backtest

5. **Alerts**:

   - Create custom alerts
   - Monitor triggered alerts
   - Alerts check in real-time

6. **Export**:
   - Export data as CSV
   - Export time-series statistics

## Troubleshooting

- **No data showing**: Wait a few seconds for data to accumulate
- **WebSocket disconnected**: Check backend is running and restart if needed
- **Charts not updating**: Check browser console for errors
- **Analytics errors**: Ensure sufficient data is available (try longer timeframes or wait longer)

## Default Configuration

- Default symbols: BTCUSDT, ETHUSDT, BNBUSDT
- Default timeframe: 1m
- Default rolling window: 20
- Database: SQLite (created automatically)
