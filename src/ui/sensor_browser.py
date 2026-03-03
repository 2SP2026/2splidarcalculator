"""
Sensor library browser — left panel with category tabs and sensor list.
"""

import json
from pathlib import Path

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.data import library_io
from src.data.sensor_manager import CATEGORIES, CATEGORY_LABELS, SensorManager
from src.ui.import_dialog import ImportPreviewDialog, ImportSummaryDialog
from src.ui.sensor_edit_dialog import SensorEditDialog


class SensorBrowser(QWidget):
    """Category tabs + filterable sensor list with CRUD toolbar."""

    # Emitted when user clicks a sensor: (category, module_id)
    sensor_selected = Signal(str, str)

    def __init__(self, manager: SensorManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._current_category: str = CATEGORIES[0]

        self._build_ui()
        self._populate_list()

        # Auto-refresh when data changes
        self.manager.data_changed.connect(self._on_data_changed)

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

        # ── Action toolbar ──
        toolbar = QWidget()
        toolbar.setObjectName("action_toolbar")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(12, 4, 12, 8)
        tb_layout.setSpacing(6)

        self.add_btn = QPushButton("➕ Add")
        self.add_btn.setObjectName("action_btn")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setToolTip("Add new sensor to this category")
        self.add_btn.clicked.connect(self._on_add)
        tb_layout.addWidget(self.add_btn)

        self.dup_btn = QPushButton("📋 Duplicate")
        self.dup_btn.setObjectName("action_btn")
        self.dup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dup_btn.setToolTip("Duplicate selected sensor as a new entry")
        self.dup_btn.clicked.connect(self._on_duplicate)
        tb_layout.addWidget(self.dup_btn)

        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.setObjectName("action_btn")
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.setToolTip("Edit selected sensor")
        self.edit_btn.clicked.connect(self._on_edit)
        tb_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setObjectName("action_btn_danger")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setToolTip("Delete selected sensor")
        self.delete_btn.clicked.connect(self._on_delete)
        tb_layout.addWidget(self.delete_btn)

        # Spacer between CRUD and library I/O
        spacer = QWidget()
        spacer.setFixedWidth(12)
        tb_layout.addWidget(spacer)

        self.export_btn = QPushButton("⬆ Export")
        self.export_btn.setObjectName("action_btn")
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setToolTip("Export sensor library to .2splib file")
        self.export_btn.clicked.connect(self._on_export)
        tb_layout.addWidget(self.export_btn)

        self.import_btn = QPushButton("⬇ Import")
        self.import_btn.setObjectName("action_btn")
        self.import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.import_btn.setToolTip("Import sensors from a .2splib file")
        self.import_btn.clicked.connect(self._on_import)
        tb_layout.addWidget(self.import_btn)

        tb_layout.addStretch()
        layout.addWidget(toolbar)

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

        # Enable/disable selection-dependent buttons
        has_selection = self.sensor_list.count() > 0
        self.dup_btn.setEnabled(has_selection)
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

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
            self.dup_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return
        self.dup_btn.setEnabled(True)
        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        module_id = current.data(Qt.ItemDataRole.UserRole)
        self.sensor_selected.emit(self._current_category, module_id)

    def _on_data_changed(self):
        """Re-populate the list after data mutations."""
        # Remember selected ID to re-select after refresh
        current = self.sensor_list.currentItem()
        selected_id = current.data(Qt.ItemDataRole.UserRole) if current else None

        self._populate_list()

        # Try to re-select the previously selected item
        if selected_id:
            for i in range(self.sensor_list.count()):
                item = self.sensor_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == selected_id:
                    self.sensor_list.setCurrentRow(i)
                    return

    # ------------------------------------------------------------------
    # CRUD actions
    # ------------------------------------------------------------------

    def _on_add(self):
        """Open dialog to add a new sensor."""
        dlg = SensorEditDialog(
            self.manager, self._current_category, module_id=None, parent=self
        )
        dlg.exec()

    def _on_duplicate(self):
        """Clone the selected sensor into a new add-mode dialog."""
        current = self.sensor_list.currentItem()
        if current is None:
            return
        module_id = current.data(Qt.ItemDataRole.UserRole)
        source = self.manager.get_module_by_id(self._current_category, module_id)
        if source is None:
            return
        # Clone data, strip the ID so a new one is generated on save
        clone = {k: v for k, v in source.items() if k != "id"}
        dlg = SensorEditDialog(
            self.manager, self._current_category,
            module_id=None, clone_data=clone, parent=self,
        )
        dlg.exec()

    def _on_edit(self):
        """Open dialog to edit the selected sensor."""
        current = self.sensor_list.currentItem()
        if current is None:
            return
        module_id = current.data(Qt.ItemDataRole.UserRole)
        dlg = SensorEditDialog(
            self.manager, self._current_category, module_id=module_id, parent=self
        )
        dlg.exec()

    def _on_delete(self):
        """Delete the selected sensor after confirmation."""
        current = self.sensor_list.currentItem()
        if current is None:
            return

        module_id = current.data(Qt.ItemDataRole.UserRole)
        display_name = current.text()

        # Check for mapping system references
        refs = self.manager.get_referencing_systems(self._current_category, module_id)
        if refs:
            ref_list = ", ".join(refs)
            QMessageBox.warning(
                self,
                "Cannot Delete",
                f"'{display_name}' is referenced by mapping system(s):\n{ref_list}\n\n"
                "Remove the reference first, then delete.",
            )
            return

        # Confirm
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete '{display_name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete_module(self._current_category, module_id)

    # ------------------------------------------------------------------
    # Library export / import
    # ------------------------------------------------------------------

    def _on_export(self):
        """Export the library — full or selected — to a .2splib file."""
        current = self.sensor_list.currentItem()

        # Build context menu for export mode
        menu = QMenu(self)
        act_full = menu.addAction("Export Full Library")
        act_selected = menu.addAction("Export Selected Sensor")
        act_selected.setEnabled(current is not None)

        action = menu.exec(self.export_btn.mapToGlobal(
            self.export_btn.rect().bottomLeft()
        ))
        if action is None:
            return

        if action == act_full:
            payload = library_io.export_full_library(self.manager)
            suggested = library_io.suggest_filename("full")
        else:
            module_id = current.data(Qt.ItemDataRole.UserRole)
            display_name = current.text()
            payload = library_io.export_selected(
                self.manager, self._current_category, [module_id]
            )
            suggested = library_io.suggest_filename("selected", display_name)

        # File save dialog
        from PySide6.QtCore import QStandardPaths
        desktop = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DesktopLocation
        )
        default_path = str(Path(desktop) / suggested)

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Sensor Library",
            default_path,
            "2SP Library Files (*.2splib);;All Files (*)",
        )
        if not filepath:
            return

        try:
            library_io.save_to_file(payload, Path(filepath))
            total = sum(
                len(payload.get(cat, [])) for cat in CATEGORIES
            )
            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {total} sensor(s) to:\n{filepath}",
            )
        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(self, "Export Failed", str(e))

    def _on_import(self):
        """Import sensors from a .2splib file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Sensor Library",
            "",
            "2SP Library Files (*.2splib);;JSON Files (*.json);;All Files (*)",
        )
        if not filepath:
            return

        # Load and validate
        try:
            payload = library_io.load_from_file(Path(filepath))
        except (json.JSONDecodeError, ValueError) as e:
            QMessageBox.critical(
                self, "Import Failed",
                f"Could not read library file:\n{e}",
            )
            return
        except Exception as e:
            logger.error(f"Import load failed: {e}")
            QMessageBox.critical(self, "Import Failed", str(e))
            return

        # Analyze
        plan = library_io.ImportPlan(self.manager, payload)

        if not plan.to_add and not plan.conflicts:
            QMessageBox.information(
                self, "Nothing to Import",
                "All sensors in this file are already in your library.",
            )
            return

        # Show preview dialog
        dlg = ImportPreviewDialog(plan, parent=self)
        if dlg.exec() != ImportPreviewDialog.DialogCode.Accepted:
            return

        # Execute import
        resolutions = dlg.get_resolutions()
        counts = library_io.execute_import(self.manager, plan, resolutions)

        # Show summary
        summary_dlg = ImportSummaryDialog(counts, parent=self)
        summary_dlg.exec()
