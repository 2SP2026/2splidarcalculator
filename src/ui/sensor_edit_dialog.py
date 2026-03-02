"""
Sensor edit dialog — form-based dialog for adding / editing sensor profiles.

Uses a field registry to dynamically generate form fields per category,
plus editable sub-tables for nested arrays (configurations, lens configs, etc.).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.data.sensor_manager import CATEGORIES, CATEGORY_LABELS, SensorManager
from src.ui.styles import COLORS


# ── Field Registry ─────────────────────────────────────────────────────
# (key, label, type, required)
# type is one of: str, int, float, bool, "list_str"

_LIDAR_FIELDS = [
    ("manufacturer", "Manufacturer", str, True),
    ("model", "Model", str, True),
    ("type", "Type", str, False),
    ("laser_channels", "Laser Channels", int, False),
    ("laser_wavelength_nm", "Wavelength (nm)", int, False),
    ("laser_wavelength_band", "Wavelength Band", str, False),
    ("laser_class", "Laser Class", str, False),
    ("laser_beam_shape", "Beam Shape", "dropdown:circular,ellipsoidal", False),
    ("laser_beam_divergence_mrad", "Beam Divergence (mrad)", float, False),
    ("laser_beam_divergence_cross_mrad", "Divergence Cross-Axis (mrad)", float, False),
    ("laser_beam_divergence_method", "Divergence Method", "dropdown:FWHM,1/e²", False),
    ("horizontal_fov_deg", "Horizontal FOV (°)", float, False),
    ("vertical_fov_deg", "Vertical FOV (°)", float, False),
    ("min_range_m", "Min Range (m)", float, False),
    ("max_instrument_range_m", "Max Range (m)", float, False),
    ("range_accuracy_mm", "Range Accuracy (mm)", float, False),
    ("range_precision_mm", "Range Precision (mm)", float, False),
    ("weight_g", "Weight (g)", float, False),
    ("weight_kg", "Weight (kg)", float, False),
    ("power_w", "Power (W)", float, False),
]

_CAMERA_FIELDS = [
    ("manufacturer", "Manufacturer", str, True),
    ("model", "Model", str, True),
    ("sensor_type", "Sensor Type", str, False),
    ("sensor_width_mm", "Sensor Width (mm)", float, False),
    ("sensor_height_mm", "Sensor Height (mm)", float, False),
    ("image_width_px", "Image Width (px)", int, False),
    ("image_height_px", "Image Height (px)", int, False),
    ("megapixels", "Megapixels", int, False),
    ("fov_deg", "FOV (°)", float, False),
    ("notes", "Notes", str, False),
]

_POS_FIELDS = [
    ("manufacturer", "Manufacturer", str, True),
    ("model", "Model", str, True),
    ("pitch_roll_accuracy_deg", "Pitch/Roll Accuracy (°)", float, False),
    ("heading_accuracy_deg", "Heading Accuracy (°)", float, False),
    ("position_accuracy_h_m", "Horizontal Accuracy (m)", float, False),
    ("position_accuracy_v_m", "Vertical Accuracy (m)", float, False),
    ("pitch_roll_accuracy_deg_rtk", "Pitch/Roll (RTK) (°)", float, False),
    ("pitch_roll_accuracy_deg_ppk", "Pitch/Roll (PPK) (°)", float, False),
    ("heading_accuracy_deg_rtk", "Heading (RTK) (°)", float, False),
    ("heading_accuracy_deg_ppk", "Heading (PPK) (°)", float, False),
    ("gnss_update_rate_hz", "GNSS Update Rate (Hz)", int, False),
    ("pos_update_rate_hz", "POS Update Rate (Hz)", int, False),
    ("gnss_constellations", "GNSS Constellations", "list_str", False),
    ("gnss_frequencies", "GNSS Frequencies", "list_str", False),
    ("notes", "Notes", str, False),
]

_SYSTEM_FIELDS = [
    ("manufacturer", "Manufacturer", str, True),
    ("system_name", "System Name", str, True),
    ("lidar_module_id", "LiDAR Module", "ref_lidar", True),
    ("camera_module_id", "Camera Module", "ref_camera", True),
    ("pos_module_id", "POS Module", "ref_pos", True),
    ("total_weight_kg", "Total Weight (kg)", float, False),
    ("ndaa_compliant", "NDAA Compliant", bool, False),
    ("onboard_storage_gb", "Onboard Storage (GB)", int, False),
    ("power_w_typical", "Power, Typical (W)", float, False),
    ("power_w_max", "Power, Max (W)", float, False),
    ("supported_aircraft", "Supported Aircraft", "list_str", False),
    ("notes", "Notes", str, False),
]

FIELD_REGISTRY = {
    "lidar_modules": _LIDAR_FIELDS,
    "camera_modules": _CAMERA_FIELDS,
    "pos_modules": _POS_FIELDS,
    "mapping_systems": _SYSTEM_FIELDS,
}

# Nested array fields per category (field_key, display_label)
NESTED_ARRAYS = {
    "lidar_modules": [("configurations", "Configurations")],
    "camera_modules": [
        ("lens_configurations", "Lens Configurations"),
        ("photo_sizes", "Photo Sizes"),
    ],
    "pos_modules": [],
    "mapping_systems": [],
}

# Reference field → source category mapping
_REF_CATEGORIES = {
    "ref_lidar": "lidar_modules",
    "ref_camera": "camera_modules",
    "ref_pos": "pos_modules",
}


class SensorEditDialog(QDialog):
    """Form dialog for adding or editing a sensor module."""

    def __init__(
        self,
        manager: SensorManager,
        category: str,
        module_id: str | None = None,
        clone_data: dict | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.manager = manager
        self.category = category
        self.module_id = module_id  # None → add mode
        self._is_edit = module_id is not None
        self._clone_data = clone_data  # Pre-fill data for duplicate mode

        # Widget references for reading values back
        self._field_widgets: dict[str, QWidget] = {}
        self._array_tables: dict[str, QTableWidget] = {}

        self._setup_dialog()
        self._build_ui()

        if self._is_edit:
            self._populate_from_existing()
        elif self._clone_data:
            self._populate_from_clone()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_dialog(self):
        cat_label = CATEGORY_LABELS.get(self.category, self.category)
        if self._clone_data:
            mode = "Duplicate"
        elif self._is_edit:
            mode = "Edit"
        else:
            mode = "Add New"
        self.setWindowTitle(f"{mode} — {cat_label}")
        self.setMinimumSize(560, 500)
        self.resize(620, 650)
        self.setModal(True)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header ──
        header = QWidget()
        header.setObjectName("dialog_header")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 16)

        cat_label = CATEGORY_LABELS.get(self.category, self.category)
        mode = "Edit" if self._is_edit else "New"
        title = QLabel(f"{mode} {cat_label.rstrip('s')}")
        title.setObjectName("dialog_title")
        header_layout.addWidget(title)

        if self._is_edit:
            id_label = QLabel(f"ID: {self.module_id}")
            id_label.setStyleSheet(
                f"color: {COLORS['text_tertiary']}; font-size: 11px;"
            )
            header_layout.addWidget(id_label)

        outer.addWidget(header)

        # ── Scrollable form area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(24, 12, 24, 12)
        form_layout.setSpacing(16)

        # Core fields — in a scroll area with generous height
        fields_group = QGroupBox("Specifications")
        fields_group.setObjectName("form_group")
        fields_form = QFormLayout(fields_group)
        fields_form.setContentsMargins(16, 20, 16, 16)
        fields_form.setSpacing(10)
        fields_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        fields_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self._form_labels: dict[str, QLabel] = {}
        fields = FIELD_REGISTRY.get(self.category, [])
        for key, label, ftype, required in fields:
            widget = self._create_field_widget(key, ftype)
            widget.setMinimumWidth(250)
            display_label = f"{label} *" if required else label
            lbl = QLabel(display_label)
            fields_form.addRow(lbl, widget)
            self._field_widgets[key] = widget
            self._form_labels[key] = lbl

        # Dynamic show/hide: cross-axis divergence only visible for ellipsoidal beams
        if self.category == "lidar_modules":
            cross_widget = self._field_widgets.get("laser_beam_divergence_cross_mrad")
            cross_label = self._form_labels.get("laser_beam_divergence_cross_mrad")
            shape_widget = self._field_widgets.get("laser_beam_shape")

            if cross_widget and cross_label and shape_widget:
                def _on_shape_changed():
                    is_ellipsoidal = shape_widget.currentData() == "ellipsoidal"
                    cross_widget.setVisible(is_ellipsoidal)
                    cross_label.setVisible(is_ellipsoidal)

                shape_widget.currentIndexChanged.connect(_on_shape_changed)
                # Set initial state
                _on_shape_changed()

        # Wrap specs in a scroll area
        specs_scroll = QScrollArea()
        specs_scroll.setWidgetResizable(True)
        specs_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        specs_scroll.setWidget(fields_group)
        specs_scroll.setMaximumHeight(450)
        form_layout.addWidget(specs_scroll)

        # Nested arrays
        nested = NESTED_ARRAYS.get(self.category, [])
        for array_key, array_label in nested:
            group = QGroupBox(array_label)
            group.setObjectName("form_group")
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(16, 20, 16, 16)
            group_layout.setSpacing(8)

            table = QTableWidget(0, 0)
            table.setObjectName("array_edit_table")
            table.verticalHeader().setVisible(False)
            table.setAlternatingRowColors(True)
            table.setShowGrid(False)
            table.setMinimumHeight(100)
            table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.ResizeToContents
            )
            table.horizontalHeader().setStretchLastSection(True)
            self._array_tables[array_key] = table
            group_layout.addWidget(table, stretch=1)

            # Add / Remove buttons
            btn_row = QHBoxLayout()
            btn_row.setSpacing(8)

            add_btn = QPushButton("+ Add Row")
            add_btn.setObjectName("action_btn")
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.clicked.connect(lambda _, t=table: self._add_table_row(t))
            btn_row.addWidget(add_btn)

            rm_btn = QPushButton("− Remove Selected")
            rm_btn.setObjectName("action_btn_danger")
            rm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            rm_btn.clicked.connect(lambda _, t=table: self._remove_table_row(t))
            btn_row.addWidget(rm_btn)

            btn_row.addStretch()
            group_layout.addLayout(btn_row)
            form_layout.addWidget(group, stretch=1)

        form_layout.addStretch()
        scroll.setWidget(form_container)
        outer.addWidget(scroll, stretch=1)

        # ── Footer buttons ──
        footer = QWidget()
        footer.setObjectName("dialog_footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 12, 24, 16)
        footer_layout.setSpacing(10)
        footer_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btn_cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save" if self._is_edit else "Add Sensor")
        save_btn.setObjectName("btn_save")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        footer_layout.addWidget(save_btn)

        outer.addWidget(footer)

    # ------------------------------------------------------------------
    # Field widget factory
    # ------------------------------------------------------------------

    def _create_field_widget(self, key: str, ftype) -> QWidget:
        """Create the appropriate input widget for a field type."""
        if ftype == str:
            w = QLineEdit()
            w.setObjectName("form_input")
            return w

        if ftype == int:
            w = QSpinBox()
            w.setObjectName("form_input")
            w.setRange(0, 999_999)
            w.setSpecialValueText("—")  # Show dash for 0 / unset
            return w

        if ftype == float:
            w = QDoubleSpinBox()
            w.setObjectName("form_input")
            w.setRange(0.0, 999_999.0)
            w.setDecimals(4)
            w.setSpecialValueText("—")
            return w

        if ftype == bool:
            w = QCheckBox()
            return w

        if ftype == "list_str":
            w = QLineEdit()
            w.setObjectName("form_input")
            w.setPlaceholderText("Comma-separated values")
            return w

        # Fixed-choice dropdowns (e.g. "dropdown:circular,ellipsoidal")
        if isinstance(ftype, str) and ftype.startswith("dropdown:"):
            options = ftype.split(":", 1)[1].split(",")
            w = QComboBox()
            w.setObjectName("form_input")
            w.addItem("— Select —", "")
            for opt in options:
                w.addItem(opt.strip(), opt.strip())
            return w

        # Reference dropdowns (mapping system → module selection)
        if isinstance(ftype, str) and ftype.startswith("ref_"):
            source_cat = _REF_CATEGORIES.get(ftype)
            w = QComboBox()
            w.setObjectName("form_input")
            w.addItem("— Select —", "")
            if source_cat:
                for module in self.manager.get_modules(source_cat):
                    display = self.manager.get_display_name(module)
                    w.addItem(display, module.get("id", ""))
            return w

        # Fallback
        w = QLineEdit()
        w.setObjectName("form_input")
        return w

    # ------------------------------------------------------------------
    # Populate for edit mode
    # ------------------------------------------------------------------

    def _populate_from_existing(self):
        """Fill form fields from existing module data."""
        module = self.manager.get_module_by_id(self.category, self.module_id)
        if module is None:
            return
        self._populate_fields(module)

    def _populate_from_clone(self):
        """Fill form fields from cloned data (duplicate mode)."""
        if not self._clone_data:
            return
        self._populate_fields(self._clone_data)

    def _populate_fields(self, module: dict):
        """Shared logic: fill form widgets and array tables from a module dict."""
        fields = FIELD_REGISTRY.get(self.category, [])
        for key, _label, ftype, _req in fields:
            widget = self._field_widgets.get(key)
            value = module.get(key)
            if widget is None or value is None:
                continue
            self._set_widget_value(widget, ftype, value)

        # Populate nested arrays
        for array_key, _label in NESTED_ARRAYS.get(self.category, []):
            items = module.get(array_key, [])
            table = self._array_tables.get(array_key)
            if table is None or not items:
                continue
            self._populate_array_table(table, items)

    def _set_widget_value(self, widget: QWidget, ftype, value):
        """Set a widget's value from JSON data, handling type mismatches."""
        try:
            if ftype == str and isinstance(widget, QLineEdit):
                if isinstance(value, list):
                    widget.setText(", ".join(str(v) for v in value))
                else:
                    widget.setText(str(value))
            elif ftype == int and isinstance(widget, QSpinBox):
                if isinstance(value, list):
                    widget.setValue(int(value[0]))
                else:
                    widget.setValue(int(value))
            elif ftype == float and isinstance(widget, QDoubleSpinBox):
                if isinstance(value, list):
                    widget.setValue(float(value[0]))
                else:
                    widget.setValue(float(value))
            elif ftype == bool and isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif ftype == "list_str" and isinstance(widget, QLineEdit):
                if isinstance(value, list):
                    widget.setText(", ".join(str(v) for v in value))
                else:
                    widget.setText(str(value))
            elif isinstance(ftype, str) and ftype.startswith("ref_") and isinstance(widget, QComboBox):
                idx = widget.findData(value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            elif isinstance(ftype, str) and ftype.startswith("dropdown:") and isinstance(widget, QComboBox):
                idx = widget.findData(str(value))
                if idx >= 0:
                    widget.setCurrentIndex(idx)
        except (TypeError, ValueError, IndexError):
            # If conversion fails, skip this field silently
            pass

    # ------------------------------------------------------------------
    # Array table helpers
    # ------------------------------------------------------------------

    def _populate_array_table(self, table: QTableWidget, items: list[dict]):
        """Fill a QTableWidget from a list of dicts."""
        if not items:
            return

        # Collect all unique keys
        all_keys = []
        seen = set()
        for item in items:
            for k in item:
                if k not in seen:
                    all_keys.append(k)
                    seen.add(k)

        table.setColumnCount(len(all_keys))
        table.setHorizontalHeaderLabels(
            [k.replace("_", " ").title() for k in all_keys]
        )
        # Store raw keys as column user data
        table.setProperty("column_keys", all_keys)

        table.setRowCount(len(items))
        for row, item in enumerate(items):
            for col, key in enumerate(all_keys):
                val = item.get(key, "")
                cell = QTableWidgetItem(self._to_cell_str(val))
                table.setItem(row, col, cell)

        table.resizeColumnsToContents()

    def _add_table_row(self, table: QTableWidget):
        """Add an empty row to a nested array table."""
        if table.columnCount() == 0:
            # First row — ask for column setup (use 'name' as default starter)
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Name", "Value"])
            table.setProperty("column_keys", ["name", "value"])

        row = table.rowCount()
        table.insertRow(row)
        for col in range(table.columnCount()):
            table.setItem(row, col, QTableWidgetItem(""))

    def _remove_table_row(self, table: QTableWidget):
        """Remove the selected row from a nested array table."""
        row = table.currentRow()
        if row >= 0:
            table.removeRow(row)

    @staticmethod
    def _to_cell_str(value) -> str:
        """Convert a JSON value to a string for table cell editing."""
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        return str(value)

    @staticmethod
    def _from_cell_str(text: str):
        """Try to convert a table cell string back to a typed value."""
        text = text.strip()
        if text == "":
            return None
        if text.lower() in ("true", "yes"):
            return True
        if text.lower() in ("false", "no"):
            return False
        # Try number conversion
        try:
            if "." in text:
                return float(text)
            return int(text)
        except ValueError:
            pass
        # Try comma-separated list
        if "," in text:
            parts = [p.strip() for p in text.split(",")]
            # Try converting list items to numbers
            typed = []
            for p in parts:
                try:
                    typed.append(float(p) if "." in p else int(p))
                except ValueError:
                    typed.append(p)
            return typed
        return text

    # ------------------------------------------------------------------
    # Read form data
    # ------------------------------------------------------------------

    def _read_form_data(self) -> dict:
        """Read all form widgets into a dict suitable for sensor_manager."""
        data = {}
        fields = FIELD_REGISTRY.get(self.category, [])

        for key, _label, ftype, _req in fields:
            widget = self._field_widgets.get(key)
            if widget is None:
                continue
            value = self._read_widget_value(widget, ftype)
            if value is not None and value != "" and value != 0:
                data[key] = value

        # Read nested arrays
        for array_key, _label in NESTED_ARRAYS.get(self.category, []):
            table = self._array_tables.get(array_key)
            if table is None or table.rowCount() == 0:
                continue
            data[array_key] = self._read_array_table(table)

        return data

    def _read_widget_value(self, widget: QWidget, ftype):
        """Read a value from a form widget."""
        if ftype == str and isinstance(widget, QLineEdit):
            return widget.text().strip()
        if ftype == int and isinstance(widget, QSpinBox):
            v = widget.value()
            return v if v != 0 else None
        if ftype == float and isinstance(widget, QDoubleSpinBox):
            v = widget.value()
            return v if v != 0.0 else None
        if ftype == bool and isinstance(widget, QCheckBox):
            return widget.isChecked()
        if ftype == "list_str" and isinstance(widget, QLineEdit):
            text = widget.text().strip()
            if not text:
                return None
            return [s.strip() for s in text.split(",") if s.strip()]
        if isinstance(ftype, str) and ftype.startswith("ref_") and isinstance(widget, QComboBox):
            val = widget.currentData()
            return val if val else None
        if isinstance(ftype, str) and ftype.startswith("dropdown:") and isinstance(widget, QComboBox):
            val = widget.currentData()
            return val if val else None
        return None

    def _read_array_table(self, table: QTableWidget) -> list[dict]:
        """Read all rows from a nested array table."""
        column_keys = table.property("column_keys") or []
        if not column_keys:
            # Fall back to header labels
            column_keys = [
                table.horizontalHeaderItem(c).text().lower().replace(" ", "_")
                for c in range(table.columnCount())
                if table.horizontalHeaderItem(c)
            ]

        rows = []
        for r in range(table.rowCount()):
            row_data = {}
            for c, key in enumerate(column_keys):
                item = table.item(r, c)
                if item:
                    val = self._from_cell_str(item.text())
                    if val is not None:
                        row_data[key] = val
            if row_data:
                rows.append(row_data)
        return rows

    # ------------------------------------------------------------------
    # Validation & save
    # ------------------------------------------------------------------

    def _on_save(self):
        """Validate and persist the form data."""
        data = self._read_form_data()

        # Check required fields
        fields = FIELD_REGISTRY.get(self.category, [])
        missing = []
        for key, label, _ftype, required in fields:
            if required and (key not in data or data[key] in (None, "", [])):
                missing.append(label)

        if missing:
            QMessageBox.warning(
                self,
                "Missing Required Fields",
                f"Please fill in:\n• " + "\n• ".join(missing),
            )
            return

        # Check for duplicate model / system_name within the category
        name_key = "system_name" if self.category == "mapping_systems" else "model"
        new_name = data.get(name_key, "")
        if new_name:
            for existing in self.manager.get_modules(self.category):
                # Skip self when editing
                if self._is_edit and existing.get("id") == self.module_id:
                    continue
                if existing.get(name_key, "") == new_name:
                    label = "System Name" if name_key == "system_name" else "Model"
                    QMessageBox.warning(
                        self,
                        "Duplicate Name",
                        f"A {CATEGORY_LABELS.get(self.category, 'sensor')} with "
                        f"{label} \"{new_name}\" already exists.\n\n"
                        f"Please use a unique name.",
                    )
                    return

        if self._is_edit:
            self.manager.update_module(self.category, self.module_id, data)
        else:
            self.manager.add_module(self.category, data)

        self.accept()
