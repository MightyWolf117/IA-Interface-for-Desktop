import os
import psutil
import warnings
from typing import Dict, Any, Optional

warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False


class HardwareDetector:
    """
    Detector dinámico y optimizado de hardware para GPUs y memoria del sistema.
    Cachea propiedades estáticas (nombre del dispositivo, VRAM total, umbrales de memoria)
    para evitar llamadas redundantes de driver en bucles de telemetría de alta frecuencia.
    """

    _gpu_cached: bool = False
    _gpu_static: Dict[str, Any] = {}
    _nvml_initialized: bool = False
    _nvml_handle: Any = None
    _nvml_failed: bool = False
    _ram_total_mb: float = 0.0

    @classmethod
    def _init_nvml(cls):
        if not PYNVML_AVAILABLE or cls._nvml_failed or cls._nvml_initialized:
            return
        try:
            pynvml.nvmlInit()
            cls._nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            cls._nvml_initialized = True
        except Exception as e:
            cls._nvml_failed = True
            print(f"[HardwareDetector] Advertencia al inicializar NVML: {e}")

    @classmethod
    def _init_gpu_cache(cls):
        if cls._gpu_cached:
            return

        # 1. Primary path: PyTorch CUDA
        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                device_id = 0
                device_name = torch.cuda.get_device_name(device_id)
                props = torch.cuda.get_device_properties(device_id)
                total_vram_mb = round(props.total_memory / (1024 * 1024), 2)
                cls._gpu_static = {
                    "available": True,
                    "name": device_name,
                    "device_id": device_id,
                    "vram_total_mb": total_vram_mb,
                    "thresholds_mb": {
                        "ahorro_40": round(total_vram_mb * 0.40, 2),
                        "equilibrado_65": round(total_vram_mb * 0.65, 2),
                        "alto_rendimiento_100": total_vram_mb
                    }
                }
                cls._gpu_cached = True
                return
            except Exception as e:
                print(f"[HardwareDetector] Advertencia al cachear torch.cuda: {e}")

        # 2. Secondary path: Direct NVIDIA NVML
        cls._init_nvml()
        if cls._nvml_initialized and cls._nvml_handle is not None:
            try:
                name = pynvml.nvmlDeviceGetName(cls._nvml_handle)
                mem = pynvml.nvmlDeviceGetMemoryInfo(cls._nvml_handle)
                total_mb = round(mem.total / (1024 * 1024), 2)
                device_name = name if isinstance(name, str) else name.decode('utf-8', errors='ignore')
                cls._gpu_static = {
                    "available": True,
                    "name": device_name,
                    "device_id": 0,
                    "vram_total_mb": total_mb,
                    "thresholds_mb": {
                        "ahorro_40": round(total_mb * 0.40, 2),
                        "equilibrado_65": round(total_mb * 0.65, 2),
                        "alto_rendimiento_100": total_mb
                    }
                }
                cls._gpu_cached = True
                return
            except Exception as e:
                print(f"[HardwareDetector] Advertencia al cachear NVML: {e}")

        # 3. CPU Fallback
        cls._gpu_static = {
            "available": False,
            "name": "CPU / No CUDA GPU Detected",
            "device_id": -1,
            "vram_total_mb": 0,
            "thresholds_mb": {
                "ahorro_40": 0,
                "equilibrado_65": 0,
                "alto_rendimiento_100": 0
            }
        }
        cls._gpu_cached = True

    @classmethod
    def get_gpu_info(cls) -> Dict[str, Any]:
        cls._init_gpu_cache()
        static = cls._gpu_static

        if not static.get("available", False):
            return {
                **static,
                "vram_allocated_mb": 0,
                "vram_reserved_mb": 0,
                "vram_free_mb": 0
            }

        device_id = static.get("device_id", 0)
        total_vram_mb = static.get("vram_total_mb", 0)

        # 1. Fast dynamic query for PyTorch CUDA allocations
        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                allocated_mb = round(torch.cuda.memory_allocated(device_id) / (1024 * 1024), 2)
                reserved_mb = round(torch.cuda.memory_reserved(device_id) / (1024 * 1024), 2)
                free_mb = max(round(total_vram_mb - reserved_mb, 2), 0)
                return {
                    **static,
                    "vram_allocated_mb": allocated_mb,
                    "vram_reserved_mb": reserved_mb,
                    "vram_free_mb": free_mb
                }
            except Exception:
                pass

        # 2. Dynamic query via NVML
        cls._init_nvml()
        if cls._nvml_initialized and cls._nvml_handle is not None:
            try:
                mem = pynvml.nvmlDeviceGetMemoryInfo(cls._nvml_handle)
                used_mb = round(mem.used / (1024 * 1024), 2)
                free_mb = round(mem.free / (1024 * 1024), 2)
                return {
                    **static,
                    "vram_allocated_mb": used_mb,
                    "vram_reserved_mb": used_mb,
                    "vram_free_mb": free_mb
                }
            except Exception:
                pass

        return {
            **static,
            "vram_allocated_mb": 0,
            "vram_reserved_mb": 0,
            "vram_free_mb": 0
        }

    @classmethod
    def get_system_ram_info(cls) -> Dict[str, Any]:
        vm = psutil.virtual_memory()
        if cls._ram_total_mb == 0.0:
            cls._ram_total_mb = round(vm.total / (1024 * 1024), 2)

        return {
            "ram_total_mb": cls._ram_total_mb,
            "ram_available_mb": round(vm.available / (1024 * 1024), 2),
            "ram_used_mb": round(vm.used / (1024 * 1024), 2),
            "ram_percent": vm.percent,
            "cpu_percent": psutil.cpu_percent(interval=None)
        }

    @classmethod
    def get_full_telemetry(cls) -> Dict[str, Any]:
        gpu = cls.get_gpu_info()
        ram = cls.get_system_ram_info()
        return {
            "gpu": gpu,
            "system": ram
        }
