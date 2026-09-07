"""
HexViewerWidget: Side-by-side hexadecimal and ASCII sector inspector widget.
Displays raw byte offsets, hex representations, ASCII translations, and Shannon entropy indicator.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QSpinBox, QPushButton
from PyQt6.QtGui import QFont
from core.entropy import calculate_entropy

class HexViewerWidget(QWidget):
    """PyQt6 widget displaying formatted hexadecimal and ASCII sector data side-by-side."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.raw_data = b""
        self.sector_size = 512
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Control Bar
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Sector:"))
        self.sector_spin = QSpinBox()
        self.sector_spin.setRange(0, 9999999)
        self.sector_spin.valueChanged.connect(self.on_sector_changed)
        control_layout.addWidget(self.sector_spin)

        self.entropy_label = QLabel("Shannon Entropy: N/A")
        self.entropy_label.setStyleSheet("font-weight: bold; color: #38BDF8;")
        control_layout.addStretch()
        control_layout.addWidget(self.entropy_label)

        layout.addLayout(control_layout)

        # Text View for Hex Inspection
        self.hex_text = QTextEdit()
        self.hex_text.setReadOnly(True)
        # Use monospaced font
        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.hex_text.setFont(font)
        self.hex_text.setStyleSheet("""
            QTextEdit {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.hex_text)

    def load_data(self, data: bytes):
        """Load byte array and format into hexadecimal & ASCII display."""
        self.raw_data = data
        entropy = calculate_entropy(data)
        self.entropy_label.setText(f"Shannon Entropy: {entropy:.4f} bits/byte")
        self.render_hex()

    def render_hex(self):
        if not self.raw_data:
            self.hex_text.setText("No data loaded.")
            return

        lines = []
        lines.append("OFFSET   00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F  |ASCII|")
        lines.append("-" * 75)

        for i in range(0, len(self.raw_data), 16):
            chunk = self.raw_data[i:i+16]
            hex_part1 = " ".join(f"{b:02X}" for b in chunk[:8])
            hex_part2 = " ".join(f"{b:02X}" for b in chunk[8:])
            hex_str = f"{hex_part1:<23}  {hex_part2:<23}"

            ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            line = f"{i:08X}  {hex_str}  |{ascii_str}|"
            lines.append(line)

        self.hex_text.setText("\n".join(lines))

    def on_sector_changed(self, value):
        pass
