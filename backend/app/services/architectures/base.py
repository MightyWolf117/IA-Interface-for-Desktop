from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
from PIL import Image


class BaseModelAdapter(ABC):
    """
    Clase base abstracta para los adaptadores de arquitectura de modelos de difusión.
    Permite el soporte modular para diferentes familias de modelos (SD 1.5, SDXL, Anima DiT, etc.)
    garantizando un ciclo de vida uniforme de carga, configuración de memoria y generación.
    """

    arch_id: str = "base"
    display_name: str = "Base Architecture"
    description: str = "Base adapter interface"
    default_width: int = 512
    default_height: int = 512
    default_cfg: float = 7.5
    default_steps: int = 20

    @classmethod
    @abstractmethod
    def can_handle(cls, model_path: str) -> bool:
        """
        Determina si este adaptador puede manejar la ruta de modelo o identificador HF proporcionado.
        """
        pass

    @classmethod
    @abstractmethod
    def load(
        cls,
        model_path: str,
        memory_mode: str = "equilibrado",
        scheduler: Optional[str] = None,
        lora_path: Optional[str] = None,
        lora_weight: float = 1.0
    ) -> Any:
        """
        Carga e inicializa el pipeline correspondiente con las políticas de memoria y componentes auxiliares.
        """
        pass

    @classmethod
    @abstractmethod
    def generate(
        cls,
        pipeline: Any,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        step_callback: Optional[Callable[[int, int, float], None]] = None
    ) -> Image.Image:
        """
        Ejecuta la inferencia sobre el pipeline y devuelve la imagen PIL generada.
        """
        pass
