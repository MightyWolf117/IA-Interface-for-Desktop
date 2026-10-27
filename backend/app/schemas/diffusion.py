from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ScanRequest(BaseModel):
    directory_path: str = Field(..., description="Ruta local en el sistema de archivos a escanear")


class ModelItem(BaseModel):
    id: str
    name: str
    type: str
    path: Optional[str] = None
    format: Optional[str] = None
    size_mb: Optional[float] = None
    description: Optional[str] = None
    recommended_vram_mb: Optional[float] = None
    architecture: Optional[str] = None
    arch_id: Optional[str] = None
    default_width: Optional[int] = None
    default_height: Optional[int] = None
    default_cfg: Optional[float] = None
    default_steps: Optional[int] = None


class ScanResponse(BaseModel):
    root_path: str
    exists: bool
    base_models: List[Dict[str, Any]]
    loras: List[Dict[str, Any]]
    controlnets: List[Dict[str, Any]]
    vaes: List[Dict[str, Any]]
    public_models: List[Dict[str, Any]]
    supported_architectures: Optional[List[Dict[str, Any]]] = None


class LoadModelRequest(BaseModel):
    model_id_or_path: str = Field(..., description="ID de Hugging Face o ruta local al modelo")
    memory_mode: str = Field(
        default="equilibrado",
        description="Modo de memoria: 'ahorro' (<=40% VRAM), 'equilibrado' (<=65% VRAM), 'alto_rendimiento' (100% VRAM)"
    )
    transfer_mode: str = Field(
        default="base64",
        description="Formato de salida: 'base64' (renderizado instantáneo en memoria) o 'disk' (guardado en carpeta outputs/ con URL)"
    )
    lora_path: Optional[str] = Field(default=None, description="Ruta opcional a archivo LoRA")
    lora_weight: float = Field(default=1.0, ge=0.0, le=2.0, description="Peso de escala del LoRA")
    scheduler: Optional[str] = Field(default="EulerA", description="Planificador de ruido: 'EulerA', 'DPM++', 'DDIM', 'UniPC', 'Default'")


class LoadModelResponse(BaseModel):
    success: bool
    model_id: str
    architecture: Optional[Dict[str, Any]] = None
    memory_mode: str
    transfer_mode: str
    device: str
    vram_allocated_mb: float
    vram_reserved_mb: float
    message: str


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Prompt descriptivo para generar la imagen")
    negative_prompt: Optional[str] = Field(
        default="ugly, deformed, disfigured, poor details, bad anatomy, blurry",
        description="Prompt negativo para excluir características"
    )
    width: int = Field(default=512, ge=256, le=1024, description="Ancho de la imagen (múltiplo de 8)")
    height: int = Field(default=512, ge=256, le=1024, description="Alto de la imagen (múltiplo de 8)")
    steps: int = Field(default=20, ge=1, le=100, description="Cantidad de pasos de muestreo de difusión")
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0, description="Escala de alineación CFG")
    seed: Optional[int] = Field(default=None, description="Semilla aleatoria fija (None para aleatoria)")


class GenerateResponse(BaseModel):
    id: str
    image_data: str = Field(..., description="Cadena Base64 (data:image/png;base64,...) o ruta local / URL")
    transfer_mode: str
    latency_ms: float
    seed: int
    steps: int
    width: int
    height: int
    vram_allocated_mb: float
    architecture: Optional[str] = None


class ModelStatusResponse(BaseModel):
    loaded: bool
    active_model: Optional[str] = None
    architecture: Optional[Dict[str, Any]] = None
    memory_mode: Optional[str] = None
    transfer_mode: Optional[str] = None
    device: str
    auxiliaries: Dict[str, Any] = {}
    vram_allocated_mb: float
    vram_reserved_mb: float


class APIEndpointInfo(BaseModel):
    method: str
    path: str
    summary: str


class APIStatusResponse(BaseModel):
    service: str
    status: str
    ports: List[Dict[str, Any]]
    endpoints: List[APIEndpointInfo]
    recent_requests: List[Dict[str, Any]]
