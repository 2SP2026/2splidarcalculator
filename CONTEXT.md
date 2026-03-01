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

1. **Sensor Library Editing (Phase 3d):**
   - Enable add / edit / delete operations on sensor profiles via the GUI.
   - Add form-based dialogs for creating new LiDAR, camera, POS, and mapping system entries.
   - Persist changes back to `sensors.json` via `sensor_manager.save()`.
2. **Calculator Core Logic (Phase 3c):**
   - Port point-density (NPD) formula from the Excel reference into `src/core/`.
   - Port GSD formula.
   - Port FOV / AGL estimation.
   - Wire calculators into the GUI (new "Calculators" sidebar panel).
