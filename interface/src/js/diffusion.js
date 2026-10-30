// ==========================================================================
// CYBER-IA // DIFFUSION MULTIMEDIA STUDIO CONTROLLER
// ==========================================================================

import { API_BASE } from "./config.js";
import { cyberAlert } from "./dialog.js";

let currentWidth = 512;
let currentHeight = 512;

export function initDiffusionStudio() {
  const form = document.querySelector("#diffusion-form");
  const promptInput = document.querySelector("#prompt-input");
  const negPromptInput = document.querySelector("#neg-prompt-input");
  const stepsSlider = document.querySelector("#steps-slider");
  const stepsVal = document.querySelector("#steps-val");
  const cfgSlider = document.querySelector("#cfg-slider");
  const cfgVal = document.querySelector("#cfg-val");
  const seedInput = document.querySelector("#seed-input");
  const randomSeedBtn = document.querySelector("#random-seed-btn");
  const genBtn = document.querySelector("#generate-btn");

  const canvasEmpty = document.querySelector("#canvas-empty");
  const renderedImg = document.querySelector("#rendered-image");
  const metaBar = document.querySelector("#canvas-meta-bar");
  const metaTime = document.querySelector("#meta-time");
  const metaSeed = document.querySelector("#meta-seed");
  const metaVram = document.querySelector("#meta-vram");
  const downloadBtn = document.querySelector("#download-img-btn");
  const progressContainer = document.querySelector("#gen-progress-container");

  // Presets
  const presetChips = document.querySelectorAll(".preset-chip");
  presetChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      if (promptInput) {
        promptInput.value = chip.getAttribute("data-prompt");
        promptInput.focus();
      }
    });
  });

  // Slider Values
  if (stepsSlider && stepsVal) {
    stepsSlider.addEventListener("input", () => (stepsVal.textContent = stepsSlider.value));
  }
  if (cfgSlider && cfgVal) {
    cfgSlider.addEventListener("input", () => (cfgVal.textContent = cfgSlider.value));
  }

  // Dimensions Pills
  const dimPills = document.querySelectorAll(".dim-pill");
  dimPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      dimPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      currentWidth = parseInt(pill.getAttribute("data-w") || "512", 10);
      currentHeight = parseInt(pill.getAttribute("data-h") || "512", 10);
    });
  });

  // Randomize Seed
  if (randomSeedBtn && seedInput) {
    randomSeedBtn.addEventListener("click", () => {
      seedInput.value = Math.floor(Math.random() * 10000000);
    });
  }

  // Generate Image
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const prompt = promptInput?.value.trim();
      if (!prompt) return;

      const negativePrompt = negPromptInput?.value.trim() || undefined;
      const steps = parseInt(stepsSlider?.value || "20", 10);
      const cfg = parseFloat(cfgSlider?.value || "7.5");
      const seed = seedInput?.value ? parseInt(seedInput.value, 10) : undefined;

      if (genBtn) {
        genBtn.disabled = true;
        genBtn.classList.add("loading");
        const genText = genBtn.querySelector(".gen-text");
        if (genText) genText.textContent = "GENERANDO...";
      }

      if (progressContainer) {
        progressContainer.style.display = "flex";
        const progFill = document.querySelector("#gen-progress-fill");
        const progStatus = document.querySelector("#prog-status-text");
        const progPercent = document.querySelector("#prog-percent-text");
        if (progFill) progFill.style.width = "0%";
        if (progStatus) progStatus.textContent = `INFERENCIA PASO 1/${steps}`;
        if (progPercent) progPercent.textContent = "0%";
      }

      try {
        const res = await fetch(`${API_BASE}/diffusion/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt: prompt,
            negative_prompt: negativePrompt,
            width: currentWidth,
            height: currentHeight,
            steps: steps,
            guidance_scale: cfg,
            seed: seed
          })
        });

        if (res.ok) {
          const data = await res.json();

          // Render image
          if (canvasEmpty) canvasEmpty.style.display = "none";
          if (renderedImg) {
            renderedImg.src = data.image_data;
            renderedImg.style.display = "block";
          }
          if (metaBar) metaBar.style.display = "flex";
          const metaArch = document.getElementById("meta-arch");
          if (metaArch) metaArch.textContent = `ARCH: ${data.architecture || "DESCONOCIDA"}`;
          if (metaTime) metaTime.textContent = `TIEMPO: ${data.latency_ms} ms`;
          if (metaSeed) metaSeed.textContent = `SEMILLA: ${data.seed}`;
          if (metaVram) metaVram.textContent = `VRAM: ${data.vram_allocated_mb} MB`;

          if (downloadBtn) {
            downloadBtn.href = data.image_data;
          }
        } else {
          const err = await res.json().catch(() => ({ detail: "Error HTTP " + res.status }));
          cyberAlert("Error durante la inferencia:\n" + (err.detail || "Error desconocido"), "FALLO DE GENERACIÓN", "error");
        }
      } catch (err) {
        cyberAlert("Fallo al comunicar con el motor de difusión:\n" + err, "ERROR DE DIFUSIÓN", "error");
      } finally {
        if (genBtn) {
          genBtn.disabled = false;
          genBtn.classList.remove("loading");
          const genText = genBtn.querySelector(".gen-text");
          if (genText) genText.textContent = "GENERAR MULTIMEDIA";
        }
        if (progressContainer) progressContainer.style.display = "none";
      }
    });
  }
}
