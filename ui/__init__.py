"""
UI package for Project-X PyQt6 desktop user interface components.
"""

from ui.main_window import MainWindow
from ui.hex_viewer import HexViewerWidget
from ui.dashboard import DashboardWidget
from ui.eraser_bridge import EraserBridge
from ui.erasure_window import ErasureWindowWidget
from ui.gallery import GalleryWidget
from ui.mode_selector import ModeSelectorWidget
from ui.recovery_window import RecoveryWindowWidget

__all__ = [
    "MainWindow",
    "HexViewerWidget",
    "DashboardWidget",
    "EraserBridge",
    "ErasureWindowWidget",
    "GalleryWidget",
    "ModeSelectorWidget",
    "RecoveryWindowWidget",
]