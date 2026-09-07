"""
ModeSelectorWidget: Main application landing view allowing selection between
Forensic Data Recovery and Secure Data Erasure operations.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import pyqtSignal, Qt

class ModeSelectorWidget(QWidget):
    """Landing mode selection screen."""

    recovery_selected = pyqtSignal()
    erasure_selected = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(main_layout)

        # Header Title
        title_label = QLabel("<h1>Project-X Digital Forensics & Sanitization Suite</h1>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label = QLabel("Select an operational engine mode to proceed")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #94A3B8; font-size: 14px; margin-bottom: 30px;")

        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)

        # Mode Cards Container
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)

        # Card 1: Forensic Recovery
        recovery_card = QFrame()
        recovery_card.setFixedSize(360, 260)
        recovery_card.setStyleSheet("""
            QFrame {
                background-color: #0F172A;
                border: 2px solid #3B82F6;
                border-radius: 12px;
                padding: 20px;
            }
            QFrame:hover {
                border-color: #60A5FA;
                background-color: #1E293B;
            }
        """)
        rc_layout = QVBoxLayout()
        recovery_card.setLayout(rc_layout)

        rc_title = QLabel("<b style='color:#38BDF8; font-size:18px;'>🔍 Forensic Data Recovery</b>")
        rc_desc = QLabel(
            "Scan raw disk sectors, virtual images, or folder paths (including all nested subdirectories).\n\n"
            "Carve & recover JPEG, PNG, PDF, ZIP, MP4, and SQLite database files with confidence scoring."
        )
        rc_desc.setWordWrap(True)
        rc_desc.setStyleSheet("color: #CBD5E1; font-size: 12px;")

        btn_recovery = QPushButton("Launch Data Recovery Engine")
        btn_recovery.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        btn_recovery.clicked.connect(self.recovery_selected.emit)

        rc_layout.addWidget(rc_title)
        rc_layout.addWidget(rc_desc)
        rc_layout.addStretch()
        rc_layout.addWidget(btn_recovery)

        cards_layout.addWidget(recovery_card)

        # Card 2: Secure Erasure
        erasure_card = QFrame()
        erasure_card.setFixedSize(360, 260)
        erasure_card.setStyleSheet("""
            QFrame {
                background-color: #0F172A;
                border: 2px solid #EF4444;
                border-radius: 12px;
                padding: 20px;
            }
            QFrame:hover {
                border-color: #F87171;
                background-color: #1E293B;
            }
        """)
        ec_layout = QVBoxLayout()
        erasure_card.setLayout(ec_layout)

        ec_title = QLabel("<b style='color:#F87171; font-size:18px;'>☣️ Secure Data Erasure</b>")
        ec_desc = QLabel(
            "Sanitize storage media and raw partition images using NIST SP 800-88, DoD 5220.22-M, and zero fills.\n\n"
            "Includes system partition protection and execution audit logging."
        )
        ec_desc.setWordWrap(True)
        ec_desc.setStyleSheet("color: #CBD5E1; font-size: 12px;")

        btn_erasure = QPushButton("Launch Data Erasure Engine")
        btn_erasure.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        btn_erasure.clicked.connect(self.erasure_selected.emit)

        ec_layout.addWidget(ec_title)
        ec_layout.addWidget(ec_desc)
        ec_layout.addStretch()
        ec_layout.addWidget(btn_erasure)

        cards_layout.addWidget(erasure_card)

        main_layout.addLayout(cards_layout)