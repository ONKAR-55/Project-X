"""
HexViewerWidget: Side-by-side hexadecimal and ASCII sector inspector widget.
Displays raw byte offsets, hex representations, ASCII translations, byte highlight overlays (red=headers, green=footers, gray=zeroes), and Shannon entropy indicators.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QSpinBox, QPushButton, QLineEdit
from PyQt6.QtGui import QFont
from core.entropy import calculate_entropy, classify_entropy

class HexViewerWidget(QWidget):
    """PyQt6 widget displaying formatted hexadecimal and ASCII sector data side-by-side with color overlays."""

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
        control_layout.addWidget(QLabel("Sector Offset:"))
        self.sector_spin = QSpinBox()
        self.sector_spin.setRange(0, 9999999)
        control_layout.addWidget(self.sector_spin)

        self.entropy_label = QLabel("Shannon Entropy: N/A")
        self.entropy_label.setStyleSheet("font-weight: bold; color: #38BDF8;")
        control_layout.addStretch()

        # Legend badges
        legend = QLabel(
            '<span style="color:#EF4444; font-weight:bold;">■ Header</span> &nbsp; '
            '<span style="color:#10B981; font-weight:bold;">■ Footer</span> &nbsp; '
            '<span style="color:#64748B; font-weight:bold;">■ Zeroes</span>'
        )
        control_layout.addWidget(legend)
        control_layout.addWidget(self.entropy_label)

        layout.addLayout(control_layout)

        # Text View for Hex Inspection
        self.hex_text = QTextEdit()
        self.hex_text.setReadOnly(True)
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
        """Load byte array and format into colored hexadecimal & ASCII display."""
        self.raw_data = data
        entropy = calculate_entropy(data)
        classification = classify_entropy(entropy)
        self.entropy_label.setText(f"Entropy: {entropy:.4f} bits/byte [{classification}]")
        self.render_hex()

    def render_hex(self):
        if not self.raw_data:
            self.hex_text.setText("No sector data loaded.")
            return

        html_lines = []
        html_lines.append('<pre style="margin:0; font-family:\'Courier New\', monospace;">')
        html_lines.append('<span style="color:#94A3B8; font-weight:bold;">OFFSET   00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F  |ASCII|</span>')
        html_lines.append('<span style="color:#475569;">' + "-" * 75 + '</span>')

        data_len = len(self.raw_data)
        for i in range(0, data_len, 16):
            chunk = self.raw_data[i:i+16]
            hex_spans = []
            ascii_chars = []

            for idx, b in enumerate(chunk):
                # Color logic: Red for headers, Green for footers, Gray for zeroes, Default white
                global_idx = i + idx
                color = "#F8FAFC"

                if b == 0x00:
                    color = "#64748B"  # Gray for zero bytes
                
                # Header signatures check
                if global_idx < 10 and self.raw_data.startswith((b"\xFF\xD8\xFF", b"\x89PNG", b"%PDF-", b"PK\x03\x04", b"SQLite")):
                    color = "#EF4444"  # Red for header magic
                elif global_idx < 12 and len(self.raw_data) >= 8 and self.raw_data[4:8] == b"ftyp":
                    color = "#EF4444"
                # Footer signatures check
                elif (b"\xFF\xD9" in chunk or b"IEND" in chunk or b"%%EOF" in chunk or b"PK\x05\x06" in chunk):
                    color = "#10B981"  # Green for footer

                hex_spans.append(f'<span style="color:{color};">{b:02X}</span>')
                
                char = chr(b) if 32 <= b <= 126 else "."
                ascii_chars.append(f'<span style="color:{color};">{char}</span>')

            # Build hex split (8 bytes - space - 8 bytes)
            part1 = " ".join(hex_spans[:8])
            part2 = " ".join(hex_spans[8:])
            
            # Padding if chunk < 16 bytes
            pad_spaces = (16 - len(chunk)) * 3
            if len(chunk) < 8:
                pad_spaces += 1

            hex_formatted = f"{part1}  {part2}".ljust(48 + pad_spaces)
            ascii_formatted = "".join(ascii_chars)
            
            line_html = f'<span style="color:#38BDF8;">{i:08X}</span>  {hex_formatted}  |<span style="color:#F1F5F9;">{ascii_formatted}</span>|'
            html_lines.append(line_html)

        html_lines.append('</pre>')
        self.hex_text.setHtml("\n".join(html_lines))

    def on_sector_changed(self, value):
        pass

