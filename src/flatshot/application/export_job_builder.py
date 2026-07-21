"""Build export job requests from shared render configuration."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from flatshot.application.contracts import ExportJobRequest, RenderConfiguration
from flatshot.core.models import ExportConfig


def build_export_job_requests(
    image_paths: Iterable[Path],
    *,
    export_config: ExportConfig,
    render_config: RenderConfiguration,
    image_overrides: dict | None = None,
) -> list[ExportJobRequest]:
    grouped: dict[Path, list[Path]] = {}
    for image_path in image_paths:
        path = Path(image_path)
        grouped.setdefault(path.parent, []).append(path)

    overrides = dict(image_overrides or {})
    return [
        ExportJobRequest(
            input_folder=folder,
            input_files=sorted(paths),
            settings=render_config.settings,
            export_config=export_config,
            curve_data=render_config.curve_data,
            preset_name=render_config.preset_name,
            image_overrides=overrides,
            render_config=render_config,
        )
        for folder, paths in sorted(grouped.items(), key=lambda item: str(item[0]))
    ]
