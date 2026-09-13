

import os
from typing import Optional

SECTOR_SIZE = 512


class SafeDiskReader:
    """Reads sector-aligned binary data blocks from physical volumes or disk images."""

    @staticmethod
    def read_sector_aligned(file_or_handle: str, offset: int, length: int) -> Optional[bytes]:
        """Aligns byte offsets to 512-byte boundaries before executing disk read."""
        aligned_offset = (offset // SECTOR_SIZE) * SECTOR_SIZE
        padding = offset - aligned_offset
        read_length = length + padding

        try:
            with open(file_or_handle, "rb", buffering=0) as f:
                f.seek(aligned_offset)
                data = f.read(read_length)
                return data[padding:padding + length]
        except Exception:
            return None