"""
SQLiteParser: Structure-aware parser for SQLite 3 database files.
Validates header magic, page size fields, B-tree header markers at offset 100, and database boundaries.
"""

import struct
from typing import Dict, Any

class SQLiteParser:
    """Parses SQLite database headers and page structures."""

    HEADER_MAGIC = b"SQLite format 3\x00"
    VALID_PAGE_TYPES = {0x02, 0x05, 0x0A, 0x0D}  # Index/Table interior/leaf pages

    def parse(self, stream: bytes) -> Dict[str, Any]:
        """Validate SQLite header magic, page size, page count, and page 1 B-tree header."""
        if not stream.startswith(self.HEADER_MAGIC) or len(stream) < 100:
            return {"valid": False, "length": 0, "metadata": {}}

        # Read 2-byte big-endian page size at offset 16
        raw_page_size = struct.unpack(">H", stream[16:18])[0]
        page_size = 65536 if raw_page_size == 1 else raw_page_size

        # Page size must be a power of 2 between 512 and 65536
        if page_size < 512 or page_size > 65536 or (page_size & (page_size - 1)) != 0:
            return {"valid": False, "length": 0, "metadata": {"error": "Invalid SQLite page size"}}

        # Read database size in pages at offset 28
        page_count = struct.unpack(">I", stream[28:32])[0]
        if page_count == 0:
            page_count = 1

        # Validate Page 1 B-tree header flag at byte offset 100 if stream buffer is large enough
        if len(stream) >= 101:
            btree_page_type = stream[100]
            if btree_page_type not in self.VALID_PAGE_TYPES:
                return {"valid": False, "length": 0, "metadata": {"error": "Invalid SQLite B-tree page header at offset 100"}}

        length = min(page_size * page_count, len(stream))

        # Check database text encoding at offset 56 (1=UTF-8, 2=UTF-16LE, 3=UTF-16BE)
        text_encoding = struct.unpack(">I", stream[56:60])[0]
        encoding_name = {1: "UTF-8", 2: "UTF-16LE", 3: "UTF-16BE"}.get(text_encoding, "Unknown")

        return {
            "valid": True,
            "length": length,
            "metadata": {
                "format": "SQLITE",
                "page_size": page_size,
                "page_count": page_count,
                "encoding": encoding_name
            }
        }