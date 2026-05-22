const mockFolders = [
  {
    id: "camisetas",
    name: "Camisetas Mayo",
    path: "D:/Produccion/Camisetas Mayo",
    count: 18,
    status: "ready",
    detail: "18 PNG",
  },
  {
    id: "chaquetas",
    name: "Chaquetas Lookbook",
    path: "D:/Produccion/Chaquetas Lookbook",
    count: 6,
    status: "warning",
    detail: "1 aviso",
  },
];

const mockImages = [
  {
    id: "img-001",
    folderId: "camisetas",
    name: "camiseta_001.png",
    detail: "1800x2400 · 1.4 MB",
    status: "ready",
    tone: "tone-a",
    exportable: true,
  },
  {
    id: "img-002",
    folderId: "camisetas",
    name: "camiseta_002.png",
    detail: "Ajuste local · 1.2 MB",
    status: "adjusted",
    tone: "tone-b",
    exportable: true,
  },
  {
    id: "img-003",
    folderId: "chaquetas",
    name: "chaqueta_003.png",
    detail: "Preview con aviso",
    status: "warning",
    tone: "tone-c",
    exportable: true,
  },
  {
    id: "img-004",
    folderId: "chaquetas",
    name: "chaqueta_004.png",
    detail: "Error de alpha",
    status: "error",
    tone: "tone-d",
    exportable: false,
  },
  {
    id: "img-005",
    folderId: "camisetas",
    name: "sudadera_005.png",
    detail: "Lista",
    status: "ready",
    tone: "tone-e",
    exportable: true,
  },
];

const presets = [
  "Luz cenital",
  "Estándar oscuro",
  "Complementos",
  "Sin sombra",
];

const statusLabels = {
  ready: "Lista",
  adjusted: "Ajustada",
  warning: "Aviso",
  error: "Error",
};

const scenarioLabels = {
  initial: "Sin lote",
  "batch-ready": "Lote listo",
  "empty-folder": "Carpeta vacía",
  "preview-loading": "Preview cargando",
  "preview-warning": "Preview con aviso",
  "preview-error": "Error de preview",
  "export-blocked": "Destino sin configurar",
  "export-ready": "Exportación lista",
  "export-running": "Exportación en curso",
  "export-completed": "Exportación completada",
  "export-partial": "Completada con errores",
  "export-failed": "Exportación fallida",
};

const defaultSettings = {
  opacity: 20,
  blur: 30,
  distance: 25,
  padding: 10,
};

const state = {
  scenario: "initial",
  batch: "none",
  selectedImageId: null,
  previewStatus: "empty",
  previewMode: "processed",
  previewBg: "rgb230",
  zoom: 100,
  filter: "all",
  search: "",
  activePreset: "Luz cenital",
  settings: { ...defaultSettings },
  presetDirty: false,
  localOverride: false,
  exportStatus: "blocked",
  destinationMode: "source",
  destinationValue: "_SALIDA_PRO",
  format: "JPG",
  size: "1800x2400",
  background: "rgb230",
  naming: "{original}{suffix}",
  progress: 0,
  processed: 0,
  errors: [],
  paused: false,
  statusText: "Añade una carpeta",
};

const timers = new Set();

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function setTimer(callback, delay) {
  const timer = window.setTimeout(() => {
    timers.delete(timer);
    callback();
  }, delay);
  timers.add(timer);
  return timer;
}

function clearTimers() {
  timers.forEach((timer) => window.clearTimeout(timer));
  timers.clear();
}

function selectedImage() {
  return mockImages.find((image) => image.id === state.selectedImageId) || null;
}

function hasBatch() {
  return state.batch === "ready" || state.batch === "scanning";
}

function activeImages() {
  return state.batch === "ready" ? mockImages : [];
}

function exportableImages() {
  return activeImages().filter((image) => image.exportable);
}

function filteredImages() {
  const term = state.search.trim().toLowerCase();
  return activeImages().filter((image) => {
    if (term && !image.name.toLowerCase().includes(term)) {
      return false;
    }
    if (state.filter === "adjusted") {
      return image.status === "adjusted";
    }
    if (state.filter === "warnings") {
      return image.status === "warning";
    }
    if (state.filter === "errors") {
      return image.status === "error";
    }
    return true;
  });
}

function validationIssues() {
  const issues = [];
  if (!hasBatch()) {
    issues.push({ level: "warning", title: "Sin lote", detail: "Añade una carpeta." });
  }
  if (state.batch === "empty") {
    issues.push({ level: "warning", title: "No hay PNG válidos", detail: "Elige otra carpeta." });
  }
  if (exportableImages().length === 0 && state.batch === "ready") {
    issues.push({ level: "error", title: "Sin imágenes exportables", detail: "Revisa los errores." });
  }
  if (!state.naming.trim()) {
    issues.push({ level: "error", title: "Naming vacío", detail: "Define una plantilla." });
  }
  if (state.destinationMode === "custom" && !state.destinationValue.trim()) {
    issues.push({ level: "error", title: "Destino sin configurar", detail: "Elige una carpeta." });
  }
  return issues;
}

function isExportReady() {
  return validationIssues().filter((issue) => issue.level === "error" || issue.title !== "Sin lote").length === 0
    && hasBatch()
    && exportableImages().length > 0;
}

function setScenario(scenario) {
  clearTimers();
  Object.assign(state, {
    scenario,
    batch: "ready",
    selectedImageId: "img-001",
    previewStatus: "ready",
    exportStatus: "ready",
    destinationMode: "source",
    destinationValue: "_SALIDA_PRO",
    progress: 0,
    processed: 0,
    errors: [],
    paused: false,
    statusText: "Listo para procesar",
  });

  if (scenario === "initial") {
    Object.assign(state, {
      batch: "none",
      selectedImageId: null,
      previewStatus: "empty",
      exportStatus: "blocked",
      statusText: "Añade una carpeta",
    });
  } else if (scenario === "empty-folder") {
    Object.assign(state, {
      batch: "empty",
      selectedImageId: null,
      previewStatus: "empty",
      exportStatus: "blocked",
      statusText: "No hay PNG válidos",
    });
  } else if (scenario === "preview-loading") {
    Object.assign(state, {
      previewStatus: "loading",
      exportStatus: "ready",
      statusText: "Generando preview",
    });
  } else if (scenario === "preview-warning") {
    Object.assign(state, {
      selectedImageId: "img-003",
      previewStatus: "warning",
      exportStatus: "ready",
      statusText: "Preview con aviso",
    });
  } else if (scenario === "preview-error") {
    Object.assign(state, {
      selectedImageId: "img-004",
      previewStatus: "error",
      exportStatus: "blocked",
      statusText: "Preview no disponible",
    });
  } else if (scenario === "export-blocked") {
    Object.assign(state, {
      destinationMode: "custom",
      destinationValue: "",
      exportStatus: "blocked",
      statusText: "Destino sin configurar",
    });
  } else if (scenario === "export-running") {
    Object.assign(state, {
      exportStatus: "running",
      progress: 42,
      processed: 2,
      statusText: `Procesando 2/${exportableImages().length}`,
    });
    render();
    return;
  } else if (scenario === "export-completed") {
    Object.assign(state, {
      exportStatus: "completed",
      progress: 100,
      processed: exportableImages().length,
      statusText: "Exportación completada",
    });
  } else if (scenario === "export-partial") {
    Object.assign(state, {
      exportStatus: "partial",
      progress: 100,
      processed: exportableImages().length,
      errors: [
        { level: "error", title: "chaqueta_004.png", detail: "No se pudo leer alpha." },
        { level: "warning", title: "chaqueta_003.png", detail: "Preview renderizada con fallback." },
      ],
      statusText: "Exportación con errores",
    });
  } else if (scenario === "export-failed") {
    Object.assign(state, {
      exportStatus: "failed",
      progress: 38,
      processed: 2,
      errors: [
        { level: "error", title: "Destino no disponible", detail: "La carpeta ya no existe." },
      ],
      statusText: "Exportación fallida",
    });
  }

  render();
}

function loadBatch() {
  clearTimers();
  Object.assign(state, {
    scenario: "batch-ready",
    batch: "scanning",
    selectedImageId: null,
    previewStatus: "empty",
    exportStatus: "blocked",
    progress: 0,
    processed: 0,
    errors: [],
    statusText: "Escaneando carpeta",
  });
  render();
  setTimer(() => {
    Object.assign(state, {
      batch: "ready",
      selectedImageId: "img-001",
      previewStatus: "loading",
      exportStatus: "ready",
      statusText: "Generando preview",
    });
    render();
    setTimer(() => {
      Object.assign(state, {
        previewStatus: "ready",
        statusText: "Listo para procesar",
      });
      render();
    }, 550);
  }, 450);
}

function clearBatch() {
  setScenario("initial");
}

function showEmptyFolder() {
  setScenario("empty-folder");
}

function selectImage(imageId) {
  const image = mockImages.find((item) => item.id === imageId);
  if (!image) {
    return;
  }
  clearTimers();
  state.selectedImageId = image.id;
  state.localOverride = image.status === "adjusted";
  state.previewStatus = "loading";
  state.statusText = "Generando preview";
  render();
  setTimer(() => {
    state.previewStatus = image.status === "error" ? "error" : image.status === "warning" ? "warning" : "ready";
    state.statusText = state.previewStatus === "error" ? "Preview no disponible" : "Preview lista";
    render();
  }, 380);
}

function markPresetDirty() {
  state.presetDirty = true;
  refreshPreviewAfterSettingChange();
}

function refreshPreviewAfterSettingChange() {
  if (hasBatch() && state.previewStatus !== "error") {
    state.previewStatus = "loading";
    state.statusText = "Generando preview";
    render();
    clearTimers();
    setTimer(() => {
      state.previewStatus = selectedImage()?.status === "warning" ? "warning" : "ready";
      state.statusText = "Preview lista";
      render();
    }, 420);
  } else {
    render();
  }
}

function startExport(options = {}) {
  clearTimers();
  if (!isExportReady()) {
    state.exportStatus = "blocked";
    state.statusText = validationIssues()[0]?.title || "Configura exportación";
    render();
    return;
  }

  Object.assign(state, {
    scenario: options.keepScenario ? "export-running" : state.scenario,
    exportStatus: "running",
    progress: 0,
    processed: 0,
    errors: [],
    paused: false,
    statusText: "Preparando exportación",
  });
  render();
  scheduleExportStep();
}

function scheduleExportStep() {
  setTimer(() => {
    if (state.exportStatus !== "running") {
      return;
    }
    if (state.paused) {
      scheduleExportStep();
      return;
    }
    const total = exportableImages().length;
    state.progress = Math.min(100, state.progress + 9);
    state.processed = Math.min(total, Math.max(1, Math.round((state.progress / 100) * total)));
    state.statusText = `Procesando ${state.processed}/${total}`;

    if (state.progress >= 100) {
      state.exportStatus = "completed";
      state.progress = 100;
      state.processed = total;
      state.statusText = "Exportación completada";
      render();
      return;
    }

    render();
    scheduleExportStep();
  }, 220);
}

function pauseExport() {
  if (state.exportStatus !== "running") {
    return;
  }
  state.paused = !state.paused;
  state.statusText = state.paused ? "Pausado" : `Procesando ${state.processed}/${exportableImages().length}`;
  render();
}

function stopExport() {
  if (state.exportStatus !== "running") {
    return;
  }
  clearTimers();
  Object.assign(state, {
    exportStatus: "failed",
    paused: false,
    errors: [{ level: "error", title: "Exportación detenida", detail: "No se generaron más archivos." }],
    statusText: "Exportación fallida",
  });
  render();
}

function reviewErrors() {
  if (!hasBatch()) {
    return;
  }
  state.filter = "errors";
  state.statusText = state.errors.length ? "Revisa errores de exportación" : "Filtro: errores";
  render();
}

function primaryAction() {
  if (!hasBatch()) {
    loadBatch();
    return;
  }
  if (state.exportStatus === "completed" || state.exportStatus === "partial") {
    clearBatch();
    return;
  }
  startExport();
}

function statusMode() {
  if (state.exportStatus === "failed" || state.previewStatus === "error") {
    return "error";
  }
  if (state.exportStatus === "running" || state.previewStatus === "loading" || state.batch === "scanning") {
    return "busy";
  }
  if (state.exportStatus === "partial" || state.previewStatus === "warning" || validationIssues().length) {
    return "busy";
  }
  return "ready";
}

function render() {
  renderTop();
  renderBatch();
  renderPreview();
  renderSettings();
  renderExport();
  renderFooter();
}

function renderTop() {
  $("#demo-scenario").value = scenarioLabels[state.scenario] ? state.scenario : "batch-ready";
  $("#active-batch-label").textContent = hasBatch()
    ? `${activeImages().length} imágenes · ${state.activePreset}`
    : state.batch === "empty"
      ? "Carpeta sin PNG"
      : "Sin lote";
  $("#top-status-text").textContent = state.statusText;
  $("#status-dot").className = `status-dot ${statusMode()}`;
}

function renderBatch() {
  const images = activeImages();
  const adjusted = images.filter((image) => image.status === "adjusted").length;
  const warnings = images.filter((image) => image.status === "warning").length;
  const errors = images.filter((image) => image.status === "error").length;

  if (state.batch === "none") {
    $("#batch-count").textContent = "0 imágenes";
    $("#batch-pill").textContent = "Sin carpeta";
    $("#folder-list").innerHTML = "";
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").textContent = "Añade una carpeta para empezar.";
    $("#image-search").value = state.search;
    renderFilterButtons();
    return;
  }

  if (state.batch === "scanning") {
    $("#batch-count").textContent = "Escaneando";
    $("#batch-pill").textContent = "Carpeta mock";
    $("#folder-list").innerHTML = folderItemHtml({
      id: "scan",
      name: "Camisetas Mayo",
      detail: "Leyendo PNG",
      count: "...",
      status: "ready",
    });
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").textContent = "Escaneando carpeta";
    renderFilterButtons();
    return;
  }

  if (state.batch === "empty") {
    $("#batch-count").textContent = "0 PNG";
    $("#batch-pill").textContent = "Sin imágenes";
    $("#folder-list").innerHTML = folderItemHtml({
      id: "empty",
      name: "Carpeta vacía",
      detail: "No hay PNG válidos",
      count: "0",
      status: "empty",
    });
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").textContent = "No hay PNG válidos.";
    renderFilterButtons();
    return;
  }

  $("#batch-count").textContent = `${images.length} imágenes`;
  $("#batch-pill").textContent = errors ? `${errors} errores` : adjusted ? `${adjusted} ajustadas` : `${warnings} avisos`;
  $("#folder-list").innerHTML = mockFolders.map(folderItemHtml).join("");
  $("#image-search").value = state.search;
  renderFilterButtons();

  const visible = filteredImages();
  $("#image-list").innerHTML = visible.map(imageItemHtml).join("");
  $("#batch-empty-note").textContent = visible.length ? "" : "Sin resultados.";
}

function folderItemHtml(folder) {
  const className = folder.status === "warning" ? "empty" : folder.status === "error" ? "error" : folder.status || "";
  return `
    <div class="folder-item ${className}" title="${escapeHtml(folder.path || folder.detail)}">
      <div>
        <strong>${escapeHtml(folder.name)}</strong>
        <small>${escapeHtml(folder.detail)}</small>
      </div>
      <span class="state-chip ${folder.status === "warning" ? "warning" : folder.status === "error" ? "error" : ""}">
        ${escapeHtml(folder.count)}
      </span>
    </div>
  `;
}

function imageItemHtml(image) {
  const selected = image.id === state.selectedImageId ? "active" : "";
  const chipClass = image.status === "warning" ? "warning" : image.status === "error" ? "error" : "";
  return `
    <button type="button" class="image-item ${selected} ${chipClass}" data-image-id="${escapeHtml(image.id)}" title="${escapeHtml(image.name)}">
      <span class="thumb ${escapeHtml(image.tone)}"></span>
      <span class="image-copy">
        <strong>${escapeHtml(image.name)}</strong>
        <small>${escapeHtml(image.detail)}</small>
      </span>
      <span class="state-chip ${chipClass}">${escapeHtml(statusLabels[image.status])}</span>
    </button>
  `;
}

function renderFilterButtons() {
  $$(".batch-filter button").forEach((button) => {
    button.classList.toggle("active", button.dataset.filter === state.filter);
  });
}

function renderPreview() {
  const image = selectedImage();
  $("#preview-name").textContent = image ? image.name : "Sin imagen seleccionada";
  $("#preview-subtitle").textContent = previewSubtitle(image);
  $("#zoom-label").textContent = `${state.zoom}%`;
  $("#preview-meta").textContent = image ? `${state.format} · ${state.size} · ${backgroundLabel(state.background)}` : "Sin imagen";
  $("#canvas-area").className = `canvas-area bg-${state.previewBg === "transparent" ? "transparent" : state.previewBg}`;
  $$(".preview-toolbar [data-preview-mode]").forEach((button) => {
    button.classList.toggle("active", button.dataset.previewMode === state.previewMode);
  });
  $$(".background-switch [data-preview-bg]").forEach((button) => {
    button.classList.toggle("active", button.dataset.previewBg === state.previewBg);
  });

  const canvas = $("#preview-canvas");
  canvas.className = `preview-canvas ${state.previewMode} bg-${state.previewBg}`;
  canvas.style.setProperty("--preview-scale", String(state.zoom / 100));

  if (!image || state.previewStatus === "empty") {
    canvas.innerHTML = previewStateHtml("Sin imagen seleccionada", "El lote aparecerá aquí.");
    return;
  }

  if (state.previewStatus === "loading") {
    canvas.innerHTML = `
      <div class="preview-state">
        <span class="loader" aria-hidden="true"></span>
        <strong>Generando preview</strong>
        <span>${escapeHtml(image.name)}</span>
      </div>
    `;
    return;
  }

  if (state.previewStatus === "error") {
    canvas.innerHTML = previewStateHtml("Preview no disponible", "Revisa alpha o archivo fuente.");
    return;
  }

  canvas.innerHTML = `
    <div class="mock-product" aria-hidden="true">
      <div class="mock-shadow"></div>
      <div class="mock-body"></div>
    </div>
    ${state.previewStatus === "warning" ? '<div class="preview-warning-card">Render con fallback. Revisa antes de exportar.</div>' : ""}
  `;
}

function previewStateHtml(title, detail) {
  return `
    <div class="preview-state">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(detail)}</span>
    </div>
  `;
}

function previewSubtitle(image) {
  if (!image) {
    return "Sin preview";
  }
  if (state.previewStatus === "loading") {
    return "Generando preview";
  }
  if (state.previewStatus === "warning") {
    return "Preview con aviso";
  }
  if (state.previewStatus === "error") {
    return "Preview no disponible";
  }
  return image.detail;
}

function renderSettings() {
  $("#active-preset").textContent = state.activePreset;
  $("#preset-dirty").textContent = state.presetDirty ? "Sin guardar" : "Sin cambios";
  $("#preset-dirty").classList.toggle("dirty", state.presetDirty);
  $("#preset-list").innerHTML = presets.map((preset) => `
    <button type="button" class="preset-chip ${preset === state.activePreset ? "active" : ""}" data-preset="${escapeHtml(preset)}">
      ${escapeHtml(preset)}
    </button>
  `).join("");

  Object.entries(state.settings).forEach(([key, value]) => {
    const input = $(`[data-setting="${key}"]`);
    const output = $(`#${key}-output`);
    if (input) {
      input.value = value;
    }
    if (output) {
      output.textContent = value;
    }
  });

  const image = selectedImage();
  const localActive = state.localOverride || image?.status === "adjusted";
  $("#local-adjustment").classList.toggle("active", localActive);
  $("#local-adjustment-text").textContent = localActive ? "Ajuste local activo" : "Sin ajuste local";
}

function renderExport() {
  $("#format-select").value = state.format;
  $("#size-select").value = state.size;
  $("#background-select").value = state.background;
  $("#destination-mode").value = state.destinationMode;
  $("#destination-input").value = state.destinationValue;
  $("#naming-input").value = state.naming;

  const issues = [...validationIssues(), ...state.errors];
  const exportable = exportableImages().length;
  const outputCount = exportable;
  const ready = isExportReady();
  const destinationText = state.destinationMode === "custom" ? state.destinationValue || "Sin configurar" : `origen / ${state.destinationValue}`;
  const statusText = ready ? "Lista" : "No lista";

  $("#export-readiness").textContent = exportStatusLabel(ready);
  $("#export-count").textContent = `${outputCount} archivos`;
  $("#export-count").classList.toggle("dirty", !ready);

  $("#export-summary").innerHTML = `
    <div class="summary-line"><span>Salida</span><strong>${escapeHtml(state.format)} · ${escapeHtml(state.size)}</strong></div>
    <div class="summary-line"><span>Fondo</span><strong>${escapeHtml(backgroundLabel(state.background))}</strong></div>
    <div class="summary-line"><span>Destino</span><strong>${escapeHtml(destinationText)}</strong></div>
    <div class="summary-line"><span>Naming</span><strong>${escapeHtml(state.naming || "Sin plantilla")}</strong></div>
    <div class="summary-line"><span>Resumen</span><strong>${exportable} imágenes · ${statusText}</strong></div>
  `;

  $("#issue-list").innerHTML = issues.map((issue) => `
    <div class="issue-item ${issue.level === "error" ? "error" : ""}">
      <strong>${escapeHtml(issue.title)}</strong>
      <span>${escapeHtml(issue.detail)}</span>
    </div>
  `).join("");
}

function exportStatusLabel(ready) {
  if (state.exportStatus === "running") {
    return state.paused ? "Pausada" : "Procesando";
  }
  if (state.exportStatus === "completed") {
    return "Completada";
  }
  if (state.exportStatus === "partial") {
    return "Con errores";
  }
  if (state.exportStatus === "failed") {
    return "Fallida";
  }
  return ready ? "Lista" : "Configura exportación";
}

function backgroundLabel(value) {
  if (value === "transparent") {
    return "Transparente";
  }
  if (value === "white") {
    return "Blanco";
  }
  return "RGB230";
}

function renderFooter() {
  const exportable = exportableImages().length;
  const issues = [...validationIssues(), ...state.errors];
  const ready = isExportReady();

  $("#footer-batch").textContent = hasBatch()
    ? `${activeImages().length} imágenes`
    : state.batch === "empty"
      ? "0 PNG"
      : "Sin lote";
  $("#footer-preview").textContent = previewFooterLabel();
  $("#footer-export").textContent = exportStatusLabel(ready);
  $("#footer-destination").textContent = !hasBatch()
    ? "Sin destino"
    : state.destinationMode === "custom"
      ? state.destinationValue || "Sin configurar"
      : `origen / ${state.destinationValue}`;
  $("#bottom-status").textContent = state.statusText;
  $("#progress-fill").style.width = `${state.progress}%`;
  $("#progress-fill").className = state.exportStatus === "failed" ? "error" : state.exportStatus === "partial" ? "warning" : "";

  $("#review-errors").disabled = issues.length === 0 && activeImages().every((image) => image.status !== "error");
  $("#pause-export").classList.toggle("is-hidden", state.exportStatus !== "running");
  $("#pause-export").textContent = state.paused ? "Reanudar" : "Pausar";
  $("#stop-export").classList.toggle("is-hidden", state.exportStatus !== "running");
  $("#open-output").disabled = !(state.exportStatus === "completed" || state.exportStatus === "partial");

  const primary = $("#primary-action");
  primary.disabled = state.exportStatus === "running" || (hasBatch() && !ready && validationIssues().some((issue) => issue.level === "error"));
  if (!hasBatch()) {
    primary.textContent = "Añadir carpeta";
  } else if (state.exportStatus === "completed" || state.exportStatus === "partial") {
    primary.textContent = "Nuevo lote";
  } else if (!ready) {
    primary.textContent = "Configura exportación";
  } else {
    primary.textContent = `Procesar ${exportable} imágenes`;
  }
}

function previewFooterLabel() {
  if (state.previewStatus === "loading") {
    return "Generando";
  }
  if (state.previewStatus === "warning") {
    return "Con aviso";
  }
  if (state.previewStatus === "error") {
    return "Error";
  }
  if (state.previewStatus === "ready") {
    return "Lista";
  }
  return "Sin imagen";
}

function handleAction(action) {
  if (action === "load-batch") {
    loadBatch();
  } else if (action === "clear-batch") {
    clearBatch();
  } else if (action === "show-empty-folder") {
    showEmptyFolder();
  } else if (action === "force-preview-error") {
    if (hasBatch()) {
      state.previewStatus = "error";
      state.statusText = "Preview no disponible";
      render();
    }
  } else if (action === "zoom-in") {
    state.zoom = Math.min(160, state.zoom + 10);
    render();
  } else if (action === "zoom-out") {
    state.zoom = Math.max(70, state.zoom - 10);
    render();
  } else if (action === "reset-settings") {
    state.settings = { ...defaultSettings };
    state.presetDirty = false;
    state.statusText = "Ajustes restaurados";
    render();
  } else if (action === "save-preset") {
    state.presetDirty = false;
    state.statusText = "Preset guardado";
    render();
  } else if (action === "toggle-local-adjustment") {
    state.localOverride = !state.localOverride;
    state.statusText = state.localOverride ? "Ajuste local activo" : "Ajuste local quitado";
    render();
  } else if (action === "pause-export") {
    pauseExport();
  } else if (action === "stop-export") {
    stopExport();
  } else if (action === "review-errors") {
    reviewErrors();
  } else if (action === "open-output") {
    state.statusText = "Destino listo para abrir";
    render();
  } else if (action === "primary") {
    primaryAction();
  }
}

document.addEventListener("click", (event) => {
  const actionTarget = event.target.closest("[data-action]");
  if (actionTarget) {
    handleAction(actionTarget.dataset.action);
    return;
  }

  const imageTarget = event.target.closest("[data-image-id]");
  if (imageTarget) {
    selectImage(imageTarget.dataset.imageId);
    return;
  }

  const filterTarget = event.target.closest("[data-filter]");
  if (filterTarget) {
    state.filter = filterTarget.dataset.filter;
    state.statusText = `Filtro: ${filterTarget.textContent.trim()}`;
    render();
    return;
  }

  const modeTarget = event.target.closest("[data-preview-mode]");
  if (modeTarget) {
    state.previewMode = modeTarget.dataset.previewMode;
    state.statusText = modeTarget.textContent.trim();
    render();
    return;
  }

  const bgTarget = event.target.closest("[data-preview-bg]");
  if (bgTarget) {
    state.previewBg = bgTarget.dataset.previewBg;
    state.statusText = `Fondo: ${bgTarget.textContent.trim()}`;
    render();
    return;
  }

  const presetTarget = event.target.closest("[data-preset]");
  if (presetTarget) {
    state.activePreset = presetTarget.dataset.preset;
    state.presetDirty = false;
    refreshPreviewAfterSettingChange();
  }
});

$("#demo-scenario").addEventListener("change", (event) => {
  setScenario(event.target.value);
});

$("#image-search").addEventListener("input", (event) => {
  state.search = event.target.value;
  render();
});

$$("[data-setting]").forEach((input) => {
  input.addEventListener("input", (event) => {
    const key = event.target.dataset.setting;
    state.settings[key] = Number(event.target.value);
    markPresetDirty();
  });
});

$("#format-select").addEventListener("change", (event) => {
  state.format = event.target.value;
  state.statusText = `Formato: ${state.format}`;
  render();
});

$("#size-select").addEventListener("change", (event) => {
  state.size = event.target.value;
  state.statusText = `Tamaño: ${state.size}`;
  render();
});

$("#background-select").addEventListener("change", (event) => {
  state.background = event.target.value;
  state.previewBg = event.target.value;
  state.statusText = `Fondo: ${backgroundLabel(state.background)}`;
  render();
});

$("#destination-mode").addEventListener("change", (event) => {
  state.destinationMode = event.target.value;
  state.destinationValue = state.destinationMode === "custom" ? "" : "_SALIDA_PRO";
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.destinationMode === "custom" ? "Destino sin configurar" : "Destino: origen";
  render();
});

$("#destination-input").addEventListener("input", (event) => {
  state.destinationValue = event.target.value;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.destinationValue.trim() ? "Destino configurado" : "Destino sin configurar";
  render();
});

$("#naming-input").addEventListener("input", (event) => {
  state.naming = event.target.value;
  state.exportStatus = isExportReady() ? "ready" : "blocked";
  state.statusText = state.naming.trim() ? "Naming actualizado" : "Naming vacío";
  render();
});

setScenario("initial");
