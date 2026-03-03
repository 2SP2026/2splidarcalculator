"""
Sensor library export/import logic.

Handles serialization to/from .2splib files (JSON with metadata header),
selective export with dependency resolution, and smart-merge import with
conflict detection.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger

from src.data.sensor_manager import CATEGORIES, SensorManager

# .2splib file format version — bump when schema changes
FORMAT_VERSION = 1

# Conflict resolution actions returned by the UI
CONFLICT_SKIP = "skip"
CONFLICT_REPLACE = "replace"
CONFLICT_COPY = "copy"
CONFLICT_SKIP_ALL = "skip_all"
CONFLICT_REPLACE_ALL = "replace_all"


# ── Export ──────────────────────────────────────────────────────────────


def export_full_library(manager: SensorManager) -> dict:
    """
    Export the entire sensor library as a serializable dict.

    Returns a dict with a 'meta' header and all four category arrays.
    """
    payload = _build_meta()
    for cat in CATEGORIES:
        payload[cat] = list(manager.get_modules(cat))  # shallow copy

    total = sum(len(payload[cat]) for cat in CATEGORIES)
    logger.info(f"Exported full library: {total} entries")
    return payload


def export_selected(
    manager: SensorManager,
    category: str,
    module_ids: list[str],
) -> dict:
    """
    Export specific modules plus their transitive dependencies.

    If a mapping system is selected, its referenced LiDAR, camera, and POS
    modules are automatically included.  If a standalone module is selected
    and it's referenced by a mapping system, only the module itself is
    exported (not the system).

    Returns a dict with a 'meta' header and only populated categories.
    """
    payload = _build_meta()
    for cat in CATEGORIES:
        payload[cat] = []

    # Track which (category, id) pairs to include
    to_export: set[tuple[str, str]] = set()

    for mid in module_ids:
        to_export.add((category, mid))

        # If it's a mapping system, pull in referenced sub-modules
        if category == "mapping_systems":
            system = manager.get_module_by_id("mapping_systems", mid)
            if system:
                for ref_key, ref_cat in [
                    ("lidar_module_id", "lidar_modules"),
                    ("camera_module_id", "camera_modules"),
                    ("pos_module_id", "pos_modules"),
                ]:
                    ref_id = system.get(ref_key, "")
                    if ref_id and manager.get_module_by_id(ref_cat, ref_id):
                        to_export.add((ref_cat, ref_id))

    # Build payload
    for cat, mid in to_export:
        module = manager.get_module_by_id(cat, mid)
        if module:
            payload[cat].append(module)

    total = sum(len(payload[cat]) for cat in CATEGORIES)
    logger.info(f"Exported {total} entries (selected + dependencies)")
    return payload


def save_to_file(payload: dict, filepath: Path) -> None:
    """Write an export payload to a .2splib JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved library file: {filepath}")


# ── Import ──────────────────────────────────────────────────────────────


def load_from_file(filepath: Path) -> dict:
    """
    Read a .2splib file and return the parsed payload dict.

    Raises ValueError if the file is malformed or missing expected keys.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Basic validation
    if not isinstance(data, dict):
        raise ValueError("Invalid library file: root is not a JSON object")

    # Allow raw sensors.json (no meta) or proper .2splib (with meta)
    has_categories = any(cat in data for cat in CATEGORIES)
    if not has_categories:
        raise ValueError(
            "Invalid library file: no recognized sensor categories found"
        )

    return data


class ImportPlan:
    """
    Analyzes an import payload against the current library and produces
    a plan of what to add, skip, or flag as a conflict.
    """

    def __init__(self, manager: SensorManager, payload: dict):
        self.manager = manager
        self.payload = payload

        # Results after analysis
        self.to_add: list[tuple[str, dict]] = []        # (category, module_data)
        self.identical: list[tuple[str, str]] = []       # (category, id) — skipped
        self.conflicts: list[tuple[str, dict, dict]] = []  # (category, incoming, existing)

        self._analyze()

    def _analyze(self):
        """Compare incoming modules against the current library."""
        for cat in CATEGORIES:
            incoming_modules = self.payload.get(cat, [])
            for incoming in incoming_modules:
                mid = incoming.get("id", "")
                if not mid:
                    # Module without an ID — treat as new
                    self.to_add.append((cat, incoming))
                    continue

                existing = self.manager.get_module_by_id(cat, mid)
                if existing is None:
                    # New module — add directly
                    self.to_add.append((cat, incoming))
                elif self._modules_equal(existing, incoming):
                    # Identical — skip silently
                    self.identical.append((cat, mid))
                else:
                    # Same ID but different data — conflict
                    self.conflicts.append((cat, incoming, existing))

    @staticmethod
    def _modules_equal(a: dict, b: dict) -> bool:
        """Deep-compare two module dicts, ignoring key order."""
        return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    @property
    def summary(self) -> str:
        """Human-readable summary of what will happen."""
        parts = []
        if self.to_add:
            parts.append(f"{len(self.to_add)} new")
        if self.identical:
            parts.append(f"{len(self.identical)} identical (skipped)")
        if self.conflicts:
            parts.append(f"{len(self.conflicts)} conflict(s)")
        return ", ".join(parts) if parts else "Nothing to import"


def execute_import(
    manager: SensorManager,
    plan: ImportPlan,
    conflict_resolutions: Optional[dict[str, str]] = None,
) -> dict:
    """
    Execute the import plan, applying conflict resolutions.

    Args:
        manager: The SensorManager to import into.
        plan: The analyzed ImportPlan.
        conflict_resolutions: A dict mapping conflict module IDs to one of:
            'skip', 'replace', 'copy'.  If None, all conflicts are skipped.

    Returns:
        A summary dict with counts: added, replaced, copied, skipped.
    """
    resolutions = conflict_resolutions or {}
    counts = {"added": 0, "replaced": 0, "copied": 0, "skipped": len(plan.identical)}

    # 1. Add new modules
    for cat, module_data in plan.to_add:
        manager.get_modules(cat).append(module_data)
        counts["added"] += 1
        logger.debug(f"Import: added '{module_data.get('id', '?')}' to {cat}")

    # 2. Handle conflicts
    for cat, incoming, existing in plan.conflicts:
        mid = incoming.get("id", "")
        action = resolutions.get(mid, CONFLICT_SKIP)

        if action == CONFLICT_SKIP or action == CONFLICT_SKIP_ALL:
            counts["skipped"] += 1
            logger.debug(f"Import: skipped conflict '{mid}'")

        elif action == CONFLICT_REPLACE or action == CONFLICT_REPLACE_ALL:
            # Replace existing in-place
            modules = manager.get_modules(cat)
            for i, m in enumerate(modules):
                if m.get("id") == mid:
                    modules[i] = incoming
                    break
            counts["replaced"] += 1
            logger.debug(f"Import: replaced '{mid}' in {cat}")

        elif action == CONFLICT_COPY:
            # Generate a new unique ID and add as copy
            manufacturer = incoming.get("manufacturer", "unknown")
            model = incoming.get("model", incoming.get("system_name", "unknown"))
            new_id = manager.generate_id(manufacturer, model)
            copy_data = dict(incoming)
            copy_data["id"] = new_id
            manager.get_modules(cat).append(copy_data)
            counts["copied"] += 1
            logger.debug(f"Import: copied '{mid}' as '{new_id}' in {cat}")

    # Save once after all mutations
    manager.save()
    manager.data_changed.emit()

    total = counts["added"] + counts["replaced"] + counts["copied"]
    logger.info(
        f"Import complete: {total} imported "
        f"({counts['added']} new, {counts['replaced']} replaced, "
        f"{counts['copied']} copies), {counts['skipped']} skipped"
    )
    return counts


# ── Helpers ─────────────────────────────────────────────────────────────


def _build_meta() -> dict:
    """Build the metadata header for an export file."""
    return {
        "meta": {
            "format": "2splib",
            "version": FORMAT_VERSION,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "app": "2SP LiDAR Calculator",
        }
    }


def suggest_filename(mode: str = "full", sensor_name: str = "") -> str:
    """
    Generate a suggested filename for the export.

    Args:
        mode: 'full' or 'selected'
        sensor_name: Optional sensor name for selected exports.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    if mode == "selected" and sensor_name:
        # Slugify the sensor name
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", sensor_name.lower()).strip("-")
        return f"2sp-{slug}-{date_str}.2splib"
    return f"2sp-sensor-library-{date_str}.2splib"
