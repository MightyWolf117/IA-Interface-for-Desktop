import os
import sys
import json
import shutil
import socket
import subprocess
import urllib.request
import urllib.error
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional

from app.core.paths import get_app_dir

# Storage path for persistent model profiles and LLM system config
PROFILES_FILE = os.path.join(get_app_dir(), "core", "model_profiles.json")
CONFIG_FILE = os.path.join(get_app_dir(), "core", "llm_config.json")

# Default core profiles
DEFAULT_CORE_PROFILES = {
    "llama3": {"name": "Llama 3 / 3.1 / 3.2", "family": "llama", "default_context": 8192},
    "qwen": {"name": "Qwen 2.5", "family": "qwen2", "default_context": 8192},
    "mistral": {"name": "Mistral / Nemo", "family": "mistral", "default_context": 8192},
    "deepseek": {"name": "DeepSeek R1 / V3", "family": "deepseek", "default_context": 16384},
    "gemma": {"name": "Gemma 2 / Gemma 3", "family": "gemma2", "default_context": 8192},
    "llava": {"name": "LLaVA / Vision Core", "family": "llava", "default_context": 4096, "is_vision": True},
    "phi": {"name": "Phi-3.5 / Phi-4", "family": "phi3", "default_context": 4096},
    "custom": {"name": "Personalizado / Genérico", "family": "custom", "default_context": 4096}
}


class TextModelManager:
    """
    Gestor inteligente de modelos de lenguaje (LLM).
    - Descubre modelos externos a través del servicio local de Ollama (http://127.0.0.1:11434).
    - Escanea directorios locales personalizados (almacén de Ollama y archivos directos GGUF).
    - Detecta automáticamente la familia/arquitectura y capacidades multimodales (Visión).
    - Permite la selección y anulación manual del core de inferencia.
    - Persiste y administra la personalización, contexto e instrucciones por modelo.
    - Controla el arranque del servicio en segundo plano de Ollama con OLLAMA_MODELS dinámico.
    """

    _ollama_base_url: str = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    _profiles_cache: Dict[str, Dict[str, Any]] = {}
    _custom_llm_path: Optional[str] = None

    @classmethod
    def get_ollama_url(cls) -> str:
        return cls._ollama_base_url

    @classmethod
    def set_ollama_url(cls, url: str):
        cls._ollama_base_url = url.rstrip("/")

    @classmethod
    def get_custom_llm_path(cls) -> str:
        if cls._custom_llm_path:
            return cls._custom_llm_path

        if os.path.isfile(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    path = cfg.get("custom_llm_path")
                    if path and os.path.isdir(path):
                        cls._custom_llm_path = path
                        return cls._custom_llm_path
            except Exception as e:
                print(f"[TextModelManager] Error leyendo configuración LLM: {e}")

        # Fallbacks por defecto
        if os.path.isdir("e:\\modelosLLM"):
            cls._custom_llm_path = "e:\\modelosLLM"
        else:
            default_dir = os.path.join(get_app_dir(), "models", "llm")
            os.makedirs(default_dir, exist_ok=True)
            cls._custom_llm_path = default_dir

        return cls._custom_llm_path

    @classmethod
    def set_custom_llm_path(cls, path: str) -> str:
        clean_path = os.path.normpath(path.strip())
        cls._custom_llm_path = clean_path
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            cfg = {}
            if os.path.isfile(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                except Exception:
                    cfg = {}
            cfg["custom_llm_path"] = clean_path
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[TextModelManager] Error guardando ruta personalizada: {e}")
        return clean_path

    @classmethod
    def find_ollama_executable(cls) -> Optional[str]:
        """Localiza el binario ejecutable de Ollama en el sistema."""
        which_path = shutil.which("ollama")
        if which_path and os.path.isfile(which_path):
            return which_path

        user_home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        candidates = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"),
            os.path.join(user_home, "AppData", "Local", "Programs", "Ollama", "ollama.exe"),
            "C:\\Program Files\\Ollama\\ollama.exe",
            "C:\\Users\\juanp\\AppData\\Local\\Programs\\Ollama\\ollama.exe"
        ]
        for c in candidates:
            if c and os.path.isfile(c):
                return c
        return None

    @classmethod
    def start_ollama_daemon(cls, custom_models_path: Optional[str] = None) -> Dict[str, Any]:
        """Inicia el servicio 'ollama serve' en segundo plano de manera desacoplada."""
        if cls.is_ollama_available():
            return {
                "success": True,
                "message": "El servicio de Ollama ya se encuentra en ejecución activa.",
                "already_running": True
            }

        ollama_bin = cls.find_ollama_executable()
        if not ollama_bin:
            return {
                "success": False,
                "message": "No se encontró el ejecutable ollama.exe en las rutas habituales del sistema.",
                "already_running": False
            }

        env = os.environ.copy()
        target_models_dir = custom_models_path or cls.get_custom_llm_path()
        if target_models_dir and os.path.isdir(target_models_dir):
            env["OLLAMA_MODELS"] = target_models_dir

        creationflags = 0
        if sys.platform == "win32":
            creationflags = (
                getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                | getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
            )

        try:
            proc = subprocess.Popen(
                [ollama_bin, "serve"],
                env=env,
                creationflags=creationflags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                close_fds=True
            )
            return {
                "success": True,
                "message": f"Servicio Ollama iniciado con éxito en segundo plano (PID: {proc.pid}).",
                "pid": proc.pid,
                "already_running": False
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Fallo al iniciar el proceso de Ollama: {str(e)}",
                "already_running": False
            }

    @classmethod
    def _load_profiles(cls) -> Dict[str, Dict[str, Any]]:
        if cls._profiles_cache:
            return cls._profiles_cache

        if os.path.isfile(PROFILES_FILE):
            try:
                with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                    cls._profiles_cache = json.load(f)
                    return cls._profiles_cache
            except Exception as e:
                print(f"[TextModelManager] Error leyendo perfiles: {e}")

        cls._profiles_cache = {}
        return cls._profiles_cache

    @classmethod
    def _save_profiles(cls):
        try:
            os.makedirs(os.path.dirname(PROFILES_FILE), exist_ok=True)
            with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(cls._profiles_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[TextModelManager] Error guardando perfiles en disco: {e}")

    @classmethod
    def get_model_profile(cls, model_id: str) -> Dict[str, Any]:
        profiles = cls._load_profiles()
        if model_id in profiles:
            return profiles[model_id]

        # Auto-generate default profile based on model ID
        detected_core = cls.detect_model_core(model_id)
        default_profile = {
            "model_id": model_id,
            "custom_name": model_id.split(":")[0].replace("-", " ").title(),
            "core": detected_core,
            "system_prompt": (
                "Eres CYBER-IA, un asistente neural de inteligencia artificial de alta precisión "
                "con interfaz Cyberpunk HUD. Responde de forma clara, técnica, estructurada "
                "y en español salvo que el usuario solicite otro idioma o código fuente."
            ),
            "temperature": 0.7,
            "top_p": 0.9,
            "context_window": DEFAULT_CORE_PROFILES.get(detected_core, {}).get("default_context", 4096),
            "max_tokens": 2048,
            "repeat_penalty": 1.1,
            "web_search_enabled": False
        }
        profiles[model_id] = default_profile
        cls._save_profiles()
        return default_profile

    @classmethod
    def save_model_profile(cls, model_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        profiles = cls._load_profiles()
        current = profiles.get(model_id, {})
        current.update(settings)
        current["model_id"] = model_id
        profiles[model_id] = current
        cls._profiles_cache = profiles
        cls._save_profiles()
        return current

    @classmethod
    def detect_model_core(cls, model_id: str, families: Optional[List[str]] = None) -> str:
        """
        Deduce el core arquitectónico a partir del identificador del modelo o metadatos de Ollama.
        """
        mid = model_id.lower()
        fam_list = [f.lower() for f in (families or [])]

        if any("clip" in f or "vision" in f or "mllama" in f for f in fam_list) or "llava" in mid or "vision" in mid:
            return "llava"
        if "llama" in mid or "llama" in fam_list:
            return "llama3"
        if "qwen" in mid or "qwen" in fam_list:
            return "qwen"
        if "deepseek" in mid or "deepseek" in fam_list:
            return "deepseek"
        if "mistral" in mid or "nemo" in mid or "mistral" in fam_list:
            return "mistral"
        if "gemma" in mid or "gemma" in fam_list:
            return "gemma"
        if "phi" in mid or "phi" in fam_list:
            return "phi"

        return "custom"

    @classmethod
    def is_ollama_available(cls) -> bool:
        """Comprueba de forma rápida y silenciosa si Ollama está respondiendo en el puerto configurado."""
        try:
            parsed = urlparse(cls._ollama_base_url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 11434
            with socket.create_connection((host, port), timeout=0.6):
                return True
        except (OSError, socket.timeout, ConnectionRefusedError):
            return False
        except Exception:
            return False

    @classmethod
    def list_ollama_models(cls) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de modelos descargados externamente a través de Ollama.
        """
        if not cls.is_ollama_available():
            return []

        url = f"{cls._ollama_base_url}/api/tags"
        models: List[Dict[str, Any]] = []

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CYBER-IA/1.2.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_models = data.get("models", [])
                    for m in raw_models:
                        name = m.get("name", "")
                        details = m.get("details", {})
                        families = details.get("families", [])
                        family = details.get("family", "")
                        param_size = details.get("parameter_size", "Desconocido")
                        quant = details.get("quantization_level", "Q4_K_M")
                        size_gb = round(m.get("size", 0) / (1024 ** 3), 2)

                        core = cls.detect_model_core(name, families + ([family] if family else []))
                        is_vision = (
                            core == "llava"
                            or any("clip" in f or "vision" in f or "mllama" in f for f in families)
                            or "vision" in name.lower()
                            or "llava" in name.lower()
                        )

                        profile = cls.get_model_profile(name)

                        models.append({
                            "id": name,
                            "name": profile.get("custom_name", name),
                            "source": "ollama",
                            "parameters": param_size,
                            "quantization": quant,
                            "size_gb": size_gb,
                            "core": profile.get("core", core),
                            "detected_core": core,
                            "is_vision": is_vision,
                            "status": "ready",
                            "settings": profile
                        })
        except Exception as e:
            print(f"[TextModelManager] Error consultando tags de Ollama: {e}")

        return models

    @classmethod
    def list_local_file_models(cls, search_paths: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Escanea directorios locales en busca de:
        1. Modelos en almacén de Ollama (manifests JSON) en carpetas personalizadas.
        2. Archivos directos .gguf o checkpoints de texto.
        """
        models: List[Dict[str, Any]] = []
        paths_to_check = search_paths or [
            cls.get_custom_llm_path(),
            "e:\\modelosLLM",
            os.path.join(get_app_dir(), "models", "llm"),
            os.path.expanduser("~/.ollama/models")
        ]

        seen_ids = set()

        for base_path in paths_to_check:
            if not base_path or not os.path.isdir(base_path):
                continue

            # 1. Escanear almacén de manifiestos de Ollama (ej. base_path/manifests)
            manifests_root = os.path.join(base_path, "manifests")
            if os.path.isdir(manifests_root):
                for root, _, files in os.walk(manifests_root):
                    for f in files:
                        manifest_file = os.path.join(root, f)
                        try:
                            # Estructura típica: manifests/registry.ollama.ai/library/<model_name>/<tag>
                            rel_parts = os.path.normpath(os.path.relpath(manifest_file, manifests_root)).split(os.sep)
                            if len(rel_parts) >= 2:
                                model_name = rel_parts[-2]
                                tag = rel_parts[-1]
                                model_id = f"{model_name}:{tag}"
                                if model_id in seen_ids:
                                    continue

                                with open(manifest_file, "r", encoding="utf-8") as mf:
                                    mdata = json.load(mf)

                                layers = mdata.get("layers", [])
                                size_bytes = sum(layer.get("size", 0) for layer in layers)
                                size_gb = round(size_bytes / (1024 ** 3), 2)
                                has_projector = any(
                                    "projector" in l.get("mediaType", "").lower()
                                    or "clip" in l.get("from", "").lower()
                                    or "vision" in l.get("from", "").lower()
                                    for l in layers
                                )

                                core = cls.detect_model_core(model_name)
                                is_vision = has_projector or core == "llava" or "vision" in model_name.lower()
                                profile = cls.get_model_profile(model_id)

                                seen_ids.add(model_id)
                                models.append({
                                    "id": model_id,
                                    "name": profile.get("custom_name", f"{model_name.capitalize()} {tag.upper()}"),
                                    "source": "local_ollama_store",
                                    "parameters": tag.upper(),
                                    "quantization": "GGUF",
                                    "size_gb": size_gb,
                                    "core": profile.get("core", core),
                                    "detected_core": core,
                                    "is_vision": is_vision,
                                    "status": "ready",
                                    "settings": profile
                                })
                        except Exception:
                            continue

            # 2. Escanear archivos directos .gguf y .bin
            for root, _, files in os.walk(base_path):
                # Saltar subcarpeta de manifests ya analizada
                if "manifests" in root.lower() or "blobs" in root.lower():
                    continue
                for f in files:
                    if f.lower().endswith((".gguf", ".bin")):
                        full_path = os.path.join(root, f)
                        model_id = f"local:{f}"
                        if model_id in seen_ids:
                            continue

                        try:
                            size_gb = round(os.path.getsize(full_path) / (1024 ** 3), 2)
                        except OSError:
                            size_gb = 0.0

                        core = cls.detect_model_core(f)
                        profile = cls.get_model_profile(model_id)
                        seen_ids.add(model_id)

                        models.append({
                            "id": model_id,
                            "name": profile.get("custom_name", f.replace(".gguf", "").replace(".bin", "")),
                            "source": "local_file",
                            "path": full_path,
                            "parameters": "GGUF Local",
                            "quantization": "GGUF",
                            "size_gb": size_gb,
                            "core": profile.get("core", core),
                            "detected_core": core,
                            "is_vision": "vision" in f.lower() or "llava" in f.lower(),
                            "status": "ready",
                            "settings": profile
                        })

        return models

    @classmethod
    def get_all_available_models(cls) -> List[Dict[str, Any]]:
        """
        Retorna la unión deduplicada de modelos disponibles (Ollama + almacén local + GGUF).
        """
        models_dict: Dict[str, Dict[str, Any]] = {}

        # 1. Modelos reportados por Ollama si está en línea
        if cls.is_ollama_available():
            for m in cls.list_ollama_models():
                models_dict[m["id"]] = m

        # 2. Modelos locales encontrados en el disco / almacén configurado
        for m in cls.list_local_file_models():
            if m["id"] not in models_dict:
                models_dict[m["id"]] = m
            else:
                models_dict[m["id"]]["local_synced"] = True

        models = list(models_dict.values())

        # Fallback informativo si no se detectó ningún modelo aún
        if not models:
            models.append({
                "id": "llama-3.2:3b",
                "name": "Llama 3.2 3B Instruct (Ollama Requerido)",
                "source": "ollama",
                "parameters": "3B",
                "quantization": "Q4_K_M",
                "size_gb": 2.0,
                "core": "llama3",
                "detected_core": "llama3",
                "is_vision": False,
                "status": "unavailable",
                "settings": cls.get_model_profile("llama-3.2:3b")
            })

        return models
