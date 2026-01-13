"""
Alert service for managing and checking trading alerts
"""
from typing import Dict, List, Optional
from services.analytics_service import AnalyticsService
import json
import os


class Alert:
    """Alert definition"""
    def __init__(self, id: str, symbol: str, condition: str, threshold: float, 
                 enabled: bool = True):
        self.id = id
        self.symbol = symbol
        self.condition = condition  # e.g., 'zscore >', 'price >', 'spread >'
        self.threshold = threshold
        self.enabled = enabled
        self.triggered = False
        self.last_triggered = None


class AlertService:
    """Service for managing alerts"""
    
    def __init__(self, analytics_service: AnalyticsService):
        self.analytics_service = analytics_service
        self.alerts: Dict[str, Alert] = {}
        self.alert_file = "alerts.json"
        self.load_alerts()
    
    def add_alert(self, alert: Alert):
        """Add an alert"""
        self.alerts[alert.id] = alert
        self.save_alerts()
    
    def remove_alert(self, alert_id: str):
        """Remove an alert"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            self.save_alerts()
    
    def get_alerts(self) -> List[Dict]:
        """Get all alerts"""
        return [{
            'id': a.id,
            'symbol': a.symbol,
            'condition': a.condition,
            'threshold': a.threshold,
            'enabled': a.enabled,
            'triggered': a.triggered,
            'last_triggered': a.last_triggered.isoformat() if a.last_triggered else None
        } for a in self.alerts.values()]
    
    async def check_alerts(self, symbol: str, price: float):
        """Check alerts for a symbol"""
        from datetime import datetime
        
        for alert in self.alerts.values():
            if not alert.enabled or alert.symbol != symbol:
                continue
            
            try:
                triggered = False
                
                if alert.condition == 'zscore >':
                    # Need to compute z-score
                    # For simplicity, we'll use a rolling window
                    import pandas as pd
                    spread_df = self.analytics_service.compute_spread(symbol, symbol, '1m')
                    if not spread_df.empty and 'spread' in spread_df.columns:
                        zscore = self.analytics_service.compute_zscore(spread_df['spread'])
                        if len(zscore) > 0 and not pd.isna(zscore.iloc[-1]):
                            if zscore.iloc[-1] > alert.threshold:
                                triggered = True
                
                elif alert.condition == 'price >':
                    if price > alert.threshold:
                        triggered = True
                elif alert.condition == 'price <':
                    if price < alert.threshold:
                        triggered = True
                elif alert.condition == 'spread >':
                    spread_df = self.analytics_service.compute_spread(symbol, symbol, '1m')
                    if not spread_df.empty and 'spread' in spread_df.columns:
                        if spread_df['spread'].iloc[-1] > alert.threshold:
                            triggered = True
                
                if triggered and not alert.triggered:
                    alert.triggered = True
                    alert.last_triggered = datetime.now()
                    # Could send notification here
                    print(f"ALERT TRIGGERED: {alert.id} - {alert.symbol} {alert.condition} {alert.threshold}")
                elif not triggered:
                    alert.triggered = False
                    
            except Exception as e:
                print(f"Error checking alert {alert.id}: {e}")
    
    def save_alerts(self):
        """Save alerts to file"""
        try:
            data = [{
                'id': a.id,
                'symbol': a.symbol,
                'condition': a.condition,
                'threshold': a.threshold,
                'enabled': a.enabled
            } for a in self.alerts.values()]
            
            with open(self.alert_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving alerts: {e}")
    
    def load_alerts(self):
        """Load alerts from file"""
        if not os.path.exists(self.alert_file):
            return
        
        try:
            with open(self.alert_file, 'r') as f:
                data = json.load(f)
            
            for item in data:
                alert = Alert(
                    id=item['id'],
                    symbol=item['symbol'],
                    condition=item['condition'],
                    threshold=item['threshold'],
                    enabled=item.get('enabled', True)
                )
                self.alerts[alert.id] = alert
        except Exception as e:
            print(f"Error loading alerts: {e}")

