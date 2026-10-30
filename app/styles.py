"""
Global application styles - High-contrast Dashboard with Vibrant Green / Blue Buttons
"""

COLORS = {
    "bg_main":       "#111622",      # Dark main background
    "bg_sidebar":    "#171e2e",      # Left sidebar background
    "bg_card":       "#1c2436",      # Card background
    "bg_input":      "#1a2234",      # Input field background
    "bg_input_focus":"#202b40",      # Input focus background
    "bg_header":     "#171e2e",      # Top header

    "border":        "#2b374e",      # Border color
    "border_light":  "#3b4b6b",      # Highlight border
    "border_focus":  "#10b981",      # Focus border (green)

    # Vibrant Button & Accent Colors
    "green_main":    "#10b981",      # Emerald Green - primary
    "green_hover":   "#34d399",      # Light green hover
    "green_press":   "#059669",      # Dark green pressed
    "green_dark_bg": "#064e3b",      # Dark green for badges

    "blue_main":     "#0284c7",      # Sky / Ocean Blue
    "blue_hover":    "#38bdf8",      # Light blue hover
    "blue_press":    "#0369a1",      # Dark blue pressed

    "teal_main":     "#0d9488",      # Teal / Cyan Green
    "teal_hover":    "#14b8a6",

    "red_main":      "#ef4444",      # Bright Red (Disconnect/Remove)
    "red_hover":     "#f87171",
    "red_press":     "#dc2626",

    "text_primary":  "#ffffff",      # Pure white text
    "text_secondary":"#cbd5e1",      # Slate light
    "text_muted":    "#94a3b8",      # Slate muted
    "text_dark":     "#64748b",      # Slate dark
}

# ===== BEAUTIFIED COMBOBOX STYLESHEET =====
COMBOBOX_STYLE = f"""
QComboBox {{
    background-color: {COLORS['bg_input']};
    color: #ffffff;
    border: 1px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 6px 30px 6px 12px;
    font-size: 13px;
    font-weight: 600;
    min-height: 24px;
}}

QComboBox:hover {{
    border: 1px solid {COLORS['green_main']};
    background-color: {COLORS['bg_input_focus']};
}}

QComboBox:focus {{
    border: 1px solid {COLORS['green_main']};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid {COLORS['border']};
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: {COLORS['bg_input']};
}}

QComboBox::drop-down:hover {{
    background-color: {COLORS['border']};
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['green_main']};
    margin-right: 2px;
}}

QComboBox QAbstractItemView {{
    background-color: #1e283d;
    color: #ffffff;
    border: 1px solid {COLORS['green_main']};
    border-radius: 6px;
    padding: 4px;
    selection-background-color: {COLORS['green_main']};
    selection-color: #042017;
    outline: none;
}}

QComboBox QAbstractItemView::item {{
    min-height: 30px;
    padding: 6px 12px;
    border-radius: 4px;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: #293652;
    color: {COLORS['green_hover']};
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: {COLORS['green_main']};
    color: #042017;
    font-weight: 800;
}}
"""

# ===== DIRECT BUTTON STYLESHEETS =====

# Vibrant Green Button
BTN_GREEN = f"""
QPushButton {{
    background-color: {COLORS['green_main']};
    color: #042017;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 800;
}}
QPushButton:hover {{
    background-color: {COLORS['green_hover']};
    color: #000000;
}}
QPushButton:pressed {{
    background-color: {COLORS['green_press']};
    color: #ffffff;
}}
QPushButton:disabled {{
    background-color: #243042;
    color: #556980;
}}
"""

# Vibrant Blue Button
BTN_BLUE = f"""
QPushButton {{
    background-color: {COLORS['blue_main']};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 800;
}}
QPushButton:hover {{
    background-color: {COLORS['blue_hover']};
    color: #000000;
}}
QPushButton:pressed {{
    background-color: {COLORS['blue_press']};
    color: #ffffff;
}}
QPushButton:disabled {{
    background-color: #243042;
    color: #556980;
}}
"""

# Vibrant Teal/Cyan Green Button
BTN_TEAL = f"""
QPushButton {{
    background-color: {COLORS['teal_main']};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 800;
}}
QPushButton:hover {{
    background-color: {COLORS['teal_hover']};
}}
QPushButton:pressed {{
    background-color: #0f766e;
}}
QPushButton:disabled {{
    background-color: #243042;
    color: #556980;
}}
"""

# Open MultiView Button
BTN_MULTIVIEW = f"""
QPushButton {{
    background-color: {COLORS['green_main']};
    color: #042017;
    border: 2px solid {COLORS['green_hover']};
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 900;
    letter-spacing: 0.5px;
}}
QPushButton:hover {{
    background-color: {COLORS['green_hover']};
    color: #000000;
}}
QPushButton:pressed {{
    background-color: {COLORS['green_press']};
    color: #ffffff;
}}
"""

# Red Button
BTN_RED = f"""
QPushButton {{
    background-color: {COLORS['red_main']};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 800;
}}
QPushButton:hover {{
    background-color: {COLORS['red_hover']};
}}
QPushButton:pressed {{
    background-color: {COLORS['red_press']};
}}
QPushButton:disabled {{
    background-color: #243042;
    color: #556980;
}}
"""

# Remove Button in Card header
BTN_REMOVE = f"""
QPushButton {{
    background-color: #b91c1c;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 800;
}}
QPushButton:hover {{
    background-color: {COLORS['red_main']};
}}
"""

# Sidebar Navigation Button
BTN_SIDEBAR = f"""
QPushButton {{
    background-color: #1e283d;
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 7px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 700;
}}
QPushButton:hover {{
    background-color: #283652;
    color: {COLORS['green_hover']};
    border: 1px solid {COLORS['green_main']};
}}
"""

BTN_SIDEBAR_ACTIVE = f"""
QPushButton {{
    background-color: {COLORS['green_main']};
    color: #042017;
    border: none;
    border-radius: 7px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
    font-weight: 900;
}}
QPushButton:hover {{
    background-color: {COLORS['green_hover']};
}}
"""


GLOBAL_STYLE = f"""
* {{
    font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
}}

QMainWindow {{
    background-color: {COLORS['bg_main']};
}}

QWidget {{
    color: {COLORS['text_primary']};
}}

/* ===== Labels ===== */
QLabel {{
    color: {COLORS['text_primary']};
    font-size: 13px;
}}

QLabel#titleLabel {{
    color: #ffffff;
    font-size: 22px;
    font-weight: 800;
}}

QLabel#statValue {{
    font-size: 26px;
    font-weight: 900;
}}

QLabel#statLabel {{
    color: {COLORS['text_muted']};
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}}

/* ===== Input Fields ===== */
QLineEdit, QSpinBox {{
    background-color: {COLORS['bg_input']};
    color: #ffffff;
    border: 1px solid {COLORS['border_light']};
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 13px;
    min-height: 22px;
    selection-background-color: {COLORS['blue_main']};
}}

QLineEdit:focus, QSpinBox:focus {{
    border: 1px solid {COLORS['green_main']};
    background-color: {COLORS['bg_input_focus']};
}}

QLineEdit:disabled, QSpinBox:disabled {{
    background-color: #161c28;
    color: {COLORS['text_dark']};
    border: 1px solid #232c3f;
}}

QLineEdit::placeholder {{
    color: {COLORS['text_dark']};
}}

/* ===== Global ComboBox Styling ===== */
{COMBOBOX_STYLE}

/* ===== Checkbox ===== */
QCheckBox {{
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    spacing: 8px;
    background: transparent;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS['border_light']};
    border-radius: 4px;
    background-color: {COLORS['bg_input']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['green_main']};
    border: 2px solid {COLORS['green_main']};
}}

/* ===== Scroll Area ===== */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background-color: {COLORS['bg_main']};
    width: 8px;
    margin: 4px 2px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border_light']};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['green_main']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ===== Slider ===== */
QSlider::groove:horizontal {{
    background: {COLORS['border']};
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: {COLORS['green_main']};
    width: 18px;
    height: 18px;
    border-radius: 9px;
    margin: -6px 0;
    border: 2px solid #ffffff;
}}

QSlider::handle:horizontal:hover {{
    background: {COLORS['green_hover']};
    width: 20px;
    height: 20px;
    border-radius: 10px;
    margin: -7px 0;
}}

QSlider::sub-page:horizontal {{
    background: {COLORS['green_main']};
    border-radius: 3px;
}}

/* ===== Status Bar ===== */
QStatusBar {{
    background-color: {COLORS['bg_sidebar']};
    color: {COLORS['text_muted']};
    border-top: 1px solid {COLORS['border']};
    font-size: 12px;
    padding: 4px 14px;
}}

/* ===== Menu Bar ===== */
QMenuBar {{
    background-color: {COLORS['bg_header']};
    color: {COLORS['text_secondary']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 3px 8px;
    font-size: 12px;
}}

QMenuBar::item {{
    padding: 6px 12px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['bg_card']};
    color: #ffffff;
}}

QMenu {{
    background-color: {COLORS['bg_card']};
    color: #ffffff;
    border: 1px solid {COLORS['border_light']};
    border-radius: 8px;
    padding: 6px;
    font-size: 13px;
}}

QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['green_main']};
    color: #042017;
    font-weight: 700;
}}

/* ===== Frame Containers ===== */
QFrame#connectionCard {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
}}

QFrame#connectionCard:hover {{
    border: 1px solid {COLORS['border_light']};
}}

QFrame#connectionCardConnected {{
    background-color: {COLORS['bg_card']};
    border: 2px solid {COLORS['green_main']};
    border-radius: 10px;
}}

QFrame#statCard {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 10px;
}}
"""

MULTIVIEW_CELL_STYLE = f"""
QFrame#mvCell {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}

QFrame#mvCell:hover {{
    border: 1px solid {COLORS['green_main']};
}}

QFrame#mvCellActive {{
    background-color: {COLORS['bg_card']};
    border: 2px solid {COLORS['green_main']};
    border-radius: 6px;
}}
"""

MULTIVIEW_HEADER_STYLE = f"""
QLabel {{
    color: #042017;
    font-size: 11px;
    font-weight: 800;
    padding: 4px 8px;
    background-color: {COLORS['green_main']};
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}}
"""
