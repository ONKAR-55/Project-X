"""
CarveValidator: Calculates confidence scores (0-100%) for carved files based on structural integrity and Shannon entropy metrics.
"""

from typing import Dict, Any
from core.entropy import calculate_entropy

class CarveValidator:
    """Calculates confidence percentage for recovered file candidates."""

    def calculate_confidence(self, file_type: str, data: bytes, parse_metadata: Dict[str, Any]) -> float:
        """
        Evaluate structural validity and data entropy to compute a confidence score from 0.0 to 100.0%.
        """
        score = 0.0
        meta = parse_metadata.get("metadata", {})

        if not parse_metadata.get("valid", False):
            return 0.0

        # Base confidence for valid header/footer matching
        score += 50.0

        entropy = calculate_entropy(data)

        if file_type == "JPEG":
            # JPEGs typically have high entropy (compressed image data: ~7.0 - 7.9)
            if 6.5 <= entropy <= 7.98:
                score += 30.0
            elif 4.0 <= entropy < 6.5:
                score += 15.0

            if meta.get("markers_found", 0) > 2:
                score += 20.0

        elif file_type == "PNG":
            # Valid PNG chunk CRCs add significant confidence
            if meta.get("valid_crc_count", 0) > 0 and meta.get("invalid_crc_count", 0) == 0:
                score += 30.0
            if meta.get("has_ihdr") and meta.get("has_iend"):
                score += 20.0

        elif file_type == "PDF":
            if meta.get("has_catalog"):
                score += 25.0
            if meta.get("has_xref"):
                score += 25.0

        elif file_type == "ZIP":
            if meta.get("local_files_count", 0) == meta.get("central_directories_count", 0):
                score += 30.0
            if meta.get("local_files_count", 0) > 0:
                score += 20.0

        return min(100.0, max(0.0, score))
