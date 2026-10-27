import os
import psutil
from typing import Dict, Any, Optional

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
    Detector dinámico de hardware para GPUs y memoria del sistema.
    Calcula los umbrales de memoria según los requisitos del usuario:
      - Modo Ahorro: <= 40% de la VRAM máxima
      - Modo Equilibrado: <= 65% de la VRAM máxima
      - Modo Alto Rendimiento: hasta el 100% de la VRAM disponible
    """

    @staticmethod
    def get_gpu_info() -> Dict[str, Any]:
        # 1. Primary path: PyTorch CUDA
        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                device_id = 0
                device_name = torch.cuda.get_device_name(device_id)
                props = torch.cuda.get_device_properties(device_id)
                total_vram_mb = round(props.total_memory / (1024 * 1024), 2)
                allocated_mb = round(torch.cuda.memory_allocated(device_id) / (1024 * 1024), 2)
                reserved_mb = round(torch.cuda.memory_reserved(device_id) / (1024 * 1024), 2)
                free_mb = round(total_vram_mb - reserved_mb, 2)

                return {
                    "available": True,
                    "name": device_name,
                    "device_id": device_id,
                    "vram_total_mb": total_vram_mb,
                    "vram_allocated_mb": allocated_mb,
                    "vram_reserved_mb": reserved_mb,
                    "vram_free_mb": max(free_mb, 0),
                    "thresholds_mb": {
                        "ahorro_40": round(total_vram_mb * 0.40, 2),
                        "equilibrado_65": round(total_vram_mb * 0.65, 2),
                        "alto_rendimiento_100": total_vram_mb
                    }
                }
            except Exception as e:
                print(f"[HardwareDetector] Advertencia en torch.cuda: {e}")

        # 2. Secondary path: Direct NVIDIA NVML
        if PYNVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name = pynvml.nvmlDeviceGetName(handle)
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                total_mb = round(mem.total / (1024 * 1024), 2)
                used_mb = round(mem.used / (1024 * 1024), 2)
                free_mb = round(mem.free / (1024 * 1024), 2)

                return {
                    "available": True,
                    "name": name if isinstance(name, str) else name.decode('utf-8', errors='ignore'),
                    "device_id": 0,
                    "vram_total_mb": total_mb,
                    "vram_allocated_mb": used_mb,
                    "vram_reserved_mb": used_mb,
                    "vram_free_mb": free_mb,
                    "thresholds_mb": {
                        "ahorro_40": round(total_mb * 0.40, 2),
                        "equilibrado_65": round(total_mb * 0.65, 2),
                        "alto_rendimiento_100": total_mb
                    }
                }
            except Exception as nvml_err:
                print(f"[HardwareDetector] Advertencia en NVML: {nvml_err}")

        # 3. CPU Fallback
        return {
            "available": False,
            "name": "CPU / No CUDA GPU Detected",
            "device_id": -1,
            "vram_total_mb": 0,
            "vram_allocated_mb": 0,
            "vram_reserved_mb": 0,
            "vram_free_mb": 0,
            "thresholds_mb": {
                "ahorro_40": 0,
                "equilibrado_65": 0,
                "alto_rendimiento_100": 0
            }
        }

    @staticmethod
    def get_system_ram_info() -> Dict[str, Any]:
        vm = psutil.virtual_memory()
        return {
            "ram_total_mb": round(vm.total / (1024 * 1024), 2),
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
