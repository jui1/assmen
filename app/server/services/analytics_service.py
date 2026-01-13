"""
Analytics service for computing trading analytics
"""
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from statsmodels.regression.linear_model import OLS
from sklearn.linear_model import HuberRegressor, TheilSenRegressor
from pykalman import KalmanFilter
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from services.data_service import DataService


class AnalyticsService:
    """Service for computing various trading analytics"""
    
    def __init__(self, data_service: DataService):
        self.data_service = data_service
    
    def compute_price_stats(self, df: pd.DataFrame) -> Dict:
        """Compute basic price statistics"""
        if df.empty or 'close' not in df.columns:
            return {}
        
        prices = df['close']
        
        return {
            'mean': float(prices.mean()),
            'std': float(prices.std()),
            'min': float(prices.min()),
            'max': float(prices.max()),
            'median': float(prices.median()),
            'current': float(prices.iloc[-1]),
            'change': float(prices.iloc[-1] - prices.iloc[0]),
            'change_pct': float((prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0] * 100) if prices.iloc[0] != 0 else 0
        }
    
    def compute_ols_hedge_ratio(self, symbol1: str, symbol2: str, 
                                timeframe: str = '1m',
                                window: int = 100) -> Dict:
        """Compute hedge ratio using OLS regression"""
        df1 = self.data_service.resample_data(symbol1, timeframe)
        df2 = self.data_service.resample_data(symbol2, timeframe)
        
        if df1.empty or df2.empty:
            return {}
        
        # Align dataframes
        merged = pd.merge(df1[['timestamp', 'close']], 
                         df2[['timestamp', 'close']], 
                         on='timestamp', 
                         suffixes=('_1', '_2'))
        
        if len(merged) < window:
            window = len(merged)
        
        if window < 10:
            return {}
        
        # Use rolling window
        merged = merged.tail(window)
        
        y = merged['close_1'].values
        x = merged['close_2'].values
        
        # OLS regression
        x_with_const = np.column_stack([np.ones(len(x)), x])
        ols_model = OLS(y, x_with_const).fit()
        
        hedge_ratio = float(ols_model.params[1])
        intercept = float(ols_model.params[0])
        r_squared = float(ols_model.rsquared)
        
        return {
            'hedge_ratio': hedge_ratio,
            'intercept': intercept,
            'r_squared': r_squared,
            'symbol1': symbol1,
            'symbol2': symbol2,
            'window': window
        }
    
    def compute_spread(self, symbol1: str, symbol2: str, 
                      timeframe: str = '1m',
                      hedge_ratio: Optional[float] = None) -> pd.DataFrame:
        """Compute spread between two symbols"""
        df1 = self.data_service.resample_data(symbol1, timeframe)
        df2 = self.data_service.resample_data(symbol2, timeframe)
        
        if df1.empty or df2.empty:
            return pd.DataFrame()
        
        # Align dataframes
        merged = pd.merge(df1[['timestamp', 'close']], 
                         df2[['timestamp', 'close']], 
                         on='timestamp', 
                         suffixes=('_1', '_2'))
        
        if hedge_ratio is None:
            # Compute hedge ratio if not provided
            ols_result = self.compute_ols_hedge_ratio(symbol1, symbol2, timeframe)
            hedge_ratio = ols_result.get('hedge_ratio', 1.0)
        
        merged['spread'] = merged['close_1'] - hedge_ratio * merged['close_2']
        
        return merged[['timestamp', 'spread', 'close_1', 'close_2']]
    
    def compute_zscore(self, series: pd.Series, window: int = 20) -> pd.Series:
        """Compute rolling z-score"""
        if len(series) < window:
            return pd.Series(index=series.index, dtype=float)
        
        rolling_mean = series.rolling(window=window).mean()
        rolling_std = series.rolling(window=window).std()
        
        zscore = (series - rolling_mean) / rolling_std
        return zscore
    
    def compute_adf_test(self, series: pd.Series) -> Dict:
        """Compute Augmented Dickey-Fuller test for stationarity"""
        if len(series) < 10:
            return {}
        
        # Remove NaN values
        series_clean = series.dropna()
        
        if len(series_clean) < 10:
            return {}
        
        try:
            result = adfuller(series_clean)
            
            return {
                'adf_statistic': float(result[0]),
                'p_value': float(result[1]),
                'critical_values': {k: float(v) for k, v in result[4].items()},
                'is_stationary': result[1] < 0.05,
                'lags_used': int(result[2]),
                'n_obs': int(result[3])
            }
        except Exception as e:
            print(f"Error in ADF test: {e}")
            return {}
    
    def compute_rolling_correlation(self, symbol1: str, symbol2: str,
                                   timeframe: str = '1m',
                                   window: int = 20) -> pd.DataFrame:
        """Compute rolling correlation between two symbols"""
        df1 = self.data_service.resample_data(symbol1, timeframe)
        df2 = self.data_service.resample_data(symbol2, timeframe)
        
        if df1.empty or df2.empty:
            return pd.DataFrame()
        
        # Align dataframes
        merged = pd.merge(df1[['timestamp', 'close']], 
                         df2[['timestamp', 'close']], 
                         on='timestamp', 
                         suffixes=('_1', '_2'))
        
        merged['rolling_corr'] = merged['close_1'].rolling(window=window).corr(merged['close_2'])
        
        return merged[['timestamp', 'rolling_corr', 'close_1', 'close_2']]
    
    def compute_kalman_hedge_ratio(self, symbol1: str, symbol2: str,
                                   timeframe: str = '1m',
                                   window: int = 100) -> Dict:
        """Compute hedge ratio using Kalman Filter"""
        df1 = self.data_service.resample_data(symbol1, timeframe)
        df2 = self.data_service.resample_data(symbol2, timeframe)
        
        if df1.empty or df2.empty:
            return {}
        
        # Align dataframes
        merged = pd.merge(df1[['timestamp', 'close']], 
                         df2[['timestamp', 'close']], 
                         on='timestamp', 
                         suffixes=('_1', '_2'))
        
        if len(merged) < window:
            window = len(merged)
        
        if window < 10:
            return {}
        
        merged = merged.tail(window)
        
        y = merged['close_1'].values
        x = merged['close_2'].values
        
        # Kalman Filter setup
        kf = KalmanFilter(
            transition_matrices=np.eye(2),
            observation_matrices=np.vstack([np.ones(len(x)), x]).T,
            initial_state_mean=[0, 1],
            n_dim_state=2,
            n_dim_obs=1
        )
        
        try:
            state_means, _ = kf.em(y).smooth(y)
            hedge_ratio = float(state_means[-1, 1])
            intercept = float(state_means[-1, 0])
            
            return {
                'hedge_ratio': hedge_ratio,
                'intercept': intercept,
                'symbol1': symbol1,
                'symbol2': symbol2,
                'method': 'kalman'
            }
        except Exception as e:
            print(f"Error in Kalman Filter: {e}")
            return {}
    
    def compute_robust_regression(self, symbol1: str, symbol2: str,
                                 timeframe: str = '1m',
                                 method: str = 'huber',
                                 window: int = 100) -> Dict:
        """Compute hedge ratio using robust regression"""
        df1 = self.data_service.resample_data(symbol1, timeframe)
        df2 = self.data_service.resample_data(symbol2, timeframe)
        
        if df1.empty or df2.empty:
            return {}
        
        # Align dataframes
        merged = pd.merge(df1[['timestamp', 'close']], 
                         df2[['timestamp', 'close']], 
                         on='timestamp', 
                         suffixes=('_1', '_2'))
        
        if len(merged) < window:
            window = len(merged)
        
        if window < 10:
            return {}
        
        merged = merged.tail(window)
        
        y = merged['close_1'].values
        x = merged['close_2'].values.reshape(-1, 1)
        
        if method == 'huber':
            model = HuberRegressor()
        elif method == 'theilsen':
            model = TheilSenRegressor()
        else:
            return {}
        
        try:
            model.fit(x, y)
            hedge_ratio = float(model.coef_[0])
            intercept = float(model.intercept_)
            
            return {
                'hedge_ratio': hedge_ratio,
                'intercept': intercept,
                'method': method,
                'symbol1': symbol1,
                'symbol2': symbol2
            }
        except Exception as e:
            print(f"Error in robust regression: {e}")
            return {}
    
    def mean_reversion_backtest(self, symbol1: str, symbol2: str,
                               timeframe: str = '1m',
                               entry_z: float = 2.0,
                               exit_z: float = 0.0,
                               window: int = 20) -> Dict:
        """Simple mean-reversion backtest"""
        spread_df = self.compute_spread(symbol1, symbol2, timeframe)
        
        if spread_df.empty or 'spread' not in spread_df.columns:
            return {}
        
        spread_series = spread_df['spread']
        zscore = self.compute_zscore(spread_series, window)
        
        # Backtest logic
        positions = []
        current_position = 0  # 0 = no position, 1 = long spread, -1 = short spread
        
        for i, z in enumerate(zscore):
            if pd.isna(z):
                continue
            
            # Entry signals
            if current_position == 0:
                if z > entry_z:
                    current_position = -1  # Short spread (expect mean reversion)
                    positions.append({
                        'timestamp': spread_df.iloc[i]['timestamp'],
                        'action': 'entry',
                        'position': -1,
                        'zscore': z,
                        'spread': spread_series.iloc[i]
                    })
                elif z < -entry_z:
                    current_position = 1  # Long spread
                    positions.append({
                        'timestamp': spread_df.iloc[i]['timestamp'],
                        'action': 'entry',
                        'position': 1,
                        'zscore': z,
                        'spread': spread_series.iloc[i]
                    })
            
            # Exit signals
            elif current_position != 0:
                if (current_position == -1 and z < exit_z) or (current_position == 1 and z > -exit_z):
                    entry_price = positions[-1]['spread'] if positions else spread_series.iloc[i]
                    pnl = (entry_price - spread_series.iloc[i]) * current_position
                    
                    positions.append({
                        'timestamp': spread_df.iloc[i]['timestamp'],
                        'action': 'exit',
                        'position': 0,
                        'zscore': z,
                        'spread': spread_series.iloc[i],
                        'pnl': pnl
                    })
                    current_position = 0
        
        # Calculate statistics
        exits = [p for p in positions if p['action'] == 'exit']
        total_trades = len(exits)
        total_pnl = sum(p.get('pnl', 0) for p in exits)
        winning_trades = len([p for p in exits if p.get('pnl', 0) > 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'positions': positions,
            'symbol1': symbol1,
            'symbol2': symbol2,
            'entry_z': entry_z,
            'exit_z': exit_z
        }
    
    def compute_cross_correlation_matrix(self, symbols: List[str],
                                        timeframe: str = '1m',
                                        window: int = 100) -> pd.DataFrame:
        """Compute cross-correlation matrix for multiple symbols"""
        data_dict = self.data_service.get_multiple_symbols(symbols, timeframe)
        
        # Align all dataframes
        aligned_data = {}
        for symbol, df in data_dict.items():
            if not df.empty and 'close' in df.columns:
                aligned_data[symbol] = df.set_index('timestamp')['close']
        
        if len(aligned_data) < 2:
            return pd.DataFrame()
        
        # Create combined dataframe
        combined = pd.DataFrame(aligned_data)
        
        if len(combined) < window:
            window = len(combined)
        
        combined = combined.tail(window)
        
        # Compute correlation matrix
        corr_matrix = combined.corr()
        
        return corr_matrix
    
    def compute_liquidity_metrics(self, symbol: str, timeframe: str = '1m') -> Dict:
        """Compute liquidity metrics"""
        df = self.data_service.resample_data(symbol, timeframe)
        
        if df.empty or 'volume' not in df.columns:
            return {}
        
        volume = df['volume']
        prices = df['close']
        
        # Volume-weighted average price approximation
        if len(df) > 0:
            vwap_approx = (prices * volume).sum() / volume.sum() if volume.sum() > 0 else prices.mean()
        else:
            vwap_approx = 0
        
        return {
            'avg_volume': float(volume.mean()),
            'total_volume': float(volume.sum()),
            'volume_std': float(volume.std()),
            'vwap_approx': float(vwap_approx),
            'current_volume': float(volume.iloc[-1]) if len(volume) > 0 else 0
        }


