(function(global) {

global.mockFolders = [
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

global.mockImages = [
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
    detail: "Personalizado · 1.2 MB",
    status: "adjusted",
    tone: "tone-b",
    exportable: true,
  },
  {
    id: "img-003",
    folderId: "chaquetas",
    name: "chaqueta_003.png",
    detail: "Vista con aviso",
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

global.mockPresets = [
  "Luz cenital",
  "Estándar oscuro",
  "Complementos",
  "Sin sombra",
];

global.STORAGE_KEYS = {
  bridgeScanPath: "flatshot.bridgeScanPath",
  selectedImagePath: "flatshot.selectedImagePath",
  imageAdjustmentPreset: "flatshot.selectedImageAdjustmentPreset",
  outputProfiles: "flatshot.outputProfiles",
  backgroundPresets: "flatshot.backgroundPresets",
  activeOutputProfile: "flatshot.activeOutputProfile",
  activeOutputFormats: "flatshot.activeOutputFormatIds",
  lastOutputFolder: "flatshot.lastOutputFolder",
  exportPreferences: "flatshot.exportPreferences",
  sessionSnapshot: "flatshot.liveReloadSession.v1",
};

global.statusLabels = {
  ready: "Lista",
  adjusted: "Personalizado",
  warning: "Aviso",
  error: "Error",
};

global.BATCH_FILTERS = {
  all: "all",
  valid: "valid",
  warnings: "warnings",
  excluded: "excluded",
};
global.IGNORED_OMISSION_REASONS = new Set([
  "system_file",
  "temporary_or_config_file",
  "unsupported_extension",
  "subfolder_not_scanned",
]);
global.ACTIONABLE_OMISSION_REASONS = new Set([
  "read_error",
]);

global.DEFAULT_VIEW_MODE = "height";
global.VIEW_MODE_LABELS = {
  height: "Alto",
  width: "Ancho",
  manual: "Manual",
};

global.scenarioLabels = {
  initial: "Sin lote",
  "batch-ready": "Lote listo",
  "empty-folder": "Carpeta vacía",
  "preview-loading": "Vista cargando",
  "preview-warning": "Vista con aviso",
  "preview-error": "Error de vista",
  "export-blocked": "Carpeta de salida sin configurar",
  "export-ready": "Exportación lista",
  "export-running": "Exportación en curso",
  "export-completed": "Exportación completada",
  "export-partial": "Completada con errores",
  "export-failed": "Exportación fallida",
};

global.shadowSettingKeys = [
  "angle",
  "distance",
  "blur",
  "spread",
  "fusion",
  "opacity",
  "noise",
  "padding",
  "contact_blur",
  "contraction",
  "adaptive_zoom",
  "scale_adjustment",
  "shadow_engine",
  "lighting_scene",
  "transparent_bg",
  "bg_color",
];

global.advancedSettingKeys = [
  "spread",
  "noise",
  "contact_blur",
  "scale_adjustment",
  "fusion",
  "angle",
  "contraction",
  "adaptive_zoom",
  "shadow_engine",
  "lighting_scene",
];

global.localOverrideKeys = ["size_delta", "shadow_delta", "blur_delta"];
global.localOverrideLimits = {
  size_delta: [-30, 30],
  shadow_delta: [-40, 40],
  blur_delta: [-40, 40],
};

global.defaultLightingScene = {
  main: {
    type: "softbox",
    x: -0.25,
    y: -0.65,
    height: 0.65,
    size: 0.55,
    intensity: 0.85,
  },
  ambient_intensity: 0.25,
};

global.shadowEngineLabels = {
  realistic_v2: "Realista V2",
  studio_2_5d: "Estudio 2.5D",
  legacy: "Clásico",
};

global.lightingScenePresets = {
  overhead_soft: {
    main: { type: "softbox", x: -0.08, y: -0.78, height: 0.72, size: 0.72, intensity: 0.82 },
    ambient_intensity: 0.30,
  },
  side_soft: {
    main: { type: "softbox", x: -0.78, y: -0.28, height: 0.58, size: 0.62, intensity: 0.86 },
    ambient_intensity: 0.28,
  },
  front_clean: {
    main: { type: "softbox", x: 0.0, y: -0.24, height: 0.82, size: 0.82, intensity: 0.72 },
    ambient_intensity: 0.36,
  },
  mild_drama: {
    main: { type: "strip", x: -0.62, y: -0.70, height: 0.46, size: 0.38, intensity: 1.02 },
    ambient_intensity: 0.18,
  },
};

global.defaultSettings = {
  angle: 180,
  opacity: 20,
  blur: 30,
  distance: 25,
  spread: 0,
  fusion: 1,
  noise: 2,
  padding: 10,
  contact_blur: 10,
  contraction: 0,
  adaptive_zoom: true,
  scale_adjustment: 0,
  shadow_engine: "realistic_v2",
  lighting_scene: global.defaultLightingScene,
  transparent_bg: false,
  bg_color: [230, 230, 230],
};

global.mockPresetSettings = {
  "Luz cenital": { ...global.defaultSettings },
  "Estándar oscuro": {
    ...global.defaultSettings,
    distance: 20,
    blur: 40,
    spread: 3,
    fusion: 5,
    opacity: 45,
    noise: 5,
    contact_blur: 12,
  },
  Complementos: {
    ...global.defaultSettings,
    distance: 18,
    blur: 22,
    opacity: 26,
    padding: 8,
    scale_adjustment: 4,
  },
  "Sin sombra": {
    ...global.defaultSettings,
    distance: 0,
    blur: 0,
    spread: 0,
    fusion: 0,
    opacity: 0,
    noise: 0,
    contact_blur: 0,
  },
};

global.defaultOutputProfiles = [
  {
    id: "jpg-rgb230-1800x2400",
    name: "JPG gris claro 1800x2400",
    enabled: true,
    format: "JPG",
    width: 1800,
    height: 2400,
    background: "rgb230",
    destinationMode: "source",
    destinationValue: "Salida",
    naming: "{original}{suffix}",
    suffix: "_PRO",
  },
  {
    id: "png-transparent-1800x2400",
    name: "PNG transparente 1800x2400",
    enabled: false,
    format: "PNG",
    width: 1800,
    height: 2400,
    background: "transparent",
    destinationMode: "source",
    destinationValue: "Salida",
    naming: "{original}{suffix}",
    suffix: "_PRO",
  },
  {
    id: "jpg-white-2000x2000",
    name: "JPG blanco 2000x2000",
    enabled: false,
    format: "JPG",
    width: 2000,
    height: 2000,
    background: "white",
    destinationMode: "source",
    destinationValue: "Salida",
    naming: "{original}{suffix}",
    suffix: "_PRO",
  },
];
global.defaultBackgroundPresets = [
  { id: "rgb230", name: "Gris claro", kind: "rgb", rgb: [230, 230, 230] },
  { id: "white", name: "Blanco", kind: "rgb", rgb: [255, 255, 255] },
  { id: "transparent", name: "Transparente", kind: "transparent", rgb: [230, 230, 230] },
];

})(typeof window !== "undefined" ? window : global);
