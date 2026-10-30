"""
MultiView Window - Displays multiple RDP connections and Live Screen Captures in a customizable grid.
Click slot -> Slot fills 100% of the entire app window. Double click slot (or Backspace / ESC) -> Return to grid.
"""
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QFrame, QScrollArea, QMenu,
    QSizePolicy, QInputDialog, QListView, QApplication, QStackedWidget
)
from PyQt5.QtCore import Qt, pyqtSignal

from app.rdp_widget import RdpWidget
from app.screen_capture_widget import ScreenCaptureWidget
from app.models import RdpConnectionInfo
from app.styles import (
    COLORS, MULTIVIEW_CELL_STYLE, MULTIVIEW_HEADER_STYLE,
    BTN_GREEN, BTN_BLUE, BTN_RED, BTN_TEAL, COMBOBOX_STYLE
)

logger = logging.getLogger(__name__)


class MultiViewCell(QFrame):
    """A single cell in the multiview grid - supports RDP sessions and Live Screen Captures."""

    single_clicked = pyqtSignal(int)
    double_clicked = pyqtSignal(int)
    context_menu_requested = pyqtSignal(int, object)
    capture_removed = pyqtSignal(int)

    def __init__(self, slot_index: int, parent=None):
        super().__init__(parent)
        self.slot_index = slot_index
        self.rdp_widget = None
        self.capture_widget = None
        self.connection_info = None
        self._is_active = False

        self.setObjectName("mvCell")
        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumSize(160, 120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
            lambda pos: self.context_menu_requested.emit(self.slot_index, pos)
        )
        self.setStyleSheet(MULTIVIEW_CELL_STYLE)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Header bar for the cell
        self._header = QLabel(f"Slot {slot_index + 1}")
        self._header.setFixedHeight(26)
        self._header.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._header.setStyleSheet(MULTIVIEW_HEADER_STYLE)
        self._header.setCursor(Qt.PointingHandCursor)
        self._header.setToolTip("Click to expand full window • Double-click to return to grid")

        # Forward header clicks to cell
        self._header.mousePressEvent = self._on_header_mouse_press
        self._header.mouseDoubleClickEvent = self._on_header_double_click
        self._layout.addWidget(self._header)

        # Content area
        self._content_widget = QWidget()
        self._content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._layout.addWidget(self._content_widget, 1)

        self._show_placeholder()

    def _on_header_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.single_clicked.emit(self.slot_index)
        event.accept()

    def _on_header_double_click(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.slot_index)
        event.accept()

    def _show_placeholder(self):
        self._clear_content()
        lbl = QLabel(f"Slot {self.slot_index + 1}\n\nEmpty\n(Click to expand)")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {COLORS['text_dark']}; font-size: 13px; font-weight: 700;")
        lbl.setCursor(Qt.PointingHandCursor)
        lbl.mousePressEvent = self._on_header_mouse_press
        lbl.mouseDoubleClickEvent = self._on_header_double_click
        self._content_layout.addWidget(lbl)

    def _clear_content(self):
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

    def assign_connection(self, connection: RdpConnectionInfo):
        self.connection_info = connection
        name = connection.display_name()
        self._header.setText(f" {name} - {connection.ip_address}")
        self._update_style(True)

    def set_rdp_widget(self, rdp_widget: RdpWidget):
        self._clear_content()
        if self.capture_widget:
            self.capture_widget.cleanup()
            self.capture_widget = None

        self.rdp_widget = rdp_widget
        self._content_layout.addWidget(rdp_widget, 1)
        self._is_active = True
        self._update_style(True)

    def remove_rdp_widget(self):
        if self.rdp_widget:
            self.rdp_widget.setParent(None)
            self.rdp_widget = None
        self.connection_info = None
        self._is_active = False
        self._header.setText(f" Slot {self.slot_index + 1}")
        self._show_placeholder()
        self._update_style(False)

    def set_capture_widget(self, capture_widget: ScreenCaptureWidget, title: str):
        self._clear_content()
        if self.rdp_widget:
            self.rdp_widget.cleanup()
            self.rdp_widget = None

        self.capture_widget = capture_widget
        self._content_layout.addWidget(capture_widget, 1)
        self._is_active = True
        self._header.setText(f" {title} (Live Capture)")
        self._header.setStyleSheet(
            f"color: #ffffff; font-size: 11px; font-weight: 800; "
            f"padding: 4px 8px; background-color: {COLORS['blue_main']}; "
            f"border-top-left-radius: 5px; border-top-right-radius: 5px;"
        )
        self._update_style(True)

    def remove_capture_widget(self):
        if self.capture_widget:
            self.capture_widget.cleanup()
            self.capture_widget.setParent(None)
            self.capture_widget = None
        self._is_active = False
        self._header.setText(f" Slot {self.slot_index + 1}")
        self._header.setStyleSheet(MULTIVIEW_HEADER_STYLE)
        self._show_placeholder()
        self._update_style(False)
        self.capture_removed.emit(self.slot_index)

    def is_empty(self) -> bool:
        return self.rdp_widget is None and self.capture_widget is None

    def _update_style(self, active: bool):
        self.setObjectName("mvCellActive" if active else "mvCell")
        self.setStyleSheet(MULTIVIEW_CELL_STYLE)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.single_clicked.emit(self.slot_index)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.slot_index)
        super().mouseDoubleClickEvent(event)


class MultiViewWindow(QMainWindow):
    """
    Window displaying multiple RDP sessions and Live Screen Captures in a grid.
    Click any slot -> That slot fills 100% of the entire app window!
    Double click slot (or Backspace / ESC) -> Return to grid view.
    """

    connection_requested = pyqtSignal(int, object)
    disconnection_requested = pyqtSignal(int)
    closed = pyqtSignal()

    def __init__(self, connections: list = None, parent=None):
        super().__init__(parent)
        self._connections = connections or []
        self._cells = []
        self._rdp_widgets = {}
        self._capture_widgets = {}
        self._grid_rows = 4
        self._grid_cols = 4
        self._fullscreen_slot = -1
        self._is_fullscreen_mode = False
        self._setup_ui()
        self._populate_grid()
        self._assign_connections()

    def _setup_ui(self):
        self.setWindowTitle("MultiView - Remote Desktop & Screen Grid")
        self.setMinimumSize(1200, 800)
        self.resize(1600, 950)
        self.setStyleSheet(f"QMainWindow {{ background-color: {COLORS['bg_main']}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        self._main_layout = QVBoxLayout(central)
        self._main_layout.setContentsMargins(12, 12, 12, 12)
        self._main_layout.setSpacing(10)

        # ===== Top Bar =====
        self._topbar = QFrame()
        self._topbar.setObjectName("topbar")
        self._topbar.setStyleSheet(
            f"QFrame#topbar {{ background-color: {COLORS['bg_card']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 8px; "
            f"min-height: 56px; max-height: 56px; }}"
        )
        tb_layout = QHBoxLayout(self._topbar)
        tb_layout.setContentsMargins(16, 0, 16, 0)
        tb_layout.setSpacing(12)

        title = QLabel("MultiView Monitor")
        title.setStyleSheet(f"color: #ffffff; font-size: 16px; font-weight: 800;")
        tb_layout.addWidget(title)

        self._grid_info = QLabel("4x4 (16 Slots)")
        self._grid_info.setStyleSheet(
            f"color: #042017; background-color: {COLORS['green_main']}; "
            f"border-radius: 4px; padding: 4px 10px; font-size: 12px; font-weight: 800;"
        )
        tb_layout.addWidget(self._grid_info)

        tb_layout.addStretch()

        lbl = QLabel("Layout:")
        lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; font-weight: 700;")
        tb_layout.addWidget(lbl)

        self._layout_combo = QComboBox()
        self._layout_combo.setView(QListView())
        self._layout_combo.setStyleSheet(COMBOBOX_STYLE)
        self._layout_combo.setFixedWidth(130)
        for text, data in [("1x1 Grid", (1,1)), ("2x2 Grid", (2,2)), ("3x3 Grid", (3,3)),
                           ("4x4 Grid", (4,4)), ("2x3 Grid", (2,3)), ("3x2 Grid", (3,2)),
                           ("1x4 Grid", (1,4)), ("4x1 Grid", (4,1)), ("Custom...", None)]:
            self._layout_combo.addItem(text, data)
        self._layout_combo.setCurrentIndex(3)
        self._layout_combo.currentIndexChanged.connect(self._on_layout_changed)
        tb_layout.addWidget(self._layout_combo)

        tb_layout.addSpacing(10)

        # Add Capture Button
        self._add_capture_btn = QPushButton("Add Capture")
        self._add_capture_btn.setStyleSheet(BTN_BLUE)
        self._add_capture_btn.setCursor(Qt.PointingHandCursor)
        self._add_capture_btn.setFixedHeight(36)
        self._add_capture_btn.setMinimumWidth(120)
        self._add_capture_btn.clicked.connect(self._add_capture_dialog)
        tb_layout.addWidget(self._add_capture_btn)

        # Connect All Button
        self._connect_all_btn = QPushButton("Connect All")
        self._connect_all_btn.setStyleSheet(BTN_GREEN)
        self._connect_all_btn.setCursor(Qt.PointingHandCursor)
        self._connect_all_btn.setFixedHeight(36)
        self._connect_all_btn.setMinimumWidth(110)
        self._connect_all_btn.clicked.connect(self._connect_all)
        tb_layout.addWidget(self._connect_all_btn)

        # Disconnect All Button
        self._disconnect_all_btn = QPushButton("Disconnect All")
        self._disconnect_all_btn.setStyleSheet(BTN_RED)
        self._disconnect_all_btn.setCursor(Qt.PointingHandCursor)
        self._disconnect_all_btn.setFixedHeight(36)
        self._disconnect_all_btn.setMinimumWidth(120)
        self._disconnect_all_btn.clicked.connect(self._disconnect_all)
        tb_layout.addWidget(self._disconnect_all_btn)

        # Fullscreen Button
        self._fullscreen_btn = QPushButton("Fullscreen")
        self._fullscreen_btn.setStyleSheet(BTN_TEAL)
        self._fullscreen_btn.setCursor(Qt.PointingHandCursor)
        self._fullscreen_btn.setFixedHeight(36)
        self._fullscreen_btn.setMinimumWidth(100)
        self._fullscreen_btn.clicked.connect(self._toggle_fullscreen)
        tb_layout.addWidget(self._fullscreen_btn)

        self._main_layout.addWidget(self._topbar)

        # ===== STACKED WIDGET: INDEX 0 = GRID VIEW, INDEX 1 = FULL-WINDOW SINGLE SLOT VIEW =====
        self._stack = QStackedWidget()

        # Page 0: Grid View (Scroll Area containing Grid Container)
        self._grid_container = QWidget()
        self._grid_container.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(6)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setWidget(self._grid_container)
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("background-color: transparent; border: none;")
        self._stack.addWidget(self._scroll)

        # Page 1: Single Slot Container (Takes 100% of entire window!)
        self._single_view_container = QWidget()
        self._single_view_container.setStyleSheet(f"background-color: {COLORS['bg_main']};")
        self._single_layout = QVBoxLayout(self._single_view_container)
        self._single_layout.setContentsMargins(0, 0, 0, 0)
        self._single_layout.setSpacing(0)
        self._stack.addWidget(self._single_view_container)

        self._main_layout.addWidget(self._stack, 1)

        self.statusBar().showMessage("Ready - Click any slot to view 100% full window • Double-click to return to grid")

    def _populate_grid(self):
        for cell in self._cells:
            cell.setParent(None)
        self._cells.clear()

        total = self._grid_rows * self._grid_cols
        for i in range(total):
            r, c = i // self._grid_cols, i % self._grid_cols
            cell = MultiViewCell(i)
            cell.single_clicked.connect(self._on_cell_single_click)
            cell.double_clicked.connect(self._on_cell_double_click)
            cell.context_menu_requested.connect(self._on_cell_context_menu)
            cell.capture_removed.connect(self._on_capture_removed)
            self._grid_layout.addWidget(cell, r, c)
            self._cells.append(cell)

        for r in range(self._grid_rows):
            self._grid_layout.setRowStretch(r, 1)
        for c in range(self._grid_cols):
            self._grid_layout.setColumnStretch(c, 1)

        self._grid_info.setText(f"{self._grid_rows}x{self._grid_cols} ({total} Slots)")

    def _assign_connections(self):
        for i, conn in enumerate(self._connections):
            if i < len(self._cells) and i not in self._capture_widgets:
                self._cells[i].assign_connection(conn)
                conn.slot_index = i

    def _on_cell_single_click(self, slot_index: int):
        """Click on any slot in grid view immediately expands it to 100% full app window."""
        if self._fullscreen_slot == -1:
            self._maximize_slot(slot_index)

    def _on_cell_double_click(self, slot_index: int):
        """Double-click on the expanded slot returns to grid view."""
        if self._fullscreen_slot >= 0:
            self._restore_grid()
        elif self._fullscreen_slot == -1:
            self._maximize_slot(slot_index)

    def _maximize_slot(self, slot_index: int):
        """Expand slot to fill 100% of the entire app window."""
        if slot_index < 0 or slot_index >= len(self._cells):
            return

        self._fullscreen_slot = slot_index
        cell = self._cells[slot_index]

        # Remove cell from grid layout
        self._grid_layout.removeWidget(cell)

        # Clear any old widget in single view container
        while self._single_layout.count():
            item = self._single_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # Place cell into single view container (expands to fill 100% of window!)
        self._single_layout.addWidget(cell, 1)
        cell.show()

        # Switch stacked widget to Page 1
        self._stack.setCurrentIndex(1)

        name = f"Slot #{slot_index + 1}"
        if cell.capture_widget:
            name = f"Monitor {cell.capture_widget.screen_index + 1} (Live Capture)"
        elif cell.connection_info:
            name = cell.connection_info.display_name()

        self.statusBar().showMessage(f"Full Window: {name} • Double-click slot or press Backspace / ESC to return to grid")

    def _restore_grid(self):
        """Restore all slots back to grid view."""
        if self._fullscreen_slot >= 0 and self._fullscreen_slot < len(self._cells):
            cell = self._cells[self._fullscreen_slot]
            self._single_layout.removeWidget(cell)
            r = self._fullscreen_slot // self._grid_cols
            c = self._fullscreen_slot % self._grid_cols
            self._grid_layout.addWidget(cell, r, c)
            cell.show()

        self._fullscreen_slot = -1
        # Switch stacked widget back to Page 0 (Grid)
        self._stack.setCurrentIndex(0)

        for cell in self._cells:
            cell.show()

        self.statusBar().showMessage("Returned to grid view • Click any slot to expand full window")

    def _add_capture_dialog(self):
        screens = QApplication.screens()
        if not screens:
            self.statusBar().showMessage("No screen monitors detected")
            return

        screen_choices = []
        for i, s in enumerate(screens):
            geom = s.geometry()
            name = f"Monitor {i + 1} ({geom.width()}x{geom.height()})"
            screen_choices.append(name)

        chosen_screen_str, ok = QInputDialog.getItem(
            self, "Add Screen Capture",
            "Select monitor to capture live onto MultiView:",
            screen_choices, 0, False
        )
        if not ok or not chosen_screen_str:
            return

        screen_idx = screen_choices.index(chosen_screen_str)

        target_slot = None
        for i, cell in enumerate(self._cells):
            if cell.is_empty():
                target_slot = i
                break

        if target_slot is None:
            for i, cell in enumerate(self._cells):
                if cell.capture_widget is None and (cell.rdp_widget is None or not cell.rdp_widget.is_connected()):
                    target_slot = i
                    break

        if target_slot is None:
            target_slot = 0

        cap = ScreenCaptureWidget(screen_index=screen_idx, fps=20)
        self._capture_widgets[target_slot] = cap
        self._cells[target_slot].set_capture_widget(cap, f"Monitor {screen_idx + 1}")
        self.statusBar().showMessage(f"Added live capture for Monitor {screen_idx + 1} to Slot #{target_slot + 1}")

    def _on_capture_removed(self, slot_index: int):
        if slot_index in self._capture_widgets:
            del self._capture_widgets[slot_index]
        self.statusBar().showMessage(f"Removed screen capture from Slot #{slot_index + 1}")

    def update_connections(self, connections: list):
        if self._fullscreen_slot >= 0:
            self._restore_grid()
        self._connections = connections
        for i, cell in enumerate(self._cells):
            if i not in self._capture_widgets:
                cell.remove_rdp_widget()
        self._rdp_widgets.clear()
        self._assign_connections()

    def set_rdp_widget(self, slot_index: int, rdp_widget: RdpWidget):
        if 0 <= slot_index < len(self._cells):
            if slot_index in self._capture_widgets:
                del self._capture_widgets[slot_index]
            self._rdp_widgets[slot_index] = rdp_widget
            self._cells[slot_index].set_rdp_widget(rdp_widget)

    def remove_rdp_widget(self, slot_index: int):
        if slot_index in self._rdp_widgets:
            del self._rdp_widgets[slot_index]
        if 0 <= slot_index < len(self._cells) and slot_index not in self._capture_widgets:
            self._cells[slot_index].remove_rdp_widget()

    def _on_layout_changed(self, index):
        if self._fullscreen_slot >= 0:
            self._restore_grid()

        data = self._layout_combo.currentData()
        if data is None:
            rows, ok1 = QInputDialog.getInt(self, "Custom Layout", "Rows:", 4, 1, 8)
            if not ok1:
                return
            cols, ok2 = QInputDialog.getInt(self, "Custom Layout", "Columns:", 4, 1, 8)
            if not ok2:
                return
            self._grid_rows, self._grid_cols = rows, cols
        else:
            self._grid_rows, self._grid_cols = data

        saved_rdp = {}
        for idx, rdp in list(self._rdp_widgets.items()):
            if idx < len(self._cells):
                saved_rdp[idx] = (rdp, self._cells[idx].connection_info)
                rdp.setParent(None)

        saved_cap = {}
        for idx, cap in list(self._capture_widgets.items()):
            saved_cap[idx] = (cap, cap.screen_index)
            cap.setParent(None)

        self._rdp_widgets.clear()
        self._capture_widgets.clear()
        self._populate_grid()
        self._assign_connections()

        for idx, (rdp, conn) in saved_rdp.items():
            if idx < len(self._cells) and conn:
                self._cells[idx].assign_connection(conn)
                self._cells[idx].set_rdp_widget(rdp)
                self._rdp_widgets[idx] = rdp

        for idx, (cap, screen_idx) in saved_cap.items():
            if idx < len(self._cells):
                self._capture_widgets[idx] = cap
                self._cells[idx].set_capture_widget(cap, f"Monitor {screen_idx + 1}")

        self.statusBar().showMessage(f"Layout set to {self._grid_rows}x{self._grid_cols}")

    def _on_cell_context_menu(self, slot_index: int, pos):
        cell = self._cells[slot_index]
        menu = QMenu(self)

        if cell.capture_widget:
            menu.addAction("Stop & Remove Capture", lambda: cell.remove_capture_widget())
            menu.addSeparator()
        elif cell.connection_info:
            if slot_index in self._rdp_widgets:
                menu.addAction("Disconnect", lambda: self.disconnection_requested.emit(slot_index))
            else:
                menu.addAction("Connect", lambda: self.connection_requested.emit(slot_index, cell.connection_info))
            menu.addSeparator()

        menu.addAction("Add Screen Capture Here", lambda: self._add_capture_to_slot(slot_index))
        menu.addSeparator()

        if self._fullscreen_slot == slot_index:
            menu.addAction("Return to Grid View", self._restore_grid)
        else:
            menu.addAction("Full Screen This Slot", lambda: self._maximize_slot(slot_index))

        menu.exec_(cell.mapToGlobal(pos))

    def _add_capture_to_slot(self, slot_index: int):
        screens = QApplication.screens()
        if not screens:
            return

        screen_choices = [f"Monitor {i + 1} ({s.geometry().width()}x{s.geometry().height()})" for i, s in enumerate(screens)]
        chosen_str, ok = QInputDialog.getItem(
            self, "Add Screen Capture", "Select monitor:", screen_choices, 0, False
        )
        if ok and chosen_str:
            screen_idx = screen_choices.index(chosen_str)
            cap = ScreenCaptureWidget(screen_index=screen_idx, fps=20)
            self._capture_widgets[slot_index] = cap
            self._cells[slot_index].set_capture_widget(cap, f"Monitor {screen_idx + 1}")
            self.statusBar().showMessage(f"Added Monitor {screen_idx + 1} capture to Slot #{slot_index + 1}")

    def _connect_all(self):
        for i, cell in enumerate(self._cells):
            if cell.connection_info and i not in self._rdp_widgets and i not in self._capture_widgets:
                self.connection_requested.emit(i, cell.connection_info)

    def _disconnect_all(self):
        for idx in list(self._rdp_widgets.keys()):
            self.disconnection_requested.emit(idx)

    # ===== TRUE FULLSCREEN LOGIC =====
    def _enter_fullscreen(self):
        self._is_fullscreen_mode = True
        self._topbar.hide()
        self.statusBar().hide()
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(2)
        self.showFullScreen()

    def _exit_fullscreen(self):
        self._is_fullscreen_mode = False
        self._topbar.show()
        self.statusBar().show()
        self._main_layout.setContentsMargins(12, 12, 12, 12)
        self._grid_layout.setSpacing(6)
        self._fullscreen_btn.setText("Fullscreen")
        self.showNormal()

    def _toggle_fullscreen(self):
        if self._is_fullscreen_mode or self.isFullScreen():
            self._exit_fullscreen()
        else:
            self._enter_fullscreen()

    def keyPressEvent(self, event):
        """Handle Backspace or ESC to return to grid or exit fullscreen."""
        if event.key() in (Qt.Key_Backspace, Qt.Key_Escape):
            if self._fullscreen_slot >= 0:
                self._restore_grid()
                event.accept()
                return
            elif self._is_fullscreen_mode or self.isFullScreen():
                self._exit_fullscreen()
                event.accept()
                return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if self._fullscreen_slot >= 0:
            self._restore_grid()

        for idx in list(self._capture_widgets.keys()):
            try:
                self._capture_widgets[idx].cleanup()
            except Exception:
                pass
        self._capture_widgets.clear()

        for idx in list(self._rdp_widgets.keys()):
            try:
                self._rdp_widgets[idx].disconnect_rdp()
                self._rdp_widgets[idx].cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up slot {idx}: {e}")
        self._rdp_widgets.clear()
        self.closed.emit()
        super().closeEvent(event)
