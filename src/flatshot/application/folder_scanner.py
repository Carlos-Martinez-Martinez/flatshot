"""Folder scanning service independent from PyQt widgets."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, UnidentifiedImageError

from flatshot.application.contracts import BatchScanResult, FolderScanResult, ImageFileInfo, OmittedScanItem
from flatshot.core.overrides import has_image_override, override_key

SUPPORTED_IMAGE_SUFFIXES = {".png"}
IGNORED_SYSTEM_NAMES = {
    ".ds_store",
    "desktop.ini",
    "thumbs.db",
}
IGNORED_SYSTEM_SUFFIXES = {
    ".ini",
    ".tmp",
    ".temp",
}


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
        total_files = sum(result.files_found for result in folder_results)
        omitted_items = [item for result in folder_results for item in result.omitted]
        omitted_by_reason: dict[str, int] = {}
        omitted_by_category: dict[str, int] = {}
        for item in omitted_items:
            omitted_by_reason[item.reason] = omitted_by_reason.get(item.reason, 0) + 1
            omitted_by_category[item.category] = omitted_by_category.get(item.category, 0) + 1
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
            total_files=total_files,
            total_omitted=len(omitted_items),
            omitted_by_reason=omitted_by_reason,
            omitted_by_category=omitted_by_category,
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
            entries = sorted(folder.iterdir(), key=lambda path: path.name.lower())
        except OSError as exc:
            return FolderScanResult(
                folder=folder,
                exists=True,
                is_dir=True,
                errors=[f"No se pudo leer la carpeta {folder}: {exc}"],
            )

        files_found = 0
        image_paths: list[Path] = []
        omitted: list[OmittedScanItem] = []

        for entry in entries:
            if entry.is_dir():
                omitted.append(
                    OmittedScanItem(
                        path=entry,
                        name=entry.name,
                        reason="subfolder_not_scanned",
                        detail="Subcarpeta no escaneada",
                        category="ignored",
                        severity="ignored",
                    )
                )
                continue

            if not entry.is_file():
                continue

            files_found += 1
            suffix = entry.suffix.lower()
            if suffix not in SUPPORTED_IMAGE_SUFFIXES:
                reason, detail = self._unsupported_file_reason(entry)
                omitted.append(
                    OmittedScanItem(
                        path=entry,
                        name=entry.name,
                        suffix=entry.suffix,
                        reason=reason,
                        detail=detail,
                        category="ignored",
                        severity="ignored",
                    )
                )
                continue

            if not self._is_readable_png(entry):
                omitted.append(
                    OmittedScanItem(
                        path=entry,
                        name=entry.name,
                        suffix=entry.suffix,
                        reason="read_error",
                        detail="No se pudo leer como PNG válido",
                        category="warning",
                        severity="warning",
                    )
                )
                continue

            image_paths.append(entry)

        images = [self._image_info(path, image_overrides, errors) for path in image_paths]
        return FolderScanResult(
            folder=folder,
            exists=True,
            is_dir=True,
            images=images,
            errors=errors,
            files_found=files_found,
            omitted=omitted,
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

    @staticmethod
    def _is_readable_png(path: Path) -> bool:
        try:
            with Image.open(path) as image:
                image.verify()
            return True
        except (OSError, UnidentifiedImageError):
            return False

    @staticmethod
    def _unsupported_file_reason(path: Path) -> tuple[str, str]:
        name = path.name.lower()
        suffix = path.suffix.lower()
        if name in IGNORED_SYSTEM_NAMES:
            return "system_file", "Archivo del sistema ignorado"
        if suffix in IGNORED_SYSTEM_SUFFIXES:
            return "temporary_or_config_file", "Archivo temporal o de configuración ignorado"
        return "unsupported_extension", f"Extensión no admitida: {path.suffix or 'sin extensión'}"
