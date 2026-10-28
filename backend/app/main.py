import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import router as chat_router
from app.api.diffusion_routes import router as diffusion_router
from app.core.api_tracker import APITrackerMiddleware

app = FastAPI(
    title="CYBER-IA Desktop Core API",
    description="Backend local de alto rendimiento en FastAPI para la interfaz de escritorio de LLMs y Difusión Multimedia.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach API Tracker Diagnostic Middleware
app.add_middleware(APITrackerMiddleware)

# CORS configuration to allow local desktop requests from Tauri
origins = [
    "http://localhost:1420",
    "http://127.0.0.1:1420",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "tauri://localhost",
    "https://tauri.localhost",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.core.paths import get_outputs_dir

# Ensure outputs directory exists and mount as static files for disk-transfer mode
outputs_dir = get_outputs_dir()
app.mount("/outputs", StaticFiles(directory=outputs_dir), name="outputs")

# Include Routers
app.include_router(chat_router, prefix="/api/v1")
app.include_router(diffusion_router, prefix="/api/v1")


@app.get("/", summary="Root endpoint")
async def root():
    return {
        "service": "CYBER-IA Desktop Core API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "api_v1": "/api/v1/health",
        "api_control": "/api/v1/system/api-status"
    }
