"""
Sensor library browser — left panel with category tabs and sensor list.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.data.sensor_manager import CATEGORIES, CATEGORY_LABELS, SensorManager


class SensorBrowser(QWidget):
    """Category tabs + filterable sensor list."""

    # Emitted when user clicks a sensor: (category, module_id)
    sensor_selected = Signal(str, str)

    def __init__(self, manager: SensorManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._current_category: str = CATEGORIES[0]

        self._build_ui()
        self._populate_list()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Category tab bar ──
        self.category_bar = QWidget()
        self.category_bar.setObjectName("category_bar")
        bar_layout = QHBoxLayout(self.category_bar)
        bar_layout.setContentsMargins(8, 0, 8, 0)
        bar_layout.setSpacing(0)

        self.tab_group = QButtonGroup(self)
        self.tab_group.setExclusive(True)

        self.tab_buttons: dict[str, QPushButton] = {}
        for cat in CATEGORIES:
            btn = QPushButton(CATEGORY_LABELS[cat])
            btn.setCheckable(True)
            btn.setObjectName("category_tab")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.tab_group.addButton(btn)
            self.tab_buttons[cat] = btn
            bar_layout.addWidget(btn)

            # Connect click to category switch
            btn.clicked.connect(lambda checked, c=cat: self._switch_category(c))

        # Set default
        self.tab_buttons[CATEGORIES[0]].setChecked(True)
        bar_layout.addStretch()

        layout.addWidget(self.category_bar)

        # ── Search bar ──
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(12, 10, 12, 6)

        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("search_bar")
        self.search_bar.setPlaceholderText("Search sensors…")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(self._filter_list)
        search_layout.addWidget(self.search_bar)

        layout.addWidget(search_container)

        # ── Sensor list ──
        self.sensor_list = QListWidget()
        self.sensor_list.setObjectName("sensor_list")
        self.sensor_list.currentItemChanged.connect(self._on_item_changed)

        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(12, 6, 12, 12)
        list_layout.addWidget(self.sensor_list)

        layout.addWidget(list_container, stretch=1)

    # ------------------------------------------------------------------
    # Data population
    # ------------------------------------------------------------------

    def _populate_list(self):
        """Fill the list widget with modules from the current category."""
        self.sensor_list.clear()
        filter_text = self.search_bar.text().strip().lower()

        modules = self.manager.get_modules(self._current_category)
        for module in modules:
            display_name = self.manager.get_display_name(module)
            if filter_text and filter_text not in display_name.lower():
                continue

            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, module["id"])
            self.sensor_list.addItem(item)

        # Auto-select first item
        if self.sensor_list.count() > 0:
            self.sensor_list.setCurrentRow(0)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _switch_category(self, category: str):
        self._current_category = category
        self.search_bar.clear()
        self._populate_list()

    def _filter_list(self, text: str):
        self._populate_list()

    def _on_item_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        if current is None:
            return
        module_id = current.data(Qt.ItemDataRole.UserRole)
        self.sensor_selected.emit(self._current_category, module_id)
