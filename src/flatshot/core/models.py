import re

from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Any, Dict, List, Literal, Mapping, Optional, Tuple

ShadowEngineName = Literal["realistic_v2", "legacy", "studio_2_5d"]
StudioLightType = Literal["softbox", "spot", "strip"]

SHADOW_ENGINE_REALISTIC_V2 = "realistic_v2"
SHADOW_ENGINE_LEGACY = "legacy"
SHADOW_ENGINE_STUDIO_2_5D = "studio_2_5d"
SHADOW_ENGINE_DEFAULT: ShadowEngineName = SHADOW_ENGINE_REALISTIC_V2
SHADOW_ENGINE_COMPAT: ShadowEngineName = SHADOW_ENGINE_LEGACY
VALID_SHADOW_ENGINES = {SHADOW_ENGINE_REALISTIC_V2, SHADOW_ENGINE_LEGACY, SHADOW_ENGINE_STUDIO_2_5D}


class StudioLight(BaseModel):
    type: StudioLightType = "softbox"
    x: float = Field(-0.25, ge=-1.0, le=1.0)
    y: float = Field(-0.65, ge=-1.0, le=1.0)
    height: float = Field(0.65, ge=0.0, le=1.0)
    size: float = Field(0.55, ge=0.0, le=1.0)
    intensity: float = Field(0.85, ge=0.0, le=1.5)


class LightingScene(BaseModel):
    main: StudioLight = Field(default_factory=StudioLight)
    ambient_intensity: float = Field(0.25, ge=0.0, le=1.0)

class ShadowSettings(BaseModel):
    angle: int = Field(180, ge=0, le=360)
    distance: int = 25
    blur: int = 30
    spread: int = 0
    fusion: int = 1
    opacity: int = 20
    noise: int = 2
    padding: int = 10
    contact_blur: int = 10
    contraction: int = 0
    adaptive_zoom: bool = True
    scale_adjustment: int = Field(0, ge=-30, le=30)
    shadow_engine: ShadowEngineName = SHADOW_ENGINE_DEFAULT
    lighting_scene: LightingScene = Field(default_factory=LightingScene)
    transparent_bg: bool = False
    bg_color: Tuple[int, int, int] = (230, 230, 230)

    @field_validator("bg_color", mode="before")
    @classmethod
    def _validate_bg_color(cls, value: Any) -> Tuple[int, int, int]:
        return _coerce_rgb_tuple(value)


def _coerce_rgb_tuple(value: Any) -> Tuple[int, int, int]:
    """Accept (r,g,b) as tuple or list, reject bools, coerce to validated int triplet."""
    if isinstance(value, tuple) and len(value) == 3:
        raw = value
    elif isinstance(value, list) and len(value) == 3:
        raw = tuple(value)
    else:
        raise ValueError("RGB color must contain exactly three values")

    rgb = []
    for channel in raw:
        if isinstance(channel, bool):
            raise ValueError("RGB channels must be integers between 0 and 255")
        try:
            numeric = int(channel)
        except (TypeError, ValueError) as exc:
            raise ValueError("RGB channels must be integers between 0 and 255") from exc
        if numeric < 0 or numeric > 255:
            raise ValueError("RGB channels must be between 0 and 255")
        rgb.append(numeric)
    return tuple(rgb)  # type: ignore[return-value]


def normalize_shadow_settings(
    data: ShadowSettings | Mapping[str, Any] | None,
    *,
    missing_engine: ShadowEngineName = SHADOW_ENGINE_COMPAT,
) -> ShadowSettings:
    """
    Build a ShadowSettings object while making the shadow engine explicit.

    Loaded presets and sessions that predate shadow_engine must keep the legacy
    renderer to preserve visual compatibility. New in-memory defaults can still
    use ShadowSettings() directly and therefore use realistic_v2.
    """
    if isinstance(data, ShadowSettings):
        if data.shadow_engine in VALID_SHADOW_ENGINES:
            return data
        return data.model_copy(update={"shadow_engine": missing_engine})

    raw = dict(data or {})
    if raw.get("shadow_engine") not in VALID_SHADOW_ENGINES:
        raw["shadow_engine"] = missing_engine
    return ShadowSettings(**raw)


def normalize_shadow_settings_dict(
    data: ShadowSettings | Mapping[str, Any] | None,
    *,
    missing_engine: ShadowEngineName = SHADOW_ENGINE_COMPAT,
) -> dict:
    return normalize_shadow_settings(data, missing_engine=missing_engine).model_dump()


class ExportVariant(BaseModel):
    id: str
    label: str
    enabled: bool = True

    # Background for this output version.
    transparent_bg: bool = False
    bg_color: Tuple[int, int, int] = (230, 230, 230)

    # Variant-specific naming and optional destination.
    suffix: str = ""
    output_subfolder: Optional[str] = None
    naming_template: Optional[str] = None
    output_destination: Optional[str] = None
    output_folder_name: Optional[str] = None
    custom_output_path: Optional[str] = None

    # Optional output format. None inherits ExportConfig.format.
    format: Optional[str] = None
    output_width: Optional[int] = Field(None, ge=1)
    output_height: Optional[int] = Field(None, ge=1)

    # Shadow adjustment for adapting one output version to a different background.
    shadow_opacity_delta: int = Field(0, ge=-100, le=100)
    shadow_opacity_override: Optional[int] = Field(None, ge=0, le=100)

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        clean = str(value).strip()
        if not clean:
            raise ValueError("Variant id cannot be empty")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", clean):
            raise ValueError("Variant id can only contain letters, numbers, _ and -")
        return clean

    @field_validator("label")
    @classmethod
    def _validate_label(cls, value: str) -> str:
        clean = str(value).strip()
        if not clean:
            raise ValueError("Variant label cannot be empty")
        return clean

    @field_validator("bg_color", mode="before")
    @classmethod
    def _validate_bg_color(cls, value: Any) -> Tuple[int, int, int]:
        return _coerce_rgb_tuple(value)

    @field_validator("suffix")
    @classmethod
    def _validate_suffix(cls, value: str) -> str:
        text = str(value)
        if any(sep in text for sep in ("/", "\\")):
            raise ValueError("Variant suffix cannot contain path separators")
        if any(ord(ch) < 32 for ch in text):
            raise ValueError("Variant suffix cannot contain control characters")
        return text

    @field_validator("output_subfolder")
    @classmethod
    def _validate_output_subfolder(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if text.startswith(("/", "\\")) or ":" in text:
            raise ValueError("Variant output subfolder must be relative")
        if any(part in {"", ".", ".."} for part in re.split(r"[\\/]+", text)):
            raise ValueError("Variant output subfolder cannot contain empty or parent parts")
        return text.replace("\\", "/")

    @field_validator("output_folder_name")
    @classmethod
    def _validate_output_folder_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if text.startswith(("/", "\\")) or ":" in text:
            raise ValueError("Variant output folder name must be relative")
        if any(part in {"", ".", ".."} for part in re.split(r"[\\/]+", text)):
            raise ValueError("Variant output folder name cannot contain empty or parent parts")
        return text.replace("\\", "/")

    @field_validator("output_destination")
    @classmethod
    def _validate_output_destination(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip().lower()
        if not text:
            return None
        if text not in {"subfolder", "custom"}:
            raise ValueError("Variant output destination must be subfolder, custom or None")
        return text

    @field_validator("custom_output_path")
    @classmethod
    def _validate_custom_output_path(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @field_validator("naming_template")
    @classmethod
    def _validate_naming_template(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        text = str(value)
        return text if text.strip() else None

    @field_validator("format")
    @classmethod
    def _validate_format(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip().upper().lstrip(".")
        if text == "JPEG":
            text = "JPG"
        if text not in {"JPG", "PNG"}:
            raise ValueError("Variant format must be JPG, PNG or None")
        return text

class ExportConfig(BaseModel):
    output_folder_name: str = "_SALIDA_PRO"
    suffix: str = "_PRO"
    format: str = "JPG"
    transparent_bg: bool = False
    bg_color: Tuple[int, int, int] = (230, 230, 230)
    variants: List[ExportVariant] = Field(default_factory=list)
    # New fields for configurable output size
    output_width: int = 1800
    output_height: int = 2400
    # Naming template: {original}, {suffix}, {folder}, {index:03d}
    naming_template: str = "{original}{suffix}"
    # Destination mode: 'subfolder' (create in each source) or 'custom' (single folder)
    output_destination: str = "subfolder"
    custom_output_path: Optional[str] = None


WEB_RGB230 = ExportVariant(
    id="web_rgb230",
    label="Web RGB230",
    enabled=True,
    bg_color=(230, 230, 230),
    transparent_bg=False,
    suffix="_PRO",
    shadow_opacity_delta=0,
)

WHITE_RGB255 = ExportVariant(
    id="white_rgb255",
    label="Blanco RGB255",
    enabled=False,
    bg_color=(255, 255, 255),
    transparent_bg=False,
    suffix="_BLANCO",
    shadow_opacity_delta=-5,
)


def _settings_mapping(config_or_settings: Any) -> dict:
    if isinstance(config_or_settings, BaseModel):
        return config_or_settings.model_dump()
    if isinstance(config_or_settings, Mapping):
        return dict(config_or_settings)
    return {}


def _fallback_export_variant(raw: Mapping[str, Any]) -> ExportVariant:
    try:
        bg_color = _coerce_rgb_tuple(raw.get("bg_color", WEB_RGB230.bg_color))
    except ValueError:
        bg_color = WEB_RGB230.bg_color
    label = "Web RGB230" if bg_color == WEB_RGB230.bg_color else "Salida principal"
    variant_id = "web_rgb230" if bg_color == WEB_RGB230.bg_color else "primary_output"
    return WEB_RGB230.model_copy(
        update={
            "id": variant_id,
            "label": label,
            "enabled": True,
            "transparent_bg": bool(raw.get("transparent_bg", False)),
            "bg_color": bg_color,
            "suffix": str(raw.get("suffix", WEB_RGB230.suffix)),
        }
    )


def normalize_export_variants(config_or_settings: Any) -> list[ExportVariant]:
    """
    Return valid output variants while preserving old single-output settings.

    Existing settings without ``variants`` become one variant equivalent to the
    previous export behavior. Invalid variant entries are ignored instead of
    breaking startup from a hand-edited settings file.
    """
    raw = _settings_mapping(config_or_settings)
    variants_data = raw.get("variants")
    parsed: list[ExportVariant] = []
    seen_ids: set[str] = set()

    if isinstance(variants_data, list):
        for item in variants_data:
            try:
                variant = item if isinstance(item, ExportVariant) else ExportVariant.model_validate(item)
            except ValidationError:
                continue
            if variant.id in seen_ids:
                continue
            parsed.append(variant)
            seen_ids.add(variant.id)

    if parsed:
        return parsed
    return [_fallback_export_variant(raw)]


def build_variant_settings(base_settings: ShadowSettings, variant: ExportVariant) -> ShadowSettings:
    settings = base_settings.model_copy(deep=True)
    settings.transparent_bg = variant.transparent_bg
    settings.bg_color = variant.bg_color

    if variant.shadow_opacity_override is not None:
        settings.opacity = variant.shadow_opacity_override
    else:
        settings.opacity = max(0, min(100, settings.opacity + variant.shadow_opacity_delta))

    return settings

class CurveData(BaseModel):
    xp: List[float]
    fp: List[float]
    base_fill: float = Field(0.52, ge=0.10, le=0.90)
    aspect_mix: float = Field(0.45, ge=0.0, le=1.0)
    occupancy_influence: float = Field(0.42, ge=0.0, le=1.0)
    manual_curve_strength: float = Field(0.60, ge=0.0, le=1.0)

class JobItem(BaseModel):
    """Represents a folder in the processing queue."""
    folder_path: str
    input_files: Optional[List[str]] = None
    status: Literal["pending", "processing", "completed", "error", "cancelled"] = "pending"
    progress: int = 0
    total_images: int = 0
    processed_images: int = 0
    error_message: Optional[str] = None

class PresetCategory(BaseModel):
    """Category containing multiple presets."""
    name: str
    presets: Dict[str, dict] = Field(default_factory=dict)  # preset_name -> ShadowSettings.dict()
    locked: bool = False  # If true, presets cannot be modified

class CategorizedPresets(BaseModel):
    """Root structure for categorized presets."""
    categories: Dict[str, PresetCategory] = Field(default_factory=dict)
    # For backward compatibility, uncategorized presets go here
    uncategorized: Dict[str, dict] = Field(default_factory=dict)
