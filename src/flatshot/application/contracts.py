"""Qt-free data contracts for application services."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from flatshot.core.models import CurveData, ExportConfig, ShadowSettings


@dataclass(frozen=True)
class RenderConfiguration:
    settings: ShadowSettings
    curve_data: CurveData | None = None
    preset_name: str | None = None


@dataclass(frozen=True)
class ImageFileInfo:
    path: Path
    name: str
    stem: str
    suffix: str
    size_bytes: int
    has_local_override: bool = False


@dataclass(frozen=True)
class OmittedScanItem:
    path: Path
    name: str
    reason: str
    detail: str
    suffix: str = ""
    category: str = "ignored"
    severity: str = "ignored"


@dataclass(frozen=True)
class FolderScanResult:
    folder: Path
    exists: bool
    is_dir: bool
    images: list[ImageFileInfo] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    files_found: int = 0
    omitted: list[OmittedScanItem] = field(default_factory=list)


@dataclass(frozen=True)
class BatchScanResult:
    folders: list[FolderScanResult] = field(default_factory=list)
    total_folders: int = 0
    total_images: int = 0
    adjusted_images: int = 0
    errors: list[str] = field(default_factory=list)
    total_files: int = 0
    total_omitted: int = 0
    omitted_by_reason: dict[str, int] = field(default_factory=dict)
    omitted_by_category: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ExportJobRequest:
    input_folder: Path
    settings: ShadowSettings
    export_config: ExportConfig
    curve_data: CurveData | None = None
    preset_name: str | None = None
    input_files: list[Path] | None = None
    image_overrides: dict | None = None
    render_config: RenderConfiguration | None = None

    def __post_init__(self) -> None:
        render_config = self.render_config or RenderConfiguration(
            settings=self.settings,
            curve_data=self.curve_data,
            preset_name=self.preset_name,
        )
        object.__setattr__(self, "render_config", render_config)
        object.__setattr__(self, "settings", render_config.settings)
        object.__setattr__(self, "curve_data", render_config.curve_data)
        object.__setattr__(self, "preset_name", render_config.preset_name)


@dataclass(frozen=True)
class ExportJobResult:
    success: bool
    processed: int
    total: int
    errors: int
    duration: float
    destinations: list[Path] = field(default_factory=list)
    fatal_error: str | None = None


@dataclass(frozen=True)
class PreviewRequest:
    settings: ShadowSettings | dict
    target_size: tuple[int, int]
    curve_data: CurveData | dict | None = None
    scale_factor: float = 1.0
    is_preview: bool = True
    image_path: Path | None = None
    image: Image.Image | None = None
    render_config: RenderConfiguration | None = None

    def __post_init__(self) -> None:
        if self.render_config is None:
            return
        object.__setattr__(self, "settings", self.render_config.settings)
        object.__setattr__(self, "curve_data", self.render_config.curve_data)


@dataclass(frozen=True)
class PreviewResult:
    width: int
    height: int
    bytes_rgb: bytes
    mode: str = "RGB"
    warning: str | None = None


@dataclass(frozen=True)
class TilePreviewRequest:
    image_path: Path
    settings: ShadowSettings | dict
    target_size: tuple[int, int]
    curve_data: CurveData | dict | None = None
    scale_factor: float = 0.1
    is_preview: bool = True


@dataclass(frozen=True)
class TilePreviewResult:
    processed: PreviewResult
    original: PreviewResult
