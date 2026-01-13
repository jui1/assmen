"""
WebSocket service for Binance data ingestion
"""

import asyncio
import websocket
import json
from datetime import datetime
from typing import Dict, List, Optional
import threading
from services.data_service import DataService
from services.alert_service import AlertService


class WebSocketService:
    """Service to handle Binance WebSocket connections and data ingestion"""

    def __init__(self, data_service: DataService, alert_service: AlertService):
        self.data_service = data_service
        self.alert_service = alert_service
        self.ws = None
        self.running = False
        self.subscribed_symbols = set()
        self.latest_data = {}
        self.lock = threading.Lock()
        self._reconnect_attempts = 0

    async def start(self):
        """Start WebSocket connection"""
        self.running = True
        # Start in a separate thread
        print("Creating WebSocket thread...")
        thread = threading.Thread(target=self._run_websocket, daemon=True)
        thread.start()
        print(f"WebSocket thread started: {thread.is_alive()}")
        # Give it a moment to start
        import time

        time.sleep(1)

    async def stop(self):
        """Stop WebSocket connection"""
        self.running = False
        if self.ws:
            self.ws.close()

    def subscribe_symbols(self, symbols: List[str]):
        """Subscribe to symbols"""
        self.subscribed_symbols.update(symbols)
        if self.ws and self.ws.sock and self.ws.sock.connected:
            self._subscribe(symbols)

    def _subscribe(self, symbols: List[str]):
        """Subscribe to Binance ticker stream"""
        if not symbols:
            return

        # For combined streams, we reconnect with new streams
        # This is handled in _run_websocket
        pass

    def _run_websocket(self):
        """Run WebSocket in a separate thread"""
        print("_run_websocket thread started")

        def on_message(ws, message):
            try:
                data = json.loads(message)

                # Debug: Print first few messages to see format
                if not hasattr(on_message, "_msg_count"):
                    on_message._msg_count = 0
                on_message._msg_count += 1
                if on_message._msg_count <= 3:
                    print(
                        f"Received Binance message #{on_message._msg_count}: {str(data)[:200]}"
                    )

                # Handle ticker data - Binance stream format
                if "stream" in data and "data" in data:
                    # Combined stream format
                    stream_data = data["data"]
                    if "c" in stream_data and "s" in stream_data:
                        symbol = stream_data["s"]
                        price = float(stream_data["c"])  # Last price
                        quantity = float(stream_data.get("q", 0))  # Last quantity
                        timestamp = datetime.fromtimestamp(
                            stream_data.get("E", 0) / 1000
                        )

                        tick_data = {
                            "timestamp": timestamp,
                            "symbol": symbol,
                            "price": price,
                            "quantity": quantity,
                        }

                        # Debug: Print first few messages
                        if symbol not in self.latest_data or len(self.latest_data) < 3:
                            print(
                                f"Received data for {symbol}: price={price}, qty={quantity}"
                            )

                        # Store data - call sync method directly from thread
                        # This avoids event loop issues when called from WebSocket thread
                        try:
                            # Debug: Print before storing
                            if not hasattr(on_message, "_stored_count"):
                                on_message._stored_count = {}
                            if symbol not in on_message._stored_count:
                                on_message._stored_count[symbol] = 0

                            self.data_service._store_tick_sync(tick_data)
                            on_message._stored_count[symbol] += 1

                            # Print first few successful stores
                            if on_message._stored_count[symbol] <= 3:
                                print(
                                    f"✓ Successfully stored tick #{on_message._stored_count[symbol]} for {symbol}"
                                )
                        except Exception as e:
                            print(f"✗ Error storing tick for {symbol} in thread: {e}")
                            import traceback

                            traceback.print_exc()

                        # Update latest data
                        with self.lock:
                            self.latest_data[symbol] = {
                                "timestamp": timestamp.isoformat(),
                                "symbol": symbol,
                                "price": price,
                                "quantity": quantity,
                            }

                        # Check alerts
                        try:
                            alert_loop = self._get_event_loop()
                            asyncio.run_coroutine_threadsafe(
                                self.alert_service.check_alerts(symbol, price),
                                alert_loop,
                            )
                        except Exception as e:
                            print(f"Error checking alerts: {e}")
                elif "c" in data and "s" in data:
                    # Direct ticker format
                    symbol = data["s"]
                    price = float(data["c"])
                    quantity = float(data.get("q", 0))
                    timestamp = datetime.fromtimestamp(data.get("E", 0) / 1000)

                    tick_data = {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "price": price,
                        "quantity": quantity,
                    }

                    # Store data - call sync method directly from thread
                    try:
                        self.data_service._store_tick_sync(tick_data)
                        print(f"✓ Stored tick for {symbol} (direct format)")
                    except Exception as e:
                        print(f"✗ Error storing tick for {symbol} in thread: {e}")
                        import traceback

                        traceback.print_exc()

                    with self.lock:
                        self.latest_data[symbol] = {
                            "timestamp": timestamp.isoformat(),
                            "symbol": symbol,
                            "price": price,
                            "quantity": quantity,
                        }

                    asyncio.run_coroutine_threadsafe(
                        self.alert_service.check_alerts(symbol, price), loop
                    )

            except Exception as e:
                print(f"Error processing WebSocket message: {e}")

        def on_error(ws, error):
            print(f"WebSocket error: {error}")

        def on_close(ws, close_status_code, close_msg):
            print(
                f"Binance WebSocket connection closed (code: {close_status_code}, reason: {close_msg})"
            )
            if self.running:
                # Reconnect with exponential backoff
                import time
                import random

                # Exponential backoff: start with 2 seconds, max 30 seconds
                reconnect_delay = min(2 * (2 ** min(self._reconnect_attempts, 4)), 30)
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0, 1)
                delay = reconnect_delay + jitter

                self._reconnect_attempts += 1
                print(
                    f"Reconnecting to Binance WebSocket in {delay:.1f} seconds (attempt {self._reconnect_attempts})..."
                )
                time.sleep(delay)
                if self.running:  # Check again before reconnecting
                    self._reconnect_attempts = 0  # Reset on successful reconnect
                    self._run_websocket()

        def on_open(ws):
            print("Binance WebSocket connection opened successfully")
            print(f"Subscribed symbols: {list(self.subscribed_symbols)}")
            # Reset reconnect attempts on successful connection
            self._reconnect_attempts = 0
            if self.subscribed_symbols:
                self._subscribe(list(self.subscribed_symbols))

        # Connect to Binance WebSocket
        # Use combined stream for multiple symbols
        if self.subscribed_symbols:
            streams = [f"{s.lower()}@ticker" for s in self.subscribed_symbols]
            # Binance combined stream format: stream1/stream2/stream3
            stream_names = "/".join(streams)
            ws_url = f"wss://stream.binance.com:9443/stream?streams={stream_names}"
            print(f"Connecting to Binance WebSocket: {ws_url}")
            print(f"Streams: {streams}")
        else:
            ws_url = "wss://stream.binance.com:9443/ws"
            print(f"Connecting to Binance WebSocket: {ws_url} (no symbols subscribed)")

        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
        )

        print("Starting Binance WebSocket...")
        try:
            self.ws.run_forever()
        except Exception as e:
            print(f"Fatal error in WebSocket run_forever: {e}")
            import traceback

            traceback.print_exc()
            if self.running:
                import time

                time.sleep(5)
                self._run_websocket()

    def _get_event_loop(self):
        """Get or create event loop for current thread"""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    async def get_latest_data(self) -> Optional[Dict]:
        """Get latest data for WebSocket streaming"""
        try:
            with self.lock:
                if self.latest_data:
                    return {
                        "type": "tick_update",
                        "data": list(self.latest_data.values()),
                    }
            return None
        except Exception as e:
            print(f"Error in get_latest_data: {e}")
            return None
