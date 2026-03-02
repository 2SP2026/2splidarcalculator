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
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.data.sensor_manager import SensorManager
from src.ui.sensor_browser import SensorBrowser
from src.ui.sensor_detail import SensorDetail
from src.ui.styles import COLORS


class MainWindow(QMainWindow):
    """Main application window."""

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

        # ── Content area ──
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # ── Splitter: browser | detail ──
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLORS['border']};
            }}
        """)

        # Browser panel (left)
        self.browser = SensorBrowser(self.manager)
        self.splitter.addWidget(self.browser)

        # Detail panel (right)
        self.detail = SensorDetail(self.manager)
        self.splitter.addWidget(self.detail)

        # Set initial sizes (30% browser, 70% detail)
        self.splitter.setSizes([350, 750])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        content_layout.addWidget(self.splitter)

        main_layout.addWidget(content_area, stretch=1)

        # ── Connect signals ──
        self.browser.sensor_selected.connect(self.detail.show_sensor)
        self.manager.data_changed.connect(self._refresh_status_bar)

        # ── Status bar ──
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._refresh_status_bar()

    def _refresh_status_bar(self):
        """Update the status bar with the current sensor count."""
        total_sensors = sum(
            len(self.manager.get_modules(cat))
            for cat in ("lidar_modules", "camera_modules", "pos_modules", "mapping_systems")
        )
        self.status.showMessage(f"Sensor Library  ·  {total_sensors} entries loaded")

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

        # Navigation buttons
        nav_items = [
            ("📡  Sensor Library", True),
            ("📐  Calculators", False),
            ("⚙️  Settings", False),
        ]

        for label, enabled in nav_items:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ForbiddenCursor)
            btn.setEnabled(enabled)
            if not enabled:
                btn.setToolTip("Coming soon")
                btn.setStyleSheet("color: rgba(255, 255, 255, 0.25);")
            else:
                btn.setProperty("active", True)
            layout.addWidget(btn)

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
