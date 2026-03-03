"""
Calculator panel — tabbed interface for NPD, GSD, and Horizontal Error calculators.

Each tab provides:
- Sensor picker with "Manual Entry" option + library sensors
- Input form with auto-populated fields from sensor data
- Real-time result display that updates on every input change
- Export to TXT (script-friendly) or HTML (presentation-grade)
"""

from pathlib import Path

from loguru import logger
from PySide6.QtCore import Qt, QStandardPaths
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.npd_calculator import NpdInputs, calculate_npd
from src.core.gsd_calculator import GsdInputs, calculate_gsd
from src.core.horizontal_error_calculator import (
    HorizontalErrorInputs,
    calculate_horizontal_error,
)
from src.core.calculator_export import ExportData, default_filename, export_txt, export_html
from src.data.sensor_manager import SensorManager
from src.ui.styles import COLORS, FONTS


# ─── Constants ────────────────────────────────────────────────────────────

_MANUAL_ENTRY = "— Manual Entry —"

# Assumptions and references for each calculator
_NPD_ASSUMPTIONS = [
    "Single pass (no sidelap / overlap)",
    "Constant ground speed and AGL",
    "Single return per pulse",
    "Uniform point distribution across the effective swath",
    "All pulses within the effective FOV generate a ground return",
]
_NPD_MATH = "NPD = (PRR × eFOV/sFOV) / (v × 2 × AGL × tan(eFOV/2))"
_NPD_REFERENCES: list[str] = []  # No external reference

_GSD_ASSUMPTIONS = [
    "Flat terrain",
    "Nadir-looking camera (no oblique angle)",
    "Pinhole camera model",
    "Square pixels (same pitch in both sensor axes)",
]
_GSD_MATH = "GSD = (pixel_pitch × AGL) / focal_length"
_GSD_REFERENCES: list[str] = []  # No external reference

_HERR_ASSUMPTIONS = [
    "Beam divergence is neglected (narrow footprint for modern sensors)",
    "Laser ranging and clock timing errors are negligible",
    "Flat terrain (no slope correction)",
]
_HERR_MATH = (
    "RMSE_H = √( GNSS² + ((tan(rp) + tan(hdg)) / 1.478 × FH)² )"
)
_HERR_REFERENCES = [
    "ASPRS Positional Accuracy Standards for Digital Geospatial Data, "
    "Edition 2, 2024 — Table B.8",
]


# ─── Helpers ──────────────────────────────────────────────────────────────


def _make_double_spin(
    minimum: float = 0.0,
    maximum: float = 999999.0,
    decimals: int = 2,
    suffix: str = "",
    value: float = 0.0,
) -> QDoubleSpinBox:
    """Create a styled QDoubleSpinBox."""
    sb = QDoubleSpinBox()
    sb.setRange(minimum, maximum)
    sb.setDecimals(decimals)
    sb.setValue(value)
    if suffix:
        sb.setSuffix(f"  {suffix}")
    sb.setMinimumWidth(180)
    sb.setObjectName("form_input")
    return sb


def _make_int_spin(
    minimum: int = 0,
    maximum: int = 99999999,
    suffix: str = "",
    value: int = 0,
) -> QSpinBox:
    """Create a styled QSpinBox."""
    sb = QSpinBox()
    sb.setRange(minimum, maximum)
    sb.setValue(value)
    if suffix:
        sb.setSuffix(f"  {suffix}")
    sb.setMinimumWidth(180)
    sb.setObjectName("form_input")
    return sb


def _make_result_card(title: str, unit: str) -> tuple[QFrame, QLabel]:
    """Create a styled result display card. Returns (frame, value_label)."""
    frame = QFrame()
    frame.setObjectName("result_card")

    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(4)

    title_lbl = QLabel(title)
    title_lbl.setObjectName("result_card_title")

    value_lbl = QLabel("—")
    value_lbl.setObjectName("result_card_value")

    unit_lbl = QLabel(unit)
    unit_lbl.setObjectName("result_card_unit")

    layout.addWidget(title_lbl)
    layout.addWidget(value_lbl)
    layout.addWidget(unit_lbl)

    return frame, value_lbl


def _make_section_label(text: str) -> QLabel:
    """Create a section header label."""
    lbl = QLabel(text)
    lbl.setObjectName("calc_section_header")
    return lbl


def _make_error_label() -> QLabel:
    """Create an inline error label (hidden by default)."""
    lbl = QLabel("")
    lbl.setObjectName("calc_error")
    lbl.setVisible(False)
    lbl.setWordWrap(True)
    return lbl


def _make_export_row() -> tuple[QWidget, QPushButton]:
    """Create an export button row. Returns (row_widget, button)."""
    row = QWidget()
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(0, 4, 0, 4)
    row_layout.addStretch()
    btn = QPushButton("📄  Export Results ▾")
    btn.setObjectName("action_btn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedWidth(180)
    row_layout.addWidget(btn)
    return row, btn


def _do_export(parent: QWidget, data: ExportData, fmt: str) -> None:
    """Show a Save dialog and export to the chosen format."""
    ext = "txt" if fmt == "txt" else "html"
    suggested = default_filename(data, ext)

    # Cross-platform default directory: Desktop
    desktop = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DesktopLocation
    )
    default_path = str(Path(desktop) / suggested)

    filter_str = (
        "Text files (*.txt)" if fmt == "txt"
        else "HTML files (*.html)"
    )

    path, _ = QFileDialog.getSaveFileName(
        parent, "Export Results", default_path, filter_str,
    )
    if not path:
        return  # user cancelled

    try:
        out = Path(path)
        if fmt == "txt":
            export_txt(data, out)
        else:
            export_html(data, out)
        logger.info(f"Exported {fmt.upper()} to {out}")
    except Exception as exc:
        logger.error(f"Export failed: {exc}")
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(parent, "Export Failed", str(exc))


def _make_info_section(
    assumptions: list[str],
    math_formula: str,
    references: list[str],
) -> QFrame:
    """Create an Assumptions & References info box."""
    frame = QFrame()
    frame.setObjectName("info_section")

    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 12, 16, 12)
    layout.setSpacing(8)

    # Title
    title = QLabel("ℹ  Assumptions & References")
    title.setObjectName("info_section_title")
    layout.addWidget(title)

    # Math model
    math_lbl = QLabel(f"<b>Model:</b>&nbsp;&nbsp;<code>{math_formula}</code>")
    math_lbl.setObjectName("info_section_text")
    math_lbl.setTextFormat(Qt.TextFormat.RichText)
    math_lbl.setWordWrap(True)
    layout.addWidget(math_lbl)

    # Assumptions
    bullets = "".join(f"<li>{a}</li>" for a in assumptions)
    assumptions_lbl = QLabel(
        f"<b>Assumptions:</b><ul style='margin:4px 0 0 -20px;'>{bullets}</ul>"
    )
    assumptions_lbl.setObjectName("info_section_text")
    assumptions_lbl.setTextFormat(Qt.TextFormat.RichText)
    assumptions_lbl.setWordWrap(True)
    layout.addWidget(assumptions_lbl)

    # References (optional)
    if references:
        ref_bullets = "".join(f"<li>{r}</li>" for r in references)
        ref_lbl = QLabel(
            f"<b>References:</b>"
            f"<ul style='margin:4px 0 0 -20px;'>{ref_bullets}</ul>"
        )
        ref_lbl.setObjectName("info_section_text")
        ref_lbl.setTextFormat(Qt.TextFormat.RichText)
        ref_lbl.setWordWrap(True)
        layout.addWidget(ref_lbl)

    return frame


# ═══════════════════════════════════════════════════════════════════════════
#  NPD Tab
# ═══════════════════════════════════════════════════════════════════════════


class NpdTab(QWidget):
    """Nominal Point Density calculator tab."""

    def __init__(self, manager: SensorManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._build_ui()
        self._connect_signals()
        self.manager.data_changed.connect(self._refresh_sensors)

    # ── Build ──────────────────────────────────────────────────

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Sensor picker ──
        layout.addWidget(_make_section_label("SENSOR"))
        picker_group = QGroupBox()
        picker_group.setObjectName("calc_group")
        picker_layout = QFormLayout(picker_group)
        picker_layout.setSpacing(10)

        self.sensor_combo = QComboBox()
        self.sensor_combo.setMinimumWidth(280)
        picker_layout.addRow("LiDAR Sensor:", self.sensor_combo)

        self.config_combo = QComboBox()
        self.config_combo.setMinimumWidth(280)
        picker_layout.addRow("Configuration:", self.config_combo)

        layout.addWidget(picker_group)

        # ── Input form ──
        layout.addWidget(_make_section_label("PARAMETERS"))
        input_group = QGroupBox()
        input_group.setObjectName("calc_group")
        input_layout = QFormLayout(input_group)
        input_layout.setSpacing(10)

        self.prr_spin = _make_double_spin(0, 10_000_000, 0, "pts/sec")
        self.speed_spin = _make_double_spin(0, 500, 1, "m/s")
        self.agl_spin = _make_double_spin(0, 20000, 1, "m")
        self.sfov_spin = _make_double_spin(0, 360, 1, "°")
        self.efov_spin = _make_double_spin(0, 360, 1, "°")

        input_layout.addRow("Pulse Repetition Rate:", self.prr_spin)
        input_layout.addRow("Ground Speed:", self.speed_spin)
        input_layout.addRow("AGL (Height):", self.agl_spin)
        input_layout.addRow("Sensor FOV:", self.sfov_spin)
        input_layout.addRow("Effective FOV:", self.efov_spin)

        layout.addWidget(input_group)

        # ── Error ──
        self.error_label = _make_error_label()
        layout.addWidget(self.error_label)

        # ── Results ──
        layout.addWidget(_make_section_label("RESULTS"))
        results_row = QHBoxLayout()
        results_row.setSpacing(12)

        card, self.npd_value = _make_result_card("Nominal Point Density", "pts/m²")
        results_row.addWidget(card)
        card, self.swath_value = _make_result_card("Swath Width", "m")
        results_row.addWidget(card)
        card, self.eff_prr_value = _make_result_card("Effective PRR", "pts/sec")
        results_row.addWidget(card)
        card, self.coverage_value = _make_result_card("Coverage Rate", "m²/s")
        results_row.addWidget(card)

        layout.addLayout(results_row)

        # ── Export ──
        export_row, self.export_btn = _make_export_row()
        layout.addWidget(export_row)

        # ── Assumptions & References ──
        layout.addWidget(_make_section_label("INFO"))
        layout.addWidget(_make_info_section(
            _NPD_ASSUMPTIONS, _NPD_MATH, _NPD_REFERENCES,
        ))

        layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._refresh_sensors()

    # ── Signals ──────────────────────────────────────────────

    def _connect_signals(self):
        self.sensor_combo.currentIndexChanged.connect(self._on_sensor_changed)
        self.config_combo.currentIndexChanged.connect(self._on_config_changed)
        for spin in (self.prr_spin, self.speed_spin, self.agl_spin,
                     self.sfov_spin, self.efov_spin):
            spin.valueChanged.connect(self._recompute)
        # Export menu
        menu = QMenu(self)
        menu.addAction("Export as TXT…", lambda: self._on_export("txt"))
        menu.addAction("Export as HTML…", lambda: self._on_export("html"))
        self.export_btn.setMenu(menu)

    # ── Sensor population ────────────────────────────────────

    def _refresh_sensors(self):
        self.sensor_combo.blockSignals(True)
        self.sensor_combo.clear()
        self.sensor_combo.addItem(_MANUAL_ENTRY, None)
        for mod in self.manager.get_modules("lidar_modules"):
            label = self.manager.get_display_name(mod)
            self.sensor_combo.addItem(label, mod.get("id"))
        self.sensor_combo.blockSignals(False)
        self._on_sensor_changed()

    def _on_sensor_changed(self):
        sensor_id = self.sensor_combo.currentData()
        self.config_combo.blockSignals(True)
        self.config_combo.clear()

        if sensor_id is None:
            # Manual entry — clear fields
            self.config_combo.setEnabled(False)
            self._set_spin_values(prr=0, sfov=0, efov=0)
        else:
            mod = self.manager.get_module_by_id("lidar_modules", sensor_id)
            if mod:
                # Populate FOV from sensor-level field
                sfov = mod.get("horizontal_fov_deg") or 0
                self.sfov_spin.setValue(sfov)
                self.efov_spin.setValue(sfov)  # Default eFOV = sFOV

                # Populate configurations
                configs = mod.get("configurations", [])
                if configs:
                    self.config_combo.setEnabled(True)
                    for cfg in configs:
                        name = cfg.get("name", "Default")
                        self.config_combo.addItem(name, cfg)
                else:
                    self.config_combo.setEnabled(False)

        self.config_combo.blockSignals(False)
        self._on_config_changed()

    def _on_config_changed(self):
        cfg = self.config_combo.currentData()
        if cfg and isinstance(cfg, dict):
            prr = cfg.get("pulse_repetition_rate_khz", 0) * 1000
            if prr == 0:
                prr = cfg.get("points_per_second", 0)
            self.prr_spin.setValue(prr)
        self._recompute()

    def _set_spin_values(self, prr=None, sfov=None, efov=None):
        if prr is not None:
            self.prr_spin.setValue(prr)
        if sfov is not None:
            self.sfov_spin.setValue(sfov)
        if efov is not None:
            self.efov_spin.setValue(efov)

    # ── Compute ──────────────────────────────────────────────

    def _recompute(self):
        self.error_label.setVisible(False)
        try:
            inputs = NpdInputs(
                prr_hz=self.prr_spin.value(),
                ground_speed_ms=self.speed_spin.value(),
                agl_m=self.agl_spin.value(),
                sensor_fov_deg=self.sfov_spin.value(),
                effective_fov_deg=self.efov_spin.value(),
            )
            result = calculate_npd(inputs)
            self.npd_value.setText(f"{result.npd_pts_m2:,.2f}")
            self.swath_value.setText(f"{result.swath_width_m:,.1f}")
            self.eff_prr_value.setText(f"{result.effective_prr_hz:,.0f}")
            self.coverage_value.setText(f"{result.coverage_rate_m2s:,.1f}")
        except (ValueError, ZeroDivisionError) as e:
            self._show_error(str(e))

    def _show_error(self, msg: str):
        self.npd_value.setText("—")
        self.swath_value.setText("—")
        self.eff_prr_value.setText("—")
        self.coverage_value.setText("—")
        self.error_label.setText(f"⚠ {msg}")
        self.error_label.setVisible(True)

    def _collect_export_data(self) -> ExportData:
        """Gather current state into an ExportData."""
        sensor_text = self.sensor_combo.currentText()
        sensor_id = self.sensor_combo.currentData()
        config_text = self.config_combo.currentText() if self.config_combo.isEnabled() else ""
        return ExportData(
            calculator_name="Nominal Point Density (NPD)",
            calculator_slug="npd",
            sensor_label=sensor_text,
            sensor_slug=sensor_id or "manual_entry",
            sensor_category="LiDAR",
            configuration_label=config_text,
            inputs=[
                ("Pulse Repetition Rate", f"{self.prr_spin.value():,.0f} pts/sec"),
                ("Ground Speed", f"{self.speed_spin.value():.1f} m/s"),
                ("AGL (Height)", f"{self.agl_spin.value():.1f} m"),
                ("Sensor FOV", f"{self.sfov_spin.value():.1f}°"),
                ("Effective FOV", f"{self.efov_spin.value():.1f}°"),
            ],
            results=[
                ("NPD", f"{self.npd_value.text()} pts/m²"),
                ("Swath Width", f"{self.swath_value.text()} m"),
                ("Effective PRR", f"{self.eff_prr_value.text()} pts/sec"),
                ("Coverage Rate", f"{self.coverage_value.text()} m²/s"),
            ],
            math_formula=_NPD_MATH,
            assumptions=_NPD_ASSUMPTIONS,
            references=_NPD_REFERENCES,
        )

    def _on_export(self, fmt: str):
        _do_export(self, self._collect_export_data(), fmt)


# ═══════════════════════════════════════════════════════════════════════════
#  GSD Tab
# ═══════════════════════════════════════════════════════════════════════════


class GsdTab(QWidget):
    """Ground Sample Distance calculator tab."""

    def __init__(self, manager: SensorManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._build_ui()
        self._connect_signals()
        self.manager.data_changed.connect(self._refresh_sensors)

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Sensor picker ──
        layout.addWidget(_make_section_label("SENSOR"))
        picker_group = QGroupBox()
        picker_group.setObjectName("calc_group")
        picker_layout = QFormLayout(picker_group)
        picker_layout.setSpacing(10)

        self.sensor_combo = QComboBox()
        self.sensor_combo.setMinimumWidth(280)
        picker_layout.addRow("Camera:", self.sensor_combo)

        self.lens_combo = QComboBox()
        self.lens_combo.setMinimumWidth(280)
        picker_layout.addRow("Lens Configuration:", self.lens_combo)

        layout.addWidget(picker_group)

        # ── Input form ──
        layout.addWidget(_make_section_label("PARAMETERS"))
        input_group = QGroupBox()
        input_group.setObjectName("calc_group")
        input_layout = QFormLayout(input_group)
        input_layout.setSpacing(10)

        self.sensor_width_spin = _make_double_spin(0, 200, 2, "mm")
        self.image_width_spin = _make_int_spin(0, 200000, "px")
        self.focal_length_spin = _make_double_spin(0, 2000, 1, "mm")
        self.agl_spin = _make_double_spin(0, 20000, 1, "m")

        input_layout.addRow("Sensor Width:", self.sensor_width_spin)
        input_layout.addRow("Image Width:", self.image_width_spin)
        input_layout.addRow("Focal Length:", self.focal_length_spin)
        input_layout.addRow("AGL (Height):", self.agl_spin)

        layout.addWidget(input_group)

        # ── Error ──
        self.error_label = _make_error_label()
        layout.addWidget(self.error_label)

        # ── Results ──
        layout.addWidget(_make_section_label("RESULTS"))
        results_row = QHBoxLayout()
        results_row.setSpacing(12)

        card, self.gsd_value = _make_result_card("Ground Sample Distance", "m/px")
        results_row.addWidget(card)
        card, self.gsd_cm_value = _make_result_card("GSD", "cm/px")
        results_row.addWidget(card)
        card, self.pixel_pitch_value = _make_result_card("Pixel Pitch", "mm")
        results_row.addWidget(card)

        layout.addLayout(results_row)

        # ── Export ──
        export_row, self.export_btn = _make_export_row()
        layout.addWidget(export_row)

        # ── Assumptions & References ──
        layout.addWidget(_make_section_label("INFO"))
        layout.addWidget(_make_info_section(
            _GSD_ASSUMPTIONS, _GSD_MATH, _GSD_REFERENCES,
        ))

        layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._refresh_sensors()

    def _connect_signals(self):
        self.sensor_combo.currentIndexChanged.connect(self._on_sensor_changed)
        self.lens_combo.currentIndexChanged.connect(self._on_lens_changed)
        for spin in (self.sensor_width_spin, self.image_width_spin,
                     self.focal_length_spin, self.agl_spin):
            spin.valueChanged.connect(self._recompute)
        # Export menu
        menu = QMenu(self)
        menu.addAction("Export as TXT…", lambda: self._on_export("txt"))
        menu.addAction("Export as HTML…", lambda: self._on_export("html"))
        self.export_btn.setMenu(menu)

    # ── Sensor population ────────────────────────────────────

    def _refresh_sensors(self):
        self.sensor_combo.blockSignals(True)
        self.sensor_combo.clear()
        self.sensor_combo.addItem(_MANUAL_ENTRY, None)
        for mod in self.manager.get_modules("camera_modules"):
            label = self.manager.get_display_name(mod)
            self.sensor_combo.addItem(label, mod.get("id"))
        self.sensor_combo.blockSignals(False)
        self._on_sensor_changed()

    def _on_sensor_changed(self):
        sensor_id = self.sensor_combo.currentData()
        self.lens_combo.blockSignals(True)
        self.lens_combo.clear()

        if sensor_id is None:
            # Manual entry
            self.lens_combo.setEnabled(False)
            self.sensor_width_spin.setValue(0)
            self.image_width_spin.setValue(0)
            self.focal_length_spin.setValue(0)
        else:
            mod = self.manager.get_module_by_id("camera_modules", sensor_id)
            if mod:
                self.sensor_width_spin.setValue(mod.get("sensor_width_mm", 0) or 0)
                self.image_width_spin.setValue(mod.get("image_width_px", 0) or 0)

                # Populate lens configurations
                lens_cfgs = mod.get("lens_configurations", [])
                if lens_cfgs:
                    self.lens_combo.setEnabled(True)
                    for lcfg in lens_cfgs:
                        name = lcfg.get("name", "Default")
                        self.lens_combo.addItem(name, lcfg)
                else:
                    self.lens_combo.setEnabled(False)
                    self.focal_length_spin.setValue(0)

        self.lens_combo.blockSignals(False)
        self._on_lens_changed()

    def _on_lens_changed(self):
        lcfg = self.lens_combo.currentData()
        if lcfg and isinstance(lcfg, dict):
            self.focal_length_spin.setValue(lcfg.get("focal_length_mm", 0) or 0)
        self._recompute()

    # ── Compute ──────────────────────────────────────────────

    def _recompute(self):
        self.error_label.setVisible(False)
        try:
            inputs = GsdInputs(
                sensor_width_mm=self.sensor_width_spin.value(),
                image_width_px=self.image_width_spin.value(),
                focal_length_mm=self.focal_length_spin.value(),
                agl_m=self.agl_spin.value(),
            )
            result = calculate_gsd(inputs)
            self.gsd_value.setText(f"{result.gsd_m:.4f}")
            self.gsd_cm_value.setText(f"{result.gsd_m * 100:.2f}")
            self.pixel_pitch_value.setText(f"{result.pixel_pitch_mm:.4f}")
        except (ValueError, ZeroDivisionError) as e:
            self._show_error(str(e))

    def _show_error(self, msg: str):
        self.gsd_value.setText("—")
        self.gsd_cm_value.setText("—")
        self.pixel_pitch_value.setText("—")
        self.error_label.setText(f"⚠ {msg}")
        self.error_label.setVisible(True)

    def _collect_export_data(self) -> ExportData:
        """Gather current state into an ExportData."""
        sensor_text = self.sensor_combo.currentText()
        sensor_id = self.sensor_combo.currentData()
        lens_text = self.lens_combo.currentText() if self.lens_combo.isEnabled() else ""
        return ExportData(
            calculator_name="Ground Sample Distance (GSD)",
            calculator_slug="gsd",
            sensor_label=sensor_text,
            sensor_slug=sensor_id or "manual_entry",
            sensor_category="Camera",
            configuration_label=lens_text,
            inputs=[
                ("Sensor Width", f"{self.sensor_width_spin.value():.2f} mm"),
                ("Image Width", f"{self.image_width_spin.value()} px"),
                ("Focal Length", f"{self.focal_length_spin.value():.1f} mm"),
                ("AGL (Height)", f"{self.agl_spin.value():.1f} m"),
            ],
            results=[
                ("GSD", f"{self.gsd_value.text()} m/px"),
                ("GSD", f"{self.gsd_cm_value.text()} cm/px"),
                ("Pixel Pitch", f"{self.pixel_pitch_value.text()} mm"),
            ],
            math_formula=_GSD_MATH,
            assumptions=_GSD_ASSUMPTIONS,
            references=_GSD_REFERENCES,
        )

    def _on_export(self, fmt: str):
        _do_export(self, self._collect_export_data(), fmt)


# ═══════════════════════════════════════════════════════════════════════════
#  Horizontal Error Tab
# ═══════════════════════════════════════════════════════════════════════════


class HorizontalErrorTab(QWidget):
    """ASPRS Horizontal Error (RMSE_H) calculator tab."""

    def __init__(self, manager: SensorManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._build_ui()
        self._connect_signals()
        self.manager.data_changed.connect(self._refresh_sensors)

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Sensor picker ──
        layout.addWidget(_make_section_label("SENSOR"))
        picker_group = QGroupBox()
        picker_group.setObjectName("calc_group")
        picker_layout = QFormLayout(picker_group)
        picker_layout.setSpacing(10)

        self.sensor_combo = QComboBox()
        self.sensor_combo.setMinimumWidth(280)
        picker_layout.addRow("POS / INS:", self.sensor_combo)

        layout.addWidget(picker_group)

        # ── Input form ──
        layout.addWidget(_make_section_label("PARAMETERS"))
        input_group = QGroupBox()
        input_group.setObjectName("calc_group")
        input_layout = QFormLayout(input_group)
        input_layout.setSpacing(10)

        self.gnss_spin = _make_double_spin(0, 100, 4, "m")
        self.rp_spin = _make_double_spin(0, 10, 4, "°")
        self.hdg_spin = _make_double_spin(0, 10, 4, "°")
        self.fh_spin = _make_double_spin(0, 20000, 1, "m")

        input_layout.addRow("GNSS Positional Error:", self.gnss_spin)
        input_layout.addRow("Roll/Pitch Accuracy:", self.rp_spin)
        input_layout.addRow("Heading Accuracy:", self.hdg_spin)
        input_layout.addRow("Flying Height:", self.fh_spin)

        layout.addWidget(input_group)

        # ── Error ──
        self.error_label = _make_error_label()
        layout.addWidget(self.error_label)

        # ── Results ──
        layout.addWidget(_make_section_label("RESULTS"))
        results_row = QHBoxLayout()
        results_row.setSpacing(12)

        card, self.rmse_value = _make_result_card("Horizontal Error (RMSE_H)", "m")
        results_row.addWidget(card)
        card, self.rmse_cm_value = _make_result_card("RMSE_H", "cm")
        results_row.addWidget(card)

        layout.addLayout(results_row)

        # ── Export ──
        export_row, self.export_btn = _make_export_row()
        layout.addWidget(export_row)

        # ── Assumptions & References ──
        layout.addWidget(_make_section_label("INFO"))
        layout.addWidget(_make_info_section(
            _HERR_ASSUMPTIONS, _HERR_MATH, _HERR_REFERENCES,
        ))

        layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._refresh_sensors()

    def _connect_signals(self):
        self.sensor_combo.currentIndexChanged.connect(self._on_sensor_changed)
        for spin in (self.gnss_spin, self.rp_spin, self.hdg_spin, self.fh_spin):
            spin.valueChanged.connect(self._recompute)
        # Export menu
        menu = QMenu(self)
        menu.addAction("Export as TXT…", lambda: self._on_export("txt"))
        menu.addAction("Export as HTML…", lambda: self._on_export("html"))
        self.export_btn.setMenu(menu)

    # ── Sensor population ────────────────────────────────────

    def _refresh_sensors(self):
        self.sensor_combo.blockSignals(True)
        self.sensor_combo.clear()
        self.sensor_combo.addItem(_MANUAL_ENTRY, None)
        for mod in self.manager.get_modules("pos_modules"):
            label = self.manager.get_display_name(mod)
            self.sensor_combo.addItem(label, mod.get("id"))
        self.sensor_combo.blockSignals(False)
        self._on_sensor_changed()

    def _on_sensor_changed(self):
        sensor_id = self.sensor_combo.currentData()
        if sensor_id is None:
            # Manual entry
            self.gnss_spin.setValue(0)
            self.rp_spin.setValue(0)
            self.hdg_spin.setValue(0)
        else:
            mod = self.manager.get_module_by_id("pos_modules", sensor_id)
            if mod:
                self.gnss_spin.setValue(mod.get("position_accuracy_h_m", 0) or 0)
                self.rp_spin.setValue(mod.get("pitch_roll_accuracy_deg", 0) or 0)
                self.hdg_spin.setValue(mod.get("heading_accuracy_deg", 0) or 0)
        self._recompute()

    # ── Compute ──────────────────────────────────────────────

    def _recompute(self):
        self.error_label.setVisible(False)
        try:
            inputs = HorizontalErrorInputs(
                gnss_error_m=self.gnss_spin.value(),
                imu_roll_pitch_error_deg=self.rp_spin.value(),
                imu_heading_error_deg=self.hdg_spin.value(),
                flying_height_m=self.fh_spin.value(),
            )
            result = calculate_horizontal_error(inputs)
            self.rmse_value.setText(f"{result.rmse_h_m:.4f}")
            self.rmse_cm_value.setText(f"{result.rmse_h_m * 100:.2f}")
        except (ValueError, ZeroDivisionError) as e:
            self._show_error(str(e))

    def _show_error(self, msg: str):
        self.rmse_value.setText("—")
        self.rmse_cm_value.setText("—")
        self.error_label.setText(f"⚠ {msg}")
        self.error_label.setVisible(True)

    def _collect_export_data(self) -> ExportData:
        """Gather current state into an ExportData."""
        sensor_text = self.sensor_combo.currentText()
        sensor_id = self.sensor_combo.currentData()
        return ExportData(
            calculator_name="Horizontal Error (RMSE_H)",
            calculator_slug="rmse_h",
            sensor_label=sensor_text,
            sensor_slug=sensor_id or "manual_entry",
            sensor_category="POS / INS",
            inputs=[
                ("GNSS Positional Error", f"{self.gnss_spin.value():.4f} m"),
                ("Roll/Pitch Accuracy", f"{self.rp_spin.value():.4f}°"),
                ("Heading Accuracy", f"{self.hdg_spin.value():.4f}°"),
                ("Flying Height", f"{self.fh_spin.value():.1f} m"),
            ],
            results=[
                ("RMSE_H", f"{self.rmse_value.text()} m"),
                ("RMSE_H", f"{self.rmse_cm_value.text()} cm"),
            ],
            math_formula=_HERR_MATH,
            assumptions=_HERR_ASSUMPTIONS,
            references=_HERR_REFERENCES,
        )

    def _on_export(self, fmt: str):
        _do_export(self, self._collect_export_data(), fmt)


# ═══════════════════════════════════════════════════════════════════════════
#  Main Calculator Panel (container for all tabs)
# ═══════════════════════════════════════════════════════════════════════════


class CalculatorPanel(QWidget):
    """Tabbed container for all calculator tools."""

    def __init__(self, manager: SensorManager, parent=None):
        super().__init__(parent)
        self.setObjectName("calculator_panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("calc_header")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 18, 24, 14)

        title = QLabel("Calculators")
        title.setObjectName("detail_title")
        header_layout.addWidget(title)

        subtitle = QLabel(
            "Estimate point density, ground sample distance, "
            "and horizontal accuracy from sensor specs and flight parameters."
        )
        subtitle.setObjectName("detail_subtitle")
        subtitle.setWordWrap(True)
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("calc_tabs")
        self.tabs.setDocumentMode(True)

        self.npd_tab = NpdTab(manager)
        self.gsd_tab = GsdTab(manager)
        self.herr_tab = HorizontalErrorTab(manager)

        self.tabs.addTab(self.npd_tab, "📡  Point Density (NPD)")
        self.tabs.addTab(self.gsd_tab, "📷  Ground Sample Distance")
        self.tabs.addTab(self.herr_tab, "🎯  Horizontal Error")

        layout.addWidget(self.tabs)
