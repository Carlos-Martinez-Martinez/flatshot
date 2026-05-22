"""Qt-free preparation for launching export workers."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from flatshot.application.contracts import ExportFolderPlan, ExportRunPlan
from flatshot.application.export_config_service import ExportConfigService
from flatshot.application.export_runner import get_enabled_export_variants
from flatshot.core.models import ExportConfig, ExportVariant


class ExportRunPlanner:
    """Build a stable export launch plan without depending on widgets."""

    def __init__(self, export_config_service: ExportConfigService | None = None) -> None:
        self.export_config_service = export_config_service or ExportConfigService()

    def prepare(
        self,
        folders: Iterable[str | Path],
        export_config: ExportConfig,
        *,
        active_variants: Iterable[ExportVariant] | None = None,
    ) -> ExportRunPlan:
        folder_paths = [Path(folder) for folder in folders]
        variants = (
            list(active_variants)
            if active_variants is not None
            else get_enabled_export_variants(export_config)
        )
        folder_plans = [
            ExportFolderPlan(
                folder=folder,
                input_files=sorted(folder.glob("*.png")),
            )
            for folder in folder_paths
        ]
        source_count = sum(len(folder_plan.input_files) for folder_plan in folder_plans)

        return ExportRunPlan(
            folders=folder_plans,
            destinations=self.export_config_service.destinations_for_folders(
                folder_paths,
                export_config,
            ),
            active_variants=variants,
            variant_labels=[variant.label for variant in variants],
            source_count=source_count,
            file_total=source_count * len(variants),
        )
