"""
JPEGParser: Structure-aware parser for JPEG file format stream.
Identifies SOI (0xFFD8) header, segment markers, and EOI (0xFFD9) trailer.
"""

from typing import Dict, Any

class JPEGParser:
    """Parses JPEG byte streams to determine valid boundaries and structural integrity."""

    SOI = b"\xFF\xD8"  # Start of Image
    EOI = b"\xFF\xD9"  # End of Image

    def parse(self, stream: bytes) -> Dict[str, Any]:
        if not stream.startswith(self.SOI):
            return {"valid": False, "length": 0, "metadata": {}}

        # Find EOI marker
        eoi_index = stream.find(self.EOI)
        if eoi_index == -1:
            # EOF missing, unclosed JPEG stream
            return {"valid": False, "length": 0, "metadata": {"error": "EOI marker not found"}}

        length = eoi_index + len(self.EOI)
        
        # Count JPEG segment markers (0xFFXX)
        marker_count = 0
        i = 2
        while i < length - 1:
            if stream[i] == 0xFF and stream[i+1] not in (0x00, 0xFF):
                marker_count += 1
            i += 1

        return {
            "valid": True,
            "length": length,
            "metadata": {
                "format": "JPEG",
                "markers_found": marker_count,
                "eoi_offset": eoi_index
            }
        }
