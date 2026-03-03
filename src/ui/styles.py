"""
2SP LiDAR Calculator — Application theme and styling.

Light theme with warm, professional aesthetic. Distinctive but easy on the eyes.
Uses Outfit for headings and system monospace for data values.
"""

# -- Color palette ----------------------------------------------------------
# Warm light theme inspired by precision instruments and survey equipment

COLORS = {
    # Base
    "bg_primary": "#FAFAF8",           # Warm off-white
    "bg_secondary": "#F0EDE8",         # Light warm gray
    "bg_tertiary": "#E6E2DB",          # Slightly darker warm gray
    "bg_card": "#FFFFFF",              # Pure white for cards
    "bg_sidebar": "#2C2C2E",          # Dark charcoal sidebar

    # Text
    "text_primary": "#1A1A1A",         # Near-black
    "text_secondary": "#5C5C5C",       # Medium gray
    "text_tertiary": "#8A8A8A",        # Light gray
    "text_on_dark": "#F0EDE8",         # Light text on dark bg
    "text_on_accent": "#1A1A1A",       # Dark text on accent

    # Accent
    "accent": "#D4883C",               # Warm amber/copper
    "accent_light": "#E8A85C",         # Lighter amber
    "accent_subtle": "#F5E6D0",        # Very light peach tint
    "accent_hover": "#C07830",         # Darker amber hover

    # Semantic
    "border": "#D8D4CE",               # Warm border
    "border_light": "#E8E4DE",         # Lighter border
    "divider": "#EAE6E0",             # Divider lines
    "shadow": "rgba(0, 0, 0, 0.06)",  # Subtle shadow
    "highlight_row": "#FDF8F0",        # Row hover highlight

    # Category badges
    "cat_lidar": "#3A7CA5",            # Steel blue
    "cat_camera": "#6B8E4E",           # Olive green
    "cat_pos": "#8B6BAE",             # Muted purple
    "cat_system": "#C07830",           # Copper/amber
}

# Category-specific colors
CATEGORY_COLORS = {
    "lidar_modules": COLORS["cat_lidar"],
    "camera_modules": COLORS["cat_camera"],
    "pos_modules": COLORS["cat_pos"],
    "mapping_systems": COLORS["cat_system"],
}

# -- Fonts ------------------------------------------------------------------

FONTS = {
    "heading": "Outfit",
    "body": "Outfit",
    "mono": "JetBrains Mono, Consolas, SF Mono, Menlo, monospace",
}

# -- Stylesheet -------------------------------------------------------------


def get_stylesheet() -> str:
    """Return the full QSS stylesheet for the application."""
    c = COLORS
    f = FONTS

    return f"""
    /* ── Global ─────────────────────────────────────────────── */
    QMainWindow {{
        background-color: {c['bg_primary']};
    }}

    QWidget {{
        font-family: '{f['body']}', 'Segoe UI', -apple-system, 'Helvetica Neue', sans-serif;
        font-size: 13px;
        color: {c['text_primary']};
    }}

    /* ── Sidebar ────────────────────────────────────────────── */
    #sidebar {{
        background-color: {c['bg_sidebar']};
        border: none;
        min-width: 200px;
        max-width: 200px;
    }}

    #sidebar QLabel#sidebar_title {{
        color: {c['accent']};
        font-size: 14px;
        font-weight: 700;
        padding: 18px 16px 4px 16px;
        font-family: '{f['heading']}', sans-serif;
        letter-spacing: 0.5px;
    }}

    #sidebar QLabel#sidebar_subtitle {{
        color: {c['text_tertiary']};
        font-size: 10px;
        padding: 0px 16px 16px 16px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }}

    #sidebar QPushButton {{
        text-align: left;
        padding: 10px 16px;
        border: none;
        border-radius: 0px;
        color: {c['text_on_dark']};
        font-size: 13px;
        font-weight: 500;
        background: transparent;
    }}

    #sidebar QPushButton:hover {{
        background-color: rgba(255, 255, 255, 0.08);
    }}

    #sidebar QPushButton:checked,
    #sidebar QPushButton[active="true"] {{
        background-color: rgba(212, 136, 60, 0.2);
        color: {c['accent_light']};
        border-left: 3px solid {c['accent']};
    }}

    /* ── Category Tabs ──────────────────────────────────────── */
    #category_bar {{
        background-color: {c['bg_secondary']};
        border-bottom: 1px solid {c['border']};
    }}

    #category_bar QPushButton {{
        padding: 10px 20px;
        border: none;
        border-bottom: 2px solid transparent;
        border-radius: 0px;
        font-size: 12px;
        font-weight: 600;
        color: {c['text_secondary']};
        background: transparent;
        letter-spacing: 0.3px;
    }}

    #category_bar QPushButton:hover {{
        color: {c['text_primary']};
        background-color: rgba(0, 0, 0, 0.03);
    }}

    #category_bar QPushButton:checked {{
        color: {c['accent']};
        border-bottom: 2px solid {c['accent']};
    }}

    /* ── Search Bar ─────────────────────────────────────────── */
    #search_bar {{
        padding: 8px 12px;
        border: 1px solid {c['border']};
        border-radius: 6px;
        background-color: {c['bg_card']};
        font-size: 13px;
        color: {c['text_primary']};
    }}

    #search_bar:focus {{
        border-color: {c['accent']};
    }}

    /* ── Sensor List ────────────────────────────────────────── */
    #sensor_list {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border_light']};
        border-radius: 8px;
        outline: none;
    }}

    #sensor_list::item {{
        padding: 12px 16px;
        border-bottom: 1px solid {c['divider']};
    }}

    #sensor_list::item:hover {{
        background-color: {c['highlight_row']};
    }}

    #sensor_list::item:selected {{
        background-color: {c['accent_subtle']};
        color: {c['text_primary']};
    }}

    /* ── Detail Panel ───────────────────────────────────────── */
    #detail_panel {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border_light']};
        border-radius: 8px;
    }}

    #detail_title {{
        font-family: '{f['heading']}', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: {c['text_primary']};
        padding-bottom: 4px;
    }}

    #detail_subtitle {{
        font-size: 13px;
        color: {c['text_secondary']};
        padding-bottom: 12px;
    }}

    #section_header {{
        font-family: '{f['heading']}', sans-serif;
        font-size: 11px;
        font-weight: 700;
        color: {c['text_tertiary']};
        letter-spacing: 1.2px;
        text-transform: uppercase;
        padding: 16px 0px 6px 0px;
    }}

    /* ── Detail Table ───────────────────────────────────────── */
    QTableWidget {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border_light']};
        border-radius: 6px;
        gridline-color: {c['divider']};
        font-size: 12px;
    }}

    QTableWidget::item {{
        padding: 6px 10px;
    }}

    QTableWidget QHeaderView::section {{
        background-color: {c['bg_secondary']};
        color: {c['text_secondary']};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        padding: 6px 10px;
        border: none;
        border-bottom: 1px solid {c['border']};
    }}

    /* ── Scrollbar ──────────────────────────────────────────── */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: {c['border']};
        border-radius: 4px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {c['text_tertiary']};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
    }}

    QScrollBar::handle:horizontal {{
        background: {c['border']};
        border-radius: 4px;
        min-width: 30px;
    }}

    /* ── Config badge ───────────────────────────────────────── */
    #config_badge {{
        background-color: {c['accent_subtle']};
        color: {c['accent']};
        border-radius: 4px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 600;
    }}

    /* ── Status Bar ─────────────────────────────────────────── */
    QStatusBar {{
        background-color: {c['bg_secondary']};
        border-top: 1px solid {c['border']};
        color: {c['text_tertiary']};
        font-size: 11px;
        padding: 4px 12px;
    }}

    /* ── Action Toolbar ─────────────────────────────────────── */
    #action_toolbar {{
        background: transparent;
    }}

    #action_btn {{
        padding: 5px 12px;
        border: 1px solid {c['border']};
        border-radius: 5px;
        background-color: {c['bg_card']};
        font-size: 12px;
        font-weight: 500;
        color: {c['text_primary']};
    }}

    #action_btn:hover {{
        background-color: {c['bg_secondary']};
        border-color: {c['accent']};
    }}

    #action_btn:disabled {{
        color: {c['text_tertiary']};
        border-color: {c['border_light']};
    }}

    #action_btn_danger {{
        padding: 5px 12px;
        border: 1px solid {c['border']};
        border-radius: 5px;
        background-color: {c['bg_card']};
        font-size: 12px;
        font-weight: 500;
        color: #B04040;
    }}

    #action_btn_danger:hover {{
        background-color: #FDF0F0;
        border-color: #B04040;
    }}

    #action_btn_danger:disabled {{
        color: {c['text_tertiary']};
        border-color: {c['border_light']};
    }}

    /* ── Edit Dialog ────────────────────────────────────────── */
    QDialog {{
        background-color: {c['bg_primary']};
    }}

    #dialog_header {{
        background-color: {c['bg_card']};
        border-bottom: 1px solid {c['border']};
    }}

    #dialog_title {{
        font-family: '{f['heading']}', sans-serif;
        font-size: 18px;
        font-weight: 700;
        color: {c['text_primary']};
    }}

    #dialog_footer {{
        background-color: {c['bg_secondary']};
        border-top: 1px solid {c['border']};
    }}

    #form_group {{
        font-family: '{f['heading']}', sans-serif;
        font-size: 12px;
        font-weight: 600;
        color: {c['text_secondary']};
        border: 1px solid {c['border_light']};
        border-radius: 8px;
        padding: 12px;
        background-color: {c['bg_card']};
    }}

    #form_group::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: {c['accent']};
    }}

    #form_input {{
        padding: 6px 10px;
        border: 1px solid {c['border']};
        border-radius: 5px;
        background-color: {c['bg_card']};
        font-size: 13px;
        color: {c['text_primary']};
    }}

    #form_input:focus {{
        border-color: {c['accent']};
    }}

    QDoubleSpinBox, QSpinBox {{
        padding: 6px 10px;
        border: 1px solid {c['border']};
        border-radius: 5px;
        background-color: {c['bg_card']};
        font-size: 13px;
        color: {c['text_primary']};
    }}

    QComboBox {{
        padding: 6px 10px;
        border: 1px solid {c['border']};
        border-radius: 5px;
        background-color: {c['bg_card']};
        font-size: 13px;
        color: {c['text_primary']};
    }}

    QComboBox:focus {{
        border-color: {c['accent']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border']};
        selection-background-color: {c['accent_subtle']};
        selection-color: {c['text_primary']};
    }}

    #btn_save {{
        padding: 8px 24px;
        border: none;
        border-radius: 6px;
        background-color: {c['accent']};
        color: {c['text_on_accent']};
        font-size: 13px;
        font-weight: 600;
    }}

    #btn_save:hover {{
        background-color: {c['accent_hover']};
    }}

    #btn_cancel {{
        padding: 8px 20px;
        border: 1px solid {c['border']};
        border-radius: 6px;
        background-color: {c['bg_card']};
        color: {c['text_secondary']};
        font-size: 13px;
        font-weight: 500;
    }}

    #btn_cancel:hover {{
        background-color: {c['bg_secondary']};
    }}

    /* ── Array Edit Table ──────────────────────────────────── */
    #array_edit_table {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border_light']};
        border-radius: 6px;
        font-size: 12px;
    }}

    #array_edit_table::item {{
        padding: 4px 8px;
    }}

    /* ── Calculator Panel ───────────────────────────────────── */
    #calculator_panel {{
        background-color: {c['bg_primary']};
    }}

    #calc_header {{
        background-color: {c['bg_card']};
        border-bottom: 1px solid {c['border']};
    }}

    #calc_section_header {{
        font-family: '{f['heading']}', sans-serif;
        font-size: 11px;
        font-weight: 700;
        color: {c['text_tertiary']};
        letter-spacing: 1.2px;
        text-transform: uppercase;
        padding: 8px 0px 2px 0px;
    }}

    #calc_group {{
        border: 1px solid {c['border_light']};
        border-radius: 8px;
        padding: 14px;
        background-color: {c['bg_card']};
    }}

    /* ── Calculator Tabs ────────────────────────────────────── */
    #calc_tabs::pane {{
        border: none;
        background-color: {c['bg_primary']};
    }}

    #calc_tabs > QTabBar::tab {{
        padding: 10px 24px;
        border: none;
        border-bottom: 2px solid transparent;
        font-size: 13px;
        font-weight: 600;
        color: {c['text_secondary']};
        background: {c['bg_secondary']};
    }}

    #calc_tabs > QTabBar::tab:hover {{
        color: {c['text_primary']};
        background-color: rgba(0, 0, 0, 0.03);
    }}

    #calc_tabs > QTabBar::tab:selected {{
        color: {c['accent']};
        border-bottom: 2px solid {c['accent']};
        background: {c['bg_card']};
    }}

    /* ── Result Cards ───────────────────────────────────────── */
    #result_card {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border_light']};
        border-radius: 10px;
        min-width: 140px;
    }}

    #result_card_title {{
        font-family: '{f['heading']}', sans-serif;
        font-size: 11px;
        font-weight: 600;
        color: {c['text_tertiary']};
        letter-spacing: 0.5px;
    }}

    #result_card_value {{
        font-family: {f['mono']};
        font-size: 24px;
        font-weight: 700;
        color: {c['accent']};
    }}

    #result_card_unit {{
        font-size: 11px;
        color: {c['text_secondary']};
    }}

    /* ── Calculator Error ───────────────────────────────────── */
    #calc_error {{
        color: #B04040;
        font-size: 12px;
        padding: 6px 12px;
        background-color: #FDF0F0;
        border: 1px solid #E8C0C0;
        border-radius: 6px;
    }}

    /* ── Info Section (Assumptions & References) ────────────── */
    #info_section {{
        background-color: #F4F6F8;
        border: 1px solid {c['border_light']};
        border-radius: 8px;
    }}

    #info_section_title {{
        font-family: '{f['heading']}', sans-serif;
        font-size: 12px;
        font-weight: 700;
        color: {c['text_secondary']};
    }}

    #info_section_text {{
        font-size: 12px;
        color: {c['text_secondary']};
        line-height: 1.5;
    }}

    #info_section_text code {{
        font-family: {f['mono']};
        font-size: 12px;
        background-color: rgba(0, 0, 0, 0.05);
        padding: 2px 6px;
        border-radius: 3px;
    }}
    """
