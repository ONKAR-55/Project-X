"""
TreeReconstructor: Handles timestamp filtering, nested directory traversal, 
and reconstruction of deleted folder hierarchies.
"""

import os
import datetime
from typing import List, Dict, Any, Optional


class TreeReconstructor:
    """Filters target paths by date cutoff and maps relative nested directory trees."""

    def __init__(self, cutoff_date: Optional[datetime.datetime] = None, recursive: bool = True):
        self.cutoff_date = cutoff_date
        self.recursive = recursive

    def is_within_date_range(self, timestamp: float) -> bool:
        """Checks if artifact timestamp is on or after the selected cutoff date."""
        if not self.cutoff_date:
            return True
        artifact_date = datetime.datetime.fromtimestamp(timestamp)
        return artifact_date >= self.cutoff_date

    def map_relative_structure(self, base_scan_path: str, item_path: str) -> str:
        """
        Reconstructs original directory structure relative to the destination folder.
        Preserves deleted parent/child subfolder paths.
        """
        norm_base = os.path.normpath(base_scan_path)
        norm_item = os.path.normpath(item_path)

        if norm_item.startswith(norm_base):
            rel_path = os.path.relpath(norm_item, norm_base)
            return os.path.dirname(rel_path)
        
        return ""