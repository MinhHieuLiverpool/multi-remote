"""
Shortcut Manager - Handles customizable keyboard shortcuts to switch slots to Master.
Saves and loads keybindings from shortcuts.json.
"""
import os
import json
import logging
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)

DEFAULT_SHORTCUTS = {
    # slot_index (1-based string) -> Qt Key name or key code
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    "10": "0",
    "11": "F1",
    "12": "F2",
    "13": "F3",
    "14": "F4",
    "15": "F5",
    "16": "F6",
}

KEY_NAME_TO_QT = {
    "1": Qt.Key_1, "2": Qt.Key_2, "3": Qt.Key_3, "4": Qt.Key_4,
    "5": Qt.Key_5, "6": Qt.Key_6, "7": Qt.Key_7, "8": Qt.Key_8,
    "9": Qt.Key_9, "0": Qt.Key_0,
    "F1": Qt.Key_F1, "F2": Qt.Key_F2, "F3": Qt.Key_F3, "F4": Qt.Key_F4,
    "F5": Qt.Key_F5, "F6": Qt.Key_F6, "F7": Qt.Key_F7, "F8": Qt.Key_F8,
    "F9": Qt.Key_F9, "F10": Qt.Key_F10, "F11": Qt.Key_F11, "F12": Qt.Key_F12,
}


def get_shortcuts_config_path() -> str:
    """Get absolute path to shortcuts.json."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "shortcuts.json")


class ShortcutManager:
    """Manages slot-to-master shortcut bindings."""

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ShortcutManager()
        return cls._instance

    def __init__(self):
        self.shortcuts = dict(DEFAULT_SHORTCUTS)
        self.modifier = "None"  # "None", "Ctrl", "Alt", "Shift"
        self.load()

    def load(self):
        path = get_shortcuts_config_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.modifier = data.get("modifier", "None")
                    self.shortcuts.update(data.get("shortcuts", {}))
                logger.info(f"Loaded shortcuts from {path}")
            except Exception as e:
                logger.error(f"Error loading shortcuts: {e}")

    def save(self):
        path = get_shortcuts_config_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "modifier": self.modifier,
                    "shortcuts": self.shortcuts
                }, f, indent=2)
            logger.info(f"Saved shortcuts to {path}")
        except Exception as e:
            logger.error(f"Error saving shortcuts: {e}")

    def match_slot(self, event) -> int | None:
        """
        Check if a QKeyEvent matches any configured slot shortcut.
        Returns 1-based slot index, or None.
        """
        key = event.key()
        modifiers = event.modifiers()

        # Check modifier requirement
        if self.modifier == "Ctrl" and not (modifiers & Qt.ControlModifier):
            return None
        elif self.modifier == "Alt" and not (modifiers & Qt.AltModifier):
            return None
        elif self.modifier == "Shift" and not (modifiers & Qt.ShiftModifier):
            return None
        elif self.modifier == "None" and (modifiers & (Qt.ControlModifier | Qt.AltModifier)):
            # If modifier is None, ignore keypresses holding Ctrl or Alt
            return None

        for slot_str, key_name in self.shortcuts.items():
            expected_qt_key = KEY_NAME_TO_QT.get(key_name)
            if expected_qt_key is not None and key == expected_qt_key:
                try:
                    return int(slot_str)
                except ValueError:
                    return None
        return None

