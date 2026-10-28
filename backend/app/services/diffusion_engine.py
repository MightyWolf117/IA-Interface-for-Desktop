import io
import gc
import os
import time
import base64
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Callable, Type

from app.core.hardware import HardwareDetector
from app.core.paths import get_outputs_dir
from app.services.architectures.base import BaseModelAdapter
from app.services.architectures.registry import ArchitectureRegistry

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None

TORCH_AVAILABLE = False
DIFFUSERS_AVAILABLE = False
IMPORT_ERROR_DETAILS = []

try:
    import torch
    TORCH_AVAILABLE = True
except Exception as e:
    import traceback
    err_msg = f"torch: {e}"
    IMPORT_ERROR_DETAILS.append(err_msg)
    print(f"[CYBER-IA DiffusionEngine] Fallo al cargar torch: {traceback.format_exc()}")

try:
    import diffusers
    DIFFUSERS_AVAILABLE = TORCH_AVAILABLE
except Exception as e:
    import traceback
    err_msg = f"diffusers: {e}"
    IMPORT_ERROR_DETAILS.append(err_msg)
    print(f"[CYBER-IA DiffusionEngine] Fallo al cargar diffusers: {traceback.format_exc()}")


class DiffusionEngine:
    """
    Motor central multi-arquitectura para la ejecución y alternancia dinámica de modelos de difusión.
    Implementa:
      - Arquitectura múltiple extensible (SD 1.5, SDXL, Anima DiT Modular, Diffusers AutoPipeline)
      - Detección automática y despacho inteligente por adaptador de arquitectura
      - Estrategias de memoria adaptativa (Ahorro 40%, Equilibrado 65%, Alto Rendimiento 100%)
      - Fallback a memoria RAM del sistema (Model & Sequential CPU Offload)
      - Soporte para componentes auxiliares (LoRA, Schedulers)
      - Salida dual configurable (Base64 vs Guardado en Disco)
    """

    _pipeline = None
    _active_model: Optional[str] = None
    _active_adapter: Optional[Type[BaseModelAdapter]] = None
    _memory_mode: str = "equilibrado"
    _transfer_mode: str = "base64"
    _auxiliaries: Dict[str, Any] = {}
    _device: str = "cuda" if (DIFFUSERS_AVAILABLE and torch.cuda.is_available()) else "cpu"

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        vram_alloc = 0
        vram_res = 0
        if DIFFUSERS_AVAILABLE and torch.cuda.is_available():
            try:
                vram_alloc = round(torch.cuda.memory_allocated() / (1024 * 1024), 2)
                vram_res = round(torch.cuda.memory_reserved() / (1024 * 1024), 2)
            except Exception:
                pass

        arch_info = {}
        if cls._active_adapter:
            arch_info = {
                "arch_id": cls._active_adapter.arch_id,
                "display_name": cls._active_adapter.display_name,
                "default_width": cls._active_adapter.default_width,
                "default_height": cls._active_adapter.default_height,
                "default_cfg": cls._active_adapter.default_cfg,
                "default_steps": cls._active_adapter.default_steps
            }

        return {
            "loaded": cls._pipeline is not None,
            "active_model": cls._active_model,
            "architecture": arch_info,
            "memory_mode": cls._memory_mode,
            "transfer_mode": cls._transfer_mode,
            "device": cls._device,
            "auxiliaries": cls._auxiliaries,
            "vram_allocated_mb": vram_alloc,
            "vram_reserved_mb": vram_res
        }

    @classmethod
    def unload_model(cls) -> Dict[str, Any]:
        """
        Descarga completamente el modelo activo y vacía la memoria VRAM y RAM.
        """
        old_model = cls._active_model
        cls._pipeline = None
        cls._active_model = None
        cls._active_adapter = None
        cls._auxiliaries = {}

        if DIFFUSERS_AVAILABLE and torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
            except Exception:
                pass
        gc.collect()

        vram_info = HardwareDetector.get_gpu_info()
        return {
            "success": True,
            "previous_model": old_model,
            "vram_allocated_mb": vram_info.get("vram_allocated_mb", 0),
            "vram_reserved_mb": vram_info.get("vram_reserved_mb", 0),
            "message": f"Modelo {old_model or ''} descargado exitosamente. Caché de VRAM y RAM liberada."
        }

    @classmethod
    def load_model(
        cls,
        model_id_or_path: str,
        memory_mode: str = "equilibrado",
        transfer_mode: str = "base64",
        lora_path: Optional[str] = None,
        lora_weight: float = 1.0,
        scheduler: Optional[str] = "EulerA",
        download_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Carga un modelo local o remoto de Hugging Face detectando dinámicamente su arquitectura
        y configurando las políticas óptimas de memoria y hardware.
        Permite descargar modelos públicos estructuradamente en la carpeta que el usuario elija.
        """
        if cls._pipeline is not None:
            cls.unload_model()

        cls._memory_mode = memory_mode.lower()
        cls._transfer_mode = transfer_mode.lower()
        cls._active_model = model_id_or_path
        cls._auxiliaries = {
            "lora": lora_path,
            "lora_weight": lora_weight,
            "scheduler": scheduler
        }

        if not DIFFUSERS_AVAILABLE or not TORCH_AVAILABLE:
            detail = "; ".join(IMPORT_ERROR_DETAILS) if IMPORT_ERROR_DETAILS else "Módulos torch / diffusers no encontrados en el entorno empaquetado."
            return {
                "success": False,
                "model_id": model_id_or_path,
                "memory_mode": cls._memory_mode,
                "transfer_mode": cls._transfer_mode,
                "device": "NO_DIFFUSERS",
                "vram_allocated_mb": 0.0,
                "vram_reserved_mb": 0.0,
                "message": f"Error crítico: El motor de difusión no está disponible en este entorno Python. Detalle: {detail}"
            }

        # 1. Comprobar si es un modelo público de HF y resolver su directorio local de destino
        actual_model_path = model_id_or_path
        if "/" in model_id_or_path and not os.path.exists(model_id_or_path) and download_dir:
            safe_name = model_id_or_path.replace("/", "--")
            target_folder = os.path.join(download_dir, safe_name)

            # Comprobar si ya existe descargado con sus archivos principales
            is_already_downloaded = False
            if os.path.isdir(target_folder):
                files = os.listdir(target_folder)
                if "model_index.json" in files or "modular_model_index.json" in files or any(f.endswith(".safetensors") for f in files):
                    is_already_downloaded = True

            if is_already_downloaded:
                print(f"[DiffusionEngine] Modelo público localizado en carpeta del usuario: {target_folder}")
                actual_model_path = target_folder
            else:
                print(f"[DiffusionEngine] Descargando modelo público '{model_id_or_path}' estructuradamente en: {target_folder}...")
                os.makedirs(target_folder, exist_ok=True)
                try:
                    from huggingface_hub import snapshot_download
                    snapshot_download(
                        repo_id=model_id_or_path,
                        local_dir=target_folder
                    )
                    actual_model_path = target_folder
                    print(f"[DiffusionEngine] ¡Descarga de '{model_id_or_path}' completada con éxito en {target_folder}!")
                except Exception as dl_err:
                    print(f"[DiffusionEngine] Error al descargar modelo en {target_folder}: {dl_err}. Intentando fallback estándar...")

        # 2. Determinar el adaptador de arquitectura óptimo
        adapter = ArchitectureRegistry.get_adapter(actual_model_path)
        print(f"[DiffusionEngine] Despachando modelo '{actual_model_path}' al adaptador: {adapter.display_name} ({adapter.arch_id})")

        # 3. Cargar a través del adaptador especializado
        pipe = adapter.load(
            model_path=actual_model_path,
            memory_mode=cls._memory_mode,
            scheduler=scheduler,
            lora_path=lora_path,
            lora_weight=lora_weight
        )

        cls._pipeline = pipe
        cls._active_adapter = adapter
        cls._device = "cuda" if (DIFFUSERS_AVAILABLE and torch.cuda.is_available()) else "cpu"

        vram_info = HardwareDetector.get_gpu_info()
        return {
            "success": True,
            "model_id": model_id_or_path,
            "architecture": {
                "arch_id": adapter.arch_id,
                "display_name": adapter.display_name,
                "description": adapter.description,
                "default_width": adapter.default_width,
                "default_height": adapter.default_height,
                "default_cfg": adapter.default_cfg,
                "default_steps": adapter.default_steps
            },
            "memory_mode": cls._memory_mode,
            "transfer_mode": cls._transfer_mode,
            "device": str(cls._device),
            "vram_allocated_mb": vram_info.get("vram_allocated_mb", 0),
            "vram_reserved_mb": vram_info.get("vram_reserved_mb", 0),
            "message": f"Modelo {model_id_or_path} inicializado correctamente bajo arquitectura '{adapter.display_name}' en modo '{cls._memory_mode}'."
        }

    @classmethod
    def generate(
        cls,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        steps: int = 20,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        step_callback: Optional[Callable[[int, int, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta la inferencia de difusión y genera la imagen en Base64 o guardado en Disco.
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow (PIL) no está instalado en este entorno de Python.")

        start_time = time.perf_counter()
        gen_id = f"gen_{uuid.uuid4().hex[:10]}"

        if seed is None or seed < 0:
            seed = int(time.time() * 1000) % 2147483647

        # Check if pipeline is ready or in preview mode
        if cls._pipeline is None:
            img = Image.new("RGB", (width, height), color=(9, 12, 21))
            draw = ImageDraw.Draw(img)
            draw.rectangle([10, 10, width - 10, height - 10], outline=(0, 240, 255), width=2)
            draw.text((25, 25), "CYBER-DIFFUSION // PREVIEW", fill=(0, 240, 255))
            draw.text((25, 55), f"PROMPT: {prompt[:40]}...", fill=(255, 0, 85))
            draw.text((25, 85), f"SEED: {seed} | STEPS: {steps}", fill=(255, 183, 0))
            draw.text((25, 115), "AVISO: Carga un modelo en 'Configurar Modelo' para inferencia real.", fill=(130, 145, 175))
        else:
            # Inferencia a través del adaptador activo
            if cls._active_adapter is not None:
                img = cls._active_adapter.generate(
                    pipeline=cls._pipeline,
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    steps=steps,
                    guidance_scale=guidance_scale,
                    seed=seed,
                    step_callback=step_callback
                )
            else:
                # Fallback estándar
                generator = torch.Generator(device="cpu").manual_seed(seed)
                kwargs = {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                    "num_inference_steps": steps,
                    "guidance_scale": guidance_scale,
                    "generator": generator
                }
                result = cls._pipeline(**kwargs)
                img = result.images[0]

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        vram_info = HardwareDetector.get_gpu_info()

        # Format output: Base64 or Disk
        if cls._transfer_mode == "disk":
            outputs_path = get_outputs_dir()
            filename = f"{gen_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
            file_path = os.path.join(outputs_path, filename)
            img.save(file_path, format="PNG")
            image_data = f"/outputs/{filename}"
        else:
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
            image_data = f"data:image/png;base64,{b64_str}"

        return {
            "id": gen_id,
            "image_data": image_data,
            "transfer_mode": cls._transfer_mode,
            "latency_ms": latency_ms,
            "seed": seed,
            "steps": steps,
            "width": width,
            "height": height,
            "vram_allocated_mb": vram_info.get("vram_allocated_mb", 0),
            "architecture": cls._active_adapter.display_name if cls._active_adapter else "Unknown"
        }

    @classmethod
    def check_public_model(cls, model_id: str, download_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprueba si un modelo público de Hugging Face ya se encuentra descargado en el directorio indicado.
        """
        safe_name = model_id.replace("/", "--")
        if not download_dir or not os.path.isdir(download_dir):
            return {
                "model_id": model_id,
                "present": False,
                "local_path": None,
                "size_mb": 0.0,
                "safe_folder_name": safe_name
            }

        target_folder = os.path.join(download_dir, safe_name)
        if os.path.isdir(target_folder):
            files = os.listdir(target_folder)
            if "model_index.json" in files or "modular_model_index.json" in files or any(f.endswith(".safetensors") for f in files):
                total_bytes = 0
                for root, _, filenames in os.walk(target_folder):
                    for fn in filenames:
                        fp = os.path.join(root, fn)
                        try:
                            total_bytes += os.path.getsize(fp)
                        except OSError:
                            pass
                return {
                    "model_id": model_id,
                    "present": True,
                    "local_path": target_folder,
                    "size_mb": round(total_bytes / (1024 * 1024), 2),
                    "safe_folder_name": safe_name
                }

        return {
            "model_id": model_id,
            "present": False,
            "local_path": target_folder,
            "size_mb": 0.0,
            "safe_folder_name": safe_name
        }

    @classmethod
    def delete_public_model(cls, model_id: str, download_dir: str) -> Dict[str, Any]:
        """
        Elimina de forma segura la carpeta de un modelo público descargado previamente en disco.
        """
        safe_name = model_id.replace("/", "--")
        target_folder = os.path.join(download_dir, safe_name)

        if not os.path.isdir(target_folder):
            return {
                "success": False,
                "model_id": model_id,
                "message": f"No se encontró la carpeta del modelo en: {target_folder}",
                "freed_mb": 0.0
            }

        total_bytes = 0
        for root, _, filenames in os.walk(target_folder):
            for fn in filenames:
                try:
                    total_bytes += os.path.getsize(os.path.join(root, fn))
                except OSError:
                    pass

        freed_mb = round(total_bytes / (1024 * 1024), 2)
        import shutil
        try:
            shutil.rmtree(target_folder)
            return {
                "success": True,
                "model_id": model_id,
                "message": f"Modelo {model_id} eliminado exitosamente. {freed_mb} MB liberados.",
                "freed_mb": freed_mb
            }
        except Exception as e:
            return {
                "success": False,
                "model_id": model_id,
                "message": f"Error al eliminar carpeta {target_folder}: {str(e)}",
                "freed_mb": 0.0
            }
