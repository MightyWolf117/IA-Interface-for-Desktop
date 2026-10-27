# ⚡ CYBER-IA // IA Interface for Desktop

<div align="center">

[![Español](https://img.shields.io/badge/Idioma-Español-00f0ff?style=flat-square)](README.md)
[![English](https://img.shields.io/badge/Language-English-ff0055?style=flat-square)](README_EN.md)

![Version](https://img.shields.io/badge/Release-v1.0.0-00f0ff?style=for-the-badge)
![License](https://img.shields.io/badge/License-GPL--3.0-ff0055?style=for-the-badge)
![Framework](https://img.shields.io/badge/Desktop-Tauri_v2-00ff66?style=for-the-badge)
![Backend](https://img.shields.io/badge/API-FastAPI_0.162-ffb700?style=for-the-badge)
![PyTorch](https://img.shields.io/badge/Compute-PyTorch_CUDA_12.4-7928ca?style=for-the-badge)

**High-performance desktop suite for running, managing, and orchestrating local generative AI models (Multimedia Diffusion and LLMs) featuring a Cyberpunk HUD aesthetic and sub-80ms real-time hardware telemetry.**

[Features](#-key-features) • [Live Showcase](#-live-visual-showcase) • [Supported Architectures](#-supported-ai-architectures) • [System Requirements](#-system-requirements) • [Installation Guide](#-installation--deployment) • [Contributing](CONTRIBUTING.md) • [Code of Conduct](CODE_OF_CONDUCT.md) • [Release Notes](RELEASE_NOTES.md) • [License](#-license--intellectual-property)

</div>

---

## 🌟 Overview

**IA Interface for Desktop (CYBER-IA)** is an open-source desktop application designed to eliminate the friction of deploying and executing local generative AI models with total privacy and hardware-level performance. It seamlessly bridges the lightning-fast, lightweight footprint of **Tauri v2 (Rust)** on the frontend with a modular, asynchronous **FastAPI (PyTorch / Diffusers)** backend.

Built from the ground up for power users and resource-constrained systems, CYBER-IA features an **Adaptive Hardware Memory Engine** capable of running cutting-edge models (from classic Stable Diffusion 1.5 up to 2-billion parameter modular Diffusion Transformers) even on 6 GB VRAM GPUs (such as the NVIDIA GeForce RTX 3050). The application safeguards operating system stability via real-time WebSocket telemetry with sub-80ms latency and proactive memory alerts.

---

## 📸 Live Visual Showcase

Below are genuine screenshots demonstrating CYBER-IA executing in a live desktop production environment:

### 1. Generative Multimedia Studio (Cyberpunk HUD)
![Multimedia Diffusion Studio](media/Generetion_Multimedia.png)
*Primary workspace featuring the neon interactive canvas, real-time denoising preview, prompt inputs, scheduler selector, WebSocket progress telemetry, and hardware memory monitors.*

### 2. Modular Model Scanner & Hardware Configuration
![Model Scanner and Configuration Modal](media/Multimedia_Menu.png)
*Interactive scanning modal with direct Windows File Explorer directory browsing, automatic multi-component architecture detection (Anima DiT, SDXL, SD 1.5), LoRA injection, and adaptive VRAM profiles.*

### 3. API Control Console & Network Telemetry
![API Diagnostic and Network Monitor](media/API_Control.png)
*Real-time network diagnostic dashboard displaying active service ports (FastAPI 8000 / Tauri 1420), interactive OpenAPI/Swagger catalog, and millisecond latency telemetry for all HTTP calls.*

---

## 🚀 Key Features

### 🎨 1. Cyberpunk HUD Desktop Interface (Tauri v2 + Rust)

- **Modular Lightweight Styling**: Built with pure CSS and ES Modules (no bloated heavy UI frameworks), featuring customizable cyan, magenta, and amber neon accents.
- **Interactive Multimedia Canvas**: Neon-framed viewport with real-time preview, toggleable scanline effects, prompt metadata inspector, and single-click high-resolution download.
- **WebSocket Step Progress**: Real-time progress bar tracking diffusion denoising steps with less than 80ms latency.
- **Native OS File Explorer**: Integrated directory browser button powered by Windows native explorer dialogs.

### 🧠 2. Multi-Architecture Diffusion Generative Engine

- **Decoupled Adapter Architecture**: The engine dynamically inspects safetensor headers and routes inference to specialized adapters (`SD15Adapter`, `SDXLAdapter`, `AnimaDiTAdapter`, `AutoDiffusersAdapter`).
- **Distributed Multi-Component Model Ingestion**: Automatically detects, parses, and injects weights split across multiple files (`.safetensors` DiT transformer, `_txt.safetensors` Qwen text encoder, and `_vae.safetensors` Wan/Qwen VAE).
- **Auxiliary Component Injection**: Native support for **LoRA** adapters (with scaling weights from 0.0 to 2.0) and on-the-fly scheduler switching (**EulerA, DPM++ 2M Karras, DDIM, UniPC**).
- **Dual Output Pipeline**: Configurable between in-memory **Base64** (instantaneous UI rendering) or persistence to the `outputs/` folder with static URL references.

### 🛡️ 3. Adaptive Hardware Engine & VRAM Protection

- **Automatic GPU Detection**: Real-time hardware telemetry via NVML/CUDA computing dynamic execution thresholds:
  - **Power Saver Mode (≤ 40% VRAM)**: Sequential offloading and aggressive memory protection for multi-tasking setups.
  - **Balanced Mode (≤ 65% VRAM)**: Standard component offloading balancing latency and VRAM footprint.
  - **High Performance Mode (Up to 100% VRAM)**: Full GPU placement for minimal generation latency.
- **Active Safety Guardrails**: Continuous evaluation triggering an emergency top banner if VRAM exceeds 88% or system RAM exceeds 90%, offering one-click mitigations (*Purge VRAM* or *Activate Saver Mode*).
- **PCIe Swapping Prevention**: Inferences run isolated inside `with torch.inference_mode():` combined with proactive `torch.cuda.empty_cache()` to prevent Windows GPU shared memory pagination.

### 💬 4. Conversational LLM Studio

- Dedicated local chat environment with channel switching, prompt engineering presets, and direct backend routing for open-weight language models.

### 🌐 5. Embedded API Control Panel & Port Inspector

- Live diagnostic dashboard tracking active ports (8000, 1420), OpenAPI/Swagger endpoints, and a colored HTTP traffic terminal measuring real-time response latency in milliseconds.

---

## 🧩 Supported AI Architectures

| Architecture | Identifier | Compatible File Formats | Recommended Resolution | Recommended CFG Scale | Representative Examples |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stable Diffusion 1.5 / 2.1** | `sd15` | `.safetensors`, `.ckpt`, Hugging Face | 512x512 | 7.0 – 8.0 | `runwayml/stable-diffusion-v1-5`, `stabilityai/sd-turbo` |
| **Stable Diffusion XL / Pony** | `sdxl` | `.safetensors`, `.ckpt`, Hugging Face | 1024x1024 | 6.5 – 7.5 | `stabilityai/stable-diffusion-xl-base-1.0`, `SSD-1B` |
| **Anima / Cosmos DiT (Modular)** | `anima_dit` | Multi-component folders, `.safetensors` + `_txt` + `_vae` | 768x768 / 512x512 | 3.5 – 4.5 | `reedAnimaFurry_v12`, `circlestone-labs/Anima-Base-v1.0-Diffusers` |
| **Diffusers Universal Pipeline** | `diffusers_auto` | Standard Hugging Face Hub repositories | Dynamic | User-defined | Standard `AutoPipelineForText2Image` pipelines |

> [!TIP]
> **Built-in DiT Safeguards**: Diffusion Transformers operate best with lower CFG values (3.5 - 4.5). The interface automatically synchronizes these parameters upon loading, and the adapter incorporates safety clamping to prevent latent blowout (solid white output) if excessive values are passed.

---

## 💻 System Requirements

### Minimum Requirements

- **Operating System**: Windows 10/11 (64-bit), Linux, or macOS.
- **CPU**: Quad-core x86_64 processor.
- **System Memory (RAM)**: 8 GB RAM.
- **Disk Storage**: 10 GB free disk space (for base models and virtual environment).
- **Graphics Acceleration**: Compatible with CPU mode for basic inference.

### Recommended Requirements

- **GPU**: NVIDIA GeForce RTX with at least 6 GB of VRAM (e.g., RTX 3050, RTX 3060, RTX 4060, or higher).
- **Driver**: NVIDIA Driver with **CUDA 12.4+** support.
- **System Memory (RAM)**: 16 GB system RAM.
- **Development Toolchain**: Python 3.10 – 3.13, Node.js 18+, and Rust (Cargo).

---

## 📦 Installation & Deployment

### 🚀 Option 1: Direct Installer Download (Recommended for End Users)

For users who want to run **CYBER-IA** directly without configuring development toolchains:

1. Navigate to the official **[GitHub Releases Page](https://github.com/MightyWolf117/IA-Interface-for-Desktop/releases)**.
2. Download the official installer package for Windows (10/11 64-bit):
   - **Official Installer**: `CYBER-IA-Setup.exe` (NSIS with Cyberpunk HUD theme and mandatory license acceptance)
3. Run the installer and launch **CYBER-IA** directly from your Start Menu or Desktop.
4. **All-in-One Autonomous Architecture**: The FastAPI inference engine and Tauri v2 desktop shell are compiled into a standalone package. Rust natively launches the backend in the background without pop-up windows and terminates all subprocesses cleanly on exit.

---

### 💻 Option 2: Running from Source (For Developers & Contributors)

If you wish to compile locally, inspect, or contribute to the codebase:

#### 1. Clone the Repository

```bash
git clone https://github.com/MightyWolf117/IA-Interface-for-Desktop.git
cd IA-Interface-for-Desktop
```

#### 2. Configure the Python Backend

It is recommended to set up the virtual environment inside the `backend` folder:

```powershell
# Windows PowerShell:
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install PyTorch and CUDA dependencies:
pip install -r requirements.txt
```

#### 3. Configure the Tauri v2 Desktop Frontend

```bash
# In a new terminal window:
cd interface
npm install
```

#### 4. Running the Application

##### Mode A: Integrated Automatic Launch (Recommended)
When you launch the desktop app, Tauri's native Rust core **automatically detects and launches the FastAPI backend in the background** (without opening extra console windows) and cleanly shuts it down upon closing the window:
```bash
cd interface
npm run tauri dev
```

##### Mode B: Decoupled Manual Launch (For terminal debugging)
If you want to view live Uvicorn and Diffusers logs in a separate terminal:
```powershell
# Terminal 1 (Backend):
cd backend
python run.py

# Terminal 2 (Frontend):
cd interface
npm run tauri dev
```

---

## 📁 Project Structure

```
IA-Interface-for-Desktop/
├── .github/                              # GitHub Actions CI/CD workflows
│   └── workflows/
│       ├── release.yml                   # Automated Windows desktop installer build & release pipeline
│       └── ci.yml                        # Continuous integration and syntax verification
├── backend/                              # FastAPI Service & Generative Inference Engine
│   ├── app/
│   │   ├── api/                          # REST routes & telemetry WebSockets
│   │   │   ├── diffusion_routes.py       # Model scanning, loading, generation & native dialogs
│   │   │   └── routes.py                 # Chat and health status endpoints
│   │   ├── core/                         # Hardware & monitoring core
│   │   │   ├── hardware.py               # NVML/CUDA GPU detector & memory thresholds
│   │   │   └── api_tracker.py            # HTTP request tracker & port telemetry
│   │   ├── schemas/                      # Pydantic data validation schemas
│   │   └── services/                     # AI inference services & architecture adapters
│   │       ├── diffusion_engine.py       # Core diffusion pipeline manager
│   │       ├── model_scanner.py          # Local model & auxiliary weight scanner
│   │       └── architectures/            # Multi-architecture adapter suite
│   │           ├── base.py               # BaseModelAdapter abstract contract
│   │           ├── sd15.py               # Stable Diffusion 1.5 / 2.1 adapter
│   │           ├── sdxl.py               # Stable Diffusion XL / Pony adapter
│   │           ├── anima.py              # Cosmos / Anima DiT Modular adapter
│   │           ├── auto_diffusers.py     # Universal diffusers fallback adapter
│   │           └── registry.py           # Dynamic adapter registry & dispatcher
│   ├── build_api.py                      # Automated backend compiler script for standalone distribution
│   ├── cyber-ia-api.spec                 # PyInstaller specification for headless backend packaging
│   ├── requirements.txt                  # Python dependencies
│   ├── run.py                            # Multiprocessing-safe startup script for Windows
│   └── README.md                         # Backend-specific documentation
│
├── interface/                            # Tauri v2 Desktop Application
│   ├── src-tauri/                        # Rust native core
│   │   ├── Cargo.toml                    # Rust crate dependencies
│   │   └── tauri.conf.json               # Window dimensions, title & IPC permissions
│   └── src/                              # Modular Frontend (Vanilla Web)
│       ├── index.html                    # Main Cyberpunk HUD layout
│       ├── styles.css                    # Central CSS import manifest
│       ├── css/                          # Modular styling sheets
│       │   ├── variables.css             # Neon color palettes and design tokens
│       │   ├── base.css                  # Holographic grid, resets, and scanlines
│       │   ├── header.css                # Top HUD, branding, and cyber clock
│       │   ├── diffusion.css             # Studio canvas, controls, and progress bar
│       │   ├── chat.css                  # Channel sidebar and message stream
│       │   ├── api-control.css           # Network diagnostics and call terminal
│       │   ├── modal.css                 # Configuration modal & memory tier cards
│       │   └── alerts.css                # Critical hardware alert styling
│       └── js/                           # ES Modules JavaScript logic
│           ├── config.js                 # API base URLs and IPC wrappers
│           ├── ui.js                     # Tab switcher and neon theme controller
│           ├── alerts.js                 # Resource threshold monitor and safety alerts
│           ├── telemetry.js              # WebSocket telemetry client (<80ms loop)
│           ├── model_modal.js            # Model scanner dialog & setting manager
│           ├── diffusion.js              # Diffusion studio controller & canvas renderer
│           ├── chat.js                   # Conversational LLM interface
│           ├── api_control.js            # Real-time network monitor controller
│           └── main.js                   # Application bootstrap entry point
│
├── CHANGELOG.md                          # Version changelog and semantic release history
├── CODE_OF_CONDUCT.md                    # Community code of conduct and safety policies
├── CONTRIBUTING.md                       # Contribution guidelines, bug reporting, and standards
├── LICENSE                               # Official GNU GPLv3 open-source license (Copyleft)
├── media/                                # Official application execution screenshots and assets
│   ├── API_Control.png                   # API control console and network telemetry screenshot
│   ├── Generetion_Multimedia.png         # Live diffusion studio workspace screenshot
│   └── Multimedia_Menu.png               # Model scanner and configuration modal screenshot
├── README.md                             # Spanish primary documentation
├── README_EN.md                          # English primary documentation
└── RELEASE_NOTES.md                      # Detailed technical engineering patch report
```

---

## 🎯 Best Practices for Optimal Generation

### Diffusion Transformer Models (Anima / Cosmos DiT)

- **Prompt Structure**: DiT anime/stylized checkpoints respond with maximum fidelity to comma-separated **Danbooru tags** in English (e.g., `1girl, wolf girl, furry, silver hair, cyber armor, neon lighting, tokyo street, masterpiece, best quality`).
- **CFG Scale**: Keep between **3.5 and 4.5**. Values exceeding 5.0 amplify latent vectors into numerical blowout.
- **Resolution**: Use **768x768** or **1024x1024** for maximum aesthetic fidelity; on 6 GB VRAM GPUs, **512x512** delivers near real-time generation (~1.4 seconds per step) without exceeding physical VRAM.

### Stable Diffusion 1.5 & SDXL Models

- **CFG Scale**: Standard range of **7.0 to 8.0**.
- **Schedulers**: **EulerA** is recommended for dynamic, stylized illustration; **DPM++ 2M Karras** provides superior photographic rendering with 20 to 30 sampling steps.

---

## 📄 License & Intellectual Property

This project is distributed under the **GNU General Public License v3.0 (GPL-3.0)**.

- **Intellectual Property Recognition**: The original software architecture, Cyberpunk HUD design, and core source code are the intellectual property of **MightyWolf117** and project contributors. All distributions, forks, and packaging must preserve original copyright notices and author attribution.
- **Strict Copyleft (Perpetual Open Source)**: Under GNU GPLv3, any modifications, forks, extensions, or derivative works incorporating this software MUST remain licensed under GNU GPL-3.0 or later, guaranteeing that the complete source code remains freely accessible and open to the community without the possibility of proprietary cloaking.

For complete legal terms, review the [LICENSE](LICENSE) file. Also see [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for contribution workflows and zero-tolerance safety standards.

---

<div align="center">

Crafted with dedication for the open-source AI community.  
**CYBER-IA // MightyWolf117**

</div>
