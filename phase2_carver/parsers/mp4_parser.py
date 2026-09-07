"""
MP4Parser: Structure-aware parser for MP4 / ISO Base Media File Format streams.
Validates atom box hierarchy ('ftyp', 'moov', 'mdat', etc.) and computes total media file boundaries.
"""

import struct
from typing import Dict, Any

class MP4Parser:
    """Parses MP4 video/audio streams by iterating through ISO atom boxes."""

    FTYP = b"ftyp"

    def parse(self, stream: bytes) -> Dict[str, Any]:
        """Traverse top-level MP4 atoms to calculate total valid stream length."""
        stream_len = len(stream)
        if stream_len < 16 or stream[4:8] != self.FTYP:
            return {"valid": False, "length": 0, "metadata": {}}

        offset = 0
        boxes = []
        has_moov = False
        has_mdat = False
        major_brand = stream[8:12].decode("ascii", errors="ignore").strip()

        while offset + 8 <= stream_len:
            box_len = struct.unpack(">I", stream[offset:offset+4])[0]
            box_type = stream[offset+4:offset+8]

            # Validate box type consists of printable ASCII characters
            if not all(32 <= b <= 126 for b in box_type):
                break

            type_str = box_type.decode("ascii", errors="ignore")

            if box_len == 1:
                # 64-bit extended size box
                if offset + 16 > stream_len:
                    break
                box_len = struct.unpack(">Q", stream[offset+8:offset+16])[0]
            elif box_len == 0:
                # Box extends to EOF
                box_len = stream_len - offset

            if box_len < 8:
                break

            boxes.append(type_str)

            if box_type == b"moov":
                has_moov = True
            elif box_type == b"mdat":
                has_mdat = True

            offset += box_len

            if offset > stream_len:
                # Box extends past current buffer boundary; truncate to current valid size
                offset = min(offset, stream_len)
                break

        if has_moov or has_mdat:
            return {
                "valid": True,
                "length": max(offset, 16),
                "metadata": {
                    "format": "MP4",
                    "major_brand": major_brand,
                    "boxes": boxes,
                    "has_moov": has_moov,
                    "has_mdat": has_mdat
                }
            }

        return {"valid": False, "length": 0, "metadata": {"error": "Missing required moov/mdat boxes"}}