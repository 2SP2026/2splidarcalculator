# Tech Stack

## Language & Runtime
| Component | Choice | Notes |
|---|---|---|
| **Language** | Python ≥ 3.12 | Type-hint-heavy codebase; uses modern syntax (match/case, etc.) |
| **Virtual Env** | `venv` | Standard library; `.venv/` is gitignored |

## Core Dependencies
| Package | Purpose |
|---|---|
| **PySide6** (≥ 6.6) | Cross-platform GUI framework (Qt for Python) |
| **pandas** (≥ 2.0) | Tabular data manipulation for calculator results and sensor tables |
| **loguru** (≥ 0.7) | Structured logging with minimal boilerplate |

## Data Storage
| Component | Choice | Rationale |
|---|---|---|
| **Sensor Library** | Local `.json` files | Zero-setup, natively supports deeply nested structures (modes, lens configs), easy to share/back up, LLM-friendly for AI-assisted data import. See `docs/SENSOR_LIB_ARCHITECTURE.md` for full rationale. |

## Branding (2SP Professional Tools)
| Token | Value |
|---|---|
| Primary Color | `#FFE500` (Yellow) |
| Background Color | `#000000` (Black) |
| Visual Identity | Yellow on Black |

## Build & Distribution
| Component | Status |
|---|---|
| **Packaging** | TBD — likely PyInstaller or Nuitka for single-binary distribution |
| **Installer** | TBD — platform-specific (`.dmg` / `.msi` / AppImage) |
