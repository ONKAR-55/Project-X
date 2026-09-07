"""
DashboardWidget: Control panel for drive selection, sanitization pattern execution, and carving tasks.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QComboBox, QPushButton, QProgressBar, QTextEdit, QFileDialog
)
from PyQt6.QtCore import pyqtSignal

class DashboardWidget(QWidget):
    """PyQt6 Dashboard for drive selection and engine execution controls."""

    wipe_requested = pyqtSignal(str, str)  # drive_path, method
    scan_requested = pyqtSignal(str)       # drive_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Drive Selection Group
        drive_group = QGroupBox("Target Storage / Disk Image Selection")
        drive_layout = QHBoxLayout()
        drive_group.setLayout(drive_layout)

        drive_layout.addWidget(QLabel("Drive/Image Path:"))
        self.drive_path_input = QLineEdit()
        self.drive_path_input.setPlaceholderText("/dev/loop0 or mock_disk.img")
        drive_layout.addWidget(self.drive_path_input)

        self.browse_btn = QPushButton("Browse Image...")
        self.browse_btn.clicked.connect(self.browse_file)
        drive_layout.addWidget(self.browse_btn)

        layout.addWidget(drive_group)

        # Operations Group
        ops_group = QGroupBox("Engine Execution")
        ops_layout = QHBoxLayout()
        ops_group.setLayout(ops_layout)

        # Sanitization Controls
        wipe_box = QVBoxLayout()
        wipe_box.addWidget(QLabel("<b>Phase 1: Data Sanitization</b>"))
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "nist_800_88 (1-Pass Random)",
            "dod_5220_3pass (3-Pass DoD)",
            "dod_5220_7pass (7-Pass DoD ECE)",
            "zero (Single Pass Zero)"
        ])
        wipe_box.addWidget(self.method_combo)
        self.wipe_btn = QPushButton("Execute Sanitization")
        self.wipe_btn.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; padding: 6px;")
        self.wipe_btn.clicked.connect(self.on_wipe_click)
        wipe_box.addWidget(self.wipe_btn)
        ops_layout.addLayout(wipe_box)

        # Carver Controls
        carve_box = QVBoxLayout()
        carve_box.addWidget(QLabel("<b>Phase 2: Forensic File Carver</b>"))
        carve_box.addWidget(QLabel("Scans headers for JPEG, PNG, PDF, ZIP"))
        self.scan_btn = QPushButton("Start Forensic Carving Scan")
        self.scan_btn.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 6px;")
        self.scan_btn.clicked.connect(self.on_scan_click)
        carve_box.addWidget(self.scan_btn)
        ops_layout.addLayout(carve_box)

        layout.addWidget(ops_group)

        # Progress & Log Window
        progress_group = QGroupBox("Execution Status & Audit Output")
        progress_layout = QVBoxLayout()
        progress_group.setLayout(progress_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #0F172A; color: #38BDF8; font-family: monospace;")
        progress_layout.addWidget(self.log_output)

        layout.addWidget(progress_group)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Disk Image File", "", "Disk Images (*.img *.raw *.bin);;All Files (*)")
        if path:
            self.drive_path_input.setText(path)

    def on_wipe_click(self):
        drive = self.drive_path_input.text().strip()
        method_raw = self.method_combo.currentText().split()[0]
        if drive:
            self.wipe_requested.emit(drive, method_raw)

    def on_scan_click(self):
        drive = self.drive_path_input.text().strip()
        if drive:
            self.scan_requested.emit(drive)

    def append_log(self, text: str):
        self.log_output.append(text)

    def set_progress(self, val: float):
        self.progress_bar.setValue(int(val))
