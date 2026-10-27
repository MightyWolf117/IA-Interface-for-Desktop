import os
import sys
import subprocess
import multiprocessing

is_frozen = getattr(sys, "frozen", False)

if is_frozen:
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(base_dir, ".venv")
    venv_scripts = os.path.join(venv_dir, "Scripts")
    venv_python = os.path.join(venv_scripts, "python.exe")

    # Auto-redirect to backend/.venv if executed with global Python
    if os.path.exists(venv_python) and os.path.abspath(sys.executable).lower() != os.path.abspath(venv_python).lower():
        env = os.environ.copy()
        env["VIRTUAL_ENV"] = venv_dir
        env["PATH"] = venv_scripts + os.pathsep + env.get("PATH", "")
        print(f"[CYBER-IA] Detectada ejecución con Python global ({sys.executable}).")
        print(f"[CYBER-IA] Re-ejecutando con el entorno virtual del proyecto: {venv_python}")
        sys.exit(subprocess.call([venv_python] + sys.argv, env=env))

    # Ensure venv and base paths for all child processes and threads
    os.environ["VIRTUAL_ENV"] = venv_dir
    if not os.environ.get("PATH", "").startswith(venv_scripts):
        os.environ["PATH"] = venv_scripts + os.pathsep + os.environ.get("PATH", "")

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# CRITICAL FOR WINDOWS MULTIPROCESSING:
# Force child worker processes to use the venv python executable, preventing fallback to global python
multiprocessing.set_executable(sys.executable)
if hasattr(sys, "_base_executable"):
    sys._base_executable = sys.executable

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # Import app components inside venv
    try:
        from app.core.hardware import HardwareDetector
        gpu_info = HardwareDetector.get_gpu_info()
        if gpu_info.get("available"):
            print(f"[CYBER-IA] GPU Detectada: {gpu_info['name']} | VRAM Total: {gpu_info['vram_total_mb']} MB")
            print(f"[CYBER-IA] Umbrales: Ahorro (<=40%): {gpu_info['thresholds_mb']['ahorro_40']} MB | Equilibrado (<=65%): {gpu_info['thresholds_mb']['equilibrado_65']} MB")
        else:
            print("[CYBER-IA] GPU CUDA no detectada. Operando en modo CPU.")
    except Exception as e:
        print(f"[CYBER-IA] Nota telemetría inicial: {e}")

    import uvicorn
    print("[CYBER-IA] Iniciando Backend FastAPI en http://127.0.0.1:8000...")
    # reload=False ensures clean PyTorch CUDA contexts on Windows without child spawn conflicts
    reload_opt = ("--reload" in sys.argv) and (not is_frozen)
    if reload_opt:
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
    else:
        from app.main import app
        uvicorn.run(app, host="127.0.0.1", port=8000)

