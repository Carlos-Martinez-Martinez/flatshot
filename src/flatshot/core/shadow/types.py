from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from PIL import Image

from flatshot.core.models import ShadowSettings


@dataclass(frozen=True)
class ShadowPaint:
    rgb: Tuple[int, int, int] = (0, 0, 0)


@dataclass(frozen=True)
class RenderDiagnostics:
    engine_requested: str
    engine_used: str
    fallback_used: bool = False
    warning: Optional[str] = None
    roi: Optional[Tuple[int, int, int, int]] = None


@dataclass(frozen=True)
class ShadowRenderContext:
    settings: ShadowSettings
    canvas_size: Tuple[int, int]
    scale_factor: float
    subject_width: int
    subject_mask_canvas: Image.Image
    subject_mask_local: Image.Image
    subject_position: Tuple[int, int]
    luminance_value: float
    background_rgb: Optional[Tuple[int, int, int]] = None
    is_preview: bool = False
    paint: ShadowPaint = field(default_factory=ShadowPaint)


@dataclass(frozen=True)
class ShadowRenderResult:
    shadow: Image.Image
    diagnostics: RenderDiagnostics
