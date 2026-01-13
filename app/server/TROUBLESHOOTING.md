# Troubleshooting: Data Not Showing

## Issue

API endpoints return empty data (`{"data": []}` or `{}`)

## Root Cause

The WebSocket thread was trying to use async/await which doesn't work in a thread context. This has been fixed.

## Solution Steps

### 1. Restart the Server

**IMPORTANT**: The server MUST be restarted for the fixes to take effect.

```bash
cd app/server
# Stop the current server (Ctrl+C)
# Then restart:
python3 main.py
```

### 2. Verify Data Storage

After restarting, check the server console. You should see:

```
✓ Stored tick #1: BTCUSDT @ $92875.43 at ...
✓ Stored tick #2: ETHUSDT @ $3203.40 at ...
```

### 3. Wait for Data Accumulation

- For **1s timeframe**: Need at least 1 second of ticks
- For **1m timeframe**: Need at least 1 minute of ticks
- For **5m timeframe**: Need at least 5 minutes of ticks

**Wait 1-2 minutes** after restart before checking the UI.

### 4. Test Endpoints

```bash
# Check if ticks are being stored
curl "http://localhost:8010/data/ticks?symbol=BTCUSDT&limit=5"

# Check OHLC data (after 1 minute)
curl "http://localhost:8010/data/ohlc?symbol=BTCUSDT&timeframe=1m"

# Check price stats (after 1 minute)
curl "http://localhost:8010/analytics/price-stats?symbol=BTCUSDT&timeframe=1m"
```

### 5. Debug Endpoint

```bash
# Check database status
curl "http://localhost:8010/debug/data-status"
```

## Expected Behavior After Fix

1. **Server Console**: Shows "✓ Stored tick #X" messages
2. **After 1 minute**: OHLC endpoint returns data
3. **After 1 minute**: Price stats endpoint returns statistics
4. **Frontend**: Statistics widget shows real values (not 0.0000)

## If Still Not Working

1. Check server console for errors
2. Verify WebSocket connection: Look for "Binance WebSocket connection opened successfully"
3. Check database file exists: `ls -la trading_data.db`
4. Check database directly: `sqlite3 trading_data.db "SELECT COUNT(*) FROM tick_data;"`
