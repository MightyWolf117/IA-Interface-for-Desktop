"""
CYBER-IA // File System & Path Management
Resolves user-writable directories for runtime outputs and assets,
preventing PermissionError when installed in protected system paths (e.g. Program Files).
"""

import os
import sys
import shutil
from typing import Optional


def get_outputs_dir() -> str:
    """
    Obtiene y asegura la existencia del directorio de salidas (outputs) para imágenes generadas.

    Estrategia de resolución:
    1. Si está en desarrollo local (no frozen) y la carpeta local de la raíz del repo es escribible:
       usa '<repo_root>/outputs'.
    2. Si está en modo empaquetado (PyInstaller / Program Files) o la carpeta local no es escribible:
       usa la carpeta de Imágenes del usuario ('%USERPROFILE%/Pictures/CYBER-IA').
    3. Fallback a '%LOCALAPPDATA%/CYBER-IA/outputs'.
    """
    # 1. Entorno de desarrollo local (código fuente no congelado)
    if not getattr(sys, "frozen", False):
        try:
            repo_outputs = os.path.abspath(
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    "outputs"
                )
            )
            os.makedirs(repo_outputs, exist_ok=True)
            test_file = os.path.join(repo_outputs, ".perm_test")
            with open(test_file, "w") as f:
                f.write("ok")
            os.remove(test_file)
            return repo_outputs
        except (PermissionError, OSError):
            pass

    # 2. Carpeta de Imágenes del usuario (~/Pictures/CYBER-IA)
    user_home = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    pictures_dir = os.path.join(user_home, "Pictures", "CYBER-IA")
    try:
        os.makedirs(pictures_dir, exist_ok=True)
        test_file = os.path.join(pictures_dir, ".perm_test")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        return pictures_dir
    except (PermissionError, OSError):
        pass

    # 3. Fallback a LocalAppData (%LOCALAPPDATA%/CYBER-IA/outputs)
    local_app_data = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or user_home
    fallback_dir = os.path.join(local_app_data, "CYBER-IA", "outputs")
    os.makedirs(fallback_dir, exist_ok=True)
    return fallback_dir


def get_model_config_dir(arch_id: str) -> Optional[str]:
    """
    Retorna la ruta absoluta al directorio de configuraciones offline pre-empaquetadas
    para la arquitectura especificada (sdxl, sd15, etc.).
    Permite cargar modelos .safetensors locales de forma 100% offline sin consultar
    el Hugging Face Hub ni depender de enlaces simbólicos en Windows.
    """
    candidates = []

    # 1. Modo empaquetado (PyInstaller)
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        candidates.append(os.path.join(base_dir, "app", "core", "configs", arch_id))
        candidates.append(os.path.join(base_dir, "_internal", "app", "core", "configs", arch_id))

    # 2. Modo desarrollo relativo a paths.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(current_dir, "configs", arch_id))

    for c in candidates:
        if os.path.isdir(c) and os.path.isfile(os.path.join(c, "model_index.json")):
            return c
    return None


def sanitize_hf_cache() -> int:
    """
    Inspecciona la caché de Hugging Face en Windows y convierte cualquier enlace simbólico
    (NTFS relative symlink) a archivos concretos con su contenido original.
    Evita fallos 'Error no file named model_index.json' cuando los procesos de Tauri o
    PyInstaller se ejecutan sin elevación o con políticas restrictivas de symlinks.
    """
    hf_home = os.environ.get("HF_HOME") or os.path.join(
        os.environ.get("USERPROFILE") or os.path.expanduser("~"),
        ".cache",
        "huggingface",
        "hub"
    )
    if not os.path.isdir(hf_home):
        return 0

    converted = 0
    try:
        for root, _, files in os.walk(hf_home):
            for f in files:
                fp = os.path.join(root, f)
                if os.path.islink(fp):
                    try:
                        target = os.path.realpath(fp)
                        if os.path.exists(target):
                            os.remove(fp)
                            shutil.copyfile(target, fp)
                            converted += 1
                    except Exception:
                        pass
    except Exception as e:
        print(f"[sanitize_hf_cache] Aviso durante saneamiento: {e}")

    return converted

