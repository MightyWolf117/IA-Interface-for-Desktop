from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    role: str = Field(..., description="Rol del mensaje: 'user', 'assistant' o 'system'")
    content: str = Field(..., description="Contenido de texto del mensaje")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Historial de mensajes de la conversación")
    model: str = Field(default="llama-3.3-70b", description="Identificador del modelo local a utilizar")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperatura de muestreo para la generación")
    max_tokens: Optional[int] = Field(default=1024, description="Límite máximo de tokens a generar")


class ChatResponse(BaseModel):
    id: str = Field(..., description="Identificador único de la respuesta generada")
    model: str = Field(..., description="Modelo que generó la respuesta")
    response: str = Field(..., description="Texto de respuesta generado")
    tokens_evaluated: int = Field(..., description="Cantidad de tokens procesados en el prompt")
    tokens_generated: int = Field(..., description="Cantidad de tokens generados en la respuesta")
    latency_ms: float = Field(..., description="Tiempo total de inferencia en milisegundos")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Marca temporal UTC")


class ModelInfo(BaseModel):
    id: str = Field(..., description="Identificador del modelo")
    name: str = Field(..., description="Nombre amigable del modelo")
    parameters: str = Field(..., description="Cantidad de parámetros (ej. 70B, 8B)")
    quantization: str = Field(..., description="Cuantización aplicada (ej. Q4_K_M, FP16)")
    status: str = Field(..., description="Estado del modelo: 'ready', 'downloading', 'unavailable'")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Estado general del servicio ('healthy')")
    service: str = Field(..., description="Nombre del servicio backend")
    version: str = Field(..., description="Versión de la API")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Marca temporal UTC")
    vram_status: Optional[str] = Field(default="optimal", description="Estado de memoria VRAM")
