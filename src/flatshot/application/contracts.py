"""Qt-free data contracts for application services."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from flatshot.core.models import CurveData, ExportConfig, ShadowSettings


@dataclass(frozen=True)
class ImageFileInfo:
    path: Path
    name: str
    stem: str
    suffix: str
    size_bytes: int
    has_local_override: bool = False


@dataclass(frozen=True)
class FolderScanResult:
    folder: Path
    exists: bool
    is_dir: bool
    images: list[ImageFileInfo] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class BatchScanResult:
    folders: list[FolderScanResult] = field(default_factory=list)
    total_folders: int = 0
    total_images: int = 0
    adjusted_images: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExportJobRequest:
    input_folder: Path
    settings: ShadowSettings
    export_config: ExportConfig
    curve_data: CurveData | None = None
    preset_name: str | None = None
    input_files: list[Path] | None = None
    image_overrides: dict | None = None


@dataclass(frozen=True)
class ExportJobResult:
    success: bool
    processed: int
    total: int
    errors: int
    duration: float
    destinations: list[Path] = field(default_factory=list)
