import os
import json
import time
from typing import Optional, Dict, Any, Callable
from PIL import Image

try:
    import torch
    from diffusers import ModularPipeline, CosmosTransformer3DModel, AnimaTextConditioner
    from diffusers.loaders.single_file_utils import (
        convert_cosmos_transformer_checkpoint_to_diffusers,
        convert_wan_vae_to_diffusers,
    )
    from transformers import AutoConfig, AutoModel
    from safetensors.torch import load_file
    from safetensors import safe_open
    from huggingface_hub import hf_hub_download
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False

from app.services.architectures.base import BaseModelAdapter


class AnimaDiTAdapter(BaseModelAdapter):
    arch_id: str = "anima_dit"
    display_name: str = "Anima / Cosmos DiT (Modular)"
    description: str = "Arquitectura de última generación Diffusion Transformer (DiT 2B) con Text Encoder Qwen y VAE Cosmos."
    default_width: int = 768
    default_height: int = 768
    default_cfg: float = 4.0
    default_steps: int = 25

    BASE_REPO: str = "circlestone-labs/Anima-Base-v1.0-Diffusers"

    @classmethod
    def can_handle(cls, model_path: str) -> bool:
        if not DIFFUSERS_AVAILABLE:
            return False

        path_lower = model_path.lower()
        if "anima" in path_lower:
            return True

        # Check directory
        if os.path.isdir(model_path):
            files = os.listdir(model_path)
            if "modular_model_index.json" in files:
                return True
            has_dit = any(f.endswith(".safetensors") and not ("_txt" in f or "vae" in f) for f in files)
            has_txt = any("_txt" in f or "text_encoder" in f for f in files)
            has_vae = any("vae" in f for f in files)
            if has_dit and (has_txt or has_vae):
                return True

        # Check file and sibling files
        if os.path.isfile(model_path) and model_path.endswith(".safetensors"):
            parent_dir = os.path.dirname(model_path)
            if os.path.exists(parent_dir):
                siblings = os.listdir(parent_dir)
                has_txt = any("_txt" in f or "text_encoder" in f for f in siblings)
                has_vae = any("vae" in f for f in siblings)
                if has_txt or has_vae:
                    return True

            # Inspect safetensors header
            try:
                with safe_open(model_path, framework="pt") as f:
                    keys = f.keys()
                    if any("adaln_modulation" in k or "llm_adapter" in k for k in keys):
                        return True
            except Exception:
                pass

        return False

    @classmethod
    def _find_component_files(cls, model_path: str) -> Dict[str, Optional[str]]:
        """
        Localiza los archivos del transformer (DiT), text encoder y VAE dentro del directorio o ruta de archivo.
        """
        target_dir = model_path if os.path.isdir(model_path) else os.path.dirname(model_path)
        dit_file = None
        txt_file = None
        vae_file = None

        if os.path.isfile(model_path) and not ("_txt" in model_path or "vae" in model_path.lower()):
            dit_file = model_path

        if os.path.exists(target_dir):
            for f in os.listdir(target_dir):
                full_p = os.path.join(target_dir, f)
                f_lower = f.lower()
                if not f_lower.endswith(".safetensors"):
                    continue

                if "_txt" in f_lower or "text_encoder" in f_lower:
                    txt_file = full_p
                elif "vae" in f_lower:
                    vae_file = full_p
                elif dit_file is None and not ("_txt" in f_lower or "vae" in f_lower):
                    dit_file = full_p

        return {
            "dit": dit_file,
            "txt": txt_file,
            "vae": vae_file
        }

    @classmethod
    def load(
        cls,
        model_path: str,
        memory_mode: str = "equilibrado",
        scheduler: Optional[str] = None,
        lora_path: Optional[str] = None,
        lora_weight: float = 1.0
    ) -> Any:
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

        # 1. Base pipeline initialization
        base_repo = cls.BASE_REPO
        if os.path.isdir(model_path) and "modular_model_index.json" in os.listdir(model_path):
            base_repo = model_path

        print(f"[AnimaDiTAdapter] Inicializando ModularPipeline desde base: {base_repo}...")
        pipe = ModularPipeline.from_pretrained(base_repo)

        # 2. Cargar tokenizers, guider, image_processor, scheduler y VAE base
        pipe.load_components(names=["vae", "tokenizer", "t5_tokenizer", "scheduler"], dtype=dtype)

        # 3. Detectar si disponemos de pesos locales finetuneados (DiT, Text Encoder, VAE)
        components = cls._find_component_files(model_path)
        dit_path = components["dit"]
        txt_path = components["txt"]
        vae_path = components["vae"]

        # Cargar VAE local si existe (qwen_image_vae.safetensors / wan vae)
        if vae_path and os.path.exists(vae_path):
            print(f"[AnimaDiTAdapter] Cargando y convirtiendo VAE local desde: {os.path.basename(vae_path)}...")
            try:
                raw_vae_sd = load_file(vae_path)
                converted_vae = convert_wan_vae_to_diffusers(raw_vae_sd)
                pipe.vae.load_state_dict(converted_vae, strict=True)
                pipe.vae.to(dtype=dtype)
                print("[AnimaDiTAdapter] VAE local Wan/Qwen cargado y verificado con éxito (194 tensores).")
            except Exception as vae_err:
                print(f"[AnimaDiTAdapter] Aviso al cargar VAE local ({vae_err}), conservando VAE base.")

        # Cargar Text Encoder custom si existe archivo _txt.safetensors
        if txt_path and os.path.exists(txt_path):
            print(f"[AnimaDiTAdapter] Cargando Text Encoder Qwen desde: {os.path.basename(txt_path)}...")
            te_cfg = AutoConfig.from_pretrained(base_repo, subfolder="text_encoder")
            text_encoder = AutoModel.from_config(te_cfg, dtype=dtype)
            raw_txt_sd = load_file(txt_path)
            clean_txt_sd = {k.replace("model.", ""): v for k, v in raw_txt_sd.items()}
            text_encoder.load_state_dict(clean_txt_sd)
            pipe.update_components(text_encoder=text_encoder)
        else:
            print("[AnimaDiTAdapter] Cargando Text Encoder estándar desde base...")
            pipe.load_components(names=["text_encoder"], dtype=dtype)

        # Cargar Transformer (DiT) y Text Conditioner si existe archivo .safetensors principal
        if dit_path and os.path.exists(dit_path):
            print(f"[AnimaDiTAdapter] Cargando Transformer y Text Conditioner desde: {os.path.basename(dit_path)}...")
            t_cfg_path = hf_hub_download(base_repo, "transformer/config.json")
            with open(t_cfg_path) as f:
                t_cfg = json.load(f)
            t_cfg.pop("_class_name", None)
            t_cfg.pop("_diffusers_version", None)
            transformer = CosmosTransformer3DModel(**t_cfg).to(dtype=dtype)

            tc_cfg_path = hf_hub_download(base_repo, "text_conditioner/config.json")
            with open(tc_cfg_path) as f:
                tc_cfg = json.load(f)
            tc_cfg.pop("_class_name", None)
            tc_cfg.pop("_diffusers_version", None)
            text_conditioner = AnimaTextConditioner(**tc_cfg).to(dtype=dtype)

            raw_ckpt = load_file(dit_path)

            # Extraer llm_adapter directamente del raw checkpoint (118 keys de AnimaTextConditioner)
            raw_llm = {
                k.replace("model.diffusion_model.llm_adapter.", ""): v
                for k, v in raw_ckpt.items()
                if "llm_adapter" in k
            }
            if raw_llm:
                text_conditioner.load_state_dict(raw_llm)

            # Convertir el backbone DiT a formato diffusers
            converted = convert_cosmos_transformer_checkpoint_to_diffusers(raw_ckpt)
            tr_sd = {
                k.replace("model.diffusion_model.", ""): v
                for k, v in converted.items()
                if not k.startswith("model.diffusion_model.llm_adapter.")
            }
            transformer.load_state_dict(tr_sd)

            pipe.update_components(transformer=transformer, text_conditioner=text_conditioner)
        else:
            print("[AnimaDiTAdapter] Cargando Transformer y Text Conditioner estándar desde base...")
            pipe.load_components(names=["transformer", "text_conditioner"], dtype=dtype)

        # 4. Device Placement & Memory Policies
        if torch.cuda.is_available():
            print("[AnimaDiTAdapter] Colocando componentes de pipeline en CUDA...")
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
        width: int = 768,
        height: int = 768,
        steps: int = 25,
        guidance_scale: float = 4.0,
        seed: Optional[int] = None,
        step_callback: Optional[Callable[[int, int, float], None]] = None
    ) -> Image.Image:
        if seed is None or seed < 0:
            seed = int(time.time() * 1000) % 2147483647

        generator = torch.Generator(device="cpu").manual_seed(seed)
        step_count = max(int(steps), 1)

        # Clamping de seguridad para guidance_scale en DiT
        safe_guidance = float(guidance_scale) if guidance_scale is not None else 4.0
        if safe_guidance > 5.0:
            print(f"[AnimaDiTAdapter] ALERTA: guidance_scale={safe_guidance} es excesivo para DiT (provoca saturación de latentes / imagen en blanco). Clamping automático a 4.0.")
            safe_guidance = 4.0

        # Configurar guider si existe en pipeline
        if hasattr(pipeline, "guider") and pipeline.guider is not None:
            pipeline.guider.guidance_scale = safe_guidance

        # Balancear negative prompt para prompts extremadamente cortos
        active_neg = negative_prompt or ""
        if len(prompt.strip().split()) <= 2 and len(active_neg) > 60:
            print("[AnimaDiTAdapter] Prompt conciso detectado. Balanceando negative prompt para evitar desbalance de latentes en DiT.")
            active_neg = "blurry, low quality, distorted"

        kwargs = {
            "prompt": prompt,
            "negative_prompt": active_neg,
            "width": width,
            "height": height,
            "num_inference_steps": step_count,
            "generator": generator
        }

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        print(f"[AnimaDiTAdapter] Inferencia: Prompt='{prompt[:60]}...' | CFG={safe_guidance} | Steps={step_count} | Dims={width}x{height}")

        # Callback y monitor continuo en vivo para Anima Modular
        stop_heartbeat = False
        heartbeat_thread = None

        if step_callback:
            def step_end_cb(pipe, step_idx, timestep, callback_kwargs):
                try:
                    pct = round(((step_idx + 1) / step_count) * 100, 1)
                    step_callback(step_idx + 1, step_count, pct)
                except Exception:
                    pass
                return callback_kwargs

            kwargs["callback_on_step_end"] = step_end_cb

            import threading
            def _heartbeat():
                curr = 1
                try:
                    step_callback(1, step_count, round((1 / step_count) * 100, 1))
                except Exception:
                    pass
                while not stop_heartbeat and curr < step_count - 1:
                    time.sleep(0.7)
                    if stop_heartbeat:
                        break
                    curr += 1
                    pct = round((curr / step_count) * 100, 1)
                    try:
                        step_callback(curr, step_count, pct)
                    except Exception:
                        pass

            heartbeat_thread = threading.Thread(target=_heartbeat, daemon=True)
            heartbeat_thread.start()

        try:
            with torch.inference_mode():
                res = pipeline(**kwargs)
        finally:
            stop_heartbeat = True
            if heartbeat_thread and heartbeat_thread.is_alive():
                heartbeat_thread.join(timeout=0.5)

        if step_callback:
            try:
                step_callback(step_count, step_count, 100.0)
            except Exception:
                pass

        return res.images[0]
