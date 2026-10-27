// ==========================================================================
// CYBER-IA // API CONTROL & DIAGNOSTICS CONTROLLER
// ==========================================================================

import { API_BASE } from "./config.js";

export function initApiControlPanel() {
  const refreshBtn = document.querySelector("#refresh-logs-btn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", fetchApiControlStatus);
  }
}

export async function fetchApiControlStatus() {
  const endpointsTbody = document.querySelector("#endpoints-tbody");
  const logsEntries = document.querySelector("#logs-entries");

  try {
    const res = await fetch(`${API_BASE}/system/api-status`);
    if (res.ok) {
      const data = await res.json();

      // Endpoints Table
      if (endpointsTbody) {
        endpointsTbody.innerHTML = "";
        data.endpoints.forEach((ep) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><span class="method-badge ${ep.method}">${ep.method}</span></td>
            <td><code>${ep.path}</code></td>
            <td>${ep.summary}</td>
          `;
          endpointsTbody.appendChild(tr);
        });
      }

      // Logs Terminal
      if (logsEntries) {
        logsEntries.innerHTML = "";
        if (data.recent_requests.length === 0) {
          logsEntries.innerHTML = '<div class="log-line"><span>--</span><span>--</span><span>No hay solicitudes registradas aún</span><span>--</span><span>--</span><span>--</span></div>';
        } else {
          data.recent_requests.forEach((req) => {
            const statusClass = req.status_code < 300 ? "ok" : req.status_code < 500 ? "warn" : "err";
            const row = document.createElement("div");
            row.className = "log-line";
            row.innerHTML = `
              <span>${req.timestamp}</span>
              <span><span class="method-badge ${req.method}">${req.method}</span></span>
              <span>${req.path}</span>
              <span><strong class="status-badge-http ${statusClass}">${req.status_code}</strong></span>
              <span>${req.duration_ms} ms</span>
              <span>${req.client}</span>
            `;
            logsEntries.appendChild(row);
          });
        }
      }
    }
  } catch (err) {
    console.warn("Error al obtener diagnóstico del API:", err);
  }
}
