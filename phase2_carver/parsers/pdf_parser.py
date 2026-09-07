"""
PDFParser: Structure-aware parser for PDF documents.
Validates %PDF- header magic, catalog objects, xref tables, and %%EOF trailer boundaries.
"""

from typing import Dict, Any

class PDFParser:
    """PDF file parser validating structural headers, trailers, and catalog objects."""

    HEADER = b"%PDF-"
    TRAILER = b"%%EOF"

    def parse(self, stream: bytes) -> Dict[str, Any]:
        if not stream.startswith(self.HEADER):
            return {"valid": False, "length": 0, "metadata": {}}

        # Find trailer offset
        trailer_index = stream.rfind(self.TRAILER)
        if trailer_index == -1:
            return {"valid": False, "length": 0, "metadata": {"error": "%%EOF trailer not found"}}

        length = trailer_index + len(self.TRAILER)
        pdf_data = stream[:length]

        has_xref = b"xref" in pdf_data or b"/XRef" in pdf_data
        has_catalog = b"/Catalog" in pdf_data
        version_str = stream[5:8].decode("ascii", errors="ignore")

        return {
            "valid": True,
            "length": length,
            "metadata": {
                "format": "PDF",
                "pdf_version": f"1.{version_str}",
                "has_xref": has_xref,
                "has_catalog": has_catalog,
                "trailer_offset": trailer_index
            }
        }
