#!/usr/bin/env python3
"""
Project-X Main Application Entry Point Orchestrator.
Supports launching PyQt6 GUI interface or executing CLI operations for sanitization & carving.
"""

import os
import sys
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ProjectX.Main")

def run_cli(args):
    """Execute Project-X in Command Line Interface (CLI) mode."""
    logger.info("Starting Project-X in CLI mode...")
    if not args.drive:
        logger.error("Error: --drive parameter is required for CLI operations.")
        sys.exit(1)

    drive_path = args.drive
    action = args.action

    logger.info(f"Target drive/image: {drive_path}")
    logger.info(f"Action requested: {action}")

    if action == "scan":
        from phase2_carver.sector_scanner import SectorScanner
        scanner = SectorScanner(drive_path)
        
        def progress_log(p):
            if int(p) % 25 == 0:
                logger.info(f"Scan progress: {p:.1f}%")

        results = scanner.scan(recursive=args.recursive, progress_callback=progress_log)
        logger.info(f"Scan complete. Discovered {len(results)} potential artifacts.")
        
        for res in results:
            print(f" - [{res.get('type', 'UNK')}] Sector: {res.get('sector', 'N/A')} | Offset: {res.get('offset', 0)} B | Size: {res.get('size_bytes', 0)} B")

    elif action == "wipe":
        from phase1_eraser.block_overwriter import BlockOverwriter
        overwriter = BlockOverwriter(drive_path)
        method = args.method or "nist_800_88"
        logger.info(f"Initiating drive wipe using method: {method}")
        overwriter.wipe(method=method)
        logger.info("Drive wipe operation completed successfully.")

    elif action == "entropy":
        from core.entropy import calculate_file_entropy
        entropy = calculate_file_entropy(drive_path)
        logger.info(f"Overall Shannon Entropy: {entropy:.4f} bits/byte")

    else:
        logger.error(f"Unknown action: {action}")
        sys.exit(1)

def run_gui():
    """Launch the PyQt6 Desktop UI main window."""
    # Headless display validation
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        logger.error("No active display environment detected ($DISPLAY / $WAYLAND_DISPLAY). Run with --cli mode instead.")
        sys.exit(1)

    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
    except ImportError as e:
        logger.error(f"PyQt6 import failed: {e}. Ensure PyQt6 is installed or pass --cli flag.")
        sys.exit(1)

    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Project-X Data Suite")
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Failed to initialize Qt Application: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Project-X: Data Sanitization & Forensic Recovery Suite"
    )
    parser.add_argument("--cli", action="store_true", help="Run in Command Line mode (no GUI)")
    parser.add_argument("--drive", type=str, help="Target raw block device or image file (e.g., /dev/loop0 or disk.img)")
    parser.add_argument("--action", type=str, choices=["scan", "wipe", "entropy"], default="scan", help="Action to perform in CLI mode")
    parser.add_argument("--method", type=str, choices=["nist_800_88", "dod_5220_3pass", "dod_5220_7pass", "zero"], default="nist_800_88", help="Sanitization method for wipe action")
    parser.add_argument("--recursive", action="store_true", default=True, help="Recursively scan nested subdirectories in folder/file targets")

    args = parser.parse_args()

    if args.cli:
        run_cli(args)
    else:
        run_gui()

if __name__ == "__main__":
    main()