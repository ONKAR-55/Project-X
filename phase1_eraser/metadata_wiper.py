"""
MetadataWiper: MFT record & Inode metadata obfuscation.
Wipes file timestamps (atime, mtime, ctime), randomizes filenames prior to deletion, and truncates file handles.
"""

import os
import secrets
import string
import logging

logger = logging.getLogger("ProjectX.Phase1.MetadataWiper")

class MetadataWiper:
    """Obfuscates file metadata attributes (timestamps, filenames) prior to file unlink."""

    @staticmethod
    def randomize_timestamps(file_path: str, epoch_time: float = 0.0):
        """Reset file access and modification timestamps to epoch zero (1970-01-01) or random date."""
        try:
            os.utime(file_path, (epoch_time, epoch_time))
            logger.info(f"Reset timestamps for {file_path} to {epoch_time}")
        except Exception as e:
            logger.error(f"Failed to reset timestamps for {file_path}: {e}")

    @staticmethod
    def obfuscate_filename(file_path: str) -> str:
        """
        Rename target file to a randomized alphanumeric string of equal length
        to obscure MFT entry / Inode directory entry strings.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        dir_name, old_name = os.path.split(file_path)
        random_chars = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(len(old_name)))
        new_path = os.path.join(dir_name, random_chars)

        os.rename(file_path, new_path)
        logger.info(f"Obfuscated filename: {old_name} -> {random_chars}")
        return new_path

    def sanitize_and_delete(self, file_path: str):
        """Full metadata wipe workflow: reset timestamps, truncate file size, obfuscate filename, and remove file."""
        if not os.path.exists(file_path):
            return

        # 1. Reset timestamps
        self.randomize_timestamps(file_path, 0.0)

        # 2. Truncate to zero size
        with open(file_path, "w") as f:
            f.truncate(0)

        # 3. Obfuscate filename
        obfuscated_path = self.obfuscate_filename(file_path)

        # 4. Unlink file
        os.remove(obfuscated_path)
        logger.info(f"Metadata wipe and deletion complete for {file_path}")
