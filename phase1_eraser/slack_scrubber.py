"""
SlackScrubber: Identifies and zeros out file slack space across cluster boundaries.
"""

import os
import logging
from phase1_eraser.direct_flusher import DirectFlusher

logger = logging.getLogger("ProjectX.Phase1.SlackScrubber")

CLUSTER_SIZE = 4096

class SlackScrubber:
    """Zeroes out unallocated slack bytes between EOF and cluster allocation boundaries."""

    def __init__(self, cluster_size: int = CLUSTER_SIZE):
        self.cluster_size = cluster_size

    def scrub_file_slack(self, file_path: str) -> int:
        """
        Zero out file slack space for a given file path.
        Returns the number of slack bytes zeroed out.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Target file does not exist: {file_path}")

        file_size = os.path.getsize(file_path)
        remainder = file_size % self.cluster_size

        if remainder == 0:
            logger.info(f"No slack space found in {file_path} (file size aligns perfectly with cluster size {self.cluster_size}).")
            return 0

        slack_bytes = self.cluster_size - remainder
        logger.info(f"File {file_path}: size={file_size} bytes, slack space={slack_bytes} bytes.")

        # Open file in binary write mode and fill slack up to cluster boundary with zeroes
        with open(file_path, "r+b") as f:
            f.seek(file_size)
            f.write(b"\x00" * slack_bytes)
            f.flush()
            DirectFlusher.flush(f)

        logger.info(f"Successfully scrubbed {slack_bytes} slack bytes from {file_path}")
        return slack_bytes

    def scrub_directory_slack(self, dir_path: str) -> int:
        """Recursively scrub file slack space for all files in a directory."""
        total_scrubbed = 0
        for root, _, files in os.walk(dir_path):
            for file in files:
                full_path = os.path.join(root, file)
                try:
                    total_scrubbed += self.scrub_file_slack(full_path)
                except Exception as e:
                    logger.error(f"Error scrubbing slack for {full_path}: {e}")
        return total_scrubbed
