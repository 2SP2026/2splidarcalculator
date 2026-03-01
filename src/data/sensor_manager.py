"""
Sensor database manager for loading, querying, and saving sensor profiles.

Reads and writes to sensors.json — the local JSON sensor library.
"""

import json
from pathlib import Path
from typing import Optional

from loguru import logger


# Default path to the sensor database, relative to this file
_DEFAULT_DB_PATH = Path(__file__).parent / "sensors.json"

# Valid top-level categories in the database
CATEGORIES = ("lidar_modules", "camera_modules", "pos_modules", "mapping_systems")

# Human-readable labels for each category
CATEGORY_LABELS = {
    "lidar_modules": "LiDAR Sensors",
    "camera_modules": "Cameras",
    "pos_modules": "POS / INS",
    "mapping_systems": "Mapping Systems",
}


class SensorManager:
    """Load, query, and manage the sensor JSON database."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or _DEFAULT_DB_PATH
        self._data: dict = {}
        self.load()

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load sensors.json from disk."""
        if not self.db_path.exists():
            logger.warning(f"Sensor database not found at {self.db_path}, starting empty")
            self._data = {cat: [] for cat in CATEGORIES}
            return

        with open(self.db_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

        total = sum(len(self._data.get(cat, [])) for cat in CATEGORIES)
        logger.info(f"Loaded {total} sensor entries from {self.db_path.name}")

    def save(self) -> None:
        """Write current data back to sensors.json."""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved sensor database to {self.db_path.name}")

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_modules(self, category: str) -> list[dict]:
        """Return all modules in a category (e.g. 'lidar_modules')."""
        return self._data.get(category, [])

    def get_module_by_id(self, category: str, module_id: str) -> Optional[dict]:
        """Look up a single module by its ID within a category."""
        for module in self.get_modules(category):
            if module.get("id") == module_id:
                return module
        return None

    def get_display_name(self, module: dict) -> str:
        """Return a human-readable display name for a module."""
        manufacturer = module.get("manufacturer", "")
        model = module.get("model", module.get("system_name", "Unknown"))
        return f"{manufacturer} {model}".strip()

    def get_all_ids(self, category: str) -> list[str]:
        """Return a list of all IDs in a category."""
        return [m["id"] for m in self.get_modules(category) if "id" in m]

    # ------------------------------------------------------------------
    # Mapping system resolution
    # ------------------------------------------------------------------

    def resolve_mapping_system(self, system_id: str) -> dict:
        """
        Resolve a mapping system to its constituent modules.

        Returns a dict with keys: system, lidar, camera, pos — each
        containing the full module dict (or None if not found).
        """
        system = self.get_module_by_id("mapping_systems", system_id)
        if system is None:
            return {"system": None, "lidar": None, "camera": None, "pos": None}

        return {
            "system": system,
            "lidar": self.get_module_by_id(
                "lidar_modules", system.get("lidar_module_id", "")
            ),
            "camera": self.get_module_by_id(
                "camera_modules", system.get("camera_module_id", "")
            ),
            "pos": self.get_module_by_id(
                "pos_modules", system.get("pos_module_id", "")
            ),
        }

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> list[str]:
        """
        Check for common issues. Returns a list of warning strings.
        """
        warnings = []

        # Check mapping systems reference valid module IDs
        for system in self.get_modules("mapping_systems"):
            sid = system.get("id", "?")
            for ref_key, ref_cat in [
                ("lidar_module_id", "lidar_modules"),
                ("camera_module_id", "camera_modules"),
                ("pos_module_id", "pos_modules"),
            ]:
                ref_id = system.get(ref_key, "")
                if ref_id and self.get_module_by_id(ref_cat, ref_id) is None:
                    warnings.append(
                        f"Mapping system '{sid}': {ref_key}='{ref_id}' not found in {ref_cat}"
                    )

        # Check for duplicate IDs within each category
        for cat in CATEGORIES:
            ids = self.get_all_ids(cat)
            seen = set()
            for mid in ids:
                if mid in seen:
                    warnings.append(f"Duplicate ID '{mid}' in {cat}")
                seen.add(mid)

        return warnings
