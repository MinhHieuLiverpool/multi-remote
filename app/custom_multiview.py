"""
Custom MultiView Window - Tối giản, không icon/chữ ô thừa ở giữa:
- Cấu hình chuẩn theo ảnh: Ô 1, Ô 2, Ô 3 đã tách 4; Ô 4 là 1 ô đơn MASTER.
- Mỗi ô chỉ có 1 DROPDOWN để chọn Source (Capture / Connect / Master / Clear).
- Thân ô (Body) hoàn toàn sạch sẽ, không có icon hộp vuông hay chữ thừa.
- Click panel để Tách 1 thành 4 / Click header nhóm để Gộp 4 về 1.
- Nút "💾 Lưu cấu hình" để lưu và khôi phục trạng thái multiview.
"""
import os
import json
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QComboBox, QSizePolicy, QApplication,
    QListView
)
from PyQt5.QtCore import Qt, pyqtSignal

from app.embedded_mstsc import EmbeddedMstscWidget
from app.screen_capture_widget import ScreenCaptureWidget
from app.shortcut_manager import ShortcutManager
from app.shortcut_settings_dialog import ShortcutSettingsDialog
from app.models import RdpConnectionInfo
from app.styles import (
    COLORS, BTN_GREEN, BTN_BLUE, BTN_RED, BTN_TEAL
)

logger = logging.getLogger(__name__)

CONFIG_FILE_NAME = "custom_multiview_config.json"


def get_multiview_config_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, CONFIG_FILE_NAME)


NORMAL_SLOT_STYLE = f"""
QFrame#customSlot {{
    background-color: {COLORS['bg_card']};
    border: 2px solid {COLORS['border']};
    border-radius: 8px;
}}
QFrame#customSlot:hover {{
    border: 2px solid {COLORS['border_light']};
}}
"""

MASTER_SLOT_STYLE = """
QFrame#customSlot {
    background-color: #172033;
    border: 2px solid #f59e0b;
    border-radius: 8px;
}
"""

GROUP_CONTAINER_STYLE = """
QFrame#splitGroup {
    background-color: #0b0f19;
    border: 2px dashed #0284c7;
    border-radius: 8px;
}
QFrame#splitGroup:hover {
    border-color: #38bdf8;
}
"""

COMBO_STYLE = """
QComboBox {
    background-color: #0f172a;
    color: #ffffff;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
    min-width: 135px;
}
QComboBox:hover {
    border-color: #0284c7;
    background-color: #1e293b;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #94a3b8;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #0f172a;
    color: #ffffff;
    border: 1px solid #334155;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    padding: 4px;
    outline: none;
}
"""


class CustomSlot(QFrame):
    """
    Một ô trong Custom MultiView.
    - Hoàn toàn tối giản: Chỉ có 1 dropdown chọn source (Capture / Connect / Master / Clear).
    - Thân ô trống hoàn toàn, không icon, không chữ ô thừa.
    - Click vào panel ô đơn -> Tách thành 4.
    - Click vào thanh tiêu đề nhóm -> Gộp về 1.
    """

    split_toggled = pyqtSignal(object)    # self
    master_selected = pyqtSignal(object)  # self

    def __init__(self, slot_id: str, window_ref, parent=None, is_sub_slot: bool = False):
        super().__init__(parent)
        self.slot_id = slot_id             # e.g. "Ô 1", "Ô 1.1"
        self.window_ref = window_ref       # tham chiếu CustomMultiViewWindow
        self.is_sub_slot = is_sub_slot     # True nếu là ô con trong nhóm
        self.is_split = False
        self.is_master = False
        self.sub_slots = []

        self.source_type = "empty"         # "empty", "capture", "connect"
        self.source_data = None            # screen_idx hoặc RdpConnectionInfo
        self.active_widget = None

        self.setObjectName("customSlot")
        self.setStyleSheet(NORMAL_SLOT_STYLE)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.PointingHandCursor)

        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(4, 4, 4, 4)
        self._root_layout.setSpacing(4)

        self._build_single_ui()

    # =========================================================================
    # GIAO DIỆN Ô ĐƠN (SINGLE / LEAF)
    # =========================================================================
    def _build_single_ui(self):
        """Dựng giao diện ô đơn: Header nhỏ gọn + Thân trống sạch sẽ."""
        self.is_split = False
        self.sub_slots.clear()
        self.setObjectName("customSlot")

        # Xóa các widget cũ
        while self._root_layout.count():
            item = self._root_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # --- Thanh Header của ô ---
        self._header = QFrame()
        self._header.setFixedHeight(34)
        self._header.setStyleSheet("background-color: #0f172a; border-radius: 5px;")
        h_layout = QHBoxLayout(self._header)
        h_layout.setContentsMargins(8, 0, 6, 0)
        h_layout.setSpacing(6)

        # Tiêu đề ô (Ô 1, Ô 1.1,...)
        self._title_lbl = QLabel(self.slot_id)
        self._title_lbl.setStyleSheet("color: #ffffff; font-weight: 800; font-size: 12px; background: transparent;")
        h_layout.addWidget(self._title_lbl)

        # Huy hiệu Master (hiện vàng khi là Master)
        self._master_badge = QLabel("★ MASTER")
        self._master_badge.setStyleSheet(
            "background-color: #f59e0b; color: #000000; font-weight: 900; font-size: 10px; "
            "padding: 2px 6px; border-radius: 3px;"
        )
        self._master_badge.setVisible(self.is_master)
        h_layout.addWidget(self._master_badge)

        h_layout.addStretch()

        # DUY NHẤT 1 DROPDOWN để chọn source (Capture, Connect, Master, Clear)
        self._combo = QComboBox()
        self._combo.setView(QListView())
        self._combo.setStyleSheet(COMBO_STYLE)
        self._combo.setCursor(Qt.PointingHandCursor)
        self._combo.setToolTip("Chọn Source: Capture màn hình, Connect RDP, hoặc Đặt Master")
        self._populate_combo()
        self._combo.currentIndexChanged.connect(self._on_combo_changed)
        h_layout.addWidget(self._combo)

        self._root_layout.addWidget(self._header)

        # --- Vùng Body hiển thị nội dung ---
        self._body_frame = QFrame()
        self._body_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._body_frame.setStyleSheet("background-color: transparent;")
        self._body_layout = QVBoxLayout(self._body_frame)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(0)
        self._root_layout.addWidget(self._body_frame, 1)

        self._show_empty_placeholder()
        self._update_border_style()

    def _show_empty_placeholder(self):
        """Thân ô trống: Hoàn toàn sạch sẽ, không có icon hộp vuông hay chữ thừa."""
        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # =========================================================================
    # CLICK PANEL ĐỂ TÁCH 1 THÀNH 4 / GỘP 4 VỀ 1
    # =========================================================================
    def mousePressEvent(self, event):
        """Click vào panel ô đơn để tách thành 4."""
        if event.button() == Qt.LeftButton:
            # Nếu click trúng dropdown combobox thì để combobox xử lý mở menu
            child = self.childAt(event.pos())
            if child is not None and (isinstance(child, QComboBox) or child.parent() == self._combo):
                super().mousePressEvent(event)
                return

            if not self.is_sub_slot and not self.is_split:
                self.split_to_four()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Double click để Focus 100% / Thu nhỏ lại ô này."""
        if event.button() == Qt.LeftButton:
            if hasattr(self.window_ref, 'toggle_focus_slot'):
                self.window_ref.toggle_focus_slot(self)
                event.accept()
                return
        super().mouseDoubleClickEvent(event)

    # =========================================================================
    # DROPDOWN CHỌN SOURCE (CAPTURE, CONNECT, MASTER, FOCUS, CLEAR)
    # =========================================================================
    def _populate_combo(self):
        """Nạp danh sách source vào dropdown."""
        self._combo.blockSignals(True)
        self._combo.clear()

        # Tiêu đề hiện tại
        if self.source_type == "capture":
            current_title = f"📺 Monitor {self.source_data + 1}"
        elif self.source_type == "connect" and self.source_data:
            current_title = f"🖥 {self.source_data.display_name()}"
        else:
            current_title = "Chọn Source ▾"

        self._combo.addItem(current_title, ("current", None))

        # 1. Capture monitors
        screens = QApplication.screens()
        for idx, s in enumerate(screens):
            geom = s.geometry()
            self._combo.addItem(f"📺 Capture: Monitor {idx + 1} ({geom.width()}x{geom.height()})", ("capture", idx))

        # 2. RDP Connections
        connections = getattr(self.window_ref, 'connections', [])
        valid_conns = [c for c in connections if c.ip_address]
        for c in valid_conns:
            self._combo.addItem(f"🖥 Connect: {c.display_name()}", ("connect", c))

        # 3. Master option
        master_label = "✓ Đang là Master" if self.is_master else "★ Đặt làm Master"
        self._combo.addItem(master_label, ("master", None))

        # 4. Focus option
        self._combo.addItem("🔍 Focus 100% (Phóng to ô này)", ("focus", None))

        # 5. Clear option
        if self.source_type != "empty":
            self._combo.addItem("❌ Xóa Source (Trống)", ("clear", None))

        self._combo.setCurrentIndex(0)
        self._combo.blockSignals(False)

    def _on_combo_changed(self, index: int):
        """Xử lý khi người dùng chọn một mục trong dropdown."""
        if index <= 0:
            return

        item_data = self._combo.itemData(index)
        if not item_data:
            return

        action_type, val = item_data
        if action_type == "capture":
            self.set_capture_source(val)
        elif action_type == "connect":
            self.set_rdp_source(val)
        elif action_type == "master":
            self._toggle_master()
        elif action_type == "focus":
            if hasattr(self.window_ref, 'toggle_focus_slot'):
                self.window_ref.toggle_focus_slot(self)
        elif action_type == "clear":
            self.clear_source()

        self._populate_combo()

    def set_capture_source(self, screen_index: int):
        """Gắn live stream màn hình vào ô này."""
        self.cleanup_active()
        self.source_type = "capture"
        self.source_data = screen_index

        self._title_lbl.setText(f"{self.slot_id} • Monitor {screen_index + 1}")
        cap = ScreenCaptureWidget(screen_index=screen_index, fps=20)
        self.active_widget = cap

        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._body_layout.addWidget(cap, 1)

    def set_rdp_source(self, conn: RdpConnectionInfo):
        """Kết nối và nhúng màn hình RDP vào ô này."""
        self.cleanup_active()
        self.source_type = "connect"
        self.source_data = conn

        self._title_lbl.setText(f"{self.slot_id} • {conn.display_name()}")
        rdp = EmbeddedMstscWidget(
            ip=conn.ip_address,
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
        self.active_widget = rdp

        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._body_layout.addWidget(rdp, 1)
        rdp.start()

    def clear_source(self):
        """Xóa source và đưa ô về trạng thái trống."""
        self.cleanup_active()
        self.source_type = "empty"
        self.source_data = None
        self._title_lbl.setText(self.slot_id)
        self._show_empty_placeholder()

    # =========================================================================
    # MASTER SELECTION
    # =========================================================================
    def _toggle_master(self):
        """Chọn ô này làm Master."""
        self.master_selected.emit(self)

    def set_master(self, is_master: bool):
        """Cập nhật trạng thái Master và đổi style viền vàng gold."""
        self.is_master = is_master
        if hasattr(self, '_master_badge'):
            self._master_badge.setVisible(is_master)
        if hasattr(self, '_combo'):
            self._populate_combo()
        self._update_border_style()

    def _update_border_style(self):
        """Đổi viền vàng gold nếu là Master."""
        if self.is_split:
            self.setStyleSheet(GROUP_CONTAINER_STYLE)
        elif self.is_master:
            self.setStyleSheet(MASTER_SLOT_STYLE)
        else:
            self.setStyleSheet(NORMAL_SLOT_STYLE)

    # =========================================================================
    # TÁCH THÀNH 4 VÀ GỘP VỀ 1 (CLICK PANEL)
    # =========================================================================
    def toggle_split(self):
        if self.is_split:
            self.unsplit_to_single()
        else:
            self.split_to_four()

    def split_to_four(self):
        """Tách ô này thành 4 ô vuông con bên trong (lưới 2x2)."""
        self.cleanup_active()
        self.is_split = True
        self.source_type = "empty"
        self.source_data = None

        while self._root_layout.count():
            item = self._root_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Thanh tiêu đề nhóm (CLICK VÀO ĐÂY ĐỂ GỘP VỀ 1)
        group_header = QFrame()
        group_header.setFixedHeight(30)
        group_header.setStyleSheet(
            "QFrame { background-color: #0f172a; border: 1px solid #0284c7; border-radius: 5px; } "
            "QFrame:hover { background-color: #1e293b; border-color: #38bdf8; }"
        )
        group_header.setCursor(Qt.PointingHandCursor)
        # Click bất kỳ vào header để Gộp về 1 lại
        group_header.mousePressEvent = lambda e: self.unsplit_to_single() if e.button() == Qt.LeftButton else None

        gh_layout = QHBoxLayout(group_header)
        gh_layout.setContentsMargins(10, 0, 10, 0)

        title = QLabel(f"⊞ {self.slot_id} (Đã tách 4 ô) — <i>Click vào đây để <b>Gộp về 1 ô</b></i>")
        title.setStyleSheet("color: #38bdf8; font-weight: 800; font-size: 11px; background: transparent;")
        gh_layout.addWidget(title)
        gh_layout.addStretch()

        self._root_layout.addWidget(group_header)

        # Lưới 2x2 chứa 4 ô con
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)

        self.sub_slots = []
        for i in range(4):
            r, c = i // 2, i % 2
            sub_id = f"{self.slot_id}.{i + 1}"
            sub = CustomSlot(sub_id, self.window_ref, self, is_sub_slot=True)
            sub.master_selected.connect(self.window_ref.on_master_selected)
            grid.addWidget(sub, r, c)
            self.sub_slots.append(sub)

        for r in range(2):
            grid.setRowStretch(r, 1)
        for c in range(2):
            grid.setColumnStretch(c, 1)

        self._root_layout.addWidget(grid_widget, 1)
        self.setObjectName("splitGroup")
        self.setStyleSheet(GROUP_CONTAINER_STYLE)
        self.split_toggled.emit(self)

    def unsplit_to_single(self):
        """Gộp 4 ô con trở lại thành 1 ô ban đầu."""
        for s in self.sub_slots:
            s.cleanup_active()
        self.is_split = False
        self._build_single_ui()
        self.split_toggled.emit(self)

    def cleanup_active(self):
        """Dọn dẹp widget đang chạy (RDP hoặc ScreenCapture)."""
        if self.active_widget:
            try:
                if hasattr(self.active_widget, 'cleanup'):
                    self.active_widget.cleanup()
                elif hasattr(self.active_widget, 'stop'):
                    self.active_widget.stop()
            except Exception as e:
                logger.error(f"Error cleaning up widget: {e}")
            self.active_widget.setParent(None)
            self.active_widget.deleteLater()
            self.active_widget = None

    def get_all_leaf_slots(self) -> list:
        """Lấy tất cả các ô lá hiện tại (dùng để quản lý Master)."""
        if not self.is_split:
            return [self]
        leaves = []
        for s in self.sub_slots:
            leaves.extend(s.get_all_leaf_slots())
        return leaves

    def to_dict(self) -> dict:
        """Xuất thông tin cấu hình của slot để lưu vào JSON."""
        data = {
            "slot_id": self.slot_id,
            "is_split": self.is_split,
            "is_master": self.is_master,
            "source_type": self.source_type,
        }
        if self.source_type == "capture":
            data["source_data"] = self.source_data
        elif self.source_type == "connect" and self.source_data:
            data["source_data"] = getattr(self.source_data, 'id', getattr(self.source_data, 'ip_address', ''))
        else:
            data["source_data"] = None

        if self.is_split:
            data["sub_slots"] = [sub.to_dict() for sub in self.sub_slots]
        return data


class CustomMultiViewWindow(QMainWindow):
    """
    Cửa sổ Custom MultiView:
    - Ban đầu theo cấu hình: Ô 1, Ô 2, Ô 3 tách 4; Ô 4 là 1 ô đơn MASTER.
    - Mỗi ô có duy nhất 1 dropdown để chọn source.
    - Click panel để Tách 4 / Gộp 1.
    - Nút "💾 Lưu cấu hình" để lưu lại toàn bộ trạng thái multiview.
    """

    closed = pyqtSignal()

    def __init__(self, connections: list = None, parent=None):
        super().__init__(parent)
        self.connections = connections or []
        self._is_fullscreen = False
        self.current_master_slot = None
        self._focused_slot = None

        self.setWindowTitle("Custom MultiView (2x2 • Tách 4 / Gộp 1)")
        self.setMinimumSize(1100, 750)
        self.resize(1400, 900)
        self.setStyleSheet(f"QMainWindow {{ background-color: {COLORS['bg_main']}; }}")

        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self._main_layout = QVBoxLayout(central)
        self._main_layout.setContentsMargins(12, 12, 12, 12)
        self._main_layout.setSpacing(10)

        # ===== Top Bar =====
        self._topbar = QFrame()
        self._topbar.setFixedHeight(50)
        self._topbar.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; border-radius: 8px;"
        )
        tb_layout = QHBoxLayout(self._topbar)
        tb_layout.setContentsMargins(16, 0, 16, 0)
        tb_layout.setSpacing(10)

        title = QLabel("Custom MultiView (2x2) — Click Panel để Tách 4 / Gộp 1")
        title.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: 800;")
        tb_layout.addWidget(title)

        self._master_indicator = QLabel("Master: Ô 4")
        self._master_indicator.setStyleSheet(
            "background-color: #f59e0b; color: #042017; font-size: 11px; font-weight: 900; "
            "padding: 4px 10px; border-radius: 4px;"
        )
        tb_layout.addWidget(self._master_indicator)

        tb_layout.addStretch()

        # Nút Lưu cấu hình (Màu xanh lá nổi bật)
        save_btn = QPushButton("💾 Lưu cấu hình")
        save_btn.setToolTip("Lưu lại cấu hình layout, các ô đã tách và source hiện tại")
        save_btn.setStyleSheet(BTN_GREEN)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedHeight(32)
        save_btn.clicked.connect(self.save_configuration)
        tb_layout.addWidget(save_btn)

        # Nút Cài đặt Phím tắt
        shortcut_btn = QPushButton("⚡ Phím tắt Master")
        shortcut_btn.setToolTip("Cấu hình phím tắt chuyển nhanh Slot sang Master")
        shortcut_btn.setStyleSheet(BTN_BLUE)
        shortcut_btn.setCursor(Qt.PointingHandCursor)
        shortcut_btn.setFixedHeight(32)
        shortcut_btn.clicked.connect(self._open_shortcut_dialog)
        tb_layout.addWidget(shortcut_btn)

        # Nút Reset về 4 ô ban đầu
        reset_btn = QPushButton("↺ Reset 4 Ô")
        reset_btn.setToolTip("Khôi phục toàn bộ về 4 ô vuông đơn ban đầu")
        reset_btn.setStyleSheet(BTN_RED)
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setFixedHeight(32)
        reset_btn.clicked.connect(self._reset_grid)
        tb_layout.addWidget(reset_btn)

        # Nút Toàn màn hình
        self._fs_btn = QPushButton("Toàn màn hình")
        self._fs_btn.setStyleSheet(BTN_TEAL)
        self._fs_btn.setCursor(Qt.PointingHandCursor)
        self._fs_btn.setFixedHeight(32)
        self._fs_btn.clicked.connect(self._toggle_fullscreen)
        tb_layout.addWidget(self._fs_btn)

        self._main_layout.addWidget(self._topbar)

        # ===== Lưới 2x2 gồm 4 ô ban đầu =====
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(8)

        self._init_slots()
        self._main_layout.addWidget(self._grid_container, 1)

        self.statusBar().showMessage(
            "Sẵn sàng — Click panel để Tách 4 / Gộp 1 • Chọn Source ở dropdown từng ô • Nhấn 'Lưu cấu hình' để lưu lại"
        )

    def _init_slots(self):
        """Khởi tạo các ô: Nếu có file cấu hình đã lưu thì load, nếu chưa có thì áp dụng cấu hình chuẩn theo ảnh."""
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.main_slots = []
        for i in range(4):
            slot_id = f"Ô {i + 1}"
            slot = CustomSlot(slot_id, self, self._grid_container, is_sub_slot=False)
            slot.master_selected.connect(self.on_master_selected)

            row, col = i // 2, i % 2
            self._grid_layout.addWidget(slot, row, col)
            self.main_slots.append(slot)

        for r in range(2):
            self._grid_layout.setRowStretch(r, 1)
        for c in range(2):
            self._grid_layout.setColumnStretch(c, 1)

        # Kiểm tra file cấu hình đã lưu
        cfg_path = get_multiview_config_path()
        if os.path.exists(cfg_path):
            try:
                self.load_configuration(cfg_path)
                return
            except Exception as e:
                logger.error(f"Lỗi đọc config đã lưu: {e}")

        # Cấu hình mặc định đúng y chang ảnh user cung cấp:
        # Ô 1 tách 4, Ô 2 tách 4, Ô 3 tách 4, Ô 4 là 1 ô đơn MASTER
        self.main_slots[0].split_to_four()
        self.main_slots[1].split_to_four()
        self.main_slots[2].split_to_four()

        # Đặt Ô 4 làm Master
        self.on_master_selected(self.main_slots[3])

    def save_configuration(self):
        """Lưu toàn bộ cấu hình MultiView ra file custom_multiview_config.json."""
        try:
            cfg = {
                "master_slot_id": self.current_master_slot.slot_id if self.current_master_slot else "Ô 4",
                "slots": [slot.to_dict() for slot in self.main_slots]
            }
            cfg_path = get_multiview_config_path()
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            self.statusBar().showMessage("✓ Đã lưu cấu hình MultiView thành công!", 4000)
            logger.info(f"Saved custom multiview config to {cfg_path}")
        except Exception as e:
            self.statusBar().showMessage(f"❌ Lỗi lưu cấu hình: {e}", 4000)
            logger.error(f"Error saving config: {e}")

    def load_configuration(self, cfg_path: str):
        """Khôi phục cấu hình từ file JSON."""
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        slots_data = cfg.get("slots", [])
        master_slot_id = cfg.get("master_slot_id", "Ô 4")

        for idx, s_data in enumerate(slots_data):
            if idx >= len(self.main_slots):
                break
            main_slot = self.main_slots[idx]
            if s_data.get("is_split", False):
                main_slot.split_to_four()
                # Khôi phục source cho các sub_slot
                sub_datas = s_data.get("sub_slots", [])
                for sub_idx, sub_d in enumerate(sub_datas):
                    if sub_idx < len(main_slot.sub_slots):
                        sub_slot = main_slot.sub_slots[sub_idx]
                        self._apply_source_from_dict(sub_slot, sub_d)
            else:
                self._apply_source_from_dict(main_slot, s_data)

        # Chọn Master
        all_active = self.get_all_active_slots()
        target_master = next((s for s in all_active if s.slot_id == master_slot_id), None)
        if target_master:
            self.on_master_selected(target_master)
        elif all_active:
            self.on_master_selected(all_active[-1])

    def _apply_source_from_dict(self, slot: CustomSlot, data: dict):
        """Áp dụng source từ dữ liệu JSON cho 1 slot."""
        stype = data.get("source_type", "empty")
        sdata = data.get("source_data")
        if stype == "capture" and sdata is not None:
            try:
                slot.set_capture_source(int(sdata))
            except Exception as e:
                logger.error(f"Error loading capture: {e}")
        elif stype == "connect" and sdata is not None:
            # Tìm connection theo id hoặc ip
            matched = next((c for c in self.connections if getattr(c, 'id', '') == sdata or c.ip_address == sdata), None)
            if matched:
                slot.set_rdp_source(matched)

    def on_master_selected(self, target_slot: CustomSlot):
        """Khi một ô được chọn làm Master, cập nhật và bỏ Master ở các ô khác."""
        all_slots = self.get_all_active_slots()
        for s in all_slots:
            s.set_master(s == target_slot)

        self.current_master_slot = target_slot
        self._master_indicator.setText(f"Master: {target_slot.slot_id}")
        self.statusBar().showMessage(f"★ {target_slot.slot_id} đã được chọn làm MASTER")

    def get_all_active_slots(self) -> list:
        """Lấy tất cả các ô lá hiện tại."""
        leaves = []
        for s in self.main_slots:
            leaves.extend(s.get_all_leaf_slots())
        return leaves

    def _open_shortcut_dialog(self):
        """Mở hộp thoại cài đặt phím tắt."""
        dlg = ShortcutSettingsDialog(self)
        dlg.exec_()

    def _reset_grid(self):
        """Reset lưới về lại 4 ô đơn ban đầu."""
        for s in self.get_all_active_slots():
            s.cleanup_active()
        cfg_path = get_multiview_config_path()
        if os.path.exists(cfg_path):
            try:
                os.remove(cfg_path)
            except Exception:
                pass
        self._init_slots()
        self.statusBar().showMessage("Đã reset về 4 ô ban đầu")

    def _toggle_fullscreen(self):
        if self._is_fullscreen or self.isFullScreen():
            self._is_fullscreen = False
            self._topbar.show()
            self.statusBar().show()
            self._main_layout.setContentsMargins(12, 12, 12, 12)
            self._fs_btn.setText("Toàn màn hình")
            self.showNormal()
        else:
            self._is_fullscreen = True
            self._topbar.hide()
            self.statusBar().hide()
            self._main_layout.setContentsMargins(0, 0, 0, 0)
            self._fs_btn.setText("Thoát toàn màn hình")
            self.showFullScreen()

    def toggle_focus_slot(self, target_slot: CustomSlot):
        """Chuyển đổi Focus 100% cho 1 ô (hoặc trở lại lưới)."""
        if self._focused_slot == target_slot:
            self.unfocus_slot()
        else:
            self.focus_slot(target_slot)

    def focus_slot(self, target_slot: CustomSlot):
        """Phóng to 1 ô chiếm 100% diện tích cửa sổ (Focus Source)."""
        for main_s in self.main_slots:
            if main_s == target_slot:
                main_s.show()
            elif target_slot in main_s.sub_slots:
                main_s.show()
                # Ẩn các ô anh em trong cùng nhóm
                for sub in main_s.sub_slots:
                    if sub != target_slot:
                        sub.hide()
                    else:
                        sub.show()
            else:
                main_s.hide()

        self._focused_slot = target_slot
        self.statusBar().showMessage(f"🔍 Đang Focus 100%: {target_slot.slot_id} — Nhấn ESC hoặc Double Click để quay lại lưới", 5000)

    def unfocus_slot(self):
        """Quay lại lưới đầy đủ."""
        for main_s in self.main_slots:
            main_s.show()
            if main_s.is_split:
                for sub in main_s.sub_slots:
                    sub.show()
        self._focused_slot = None
        self.statusBar().showMessage("Đã quay lại lưới Custom MultiView", 3000)

    def keyPressEvent(self, event):
        # ESC -> thoát Focus hoặc thoát toàn màn hình
        if event.key() == Qt.Key_Escape:
            if self._focused_slot is not None:
                self.unfocus_slot()
                event.accept()
                return
            if self._is_fullscreen or self.isFullScreen():
                self._toggle_fullscreen()
                event.accept()
                return

        # Phím tắt chuyển slot sang Master (1-16 hoặc F1-F12)
        slot_idx = ShortcutManager.get_instance().match_slot(event)
        if slot_idx is not None:
            active_slots = self.get_all_active_slots()
            if 1 <= slot_idx <= len(active_slots):
                target = active_slots[slot_idx - 1]
                self.on_master_selected(target)
                event.accept()
                return

        super().keyPressEvent(event)

    def closeEvent(self, event):
        for s in self.get_all_active_slots():
            s.cleanup_active()
        self.closed.emit()
        super().closeEvent(event)
