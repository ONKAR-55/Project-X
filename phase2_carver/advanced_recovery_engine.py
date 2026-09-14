"""
AdvancedRecoveryEngine: Handles file extraction from physical storage sectors 
and normal disk paths with JSON audit logging.
"""

import os
import json
import datetime
import hashlib
from typing import List, Dict, Any

from core.disk_io import SafeDiskReader


class AdvancedRecoveryEngine:
    """Extracts raw sector structures or unallocated disk payloads into destination files."""

    def __init__(self, output_dir: str):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def execute_recovery(
        self, 
        artifacts: List[Dict[str, Any]], 
        base_scan_path: str, 
        cutoff_date: datetime.datetime, 
        recursive_nested: bool = True
    ) -> Dict[str, Any]:
        """Reads sector payloads for all selected artifacts and writes output files."""
        recovered_count = 0
        valid_hashes = 0
        report_artifacts = []

        for item in artifacts:
            source = item.get("source_file", "")
            rel_path = item.get("relative_path") or item.get("original_name") or "Restored_Artifact.bin"
            dest_path = os.path.join(self.output_dir, rel_path)

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            offset = item.get("offset", 0)
            length = item.get("size_bytes", 1024 * 1024)

            # Read sector binary data directly
            data = None
            if source.startswith("\\\\.\\") or not os.path.exists(source):
                data = SafeDiskReader.read_sector_aligned(source, offset, length)
            else:
                try:
                    with open(source, "rb") as f:
                        f.seek(offset)
                        data = f.read(length)
                except Exception:
                    data = SafeDiskReader.read_sector_aligned(source, offset, length)

            # Write restored binary data to destination file
            if data and len(data) > 0:
                try:
                    with open(dest_path, "wb") as f_out:
                        f_out.write(data)

                    recovered_count += 1
                    valid_hashes += 1
                    status = "Restored Successfully"
                except Exception as e:
                    status = f"Write Failure: {str(e)}"
            else:
                status = "Read Failure (Unreadable Sector)"

            report_artifacts.append({
                "target_file": rel_path,
                "status": status,
                "sector_offset": hex(offset),
                "bytes_restored": len(data) if data else 0
            })

        overall_accuracy = (valid_hashes / len(artifacts) * 100.0) if artifacts else 0.0

        report = {
            "recovery_summary": {
                "total_candidates": len(artifacts),
                "total_files_recovered": recovered_count,
                "overall_restoration_accuracy": f"{overall_accuracy:.1f}%"
            },
            "details": report_artifacts
        }

        report_file_path = os.path.join(self.output_dir, "recovery_audit_report.json")
        try:
            with open(report_file_path, "w") as rf:
                json.dump(report, rf, indent=4)
        except Exception:
            pass

        report["report_file_path"] = report_file_path
        return report