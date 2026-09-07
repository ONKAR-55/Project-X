"""
ZIPParser: Structure-aware parser for ZIP archives.
Evaluates Local File Headers (PK\\x03\\x04), Central Directory (PK\\x01\\x02), and End of Central Directory (PK\\x05\\x06).
"""

import struct
from typing import Dict, Any

class ZIPParser:
    """ZIP format parser evaluating local file headers, central directory, and archive integrity."""

    LOCAL_HEADER_SIG = b"PK\x03\x04"
    CENTRAL_DIR_SIG = b"PK\x01\x02"
    END_CENTRAL_DIR_SIG = b"PK\x05\x06"

    def parse(self, stream: bytes) -> Dict[str, Any]:
        if not stream.startswith(self.LOCAL_HEADER_SIG):
            return {"valid": False, "length": 0, "metadata": {}}

        # Find End of Central Directory record
        eocd_index = stream.find(self.END_CENTRAL_DIR_SIG)
        if eocd_index == -1:
            return {"valid": False, "length": 0, "metadata": {"error": "EOCD marker PK\\x05\\x06 not found"}}

        # Minimum EOCD size is 22 bytes
        length = eocd_index + 22
        if len(stream) < length:
            return {"valid": False, "length": 0, "metadata": {"error": "Truncated ZIP stream"}}

        # Parse EOCD to get comment length if present
        comment_len = struct.unpack("<H", stream[eocd_index+20:eocd_index+22])[0]
        length += comment_len

        # Count local files in ZIP archive
        local_files_count = stream[:eocd_index].count(self.LOCAL_HEADER_SIG)
        central_dirs_count = stream[:eocd_index].count(self.CENTRAL_DIR_SIG)

        return {
            "valid": True,
            "length": length,
            "metadata": {
                "format": "ZIP",
                "local_files_count": local_files_count,
                "central_directories_count": central_dirs_count,
                "eocd_offset": eocd_index
            }
        }
