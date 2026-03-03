# 2SP LiDAR Calculator App — Project Context & Session Log

## Project Goal
Migrate the existing Excel-based "Leo's LiDAR Calculators" into a standalone, cross-platform Desktop Application with a modern GUI. The application will allow users to rapidly estimate Point Density, GSD, Coverage Area, and required overlap settings based on hardware specs and flight parameters.

## Key Architectural Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| GUI Framework | PySide6 (Qt) | Mature, cross-platform, native look & feel, strong table/widget support |
| Sensor Storage | Local `.json` files | Zero-setup, nests naturally, no JOINs needed, LLM-friendly for AI import |
| Database Shape | 4-module modular (`lidar`, `camera`, `pos`, `mapping_systems`) | Mirrors real-world mix-and-match hardware; enforces DRY |
| Logging | loguru | Minimal config, structured output, great for debugging GUI apps |
| UI Theme | Warm light theme | Amber/copper accents, dark sidebar, easy on the eyes |

> See `docs/SENSOR_LIB_ARCHITECTURE.md` for the full design rationale on modes, lens configs, and generic POS entries.

## Current Status

### Session 1 — Planning & Scaffolding ✅
- Agreed on Python 3.12+, PySide6 GUI, and lightweight local JSON database for sensor storage.
- Virtual environment active, dependencies installed, 2SP metadata files (`program.json`, `version.py`) created, GitHub repository synced.
- Sensor database architecture designed and documented (4-module modular approach).

### Session 2 — Sensor Library & GUI ✅
- **Sensor JSON Library:** Created `src/data/sensors.json` with specs extracted from 4 datasheets using `pdfplumber`. Contains 4 LiDAR, 3 camera, 3 POS, and 2 mapping system entries with full configuration arrays.
- **Data Access Layer:** Created `src/data/sensor_manager.py` with load/save, query by category/ID, mapping system resolution, and validation (0 warnings).
- **PySide6 GUI:** Built and tested — sidebar navigation, category tabs (LiDAR/Camera/POS/Systems), search filter, sensor list, and read-only detail panel with specs tables and configuration grids.
- **Document Reorganization:** Consolidated `lib_sensors/` + `references/` into `references/{datasheets, specifications, calculators}`. Created `docs/TECH_STACK.md` and `requirements.txt`.

## Relevant Documentation

| Document | Purpose |
| --- | --- |
| `docs/TECH_STACK.md` | Technology choices and dependency versions |
| `docs/SENSOR_LIB_ARCHITECTURE.md` | Design rationale for the sensor database (modes, inter-spec constraints, generic POS) |
| `docs/JSON_SENSOR_SCHEMA.md` | Agreed-upon JSON schema layout for the application backend |
| `references/datasheets/` | Manufacturer datasheets for supported sensors (RIEGL, Hesai, DJI, RESEPI) |
| `references/specifications/` | Industry standards — ASPRS LAS 1.4 format spec, ASPRS Positional Accuracy Standards (2024 Ed.2), and ASPRS LiDAR Density Guidelines (2025 Ed.1). The latter two provide formulas for estimating horizontal/vertical accuracy from INS/POS specs and required point density thresholds. |
| `references/calculators/` | Original Excel calculator being ported to this application |

## Next Steps (Session 3)

### Session 3 — Sensor Library Editing ✅
- **SensorManager CRUD:** Refactored `SensorManager` to inherit `QObject`, added `data_changed` signal. Implemented `add_module`, `update_module`, `delete_module` with auto-save and signal emission. Added `generate_id` (slugified, collision-safe) and `get_referencing_systems` (delete safety check).
- **SensorEditDialog:** New form-based dialog with a `FIELD_REGISTRY` for dynamic field generation per category. Supports `QLineEdit`, `QSpinBox`, `QDoubleSpinBox`, `QCheckBox`, `QComboBox`, and a generic `dropdown:` type for fixed-choice fields. Includes nested array editing (configurations, lens configs, photo sizes) via `QTableWidget` with add/remove row controls.
- **Mapping System References:** Module reference fields (`lidar_module_id`, `camera_module_id`, `pos_module_id`) render as dropdowns populated from the corresponding category.
- **Duplicate Feature:** 📋 Duplicate button clones an existing sensor's data into a new add-mode dialog. Duplicate name validation prevents saving entries with the same Model or System Name within a category.
- **Beam Divergence Specs:** Added `laser_beam_shape` (circular/ellipsoidal dropdown), `laser_beam_divergence_method` (FWHM / 1/e² dropdown), and `laser_beam_divergence_cross_mrad` (conditionally visible for ellipsoidal beams only).
- **UI Polish:** Action toolbar (Add, Duplicate, Edit, Delete) with enable/disable logic. Rebalanced detail panel and edit dialog layouts — specs table capped with scroll, configs table gets more vertical space. Input widths doubled, labels left-aligned.
- **Auto-Refresh:** `data_changed` signal connected to sensor list, detail panel, and status bar — all update automatically after any mutation.
- **Validation:** Required field checks, duplicate name prevention, and mapping system reference safety on delete.

### Session 4 — Calculator Core Logic ✅
- **NPD Calculator:** `src/core/npd_calculator.py` — Nominal Point Density estimation. Sensor-agnostic, forward-only model. Inputs: PRR, ground speed, AGL, sensor FOV (sFOV), effective FOV (eFOV). Applies proportional PRR scaling (`eFOV/sFOV`), then `NPD = effective_PRR / (v × W)`. 11 unit tests.
- **GSD Calculator:** `src/core/gsd_calculator.py` — Ground Sample Distance estimation. Pinhole model: `GSD = (pixel_pitch × AGL) / focal_length`. 7 unit tests.
- **Horizontal Error Calculator:** `src/core/horizontal_error_calculator.py` — ASPRS RMSE_H model for LiDAR point cloud horizontal accuracy based on GNSS and IMU specs. Validated against ASPRS Table B.8 and 3 real mapping systems. IMU inputs in degrees, converted internally. 12 unit tests.
- **All modules** are self-contained (stdlib only, no Qt/DB dependencies) and importable into other programs. Total: **30 passing tests** across `tests/`.

## Next Steps (Session 5)

### Session 5 — Calculator GUI & Export ✅
- **Calculator Panel:** New `src/ui/calculator_panel.py` — three tabbed calculators (NPD, GSD, RMSE_H) integrated into the main window via `QStackedWidget` with sidebar navigation toggle.
- **Sensor Picker:** Each tab has a `QComboBox` for selecting sensors from the library (LiDAR, Camera, POS respectively), plus a **"— Manual Entry —"** option for freeform input. Selecting a sensor auto-populates spec fields (PRR, FOV, focal length, GNSS error, etc.). Fields remain editable for what-if analysis.
- **Real-Time Results:** Calculations update instantly on every input change — no "Calculate" button needed. Results displayed in styled cards with large numeric values and units.
- **Assumptions & References:** Each tab shows an expandable info section with the math model formula, assumptions list, and authoritative references (e.g., ASPRS Edition 2, 2024 for RMSE_H).
- **Export:** `src/core/calculator_export.py` — two export formats:
  - **TXT:** Structured `[SECTION]` + key-value pairs for easy script parsing.
  - **HTML:** Standalone presentation-grade report with DM Sans + JetBrains Mono, light theme with corporate blue (`#1B5E94`) accents, result hero cards, and `@media print` styles.
  - Auto-generated filename: `{calculator}-{sensor}-{YYYY-MM-DD}`. Native `QFileDialog` with cross-platform Desktop default via `QStandardPaths`.
- **Styles:** Added QSS rules for calculator tabs, result cards, info sections, error labels, and active sidebar button states.
- **Tests:** All 30 existing unit tests pass. Import checks clean.

## Next Steps (Session 6)

### Session 6 — Library Export/Import & Windows Executable ✅
- **Library Export/Import:** `src/data/library_io.py` — pure-Python (no Qt) module for sharing sensor libraries via `.2splib` files (JSON with metadata header).
  - **Export Full Library:** Serializes all 4 categories with a `meta` header (format version, timestamp, app name).
  - **Export Selected:** Exports only the selected sensor. If it's a **mapping system**, auto-includes its referenced LiDAR, camera, and POS sub-modules (transitive dependency resolution).
  - **Smart-Merge Import:** Analyzes incoming file against current library — detects new entries, identical duplicates (auto-skipped), and conflicts (same ID, different data).
  - **Conflict Resolution:** Per-conflict UI with three options: *Skip*, *Replace*, or *Import as Copy* (generates new unique ID). Bulk actions (Skip All / Replace All) for multiple conflicts.
  - **Import Preview Dialog:** `src/ui/import_dialog.py` — shows categorized summary (new / identical / conflicts) with diff highlights before committing. Post-import summary dialog with counts.
  - **UI Integration:** `⬆ Export` (dropdown: Full Library / Selected Sensor) and `⬇ Import` buttons in the sensor browser toolbar. Native file dialogs with `.2splib` filter, also accepts raw `.json`.
  - **File Format:** `.2splib` — JSON with custom extension. Human-readable, self-contained (no broken references), forward-compatible via `meta.version`.
  - **Tests:** 22 new unit tests covering export (full + selected + dependency resolution), file I/O (round-trip, validation, malformed files), import plan analysis (new/identical/conflict), import execution (skip/replace/copy), and filename generation. **Total: 52 passing tests.**
- **Windows Executable:** PyInstaller one-folder build for distribution without Python installed.
  - **Spec file:** `2sp_lidar_calculator.spec` — excludes unused packages (numpy, pandas, matplotlib, tkinter), bundles `sensors.json` as seed data.
  - **Frozen-mode paths:** `sensor_manager.py` detects PyInstaller frozen mode (`sys.frozen`). On first launch, copies bundled `sensors.json` to a writable location next to the exe.
  - **Logging fix:** In windowed mode (`console=False`), `sys.stderr` is `None`. Logger now falls back to a `2sp_calculator.log` file next to the exe with 1 MB rotation.
  - **Output:** `dist/2SP_LiDAR_Calculator/` (~120 MB, 212 files). Compresses to ~48 MB zip for distribution.

## Next Steps (Session 7)

1. **Additional Calculators:**
   - Port FOV / AGL estimation calculator.
2. **Testing:**
   - Integration tests for sensor manager CRUD operations.
   - GUI smoke tests with `pytest-qt`.
3. **Polish:**
   - Active sidebar button visual indicator.
   - Keyboard shortcuts for navigation.
   - App icon for the Windows executable.
