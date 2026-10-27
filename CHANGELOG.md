# Changelog - IA Interface for Desktop

Todas las modificaciones notables realizadas en este proyecto serán documentadas en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

## [1.0.0] - 2026-10-27

### Added

- **Backend (FastAPI)**:
  - Inicialización del entorno virtual Python (`.venv`) y definición estricta de dependencias en [requirements.txt](backend/requirements.txt).
  - Estructuración modular en `backend/app` con separación de esquemas, rutas y configuración de servidor.
  - Creación de esquemas Pydantic en [chat.py](backend/app/schemas/chat.py) para `ChatMessage`, `ChatRequest`, `ChatResponse`, `ModelInfo` y `HealthResponse`.
  - Implementación de rutas API en [routes.py](backend/app/api/routes.py):
    - `GET /api/v1/health`: Comprobación de estado y disponibilidad del servicio.
    - `GET /api/v1/models`: Catálogo de modelos locales disponibles.
    - `POST /api/v1/chat`: Endpoint de inferencia y completado de chat.
  - Configuración de FastAPI con soporte CORS para la aplicación de escritorio Tauri en [main.py](backend/app/main.py).
  - Script de arranque directo [run.py](backend/run.py) con Uvicorn en puerto 8000.
  - Documentación detallada en [backend/README.md](backend/README.md).

- **Frontend (Tauri v2 + Cyberpunk Neon UI)**:
  - Andamiaje de proyecto Tauri v2 en [interface/](interface/).
  - Configuración de ventana de escritorio (1280x840, tema oscuro) en [tauri.conf.json](interface/src-tauri/tauri.conf.json).
  - Maquetación HUD Cyberpunk con estética de neón en [index.html](interface/src/index.html).
  - Sistema de diseño de neón cyberpunk en [styles.css](interface/src/styles.css) (brillos cian, magenta, ámbar, verde, esquinas recortadas, scanlines opcionales, cuadrícula holográfica, animaciones de ondas de audio y telemetría de hardware).
  - Lógica interactiva en [main.js](interface/src/main.js) con enlace IPC nativo a Rust mediante `window.__TAURI__.core.invoke("greet")`, selector de temas de acento, reloj cibernético en tiempo real, gestión de canales y simulación de flujo de prompts.

- **Motor de Difusión y Optimización de Memoria (Backend)**:
  - Instalación y vinculación de PyTorch con soporte nativo CUDA 12.4 (RTX 3050 6GB) y librerías `diffusers`, `transformers`, `accelerate`, `safetensors`, `psutil`, `websockets` en [requirements.txt](backend/requirements.txt).
  - Implementación del detector de hardware en [hardware.py](backend/app/core/hardware.py) calculando umbrales de VRAM dinámicos en tiempo de ejecución:
    - Modo Ahorro: <= 40% VRAM (~2.4 GB) con `enable_sequential_cpu_offload` y `enable_attention_slicing`.
    - Modo Equilibrado: <= 65% VRAM (~4.0 GB) con `enable_model_cpu_offload`.
    - Modo Alto Rendimiento: Hasta 100% VRAM (6.1 GB) sin offload.
  - Implementación del motor modular de difusión en [diffusion_engine.py](backend/app/services/diffusion_engine.py) con soporte para:
    - Carga de checkpoints locales (`.safetensors`, `.ckpt`) y modelos de Hugging Face.
    - Componentes auxiliares (adaptadores LoRA con ajuste de peso 0.0 - 2.0, planificadores Schedulers EulerA, DPM++ 2M Karras, DDIM, UniPC).
    - Salida dual configurable: Base64 en memoria (renderizado instantáneo) o Guardado en disco en `outputs/` con URL estática.
    - Descarga total del modelo con vaciado de caché VRAM (`torch.cuda.empty_cache()` y `gc.collect()`).
  - Escáner inteligente de modelos en [model_scanner.py](backend/app/services/model_scanner.py) que detecta recursivamente modelos base y auxiliares en cualquier directorio local indicado por el usuario.
  - Servicio de telemetría por WebSocket (<80ms) en [diffusion_routes.py](backend/app/api/diffusion_routes.py) para transmisión de métricas de hardware a 15-20 FPS y progreso de inferencia paso a paso.
  - Middleware de diagnóstico y Panel de Control del API en [api_tracker.py](backend/app/core/api_tracker.py) registrando puertos abiertos (8000, 1420), endpoints y registro en tiempo real de códigos HTTP y tiempos de respuesta.

- **Estudio Multimedia y Panel de Diagnóstico (Frontend Tauri v2)**:
  - Sistema de navegación por pestañas en [index.html](interface/src/index.html): `DIFUSIÓN IA`, `CHAT LLM` y `API CONTROL`.
  - Estudio de Generación Multimedia con matriz de prompt positivo/negativo, presets rápidos (#CYBER_CITY, #MECH_WARRIOR), selectores de dimensiones (512x512, 768x768, 1024x1024), controles deslizantes de Steps/CFG/Semilla, lienzo de imagen con marco de neón, inspector de metadatos y descarga directa.
  - Barra de progreso de inferencia en tiempo real conectada al canal WebSocket.
  - Modal de configuración y escaneo de modelos:
    - Selector y explorador de rutas de disco con detección dinámica de subcarpetas.
    - Conmutador de perfil de memoria según umbrales de VRAM/RAM.
    - Conmutador de formato de transferencia (Base64 vs Disco) con descripciones explicativas.
    - Inyección de adaptadores LoRA y Schedulers.
  - Panel de Control del API en la interfaz mostrando puertos del sistema, tabla de rutas y terminal interactivo de solicitudes HTTP con códigos de estado coloreados.

- **Refactorización Modular de la Interfaz & Sistema de Alerta de Límites Críticos**:
  - Desacoplamiento de la arquitectura monolítica del frontend en módulos especializados e independientes:
    - **CSS Modular (`interface/src/css/`)**:
      - [variables.css](interface/src/css/variables.css): Paletas de colores neón, tokens de brillo y tipografías.
      - [base.css](interface/src/css/base.css): Resets, cuadrícula holográfica, botones y capas de scanlines.
      - [header.css](interface/src/css/header.css): HUD superior, branding, selectores de modo y reloj cibernético.
      - [diffusion.css](interface/src/css/diffusion.css): Controles de estudio, canvas multimedia y barra de progreso.
      - [chat.css](interface/src/css/chat.css): Barra lateral de canales y feed de mensajes.
      - [api-control.css](interface/src/css/api-control.css): Diagnóstico de puertos, rutas y consola de llamadas HTTP.
      - [modal.css](interface/src/css/modal.css): Modal de configuración, tarjetas de memoria y formatos de salida.
      - [alerts.css](interface/src/css/alerts.css): Estilos visuales del banner de emergencia Cyberpunk con efectos de parpadeo y botones de mitigación.
      - [styles.css](interface/src/styles.css): Manifiesto de importación centralizado y ultraligero (426 bytes).
    - **JavaScript Modular ES Modules (`interface/src/js/`)**:
      - [config.js](interface/src/js/config.js): Endpoints de API y puente seguro de invocación IPC nativo de Tauri v2.
      - [alerts.js](interface/src/js/alerts.js): Monitor de seguridad de recursos que evalúa continuamente el consumo en tiempo real. Activa automáticamente un banner de alerta crítica si la VRAM supera el 88% o la RAM del sistema supera el 90%, ofreciendo mitigación inmediata con 1 clic ("PURGAR VRAM AHORA" o "ACTIVAR MODO AHORRO").
      - [telemetry.js](interface/src/js/telemetry.js): Cliente WebSocket de telemetría de hardware (<80ms) y barra de progreso de pasos.
      - [ui.js](interface/src/js/ui.js): Controlador de reloj en tiempo real, selector de acentos neón y alternador de pestañas.
      - [model_modal.js](interface/src/js/model_modal.js): Controlador del modal de escaneo de carpetas y carga dinámica de modelos/LoRAs.
      - [diffusion.js](interface/src/js/diffusion.js): Controlador del estudio de difusión, parámetros de inferencia y renderizado en canvas.
      - [chat.js](interface/src/js/chat.js): Gestión de mensajes y prompts del modo de conversación LLM.
      - [api_control.js](interface/src/js/api_control.js): Controlador del visor de puertos y terminal de solicitudes en tiempo real.
      - [main.js](interface/src/main.js): Orquestador principal modular, limpio y ligero (1.1 KB).

- **Configuración del Repositorio & Alineación de Versión (v1.0.0)**:
  - Actualización de [.gitignore](.gitignore) con reglas para Python (`.venv`, `__pycache__`), Node (`node_modules`) y Rust/Tauri (`target`).
  - Estandarización de metadatos de versión `1.0.0` y nombres de paquete unificados en toda la pila tecnológica:
    - Backend: `FastAPI` (título `CYBER-IA Desktop Core API`, versión `1.0.0` en `main.py` y `routes.py`).
    - Frontend Node: `package.json` (`cyber-ia-desktop`, versión `1.0.0`).
    - Contenedor Nativo: `tauri.conf.json` (`productName: "CYBER-IA"`, `version: "1.0.0"`, `identifier: "com.mightywolf.cyberia"`).
    - Crate Rust: `Cargo.toml` (`name = "cyber-ia"`, `version = "1.0.0"`, `authors = ["MightyWolf117"]`).
    - HUD Branding: `index.html` exhibe `NEURAL DESKTOP v1.0.0 // TAURI v2`.

- **Motor Multi-Arquitectura para Difusión (`backend/app/services/architectures/`)**:
  - Implementación del patrón Adapter para soporte desacoplado, modular y extensible de múltiples arquitecturas de IA generativa:
    - [base.py](backend/app/services/architectures/base.py): Contrato abstracto `BaseModelAdapter` que define el ciclo de vida estándar (`can_handle`, `load`, `generate`, `get_metadata`).
    - [sd15.py](backend/app/services/architectures/sd15.py): Adaptador `SD15Adapter` para Stable Diffusion 1.5 y 2.1 (checkpoints monolíticos `.safetensors`, `.ckpt` y repositorios Hugging Face como `runwayml/stable-diffusion-v1-5`, `stabilityai/sd-turbo`), conmutación de schedulers (EulerA, DPM++, DDIM, UniPC) y perfiles de memoria automáticos.
    - [sdxl.py](backend/app/services/architectures/sdxl.py): Adaptador `SDXLAdapter` para Stable Diffusion XL, Pony y modelos compactos derivados (`segmind/SSD-1B`), con parámetros recomendados de 1024x1024 y gestión de VRAM.
    - [anima.py](backend/app/services/architectures/anima.py): Adaptador `AnimaDiTAdapter` para modelos Diffusion Transformer modulares (DiT 2B Cosmos con Qwen text encoder y Cosmos VAE, como `reedAnimaFurry_v12` y `circlestone-labs/Anima-Base-v1.0-Diffusers`):
      - Detección e inspección quirúrgica de pesos distribuidos en subcarpetas locales (`.safetensors` transformer DiT, `_txt.safetensors` Qwen text encoder, `_vae.safetensors` Cosmos/Qwen VAE).
      - Mapeo y conversión automática de tensores de Cosmos DiT (`convert_cosmos_transformer_checkpoint_to_diffusers`) e inyección aislada del adaptador LLM (`AnimaTextConditioner`).
      - Carga perezosa de componentes base (`ModularPipeline`, tokenizers Qwen/T5, guider de atención cruzada, scheduler) con reutilización de caché sin descargas duplicadas.
      - Inferencia en precisión nativa `torch.bfloat16` optimizada para tarjetas con 6 GB de VRAM (NVIDIA RTX 3050).
    - [auto_diffusers.py](backend/app/services/architectures/auto_diffusers.py): Adaptador genérico `AutoDiffusersAdapter` como respaldo universal para cualquier pipeline estándar de Hugging Face.
    - [registry.py](backend/app/services/architectures/registry.py): Registro centralizado `ArchitectureRegistry` que evalúa rutas y formatos por orden de prioridad declarativa y despacha dinámicamente al adaptador óptimo.
  - Actualización de [model_scanner.py](backend/app/services/model_scanner.py):
    - Detección y consolidación automática de directorios multicomponente (como `reedAnimaFurry_v12`) como un único modelo ejecutable, filtrando archivos auxiliares (`_txt`, `_vae`) para evitar polución en el catálogo de modelos.
    - Asignación automática de tags de arquitectura (`modular_dit`, `sd15`, `sdxl`, `diffusers_auto`) y recomendaciones de resolución y CFG (768x768, CFG 4.0 para Anima).
  - Actualización de [diffusion_engine.py](backend/app/services/diffusion_engine.py):
    - Desacoplamiento total de la lógica de carga e inferencia mediante delegación directa al registro de adaptadores.
    - Registro de arquitectura activa y exposición en tiempo real en los estados de salud (`/status`), carga (`/load`) y generación (`/generate`).
  - Actualización del Frontend Cyberpunk ([index.html](interface/src/index.html), [model_modal.js](interface/src/js/model_modal.js), [diffusion.js](interface/src/js/diffusion.js)):
    - Badge de arquitectura interactivo en la sub-barra HUD superior (`ARCH: ANIMA_DIT`, `ARCH: SD15`, etc.).
    - Cuadro informativo en vivo en el modal de configuración con detalles de arquitectura, descripción técnica y valores recomendados.
    - Auto-actualización de sliders de dimensiones (512x512, 768x768, 1024x1024) y escala CFG al seleccionar o cargar un modelo según su arquitectura recomendada.
    - Etiqueta de arquitectura activa integrada en el inspector de metadatos del canvas multimedia tras cada generación.

- **Gestión Automática del Ciclo de Vida del Backend (Tauri v2 + Rust)**:
  - Implementación del gestor de procesos nativo en Rust ([interface/src-tauri/src/lib.rs](interface/src-tauri/src/lib.rs)):
    - **Arranque en Segundo Plano Automático**: Al abrir la aplicación Tauri, comprueba si el puerto 8000 está activo. Si no lo está, localiza automáticamente el entorno virtual (`backend/.venv/Scripts/python.exe`) y ejecuta `run.py` en segundo plano oculto (`CREATE_NO_WINDOW`), sin abrir ventanas de terminal invasivas.
    - **Cierre y Purga Automática al Salir**: Captura los eventos de cierre de ventana y salida de Tauri (`RunEvent::ExitRequested` / `Exit`) ejecutando la terminación en árbol del subproceso (`taskkill /PID <pid> /T /F` en Windows), eliminando completamente cualquier proceso huérfano de Python o Uvicorn y liberando la memoria VRAM y el puerto 8000 al cerrar la ventana.
    - **Comandos IPC**: Exposición de `check_backend_status` y `kill_backend_process` para control y diagnóstico desde la interfaz.

- **Documentación Especializada, Soporte Bilingüe y Gobernanza Open Source**:
  - Creación del informe de ingeniería y registro de parches [RELEASE_NOTES.md](RELEASE_NOTES.md) con análisis post-mortem de errores, benchmark de consumo de hardware y arquitectura en 6 capas.
  - Creación de la documentación completa en inglés en [README_EN.md](README_EN.md) con selector interactivo de idioma en el encabezado de ambos manuales.
  - Adopción de la licencia de código abierto con Copyleft estricto **GNU General Public License v3.0 (GPL-3.0)** en [LICENSE](LICENSE), garantizando el reconocimiento explícito de la propiedad intelectual de `MightyWolf117` y colaboradores, e imponiendo que cualquier bifurcación, modificación o trabajo derivado deba permanecer como código abierto libre a perpetuidad.
  - Creación de la guía de contribución [CONTRIBUTING.md](CONTRIBUTING.md), estableciendo el flujo de trabajo (forks, ramas semánticas, estándares de código), directrices rigurosas para el reporte de bugs (hardware, modelos, logs), tipificación de aportes aceptados y políticas de **Tolerancia Cero** contra contenido NSFW con menores de edad (CSAM/CSAE), estatutos de Zoofilia/Bestialismo, discurso de odio y amenazas cibernéticas (malware, spyware, miners).
  - Creación del código de conducta comunitario [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) con compromisos de inclusión, prohibiciones explícitas, moderación a cargo de `MightyWolf117` y medidas disciplinarias/legales.
  - Integración de demostración visual con capturas reales de ejecución en la carpeta [media/](media/) (`Generetion_Multimedia.png`, `Multimedia_Menu.png`, `API_Control.png`) embebidas en [README.md](README.md) y [README_EN.md](README_EN.md).
- **Integración Nativa del Ciclo de Vida del Backend (Tauri v2 + Rust)**:
  - Implementación en [interface/src-tauri/src/lib.rs](interface/src-tauri/src/lib.rs) del arranque automático del servidor FastAPI en segundo plano sin desplegar ventanas cmd emergentes invasivas (`CREATE_NO_WINDOW = 0x08000000`).
  - Terminación limpia de subprocesos al cerrar la aplicación de escritorio (`RunEvent::ExitRequested` / `Exit`) ejecutando `taskkill /PID {pid} /T /F` para garantizar que ni FastAPI ni Uvicorn queden como procesos zombis en el sistema.
  - Arquitectura de ejecución dual (`resolve_backend`): detección automática de binario compilado empaquetado (`resources/api/cyber-ia-api.exe`) para el instalador final, con respaldo transparente a modo script (`run.py` con entorno `.venv`) durante el desarrollo local.
- **Personalización Visual de Instaladores y Aceptación Obligatoria de Licencia (NSIS & WiX)**:
  - Configuración en [interface/src-tauri/tauri.conf.json](interface/src-tauri/tauri.conf.json) de pantallas de licencia obligatorias para ambos instaladores mediante [INSTALLER_LICENSE.txt](interface/src-tauri/INSTALLER_LICENSE.txt) e [INSTALLER_LICENSE.rtf](interface/src-tauri/INSTALLER_LICENSE.rtf), forzando al usuario a aceptar la licencia GNU GPLv3 y las políticas de tolerancia cero (menores, zoofilia, odio y malware) antes de proceder con la instalación.
  - Generación e integración de gráficos temáticos Cyberpunk HUD para los instaladores de Windows:
    - Banner lateral para instalador NSIS [icons/nsis_sidebar.bmp](interface/src-tauri/icons/nsis_sidebar.bmp) (164x314) y cabecera horizontal [icons/nsis_header.bmp](interface/src-tauri/icons/nsis_header.bmp) (150x57).
    - Banner superior para instalador WiX [icons/wix_banner.bmp](interface/src-tauri/icons/wix_banner.bmp) (493x58) y diálogo principal [icons/wix_dialog.bmp](interface/src-tauri/icons/wix_dialog.bmp) (493x312).
- **Identidad Visual Oficial e Iconografía Personalizada de CYBER-IA**:
  - Creación del emblema oficial de **CYBER-IA** (cabeza geométrica de lobo cibernético fusionada con núcleo neural de IA, líneas de neón cian/magenta y marco hexagonal sobre fondo obsidiana).
  - Generación de conjunto completo de iconos para Windows, macOS y Web:
    - [interface/src-tauri/icons/icon.ico](interface/src-tauri/icons/icon.ico) multi-resolución (16x16 hasta 256x256) reemplazando el icono predeterminado de Tauri en el ejecutable, barra de tareas de Windows, barra de título y conmutador Alt-Tab.
    - Iconos PNG escalados (`32x32`, `128x128`, `256x256`, `512x512`) y tiles del menú Inicio de Windows.
    - Favicon Web y logotipo interactivo en el HUD superior de la interfaz ([interface/src/index.html](interface/src/index.html) y [interface/src/css/header.css](interface/src/css/header.css)).

### Fixed

- **Resolución de Dependencias en GitHub Actions y Compatibilidad de NumPy**:
  - Se corrigió el fallo de compilación en el runner de GitHub Actions donde `numpy==2.5.2` requería estrictamente Python >= 3.12 mientras el workflow corría sobre 3.11.
  - Se actualizó el entorno de compilación en [.github/workflows/release.yml](.github/workflows/release.yml) y [.github/workflows/ci.yml](.github/workflows/ci.yml) a Python 3.12 nativo.
  - Se flexibilizó la restricción de versión en [backend/requirements.txt](backend/requirements.txt) a `numpy>=1.26.0,<3.0.0` y se inyectó la cabecera `--extra-index-url https://download.pytorch.org/whl/cu124` para resolución automática de PyTorch CUDA en entornos limpios de CI.
- **Detección y Reconocimiento de GPU (NVIDIA RTX 3050 6GB)**:
  - Se corrigió el problema raíz donde la VRAM se mostraba como `0 / 1 MB [0%]`. En Windows con Python 3.13, los procesos trabajadores generados por Uvicorn (`spawn_main`) recurrían a `sys._base_executable` apuntando al Python global (sin PyTorch ni CUDA) en lugar del entorno `.venv`.
  - Se configuró explícitamente `multiprocessing.set_executable(sys.executable)` y `sys._base_executable = sys.executable` en [run.py](backend/run.py), además de inyectar `VIRTUAL_ENV` y `PATH` en el entorno heredado.
  - Se incorporó soporte dual con biblioteca `pynvml` (`nvidia-ml-py`) en [hardware.py](backend/app/core/hardware.py) como vía alternativa directa al driver de NVIDIA.
  - Se actualizó [telemetry.js](interface/src/js/telemetry.js) para mostrar claramente `SIN CUDA (MODO CPU)` cuando no haya GPU disponible en lugar del valor artificial de `1 MB`.
- **Error `name 'Image' is not defined` & Carga de Modelos Públicos**:
  - Se corrigió la importación de Pillow (`PIL.Image`, `ImageDraw`) a nivel de módulo en [diffusion_engine.py](backend/app/services/diffusion_engine.py), previniendo excepciones `NameError` al generar previsualizaciones o imágenes.
  - Se integró `AutoPipelineForText2Image` con bypass de safety checker (`safety_checker=None`, `requires_safety_checker=False` para SD 1.5) y respaldo a `DiffusionPipeline` en [diffusion_engine.py](backend/app/services/diffusion_engine.py), permitiendo la descarga e inicialización correcta de modelos de Hugging Face (`stabilityai/sd-turbo`, `runwayml/stable-diffusion-v1-5`).
  - Se implementó validación estricta de `resp.success` en [model_modal.js](interface/src/js/model_modal.js) con retroalimentación visual de descarga y alertas informativas en caso de fallo.
  - Se migraron las operaciones de carga (`load_model`) y generación (`generate`) a hilos de trabajo asíncronos (`asyncio.to_thread`) en [diffusion_routes.py](backend/app/api/diffusion_routes.py) para que las descargas de modelos no bloqueen el servidor ni desconecten el WebSocket.
- **Selector Nativo de Carpetas de Windows**:
  - Se creó el endpoint `POST /api/v1/system/browse-folder` en [diffusion_routes.py](backend/app/api/diffusion_routes.py) que despliega la ventana nativa del Explorador de Archivos de Windows, con forzado de foco a primer plano (`root.attributes("-topmost", True)`, `root.lift()`) y mecanismo de respaldo automático con PowerShell (`System.Windows.Forms.FolderBrowserDialog`).
  - Se añadió el botón `📁 EXAMINAR...` en el modal de configuración en [index.html](interface/src/index.html) y su controlador en [model_modal.js](interface/src/js/model_modal.js) que rellena la ruta seleccionada y ejecuta el escaneo automáticamente.
- **Carga de Checkpoints Locales (.safetensors / .ckpt) & Inferencia de Modelos DiT Modulares (Anima / Cosmos DiT)**:
  - Se corrigió el fallo `DiffusionPipeline has no attribute 'from_single_file'` en [diffusion_engine.py](backend/app/services/diffusion_engine.py), integrando [StableDiffusionXLPipeline](backend/app/services/diffusion_engine.py) y [StableDiffusionPipeline](backend/app/services/diffusion_engine.py) para cargar modelos monolíticos estándar de Civitai (SD 1.5, SD 2.1, SDXL, Pony).
  - Se implementó la ingeniería inversa del grafo de pesos de Anima / Cosmos DiT en [anima.py](backend/app/services/architectures/anima.py):
    - Corrección de prefijo `model.` para cargar correctamente el codificador de texto Qwen3 en `AutoModel` (310 tensores validados).
    - Separación y desensamble de los 118 tensores del adaptador LLM (`llm_adapter`) y mapeo de los 567 tensores del Transformer 3D Cosmos mediante `convert_cosmos_transformer_checkpoint_to_diffusers`.
    - Inicialización de los tokenizers duales (`tokenizer` y `t5_tokenizer`) requeridos por `_get_qwen_prompt_embeds` eliminando excepciones `TypeError: 'NoneType' object is not callable`.
- **Corrección de `ZeroDivisionError: integer division or modulo by zero` en Atención Sliced**:
  - Se localizó la causa exacta en `SlicedAttnProcessor` de Diffusers (`(batch_size_attention - 1) // self.slice_size`), la cual ocurría al invocar `enable_attention_slicing()` debido a que calculaba `slice_size = 0`.
  - Se eliminó la dependencia de `enable_attention_slicing()` en [diffusion_engine.py](backend/app/services/diffusion_engine.py) permitiendo a PyTorch 2.6 utilizar su atención nativa optimizada SDPA (`torch.nn.functional.scaled_dot_product_attention` / FlashAttention), logrando inferencias 100% estables en ~4.5 segundos en la RTX 3050 sin errores aritméticos.
- **Corrección de Salida en Blanco (`[255, 255, 255]`) en Modelos DiT (Anima / Cosmos DiT)**:
  - **Causa Raíz Identificada**: Los Diffusion Transformers con condicionamiento Qwen (Flow Matching) operan con un rango de Classifier-Free Guidance (CFG) óptimo de **3.5 a 4.5**. Al emplear el valor por defecto de Stable Diffusion 1.5 (`CFG = 7.5`), el cálculo de guía incondicional vs condicional amplifica de forma excesiva los tensores de latentes, saturando la descomposición del VAE y provocando un colapso numérico a blanco absoluto. El efecto se agravaba aún más al ingresar prompts concisos (1-2 palabras) con el negative prompt extenso predeterminado de la UI.
  - **Sincronización en la Interfaz Web / Tauri**: En [model_modal.js](interface/src/js/model_modal.js) se corrigieron los selectores DOM desalineados (`#cfg-slider` en lugar del id previo `#cfg-scale-slider`, y activación programática de los selectores `.dim-pill`), garantizando que al seleccionar o cargar modelos Anima DiT la interfaz se sincronice automáticamente con los valores recomendados: **CFG 4.0**, **25 pasos** y **768x768 píxeles**.
  - **Mecanismo de Clamping de Seguridad en Backend**: En [anima.py](backend/app/services/architectures/anima.py) se añadió en `AnimaDiTAdapter.generate` una salvaguarda que limita automáticamente cualquier `guidance_scale > 5.0` a un valor seguro de `4.0`, asignándolo directamente a `pipeline.guider.guidance_scale`. Además, se balancea automáticamente el negative prompt cuando se reciben prompts extremadamente cortos, garantizando imágenes ricas en detalle, color y contraste en cualquier circunstancia.
- **Validación de Modelos Auxiliares Locales, Integración de VAE Nativo y Flujo de Prompts**:
  - **Inspección de Auxiliares en Disco (`reedAnimaFurry_v12`)**:
    - `reedAnimaFurry_v12.safetensors` (3.9 GB): 100% de tensores validados (567 del Transformer DiT y 118 del adaptador LLM `llm_adapter`).
    - `reedAnimaFurry_v12_txt.safetensors` (1.1 GB): 100% de los 310 tensores de Qwen3 cargados sin pérdidas (`AutoModel`).
    - `qwen_image_vae.safetensors` (242 MB): Se identificó que este archivo no se estaba cargando. Se determinó su estructura de tensores Wan VAE y se implementó su conversión mediante `convert_wan_vae_to_diffusers`, encajando los 194 tensores con `strict=True` en `AutoencoderKLQwenImage` de Diffusers.
  - **Trazabilidad y Flujo del Prompt**:
    - Se comprobó que el prompt viaja intacto desde el campo del formulario en la interfaz Web hacia la API FastAPI y la tubería de inferencia.
    - El pipeline modular procesa el texto en dos vías complementarias: `tokenizer` (Qwen2 con 151k tokens) y `t5_tokenizer` (T5 con 32k tokens), fusionándolos en `AnimaTextConditioner` para alimentar la atención cruzada del DiT.
    - **Fidelidad Semántica y Prompting Danbooru**: Se verificó que los modelos finetuneados de la serie Reed Anima Furry responden con máxima fidelidad a etiquetas separadas por comas en inglés (tags estilo Danbooru/e621: `1girl, wolf girl, furry, silver hair, cyber armor, masterpiece`), logrando que cada elemento solicitado aparezca reflejado en la imagen final, mientras que oraciones extensas o prosa en español generan representaciones más difusas.
  - **Optimización de Memoria en Inferencia**:
    - Se aisló la inferencia dentro de `with torch.inference_mode():` y se añadió liberación preventiva de caché con `torch.cuda.empty_cache()` en [anima.py](backend/app/services/architectures/anima.py), reduciendo picos de memoria para prevenir el desbordamiento hacia la memoria compartida del sistema.
