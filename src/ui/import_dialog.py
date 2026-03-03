"""
Import library dialog — shows import preview and handles conflict resolution.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.data.library_io import (
    CONFLICT_COPY,
    CONFLICT_REPLACE,
    CONFLICT_REPLACE_ALL,
    CONFLICT_SKIP,
    CONFLICT_SKIP_ALL,
    ImportPlan,
)
from src.data.sensor_manager import CATEGORY_LABELS
from src.ui.styles import COLORS


class ImportPreviewDialog(QDialog):
    """
    Shows what will be imported and lets the user resolve conflicts.

    After exec(), call get_resolutions() to retrieve the conflict
    resolution dict keyed by module ID.
    """

    def __init__(self, plan: ImportPlan, parent=None):
        super().__init__(parent)
        self.plan = plan
        self._conflict_groups: dict[str, QButtonGroup] = {}
        self._bulk_action: str | None = None

        self.setWindowTitle("Import Sensor Library")
        self.setMinimumWidth(560)
        self.setMinimumHeight(400)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Header ──
        header = QLabel("Import Preview")
        header.setObjectName("dialog_title")
        layout.addWidget(header)

        summary = QLabel(self.plan.summary)
        summary.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(summary)

        # ── Scrollable content ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        scroll_layout.setContentsMargins(0, 8, 0, 0)

        # ── New entries ──
        if self.plan.to_add:
            group = self._make_section(
                "✅  New Entries",
                f"{len(self.plan.to_add)} sensor(s) will be added to your library.",
                COLORS["cat_camera"],
            )
            group_layout = group.layout()
            for cat, module in self.plan.to_add:
                name = _module_display(module)
                cat_label = CATEGORY_LABELS.get(cat, cat)
                entry = QLabel(f"  •  {name}  ({cat_label})")
                entry.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; padding: 1px 0;")
                group_layout.addWidget(entry)
            scroll_layout.addWidget(group)

        # ── Identical (skipped) ──
        if self.plan.identical:
            group = self._make_section(
                "⏭️  Already in Library",
                f"{len(self.plan.identical)} identical sensor(s) will be skipped.",
                COLORS["text_tertiary"],
            )
            scroll_layout.addWidget(group)

        # ── Conflicts ──
        if self.plan.conflicts:
            conflict_header = self._make_section(
                "⚠️  Conflicts",
                f"{len(self.plan.conflicts)} sensor(s) already exist with different data.",
                "#B07020",
            )
            conflict_layout = conflict_header.layout()

            # Bulk action row
            if len(self.plan.conflicts) > 1:
                bulk_row = QWidget()
                bulk_layout = QHBoxLayout(bulk_row)
                bulk_layout.setContentsMargins(4, 4, 4, 8)
                bulk_layout.setSpacing(8)

                bulk_label = QLabel("Apply to all:")
                bulk_label.setStyleSheet(
                    f"font-size: 12px; font-weight: 600; color: {COLORS['text_secondary']};"
                )
                bulk_layout.addWidget(bulk_label)

                skip_all_btn = _action_button("Skip All")
                skip_all_btn.clicked.connect(lambda: self._apply_bulk(CONFLICT_SKIP_ALL))
                bulk_layout.addWidget(skip_all_btn)

                replace_all_btn = _action_button("Replace All")
                replace_all_btn.clicked.connect(lambda: self._apply_bulk(CONFLICT_REPLACE_ALL))
                bulk_layout.addWidget(replace_all_btn)

                bulk_layout.addStretch()
                conflict_layout.addWidget(bulk_row)

            # Per-conflict cards
            for cat, incoming, existing in self.plan.conflicts:
                card = self._make_conflict_card(cat, incoming, existing)
                conflict_layout.addWidget(card)

            scroll_layout.addWidget(conflict_header)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)

        # ── Footer buttons ──
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 0)
        footer_layout.addStretch()

        from PySide6.QtWidgets import QPushButton

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("btn_cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(cancel_btn)

        import_btn = QPushButton("Import")
        import_btn.setObjectName("btn_save")
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(self.accept)
        footer_layout.addWidget(import_btn)

        layout.addWidget(footer)

    def _make_section(self, title: str, subtitle: str, color: str) -> QGroupBox:
        """Create a styled section group box."""
        group = QGroupBox()
        group.setObjectName("form_group")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {color}; border: none;"
        )
        group_layout.addWidget(title_label)

        sub_label = QLabel(subtitle)
        sub_label.setStyleSheet(
            f"font-size: 12px; color: {COLORS['text_secondary']}; border: none;"
        )
        sub_label.setWordWrap(True)
        group_layout.addWidget(sub_label)

        return group

    def _make_conflict_card(self, cat: str, incoming: dict, existing: dict) -> QWidget:
        """Build a single conflict resolution card."""
        mid = incoming.get("id", "?")
        name = _module_display(incoming)
        cat_label = CATEGORY_LABELS.get(cat, cat)

        card = QWidget()
        card.setStyleSheet(
            f"""
            QWidget {{
                background-color: #FDF8F0;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
            """
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)

        # Module name + category
        name_label = QLabel(f"{name}  ·  {cat_label}")
        name_label.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {COLORS['text_primary']}; border: none;"
        )
        card_layout.addWidget(name_label)

        # Diff summary — show first N differing keys
        diff_keys = _diff_keys(existing, incoming)
        if diff_keys:
            diff_text = ", ".join(diff_keys[:5])
            if len(diff_keys) > 5:
                diff_text += f" (+{len(diff_keys) - 5} more)"
            diff_label = QLabel(f"Differs in: {diff_text}")
            diff_label.setStyleSheet(
                f"font-size: 11px; color: {COLORS['text_tertiary']}; border: none;"
            )
            diff_label.setWordWrap(True)
            card_layout.addWidget(diff_label)

        # Radio buttons for resolution
        radio_row = QWidget()
        radio_layout = QHBoxLayout(radio_row)
        radio_layout.setContentsMargins(0, 4, 0, 0)
        radio_layout.setSpacing(16)

        btn_group = QButtonGroup(self)
        for label, action in [
            ("Skip", CONFLICT_SKIP),
            ("Replace", CONFLICT_REPLACE),
            ("Import as Copy", CONFLICT_COPY),
        ]:
            radio = QRadioButton(label)
            radio.setStyleSheet(
                f"font-size: 12px; color: {COLORS['text_primary']}; border: none;"
            )
            radio.setProperty("action", action)
            btn_group.addButton(radio)
            radio_layout.addWidget(radio)
            if action == CONFLICT_SKIP:
                radio.setChecked(True)  # default

        radio_layout.addStretch()
        card_layout.addWidget(radio_row)

        self._conflict_groups[mid] = btn_group

        return card

    def _apply_bulk(self, action: str):
        """Set all conflict radio buttons to the given bulk action."""
        target = CONFLICT_SKIP if action == CONFLICT_SKIP_ALL else CONFLICT_REPLACE
        self._bulk_action = action

        for mid, btn_group in self._conflict_groups.items():
            for radio in btn_group.buttons():
                if radio.property("action") == target:
                    radio.setChecked(True)
                    break

    def get_resolutions(self) -> dict[str, str]:
        """
        Return a dict mapping conflict module IDs to the chosen action.

        Call this after exec() returns Accepted.
        """
        resolutions = {}
        for mid, btn_group in self._conflict_groups.items():
            checked = btn_group.checkedButton()
            if checked:
                resolutions[mid] = checked.property("action")
            else:
                resolutions[mid] = CONFLICT_SKIP  # fallback
        return resolutions


class ImportSummaryDialog(QDialog):
    """Simple dialog showing the results of an import operation."""

    def __init__(self, counts: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Complete")
        self.setMinimumWidth(380)
        self._build_ui(counts)

    def _build_ui(self, counts: dict):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        # Icon + title
        title = QLabel("✅  Import Complete")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: 700; color: {COLORS['text_primary']};"
        )
        layout.addWidget(title)

        # Counts
        total_imported = counts["added"] + counts["replaced"] + counts["copied"]
        lines = []
        if counts["added"]:
            lines.append(f"  •  {counts['added']} new sensor(s) added")
        if counts["replaced"]:
            lines.append(f"  •  {counts['replaced']} sensor(s) replaced")
        if counts["copied"]:
            lines.append(f"  •  {counts['copied']} sensor(s) imported as copies")
        if counts["skipped"]:
            lines.append(f"  •  {counts['skipped']} sensor(s) skipped")

        if not lines:
            lines.append("  No changes were made.")

        for line in lines:
            lbl = QLabel(line)
            lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']};")
            layout.addWidget(lbl)

        layout.addSpacing(8)

        # OK button
        from PySide6.QtWidgets import QPushButton

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("btn_save")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setFixedWidth(80)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)


# ── Helpers ──────────────────────────────────────────────────────────────


def _module_display(module: dict) -> str:
    """Return a readable name for a module dict."""
    manufacturer = module.get("manufacturer", "")
    model = module.get("model", module.get("system_name", "Unknown"))
    return f"{manufacturer} {model}".strip()


def _diff_keys(a: dict, b: dict) -> list[str]:
    """Return a list of top-level keys where a and b differ."""
    all_keys = set(a.keys()) | set(b.keys())
    diffs = []
    for key in sorted(all_keys):
        if key == "id":
            continue  # IDs match by definition in a conflict
        if a.get(key) != b.get(key):
            diffs.append(key)
    return diffs


def _action_button(text: str):
    """Create a small styled button for bulk actions."""
    from PySide6.QtWidgets import QPushButton

    btn = QPushButton(text)
    btn.setObjectName("action_btn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedHeight(26)
    return btn
