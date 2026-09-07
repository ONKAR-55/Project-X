"""
PNGParser: Structure-aware parser for PNG files.
Validates PNG header magic (89 PNG \r \n 1A \n), chunk length headers, chunk types (IHDR, IDAT, IEND), and CRC32 checksums.
"""

import zlib
import struct
from typing import Dict, Any

class PNGParser:
    """PNG file parser validating chunk headers and CRC32 integrity."""

    PNG_HEADER = b"\x89PNG\r\n\x1A\n"

    def parse(self, stream: bytes) -> Dict[str, Any]:
        if not stream.startswith(self.PNG_HEADER):
            return {"valid": False, "length": 0, "metadata": {}}

        offset = len(self.PNG_HEADER)
        stream_len = len(stream)
        chunks = []

        valid_crc_count = 0
        invalid_crc_count = 0

        while offset + 12 <= stream_len:
            length = struct.unpack(">I", stream[offset:offset+4])[0]
            chunk_type = stream[offset+4:offset+8]
            
            chunk_data_start = offset + 8
            chunk_data_end = chunk_data_start + length

            if chunk_data_end + 4 > stream_len:
                break

            chunk_data = stream[chunk_data_start:chunk_data_end]
            expected_crc = struct.unpack(">I", stream[chunk_data_end:chunk_data_end+4])[0]
            
            # CRC calculation over Chunk Type + Chunk Data
            calc_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF

            if calc_crc == expected_crc:
                valid_crc_count += 1
            else:
                invalid_crc_count += 1

            chunks.append(chunk_type.decode("ascii", errors="ignore"))
            offset = chunk_data_end + 4

            if chunk_type == b"IEND":
                return {
                    "valid": True,
                    "length": offset,
                    "metadata": {
                        "format": "PNG",
                        "chunks": chunks,
                        "valid_crc_count": valid_crc_count,
                        "invalid_crc_count": invalid_crc_count,
                        "has_ihdr": "IHDR" in chunks,
                        "has_iend": True
                    }
                }

        return {"valid": False, "length": 0, "metadata": {"error": "Incomplete PNG stream or missing IEND"}}
