# Preset Import Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add portable preset export/import to the FlatShot desktop bridge and UI, with `Importar como copia` as the default conflict strategy.

**Architecture:** Keep preset parsing, normalization, conflict detection, copy-name generation, overwrite behavior, and persistence in `PresetService`. Expose small JSON bridge operations for export, import preview, and import execution. Keep the frontend responsible for file picker/download UI, conflict modal state, and status text only.

**Tech Stack:** Python 3.10+, Pillow-independent preset service logic, Pydantic models in `flatshot.core.models`, built-in `http.server` bridge, vanilla HTML/CSS/JS frontend, pytest, Node-based frontend helper tests.

---

## File Map

- Modify: `src/flatshot/application/preset_service.py`
  - Add service-owned export payload generation.
  - Add import preview from parsed JSON data.
  - Add copy and overwrite import strategies.
  - Keep existing file-based import/export methods as wrappers for compatibility.
- Modify: `src/flatshot/bridge/service.py`
  - Add `export_presets`, `preview_preset_import`, and `import_presets`.
  - Convert `PresetService` `ValueError` into short `InvalidRequestError` messages.
- Modify: `src/flatshot/bridge/http_server.py`
  - Add `GET /presets/export`.
  - Add `POST /presets/import/preview`.
  - Add `POST /presets/import`.
- Modify: `apps/flatshot-desktop/frontend/index.html`
  - Add visible `Importar` and `Exportar` controls in the preset manager.
  - Add hidden JSON file input.
  - Add compact preset-import conflict modal using existing modal classes.
  - Add `preset-transfer.js` script before `app.js`.
- Create: `apps/flatshot-desktop/frontend/preset-transfer.js`
  - Own frontend-only copy such as import status text, conflict modal HTML, and export file naming.
- Modify: `apps/flatshot-desktop/frontend/app.js`
  - Fetch backend export payload for download.
  - Open file picker, parse JSON, preview import, show conflict modal, execute copy or overwrite strategy.
  - Refresh presets from bridge response while preserving active preset when possible.
  - Keep mock export fallback for development mode only.
- Modify: `tests/test_preset_service.py`
  - Add service import preview/copy/overwrite/invalid tests.
- Modify: `tests/test_bridge_service.py`
  - Add bridge methods tests.
- Modify: `tests/test_bridge_http_server.py`
  - Add HTTP endpoint tests.
- Modify: `tests/test_frontend_settings_view.py`
  - Add import/export control and preset-transfer helper tests.

Do not touch core image processing, export runner behavior, output naming, output folders, source image handling, or image rendering settings.

---

### Task 1: PresetService Import/Export Contract

**Files:**
- Modify: `tests/test_preset_service.py`
- Modify: `src/flatshot/application/preset_service.py`

- [ ] **Step 1: Add failing service tests for preview, copy, overwrite, and invalid import metadata**

Append these tests near the existing import/export tests in `tests/test_preset_service.py`:

```python
def _preset_bundle(custom_presets: dict) -> dict:
    return {
        "flatshot_export": {"type": "presets", "version": 1},
        "presets": {
            "categories": {
                "custom": {
                    "name": "Personalizados",
                    "presets": custom_presets,
                    "locked": False,
                }
            },
            "uncategorized": {},
        },
    }


def test_preview_presets_import_detects_conflicts_without_writing(tmp_path):
    service = PresetService(tmp_path)
    existing = service.get_default_categorized_presets()
    existing.categories["custom"].presets["Local"] = {"angle": 90, "distance": 20}
    service.save_all_presets(existing)
    before = service.categorized_presets_path.read_text(encoding="utf-8")

    preview = service.preview_presets_import(
        _preset_bundle(
            {
                "Local": {"angle": 140, "distance": 12},
                "Remoto": {"angle": 45, "distance": 8},
            }
        )
    )

    assert preview == {
        "ok": True,
        "presetCount": 2,
        "conflicts": ["Local"],
        "recommendedStrategy": "copy",
        "wouldCopy": 1,
    }
    assert service.categorized_presets_path.read_text(encoding="utf-8") == before


def test_import_presets_copy_strategy_renames_conflicts_deterministically(tmp_path):
    service = PresetService(tmp_path)
    existing = service.get_default_categorized_presets()
    existing.categories["custom"].presets["Local"] = {"angle": 90, "distance": 20}
    existing.categories["custom"].presets["Local copia"] = {"angle": 91, "distance": 21}
    service.save_all_presets(existing)

    imported, summary = service.import_presets(
        _preset_bundle(
            {
                "Local": {"angle": 140, "distance": 12},
                "Remoto": {"angle": 45, "distance": 8},
            }
        ),
        strategy="copy",
    )

    flat = service.get_flat_presets_from_categorized(imported)
    assert flat["Local"]["angle"] == 90
    assert flat["Local copia"]["angle"] == 91
    assert flat["Local copia 2"]["angle"] == 140
    assert flat["Remoto"]["angle"] == 45
    assert summary == {
        "imported": 2,
        "copied": 1,
        "overwritten": 0,
        "conflicts": ["Local"],
    }


def test_import_presets_overwrite_strategy_replaces_conflicts(tmp_path):
    service = PresetService(tmp_path)
    existing = service.get_default_categorized_presets()
    existing.categories["custom"].presets["Local"] = {"angle": 90, "distance": 20}
    service.save_all_presets(existing)

    imported, summary = service.import_presets(
        _preset_bundle({"Local": {"angle": 140, "distance": 12}}),
        strategy="overwrite",
    )

    flat = service.get_flat_presets_from_categorized(imported)
    assert flat["Local"]["angle"] == 140
    assert flat["Local"]["distance"] == 12
    assert summary == {
        "imported": 1,
        "copied": 0,
        "overwritten": 1,
        "conflicts": ["Local"],
    }


def test_parse_imported_presets_rejects_non_preset_export(tmp_path):
    service = PresetService(tmp_path)

    with pytest.raises(ValueError, match="Archivo de ajustes no compatible"):
        service.preview_presets_import({"flatshot_export": {"type": "ui_preferences"}})
```

- [ ] **Step 2: Run the service tests to verify they fail**

Run:

```bash
pytest tests/test_preset_service.py -q
```

Expected: fail because `preview_presets_import` and `import_presets` are not defined.

- [ ] **Step 3: Add service import/export helpers**

In `src/flatshot/application/preset_service.py`, update imports and add class helpers inside `PresetService`.

Import update:

```python
from typing import Any, Optional
```

Add these methods after `load_flat_presets`:

```python
    def export_presets_payload(self) -> dict[str, Any]:
        presets = self.load_categorized_presets()
        return {
            "flatshot_export": {
                "type": "presets",
                "version": self.PRESETS_EXPORT_VERSION,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "preset_count": len(self.get_flat_presets_from_categorized(presets)),
            },
            "presets": presets.model_dump(),
        }

    def preview_presets_import(self, data: dict[str, Any]) -> dict[str, Any]:
        imported = self.parse_imported_presets(data)
        incoming_names = list(self.get_flat_presets_from_categorized(imported).keys())
        existing_names = set(self.load_flat_presets().keys())
        conflicts = [name for name in incoming_names if name in existing_names]
        return {
            "ok": True,
            "presetCount": len(incoming_names),
            "conflicts": conflicts,
            "recommendedStrategy": "copy",
            "wouldCopy": len(conflicts),
        }

    def import_presets(
        self,
        data: dict[str, Any],
        *,
        strategy: str = "copy",
    ) -> tuple[CategorizedPresets, dict[str, Any]]:
        if strategy not in {"copy", "overwrite"}:
            raise ValueError("Field 'strategy' must be 'copy' or 'overwrite'.")

        incoming = self.parse_imported_presets(data)
        base = self.load_categorized_presets()
        merged, summary = self.merge_imported_categorized_presets(
            base,
            incoming,
            strategy=strategy,
        )
        self.save_all_presets(merged)
        return merged, summary
```

Replace `export_presets_to_file` with this body:

```python
    def export_presets_to_file(self, file_path: str | Path) -> bool:
        try:
            with Path(file_path).open("w", encoding="utf-8") as handle:
                json.dump(self.export_presets_payload(), handle, indent=4, ensure_ascii=False)
            return True
        except Exception as exc:
            logging.error(f"Error exporting presets: {exc}")
            return False
```

Replace `import_presets_from_file` with this body:

```python
    def import_presets_from_file(self, file_path: str | Path, merge: bool = True) -> Optional[CategorizedPresets]:
        try:
            with Path(file_path).open("r", encoding="utf-8") as handle:
                data = json.load(handle)

            if merge:
                imported, _summary = self.import_presets(data, strategy="overwrite")
            else:
                imported = self.parse_imported_presets(data)
                self.save_all_presets(imported)
            return imported
        except Exception as exc:
            logging.error(f"Error importing presets: {exc}")
            return None
```

Replace the first part of `parse_imported_presets` with:

```python
    @classmethod
    def parse_imported_presets(cls, data: dict) -> CategorizedPresets:
        if not isinstance(data, dict):
            raise ValueError("El archivo de presets no contiene un objeto JSON válido.")

        candidate = data
        export_meta = data.get("flatshot_export")
        if isinstance(export_meta, dict):
            if export_meta.get("type") != "presets":
                raise ValueError("Archivo de ajustes no compatible.")
            candidate = data.get("presets", {})
```

Add these static/class helpers before `merge_categorized_presets`:

```python
    @classmethod
    def merge_imported_categorized_presets(
        cls,
        base: CategorizedPresets,
        incoming: CategorizedPresets,
        *,
        strategy: str,
    ) -> tuple[CategorizedPresets, dict[str, Any]]:
        base_data = base.model_dump()
        incoming_data = incoming.model_dump()
        existing_names = set(cls.get_flat_presets_from_categorized(CategorizedPresets(**base_data)).keys())
        used_names = set(existing_names)
        conflicts: list[str] = []
        copied = 0
        overwritten = 0
        imported_count = 0

        for category_id, category in incoming_data.get("categories", {}).items():
            target_category = base_data.setdefault("categories", {}).setdefault(
                category_id,
                {
                    "name": category.get("name") or category_id,
                    "presets": {},
                    "locked": category.get("locked", False),
                },
            )
            target_category.setdefault("presets", {})
            for name, settings in (category.get("presets") or {}).items():
                imported_count += 1
                target_name = name
                if name in existing_names:
                    conflicts.append(name)
                    if strategy == "copy":
                        target_name = cls.unique_preset_copy_name(name, used_names)
                        copied += 1
                    else:
                        cls.remove_preset_named(base_data, name)
                        overwritten += 1
                target_category["presets"][target_name] = settings
                used_names.add(target_name)

        base_data.setdefault("uncategorized", {})
        for name, settings in (incoming_data.get("uncategorized") or {}).items():
            imported_count += 1
            target_name = name
            if name in existing_names:
                conflicts.append(name)
                if strategy == "copy":
                    target_name = cls.unique_preset_copy_name(name, used_names)
                    copied += 1
                else:
                    cls.remove_preset_named(base_data, name)
                    overwritten += 1
            base_data["uncategorized"][target_name] = settings
            used_names.add(target_name)

        return cls.normalize_categorized_presets(
            CategorizedPresets(**base_data),
            missing_engine=SHADOW_ENGINE_COMPAT,
        ), {
            "imported": imported_count,
            "copied": copied,
            "overwritten": overwritten,
            "conflicts": conflicts,
        }

    @staticmethod
    def unique_preset_copy_name(name: str, used_names: set[str]) -> str:
        base_name = f"{name} copia"
        if base_name not in used_names:
            return base_name
        suffix = 2
        while f"{base_name} {suffix}" in used_names:
            suffix += 1
        return f"{base_name} {suffix}"

    @staticmethod
    def remove_preset_named(categorized_data: dict[str, Any], name: str) -> None:
        for category in (categorized_data.get("categories") or {}).values():
            (category.get("presets") or {}).pop(name, None)
        (categorized_data.get("uncategorized") or {}).pop(name, None)
```

- [ ] **Step 4: Run the service tests**

Run:

```bash
pytest tests/test_preset_service.py -q
```

Expected: all tests in `tests/test_preset_service.py` pass.

- [ ] **Step 5: Commit service contract**

Run:

```bash
git add src/flatshot/application/preset_service.py tests/test_preset_service.py
git commit -m "Add preset import conflict strategies"
```

---

### Task 2: Bridge Service And HTTP Endpoints

**Files:**
- Modify: `tests/test_bridge_service.py`
- Modify: `tests/test_bridge_http_server.py`
- Modify: `src/flatshot/bridge/service.py`
- Modify: `src/flatshot/bridge/http_server.py`

- [ ] **Step 1: Add failing bridge service tests**

Append these tests after existing preset save/delete tests in `tests/test_bridge_service.py`:

```python
def _preset_import_bundle(custom_presets: dict) -> dict:
    return {
        "flatshot_export": {"type": "presets", "version": 1},
        "presets": {
            "categories": {
                "custom": {
                    "name": "Personalizados",
                    "presets": custom_presets,
                    "locked": False,
                }
            },
            "uncategorized": {},
        },
    }


def test_bridge_export_presets_returns_portable_bundle(tmp_path):
    preset_service = PresetService(tmp_path)
    categorized = preset_service.get_default_categorized_presets()
    categorized.categories["custom"].presets["Local"] = {"angle": 90, "distance": 10}
    preset_service.save_all_presets(categorized)

    response = _service(tmp_path).export_presets()

    assert response["flatshot_export"]["type"] == "presets"
    assert response["flatshot_export"]["preset_count"] == 3
    assert response["presets"]["categories"]["custom"]["presets"]["Local"]["shadow_engine"] == "legacy"


def test_bridge_preview_preset_import_reports_conflicts(tmp_path):
    preset_service = PresetService(tmp_path)
    categorized = preset_service.get_default_categorized_presets()
    categorized.categories["custom"].presets["Local"] = {"angle": 90, "distance": 10}
    preset_service.save_all_presets(categorized)

    response = _service(tmp_path).preview_preset_import(
        {"data": _preset_import_bundle({"Local": {"angle": 140, "distance": 12}})}
    )

    assert response["ok"] is True
    assert response["presetCount"] == 1
    assert response["conflicts"] == ["Local"]
    assert response["recommendedStrategy"] == "copy"


def test_bridge_import_presets_copy_strategy_returns_refreshed_list(tmp_path):
    preset_service = PresetService(tmp_path)
    categorized = preset_service.get_default_categorized_presets()
    categorized.categories["custom"].presets["Local"] = {"angle": 90, "distance": 10}
    preset_service.save_all_presets(categorized)

    response = _service(tmp_path).import_presets(
        {
            "data": _preset_import_bundle({"Local": {"angle": 140, "distance": 12}}),
            "strategy": "copy",
        }
    )

    names = {item["name"] for item in response["items"]}
    assert response["ok"] is True
    assert response["imported"] == 1
    assert response["copied"] == 1
    assert response["overwritten"] == 0
    assert response["conflicts"] == ["Local"]
    assert {"Local", "Local copia"} <= names


def test_bridge_import_presets_rejects_invalid_payload(tmp_path):
    with pytest.raises(Exception) as exc:
        _service(tmp_path).import_presets({"data": {"flatshot_export": {"type": "ui_preferences"}}})

    assert "Archivo de ajustes no compatible" in str(exc.value)
```

If `pytest` is not already imported in `tests/test_bridge_service.py`, add:

```python
import pytest
```

- [ ] **Step 2: Add failing HTTP endpoint tests**

Append these tests after `test_bridge_http_presets_include_settings` in `tests/test_bridge_http_server.py`:

```python
def _http_preset_import_bundle(custom_presets: dict) -> dict:
    return {
        "flatshot_export": {"type": "presets", "version": 1},
        "presets": {
            "categories": {
                "custom": {
                    "name": "Personalizados",
                    "presets": custom_presets,
                    "locked": False,
                }
            },
            "uncategorized": {},
        },
    }


def test_bridge_http_export_presets(tmp_path):
    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "GET", "/presets/export")

    assert status == 200
    assert data["flatshot_export"]["type"] == "presets"
    assert data["presets"]["categories"]["ropa_clara"]["presets"]["Luz cenital"]["shadow_engine"] == "realistic_v2"


def test_bridge_http_preview_preset_import(tmp_path):
    bundle = _http_preset_import_bundle({"Luz cenital": {"angle": 140, "distance": 12}})

    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(port, "POST", "/presets/import/preview", {"data": bundle})

    assert status == 200
    assert data["ok"] is True
    assert data["conflicts"] == ["Luz cenital"]
    assert data["recommendedStrategy"] == "copy"


def test_bridge_http_import_presets_copy(tmp_path):
    bundle = _http_preset_import_bundle({"Luz cenital": {"angle": 140, "distance": 12}})

    with running_bridge(tmp_path / "config") as port:
        status, data = request_json(
            port,
            "POST",
            "/presets/import",
            {"data": bundle, "strategy": "copy"},
        )

    names = {item["name"] for item in data["items"]}
    assert status == 200
    assert data["ok"] is True
    assert data["copied"] == 1
    assert {"Luz cenital", "Luz cenital copia"} <= names
```

- [ ] **Step 3: Run bridge tests to verify they fail**

Run:

```bash
pytest tests/test_bridge_service.py tests/test_bridge_http_server.py -q
```

Expected: fail because bridge methods and HTTP routes are missing.

- [ ] **Step 4: Implement bridge service methods**

In `src/flatshot/bridge/service.py`, add these methods after `delete_preset`:

```python
    def export_presets(self) -> dict[str, Any]:
        service = self._writable_preset_service()
        return service.export_presets_payload()

    def preview_preset_import(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise InvalidRequestError("Expected a JSON object.")

        service = self._writable_preset_service()
        try:
            return service.preview_presets_import(_preset_import_data(payload))
        except ValueError as exc:
            raise InvalidRequestError(str(exc)) from exc

    def import_presets(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            raise InvalidRequestError("Expected a JSON object.")

        strategy = str(payload.get("strategy") or "copy")
        service = self._writable_preset_service()
        try:
            _imported, summary = service.import_presets(
                _preset_import_data(payload),
                strategy=strategy,
            )
        except ValueError as exc:
            raise InvalidRequestError(str(exc)) from exc

        response = self.list_presets()
        response["ok"] = True
        response.update(summary)
        return response
```

Add this helper near `_json_compatible`:

```python
def _preset_import_data(payload: Mapping[str, Any]) -> dict[str, Any]:
    data = payload.get("data", payload)
    if not isinstance(data, Mapping):
        raise InvalidRequestError("Field 'data' must be a JSON object.")
    return dict(data)
```

- [ ] **Step 5: Implement HTTP routes**

In `src/flatshot/bridge/http_server.py`, update `do_GET`:

```python
            elif path == "/presets/export":
                self._send_json(self.server.service.export_presets())
```

Place it directly after the existing `/presets` branch.

Update `do_POST`:

```python
            elif path == "/presets/import/preview":
                self._send_json(self.server.service.preview_preset_import(self._read_json_body()))
            elif path == "/presets/import":
                self._send_json(self.server.service.import_presets(self._read_json_body()))
```

Place these after `/presets/delete`.

Update the GET-only set in `do_POST`:

```python
                if path in {"/health", "/app-info", "/capabilities", "/presets", "/presets/export", "/ui/preferences"}:
                    raise MethodNotAllowedError("Use GET for this endpoint.")
```

Update `do_GET` method-not-allowed handling before `path.startswith("/exports/")`:

```python
            elif path in {"/presets/import/preview", "/presets/import"}:
                raise MethodNotAllowedError("Use POST for this endpoint.")
```

- [ ] **Step 6: Run bridge tests**

Run:

```bash
pytest tests/test_bridge_service.py tests/test_bridge_http_server.py -q
```

Expected: all tests pass.

- [ ] **Step 7: Commit bridge endpoints**

Run:

```bash
git add src/flatshot/bridge/service.py src/flatshot/bridge/http_server.py tests/test_bridge_service.py tests/test_bridge_http_server.py
git commit -m "Expose preset import export bridge endpoints"
```

---

### Task 3: Frontend Preset Transfer Helpers And Controls

**Files:**
- Create: `apps/flatshot-desktop/frontend/preset-transfer.js`
- Modify: `apps/flatshot-desktop/frontend/index.html`
- Modify: `tests/test_frontend_settings_view.py`

- [ ] **Step 1: Add failing frontend tests for controls and helper output**

Update `test_settings_actions_are_scoped_to_inspector_panel` in `tests/test_frontend_settings_view.py` so it also asserts:

```python
    assert 'data-action="import-presets"' in html
    assert 'data-action="export-presets"' in html
    assert 'id="preset-import-input"' in html
    assert 'id="preset-import-modal"' in html
    assert "preset-transfer.js" in html
```

Add this new test near `test_settings_view_renders_preset_and_state_contracts`:

```python
@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for frontend helper checks")
def test_preset_transfer_helpers_render_import_copy_contracts():
    helper_path = FRONTEND_DIR / "preset-transfer.js"
    script = f"""
const assert = require("node:assert/strict");
const helpers = require({json.dumps(str(helper_path))});

assert.equal(helpers.presetExportFileName(new Date("2026-06-25T12:00:00Z")), "flatshot-ajustes-20260625.json");
assert.equal(helpers.presetImportStatusText({{ imported: 5, copied: 2, overwritten: 0 }}), "Importados 5 ajustes · 2 como copia");
assert.equal(helpers.presetImportStatusText({{ imported: 1, copied: 0, overwritten: 1 }}), "Importado 1 ajuste · 1 sobrescrito");
assert.equal(helpers.presetImportStatusText({{ imported: 3, copied: 0, overwritten: 0 }}), "Importados 3 ajustes");

const html = helpers.presetImportConflictHtml({{ presetCount: 3, conflicts: ["Luz <cenital>", "Local"] }});
assert.equal(html.includes("3 ajustes en el archivo"), true);
assert.equal(html.includes("2 conflictos"), true);
assert.equal(html.includes("Luz &lt;cenital&gt;"), true);
assert.equal(html.includes("Importar como copia"), true);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
```

- [ ] **Step 2: Run frontend settings tests to verify they fail**

Run:

```bash
pytest tests/test_frontend_settings_view.py -q
```

Expected: fail because `preset-transfer.js` and import controls are missing.

- [ ] **Step 3: Add preset transfer helper module**

Create `apps/flatshot-desktop/frontend/preset-transfer.js`:

```javascript
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.FlatShotPresetTransfer = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const escapeHtml = globalThis.FlatShotFormatters?.escapeHtml || function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  };

  function plural(count, singular, pluralText) {
    return Number(count) === 1 ? singular : pluralText;
  }

  function presetExportFileName(date = new Date()) {
    const stamp = date.toISOString().slice(0, 10).replaceAll("-", "");
    return `flatshot-ajustes-${stamp}.json`;
  }

  function presetImportStatusText(summary = {}) {
    const imported = Number(summary.imported) || 0;
    const copied = Number(summary.copied) || 0;
    const overwritten = Number(summary.overwritten) || 0;
    const parts = [
      `${imported === 1 ? "Importado" : "Importados"} ${imported} ${plural(imported, "ajuste", "ajustes")}`,
    ];
    if (copied) {
      parts.push(`${copied} como copia`);
    }
    if (overwritten) {
      parts.push(`${overwritten} ${plural(overwritten, "sobrescrito", "sobrescritos")}`);
    }
    return parts.join(" · ");
  }

  function presetImportConflictHtml(preview = {}) {
    const presetCount = Number(preview.presetCount) || 0;
    const conflicts = Array.isArray(preview.conflicts) ? preview.conflicts : [];
    const conflictCount = conflicts.length;
    const names = conflicts.slice(0, 4).map((name) => `<strong>${escapeHtml(name)}</strong>`).join("");
    const overflow = conflictCount > 4 ? `<small>+${conflictCount - 4} más</small>` : "";
    return `
      <div class="export-confirm-summary">
        <div><span>Archivo</span><strong>${presetCount} ${plural(presetCount, "ajuste", "ajustes")} en el archivo</strong></div>
        <div><span>Coincidencias</span><strong>${conflictCount} ${plural(conflictCount, "conflicto", "conflictos")}</strong></div>
      </div>
      <section class="export-confirm-section">
        <h3>Importar como copia</h3>
        <div class="export-confirm-risks">
          <article class="export-confirm-risk warning">
            <span>!</span>
            <div>
              <strong>Ya existen ajustes con esos nombres</strong>
              <small>La opción recomendada crea nombres nuevos y conserva los actuales.</small>
            </div>
          </article>
        </div>
      </section>
      <section class="export-confirm-section">
        <h3>Ajustes con conflicto</h3>
        <div class="export-confirm-summary">${names}${overflow}</div>
      </section>
    `;
  }

  return {
    escapeHtml,
    presetExportFileName,
    presetImportConflictHtml,
    presetImportStatusText,
  };
});
```

- [ ] **Step 4: Add controls and modal markup**

In `apps/flatshot-desktop/frontend/index.html`, inside `.button-row.preset-actions`, after `Guardar como nuevo`, add:

```html
                  <button type="button" data-action="import-presets">Importar</button>
                  <button type="button" data-action="export-presets">Exportar</button>
```

After the closing `</details>` for the local-adjustment section and before the export section, add:

```html
          <input type="file" id="preset-import-input" accept="application/json,.json" hidden />
```

After the export confirm modal and before the app settings modal, add:

```html
      <div class="app-settings-backdrop export-confirm-backdrop is-hidden" id="preset-import-modal" role="dialog" aria-modal="true" aria-labelledby="preset-import-title" aria-hidden="true">
        <section class="app-settings-dialog export-confirm-dialog">
          <header class="app-settings-header">
            <div>
              <span class="eyebrow">Ajustes</span>
              <h2 id="preset-import-title">Importar ajustes</h2>
              <small id="preset-import-subtitle">Hay nombres repetidos.</small>
            </div>
            <button type="button" class="icon-button" data-action="cancel-preset-import" aria-label="Cerrar importación">×</button>
          </header>
          <div class="export-confirm-content" id="preset-import-body"></div>
          <footer class="app-settings-footer">
            <button type="button" data-action="cancel-preset-import">Cancelar</button>
            <button type="button" data-action="confirm-preset-import-overwrite">Sobrescribir existentes</button>
            <button type="button" class="primary" id="preset-import-copy-action" data-action="confirm-preset-import-copy">Importar como copia</button>
          </footer>
        </section>
      </div>
```

Add the script before `app.js`:

```html
    <script src="./preset-transfer.js?v=20260616-inspector-fit-height"></script>
```

- [ ] **Step 5: Run frontend settings tests**

Run:

```bash
pytest tests/test_frontend_settings_view.py -q
```

Expected: all tests in `tests/test_frontend_settings_view.py` pass.

- [ ] **Step 6: Run CSS contract checks because HTML/frontend changed**

Run:

```bash
python scripts/audit_css.py --check
pytest tests/test_frontend_css_contract.py -q
```

Expected: both commands pass. If the CSS audit fails, fix selector ownership in the existing owning CSS module instead of adding `!important`.

- [ ] **Step 7: Commit frontend controls and helper**

Run:

```bash
git add apps/flatshot-desktop/frontend/index.html apps/flatshot-desktop/frontend/preset-transfer.js tests/test_frontend_settings_view.py
git commit -m "Add preset import export UI controls"
```

---

### Task 4: Frontend Import/Export Flow Wiring

**Files:**
- Modify: `apps/flatshot-desktop/frontend/app.js`
- Modify: `tests/test_frontend_settings_view.py`

- [ ] **Step 1: Add failing source-level app wiring assertions**

Add this test to `tests/test_frontend_settings_view.py`:

```python
def test_preset_import_export_actions_are_wired_to_bridge():
    app_js = APP_PATH.read_text(encoding="utf-8")

    assert "function openPresetImportPicker()" in app_js
    assert "async function handlePresetImportFile(file)" in app_js
    assert 'bridgeRequest("/presets/export")' in app_js
    assert 'bridgeRequest("/presets/import/preview"' in app_js
    assert 'bridgeRequest("/presets/import"' in app_js
    assert 'data-action="confirm-preset-import-copy"' in (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
    assert 'data-action="confirm-preset-import-overwrite"' in (FRONTEND_DIR / "index.html").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run the focused frontend test to verify it fails**

Run:

```bash
pytest tests/test_frontend_settings_view.py::test_preset_import_export_actions_are_wired_to_bridge -q
```

Expected: fail because the app functions are not present yet.

- [ ] **Step 3: Add preset import state**

In `apps/flatshot-desktop/frontend/app.js`, extend the initial `state` object near existing preset state:

```javascript
  presetImportOpen: false,
  presetImportData: null,
  presetImportPreview: null,
```

In `restoreSessionSnapshot`, keep this transient state reset:

```javascript
    presetImportOpen: false,
    presetImportData: null,
    presetImportPreview: null,
```

- [ ] **Step 4: Replace backend export flow while keeping mock fallback**

Replace `exportPresetCollection()` with:

```javascript
async function exportPresetCollection() {
  state.statusText = "Exportando ajustes";
  render();
  try {
    const payload = state.bridgeMode === "bridge"
      ? await bridgeRequest("/presets/export", { timeoutMs: 8000 })
      : presetsExportPayload();
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = presetTransferHelpers.presetExportFileName();
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    const count = Number(payload.flatshot_export?.preset_count) || activePresetItems().length;
    state.statusText = `${count} ajustes exportados`;
  } catch (error) {
    state.statusText = `No se pudieron exportar los ajustes: ${bridgeErrorMessage(error)}`;
  }
  render();
}
```

Add this constant near other helper module constants:

```javascript
const presetTransferHelpers = window.FlatShotPresetTransfer;
```

If the app file does not group helper constants, place it next to `settingsViewHelpers`.

- [ ] **Step 5: Add import picker and JSON parsing flow**

Add these functions near `exportPresetCollection()`:

```javascript
function openPresetImportPicker() {
  const input = $("#preset-import-input");
  if (!input) {
    state.statusText = "Selector de importación no disponible";
    render();
    return;
  }
  input.value = "";
  input.click();
}

async function handlePresetImportFile(file) {
  if (!file) {
    return;
  }
  if (state.bridgeMode !== "bridge") {
    state.statusText = "Conexión local no disponible";
    render();
    return;
  }

  state.statusText = "Leyendo ajustes";
  render();

  let data;
  try {
    data = JSON.parse(await file.text());
  } catch (_error) {
    state.statusText = "Archivo JSON no válido";
    render();
    return;
  }

  try {
    const preview = await bridgeRequest("/presets/import/preview", {
      method: "POST",
      body: JSON.stringify({ data }),
      timeoutMs: 8000,
    });
    if (Array.isArray(preview.conflicts) && preview.conflicts.length) {
      openPresetImportConfirm(data, preview);
      return;
    }
    await executePresetImport(data, "copy");
  } catch (error) {
    state.statusText = `No se pudieron importar los ajustes: ${bridgeErrorMessage(error)}`;
    render();
  }
}
```

- [ ] **Step 6: Add conflict modal rendering and actions**

Add these functions near export confirm modal functions:

```javascript
function renderPresetImportConfirm() {
  const modal = $("#preset-import-modal");
  if (!modal) {
    return;
  }
  modal.classList.toggle("is-hidden", !state.presetImportOpen);
  modal.setAttribute("aria-hidden", state.presetImportOpen ? "false" : "true");
  if (!state.presetImportOpen) {
    return;
  }
  const body = $("#preset-import-body");
  if (body) {
    body.innerHTML = presetTransferHelpers.presetImportConflictHtml(state.presetImportPreview || {});
  }
  const subtitle = $("#preset-import-subtitle");
  if (subtitle) {
    const conflicts = state.presetImportPreview?.conflicts?.length || 0;
    subtitle.textContent = `${conflicts} nombre${conflicts === 1 ? "" : "s"} repetido${conflicts === 1 ? "" : "s"}`;
  }
}

function openPresetImportConfirm(data, preview) {
  rememberModalFocusReturn();
  state.exportConfirmOpen = false;
  state.batchDetailOpen = false;
  state.appSettingsOpen = false;
  state.presetImportOpen = true;
  state.presetImportData = data;
  state.presetImportPreview = preview;
  state.statusText = "Revisar importación";
  render();
  queueModalFocus("#preset-import-modal", "#preset-import-copy-action");
}

function closePresetImportConfirm({ renderAfter = true } = {}) {
  releaseModalFocusBeforeHide();
  state.presetImportOpen = false;
  state.presetImportData = null;
  state.presetImportPreview = null;
  if (renderAfter) {
    render();
  }
}

async function confirmPresetImport(strategy) {
  const data = state.presetImportData;
  if (!data) {
    closePresetImportConfirm();
    return;
  }
  closePresetImportConfirm({ renderAfter: false });
  await executePresetImport(data, strategy);
}

async function executePresetImport(data, strategy) {
  state.statusText = strategy === "overwrite" ? "Sobrescribiendo ajustes" : "Importando ajustes";
  render();
  try {
    const response = await bridgeRequest("/presets/import", {
      method: "POST",
      body: JSON.stringify({ data, strategy }),
      timeoutMs: 8000,
    });
    const previousPreset = state.activePreset;
    applyBridgePresets(response);
    if (previousPreset && activePresetItems().some((preset) => preset.name === previousPreset)) {
      state.activePreset = previousPreset;
      applyPresetSettings(previousPreset, { refresh: false, statusText: state.statusText });
    }
    state.presetDirty = false;
    state.statusText = presetTransferHelpers.presetImportStatusText(response);
  } catch (error) {
    state.statusText = `No se pudieron importar los ajustes: ${bridgeErrorMessage(error)}`;
  }
  render();
}
```

Update the main `render()` function so it calls:

```javascript
  renderPresetImportConfirm();
```

Place it next to `renderExportConfirm()`.

Update `currentOpenModal()`:

```javascript
  if (state.presetImportOpen) {
    return $("#preset-import-modal");
  }
```

Place it before `exportConfirmOpen`.

Update backdrop click handling:

```javascript
  if (event.target.id === "preset-import-modal") {
    closePresetImportConfirm();
    return;
  }
```

Update Escape handling:

```javascript
    if (state.presetImportOpen) {
      closePresetImportConfirm();
      event.preventDefault();
      return;
    }
```

- [ ] **Step 7: Wire actions and file input change**

In `handleAction`, add:

```javascript
  } else if (action === "import-presets") {
    openPresetImportPicker();
  } else if (action === "cancel-preset-import") {
    closePresetImportConfirm();
  } else if (action === "confirm-preset-import-copy") {
    void confirmPresetImport("copy");
  } else if (action === "confirm-preset-import-overwrite") {
    void confirmPresetImport("overwrite");
```

Place `import-presets` next to `export-presets`.

Change the existing export action to call the async function:

```javascript
  } else if (action === "export-presets") {
    void exportPresetCollection();
```

In the document `change` listener, add before the output profile form branch:

```javascript
  if (event.target?.id === "preset-import-input") {
    const file = event.target.files?.[0] || null;
    void handlePresetImportFile(file);
    return;
  }
```

In `renderAccessibilityHints`, add:

```javascript
  setControlHint($("[data-action='import-presets']"), "Importar ajustes desde un archivo JSON");
  setControlHint($("[data-action='export-presets']"), "Exportar ajustes a un archivo JSON");
```

- [ ] **Step 8: Run focused frontend tests**

Run:

```bash
pytest tests/test_frontend_settings_view.py -q
```

Expected: all settings view tests pass.

- [ ] **Step 9: Run CSS contract checks because frontend changed**

Run:

```bash
python scripts/audit_css.py --check
pytest tests/test_frontend_css_contract.py -q
```

Expected: both pass.

- [ ] **Step 10: Commit frontend flow**

Run:

```bash
git add apps/flatshot-desktop/frontend/app.js tests/test_frontend_settings_view.py
git commit -m "Wire preset import export frontend flow"
```

---

### Task 5: Full Verification And Manual Checks

**Files:**
- No planned source edits.

- [ ] **Step 1: Run focused backend and frontend tests**

Run:

```bash
pytest tests/test_preset_service.py tests/test_bridge_service.py tests/test_bridge_http_server.py tests/test_frontend_settings_view.py -q
```

Expected: all pass.

- [ ] **Step 2: Run required CSS/frontend checks**

Run:

```bash
python scripts/audit_css.py --check
pytest tests/test_frontend_css_contract.py -q
```

Expected: both pass.

- [ ] **Step 3: Run the full test suite**

Run:

```bash
pytest
```

Expected: all tests pass.

- [ ] **Step 4: Launch the desktop app for manual verification**

Run:

```bash
python apps/flatshot-desktop/run_dev.py
```

Expected: the dev server starts and prints the local URL.

- [ ] **Step 5: Manual check export/import workflow**

In the launched app:

1. Open `Avanzado`.
2. Open `Gestionar ajustes`.
3. Click `Exportar`.
4. Confirm a `flatshot-ajustes-YYYYMMDD.json` file downloads.
5. Click `Importar` and choose that exported JSON.
6. If the file conflicts with existing presets, choose `Importar como copia`.
7. Confirm copied names appear in the preset list without replacing the originals.
8. Import the same file again and choose `Sobrescribir existentes`.
9. Confirm the preset list refreshes and the app remains usable.
10. Try an invalid `.json` file and confirm the status says `Archivo JSON no válido` or `No se pudieron importar los ajustes`.

- [ ] **Step 6: Manual check processing invariant**

Using any valid PNG folder:

1. Load a folder with PNGs.
2. Select a preset that existed before this feature.
3. Generate a preview.
4. Start a small export.
5. Confirm output files are created in the configured destination with the existing naming behavior.

Expected: exported image appearance and file-output behavior are unchanged unless an imported preset is explicitly selected.

- [ ] **Step 7: Final status check**

Run:

```bash
git status --short
```

Expected: clean working tree after commits, or only intentional uncommitted manual artifacts outside git.

If temporary downloads, logs, caches, or generated exports appear, remove only those generated artifacts after confirming they are not source images or user config.
