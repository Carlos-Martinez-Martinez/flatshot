"""Export endpoint operations for FlatShotBridgeService."""

from __future__ import annotations

from typing import Any, Mapping
from uuid import uuid4

from flatshot.application.export_preflight import InsufficientExportSpaceError
from flatshot.application.export_runner import get_enabled_export_variants
from flatshot.bridge.errors import BridgeError
from flatshot.bridge.export_jobs import BridgeExportJob
from flatshot.bridge.serialization import serialize_path


def prepare_export(service, payload: Mapping[str, Any]) -> dict[str, Any]:
    requests, config = service._export_requests(payload)
    service._validate_export_outputs(requests)
    _validate_export_space(service, requests)
    image_count = sum(len(request.input_files or []) for request in requests)
    variants = get_enabled_export_variants(config)
    destinations = service.export_config_service.destinations_for_folders(
        [request.input_folder for request in requests],
        config,
    )
    return {
        "ok": True,
        "sourceImages": image_count,
        "totalOutputs": image_count * len(variants),
        "destinations": [serialize_path(path) for path in destinations],
        "activeVariants": [
            {
                "id": variant.id,
                "label": variant.label,
                "format": variant.format or config.format,
                "outputWidth": variant.output_width or config.output_width,
                "outputHeight": variant.output_height or config.output_height,
                "destinationMode": variant.output_destination or config.output_destination,
                "outputFolderName": variant.output_folder_name or config.output_folder_name,
                "customOutputPath": variant.custom_output_path or config.custom_output_path,
                "namingTemplate": variant.naming_template or config.naming_template,
                "suffix": variant.suffix,
                "maxFileSizeKb": variant.max_file_size_kb if (variant.format or config.format) == "JPG" else None,
            }
            for variant in variants
        ],
        "errors": [],
    }


def start_export(service, payload: Mapping[str, Any]) -> dict[str, Any]:
    requests, config = service._export_requests(payload)
    service._validate_export_outputs(requests)
    _validate_export_space(service, requests)
    image_count = sum(len(request.input_files or []) for request in requests)
    variants = get_enabled_export_variants(config)
    destinations = service.export_config_service.destinations_for_folders(
        [request.input_folder for request in requests],
        config,
    )
    job_id = uuid4().hex

    job = BridgeExportJob(
        job_id=job_id,
        requests=requests,
        source_images=image_count,
        total_outputs=image_count * len(variants),
        destinations=destinations,
        runner_factory=service.export_runner_factory,
        manifest_writer=service.export_job_repository.write_manifest,
    )
    with service._jobs_lock:
        service._prune_finished_jobs_locked(reserve_slots=1)
        active_count = sum(
            1 for active_job in service._jobs.values()
            if active_job.status in {"queued", "running", "paused", "cancelling"}
        )
        if active_count >= service.max_concurrent_exports:
            raise BridgeError(
                "export_busy",
                "Ya hay una exportación en curso. Espera a que termine o cancélala.",
                status=409,
            )
        service._jobs[job_id] = job
    job.start()
    return job.snapshot()


def _validate_export_space(service, requests) -> None:
    try:
        service._ensure_export_space(requests)
    except InsufficientExportSpaceError as exc:
        check = exc.check
        raise BridgeError(
            "export_insufficient_space",
            "No hay espacio suficiente para preparar la exportación. "
            f"Disponible: {_format_bytes(check.free_bytes)}; "
            f"necesario: {_format_bytes(check.required_bytes)}.",
            status=507,
        ) from exc


def _format_bytes(value: int) -> str:
    size = float(max(0, int(value)))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
