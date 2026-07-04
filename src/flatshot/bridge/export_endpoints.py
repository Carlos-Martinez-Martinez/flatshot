"""Export endpoint operations for FlatShotBridgeService."""

from __future__ import annotations

from typing import Any, Mapping
from uuid import uuid4

from flatshot.application.export_runner import get_enabled_export_variants
from flatshot.bridge.errors import BridgeError
from flatshot.bridge.export_jobs import BridgeExportJob
from flatshot.bridge.serialization import serialize_path


def prepare_export(service, payload: Mapping[str, Any]) -> dict[str, Any]:
    requests, config = service._export_requests(payload)
    service._validate_export_outputs(requests)
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
    image_count = sum(len(request.input_files or []) for request in requests)
    variants = get_enabled_export_variants(config)
    destinations = service.export_config_service.destinations_for_folders(
        [request.input_folder for request in requests],
        config,
    )
    job_id = uuid4().hex

    with service._jobs_lock:
        service._prune_finished_jobs_locked(reserve_slots=1)
        active_count = sum(
            1 for job in service._jobs.values() if job.status in {"queued", "running", "paused", "cancelling"}
        )
        if active_count >= service.max_concurrent_exports:
            raise BridgeError(
                "export_busy",
                "Ya hay una exportación en curso. Espera a que termine o cancélala.",
                status=409,
            )

    job = BridgeExportJob(
        job_id=job_id,
        requests=requests,
        source_images=image_count,
        total_outputs=image_count * len(variants),
        destinations=destinations,
        runner_factory=service.export_runner_factory,
    )
    with service._jobs_lock:
        service._jobs[job_id] = job
    job.start()
    return job.snapshot()
