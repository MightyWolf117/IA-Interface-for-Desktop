import os
import time
from typing import Optional, Dict, Any, Callable
from PIL import Image

try:
    import torch
    from diffusers import (
        StableDiffusionPipeline,
        EulerAncestralDiscreteScheduler,
        DPMSolverMultistepScheduler,
        DDIMScheduler,
        UniPCMultistepScheduler
    )
    from safetensors import safe_open
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False

from app.services.architectures.base import BaseModelAdapter


class SD15Adapter(BaseModelAdapter):
    arch_id: str = "sd15"
    display_name: str = "Stable Diffusion 1.5 / 2.1"
    description: str = "Arquitectura clásica de difusión latente SD 1.5 (512x512). Máxima compatibilidad con LoRAs."
    default_width: int = 512
    default_height: int = 512
    default_cfg: float = 7.5
    default_steps: int = 20

    @classmethod
    def can_handle(cls, model_path: str) -> bool:
        if not DIFFUSERS_AVAILABLE:
            return False

        # HF model check
        if "stable-diffusion-v1-5" in model_path.lower() or "sd-turbo" in model_path.lower() or "sd-v1" in model_path.lower():
            return True

        if os.path.isfile(model_path) and model_path.endswith((".safetensors", ".ckpt")):
            # Inspect safetensors header keys
            if model_path.endswith(".safetensors"):
                try:
                    with safe_open(model_path, framework="pt") as f:
                        keys = f.keys()
                        # If it has DiT/Cosmos keys or SDXL keys, it is not SD 1.5
                        if any("adaln_modulation" in k or "llm_adapter" in k for k in keys):
                            return False
                        if any("conditioner.embedders.1" in k or "model.diffusion_model.label_emb" in k for k in keys):
                            return False
                        # SD 1.5 typically has classic UNet and CLIP text model keys
                        if any("model.diffusion_model.input_blocks" in k or "down_blocks" in k for k in keys):
                            return True
                except Exception:
                    pass
            # Default fallback for single files if not SDXL
            return True

        return False

    @classmethod
    def load(
        cls,
        model_path: str,
        memory_mode: str = "equilibrado",
        scheduler: Optional[str] = "EulerA",
        lora_path: Optional[str] = None,
        lora_weight: float = 1.0
    ) -> Any:
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        if os.path.isfile(model_path) and model_path.endswith((".safetensors", ".ckpt")):
            from app.core.paths import get_model_config_dir
            sd15_cfg = get_model_config_dir("sd15")
            single_file_kwargs = {
                "torch_dtype": torch_dtype,
                "use_safetensors": True,
                "load_safety_checker": False
            }
            if sd15_cfg:
                print(f"[SD15Adapter] Utilizando configuración offline pre-empaquetada desde: {sd15_cfg}")
                single_file_kwargs["config"] = sd15_cfg

            try:
                pipe = StableDiffusionPipeline.from_single_file(
                    model_path,
                    **single_file_kwargs
                )
            except Exception as e:
                if "model_index.json" in str(e) or "EnvironmentError" in type(e).__name__:
                    print(f"[SD15Adapter] Fallo con configuración personalizada ({e}). Reintentando carga directa...")
                    pipe = StableDiffusionPipeline.from_single_file(
                        model_path,
                        torch_dtype=torch_dtype,
                        use_safetensors=True,
                        load_safety_checker=False
                    )
                else:
                    raise
        else:
            load_kwargs = {"torch_dtype": torch_dtype, "safety_checker": None, "requires_safety_checker": False}
            pipe = StableDiffusionPipeline.from_pretrained(model_path, **load_kwargs)

        # Configure scheduler
        if scheduler and hasattr(pipe, "scheduler"):
            try:
                cfg = pipe.scheduler.config
                if scheduler == "EulerA":
                    pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(cfg)
                elif scheduler == "DPM++":
                    pipe.scheduler = DPMSolverMultistepScheduler.from_config(cfg, use_karras_sigmas=True)
                elif scheduler == "DDIM":
                    pipe.scheduler = DDIMScheduler.from_config(cfg)
                elif scheduler == "UniPC":
                    pipe.scheduler = UniPCMultistepScheduler.from_config(cfg)
            except Exception as sch_err:
                print(f"[SD15Adapter] Error configurando scheduler {scheduler}: {sch_err}")

        # Configure LoRA
        if lora_path and os.path.exists(lora_path) and hasattr(pipe, "load_lora_weights"):
            try:
                pipe.load_lora_weights(lora_path)
                if hasattr(pipe, "fuse_lora"):
                    pipe.fuse_lora(lora_scale=lora_weight)
            except Exception as lora_err:
                print(f"[SD15Adapter] Error configurando LoRA {lora_path}: {lora_err}")

        # Apply memory policy
        if torch.cuda.is_available():
            if memory_mode == "ahorro":
                pipe.enable_sequential_cpu_offload()
                if hasattr(pipe, "enable_vae_tiling"):
                    pipe.enable_vae_tiling()
            elif memory_mode == "equilibrado":
                pipe.enable_model_cpu_offload()
            else:
                pipe.to("cuda")
        else:
            pipe.to("cpu")

        return pipe

    @classmethod
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
        if seed is None or seed < 0:
            seed = int(time.time() * 1000) % 2147483647

        generator = torch.Generator(device="cpu").manual_seed(seed)
        step_count = max(int(steps), 1)

        if step_callback:
            import inspect

            def step_end_cb(pipe, step_idx, timestep, callback_kwargs):
                try:
                    pct = round(((step_idx + 1) / step_count) * 100, 1)
                    step_callback(step_idx + 1, step_count, pct)
                except Exception:
                    pass
                return callback_kwargs

            sig = inspect.signature(pipeline.__call__)
            if "callback_on_step_end" in sig.parameters or hasattr(pipeline, "callback_on_step_end"):
                kwargs["callback_on_step_end"] = step_end_cb
                if "callback_on_step_end_tensor_inputs" in sig.parameters:
                    kwargs["callback_on_step_end_tensor_inputs"] = ["latents"]
            elif "callback" in sig.parameters:
                kwargs["callback"] = lambda step, ts, lat: step_callback(step + 1, step_count, round(((step + 1) / step_count) * 100, 1))
                kwargs["callback_steps"] = 1

        res = pipeline(**kwargs)
        return res.images[0]
