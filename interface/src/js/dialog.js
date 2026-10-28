// ==========================================================================
// CYBER-IA // CUSTOM CYBERPUNK HUD MODAL DIALOGS
// Replaces native browser/WebView2 alerts, confirms, and prompts
// ==========================================================================

let overlayEl = null;
let cardEl = null;
let titleEl = null;
let iconEl = null;
let badgeEl = null;
let messageEl = null;
let inputWrapEl = null;
let inputEl = null;
let okBtnEl = null;
let cancelBtnEl = null;
let closeBtnEl = null;

let currentResolve = null;
let activeMode = "alert"; // "alert" | "confirm" | "prompt"

function ensureDialogDOM() {
  if (overlayEl) return;

  let existing = document.getElementById("cyber-dialog-overlay");
  if (!existing) {
    const markup = `
      <div class="cyber-dialog-overlay" id="cyber-dialog-overlay" style="display: none;">
        <div class="cyber-dialog-card" id="cyber-dialog-card">
          <div class="cyber-dialog-header">
            <div class="cyber-dialog-title" id="cyber-dialog-title">
              <span class="cyber-dialog-icon" id="cyber-dialog-icon">⚡</span>
              <span id="cyber-dialog-title-text">SISTEMA // NOTIFICACIÓN</span>
            </div>
            <button class="cyber-dialog-close-btn" id="cyber-dialog-close-btn" title="Cerrar">✕</button>
          </div>
          <div class="cyber-dialog-body">
            <div class="cyber-dialog-badge" id="cyber-dialog-badge">STATUS: INFO</div>
            <div class="cyber-dialog-message" id="cyber-dialog-message"></div>
            <div id="cyber-dialog-input-wrap" style="display: none;">
              <input type="text" class="cyber-dialog-input" id="cyber-dialog-input" spellcheck="false" autocomplete="off" />
            </div>
          </div>
          <div class="cyber-dialog-footer">
            <button type="button" class="cyber-btn" id="cyber-dialog-cancel-btn" style="display: none;">CANCELAR</button>
            <button type="button" class="cyber-btn cyber-btn-primary" id="cyber-dialog-ok-btn">ACEPTAR</button>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML("beforeend", markup);
  }

  overlayEl = document.getElementById("cyber-dialog-overlay");
  cardEl = document.getElementById("cyber-dialog-card");
  titleEl = document.getElementById("cyber-dialog-title-text");
  iconEl = document.getElementById("cyber-dialog-icon");
  badgeEl = document.getElementById("cyber-dialog-badge");
  messageEl = document.getElementById("cyber-dialog-message");
  inputWrapEl = document.getElementById("cyber-dialog-input-wrap");
  inputEl = document.getElementById("cyber-dialog-input");
  okBtnEl = document.getElementById("cyber-dialog-ok-btn");
  cancelBtnEl = document.getElementById("cyber-dialog-cancel-btn");
  closeBtnEl = document.getElementById("cyber-dialog-close-btn");

  okBtnEl.addEventListener("click", () => handleAction(true));
  cancelBtnEl.addEventListener("click", () => handleAction(false));
  closeBtnEl.addEventListener("click", () => handleAction(false));

  overlayEl.addEventListener("click", (e) => {
    if (e.target === overlayEl) {
      handleAction(false);
    }
  });

  window.addEventListener("keydown", (e) => {
    if (overlayEl && overlayEl.style.display !== "none") {
      if (e.key === "Enter") {
        e.preventDefault();
        handleAction(true);
      } else if (e.key === "Escape") {
        e.preventDefault();
        handleAction(false);
      }
    }
  });
}

function handleAction(isConfirm) {
  if (!overlayEl || overlayEl.style.display === "none") return;

  const resolve = currentResolve;
  currentResolve = null;
  overlayEl.style.display = "none";

  if (!resolve) return;

  if (activeMode === "alert") {
    resolve();
  } else if (activeMode === "confirm") {
    resolve(Boolean(isConfirm));
  } else if (activeMode === "prompt") {
    resolve(isConfirm ? (inputEl ? inputEl.value : "") : null);
  }
}

function showDialog({ title, message, type = "info", mode = "alert", defaultValue = "" }) {
  ensureDialogDOM();
  activeMode = mode;

  // Cleanup card classes
  cardEl.classList.remove("dialog-error", "dialog-warning", "dialog-success", "dialog-info");
  cardEl.classList.add(`dialog-${type}`);

  // Icons and badges
  const icons = {
    error: "⚠️",
    warning: "⚡",
    success: "✅",
    info: "ℹ️"
  };

  const defaultTitles = {
    error: "ERROR DEL SISTEMA",
    warning: "ADVERTENCIA NEURAL",
    success: "OPERACIÓN COMPLETADA",
    info: "NOTIFICACIÓN HUD"
  };

  iconEl.textContent = icons[type] || "⚡";
  titleEl.textContent = title || defaultTitles[type] || "MENSAJE DEL SISTEMA";
  badgeEl.textContent = `CANAL: ${type.toUpperCase()}`;
  messageEl.textContent = String(message || "");

  // Configure mode controls
  if (mode === "prompt") {
    inputWrapEl.style.display = "block";
    inputEl.value = defaultValue || "";
    cancelBtnEl.style.display = "inline-block";
    okBtnEl.style.display = "inline-block";
    setTimeout(() => inputEl.focus(), 50);
  } else if (mode === "confirm") {
    inputWrapEl.style.display = "none";
    cancelBtnEl.style.display = "inline-block";
    okBtnEl.style.display = "inline-block";
    setTimeout(() => okBtnEl.focus(), 50);
  } else {
    // alert
    inputWrapEl.style.display = "none";
    cancelBtnEl.style.display = "none";
    okBtnEl.style.display = "inline-block";
    setTimeout(() => okBtnEl.focus(), 50);
  }

  overlayEl.style.display = "flex";

  return new Promise((resolve) => {
    currentResolve = resolve;
  });
}

/**
 * Muestra una alerta con estética Cyberpunk HUD.
 * @param {string} message - Mensaje o detalle del error.
 * @param {string} [title] - Título en el encabezado.
 * @param {"info" | "warning" | "error" | "success"} [type="info"] - Estilo visual del diálogo.
 * @returns {Promise<void>}
 */
export function cyberAlert(message, title, type = "info") {
  // Auto-detect error type if message contains error keywords and type is default
  if (type === "info" && typeof message === "string") {
    const lower = message.toLowerCase();
    if (lower.includes("error") || lower.includes("fallo") || lower.includes("crítico")) {
      type = "error";
    } else if (lower.includes("advertencia") || lower.includes("límite")) {
      type = "warning";
    }
  }
  return showDialog({ message, title, type, mode: "alert" });
}

/**
 * Muestra un diálogo de confirmación con botones ACEPTAR y CANCELAR.
 * @param {string} message - Pregunta o texto de confirmación.
 * @param {string} [title] - Título del diálogo.
 * @param {"info" | "warning" | "error" | "success"} [type="warning"] - Estilo visual.
 * @returns {Promise<boolean>}
 */
export function cyberConfirm(message, title, type = "warning") {
  return showDialog({ message, title, type, mode: "confirm" });
}

/**
 * Muestra un diálogo para ingreso de texto por el usuario.
 * @param {string} message - Prompt o instrucción.
 * @param {string} [defaultValue=""] - Valor por defecto.
 * @param {string} [title] - Título del diálogo.
 * @returns {Promise<string|null>}
 */
export function cyberPrompt(message, defaultValue = "", title = "ENTRADA DE DATOS") {
  return showDialog({ message, title, type: "info", mode: "prompt", defaultValue });
}

/**
 * Inicializa el sistema de diálogos y sobrescribe globalmente window.alert, window.confirm y window.prompt
 * para garantizar que WebView2 nunca despliegue los cuadros grises nativos.
 */
export function initDialogSystem() {
  ensureDialogDOM();

  window.alert = function (message) {
    return cyberAlert(message);
  };

  window.confirm = function (message) {
    return cyberConfirm(message);
  };

  window.prompt = function (message, defaultValue) {
    return cyberPrompt(message, defaultValue);
  };

  console.log("[CYBER-IA] Sistema de Diálogos Cyberpunk HUD inicializado y vinculado a window.alert.");
}

