"""
Source Display Window - Hiển thị THUẦN source, không có bất kỳ UI nào trên source.
- Đọc cấu hình từ custom_multiview_config.json.
- Flatten tất cả leaf slot thành 1 lưới phẳng.
- Mỗi ô chỉ hiện source (ScreenCapture hoặc RDP), không header, không dropdown, không border thừa.
- Master slot có viền vàng mỏng để phân biệt.
- Double click vào ô -> Focus 100%. ESC hoặc double click lại -> quay về lưới.
"""
import os
import json
import math
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QSizePolicy, QApplication, QStackedWidget
)
from PyQt5.QtCore import Qt, pyqtSignal

from app.screen_capture_widget import ScreenCaptureWidget
from app.embedded_mstsc import EmbeddedMstscWidget
from app.models import RdpConnectionInfo
from app.styles import COLORS, BTN_TEAL

logger = logging.getLogger(__name__)

CONFIG_FILE = "custom_multiview_config.json"

# Style cho ô source: hoàn toàn trong suốt, không border
CELL_EMPTY_STYLE = """
QFrame#srcCell {
    background-color: #0b0f19;
    border: 1px solid #1e293b;
    border-radius: 4px;
}
"""

CELL_ACTIVE_STYLE = """
QFrame#srcCell {
    background-color: #0b0f19;
    border: none;
    border-radius: 0px;
}
"""

CELL_MASTER_STYLE = """
QFrame#srcCell {
    background-color: #0b0f19;
    border: 2px solid #f59e0b;
    border-radius: 4px;
}
"""


class SourceCell(QFrame):
    """Ô hiển thị thuần source — không header, không dropdown, không gì cả."""

    double_clicked = pyqtSignal(int)

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.is_master = False
        self.source_type = "empty"
        self.active_widget = None

        self.setObjectName("srcCell")
        self.setStyleSheet(CELL_EMPTY_STYLE)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def set_capture(self, screen_index: int):
        """Gắn live screen capture — chỉ source, không UI."""
        self.cleanup()
        self.source_type = "capture"
        cap = ScreenCaptureWidget(screen_index=screen_index, fps=20)
        self.active_widget = cap
        self._layout.addWidget(cap, 1)
        self.setStyleSheet(CELL_MASTER_STYLE if self.is_master else CELL_ACTIVE_STYLE)

    def set_rdp(self, conn: RdpConnectionInfo):
        """Gắn RDP session — chỉ source, không UI."""
        self.cleanup()
        self.source_type = "connect"
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
        self._layout.addWidget(rdp, 1)
        rdp.start()
        self.setStyleSheet(CELL_MASTER_STYLE if self.is_master else CELL_ACTIVE_STYLE)

    def set_master(self, is_master: bool):
        self.is_master = is_master
        if self.source_type == "empty":
            self.setStyleSheet(CELL_MASTER_STYLE if is_master else CELL_EMPTY_STYLE)
        else:
            self.setStyleSheet(CELL_MASTER_STYLE if is_master else CELL_ACTIVE_STYLE)

    def cleanup(self):
        if self.active_widget:
            try:
                if hasattr(self.active_widget, 'cleanup'):
                    self.active_widget.cleanup()
                elif hasattr(self.active_widget, 'stop'):
                    self.active_widget.stop()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
            self.active_widget.setParent(None)
            self.active_widget.deleteLater()
            self.active_widget = None
        self.source_type = "empty"

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.index)
        super().mouseDoubleClickEvent(event)


class SourceDisplayWindow(QMainWindow):
    """
    Cửa sổ hiển thị THUẦN source — không có bất kỳ UI nào trên source.
    - Đọc config từ custom_multiview_config.json
    - Flatten tất cả leaf slot -> grid phẳng
    - Mỗi ô chỉ hiện source (Capture / RDP), không header, không dropdown
    - Double click = Focus 100%
    """

    closed = pyqtSignal()

    def __init__(self, connections: list = None, parent=None):
        super().__init__(parent)
        self.connections = connections or []
        self._cells = []
        self._focused_index = -1
        self._is_fullscreen = False

        self.setWindowTitle("MultiView — Source Display")
        self.setMinimumSize(1100, 750)
        self.resize(1400, 900)
        self.setStyleSheet(f"QMainWindow {{ background-color: #0b0f19; }}")

        self._setup_ui()
        self._load_and_display()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self._main_layout = QVBoxLayout(central)
        self._main_layout.setContentsMargins(2, 2, 2, 2)
        self._main_layout.setSpacing(2)

        # Thanh top bar cực nhỏ gọn (chỉ nút toàn màn hình)
        self._topbar = QFrame()
        self._topbar.setFixedHeight(36)
        self._topbar.setStyleSheet(
            f"background-color: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; border-radius: 4px;"
        )
        tb_layout = QHBoxLayout(self._topbar)
        tb_layout.setContentsMargins(10, 0, 10, 0)
        tb_layout.setSpacing(8)

        title = QLabel("MultiView — Source Display (Double click để Focus / ESC để quay lại)")
        title.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 700;")
        tb_layout.addWidget(title)

        tb_layout.addStretch()

        self._fs_btn = QPushButton("Toàn màn hình")
        self._fs_btn.setStyleSheet(BTN_TEAL)
        self._fs_btn.setCursor(Qt.PointingHandCursor)
        self._fs_btn.setFixedHeight(28)
        self._fs_btn.clicked.connect(self._toggle_fullscreen)
        tb_layout.addWidget(self._fs_btn)

        self._main_layout.addWidget(self._topbar)

        # Grid container
        self._grid_container = QWidget()
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(2)
        self._main_layout.addWidget(self._grid_container, 1)

    def _load_and_display(self):
        """Đọc config và hiển thị source."""
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), CONFIG_FILE)
        slots_info = []
        master_id = "Ô 4"

        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                master_id = cfg.get("master_slot_id", "Ô 4")
                for s in cfg.get("slots", []):
                    if s.get("is_split", False):
                        for sub in s.get("sub_slots", []):
                            slots_info.append(sub)
                    else:
                        slots_info.append(s)
            except Exception as e:
                logger.error(f"Error reading config: {e}")

        if not slots_info:
            # Mặc định: 12 ô con (3 nhóm x 4) + 1 ô master = 13 slot
            for i in range(1, 4):
                for j in range(1, 5):
                    slots_info.append({"slot_id": f"Ô {i}.{j}", "source_type": "empty"})
            slots_info.append({"slot_id": "Ô 4", "source_type": "empty"})

        # Tính grid layout tối ưu
        n = len(slots_info)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)

        # Tạo cells
        self._cells.clear()
        for idx, s_info in enumerate(slots_info):
            r, c = idx // cols, idx % cols
            cell = SourceCell(idx)
            cell.double_clicked.connect(self._on_double_click)
            self._grid_layout.addWidget(cell, r, c)
            self._cells.append(cell)

            slot_id = s_info.get("slot_id", "")
            stype = s_info.get("source_type", "empty")
            sdata = s_info.get("source_data")
            is_master = (slot_id == master_id) or s_info.get("is_master", False)

            cell.set_master(is_master)

            if stype == "capture" and sdata is not None:
                try:
                    cell.set_capture(int(sdata))
                except Exception as e:
                    logger.error(f"Error setting capture for slot {idx}: {e}")
            elif stype == "connect" and sdata is not None:
                conn = next(
                    (c for c in self.connections
                     if getattr(c, 'id', '') == sdata or c.ip_address == sdata),
                    None
                )
                if conn:
                    cell.set_rdp(conn)

        for r in range(rows):
            self._grid_layout.setRowStretch(r, 1)
        for c in range(cols):
            self._grid_layout.setColumnStretch(c, 1)

    def _on_double_click(self, index: int):
        """Double click -> Focus 100% hoặc quay lại grid."""
        if self._focused_index == index:
            # Quay lại grid
            for cell in self._cells:
                cell.show()
            self._focused_index = -1
        else:
            # Focus 100%
            for i, cell in enumerate(self._cells):
                if i == index:
                    cell.show()
                else:
                    cell.hide()
            self._focused_index = index

    def _toggle_fullscreen(self):
        if self._is_fullscreen or self.isFullScreen():
            self._is_fullscreen = False
            self._topbar.show()
            self._main_layout.setContentsMargins(2, 2, 2, 2)
            self._fs_btn.setText("Toàn màn hình")
            self.showNormal()
        else:
            self._is_fullscreen = True
            self._topbar.hide()
            self._main_layout.setContentsMargins(0, 0, 0, 0)
            self._fs_btn.setText("Thoát toàn màn hình")
            self.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self._focused_index >= 0:
                for cell in self._cells:
                    cell.show()
                self._focused_index = -1
                event.accept()
                return
            if self._is_fullscreen or self.isFullScreen():
                self._toggle_fullscreen()
                event.accept()
                return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        for cell in self._cells:
            cell.cleanup()
        self.closed.emit()
        super().closeEvent(event)

