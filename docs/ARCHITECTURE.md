# Architecture

FlatShot is a local desktop application with a static web interface and a Python bridge. Its primary constraint is that maintenance and UI work must not silently change exported images.

## Layers

```text
apps/flatshot-desktop/frontend
  presentation, interaction state, bridge requests
          |
src/flatshot/bridge
  loopback HTTP adapter, authorization, path policy
          |
src/flatshot/application
  folder scans, previews, export planning, queues, snapshots, events
          |
src/flatshot/core
  processing models, validation, naming, image/shadow algorithms
          |
src/flatshot/utils and local filesystem
  configuration, cache, atomic output operations
```

The dependency direction is downward. Core and application services do not import browser objects or UI widgets, and service inputs and outputs should stay serializable for future CLI or shell adapters.

## Runtime flow

The desktop launcher serves frontend assets and starts the bridge on `127.0.0.1`. It generates a per-run token, supplies the frontend origin allowlist, and opens the app. The frontend sends authenticated requests. Scan and export runners coordinate background work and emit state updates to the UI.

## File safety

- Imported source images are read-only inputs.
- Export tasks snapshot sources when required for stable processing.
- Output planning validates destinations and collisions before processing.
- Output creation uses temporary files and exclusive publication paths where implemented.
- Cache cleanup is limited to a dedicated, marked FlatShot cache directory and recognized cache filenames.

Path checks reduce accidental and malicious traversal. A remaining low-severity race exists when an authorized destination directory is concurrently replaced between validation and asynchronous write; robust cross-platform directory-handle-relative writes are tracked in the roadmap.

## Output compatibility

Image behavior includes alpha/RGB conversion, background composition, dimensions, DPI, JPG quality and subsampling, PNG encoding, naming, suffixes, destinations, cache keys, and local overrides. Changes in these areas require targeted tests and representative manual comparisons. Structural refactors should preserve these contracts.

## Configuration

Configuration is stored under an OS-appropriate FlatShot namespace. Readers tolerate missing optional values and migration copies legacy configuration without deleting it. Committed code must not contain user-specific absolute paths.

## Testing boundaries

- Unit and service tests validate models, paths, state, naming, processing, and bridge behavior.
- CSS audits validate cascade ownership and frontend contracts.
- E2E and visual smoke scripts validate static application structure and assets.
- Benchmarks detect major render regressions.
- Portable builds validate packaging structure.

Automated checks do not prove subjective visual equivalence or production behavior on every machine; manual checks remain part of output-sensitive releases.
