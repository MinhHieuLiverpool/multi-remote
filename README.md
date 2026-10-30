# Multi Remote Desktop Manager

A modern, high-performance Windows Remote Desktop (RDP) management tool with an IoT-style dark dashboard, MultiView grid layout (up to 16 slots), live screen capture, and real-time remote session embedding.

---

## 🌟 Key Features

- **Dark IoT Modern Dashboard**: High-contrast, sleek UI built with PyQt5.
- **Multi-Server Preset Management**: Easily save, configure, and connect to multiple remote servers (IP, custom RDP Port, Domain, Resolution, Color Depth, Bitrate, H.264 / AVC acceleration).
- **MultiView Grid (Up to 16 Slots / 4x4)**:
  - Customizable grid layouts (1x1, 2x2, 3x3, 4x4, 2x3, custom).
  - Embeds real Windows RDP sessions directly inside grid slots without popup clutter.
  - **Single-Click Slot Zoom**: Click any slot to expand it to 100% full application window.
  - **Double-Click or Backspace / ESC**: Seamlessly restore back to the grid view.
- **Local Live Screen Capture**: Add real-time local monitor capture feeds (Monitor 1, Monitor 2, etc.) into any MultiView slot at 20 FPS.
- **Smart Audio Routing**:
  - Keep audio on the remote PC (default: no sound device hijacking / muting on remote client).
  - Play remote audio locally or mute on demand.
- **Standalone Build Script**: Preconfigured PyInstaller script (`build_exe.py`) to produce a portable `.exe`.

---

## 🚀 Getting Started

### 1. Requirements

- Windows 10 / 11 (64-bit)
- Python 3.10+
- Dependencies listed in `requirements.txt`

### 2. Installation

Clone this repository and install dependencies:

```bash
git clone https://github.com/MinhHieuLiverpool/multi-remote.git
cd multi-remote
pip install -r requirements.txt
```

### 3. Run Application

```bash
python main.py
```

### 4. Build Standalone `.exe`

Run the included build script:

```bash
python build_exe.py
# or double-click build.bat
```

The resulting executable will be placed in `dist/MultiRemoteDesktop.exe`.

---

## 📁 Project Structure

```
multi-remote/
├── app/
│   ├── about_dialog.py          # About & system specs dialog
│   ├── check.svg                # Checkmark asset for custom styled checkboxes
│   ├── connection_panel.py      # Connection card widgets & parameters UI
│   ├── embedded_mstsc.py        # Windows RDP native window embedder (Win32 / Qt)
│   ├── main_window.py           # Dashboard window with sidebar & navigation
│   ├── models.py                # RdpConnectionInfo dataclass & JSON storage
│   ├── multiview_window.py      # MultiView grid (4x4) & 100% slot zoom manager
│   ├── rdp_launcher.py          # RDP file generator & mstsc launcher
│   ├── rdp_widget.py            # ActiveX fallback wrapper
│   ├── screen_capture_widget.py # Live local screen grabber
│   └── styles.py                # Global dark theme stylesheet & color palette
├── build.bat                    # 1-Click build batch script
├── build_exe.py                 # PyInstaller automated build pipeline
├── connections.json             # Saved connection presets
├── main.py                      # Application entry point
├── MultiRemoteDesktop.spec      # PyInstaller spec configuration
└── requirements.txt             # Python package dependencies
```

---

## 📄 License

MIT License.

