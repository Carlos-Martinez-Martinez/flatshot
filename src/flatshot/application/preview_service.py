"""Qt-free preview rendering service."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

from PIL import Image

from flatshot.application.contracts import PreviewRequest, PreviewResult, TilePreviewRequest, TilePreviewResult
from flatshot.core.engine import ShadowEngine
from flatshot.core.models import CurveData, SHADOW_ENGINE_DEFAULT, ShadowSettings, normalize_shadow_settings


class PreviewService:
    def render_preview(self, request: PreviewRequest) -> PreviewResult:
        settings = self._settings(request.settings)
        curve_data = self._curve_data(request.curve_data)

        if request.image is not None:
            return self._render_image(
                request.image,
                settings,
                request.target_size,
                request.scale_factor,
                curve_data,
                request.is_preview,
            )

        if request.image_path is None:
            raise ValueError("PreviewRequest requires image or image_path")

        with Image.open(Path(request.image_path)) as opened:
            image = opened.convert("RGBA")
            return self._render_image(
                image,
                settings,
                request.target_size,
                request.scale_factor,
                curve_data,
                request.is_preview,
            )

    def render_tile_preview(self, request: TilePreviewRequest) -> TilePreviewResult:
        settings = self._settings(request.settings)
        curve_data = self._curve_data(request.curve_data)

        with Image.open(Path(request.image_path)) as opened:
            image = opened.convert("RGBA")
            processed = self._render_image(
                image,
                settings,
                request.target_size,
                request.scale_factor,
                curve_data,
                request.is_preview,
            )

            original = image.copy()
            original.thumbnail((request.target_size[0], request.target_size[1]))
            original_result = self._to_rgb_result(original, settings.bg_color)

        return TilePreviewResult(processed=processed, original=original_result)

    @staticmethod
    def _settings(settings: ShadowSettings | Mapping) -> ShadowSettings:
        return normalize_shadow_settings(settings, missing_engine=SHADOW_ENGINE_DEFAULT)

    @staticmethod
    def _curve_data(curve_data: CurveData | Mapping | None) -> CurveData | None:
        if curve_data is None:
            return None
        if isinstance(curve_data, CurveData):
            return curve_data
        return CurveData(**dict(curve_data))

    def _render_image(
        self,
        image: Image.Image,
        settings: ShadowSettings,
        target_size: tuple[int, int],
        scale_factor: float,
        curve_data: CurveData | None,
        is_preview: bool,
    ) -> PreviewResult:
        final_pil, diagnostics = ShadowEngine._aplicar_efectos_with_diagnostics(
            image,
            settings,
            target_size,
            scale_factor=scale_factor,
            curve_data=curve_data,
            is_preview=is_preview,
        )
        warning = diagnostics.warning if diagnostics.fallback_used else None
        return self._to_rgb_result(final_pil, settings.bg_color, warning)

    @staticmethod
    def _to_rgb_result(
        image: Image.Image,
        bg_color: tuple[int, int, int],
        warning: str | None = None,
    ) -> PreviewResult:
        if image.mode == "RGBA":
            bg = Image.new("RGB", image.size, bg_color)
            bg.paste(image, (0, 0), mask=image)
            image = bg

        image = image.convert("RGB")
        return PreviewResult(
            width=image.width,
            height=image.height,
            bytes_rgb=image.tobytes("raw", "RGB"),
            warning=warning,
        )
