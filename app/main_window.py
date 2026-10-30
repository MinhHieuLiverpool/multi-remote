"""
Main application window - Professional Dashboard Theme with Wide Sidebar and Vibrant Green / Blue Buttons.
Uses mstsc.exe (Windows native RDP) for reliable connections + cmdkey for credentials.
"""
import logging
import threading
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame,
    QMessageBox, QFileDialog, QSizePolicy, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject

from app.connection_panel import ConnectionCard
from app.multiview_window import MultiViewWindow
from app.rdp_widget import RdpWidget
from app.embedded_mstsc import EmbeddedMstscWidget
from app.rdp_launcher import test_port_reachable, delete_credentials
from app.models import RdpConnectionInfo, save_connections, load_connections
from app.styles import (
    COLORS, BTN_GREEN, BTN_BLUE, BTN_TEAL, BTN_RED, BTN_MULTIVIEW,
    BTN_SIDEBAR, BTN_SIDEBAR_ACTIVE
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class StatCard(QFrame):
    """Stat card for the dashboard header - never crops text."""

    def __init__(self, label: str, value: str, color: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setMinimumHeight(86)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet(
            f"QFrame#statCard {{ background-color: {COLORS['bg_card']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 10px; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        # Label on top
        self._label = QLabel(label)
        self._label.setObjectName("statLabel")
        self._label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; font-weight: 800; text-transform: uppercase;")
        layout.addWidget(self._label)

        # Large value
        self._value_label = QLabel(value)
        self._value_label.setObjectName("statValue")
        self._value_label.setStyleSheet(
            f"color: {color or COLORS['green_main']}; font-size: 26px; font-weight: 900;"
        )
        layout.addWidget(self._value_label)

    def set_value(self, value: str):
        self._value_label.setText(value)


class MainWindow(QMainWindow):
    """Main window for Multi Remote Desktop Manager."""

    MAX_CONNECTIONS = 16

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connections = []
        self._cards = []
        self._rdp_widgets = {}
        self._multiview_window = None
        self._setup_ui()
        self._setup_menu()
        self._load_saved_connections()

    def _setup_ui(self):
        self.setWindowTitle("Multi Remote Desktop Manager")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 850)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ===== LEFT SIDEBAR =====
        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(
            f"QFrame#sidebarFrame {{ background-color: {COLORS['bg_sidebar']}; "
            f"border-right: 1px solid {COLORS['border']}; }}"
        )
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(14, 20, 14, 20)
        sb_layout.setSpacing(10)

        brand_label = QLabel("REMOTE DESKTOP")
        brand_label.setStyleSheet(
            f"color: {COLORS['green_main']}; font-size: 15px; font-weight: 900; letter-spacing: 1px;"
        )
        sb_layout.addWidget(brand_label)

        subbrand_label = QLabel("Manager v1.0")
        subbrand_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; font-weight: 600; margin-bottom: 12px;"
        )
        sb_layout.addWidget(subbrand_label)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet(f"background-color: {COLORS['border']}; max-height: 1px; border: none;")
        sb_layout.addWidget(sep1)

        sb_layout.addSpacing(6)

        self._nav_connections = QPushButton("Connections List")
        self._nav_connections.setStyleSheet(BTN_SIDEBAR_ACTIVE)
        self._nav_connections.setCursor(Qt.PointingHandCursor)
        self._nav_connections.clicked.connect(lambda: self._set_nav("connections"))
        sb_layout.addWidget(self._nav_connections)

        self._nav_multiview = QPushButton("Open MultiView")
        self._nav_multiview.setStyleSheet(BTN_SIDEBAR)
        self._nav_multiview.setCursor(Qt.PointingHandCursor)
        self._nav_multiview.clicked.connect(self._open_multiview)
        sb_layout.addWidget(self._nav_multiview)

        sb_layout.addSpacing(10)

        sec_label = QLabel("MANAGEMENT")
        sec_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; font-weight: 800; letter-spacing: 1px; margin-top: 8px;"
        )
        sb_layout.addWidget(sec_label)

        self._nav_save = QPushButton("Save Config")
        self._nav_save.setStyleSheet(BTN_SIDEBAR)
        self._nav_save.setCursor(Qt.PointingHandCursor)
        self._nav_save.clicked.connect(self._save_connections)
        sb_layout.addWidget(self._nav_save)

        self._nav_load = QPushButton("Load Config")
        self._nav_load.setStyleSheet(BTN_SIDEBAR)
        self._nav_load.setCursor(Qt.PointingHandCursor)
        self._nav_load.clicked.connect(self._load_connections_dialog)
        sb_layout.addWidget(self._nav_load)

        sb_layout.addStretch()

        self._nav_about = QPushButton("About Application")
        self._nav_about.setStyleSheet(BTN_SIDEBAR)
        self._nav_about.setCursor(Qt.PointingHandCursor)
        self._nav_about.clicked.connect(self._show_about)
        sb_layout.addWidget(self._nav_about)

        root_layout.addWidget(sidebar)

        # ===== MAIN CONTENT AREA =====
        content = QWidget()
        content.setObjectName("contentArea")
        content.setStyleSheet(f"QWidget#contentArea {{ background-color: {COLORS['bg_main']}; }}")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 16)
        content_layout.setSpacing(16)

        # --- Top Header ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        title = QLabel("Remote Desktop Manager")
        title.setObjectName("titleLabel")
        title_col.addWidget(title)
        subtitle = QLabel("Manage, configure H.264 bitrate, and multi-view your RDP servers")
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px;")
        title_col.addWidget(subtitle)
        header_layout.addLayout(title_col)

        header_layout.addStretch()

        self._multiview_btn = QPushButton("Open MultiView (4x4)")
        self._multiview_btn.setStyleSheet(BTN_MULTIVIEW)
        self._multiview_btn.setCursor(Qt.PointingHandCursor)
        self._multiview_btn.setFixedHeight(46)
        self._multiview_btn.setMinimumWidth(220)
        self._multiview_btn.clicked.connect(self._open_multiview)
        header_layout.addWidget(self._multiview_btn)

        content_layout.addLayout(header_layout)

        # --- Stat Cards Row ---
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)

        self._stat_total = StatCard("TOTAL SERVERS", "0", COLORS['green_main'])
        stats_layout.addWidget(self._stat_total)

        self._stat_connected = StatCard("CONNECTED", "0", COLORS['blue_main'])
        stats_layout.addWidget(self._stat_connected)

        self._stat_disconnected = StatCard("DISCONNECTED", "0", COLORS['red_main'])
        stats_layout.addWidget(self._stat_disconnected)

        self._stat_bitrate = StatCard("AVERAGE BITRATE", "0 kbps", "#f59e0b")
        stats_layout.addWidget(self._stat_bitrate)

        content_layout.addLayout(stats_layout)

        # --- Action Bar with Colored Buttons ---
        action_bar = QFrame()
        action_bar.setObjectName("actionBarFrame")
        action_bar.setStyleSheet(
            f"QFrame#actionBarFrame {{ background-color: {COLORS['bg_card']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 8px; }}"
        )
        action_bar.setMinimumHeight(56)
        ab_layout = QHBoxLayout(action_bar)
        ab_layout.setContentsMargins(16, 0, 16, 0)
        ab_layout.setSpacing(10)

        add_btn = QPushButton("Add Connection")
        add_btn.setStyleSheet(BTN_GREEN)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedHeight(36)
        add_btn.setMinimumWidth(140)
        add_btn.clicked.connect(lambda: self._add_connection())
        ab_layout.addWidget(add_btn)

        add_multi_btn = QPushButton("Add Multiple IPs")
        add_multi_btn.setStyleSheet(BTN_BLUE)
        add_multi_btn.setCursor(Qt.PointingHandCursor)
        add_multi_btn.setFixedHeight(36)
        add_multi_btn.setMinimumWidth(140)
        add_multi_btn.clicked.connect(self._add_multiple_connections)
        ab_layout.addWidget(add_multi_btn)

        ab_layout.addStretch()

        self._count_label = QLabel("0 / 16 Servers")
        self._count_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px; font-weight: 700; "
            f"padding-right: 8px;"
        )
        ab_layout.addWidget(self._count_label)

        ca_btn = QPushButton("Connect All")
        ca_btn.setStyleSheet(BTN_TEAL)
        ca_btn.setCursor(Qt.PointingHandCursor)
        ca_btn.setFixedHeight(36)
        ca_btn.setMinimumWidth(110)
        ca_btn.clicked.connect(self._connect_all)
        ab_layout.addWidget(ca_btn)

        da_btn = QPushButton("Disconnect All")
        da_btn.setStyleSheet(BTN_RED)
        da_btn.setCursor(Qt.PointingHandCursor)
        da_btn.setFixedHeight(36)
        da_btn.setMinimumWidth(120)
        da_btn.clicked.connect(self._disconnect_all)
        ab_layout.addWidget(da_btn)

        content_layout.addWidget(action_bar)

        # --- Connection Cards Scroll Area ---
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_area.setStyleSheet("border: none; background: transparent;")

        self._scroll_widget = QWidget()
        self._scroll_widget.setStyleSheet("background: transparent;")
        self._scroll_layout = QVBoxLayout(self._scroll_widget)
        self._scroll_layout.setSpacing(12)
        self._scroll_layout.setContentsMargins(0, 0, 10, 0)
        self._scroll_layout.addStretch()

        self._scroll_area.setWidget(self._scroll_widget)
        content_layout.addWidget(self._scroll_area, 1)

        root_layout.addWidget(content, 1)

        self.statusBar().showMessage("Ready - Configure servers and connect")
        self._update_stats()

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        file_menu.addAction("Save Connections", self._save_connections, "Ctrl+S")
        file_menu.addAction("Load Connections", self._load_connections_dialog, "Ctrl+O")
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close, "Alt+F4")

        view_menu = menubar.addMenu("&View")
        view_menu.addAction("Open MultiView", self._open_multiview, "Ctrl+M")

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("About", self._show_about)

    def _set_nav(self, page: str):
        if page == "connections":
            self._nav_connections.setStyleSheet(BTN_SIDEBAR_ACTIVE)
            self._nav_multiview.setStyleSheet(BTN_SIDEBAR)
        elif page == "multiview":
            self._nav_connections.setStyleSheet(BTN_SIDEBAR)
            self._nav_multiview.setStyleSheet(BTN_SIDEBAR_ACTIVE)

    def _add_connection(self, connection: RdpConnectionInfo = None, scroll_to_end: bool = True):
        if len(self._connections) >= self.MAX_CONNECTIONS:
            QMessageBox.warning(self, "Limit Reached",
                                f"Maximum {self.MAX_CONNECTIONS} connections allowed.")
            return

        conn = connection or RdpConnectionInfo()
        self._connections.append(conn)

        index = len(self._connections) - 1
        card = ConnectionCard(index, conn)
        card.connect_requested.connect(self._on_connect)
        card.disconnect_requested.connect(self._on_disconnect)
        card.remove_requested.connect(self._on_remove)
        card.data_changed.connect(self._on_data_changed)
        self._cards.append(card)

        self._scroll_layout.insertWidget(self._scroll_layout.count() - 1, card)
        self._update_stats()
        self.statusBar().showMessage(f"Added connection #{index + 1}")

        if scroll_to_end:
            QTimer.singleShot(100, lambda: self._scroll_area.verticalScrollBar().setValue(
                self._scroll_area.verticalScrollBar().maximum()
            ))

    def _add_multiple_connections(self):
        text, ok = QInputDialog.getMultiLineText(
            self, "Add Multiple IPs",
            "Enter IP addresses (one per line):\n"
            "Format: IP  or  IP:Port  or  IP:Port:Username:Password",
            ""
        )
        if ok and text.strip():
            lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
            for line in lines:
                parts = line.split(':')
                conn = RdpConnectionInfo()
                conn.ip_address = parts[0].strip()
                if len(parts) >= 2:
                    try:
                        conn.port = int(parts[1].strip())
                    except ValueError:
                        pass
                if len(parts) >= 3:
                    conn.username = parts[2].strip()
                if len(parts) >= 4:
                    conn.password = parts[3].strip()
                self._add_connection(conn)

    def _on_connect(self, index: int):
        if index >= len(self._connections):
            return

        card = self._cards[index]
        conn = card.get_connection_info()
        self._connections[index] = conn

        ip = conn.ip_address.strip()
        if not ip:
            QMessageBox.warning(self, "Thiếu IP", "Vui lòng nhập địa chỉ IP!")
            return

        card.set_connecting()
        self.statusBar().showMessage(f"Đang chuẩn bị kết nối {conn.display_name()} ({ip}:{conn.port})...")

        # Automatically open and show MultiView window if not yet visible
        if self._multiview_window is None:
            self._open_multiview()
        else:
            self._multiview_window.show()
            self._multiview_window.activateWindow()

        try:
            # Clean up any existing widget for this slot
            if index in self._rdp_widgets:
                self._on_disconnect(index)

            # Create EmbeddedMstscWidget
            rdp = EmbeddedMstscWidget(
                ip=ip,
                port=conn.port,
                username=conn.username,
                password=conn.password,
                domain=conn.domain,
                width=conn.desktop_width,
                height=conn.desktop_height,
                color_depth=conn.color_depth,
                use_h264=conn.use_h264,
                network_type=conn.network_type,
                smart_sizing=True,
                enable_nla=conn.enable_nla,
                compress=conn.compress,
                audio_mode=getattr(conn, 'audio_mode', 1),
            )

            # Connect signals
            rdp.connected.connect(lambda idx=index: self._on_rdp_connected(idx))
            rdp.disconnected.connect(lambda idx=index: self._on_rdp_disconnected(idx))
            rdp.failed.connect(lambda msg, idx=index: self._on_rdp_failed(idx, msg))

            self._rdp_widgets[index] = rdp
            conn.slot_index = index

            # Place widget inside the MultiView slot!
            if self._multiview_window and index < len(self._multiview_window._cells):
                self._multiview_window.set_rdp_widget(index, rdp)

            # Start connecting and embedding into slot
            rdp.start()
            self.statusBar().showMessage(f"Đang kết nối và nhúng {conn.display_name()} vào MultiView...")

        except Exception as e:
            card.set_failed(str(e))
            logger.error(f"Connection error: {e}", exc_info=True)

    def _on_rdp_connected(self, index: int):
        """Called when embedded RDP session connects successfully."""
        if index < len(self._cards):
            self._cards[index].set_connected(True)
        if index < len(self._connections):
            self._connections[index].is_connected = True
        self._update_stats()
        ip = self._connections[index].ip_address if index < len(self._connections) else ""
        name = self._connections[index].display_name() if index < len(self._connections) else f"Slot #{index+1}"
        self.statusBar().showMessage(f"✓ Đã kết nối và hiển thị {name} ({ip}) trên MultiView")

    def _on_rdp_disconnected(self, index: int, reason: int = 0):
        """Called when session ends or is closed."""
        if index < len(self._cards):
            self._cards[index].set_connected(False)
        if index < len(self._connections):
            self._connections[index].is_connected = False
        if index in self._rdp_widgets:
            del self._rdp_widgets[index]
        self._update_stats()
        self.statusBar().showMessage(f"Session #{index + 1} disconnected")

    def _on_rdp_failed(self, index: int, message: str):
        """Called when connection fails or timeout occurs."""
        if index < len(self._cards):
            self._cards[index].set_failed(message)
        if index < len(self._connections):
            self._connections[index].is_connected = False
        if index in self._rdp_widgets:
            del self._rdp_widgets[index]
        self._update_stats()
        self.statusBar().showMessage(f"Lỗi Slot #{index + 1}: {message}")

    def _on_disconnect(self, index: int):
        if index in self._rdp_widgets:
            widget = self._rdp_widgets[index]
            try:
                if hasattr(widget, 'cleanup'):
                    widget.cleanup()
                elif hasattr(widget, 'stop'):
                    widget.stop()
                elif hasattr(widget, 'terminate'):
                    widget.terminate()
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
            del self._rdp_widgets[index]

            if self._multiview_window:
                self._multiview_window.remove_rdp_widget(index)

        if index < len(self._connections):
            self._connections[index].is_connected = False
        if index < len(self._cards):
            self._cards[index].set_connected(False)

        self._update_stats()
        self.statusBar().showMessage(f"Disconnected server #{index + 1}")

    def _on_remove(self, index: int):
        if index >= len(self._connections):
            return

        if index in self._rdp_widgets:
            self._on_disconnect(index)

        card = self._cards.pop(index)
        card.setParent(None)
        card.deleteLater()
        self._connections.pop(index)

        for i, c in enumerate(self._cards):
            c.set_index(i)

        new_rdp = {}
        for k, v in self._rdp_widgets.items():
            if k > index:
                new_rdp[k - 1] = v
            elif k < index:
                new_rdp[k] = v
        self._rdp_widgets = new_rdp

        self._update_stats()
        self.statusBar().showMessage("Removed connection")

    def _on_data_changed(self, index: int):
        if index < len(self._cards):
            self._connections[index] = self._cards[index].get_connection_info()
        self._update_stats()
        self._auto_save()

    def _on_rdp_connected(self, index: int):
        """Called ONLY when Windows RDP handshake succeeds."""
        if index < len(self._cards):
            self._cards[index].set_connected(True)
        if index < len(self._connections):
            self._connections[index].is_connected = True
        self._update_stats()
        ip = self._connections[index].ip_address if index < len(self._connections) else ""
        self.statusBar().showMessage(f"Connected to {ip}")

    def _on_rdp_disconnected(self, index: int, reason: int):
        """Called when session ends or is closed."""
        if index < len(self._cards):
            self._cards[index].set_connected(False)
        if index < len(self._connections):
            self._connections[index].is_connected = False
        if index in self._rdp_widgets:
            del self._rdp_widgets[index]
        self._update_stats()

    def _on_rdp_failed(self, index: int, message: str):
        """Called when server is unreachable, ping fails, or timeout occurs."""
        if index < len(self._cards):
            self._cards[index].set_failed(message)
        if index < len(self._connections):
            self._connections[index].is_connected = False
        if index in self._rdp_widgets:
            del self._rdp_widgets[index]
        self._update_stats()
        self.statusBar().showMessage(f"Server #{index + 1} connection failed: {message}")

    def _connect_all(self):
        for i, conn in enumerate(self._connections):
            if conn.ip_address and not conn.is_connected:
                self._on_connect(i)

    def _disconnect_all(self):
        for i in list(self._rdp_widgets.keys()):
            self._on_disconnect(i)

    def _open_multiview(self):
        if self._multiview_window:
            self._multiview_window.activateWindow()
            self._multiview_window.raise_()
            return

        connections = []
        for i, card in enumerate(self._cards):
            conn = card.get_connection_info()
            self._connections[i] = conn
            connections.append(conn)

        self._multiview_window = MultiViewWindow(connections)
        self._multiview_window.connection_requested.connect(self._on_multiview_connect)
        self._multiview_window.disconnection_requested.connect(self._on_multiview_disconnect)
        self._multiview_window.closed.connect(self._on_multiview_closed)

        for idx, rdp in self._rdp_widgets.items():
            if idx < 16:
                self._multiview_window.set_rdp_widget(idx, rdp)

        self._multiview_window.show()
        self._set_nav("multiview")
        self.statusBar().showMessage("MultiView window opened")

    def _on_multiview_connect(self, slot_index: int, connection: RdpConnectionInfo):
        self._on_connect(slot_index)

    def _on_multiview_disconnect(self, slot_index: int):
        self._on_disconnect(slot_index)

    def _on_multiview_closed(self):
        self._multiview_window = None
        self._set_nav("connections")
        self.statusBar().showMessage("MultiView window closed")

    def _update_stats(self):
        total = len(self._connections)
        connected = sum(1 for c in self._connections if c.is_connected)
        disconnected = total - connected

        self._stat_total.set_value(str(total))
        self._stat_connected.set_value(str(connected))
        self._stat_disconnected.set_value(str(disconnected))
        self._count_label.setText(f"{total} / {self.MAX_CONNECTIONS} Servers")

        if total > 0:
            avg = sum(c.bitrate_kbps for c in self._connections) // total
            self._stat_bitrate.set_value(f"{avg} kbps")
        else:
            self._stat_bitrate.set_value("0 kbps")

    def _save_connections(self):
        connections = [card.get_connection_info() for card in self._cards]
        try:
            save_connections(connections)
            self.statusBar().showMessage("Connections saved successfully")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{e}")

    def _auto_save(self):
        if not hasattr(self, '_auto_save_timer'):
            self._auto_save_timer = QTimer(self)
            self._auto_save_timer.setSingleShot(True)
            self._auto_save_timer.timeout.connect(self._save_connections)
        self._auto_save_timer.start(2000)

    def _load_saved_connections(self):
        connections = load_connections()
        if not connections:
            for i in range(1, 11):
                connections.append(RdpConnectionInfo(
                    name=f"Server {i:02d}",
                    ip_address=f"192.168.1.{100 + i}",
                    port=3389,
                    username="administrator",
                    use_h264=True,
                    bitrate_kbps=15000,
                    desktop_width=1920,
                    desktop_height=1080
                ))
            save_connections(connections)

        for conn in connections:
            self._add_connection(conn, scroll_to_end=False)

        self.statusBar().showMessage(f"Loaded {len(connections)} saved connections")
        QTimer.singleShot(150, lambda: self._scroll_area.verticalScrollBar().setValue(0))

    def _load_connections_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load Connections", "", "JSON Files (*.json);;All Files (*)")
        if filepath:
            connections = load_connections(filepath)
            while self._cards:
                self._on_remove(0)
            for conn in connections:
                self._add_connection(conn, scroll_to_end=False)
            QTimer.singleShot(150, lambda: self._scroll_area.verticalScrollBar().setValue(0))

    def _show_about(self):
        from app.about_dialog import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec_()

    def closeEvent(self, event):
        self._save_connections()
        if self._multiview_window:
            self._multiview_window.close()
        for idx in list(self._rdp_widgets.keys()):
            try:
                self._rdp_widgets[idx].disconnect_rdp()
                self._rdp_widgets[idx].cleanup()
            except Exception:
                pass
        self._rdp_widgets.clear()
        super().closeEvent(event)
