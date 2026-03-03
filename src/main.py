"""
2SP LiDAR Calculator — Application entry point.
"""

import sys
from pathlib import Path

from loguru import logger
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

# Ensure src/ is importable when running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ui.main_window import MainWindow
from src.ui.styles import get_stylesheet


def _load_fonts(app: QApplication) -> None:
    """Set up application fonts."""
    # Use Outfit if available, then platform-native sans-serif
    if QFontDatabase.hasFamily("Outfit"):
        default_font = QFont("Outfit", 13)
    elif QFontDatabase.hasFamily("Segoe UI"):  # Windows
        default_font = QFont("Segoe UI", 13)
    elif QFontDatabase.hasFamily("Helvetica Neue"):  # macOS
        default_font = QFont("Helvetica Neue", 13)
    else:
        default_font = QFont("sans-serif", 13)
    app.setFont(default_font)


def main():
    """Launch the 2SP LiDAR Calculator application."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | {message}",
    )

    logger.info("Starting 2SP LiDAR Calculator v0.1.0")

    # Qt6 enables high-DPI scaling automatically
    app = QApplication(sys.argv)
    app.setApplicationName("2SP LiDAR Calculator")
    app.setOrganizationName("2SP")

    # Load fonts and apply theme
    _load_fonts(app)
    app.setStyleSheet(get_stylesheet())

    # Create and show main window
    window = MainWindow()
    window.show()

    logger.info("Application ready")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
