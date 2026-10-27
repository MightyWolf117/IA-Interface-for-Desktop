"""
CYBER-IA // Automated Backend Compilation Script
Builds the FastAPI backend with PyInstaller and deploys it to the Tauri resource directory.
"""

import os
import sys
import shutil
import subprocess

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.join(root_dir, "backend")
    tauri_resources_dir = os.path.join(root_dir, "interface", "src-tauri", "resources", "api")

    print("[BUILD] Iniciando compilación de la API de CYBER-IA...")
    print(f"[BUILD] Directorio del Backend: {backend_dir}")
    print(f"[BUILD] Destino de Recursos Tauri: {tauri_resources_dir}")

    spec_path = os.path.join(backend_dir, "cyber-ia-api.spec")
    if not os.path.exists(spec_path):
        print(f"[ERROR] No se encontró el archivo spec: {spec_path}")
        sys.exit(1)

    # Ejecutar PyInstaller
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        spec_path,
    ]
    print(f"[BUILD] Ejecutando: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=backend_dir)
    if result.returncode != 0:
        print("[ERROR] Falló la compilación de PyInstaller.")
        sys.exit(result.returncode)

    dist_dir = os.path.join(backend_dir, "dist", "cyber-ia-api")
    if not os.path.exists(dist_dir):
        print(f"[ERROR] No se generó la carpeta dist: {dist_dir}")
        sys.exit(1)

    # Desplegar al directorio de recursos de Tauri
    if os.path.exists(tauri_resources_dir):
        print(f"[BUILD] Limpiando carpeta de recursos previa: {tauri_resources_dir}")
        shutil.rmtree(tauri_resources_dir)

    print(f"[BUILD] Copiando distribución compilada a: {tauri_resources_dir}")
    shutil.copytree(dist_dir, tauri_resources_dir)
    print("[BUILD] ¡API compilada e integrada en los recursos de Tauri exitosamente!")

if __name__ == "__main__":
    main()
