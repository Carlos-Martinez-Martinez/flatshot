"""Folder scanning service independent from PyQt widgets."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from flatshot.application.contracts import BatchScanResult, FolderScanResult, ImageFileInfo
from flatshot.core.overrides import has_image_override, override_key


class FolderScanner:
    """Scan selected source folders for PNG files and local override state."""

    def scan_folders(
        self,
        folders: Iterable[str | Path],
        image_overrides: dict | None = None,
    ) -> BatchScanResult:
        overrides = dict(image_overrides or {})
        folder_results = [self._scan_folder(Path(folder), overrides) for folder in folders]
        errors = [error for result in folder_results for error in result.errors]
        total_images = sum(len(result.images) for result in folder_results)
        adjusted_images = sum(
            1
            for result in folder_results
            for image in result.images
            if image.has_local_override
        )

        return BatchScanResult(
            folders=folder_results,
            total_folders=len(folder_results),
            total_images=total_images,
            adjusted_images=adjusted_images,
            errors=errors,
        )

    def _scan_folder(self, folder: Path, image_overrides: dict) -> FolderScanResult:
        exists = folder.exists()
        is_dir = folder.is_dir()
        errors: list[str] = []

        if not exists:
            return FolderScanResult(
                folder=folder,
                exists=False,
                is_dir=False,
                errors=[f"La carpeta no existe: {folder}"],
            )

        if not is_dir:
            return FolderScanResult(
                folder=folder,
                exists=True,
                is_dir=False,
                errors=[f"No es una carpeta: {folder}"],
            )

        try:
            image_paths = sorted(folder.glob("*.png"), key=lambda path: path.name.lower())
        except OSError as exc:
            return FolderScanResult(
                folder=folder,
                exists=True,
                is_dir=True,
                errors=[f"No se pudo leer la carpeta {folder}: {exc}"],
            )

        images = [self._image_info(path, image_overrides, errors) for path in image_paths]
        return FolderScanResult(
            folder=folder,
            exists=True,
            is_dir=True,
            images=images,
            errors=errors,
        )

    def _image_info(self, path: Path, image_overrides: dict, errors: list[str]) -> ImageFileInfo:
        try:
            size_bytes = path.stat().st_size
        except OSError as exc:
            size_bytes = 0
            errors.append(f"No se pudo leer {path}: {exc}")

        local_key = override_key(str(path))
        return ImageFileInfo(
            path=path,
            name=path.name,
            stem=path.stem,
            suffix=path.suffix,
            size_bytes=size_bytes,
            has_local_override=has_image_override(image_overrides.get(local_key, {})),
        )
