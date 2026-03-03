"""
Sensor database manager for loading, querying, and saving sensor profiles.

Reads and writes to sensors.json — the local JSON sensor library.
"""

import json
import re
import shutil
import sys
from pathlib import Path
from typing import Optional

from loguru import logger
from PySide6.QtCore import QObject, Signal


def _resolve_db_path() -> Path:
    """
    Determine the writable path to sensors.json.

    In development mode, this is simply next to this source file.
    In a PyInstaller frozen build, the bundled sensors.json lives in a
    read-only location, so we copy it to a writable directory next to
    the executable on first launch.
    """
    if getattr(sys, "frozen", False):
        # Running as a frozen PyInstaller bundle
        exe_dir = Path(sys.executable).parent
        writable_db = exe_dir / "sensors.json"

        if not writable_db.exists():
            # First launch — copy bundled default to writable location
            bundled = Path(sys._MEIPASS) / "src" / "data" / "sensors.json"
            if bundled.exists():
                shutil.copy2(bundled, writable_db)
                logger.info(f"Copied default sensor database to {writable_db}")
            else:
                logger.warning("No bundled sensors.json found in frozen build")

        return writable_db
    else:
        # Development mode — use file relative to this module
        return Path(__file__).parent / "sensors.json"


# Default path to the sensor database
_DEFAULT_DB_PATH = _resolve_db_path()

# Valid top-level categories in the database
CATEGORIES = ("lidar_modules", "camera_modules", "pos_modules", "mapping_systems")

# Human-readable labels for each category
CATEGORY_LABELS = {
    "lidar_modules": "LiDAR Sensors",
    "camera_modules": "Cameras",
    "pos_modules": "POS / INS",
    "mapping_systems": "Mapping Systems",
}


class SensorManager(QObject):
    """Load, query, and manage the sensor JSON database."""

    # Emitted after any mutation (add / update / delete)
    data_changed = Signal()

    def __init__(self, db_path: Optional[Path] = None, parent=None):
        super().__init__(parent)
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
    # CRUD mutations
    # ------------------------------------------------------------------

    def generate_id(self, manufacturer: str, model: str) -> str:
        """
        Auto-generate a slug ID from manufacturer + model.

        Example: 'Hesai', 'XT32-M2X' → 'hesai_xt32_m2x'
        Appends _2, _3 etc. if the ID already exists across all categories.
        """
        raw = f"{manufacturer}_{model}".lower()
        slug = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")

        # De-duplicate across all categories
        all_ids = set()
        for cat in CATEGORIES:
            all_ids.update(self.get_all_ids(cat))

        if slug not in all_ids:
            return slug

        counter = 2
        while f"{slug}_{counter}" in all_ids:
            counter += 1
        return f"{slug}_{counter}"

    def add_module(self, category: str, data: dict) -> str:
        """
        Add a new module to a category. Returns the assigned ID.

        The 'id' key is auto-generated if not present.
        Saves to disk and emits data_changed.
        """
        if "id" not in data:
            manufacturer = data.get("manufacturer", "unknown")
            model = data.get("model", data.get("system_name", "unknown"))
            data["id"] = self.generate_id(manufacturer, model)

        self._data.setdefault(category, []).append(data)
        self.save()
        self.data_changed.emit()
        logger.info(f"Added '{data['id']}' to {category}")
        return data["id"]

    def update_module(self, category: str, module_id: str, data: dict) -> bool:
        """
        Replace an existing module's data in-place.

        The 'id' field in data is forced to match module_id.
        Saves to disk and emits data_changed. Returns True on success.
        """
        modules = self.get_modules(category)
        for i, module in enumerate(modules):
            if module.get("id") == module_id:
                data["id"] = module_id  # Preserve original ID
                modules[i] = data
                self.save()
                self.data_changed.emit()
                logger.info(f"Updated '{module_id}' in {category}")
                return True
        logger.warning(f"Module '{module_id}' not found in {category} for update")
        return False

    def delete_module(self, category: str, module_id: str) -> bool:
        """
        Remove a module from a category.

        Saves to disk and emits data_changed. Returns True on success.
        """
        modules = self.get_modules(category)
        for i, module in enumerate(modules):
            if module.get("id") == module_id:
                modules.pop(i)
                self.save()
                self.data_changed.emit()
                logger.info(f"Deleted '{module_id}' from {category}")
                return True
        logger.warning(f"Module '{module_id}' not found in {category} for deletion")
        return False

    def get_referencing_systems(self, category: str, module_id: str) -> list[str]:
        """
        Return a list of mapping system IDs that reference this module.

        Used to warn before deleting a module that is part of a system.
        """
        if category == "mapping_systems":
            return []

        ref_key_map = {
            "lidar_modules": "lidar_module_id",
            "camera_modules": "camera_module_id",
            "pos_modules": "pos_module_id",
        }
        ref_key = ref_key_map.get(category)
        if not ref_key:
            return []

        refs = []
        for system in self.get_modules("mapping_systems"):
            if system.get(ref_key) == module_id:
                refs.append(system.get("id", "?"))
        return refs

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
