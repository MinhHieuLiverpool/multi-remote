"""Data models for RDP connections."""
from dataclasses import dataclass, field
from typing import Optional
import json
import os


@dataclass
class RdpConnectionInfo:
    """Stores RDP connection parameters."""
    name: str = ""
    ip_address: str = ""
    port: int = 3389
    username: str = ""
    password: str = ""
    domain: str = ""
    desktop_width: int = 1920
    desktop_height: int = 1080
    color_depth: int = 32          # 16, 24, 32
    use_h264: bool = True
    bitrate_kbps: int = 15000      # Target bitrate in kbps
    network_type: int = 6          # 1=Modem,2=BroadbandLow,3=Satellite,4=BroadbandHigh,5=WAN,6=LAN,7=Auto
    smart_sizing: bool = True
    enable_nla: bool = True
    compress: bool = True
    audio_mode: int = 1            # 0=This PC, 1=Remote PC (Default), 2=Mute
    # Runtime state (not saved)
    is_connected: bool = field(default=False, repr=False)
    slot_index: int = field(default=-1, repr=False)  # position in multiview grid

    def display_name(self) -> str:
        if self.name:
            return self.name
        return self.ip_address or "New Connection"

    def to_dict(self) -> dict:
        """Serialize to dict (exclude runtime state)."""
        return {
            "name": self.name,
            "ip_address": self.ip_address,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "domain": self.domain,
            "desktop_width": self.desktop_width,
            "desktop_height": self.desktop_height,
            "color_depth": self.color_depth,
            "use_h264": self.use_h264,
            "bitrate_kbps": self.bitrate_kbps,
            "network_type": self.network_type,
            "smart_sizing": self.smart_sizing,
            "enable_nla": self.enable_nla,
            "compress": self.compress,
            "audio_mode": self.audio_mode,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RdpConnectionInfo":
        """Deserialize from dict."""
        return cls(
            name=data.get("name", ""),
            ip_address=data.get("ip_address", ""),
            port=data.get("port", 3389),
            username=data.get("username", ""),
            password=data.get("password", ""),
            domain=data.get("domain", ""),
            desktop_width=data.get("desktop_width", 1920),
            desktop_height=data.get("desktop_height", 1080),
            color_depth=data.get("color_depth", 32),
            use_h264=data.get("use_h264", True),
            bitrate_kbps=data.get("bitrate_kbps", 15000),
            network_type=data.get("network_type", 6),
            smart_sizing=data.get("smart_sizing", True),
            enable_nla=data.get("enable_nla", True),
            compress=data.get("compress", True),
            audio_mode=data.get("audio_mode", 1),
        )


NETWORK_TYPES = {
    1: "Modem (56 Kbps)",
    2: "Broadband Low (256 Kbps - 2 Mbps)",
    3: "Satellite (2 Mbps - 16 Mbps)",
    4: "Broadband High (2 Mbps - 10 Mbps)",
    5: "WAN (10 Mbps+)",
    6: "LAN (10 Mbps+, low latency)",
    7: "Auto Detect",
}


RESOLUTION_PRESETS = [
    (1920, 1080, "1920×1080 (Full HD)"),
    (1280, 720, "1280×720 (HD)"),
    (1366, 768, "1366×768"),
    (1600, 900, "1600×900"),
    (2560, 1440, "2560×1440 (2K)"),
    (3840, 2160, "3840×2160 (4K)"),
    (800, 600, "800×600"),
    (1024, 768, "1024×768"),
]


import sys

def get_config_dir() -> str:
    """Get directory where connections.json should be saved/loaded."""
    if getattr(sys, "frozen", False):
        # Running as compiled .exe -> save beside the .exe
        return os.path.dirname(sys.executable)
    # Running from source .py -> save in project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def save_connections(connections: list, filepath: str = None):
    """Save connections to JSON file."""
    if filepath is None:
        filepath = os.path.join(get_config_dir(), "connections.json")
    data = [conn.to_dict() for conn in connections]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_connections(filepath: str = None) -> list:
    """Load connections from JSON file."""
    if filepath is None:
        filepath = os.path.join(get_config_dir(), "connections.json")
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [RdpConnectionInfo.from_dict(d) for d in data]
    except (json.JSONDecodeError, KeyError):
        return []


