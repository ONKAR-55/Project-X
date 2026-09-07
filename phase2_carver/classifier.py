"""
ArtifactClassifier: Categorizes carved file artifacts into functional groups.
"""

from typing import Dict, Any, Optional

CATEGORY_MAPPING = {
    "JPEG": "Images",
    "PNG": "Images",
    "GIF": "Images",
    "PDF": "Documents",
    "DOCX": "Documents",
    "ZIP": "Archives",
    "TAR": "Archives",
    "GZ": "Archives",
    "SQLITE": "System Databases",
    "DB": "System Databases",
    "MP4": "Media Streams",
    "AVI": "Media Streams",
    "MKV": "Media Streams"
}

class ArtifactClassifier:
    """Classifies recovered binary streams into standard forensic categories."""

    def classify(self, file_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Return target category name for file type."""
        clean_type = file_type.upper()
        if metadata and metadata.get("is_docx"):
            return "Documents"
        return CATEGORY_MAPPING.get(clean_type, "Unclassified Artifacts")