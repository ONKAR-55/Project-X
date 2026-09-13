"""
Project-X: Main Entry Point
Forensic Data Recovery & Permanent Erasure Utility
"""

import sys
import os

# Add project root directory to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def is_admin() -> bool:
    """Checks for administrative / root privileges required for raw drive access."""
    try:
        if os.name == "nt":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def main():
    # Print warning if running without elevated permissions
    if not is_admin():
        print("[!] Warning: Running without Administrator / Root privileges.")
        print("[!] Direct raw sector carving (e.g. \\\\.\\E: or /dev/sdX) may fail.\n")

    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow

        app = QApplication(sys.argv)
        app.setApplicationName("Project-X Forensic Suite")
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
    except ImportError as e:
        print(f"[!] Import Error: {e}")
        print("[!] Ensure dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Fatal Launch Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()