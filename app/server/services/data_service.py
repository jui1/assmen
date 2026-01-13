"""
Data service for storing and retrieving trading data
"""

from database.database import SessionLocal
from database.models import TickData, OHLCData
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import asyncio
from concurrent.futures import ThreadPoolExecutor


class DataService:
    """Service for data storage and retrieval"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def store_tick(self, tick_data: Dict):
        """Store tick data asynchronously"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If no event loop in current thread, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        await loop.run_in_executor(self.executor, self._store_tick_sync, tick_data)

    def _store_tick_sync(self, tick_data: Dict):
        """Synchronously store tick data"""
        db = SessionLocal()
        try:
            tick = TickData(
                timestamp=tick_data["timestamp"],
                symbol=tick_data["symbol"],
                price=tick_data["price"],
                quantity=tick_data["quantity"],
            )
            db.add(tick)
            db.commit()

            # Debug: Print first few stored ticks and periodic updates
            count = (
                db.query(TickData)
                .filter(TickData.symbol == tick_data["symbol"])
                .count()
            )
            if count <= 5:
                print(
                    f"✓ Stored tick #{count}: {tick_data['symbol']} @ ${tick_data['price']:.2f} at {tick_data['timestamp']}"
                )
            elif count % 100 == 0:
                print(
                    f"✓ Stored {count} ticks for {tick_data['symbol']} (latest: ${tick_data['price']:.2f})"
                )
        except Exception as e:
            print(
                f"✗ Error storing tick data for {tick_data.get('symbol', 'unknown')}: {e}"
            )
            import traceback

            traceback.print_exc()
            db.rollback()
        finally:
            db.close()

    def get_ticks(
        self,
        symbol: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 10000,
    ) -> pd.DataFrame:
        """Get tick data as DataFrame"""
        db = SessionLocal()
        try:
            query = db.query(TickData).filter(TickData.symbol == symbol)

            if start_time:
                query = query.filter(TickData.timestamp >= start_time)
            if end_time:
                query = query.filter(TickData.timestamp <= end_time)

            query = query.order_by(TickData.timestamp.desc()).limit(limit)

            ticks = query.all()

            data = [
                {
                    "timestamp": t.timestamp,
                    "symbol": t.symbol,
                    "price": t.price,
                    "quantity": t.quantity,
                }
                for t in ticks
            ]

            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            df = df.sort_values("timestamp")
            return df
        finally:
            db.close()

    def resample_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Resample tick data to OHLC"""
        df = self.get_ticks(symbol, start_time, end_time)

        if df.empty:
            print(f"No tick data available for {symbol} to resample")
            return pd.DataFrame()

        print(f"Resampling {len(df)} ticks for {symbol} with timeframe {timeframe}")

        df = df.set_index("timestamp")

        # Resample based on timeframe
        timeframe_map = {"1s": "1S", "1m": "1T", "5m": "5T"}

        freq = timeframe_map.get(timeframe, "1T")

        ohlc = df["price"].resample(freq).ohlc()
        volume = df["quantity"].resample(freq).sum()

        result = pd.DataFrame(
            {
                "open": ohlc["open"],
                "high": ohlc["high"],
                "low": ohlc["low"],
                "close": ohlc["close"],
                "volume": volume,
            }
        )

        result = result.dropna()

        if result.empty:
            print(f"Resampled result is empty for {symbol} with timeframe {timeframe}")
            return pd.DataFrame()

        result["symbol"] = symbol
        result["timeframe"] = timeframe
        result = result.reset_index()

        print(f"Resampled to {len(result)} OHLC bars for {symbol}")

        # Store OHLC data
        self._store_ohlc(result)

        return result

    def _store_ohlc(self, ohlc_df: pd.DataFrame):
        """Store OHLC data"""
        db = SessionLocal()
        try:
            for _, row in ohlc_df.iterrows():
                ohlc = OHLCData(
                    timestamp=row["timestamp"],
                    symbol=row["symbol"],
                    timeframe=row["timeframe"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row.get("volume", 0),
                )
                db.add(ohlc)
            db.commit()
        except Exception as e:
            print(f"Error storing OHLC data: {e}")
            db.rollback()
        finally:
            db.close()

    def get_ohlc(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Get OHLC data"""
        db = SessionLocal()
        try:
            query = db.query(OHLCData).filter(
                OHLCData.symbol == symbol, OHLCData.timeframe == timeframe
            )

            if start_time:
                query = query.filter(OHLCData.timestamp >= start_time)
            if end_time:
                query = query.filter(OHLCData.timestamp <= end_time)

            query = query.order_by(OHLCData.timestamp)

            ohlc_data = query.all()

            if not ohlc_data:
                return pd.DataFrame()

            data = [
                {
                    "timestamp": o.timestamp,
                    "symbol": o.symbol,
                    "timeframe": o.timeframe,
                    "open": o.open,
                    "high": o.high,
                    "low": o.low,
                    "close": o.close,
                    "volume": o.volume,
                }
                for o in ohlc_data
            ]

            return pd.DataFrame(data)
        finally:
            db.close()

    def get_multiple_symbols(
        self,
        symbols: List[str],
        timeframe: str = "1m",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Get data for multiple symbols"""
        result = {}
        for symbol in symbols:
            if timeframe in ["1s", "1m", "5m"]:
                df = self.resample_data(symbol, timeframe, start_time, end_time)
            else:
                df = self.get_ohlc(symbol, timeframe, start_time, end_time)
            result[symbol] = df
        return result
