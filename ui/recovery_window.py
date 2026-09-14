"""
RecoveryWindowWidget: Dedicated Forensic Data Recovery Window.
Implements the multi-step guided workflow:
Path Selection -> Recursive Nested Scan -> File Checkbox Selection (Select All) -> Destination Selection -> Batch Recovery.
"""

import os
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QTextEdit, QFileDialog, QMessageBox, QComboBox, QSplitter
)
from PyQt6.QtCore import pyqtSignal, Qt, QThread
from phase2_carver.sector_scanner import SectorScanner
from ui.hex_viewer import HexViewerWidget
from ui.gallery import GalleryWidget
from core.audit_logger import AuditLogger

class CarverWorkerThread(QThread):
    """Background worker executing file carving and folder scanning."""
    progress = pyqtSignal(float)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, target_path: str, recursive: bool = True):
        super().__init__()
        self.target_path = target_path
        self.recursive = recursive

    def run(self):
        try:
            scanner = SectorScanner(self.target_path)
            results = scanner.scan(recursive=self.recursive, progress_callback=self.progress.emit)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

class RecoveryWindowWidget(QWidget):
    """Dedicated Forensic Data Recovery Window."""

    back_to_menu = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.carved_results: List[Dict[str, Any]] = []
        self.audit_logger = AuditLogger()
        self.recovery_engine = BatchRecoveryEngine()
        self.scan_worker: CarverWorkerThread = None
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

        top_title = QLabel("<h2>Forensic Data Recovery Engine</h2>")
        top_layout.addWidget(top_title)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # Step 1: Target Path & Scope Selection
        step1_box = QGroupBox("Step 1: Target Path & Scan Scope Configuration")
        step1_layout = QVBoxLayout()
        step1_box.setLayout(step1_layout)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Target Path (Folder, Volume, Disk Image):"))
        self.source_path_input = QLineEdit()
        self.source_path_input.setPlaceholderText("Select folder, raw drive (/dev/sda), or forensic image (mock_disk.img)")
        row1.addWidget(self.source_path_input)

        browse_folder_btn = QPushButton("Browse Folder...")
        browse_folder_btn.clicked.connect(self.browse_folder)
        row1.addWidget(browse_folder_btn)

        browse_image_btn = QPushButton("Browse Disk Image...")
        browse_image_btn.clicked.connect(self.browse_image)
        row1.addWidget(browse_image_btn)

        step1_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.recursive_chk = QCheckBox("Deep Recursive Scan (Scan parent directory and ALL nested subfolder locations)")
        self.recursive_chk.setChecked(True)
        self.recursive_chk.setStyleSheet("font-weight: bold; color: #38BDF8;")
        row2.addWidget(self.recursive_chk)
        row2.addStretch()

        self.scan_btn = QPushButton("🔍 Scan Files & Sectors")
        self.scan_btn.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 8px 16px; font-size: 13px;")
        self.scan_btn.clicked.connect(self.start_scan)
        row2.addWidget(self.scan_btn)

        step1_layout.addLayout(row2)
        main_layout.addWidget(step1_box)

        # Progress Bar & Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Step 2 & 3: File Selection & Batch Recovery Controls
        step2_box = QGroupBox("Step 2: File Selection & Output Destination")
        step2_layout = QVBoxLayout()
        step2_box.setLayout(step2_layout)

        # Selection Control Bar
        control_bar = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_files)
        control_bar.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all_files)
        control_bar.addWidget(deselect_all_btn)

        control_bar.addWidget(QLabel("Category Filter:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All Categories", "Images", "Documents", "Archives", "System Databases", "Media Streams"])
        self.category_combo.currentTextChanged.connect(self.filter_table)
        control_bar.addWidget(self.category_combo)

        control_bar.addStretch()
        self.selected_count_label = QLabel("Selected: 0 files")
        self.selected_count_label.setStyleSheet("font-weight: bold; color: #F59E0B;")
        control_bar.addWidget(self.selected_count_label)

        step2_layout.addLayout(control_bar)

        # Discovered Files Table
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(8)
        self.files_table.setHorizontalHeaderLabels([
            "Select", "Format", "Category", "Location / Sector", "Offset", "Size", "Confidence", "SHA-256 Hash"
        ])
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.files_table.setStyleSheet("QTableWidget { background-color: #0F172A; color: #F8FAFC; gridline-color: #334155; }")
        self.files_table.itemChanged.connect(self.on_table_item_changed)
        step2_layout.addWidget(self.files_table)

        # Step 3 Destination & Execute Recovery Bar
        rec_bar = QHBoxLayout()
        rec_bar.addWidget(QLabel("<b>Destination Folder:</b>"))
        self.dest_path_input = QLineEdit()
        self.dest_path_input.setPlaceholderText("Select directory path where recovered files will be saved")
        rec_bar.addWidget(self.dest_path_input)

        browse_dest_btn = QPushButton("Browse Destination...")
        browse_dest_btn.clicked.connect(self.browse_destination)
        rec_bar.addWidget(browse_dest_btn)

        self.recover_btn = QPushButton("🚀 RECOVER SELECTED FILES")
        self.recover_btn.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 10px 20px; font-size: 14px;")
        self.recover_btn.clicked.connect(self.execute_recovery)
        rec_bar.addWidget(self.recover_btn)

        step2_layout.addLayout(rec_bar)
        main_layout.addWidget(step2_box)

        # Log Output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(120)
        self.log_output.setStyleSheet("background-color: #0F172A; color: #38BDF8; font-family: monospace;")
        main_layout.addWidget(self.log_output)

    def browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Parent Directory / Folder to Recover")
        if path:
            self.source_path_input.setText(path)

    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Forensic Disk Image / Device", "", "Disk Images (*.img *.raw *.dd *.bin);;All Files (*)")
        if path:
            self.source_path_input.setText(path)

    def browse_destination(self):
        path = QFileDialog.getExistingDirectory(self, "Select Destination Directory for Recovered Files")
        if path:
            self.dest_path_input.setText(path)

    def start_scan(self):
        target = self.source_path_input.text().strip()
        if not target or not os.path.exists(target):
            QMessageBox.warning(self, "Invalid Path", "Please select a valid folder, volume, or disk image path.")
            return

        if self.scan_worker and self.scan_worker.isRunning():
            return

        self.log_output.append(f"Starting scan on target '{target}' (Recursive: {self.recursive_chk.isChecked()})...")
        self.progress_bar.setValue(0)
        self.scan_btn.setEnabled(False)

        self.scan_worker = CarverWorkerThread(target, recursive=self.recursive_chk.isChecked())
        self.scan_worker.progress.connect(self.update_progress)
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.error.connect(self.on_scan_error)
        self.scan_worker.start()

    def update_progress(self, val: float):
        self.progress_bar.setValue(int(val))

    def on_scan_finished(self, results: list):

        self.scan_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.carved_results = results
        self.log_output.append(f"Scan complete. Found {len(results)} potential files for recovery.")

        self.populate_table(results)

    def on_scan_error(self, err: str):
        self.scan_btn.setEnabled(True)
        self.log_output.append(f"Error during scan: {err}")
        QMessageBox.critical(self, "Scan Error", f"An error occurred during file scanning:\n{err}")

    def populate_table(self, results: list):
        self.files_table.blockSignals(True)
        self.files_table.setRowCount(0)

        filter_cat = self.category_combo.currentText()

        for r in results:
            cat = r.get("category", "Unclassified")
            if filter_cat != "All Categories" and cat != filter_cat:
                continue

            row = self.files_table.rowCount()
            self.files_table.insertRow(row)

            # Checkbox item
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_item.setCheckState(Qt.CheckState.Checked)  # Checked by default
            chk_item.setData(Qt.ItemDataRole.UserRole, r)
            self.files_table.setItem(row, 0, chk_item)

            self.files_table.setItem(row, 1, QTableWidgetItem(r.get("type", "UNKNOWN")))
            self.files_table.setItem(row, 2, QTableWidgetItem(cat))
            
            loc_str = r.get("source_file", f"Sector {r.get('sector')}")
            self.files_table.setItem(row, 3, QTableWidgetItem(str(loc_str)))
            self.files_table.setItem(row, 4, QTableWidgetItem(f"{r.get('offset'):,} B"))
            self.files_table.setItem(row, 5, QTableWidgetItem(f"{r.get('size_bytes'):,} B"))
            self.files_table.setItem(row, 6, QTableWidgetItem(f"{r.get('confidence_score'):.1f}%"))
            self.files_table.setItem(row, 7, QTableWidgetItem(r.get("sha256", "")[:16] + "..."))

        self.files_table.blockSignals(False)
        self.update_selected_count()

    def filter_table(self):
        self.populate_table(self.carved_results)

    def select_all_files(self):
        self.files_table.blockSignals(True)
        for r in range(self.files_table.rowCount()):
            item = self.files_table.item(r, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
        self.files_table.blockSignals(False)
        self.update_selected_count()

    def deselect_all_files(self):
        self.files_table.blockSignals(True)
        for r in range(self.files_table.rowCount()):
            item = self.files_table.item(r, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
        self.files_table.blockSignals(False)
        self.update_selected_count()

    def on_table_item_changed(self, item):
        if item.column() == 0:
            self.update_selected_count()

    def update_selected_count(self):
        count = 0
        for r in range(self.files_table.rowCount()):
            item = self.files_table.item(r, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                count += 1
        self.selected_count_label.setText(f"Selected: {count} files")

    def execute_recovery(self):
        selected_artifacts = []
        for r in range(self.files_table.rowCount()):
            item = self.files_table.item(r, 0)
            if item and item.checkState() == Qt.CheckState.Checked:
                artifact = item.data(Qt.ItemDataRole.UserRole)
                if artifact:
                    selected_artifacts.append(artifact)

        if not selected_artifacts:
            QMessageBox.warning(self, "No Selection", "Please select at least one file to recover.")
            return

        dest_dir = self.dest_path_input.text().strip()
        if not dest_dir:
            # Prompt user to choose output folder if not entered
            dest_dir = QFileDialog.getExistingDirectory(self, "Select Recovery Destination Directory")
            if dest_dir:
                self.dest_path_input.setText(dest_dir)
            else:
                return

        self.log_output.append(f"Executing batch recovery of {len(selected_artifacts)} files to '{dest_dir}'...")

        # Perform recovery logic
        res = self.recovery_engine.recover_artifacts(selected_artifacts, dest_dir)

        # Log audit entry
        self.audit_logger.log_event("BATCH_RECOVERY", {
            "target": self.source_path_input.text().strip(),
            "destination": dest_dir,
            "recovered": res["total_recovered"],
            "total_bytes": res["total_bytes"],
            "status": "SUCCESS"
        })
        self.audit_logger.export_json(os.path.join(dest_dir, "recovery_audit_certificate.json"))
        self.audit_logger.export_pdf(os.path.join(dest_dir, "recovery_audit_certificate.pdf"))

        msg = (
            f"🎉 Batch Data Recovery Complete!\n\n"
            f"Successfully Recovered: {res['total_recovered']} files\n"
            f"Total Bytes Recovered: {res['total_bytes']:,} bytes\n"
            f"Destination Directory: {dest_dir}\n\n"
            f"Files have been organized into categorized subfolders (Images, Documents, Archives, Databases, Media) with cryptographic audit certificates."
        )
        self.log_output.append(f"Recovery complete. {res['total_recovered']} files saved to {dest_dir}")
        QMessageBox.information(self, "Recovery Successful", msg)
