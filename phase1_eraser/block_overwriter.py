"""
BlockOverwriter Engine: Performs multi-pass pattern overwriting, cache flushing, 
file renaming (metadata wiping), and file unlinking.
"""

import os
import random
import string
from typing import Dict, Any


class BlockOverwriter:
    """Handles low-level sanitization and file deletion."""

    @staticmethod
    def sanitize_and_delete(filepath: str, passes: int = 3) -> Dict[str, Any]:
        """Overwrites data blocks, flushes disk buffers, renames, and unlinks file."""
        abspath = os.path.abspath(filepath)
        if not os.path.exists(abspath):
            return {"success": False, "error": "File not found"}

        try:
            file_size = os.path.getsize(abspath)
            
            # --- Pass 1-3: Multi-Pass Block Overwriting ---
            with open(abspath, "r+b") as f:
                for current_pass in range(1, passes + 1):
                    f.seek(0)
                    if current_pass == 1:
                        pattern = b"\x00" * 65536  # All Zeros
                    elif current_pass == 2:
                        pattern = b"\xFF" * 65536  # All Ones
                    else:
                        pattern = os.urandom(65536) # Random Bytes

                    bytes_written = 0
                    while bytes_written < file_size:
                        chunk = min(65536, file_size - bytes_written)
                        f.write(pattern[:chunk])
                        bytes_written += chunk

                    # Direct Buffer Flush to Physical Storage
                    f.flush()
                    os.fsync(f.fileno())

                # Truncate payload to zero
                f.seek(0)
                f.truncate(0)
                f.flush()
                os.fsync(f.fileno())

            # --- Metadata Wiping (Filename Obfuscation) ---
            dirname = os.path.dirname(abspath)
            random_name = "".join(random.choices(string.ascii_letters + string.digits, k=16))
            obfuscated_path = os.path.join(dirname, random_name)

            os.rename(abspath, obfuscated_path)

            # --- Final Unlink ---
            os.remove(obfuscated_path)

            return {
                "success": True,
                "original_path": abspath,
                "wiped_bytes": file_size,
                "passes_completed": passes
            }

        except Exception as e:
            return {
                "success": False,
                "original_path": abspath,
                "error": str(e)
            }