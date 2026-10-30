// ==========================================================================
// CYBER-IA // MODEL CONFIGURATION & SCANNER MODAL CONTROLLER
// ==========================================================================

import { API_BASE } from "./config.js";
import { cyberAlert, cyberConfirm } from "./dialog.js";

// Cache local de modelos para acceso rápido a metadatos de arquitectura
const modelsMetadataCache = new Map();
let publicModelCacheStatus = { present: false, size_mb: 0, path: "" };

export function initModelConfigModal() {
  const modal = document.querySelector("#modal-model-config");
  const openBtn = document.querySelector("#open-config-btn");
  const closeBtn = document.querySelector("#modal-close-btn");
  const cancelBtn = document.querySelector("#modal-cancel-btn");
  const scanBtn = document.querySelector("#start-scan-btn");
  const applyBtn = document.querySelector("#modal-apply-btn");
  const unloadBtn = document.querySelector("#unload-model-btn");

  const scanPathInput = document.querySelector("#scan-path-input");
  const downloadPathInput = document.querySelector("#download-path-input");
  const browseDownloadBtn = document.querySelector("#browse-download-dir-btn");
  const downloadDirStatus = document.querySelector("#download-dir-status");
  const publicModelTools = document.querySelector("#public-model-tools");
  const publicModelStatusTag = document.querySelector("#public-model-status-tag");
  const deletePublicModelBtn = document.querySelector("#delete-public-model-btn");

  const modelDropdown = document.querySelector("#model-select-dropdown");
  const loraDropdown = document.querySelector("#lora-select-dropdown");
  const loraWeightSlider = document.querySelector("#lora-weight-slider");
  const loraWeightVal = document.querySelector("#lora-weight-val");
  const schedulerDropdown = document.querySelector("#scheduler-select-dropdown");

  const archBadge = document.querySelector("#modal-arch-badge");
  const archDesc = document.querySelector("#modal-arch-desc");
  const archDims = document.querySelector("#modal-arch-dims");

  // Fetch initial Hardware info & populate dynamic limits
  initHardwareInfo();

  // Open / Close Modal
  if (openBtn) openBtn.addEventListener("click", () => {
    modal.style.display = "flex";
    if (modelDropdown) checkPublicModelStatus(modelDropdown.value);
  });
  if (closeBtn) closeBtn.addEventListener("click", () => (modal.style.display = "none"));
  if (cancelBtn) cancelBtn.addEventListener("click", () => (modal.style.display = "none"));

  // LoRA Weight Slider
  if (loraWeightSlider && loraWeightVal) {
    loraWeightSlider.addEventListener("input", () => {
      loraWeightVal.textContent = loraWeightSlider.value;
    });
  }

  async function checkPublicModelStatus(modelId) {
    if (!modelId || !modelId.includes("/")) {
      if (publicModelTools) publicModelTools.style.display = "none";
      if (deletePublicModelBtn) deletePublicModelBtn.style.display = "none";
      return;
    }

    if (publicModelTools) publicModelTools.style.display = "flex";
    if (publicModelStatusTag) {
      publicModelStatusTag.textContent = "VERIFICANDO DISCO...";
      publicModelStatusTag.style.color = "var(--text-muted)";
      publicModelStatusTag.style.borderColor = "var(--border-subtle)";
    }

    const downloadDir = downloadPathInput?.value.trim() || scanPathInput?.value.trim() || "models";
    try {
      const res = await fetch(`${API_BASE}/models/check-public`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_id: modelId, download_dir: downloadDir })
      });
      if (res.ok) {
        const data = await res.json();
        publicModelCacheStatus = data;
        if (data.present) {
          if (publicModelStatusTag) {
            publicModelStatusTag.textContent = `✅ EN DISCO (${data.size_mb} MB)`;
            publicModelStatusTag.style.color = "var(--neon-green)";
            publicModelStatusTag.style.borderColor = "rgba(0, 255, 117, 0.5)";
          }
          if (deletePublicModelBtn) {
            deletePublicModelBtn.style.display = "inline-flex";
            deletePublicModelBtn.dataset.modelId = modelId;
            deletePublicModelBtn.dataset.downloadDir = downloadDir;
          }
        } else {
          if (publicModelStatusTag) {
            publicModelStatusTag.textContent = "📥 NO DESCARGADO (~2 a 4 GB)";
            publicModelStatusTag.style.color = "var(--neon-amber)";
            publicModelStatusTag.style.borderColor = "rgba(255, 183, 0, 0.5)";
          }
          if (deletePublicModelBtn) deletePublicModelBtn.style.display = "none";
        }
      }
    } catch (e) {
      console.warn("Fallo verificando estado de modelo público:", e);
    }
  }

  // Sincronizar carpeta de descarga con escaneo a menos que el usuario la personalice
  if (scanPathInput && downloadPathInput) {
    scanPathInput.addEventListener("input", () => {
      if (!downloadPathInput.dataset.custom) {
        downloadPathInput.value = scanPathInput.value;
      }
      if (modelDropdown) checkPublicModelStatus(modelDropdown.value);
    });
  }

  if (browseDownloadBtn) {
    browseDownloadBtn.addEventListener("click", async () => {
      const origText = browseDownloadBtn.innerHTML;
      browseDownloadBtn.innerHTML = "<span>ABRIENDO...</span>";
      try {
        const res = await fetch(`${API_BASE}/system/browse-folder`, { method: "POST" });
        if (res.ok) {
          const data = await res.json();
          if (data.selected_path && downloadPathInput) {
            downloadPathInput.value = data.selected_path;
            downloadPathInput.dataset.custom = "true";
            if (downloadDirStatus) {
              downloadDirStatus.textContent = "PERSONALIZADA";
              downloadDirStatus.style.color = "var(--neon-pink)";
              downloadDirStatus.style.borderColor = "var(--neon-pink)";
            }
            if (modelDropdown) checkPublicModelStatus(modelDropdown.value);
          }
        }
      } catch (err) {
        console.warn("Fallo al invocar diálogo de carpeta de descargas:", err);
      } finally {
        browseDownloadBtn.innerHTML = origText;
      }
    });
  }

  if (deletePublicModelBtn) {
    deletePublicModelBtn.addEventListener("click", async () => {
      const modelId = deletePublicModelBtn.dataset.modelId;
      const downloadDir = deletePublicModelBtn.dataset.downloadDir;
      if (!modelId || !downloadDir) return;

      const safeFolder = modelId.replace("/", "--");
      const confirmed = await cyberConfirm(
        `¿Deseas eliminar la versión descargada de este modelo?\n\nModelo: ${modelId}\nCarpeta: ${downloadDir}\\${safeFolder}\n\nEsta acción liberará espacio en tu disco de forma permanente.`,
        "CONFIRMAR ELIMINACIÓN",
        "warning"
      );

      if (confirmed) {
        deletePublicModelBtn.disabled = true;
        deletePublicModelBtn.textContent = "ELIMINANDO...";
        try {
          const res = await fetch(`${API_BASE}/models/delete-public`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model_id: modelId, download_dir: downloadDir })
          });
          if (res.ok) {
            const data = await res.json();
            cyberAlert(data.message, "MODELO ELIMINADO", "success");
            checkPublicModelStatus(modelId);
            if (scanBtn) scanBtn.click();
          } else {
            cyberAlert("Error al eliminar la carpeta del modelo.", "ERROR DE BORRADO", "error");
          }
        } catch (err) {
          cyberAlert("Error de comunicación: " + err, "ERROR", "error");
        } finally {
          deletePublicModelBtn.disabled = false;
          deletePublicModelBtn.innerHTML = "<span>🗑️ BORRAR VERSIÓN</span>";
        }
      }
    });
  }

  // Actualizar tarjeta de arquitectura y estado de modelo al cambiar en el dropdown
  if (modelDropdown) {
    modelDropdown.addEventListener("change", () => {
      updateArchitecturePreview(modelDropdown.value);
      checkPublicModelStatus(modelDropdown.value);
    });
  }

  // Native Windows Folder Browser Dialog
  const browseBtn = document.querySelector("#browse-folder-btn");
  if (browseBtn) {
    browseBtn.addEventListener("click", async () => {
      const origText = browseBtn.innerHTML;
      browseBtn.innerHTML = "<span>ABRIENDO...</span>";
      try {
        const res = await fetch(`${API_BASE}/system/browse-folder`, { method: "POST" });
        if (res.ok) {
          const data = await res.json();
          if (data.selected_path && scanPathInput) {
            scanPathInput.value = data.selected_path;
            if (!downloadPathInput?.dataset.custom && downloadPathInput) {
              downloadPathInput.value = data.selected_path;
            }
            if (scanBtn) scanBtn.click();
            if (modelDropdown) checkPublicModelStatus(modelDropdown.value);
          }
        } else {
          cyberAlert("No se pudo abrir el explorador de carpetas de Windows.", "EXPLORADOR DE CARPETAS", "error");
        }
      } catch (err) {
        console.warn("Fallo al invocar diálogo nativo:", err);
        cyberAlert("Error al invocar diálogo de Windows: " + err, "EXPLORADOR DE CARPETAS", "error");
      } finally {
        browseBtn.innerHTML = origText;
      }
    });
  }

  // Scan Directory
  if (scanBtn) {
    scanBtn.addEventListener("click", async () => {
      const dirPath = scanPathInput?.value.trim() || "models";
      scanBtn.textContent = "ESCANEANDO...";
      try {
        const res = await fetch(`${API_BASE}/models/scan`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ directory_path: dirPath })
        });

        if (res.ok) {
          const data = await res.json();

          // Populate Public Models if returned
          if (data.public_models && Array.isArray(data.public_models)) {
            data.public_models.forEach((m) => {
              modelsMetadataCache.set(m.id, m);
            });
          }

          // Populate Local Group
          const localGroup = document.querySelector("#optgroup-local");
          if (localGroup) {
            localGroup.innerHTML = "";
            if (data.base_models.length === 0) {
              localGroup.innerHTML = "<option disabled>No se hallaron modelos en la ruta</option>";
            } else {
              data.base_models.forEach((m) => {
                modelsMetadataCache.set(m.id, m);
                const opt = document.createElement("option");
                opt.value = m.id;
                opt.textContent = `${m.name} [${m.architecture || m.type}]`;
                localGroup.appendChild(opt);
              });
            }
          }

          // Populate LoRAs
          if (loraDropdown) {
            loraDropdown.innerHTML = '<option value="">Ninguno</option>';
            data.loras.forEach((l) => {
              const opt = document.createElement("option");
              opt.value = l.path;
              opt.textContent = `${l.name} (${l.size_mb} MB)`;
              loraDropdown.appendChild(opt);
            });
          }

          // Trigger architecture preview update for the selected model
          if (modelDropdown) {
            updateArchitecturePreview(modelDropdown.value);
          }
        }
      } catch (err) {
        cyberAlert("Error al escanear directorio:\n" + err, "ERROR DE ESCANEO", "error");
      } finally {
        scanBtn.textContent = "ESCANEAR CARPETA";
      }
    });
  }

  // Apply / Load Model
  if (applyBtn) {
    applyBtn.addEventListener("click", async () => {
      const selectedModel = modelDropdown?.value;
      const memMode = document.querySelector('input[name="memory_mode"]:checked')?.value || "equilibrado";
      const transMode = document.querySelector('input[name="transfer_mode"]:checked')?.value || "base64";
      const loraPath = loraDropdown?.value || null;
      const loraWeight = parseFloat(loraWeightSlider?.value || "1.0");
      const scheduler = schedulerDropdown?.value || "EulerA";

      if (!selectedModel) {
        cyberAlert("Por favor selecciona un modelo antes de continuar.", "SELECCIÓN REQUERIDA", "warning");
        return;
      }

      const downloadDir = downloadPathInput?.value.trim() || scanPathInput?.value.trim() || "models";

      // Si es un modelo público no descargado en disco, pedir confirmación antes de iniciar descarga pesada
      const dlContainer = document.querySelector("#modal-download-progress-container");
      const dlFill = document.querySelector("#modal-download-progress-fill");
      const dlStatus = document.querySelector("#modal-download-status");
      const dlPercent = document.querySelector("#modal-download-percent");
      const dlFile = document.querySelector("#modal-download-file");
      const dlMb = document.querySelector("#modal-download-mb");

      if (selectedModel.includes("/") && !publicModelCacheStatus.present) {
        const safeFolder = selectedModel.replace("/", "--");
        const confirmed = await cyberConfirm(
          `El modelo público '${selectedModel}' no se encuentra en tu disco.\n\n¿Deseas descargarlo en:\n${downloadDir}\\${safeFolder}?\n\nSe descargará como una carpeta estándar para que puedas verla, usarla o borrarla cuando desees.`,
          "DESCARGAR MODELO PÚBLICO",
          "info"
        );
        if (!confirmed) {
          return;
        }
        applyBtn.textContent = "DESCARGANDO MODELO A DISCO...";
        if (dlContainer) {
          dlContainer.style.display = "block";
          if (dlFill) dlFill.style.width = "0%";
          if (dlStatus) dlStatus.textContent = "INICIANDO DESCARGA...";
          if (dlPercent) dlPercent.textContent = "0%";
          if (dlFile) dlFile.textContent = "Conectando con Hugging Face...";
          if (dlMb) dlMb.textContent = "0 / 0 MB";
        }
      } else {
        applyBtn.textContent = "INICIALIZANDO MOTOR...";
        if (dlContainer) dlContainer.style.display = "none";
      }

      applyBtn.disabled = true;
      try {
        const res = await fetch(`${API_BASE}/diffusion/load`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model_id_or_path: selectedModel,
            memory_mode: memMode,
            transfer_mode: transMode,
            lora_path: loraPath,
            lora_weight: loraWeight,
            scheduler: scheduler,
            download_dir: downloadDir
          })
        });

        if (res.ok) {
          const resp = await res.json();
          if (!resp.success) {
            cyberAlert(resp.message || "Error al inicializar pipeline.", "FALLO AL CARGAR MODELO", "error");
            return;
          }

          // Actualizar estado de descarga del modelo
          checkPublicModelStatus(selectedModel);
          if (scanBtn) scanBtn.click();

          // Update Sub-HUD
          const nameEl = document.querySelector("#diff-model-name");
          const archTag = document.querySelector("#tag-arch-mode");
          const memTag = document.querySelector("#tag-memory-mode");
          const transTag = document.querySelector("#tag-transfer-mode");
          const loraTag = document.querySelector("#tag-lora-mode");

          const modelName = selectedModel.split("/").pop() || selectedModel;
          if (nameEl) nameEl.textContent = modelName;

          const archDisplayName = resp.architecture?.display_name || "ESTÁNDAR";
          if (archTag) archTag.textContent = `ARQ: ${archDisplayName.toUpperCase()}`;
          if (memTag) memTag.textContent = `PERFIL: ${memMode.toUpperCase()}`;
          if (transTag) transTag.textContent = `SALIDA: ${transMode.toUpperCase()}`;
          if (loraTag) loraTag.textContent = loraPath ? `LORA: ${loraPath.split("/").pop()} (${loraWeight}x)` : "LORA: NINGUNO";

          // Auto-adjust resolution inputs if default recommendation exists
          if (resp.architecture) {
            const cfgInput = document.querySelector("#cfg-slider");
            const cfgVal = document.querySelector("#cfg-val");
            const stepsInput = document.querySelector("#steps-slider");
            const stepsVal = document.querySelector("#steps-val");

            if (cfgInput && resp.architecture.default_cfg) {
              cfgInput.value = resp.architecture.default_cfg;
              if (cfgVal) cfgVal.textContent = resp.architecture.default_cfg;
            }

            if (stepsInput && resp.architecture.default_steps) {
              stepsInput.value = resp.architecture.default_steps;
              if (stepsVal) stepsVal.textContent = resp.architecture.default_steps;
            }

            if (resp.architecture.default_width) {
              const targetDimPill = document.querySelector(`.dim-pill[data-w="${resp.architecture.default_width}"]`);
              if (targetDimPill) {
                targetDimPill.click();
              }
            }
          }

          modal.style.display = "none";
        } else {
          const errData = await res.json().catch(() => ({ detail: "Error HTTP " + res.status }));
          cyberAlert("Error cargando modelo:\n" + (errData.detail || "Error desconocido"), "ERROR AL CARGAR MODELO", "error");
        }
      } catch (err) {
        cyberAlert("Fallo de conexión al cargar modelo:\n" + err, "ERROR DE COMUNICACIÓN", "error");
      } finally {
        applyBtn.disabled = false;
        applyBtn.textContent = "INICIALIZAR MOTOR Y CARGAR MODELO";
        const dlContainer = document.querySelector("#modal-download-progress-container");
        if (dlContainer) dlContainer.style.display = "none";
      }
    });
  }

  // Unload Model
  if (unloadBtn) {
    unloadBtn.addEventListener("click", async () => {
      try {
        const res = await fetch(`${API_BASE}/diffusion/unload`, { method: "POST" });
        if (res.ok) {
          const nameEl = document.querySelector("#diff-model-name");
          const archTag = document.querySelector("#tag-arch-mode");
          if (nameEl) nameEl.textContent = "MODELO DESCARGADO (VRAM LIBERADA)";
          if (archTag) archTag.textContent = "ARQUITECTURA: NINGUNA";
        }
      } catch (err) {
        cyberAlert("Error al descargar modelo:\n" + err, "ERROR DE DESCARGA", "error");
      }
    });
  }

  // Initial preview update
  if (modelDropdown) {
    updateArchitecturePreview(modelDropdown.value);
  }
}

function updateArchitecturePreview(modelId) {
  const archBadge = document.querySelector("#modal-arch-badge");
  const archDesc = document.querySelector("#modal-arch-desc");
  const archDims = document.querySelector("#modal-arch-dims");
  const archBox = document.querySelector("#modal-arch-info");

  if (!archBox || !modelId) return;

  const cached = modelsMetadataCache.get(modelId);
  if (cached) {
    if (archBadge) archBadge.textContent = cached.architecture || cached.arch_id || "SD 1.5";
    if (archDesc) archDesc.textContent = cached.description || "Modelo de difusión detectado";
    if (archDims) {
      const w = cached.default_width || 512;
      const h = cached.default_height || 512;
      const cfg = cached.default_cfg || 7.5;
      archDims.textContent = `${w}x${h} | CFG: ${cfg}`;
    }
  } else {
    // Check known IDs
    if (modelId.includes("sd-turbo")) {
      if (archBadge) archBadge.textContent = "SD 2.1 Fast";
      if (archDesc) archDesc.textContent = "Adversarial 1-4 pasos";
      if (archDims) archDims.textContent = "512x512 | CFG: 1.5";
    } else if (modelId.includes("SSD-1B")) {
      if (archBadge) archBadge.textContent = "SDXL Distill";
      if (archDesc) archDesc.textContent = "SDXL compacto 1024x1024";
      if (archDims) archDims.textContent = "1024x1024 | CFG: 7.0";
    } else if (modelId.includes("Anima") || modelId.includes("anima")) {
      if (archBadge) archBadge.textContent = "Anima DiT";
      if (archDesc) archDesc.textContent = "Diffusion Transformer 2B Anime";
      if (archDims) archDims.textContent = "768x768 | CFG: 4.0";
    } else {
      if (archBadge) archBadge.textContent = "SD 1.5";
      if (archDesc) archDesc.textContent = "Modelo estándar 512x512";
      if (archDims) archDims.textContent = "512x512 | CFG: 7.5";
    }
  }
}

async function initHardwareInfo() {
  try {
    const res = await fetch(`${API_BASE}/hardware/info`);
    if (res.ok) {
      const data = await res.json();
      const thresholds = data.gpu?.thresholds_mb;
      const totalVram = data.gpu?.vram_total_mb;

      if (thresholds) {
        const ahorroEl = document.querySelector("#limit-ahorro");
        const eqEl = document.querySelector("#limit-equilibrado");
        const altoEl = document.querySelector("#limit-alto");

        if (ahorroEl) ahorroEl.textContent = `<= 40% VRAM (~${thresholds.ahorro_40} MB)`;
        if (eqEl) eqEl.textContent = `<= 65% VRAM (~${thresholds.equilibrado_65} MB)`;
        if (altoEl) altoEl.textContent = `HASTA 100% VRAM (${totalVram} MB)`;
      }
    }
  } catch (err) {
    console.warn("No se pudo obtener información inicial de hardware:", err);
  }
}
