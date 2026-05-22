from pathlib import Path

from flatshot.application.export_config_service import ExportConfigService
from flatshot.core.models import ExportConfig, WEB_RGB230, WHITE_RGB255


def test_build_from_settings_preserves_existing_defaults_and_normalizes_format():
    service = ExportConfigService()

    config = service.build_from_settings({"format": "jpeg"}, variants=[WEB_RGB230])

    assert config.output_folder_name == "_SALIDA_PRO"
    assert config.suffix == "_PRO"
    assert config.format == "JPG"
    assert config.output_width == 1800
    assert config.output_height == 2400
    assert config.naming_template == "{original}{suffix}"
    assert config.output_destination == "subfolder"
    assert config.variants == [WEB_RGB230]


def test_build_from_settings_accepts_ui_destination_overrides(tmp_path):
    service = ExportConfigService()

    config = service.build_from_settings(
        {"output_destination": "subfolder", "custom_output_path": None},
        output_destination_override="custom",
        custom_output_path_override=tmp_path,
    )

    assert config.output_destination == "custom"
    assert config.custom_output_path == str(tmp_path)


def test_validate_accepts_normal_subfolder_config():
    service = ExportConfigService()
    config = ExportConfig(output_destination="subfolder", output_folder_name="_SALIDA_PRO")

    assert service.validate(config) == []


def test_validate_reports_custom_destination_without_path():
    service = ExportConfigService()
    config = ExportConfig(output_destination="custom", custom_output_path=None)

    assert service.validate(config) == ["El destino personalizado requiere una carpeta."]


def test_validate_reports_invalid_dimensions_format_destination_folder_and_template():
    service = ExportConfigService()
    config = ExportConfig(
        format="GIF",
        output_width=0,
        output_height=-1,
        output_destination="elsewhere",
        output_folder_name="",
        naming_template="",
    )

    errors = service.validate(config)

    assert "El formato de exportación debe ser JPG o PNG." in errors
    assert "El tamaño de exportación debe ser positivo." in errors
    assert "El destino de exportación debe ser subfolder o custom." in errors
    assert "La plantilla de nombre no puede estar vacía." in errors


def test_validate_reports_empty_subfolder_name_for_subfolder_destination():
    service = ExportConfigService()
    config = ExportConfig(output_destination="subfolder", output_folder_name="")

    assert "El nombre de la subcarpeta de salida no puede estar vacío." in service.validate(config)


def test_destinations_for_folders_uses_subfolder_destination_and_enabled_variants(tmp_path):
    service = ExportConfigService()
    folder_a = tmp_path / "a"
    folder_b = tmp_path / "b"
    white_variant = WHITE_RGB255.model_copy(
        update={"enabled": True, "output_subfolder": "white"}
    )
    disabled_variant = WEB_RGB230.model_copy(update={"id": "disabled", "enabled": False})
    config = ExportConfig(
        output_destination="subfolder",
        output_folder_name="_OUT",
        variants=[WEB_RGB230, white_variant, disabled_variant],
    )

    assert service.destinations_for_folders([folder_a, folder_b], config) == [
        folder_a / "_OUT",
        folder_a / "_OUT" / "white",
        folder_b / "_OUT",
        folder_b / "_OUT" / "white",
    ]


def test_destinations_for_folders_uses_custom_destination(tmp_path):
    service = ExportConfigService()
    custom = tmp_path / "exports"
    config = ExportConfig(
        output_destination="custom",
        custom_output_path=str(custom),
        variants=[WEB_RGB230],
    )

    assert service.destinations_for_folders([tmp_path / "ignored"], config) == [custom]


def test_destinations_for_folders_returns_empty_for_missing_custom_path(tmp_path):
    service = ExportConfigService()
    config = ExportConfig(output_destination="custom", custom_output_path=None, variants=[WEB_RGB230])

    assert service.destinations_for_folders([tmp_path], config) == []
