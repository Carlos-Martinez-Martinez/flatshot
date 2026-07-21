from pathlib import Path

from flatshot.application.contracts import RenderConfiguration
from flatshot.application.export_job_builder import build_export_job_requests
from flatshot.core.models import ExportConfig, ShadowSettings
from flatshot.core.scaling import DEFAULT_SCALE_CURVE, normalize_curve_data


def test_build_export_job_requests_groups_images_by_folder_with_render_configuration(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    first_b = first / "b.png"
    first_a = first / "a.png"
    second_a = second / "a.png"
    for path in (first_b, first_a, second_a):
        path.write_bytes(b"png")
    export_config = ExportConfig(format="PNG", output_width=8, output_height=8)
    curve_data = normalize_curve_data(DEFAULT_SCALE_CURVE.copy())
    render_config = RenderConfiguration(
        settings=ShadowSettings(opacity=0, blur=0, noise=0),
        curve_data=curve_data,
        preset_name="Plano",
    )
    image_overrides = {str(first_a): {"size_delta": 4}}

    requests = build_export_job_requests(
        [first_b, second_a, first_a],
        export_config=export_config,
        render_config=render_config,
        image_overrides=image_overrides,
    )

    assert [request.input_folder for request in requests] == [first, second]
    assert requests[0].input_files == [first_a, first_b]
    assert requests[1].input_files == [second_a]
    assert all(request.render_config == render_config for request in requests)
    assert all(request.settings == render_config.settings for request in requests)
    assert all(request.curve_data == curve_data for request in requests)
    assert all(request.preset_name == "Plano" for request in requests)
    assert requests[0].image_overrides == image_overrides


def test_build_export_job_requests_returns_no_jobs_for_empty_image_list():
    render_config = RenderConfiguration(settings=ShadowSettings())

    requests = build_export_job_requests(
        [],
        export_config=ExportConfig(),
        render_config=render_config,
    )

    assert requests == []
