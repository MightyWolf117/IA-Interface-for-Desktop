import io
import os
import sys
import copy
import subprocess
import multiprocessing

# Disable symbolic links on Windows for Hugging Face Hub to ensure standard file copies
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

# ==============================================================================
# WINDOWS WINDOWLESS / NOCONSOLE STREAM SAFEGUARD
# When running as a GUI application, with CREATE_NO_WINDOW, or in PyInstaller
# windowless mode, sys.stdout and sys.stderr are initialized as None.
# This causes Uvicorn's ColourizedFormatter to crash with:
#   AttributeError: 'NoneType' object has no attribute 'isatty'
# ==============================================================================
class SafeStream(io.StringIO):
    def __init__(self, log_filepath=None, target_stream=None):
        super().__init__()
        self.target = target_stream
        self.log_filepath = log_filepath
        self._file = None
        if log_filepath:
            try:
                os.makedirs(os.path.dirname(log_filepath), exist_ok=True)
                self._file = open(log_filepath, "a", encoding="utf-8", buffering=1)
            except Exception:
                self._file = None

    def isatty(self):
        if self.target and hasattr(self.target, "isatty"):
            try:
                return self.target.isatty()
            except Exception:
                return False
        return False

    def write(self, s):
        if not s:
            return 0
        if self.target and hasattr(self.target, "write"):
            try:
                self.target.write(s)
            except Exception:
                pass
        if self._file:
            try:
                self._file.write(s)
            except Exception:
                pass
        return len(s)

    def flush(self):
        if self.target and hasattr(self.target, "flush"):
            try:
                self.target.flush()
            except Exception:
                pass
        if self._file:
            try:
                self._file.flush()
            except Exception:
                pass

# Determine a user-writable path for logging
log_dir = os.path.join(
    os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or os.path.expanduser("~"),
    "CYBER-IA",
    "logs"
)
log_file = os.path.join(log_dir, "backend.log")

if sys.stdout is None or not hasattr(sys.stdout, "isatty"):
    sys.stdout = SafeStream(log_filepath=log_file, target_stream=sys.stdout)
if sys.stderr is None or not hasattr(sys.stderr, "isatty"):
    sys.stderr = SafeStream(log_filepath=log_file, target_stream=sys.stderr)
if sys.stdin is None:
    sys.stdin = io.StringIO()

is_frozen = getattr(sys, "frozen", False)

if is_frozen:
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.executable)))
    # Register DLL search paths on Windows for PyTorch & CUDA C-extensions (Python 3.8+)
    if sys.platform == "win32":
        candidate_dll_dirs = [
            base_dir,
            os.path.join(base_dir, "_internal"),
            os.path.join(base_dir, "torch", "lib"),
            os.path.join(base_dir, "_internal", "torch", "lib"),
        ]
        for d in candidate_dll_dirs:
            if os.path.isdir(d):
                try:
                    os.add_dll_directory(d)
                except Exception:
                    pass
                os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
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
    
    # Sanitize Windows Hugging Face Hub symlinks into real files to avoid model loading errors
    try:
        from app.core.paths import sanitize_hf_cache
        fixed_links = sanitize_hf_cache()
        if fixed_links > 0:
            print(f"[CYBER-IA] Se sanearon {fixed_links} enlaces simbólicos en la caché de Hugging Face.")
    except Exception as e:
        print(f"[CYBER-IA] Aviso comprobando caché Hugging Face: {e}")

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

    # Setup safe logging configuration without colourized isatty dependency
    log_config = copy.deepcopy(uvicorn.config.LOGGING_CONFIG)
    if "formatters" in log_config:
        if "default" in log_config["formatters"]:
            log_config["formatters"]["default"]["use_colors"] = False
        if "access" in log_config["formatters"]:
            log_config["formatters"]["access"]["use_colors"] = False

    print("[CYBER-IA] Iniciando Backend FastAPI en http://127.0.0.1:8000...")
    # reload=False ensures clean PyTorch CUDA contexts on Windows without child spawn conflicts
    reload_opt = ("--reload" in sys.argv) and (not is_frozen)
    if reload_opt:
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, log_config=log_config)
    else:
        from app.main import app
        uvicorn.run(app, host="127.0.0.1", port=8000, log_config=log_config)

