(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotFolderDrop = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const FILE_EXTENSIONS = new Set([
    "png",
    "jpg",
    "jpeg",
    "webp",
    "gif",
    "bmp",
    "tif",
    "tiff",
    "psd",
    "avif",
    "heic",
  ]);

  function cleanPath(value) {
    return String(value || "").trim().replace(/^"|"$/g, "");
  }

  function fileUrlToLocalPath(value) {
    const raw = cleanPath(value);
    if (!raw.toLowerCase().startsWith("file:")) {
      return raw;
    }
    try {
      const url = new URL(raw);
      const decodedPath = decodeURIComponent(url.pathname || "");
      if (url.hostname) {
        return `//${url.hostname}${decodedPath}`;
      }
      return decodedPath.replace(/^\/([a-zA-Z]:\/)/, "$1");
    } catch (error) {
      return raw;
    }
  }

  function extensionFromPath(path) {
    const name = cleanPath(path).split(/[\\/]/).pop() || "";
    const match = /\.([^.]+)$/.exec(name);
    return match ? match[1].toLowerCase() : "";
  }

  function looksLikeFile(file = {}) {
    const type = String(file.type || "").trim();
    const extension = extensionFromPath(file.path || file.name);
    return Boolean(type) || FILE_EXTENSIONS.has(extension);
  }

  function pathFromTextData(dataTransfer) {
    const types = ["text/uri-list", "text/plain"];
    for (const type of types) {
      const raw = dataTransfer?.getData?.(type);
      const lines = String(raw || "")
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line && !line.startsWith("#"));
      for (const line of lines) {
        const path = fileUrlToLocalPath(line);
        if (path) {
          return path;
        }
      }
    }
    return "";
  }

  function hasDirectoryEntry(dataTransfer) {
    const items = Array.from(dataTransfer?.items || []);
    return items.some((item) => {
      try {
        const entry = item.webkitGetAsEntry?.();
        return Boolean(entry?.isDirectory);
      } catch (error) {
        return false;
      }
    });
  }

  function resolveDroppedFolderPath(dataTransfer) {
    const textPath = pathFromTextData(dataTransfer);
    if (textPath) {
      return { status: "ready", path: textPath, message: "" };
    }

    const files = Array.from(dataTransfer?.files || []);
    const pathFile = files.find((file) => cleanPath(file.path));
    if (pathFile) {
      if (looksLikeFile(pathFile)) {
        return {
          status: "invalid",
          path: "",
          message: "Suelta una carpeta, no archivos sueltos.",
        };
      }
      return { status: "ready", path: cleanPath(pathFile.path), message: "" };
    }

    if (files.some(looksLikeFile)) {
      return {
        status: "invalid",
        path: "",
        message: "Suelta una carpeta, no archivos sueltos.",
      };
    }

    if (hasDirectoryEntry(dataTransfer) || files.length) {
      return {
        status: "unsupported",
        path: "",
        message: "No se pudo leer la ruta de la carpeta. Usa Buscar carpeta.",
      };
    }

    return {
      status: "invalid",
      path: "",
      message: "El elemento soltado no parece una carpeta válida.",
    };
  }

  return {
    fileUrlToLocalPath,
    resolveDroppedFolderPath,
  };
});
