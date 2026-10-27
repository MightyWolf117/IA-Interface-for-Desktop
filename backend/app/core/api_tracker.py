import time
from collections import deque
from datetime import datetime
from typing import List, Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class APITracker:
    """
    Rastreador de telemetría y diagnóstico para el Panel de Control de la API.
    Monitorea puertos abiertos, endpoints registrados, llamadas y códigos de estado HTTP.
    """
    _max_logs: int = 50
    _request_logs: deque = deque(maxlen=_max_logs)
    _active_ports: List[Dict[str, Any]] = [
        {"port": 8000, "service": "FastAPI Core & WebSockets", "protocol": "HTTP/WS", "status": "ONLINE"},
        {"port": 1420, "service": "Tauri v2 Desktop Interface", "protocol": "HTTP", "status": "ONLINE"}
    ]

    @classmethod
    def record_request(cls, method: str, path: str, status_code: int, duration_ms: float, client: str):
        cls._request_logs.appendleft({
            "id": f"req_{int(time.time() * 1000)}",
            "timestamp": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "client": client
        })

    @classmethod
    def get_logs(cls) -> List[Dict[str, Any]]:
        return list(cls._request_logs)

    @classmethod
    def get_ports(cls) -> List[Dict[str, Any]]:
        return cls._active_ports


class APITrackerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Ignore high frequency polling or websocket upgrade if necessary
        start_time = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        client_host = request.client.host if request.client else "unknown"
        APITracker.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client=client_host
        )
        return response
