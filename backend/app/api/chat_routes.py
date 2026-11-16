import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services.text_model_manager import TextModelManager, DEFAULT_CORE_PROFILES
from app.services.web_search_service import WebSearchService
from app.services.multimedia_parser import MultimediaParser
from app.services.chat_engine import ChatEngine

router = APIRouter(prefix="/chat", tags=["Chat LLM & Multimedia"])


class ModelSettingsPayload(BaseModel):
    custom_name: Optional[str] = None
    core: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    context_window: Optional[int] = Field(default=None, ge=512, le=131072)
    max_tokens: Optional[int] = Field(default=None, ge=64, le=32768)
    repeat_penalty: Optional[float] = Field(default=None, ge=0.0, le=2.5)
    web_search_enabled: Optional[bool] = None


class ChatStreamRequest(BaseModel):
    model: str = Field(..., description="ID del modelo local o de Ollama a ejecutar")
    messages: List[Dict[str, Any]] = Field(..., description="Historial de mensajes de la conversación")
    web_search: bool = Field(default=False, description="Activa la búsqueda en internet en tiempo real")
    attached_docs: Optional[List[Dict[str, Any]]] = Field(default=None, description="Documentos y hojas de cálculo analizados")
    attached_images: Optional[List[str]] = Field(default=None, description="Imágenes en Base64 para modelos multimodales")
    override_settings: Optional[Dict[str, Any]] = Field(default=None, description="Sobrescribe ajustes temporalmente")


class SearchPreviewRequest(BaseModel):
    query: str
    max_results: int = 4


class ScanLLMDirectoryRequest(BaseModel):
    directory_path: str = Field(..., description="Ruta de carpeta local a escanear (GGUF o almacén de Ollama)")


@router.get("/status", summary="Estado del servicio de modelos de texto")
async def get_text_service_status():
    ollama_online = TextModelManager.is_ollama_available()
    return {
        "ollama_available": ollama_online,
        "ollama_url": TextModelManager.get_ollama_url(),
        "custom_path": TextModelManager.get_custom_llm_path(),
        "cores_available": list(DEFAULT_CORE_PROFILES.keys())
    }


@router.get("/ollama/status", summary="Estado del daemon local de Ollama")
async def get_ollama_status():
    return {
        "online": TextModelManager.is_ollama_available(),
        "url": TextModelManager.get_ollama_url(),
        "executable_path": TextModelManager.find_ollama_executable(),
        "custom_models_path": TextModelManager.get_custom_llm_path()
    }


@router.post("/ollama/start", summary="Iniciar servicio de Ollama en segundo plano")
async def start_ollama_daemon():
    result = TextModelManager.start_ollama_daemon()
    return result


@router.get("/cores", summary="Lista de arquitecturas y cores soportados")
async def list_cores():
    return DEFAULT_CORE_PROFILES


@router.get("/models", summary="Listar todos los modelos de texto disponibles")
async def list_text_models(custom_path: Optional[str] = None):
    if custom_path and os.path.isdir(custom_path):
        TextModelManager.set_custom_llm_path(custom_path)
    models = TextModelManager.get_all_available_models()
    return {
        "count": len(models),
        "ollama_online": TextModelManager.is_ollama_available(),
        "custom_path": TextModelManager.get_custom_llm_path(),
        "models": models
    }


@router.post("/models/scan", summary="Escanear carpeta local personalizada en busca de modelos LLM")
async def scan_llm_models_directory(req: ScanLLMDirectoryRequest):
    if req.directory_path and os.path.isdir(req.directory_path):
        TextModelManager.set_custom_llm_path(req.directory_path)
    models = TextModelManager.list_local_file_models([req.directory_path])
    return {
        "directory_path": req.directory_path,
        "count": len(models),
        "models": models
    }


@router.get("/models/{model_id:path}/settings", summary="Obtener ajustes personalizados del modelo")
async def get_model_settings(model_id: str):
    profile = TextModelManager.get_model_profile(model_id)
    return profile


@router.post("/models/{model_id:path}/settings", summary="Guardar ajustes personalizados del modelo")
async def update_model_settings(model_id: str, payload: ModelSettingsPayload):
    updates = {k: v for k, v in payload.dict().items() if v is not None}
    saved = TextModelManager.save_model_profile(model_id, updates)
    return {
        "success": True,
        "model_id": model_id,
        "settings": saved
    }


@router.post("/upload", summary="Subir y extraer contenido de archivos multimedia")
async def upload_attachment(file: UploadFile = File(...)):
    """
    Recibe documentos (PDF, Word, Excel, CSV, Texto plano o imágenes),
    los analiza y devuelve el texto estructurado o Base64.
    """
    try:
        content_bytes = await file.read()
        parsed = MultimediaParser.parse_uploaded_file(file.filename or "archivo", content_bytes)
        return {
            "success": True,
            "file": parsed
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al procesar archivo adjunto: {str(e)}"
        )


@router.post("/search-preview", summary="Previsualizar resultados de búsqueda web")
async def preview_web_search(req: SearchPreviewRequest):
    results = WebSearchService.execute_search(req.query, max_results=req.max_results)
    return {
        "query": req.query,
        "count": len(results),
        "results": results
    }


@router.post("/stream", summary="Stream de respuesta de chat LLM (Server-Sent Events)")
async def stream_chat(req: ChatStreamRequest):
    """
    Genera la respuesta del LLM con streaming token a token vía text/event-stream.
    """
    if not req.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La conversación no puede estar vacía."
        )

    return StreamingResponse(
        ChatEngine.stream_chat_completion(
            model=req.model,
            messages=req.messages,
            web_search=req.web_search,
            attached_docs=req.attached_docs,
            attached_images=req.attached_images,
            override_settings=req.override_settings
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

