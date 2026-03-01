# Sensor Library Architecture & Design Decisions

This document details the architectural decisions made regarding the application's internal database for storing sensor hardware specifications.

## 1. Modular Database Design vs. Monolithic
Instead of treating a "drone payload" as a single monolithic block of data, the database is split into four distinct, loosely coupled tables:
*   `lidar_modules`
*   `camera_modules`
*   `pos_modules`
*   `mapping_systems`

**Rationale:** Modern mapping systems (like a RESEPI Hesai XT32 or a custom M300 build) mix and match parts from different manufacturers. A monolithic design would force us to redefine the specs of a Sony a5100 every time it is paired with a different laser. The modular approach enforces the DRY (Don't Repeat Yourself) principle, allowing the same camera or INS to be referenced by multiple payloads.

## 2. Dealing with Inter-Spec Constraints (The "Modes" Solution)
High-end LiDAR sensors (like RIEGL) often have interrelated limitations. For instance, as you increase the Pulse Repetition Frequency (PRF), the maximum effective range decreases due to energy limitations.

**Rationale for using `configurations` arrays:**
Instead of writing complex Python logic to dynamically calculate the physics of laser signal degradation, we store manufacturer-defined "Measurement Programs" or "Configurations" as nested arrays within the sensor object. 
*   When a user selects the "300 kHz" mode in the UI, the application simply looks up that mode's predefined `max_range` and applies it as a hard constraint for the flight planning math.

## 3. Separating Camera Bodies and Interchangeable Lenses
A single camera sensor (e.g., Sony APS-C 24MP) might be flown with a 16mm lens for wider coverage, or a 24mm/35mm lens for higher GSD.

**Rationale for nested `lens_configurations`:**
By placing lens choices inside the Camera module object, the Ground Sample Distance (GSD) calculator knows exactly which focal length to use based on the user's secondary dropdown selection in the UI. 

## 4. Opaque Manufacturer Specs (Generic POS Modules)
Many commercial systems (like the DJI Zenmuse L-series) use proprietary, white-labeled INS hardware, meaning the user only knows the required performance specs (e.g., "0.03 deg Pitch/Roll accuracy") but not the actual hardware model name.

**Rationale for Generic Entries:**
The `pos_modules` table is designed to accept either precise hardware (e.g., Applanix APX-15) OR generic "Class" profiles (e.g., "L3 Integrated INS"). This allows the flight planning calculations (like trajectory error estimation) to function perfectly via the numbers provided in the datasheet, without forcing the user to identify hidden hardware components.

## 5. Technology Choice: Plain JSON Files
**Rationale:** We chose to use plain `.json` files stored locally over a full SQLite database. It is incredibly lightweight, requires zero setup, natively supports our highly nested data structures without complex JOIN operations, and can be easily backed up or shared between colleagues. AI-assisted importing via LLM APIs is also natively compatible with spitting out structured JSON.
