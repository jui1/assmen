## Detail Description

- **Backend**: Python FastAPI (real-time data ingestion, analytics, storage) - **Python only, no NestJS**
- **Frontend**: React + TypeScript (interactive dashboard, real-time charts)

## Features

### Data Ingestion

- Real-time WebSocket connection to Binance
- Automatic data storage in SQLite
- Support for multiple symbols simultaneously

### Data Processing

- Resampling to multiple timeframes (1s, 1m, 5m)
- OHLC aggregation
- Efficient data storage and retrieval

### Analytics

- **Price Statistics**: Mean, std, min, max, median, change
- **Hedge Ratio**: OLS regression, Kalman Filter, Robust regression (Huber, Theil-Sen)
- **Spread Analysis**: Spread calculation with customizable hedge ratio
- **Z-Score**: Rolling z-score for mean-reversion analysis
- **ADF Test**: Augmented Dickey-Fuller test for stationarity
- **Rolling Correlation**: Dynamic correlation analysis
- **Cross-Correlation Matrix**: Heatmap visualization
- **Mean-Reversion Backtest**: Simple backtest with entry/exit signals
- **Liquidity Metrics**: Volume analysis

### Visualization

- Real-time price charts
- Spread visualization
- Z-score charts with thresholds
- Correlation plots
- Correlation heatmaps
- Interactive controls (zoom, pan, hover)

### Alerts

- Custom alert rules (z-score, price, spread thresholds)
- Real-time alert monitoring
- Alert history

### Data Export

- CSV export for OHLC data
- Time-series statistics export
- Downloadable analytics results

## Setup

### Backend Setup

1. Navigate to the server directory:

```bash
cd app/server
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the server:

```bash
python main.py
```

Or use the startup script:

```bash
./run.sh
```

The API will be available at http://localhost:8010
API documentation at http://localhost:8010/docs

### Frontend Setup

1. Navigate to the client directory:

```bash
cd app/clients
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

The frontend will be available at http://localhost:5173

## Usage

1. Start the backend server first
2. Start the frontend development server
3. Open http://localhost:5173 in your browser
4. Select symbols and timeframes from the controls
5. View real-time analytics and charts
6. Configure alerts as needed
7. Export data when needed

## Default Symbols

The application starts with these default symbols:

- BTCUSDT
- ETHUSDT
- BNBUSDT

You can subscribe to additional symbols through the API or modify the default list in `main.py`.

## Database

SQLite database is automatically created at `app/server/trading_data.db`. The database stores:

- Raw tick data
- OHLC aggregated data
- Analytics results
- Alert configurations

## API Endpoints

Key endpoints:

- `GET /symbols` - Get available symbols
- `GET /data/ohlc` - Get OHLC data
- `GET /analytics/price-stats` - Get price statistics
- `GET /analytics/hedge-ratio` - Get hedge ratio
- `GET /analytics/spread` - Get spread data
- `GET /analytics/zscore` - Get z-score data
- `GET /analytics/adf-test` - Run ADF test
- `GET /analytics/correlation` - Get correlation data
- `GET /analytics/correlation-matrix` - Get correlation matrix
- `GET /analytics/backtest` - Run backtest
- `GET /alerts` - Get all alerts
- `POST /alerts` - Create alert
- `DELETE /alerts/{id}` - Delete alert
- `GET /export/csv` - Export data as CSV
- `POST /upload/ohlc` - Upload OHLC data (optional)



## Technologies

- **Backend**: FastAPI, SQLAlchemy, Pandas, NumPy, SciPy, Statsmodels, PyKalman
- **Frontend**: React, TypeScript, Plotly, Tailwind CSS, Axios
- **Database**: SQLite
- **WebSocket**: websocket-client, FastAPI WebSocket
