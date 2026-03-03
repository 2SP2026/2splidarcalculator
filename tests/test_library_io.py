"""
Tests for src/data/library_io — export / import / conflict resolution.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.data.library_io import (
    CONFLICT_COPY,
    CONFLICT_REPLACE,
    CONFLICT_SKIP,
    FORMAT_VERSION,
    ImportPlan,
    execute_import,
    export_full_library,
    export_selected,
    load_from_file,
    save_to_file,
    suggest_filename,
)
from src.data.sensor_manager import CATEGORIES


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def mock_manager():
    """Create a mock SensorManager with a small test library."""
    manager = MagicMock()

    lidar = [
        {"id": "test_lidar_1", "manufacturer": "TestCo", "model": "L1", "prr": 100},
        {"id": "test_lidar_2", "manufacturer": "TestCo", "model": "L2", "prr": 200},
    ]
    camera = [
        {"id": "test_cam_1", "manufacturer": "CamCo", "model": "C1", "mp": 24},
    ]
    pos = [
        {"id": "test_pos_1", "manufacturer": "PosCo", "model": "P1", "accuracy": 0.02},
    ]
    systems = [
        {
            "id": "test_system_1",
            "manufacturer": "SysCo",
            "system_name": "S1",
            "lidar_module_id": "test_lidar_1",
            "camera_module_id": "test_cam_1",
            "pos_module_id": "test_pos_1",
        },
    ]

    data = {
        "lidar_modules": lidar,
        "camera_modules": camera,
        "pos_modules": pos,
        "mapping_systems": systems,
    }

    def get_modules(cat):
        return data.get(cat, [])

    def get_module_by_id(cat, mid):
        for m in data.get(cat, []):
            if m.get("id") == mid:
                return m
        return None

    def get_all_ids(cat):
        return [m["id"] for m in data.get(cat, [])]

    manager.get_modules.side_effect = get_modules
    manager.get_module_by_id.side_effect = get_module_by_id
    manager.get_all_ids.side_effect = get_all_ids
    manager.generate_id.return_value = "test_lidar_1_2"

    return manager


# ── Export tests ────────────────────────────────────────────────────────


class TestExportFullLibrary:
    def test_includes_meta_header(self, mock_manager):
        result = export_full_library(mock_manager)
        assert "meta" in result
        assert result["meta"]["format"] == "2splib"
        assert result["meta"]["version"] == FORMAT_VERSION

    def test_includes_all_categories(self, mock_manager):
        result = export_full_library(mock_manager)
        for cat in CATEGORIES:
            assert cat in result

    def test_correct_total_count(self, mock_manager):
        result = export_full_library(mock_manager)
        total = sum(len(result[cat]) for cat in CATEGORIES)
        assert total == 5  # 2 lidar + 1 camera + 1 pos + 1 system


class TestExportSelected:
    def test_export_standalone_module(self, mock_manager):
        """Exporting a lidar should only include that lidar."""
        result = export_selected(mock_manager, "lidar_modules", ["test_lidar_1"])
        assert len(result["lidar_modules"]) == 1
        assert result["lidar_modules"][0]["id"] == "test_lidar_1"
        assert len(result["camera_modules"]) == 0
        assert len(result["mapping_systems"]) == 0

    def test_export_mapping_system_includes_dependencies(self, mock_manager):
        """Exporting a mapping system should pull in its sub-modules."""
        result = export_selected(mock_manager, "mapping_systems", ["test_system_1"])
        assert len(result["mapping_systems"]) == 1
        assert len(result["lidar_modules"]) == 1
        assert len(result["camera_modules"]) == 1
        assert len(result["pos_modules"]) == 1

    def test_export_selected_has_meta(self, mock_manager):
        result = export_selected(mock_manager, "lidar_modules", ["test_lidar_1"])
        assert "meta" in result


# ── File I/O tests ──────────────────────────────────────────────────────


class TestFileIO:
    def test_save_and_load(self, tmp_path, mock_manager):
        """Round-trip: export → save → load should preserve data."""
        payload = export_full_library(mock_manager)
        filepath = tmp_path / "test.2splib"
        save_to_file(payload, filepath)

        loaded = load_from_file(filepath)
        assert loaded["meta"]["format"] == "2splib"
        assert len(loaded["lidar_modules"]) == 2

    def test_load_invalid_json(self, tmp_path):
        filepath = tmp_path / "bad.2splib"
        filepath.write_text("not json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            load_from_file(filepath)

    def test_load_missing_categories(self, tmp_path):
        filepath = tmp_path / "empty.2splib"
        filepath.write_text('{"foo": "bar"}', encoding="utf-8")
        with pytest.raises(ValueError, match="no recognized sensor categories"):
            load_from_file(filepath)

    def test_load_raw_sensors_json(self, tmp_path):
        """Should accept a plain sensors.json without a meta header."""
        data = {"lidar_modules": [{"id": "x", "model": "X"}]}
        filepath = tmp_path / "sensors.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")
        loaded = load_from_file(filepath)
        assert len(loaded["lidar_modules"]) == 1


# ── Import plan tests ──────────────────────────────────────────────────


class TestImportPlan:
    def test_new_module_detected(self, mock_manager):
        payload = {
            "lidar_modules": [
                {"id": "brand_new", "manufacturer": "New", "model": "N1"}
            ],
            "camera_modules": [],
            "pos_modules": [],
            "mapping_systems": [],
        }
        plan = ImportPlan(mock_manager, payload)
        assert len(plan.to_add) == 1
        assert len(plan.conflicts) == 0
        assert len(plan.identical) == 0

    def test_identical_module_skipped(self, mock_manager):
        # Import an exact copy of an existing module
        payload = {
            "lidar_modules": [
                {"id": "test_lidar_1", "manufacturer": "TestCo", "model": "L1", "prr": 100}
            ],
            "camera_modules": [],
            "pos_modules": [],
            "mapping_systems": [],
        }
        plan = ImportPlan(mock_manager, payload)
        assert len(plan.to_add) == 0
        assert len(plan.identical) == 1
        assert len(plan.conflicts) == 0

    def test_conflict_detected(self, mock_manager):
        # Same ID but different data
        payload = {
            "lidar_modules": [
                {"id": "test_lidar_1", "manufacturer": "TestCo", "model": "L1", "prr": 999}
            ],
            "camera_modules": [],
            "pos_modules": [],
            "mapping_systems": [],
        }
        plan = ImportPlan(mock_manager, payload)
        assert len(plan.to_add) == 0
        assert len(plan.identical) == 0
        assert len(plan.conflicts) == 1

    def test_summary_format(self, mock_manager):
        payload = {
            "lidar_modules": [
                {"id": "brand_new", "manufacturer": "A", "model": "B"},
                {"id": "test_lidar_1", "manufacturer": "TestCo", "model": "L1", "prr": 999},
            ],
            "camera_modules": [],
            "pos_modules": [],
            "mapping_systems": [],
        }
        plan = ImportPlan(mock_manager, payload)
        assert "1 new" in plan.summary
        assert "1 conflict" in plan.summary

    def test_has_conflicts_property(self, mock_manager):
        payload = {"lidar_modules": [{"id": "new", "model": "X"}]}
        plan = ImportPlan(mock_manager, payload)
        assert not plan.has_conflicts


# ── Execute import tests ────────────────────────────────────────────────


class TestExecuteImport:
    def test_add_new_modules(self, mock_manager):
        payload = {
            "lidar_modules": [
                {"id": "new_mod", "manufacturer": "X", "model": "Y"}
            ],
        }
        plan = ImportPlan(mock_manager, payload)
        counts = execute_import(mock_manager, plan)

        assert counts["added"] == 1
        assert counts["skipped"] == 0
        mock_manager.save.assert_called_once()
        mock_manager.data_changed.emit.assert_called_once()

    def test_skip_conflict(self, mock_manager):
        payload = {
            "lidar_modules": [
                {"id": "test_lidar_1", "manufacturer": "TestCo", "model": "L1", "prr": 999}
            ],
        }
        plan = ImportPlan(mock_manager, payload)
        resolutions = {"test_lidar_1": CONFLICT_SKIP}
        counts = execute_import(mock_manager, plan, resolutions)

        assert counts["skipped"] == 1
        assert counts["replaced"] == 0

    def test_replace_conflict(self, mock_manager):
        payload = {
            "lidar_modules": [
                {"id": "test_lidar_1", "manufacturer": "TestCo", "model": "L1", "prr": 999}
            ],
        }
        plan = ImportPlan(mock_manager, payload)
        resolutions = {"test_lidar_1": CONFLICT_REPLACE}
        counts = execute_import(mock_manager, plan, resolutions)

        assert counts["replaced"] == 1

    def test_copy_conflict(self, mock_manager):
        payload = {
            "lidar_modules": [
                {"id": "test_lidar_1", "manufacturer": "TestCo", "model": "L1", "prr": 999}
            ],
        }
        plan = ImportPlan(mock_manager, payload)
        resolutions = {"test_lidar_1": CONFLICT_COPY}
        counts = execute_import(mock_manager, plan, resolutions)

        assert counts["copied"] == 1
        mock_manager.generate_id.assert_called_once()


# ── Filename suggestion ────────────────────────────────────────────────


class TestSuggestFilename:
    def test_full_export_filename(self):
        name = suggest_filename("full")
        assert name.startswith("2sp-sensor-library-")
        assert name.endswith(".2splib")

    def test_selected_export_filename(self):
        name = suggest_filename("selected", "RIEGL miniVUX-3UAV")
        assert "riegl" in name
        assert name.endswith(".2splib")

    def test_selected_no_name_falls_back(self):
        name = suggest_filename("selected", "")
        assert name.startswith("2sp-sensor-library-")
