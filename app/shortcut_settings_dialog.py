"""
Shortcut Settings Dialog - UI to configure keybindings for switching slots to Master.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QComboBox, QScrollArea, QWidget, QFrame, QListView
)
from PyQt5.QtCore import Qt
from app.shortcut_manager import ShortcutManager, KEY_NAME_TO_QT
from app.styles import (
    COLORS, BTN_GREEN, BTN_BLUE, BTN_RED, COMBOBOX_STYLE
)


class ShortcutSettingsDialog(QDialog):
    """High-contrast modal dialog to configure slot-to-master shortcuts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Shortcut Settings — Send Slot to Master")
        self.setMinimumSize(540, 620)
        self.resize(580, 660)
        self.setStyleSheet(f"background-color: {COLORS['bg_main']}; color: #ffffff;")
        self.manager = ShortcutManager.get_instance()
        self._combos = {}
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Title Header
        header = QHBoxLayout()
        icon_lbl = QLabel("⚡")
        icon_lbl.setStyleSheet("font-size: 28px;")
        header.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("Keyboard Shortcut Settings")
        title.setStyleSheet("font-size: 18px; font-weight: 900; color: #ffffff;")
        subtitle = QLabel("Press configured key to immediately send that Slot to the Master Monitor")
        subtitle.setStyleSheet(f"font-size: 12px; color: {COLORS['text_muted']};")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()
        main_layout.addLayout(header)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px;")
        main_layout.addWidget(div)

        # Modifier Selection Box
        mod_card = QFrame()
        mod_card.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; border-radius: 8px;"
        )
        mod_layout = QHBoxLayout(mod_card)
        mod_layout.setContentsMargins(16, 12, 16, 12)

        mod_title = QLabel("Key Modifier:")
        mod_title.setStyleSheet("font-weight: 800; font-size: 13px; color: #ffffff;")
        mod_layout.addWidget(mod_title)

        self._mod_combo = QComboBox()
        self._mod_combo.setView(QListView())
        self._mod_combo.setStyleSheet(COMBOBOX_STYLE)
        self._mod_combo.setFixedWidth(160)
        for m in ["None", "Ctrl", "Alt", "Shift"]:
            self._mod_combo.addItem(f"{m} (e.g. {m + '+' if m != 'None' else ''}1)", m)
        idx = self._mod_combo.findData(self.manager.modifier)
        if idx >= 0:
            self._mod_combo.setCurrentIndex(idx)
        mod_layout.addWidget(self._mod_combo)
        mod_layout.addStretch()

        # Preset Button: Number keys
        num_preset_btn = QPushButton("Use 1-9 Keys")
        num_preset_btn.setStyleSheet(BTN_BLUE)
        num_preset_btn.setCursor(Qt.PointingHandCursor)
        num_preset_btn.setFixedHeight(30)
        num_preset_btn.clicked.connect(self._apply_number_preset)
        mod_layout.addWidget(num_preset_btn)

        # Preset Button: F1-F12 keys
        fn_preset_btn = QPushButton("Use F1-F12")
        fn_preset_btn.setStyleSheet(BTN_BLUE)
        fn_preset_btn.setCursor(Qt.PointingHandCursor)
        fn_preset_btn.setFixedHeight(30)
        fn_preset_btn.clicked.connect(self._apply_fn_preset)
        mod_layout.addWidget(fn_preset_btn)

        main_layout.addWidget(mod_card)

        # Scroll Area with Slot Mappings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}"
            "QScrollBar:vertical { background: #111622; width: 10px; border-radius: 5px; }"
            "QScrollBar::handle:vertical { background: #2b374e; border-radius: 5px; min-height: 20px; }"
        )

        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        grid = QGridLayout(content)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setSpacing(12)

        available_keys = list(KEY_NAME_TO_QT.keys())

        for slot_num in range(1, 17):
            r = (slot_num - 1) // 2
            c = ((slot_num - 1) % 2) * 3

            lbl = QLabel(f"Slot {slot_num}:")
            lbl.setStyleSheet("font-weight: 700; font-size: 13px; color: #cbd5e1;")
            grid.addWidget(lbl, r, c)

            arrow = QLabel("➔ Send to Master:")
            arrow.setStyleSheet(f"font-size: 11px; color: {COLORS['green_main']};")
            grid.addWidget(arrow, r, c + 1)

            combo = QComboBox()
            combo.setView(QListView())
            combo.setStyleSheet(COMBOBOX_STYLE)
            combo.setFixedWidth(80)
            combo.addItem("None", "")
            for k in available_keys:
                combo.addItem(k, k)

            # Set current key
            cur_key = self.manager.shortcuts.get(str(slot_num), "")
            combo_idx = combo.findData(cur_key)
            if combo_idx >= 0:
                combo.setCurrentIndex(combo_idx)

            self._combos[str(slot_num)] = combo
            grid.addWidget(combo, r, c + 2)

        scroll.setWidget(content)
        main_layout.addWidget(scroll, 1)

        # Bottom Action Bar
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)

        tip = QLabel("💡 Tip: Click on MultiView window to focus, then press key to swap.")
        tip.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        btn_box.addWidget(tip)
        btn_box.addStretch()

        reset_btn = QPushButton("Reset Defaults")
        reset_btn.setStyleSheet(BTN_RED)
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setFixedHeight(36)
        reset_btn.clicked.connect(self._reset_defaults)
        btn_box.addWidget(reset_btn)

        save_btn = QPushButton("Save & Apply")
        save_btn.setStyleSheet(BTN_GREEN)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedHeight(36)
        save_btn.setMinimumWidth(120)
        save_btn.clicked.connect(self._save_and_close)
        btn_box.addWidget(save_btn)

        main_layout.addLayout(btn_box)

    def _apply_number_preset(self):
        self._mod_combo.setCurrentIndex(self._mod_combo.findData("None"))
        for i in range(1, 10):
            combo = self._combos.get(str(i))
            if combo:
                combo.setCurrentIndex(combo.findData(str(i)))
        if "10" in self._combos:
            self._combos["10"].setCurrentIndex(self._combos["10"].findData("0"))

    def _apply_fn_preset(self):
        self._mod_combo.setCurrentIndex(self._mod_combo.findData("None"))
        for i in range(1, 13):
            combo = self._combos.get(str(i))
            if combo:
                combo.setCurrentIndex(combo.findData(f"F{i}"))

    def _reset_defaults(self):
        self._apply_number_preset()
        for i in range(11, 17):
            combo = self._combos.get(str(i))
            if combo:
                combo.setCurrentIndex(combo.findData(f"F{i - 10}"))

    def _save_and_close(self):
        self.manager.modifier = self._mod_combo.currentData()
        for slot_str, combo in self._combos.items():
            self.manager.shortcuts[slot_str] = combo.currentData()
        self.manager.save()
        self.accept()

