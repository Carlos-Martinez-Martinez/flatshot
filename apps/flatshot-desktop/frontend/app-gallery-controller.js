function renderBatchSummary() {
  const summary = $("#batch-summary");
  const visible = getVisibleAppState();
  const counts = visible.counts;
  const diagnostics = state.scanDiagnostics || emptyScanDiagnostics();
  const sourcePath = state.batch === "ready"
    ? activeFolders()[0]?.path || state.bridgeScanPath
    : state.batch === "empty" && state.realFolders.length
      ? state.realFolders[0]?.path || state.bridgeScanPath
      : state.bridgeScanPath;
  const outputLine = batchOutputLine();
  const destinationLine = batchDestinationLine();
  const warningsLabel = counts.nonBlockingWarnings ? preflightHelpers.countText(counts.nonBlockingWarnings, "aviso", "avisos") : "Sin avisos";
  const ignoredLabel = counts.ignoredFiles ? preflightHelpers.countText(counts.ignoredFiles, "ignorado", "ignorados") : "Sin ignorados";

  summary.innerHTML = batchViewHelpers.batchSummaryHtml({
    batch: state.batch,
    counts,
    destinationLine,
    diagnostics,
    hasScanError: state.scanIssues.some((issue) => issue.level === "error"),
    ignoredLabel,
    namingExample: namingExample(),
    namingLabel: namingHumanLabel(),
    outputLine,
    outputProfileName: outputProfileDisplayName(),
    sourceFolderName: sourceFolderName(),
    sourcePath,
    visible,
    warningsLabel,
  });
}

function batchOutputLine() {
  const profiles = exportOutputProfiles();
  if (!profiles.length) {
    return "Sin salidas activas";
  }
  return batchViewHelpers.batchOutputLine({
    background: state.background,
    format: state.format,
    profileLines: profiles.length > 1 ? profiles.map((profile) => `${profile.format} ${outputProfileHelpers.outputProfileSize(profile).replace("x", "×")}`) : [],
    size: state.size,
  });
}

function outputProfilesSummaryLabel(profiles = exportOutputProfiles()) {
  if (!profiles.length) {
    return "Sin salidas activas";
  }
  return batchViewHelpers.outputProfilesSummaryLabel({
    backgroundLabel: settingsViewHelpers.backgroundLabel(state.background),
    format: state.format,
    profileLabels: profiles.length > 1 ? profiles.map((profile) => `${profile.name} (${profile.format})`) : [],
    sizeLabel: outputSizeDisplay(),
  });
}

function batchDestinationLine() {
  const profiles = exportOutputProfiles();
  if (!profiles.length) {
    return "Sin destino activo";
  }
  return batchViewHelpers.batchDestinationLine({
    destinationMode: state.destinationMode,
    destinationValue: state.destinationValue,
    profileDestinations: profiles.length > 1 ? profiles.map(outputProfileViewHelpers.profileDestinationPreviewLabel) : [],
  });
}

function renderBatch() {
  const images = activeImages();
  const counts = batchCounts();
  const adjusted = imageAdjustmentOverrideCount(images);
  const valid = images.filter((image) => image.status === "ready" || hasImageAdjustmentOverride(image)).length;
  const warnings = images.filter((image) => image.status === "warning").length;
  const errors = images.filter((image) => image.status === "error" || exportItemState(image)?.status === "error").length;
  const ignored = counts.ignoredFiles;
  const issueCount = counts.reviewIssues;
  const filmstripCount = $("#filmstrip-count");
  $("#image-search").value = state.search;
  updateBatchSearchClear();
  renderGalleryViewButtons();
  renderGalleryOutputControl();

  if (state.batch === "none") {
    $("#batch-count").textContent = "Sin lote";
    setBatchPill("Sin carpeta", "muted");
    setGalleryTitle(0, "Sin lote");
    setGalleryMeta("");
    $("#batch-visible-count").textContent = "";
    $("#folder-list").innerHTML = "";
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").innerHTML = "";
    if (filmstripCount) {
      filmstripCount.textContent = "Sin lote";
    }
    renderFilterButtons();
    return;
  }

  const sidebarSummaryText = batchViewHelpers.sidebarLotSummaryText({
    batch: state.batch,
    hasBatch: hasBatch(),
    nonBlockingWarnings: counts.nonBlockingWarnings,
    readyLabel: preflightHelpers.readyImagesText(counts.exportableImages),
    scanStatus: state.scanStatus,
  });

  if (state.batch === "scanning") {
    $("#batch-count").textContent = "Escaneando";
    setBatchPill("Escaneando", "active");
    setGalleryTitle(0, "Escaneando");
    setGalleryMeta(state.scanStatus || "Leyendo carpeta");
    $("#batch-visible-count").textContent = sidebarSummaryText;
    $("#folder-list").innerHTML = batchDetailViewHelpers.folderItemHtml({
      id: "scan",
      name: isBridgeBatch() || !devMode ? formatterHelpers.basename(parseFolderInput(state.bridgeScanPath)[0]) || "Ruta" : "Camisetas Mayo",
      path: state.bridgeScanPath,
      detail: "Leyendo imágenes",
      count: "...",
      status: "ready",
    });
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").innerHTML = "";
    if (filmstripCount) {
      filmstripCount.textContent = "Escaneando";
    }
    renderFilterButtons();
    return;
  }

  if (state.batch === "empty") {
    const emptyFolders = isBridgeBatch() && state.realFolders.length
      ? state.realFolders
      : [{
          id: "empty",
          name: "Carpeta vacía",
          detail: "No hay PNG válidos",
          count: "0",
          status: "empty",
        }];
    $("#batch-count").textContent = "Sin imágenes";
    setBatchPill("Sin imágenes", "muted");
    setGalleryTitle(0, "No hay PNG válidos");
    setGalleryMeta(sidebarSummaryText);
    $("#batch-visible-count").textContent = sidebarSummaryText;
    $("#folder-list").innerHTML = emptyFolders.map((folder) => batchDetailViewHelpers.folderItemHtml(folder)).join("");
    $("#image-list").innerHTML = "";
    $("#batch-empty-note").innerHTML = emptyBatchNoteHtml();
    if (filmstripCount) {
      filmstripCount.textContent = "Sin imágenes";
    }
    renderFilterButtons();
    return;
  }

  const exportable = exportableImages().length;
  $("#batch-count").textContent = exportable ? preflightHelpers.readyImagesText(exportable) : "Sin exportables";
  const batchPillState = batchViewHelpers.batchPillState({
    adjustedCount: adjusted,
    issueCount,
  });
  setBatchPill(batchPillState.label, batchPillState.tone);
  $("#folder-list").innerHTML = "";
  ensureGalleryFilterAvailable(images);
  renderFilterButtons();

  const visible = filteredImages();
  const imageList = $("#image-list");
  const preservedScrollLeft = imageList.scrollLeft;
  const virtualWindow = galleryVirtualWindow(visible);
  const renderedImages = visible.slice(virtualWindow.start, virtualWindow.end);
  setGalleryTitle(exportable);
  setGalleryMeta(galleryBatchMetaText(counts, images));
  $("#batch-visible-count").textContent = galleryVisibleCountText(visible.length, images.length);
  imageList.classList.toggle("is-virtualized", virtualWindow.virtualized);
  imageList.innerHTML = [
    galleryVirtualSpacerHtml(virtualWindow.paddingTop),
    ...renderedImages.map(imageItemHtml),
    galleryVirtualSpacerHtml(virtualWindow.paddingBottom),
  ].join("");
  imageList.scrollLeft = preservedScrollLeft;
  queueThumbnailPreload(renderedImages);
  $("#batch-empty-note").innerHTML = visible.length ? "" : filteredEmptyHtml(images.length, valid, warnings, errors);
  if (filmstripCount) {
    filmstripCount.textContent = visible.length === images.length
      ? `${images.length} imágenes`
      : `${visible.length} de ${images.length}`;
  }
}
function galleryVisibleCountText(visibleCount, totalCount) {
  const visibleText = visibleCount === totalCount ? "" : `${visibleCount}/${totalCount}`;
  const selectedCount = state.selectedImageIds.length;
  const selectedText = selectedCount > 1 ? `${selectedCount} seleccionadas` : "";
  return [visibleText, selectedText].filter(Boolean).join(" · ");
}

function galleryVirtualWindow(images = []) {
  const imageList = $("#image-list");
  const scrollTop = Number.isFinite(state.galleryScrollTop)
    ? state.galleryScrollTop
    : imageList?.scrollLeft || 0;
  return galleryHelpers.virtualGalleryWindow({
    total: images.length,
    scrollTop,
    viewportHeight: imageList?.clientWidth || 0,
    rowHeight: state.galleryView === "list" ? 220 : galleryThumbnailColumnWidth(),
    columns: 1,
    overscanRows: 3,
    threshold: 100,
  });
}

function galleryThumbnailColumnWidth() {
  return { small: 132, medium: 160, large: 218 }[state.interfacePreferences.thumbnailSize] || 160;
}

function galleryVirtualSpacerHtml(height) {
  const normalized = Math.max(0, Math.round(Number(height) || 0));
  return normalized
    ? `<div class="gallery-virtual-spacer" style="width:${normalized}px" aria-hidden="true"></div>`
    : "";
}

function setGalleryTitle(count, label = "") {
  const title = $("#gallery-title");
  if (title) {
    title.textContent = label || preflightHelpers.readyImagesText(Number(count) || 0);
  }
}

function setGalleryMeta(text = "") {
  const meta = $("#gallery-batch-meta");
  if (meta) {
    meta.textContent = text;
    meta.title = text;
  }
}

function galleryBatchMetaText(counts = batchCounts(), images = activeImages()) {
  const filesFound = counts.filesFound === null ? images.length : Number(counts.filesFound) || images.length;
  const parts = [
    batchViewHelpers.detectedFormatLabel(images),
    filesFound ? `${filesFound} archivos` : "",
  ].filter(Boolean);
  if (counts.nonBlockingWarnings) {
    parts.push(`${counts.nonBlockingWarnings} ${counts.nonBlockingWarnings === 1 ? "aviso" : "avisos"}`);
  }
  if (counts.ignoredFiles) {
    parts.push(`${counts.ignoredFiles} ${counts.ignoredFiles === 1 ? "ignorado" : "ignorados"}`);
  }
  return parts.join(" · ");
}

function renderGalleryOutputControl() {
  const control = $("#gallery-output-control");
  const select = $("#gallery-output-select");
  if (!control || !select) {
    return;
  }
  const profiles = galleryOutputProfiles();
  const showControl = state.batch === "ready" && profiles.length > 1;
  control.hidden = !showControl;
  if (!showControl) {
    select.innerHTML = "";
    return;
  }
  const context = galleryActiveOutputContext();
  const customOption = context.id === "__custom"
    ? `<option value="__custom">Salida personalizada · ${escapeHtml(context.label)}</option>`
    : "";
  select.innerHTML = `${customOption}${profiles.map((profile) => {
    return `<option value="${escapeHtml(profile.id)}">${escapeHtml(profile.name)}</option>`;
  }).join("")}`;
  select.value = context.id;
  if (select.value !== context.id) {
    select.value = profiles[0]?.id || "";
  }
  select.title = context.summary;
}

function setBatchPill(label, tone = "muted") {
  const pill = $("#batch-pill");
  pill.textContent = label;
  pill.className = `batch-rail__badge is-${tone}`;
}

function updateBatchSearchClear() {
  const clearButton = $("#image-search-clear");
  if (!clearButton) {
    return;
  }
  const hasSearch = Boolean(state.search.trim());
  clearButton.classList.toggle("is-visible", hasSearch);
  clearButton.disabled = !hasSearch;
}

function filteredEmptyHtml(total, valid, warnings, errors) {
  return galleryHelpers.filteredEmptyHtml({
    errors,
    filter: state.filter,
    search: state.search,
    total,
    valid,
    warnings,
  });
}

function filterEmptyDetail() {
  return galleryHelpers.filterEmptyDetail({
    filter: state.filter,
    search: state.search,
  });
}

function emptyBatchNoteHtml() {
  return galleryHelpers.emptyBatchNoteHtml({
    ignored: ignoredOmissions().length,
    ignoredSummary: ignoredSummaryText(),
    scanStatus: state.scanStatus,
    subfoldersOmitted: ignoredOmissions().filter((item) => item.reason === "subfolder_not_scanned").length,
  });
}

function imageItemHtml(image) {
  const exportState = exportItemState(image);
  const imageStatus = hasImageAdjustmentOverride(image) ? "adjusted" : image.status;
  const thumbnailSrc = imageThumbnailSrc(image);
  const selectedIds = new Set(state.selectedImageIds);
  const selected = selectedIds.has(image.id) || image.id === state.selectedImageId;
  return galleryHelpers.imageItemHtml({
    exportState,
    fileType: imageFileType(image),
    image,
    imageStatus,
    outputLabel: "",
    primarySelected: image.id === state.selectedImageId,
    selected,
    statusLabels,
    thumbState: thumbnailState(image, thumbnailSrc),
    thumbnailSrc,
  });
}

function galleryFilterCounts(images = activeImages()) {
  return galleryHelpers.galleryFilterCounts(images, exportItemStatusMap(images));
}

function ensureGalleryFilterAvailable(images = activeImages()) {
  const nextFilter = galleryHelpers.resolveAvailableFilter(state.filter, images, exportItemStatusMap(images));
  if (nextFilter !== state.filter) {
    state.filter = nextFilter;
  }
}

function renderFilterButtons() {
  const images = activeImages();
  const counts = galleryFilterCounts(images);
  const buttonStates = galleryHelpers.galleryFilterButtonStates({
    activeFilter: state.filter,
    counts,
  });
  const visibleCount = buttonStates.filter((item) => !item.hidden).length;
  const filterGroup = $(".gallery-filter");
  if (filterGroup) {
    filterGroup.hidden = visibleCount <= 1;
  }
  $$(".batch-filter button").forEach((button) => {
    const filter = button.dataset.filter;
    const buttonState = buttonStates.find((item) => item.filter === filter);
    if (!buttonState) {
      return;
    }
    button.innerHTML = `${escapeHtml(buttonState.label)} <span>${escapeHtml(buttonState.count)}</span>`;
    button.title = buttonState.title;
    button.style.order = String(buttonState.order);
    button.classList.toggle("active", buttonState.active);
    button.classList.toggle("is-empty", buttonState.empty);
    button.hidden = buttonState.hidden;
  });
}

function renderGalleryViewButtons() {
  $$("[data-gallery-view]").forEach((button) => {
    const active = button.dataset.galleryView === state.galleryView;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
}
