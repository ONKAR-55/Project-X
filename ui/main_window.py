"""
MainWindow Module: Modern UI for Project-X Forensic Suite.
Provides a clean, dark-themed interface for Secure Erasure and Forensic Data Recovery.
"""

import sys
import os
import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QProgressBar,
    QTextEdit, QSpinBox, QCheckBox, QDateEdit, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from phase1_eraser.eraser_orchestrator import EraserOrchestrator
from phase2_carver.sector_scanner import SectorScanner
from phase2_carver.advanced_recovery_engine import AdvancedRecoveryEngine

# Modern Dark QSS Stylesheet
DARK_STYLESHEET = """
QMainWindow {
    background-color: #0f172a;
}
QWidget {
    color: #f8fafc;
    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #1e293b;
    background-color: #0f172a;
    border-radius: 8px;
}
QTabBar::tab {
    background: #1e293b;
    color: #94a3b8;
    padding: 12px 24px;
    font-weight: bold;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background: #3b82f6;
    color: #ffffff;
}
QGroupBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #38bdf8;
}
QLineEdit, QSpinBox, QDateEdit {
    background-color: #0f172a;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 8px;
    color: #f8fafc;
}
QLineEdit:focus, QSpinBox:focus, QDateEdit:focus {
    border: 1px solid #38bdf8;
}
QPushButton {
    background-color: #3b82f6;
    color: #ffffff;
    border-radius: 6px;
    padding: 10px 18px;
    font-weight: bold;
    border: none;
}
QPushButton:hover {
    background-color: #2563eb;
}
QPushButton#dangerBtn {
    background-color: #ef4444;
}
QPushButton#dangerBtn:hover {
    background-color: #dc2626;
}
QProgressBar {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #38bdf8;
    border-radius: 5px;
}
QTextEdit {
    background-color: #090d16;
    border: 1px solid #334155;
    border-radius: 6px;
    color: #38bdf8;
    font-family: 'Consolas', 'Courier New', monospace;
}
"""


# --- Background Threads ---

class EraserWorker(QThread):
    finished_signal = pyqtSignal(dict)
    log_signal = pyqtSignal(str)

    def __init__(self, target_path: str):
        super().__init__()
        self.target_path = target_path

    def run(self):
        self.log_signal.emit(f"[*] Starting secure destruction for: {self.target_path}")
        orchestrator = EraserOrchestrator(self.target_path)
        report = orchestrator.execute_full_erasure()
        self.finished_signal.emit(report)


class RecoveryWorker(QThread):
    finished_signal = pyqtSignal(dict)
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(float)

    def __init__(self, target_path: str, dest_dir: str, cutoff_date: datetime.datetime, recursive: bool):
        super().__init__()
        self.target_path = target_path
        self.dest_dir = dest_dir
        self.cutoff_date = cutoff_date
        self.recursive = recursive

    def run(self):
        self.log_signal.emit(f"[*] Scanning target: {self.target_path}")
        scanner = SectorScanner(self.target_path)
        artifacts = scanner.scan(
            recursive=self.recursive,
            progress_callback=lambda pct: self.progress_signal.emit(pct)
        )
        self.log_signal.emit(f"[+] Scan complete. Found {len(artifacts)} candidate artifacts.")

        self.log_signal.emit(f"[*] Restoring structure to: {self.dest_dir}")
        engine = AdvancedRecoveryEngine(self.dest_dir)
        report = engine.execute_recovery(
            artifacts=artifacts,
            base_scan_path=self.target_path,
            cutoff_date=self.cutoff_date,
            recursive_nested=self.recursive
        )
        self.finished_signal.emit(report)


# --- Main Application Window ---

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project-X Forensic Suite")
        self.resize(950, 700)
        self.setStyleSheet(DARK_STYLESHEET)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Title Banner
        title_label = QLabel("PROJECT-X : FORENSIC SUITE")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #38bdf8; letter-spacing: 1px;")
        main_layout.addWidget(title_label)

        # Tab Widget Navigation
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tab_eraser = QWidget()
        self.tab_recovery = QWidget()

        self.tabs.addTab(self.tab_eraser, "Phase 1: Secure Eraser")
        self.tabs.addTab(self.tab_recovery, "Phase 2: Data Recovery")

        self._build_eraser_tab()
        self._build_recovery_tab()

    # --- Phase 1: Eraser View ---

    def _build_eraser_tab(self):
        layout = QVBoxLayout(self.tab_eraser)
        layout.setSpacing(12)

        # Target Selection Group
        group_target = QGroupBox("Target File & System Trace Scrubbing")
        target_layout = QHBoxLayout(group_target)

        self.txt_erase_path = QLineEdit()
        self.txt_erase_path.setPlaceholderText("Select file to permanently destroy...")
        btn_browse_erase = QPushButton("Browse File")
        btn_browse_erase.clicked.connect(self._browse_erase_file)

        target_layout.addWidget(self.txt_erase_path)
        target_layout.addWidget(btn_browse_erase)
        layout.addWidget(group_target)

        # Action Group
        group_opts = QGroupBox("Erasure Controls")
        opts_layout = QHBoxLayout(group_opts)

        self.btn_start_erase = QPushButton("Destroy & Scrub System Traces")
        self.btn_start_erase.setObjectName("dangerBtn")
        self.btn_start_erase.clicked.connect(self._start_erasure)
        opts_layout.addWidget(self.btn_start_erase)
        layout.addWidget(group_opts)

        # Log Output
        self.txt_erase_log = QTextEdit()
        self.txt_erase_log.setReadOnly(True)
        layout.addWidget(self.txt_erase_log)

    def _browse_erase_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Destroy")
        if file_path:
            self.txt_erase_path.setText(file_path)

    def _start_erasure(self):
        target = self.txt_erase_path.text().strip()
        if not target or not os.path.exists(target):
            QMessageBox.warning(self, "Warning", "Please select a valid existing target file.")
            return

        reply = QMessageBox.question(
            self, "Confirm Destruction",
            f"Are you sure you want to permanently destroy:\n{target}\n\nThis operation cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_start_erase.setEnabled(False)
        self.txt_erase_log.clear()

        self.eraser_thread = EraserWorker(target)
        self.eraser_thread.log_signal.connect(self._log_erase)
        self.eraser_thread.finished_signal.connect(self._erasure_complete)
        self.eraser_thread.start()

    def _log_erase(self, msg: str):
        self.txt_erase_log.append(msg)

    def _erasure_complete(self, report: dict):
        self.btn_start_erase.setEnabled(True)
        status = report.get("target_file", {}).get("status", "Completed")
        removed = len(report.get("trace_scrubbing", {}).get("removed_traces", []))
        remaining = len(report.get("trace_scrubbing", {}).get("locked_or_remaining_traces", []))
        report_path = report.get("saved_report_path", "N/A")

        self.txt_erase_log.append("\n=== ERASURE COMPLETE ===")
        self.txt_erase_log.append(f"Target Status: {status}")
        self.txt_erase_log.append(f"Traces Removed: {removed}")
        self.txt_erase_log.append(f"Traces Remaining: {remaining}")
        self.txt_erase_log.append(f"Audit Report: {report_path}")

    # --- Phase 2: Recovery View ---

    def _build_recovery_tab(self):
        layout = QVBoxLayout(self.tab_recovery)
        layout.setSpacing(12)

        # Source Selection
        group_src = QGroupBox("Recovery Source & Destination")
        src_layout = QVBoxLayout(group_src)

        h1 = QHBoxLayout()
        self.txt_rec_src = QLineEdit()
        self.txt_rec_src.setPlaceholderText("Drive Letter (e.g. E:), Directory Path, or Disk Image")
        btn_browse_src = QPushButton("Browse Folder")
        btn_browse_src.clicked.connect(self._browse_rec_src)
        h1.addWidget(self.txt_rec_src)
        h1.addWidget(btn_browse_src)
        src_layout.addLayout(h1)

        h2 = QHBoxLayout()
        self.txt_rec_dest = QLineEdit()
        self.txt_rec_dest.setText(os.path.abspath("./Restored_Data"))
        btn_browse_dest = QPushButton("Destination Folder")
        btn_browse_dest.clicked.connect(self._browse_rec_dest)
        h2.addWidget(self.txt_rec_dest)
        h2.addWidget(btn_browse_dest)
        src_layout.addLayout(h2)

        layout.addWidget(group_src)

        # Filters & Options
        group_opts = QGroupBox("Filters & Hierarchy Settings")
        opts_layout = QHBoxLayout(group_opts)

        opts_layout.addWidget(QLabel("Date Cutoff (After):"))
        self.date_cutoff = QDateEdit()
        self.date_cutoff.setDate(datetime.date(2026, 1, 1))
        self.date_cutoff.setCalendarPopup(True)
        opts_layout.addWidget(self.date_cutoff)

        self.chk_recursive = QCheckBox("Preserve & Recover Nested Folders")
        self.chk_recursive.setChecked(True)
        opts_layout.addWidget(self.chk_recursive)

        self.btn_start_rec = QPushButton("Start Forensic Recovery")
        self.btn_start_rec.clicked.connect(self._start_recovery)
        opts_layout.addWidget(self.btn_start_rec)

        layout.addWidget(group_opts)

        # Progress & Log
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.txt_rec_log = QTextEdit()
        self.txt_rec_log.setReadOnly(True)
        layout.addWidget(self.txt_rec_log)

    def _browse_rec_src(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Target Folder / Volume")
        if folder:
            self.txt_rec_src.setText(folder)

    def _browse_rec_dest(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Recovery Output Directory")
        if folder:
            self.txt_rec_dest.setText(folder)

    def _start_recovery(self):
        src = self.txt_rec_src.text().strip()
        dest = self.txt_rec_dest.text().strip()

        if not src:
            QMessageBox.warning(self, "Warning", "Please specify a target drive letter, directory, or image.")
            return

        qdate = self.date_cutoff.date()
        cutoff_dt = datetime.datetime(qdate.year(), qdate.month(), qdate.day())
        recursive = self.chk_recursive.isChecked()

        self.btn_start_rec.setEnabled(False)
        self.txt_rec_log.clear()
        self.progress_bar.setValue(0)

        self.recovery_thread = RecoveryWorker(src, dest, cutoff_dt, recursive)
        self.recovery_thread.log_signal.connect(self._log_rec)
        self.recovery_thread.progress_signal.connect(lambda val: self.progress_bar.setValue(int(val)))
        self.recovery_thread.finished_signal.connect(self._recovery_complete)
        self.recovery_thread.start()

    def _log_rec(self, msg: str):
        self.txt_rec_log.append(msg)

    def _recovery_complete(self, report: dict):
        self.btn_start_rec.setEnabled(True)
        self.progress_bar.setValue(100)

        summary = report.get("recovery_summary", {})
        folders = summary.get("nested_folders_restored", 0)
        files = summary.get("total_files_recovered", 0)
        accuracy = summary.get("overall_restoration_accuracy", "0.0%")
        report_file = report.get("report_file_path", "N/A")

        self.txt_rec_log.append("\n=== RECOVERY COMPLETE ===")
        self.txt_rec_log.append(f"Restored Folders: {folders}")
        self.txt_rec_log.append(f"Restored Files: {files}")
        self.txt_rec_log.append(f"Restoration Accuracy: {accuracy}")
        self.txt_rec_log.append(f"Audit Report: {report_file}")