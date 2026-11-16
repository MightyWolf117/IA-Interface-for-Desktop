// ==========================================================================
// CYBER-IA // CHAT LLM CONTROLLER (MULTIMODAL & WEB SEARCH)
// ==========================================================================

import { API_BASE } from "./config.js";
import { cyberAlert, cyberConfirm } from "./dialog.js";

let activeModelId = "";
let activeModelProfile = null;
let conversationHistory = [];
let attachedDocs = [];
let attachedImages = [];
let webSearchActive = false;
let isStreaming = false;
let ollamaAlertPrompted = false;

export async function initChatLLM() {
  const promptForm = document.querySelector("#prompt-form");
  const promptTextarea = document.querySelector("#prompt-textarea");
  const chatFeed = document.querySelector("#chat-feed");
  const modelSelect = document.querySelector("#chat-model-select");
  const attachBtn = document.querySelector("#chat-attach-btn");
  const fileInput = document.querySelector("#chat-file-input");
  const webToggleBtn = document.querySelector("#chat-web-toggle-btn");
  const webLabel = document.querySelector("#chat-web-label");
  const attachmentsTray = document.querySelector("#chat-attachments-tray");

  // Chat Actions
  const clearBtn = document.querySelector("#chat-clear-btn");
  const newBtn = document.querySelector("#chat-new-btn");
  const exportBtn = document.querySelector("#chat-export-btn");

  // Modal Settings Elements
  const openSettingsBtn = document.querySelector("#open-chat-settings-btn");
  const settingsModal = document.querySelector("#modal-chat-settings");
  const closeSettingsBtn = document.querySelector("#modal-chat-settings-close-btn");
  const cancelSettingsBtn = document.querySelector("#modal-chat-settings-cancel-btn");
  const saveSettingsBtn = document.querySelector("#modal-chat-settings-save-btn");

  // Sliders in Settings
  const sliderCtx = document.querySelector("#setting-context-window");
  const valCtx = document.querySelector("#val-context-window");
  const sliderMaxTok = document.querySelector("#setting-max-tokens");
  const valMaxTok = document.querySelector("#val-max-tokens");
  const sliderTemp = document.querySelector("#setting-temperature");
  const valTemp = document.querySelector("#val-temperature");
  const sliderTopP = document.querySelector("#setting-top-p");
  const valTopP = document.querySelector("#val-top-p");

  // Ollama & Custom Local LLM Folder Controls
  const startOllamaBtn = document.querySelector("#chat-start-ollama-btn");
  const chatPathInput = document.querySelector("#chat-llm-path-input");
  const browseFolderBtn = document.querySelector("#chat-browse-folder-btn");
  const scanFolderBtn = document.querySelector("#chat-scan-folder-btn");
  const scanStatusLabel = document.querySelector("#chat-llm-scan-status");

  const savedPath = localStorage.getItem("cyber_llm_path") || (chatPathInput ? chatPathInput.value : "E:\\modelosLLM");
  if (chatPathInput) {
    chatPathInput.value = savedPath;
  }

  // 1. Cargar Modelos Disponibles y Cores
  await loadAvailableModels(savedPath);

  // Botón Encender Ollama manual
  if (startOllamaBtn) {
    startOllamaBtn.addEventListener("click", async () => {
      await startOllamaService();
    });
  }

  // Botón Examinar Carpeta Local de Modelos LLM (Native Windows Dialog)
  if (browseFolderBtn && chatPathInput) {
    browseFolderBtn.addEventListener("click", async () => {
      const origText = browseFolderBtn.innerHTML;
      browseFolderBtn.innerHTML = "<span>ABRIENDO...</span>";
      try {
        const res = await fetch(`${API_BASE}/system/browse-folder`, { method: "POST" });
        if (res.ok) {
          const data = await res.json();
          if (data.selected_path) {
            chatPathInput.value = data.selected_path;
            localStorage.setItem("cyber_llm_path", data.selected_path);
            if (scanFolderBtn) scanFolderBtn.click();
          }
        } else {
          cyberAlert("No se pudo abrir el explorador de carpetas de Windows.", "EXPLORADOR DE CARPETAS", "error");
        }
      } catch (err) {
        console.warn("[ChatLLM] Error abriendo diálogo nativo:", err);
        cyberAlert("Error al invocar diálogo de Windows: " + err, "EXPLORADOR DE CARPETAS", "error");
      } finally {
        browseFolderBtn.innerHTML = origText;
      }
    });
  }

  // Botón Escanear Carpeta Local de Modelos LLM
  if (scanFolderBtn && chatPathInput) {
    scanFolderBtn.addEventListener("click", async () => {
      const dirPath = chatPathInput.value.trim() || "models/llm";
      scanFolderBtn.textContent = "ESCANEANDO...";
      if (scanStatusLabel) scanStatusLabel.textContent = "Escaneando modelos en disco...";
      try {
        const res = await fetch(`${API_BASE}/chat/models/scan`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ directory_path: dirPath })
        });
        if (res.ok) {
          const data = await res.json();
          localStorage.setItem("cyber_llm_path", dirPath);
          if (scanStatusLabel) {
            scanStatusLabel.textContent = `Escaneo completado: ${data.count} modelos encontrados.`;
          }
          await loadAvailableModels(dirPath);
        } else {
          cyberAlert("Error al escanear carpeta de modelos LLM.", "ESCANEO LLM", "error");
        }
      } catch (err) {
        console.warn("[ChatLLM] Error escaneando carpeta:", err);
        cyberAlert("Fallo de conexión al escanear: " + err, "ESCANEO LLM", "error");
      } finally {
        scanFolderBtn.innerHTML = "<span>🔄 ESCANEAR</span>";
      }
    });
  }

  // 2. Event Listeners para Selección de Modelo
  if (modelSelect) {
    modelSelect.addEventListener("change", async (e) => {
      const selected = e.target.value;
      if (selected) {
        await switchActiveModel(selected);
      }
    });
  }

  // 3. Conmutador de Búsqueda Web
  if (webToggleBtn) {
    webToggleBtn.addEventListener("click", () => {
      webSearchActive = !webSearchActive;
      if (webSearchActive) {
        webToggleBtn.classList.add("active");
        if (webLabel) webLabel.textContent = "WEB: ON";
      } else {
        webToggleBtn.classList.remove("active");
        if (webLabel) webLabel.textContent = "WEB: OFF";
      }
    });
  }

  // 4. Captura de Portapapeles (Ctrl+V) para Imágenes y Capturas de Pantalla
  if (promptTextarea) {
    promptTextarea.addEventListener("paste", (e) => {
      const items = (e.clipboardData || e.originalEvent.clipboardData)?.items;
      if (!items) return;

      for (let index = 0; index < items.length; index++) {
        const item = items[index];
        if (item.type.indexOf("image") !== -1) {
          const blob = item.getAsFile();
          const reader = new FileReader();
          reader.onload = (event) => {
            const b64 = event.target.result;
            addAttachmentImage(b64, "Captura de pantalla (Portapapeles)");
          };
          reader.readAsDataURL(blob);
          e.preventDefault();
        }
      }
    });

    // Enter para enviar, Shift+Enter para salto de línea
    promptTextarea.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (promptForm) promptForm.dispatchEvent(new Event("submit"));
      }
    });
  }

  // 5. Botón de Adjuntar Archivos (PDF, DOCX, XLSX, CSV, Imágenes)
  if (attachBtn && fileInput) {
    attachBtn.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", async () => {
      const files = Array.from(fileInput.files);
      if (!files.length) return;

      for (const file of files) {
        await handleUploadedFile(file);
      }
      fileInput.value = "";
    });
  }

  // 6. Enviar Mensaje y Streaming de Respuesta
  if (promptForm && promptTextarea) {
    promptForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (isStreaming) return;

      const userText = promptTextarea.value.trim();
      if (!userText && !attachedImages.length && !attachedDocs.length) return;

      // Renderizar mensaje del usuario
      appendUserMessage(userText, [...attachedImages], [...attachedDocs]);

      // Guardar en historial conversacional
      conversationHistory.push({
        role: "user",
        content: userText || "[Elemento multimedia adjunto]"
      });

      // Preparar payloads
      const payloadDocs = [...attachedDocs];
      const payloadImages = [...attachedImages];

      // Limpiar entrada y bandeja de adjuntos
      promptTextarea.value = "";
      clearAttachments();

      // Iniciar mensaje del asistente con cursor de streaming
      const aiMsgElement = createAiMessagePlaceholder();
      const bodyContainer = aiMsgElement.querySelector(".msg-body");
      const cursorSpan = document.createElement("span");
      cursorSpan.className = "streaming-cursor";
      bodyContainer.appendChild(cursorSpan);

      isStreaming = true;
      const sendBtn = document.querySelector("#chat-send-btn");
      if (sendBtn) sendBtn.disabled = true;

      let fullAiResponse = "";
      let responseSources = [];

      try {
        const response = await fetch(`${API_BASE}/chat/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model: activeModelId,
            messages: conversationHistory,
            web_search: webSearchActive,
            attached_docs: payloadDocs,
            attached_images: payloadImages
          })
        });

        if (!response.ok) {
          throw new Error(`Error ${response.status}: ${await response.text()}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const cleanLine = line.trim();
            if (cleanLine.startsWith("data: ")) {
              try {
                const chunkData = JSON.parse(cleanLine.substring(6));
                if (chunkData.token) {
                  fullAiResponse += chunkData.token;
                  bodyContainer.textContent = fullAiResponse;
                  bodyContainer.appendChild(cursorSpan);
                  if (chatFeed) chatFeed.scrollTop = chatFeed.scrollHeight;
                }
                if (chunkData.done) {
                  if (chunkData.sources) responseSources = chunkData.sources;
                }
              } catch (_) {}
            }
          }
        }
      } catch (err) {
        fullAiResponse += `\n\n[ERROR]: ${err.message}`;
        bodyContainer.textContent = fullAiResponse;
      } finally {
        isStreaming = false;
        if (sendBtn) sendBtn.disabled = false;
        cursorSpan.remove();

        // Renderizar Markdown estructurado, bloques de código con botón de copiar y fuentes
        bodyContainer.innerHTML = renderMarkdown(fullAiResponse);
        if (responseSources.length > 0) {
          appendWebSourcesBox(bodyContainer, responseSources);
        }
        setupCodeCopyButtons(bodyContainer);

        // Registrar en historial
        conversationHistory.push({
          role: "assistant",
          content: fullAiResponse
        });

        if (chatFeed) chatFeed.scrollTop = chatFeed.scrollHeight;
      }
    });
  }

  // 7. Modal de Ajustes Específicos por Modelo
  setupSettingsModal(
    openSettingsBtn,
    settingsModal,
    closeSettingsBtn,
    cancelSettingsBtn,
    saveSettingsBtn,
    sliderCtx,
    valCtx,
    sliderMaxTok,
    valMaxTok,
    sliderTemp,
    valTemp,
    sliderTopP,
    valTopP
  );

  // 8. Botones de Limpiar y Exportar
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      conversationHistory = [];
      clearAttachments();
      if (chatFeed) {
        chatFeed.innerHTML = `
          <div class="message-wrapper system-msg">
            <div class="system-msg-content">
              <span class="neon-glyph">⚡</span>
              <span>[SISTEMA LIMPIADO]: Historial conversacional reiniciado. Enlace neural listo.</span>
            </div>
          </div>
        `;
      }
    });
  }

  if (newBtn) {
    newBtn.addEventListener("click", () => {
      conversationHistory = [];
      clearAttachments();
      if (promptTextarea) promptTextarea.value = "";
      if (chatFeed) {
        chatFeed.innerHTML = `
          <div class="message-wrapper system-msg">
            <div class="system-msg-content">
              <span class="neon-glyph">⚡</span>
              <span>[NUEVA CONVERSACIÓN]: Sesión activa iniciada con modelo ${activeModelId}.</span>
            </div>
          </div>
        `;
      }
    });
  }

  if (exportBtn) {
    exportBtn.addEventListener("click", exportConversationToMarkdown);
  }
}

// --------------------------------------------------------------------------
// CARGA Y SELECCIÓN DE MODELOS & GESTIÓN DE OLLAMA
// --------------------------------------------------------------------------
async function startOllamaService() {
  const ollamaStatusText = document.querySelector("#chat-ollama-status-text");
  const startOllamaBtn = document.querySelector("#chat-start-ollama-btn");
  const ollamaDot = document.querySelector("#chat-ollama-dot");

  if (startOllamaBtn) {
    startOllamaBtn.disabled = true;
    startOllamaBtn.textContent = "INICIANDO...";
  }
  if (ollamaStatusText) {
    ollamaStatusText.textContent = "OLLAMA: INICIANDO...";
  }
  if (ollamaDot) {
    ollamaDot.style.background = "#00f0ff";
    ollamaDot.style.boxShadow = "0 0 8px #00f0ff";
  }

  try {
    const res = await fetch(`${API_BASE}/chat/ollama/start`, { method: "POST" });
    const data = await res.json();
    if (data.success) {
      cyberAlert("Iniciando servicio de Ollama en segundo plano...\nEsperando enlace con el puerto 11434.", "SERVICIO OLLAMA", "info");
      // Esperar brevemente a que el servidor enlace el socket
      await new Promise((r) => setTimeout(r, 2500));
    } else {
      cyberAlert(data.message || "No se pudo iniciar el servicio de Ollama.", "SERVICIO OLLAMA", "error");
    }
  } catch (err) {
    console.warn("[ChatLLM] Error iniciando Ollama:", err);
    cyberAlert("Fallo de conexión al intentar iniciar Ollama: " + err, "SERVICIO OLLAMA", "error");
  } finally {
    if (startOllamaBtn) startOllamaBtn.disabled = false;
    const currentPath = document.querySelector("#chat-llm-path-input")?.value.trim() || "";
    await loadAvailableModels(currentPath);
  }
}

async function loadAvailableModels(customPath = "") {
  const modelSelect = document.querySelector("#chat-model-select");
  const ollamaDot = document.querySelector("#chat-ollama-dot");
  const ollamaStatusText = document.querySelector("#chat-ollama-status-text");
  const startOllamaBtn = document.querySelector("#chat-start-ollama-btn");
  const scanStatusLabel = document.querySelector("#chat-llm-scan-status");

  if (!modelSelect) return;

  try {
    const query = customPath ? `?custom_path=${encodeURIComponent(customPath)}` : "";
    const res = await fetch(`${API_BASE}/chat/models${query}`);
    if (!res.ok) return;

    const data = await res.json();
    const models = data.models || [];
    const isOnline = Boolean(data.ollama_online);

    // Actualizar estado visual de Ollama
    if (isOnline) {
      if (ollamaDot) {
        ollamaDot.style.background = "#00ff66";
        ollamaDot.style.boxShadow = "0 0 8px #00ff66";
      }
      if (ollamaStatusText) {
        ollamaStatusText.textContent = "OLLAMA: ONLINE (11434)";
        ollamaStatusText.style.color = "var(--neon-green, #00ff66)";
      }
      if (startOllamaBtn) startOllamaBtn.style.display = "none";
    } else {
      if (ollamaDot) {
        ollamaDot.style.background = "#ff3366";
        ollamaDot.style.boxShadow = "0 0 8px #ff3366";
      }
      if (ollamaStatusText) {
        ollamaStatusText.textContent = "OLLAMA: APAGADO";
        ollamaStatusText.style.color = "var(--neon-pink, #ff3366)";
      }
      if (startOllamaBtn) {
        startOllamaBtn.style.display = "inline-block";
        startOllamaBtn.textContent = "⚡ ENCENDER";
      }

      // Alerta al usuario si no está encendido (solo una vez por sesión o al cargar)
      if (!ollamaAlertPrompted) {
        ollamaAlertPrompted = true;
        setTimeout(async () => {
          const wantToStart = await cyberConfirm(
            "El servicio local de Ollama (127.0.0.1:11434) no está encendido.\n\n" +
            "¿Deseas iniciarlo ahora en segundo plano para habilitar la inferencia completa y todos tus modelos?\n\n" +
            "(Nota: También puedes usar tus modelos locales de la carpeta configurada sin inconvenientes).",
            "SERVICIO OLLAMA DETENIDO",
            "warning"
          );
          if (wantToStart) {
            await startOllamaService();
          }
        }, 200);
      }
    }

    if (scanStatusLabel && data.custom_path) {
      scanStatusLabel.textContent = `Ruta: ${data.custom_path} (${models.length} modelos detectados)`;
    }

    modelSelect.innerHTML = "";

    if (models.length === 0) {
      modelSelect.innerHTML = `<option value="">No hay modelos disponibles</option>`;
      return;
    }

    models.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m.id;
      const visionTag = m.is_vision ? " [VISIÓN]" : "";
      let sourceTag = "";
      if (m.source === "ollama") sourceTag = " (Ollama)";
      else if (m.source === "local_ollama_store") sourceTag = " (Almacén Local)";
      else if (m.source === "local_file") sourceTag = " (GGUF Local)";
      opt.textContent = `${m.name} [${m.parameters || "GGUF"}]${visionTag}${sourceTag}`;
      modelSelect.appendChild(opt);
    });

    // Mantener modelo activo actual o seleccionar el primero
    if (activeModelId && models.some((m) => m.id === activeModelId)) {
      modelSelect.value = activeModelId;
      await switchActiveModel(activeModelId);
    } else {
      await switchActiveModel(models[0].id);
    }
  } catch (err) {
    console.warn("[ChatLLM] Error cargando catálogo de modelos:", err);
  }
}

async function switchActiveModel(modelId) {
  activeModelId = modelId;

  // Actualizar tarjeta lateral del HUD
  const modelNameEl = document.querySelector("#chat-active-model-name");
  const modelMetaEl = document.querySelector("#chat-active-model-meta");
  const statusBadge = document.querySelector("#chat-engine-status-badge");
  const modelSelect = document.querySelector("#chat-model-select");

  if (modelSelect && modelSelect.value !== modelId) {
    modelSelect.value = modelId;
  }

  try {
    const res = await fetch(`${API_BASE}/chat/models/${encodeURIComponent(modelId)}/settings`);
    if (res.ok) {
      activeModelProfile = await res.json();
    }
  } catch (_) {
    activeModelProfile = { model_id: modelId, custom_name: modelId, core: "custom" };
  }

  const name = activeModelProfile?.custom_name || modelId.split(":")[0];
  const core = (activeModelProfile?.core || "custom").toUpperCase();
  const ctx = activeModelProfile?.context_window || 4096;

  if (modelNameEl) modelNameEl.textContent = name.toUpperCase();
  if (modelMetaEl) modelMetaEl.textContent = `CORE: ${core} // ${ctx} TOKENS`;
  if (statusBadge) {
    statusBadge.textContent = "MODELO LISTO // HUD";
  }
}

// --------------------------------------------------------------------------
// AJUSTES ESPECÍFICOS POR MODELO
// --------------------------------------------------------------------------
function setupSettingsModal(
  openBtn, modal, closeBtn, cancelBtn, saveBtn,
  sliderCtx, valCtx, sliderMaxTok, valMaxTok, sliderTemp, valTemp, sliderTopP, valTopP
) {
  if (!modal) return;

  const showModal = () => {
    if (!activeModelProfile) return;
    const titleEl = document.querySelector("#modal-chat-settings-title");
    if (titleEl) titleEl.textContent = `AJUSTES: ${activeModelProfile.custom_name || activeModelId}`;

    const inputName = document.querySelector("#setting-custom-name");
    const selectCore = document.querySelector("#setting-core-select");
    const textPrompt = document.querySelector("#setting-system-prompt");
    const checkWeb = document.querySelector("#setting-web-search-default");

    if (inputName) inputName.value = activeModelProfile.custom_name || "";
    if (selectCore) selectCore.value = activeModelProfile.core || "custom";
    if (textPrompt) textPrompt.value = activeModelProfile.system_prompt || "";

    if (sliderCtx && valCtx) {
      sliderCtx.value = activeModelProfile.context_window || 4096;
      valCtx.textContent = sliderCtx.value;
    }
    if (sliderMaxTok && valMaxTok) {
      sliderMaxTok.value = activeModelProfile.max_tokens || 2048;
      valMaxTok.textContent = sliderMaxTok.value;
    }
    if (sliderTemp && valTemp) {
      sliderTemp.value = Number(activeModelProfile.temperature || 0.7).toFixed(2);
      valTemp.textContent = sliderTemp.value;
    }
    if (sliderTopP && valTopP) {
      sliderTopP.value = Number(activeModelProfile.top_p || 0.9).toFixed(2);
      valTopP.textContent = sliderTopP.value;
    }
    if (checkWeb) {
      checkWeb.checked = !!activeModelProfile.web_search_enabled;
    }

    modal.style.display = "flex";
  };

  const hideModal = () => { modal.style.display = "none"; };

  if (openBtn) openBtn.addEventListener("click", showModal);
  if (closeBtn) closeBtn.addEventListener("click", hideModal);
  if (cancelBtn) cancelBtn.addEventListener("click", hideModal);

  // Sync sliders con etiquetas numéricas
  if (sliderCtx && valCtx) sliderCtx.addEventListener("input", () => valCtx.textContent = sliderCtx.value);
  if (sliderMaxTok && valMaxTok) sliderMaxTok.addEventListener("input", () => valMaxTok.textContent = sliderMaxTok.value);
  if (sliderTemp && valTemp) sliderTemp.addEventListener("input", () => valTemp.textContent = Number(sliderTemp.value).toFixed(2));
  if (sliderTopP && valTopP) sliderTopP.addEventListener("input", () => valTopP.textContent = Number(sliderTopP.value).toFixed(2));

  // Guardar Ajustes
  if (saveBtn) {
    saveBtn.addEventListener("click", async () => {
      const inputName = document.querySelector("#setting-custom-name");
      const selectCore = document.querySelector("#setting-core-select");
      const textPrompt = document.querySelector("#setting-system-prompt");
      const checkWeb = document.querySelector("#setting-web-search-default");

      const payload = {
        custom_name: inputName?.value.trim() || activeModelId,
        core: selectCore?.value || "custom",
        system_prompt: textPrompt?.value.trim() || "",
        context_window: parseInt(sliderCtx?.value || "4096", 10),
        max_tokens: parseInt(sliderMaxTok?.value || "2048", 10),
        temperature: parseFloat(sliderTemp?.value || "0.7"),
        top_p: parseFloat(sliderTopP?.value || "0.9"),
        web_search_enabled: !!checkWeb?.checked
      };

      try {
        const res = await fetch(`${API_BASE}/chat/models/${encodeURIComponent(activeModelId)}/settings`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const resData = await res.json();
          activeModelProfile = resData.settings;
          await switchActiveModel(activeModelId);
          hideModal();
          cyberAlert("Ajustes del modelo guardados correctamente.", "AJUSTES GUARDADOS", "success");
        } else {
          cyberAlert("Error guardando ajustes en backend.", "ERROR DE AJUSTES", "error");
        }
      } catch (err) {
        cyberAlert("Fallo de conexión al guardar ajustes: " + err, "ERROR DE CONEXIÓN", "error");
      }
    });
  }
}

// --------------------------------------------------------------------------
// GESTIÓN DE ADJUNTOS (IMÁGENES Y DOCUMENTOS)
// --------------------------------------------------------------------------
function addAttachmentImage(base64Data, label = "Imagen") {
  attachedImages.push(base64Data);
  renderAttachmentsTray();
}

async function handleUploadedFile(file) {
  const isImage = file.type.startsWith("image/");
  if (isImage) {
    const reader = new FileReader();
    reader.onload = (e) => {
      addAttachmentImage(e.target.result, file.name);
    };
    reader.readAsDataURL(file);
    return;
  }

  // Si es documento o tabla, subirlo al extractor del backend
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${API_BASE}/chat/upload`, {
      method: "POST",
      body: formData
    });

    if (res.ok) {
      const data = await res.json();
      attachedDocs.push(data.file);
      renderAttachmentsTray();
    } else {
      cyberAlert(`No se pudo procesar el archivo '${file.name}'.`, "ERROR DE ARCHIVO", "error");
    }
  } catch (err) {
    cyberAlert(`Error procesando adjunto: ${err}`, "ERROR DE ADJUNTO", "error");
  }
}

function renderAttachmentsTray() {
  const tray = document.querySelector("#chat-attachments-tray");
  if (!tray) return;

  tray.innerHTML = "";

  if (attachedImages.length === 0 && attachedDocs.length === 0) {
    tray.style.display = "none";
    return;
  }

  tray.style.display = "flex";

  // Renderizar imágenes
  attachedImages.forEach((b64, idx) => {
    const chip = document.createElement("div");
    chip.className = "attachment-chip chip-image";
    chip.innerHTML = `
      <img src="${b64}" alt="Captura">
      <span class="chip-name">Imagen_${idx + 1}</span>
      <button type="button" class="chip-remove-btn" data-img-idx="${idx}">✕</button>
    `;
    chip.querySelector(".chip-remove-btn").addEventListener("click", () => {
      attachedImages.splice(idx, 1);
      renderAttachmentsTray();
    });
    tray.appendChild(chip);
  });

  // Renderizar documentos
  attachedDocs.forEach((doc, idx) => {
    const chip = document.createElement("div");
    chip.className = "attachment-chip chip-doc";
    chip.innerHTML = `
      <span>📄</span>
      <span class="chip-name">${doc.filename}</span>
      <button type="button" class="chip-remove-btn" data-doc-idx="${idx}">✕</button>
    `;
    chip.querySelector(".chip-remove-btn").addEventListener("click", () => {
      attachedDocs.splice(idx, 1);
      renderAttachmentsTray();
    });
    tray.appendChild(chip);
  });
}

function clearAttachments() {
  attachedImages = [];
  attachedDocs = [];
  renderAttachmentsTray();
}

// --------------------------------------------------------------------------
// RENDERIZADO DE MENSAJES Y MARKDOWN
// --------------------------------------------------------------------------
function appendUserMessage(text, images, docs) {
  const chatFeed = document.querySelector("#chat-feed");
  if (!chatFeed) return;

  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper user-msg";

  let mediaHtml = "";
  if (images && images.length) {
    mediaHtml += `<div class="user-msg-attachments">`;
    images.forEach((imgB64) => {
      mediaHtml += `<img src="${imgB64}" class="user-msg-thumb" alt="Adjunto">`;
    });
    mediaHtml += `</div>`;
  }

  if (docs && docs.length) {
    mediaHtml += `<div class="user-msg-attachments">`;
    docs.forEach((d) => {
      mediaHtml += `<span class="user-msg-doc-tag">📄 ${d.filename}</span>`;
    });
    mediaHtml += `</div>`;
  }

  wrapper.innerHTML = `
    <div class="msg-header">
      <span class="avatar-title">NETRUNNER // OPERADOR</span>
    </div>
    <div class="msg-body">
      ${mediaHtml}
      <p>${escapeHtml(text)}</p>
    </div>
  `;

  chatFeed.appendChild(wrapper);
  chatFeed.scrollTop = chatFeed.scrollHeight;
}

function createAiMessagePlaceholder() {
  const chatFeed = document.querySelector("#chat-feed");
  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper ai-msg";
  wrapper.innerHTML = `
    <div class="msg-header">
      <span class="avatar-title">AI_CORE // ${activeModelId.toUpperCase()}</span>
    </div>
    <div class="msg-body"></div>
  `;
  if (chatFeed) {
    chatFeed.appendChild(wrapper);
    chatFeed.scrollTop = chatFeed.scrollHeight;
  }
  return wrapper;
}

function appendWebSourcesBox(container, sources) {
  if (!sources || !sources.length) return;

  const box = document.createElement("div");
  box.className = "web-sources-box";
  let itemsHtml = "";
  sources.forEach((s) => {
    itemsHtml += `
      <li class="web-source-item">
        <a href="${s.url}" target="_blank" rel="noopener noreferrer">
          <span>🔗</span>
          <span>${escapeHtml(s.title || s.url)}</span>
        </a>
      </li>
    `;
  });

  box.innerHTML = `
    <div class="web-sources-title">
      <span>🌐</span> FUENTES Y ENLACES DE BÚSQUEDA WEB:
    </div>
    <ul class="web-sources-list">
      ${itemsHtml}
    </ul>
  `;

  container.appendChild(box);
}

function renderMarkdown(text) {
  if (!text) return "";

  // 1. Bloques de código preformateados (```lang ... ```)
  const codeBlocks = [];
  let formatted = text.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const idx = codeBlocks.length;
    codeBlocks.push({ lang: lang || "code", code: code });
    return `__CODE_BLOCK_${idx}__`;
  });

  // 2. Escape HTML básico en texto normal
  formatted = escapeHtml(formatted);

  // 3. Negrita (**texto**) y Cursiva (*texto*)
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  formatted = formatted.replace(/\*(.*?)\*/g, "<em>$1</em>");

  // 4. Código inline (`code`)
  formatted = formatted.replace(/`([^`]+)`/g, "<code>$1</code>");

  // 5. Enlaces Markdown [texto](url)
  formatted = formatted.replace(/\[(.*?)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" class="chat-link">$1</a>');

  // 6. Encabezados (#, ##, ###)
  formatted = formatted.replace(/^### (.*$)/gim, "<h3>$1</h3>");
  formatted = formatted.replace(/^## (.*$)/gim, "<h2>$1</h2>");
  formatted = formatted.replace(/^# (.*$)/gim, "<h1>$1</h1>");

  // 7. Párrafos y saltos de línea
  formatted = formatted.replace(/\n\n/g, "</p><p>");
  formatted = formatted.replace(/\n/g, "<br>");
  formatted = `<p>${formatted}</p>`;

  // 8. Restaurar bloques de código con cabecera y botón de copiar
  codeBlocks.forEach((item, idx) => {
    const blockHtml = `
      <div class="code-block-wrapper">
        <div class="code-header">
          <span>${item.lang.toUpperCase()}</span>
          <button type="button" class="copy-code-btn" data-code="${escapeAttribute(item.code)}">COPIAR</button>
        </div>
        <pre><code>${escapeHtml(item.code)}</code></pre>
      </div>
    `;
    formatted = formatted.replace(`__CODE_BLOCK_${idx}__`, blockHtml);
  });

  return formatted;
}

function setupCodeCopyButtons(container) {
  const buttons = container.querySelectorAll(".copy-code-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const code = btn.getAttribute("data-code");
      if (code) {
        navigator.clipboard.writeText(code).then(() => {
          btn.textContent = "COPIADO ✔";
          setTimeout(() => btn.textContent = "COPIAR", 2000);
        });
      }
    });
  });
}

function exportConversationToMarkdown() {
  if (!conversationHistory.length) {
    cyberAlert("No hay mensajes en la conversación para exportar.", "AVISO", "warning");
    return;
  }

  let md = `# CYBER-IA // Transcripción de Sesión Neural\n`;
  md += `**Modelo Activo:** ${activeModelId}\n`;
  md += `**Fecha:** ${new Date().toLocaleString()}\n\n---\n\n`;

  conversationHistory.forEach((msg) => {
    const sender = msg.role === "user" ? "### 👤 USUARIO" : `### ⚡ ASISTENTE (${activeModelId})`;
    md += `${sender}\n\n${msg.content}\n\n---\n\n`;
  });

  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `CyberIA_Chat_${Date.now()}.md`;
  a.click();
  URL.revokeObjectURL(url);
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function escapeAttribute(str) {
  if (!str) return "";
  return str.replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
