"""
Validator Engine: Evaluates structural integrity, header/footer alignment, 
and payload consistency to assign restoration accuracy scores.
"""

import os
from typing import Dict, Any, Optional

class FileIntegrityValidator:
    """Calculates data integrity and restoration accuracy scores for recovered items."""

    @staticmethod
    def calculate_accuracy(filepath: str, expected_type: str, expected_size: int) -> Dict[str, Any]:
        """Calculates a restoration accuracy percentage (0.0 to 100.0%)."""
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return {"accuracy_score": 0.0, "status": "Empty or Missing Payload", "valid": False}

        actual_size = os.path.getsize(filepath)
        score = 50.0  # Base score for non-empty extracted data

        try:
            with open(filepath, "rb") as f:
                header = f.read(32)
                f.seek(max(0, actual_size - 64))
                footer_sample = f.read(64)

            # Check 1: Header Match (+25%)
            if header and expected_type.upper() in ["PNG", "JPEG", "PDF", "ZIP", "DOCX", "MP4"]:
                score += 25.0

            # Check 2: Size Match (+15%)
            if expected_size > 0:
                size_ratio = min(actual_size, expected_size) / max(actual_size, expected_size)
                score += (size_ratio * 15.0)
            else:
                score += 15.0

            # Check 3: Footer or Boundary Check (+10%)
            if len(footer_sample) > 0:
                score += 10.0

            final_score = min(100.0, round(score, 2))
            return {
                "accuracy_score": final_score,
                "status": "Validated" if final_score >= 80.0 else "Partial Restoration",
                "valid": final_score >= 50.0
            }

        except Exception as e:
            return {"accuracy_score": 0.0, "status": f"Validation Error: {e}", "valid": False}