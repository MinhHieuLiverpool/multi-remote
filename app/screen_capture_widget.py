"""
Screen Capture Widget - Captures local monitor screen in real-time and displays it in a MultiView cell.
"""
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap

logger = logging.getLogger(__name__)


class ScreenCaptureWidget(QWidget):
    """
    Widget that streams a live feed of a local monitor into a cell.
    """
    capture_stopped = pyqtSignal()

    def __init__(self, screen_index: int = 0, fps: int = 20, parent=None):
        super().__init__(parent)
        self.screen_index = screen_index
        self._fps = max(1, min(fps, 30))
        self._interval_ms = int(1000 / self._fps)
        self._is_capturing = False
        self._current_pixmap = None

        self._setup_ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._grab_frame)
        self.start_capture()

    def _setup_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._video_label = QLabel(self)
        self._video_label.setAlignment(Qt.AlignCenter)
        self._video_label.setStyleSheet("background-color: #0b0f19;")
        self._video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._layout.addWidget(self._video_label)

    def start_capture(self):
        """Start streaming the local screen."""
        if not self._is_capturing:
            self._is_capturing = True
            self._timer.start(self._interval_ms)
            logger.info(f"Started live capture for Screen {self.screen_index} at {self._fps} FPS")

    def stop_capture(self):
        """Stop streaming."""
        if self._is_capturing:
            self._is_capturing = False
            self._timer.stop()
            logger.info(f"Stopped live capture for Screen {self.screen_index}")
            self.capture_stopped.emit()

    def is_capturing(self) -> bool:
        return self._is_capturing

    def _grab_frame(self):
        """Grab a single screen frame and render it."""
        try:
            screens = QApplication.screens()
            if not screens:
                return

            # Validate screen index
            idx = self.screen_index if 0 <= self.screen_index < len(screens) else 0
            screen = screens[idx]

            # Grab the desktop window
            self._current_pixmap = screen.grabWindow(0)
            self._update_display()
        except Exception as e:
            logger.error(f"Error grabbing screen frame: {e}")

    def _update_display(self):
        if self._current_pixmap and not self._current_pixmap.isNull():
            size = self._video_label.size()
            if size.width() > 10 and size.height() > 10:
                scaled = self._current_pixmap.scaled(
                    size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self._video_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display()

    def cleanup(self):
        self.stop_capture()
        self._current_pixmap = None

