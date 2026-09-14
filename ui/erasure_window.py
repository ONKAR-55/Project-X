"""
ErasureWindowWidget: Dedicated Secure Data Erasure Window.
Provides user controls for Phase 1 data sanitization pattern execution and slack space scrubbing.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QComboBox, QProgressBar, QTextEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from ui.eraser_bridge import EraserBridge
from core.audit_logger import AuditLogger

class ErasureWindowWidget(QWidget):
    """Dedicated Secure Data Erasure Window."""

    back_to_menu = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.eraser_bridge = EraserBridge()
        self.audit_logger = AuditLogger()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Top Bar with Back Button
        top_layout = QHBoxLayout()
        back_btn = QPushButton("← Return to Main Menu")
        back_btn.setStyleSheet("background-color: #334155; color: white; padding: 6px 12px; border-radius: 4px;")
        back_btn.clicked.connect(self.back_to_menu.emit)
        top_layout.addWidget(back_btn)

        top_title = QLabel("<h2>Secure Data Erasure Engine</h2>")
        top_layout.addWidget(top_title)
        top_layout.addStretch()

        badge_text = "ROOT / ADMIN PRIVILEGES"
        badge_color = "#10B981"
        privilege_badge = QLabel(f"<b style='background-color:{badge_color}; color:white; padding: 4px 8px; border-radius:4px;'>{badge_text}</b>")
        top_layout.addWidget(privilege_badge)

        main_layout.addLayout(top_layout)

        # Target Selection Group
        drive_group = QGroupBox("Target Storage Device / File Selection")
        drive_layout = QHBoxLayout()
        drive_group.setLayout(drive_layout)

        drive_layout.addWidget(QLabel("Target Device/File:"))
        self.drive_path_input = QLineEdit()
        self.drive_path_input.setPlaceholderText("Enter block device (/dev/sda) or image file path")
        self.drive_path_input.textChanged.connect(self.update_drive_warning)
        drive_layout.addWidget(self.drive_path_input)

        browse_btn = QPushButton("Browse Image...")
        browse_btn.clicked.connect(self.browse_file)
        drive_layout.addWidget(browse_btn)

        main_layout.addWidget(drive_group)

        # System Partition Warning Banner
        self.sys_warning_label = QLabel("")
        self.sys_warning_label.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 12px; margin-bottom: 4px;")
        main_layout.addWidget(self.sys_warning_label)

        # Sanitization Algorithm Options
        ops_group = QGroupBox("Sanitization Pattern & Algorithm Selection")
        ops_layout = QVBoxLayout()
        ops_group.setLayout(ops_layout)

        ops_layout.addWidget(QLabel("<b>Overwriting Algorithm:</b>"))
        self.method_combo = QComboBox()
        self.method_combo.addItems([
            "nist_800_88 (NIST SP 800-88 Rev 1 - Single Pass Random / Purge)",
            "dod_5220_3pass (DoD 5220.22-M - 3-Pass Overwrite Standard)",
            "dod_5220_7pass (DoD 5220.22-M ECE - 7-Pass High-Security Wipe)",
            "zero (Single Pass Zero Scrub)"
        ])
        ops_layout.addWidget(self.method_combo)

        self.wipe_btn = QPushButton("PERMANENTLY ERASE DATA")
        self.wipe_btn.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; padding: 12px; font-size: 14px;")
        self.wipe_btn.clicked.connect(self.on_wipe_click)
        ops_layout.addWidget(self.wipe_btn)

        main_layout.addWidget(ops_group)

        # Progress Bar & Output Logs
        progress_group = QGroupBox("Execution Output & Cryptographic Log")
        progress_layout = QVBoxLayout()
        progress_group.setLayout(progress_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #0F172A; color: #38BDF8; font-family: monospace;")
        progress_layout.addWidget(self.log_output)

        main_layout.addWidget(progress_group)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Disk Image File", "", "Disk Images (*.img *.raw *.dd *.bin);;All Files (*)")
        if path:
            self.drive_path_input.setText(path)

    def update_drive_warning(self, path: str):
        path = path.strip()
        if path:
            self.sys_warning_label.setText("⚠️ WARNING: Target path appears to be a SYSTEM OS PARTITION! Erasing this path will destroy the OS!")
        else:
            self.sys_warning_label.setText("")

    def update_progress(self, val: float):
        self.progress_bar.setValue(int(val))

    def on_wipe_click(self):
        drive = self.drive_path_input.text().strip()
        if not drive or not os.path.exists(drive):
            QMessageBox.warning(self, "Invalid Path", "Please specify a valid storage target path to sanitize.")
            return

        method_raw = self.method_combo.currentText().split()[0]

        reply = QMessageBox.warning(
            self, "CONFIRM PERMANENT DELETION",
            f"CRITICAL WARNING: This action will PERMANENTLY ERASE all data on:\n'{drive}'\n\nUsing algorithm: '{method_raw}'. Data will be unrecoverable. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.log_output.append(f"Initiating sanitization pass on {drive} with {method_raw}...")
            self.progress_bar.setValue(0)
            try:
                res = self.eraser_bridge.execute_wipe(
                    drive, method_raw, progress_callback=self.update_progress
                )
                self.log_output.append(f"Sanitization Execution Status: {res.get('message')}")
                self.audit_logger.log_event("WIPE_EXECUTE", {"target": drive, "method": method_raw, "status": res.get("status")})
                QMessageBox.information(self, "Wipe Operation Complete", f"Sanitization complete: {res.get('message')}")
            except Exception as e:
                self.log_output.append(f"Error during sanitization: {e}")
                self.audit_logger.log_event("WIPE_ERROR", {"target": drive, "error": str(e), "status": "FAILED"})
                QMessageBox.critical(self, "Wipe Error", f"Erasure failed: {e}")

