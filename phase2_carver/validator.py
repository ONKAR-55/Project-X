"""
CarveValidator: Calculates confidence scores (0-100%) for carved files.
"""

from typing import Dict, Any
from core.entropy import calculate_entropy

class CarveValidator:
    """Calculates confidence percentage for recovered file candidates."""

    def calculate_confidence(self, file_type: str, data: bytes, parse_metadata: Dict[str, Any]) -> float:
        """Evaluate structural validity and entropy to compute confidence score."""
        if not parse_metadata.get("valid", False):
            return 0.0

        score = 50.0  # Base score for valid header magic
        meta = parse_metadata.get("metadata", parse_metadata)
        clean_type = file_type.upper()

        entropy = calculate_entropy(data)

        if clean_type == "JPEG":
            if 6.5 <= entropy <= 7.98:
                score += 25.0
            elif 4.0 <= entropy < 6.5:
                score += 10.0

            if meta.get("markers_found", 0) > 2:
                score += 15.0
            if meta.get("has_exif"):
                score += 10.0

        elif clean_type == "PNG":
            if meta.get("valid_crc_count", 0) > 0 and meta.get("invalid_crc_count", 0) == 0:
                score += 30.0
            if meta.get("has_ihdr") and meta.get("has_iend"):
                score += 20.0

        elif clean_type == "PDF":
            if meta.get("has_catalog"):
                score += 25.0
            if meta.get("has_xref"):
                score += 25.0

        elif clean_type == "ZIP":
            if meta.get("local_files_count", 0) == meta.get("central_directories_count", 0) and meta.get("local_files_count", 0) > 0:
                score += 30.0
            elif meta.get("local_files_count", 0) > 0:
                score += 20.0

        elif clean_type == "MP4":
            if meta.get("has_moov") and meta.get("has_mdat"):
                score += 35.0
            elif meta.get("has_moov") or meta.get("has_mdat"):
                score += 20.0
            if meta.get("major_brand"):
                score += 15.0

        elif clean_type == "SQLITE":
            if meta.get("page_size", 0) in [512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]:
                score += 25.0
            if meta.get("page_count", 0) > 0:
                score += 25.0

        return min(100.0, max(0.0, score))