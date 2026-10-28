"""
CYBER-IA // File System & Path Management
Resolves user-writable directories for runtime outputs and assets,
preventing PermissionError when installed in protected system paths (e.g. Program Files).
"""

import os
import sys


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
