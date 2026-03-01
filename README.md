# 2SP LiDAR Calculator App

Cross-platform Desktop Application for LiDAR and Photogrammetry Mission Planning calculations.

* **Version:** 0.1.0
* **Author:** Leo L. (twosigmaplus@gmail.com)
* **Suite:** 2SP Professional Tools

## Overview
This application provides quick estimation tools for determining expected point density, GSD, coverage area, and required overlapping flight lines for common drone-based LiDAR payloads.

## Project Structure
```
├── CONTEXT.md                # Project context & session log
├── docs/                     # Project documentation
│   ├── TECH_STACK.md         #   Technology choices & dependencies
│   ├── SENSOR_LIB_ARCHITECTURE.md  #   Sensor database design rationale
│   └── JSON_SENSOR_SCHEMA.md #   JSON schema for sensor data
├── references/               # Reference materials
│   ├── datasheets/           #   Manufacturer sensor datasheets
│   ├── specifications/       #   Industry standards (LAS 1.4, etc.)
│   └── calculators/          #   Original Excel calculator
├── src/                      # Application source code
│   ├── core/                 #   Calculator logic & formulas
│   ├── data/                 #   Sensor JSON data files
│   └── ui/                   #   PySide6 GUI widgets
└── tests/                    # Unit & integration tests
```

## Development Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
