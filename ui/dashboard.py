"""
DashboardWidget: Control panel for drive selection, system privilege status, drive partition details, and engine execution.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QComboBox, QPushButton, QProgressBar, QTextEdit, QFileDialog
)
from PyQt6.QtCore import pyqtSignal
from core.disk_io import is_admin_or_root, is_system_partition, DiskIO

class DashboardWidget(QWidget):
    """PyQt6 Dashboard for drive selection, privilege badges, and engine execution controls."""

    wipe_requested = pyqtSignal(str, str)  # drive_path, method
    scan_requested = pyqtSignal(str)       # drive_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header Privilege Badge Bar
        header_layout = QHBoxLayout()
        header_title = QLabel("<h2>Integrated Forensic Carver & Sanitization Engine</h2>")
        header_layout.addWidget(header_title)
        header_layout.addStretch()

        has_admin = is_admin_or_root()
        badge_text = "ROOT / ADMIN PRIVILEGES" if has_admin else "USER PRIVILEGES (LIMITED)"
        badge_color = "#10B981" if has_admin else "#F59E0B"
        privilege_badge = QLabel(f"<b style='background-color:{badge_color}; color:white; padding: 4px 8px; border-radius:4px;'>{badge_text}</b>")
        header_layout.addWidget(privilege_badge)
        layout.addLayout(header_layout)

        # Drive Selection Group
        drive_group = QGroupBox("Target Storage / Forensic Image Selection")
        drive_layout = QHBoxLayout()
        drive_group.setLayout(drive_layout)

        drive_layout.addWidget(QLabel("Target Path:"))
        self.drive_path_input = QLineEdit()
        self.drive_path_input.setPlaceholderText("Select raw drive (/dev/sda) or forensic image (mock_disk.img)")
        self.drive_path_input.textChanged.connect(self.update_drive_info)
        drive_layout.addWidget(self.drive_path_input)

        self.browse_btn = QPushButton("Browse Forensic Image...")
        self.browse_btn.clicked.connect(self.browse_file)
        drive_layout.addWidget(self.browse_btn)

        layout.addWidget(drive_group)

        # Partition & Drive Metadata Display
        self.drive_info_label = QLabel("Drive Info: No target selected.")
        self.drive_info_label.setStyleSheet("color: #94A3B8; font-size: 11px; padding: 2px 4px;")
        layout.addWidget(self.drive_info_label)

        # Operations Group
        ops_group = QGroupBox("Engine Execution Control")
        ops_layout = QHBoxLayout()
        ops_group.setLayout(ops_layout)

        # Sanitization Controls
        wipe_box = QVBoxLayout()
        wipe_box.addWidget(QLabel("<b>Phase 1: Secure Data Sanitization</b>"))
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "nist_800_88 (1-Pass Random / Purge)",
            "dod_5220_3pass (3-Pass DoD Wiping)",
            "dod_5220_7pass (7-Pass DoD ECE High Security)",
            "zero (Single Pass Zero Scrub)"
        ])
        wipe_box.addWidget(self.method_combo)
        self.wipe_btn = QPushButton("Execute Secure Erasure")
        self.wipe_btn.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; padding: 6px;")
        self.wipe_btn.clicked.connect(self.on_wipe_click)
        wipe_box.addWidget(self.wipe_btn)
        ops_layout.addLayout(wipe_box)

        # Carver Controls
        carve_box = QVBoxLayout()
        carve_box.addWidget(QLabel("<b>Phase 2: Forensic Recovery & Carving Engine</b>"))
        carve_box.addWidget(QLabel("Scans sector streams for JPEG, PNG, PDF, ZIP, MP4, SQLite"))
        self.scan_btn = QPushButton("Start Multithreaded Carving Scan")
        self.scan_btn.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 6px;")
        self.scan_btn.clicked.connect(self.on_scan_click)
        carve_box.addWidget(self.scan_btn)
        ops_layout.addLayout(carve_box)

        layout.addWidget(ops_group)

        # Progress & Log Window
        progress_group = QGroupBox("Execution Status & Audit Output Log")
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
        path, _ = QFileDialog.getOpenFileName(self, "Select Disk Image File", "", "Forensic Disk Images (*.img *.raw *.dd *.bin);;All Files (*)")
        if path:
            self.drive_path_input.setText(path)

    def update_drive_info(self, path: str):
        path = path.strip()
        if not path or not os.path.exists(path):
            self.drive_info_label.setText("Drive Info: Path does not exist or unselected.")
            return

        is_sys = is_system_partition(path)
        sys_str = "<b style='color:#EF4444;'>YES [SYSTEM PARTITION WARNING]</b>" if is_sys else "<span style='color:#10B981;'>NO</span>"
        try:
            size_bytes = os.path.getsize(path)
            size_mb = size_bytes / (1024 * 1024)
            self.drive_info_label.setText(
                f"Target Size: <b>{size_mb:.2f} MB</b> ({size_bytes:,} bytes) | Sector Count: <b>{size_bytes // 512:,}</b> | System Partition: {sys_str}"
            )
        except Exception:
            self.drive_info_label.setText(f"Target Path: {path} | System Partition: {sys_str}")

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

