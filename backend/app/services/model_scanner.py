import os
from typing import Dict, List, Any
from app.services.architectures.registry import ArchitectureRegistry


class ModelScanner:
    """
    Escáner inteligente de modelos locales de difusión y componentes auxiliares (LoRA, ControlNet, VAE).
    Detecta automáticamente arquitecturas (SD 1.5, SDXL, Anima DiT Modular, Diffusers)
    y organiza opciones dinámicas para la interfaz.
    """

    PUBLIC_MODELS = [
        {
            "id": "runwayml/stable-diffusion-v1-5",
            "name": "Stable Diffusion v1.5 (Standard)",
            "type": "public_hf",
            "format": "diffusers",
            "description": "Modelo clásico y confiable de 512x512. Excelente compatibilidad con LoRAs y ControlNet.",
            "recommended_vram_mb": 4096,
            "arch_id": "sd15",
            "architecture": "SD 1.5",
            "default_width": 512,
            "default_height": 512,
            "default_cfg": 7.5,
            "default_steps": 20
        },
        {
            "id": "stabilityai/sd-turbo",
            "name": "SD-Turbo (Ultra Rápido)",
            "type": "public_hf",
            "format": "diffusers",
            "description": "Modelo adversarial destilado capaz de generar imágenes en 1 a 4 pasos.",
            "recommended_vram_mb": 3072,
            "arch_id": "sd15",
            "architecture": "SD 2.1 Adversarial",
            "default_width": 512,
            "default_height": 512,
            "default_cfg": 1.5,
            "default_steps": 4
        },
        {
            "id": "segmind/SSD-1B",
            "name": "SSD-1B (SDXL Compacto)",
            "type": "public_hf",
            "format": "diffusers",
            "description": "Versión 50% más pequeña y rápida de SDXL con calidad de 1024x1024.",
            "recommended_vram_mb": 4608,
            "arch_id": "sdxl",
            "architecture": "SDXL-Distill",
            "default_width": 1024,
            "default_height": 1024,
            "default_cfg": 7.0,
            "default_steps": 25
        },
        {
            "id": "circlestone-labs/Anima-Base-v1.0-Diffusers",
            "name": "Anima Base v1.0 (DiT 2B Anime)",
            "type": "public_hf",
            "format": "modular_diffusers",
            "description": "Modelo DiT (Diffusion Transformer) 2B de CircleStone Labs & Comfy Org especializado en anime.",
            "recommended_vram_mb": 6144,
            "arch_id": "anima_dit",
            "architecture": "Anima DiT",
            "default_width": 768,
            "default_height": 768,
            "default_cfg": 4.0,
            "default_steps": 25
        }
    ]

    @classmethod
    def scan_directory(cls, root_dir: str) -> Dict[str, Any]:
        """
        Escanea un directorio local en busca de modelos de difusión completos y auxiliares.
        """
        result = {
            "root_path": root_dir,
            "exists": False,
            "base_models": [],
            "loras": [],
            "controlnets": [],
            "vaes": [],
            "public_models": cls.PUBLIC_MODELS,
            "supported_architectures": ArchitectureRegistry.list_supported_architectures()
        }

        if not os.path.exists(root_dir) or not os.path.isdir(root_dir):
            return result

        result["exists"] = True

        for root, dirs, files in os.walk(root_dir):
            # Limit depth relative to root_dir
            rel_depth = root[len(root_dir):].count(os.sep)
            if rel_depth > 3:
                continue

            # 1. Check if current directory is a Modular DiT Model (like reedAnimaFurry_v12)
            has_dit = any(f.endswith(".safetensors") and not ("_txt" in f or "vae" in f) for f in files)
            has_txt = any("_txt" in f or "text_encoder" in f for f in files)
            has_vae = any("vae" in f for f in files)

            if has_dit and (has_txt or has_vae) and root != root_dir:
                total_size_mb = 0
                for f in files:
                    if f.endswith(".safetensors"):
                        try:
                            total_size_mb += os.path.getsize(os.path.join(root, f)) / (1024 * 1024)
                        except OSError:
                            pass

                arch_meta = ArchitectureRegistry.detect_architecture(root)
                result["base_models"].append({
                    "id": root.replace("\\", "/"),
                    "name": os.path.basename(root),
                    "type": "modular_dit",
                    "path": root,
                    "format": "modular",
                    "size_mb": round(total_size_mb, 2),
                    "arch_id": arch_meta["arch_id"],
                    "architecture": arch_meta["display_name"],
                    "description": arch_meta["description"],
                    "default_width": arch_meta["default_width"],
                    "default_height": arch_meta["default_height"],
                    "default_cfg": arch_meta["default_cfg"],
                    "default_steps": arch_meta["default_steps"]
                })
                # Prevent scanning deeper inside this model folder
                dirs.clear()
                continue

            # 2. Check if current directory is a Diffusers or Modular pipeline
            if "model_index.json" in files or "modular_model_index.json" in files:
                model_name = os.path.basename(root)
                arch_meta = ArchitectureRegistry.detect_architecture(root)
                result["base_models"].append({
                    "id": root.replace("\\", "/"),
                    "name": model_name,
                    "type": "local_diffusers",
                    "path": root,
                    "format": "directory",
                    "arch_id": arch_meta["arch_id"],
                    "architecture": arch_meta["display_name"],
                    "description": arch_meta["description"],
                    "default_width": arch_meta["default_width"],
                    "default_height": arch_meta["default_height"],
                    "default_cfg": arch_meta["default_cfg"],
                    "default_steps": arch_meta["default_steps"]
                })
                dirs.clear()
                continue

            # 3. Check for standalone files (.safetensors, .ckpt)
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in [".safetensors", ".ckpt"]:
                    full_path = os.path.join(root, f)
                    try:
                        size_mb = round(os.path.getsize(full_path) / (1024 * 1024), 2)
                    except OSError:
                        size_mb = 0

                    fname_lower = f.lower()

                    # Auxiliary classification
                    if "lora" in fname_lower or (size_mb > 10 and size_mb < 400 and "vae" not in fname_lower):
                        result["loras"].append({
                            "id": full_path.replace("\\", "/"),
                            "name": f,
                            "path": full_path,
                            "size_mb": size_mb,
                            "type": "lora"
                        })
                    elif "control" in fname_lower:
                        result["controlnets"].append({
                            "id": full_path.replace("\\", "/"),
                            "name": f,
                            "path": full_path,
                            "size_mb": size_mb,
                            "type": "controlnet"
                        })
                    elif "vae" in fname_lower:
                        result["vaes"].append({
                            "id": full_path.replace("\\", "/"),
                            "name": f,
                            "path": full_path,
                            "size_mb": size_mb,
                            "type": "vae"
                        })
                    elif "_txt" in fname_lower or "text_encoder" in fname_lower:
                        # Modular text encoder, not a standalone model
                        continue
                    elif size_mb > 800:
                        # Full diffusion checkpoint
                        arch_meta = ArchitectureRegistry.detect_architecture(full_path)
                        result["base_models"].append({
                            "id": full_path.replace("\\", "/"),
                            "name": f,
                            "path": full_path,
                            "size_mb": size_mb,
                            "type": "single_file",
                            "format": ext[1:],
                            "arch_id": arch_meta["arch_id"],
                            "architecture": arch_meta["display_name"],
                            "description": arch_meta["description"],
                            "default_width": arch_meta["default_width"],
                            "default_height": arch_meta["default_height"],
                            "default_cfg": arch_meta["default_cfg"],
                            "default_steps": arch_meta["default_steps"]
                        })

        return result
