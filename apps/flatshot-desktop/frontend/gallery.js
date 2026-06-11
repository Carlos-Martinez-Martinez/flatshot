(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotGallery = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const DEFAULT_FILTERS = {
    all: "all",
    valid: "valid",
    warnings: "warnings",
    excluded: "excluded",
  };

  function basename(path) {
    return String(path || "").split(/[\\/]/).filter(Boolean).pop() || "";
  }

  function imageFileStem(name) {
    return basename(name).replace(/\.[^.\\/]+$/, "") || basename(name) || "Imagen";
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function imageSearchText(image) {
    const name = String(image?.name || "");
    const stem = imageFileStem(name);
    const path = String(image?.path || "");
    const tokens = stem.split(/[^a-z0-9]+/i).filter(Boolean);
    return [name, stem, path, ...tokens].join(" ").toLowerCase();
  }

  function isValidImage(image) {
    return image.status === "ready" || image.status === "adjusted";
  }

  function isExcludedImage(image, exportItemStatuses = new Map()) {
    return !image.exportable || image.status === "error" || exportItemStatuses.get(image.id)?.status === "error";
  }

  function filteredImages(images = [], options = {}) {
    const filters = options.filters || DEFAULT_FILTERS;
    const filter = options.filter || filters.all;
    const term = String(options.search || "").trim().toLowerCase();
    const exportItemStatuses = options.exportItemStatuses || new Map();
    return images.filter((image) => {
      if (term && !imageSearchText(image).includes(term)) {
        return false;
      }
      if (filter === filters.valid) {
        return isValidImage(image);
      }
      if (filter === filters.warnings) {
        return image.status === "warning";
      }
      if (filter === filters.excluded) {
        return isExcludedImage(image, exportItemStatuses);
      }
      return true;
    });
  }

  function filterDisplayName(filter = DEFAULT_FILTERS.all) {
    const labels = {
      all: "todas",
      valid: "listas",
      warnings: "con aviso",
      excluded: "excluidas",
    };
    return labels[filter] || "imágenes";
  }

  function filterStatusText(filter = DEFAULT_FILTERS.all) {
    if (filter === DEFAULT_FILTERS.all) {
      return "Mostrando todo";
    }
    return `Mostrando ${filterDisplayName(filter)}`;
  }

  function galleryFilterCounts(images = [], exportItemStatuses = new Map()) {
    return {
      all: images.length,
      valid: images.filter(isValidImage).length,
      warnings: images.filter((image) => image.status === "warning").length,
      excluded: images.filter((image) => isExcludedImage(image, exportItemStatuses)).length,
    };
  }

  function galleryFilterVisible(filter, counts = galleryFilterCounts()) {
    if (filter === DEFAULT_FILTERS.all) {
      return true;
    }
    if (filter === DEFAULT_FILTERS.valid) {
      return counts.valid > 0 && counts.valid !== counts.all;
    }
    if (filter === DEFAULT_FILTERS.warnings) {
      return counts.warnings > 0;
    }
    if (filter === DEFAULT_FILTERS.excluded) {
      return counts.excluded > 0;
    }
    return false;
  }

  function resolveAvailableFilter(filter, images = [], exportItemStatuses = new Map()) {
    const counts = galleryFilterCounts(images, exportItemStatuses);
    return galleryFilterVisible(filter, counts) ? filter : DEFAULT_FILTERS.all;
  }

  function galleryFilterButtonStates(options = {}) {
    const counts = options.counts || {};
    const activeFilter = options.activeFilter || DEFAULT_FILTERS.all;
    const labels = {
      all: "Todas",
      valid: "Listas",
      warnings: "Avisos",
      excluded: "Excluidas",
    };
    const order = { all: 1, valid: 2, warnings: 3, excluded: 4 };
    const visibleFilters = Object.keys(labels).filter((filter) => galleryFilterVisible(filter, counts));
    return Object.keys(labels).map((filter) => {
      const count = Number(counts[filter]) || 0;
      return {
        filter,
        label: labels[filter],
        count,
        title: `${labels[filter]} ${count}`,
        order: order[filter] || 9,
        active: filter === activeFilter,
        empty: filter !== DEFAULT_FILTERS.all && !count,
        hidden: visibleFilters.length <= 1 || !visibleFilters.includes(filter),
      };
    });
  }

  function filteredEmptyHtml(options = {}) {
    const total = Number(options.total) || 0;
    if (!total) {
      return "No hay imágenes en este lote.";
    }
    const labels = {
      valid: "listas",
      warnings: "con avisos",
      excluded: "excluidas",
    };
    const search = String(options.search || "").trim();
    const filter = options.filter || DEFAULT_FILTERS.all;
    if (search) {
      const searchDetail = filter === DEFAULT_FILTERS.all
        ? `No hay imágenes que coincidan con "${search}".`
        : `No hay imágenes que coincidan con "${search}" en el filtro actual.`;
      return `
      <strong>No hay imágenes que coincidan</strong>
      <span>${escapeHtml(searchDetail)}</span>
      <button type="button" data-action="clear-filter">Limpiar búsqueda</button>
    `;
    }
    const counts = {
      valid: Number(options.valid) || 0,
      warnings: Number(options.warnings) || 0,
      excluded: Number(options.errors) || 0,
    };
    const label = labels[filter] || "con este filtro";
    const count = counts[filter] || 0;
    return `
    <strong>No hay imágenes ${escapeHtml(label)}.</strong>
    <small>${escapeHtml(total)} imágenes en el lote · ${escapeHtml(count)} en este filtro</small>
    <button type="button" data-action="clear-filter">Ver todas</button>
  `;
  }

  function filterEmptyDetail(options = {}) {
    const search = String(options.search || "").trim();
    if (search) {
      return `No hay coincidencias para "${search}".`;
    }
    if (options.filter === DEFAULT_FILTERS.warnings) {
      return "El lote no contiene imágenes con avisos.";
    }
    if (options.filter === DEFAULT_FILTERS.excluded) {
      return "No hay imágenes excluidas de la exportación.";
    }
    if (options.filter === DEFAULT_FILTERS.valid) {
      return "No hay imágenes listas en este filtro.";
    }
    return "No hay imágenes visibles con el filtro activo.";
  }

  function emptyBatchNoteHtml(options = {}) {
    const ignored = Number(options.ignored) || 0;
    const detail = ignored
      ? `Esta carpeta no contiene PNG válidos. ${options.ignoredSummary || ""}.`
      : options.scanStatus || "Esta carpeta no contiene imágenes compatibles.";
    return `
    <strong>No se encontraron imágenes compatibles</strong>
    <span>${escapeHtml(detail)}</span>
    <button type="button" class="primary" data-action="pick-bridge-folder">Elegir otra carpeta</button>
  `;
  }

  function compactImageDetail(detail) {
    return String(detail || "")
      .replace(/^PNG\s*·\s*/i, "")
      .replace(/^JPG\s*·\s*/i, "")
      .replace(/^JPEG\s*·\s*/i, "")
      .replace(/^Lista$/i, "")
      .trim();
  }

  function assetStatusLabel(status, statusLabels = {}) {
    if (status === "ready") {
      return "Lista";
    }
    if (status === "adjusted") {
      return "Personalizado";
    }
    return statusLabels[status] || "Lista";
  }

  function assetStatusIcon(status) {
    if (status === "warning") {
      return "!";
    }
    if (status === "error") {
      return "×";
    }
    if (status === "exported") {
      return "✓";
    }
    if (status === "adjusted") {
      return "*";
    }
    return "✓";
  }

  function thumbnailState(options = {}) {
    const src = options.src || "";
    if (!src) {
      return { status: "error", error: "Sin preview" };
    }
    const stored = options.stored || null;
    if (stored?.src === src || stored?.sourceSrc === src) {
      return stored;
    }
    return { status: "loading", src, error: "" };
  }

  function mockThumbnailDataUrl(image) {
    const palettes = {
      "tone-a": ["#f8f1e8", "#b7d6c8", "#34534a"],
      "tone-b": ["#f8e1dc", "#dfe9ec", "#723d45"],
      "tone-c": ["#ded8cf", "#8db9ad", "#33423f"],
      "tone-d": ["#f2e6bd", "#c7d7ea", "#67510f"],
      "tone-e": ["#e3ecfa", "#b7d2c9", "#294d63"],
    };
    const [bgA, bgB, ink] = palettes[image?.tone] || palettes["tone-a"];
    const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="${bgA}"/>
          <stop offset="1" stop-color="${bgB}"/>
        </linearGradient>
      </defs>
      <rect width="96" height="96" rx="8" fill="url(#bg)"/>
      <path d="M34 18h28l13 12-9 11-6-4v38H36V37l-6 4-9-11 13-12z" fill="#fff" fill-opacity=".86"/>
      <path d="M34 18h28l13 12-9 11-6-4v38H36V37l-6 4-9-11 13-12z" fill="none" stroke="${ink}" stroke-opacity=".34" stroke-width="2"/>
    </svg>
  `;
    return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg.trim())}`;
  }

  function thumbnailHtml(image, current = {}, src = "") {
    const status = current.status || "loading";
    const error = current.error || "Sin preview";
    const alt = `Miniatura de ${image.name}`;
    const displaySrc = current.resolvedSrc || current.src || src;
    return `
    <span class="thumb is-${escapeHtml(status)}" data-thumb-id="${escapeHtml(image.id)}">
      ${displaySrc ? `<img class="thumb-image" src="${escapeHtml(displaySrc)}" alt="${escapeHtml(alt)}" loading="eager" data-image-id="${escapeHtml(image.id)}" />` : ""}
      <span class="thumb-skeleton" aria-hidden="true"></span>
      <span class="thumb-error">${escapeHtml(error)}</span>
    </span>
  `;
  }

  function imageItemHtml(options = {}) {
    const image = options.image || {};
    const selected = options.selected ? "active" : "";
    const exportState = options.exportState || null;
    const imageStatus = options.imageStatus || image.status;
    const effectiveStatus = exportState?.status || imageStatus;
    const chipClass = effectiveStatus === "warning"
      ? "warning"
      : effectiveStatus === "error"
        ? "error"
        : effectiveStatus === "exported"
          ? "exported"
          : imageStatus === "adjusted" ? "adjusted" : "ready";
    const chipLabel = exportState?.label || assetStatusLabel(imageStatus, options.statusLabels || {});
    const title = image.path || image.name;
    const detail = image.detail === "Lista" ? "" : image.detail;
    const displayName = options.displayName || imageFileStem(image.name);
    const fileType = options.fileType || "Imagen";
    const compactDetailText = compactImageDetail(detail);
    const metadata = !compactDetailText
      ? fileType
      : compactDetailText.toUpperCase().startsWith(fileType)
        ? compactDetailText
        : `${fileType} · ${compactDetailText}`;
    const thumbState = options.thumbState || {};
    const previewNote = thumbState.status === "error" ? " · sin preview" : "";
    const statusText = chipLabel ? ` · ${chipLabel}` : "";
    const stateIcon = assetStatusIcon(effectiveStatus);
    const stateBadgeHtml = effectiveStatus === "ready" ? "" : `
      <span class="asset-state ${chipClass}" role="img" title="${escapeHtml(chipLabel || "Lista")}" aria-label="${escapeHtml(chipLabel || "Lista")}">
        <span aria-hidden="true">${escapeHtml(stateIcon)}</span>
        <em>${escapeHtml(chipLabel || "Lista")}</em>
      </span>
    `;
    return `
    <button type="button" class="image-item asset-row ${selected} ${chipClass}" data-image-id="${escapeHtml(image.id)}" title="${escapeHtml(title)}" aria-pressed="${selected ? "true" : "false"}" aria-label="${escapeHtml(`${image.name}${statusText}`)}">
      ${thumbnailHtml(image, thumbState, options.thumbnailSrc || "")}
      <span class="image-copy">
        <strong>${escapeHtml(displayName)}</strong>
        <small>${escapeHtml(`${metadata}${previewNote}`)}</small>
      </span>
      ${stateBadgeHtml}
    </button>
  `;
  }

  return {
    assetStatusIcon,
    assetStatusLabel,
    filterDisplayName,
    filteredEmptyHtml,
    filteredImages,
    filterEmptyDetail,
    filterStatusText,
    galleryFilterCounts,
    galleryFilterButtonStates,
    galleryFilterVisible,
    basename,
    compactImageDetail,
    emptyBatchNoteHtml,
    escapeHtml,
    imageFileStem,
    imageItemHtml,
    imageSearchText,
    isExcludedImage,
    isValidImage,
    mockThumbnailDataUrl,
    resolveAvailableFilter,
    thumbnailState,
    thumbnailHtml,
  };
});
