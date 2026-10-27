from app.services.architectures.base import BaseModelAdapter
from app.services.architectures.sd15 import SD15Adapter
from app.services.architectures.sdxl import SDXLAdapter
from app.services.architectures.anima import AnimaDiTAdapter
from app.services.architectures.auto_diffusers import AutoDiffusersAdapter
from app.services.architectures.registry import ArchitectureRegistry

__all__ = [
    "BaseModelAdapter",
    "SD15Adapter",
    "SDXLAdapter",
    "AnimaDiTAdapter",
    "AutoDiffusersAdapter",
    "ArchitectureRegistry"
]
