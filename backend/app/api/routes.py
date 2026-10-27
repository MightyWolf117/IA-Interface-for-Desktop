import time
import uuid
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ModelInfo,
    HealthResponse,
)

router = APIRouter(tags=["AI Core"])

# Mock catalogue of local models (ready to connect with llama.cpp, Ollama or custom local engine)
AVAILABLE_MODELS: List[ModelInfo] = [
    ModelInfo(
        id="llama-3.3-70b",
        name="Llama 3.3 70B Instruct",
        parameters="70B",
        quantization="Q4_K_M",
        status="ready",
    ),
    ModelInfo(
        id="deepseek-r1",
        name="DeepSeek R1 Distill",
        parameters="32B",
        quantization="Q4_K_S",
        status="ready",
    ),
    ModelInfo(
        id="mistral-nemo",
        name="Mistral Nemo 12B",
        parameters="12B",
        quantization="Q8_0",
        status="ready",
    ),
]


@router.get("/health", response_model=HealthResponse, summary="Verificar estado del servicio")
async def health_check():
    """
    Endpoint de comprobación de salud para el backend y verificación de estado de VRAM.
    """
    return HealthResponse(
        status="healthy",
        service="CYBER-IA-Backend-Core",
        version="1.0.0",
        vram_status="optimal",
    )


@router.get("/models", response_model=List[ModelInfo], summary="Listar modelos locales disponibles")
async def list_models():
    """
    Retorna la lista de modelos de lenguaje disponibles en el entorno local.
    """
    return AVAILABLE_MODELS


@router.post("/chat", response_model=ChatResponse, summary="Generar respuesta de chat con IA")
async def generate_chat_completion(request: ChatRequest):
    """
    Recibe el historial de mensajes de la interfaz y genera una respuesta de IA.
    Listo para conectarse al runtime local de inferencia.
    """
    start_time = time.perf_counter()

    if not request.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La lista de mensajes no puede estar vacía.",
        )

    last_user_msg = None
    for msg in reversed(request.messages):
        if msg.role == "user":
            last_user_msg = msg.content
            break

    if not last_user_msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere al menos un mensaje con rol 'user'.",
        )

    # Simulated local inference generation (extensible with local llama-cpp-python or engine)
    elapsed_ms = round((time.perf_counter() - start_time) * 1000 + 45.0, 2)
    response_text = (
        f"[NEURAL_CORE // {request.model.upper()}]: "
        f"Recibida directiva local: \"{last_user_msg}\". "
        f"Procesamiento de tensores ejecutado correctamente en backend FastAPI."
    )

    return ChatResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
        model=request.model,
        response=response_text,
        tokens_evaluated=len(last_user_msg.split()) * 2,
        tokens_generated=len(response_text.split()) * 2,
        latency_ms=elapsed_ms,
    )
