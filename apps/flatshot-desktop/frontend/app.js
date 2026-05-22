const state = {
  selectedImage: "camiseta_001.png",
  selectedKind: "Web RGB230",
  preset: "Luz cenital",
  format: "JPG",
  processing: false,
  progress: 0,
  timer: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const statusDot = $("#status-dot");
const topStatusText = $("#top-status-text");
const bottomStatus = $("#bottom-status");
const progressFill = $("#progress-fill");
const processButton = $("#process-batch");
const openOutputButton = $("#open-output");
const batchCount = $("#batch-count");
const adjustedCount = $("#adjusted-count");
const folderRow = $("#folder-row");
const imageList = $("#image-list");

function setStatus(text, mode = "ready") {
  topStatusText.textContent = text;
  bottomStatus.textContent = text;
  statusDot.className = `status-dot ${mode}`;
}

function setProgress(value) {
  state.progress = Math.max(0, Math.min(100, value));
  progressFill.style.width = `${state.progress}%`;
}

function selectImage(button) {
  $$(".image-item").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  state.selectedImage = button.dataset.name;
  state.selectedKind = button.dataset.kind;
  $("#preview-name").textContent = state.selectedImage;
  $("#preview-meta").textContent = `${state.format} · 1800x2400 · ${state.selectedKind}`;
  $("#preview-warning").textContent = state.selectedKind === "Ajuste local" ? "Ajuste local activo" : "Sin avisos";
}

function selectPreset(button) {
  $$(".preset-chip").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  state.preset = button.textContent.trim();
  $("#active-preset").textContent = state.preset;
  setStatus("Preview pendiente de actualizar", "busy");
  window.setTimeout(() => setStatus("Listo para procesar", "ready"), 500);
}

function selectFormat(button) {
  $$(".export-format button").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  state.format = button.textContent.trim();
  $("#export-format-label").textContent = state.format;
  $("#preview-meta").textContent = `${state.format} · 1800x2400 · ${state.selectedKind}`;
}

function filterBatch(button) {
  $$(".batch-filter button").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");

  const mode = button.textContent.trim();
  $$(".image-item").forEach((item) => {
    const isAdjusted = item.dataset.kind === "Ajuste local";
    const isError = item.dataset.kind === "Error";
    item.hidden = (mode === "Ajustadas" && !isAdjusted) || (mode === "Errores" && !isError);
  });

  setStatus(mode === "Errores" ? "Sin errores en el lote" : `Filtro: ${mode}`, "ready");
}

function simulateExport() {
  if (state.processing) {
    return;
  }

  state.processing = true;
  processButton.disabled = true;
  openOutputButton.disabled = true;
  setProgress(0);
  setStatus("Preparando exportación", "busy");

  state.timer = window.setInterval(() => {
    const next = state.progress + 8;
    setProgress(next);

    const processed = Math.min(24, Math.max(1, Math.round((state.progress / 100) * 24)));
    setStatus(`Procesando ${processed}/24`, "busy");

    if (state.progress >= 100) {
      window.clearInterval(state.timer);
      state.processing = false;
      processButton.disabled = false;
      openOutputButton.disabled = false;
      setStatus("Exportación completada", "ready");
    }
  }, 180);
}

function clearBatch() {
  if (state.timer) {
    window.clearInterval(state.timer);
  }
  state.processing = false;
  processButton.disabled = false;
  openOutputButton.disabled = true;
  $$(".image-item").forEach((item) => item.classList.remove("active"));
  $$(".batch-filter button").forEach((item, index) => item.classList.toggle("active", index === 0));
  $("#batch-title").textContent = "Sin lote";
  batchCount.textContent = "0 PNG";
  adjustedCount.textContent = "Sin ajustes";
  folderRow.querySelector(".folder-name").textContent = "Sin carpeta";
  folderRow.querySelector(".folder-name").title = "Sin carpeta";
  folderRow.querySelector("span:last-child").textContent = "0";
  imageList.classList.add("empty");
  $("#preview-name").textContent = "Sin imagen seleccionada";
  $("#preview-meta").textContent = "Sin preview";
  $("#preview-warning").textContent = "Sin avisos";
  setProgress(0);
  setStatus("Añade una carpeta", "ready");
}

function loadSampleBatch() {
  $("#batch-title").textContent = "Lote de muestra";
  batchCount.textContent = "24 PNG";
  adjustedCount.textContent = "2 ajustadas";
  folderRow.querySelector(".folder-name").textContent = "Camisetas Mayo";
  folderRow.querySelector(".folder-name").title = "Camisetas Mayo";
  folderRow.querySelector("span:last-child").textContent = "24";
  imageList.classList.remove("empty");
  $$(".image-item").forEach((item) => {
    item.hidden = false;
  });
  $$(".batch-filter button").forEach((item, index) => item.classList.toggle("active", index === 0));
  const firstImage = $(".image-item");
  if (firstImage) {
    selectImage(firstImage);
  }
  setProgress(0);
  setStatus("Lote cargado", "ready");
}

function attachEvents() {
  $$(".image-item").forEach((button) => {
    button.addEventListener("click", () => selectImage(button));
  });

  $$(".preset-chip").forEach((button) => {
    button.addEventListener("click", () => selectPreset(button));
  });

  $$(".export-format button").forEach((button) => {
    button.addEventListener("click", () => selectFormat(button));
  });

  $$(".batch-filter button").forEach((button) => {
    button.addEventListener("click", () => filterBatch(button));
  });

  $$(".preview-tools .tool").forEach((button) => {
    button.addEventListener("click", () => {
      $$(".preview-tools .tool").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      setStatus(`${button.dataset.mode} · preview lista`, "ready");
    });
  });

  $$(".control-row input").forEach((input) => {
    const output = input.closest(".control-row").querySelector("output");
    input.addEventListener("input", () => {
      output.textContent = input.value;
      setStatus("Preview pendiente de actualizar", "busy");
    });
    input.addEventListener("change", () => setStatus("Listo para procesar", "ready"));
  });

  $("#add-folder").addEventListener("click", () => {
    setStatus("Escaneando carpeta", "busy");
    window.setTimeout(loadSampleBatch, 450);
  });

  $("#clear-batch").addEventListener("click", clearBatch);
  processButton.addEventListener("click", simulateExport);
  openOutputButton.addEventListener("click", () => setStatus("Destino listo para abrir", "ready"));
}

attachEvents();
