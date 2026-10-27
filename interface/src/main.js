// ==========================================================================
// CYBER-IA // MAIN MODULAR APP ORCHESTRATOR
// ==========================================================================

import { initUI } from "./js/ui.js";
import { initAlertsSystem } from "./js/alerts.js";
import { initWebSocketTelemetry } from "./js/telemetry.js";
import { initModelConfigModal } from "./js/model_modal.js";
import { initDiffusionStudio } from "./js/diffusion.js";
import { initChatLLM } from "./js/chat.js";
import { initApiControlPanel } from "./js/api_control.js";

window.addEventListener("DOMContentLoaded", () => {
  // 1. Initialize UI elements (Clock, Themes, Tabs, Scanlines)
  initUI();

  // 2. Initialize Emergency System Limits Alert Monitor
  initAlertsSystem();

  // 3. Connect to Ultra Low-Latency Telemetry Stream (<80ms)
  initWebSocketTelemetry();

  // 4. Initialize Model Scanner & Configuration Modal
  initModelConfigModal();

  // 5. Initialize Diffusion Multimedia Studio
  initDiffusionStudio();

  // 6. Initialize Chat LLM Console
  initChatLLM();

  // 7. Initialize API Control & Diagnostics Panel
  initApiControlPanel();
});
