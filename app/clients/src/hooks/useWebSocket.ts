/**
 * WebSocket hook for real-time data updates
 */
import { useEffect, useRef, useState } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8010/ws';

export interface TickUpdate {
  timestamp: string;
  symbol: string;
  price: number;
  quantity: number;
}

export interface WebSocketMessage {
  type: string;
  data: unknown;
}

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [latestData, setLatestData] = useState<TickUpdate[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | undefined>(undefined);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 10; // Maximum reconnection attempts
  const baseReconnectDelay = 1000; // Start with 1 second
  const maxReconnectDelay = 30000; // Max 30 seconds

  useEffect(() => {
    let isMounted = true;
    let shouldReconnect = true;

    const getReconnectDelay = (attempts: number): number => {
      // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (max)
      const delay = Math.min(
        baseReconnectDelay * Math.pow(2, attempts),
        maxReconnectDelay
      );
      return delay;
    };

    const connect = () => {
      if (!isMounted || !shouldReconnect) return;

      // Don't reconnect if we've exceeded max attempts
      if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
        console.error(
          `Max reconnection attempts (${maxReconnectAttempts}) reached. Stopping reconnection.`
        );
        return;
      }

      try {
        // Close existing connection if any
        if (wsRef.current) {
          if (wsRef.current.readyState !== WebSocket.CLOSED) {
            wsRef.current.close();
          }
          wsRef.current = null;
        }

        console.log(
          `Attempting to connect (attempt ${
            reconnectAttemptsRef.current + 1
          }/${maxReconnectAttempts})...`
        );
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) {
            ws.close();
            return;
          }
          console.log('WebSocket connected successfully');
          setIsConnected(true);
          reconnectAttemptsRef.current = 0; // Reset on successful connection
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;

          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            if (message.type === 'tick_update' && message.data) {
              // Type guard to ensure data is an array of TickUpdate
              if (Array.isArray(message.data)) {
                setLatestData(message.data as TickUpdate[]);
              }
            } else if (message.type === 'ping') {
              // Keep connection alive, no action needed
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          if (!isMounted) return;
          console.error('WebSocket error:', error);
          setIsConnected(false);
        };

        ws.onclose = (event) => {
          if (!isMounted) return;

          console.log(
            `WebSocket disconnected (code: ${event.code}, reason: ${
              event.reason || 'none'
            })`
          );
          setIsConnected(false);

          // Only reconnect if:
          // 1. It wasn't a manual close (code 1000)
          // 2. Component is still mounted
          // 3. We haven't exceeded max attempts
          if (
            event.code !== 1000 &&
            isMounted &&
            shouldReconnect &&
            reconnectAttemptsRef.current < maxReconnectAttempts
          ) {
            reconnectAttemptsRef.current += 1;
            const delay = getReconnectDelay(reconnectAttemptsRef.current - 1);
            console.log(
              `Reconnecting in ${delay / 1000} seconds... (attempt ${
                reconnectAttemptsRef.current
              }/${maxReconnectAttempts})`
            );

            reconnectTimeoutRef.current = window.setTimeout(() => {
              if (
                isMounted &&
                shouldReconnect &&
                (!wsRef.current ||
                  wsRef.current.readyState === WebSocket.CLOSED)
              ) {
                connect();
              }
            }, delay);
          } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
            console.error(
              'Max reconnection attempts reached. Please refresh the page.'
            );
          }
        };
      } catch (error) {
        console.error('Error connecting WebSocket:', error);
        setIsConnected(false);
        if (isMounted && shouldReconnect) {
          reconnectAttemptsRef.current += 1;
          if (reconnectAttemptsRef.current < maxReconnectAttempts) {
            const delay = getReconnectDelay(reconnectAttemptsRef.current - 1);
            reconnectTimeoutRef.current = window.setTimeout(() => {
              if (isMounted && shouldReconnect) connect();
            }, delay);
          }
        }
      }
    };

    connect();

    return () => {
      isMounted = false;
      shouldReconnect = false; // Prevent reconnection on cleanup
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.onclose = null; // Prevent reconnection on cleanup
        wsRef.current.close(1000, 'Component unmounting');
        wsRef.current = null;
      }
    };
  }, []);

  return { isConnected, latestData };
};
