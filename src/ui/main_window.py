"""
Main application window with sidebar navigation and content panels.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.data.sensor_manager import SensorManager
from src.ui.calculator_panel import CalculatorPanel
from src.ui.sensor_browser import SensorBrowser
from src.ui.sensor_detail import SensorDetail
from src.ui.styles import COLORS


class MainWindow(QMainWindow):
    """Main application window."""

    # Page indices for QStackedWidget
    PAGE_LIBRARY = 0
    PAGE_CALCULATORS = 1

    def __init__(self):
        super().__init__()

        self.setWindowTitle("2SP LiDAR Calculator")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)

        # Load sensor data
        self.manager = SensorManager()

        # Validate on startup
        warnings = self.manager.validate()
        for w in warnings:
            from loguru import logger
            logger.warning(f"Sensor DB: {w}")

        self._nav_buttons: list[QPushButton] = []
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──
        sidebar = self._build_sidebar()
        main_layout.addWidget(sidebar)

        # ── Content area (stacked pages) ──
        self.stack = QStackedWidget()

        # ── Page 0: Sensor Library ──
        library_page = QWidget()
        library_layout = QVBoxLayout(library_page)
        library_layout.setContentsMargins(0, 0, 0, 0)
        library_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLORS['border']};
            }}
        """)

        self.browser = SensorBrowser(self.manager)
        self.splitter.addWidget(self.browser)

        self.detail = SensorDetail(self.manager)
        self.splitter.addWidget(self.detail)

        self.splitter.setSizes([350, 750])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        library_layout.addWidget(self.splitter)
        self.stack.addWidget(library_page)

        # ── Page 1: Calculators ──
        self.calc_panel = CalculatorPanel(self.manager)
        self.stack.addWidget(self.calc_panel)

        main_layout.addWidget(self.stack, stretch=1)

        # ── Connect signals ──
        self.browser.sensor_selected.connect(self.detail.show_sensor)
        self.manager.data_changed.connect(self._refresh_status_bar)

        # ── Status bar ──
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._refresh_status_bar()

        # Start on Sensor Library page
        self._switch_page(self.PAGE_LIBRARY)

    def _switch_page(self, index: int):
        """Switch the stacked widget to the given page index."""
        self.stack.setCurrentIndex(index)
        # Update sidebar active state
        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("active", i == index)
            # Force style re-evaluation
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._refresh_status_bar()

    def _refresh_status_bar(self):
        """Update the status bar based on the active page."""
        if self.stack.currentIndex() == self.PAGE_LIBRARY:
            total_sensors = sum(
                len(self.manager.get_modules(cat))
                for cat in ("lidar_modules", "camera_modules",
                            "pos_modules", "mapping_systems")
            )
            self.status.showMessage(
                f"Sensor Library  ·  {total_sensors} entries loaded"
            )
        else:
            self.status.showMessage("Calculators  ·  Real-time estimation mode")

    def _build_sidebar(self) -> QWidget:
        """Build the dark sidebar with navigation."""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Brand
        title = QLabel("LiDAR Calculator")
        title.setObjectName("sidebar_title")
        layout.addWidget(title)

        subtitle = QLabel("2SP Professional Tools")
        subtitle.setObjectName("sidebar_subtitle")
        layout.addWidget(subtitle)

        # Navigation buttons — (label, page_index or None for disabled)
        nav_items = [
            ("📡  Sensor Library", self.PAGE_LIBRARY),
            ("📐  Calculators", self.PAGE_CALCULATORS),
            ("⚙️  Settings", None),
        ]

        for label, page_index in nav_items:
            btn = QPushButton(label)
            enabled = page_index is not None
            btn.setCursor(
                Qt.CursorShape.PointingHandCursor if enabled
                else Qt.CursorShape.ForbiddenCursor
            )
            btn.setEnabled(enabled)
            if not enabled:
                btn.setToolTip("Coming soon")
                btn.setStyleSheet("color: rgba(255, 255, 255, 0.25);")
            else:
                btn.clicked.connect(
                    lambda checked, idx=page_index: self._switch_page(idx)
                )
            layout.addWidget(btn)
            self._nav_buttons.append(btn)

        layout.addStretch()

        # Version label at bottom
        version_label = QLabel("v0.1.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet(f"""
            color: {COLORS['text_tertiary']};
            font-size: 10px;
            padding: 12px;
        """)
        layout.addWidget(version_label)

        return sidebar
