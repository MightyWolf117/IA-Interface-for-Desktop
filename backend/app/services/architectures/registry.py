from typing import List, Type, Dict, Any, Optional

from app.services.architectures.base import BaseModelAdapter
from app.services.architectures.anima import AnimaDiTAdapter
from app.services.architectures.sdxl import SDXLAdapter
from app.services.architectures.sd15 import SD15Adapter
from app.services.architectures.auto_diffusers import AutoDiffusersAdapter


class ArchitectureRegistry:
    """
    Registro y despachador central de arquitecturas de modelos de difusión.
    Permite identificar dinámicamente la arquitectura de cualquier modelo y delegar
    las operaciones de carga, optimización de hardware y generación al adaptador específico.
    """

    # Orden de precedencia para evaluación: de más específico a genérico
    _ADAPTERS: List[Type[BaseModelAdapter]] = [
        AnimaDiTAdapter,
        SDXLAdapter,
        SD15Adapter,
        AutoDiffusersAdapter
    ]

    @classmethod
    def get_adapter(cls, model_path: str) -> Type[BaseModelAdapter]:
        """
        Determina y devuelve el adaptador óptimo para el modelo indicado.
        """
        for adapter in cls._ADAPTERS:
            try:
                if adapter.can_handle(model_path):
                    return adapter
            except Exception:
                continue

        # Fallback predeterminado a SD 1.5 si no hay coincidencia
        return SD15Adapter

    @classmethod
    def detect_architecture(cls, model_path: str) -> Dict[str, Any]:
        """
        Devuelve metadatos descriptivos de la arquitectura del modelo.
        """
        adapter = cls.get_adapter(model_path)
        return {
            "arch_id": adapter.arch_id,
            "display_name": adapter.display_name,
            "description": adapter.description,
            "default_width": adapter.default_width,
            "default_height": adapter.default_height,
            "default_cfg": adapter.default_cfg,
            "default_steps": adapter.default_steps
        }

    @classmethod
    def list_supported_architectures(cls) -> List[Dict[str, Any]]:
        """
        Lista todas las arquitecturas soportadas por el sistema.
        """
        return [
            {
                "arch_id": a.arch_id,
                "display_name": a.display_name,
                "description": a.description,
                "default_width": a.default_width,
                "default_height": a.default_height,
                "default_cfg": a.default_cfg,
                "default_steps": a.default_steps
            }
            for a in cls._ADAPTERS
        ]
