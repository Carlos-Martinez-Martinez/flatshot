"""
FlatShot CLI - Command Line Interface
Process product images from the command line.
"""
import argparse
import sys
from pathlib import Path

from flatshot.application.contracts import ExportJobRequest
from flatshot.application.config_paths import ConfigPathResolver
from flatshot.application.events import ExportImageCompletedEvent, ExportLogEvent, ExportProgressEvent
from flatshot.application.export_runner import ExportRunner
from flatshot.application.log_service import ActivityLogService
from flatshot.application.preset_service import PresetService
from flatshot.application.settings_service import SettingsService
from flatshot.core.models import (
    SHADOW_ENGINE_COMPAT,
    SHADOW_ENGINE_LEGACY,
    SHADOW_ENGINE_REALISTIC_V2,
    SHADOW_ENGINE_STUDIO_2_5D,
    ExportConfig,
    ShadowSettings,
    normalize_shadow_settings,
)
from flatshot.core.scaling import DEFAULT_SCALE_CURVE, normalize_curve_data


class CliExportSink:
    def __init__(self, logger: ActivityLogService) -> None:
        self.logger = logger

    def emit(self, event) -> None:
        if isinstance(event, ExportProgressEvent):
            print(f"\r[{event.percent:3d}%] Processing: {event.processed}/{event.total}", end="", flush=True)
            return

        if isinstance(event, ExportImageCompletedEvent) and not event.success:
            self.logger.log_error(event.image_name, str(event.source_path or ""))
            return

        if isinstance(event, ExportLogEvent):
            if event.message.startswith("Aviso:"):
                print(f"\nWarning: {event.message.removeprefix('Aviso:').strip()}")
            elif event.message.startswith("Error:"):
                self.logger.log_error(event.message)
                print(f"\n{event.message}")


def _path_resolver() -> ConfigPathResolver:
    return ConfigPathResolver()


def _preset_service() -> PresetService:
    return PresetService(_path_resolver().config_dir())


def _log_service() -> ActivityLogService:
    return ActivityLogService.from_config_dir(_path_resolver().config_dir())


def list_presets():
    """List all available presets."""
    service = _preset_service()
    presets = service.load_categorized_presets()
    flat = service.get_flat_presets_from_categorized(presets)
    
    if not flat:
        print("No presets found.")
        return
    
    print("\nAvailable Presets:\n")
    
    # Show by category
    for category in presets.categories.values():
        if category.presets:
            print(f"  [{category.name}]")
            for name in category.presets.keys():
                print(f"    • {name}")
    
    if presets.uncategorized:
        print("  [Sin categoría]")
        for name in presets.uncategorized.keys():
            print(f"    • {name}")
    
    print()


def get_preset_settings(preset_name: str) -> ShadowSettings:
    """Get ShadowSettings from a preset name."""
    service = _preset_service()
    presets = service.load_categorized_presets()
    flat = service.get_flat_presets_from_categorized(presets)
    
    if preset_name not in flat:
        print(f"Error: Preset '{preset_name}' not found.")
        print("Use --list-presets to see available presets.")
        sys.exit(1)
    
    return normalize_shadow_settings(
        flat[preset_name],
        missing_engine=SHADOW_ENGINE_COMPAT,
    )


def _load_app_settings() -> dict:
    """Load app settings for CLI defaults without changing old visual output."""
    return SettingsService(_path_resolver().settings_file()).load_existing(fallback={})


def process_folder(args):
    """Process a folder of images."""
    input_folder = Path(args.input)
    
    if not input_folder.exists():
        print(f"Error: Folder '{input_folder}' does not exist.")
        sys.exit(1)
    
    app_settings = _load_app_settings()

    # Get settings from explicit CLI, preset, global config or model defaults.
    if args.preset:
        settings = get_preset_settings(args.preset)
        print(f"Using preset: {args.preset}")
    elif app_settings:
        settings = normalize_shadow_settings(
            app_settings,
            missing_engine=SHADOW_ENGINE_COMPAT,
        )
        print("Using global settings")
    else:
        settings = ShadowSettings()
        print("Using default settings")

    shadow_engine_override = getattr(args, "shadow_engine", None)
    if shadow_engine_override:
        settings = settings.model_copy(update={"shadow_engine": shadow_engine_override})
    
    # Parse output size
    if args.size:
        try:
            width, height = map(int, args.size.lower().split('x'))
        except ValueError:
            print(f"Error: Invalid size format '{args.size}'. Use WIDTHxHEIGHT (e.g., 1800x2400)")
            sys.exit(1)
    else:
        width, height = 1800, 2400
    
    # Build export config
    export_config = ExportConfig(
        output_folder_name=args.output or "_SALIDA_CLI",
        suffix=args.suffix or "_PRO",
        format=args.format or "JPG",
        output_width=width,
        output_height=height,
        naming_template=args.template or "{original}{suffix}"
    )
    
    # Find images
    images = list(input_folder.glob("*.png"))
    total = len(images)
    
    if total == 0:
        print(f"No PNG images found in '{input_folder}'")
        sys.exit(0)
    
    print(f"\nFound {total} images to process")
    print(f"Output: {input_folder / export_config.output_folder_name}")
    print(f"Size: {width}x{height}")
    print(f"Format: {export_config.format}")
    
    if args.dry_run:
        print("\n[DRY RUN] No images will be processed.")
        return
    
    # Load curve data
    curve_dict = app_settings.get('scale_curve', DEFAULT_SCALE_CURVE.copy())
    curve_data = normalize_curve_data(curve_dict)

    logger = _log_service()
    logger.log_export_start(str(input_folder), total, args.preset)

    request = ExportJobRequest(
        input_folder=input_folder,
        input_files=sorted(images),
        settings=settings,
        export_config=export_config,
        curve_data=curve_data,
    )
    result = ExportRunner(event_sink=CliExportSink(logger)).run(request)

    logger.log_export_complete(str(input_folder), result.processed, result.total, result.duration)

    print(f"\n\n✓ Completed: {result.processed}/{result.total} images in {result.duration:.1f}s")
    if result.errors > 0:
        print(f"✗ Errors: {result.errors}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="flatshot",
        description="FlatShot - Product Image Shadow Tool"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List presets command
    subparsers.add_parser("list-presets", help="List available presets")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process images in a folder")
    process_parser.add_argument(
        "--input", "-i", required=True,
        help="Input folder containing PNG images"
    )
    process_parser.add_argument(
        "--preset", "-p",
        help="Preset name to use for shadow settings"
    )
    process_parser.add_argument(
        "--shadow-engine",
        choices=[SHADOW_ENGINE_REALISTIC_V2, SHADOW_ENGINE_STUDIO_2_5D, SHADOW_ENGINE_LEGACY],
        help="Shadow renderer override: realistic_v2, studio_2_5d or legacy"
    )
    process_parser.add_argument(
        "--output", "-o",
        help="Output subfolder name (default: _SALIDA_CLI)"
    )
    process_parser.add_argument(
        "--size", "-s",
        help="Output size as WIDTHxHEIGHT (default: 1800x2400)"
    )
    process_parser.add_argument(
        "--format", "-f", choices=["JPG", "PNG"], default="JPG",
        help="Output format (default: JPG)"
    )
    process_parser.add_argument(
        "--suffix",
        help="Filename suffix (default: _PRO)"
    )
    process_parser.add_argument(
        "--template",
        help="Naming template (default: {original}{suffix})"
    )
    process_parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be done without processing"
    )
    
    args = parser.parse_args()
    
    if args.command == "list-presets":
        list_presets()
    elif args.command == "process":
        process_folder(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
