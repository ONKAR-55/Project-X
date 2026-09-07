"""
MainWindow: PyQt6 desktop application layout combining Dashboard and Hex Viewer.
"""

from PyQt6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar, QMessageBox
from ui.dashboard import DashboardWidget
from ui.hex_viewer import HexViewerWidget
from core.audit_logger import AuditLogger

class MainWindow(QMainWindow):
    """Main desktop interface window for Project-X."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project-X: Enterprise Data Sanitization & Forensic Suite")
        self.resize(1024, 768)

        self.audit_logger = AuditLogger()
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.dashboard = DashboardWidget()
        self.tabs.addTab(self.dashboard, "Operations Dashboard")

        self.hex_viewer = HexViewerWidget()
        self.tabs.addTab(self.hex_viewer, "Sector Hex Inspector")

        # Connect Dashboard Signals
        self.dashboard.wipe_requested.connect(self.handle_wipe)
        self.dashboard.scan_requested.connect(self.handle_scan)

        self.statusBar().showMessage("Ready")

    def handle_wipe(self, drive_path: str, method: str):
        reply = QMessageBox.question(
            self, "Confirm Disk Wipe",
            f"WARNING: Sanitization using method '{method}' will overwrite data on '{drive_path}'. Proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.dashboard.append_log(f"Starting wipe pass on {drive_path} with {method}...")
            try:
                from phase1_eraser.block_overwriter import BlockOverwriter
                overwriter = BlockOverwriter(drive_path)
                overwriter.wipe(method=method, progress_callback=self.dashboard.set_progress)
                self.dashboard.append_log("Sanitization complete!")
                self.audit_logger.log_event("WIPE_COMPLETE", {"target": drive_path, "method": method, "status": "SUCCESS"})
                self.statusBar().showMessage("Wipe operation completed.")
            except Exception as e:
                self.dashboard.append_log(f"Error during wipe: {e}")
                self.audit_logger.log_event("WIPE_ERROR", {"target": drive_path, "error": str(e), "status": "FAILED"})

    def handle_scan(self, drive_path: str):
        self.dashboard.append_log(f"Starting forensic scan on {drive_path}...")
        try:
            from phase2_carver.sector_scanner import SectorScanner
            scanner = SectorScanner(drive_path)
            results = scanner.scan()
            self.dashboard.append_log(f"Found {len(results)} potential files.")
            for r in results:
                self.dashboard.append_log(f" - [{r['type']}] Sector {r['sector']} (Size: {r['size_bytes']} bytes, Score: {r['confidence_score']}%)")

            # Load first sector into hex viewer if data exists
            if results and "data" in results[0]:
                self.hex_viewer.load_data(results[0]["data"][:512])

            self.audit_logger.log_event("SCAN_COMPLETE", {"target": drive_path, "found": len(results), "status": "SUCCESS"})
            self.statusBar().showMessage(f"Scan finished. Found {len(results)} files.")
        except Exception as e:
            self.dashboard.append_log(f"Error during scan: {e}")
            self.audit_logger.log_event("SCAN_ERROR", {"target": drive_path, "error": str(e), "status": "FAILED"})
