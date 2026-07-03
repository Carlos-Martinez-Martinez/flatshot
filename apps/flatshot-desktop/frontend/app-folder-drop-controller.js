let folderDropDepth = 0;

function setFolderDropState(active, message = "") {
  const nextActive = Boolean(active);
  if (state.folderDropActive === nextActive && state.folderDropMessage === message) {
    return;
  }
  state.folderDropActive = nextActive;
  state.folderDropMessage = message;
  render();
}

function hasFolderDropPayload(event) {
  return Boolean(event?.dataTransfer);
}

function handleDocumentDragEnter(event) {
  if (!hasFolderDropPayload(event)) {
    return;
  }
  folderDropDepth += 1;
  event.preventDefault();
  setFolderDropState(true, "Suelta la carpeta para escanear");
}

function handleDocumentDragOver(event) {
  if (!hasFolderDropPayload(event)) {
    return;
  }
  event.preventDefault();
  event.dataTransfer.dropEffect = "copy";
  if (!state.folderDropActive) {
    setFolderDropState(true, "Suelta la carpeta para escanear");
  }
}

function handleDocumentDragLeave(event) {
  if (!hasFolderDropPayload(event)) {
    return;
  }
  folderDropDepth = Math.max(0, folderDropDepth - 1);
  if (folderDropDepth === 0) {
    setFolderDropState(false, state.folderDropMessage);
  }
}

function handleDocumentDrop(event) {
  if (!hasFolderDropPayload(event)) {
    return;
  }
  event.preventDefault();
  event.stopPropagation();
  folderDropDepth = 0;

  const result = folderDropHelpers.resolveDroppedFolderPath(event.dataTransfer);
  if (result.status === "ready" && result.path) {
    state.bridgeScanPath = result.path;
    state.folderDropActive = false;
    state.folderDropMessage = "";
    state.statusText = "Escaneando carpeta";
    state.bridgeMessage = "Carpeta soltada";
    persistBridgeScanPath(result.path);
    render();
    void scanBridgeFolder();
    return;
  }

  const message = result.message || "No se pudo usar el elemento soltado.";
  state.folderDropActive = false;
  state.folderDropMessage = message;
  state.bridgeMessage = message;
  state.statusText = message;
  render();
}

function scanRecentFolder(target) {
  const path = target?.dataset?.recentFolderPath || "";
  if (!path) {
    return;
  }
  state.bridgeScanPath = path;
  state.statusText = "Escaneando carpeta reciente";
  persistBridgeScanPath(path);
  render();
  void scanBridgeFolder();
}

function removeRecentFolder(target) {
  const path = target?.dataset?.recentFolderPath || "";
  if (!path) {
    return;
  }
  state.recentFolders = recentFolderHelpers.forgetRecentFolder(window.localStorage, STORAGE_KEYS.recentFolders, path);
  state.statusText = "Carpeta reciente eliminada";
  render();
}

function clearFolderDropMessage() {
  if (!state.folderDropMessage) {
    return;
  }
  state.folderDropMessage = "";
  render();
}
