"""
API routes for the trading analytics application
"""

from fastapi import APIRouter, Query, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional, Any
from datetime import datetime
import pandas as pd
import numpy as np
import io
import math

from services.data_service import DataService
from services.analytics_service import AnalyticsService
from services.alert_service import AlertService, Alert


def clean_json_value(value: Any) -> Any:
    """Convert NaN, Inf, and -Inf to JSON-compliant values"""

    # Handle None first
    if value is None:
        return None

    # Handle numpy types first (before checking for iterables)
    if isinstance(value, np.bool_):
        return bool(value)
    elif isinstance(value, (np.integer, np.int64, np.int32, np.int8, np.int16)):
        return int(value)
    elif isinstance(value, (np.floating, np.float64, np.float32, np.float16)):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    elif isinstance(value, np.ndarray):
        return [clean_json_value(item) for item in value.tolist()]
    # Handle Python native types
    elif isinstance(value, bool):
        return value
    elif isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    elif isinstance(value, (int, str)):
        return value
    elif isinstance(value, dict):
        return {k: clean_json_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [clean_json_value(item) for item in value]
    # Handle datetime and other special types
    elif hasattr(value, "isoformat"):
        return value.isoformat()
    # Handle other types - convert to string as last resort
    else:
        try:
            # Try to convert to native Python type
            if hasattr(value, "item"):  # numpy scalar
                return clean_json_value(value.item())
            return str(value)
        except (TypeError, ValueError, AttributeError):
            return str(value)


router = APIRouter()

# These will be injected
data_service: Optional[DataService] = None
analytics_service: Optional[AnalyticsService] = None
alert_service: Optional[AlertService] = None


def set_services(ds: DataService, as_: AnalyticsService, als: AlertService):
    """Set service instances"""
    global data_service, analytics_service, alert_service
    data_service = ds
    analytics_service = as_
    alert_service = als


@router.get("/symbols")
async def get_symbols():
    """Get available symbols"""
    # Default Binance symbols
    return {
        "symbols": [
            "BTCUSDT",
            "ETHUSDT",
            "BNBUSDT",
            "ADAUSDT",
            "SOLUSDT",
            "XRPUSDT",
            "DOTUSDT",
            "DOGEUSDT",
            "AVAXUSDT",
            "LINKUSDT",
        ]
    }


@router.post("/debug/test-store")
async def test_store():
    """Test endpoint to manually store a tick (for debugging)"""
    if not data_service:
        return {"error": "Data service not initialized"}

    from datetime import datetime

    test_tick = {
        "timestamp": datetime.now(),
        "symbol": "BTCUSDT",
        "price": 92875.43,
        "quantity": 100.0,
    }

    try:
        data_service._store_tick_sync(test_tick)
        return {"success": True, "message": "Test tick stored", "tick": test_tick}
    except Exception as e:
        import traceback

        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


@router.get("/debug/data-status")
async def get_data_status():
    """Debug endpoint to check data status"""
    if not data_service:
        return {"error": "Data service not initialized"}

    from database.database import SessionLocal, DATABASE_URL
    from database.models import TickData
    import os

    db = SessionLocal()
    try:
        # Check database file
        db_file = (
            DATABASE_URL.replace("sqlite:///", "") if "sqlite" in DATABASE_URL else None
        )
        db_exists = os.path.exists(db_file) if db_file else None
        db_size = os.path.getsize(db_file) if db_file and db_exists else 0

        # Count ticks per symbol
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        status = {
            "database": {
                "url": DATABASE_URL,
                "file": db_file,
                "exists": db_exists,
                "size_bytes": db_size,
            },
            "symbols": {},
        }

        for symbol in symbols:
            count = db.query(TickData).filter(TickData.symbol == symbol).count()
            latest = (
                db.query(TickData)
                .filter(TickData.symbol == symbol)
                .order_by(TickData.timestamp.desc())
                .first()
            )
            status["symbols"][symbol] = {
                "tick_count": count,
                "latest_timestamp": latest.timestamp.isoformat() if latest else None,
                "latest_price": latest.price if latest else None,
            }

        # Get total count
        total_ticks = db.query(TickData).count()
        status["total_ticks"] = total_ticks

        return status
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}
    finally:
        db.close()


@router.get("/data/ticks")
async def get_ticks(
    symbol: str = Query(..., description="Trading symbol"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    limit: int = Query(1000, description="Maximum number of records"),
):
    """Get tick data"""
    if not data_service:
        raise HTTPException(status_code=500, detail="Data service not initialized")

    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None

    df = data_service.get_ticks(symbol, start, end, limit)

    if df.empty:
        return {"data": []}

    df["timestamp"] = df["timestamp"].apply(
        lambda x: x.isoformat() if hasattr(x, "isoformat") else str(x)
    )

    return {"data": df.to_dict("records")}


@router.get("/data/ohlc")
async def get_ohlc(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1m", description="Timeframe: 1s, 1m, 5m"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
):
    """Get OHLC data"""
    if not data_service:
        raise HTTPException(status_code=500, detail="Data service not initialized")

    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None

    # First check if we have any tick data
    tick_count = len(data_service.get_ticks(symbol, start, end, limit=1))
    if tick_count == 0:
        print(f"No tick data found for {symbol}. WebSocket may not be receiving data.")
        return {
            "data": [],
            "message": "No data available yet. Waiting for WebSocket data...",
        }

    if timeframe in ["1s", "1m", "5m"]:
        df = data_service.resample_data(symbol, timeframe, start, end)
    else:
        df = data_service.get_ohlc(symbol, timeframe, start, end)

    if df.empty:
        print(f"Resampled data is empty for {symbol} with timeframe {timeframe}")
        return {
            "data": [],
            "message": "Insufficient data for resampling. Need more tick data.",
        }

    df["timestamp"] = df["timestamp"].apply(
        lambda x: x.isoformat() if hasattr(x, "isoformat") else str(x)
    )

    return {"data": df.to_dict("records")}


@router.get("/analytics/price-stats")
async def get_price_stats(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1m", description="Timeframe"),
):
    """Get price statistics"""
    if not analytics_service or not data_service:
        raise HTTPException(status_code=500, detail="Services not initialized")

    df = data_service.resample_data(symbol, timeframe)

    if df.empty:
        return {}

    stats = analytics_service.compute_price_stats(df)
    # Clean NaN/Inf values before returning
    return clean_json_value(stats)


@router.get("/analytics/hedge-ratio")
async def get_hedge_ratio(
    symbol1: str = Query(..., description="First symbol"),
    symbol2: str = Query(..., description="Second symbol"),
    timeframe: str = Query("1m", description="Timeframe"),
    method: str = Query("ols", description="Method: ols, kalman, huber, theilsen"),
    window: int = Query(100, description="Window size"),
):
    """Get hedge ratio"""
    if not analytics_service:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")

    if method == "ols":
        result = analytics_service.compute_ols_hedge_ratio(
            symbol1, symbol2, timeframe, window
        )
    elif method == "kalman":
        result = analytics_service.compute_kalman_hedge_ratio(
            symbol1, symbol2, timeframe, window
        )
    elif method in ["huber", "theilsen"]:
        result = analytics_service.compute_robust_regression(
            symbol1, symbol2, timeframe, method, window
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid method")

    # Clean NaN/Inf values
    return clean_json_value(result)


@router.get("/analytics/spread")
async def get_spread(
    symbol1: str = Query(..., description="First symbol"),
    symbol2: str = Query(..., description="Second symbol"),
    timeframe: str = Query("1m", description="Timeframe"),
    hedge_ratio: Optional[float] = Query(None, description="Hedge ratio (optional)"),
):
    """Get spread data"""
    if not analytics_service:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")

    df = analytics_service.compute_spread(symbol1, symbol2, timeframe, hedge_ratio)

    if df.empty:
        return {"data": []}

    df["timestamp"] = df["timestamp"].apply(
        lambda x: x.isoformat() if hasattr(x, "isoformat") else str(x)
    )

    # Clean NaN/Inf values
    records = df.to_dict("records")
    cleaned_records = [clean_json_value(record) for record in records]

    return {"data": cleaned_records}


@router.get("/analytics/zscore")
async def get_zscore(
    symbol1: str = Query(..., description="First symbol"),
    symbol2: str = Query(..., description="Second symbol"),
    timeframe: str = Query("1m", description="Timeframe"),
    window: int = Query(20, description="Z-score window"),
):
    """Get z-score data"""
    if not analytics_service:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")

    spread_df = analytics_service.compute_spread(symbol1, symbol2, timeframe)

    if spread_df.empty or "spread" not in spread_df.columns:
        return {"data": []}

    zscore = analytics_service.compute_zscore(spread_df["spread"], window)

    result = pd.DataFrame(
        {
            "timestamp": spread_df["timestamp"],
            "zscore": zscore.values,
            "spread": spread_df["spread"].values,
        }
    )

    result = result.dropna()
    result["timestamp"] = result["timestamp"].apply(
        lambda x: x.isoformat() if hasattr(x, "isoformat") else str(x)
    )

    # Clean NaN/Inf values
    records = result.to_dict("records")
    cleaned_records = [clean_json_value(record) for record in records]

    return {"data": cleaned_records}


@router.get("/analytics/adf-test")
async def get_adf_test(
    symbol1: str = Query(..., description="First symbol"),
    symbol2: str = Query(..., description="Second symbol"),
    timeframe: str = Query("1m", description="Timeframe"),
):
    """Get ADF test results"""
    if not analytics_service:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")

    spread_df = analytics_service.compute_spread(symbol1, symbol2, timeframe)

    if spread_df.empty or "spread" not in spread_df.columns:
        return {}

    result = analytics_service.compute_adf_test(spread_df["spread"])
    # Clean NaN/Inf values
    return clean_json_value(result)


@router.get("/analytics/correlation")
async def get_correlation(
    symbol1: str = Query(..., description="First symbol"),
    symbol2: str = Query(..., description="Second symbol"),
    timeframe: str = Query("1m", description="Timeframe"),
    window: int = Query(20, description="Rolling window"),
):
    """Get rolling correlation"""
    if not analytics_service:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")

    df = analytics_service.compute_rolling_correlation(
        symbol1, symbol2, timeframe, window
    )

    if df.empty:
        return {"data": []}

    df["timestamp"] = df["timestamp"].apply(
        lambda x: x.isoformat() if hasattr(x, "isoformat") else str(x)
    )

    # Clean NaN/Inf values before converting to dict
    records = df.to_dict("records")
    cleaned_records = [clean_json_value(record) for record in records]

    return {"data": cleaned_records}


@router.get("/analytics/correlation-matrix")
async def get_correlation_matrix(
    symbols: str = Query(..., description="Comma-separated symbols"),
    timeframe: str = Query("1m", description="Timeframe"),
    window: int = Query(100, description="Window size"),
):
    """Get correlation matrix"""
    if not analytics_service:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")

    symbol_list = [s.strip() for s in symbols.split(",")]
    corr_matrix = analytics_service.compute_cross_correlation_matrix(
        symbol_list, timeframe, window
    )

    if corr_matrix.empty:
        return {"data": {}}

    # Clean NaN/Inf values
    matrix_dict = corr_matrix.to_dict()
    return {"data": clean_json_value(matrix_dict)}


@router.get("/analytics/backtest")
async def get_backtest(
    symbol1: str = Query(..., description="First symbol"),
    symbol2: str = Query(..., description="Second symbol"),
    timeframe: str = Query("1m", description="Timeframe"),
    entry_z: float = Query(2.0, description="Entry z-score threshold"),
    exit_z: float = Query(0.0, description="Exit z-score threshold"),
    window: int = Query(20, description="Z-score window"),
):
    """Get mean-reversion backtest results"""
    if not analytics_service:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")

    result = analytics_service.mean_reversion_backtest(
        symbol1, symbol2, timeframe, entry_z, exit_z, window
    )

    # Convert positions timestamps
    if "positions" in result:
        for pos in result["positions"]:
            if "timestamp" in pos and hasattr(pos["timestamp"], "isoformat"):
                pos["timestamp"] = pos["timestamp"].isoformat()

    # Clean NaN/Inf values
    return clean_json_value(result)


@router.get("/analytics/liquidity")
async def get_liquidity(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1m", description="Timeframe"),
):
    """Get liquidity metrics"""
    if not analytics_service:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")

    result = analytics_service.compute_liquidity_metrics(symbol, timeframe)
    # Clean NaN/Inf values
    return clean_json_value(result)


@router.get("/analytics/time-series-stats")
async def get_time_series_stats(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1m", description="Timeframe"),
    window: int = Query(60, description="Number of periods"),
):
    """Get time-series statistics for each period"""
    if not data_service or not analytics_service:
        raise HTTPException(status_code=500, detail="Services not initialized")

    df = data_service.resample_data(symbol, timeframe)

    if df.empty:
        return {"data": []}

    df = df.tail(window)

    # Compute stats for each row
    results = []
    for i in range(len(df)):
        window_df = df.iloc[max(0, i - 20) : i + 1]  # Rolling 20-period window
        if len(window_df) > 0:
            stats = analytics_service.compute_price_stats(window_df)
            stats["timestamp"] = (
                df.iloc[i]["timestamp"].isoformat()
                if hasattr(df.iloc[i]["timestamp"], "isoformat")
                else str(df.iloc[i]["timestamp"])
            )
            stats["price"] = float(df.iloc[i]["close"])
            stats["volume"] = float(df.iloc[i].get("volume", 0))
            # Clean NaN/Inf values before returning
            stats = clean_json_value(stats)
            results.append(stats)

    return {"data": results}


@router.get("/alerts")
async def get_alerts():
    """Get all alerts"""
    if not alert_service:
        raise HTTPException(status_code=500, detail="Alert service not initialized")

    return {"alerts": alert_service.get_alerts()}


@router.post("/alerts")
async def create_alert(
    symbol: str = Query(..., description="Trading symbol"),
    condition: str = Query(
        ..., description="Condition: zscore >, price >, price <, spread >"
    ),
    threshold: float = Query(..., description="Threshold value"),
):
    """Create a new alert"""
    if not alert_service:
        raise HTTPException(status_code=500, detail="Alert service not initialized")

    import uuid

    alert_id = str(uuid.uuid4())
    alert = Alert(alert_id, symbol, condition, threshold)
    alert_service.add_alert(alert)

    return {"id": alert_id, "message": "Alert created"}


@router.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert"""
    if not alert_service:
        raise HTTPException(status_code=500, detail="Alert service not initialized")

    alert_service.remove_alert(alert_id)
    return {"message": "Alert deleted"}


@router.get("/export/csv")
async def export_csv(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("1m", description="Timeframe"),
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
):
    """Export data as CSV"""
    if not data_service:
        raise HTTPException(status_code=500, detail="Data service not initialized")

    start = datetime.fromisoformat(start_time) if start_time else None
    end = datetime.fromisoformat(end_time) if end_time else None

    if timeframe in ["1s", "1m", "5m"]:
        df = data_service.resample_data(symbol, timeframe, start, end)
    else:
        df = data_service.get_ohlc(symbol, timeframe, start, end)

    if df.empty:
        raise HTTPException(status_code=404, detail="No data found")

    # Convert to CSV
    stream = io.StringIO()
    df.to_csv(stream, index=False)

    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={symbol}_{timeframe}.csv"
        },
    )


@router.post("/upload/ohlc")
async def upload_ohlc(file: UploadFile = File(...)):
    """Upload OHLC data (optional feature)"""
    if not data_service:
        raise HTTPException(status_code=500, detail="Data service not initialized")

    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))

        # Validate columns
        required_cols = ["timestamp", "open", "high", "low", "close"]
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(status_code=400, detail="Missing required columns")

        # Store OHLC data
        # This is a simplified version - you'd want to properly parse and store
        return {"message": "Data uploaded successfully", "rows": len(df)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
