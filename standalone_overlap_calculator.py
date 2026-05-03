import sys
import math
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QDoubleSpinBox, QSlider, QRadioButton, QGroupBox, QFrame
)

class SliderSpinBox(QWidget):
    """A custom widget combining a QSlider and QDoubleSpinBox for easy interactive input."""
    valueChanged = Signal(float)
    
    def __init__(self, label_text, min_val, max_val, decimals=1, suffix=""):
        super().__init__()
        self.decimals = decimals
        self.multiplier = 10 ** decimals
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(label_text)
        self.label.setMinimumWidth(110)
        self.label.setStyleSheet("font-weight: 500; font-size: 13px;")
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(int(min_val * self.multiplier))
        self.slider.setMaximum(int(max_val * self.multiplier))
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setMinimum(min_val)
        self.spinbox.setMaximum(max_val)
        self.spinbox.setDecimals(decimals)
        self.spinbox.setSuffix(suffix)
        self.spinbox.setMinimumWidth(100)
        self.spinbox.setStyleSheet("padding: 4px; font-size: 13px;")
        
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        layout.addWidget(self.spinbox)
        
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)

    def _on_slider_changed(self, val):
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(val / self.multiplier)
        self.spinbox.blockSignals(False)
        self.valueChanged.emit(self.spinbox.value())
        
    def _on_spinbox_changed(self, val):
        self.slider.blockSignals(True)
        self.slider.setValue(int(val * self.multiplier))
        self.slider.blockSignals(False)
        self.valueChanged.emit(val)
        
    def set_value(self, val):
        self.spinbox.setValue(val)
        
    def value(self):
        return self.spinbox.value()
        
    def set_range(self, min_val, max_val):
        self.spinbox.setMinimum(min_val)
        self.spinbox.setMaximum(max_val)
        self.slider.setMinimum(int(min_val * self.multiplier))
        self.slider.setMaximum(int(max_val * self.multiplier))

    def set_suffix(self, suffix):
        self.spinbox.setSuffix(suffix)

class OverlapCalculatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone LiDAR Flight Overlap Calculator")
        self.setMinimumSize(600, 550)
        
        self.is_metric = True  # True for Meters, False for Feet
        self.FT_TO_M = 0.3048
        
        self._build_ui()
        self._connect_signals()
        self._update_visibility()
        self._recalculate()
        
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # --- Top: Unit Selection ---
        unit_group = QGroupBox("Measurement Unit")
        unit_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #bdc3c7; border-radius: 6px; margin-top: 16px; padding-top: 8px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 10px; padding: 0 3px; }")
        unit_layout = QHBoxLayout(unit_group)
        self.radio_meter = QRadioButton("Meters (m)")
        self.radio_meter.setChecked(True)
        self.radio_foot = QRadioButton("Feet (ft)")
        unit_layout.addWidget(self.radio_meter)
        unit_layout.addWidget(self.radio_foot)
        unit_layout.addStretch()
        main_layout.addWidget(unit_group)
        
        # --- Target Selector ---
        target_layout = QHBoxLayout()
        target_label = QLabel("<b>What do you want to calculate?</b>")
        target_label.setStyleSheet("font-size: 14px;")
        self.target_combo = QComboBox()
        self.target_combo.addItems([
            "Overlap Percentage (%)",
            "Flight Line Spacing",
            "Flight Altitude (AGL)",
            "Sensor FOV"
        ])
        self.target_combo.setStyleSheet("padding: 4px 12px; font-size: 13px; font-weight: bold;")
        self.target_combo.setMinimumWidth(200)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_combo)
        target_layout.addStretch()
        main_layout.addLayout(target_layout)
        
        # --- Input Sliders ---
        self.inputs_group = QGroupBox("Input Parameters")
        self.inputs_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #bdc3c7; border-radius: 6px; margin-top: 16px; padding-top: 8px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 10px; padding: 0 3px; }")
        inputs_layout = QVBoxLayout(self.inputs_group)
        inputs_layout.setSpacing(15)
        
        self.fov_input = SliderSpinBox("Sensor FOV:", 10.0, 180.0, decimals=1, suffix=" °")
        self.fov_input.set_value(90.0)
        
        self.alt_input = SliderSpinBox("Altitude (AGL):", 5.0, 1000.0, decimals=1, suffix=" m")
        self.alt_input.set_value(50.0)
        
        self.spacing_input = SliderSpinBox("Line Spacing:", 1.0, 1000.0, decimals=1, suffix=" m")
        self.spacing_input.set_value(30.0)
        
        self.overlap_input = SliderSpinBox("Target Overlap:", 0.0, 99.0, decimals=1, suffix=" %")
        self.overlap_input.set_value(50.0)
        
        self.feature_height_input = SliderSpinBox("Feature Height:", 0.0, 500.0, decimals=1, suffix=" m")
        self.feature_height_input.set_value(0.0)
        
        inputs_layout.addWidget(self.fov_input)
        inputs_layout.addWidget(self.alt_input)
        inputs_layout.addWidget(self.spacing_input)
        inputs_layout.addWidget(self.overlap_input)
        inputs_layout.addWidget(self.feature_height_input)
        
        main_layout.addWidget(self.inputs_group)
        
        # --- Result Display ---
        self.result_frame = QFrame()
        self.result_frame.setStyleSheet("""
            QFrame {
                background-color: #2C2C2E;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        result_layout = QVBoxLayout(self.result_frame)
        self.result_title = QLabel("Calculated Overlap Percentage")
        self.result_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_title.setStyleSheet("font-size: 14px; color: #E6E2DB;")
        
        self.result_value = QLabel("0.0 %")
        self.result_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_value.setStyleSheet("font-size: 44px; font-weight: bold; color: #FFD700;")
        
        self.secondary_result_title = QLabel("Ground Overlap (Bare Earth)")
        self.secondary_result_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.secondary_result_title.setStyleSheet("font-size: 13px; color: #95a5a6; margin-top: 15px;")
        
        self.secondary_result_value = QLabel("0.0 %")
        self.secondary_result_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.secondary_result_value.setStyleSheet("font-size: 26px; font-weight: bold; color: #bdc3c7;")
        
        result_layout.addWidget(self.result_title)
        result_layout.addWidget(self.result_value)
        result_layout.addWidget(self.secondary_result_title)
        result_layout.addWidget(self.secondary_result_value)
        main_layout.addWidget(self.result_frame)
        
        main_layout.addStretch()
        
    def _connect_signals(self):
        self.radio_meter.toggled.connect(self._on_unit_toggled)
        self.target_combo.currentIndexChanged.connect(self._on_target_changed)
        
        self.fov_input.valueChanged.connect(self._recalculate)
        self.alt_input.valueChanged.connect(self._recalculate)
        self.spacing_input.valueChanged.connect(self._recalculate)
        self.overlap_input.valueChanged.connect(self._recalculate)
        self.feature_height_input.valueChanged.connect(self._recalculate)
        
    def _on_unit_toggled(self):
        was_metric = self.is_metric
        self.is_metric = self.radio_meter.isChecked()
        
        if was_metric == self.is_metric:
            return
            
        suffix = " m" if self.is_metric else " ft"
        self.alt_input.set_suffix(suffix)
        self.spacing_input.set_suffix(suffix)
        self.feature_height_input.set_suffix(suffix)
        
        # Convert ranges and current values
        self.alt_input.blockSignals(True)
        self.spacing_input.blockSignals(True)
        self.feature_height_input.blockSignals(True)
        
        if self.is_metric:
            self.alt_input.set_range(5.0, 1000.0)
            self.alt_input.set_value(self.alt_input.value() * self.FT_TO_M)
            self.spacing_input.set_range(1.0, 1000.0)
            self.spacing_input.set_value(self.spacing_input.value() * self.FT_TO_M)
            self.feature_height_input.set_range(0.0, 500.0)
            self.feature_height_input.set_value(self.feature_height_input.value() * self.FT_TO_M)
        else:
            self.alt_input.set_range(15.0, 3000.0)
            self.alt_input.set_value(self.alt_input.value() / self.FT_TO_M)
            self.spacing_input.set_range(3.0, 3000.0)
            self.spacing_input.set_value(self.spacing_input.value() / self.FT_TO_M)
            self.feature_height_input.set_range(0.0, 1500.0)
            self.feature_height_input.set_value(self.feature_height_input.value() / self.FT_TO_M)
            
        self.alt_input.blockSignals(False)
        self.spacing_input.blockSignals(False)
        self.feature_height_input.blockSignals(False)
        self._recalculate()
        
    def _on_target_changed(self):
        self._update_visibility()
        self._recalculate()
        
    def _update_visibility(self):
        idx = self.target_combo.currentIndex()
        self.overlap_input.setVisible(idx != 0)
        self.spacing_input.setVisible(idx != 1)
        self.alt_input.setVisible(idx != 2)
        self.fov_input.setVisible(idx != 3)
        
        titles = [
            "Calculated Safety Overlap (At Canopy)",
            "Required Line Spacing",
            "Required Altitude (AGL)",
            "Required Sensor FOV"
        ]
        self.result_title.setText(titles[idx])
        
    def _get_w(self, alt, fov_deg):
        fov_rad = math.radians(fov_deg)
        return 2 * alt * math.tan(fov_rad / 2)
        
    def _recalculate(self):
        idx = self.target_combo.currentIndex()
        
        fov = self.fov_input.value()
        alt = self.alt_input.value()
        spacing = self.spacing_input.value()
        overlap = self.overlap_input.value()
        feat_h = self.feature_height_input.value()
        
        eff_alt = max(0.0, alt - feat_h)
        unit_str = "m" if self.is_metric else "ft"
        
        try:
            if idx == 0:  # Solve Overlap
                W_safe = self._get_w(eff_alt, fov)
                if W_safe == 0: val = 0.0
                else: val = max(0.0, (1 - spacing / W_safe) * 100)
                self.result_value.setText(f"{val:.1f} %")
                final_fov, final_alt, final_spacing = fov, alt, spacing
                
            elif idx == 1:  # Solve Spacing
                W_safe = self._get_w(eff_alt, fov)
                val = max(0.0, W_safe * (1 - overlap / 100))
                self.result_value.setText(f"{val:.1f} {unit_str}")
                final_fov, final_alt, final_spacing = fov, alt, val
                
            elif idx == 2:  # Solve Altitude
                if overlap >= 100: val = float('inf')
                else:
                    W_safe = spacing / (1 - overlap / 100)
                    fov_rad = math.radians(fov)
                    if fov_rad == 0: val = float('inf')
                    else: 
                        safe_agl = max(0.0, W_safe / (2 * math.tan(fov_rad / 2)))
                        val = safe_agl + feat_h
                if val == float('inf'):
                    self.result_value.setText("Impossible")
                    final_fov, final_alt, final_spacing = fov, float('inf'), spacing
                else:
                    self.result_value.setText(f"{val:.1f} {unit_str}")
                    final_fov, final_alt, final_spacing = fov, val, spacing
                    
            elif idx == 3:  # Solve FOV
                if overlap >= 100 or eff_alt <= 0: val = 180.0
                else:
                    W_safe = spacing / (1 - overlap / 100)
                    if W_safe / (2 * eff_alt) > 1000: # Effectively near 180 deg
                        val = 180.0
                    else:
                        fov_rad = 2 * math.atan(W_safe / (2 * eff_alt))
                        val = math.degrees(fov_rad)
                self.result_value.setText(f"{val:.1f} °")
                final_fov, final_alt, final_spacing = val, alt, spacing
                
            if feat_h > 0 and final_alt != float('inf'):
                self.secondary_result_title.setVisible(True)
                self.secondary_result_value.setVisible(True)
                W_ground = self._get_w(final_alt, final_fov)
                if W_ground == 0: ground_ov = 0.0
                else: ground_ov = max(0.0, (1 - final_spacing / W_ground) * 100)
                self.secondary_result_value.setText(f"{ground_ov:.1f} %")
            else:
                self.secondary_result_title.setVisible(False)
                self.secondary_result_value.setVisible(False)
                
        except Exception as e:
            self.result_value.setText("Error")
            self.secondary_result_value.setText("")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Optional: Basic app styling for buttons and sliders
    app.setStyleSheet("""
        QSlider::groove:horizontal { border: 1px solid #999999; height: 6px; background: #dfe6e9; margin: 2px 0; border-radius: 3px; }
        QSlider::handle:horizontal { background: #0984e3; border: 1px solid #0984e3; width: 16px; margin: -5px 0; border-radius: 8px; }
        QSlider::handle:horizontal:hover { background: #74b9ff; }
    """)
    
    window = OverlapCalculatorApp()
    window.show()
    sys.exit(app.exec())
