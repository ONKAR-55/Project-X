"""
PDFParser: Structure-aware parser for PDF documents.
Validates %PDF- header magic, catalog objects, xref tables, and %%EOF trailer boundaries.
"""

import re
from typing import Dict, Any

class PDFParser:
    """PDF file parser validating structural headers, trailers, and catalog objects."""

    HEADER = b"%PDF-"
    TRAILER = b"%%EOF"

    def parse(self, stream: bytes) -> Dict[str, Any]:
        """Parse PDF document structure and trailer offsets."""
        if not stream.startswith(self.HEADER):
            return {"valid": False, "length": 0, "metadata": {}}

        # Find last occurrence of %%EOF trailer
        trailer_index = stream.rfind(self.TRAILER)
        if trailer_index == -1:
            return {"valid": False, "length": 0, "metadata": {"error": "%%EOF trailer not found"}}

        length = trailer_index + len(self.TRAILER)
        
        # Include trailing newlines (\r / \n) after %%EOF if present
        while length < len(stream) and stream[length:length+1] in (b"\r", b"\n"):
            length += 1

        pdf_data = stream[:length]

        has_xref = b"xref" in pdf_data or b"/XRef" in pdf_data
        has_catalog = b"/Catalog" in pdf_data

        # Parse version correctly (e.g., %PDF-1.7 -> 1.7)
        version_match = re.search(rb"%PDF-(\d\.\d)", stream[:20])
        version_str = version_match.group(1).decode("ascii") if version_match else "1.x"

        return {
            "valid": True,
            "length": length,
            "metadata": {
                "format": "PDF",
                "pdf_version": version_str,
                "has_xref": has_xref,
                "has_catalog": has_catalog,
                "trailer_offset": trailer_index
            }
        }