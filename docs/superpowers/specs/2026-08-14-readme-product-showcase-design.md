# FlatShot README Product Showcase Design

**Date:** 2026-08-14

**Status:** Approved for implementation planning

**Scope:** Public README presentation, representative sample processing, and documentation media

## Objective

Turn the root README from a documentation-first repository overview into a
product-first technical landing page. A visitor should understand what
FlatShot looks like, what workflow it supports, and what result it produces
before reaching installation, architecture, or contributor information.

The work must remain truthful to the current product. FlatShot prepares batches
of transparent product PNGs, previews presentation and shadows, supports review
and per-image adjustments, and exports new production-ready files. It does not
currently remove backgrounds from raw photography or run an AI model.

## Chosen direction

Use a balanced product-first README:

1. concise positioning and a large real application screenshot;
2. a short workflow animation;
3. real before/after examples produced by FlatShot;
4. a compact visual explanation of the workflow;
5. three supporting interface screenshots;
6. a short real-production context section;
7. download and quick-start instructions;
8. architecture, validation, safety, and contributor material below the
   product presentation.

This preserves the repository's technical credibility while giving a visual
product the visual proof it currently lacks.

Alternatives rejected:

- Adding a few screenshots to the existing structure would leave installation
  and repository mechanics ahead of the product story.
- An almost text-free showcase would be attractive but would weaken technical
  onboarding and make the project less useful to contributors.
- Presenting FlatShot as an AI background-removal tool would overstate the
  implemented product and make the examples misleading.

## Positioning and copy

The primary line is:

> Local-first production workbench for turning transparent fashion product
> images into consistent, e-commerce-ready assets.

Supporting copy should emphasize batch review, visual consistency, explicit
export control, safe source handling, and a native Windows portable. Avoid
claims that FlatShot accepts arbitrary raw photography, removes backgrounds,
or performs generative AI processing.

The transformation label is:

`SOURCE PNG -> FLATSHOT -> E-COMMERCE OUTPUT`

`SOURCE PNG` is more accurate than `RAW INPUT` for the supplied transparent
assets.

## README information architecture

The final root README will use this order:

1. `FlatShot` title and no more than four restrained badges.
2. Product positioning sentence.
3. Large hero screenshot from the native FlatShot window with a real sample
   batch loaded.
4. Short workflow demo showing the complete path from folder selection to
   export result.
5. `Source to output` section with four representative before/after examples.
6. `What it actually does` with the flow
   `Folder -> Adjust -> Preview -> Review -> Export` and no more than six
   bullets. Do not introduce an approval action that the current application
   does not expose.
7. Three interface screenshots: full workspace, selected-image adjustments,
   and batch review/export. The source/output comparison remains an editorial
   before/after section because FlatShot's in-app comparison controls are not
   exposed in production mode.
8. `Built for a real production workflow` with a concise origin statement and
   a note that the public demo uses synthetic sample garments to avoid exposing
   client assets.
9. `Download for Windows` using the repository's latest-release route.
10. Source quick start.
11. Production workflow, architecture, validation, portable builds, safety,
    contributing, and license.

Long development and packaging instructions may use `<details>` blocks where
that improves scanning. Safety guarantees and the source-not-overwritten rule
remain visible rather than hidden.

## Sample asset handling

The twelve supplied PNGs live under:

`C:\Users\Carlos\OneDrive\Escritorio\Flatshot\PNG`

They are source material for the documentation demo. They must not be renamed,
moved, overwritten, or recompressed in place. A separate local staging tree
will be created:

```text
C:\Users\Carlos\OneDrive\Escritorio\Flatshot\README-DEMO\
  input\
  output\
  capture\
```

The `input` directory will contain copies with fictional, brand-neutral product
references:

| Garment | Public demo filename |
| --- | --- |
| White T-shirt | `FS-SS26-0101-WH.png` |
| Black hoodie | `FS-SS26-0102-BK.png` |
| Light-wash jeans | `FS-SS26-0201-LB.png` |
| Blue striped shirt | `FS-SS26-0103-BL.png` |
| Cream cable-knit sweater | `FS-SS26-0104-CR.png` |
| Black dress | `FS-SS26-0301-BK.png` |
| Olive bomber jacket | `FS-SS26-0401-OL.png` |
| Navy polo shirt | `FS-SS26-0105-NV.png` |
| Beige pleated skirt | `FS-SS26-0302-BE.png` |
| Burgundy cardigan | `FS-SS26-0106-BU.png` |
| Black tailored shorts | `FS-SS26-0202-BK.png` |
| Grey padded vest | `FS-SS26-0402-GY.png` |

The full-resolution sample folder is not committed merely to support the demo.
Only optimized derived media required by the README is added to Git.

## Representative processing

The twelve staged inputs will be opened as a real FlatShot batch. A neutral
e-commerce presentation will be selected and applied through the existing
product controls. Settings must be recorded with the capture notes so the
documentation result is reproducible.

The public before/after set uses:

- white T-shirt, to demonstrate light-product separation;
- black hoodie, to demonstrate dark-product definition;
- light-wash jeans, to demonstrate a long lower-body silhouette;
- cream cable-knit sweater, to demonstrate texture and complex edges.

The source side is shown against a checkerboard or clearly labelled neutral
alpha surface. The output side is the actual exported FlatShot result. No
manual retouching may improve either side after export. If an asset contains an
unhelpful edge artifact, choose another representative garment rather than
silently repairing it.

This documentation work does not change the processing engine, presets,
default settings, or exported-image behavior.

## Hero screenshot

The hero is captured from FlatShot's native WebView2/pywebview window, without
browser chrome. It shows a real twelve-image batch using the fictional product
references, a representative selected garment, the batch rail, preview, and
the essential inspector/export context.

The composition should remain legible when GitHub renders the README at a
typical desktop width. Debug controls, user-specific absolute paths, unrelated
desktop content, notifications, and private information must not appear.

The preferred selected product is the olive bomber or cream cable-knit sweater,
chosen after capture based on which gives the clearest balance between the
viewer, thumbnails, and inspector.

## Workflow animation

The animation lasts approximately 10-15 seconds and shows one continuous,
credible flow:

1. select the staged folder;
2. select a garment;
3. apply or adjust the presentation;
4. compare source and processed appearance;
5. review readiness;
6. process/export;
7. show the completed result.

Capture is performed in the native FlatShot window. Cursor movement, pauses,
and repeated clicks are edited out of the final documentation media, but the
application state and results must remain real. Keep a local high-quality
master and commit an optimized animation suitable for GitHub. The target is an
animation under 8 MB; if acceptable readability cannot be achieved, use a
compact storyboard image and link to the local master only during review rather
than committing an oversized file.

## Supporting screenshots

Exactly three supporting screenshots are planned:

1. **Workspace:** batch rail, selected product, preview, and active context.
2. **Selected image:** processed preview and the real local/global adjustment
   context focused on one garment.
3. **Batch review and export:** readiness, exceptions if present, output
   configuration, and process action.

Each screenshot gets useful alt text. Screenshots must not duplicate the hero
without adding a distinct product capability.

## Documentation media layout

Optimized public media will live under:

```text
docs/readme-assets/
  hero-workbench.webp
  workflow-demo.gif
  source-output-light.webp
  source-output-dark.webp
  source-output-denim.webp
  source-output-texture.webp
  ui-workspace.webp
  ui-selected-adjustment.webp
  ui-batch-review.webp
```

Filenames may change only when the final selected garment makes a semantic name
more accurate. Static media should use WebP when it materially reduces size
without visible degradation. Derived assets must have unnecessary metadata
removed.

The reviewable draft will live at:

`docs/readme-preview/README.md`

It will use the intended final content order and relative media links. The root
`README.md` remains unchanged until the user approves the complete preview.
After approval, the draft content is applied to the root README and the preview
document is removed unless it provides continuing maintenance value.

## Real-production context

The case section uses this direction:

> Built for a real production workflow
>
> FlatShot originated inside a fashion e-commerce photography workflow, where
> large product-image batches need to be reviewed, prepared, and delivered
> consistently.

It must not mention the company, customers, internal volumes, private tools, or
confidential process details. A nearby note states that public screenshots use
synthetic sample garments so the real workflow can be demonstrated without
publishing client assets.

## Failure handling and truthful fallbacks

- If the staged folder does not scan, diagnose the existing workflow rather
  than altering source files.
- If the chosen preset produces a weak example, use another existing setting
  and record it; do not change processing code for README aesthetics.
- If a native-window capture fails because of WebView2 capture limitations,
  use an actual desktop screenshot path rather than substituting an unrelated
  mockup.
- If an export cannot be completed, do not fabricate a final output.
- If the animation is too large, reduce duration, dimensions, or frame rate;
  do not commit a needlessly heavy repository asset.
- If personal paths or desktop content are visible, recapture rather than blur
  sensitive content into a public asset.

## Validation and acceptance

The preview is ready for user review only when:

1. the original twelve PNGs are byte-for-byte unchanged;
2. the staged input names contain no ChatGPT timestamps or brand references;
3. the hero shows the native FlatShot window with a real batch loaded;
4. the animation covers folder, selection, adjustment, review, and export;
5. all four before/after outputs were generated by FlatShot;
6. exactly three supporting screenshots cover distinct capabilities;
7. no user-specific path or private desktop content is visible;
8. the draft opens with valid relative media links;
9. alt text describes every public image;
10. total committed media size is reviewed, with a target below 15 MB;
11. `git diff --check` is clean;
12. the root `README.md` is still unchanged during preview review;
13. exported image behavior in the application code is unchanged.

The final README application requires a second user approval after viewing the
draft and media together.

## Out of scope

- Changing FlatShot image processing to improve documentation examples.
- Adding AI, background removal, or raw-photo ingestion claims.
- Publishing client or company assets.
- Posting or replying on Reddit.
- Redesigning the application interface.
- Changing the portable runtime or release artifact.
- Updating the root README before preview approval.
- Committing the full-resolution twelve-image source set without a separate
  explicit decision.
