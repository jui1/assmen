"""
Database models for trading data
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, Index
from sqlalchemy.sql import func
from database.database import Base


class TickData(Base):
    """Raw tick data from WebSocket"""
    __tablename__ = "tick_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    symbol = Column(String, index=True)
    price = Column(Float)
    quantity = Column(Float)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
    )


class OHLCData(Base):
    """OHLC aggregated data"""
    __tablename__ = "ohlc_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    symbol = Column(String, index=True)
    timeframe = Column(String)  # '1s', '1m', '5m'
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp'),
    )


class AnalyticsResult(Base):
    """Stored analytics results"""
    __tablename__ = "analytics_results"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    symbol = Column(String, index=True)
    symbol2 = Column(String, nullable=True)  # For pair analytics
    timeframe = Column(String)
    metric_name = Column(String)
    metric_value = Column(Float)
    extra_data = Column(String)  # JSON string for additional data (renamed from metadata to avoid SQLAlchemy reserved word)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_symbol_metric_timestamp', 'symbol', 'metric_name', 'timestamp'),
    )


