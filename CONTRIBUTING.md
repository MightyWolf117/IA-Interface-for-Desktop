# 🛠️ Guía de Contribución // CYBER-IA

Bienvenido a la comunidad de desarrollo de **IA Interface for Desktop (CYBER-IA)**. Agradecemos profundamente el interés en mejorar esta plataforma de inferencia de Inteligencia Artificial local de alto rendimiento.

Para garantizar un ecosistema colaborativo eficiente, seguro, ético y de máxima calidad técnica, todas las personas que deseen contribuir deben seguir las pautas detalladas a continuación.

---

## 📜 1. Filosofía de Código Abierto y Propiedad Intelectual

1. **Licencia Copyleft Estricta (GNU GPLv3)**:
   Este proyecto es y será siempre software libre y de código abierto bajo la licencia **GNU General Public License v3.0 (GPL-3.0)**.
   - **Requisito de Código Abierto Perpetuo**: Cualquier contribución, adición, mejora, bifurcación (fork) o trabajo derivado que incorpore código de CYBER-IA **debe distribuirse bajo la misma licencia GPL-3.0 o posterior**, garantizando que el código fuente esté disponible de forma pública, transparente y gratuita para toda la comunidad.
   - **Prohibición de Código Propietario**: No se aceptará ninguna contribución que pretenda privatizar, ofuscar o restringir las libertades de los usuarios finales o de la comunidad de desarrolladores.

2. **Reconocimiento de Autoría y Propiedad Intelectual**:
   La arquitectura original, el diseño del HUD Cyberpunk y el código base inicial son obra y propiedad intelectual de **MightyWolf117** y los colaboradores reconocidos del repositorio. Toda distribución o derivación debe conservar íntegramente los avisos de autoría, derechos de autor y licencias originales.

---

## 🛡️ 2. Políticas Éticas, Legales y de Seguridad Estrictas (Tolerancia Cero)

Para mantener la integridad moral del proyecto y cumplir con la legislación internacional vigente, se establecen las siguientes políticas de **Tolerancia Cero**. Cualquier violación resultará en el rechazo inmediato del aporte, revocación de acceso al repositorio y, de ser procedente, notificación a las autoridades pertinentes:

### 🚫 Prohibición Absoluta de Explotación de Menores (CSAM / CSAE)
- Queda terminantemente prohibido aportar, integrar, promover o facilitar modelos, adaptadores, configuraciones, prompts de prueba, scripts o documentación que involucren contenido sexual o de desnudez relacionado con menores de edad (CSAM / CSAE).
- Esta prohibición no admite excepciones de ninguna índole (artísticas, satíricas o de investigación).

### 🚫 Prohibición de Zoofilia y Abuso Sexual Animal
- Queda estrictamente prohibido cualquier aporte, adaptador de modelo, prompt o funcionalidad que promueva, facilite o genere representaciones de actos sexuales o parafilias que involucren animales, en conformidad con los estatutos penales de protección animal y prohibición de zoofilia / bestialismo.

### 🚫 Prohibición de Discurso de Odio y Discriminación
- No se aceptarán contribuciones, datos de entrenamiento o prompts predeterminados diseñados para promover odio, denigración, violencia o acoso contra individuos o grupos basados en su raza, etnia, religión, género, identidad u orientación sexual, discapacidad o condición social.

### 🚫 Prohibición Absoluta de Malware, Spyware y Amenazas Cibernéticas
- Queda terminantemente prohibido introducir:
  - Código malicioso, troyanos, ransomware, keyloggers o puertas traseras (backdoors).
  - Software espía (spyware) o telemetría invasiva oculta no consentida por el usuario.
  - Mineros de criptomonedas (cryptominers) en segundo plano o uso oculto de recursos de GPU/CPU.
  - Ofuscación maliciosa o descarga de binarios externos no verificados en tiempo de ejecución.
- Todo el código fuente de las contribuciones debe ser 100% legible, auditable y ceñirse de forma transparente a las funciones declaradas de la plataforma de escritorio.

---

## 🧩 3. Tipificación de Aportes Aceptados

El proyecto da la bienvenida a las siguientes categorías de contribuciones técnicas:

| Categoría | Descripción y Ámbito | Requisitos Técnicos |
| :--- | :--- | :--- |
| **Adaptadores de Difusión** | Implementación de nuevas arquitecturas de generación en `backend/app/services/architectures/`. | Heredar de `BaseModelAdapter`, implementar lazy-loading, descarga secuencial y compatibilidad con safetensors. |
| **Optimización de Hardware** | Mejoras en la detección NVML, gestión dinámica de VRAM, quantización y prevención de desbordamientos (OOM). | Sin introducir dependencias binarias pesadas no multiplataforma; pruebas en GPUs de gama de entrada (<= 6GB VRAM). |
| **Mejoras del HUD Cyberpunk** | Nuevos módulos visuales, controles de lienzo interactivo, micro-animaciones CSS y optimización del WebView. | Vanilla CSS y Vanilla JS (ES Modules) exclusivamente. Respetar la paleta de colores neón y evitar frameworks pesados (React, Tailwind, Vue). |
| **Rendimiento e IPC Tauri** | Optimización del ciclo de vida del subproceso FastAPI, eventos nativos de Rust y manejo de ventanas. | Cumplir estrictamente con Rust 2021 edition, `cargo check` y `cargo fmt` limpios, y gestión limpia de procesos en Windows/Linux/macOS. |
| **Diagnóstico y Red** | Mejoras en el terminal de API, nuevos endpoints REST documentados en OpenAPI o telemetría WebSocket. | Pydantic v2, rutas asíncronas en FastAPI y control estricto de latencias en milisegundos. |
| **Documentación y Guías** | Correcciones técnicas, traducciones bilingües (Español/Inglés) y guías de optimización de prompts. | Formato Markdown GitHub Flavored con enlaces funcionales. |

---

## 🔄 4. Proceso para Realizar Aportes (Workflow de Desarrollo)

### Paso 1: Clonar y Bifurcar (Fork)
1. Haz un **Fork** del repositorio principal: [https://github.com/MightyWolf117/IA-Interface-for-Desktop](https://github.com/MightyWolf117/IA-Interface-for-Desktop).
2. Clona tu bifurcación localmente:
   ```bash
   git clone https://github.com/TU_USUARIO/IA-Interface-for-Desktop.git
   cd IA-Interface-for-Desktop
   ```

### Paso 2: Crear una Rama Semántica
Crea una rama descriptiva que identifique la naturaleza de tu trabajo:
```bash
git checkout -b feat/nuevo-adaptador-flux
# O para corrección de bugs:
git checkout -b fix/vram-telemetry-overflow
# O para documentación:
git checkout -b docs/guia-optimizacion-dit
```

### Paso 3: Estándares de Código
- **Backend (Python)**:
  - Respetar **PEP 8** y anotaciones de tipo (`typing`).
  - Utilizar modelos **Pydantic v2** para validación de entradas y respuestas.
  - Preservar la arquitectura modular orientada a servicios y adaptadores.
  - Nunca incluir llamadas bloqueantes directas en el bucle principal asíncrono de FastAPI.
- **Frontend (Tauri / Web)**:
  - Usar **Vanilla JavaScript (ES Modules)** estructurado en `interface/src/js/`.
  - Usar **Vanilla CSS modular** con variables predefinidas en `variables.css`.
  - Asegurar un diseño completamente responsivo y compatible con WebView2 (Windows), WebKit (macOS/Linux).
- **Core Nativo (Rust)**:
  - Formatear con `cargo fmt`.
  - Verificar que no existan advertencias ni errores con `cargo check`.
  - Mantener el aislamiento de subprocesos (ej. flag `CREATE_NO_WINDOW` en Windows para evitar abrir ventanas cmd indeseadas).

### Paso 4: Pruebas Locales
Antes de someter tu cambio, valida manualmente:
1. El backend inicia correctamente con `python run.py`.
2. El frontend de escritorio compila y ejecuta sin errores con `npm run tauri dev`.
3. La telemetría WebSocket conecta y transmite métricas de hardware a menos de 80ms de latencia.
4. Las generaciones de imágenes o consultas de chat se completan sin memory leaks en PyTorch.

### Paso 5: Enviar el Pull Request
1. Realiza el push a tu repositorio remoto:
   ```bash
   git push origin feat/tu-funcionalidad
   ```
2. Abre un **Pull Request** hacia la rama `main` del repositorio oficial.
3. Completa la descripción del PR explicando:
   - Resumen claro del cambio propuesto.
   - Motivación o Issue asociado (ej. `Fixes #12`).
   - Especificaciones del hardware donde se realizaron las pruebas (GPU, VRAM, OS).
   - Capturas de pantalla o logs si aplica.

---

## 🐛 5. Proceso para Reportar Bugs

Si detectas un fallo, comportamiento errático o fuga de memoria, por favor abre un **Issue** en GitHub siguiendo este formato:

### Plantilla de Reporte de Fallos

```markdown
### 📌 Descripción del Problema
Una explicación clara y concisa de lo que ocurrió.

### 💻 Entorno y Especificaciones de Hardware
- **Versión de CYBER-IA**: (ej. v1.0.0)
- **Sistema Operativo**: (ej. Windows 11 Pro 64-bit versión 23H2)
- **Procesador (CPU)**: (ej. AMD Ryzen 7 5700X)
- **Tarjeta Gráfica (GPU)**: (ej. NVIDIA GeForce RTX 3050 6GB)
- **Versión de Driver NVIDIA / CUDA**: (ej. Driver 560.94 / CUDA 12.6)
- **Memoria RAM del Sistema**: (ej. 16 GB)

### 🤖 Modelo de IA Involucrado
- **Nombre o Repositorio**: (ej. circlestone-labs/Anima-Base-v1.0-Diffusers)
- **Arquitectura seleccionada**: (ej. `anima_dit`, `sdxl`, `sd15`)
- **Tipo de Archivos**: (.safetensors único, carpeta multicomponente, Hugging Face Hub)

### 🔁 Pasos para Reproducir
1. Abrir la aplicación de escritorio.
2. Ir a la pestaña "Estudio de Difusión".
3. Cargar el modelo XYZ con scheduler ABC.
4. Generar con parámetros: 25 pasos, CFG 4.0, resolución 768x768.
5. Observar el error que se produce.

### 📋 Logs de la Consola
Pega los logs relevantes del backend (terminal FastAPI) o de las herramientas de desarrollador del WebView (F12):
```
[Logs aquí...]
```

### 🎯 Comportamiento Esperado vs. Observado
- **Esperado**: La imagen debía generarse en el lienzo en ~15 segundos.
- **Observado**: La VRAM se saturó al 99% y el proceso arrojó `CUDA out of memory`.
```

---

## 🤝 6. Reconocimiento a los Contribuidores

Todas las contribuciones aceptadas serán debidamente acreditadas en el archivo `CHANGELOG.md` y en las notas de lanzamiento oficiales de cada versión. ¡Gracias por hacer crecer a **CYBER-IA** de forma ética, abierta y de alto rendimiento!
