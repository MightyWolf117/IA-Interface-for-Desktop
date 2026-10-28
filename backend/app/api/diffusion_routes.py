import asyncio
import json
import os
from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.hardware import HardwareDetector
from app.core.api_tracker import APITracker
from app.services.model_scanner import ModelScanner
from app.services.diffusion_engine import DiffusionEngine
from app.schemas.diffusion import (
    ScanRequest,
    ScanResponse,
    LoadModelRequest,
    LoadModelResponse,
    CheckPublicModelRequest,
    CheckPublicModelResponse,
    DeletePublicModelRequest,
    DeletePublicModelResponse,
    GenerateRequest,
    GenerateResponse,
    ModelStatusResponse,
    APIStatusResponse,
    APIEndpointInfo
)

router = APIRouter(tags=["Diffusion & Telemetry"])

# Active WebSocket connections for real-time telemetry (<100ms)
active_telemetry_sockets: List[WebSocket] = []


@router.get("/hardware/info", summary="Obtener información de hardware y umbrales dinámicos")
async def get_hardware_info():
    """
    Retorna la GPU detectada, VRAM total y los umbrales dinámicos:
      - Modo Ahorro: 40% VRAM
      - Modo Equilibrado: 65% VRAM
      - Modo Alto Rendimiento: 100% VRAM
    """
    return HardwareDetector.get_full_telemetry()


@router.post("/system/browse-folder", summary="Abrir explorador nativo de Windows para seleccionar carpeta")
async def browse_native_folder():
    """
    Despliega la ventana nativa del Explorador de Windows para que el usuario elija una carpeta en disco.
    """
    def _open_dialog():
        selected = None
        # Método 1: Tkinter nativo con forzado de foco y primer plano
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.lift()
            root.attributes("-topmost", True)
            root.focus_force()
            selected = filedialog.askdirectory(title="Seleccionar Carpeta de Modelos de IA")
            root.destroy()
        except Exception as tk_err:
            print(f"[browse_native_folder] Fallback de Tkinter: {tk_err}")
            selected = None

        # Método 2: Fallback con Windows Forms de PowerShell si Tkinter no entregó ruta o falló
        if not selected:
            try:
                import subprocess
                ps_script = (
                    'Add-Type -AssemblyName System.Windows.Forms; '
                    '$dlg = New-Object System.Windows.Forms.FolderBrowserDialog; '
                    '$dlg.Description = "CYBER-IA - Seleccionar Carpeta de Modelos"; '
                    '$dlg.ShowNewFolderButton = $true; '
                    'if ($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { '
                    '  Write-Output $dlg.SelectedPath '
                    '}'
                )
                res = subprocess.check_output(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                    text=True,
                    timeout=60
                ).strip()
                if res and os.path.isdir(res):
                    selected = res
            except Exception as ps_err:
                print(f"[browse_native_folder] Fallback PowerShell: {ps_err}")

        if selected:
            selected = selected.replace("\\", "/")

        return selected

    path = await asyncio.to_thread(_open_dialog)
    return {"selected_path": path, "canceled": path is None}



@router.post("/models/scan", response_model=ScanResponse, summary="Escanear carpeta en busca de modelos y auxiliares")
async def scan_models_directory(request: ScanRequest):
    """
    Inspecciona una ruta local en disco para detectar modelos de difusión (.safetensors, carpetas)
    y componentes auxiliares (LoRAs, ControlNet, VAEs).
    """
    scan_result = ModelScanner.scan_directory(request.directory_path)
    return scan_result


@router.post("/models/check-public", response_model=CheckPublicModelResponse, summary="Verificar presencia local de modelo público")
async def check_public_model(request: CheckPublicModelRequest):
    """
    Comprueba si un modelo público de Hugging Face ya se encuentra descargado en el directorio indicado.
    """
    return await asyncio.to_thread(
        DiffusionEngine.check_public_model,
        model_id=request.model_id,
        download_dir=request.download_dir
    )


@router.post("/models/delete-public", response_model=DeletePublicModelResponse, summary="Eliminar carpeta de modelo público de disco")
async def delete_public_model(request: DeletePublicModelRequest):
    """
    Elimina la versión descargada de un modelo público para liberar espacio en disco.
    """
    return await asyncio.to_thread(
        DiffusionEngine.delete_public_model,
        model_id=request.model_id,
        download_dir=request.download_dir
    )


@router.post("/diffusion/load", response_model=LoadModelResponse, summary="Cargar modelo con política de memoria")
async def load_diffusion_model(request: LoadModelRequest):
    """
    Carga un modelo local o de Hugging Face aplicando la política de memoria seleccionada
    y el formato de transferencia de salida (Base64 vs Disco).
    """
    try:
        result = await asyncio.to_thread(
            DiffusionEngine.load_model,
            model_id_or_path=request.model_id_or_path,
            memory_mode=request.memory_mode,
            transfer_mode=request.transfer_mode,
            lora_path=request.lora_path,
            lora_weight=request.lora_weight,
            scheduler=request.scheduler,
            download_dir=request.download_dir
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al inicializar el modelo de difusión: {str(e)}"
        )


@router.post("/diffusion/unload", summary="Descargar modelo activo y liberar VRAM")
async def unload_diffusion_model():
    """
    Descarga el modelo actual y vacía los cachés de PyTorch y recolección de basura.
    """
    return await asyncio.to_thread(DiffusionEngine.unload_model)


@router.get("/diffusion/status", response_model=ModelStatusResponse, summary="Estado del motor de difusión")
async def get_diffusion_status():
    """
    Retorna si hay un modelo cargado, su perfil de memoria, formato y consumo actual de VRAM.
    """
    return DiffusionEngine.get_status()


@router.post("/diffusion/generate", response_model=GenerateResponse, summary="Generar imagen por difusión")
async def generate_image(request: GenerateRequest):
    """
    Genera una imagen a partir del prompt y parámetros provistos.
    Transmite el progreso en tiempo real a los WebSockets conectados.
    """
    loop = asyncio.get_running_loop()

    # Callback to broadcast step progress over WebSockets safely from thread
    def progress_callback(step: int, total_steps: int, pct: float):
        payload = json.dumps({
            "type": "generation_progress",
            "step": step,
            "total_steps": total_steps,
            "percent": pct
        })
        for ws in list(active_telemetry_sockets):
            try:
                loop.call_soon_threadsafe(asyncio.create_task, ws.send_text(payload))
            except Exception:
                pass

    try:
        result = await asyncio.to_thread(
            DiffusionEngine.generate,
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
            step_callback=progress_callback
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante la generación de imagen: {str(e)}"
        )


@router.get("/system/api-status", response_model=APIStatusResponse, summary="Panel de Control y Diagnóstico del API")
async def get_api_control_status():
    """
    Panel de diagnóstico para la interfaz:
    Lista los puertos abiertos, endpoints registrados, y el historial reciente de solicitudes con sus códigos HTTP.
    """
    # Registered endpoints in router
    endpoints = [
        APIEndpointInfo(method="GET", path="/api/v1/health", summary="Comprobación de salud básica"),
        APIEndpointInfo(method="GET", path="/api/v1/hardware/info", summary="Telemetría y umbrales de VRAM"),
        APIEndpointInfo(method="POST", path="/api/v1/models/scan", summary="Escaneo local de modelos y auxiliares"),
        APIEndpointInfo(method="POST", path="/api/v1/diffusion/load", summary="Carga modular de modelo con offload"),
        APIEndpointInfo(method="POST", path="/api/v1/diffusion/unload", summary="Descarga y vaciado de VRAM"),
        APIEndpointInfo(method="GET", path="/api/v1/diffusion/status", summary="Estado del motor de difusión"),
        APIEndpointInfo(method="POST", path="/api/v1/diffusion/generate", summary="Generación multimedia de difusión"),
        APIEndpointInfo(method="GET", path="/api/v1/system/api-status", summary="Panel de control y puertos del API"),
        APIEndpointInfo(method="WS", path="/api/v1/ws/telemetry", summary="Stream de telemetría de hardware (<100ms)")
    ]

    return APIStatusResponse(
        service="IA-Interface-Desktop Core API",
        status="ONLINE",
        ports=APITracker.get_ports(),
        endpoints=endpoints,
        recent_requests=APITracker.get_logs()
    )


@router.websocket("/ws/telemetry")
async def websocket_telemetry_stream(websocket: WebSocket):
    """
    Canal WebSocket de telemetría de ultra baja latencia (< 80ms).
    Transmite métricas de VRAM asignada, RAM del sistema y progreso de inferencia a 15-20 FPS.
    """
    await websocket.accept()
    active_telemetry_sockets.append(websocket)

    try:
        while True:
            # Gather telemetry snapshot (< 80ms delay)
            telemetry = HardwareDetector.get_full_telemetry()
            model_status = DiffusionEngine.get_status()

            payload = {
                "type": "hardware_telemetry",
                "timestamp": asyncio.get_event_loop().time(),
                "telemetry": telemetry,
                "model_status": model_status
            }
            await websocket.send_text(json.dumps(payload))
            # Sleep 75ms for high-frequency low-overhead updates (sub-100ms)
            await asyncio.sleep(0.075)
    except WebSocketDisconnect:
        active_telemetry_sockets.remove(websocket)
    except Exception:
        if websocket in active_telemetry_sockets:
            active_telemetry_sockets.remove(websocket)
