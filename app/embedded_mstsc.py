"""
EmbeddedMstscWidget - Embeds a live mstsc.exe (Windows RDP) window inside a PyQt5 widget.

Strategy:
1. Launch mstsc.exe with a .rdp config file
2. Continuously poll for TscShellContainerClass window (even before it becomes visible)
3. Strip title bar & borders, then embed via QWidget.createWindowContainer
4. Track window lifetime via Win32 IsWindow(hwnd)
"""
import ctypes
import ctypes.wintypes
import logging
import subprocess
import os
import time

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QWindow

from app.rdp_launcher import (
    launch_mstsc, build_rdp_file, store_credentials,
    delete_credentials, test_port_reachable, _find_mstsc,
    trust_server_in_registry
)

logger = logging.getLogger(__name__)

# Global set of HWNDs already embedded to prevent cross-slot conflicts
CLAIMED_HWNDS = set()

# ── Win32 constants ───────────────────────────────────────────────────────────
GWL_STYLE        = -16
GWL_EXSTYLE      = -20
WS_CHILD         = 0x40000000
WS_POPUP         = 0x80000000
WS_VISIBLE       = 0x10000000
WS_CAPTION       = 0x00C00000
WS_THICKFRAME    = 0x00040000
WS_BORDER        = 0x00800000
WS_DLGFRAME      = 0x00400000
WS_SYSMENU       = 0x00080000
WS_MINIMIZEBOX   = 0x00020000
WS_MAXIMIZEBOX   = 0x00010000
WS_EX_DLGMODALFRAME = 0x00000001
WS_EX_WINDOWEDGE = 0x00000100
WS_EX_CLIENTEDGE = 0x00000200
SWP_NOZORDER     = 0x0004
SWP_NOACTIVATE   = 0x0010
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW   = 0x0040
SW_SHOW          = 5

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

EnumWindowsProc = ctypes.WINFUNCTYPE(
    ctypes.c_bool,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LPARAM
)


def _find_tsc_window(pid: int, ip: str = "") -> int | None:
    """
    Find the real TscShellContainerClass window for the RDP session.
    Does NOT filter out invisible windows (catches it early before it paints).
    """
    tsc_candidates = []

    @EnumWindowsProc
    def _cb(hwnd, _):
        if hwnd in CLAIMED_HWNDS:
            return True

        proc_id = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))
        matches_pid = (pid > 0 and proc_id.value == pid)

        # Get class name
        buf_class = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf_class, 256)
        cls = buf_class.value

        # Get window text
        length = user32.GetWindowTextLengthW(hwnd)
        title = ""
        if length > 0:
            buf_text = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf_text, length + 1)
            title = buf_text.value

        # ONLY accept TscShellContainerClass!
        if "TscShellContainerClass" in cls:
            rect = ctypes.wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            w = rect.right - rect.left
            h = rect.bottom - rect.top

            # Priority 1: matches PID exactly
            if matches_pid:
                tsc_candidates.insert(0, (1, hwnd))
            # Priority 2: title contains target IP
            elif ip and ip in title:
                tsc_candidates.append((2, hwnd))
            # Priority 3: any unclaimed TscShellContainerClass
            else:
                tsc_candidates.append((3, hwnd))

        # If it's a dialog (#32770) from our process, bring it to front so user sees it
        elif matches_pid and "#32770" in cls:
            user32.SetForegroundWindow(hwnd)

        return True

    user32.EnumWindows(_cb, 0)
    if tsc_candidates:
        tsc_candidates.sort(key=lambda x: x[0])
        best_hwnd = tsc_candidates[0][1]
        logger.info(f"Found TscShellContainerClass window HWND={best_hwnd}")
        return best_hwnd
    return None


def _strip_decorations(hwnd: int):
    """Remove title bar, borders, popup style so it acts like a true child control."""
    try:
        style = user32.GetWindowLongW(hwnd, GWL_STYLE)
        style &= ~(WS_CAPTION | WS_THICKFRAME | WS_BORDER |
                   WS_DLGFRAME | WS_SYSMENU | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_POPUP)
        style |= (WS_CHILD | WS_VISIBLE)
        user32.SetWindowLongW(hwnd, GWL_STYLE, style)

        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex_style &= ~(WS_EX_DLGMODALFRAME | WS_EX_WINDOWEDGE | WS_EX_CLIENTEDGE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

        user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0,
            SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED
        )
    except Exception as e:
        logger.error(f"Error stripping decorations: {e}")


def _reparent_window(hwnd: int, parent_hwnd: int, w: int, h: int):
    """Direct Win32 SetParent reparenting fallback."""
    try:
        user32.SetParent(hwnd, parent_hwnd)
        user32.SetWindowPos(
            hwnd, 0, 0, 0, max(w, 20), max(h, 20),
            SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED | SWP_SHOWWINDOW
        )
    except Exception as e:
        logger.error(f"Error reparenting window: {e}")


class EmbeddedMstscWidget(QWidget):
    """
    Launches mstsc.exe and embeds its window inside this Qt widget.
    """

    connected    = pyqtSignal()
    disconnected = pyqtSignal()
    failed       = pyqtSignal(str)

    def __init__(
        self,
        ip: str,
        port: int = 3389,
        username: str = "",
        password: str = "",
        domain: str = "",
        width: int = 1920,
        height: int = 1080,
        color_depth: int = 32,
        use_h264: bool = True,
        network_type: int = 6,
        smart_sizing: bool = True,
        enable_nla: bool = True,
        compress: bool = True,
        audio_mode: int = 1,
        parent=None,
    ):
        super().__init__(parent)
        self.ip       = ip
        self.port     = port
        self.username = username
        self.password = password
        self.domain   = domain

        self._conn_params = dict(
            ip=ip, port=port, username=username, password=password,
            domain=domain, width=width, height=height,
            color_depth=color_depth, use_h264=use_h264,
            network_type=network_type, smart_sizing=True,
            enable_nla=enable_nla, compress=compress,
            audio_mode=audio_mode,
        )

        self._proc:         subprocess.Popen | None = None
        self._mstsc_hwnd:   int | None = None
        self._qwindow:      QWindow | None = None
        self._container:    QWidget | None = None
        self._embedded      = False
        self._poll_count    = 0
        self._MAX_POLLS     = 400          # 400 × 150 ms = 60s max wait

        self._setup_ui()

        # Poll timer — polls every 150ms to immediately catch TscShellContainerClass
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(150)
        self._poll_timer.timeout.connect(self._poll_for_window)

        # Process watch timer — detects when mstsc window closes
        self._watch_timer = QTimer(self)
        self._watch_timer.setInterval(1000)
        self._watch_timer.timeout.connect(self._check_process)

    def _setup_ui(self):
        self.setMinimumSize(160, 120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_NativeWindow, True)
        self.setStyleSheet("background-color: #0b0f19;")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._status_lbl = QLabel("Initializing…")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        self._status_lbl.setWordWrap(True)
        self._status_lbl.setStyleSheet(
            "color: #60a5fa; font-size: 13px; font-weight: 700; padding: 20px;"
        )
        self._layout.addWidget(self._status_lbl)

    def _show_status(self, text: str, error: bool = False):
        color = "#ef4444" if error else "#60a5fa"
        self._status_lbl.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: 700; padding: 20px;"
        )
        self._status_lbl.setText(text)
        self._status_lbl.show()

    def start(self):
        """Launch mstsc.exe and begin polling for its window."""
        ip   = self._conn_params["ip"]
        port = self._conn_params["port"]

        # Quick port check
        if not test_port_reachable(ip, port, timeout=3.0):
            self._show_status(f"⚠ Cannot reach {ip}:{port}", error=True)
            self.failed.emit(f"Port {port} not reachable on {ip}")
            return

        # Suppress caution prompt in registry for this IP
        trust_server_in_registry(ip)

        # Store credentials
        if self.username and self.password:
            store_credentials(ip, port, self.username, self.password, self.domain)

        # Build .rdp file and launch
        rdp_file = build_rdp_file(**{
            k: v for k, v in self._conn_params.items()
            if k not in ("username", "password")
        }, username=self.username)

        mstsc_exe = _find_mstsc()
        try:
            self._proc = subprocess.Popen([mstsc_exe, rdp_file])
            logger.info(f"EmbeddedMstsc: launched mstsc.exe PID={self._proc.pid} for {ip}:{port}")
            self._show_status(f"⟳  Connecting to {ip}:{port}…")
            self._poll_count = 0
            self._poll_timer.start()
        except Exception as e:
            msg = f"Failed to launch mstsc.exe: {e}"
            logger.error(msg)
            self._show_status(msg, error=True)
            self.failed.emit(msg)

    def _poll_for_window(self):
        """Called every 150 ms; tries to find and embed the real TscShellContainerClass window."""
        self._poll_count += 1
        elapsed_sec = int(self._poll_count * 0.15)
        self._status_lbl.setText(f"⟳  Connecting to {self.ip}:{self.port}… ({elapsed_sec}s)")

        if self._poll_count > self._MAX_POLLS:
            self._poll_timer.stop()
            self._show_status("⚠ Timeout waiting for RDP session (60s)", error=True)
            self.stop()
            self.failed.emit("Timeout waiting for mstsc session window")
            return

        # Look for the real TscShellContainerClass session window
        hwnd = _find_tsc_window(self._proc.pid if self._proc else 0, self.ip)
        if hwnd is not None:
            logger.info(f"Matched TscShellContainerClass HWND={hwnd} for {self.ip}")
            self._poll_timer.stop()
            self._mstsc_hwnd = hwnd
            CLAIMED_HWNDS.add(hwnd)
            self._embed_window()

    def _embed_window(self):
        """Reparent the mstsc TscShellContainerClass window into this widget."""
        if not self._mstsc_hwnd:
            return

        hwnd = self._mstsc_hwnd
        logger.info(f"Embedding HWND={hwnd} into Qt widget...")

        try:
            _strip_decorations(hwnd)

            # Preferred method: QWidget.createWindowContainer
            try:
                self._qwindow = QWindow.fromWinId(hwnd)
                self._container = QWidget.createWindowContainer(self._qwindow, self)
                self._container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                self._layout.addWidget(self._container, 1)
                logger.info("Successfully embedded via createWindowContainer")
            except Exception as e:
                logger.warning(f"createWindowContainer failed: {e}. Falling back to SetParent.")
                parent_hwnd = int(self.winId())
                _reparent_window(hwnd, parent_hwnd, self.width(), self.height())

            self._embedded = True
            self._status_lbl.hide()

            user32.ShowWindow(hwnd, SW_SHOW)
            user32.SetFocus(hwnd)
            self.connected.emit()

            # Start watching for window close
            self._watch_timer.start()

        except Exception as e:
            msg = f"Embed failed: {e}"
            logger.error(msg)
            self._show_status(msg, error=True)
            self.failed.emit(msg)

    def _check_process(self):
        """Watch timer: detect when mstsc window is closed."""
        if self._mstsc_hwnd:
            if not user32.IsWindow(self._mstsc_hwnd):
                self._watch_timer.stop()
                self._embedded = False
                logger.info(f"EmbeddedMstsc: session window closed for {self.ip}")
                CLAIMED_HWNDS.discard(self._mstsc_hwnd)
                self._mstsc_hwnd = None
                delete_credentials(self.ip, self.port)
                self.disconnected.emit()

    def stop(self):
        """Terminate the embedded mstsc session."""
        self._poll_timer.stop()
        self._watch_timer.stop()
        if self._mstsc_hwnd:
            CLAIMED_HWNDS.discard(self._mstsc_hwnd)
            try:
                user32.PostMessageW(self._mstsc_hwnd, 0x0010, 0, 0) # WM_CLOSE
            except Exception:
                pass
            self._mstsc_hwnd = None

        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass
        self._proc = None
        self._embedded = False
        delete_credentials(self.ip, self.port)

    def is_connected(self) -> bool:
        return self._embedded and self._mstsc_hwnd is not None and user32.IsWindow(self._mstsc_hwnd)

    def cleanup(self):
        self.stop()

    def disconnect_rdp(self):
        """Compatibility alias for disconnect."""
        self.stop()

    def mousePressEvent(self, event):
        """Focus the embedded remote window on click."""
        if self._mstsc_hwnd:
            try:
                user32.SetFocus(self._mstsc_hwnd)
            except Exception:
                pass
        super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # If fallback SetParent was used, keep window sized
        if self._embedded and self._mstsc_hwnd and self._container is None:
            try:
                user32.MoveWindow(
                    self._mstsc_hwnd, 0, 0,
                    max(self.width(), 20), max(self.height(), 20), True
                )
            except Exception:
                pass

    def closeEvent(self, event):
        self.stop()
        super().closeEvent(event)
