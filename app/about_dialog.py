"""
Custom Beautified About Dialog for Multi Remote Desktop Manager
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt
from app.styles import COLORS, BTN_GREEN


class AboutDialog(QDialog):
    """Modern dark theme About Dialog with high-tech cards and clear specs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Multi Remote Desktop Manager")
        self.setFixedSize(560, 520)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_main']};
                border: 1.5px solid {COLORS['border_light']};
                border-radius: 12px;
            }}
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # ===== Header: Logo + App Name + Version Badge =====
        header = QHBoxLayout()
        header.setSpacing(16)

        # Hexagon logo box
        logo_box = QLabel("⬡")
        logo_box.setAlignment(Qt.AlignCenter)
        logo_box.setFixedSize(54, 54)
        logo_box.setStyleSheet(f"""
            background-color: {COLORS['bg_card']};
            color: {COLORS['green_main']};
            font-size: 32px;
            font-weight: bold;
            border: 2px solid {COLORS['green_main']};
            border-radius: 12px;
        """)
        header.addWidget(logo_box)

        # Title & Subtitle
        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        title_row = QHBoxLayout()
        title_lbl = QLabel("Multi Remote Desktop")
        title_lbl.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: 900;")
        title_row.addWidget(title_lbl)

        ver_badge = QLabel("v1.0 PRO")
        ver_badge.setStyleSheet(f"""
            color: #042017;
            background-color: {COLORS['green_main']};
            font-size: 11px;
            font-weight: 900;
            padding: 2px 8px;
            border-radius: 4px;
        """)
        title_row.addWidget(ver_badge)
        title_row.addStretch()
        title_col.addLayout(title_row)

        desc_lbl = QLabel("Professional Multi-Session RDP & Live Screen Monitor")
        desc_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; font-weight: 600;")
        title_col.addWidget(desc_lbl)

        header.addLayout(title_col)
        layout.addLayout(header)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px; border: none;")
        layout.addWidget(sep)

        # ===== 4 Feature Cards Grid =====
        cards_grid = QGridLayout()
        cards_grid.setSpacing(12)

        cards_grid.addWidget(self._make_feature_card(
            "Native Windows RDP",
            "Powered by Microsoft Terminal Services engine (mstscax.dll v10). Full keyboard, mouse, audio & NLA authentication.",
            COLORS['green_main']
        ), 0, 0)

        cards_grid.addWidget(self._make_feature_card(
            "H.264 / AVC Codec",
            "Hardware video acceleration with dynamic bitrate control from 1,000 to 50,000 kbps for smooth low-latency streaming.",
            COLORS['blue_main']
        ), 0, 1)

        cards_grid.addWidget(self._make_feature_card(
            "MultiView 16 Grid",
            "Customizable 1x1 to 4x4 matrix. 1-click to maximize any slot, double-click to return to grid view. Pure Fullscreen mode.",
            "#a855f7"
        ), 1, 0)

        cards_grid.addWidget(self._make_feature_card(
            "Live Screen Capture",
            "Add local physical monitors directly into grid cells. Stream live displays alongside remote servers in real-time.",
            COLORS['teal_main']
        ), 1, 1)

        layout.addLayout(cards_grid)

        # ===== System Tech Specs Card =====
        specs_card = QFrame()
        specs_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 14px;
            }}
        """)
        specs_layout = QHBoxLayout(specs_card)
        specs_layout.setContentsMargins(12, 8, 12, 8)

        def make_spec(label, value):
            col = QVBoxLayout()
            col.setSpacing(2)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: 800; text-transform: uppercase;")
            val = QLabel(value)
            val.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 700;")
            col.addWidget(lbl)
            col.addWidget(val)
            return col

        specs_layout.addLayout(make_spec("RDP Engine", "mstscax.dll v10"))
        specs_layout.addLayout(make_spec("Architecture", "Windows 64-bit"))
        specs_layout.addLayout(make_spec("Framework", "Python 3.13 / PyQt5"))
        specs_layout.addLayout(make_spec("Max Slots", "16 Simultaneous"))

        layout.addWidget(specs_card)

        # ===== Bottom: Close Button =====
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(BTN_GREEN)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedSize(130, 38)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _make_feature_card(self, title: str, description: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-left: 3.5px solid {accent_color};
                border-radius: 8px;
            }}
        """)
        l = QVBoxLayout(card)
        l.setContentsMargins(14, 12, 14, 12)
        l.setSpacing(4)

        t = QLabel(title)
        t.setStyleSheet(f"color: #ffffff; font-size: 13px; font-weight: 800;")
        l.addWidget(t)

        d = QLabel(description)
        d.setWordWrap(True)
        d.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; line-height: 15px;")
        l.addWidget(d)

        return card

