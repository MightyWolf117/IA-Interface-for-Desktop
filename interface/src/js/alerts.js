// ==========================================================================
// CYBER-IA // CRITICAL SYSTEM ALERTS & STABILITY MONITOR
// ==========================================================================

import { API_BASE } from "./config.js";
import { cyberAlert } from "./dialog.js";

let alertBannerEl = null;
let alertMetricTagEl = null;
let alertDescEl = null;
let purgeBtnEl = null;
let offloadBtnEl = null;
let dismissBtnEl = null;

let isUserDismissed = false;

export function initAlertsSystem() {
  alertBannerEl = document.querySelector("#system-critical-alert");
  alertMetricTagEl = document.querySelector("#alert-metric-tag");
  alertDescEl = document.querySelector("#alert-desc");
  purgeBtnEl = document.querySelector("#alert-purge-btn");
  offloadBtnEl = document.querySelector("#alert-offload-btn");
  dismissBtnEl = document.querySelector("#alert-dismiss-btn");

  if (dismissBtnEl) {
    dismissBtnEl.addEventListener("click", () => {
      isUserDismissed = true;
      if (alertBannerEl) alertBannerEl.style.display = "none";
    });
  }

  // Quick action: Purge VRAM immediately
  if (purgeBtnEl) {
    purgeBtnEl.addEventListener("click", async () => {
      purgeBtnEl.textContent = "PURGANDO...";
      try {
        const res = await fetch(`${API_BASE}/diffusion/unload`, { method: "POST" });
        if (res.ok) {
          hideCriticalAlert();
          const nameEl = document.querySelector("#diff-model-name");
          if (nameEl) nameEl.textContent = "VRAM PURGADA DE EMERGENCIA";
        }
      } catch (err) {
        cyberAlert("Fallo al purgar VRAM:\n" + err, "ALERTA DE MEMORIA", "error");
      } finally {
        purgeBtnEl.textContent = "PURGAR VRAM AHORA";
      }
    });
  }

  // Quick action: Switch active model to Ahorro (Sequential CPU Offload to RAM)
  if (offloadBtnEl) {
    offloadBtnEl.addEventListener("click", async () => {
      offloadBtnEl.textContent = "APLICANDO...";
      try {
        const statusRes = await fetch(`${API_BASE}/diffusion/status`);
        const statusData = await statusRes.json();
        const activeModel = statusData.active_model || "runwayml/stable-diffusion-v1-5";

        const loadRes = await fetch(`${API_BASE}/diffusion/load`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model_id_or_path: activeModel,
            memory_mode: "ahorro",
            transfer_mode: "base64"
          })
        });

        if (loadRes.ok) {
          hideCriticalAlert();
          const memTag = document.querySelector("#tag-memory-mode");
          if (memTag) memTag.textContent = "PERFIL: AHORRO (CPU OFFLOAD)";
        }
      } catch (err) {
        cyberAlert("Fallo al aplicar modo Ahorro:\n" + err, "MODO AHORRO", "error");
      } finally {
        offloadBtnEl.textContent = "ACTIVAR MODO AHORRO";
      }
    });
  }
}

/**
 * Evalúa los recursos en tiempo real (<100ms) y activa la alerta si se superan los límites de seguridad
 */
export function evaluateSystemLimits(vramAllocated, vramTotal, ramPercent) {
  if (!alertBannerEl) return;

  const vramPercent = vramTotal > 0 ? Math.round((vramAllocated / vramTotal) * 100) : 0;
  const isVramCritical = vramPercent >= 88;
  const isRamCritical = ramPercent >= 90;

  if (isVramCritical || isRamCritical) {
    if (!isUserDismissed) {
      alertBannerEl.style.display = "flex";

      if (isVramCritical && isRamCritical) {
        if (alertMetricTagEl) alertMetricTagEl.textContent = `VRAM: ${vramPercent}% | RAM: ${ramPercent}%`;
        if (alertDescEl) alertDescEl.textContent = "Alerta crítica de estabilidad: VRAM y memoria RAM saturadas al límite. Peligro inminente de cierre inesperado o bloqueo de controladores GPU.";
      } else if (isVramCritical) {
        if (alertMetricTagEl) alertMetricTagEl.textContent = `VRAM: ${vramPercent}% (LÍMITE CRÍTICO)`;
        if (alertDescEl) alertDescEl.textContent = `La GPU ha alcanzado ${vramAllocated}/${vramTotal} MB. Se recomienda purgar memoria o activar el modo Ahorro para derivar tensores a la memoria RAM.`;
      } else {
        if (alertMetricTagEl) alertMetricTagEl.textContent = `RAM SISTEMA: ${ramPercent}% (LÍMITE CRÍTICO)`;
        if (alertDescEl) alertDescEl.textContent = "La memoria RAM del equipo está al borde de su capacidad máxima. Riesgo de congelamiento del sistema operativo.";
      }
    }
  } else {
    // Drop back to safe zone, reset dismissal state
    hideCriticalAlert();
    isUserDismissed = false;
  }
}

export function hideCriticalAlert() {
  if (alertBannerEl) {
    alertBannerEl.style.display = "none";
  }
}
