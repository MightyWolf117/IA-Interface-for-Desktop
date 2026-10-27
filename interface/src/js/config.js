// ==========================================================================
// CYBER-IA // CONFIG & NATIVE TAURI BRIDGE
// ==========================================================================

export const APP_NAME = "CYBER-IA";
export const APP_VERSION = "1.0.0";
export const API_BASE = "http://127.0.0.1:8000/api/v1";
export const WS_TELEMETRY_URL = "ws://127.0.0.1:8000/api/v1/ws/telemetry";

// Safe Tauri Core IPC accessor
export const tauriCore = window.__TAURI__?.core;

export async function invokeTauriCommand(command, args = {}) {
  if (tauriCore && typeof tauriCore.invoke === "function") {
    return await tauriCore.invoke(command, args);
  }
  // Graceful browser fallback simulation
  return `[SIM_TAURI_IPC] Comando '${command}' ejecutado en entorno web.`;
}
