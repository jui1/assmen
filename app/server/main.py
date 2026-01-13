"""
Main FastAPI application for real-time trading analytics
"""

import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
from contextlib import asynccontextmanager

from services.websocket_service import WebSocketService
from services.data_service import DataService
from services.analytics_service import AnalyticsService
from services.alert_service import AlertService
from api.routes import router, set_services
from database.database import init_db

# Global services
websocket_service = None
data_service = None
analytics_service = None
alert_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global websocket_service, data_service, analytics_service, alert_service

    # Initialize database
    init_db()

    # Initialize services
    data_service = DataService()
    analytics_service = AnalyticsService(data_service)
    alert_service = AlertService(analytics_service)
    websocket_service = WebSocketService(data_service, alert_service)

    # Inject services into routes
    set_services(data_service, analytics_service, alert_service)

    # Store websocket service globally for API access
    app.state.websocket_service = websocket_service

    # Start WebSocket ingestion with default symbols
    print("Subscribing to symbols: BTCUSDT, ETHUSDT, BNBUSDT")
    websocket_service.subscribe_symbols(["BTCUSDT", "ETHUSDT", "BNBUSDT"])
    print("Starting WebSocket service...")
    await websocket_service.start()
    print("WebSocket service started. Waiting for data...")

    yield

    # Cleanup on shutdown
    await websocket_service.stop()


app = FastAPI(
    title="Trading Analytics API",
    description="Real-time trading data analytics and visualization",
    version="1.0.0",
    lifespan=lifespan,
)

# Allowed origins for CORS
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:5174",
]

# CORS middleware - must be added before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


def get_cors_headers(request: Request):
    """Get CORS headers based on request origin"""
    origin = request.headers.get("origin")
    if origin in ALLOWED_ORIGINS:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    return {}


# Exception handlers to ensure CORS headers are always added
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with CORS headers"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=get_cors_headers(request),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with CORS headers"""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
        headers=get_cors_headers(request),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with CORS headers"""
    import traceback

    print(f"Unhandled exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
        headers=get_cors_headers(request),
    )


# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Trading Analytics API", "status": "running"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming to frontend"""
    await websocket.accept()
    print(f"WebSocket client connected: {websocket.client}")

    import asyncio

    global websocket_service

    try:
        while True:
            try:
                # Check if connection is still open
                # FastAPI WebSocket doesn't expose a direct state check,
                # so we catch the exception when trying to send

                # Send real-time updates
                if websocket_service:
                    data = await websocket_service.get_latest_data()
                    if data:
                        await websocket.send_json(data)
                    else:
                        # Send ping to keep connection alive
                        await websocket.send_json({"type": "ping", "data": []})
                else:
                    # Send empty update to keep connection alive
                    await websocket.send_json({"type": "ping", "data": []})

                await asyncio.sleep(0.5)  # Update every 500ms

            except WebSocketDisconnect:
                print("WebSocket client disconnected normally")
                break
            except RuntimeError as e:
                # Connection closed error
                if "close" in str(e).lower() or "closed" in str(e).lower():
                    print("WebSocket connection closed by client")
                    break
                else:
                    print(f"WebSocket runtime error: {e}")
                    break
            except Exception as e:
                error_msg = str(e).lower()
                # Check if it's a connection closed error
                if (
                    "close" in error_msg
                    or "closed" in error_msg
                    or "cannot call" in error_msg
                ):
                    print("WebSocket connection closed, stopping loop")
                    break
                else:
                    print(f"Error in WebSocket loop: {e}")
                    # Wait a bit before retrying
                    await asyncio.sleep(1)

    except WebSocketDisconnect:
        print("WebSocket client disconnected normally")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        print("WebSocket endpoint cleaned up")


if __name__ == "__main__":
    port = int(
        os.getenv("PORT", 8010)
    )  # Use 8002 as default since 8000 and 8001 are occupied
    print(f"Starting server on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
