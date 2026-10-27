use std::net::TcpStream;
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::{Manager, RunEvent};

#[cfg(windows)]
use std::os::windows::process::CommandExt;

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;

pub struct BackendState(pub Arc<Mutex<Option<Child>>>);

/// Comprueba si el servidor FastAPI ya está escuchando en el puerto 8000
fn is_backend_alive() -> bool {
    TcpStream::connect_timeout(
        &"127.0.0.1:8000".parse().unwrap(),
        Duration::from_millis(400),
    )
    .is_ok()
}

/// Localiza la carpeta `backend` en entornos de desarrollo o empaquetados
fn find_backend_dir() -> Option<PathBuf> {
    // 1. Relativo al directorio de trabajo actual
    if let Ok(cwd) = std::env::current_dir() {
        let candidates = [
            cwd.join("../backend"),
            cwd.join("backend"),
            cwd.join("../../backend"),
        ];
        for c in &candidates {
            if c.join("run.py").exists() {
                if let Ok(canonical) = c.canonicalize() {
                    return Some(canonical);
                }
                return Some(c.clone());
            }
        }
    }

    // 2. Relativo al ejecutable actual
    if let Ok(exe) = std::env::current_exe() {
        let mut cur = exe.parent();
        for _ in 0..6 {
            if let Some(p) = cur {
                let candidate = p.join("backend");
                if candidate.join("run.py").exists() {
                    if let Ok(canonical) = candidate.canonicalize() {
                        return Some(canonical);
                    }
                    return Some(candidate);
                }
                cur = p.parent();
            } else {
                break;
            }
        }
    }

    None
}

/// Encuentra el intérprete de Python óptimo (priorizando el entorno .venv del backend)
fn find_python_executable(backend_dir: &Path) -> PathBuf {
    #[cfg(windows)]
    {
        let venv_python = backend_dir.join(".venv").join("Scripts").join("python.exe");
        if venv_python.exists() {
            return venv_python;
        }
    }

    #[cfg(not(windows))]
    {
        let venv_python = backend_dir.join(".venv").join("bin").join("python");
        if venv_python.exists() {
            return venv_python;
        }
    }

    // Fallback al comando del sistema
    PathBuf::from("python")
}

/// Termina limpiamente el proceso hijo del backend y todo su árbol de procesos
fn terminate_backend_child(child: &mut Child) {
    let pid = child.id();
    println!("[CYBER-IA Rust] Terminando árbol de procesos del backend (PID: {})...", pid);

    #[cfg(windows)]
    {
        let _ = Command::new("taskkill")
            .args(["/PID", &pid.to_string(), "/T", "/F"])
            .creation_flags(CREATE_NO_WINDOW)
            .output();
    }

    #[cfg(not(windows))]
    {
        let _ = child.kill();
    }

    let _ = child.wait();
    println!("[CYBER-IA Rust] Backend terminado exitosamente.");
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
fn check_backend_status() -> bool {
    is_backend_alive()
}

#[tauri::command]
fn kill_backend_process(state: tauri::State<BackendState>) -> Result<String, String> {
    if let Ok(mut lock) = state.0.lock() {
        if let Some(mut child) = lock.take() {
            let pid = child.id();
            terminate_backend_child(&mut child);
            return Ok(format!("Backend PID {} terminado.", pid));
        }
    }
    Ok("No había proceso de backend administrado por esta instancia.".to_string())
}

enum BackendTarget {
    CompiledBinary(PathBuf),
    PythonScript {
        python: PathBuf,
        script: PathBuf,
        cwd: PathBuf,
    },
}

/// Resuelve el mecanismo de ejecución del backend:
/// 1. Binario compilado empaquetado (Modo Instalador / Producción)
/// 2. Script Python con entorno virtual (Modo Desarrollo local)
fn resolve_backend(app: &tauri::App) -> Option<BackendTarget> {
    // 1. Buscar binario compilado empaquetado en el directorio de recursos oficial de Tauri
    if let Ok(res_dir) = app.path().resource_dir() {
        let binary_candidates = [
            res_dir.join("api").join("cyber-ia-api.exe"),
            res_dir.join("cyber-ia-api.exe"),
            res_dir.join("resources").join("api").join("cyber-ia-api.exe"),
            res_dir.join("api").join("cyber-ia-api"),
            res_dir.join("cyber-ia-api"),
        ];
        for b in &binary_candidates {
            if b.is_file() {
                println!("[CYBER-IA Rust] Binario empaquetado de API localizado en resource_dir: {:?}", b);
                return Some(BackendTarget::CompiledBinary(b.clone()));
            }
        }
    }

    // 2. Buscar binario compilado relativo al ejecutable principal
    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            let exe_candidates = [
                exe_dir.join("cyber-ia-api.exe"),
                exe_dir.join("api").join("cyber-ia-api.exe"),
                exe_dir.join("resources").join("api").join("cyber-ia-api.exe"),
                exe_dir.join("resources").join("cyber-ia-api.exe"),
                exe_dir.join("cyber-ia-api"),
            ];
            for b in &exe_candidates {
                if b.is_file() {
                    println!("[CYBER-IA Rust] Binario empaquetado de API localizado junto al ejecutable: {:?}", b);
                    return Some(BackendTarget::CompiledBinary(b.clone()));
                }
            }
        }
    }

    // 3. Fallback a modo de desarrollo local (backend/run.py con entorno .venv o python del sistema)
    if let Some(backend_dir) = find_backend_dir() {
        let python_exe = find_python_executable(&backend_dir);
        let script = backend_dir.join("run.py");
        println!("[CYBER-IA Rust] Modo desarrollo: usando script Python {:?}", script);
        return Some(BackendTarget::PythonScript {
            python: python_exe,
            script,
            cwd: backend_dir,
        });
    }

    None
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let backend_child: Arc<Mutex<Option<Child>>> = Arc::new(Mutex::new(None));
    let backend_child_setup = Arc::clone(&backend_child);

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(BackendState(backend_child))
        .invoke_handler(tauri::generate_handler![
            greet,
            check_backend_status,
            kill_backend_process
        ])
        .setup(move |app| {
            // 1. Si el backend ya está corriendo externamente, lo reutilizamos
            if is_backend_alive() {
                println!("[CYBER-IA Rust] Backend FastAPI detectado activo en 127.0.0.1:8000. Reutilizando instancia existente.");
                return Ok(());
            }

            // 2. Si no está corriendo, resolvemos y arrancamos el backend subordinado
            if let Some(target) = resolve_backend(app) {
                let mut cmd = match &target {
                    BackendTarget::CompiledBinary(bin_path) => {
                        println!("[CYBER-IA Rust] Iniciando binario de API empaquetado: {:?}", bin_path);
                        let mut c = Command::new(bin_path);
                        if let Some(parent) = bin_path.parent() {
                            c.current_dir(parent);
                        }
                        c
                    }
                    BackendTarget::PythonScript { python, script, cwd } => {
                        println!("[CYBER-IA Rust] Iniciando API en modo desarrollo: {:?} {:?}", python, script);
                        let mut c = Command::new(python);
                        c.arg(script).current_dir(cwd);
                        c
                    }
                };

                #[cfg(windows)]
                cmd.creation_flags(CREATE_NO_WINDOW);

                match cmd.spawn() {
                    Ok(child) => {
                        println!("[CYBER-IA Rust] Proceso backend FastAPI subordinado iniciado con éxito (PID: {}).", child.id());
                        if let Ok(mut lock) = backend_child_setup.lock() {
                            *lock = Some(child);
                        }
                    }
                    Err(e) => {
                        eprintln!("[CYBER-IA Rust] Error al iniciar subproceso del backend: {}", e);
                    }
                }
            } else {
                eprintln!("[CYBER-IA Rust] Advertencia: No se localizó ni el binario empaquetado de la API ni la carpeta 'backend/'.");
            }

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("Error al construir la aplicación Tauri")
        .run(|app_handle, event| {
            // Al cerrarse la ventana o solicitarse salir, cerramos el backend hijo
            if let RunEvent::ExitRequested { .. } | RunEvent::Exit = event {
                println!("[CYBER-IA Rust] Cerrando aplicación: terminando backend subordinado...");
                let state = app_handle.state::<BackendState>();
                if let Ok(mut lock) = state.0.lock() {
                    if let Some(mut child) = lock.take() {
                        terminate_backend_child(&mut child);
                    }
                }
            }
        });
}
