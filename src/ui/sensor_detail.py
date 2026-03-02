"""
Sensor detail panel — right panel showing specs and configurations.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.data.sensor_manager import SensorManager
from src.ui.styles import CATEGORY_COLORS, COLORS


# Fields to skip in the detail display (internal / already shown)
_SKIP_FIELDS = {
    "id",
    "configurations",
    "lens_configurations",
    "photo_sizes",
    "scan_mode_fov",
    "scan_modes",
}

# Human-readable labels for common JSON keys
_FIELD_LABELS = {
    "manufacturer": "Manufacturer",
    "model": "Model",
    "system_name": "System Name",
    "type": "Type",
    "laser_channels": "Laser Channels",
    "laser_wavelength_nm": "Wavelength (nm)",
    "laser_wavelength_band": "Wavelength Band",
    "laser_class": "Laser Class",
    "laser_beam_divergence_mrad": "Beam Divergence (mrad)",
    "laser_beam_divergence_cross_mrad": "Divergence Cross-Axis (mrad)",
    "laser_beam_shape": "Beam Shape",
    "laser_beam_divergence_method": "Divergence Method",
    "horizontal_fov_deg": "Horizontal FOV (°)",
    "vertical_fov_deg": "Vertical FOV (°)",
    "vertical_fov_range_deg": "Vertical FOV Range (°)",
    "vertical_resolution_deg": "Vertical Resolution (°)",
    "min_range_m": "Min Range (m)",
    "max_instrument_range_m": "Max Instrument Range (m)",
    "range_accuracy_cm": "Range Accuracy (cm)",
    "range_accuracy_mm": "Range Accuracy (mm)",
    "range_precision_cm": "Range Precision (cm)",
    "range_precision_mm": "Range Precision (mm)",
    "ranging_accuracy_mm": "Ranging Accuracy (mm)",
    "ranging_repeatability_mm": "Repeatability (mm)",
    "weight_g": "Weight (g)",
    "weight_kg": "Weight (kg)",
    "total_weight_kg": "Total Weight (kg)",
    "power_w": "Power (W)",
    "power_w_nominal": "Power, Nominal (W)",
    "power_w_typical": "Power, Typical (W)",
    "power_w_max": "Power, Max (W)",
    "scan_speed_scans_per_sec_range": "Scan Speed Range (scans/s)",
    "angular_step_width_deg_range": "Angular Step Width Range (°)",
    "angle_measurement_resolution_deg": "Angle Resolution (°)",
    "lines_per_second_max": "Max Lines/Second",
    "vertical_scan_lines_deg": "Vertical Scan Lines (°)",
    # Camera
    "sensor_type": "Sensor Type",
    "sensor_width_mm": "Sensor Width (mm)",
    "sensor_height_mm": "Sensor Height (mm)",
    "image_width_px": "Image Width (px)",
    "image_height_px": "Image Height (px)",
    "megapixels": "Megapixels",
    "combined_horizontal_fov_deg": "Combined HFOV (°)",
    "fov_deg": "FOV (°)",
    # POS
    "pitch_roll_accuracy_deg": "Pitch/Roll Accuracy (°)",
    "heading_accuracy_deg": "Heading Accuracy (°)",
    "position_accuracy_h_m": "Horizontal Accuracy (m)",
    "position_accuracy_v_m": "Vertical Accuracy (m)",
    "pitch_roll_accuracy_deg_rtk": "Pitch/Roll Accuracy, RTK (°)",
    "pitch_roll_accuracy_deg_ppk": "Pitch/Roll Accuracy, PPK (°)",
    "heading_accuracy_deg_rtk": "Heading Accuracy, RTK (°)",
    "heading_accuracy_deg_ppk": "Heading Accuracy, PPK (°)",
    "gnss_update_rate_hz": "GNSS Update Rate (Hz)",
    "pos_update_rate_hz": "POS Update Rate (Hz)",
    "gnss_constellations": "GNSS Constellations",
    "gnss_frequencies": "GNSS Frequencies",
    # System
    "lidar_module_id": "LiDAR Module",
    "camera_module_id": "Camera Module",
    "pos_module_id": "POS Module",
    "ndaa_compliant": "NDAA Compliant",
    "onboard_storage_gb": "Onboard Storage (GB)",
    "supported_aircraft": "Supported Aircraft",
    "notes": "Notes",
}


def _format_value(value) -> str:
    """Format a JSON value for display."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, float):
        # Show integers without decimals
        if value == int(value):
            return str(int(value))
        return f"{value:.4g}"
    return str(value)


def _label_for_key(key: str) -> str:
    """Return a human-readable label for a JSON key."""
    if key in _FIELD_LABELS:
        return _FIELD_LABELS[key]
    # Fallback: title-case with underscores replaced
    return key.replace("_", " ").title()


class SensorDetail(QWidget):
    """Read-only detail view for a selected sensor module."""

    def __init__(self, manager: SensorManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._current_category: str | None = None
        self._current_module_id: str | None = None
        self._build_ui()

        # Auto-refresh when data changes
        self.manager.data_changed.connect(self._on_data_changed)

    def _build_ui(self):
        # Outer scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.content = QWidget()
        self.content.setObjectName("detail_panel")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(24, 20, 24, 20)
        self.content_layout.setSpacing(0)

        # Title area
        self.title_label = QLabel("Select a sensor")
        self.title_label.setObjectName("detail_title")
        self.content_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("detail_subtitle")
        self.content_layout.addWidget(self.subtitle_label)

        # Placeholder for dynamic content
        self.specs_container = QWidget()
        self.specs_layout = QVBoxLayout(self.specs_container)
        self.specs_layout.setContentsMargins(0, 0, 0, 0)
        self.specs_layout.setSpacing(4)
        self.content_layout.addWidget(self.specs_container)

        self.content_layout.addStretch()

        scroll.setWidget(self.content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_sensor(self, category: str, module_id: str):
        """Display the detail view for a given sensor."""
        self._current_category = category
        self._current_module_id = module_id

        module = self.manager.get_module_by_id(category, module_id)
        if module is None:
            self.title_label.setText("Sensor not found")
            self.subtitle_label.setText("")
            return

        # Update title
        display_name = self.manager.get_display_name(module)
        self.title_label.setText(display_name)

        # Category badge as subtitle
        from src.data.sensor_manager import CATEGORY_LABELS

        cat_label = CATEGORY_LABELS.get(category, category)
        cat_color = CATEGORY_COLORS.get(category, COLORS["accent"])
        self.subtitle_label.setText(f"<span style='color: {cat_color};'>{cat_label}</span>")

        # Clear old content
        self._clear_specs()

        # ── Core specs table ──
        self._add_section_header("SPECIFICATIONS")
        self._add_specs_table(module)

        # ── Configurations ──
        configs = module.get("configurations", [])
        if configs:
            self._add_section_header("CONFIGURATIONS")
            self._add_configs_table(configs)

        # ── Lens configurations (cameras) ──
        lenses = module.get("lens_configurations", [])
        if lenses:
            self._add_section_header("LENS CONFIGURATIONS")
            self._add_configs_table(lenses)

        # ── Photo sizes (cameras) ──
        photos = module.get("photo_sizes", [])
        if photos:
            self._add_section_header("PHOTO SIZES")
            self._add_configs_table(photos)

        # ── Scan mode FOV (DJI L3) ──
        scan_fov = module.get("scan_mode_fov", {})
        if scan_fov:
            self._add_section_header("SCAN MODE FOV")
            self._add_scan_mode_fov(scan_fov)

        # ── Mapping system resolution ──
        if category == "mapping_systems":
            self._add_section_header("CONSTITUENT MODULES")
            self._add_system_resolution(module_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _clear_specs(self):
        """Remove all dynamic widgets from the specs container."""
        while self.specs_layout.count():
            item = self.specs_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _add_section_header(self, text: str):
        label = QLabel(text)
        label.setObjectName("section_header")
        self.specs_layout.addWidget(label)

    def _add_specs_table(self, module: dict):
        """Add a key-value table of core specs."""
        # Collect displayable fields
        rows = []
        for key, value in module.items():
            if key in _SKIP_FIELDS:
                continue
            label = _label_for_key(key)
            display_val = _format_value(value)
            rows.append((label, display_val))

        if not rows:
            return

        table = QTableWidget(len(rows), 2)
        table.setHorizontalHeaderLabels(["Property", "Value"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)

        for i, (label, val) in enumerate(rows):
            key_item = QTableWidgetItem(label)
            key_item.setForeground(Qt.GlobalColor.darkGray)
            table.setItem(i, 0, key_item)

            val_item = QTableWidgetItem(val)
            table.setItem(i, 1, val_item)

        # Size table to content — capped at 280px to leave room for configs
        table.resizeRowsToContents()
        total_height = sum(table.rowHeight(r) for r in range(table.rowCount()))
        total_height += table.horizontalHeader().height() + 4
        table.setFixedHeight(min(total_height, 280))
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.specs_layout.addWidget(table)

    def _add_configs_table(self, configs: list[dict]):
        """Add a table showing configuration modes."""
        if not configs:
            return

        # Gather all unique keys across configs
        all_keys = []
        seen = set()
        for cfg in configs:
            for key in cfg:
                if key not in seen:
                    all_keys.append(key)
                    seen.add(key)

        table = QTableWidget(len(configs), len(all_keys))
        headers = [_label_for_key(k) for k in all_keys]
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)

        for row_idx, cfg in enumerate(configs):
            for col_idx, key in enumerate(all_keys):
                value = cfg.get(key)
                item = QTableWidgetItem(_format_value(value))
                table.setItem(row_idx, col_idx, item)

        table.resizeColumnsToContents()
        table.resizeRowsToContents()

        # Size to content — generous height for configs visibility
        total_height = sum(table.rowHeight(r) for r in range(table.rowCount()))
        total_height += table.horizontalHeader().height() + 4
        table.setFixedHeight(min(total_height, 500))

        # Allow horizontal scrolling for wide tables
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)

        self.specs_layout.addWidget(table)

    def _add_scan_mode_fov(self, scan_fov: dict):
        """Display scan mode FOV as a compact table."""
        rows = []
        for mode, fov in scan_fov.items():
            h = fov.get("horizontal_deg", "—")
            v = fov.get("vertical_deg", "—")
            rows.append((mode.replace("_", " ").title(), f"{h}°", f"{v}°"))

        table = QTableWidget(len(rows), 3)
        table.setHorizontalHeaderLabels(["Mode", "Horizontal", "Vertical"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)

        for i, (mode, h, v) in enumerate(rows):
            table.setItem(i, 0, QTableWidgetItem(mode))
            table.setItem(i, 1, QTableWidgetItem(h))
            table.setItem(i, 2, QTableWidgetItem(v))

        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        total_height = sum(table.rowHeight(r) for r in range(table.rowCount()))
        total_height += table.horizontalHeader().height() + 4
        table.setFixedHeight(min(total_height, 200))
        table.horizontalHeader().setStretchLastSection(True)

        self.specs_layout.addWidget(table)

    def _add_system_resolution(self, system_id: str):
        """Show the resolved LiDAR/Camera/POS modules for a mapping system."""
        resolved = self.manager.resolve_mapping_system(system_id)

        for role in ("lidar", "camera", "pos"):
            module = resolved.get(role)
            if module is None:
                continue

            name = self.manager.get_display_name(module)
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 4, 0, 4)

            role_label = QLabel(f"{role.upper()}:")
            role_label.setFixedWidth(70)
            role_label.setStyleSheet(f"color: {COLORS['text_tertiary']}; font-weight: 600; font-size: 11px;")
            row_layout.addWidget(role_label)

            name_label = QLabel(name)
            name_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px;")
            row_layout.addWidget(name_label)
            row_layout.addStretch()

            self.specs_layout.addWidget(row_widget)

    def _on_data_changed(self):
        """Re-render the current sensor when data changes."""
        if self._current_category and self._current_module_id:
            self.show_sensor(self._current_category, self._current_module_id)
