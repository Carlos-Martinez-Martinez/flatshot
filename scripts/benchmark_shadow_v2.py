from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
from pathlib import Path
from time import perf_counter

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flatshot.core.engine import ShadowEngine
from flatshot.core.models import ShadowSettings
from flatshot.core.shadow.realistic_v2 import render_realistic_v2
from flatshot.core.shadow.studio_2_5d import render_studio_2_5d
from flatshot.core.shadow.types import ShadowRenderContext


OBJECTIVES_MS = {
    "shadow_pure_1800x2400": 100.0,
    "preview_complete": 150.0,
    "export_complete_1800x2400_no_save": 500.0,
}


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    idx = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * pct)))
    return ordered[idx]


def make_subject(size: tuple[int, int], product: str, alpha: str) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if product == "small":
        box = (int(w * 0.38), int(h * 0.32), int(w * 0.62), int(h * 0.66))
    else:
        box = (int(w * 0.20), int(h * 0.14), int(w * 0.80), int(h * 0.84))

    if alpha == "complex":
        draw.rounded_rectangle(box, radius=max(6, w // 80), fill=(65, 90, 150, 235))
        for i in range(10):
            x0 = box[0] + i * max(1, (box[2] - box[0]) // 10)
            draw.line((x0, box[1], x0 + 30, box[3]), fill=(255, 255, 255, 70), width=max(1, w // 240))
        draw.ellipse(
            (
                box[0] - int(w * 0.03),
                box[1] + int(h * 0.20),
                box[0] + int(w * 0.10),
                box[1] + int(h * 0.36),
            ),
            fill=(65, 90, 150, 160),
        )
    else:
        draw.rounded_rectangle(box, radius=max(4, w // 100), fill=(70, 95, 155, 255))
    return img


def make_context(target_size: tuple[int, int], product: str, background: str, alpha: str, engine: str) -> ShadowRenderContext:
    subject = make_subject(target_size, product, alpha)
    mask = subject.getchannel("A")
    settings = ShadowSettings(
        shadow_engine=engine,
        adaptive_zoom=False,
        angle=180,
        distance=32,
        blur=30,
        contact_blur=10,
        opacity=30,
        noise=0,
        transparent_bg=(background == "transparent"),
    )
    return ShadowRenderContext(
        settings=settings,
        canvas_size=target_size,
        scale_factor=1.0,
        subject_width=mask.getbbox()[2] - mask.getbbox()[0] if mask.getbbox() else 0,
        subject_mask_canvas=mask,
        subject_mask_local=mask.crop(mask.getbbox()) if mask.getbbox() else mask,
        subject_position=(0, 0),
        luminance_value=0.5,
        background_rgb=None if background == "transparent" else (245, 245, 245),
    )


def time_call(runs: int, fn) -> list[float]:
    values = []
    for _ in range(runs):
        start = perf_counter()
        fn()
        values.append((perf_counter() - start) * 1000.0)
    return values


def summarize(values: list[float]) -> dict:
    return {
        "median_ms": round(statistics.median(values), 2),
        "p95_ms": round(percentile(values, 0.95), 2),
        "min_ms": round(min(values), 2),
        "max_ms": round(max(values), 2),
    }


def render_shadow_pure(context: ShadowRenderContext):
    if context.settings.shadow_engine == "studio_2_5d":
        return render_studio_2_5d(context)
    return render_realistic_v2(context)


def benchmark_case(size: tuple[int, int], product: str, background: str, alpha: str, runs: int, include_save: bool, engine: str) -> dict:
    source = make_subject((900, 1200), product, alpha)
    settings = ShadowSettings(
        shadow_engine=engine,
        adaptive_zoom=False,
        angle=180,
        distance=32,
        blur=30,
        contact_blur=10,
        opacity=30,
        noise=0,
        transparent_bg=(background == "transparent"),
        bg_color=(245, 245, 245),
    )
    context = make_context(size, product, background, alpha, engine)

    result = {
        "case": {
            "size": f"{size[0]}x{size[1]}",
            "product": product,
            "background": background,
            "alpha": alpha,
        },
        "shadow_pure": summarize(time_call(runs, lambda: render_shadow_pure(context))),
        "preview_complete": summarize(
            time_call(
                runs,
                lambda: ShadowEngine.aplicar_efectos(
                    source,
                    settings,
                    (450, 600),
                    scale_factor=0.25,
                    is_preview=True,
                ),
            )
        ),
        "export_complete_no_save": summarize(
            time_call(
                runs,
                lambda: ShadowEngine.aplicar_efectos(source, settings, size, scale_factor=1.0),
            )
        ),
    }

    if include_save:
        with tempfile.TemporaryDirectory(prefix="flatshot_bench_") as tmp:
            out_path = Path(tmp) / "out.png"

            def export_with_save():
                image = ShadowEngine.aplicar_efectos(source, settings, size, scale_factor=1.0)
                image.save(out_path, optimize=False, compress_level=0)

            result["export_complete_with_save"] = summarize(time_call(runs, export_with_save))
    return result


def build_cases(quick: bool, smoke: bool = False) -> list[tuple[tuple[int, int], str, str, str]]:
    if smoke:
        return [((120, 160), "small", "white", "clean")]
    if quick:
        return [((1800, 2400), "large", "white", "complex")]

    cases = []
    for size in ((1000, 1500), (1800, 2400), (3000, 4000)):
        cases.append((size, "small", "white", "clean"))
        cases.append((size, "large", "white", "complex"))
        cases.append((size, "large", "transparent", "complex"))
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark FlatShot shadow renderers.")
    parser.add_argument("--runs", type=int, default=5, help="Runs per metric.")
    parser.add_argument("--quick", action="store_true", help="Run only the 1800x2400 reference case.")
    parser.add_argument("--smoke", action="store_true", help="Run a tiny case suitable for test and CI smoke checks.")
    parser.add_argument("--include-save", action="store_true", help="Also measure export with PNG save.")
    parser.add_argument("--engine", choices=["realistic_v2", "studio_2_5d"], default="realistic_v2", help="Shadow engine to benchmark.")
    parser.add_argument("--json", dest="json_path", help="Optional output JSON path.")
    args = parser.parse_args()

    runs = max(1, args.runs)
    results = [
        benchmark_case(size, product, background, alpha, runs, args.include_save, args.engine)
        for size, product, background, alpha in build_cases(args.quick, args.smoke)
    ]

    print(f"FlatShot {args.engine} benchmark")
    print(f"runs={runs} include_save={args.include_save}")
    for item in results:
        case = item["case"]
        label = f"{case['size']} {case['product']} {case['background']} {case['alpha']}"
        print(f"\n{label}")
        for metric, values in item.items():
            if metric == "case":
                continue
            print(f"  {metric}: median={values['median_ms']}ms p95={values['p95_ms']}ms")

    reference = next((item for item in results if item["case"]["size"] == "1800x2400"), None)
    if reference:
        print("\nObjectives")
        checks = {
            "shadow_pure_1800x2400": reference["shadow_pure"]["median_ms"],
            "preview_complete": reference["preview_complete"]["median_ms"],
            "export_complete_1800x2400_no_save": reference["export_complete_no_save"]["median_ms"],
        }
        for name, value in checks.items():
            target = OBJECTIVES_MS[name]
            status = "PASS" if value < target else "WARN"
            print(f"  {status} {name}: {value}ms target<{target}ms")

    if args.json_path:
        Path(args.json_path).write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
