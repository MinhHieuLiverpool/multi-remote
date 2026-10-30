"""
RDP ActiveX Control wrapper using QAxWidget.
Embeds the Microsoft Terminal Services ActiveX control (mstscax.dll).
Accurately tracks real Windows RDP connection states.
"""
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

logger = logging.getLogger(__name__)

try:
    from PyQt5.QAxContainer import QAxWidget
    HAS_AX = True
except ImportError:
    HAS_AX = False
    logger.warning("QAxContainer not available. RDP embedding will be disabled.")


RDP_PROG_IDS = [
    "MsRdpClient10.MsRdpClient10",
    "MsRdpClient9.MsRdpClient9",
    "MsRdpClient8.MsRdpClient8",
    "MsRdpClient7.MsRdpClient7",
    "MsTscAx.MsTscAx",
]

# Standard RDP Disconnect Reason descriptions
DISCONNECT_REASONS = {
    0:    "No info",
    1:    "Disconnected by user",
    2:    "Local disconnect",
    3:    "Remote user disconnected",
    260:  "DNS name lookup failed",
    262:  "Out of memory",
    264:  "Connection timed out",
    516:  "Host unreachable or port 3389 blocked",
    522:  "Host key mismatch (possible MITM)",
    772:  "Remote desktop services not started on server",
    1028: "DNS lookup failed (no response)",
    1032: "Session disconnected (another user logged in)",
    2056: "Licensing error",
    2308: "Connection reset by server",
    2311: "Session remotely ended",
    2312: "Server out of memory / license limit",
    3078: "NLA / CredSSP auth failed (wrong password or domain)",
    3080: "Account disabled or locked out",
    3334: "Smartcard authentication failed",
    3590: "Role service not licensed",
    3974: "NLA authentication failed (CredSSP protocol error)",
}

# Codes that indicate credential / NLA errors (NOT network unreachable)
NLA_ERROR_CODES = {3078, 3080, 3334, 3590, 3974}

# Codes that indicate network-level errors
NETWORK_ERROR_CODES = {260, 264, 516, 772, 1028}


class RdpWidget(QWidget):
    """
    Widget that wraps the Microsoft RDP ActiveX control.
    Provides methods to connect/disconnect and configure RDP settings.
    Accurately emits signals based on real Windows RDP events.
    """
    connecting = pyqtSignal()
    connected = pyqtSignal()
    disconnected = pyqtSignal(int)      # disconnect reason code
    connection_failed = pyqtSignal(str) # error message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ax_widget = None
        self._is_connected = False
        self._prog_id = None
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_connection_timeout)
        self._setup_ui()

    def _setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        if not HAS_AX:
            self._show_error("QAxContainer module not available.")
            return

        for prog_id in RDP_PROG_IDS:
            try:
                ax = QAxWidget(prog_id, self)
                server = ax.property("Server")
                self._ax_widget = ax
                self._prog_id = prog_id
                self._layout.addWidget(ax)
                logger.info(f"Created RDP control with ProgID: {prog_id}")
                self._connect_events()
                break
            except Exception as e:
                logger.debug(f"Failed to create {prog_id}: {e}")
                try:
                    ax.deleteLater()
                except Exception:
                    pass
                continue

        if self._ax_widget is None:
            self._show_error(
                "Could not create RDP ActiveX control.\n"
                "Make sure mstscax.dll is registered on Windows."
            )

    def _show_error(self, message: str):
        lbl = QLabel(message)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #ef4444; font-size: 13px; font-weight: 700; padding: 20px;")
        lbl.setWordWrap(True)
        self._layout.addWidget(lbl)

    def _connect_events(self):
        if self._ax_widget is None:
            return

        # Real ActiveX COM Events from Windows mstscax.dll
        try:
            self._ax_widget.OnConnecting.connect(self._on_connecting)
        except Exception:
            pass
        try:
            self._ax_widget.OnConnected.connect(self._on_connected)
        except Exception:
            pass
        try:
            self._ax_widget.OnLoginComplete.connect(self._on_connected)
        except Exception:
            pass
        try:
            self._ax_widget.OnDisconnected.connect(self._on_disconnected)
        except Exception:
            pass
        try:
            self._ax_widget.OnFatalError.connect(self._on_fatal_error)
        except Exception:
            pass
        try:
            self._ax_widget.OnLogonError.connect(self._on_logon_error)
        except Exception:
            pass

    def _on_connecting(self):
        logger.info("RDP Event: Connecting...")
        self.connecting.emit()

    def _on_connected(self):
        """Fired ONLY when Windows RDP successfully establishes connection."""
        self._timeout_timer.stop()
        self._is_connected = True
        logger.info("RDP Event: Connected successfully to server")
        self.connected.emit()

    def _on_disconnected(self, reason=0):
        """Fired when Windows RDP disconnects or cannot reach server."""
        self._timeout_timer.stop()
        self._is_connected = False
        reason_code = reason if isinstance(reason, int) else 0
        desc = DISCONNECT_REASONS.get(reason_code, f"Unknown disconnect code {reason_code}")
        logger.info(f"RDP Event: Disconnected, reason={reason_code} ({desc})")

        if reason_code in NLA_ERROR_CODES:
            # NLA / CredSSP authentication failure
            logger.error(f"NLA/Credential error: {desc}")
            self.connection_failed.emit(f"Xác thực thất bại: {desc}\n→ Thử: tắt NLA, hoặc kiểm tra Username/Password/Domain")
        elif reason_code in NETWORK_ERROR_CODES:
            logger.error(f"Network error: {desc}")
            self.connection_failed.emit(f"Không thể kết nối mạng: {desc}")
        elif reason_code in (0, 1, 2, 3):
            # Normal / intentional disconnect
            self.disconnected.emit(reason_code)
        else:
            self.connection_failed.emit(f"{desc} (code={reason_code})")

    def _on_fatal_error(self, error_code=0):
        self._timeout_timer.stop()
        self._is_connected = False
        msg = f"RDP Fatal error (Code: {error_code})"
        logger.error(msg)
        self.connection_failed.emit(msg)

    def _on_logon_error(self, error_code=0):
        self._timeout_timer.stop()
        self._is_connected = False
        msg = f"Login failed: Invalid credentials (Code: {error_code})"
        logger.error(msg)
        self.connection_failed.emit(msg)

    def _on_connection_timeout(self):
        """Fired if server does not respond within timeout period."""
        if not self.is_connected():
            logger.warning("RDP connection timed out (no response from server)")
            self.disconnect_rdp()
            self.connection_failed.emit("Connection timed out (Host unreachable or Port 3389 blocked)")

    def is_available(self) -> bool:
        return self._ax_widget is not None

    def is_connected(self) -> bool:
        if not self.is_available():
            return False
        try:
            # 0=Disconnected, 1=Connecting, 2=Connected
            state = self._ax_widget.property("Connected")
            return state == 2
        except Exception:
            return self._is_connected

    def configure(self, ip: str, port: int = 3389, username: str = "",
                  password: str = "", domain: str = "",
                  width: int = 1920, height: int = 1080,
                  color_depth: int = 32, use_h264: bool = True,
                  bitrate_kbps: int = 15000, network_type: int = 6,
                  smart_sizing: bool = True, enable_nla: bool = True,
                  compress: bool = True):
        if not self.is_available():
            return

        ax = self._ax_widget
        try:
            ax.setProperty("Server", ip)
            ax.setProperty("UserName", username)

            # Domain: set if provided; for local accounts leave blank
            # For workgroup PCs: leave empty or use computer hostname
            # For AD domain PCs: use domain name (e.g. "CORP" or "CORP.LOCAL")
            if domain and domain.strip():
                ax.setProperty("Domain", domain.strip())
                logger.info(f"RDP: Domain set to '{domain.strip()}'")
            else:
                ax.setProperty("Domain", "")  # Explicitly clear; ensures local account auth
                logger.info("RDP: No domain set (local account or Microsoft Account login)")

            ax.setProperty("DesktopWidth", width)
            ax.setProperty("DesktopHeight", height)
            ax.setProperty("ColorDepth", color_depth)

            # Advanced Settings - try each version until one works
            adv = None
            for ver in ["AdvancedSettings9", "AdvancedSettings8", "AdvancedSettings7",
                        "AdvancedSettings6", "AdvancedSettings5", "AdvancedSettings2",
                        "AdvancedSettings"]:
                try:
                    adv = ax.querySubObject(ver)
                    if adv is not None:
                        logger.info(f"RDP: Using {ver}")
                        break
                except Exception:
                    continue

            if adv is not None:
                try:
                    adv.setProperty("RDPPort", port)
                except Exception:
                    pass

                if password:
                    try:
                        adv.setProperty("ClearTextPassword", password)
                        logger.info("RDP: Password configured via ClearTextPassword")
                    except Exception as e:
                        logger.warning(f"RDP: ClearTextPassword failed: {e} — user may need to enter password manually")

                try:
                    adv.setProperty("Compress", 1 if compress else 0)
                except Exception:
                    pass

                try:
                    # NLA / CredSSP: if disabled, server shows Windows login dialog inside RDP
                    # If enabled, credentials must be valid BEFORE connection starts
                    adv.setProperty("EnableCredSspSupport", enable_nla)
                    logger.info(f"RDP: NLA/CredSSP {'enabled' if enable_nla else 'disabled (classic login dialog)'}")
                except Exception:
                    pass

                try:
                    adv.setProperty("SmartSizing", smart_sizing)
                except Exception:
                    pass

                try:
                    adv.setProperty("NetworkConnectionType", network_type)
                except Exception:
                    pass

                if use_h264:
                    try:
                        adv.setProperty("PerformanceFlags", 0)
                        adv.setProperty("VideoPlaybackMode", 1)
                    except Exception:
                        pass

            try:
                ax.setProperty("FullScreen", False)
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Error configuring RDP: {e}")

    def connect_rdp(self):
        """Initiate real RDP connection through Microsoft ActiveX."""
        if not self.is_available():
            self.connection_failed.emit("RDP control not available")
            return

        if self.is_connected():
            return

        try:
            self._is_connected = False
            # Start 45s timeout timer - enough time for NLA dialog + user login
            self._timeout_timer.start(45000)
            self._ax_widget.dynamicCall("Connect()")
            logger.info("Real RDP Connect() initiated. Awaiting server response...")
        except Exception as e:
            self._timeout_timer.stop()
            msg = f"Connect call failed: {e}"
            logger.error(msg)
            self.connection_failed.emit(msg)

    def disconnect_rdp(self):
        """Disconnect RDP session."""
        self._timeout_timer.stop()
        if not self.is_available():
            return
        try:
            self._ax_widget.dynamicCall("Disconnect()")
            self._is_connected = False
            self.disconnected.emit(2)
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
            self._is_connected = False

    def cleanup(self):
        self._timeout_timer.stop()
        if self._is_connected:
            try:
                self.disconnect_rdp()
            except Exception:
                pass
        if self._ax_widget:
            try:
                self._ax_widget.close()
                self._ax_widget.deleteLater()
            except Exception:
                pass
            self._ax_widget = None
