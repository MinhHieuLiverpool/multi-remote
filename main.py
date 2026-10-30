"""
Multi Remote Desktop Manager
- Kết nối RDP tới nhiều IP (lên đến 16)
- Cấu hình H264, bitrate, resolution
- MultiView 4x4 (có thể custom layout)
"""
import sys
import os
import logging

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging to console and file (helps debug RDP connection issues)
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8")
    ]
)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from app.main_window import MainWindow


def main():
    # Enable High DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Multi Remote Desktop")
    app.setOrganizationName("MultiRemote")

    # Apply global stylesheet
    from app.styles import GLOBAL_STYLE
    app.setStyleSheet(GLOBAL_STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

