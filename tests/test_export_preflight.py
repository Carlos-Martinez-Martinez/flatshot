from pathlib import Path

from flatshot.application.contracts import ExportJobRequest
from flatshot.application.export_preflight import ensure_export_space
from flatshot.core.models import CurveData, ExportConfig, ExportVariant, ShadowSettings


def _request(tmp_path: Path) -> ExportJobRequest:
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    return ExportJobRequest(
        input_folder=tmp_path,
        input_files=[source],
        settings=ShadowSettings(),
        export_config=ExportConfig(
            output_width=100,
            output_height=100,
            variants=[
                ExportVariant(id="one", label="One", output_width=100, output_height=100),
                ExportVariant(id="two", label="Two", output_width=100, output_height=100),
            ],
        ),
        curve_data=CurveData(xp=[0.0, 1.0], fp=[1.0, 1.0]),
    )


def test_export_preflight_accounts_for_variant_pixels(tmp_path):
    request = _request(tmp_path)

    check = ensure_export_space(
        [request],
        checked_path=tmp_path,
        disk_usage=lambda _path: type("Usage", (), {"free": 100_000_000})(),
        buffer_bytes=0,
        multiplier=1,
    )

    assert check.required_bytes >= 100 * 100 * 4 * 2
