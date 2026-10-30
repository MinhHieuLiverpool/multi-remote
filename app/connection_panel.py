"""
Connection card widget - High-contrast dashboard styling with accurate connection status.
"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QSpinBox, QComboBox, QCheckBox,
    QPushButton, QWidget, QSlider, QMessageBox, QListView
)
from PyQt5.QtCore import Qt, pyqtSignal
from app.models import RdpConnectionInfo, NETWORK_TYPES, RESOLUTION_PRESETS
from app.styles import COLORS, BTN_GREEN, BTN_RED, BTN_REMOVE, COMBOBOX_STYLE


class ConnectionCard(QFrame):
    """A card widget representing a single RDP connection."""

    connect_requested = pyqtSignal(int)
    disconnect_requested = pyqtSignal(int)
    remove_requested = pyqtSignal(int)
    data_changed = pyqtSignal(int)

    def __init__(self, index: int, connection: RdpConnectionInfo = None, parent=None):
        super().__init__(parent)
        self.index = index
        self._connection = connection or RdpConnectionInfo()
        self._is_connected = False
        self.setObjectName("connectionCard")
        self.setFrameShape(QFrame.NoFrame)
        self._setup_ui()
        self._load_from_connection()

    def _setup_ui(self):
        """Build the card UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(18, 16, 18, 16)

        # ===== Header row =====
        header = QHBoxLayout()
        header.setSpacing(12)

        # Index badge
        self._index_label = QLabel(f"#{self.index + 1}")
        self._index_label.setStyleSheet(
            f"color: #042017; font-size: 11px; font-weight: 900; "
            f"background-color: {COLORS['green_main']}; border-radius: 4px; "
            f"padding: 3px 10px;"
        )
        self._index_label.setAlignment(Qt.AlignCenter)
        self._index_label.setFixedHeight(22)
        header.addWidget(self._index_label)

        # Name field
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter server/connection name...")
        self._name_edit.setMinimumWidth(220)
        self._name_edit.setStyleSheet(
            f"background-color: {COLORS['bg_input']}; border: 1px solid {COLORS['border_light']}; "
            f"border-radius: 5px; color: #ffffff; font-size: 14px; font-weight: 700; "
            f"padding: 5px 10px;"
        )
        self._name_edit.textChanged.connect(lambda: self.data_changed.emit(self.index))
        header.addWidget(self._name_edit)

        header.addStretch()

        # Status text
        self._status_label = QLabel("Disconnected")
        self._status_label.setStyleSheet(f"color: {COLORS['red_main']}; font-size: 12px; font-weight: 800;")
        header.addWidget(self._status_label)

        # Remove button
        self._remove_btn = QPushButton("Remove")
        self._remove_btn.setStyleSheet(BTN_REMOVE)
        self._remove_btn.setToolTip("Remove this connection")
        self._remove_btn.setCursor(Qt.PointingHandCursor)
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.index))
        header.addWidget(self._remove_btn)

        main_layout.addLayout(header)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px; border: none;")
        main_layout.addWidget(sep)

        # ===== Connection fields grid =====
        fields_layout = QGridLayout()
        fields_layout.setHorizontalSpacing(16)
        fields_layout.setVerticalSpacing(10)
        fields_layout.setColumnStretch(1, 2)
        fields_layout.setColumnStretch(3, 2)

        row = 0

        # Row 0: IP + Port
        fields_layout.addWidget(self._make_label("IP Address"), row, 0)
        self._ip_edit = QLineEdit()
        self._ip_edit.setPlaceholderText("192.168.1.100")
        self._ip_edit.textChanged.connect(lambda: self.data_changed.emit(self.index))
        fields_layout.addWidget(self._ip_edit, row, 1)

        fields_layout.addWidget(self._make_label("Port"), row, 2)
        self._port_spin = QSpinBox()
        self._port_spin.setRange(1, 65535)
        self._port_spin.setValue(3389)
        self._port_spin.setFixedWidth(100)
        fields_layout.addWidget(self._port_spin, row, 3)

        row += 1

        # Row 1: Username + Password
        fields_layout.addWidget(self._make_label("Username"), row, 0)
        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText("administrator")
        fields_layout.addWidget(self._user_edit, row, 1)

        fields_layout.addWidget(self._make_label("Password"), row, 2)
        self._pass_edit = QLineEdit()
        self._pass_edit.setEchoMode(QLineEdit.Password)
        self._pass_edit.setPlaceholderText("••••••••")
        fields_layout.addWidget(self._pass_edit, row, 3)

        row += 1

        # Row 2: Domain + Resolution
        fields_layout.addWidget(self._make_label("Domain"), row, 0)
        self._domain_edit = QLineEdit()
        self._domain_edit.setPlaceholderText("(Optional)")
        fields_layout.addWidget(self._domain_edit, row, 1)

        fields_layout.addWidget(self._make_label("Resolution"), row, 2)
        self._res_combo = QComboBox()
        self._res_combo.setView(QListView())
        self._res_combo.setStyleSheet(COMBOBOX_STYLE)
        for w, h, label in RESOLUTION_PRESETS:
            self._res_combo.addItem(label, (w, h))
        fields_layout.addWidget(self._res_combo, row, 3)

        row += 1

        # Row 3: Color Depth + Network
        fields_layout.addWidget(self._make_label("Color Depth"), row, 0)
        self._depth_combo = QComboBox()
        self._depth_combo.setView(QListView())
        self._depth_combo.setStyleSheet(COMBOBOX_STYLE)
        self._depth_combo.addItem("32-bit (True Color)", 32)
        self._depth_combo.addItem("24-bit", 24)
        self._depth_combo.addItem("16-bit (High Color)", 16)
        fields_layout.addWidget(self._depth_combo, row, 1)

        fields_layout.addWidget(self._make_label("Network"), row, 2)
        self._network_combo = QComboBox()
        self._network_combo.setView(QListView())
        self._network_combo.setStyleSheet(COMBOBOX_STYLE)
        for key, label in NETWORK_TYPES.items():
            self._network_combo.addItem(label, key)
        self._network_combo.setCurrentIndex(5)
        fields_layout.addWidget(self._network_combo, row, 3)

        row += 1

        # Row 4: Audio
        fields_layout.addWidget(self._make_label("Audio"), row, 0)
        self._audio_combo = QComboBox()
        self._audio_combo.setView(QListView())
        self._audio_combo.setStyleSheet(COMBOBOX_STYLE)
        self._audio_combo.addItem("Remote PC (Default)", 1)
        self._audio_combo.addItem("Play on this PC", 0)
        self._audio_combo.addItem("Do not play / Mute", 2)
        self._audio_combo.currentIndexChanged.connect(lambda: self.data_changed.emit(self.index))
        fields_layout.addWidget(self._audio_combo, row, 1)

        main_layout.addLayout(fields_layout)

        # ===== Codec & Bitrate row =====
        codec_layout = QHBoxLayout()
        codec_layout.setSpacing(16)

        # H264 toggle
        self._h264_check = QCheckBox("H.264 / AVC")
        self._h264_check.setChecked(True)
        self._h264_check.setToolTip("Enable H.264 hardware acceleration")
        codec_layout.addWidget(self._h264_check)

        # Bitrate
        codec_layout.addWidget(self._make_label("Bitrate"))
        self._bitrate_slider = QSlider(Qt.Horizontal)
        self._bitrate_slider.setRange(1000, 50000)
        self._bitrate_slider.setValue(15000)
        self._bitrate_slider.setSingleStep(500)
        self._bitrate_slider.setMinimumWidth(180)
        self._bitrate_slider.valueChanged.connect(self._update_bitrate_label)
        codec_layout.addWidget(self._bitrate_slider, 1)

        self._bitrate_label = QLabel("15000 kbps")
        self._bitrate_label.setFixedWidth(105)
        self._bitrate_label.setStyleSheet(
            f"color: {COLORS['green_main']}; font-weight: 800; font-size: 13px; "
            f"background-color: {COLORS['bg_input']}; border: 1px solid {COLORS['green_main']}; "
            f"border-radius: 5px; padding: 4px 8px;"
        )
        self._bitrate_label.setAlignment(Qt.AlignCenter)
        codec_layout.addWidget(self._bitrate_label)

        # Option checkboxes
        self._nla_check = QCheckBox("NLA")
        self._nla_check.setChecked(True)
        codec_layout.addWidget(self._nla_check)

        self._compress_check = QCheckBox("Compress")
        self._compress_check.setChecked(True)
        codec_layout.addWidget(self._compress_check)

        self._smart_check = QCheckBox("Smart Sizing")
        self._smart_check.setChecked(True)
        codec_layout.addWidget(self._smart_check)

        main_layout.addLayout(codec_layout)

        # ===== Action Buttons =====
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        self._connect_btn = QPushButton("Connect")
        self._connect_btn.setStyleSheet(BTN_GREEN)
        self._connect_btn.setCursor(Qt.PointingHandCursor)
        self._connect_btn.setMinimumWidth(140)
        self._connect_btn.setFixedHeight(38)
        self._connect_btn.clicked.connect(self._on_connect)
        btn_layout.addWidget(self._connect_btn)

        self._disconnect_btn = QPushButton("Disconnect")
        self._disconnect_btn.setStyleSheet(BTN_RED)
        self._disconnect_btn.setCursor(Qt.PointingHandCursor)
        self._disconnect_btn.setMinimumWidth(140)
        self._disconnect_btn.setFixedHeight(38)
        self._disconnect_btn.setEnabled(False)
        self._disconnect_btn.clicked.connect(self._on_disconnect)
        btn_layout.addWidget(self._disconnect_btn)

        main_layout.addLayout(btn_layout)

    def _make_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 12px; "
            f"font-weight: 700; min-width: 80px;"
        )
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return lbl

    def _update_bitrate_label(self, value):
        self._bitrate_label.setText(f"{value} kbps")

    def _load_from_connection(self):
        c = self._connection
        self._name_edit.setText(c.name)
        self._ip_edit.setText(c.ip_address)
        self._port_spin.setValue(c.port)
        self._user_edit.setText(c.username)
        self._pass_edit.setText(c.password)
        self._domain_edit.setText(c.domain)

        for i, (w, h, _) in enumerate(RESOLUTION_PRESETS):
            if w == c.desktop_width and h == c.desktop_height:
                self._res_combo.setCurrentIndex(i)
                break

        for i in range(self._depth_combo.count()):
            if self._depth_combo.itemData(i) == c.color_depth:
                self._depth_combo.setCurrentIndex(i)
                break

        for i in range(self._network_combo.count()):
            if self._network_combo.itemData(i) == c.network_type:
                self._network_combo.setCurrentIndex(i)
                break

        audio = getattr(c, 'audio_mode', 1)
        for i in range(self._audio_combo.count()):
            if self._audio_combo.itemData(i) == audio:
                self._audio_combo.setCurrentIndex(i)
                break

        self._h264_check.setChecked(c.use_h264)
        self._bitrate_slider.setValue(c.bitrate_kbps)
        self._nla_check.setChecked(c.enable_nla)
        self._compress_check.setChecked(c.compress)
        self._smart_check.setChecked(c.smart_sizing)

    def get_connection_info(self) -> RdpConnectionInfo:
        res = self._res_combo.currentData() or (1920, 1080)
        return RdpConnectionInfo(
            name=self._name_edit.text().strip(),
            ip_address=self._ip_edit.text().strip(),
            port=self._port_spin.value(),
            username=self._user_edit.text().strip(),
            password=self._pass_edit.text(),
            domain=self._domain_edit.text().strip(),
            desktop_width=res[0],
            desktop_height=res[1],
            color_depth=self._depth_combo.currentData() or 32,
            use_h264=self._h264_check.isChecked(),
            bitrate_kbps=self._bitrate_slider.value(),
            network_type=self._network_combo.currentData() or 6,
            smart_sizing=self._smart_check.isChecked(),
            enable_nla=self._nla_check.isChecked(),
            compress=self._compress_check.isChecked(),
            audio_mode=self._audio_combo.currentData() if self._audio_combo.currentData() is not None else 1,
            is_connected=self._is_connected,
        )

    def set_index(self, index: int):
        self.index = index
        self._index_label.setText(f"#{index + 1}")

    def set_connected(self, connected: bool):
        self._is_connected = connected
        if connected:
            self._status_label.setText("Connected")
            self._status_label.setStyleSheet(f"color: {COLORS['green_main']}; font-size: 12px; font-weight: 800;")
            self._connect_btn.setEnabled(False)
            self._disconnect_btn.setEnabled(True)
            self.setObjectName("connectionCardConnected")
            self.setStyleSheet(f"QFrame#connectionCardConnected {{ background-color: {COLORS['bg_card']}; border: 2px solid {COLORS['green_main']}; border-radius: 10px; }}")
            self._set_fields_enabled(False)
        else:
            self._status_label.setText("Disconnected")
            self._status_label.setStyleSheet(f"color: {COLORS['red_main']}; font-size: 12px; font-weight: 800;")
            self._connect_btn.setEnabled(True)
            self._disconnect_btn.setEnabled(False)
            self.setObjectName("connectionCard")
            self.setStyleSheet(f"QFrame#connectionCard {{ background-color: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; border-radius: 10px; }}")
            self._set_fields_enabled(True)

    def set_connecting(self):
        self._is_connected = False
        self._status_label.setText("Connecting...")
        self._status_label.setStyleSheet("color: #f59e0b; font-size: 12px; font-weight: 800;")
        self._connect_btn.setEnabled(False)
        self._disconnect_btn.setEnabled(True)
        self._set_fields_enabled(False)

    def set_failed(self, error_msg: str):
        """Called when real connection fails (Host unreachable / timeout)."""
        self._is_connected = False
        short_msg = "Unreachable" if "unreachable" in error_msg.lower() or "516" in error_msg else "Failed"
        self._status_label.setText(f"Failed: {short_msg}")
        self._status_label.setToolTip(error_msg)
        self._status_label.setStyleSheet("color: #f87171; font-size: 12px; font-weight: 800;")
        self._connect_btn.setEnabled(True)
        self._disconnect_btn.setEnabled(False)
        self.setObjectName("connectionCard")
        self.setStyleSheet(f"QFrame#connectionCard {{ background-color: {COLORS['bg_card']}; border: 1px solid #dc2626; border-radius: 10px; }}")
        self._set_fields_enabled(True)

    def _set_fields_enabled(self, enabled: bool):
        for w in [self._ip_edit, self._port_spin, self._user_edit, self._pass_edit,
                  self._domain_edit, self._res_combo, self._depth_combo, self._network_combo,
                  self._h264_check, self._bitrate_slider, self._nla_check, self._compress_check,
                  self._smart_check]:
            w.setEnabled(enabled)

    def _on_connect(self):
        ip = self._ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(self, "Warning", "Please enter an IP address.")
            return
        self.connect_requested.emit(self.index)

    def _on_disconnect(self):
        self.disconnect_requested.emit(self.index)
