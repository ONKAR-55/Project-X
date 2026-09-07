"""
MainWindow: PyQt6 desktop application container managing separate operational windows:
- Mode Selection Landing View
- Dedicated Forensic Data Recovery Window
- Dedicated Secure Data Erasure Window
"""

from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QStatusBar
from ui.mode_selector import ModeSelectorWidget
from ui.recovery_window import RecoveryWindowWidget
from ui.erasure_window import ErasureWindowWidget

class MainWindow(QMainWindow):
    """Main application container window managing separate recovery and erasure modes."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project-X: Digital Forensics & Secure Sanitization Suite")
        self.resize(1150, 820)
        self.init_ui()

    def init_ui(self):
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Screen 0: Mode Selection Landing
        self.mode_selector = ModeSelectorWidget()
        self.mode_selector.recovery_selected.connect(self.show_recovery_window)
        self.mode_selector.erasure_selected.connect(self.show_erasure_window)
        self.stack.addWidget(self.mode_selector)

        # Screen 1: Dedicated Recovery Window
        self.recovery_window = RecoveryWindowWidget()
        self.recovery_window.back_to_menu.connect(self.show_mode_selector)
        self.stack.addWidget(self.recovery_window)

        # Screen 2: Dedicated Erasure Window
        self.erasure_window = ErasureWindowWidget()
        self.erasure_window.back_to_menu.connect(self.show_mode_selector)
        self.stack.addWidget(self.erasure_window)

        self.statusBar().showMessage("Ready - Select operational mode")

    def show_mode_selector(self):
        self.stack.setCurrentWidget(self.mode_selector)
        self.statusBar().showMessage("Main Menu - Select operational mode")

    def show_recovery_window(self):
        self.stack.setCurrentWidget(self.recovery_window)
        self.statusBar().showMessage("Forensic Data Recovery Engine Active")

    def show_erasure_window(self):
        self.stack.setCurrentWidget(self.erasure_window)
        self.statusBar().showMessage("Secure Data Erasure Engine Active")


