// ==========================================================================
// CYBER-IA // UI INTERACTION CONTROLLER (THEMES, TABS, CLOCK)
// ==========================================================================

import { fetchApiControlStatus } from "./api_control.js";

export function initUI() {
  initClock();
  initThemePicker();
  initScanlinesToggle();
  initNavTabs();
}

function initClock() {
  const clockEl = document.querySelector("#cyber-clock");
  function update() {
    const now = new Date();
    const timeStr = now.toTimeString().split(" ")[0];
    if (clockEl) {
      clockEl.textContent = `${timeStr} // UTC${now.getTimezoneOffset() <= 0 ? "+" : "-"}${Math.abs(now.getTimezoneOffset() / 60)}`;
    }
  }
  update();
  setInterval(update, 1000);
}

function initThemePicker() {
  const themeButtons = document.querySelectorAll(".neon-dot-btn");
  themeButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      themeButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const color = btn.getAttribute("data-color");
      document.documentElement.setAttribute("data-theme", color);
    });
  });
}

function initScanlinesToggle() {
  const toggleBtn = document.querySelector("#toggle-scanlines-btn");
  const layer = document.querySelector("#scanlines-layer");
  if (toggleBtn && layer) {
    toggleBtn.addEventListener("click", () => {
      const isHidden = layer.classList.toggle("hidden");
      toggleBtn.textContent = isHidden ? "SCANLINES: OFF" : "SCANLINES: ON";
    });
  }
}

function initNavTabs() {
  const navBtns = document.querySelectorAll(".nav-mode-btn");
  const views = document.querySelectorAll(".view-container");

  navBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      navBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      const targetId = btn.getAttribute("data-target");
      views.forEach((v) => {
        v.classList.remove("active");
        if (v.id === targetId) v.classList.add("active");
      });

      if (targetId === "view-api-control") {
        fetchApiControlStatus();
      }
    });
  });
}
