# Backend FastAPI - IA Interface for Desktop

Backend local en Python utilizando **FastAPI** y **Uvicorn**, diseñado para integrarse con la interfaz de escritorio en **Tauri v2**.

## 🚀 Inicio Rápido

### 1. Activar entorno virtual
En Windows PowerShell:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
```

O en CMD:
```cmd
cd backend
.\.venv\Scripts\activate.bat
```

### 2. Instalar dependencias (si es necesario en una nueva máquina)
```powershell
pip install -r requirements.txt
```

### 3. Ejecutar el servidor de desarrollo
```powershell
python run.py
```
O con Uvicorn directamente:
```powershell
uvicorn app.main:app --reload --port 8000
```

El servidor estará disponible en `http://127.0.0.1:8000`.

## 📖 Documentación Interactiva (Swagger / OpenAPI)
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Redoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 📡 Endpoints Disponibles

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `GET` | `/` | Comprobación de estado base e información de rutas. |
| `GET` | `/api/v1/health` | Estado del servicio y disponibilidad de VRAM. |
| `GET` | `/api/v1/models` | Listado de modelos locales disponibles. |
| `POST` | `/api/v1/chat` | Generación de respuesta de chat a partir de mensajes. |

## 📁 Estructura del Backend
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # Configuración de FastAPI, CORS y middleware
│   ├── api/             # Routers y controladores de endpoints
│   │   ├── __init__.py
│   │   └── routes.py
│   └── schemas/         # Modelos de datos Pydantic
│       ├── __init__.py
│       └── chat.py
├── .venv/               # Entorno virtual de Python
├── requirements.txt     # Dependencias del proyecto
├── run.py               # Script de inicio directo
└── README.md            # Documentación del backend
```
