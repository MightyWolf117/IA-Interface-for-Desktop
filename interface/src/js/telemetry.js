// ==========================================================================
// CYBER-IA // REAL-TIME TELEMETRY (<100ms WEBSOCKET STREAM)
// ==========================================================================

import { WS_TELEMETRY_URL } from "./config.js";
import { evaluateSystemLimits } from "./alerts.js";

let telemetrySocket = null;
let telemetryReconnectTimer = null;

export function initWebSocketTelemetry() {
  const vramText = document.querySelector("#hud-vram-text");
  const ramText = document.querySelector("#hud-ram-text");
  const wsText = document.querySelector("#hud-ws-text");
  const vramDot = document.querySelector("#vram-dot");

  try {
    telemetrySocket = new WebSocket(WS_TELEMETRY_URL);

    telemetrySocket.onopen = () => {
      if (wsText) {
        wsText.textContent = "ONLINE (<80ms)";
        wsText.style.color = "var(--neon-green)";
      }
    };

    telemetrySocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Hardware Telemetry packet (<80ms)
        if (data.type === "hardware_telemetry") {
          const gpu = data.telemetry?.gpu;
          const ram = data.telemetry?.system;

          if (gpu && vramText) {
            if (gpu.available && gpu.vram_total_mb > 0) {
              const alloc = Math.round(gpu.vram_allocated_mb || 0);
              const total = Math.round(gpu.vram_total_mb);
              const pct = Math.round((alloc / total) * 100);
              vramText.textContent = `${alloc} / ${total} MB [${pct}%]`;

              // Color coding status dot
              if (vramDot) {
                vramDot.className = "status-dot " + (pct > 80 ? "red" : pct > 45 ? "yellow" : "green");
              }

              // Real-time Critical Limits Safety Evaluation
              if (ram) {
                evaluateSystemLimits(alloc, total, ram.ram_percent);
              }
            } else {
              vramText.textContent = "SIN CUDA (MODO CPU)";
              if (vramDot) vramDot.className = "status-dot yellow";
            }
          }

          if (ram && ramText) {
            const usedGb = (ram.ram_used_mb / 1024).toFixed(1);
            const totalGb = (ram.ram_total_mb / 1024).toFixed(1);
            ramText.textContent = `${usedGb} / ${totalGb} GB [${ram.ram_percent}%]`;
          }
        }

        // Generation Step Progress packet
        if (data.type === "generation_progress") {
          const progContainer = document.querySelector("#gen-progress-container");
          const progFill = document.querySelector("#gen-progress-fill");
          const progStatus = document.querySelector("#prog-status-text");
          const progPercent = document.querySelector("#prog-percent-text");

          if (progContainer) progContainer.style.display = "flex";
          if (progFill) progFill.style.width = `${data.percent}%`;
          if (progStatus) progStatus.textContent = `INFERENCIA PASO ${data.step}/${data.total_steps}`;
          if (progPercent) progPercent.textContent = `${data.percent}%`;
        }
      } catch (err) {
        console.error("Error al procesar paquete de telemetría:", err);
      }
    };

    telemetrySocket.onclose = () => {
      if (wsText) {
        wsText.textContent = "RECONECTANDO...";
        wsText.style.color = "var(--neon-pink)";
      }
      clearTimeout(telemetryReconnectTimer);
      telemetryReconnectTimer = setTimeout(initWebSocketTelemetry, 3000);
    };

    telemetrySocket.onerror = () => {
      if (telemetrySocket) telemetrySocket.close();
    };
  } catch (e) {
    console.warn("WebSocket no disponible, reintentando...", e);
  }
}
