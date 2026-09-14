"""
MainWindow Module: Fixed UI text mnemonic glitches, cleaned tree widget column 
overlaps, and updated tree selection payload routing.
"""

import sys
import os
import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QProgressBar,
    QTextEdit, QCheckBox, QDateEdit, QGroupBox, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from phase1_eraser.eraser_orchestrator import EraserOrchestrator
from phase2_carver.sector_scanner import SectorScanner
from phase2_carver.advanced_recovery_engine import AdvancedRecoveryEngine

DARK_STYLESHEET = """
QMainWindow { background-color: #0f172a; }
QWidget { color: #f8fafc; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
QTabWidget::pane { border: 1px solid #1e293b; background-color: #0f172a; border-radius: 8px; }
QTabBar::tab { background: #1e293b; color: #94a3b8; padding: 10px 20px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #3b82f6; color: #ffffff; }
QGroupBox { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; margin-top: 10px; padding: 12px; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 6px; color: #38bdf8; }
QLineEdit, QDateEdit { background-color: #0f172a; border: 1px solid #475569; border-radius: 6px; padding: 6px; color: #f8fafc; }
QPushButton { background-color: #3b82f6; color: #ffffff; border-radius: 6px; padding: 8px 14px; font-weight: bold; border: none; }
QPushButton:hover { background-color: #2563eb; }
QPushButton:disabled { background-color: #334155; color: #64748b; }
QPushButton#dangerBtn { background-color: #ef4444; }
QPushButton#dangerBtn:hover { background-color: #dc2626; }
QPushButton#secondaryBtn { background-color: #334155; color: #f8fafc; }
QPushButton#secondaryBtn:hover { background-color: #475569; }
QProgressBar { background-color: #0f172a; border: 1px solid #334155; border-radius: 6px; text-align: center; color: #ffffff; }
QProgressBar::chunk { background-color: #38bdf8; border-radius: 5px; }
QTextEdit, QTreeWidget { background-color: #090d16; border: 1px solid #334155; border-radius: 6px; color: #f8fafc; }
QHeaderView::section { background-color: #1e293b; color: #38bdf8; padding: 6px; border: 1px solid #334155; font-weight: bold; }
"""


class ScanWorker(QThread):
    finished_signal = pyqtSignal(list)
    progress_signal = pyqtSignal(float)
    log_signal = pyqtSignal(str)

    def __init__(self, target_path: str):
        super().__init__()
        self.target_path = target_path

    def run(self):
        self.log_signal.emit(f"[*] Scanning sectors and disk space for: {self.target_path}")
        scanner = SectorScanner(self.target_path)
        artifacts = scanner.scan(
            recursive=True,
            progress_callback=lambda pct: self.progress_signal.emit(pct)
        )
        self.finished_signal.emit(artifacts)


class RestoreWorker(QThread):
    finished_signal = pyqtSignal(dict)
    log_signal = pyqtSignal(str)

    def __init__(self, selected_artifacts: list, base_path: str, dest_dir: str, cutoff_date: datetime.datetime, recursive: bool):
        super().__init__()
        self.selected_artifacts = selected_artifacts
        self.base_path = base_path
        self.dest_dir = dest_dir
        self.cutoff_date = cutoff_date
        self.recursive = recursive

    def run(self):
        self.log_signal.emit(f"[*] Restoring {len(self.selected_artifacts)} selected items...")
        engine = AdvancedRecoveryEngine(self.dest_dir)
        report = engine.execute_recovery(
            artifacts=self.selected_artifacts,
            base_scan_path=self.base_path,
            cutoff_date=self.cutoff_date,
            recursive_nested=self.recursive
        )
        self.finished_signal.emit(report)


class EraserWorker(QThread):
    finished_signal = pyqtSignal(dict)
    log_signal = pyqtSignal(str)

    def __init__(self, target_path: str):
        super().__init__()
        self.target_path = target_path

    def run(self):
        orchestrator = EraserOrchestrator(self.target_path)
        report = orchestrator.execute_full_erasure()
        self.finished_signal.emit(report)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project-X Forensic Suite")
        self.resize(1100, 800)
        self.setStyleSheet(DARK_STYLESHEET)
        self.scanned_artifacts = []

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        title_label = QLabel("PROJECT-X : FORENSIC SUITE")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #38bdf8;")
        main_layout.addWidget(title_label)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tab_eraser = QWidget()
        self.tab_recovery = QWidget()
        self.tabs.addTab(self.tab_eraser, "Phase 1: Secure Eraser")
        self.tabs.addTab(self.tab_recovery, "Phase 2: Data Recovery")

        self._build_eraser_tab()
        self._build_recovery_tab()

    def _build_eraser_tab(self):
        layout = QVBoxLayout(self.tab_eraser)
        group_target = QGroupBox("Target File and System Trace Scrubbing")
        target_layout = QHBoxLayout(group_target)

        self.txt_erase_path = QLineEdit()
        self.txt_erase_path.setPlaceholderText("Select file to permanently destroy...")
        btn_browse_erase = QPushButton("Browse File")
        btn_browse_erase.clicked.connect(self._browse_erase_file)

        target_layout.addWidget(self.txt_erase_path)
        target_layout.addWidget(btn_browse_erase)
        layout.addWidget(group_target)

        self.btn_start_erase = QPushButton("Destroy and Scrub System Traces")
        self.btn_start_erase.setObjectName("dangerBtn")
        self.btn_start_erase.clicked.connect(self._start_erasure)
        layout.addWidget(self.btn_start_erase)

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
            QMessageBox.warning(self, "Warning", "Select a valid existing file.")
            return

        reply = QMessageBox.question(self, "Confirm Destruction", f"Permanently wipe {target}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.btn_start_erase.setEnabled(False)
            self.eraser_thread = EraserWorker(target)
            self.eraser_thread.log_signal.connect(lambda msg: self.txt_erase_log.append(msg))
            self.eraser_thread.finished_signal.connect(self._erasure_complete)
            self.eraser_thread.start()

    def _erasure_complete(self, report: dict):
        self.btn_start_erase.setEnabled(True)
        self.txt_erase_log.append("\n=== ERASURE COMPLETE ===")
        self.txt_erase_log.append(f"Status: {report.get('target_file', {}).get('status')}")

    def _build_recovery_tab(self):
        layout = QVBoxLayout(self.tab_recovery)

        # 1. Source & Output Controls
        group_src = QGroupBox("1. Select Scan Target and Output Folder")
        src_layout = QVBoxLayout(group_src)

        h1 = QHBoxLayout()
        self.txt_rec_src = QLineEdit()
        self.txt_rec_src.setPlaceholderText("Drive Letter (e.g., E:\\), Path, or Image file")
        btn_browse_src = QPushButton("Browse Source")
        btn_browse_src.clicked.connect(self._browse_rec_src)
        h1.addWidget(self.txt_rec_src)
        h1.addWidget(btn_browse_src)
        src_layout.addLayout(h1)

        h2 = QHBoxLayout()
        self.txt_rec_dest = QLineEdit()
        self.txt_rec_dest.setText(os.path.abspath("./Restored_Data"))
        btn_browse_dest = QPushButton("Destination Directory")
        btn_browse_dest.clicked.connect(self._browse_rec_dest)
        h2.addWidget(self.txt_rec_dest)
        h2.addWidget(btn_browse_dest)
        src_layout.addLayout(h2)
        layout.addWidget(group_src)

        # 2. Controls & Actions
        group_opts = QGroupBox("2. Controls and Actions")
        opts_layout = QHBoxLayout(group_opts)

        opts_layout.addWidget(QLabel("Date Cutoff:"))
        self.date_cutoff = QDateEdit()
        self.date_cutoff.setDate(datetime.date(2026, 1, 1))
        self.date_cutoff.setCalendarPopup(True)
        opts_layout.addWidget(self.date_cutoff)

        self.chk_recursive = QCheckBox("Preserve Folder Structure")
        self.chk_recursive.setChecked(True)
        opts_layout.addWidget(self.chk_recursive)

        self.btn_scan = QPushButton("Scan for Recoverable Files")
        self.btn_scan.clicked.connect(self._start_scan)
        opts_layout.addWidget(self.btn_scan)

        self.btn_restore_selected = QPushButton("Restore Selected Items")
        self.btn_restore_selected.setEnabled(False)
        self.btn_restore_selected.clicked.connect(self._start_restore)
        opts_layout.addWidget(self.btn_restore_selected)

        layout.addWidget(group_opts)

        # 3. Selection Action Bar
        tree_ctrl_layout = QHBoxLayout()
        btn_select_all = QPushButton("Select All")
        btn_select_all.setObjectName("secondaryBtn")
        btn_select_all.clicked.connect(lambda: self._set_all_check_states(Qt.CheckState.Checked))

        btn_deselect_all = QPushButton("Deselect All")
        btn_deselect_all.setObjectName("secondaryBtn")
        btn_deselect_all.clicked.connect(lambda: self._set_all_check_states(Qt.CheckState.Unchecked))

        sort_label = QLabel("Tip: Click column headers to sort by Name, Type, Date, Size, or Offset")
        sort_label.setStyleSheet("color: #64748b; font-style: italic;")

        tree_ctrl_layout.addWidget(btn_select_all)
        tree_ctrl_layout.addWidget(btn_deselect_all)
        tree_ctrl_layout.addStretch()
        tree_ctrl_layout.addWidget(sort_label)
        layout.addLayout(tree_ctrl_layout)

        # 4. Integrated Clean Tree Widget (No Column 0 Overlap)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels([
            "Name / Folder Hierarchy", "Type / Status", "Date Modified / Deleted", "Size (Bytes)", "Offset"
        ])
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree_widget.setSortingEnabled(True)
        layout.addWidget(self.tree_widget)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.txt_rec_log = QTextEdit()
        self.txt_rec_log.setReadOnly(True)
        self.txt_rec_log.setMaximumHeight(90)
        layout.addWidget(self.txt_rec_log)

    def _browse_rec_src(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Target Folder / Drive")
        if folder:
            self.txt_rec_src.setText(folder)

    def _browse_rec_dest(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Location")
        if folder:
            self.txt_rec_dest.setText(folder)

    def _start_scan(self):
        src = self.txt_rec_src.text().strip()
        if not src:
            QMessageBox.warning(self, "Warning", "Please specify a target drive or directory.")
            return

        self.btn_scan.setEnabled(False)
        self.btn_restore_selected.setEnabled(False)
        self.tree_widget.clear()
        self.txt_rec_log.clear()
        self.progress_bar.setValue(0)

        self.scan_thread = ScanWorker(src)
        self.scan_thread.log_signal.connect(lambda msg: self.txt_rec_log.append(msg))
        self.scan_thread.progress_signal.connect(lambda val: self.progress_bar.setValue(int(val)))
        self.scan_thread.finished_signal.connect(self._scan_complete)
        self.scan_thread.start()

    def _scan_complete(self, artifacts: list):
        self.scanned_artifacts = artifacts
        self.btn_scan.setEnabled(True)
        self.progress_bar.setValue(100)
        self.txt_rec_log.append(f"[+] Found {len(artifacts)} recoverable item candidates.")

        if not artifacts:
            QMessageBox.information(self, "Scan Result", "No deleted artifacts or files detected.")
            return

        self._build_nested_tree(artifacts)
        self.btn_restore_selected.setEnabled(True)

    def _build_nested_tree(self, artifacts: list):
        """Constructs a clean nested folder hierarchy directly into Column 0."""
        self.tree_widget.setSortingEnabled(False)
        self.tree_widget.clear()

        folder_nodes = {}

        for item in artifacts:
            rel_path = item.get("relative_path") or item.get("original_name") or "Carved_Files/Unknown"
            parts = [p for p in rel_path.replace("\\", "/").strip("/").split("/") if p]

            current_parent = None
            accumulated_path = ""

            # Build intermediate folder nodes
            for folder_part in parts[:-1]:
                accumulated_path = f"{accumulated_path}/{folder_part}" if accumulated_path else folder_part
                if accumulated_path not in folder_nodes:
                    folder_item = QTreeWidgetItem([folder_part, "Directory", "-", "-", "-"])
                    folder_item.setFlags(folder_item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsAutoTristate)
                    folder_item.setCheckState(0, Qt.CheckState.Checked)

                    if current_parent:
                        current_parent.addChild(folder_item)
                    else:
                        self.tree_widget.addTopLevelItem(folder_item)

                    folder_nodes[accumulated_path] = folder_item

                current_parent = folder_nodes[accumulated_path]

            # Leaf File Node
            file_name = parts[-1] if parts else rel_path
            status = item.get("status", "Deleted Candidate")
            date_str = item.get("date_str") or "Unallocated Sector"
            size_str = str(item.get("size_bytes", 0))
            offset_str = hex(item.get("offset", 0)) if "offset" in item else "N/A"

            file_node = QTreeWidgetItem([file_name, status, date_str, size_str, offset_str])
            file_node.setFlags(file_node.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            file_node.setCheckState(0, Qt.CheckState.Checked)
            file_node.setData(0, Qt.ItemDataRole.UserRole, item)

            if current_parent:
                current_parent.addChild(file_node)
            else:
                self.tree_widget.addTopLevelItem(file_node)

        self.tree_widget.setSortingEnabled(True)

    def _set_all_check_states(self, state: Qt.CheckState):
        """Recursively toggles check states across all tree items."""
        def recurse_set(item: QTreeWidgetItem):
            item.setCheckState(0, state)
            for i in range(item.childCount()):
                recurse_set(item.child(i))

        for i in range(self.tree_widget.topLevelItemCount()):
            recurse_set(self.tree_widget.topLevelItem(i))

    def _get_selected_artifacts(self) -> list:
        """Collects payload dictionaries for all checked file nodes."""
        selected = []

        def recurse_get(item: QTreeWidgetItem):
            if item.childCount() == 0:  # Leaf file node
                if item.checkState(0) == Qt.CheckState.Checked:
                    data = item.data(0, Qt.ItemDataRole.UserRole)
                    if data:
                        selected.append(data)
            else:
                for i in range(item.childCount()):
                    recurse_get(item.child(i))

        for i in range(self.tree_widget.topLevelItemCount()):
            recurse_get(self.tree_widget.topLevelItem(i))

        return selected

    def _start_restore(self):
        selected_artifacts = self._get_selected_artifacts()
        if not selected_artifacts:
            QMessageBox.warning(self, "Warning", "No files selected. Check at least one item in the tree view.")
            return

        src = self.txt_rec_src.text().strip()
        dest = self.txt_rec_dest.text().strip()
        qdate = self.date_cutoff.date()
        cutoff_dt = datetime.datetime(qdate.year(), qdate.month(), qdate.day())
        recursive = self.chk_recursive.isChecked()

        self.btn_restore_selected.setEnabled(False)
        self.restore_thread = RestoreWorker(selected_artifacts, src, dest, cutoff_dt, recursive)
        self.restore_thread.log_signal.connect(lambda msg: self.txt_rec_log.append(msg))
        self.restore_thread.finished_signal.connect(self._restore_complete)
        self.restore_thread.start()

    def _restore_complete(self, report: dict):
        self.btn_restore_selected.setEnabled(True)
        summary = report.get("recovery_summary", {})
        files_count = summary.get("total_files_recovered", 0)
        accuracy = summary.get("overall_restoration_accuracy", "0.0%")
        report_file = report.get("report_file_path", "N/A")

        self.txt_rec_log.append("\n=== RESTORE OPERATION COMPLETE ===")
        self.txt_rec_log.append(f"Restored Items: {files_count}")
        self.txt_rec_log.append(f"Accuracy Score: {accuracy}")
        self.txt_rec_log.append(f"Audit Report: {report_file}")