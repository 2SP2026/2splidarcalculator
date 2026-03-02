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

## Next Steps (Session 4)

1. **Calculator Core Logic (Phase 3c):**
   - Port point-density (NPD) formula from the Excel reference into `src/core/`.
   - Port GSD formula.
   - Port FOV / AGL estimation.
2. **Wire Calculators into GUI:**
   - Create a new "Calculators" sidebar panel.
   - Build input forms that reference sensors from the library.
   - Display computed results with real-time updates.
3. **Testing:**
   - Unit tests for calculator formulas against known Excel outputs.
   - Integration tests for sensor manager CRUD operations.
