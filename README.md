# Project-X: Data Sanitization & Forensic Recovery Suite

**Project-X** is an enterprise-grade forensic engine combining low-level secure data sanitization (Phase 1) and structure-aware file carving & recovery (Phase 2). Built with raw physical sector access capabilities, HMAC-SHA256 audit logging, and a PyQt6 desktop hex viewer interface.

---

## 🏗 Directory Architecture

```text
Project-X/
├── core/                  # SHARED: Low-level utilities and system bindings
│   ├── __init__.py
│   ├── disk_io.py         # Raw sector access handles (Win32 API / Linux block dev)
│   ├── entropy.py         # Shannon entropy calculations for sector analysis
│   └── audit_logger.py    # HMAC-SHA256 signed audit report generator
│
├── phase1_eraser/         # YOUR WORKSPACE: Data Sanitization Engine
│   ├── __init__.py
│   ├── block_overwriter.py # NIST 800-88 / DoD 5220.22-M multi-pass overwriting
│   ├── slack_scrubber.py  # File slack space cluster boundary zeroing
│   ├── metadata_wiper.py  # MFT record & Inode metadata obfuscation
│   └── direct_flusher.py  # Low-level OS buffer bypass (O_DIRECT / FlushFileBuffers)
│
├── phase2_carver/         # PARTNER'S WORKSPACE: Forensic Recovery Engine
│   ├── __init__.py
│   ├── sector_scanner.py  # Direct physical sector header/footer scanner
│   ├── parsers/           # Structure-aware file format parsers
│   │   ├── jpeg_parser.py # JPEG chunk reader
│   │   ├── png_parser.py  # PNG chunk length & CRC32 validator
│   │   ├── pdf_parser.py  # PDF structural validator
│   │   └── zip_parser.py  # ZIP central directory parser
│   └── validator.py       # Confidence score calculator (0-100%)
│
├── ui/                    # SHARED: User Interface Components
│   ├── main_window.py     # PyQt6 desktop application layout
│   ├── hex_viewer.py      # Side-by-side hexadecimal sector inspector
│   └── dashboard.py       # Drive selection and execution controls
│
├── tests/                 # Integration & Validation Test Suites
│   ├── test_erasure.py    # Phase 1 unit tests
│   ├── test_carving.py    # Phase 2 unit tests
│   └── make_mock_disk.py  # Script to generate raw .img disk datasets
│
├── requirements.txt       # Python dependencies (PyQt6, pywin32, reportlab)
├── .gitignore             # Ignores .img, .raw, build caches, and test logs
├── README.md              # Project documentation and module responsibilities
└── main.py                # Main application orchestrator entry point
```

---

## ⚡ Key Features

- **Multi-Pass Sanitization**: Supports NIST SP 800-88 (Clear/Purge) and DoD 5220.22-M 3-pass & 7-pass pattern wipes.
- **Slack & Metadata Scrubbing**: Zero out file slack space and obfuscate MFT/Inode metadata structures.
- **Unbuffered I/O**: Direct disk access using OS-native unbuffered handles (`O_DIRECT` / `FlushFileBuffers`).
- **Structure-Aware File Carving**: Dynamic sector scanning and parsing for JPEG, PNG, PDF, and ZIP binary signatures with CRC verification.
- **Entropy Analysis**: Calculates Shannon entropy per cluster/sector to evaluate data randomness.
- **Cryptographic Audit Logs**: HMAC-SHA256 signature verification for sanitization reports exported to JSON/PDF.
- **Interactive PyQt6 Hex Inspector**: Side-by-side hexadecimal and ASCII visualizer for real-time sector inspection.

---

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Creating Synthetic Test Disk Image

```bash
python3 tests/make_mock_disk.py --output mock_disk.img --size-mb 10
```

### Running Test Suite

```bash
pytest tests/
```

### Launching Main Application

```bash
# Launch GUI Interface
python3 main.py

# Run in CLI Mode
python3 main.py --cli --drive mock_disk.img --action scan
```
