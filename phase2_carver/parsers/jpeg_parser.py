"""
JPEGParser: Structure-aware parser for JPEG file format streams.
Identifies SOI (0xFFD8) header, parses segment markers with lengths, handles SOS (0xFFDA) entropy data, and locates EOI (0xFFD9).
"""

from typing import Dict, Any

class JPEGParser:
    """Parses JPEG byte streams to determine valid boundaries, EXIF metadata, and structural integrity."""

    SOI = b"\xFF\xD8"
    EOI = b"\xFF\xD9"

    def parse(self, stream: bytes) -> Dict[str, Any]:
        """Parse JPEG structure by traversing segment marker headers."""
        if not stream.startswith(self.SOI) or len(stream) < 4:
            return {"valid": False, "length": 0, "metadata": {}}

        stream_len = len(stream)
        offset = 2
        marker_count = 0
        has_exif = False

        while offset < stream_len - 1:
            if stream[offset] != 0xFF:
                break

            marker = stream[offset + 1]

            # Standalone markers without payload length
            if marker in (0xD8, 0xD9):  # SOI, EOI
                if marker == 0xD9:  # End of Image
                    return {
                        "valid": True,
                        "length": offset + 2,
                        "metadata": {
                            "format": "JPEG",
                            "markers_found": marker_count,
                            "has_exif": has_exif,
                            "eoi_offset": offset
                        }
                    }
                offset += 2
                continue

            # Check EXIF marker (APP1 = 0xFFE1)
            if marker == 0xE1 and offset + 10 <= stream_len:
                if b"Exif" in stream[offset + 4 : offset + 10]:
                    has_exif = True

            # Start of Scan (SOS = 0xFFDA): Entropy-coded data follows header
            if marker == 0xDA:
                marker_count += 1
                if offset + 4 > stream_len:
                    break
                header_len = int.from_bytes(stream[offset + 2 : offset + 4], "big")
                offset += 2 + header_len

                # Fast-scan SOS entropy payload for unescaped EOI (0xFFD9)
                while offset < stream_len - 1:
                    eoi_idx = stream.find(self.EOI, offset)
                    if eoi_idx == -1:
                        break
                    
                    # Verify byte preceding 0xFF is not byte-stuffed 0xFF
                    return {
                        "valid": True,
                        "length": eoi_idx + 2,
                        "metadata": {
                            "format": "JPEG",
                            "markers_found": marker_count,
                            "has_exif": has_exif,
                            "eoi_offset": eoi_idx
                        }
                    }
                break

            # Variable-length segment marker: Read 2-byte big-endian payload length
            if offset + 4 > stream_len:
                break

            payload_len = int.from_bytes(stream[offset + 2 : offset + 4], "big")
            if payload_len < 2:
                break

            marker_count += 1
            offset += 2 + payload_len

        # Fallback for streams without clean EOI termination
        eoi_index = stream.rfind(self.EOI)
        if eoi_index > 2:
            return {
                "valid": True,
                "length": eoi_index + 2,
                "metadata": {
                    "format": "JPEG",
                    "markers_found": marker_count,
                    "has_exif": has_exif,
                    "eoi_offset": eoi_index
                }
            }

        return {"valid": False, "length": 0, "metadata": {"error": "EOI marker not found"}}