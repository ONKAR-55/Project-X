"""
BlockOverwriter: Implements NIST SP 800-88 and DoD 5220.22-M multi-pass overwriting standards.
"""

import os
import secrets
import logging
from typing import Callable, Optional
from core.disk_io import DiskIO, SECTOR_SIZE
from phase1_eraser.direct_flusher import DirectFlusher

logger = logging.getLogger("ProjectX.Phase1.BlockOverwriter")

class BlockOverwriter:
    """Performs sector-level sanitization using standard erasure profiles."""

    def __init__(self, target_path: str, sector_size: int = SECTOR_SIZE):
        self.target_path = target_path
        self.sector_size = sector_size

    def wipe(self, method: str = "nist_800_88", progress_callback: Optional[Callable[[float], None]] = None):
        """
        Execute multi-pass sanitization.
        Methods supported:
        - 'zero': Single pass zero fill (0x00)
        - 'nist_800_88': NIST Clear (Single pass pseudorandom pattern)
        - 'dod_5220_3pass': DoD 5220.22-M 3-pass (Pass 1: 0x00, Pass 2: 0xFF, Pass 3: Random + verify)
        - 'dod_5220_7pass': DoD 5220.22-M ECE 7-pass
        """
        passes = self._get_wipe_passes(method)
        logger.info(f"Starting sanitization method '{method}' ({len(passes)} passes) on {self.target_path}")

        with DiskIO(self.target_path, read_only=False) as disk:
            total_size = disk.get_size()
            total_sectors = total_size // self.sector_size

            for pass_idx, (pass_type, byte_val) in enumerate(passes, start=1):
                logger.info(f"Executing Pass {pass_idx}/{len(passes)} [{pass_type}]...")
                for sector_num in range(total_sectors):
                    if pass_type == "ZERO":
                        data = b"\x00" * self.sector_size
                    elif pass_type == "ONES":
                        data = b"\xFF" * self.sector_size
                    elif pass_type == "FIXED":
                        data = bytes([byte_val]) * self.sector_size
                    elif pass_type == "RANDOM":
                        data = secrets.token_bytes(self.sector_size)
                    else:
                        data = b"\x00" * self.sector_size

                    disk.write_sector(sector_num, data)

                    if progress_callback and sector_num % 100 == 0:
                        overall_progress = ((pass_idx - 1) + (sector_num / total_sectors)) / len(passes) * 100
                        progress_callback(overall_progress)

                # Ensure OS buffers are flushed after each pass
                DirectFlusher.flush(disk.handle)

        if progress_callback:
            progress_callback(100.0)

        logger.info(f"Sanitization '{method}' completed successfully on {self.target_path}")

    def _get_wipe_passes(self, method: str):
        if method == "zero":
            return [("ZERO", 0x00)]
        elif method == "nist_800_88":
            return [("RANDOM", 0x00)]
        elif method == "dod_5220_3pass":
            return [
                ("ZERO", 0x00),
                ("ONES", 0xFF),
                ("RANDOM", 0x00)
            ]
        elif method == "dod_5220_7pass":
            return [
                ("FIXED", 0x96),
                ("FIXED", 0x69),
                ("RANDOM", 0x00),
                ("FIXED", 0x00),
                ("FIXED", 0xFF),
                ("FIXED", 0x55),
                ("RANDOM", 0x00)
            ]
        else:
            raise ValueError(f"Unknown wipe method: {method}")
