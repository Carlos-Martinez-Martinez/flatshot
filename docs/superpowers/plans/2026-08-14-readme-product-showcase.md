# FlatShot README Product Showcase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a truthful, product-first FlatShot README preview using a real native-app session, real FlatShot exports, optimized documentation media, and a protected second approval before replacing the root README.

**Architecture:** Keep full-resolution sample inputs and capture masters outside Git under a dedicated OneDrive staging tree. Commit only optimized documentation media and a temporary Markdown preview; after explicit preview approval, apply the approved copy to the root README and remove the temporary preview document. No application, processing, preset, export, or frontend code changes are allowed.

**Tech Stack:** PowerShell 7, FlatShot's existing Python 3.12 environment, native WebView2/pywebview portable, FFmpeg `C:\ffmpeg\bin\ffmpeg.exe`, GitHub-flavored Markdown, WebP, GIF.

## Global Constraints

- The source folder is `C:\Users\Carlos\OneDrive\Escritorio\Flatshot\PNG` and its twelve PNGs remain byte-for-byte unchanged.
- Work only on branch `codex/readme-product-showcase`.
- The root `README.md` remains unchanged until the explicit user-review checkpoint in Task 6 is approved.
- Use copies with the exact fictional references defined in the approved design; never commit ChatGPT timestamp filenames.
- Public claims must describe transparent product PNG preparation, previews, shadows, review, and export; do not claim AI, raw-photo ingestion, or background removal.
- Public product flow is `Folder -> Adjust -> Preview -> Review -> Export`; do not invent an approval action.
- Hero, workflow animation, and production UI screenshots must show the native FlatShot window without browser chrome or development controls.
- Use only existing presets and output profiles. Do not change image-processing code or presets for documentation aesthetics.
- Do not add runtime or development dependencies.
- Commit only optimized derived media; keep source PNG copies, JPG outputs, lossless captures, and MP4 masters outside Git.
- Target `workflow-demo.gif` below 8 MB and all committed media below 15 MB.
- No user-specific absolute path, desktop notification, client asset, or confidential company detail may be visible in public media.
- Root README application requires a second explicit approval after the complete preview is shown.

## File Map

**Create in Git during preview:**

- `docs/readme-assets/hero-workbench.webp` — large native-window hero.
- `docs/readme-assets/workflow-demo.gif` — optimized 10-15 second workflow.
- `docs/readme-assets/source-output-light.webp` — white T-shirt source/output pair.
- `docs/readme-assets/source-output-dark.webp` — black hoodie source/output pair.
- `docs/readme-assets/source-output-denim.webp` — jeans source/output pair.
- `docs/readme-assets/source-output-texture.webp` — cable-knit source/output pair.
- `docs/readme-assets/ui-workspace.webp` — workspace capability screenshot.
- `docs/readme-assets/ui-selected-adjustment.webp` — selected-image/local-adjustment screenshot.
- `docs/readme-assets/ui-batch-review.webp` — batch review/export screenshot.
- `docs/readme-preview/README.md` — complete reviewable README draft.
- `docs/readme-preview/capture-notes.md` — source hashes, exact preset/output settings, capture dimensions, and media sizes used during review.

**Modify only after Task 6 approval:**

- `README.md` — replace the documentation-first ordering with the approved product-first draft.

**Delete only after Task 6 approval and final README application:**

- `docs/readme-preview/README.md`
- `docs/readme-preview/capture-notes.md`

**Local-only staging:**

```text
C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\
  input\
  output\
  capture\
    source-hashes.json
    staged-hashes.json
    workflow-master.mp4
    *.png
```

---

### Task 1: Build a non-destructive sample staging batch

**Files:**

- Read: `C:\Users\Carlos\OneDrive\Escritorio\Flatshot\PNG\*.png`
- Create locally: `C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\input\*.png`
- Create locally: `C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\capture\source-hashes.json`
- Create locally: `C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\capture\staged-hashes.json`

**Interfaces:**

- Consumes: the twelve original PNG files supplied by the user.
- Produces: a twelve-file staging folder with fictional references and two SHA-256 manifests used by every later task.

- [ ] **Step 1: Verify repository and source preconditions**

Run:

```powershell
git branch --show-current
git status --short --branch
Get-ChildItem -LiteralPath 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\PNG' -File -Filter '*.png' |
  Sort-Object Name |
  Select-Object Name, Length
```

Expected: branch `codex/readme-product-showcase`, clean worktree, exactly twelve PNG files.

- [ ] **Step 2: Create the local staging directories without deleting existing data**

Run:

```powershell
$demoRoot = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO'
foreach ($directory in @('input', 'output', 'capture')) {
  $target = Join-Path $demoRoot $directory
  if (-not (Test-Path -LiteralPath $target)) {
    New-Item -ItemType Directory -Path $target | Out-Null
  }
}
```

Expected: all three directories exist; no existing file is removed or overwritten.

- [ ] **Step 3: Record source hashes before copying**

Run:

```powershell
$sourceRoot = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\PNG'
$captureRoot = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\capture'
Get-ChildItem -LiteralPath $sourceRoot -File -Filter '*.png' |
  Sort-Object Name |
  Get-FileHash -Algorithm SHA256 |
  Select-Object Path, Hash |
  ConvertTo-Json |
  Set-Content -LiteralPath (Join-Path $captureRoot 'source-hashes.json') -Encoding utf8
```

Expected: `source-hashes.json` contains twelve entries.

- [ ] **Step 4: Copy each source to its exact fictional reference**

Run:

```powershell
$sourceRoot = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\PNG'
$inputRoot = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\input'
$renameMap = [ordered]@{
  'ChatGPT Image 14 ago 2026, 23_09_52 (1).png' = 'FS-SS26-0101-WH.png'
  'ChatGPT Image 14 ago 2026, 23_09_52 (2).png' = 'FS-SS26-0102-BK.png'
  'ChatGPT Image 14 ago 2026, 23_09_53 (3).png' = 'FS-SS26-0201-LB.png'
  'ChatGPT Image 14 ago 2026, 23_09_53 (4).png' = 'FS-SS26-0103-BL.png'
  'ChatGPT Image 14 ago 2026, 23_09_53 (5).png' = 'FS-SS26-0104-CR.png'
  'ChatGPT Image 14 ago 2026, 23_09_54 (6).png' = 'FS-SS26-0301-BK.png'
  'ChatGPT Image 14 ago 2026, 23_12_06 (1).png' = 'FS-SS26-0401-OL.png'
  'ChatGPT Image 14 ago 2026, 23_12_06 (2).png' = 'FS-SS26-0105-NV.png'
  'ChatGPT Image 14 ago 2026, 23_12_06 (3).png' = 'FS-SS26-0302-BE.png'
  'ChatGPT Image 14 ago 2026, 23_12_06 (4).png' = 'FS-SS26-0106-BU.png'
  'ChatGPT Image 14 ago 2026, 23_12_07 (5).png' = 'FS-SS26-0202-BK.png'
  'ChatGPT Image 14 ago 2026, 23_12_07 (6).png' = 'FS-SS26-0402-GY.png'
}
foreach ($entry in $renameMap.GetEnumerator()) {
  $source = Join-Path $sourceRoot $entry.Key
  $destination = Join-Path $inputRoot $entry.Value
  if (Test-Path -LiteralPath $destination) {
    $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    $destinationHash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash
    if ($sourceHash -ne $destinationHash) {
      throw "Conflicting staged file: $destination"
    }
    continue
  }
  Copy-Item -LiteralPath $source -Destination $destination -ErrorAction Stop
}
```

Expected: twelve staged files with `FS-SS26-*` names; rerunning is idempotent when hashes match and fails closed on a conflict.

- [ ] **Step 5: Record staged hashes and prove byte identity**

Run:

```powershell
$inputRoot = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\input'
$captureRoot = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\capture'
Get-ChildItem -LiteralPath $inputRoot -File -Filter '*.png' |
  Sort-Object Name |
  Get-FileHash -Algorithm SHA256 |
  Select-Object Path, Hash |
  ConvertTo-Json |
  Set-Content -LiteralPath (Join-Path $captureRoot 'staged-hashes.json') -Encoding utf8
if ((Get-ChildItem -LiteralPath $inputRoot -File -Filter '*.png').Count -ne 12) {
  throw 'Expected exactly 12 staged PNG files.'
}
```

Expected: twelve unique staged names and the same set of twelve SHA-256 values as the source manifest.

---

### Task 2: Produce a real FlatShot output batch

**Files:**

- Execute: `scripts/build_portable.py`
- Execute: `release/FlatShotPortable/Abrir FlatShot.vbs`
- Read through UI: `C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\input`
- Create through FlatShot: `C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\output\*_PRO.jpg`

**Interfaces:**

- Consumes: Task 1 staged inputs and the existing `Luz cenital`, `Estándar oscuro`, and `Web RGB230` product configuration.
- Produces: twelve real FlatShot JPG exports and a loaded native application state for capture.

- [ ] **Step 1: Stop only the previously launched development runner if it is still active**

Inspect the current task terminal/session first. If unified session `14851` is still running `apps/flatshot-desktop/run_dev.py --open`, send `Ctrl+C` to that session. Otherwise query exact command lines and stop only the matching `run_dev.py` parent process; never kill all Python processes.

Expected: ports `4173` and `8765` are free or owned only by the native launcher started later.

- [ ] **Step 2: Refresh and smoke-check the development portable**

Run:

```powershell
python scripts/build_portable.py --skip-venv
release\FlatShotPortable\venv\Scripts\python.exe release\FlatShotPortable\FlatShot.pyw --smoke
```

Expected: portable refresh succeeds and smoke exits `0` after frontend and bridge checks.

- [ ] **Step 3: Launch the native window**

Run:

```powershell
Start-Process -FilePath 'C:\Users\Carlos\Documents\Scripts\flatshot\release\FlatShotPortable\Abrir FlatShot.vbs'
```

Expected: a visible window titled `FlatShot`, backed by a newly started `msedgewebview2` process; no browser tab.

- [ ] **Step 4: Load the staged folder and establish the documented look**

Drive the visible UI using its production labels:

1. choose `Elegir carpeta` or `Seleccionar carpeta`;
2. select `C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\input`;
3. verify the batch count is twelve;
4. select global adjustment `Luz cenital` and apply it to the batch;
5. select `FS-SS26-0102-BK.png`, choose `Estándar oscuro`, and apply it only to that image;
6. keep the existing `Web RGB230` output, JPG format, `Gris claro` background `(230, 230, 230)`, suffix `_PRO`, and naming `{original}{suffix}`;
7. set the destination to `C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\output`.

Expected: preview generation completes, output readiness is positive, and the black hoodie visibly uses a local adjustment while the batch uses `Luz cenital`.

- [ ] **Step 5: Export the twelve-image batch through the real UI**

Use the primary `Procesar 12 imágenes` action, review the `Exportar lote` confirmation, and choose `Exportar`. Wait for `completed`; do not close the window because Task 3 reuses the loaded state.

Expected: the UI reports completion and remains responsive.

- [ ] **Step 6: Verify outputs and source immutability**

Run:

```powershell
$outputRoot = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\output'
$outputs = Get-ChildItem -LiteralPath $outputRoot -File -Filter '*_PRO.jpg' | Sort-Object Name
if ($outputs.Count -ne 12) { throw "Expected 12 exports, found $($outputs.Count)." }
$outputs | Select-Object Name, Length
$sourceRoot = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\PNG'
$before = Get-Content -Raw 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\capture\source-hashes.json' | ConvertFrom-Json
$after = Get-ChildItem -LiteralPath $sourceRoot -File -Filter '*.png' | Get-FileHash -Algorithm SHA256
foreach ($item in $before) {
  $match = $after | Where-Object Path -eq $item.Path
  if (-not $match -or $match.Hash -ne $item.Hash) { throw "Source changed: $($item.Path)" }
}
```

Expected: twelve non-empty exports and all original hashes unchanged.

---

### Task 3: Capture the native product session and workflow master

**Files:**

- Create locally: `C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\capture\hero-workbench.png`
- Create locally: `...\capture\ui-workspace.png`
- Create locally: `...\capture\ui-selected-adjustment.png`
- Create locally: `...\capture\ui-batch-review.png`
- Create locally: `...\capture\workflow-master.mp4`

**Interfaces:**

- Consumes: Task 2 loaded native window and completed output batch.
- Produces: lossless still captures plus a high-quality MP4 master for Task 4.

- [ ] **Step 1: Prepare a clean capture state**

Keep the native window at its default `1360 x 900` or maximize it if the complete interface remains visible. Close unrelated windows behind it, disable transient notifications for the capture interval, ensure no absolute path is expanded in the UI, and keep production mode (`dev=0`).

Expected: window title is exactly `FlatShot`; no browser chrome, QA controls, logs, desktop notifications, or private paths are visible.

- [ ] **Step 2: Capture the hero**

Select `FS-SS26-0401-OL.png` (olive bomber), show the standard workspace with batch rail, processed preview, adjustment context, and output readiness, then run:

```powershell
& 'C:\ffmpeg\bin\ffmpeg.exe' -y -f gdigrab -framerate 1 -draw_mouse 0 -i 'title=FlatShot' -frames:v 1 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\capture\hero-workbench.png'
```

Expected: one lossless full-window PNG with readable product names and no outside desktop content.

- [ ] **Step 3: Capture three distinct supporting states**

Capture each state with the same FFmpeg command pattern and the indicated filename:

1. `ui-workspace.png`: cream cable-knit selected, full batch rail and essential inspector.
2. `ui-selected-adjustment.png`: black hoodie selected, local `Estándar oscuro` adjustment context visible.
3. `ui-batch-review.png`: review/export context showing twelve ready images, `Web RGB230`, destination readiness, and process action without opening a user-specific full path.

Expected: exactly three PNGs, each documenting a distinct production capability.

- [ ] **Step 4: Restore a pre-export state for the workflow recording**

Use the loaded folder and existing settings, return to the normal ready state, select the white T-shirt, and ensure the next export can use an empty destination or a non-colliding naming run. If prior outputs would collide, use a fresh local-only destination `README-DEMO\output\workflow-run`; create it without deleting existing outputs.

- [ ] **Step 5: Record a high-quality workflow master**

Start a 25-second hidden FFmpeg recorder:

```powershell
$captureRoot = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\capture'
$ffmpegArgs = @(
  '-y', '-f', 'gdigrab', '-framerate', '15', '-draw_mouse', '1',
  '-i', 'title=FlatShot', '-t', '25', '-c:v', 'libx264', '-preset', 'veryfast',
  '-crf', '18', '-pix_fmt', 'yuv420p', (Join-Path $captureRoot 'workflow-master.mp4')
)
$recorder = Start-Process -FilePath 'C:\ffmpeg\bin\ffmpeg.exe' -ArgumentList $ffmpegArgs -WindowStyle Hidden -PassThru
```

Wait exactly three seconds after starting the recorder, then perform one coherent
sequence during seconds `3-17`: choose the staged folder if the picker can be
shown without losing state, select the black hoodie, expose its adjustment
context, return to processed preview, open review/export, start export, and
show the completed result. Allow the recorder to exit on its 25-second limit.

Expected: a playable MP4 with every requested workflow state; waiting time may remain in the master because Task 4 trims it.

- [ ] **Step 6: Inspect every capture before optimization**

Open all four PNGs and the MP4. Reject and recapture any frame containing a private path, unrelated window, cursor over important copy, loading skeleton, partial image, clipped panel, browser chrome, or WebView fallback.

---

### Task 4: Create optimized public documentation media

**Files:**

- Create: `docs/readme-assets/*.webp`
- Create: `docs/readme-assets/workflow-demo.gif`
- Read: Task 1 staged inputs, Task 2 outputs, and Task 3 captures.

**Interfaces:**

- Consumes: lossless local captures and real FlatShot exports.
- Produces: the nine optimized media files referenced by the Markdown preview.

- [ ] **Step 1: Create the public asset directory**

Run:

```powershell
if (-not (Test-Path -LiteralPath 'docs\readme-assets')) {
  New-Item -ItemType Directory -Path 'docs\readme-assets' | Out-Null
}
```

- [ ] **Step 2: Convert the hero and supporting screenshots to WebP**

Run this mapping with FFmpeg quality `86` and metadata stripped:

```powershell
$captureRoot = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\capture'
$stillMap = [ordered]@{
  'hero-workbench.png' = 'docs\readme-assets\hero-workbench.webp'
  'ui-workspace.png' = 'docs\readme-assets\ui-workspace.webp'
  'ui-selected-adjustment.png' = 'docs\readme-assets\ui-selected-adjustment.webp'
  'ui-batch-review.png' = 'docs\readme-assets\ui-batch-review.webp'
}
foreach ($entry in $stillMap.GetEnumerator()) {
  & 'C:\ffmpeg\bin\ffmpeg.exe' -y -i (Join-Path $captureRoot $entry.Key) -map_metadata -1 -c:v libwebp -quality 86 -compression_level 6 $entry.Value
  if ($LASTEXITCODE -ne 0) { throw "FFmpeg failed for $($entry.Key)" }
}
```

Expected: four readable WebP files with no metadata or transparency requirement.

- [ ] **Step 3: Build four deterministic source/output composites**

For each pair, use the source PNG on a light neutral panel and the real FlatShot JPG on its RGB230 panel. The filter below creates a `1440 x 720` side-by-side image without retouching either product:

```powershell
function New-SourceOutputComposite {
  param(
    [Parameter(Mandatory)] [string] $Source,
    [Parameter(Mandatory)] [string] $Output,
    [Parameter(Mandatory)] [string] $Destination
  )
  $filter = "color=c=0xF4F4F4:s=720x720:d=1[bg0];color=c=0xE6E6E6:s=720x720:d=1[bg1];[0:v]scale=680:680:force_original_aspect_ratio=decrease[src];[1:v]scale=680:680:force_original_aspect_ratio=decrease[out];[bg0][src]overlay=(W-w)/2:(H-h)/2:format=auto[left];[bg1][out]overlay=(W-w)/2:(H-h)/2:format=auto[right];[left][right]hstack=inputs=2[final]"
  & 'C:\ffmpeg\bin\ffmpeg.exe' -y -i $Source -i $Output -filter_complex $filter -map '[final]' -frames:v 1 -map_metadata -1 -c:v libwebp -quality 88 -compression_level 6 $Destination
  if ($LASTEXITCODE -ne 0) { throw "Composite failed: $Destination" }
}
$inputRoot = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\input'
$outputRoot = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\output'
New-SourceOutputComposite (Join-Path $inputRoot 'FS-SS26-0101-WH.png') (Join-Path $outputRoot 'FS-SS26-0101-WH_PRO.jpg') 'docs\readme-assets\source-output-light.webp'
New-SourceOutputComposite (Join-Path $inputRoot 'FS-SS26-0102-BK.png') (Join-Path $outputRoot 'FS-SS26-0102-BK_PRO.jpg') 'docs\readme-assets\source-output-dark.webp'
New-SourceOutputComposite (Join-Path $inputRoot 'FS-SS26-0201-LB.png') (Join-Path $outputRoot 'FS-SS26-0201-LB_PRO.jpg') 'docs\readme-assets\source-output-denim.webp'
New-SourceOutputComposite (Join-Path $inputRoot 'FS-SS26-0104-CR.png') (Join-Path $outputRoot 'FS-SS26-0104-CR_PRO.jpg') 'docs\readme-assets\source-output-texture.webp'
```

Expected: four side-by-side WebPs whose left pixels come from staged source files and right pixels from FlatShot exports.

- [ ] **Step 4: Trim and optimize the workflow animation**

Use the fixed seconds `3-17` capture interval defined in Task 3, then run:

```powershell
$master = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\capture\workflow-master.mp4'
$trimmed = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\capture\workflow-trimmed.mp4'
$palette = 'C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\capture\workflow-palette.png'
& 'C:\ffmpeg\bin\ffmpeg.exe' -y -ss '00:00:03' -i $master -t '00:00:14' -an -c:v libx264 -crf 18 -preset veryfast $trimmed
& 'C:\ffmpeg\bin\ffmpeg.exe' -y -i $trimmed -vf 'fps=12,scale=960:-2:flags=lanczos,palettegen=max_colors=128' $palette
& 'C:\ffmpeg\bin\ffmpeg.exe' -y -i $trimmed -i $palette -lavfi 'fps=12,scale=960:-2:flags=lanczos[x];[x][1:v]paletteuse=dither=sierra2_4a' 'docs\readme-assets\workflow-demo.gif'
```

If the GIF exceeds 8 MB, regenerate at `fps=10`, width `800`, and `max_colors=96`. Do not reduce legibility below readable primary labels.

- [ ] **Step 5: Validate media count, dimensions, and total size**

Run:

```powershell
$assets = Get-ChildItem -LiteralPath 'docs\readme-assets' -File
if ($assets.Count -ne 9) { throw "Expected 9 public media files, found $($assets.Count)." }
$totalBytes = ($assets | Measure-Object Length -Sum).Sum
if ($totalBytes -gt 15MB) { throw "Public media exceeds 15 MB: $totalBytes bytes" }
$assets | Sort-Object Name | Select-Object Name, Length
& 'C:\ffmpeg\bin\ffprobe.exe' -v error -show_entries stream=width,height,duration -of default=noprint_wrappers=1 'docs\readme-assets\workflow-demo.gif'
```

Expected: nine files, GIF below 8 MB, total below 15 MB, no zero-byte output.

- [ ] **Step 6: Visually inspect all optimized files**

Use the image viewer for every WebP and play the GIF. Compare representative optimized media against the lossless captures and outputs. Reject visible text damage, color shifts, halos introduced by composition, clipped products, or unreadable UI.

- [ ] **Step 7: Commit the optimized media**

Run:

```powershell
git add -- docs/readme-assets
git diff --cached --check
git commit -m "docs: add FlatShot product showcase media"
```

Expected: commit contains exactly nine documentation media files.

---

### Task 5: Build and validate the product-first README preview

**Files:**

- Create: `docs/readme-preview/README.md`
- Create: `docs/readme-preview/capture-notes.md`
- Read without modifying: `README.md`

**Interfaces:**

- Consumes: Task 4 media paths and the existing technical README content.
- Produces: a complete GitHub-flavored Markdown preview ready for the second user approval.

- [ ] **Step 1: Create the preview directory**

Run:

```powershell
if (-not (Test-Path -LiteralPath 'docs\readme-preview')) {
  New-Item -ItemType Directory -Path 'docs\readme-preview' | Out-Null
}
```

- [ ] **Step 2: Write the product-facing top half of the preview**

Create `docs/readme-preview/README.md` with `apply_patch`. Its opening content must use these exact claims and relative links:

```markdown
# FlatShot

[![Release](https://img.shields.io/github/v/release/Carlos-Martinez-Martinez/flatshot)](https://github.com/Carlos-Martinez-Martinez/flatshot/releases/latest)
[![Windows](https://img.shields.io/badge/Windows-portable-0078D4)](https://github.com/Carlos-Martinez-Martinez/flatshot/releases/latest)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../../LICENSE)

Local-first production workbench for turning transparent fashion product images into consistent, e-commerce-ready assets.

![FlatShot workspace with a twelve-item fashion batch loaded](../readme-assets/hero-workbench.webp)

## See the workflow

Open a folder, adjust the presentation, review the batch, and export production-ready copies without modifying the source images.

![FlatShot workflow from folder selection to completed export](../readme-assets/workflow-demo.gif)

## Source PNG to e-commerce output

Every result below was exported by FlatShot from the sample source PNG shown beside it. No manual retouching was applied after export.

| Light garment | Dark garment |
| --- | --- |
| ![White T-shirt source PNG and FlatShot output](../readme-assets/source-output-light.webp) | ![Black hoodie source PNG and FlatShot output](../readme-assets/source-output-dark.webp) |

| Denim silhouette | Textured knit |
| --- | --- |
| ![Light-wash jeans source PNG and FlatShot output](../readme-assets/source-output-denim.webp) | ![Cable-knit sweater source PNG and FlatShot output](../readme-assets/source-output-texture.webp) |

## What it actually does

`Folder -> Adjust -> Preview -> Review -> Export`

- Imports local folders of PNG product images into a reviewable batch.
- Applies reusable presentation presets globally or to an individual image.
- Previews background, placement, and shadow without changing the source file.
- Surfaces invalid files, exclusions, and per-image exceptions before export.
- Configures format, naming, destination, and reusable output profiles explicitly.
- Processes long batches with progress, pause, stop, manifests, and safe non-overwriting output.

## Inside FlatShot

### Production workspace

![FlatShot batch rail, processed preview, and inspector](../readme-assets/ui-workspace.webp)

### Per-image control

![FlatShot selected-image adjustment workflow](../readme-assets/ui-selected-adjustment.webp)

### Review and export readiness

![FlatShot batch review and export configuration](../readme-assets/ui-batch-review.webp)

## Built for a real production workflow

FlatShot originated inside a fashion e-commerce photography workflow, where large product-image batches need to be reviewed, prepared, and delivered consistently.

The public demo uses synthetic, brand-neutral sample garments so the workflow can be shown without publishing client assets.

## Download for Windows

[Download the latest portable Windows release](https://github.com/Carlos-Martinez-Martinez/flatshot/releases/latest). Extract the ZIP and run `FlatShot.exe` or `Abrir FlatShot.vbs`; no system-wide Python installation is required.
```

Expected: the first screen of the preview is product-focused, all claims match current behavior, and no private path appears.

- [ ] **Step 3: Reorder and preserve the technical content**

After `Download for Windows`, add the existing stable-release status and source `Quick start`, followed by the current `Production workflow`, `Architecture`, `Validation`, `Portable Windows builds`, `Safety and compatibility`, `Contributing`, and `License` content from root `README.md`. Remove the old top-level `Highlights` section because its unique product information is now covered by `What it actually does`. Keep commands, versions, security links, and the source-not-overwritten guarantee unchanged.

Expected: the preview is a complete replacement README, not merely a visual fragment.

- [ ] **Step 4: Write capture notes with exact provenance**

Create `docs/readme-preview/capture-notes.md` with `apply_patch`. Record:

- date and branch;
- source and staged manifest paths;
- `Luz cenital` as the global adjustment;
- `Estándar oscuro` as the black-hoodie local adjustment;
- `Web RGB230`, JPG, `(230, 230, 230)`, `_PRO`, and `{original}{suffix}`;
- native window title and capture dimensions;
- exact source/output references used by each comparison;
- each public asset's byte size;
- statement that sources were hash-verified unchanged and outputs were generated by FlatShot.

- [ ] **Step 5: Validate links and root README immutability**

Run:

```powershell
$preview = Get-Content -Raw 'docs\readme-preview\README.md'
$matches = [regex]::Matches($preview, '\]\(\.\./readme-assets/([^\)]+)\)')
foreach ($match in $matches) {
  $path = Join-Path 'docs\readme-assets' $match.Groups[1].Value
  if (-not (Test-Path -LiteralPath $path)) { throw "Missing preview asset: $path" }
}
if ($matches.Count -ne 9) { throw "Expected 9 media references, found $($matches.Count)." }
git diff origin/main -- README.md
git diff --check
```

Expected: nine valid media references, no root README diff, and clean whitespace validation.

- [ ] **Step 6: Run documentation-safe repository checks**

Run:

```powershell
python scripts/check_application_answers.py
python -m pytest
```

Expected: both commands pass. CSS/frontend audit commands are not required because no frontend file changes.

- [ ] **Step 7: Commit the reviewable preview**

Run:

```powershell
git add -- docs/readme-preview
git diff --cached --check
git commit -m "docs: add product-first README preview"
```

Expected: commit contains only the two preview Markdown files.

---

### Task 6: Present the complete preview and stop for approval

**Files:**

- Review: `docs/readme-preview/README.md`
- Review: `docs/readme-assets/*`
- Confirm unchanged: `README.md`

**Interfaces:**

- Consumes: Tasks 4 and 5 committed preview artifacts.
- Produces: explicit user approval or a concrete revision list. Task 7 must not begin without approval.

- [ ] **Step 1: Show the preview and representative media**

Provide a clickable link to `docs/readme-preview/README.md`, render the hero, four source/output composites, and GIF in the handoff, and summarize total media size and exact checks run.

- [ ] **Step 2: Report the protected state**

State explicitly that original PNG hashes match, root `README.md` is unchanged, no processing code changed, and all displayed outputs came from FlatShot.

- [ ] **Step 3: Wait for explicit approval**

Accept either approval to apply the draft to root `README.md` or requested changes. If changes are requested, update preview/media only, rerun Task 5 validation, and present the revised preview again.

---

### Task 7: Apply the approved preview to the root README

**Files:**

- Modify: `README.md`
- Delete: `docs/readme-preview/README.md`
- Delete: `docs/readme-preview/capture-notes.md`
- Preserve: `docs/readme-assets/*`

**Interfaces:**

- Consumes: explicit Task 6 approval and the approved preview content.
- Produces: the final product-first root README with stable media links and no temporary preview documents.

- [ ] **Step 1: Apply the approved Markdown**

Use `apply_patch` to replace root `README.md` with the approved preview content, changing preview-relative media paths from `../readme-assets/...` to `docs/readme-assets/...` and changing the preview-relative license link `../../LICENSE` to `LICENSE`.

- [ ] **Step 2: Remove the temporary preview files**

Use `apply_patch` to delete `docs/readme-preview/README.md` and `docs/readme-preview/capture-notes.md`. Remove the now-empty directory only if empty; keep specs, plans, and public assets.

- [ ] **Step 3: Validate all root README media links**

Run:

```powershell
$readme = Get-Content -Raw 'README.md'
$matches = [regex]::Matches($readme, '\]\(docs/readme-assets/([^\)]+)\)')
foreach ($match in $matches) {
  $path = Join-Path 'docs\readme-assets' $match.Groups[1].Value
  if (-not (Test-Path -LiteralPath $path)) { throw "Missing README asset: $path" }
}
if ($matches.Count -ne 9) { throw "Expected 9 README media references, found $($matches.Count)." }
```

Expected: exactly nine valid product-media references.

- [ ] **Step 4: Run final repository verification**

Run:

```powershell
git diff --check
python scripts/check_application_answers.py
python -m pytest
git status --short --branch
```

Expected: checks pass; changes are limited to root README, approved assets, specs/plans, and deletion of temporary preview files.

- [ ] **Step 5: Reconfirm source and media safety**

Re-run the Task 2 source-hash comparison. Confirm public media total remains below 15 MB and `git diff --name-only origin/main` contains no application, frontend, processing, configuration, or test files.

- [ ] **Step 6: Commit the final README application**

Run:

```powershell
git add -A -- README.md docs/readme-assets docs/readme-preview
git diff --cached --check
git commit -m "docs: turn README into FlatShot product showcase"
```

Expected: final documentation commit applies the approved preview and removes temporary review files without changing application output.
