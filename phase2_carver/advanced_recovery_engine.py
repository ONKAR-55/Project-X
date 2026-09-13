"""
AdvancedRecoveryEngine: Orchestrates folder hierarchy rebuilding, file extraction, 
accuracy validation, and comprehensive forensic report generation.
"""

import os
import json
import shutil
import datetime
from typing import List, Dict, Any, Optional
from phase2_carver.validator import FileIntegrityValidator
from phase2_carver.tree_reconstructor import TreeReconstructor


class AdvancedRecoveryEngine:
    """Handles deep tree recovery, file extraction, failure tracking, and reporting."""

    def __init__(self, destination_root: str):
        self.destination_root = os.path.abspath(destination_root)

    def execute_recovery(
        self,
        artifacts: List[Dict[str, Any]],
        base_scan_path: str,
        cutoff_date: Optional[datetime.datetime] = None,
        recursive_nested: bool = True
    ) -> Dict[str, Any]:
        """
        Restores deleted folders and files while keeping parent/child hierarchy intact.
        Outputs a detailed performance and forensic accuracy report.
        """
        os.makedirs(self.destination_root, exist_ok=True)
        reconstructor = TreeReconstructor(cutoff_date=cutoff_date, recursive=recursive_nested)

        recovered_files = []
        failed_items = []
        created_folders = set()

        total_bytes_restored = 0
        accuracy_scores = []

        for idx, item in enumerate(artifacts, start=1):
            source_path = item.get("source_file") or item.get("drive_path", "")
            item_time = item.get("timestamp") or os.path.getmtime(source_path) if os.path.exists(source_path) else 0

            # 1. Apply Date Filtering
            if not reconstructor.is_within_date_range(item_time):
                continue

            # 2. Reconstruct Parent & Nested Folder Hierarchy
            rel_dir = reconstructor.map_relative_structure(base_scan_path, source_path) if recursive_nested else ""
            target_dir = os.path.join(self.destination_root, rel_dir)
            
            try:
                os.makedirs(target_dir, exist_ok=True)
                created_folders.add(target_dir)
            except Exception as e:
                failed_items.append({
                    "item": source_path,
                    "reason": f"Failed to create target folder directory: {e}"
                })
                continue

            # Determine Output Filename
            original_name = item.get("original_name")
            file_ext = (item.get("type") or "bin").lower()
            sha_prefix = (item.get("sha256") or f"id_{idx}")[:8]

            filename = original_name if original_name else f"restored_{idx:04d}_{sha_prefix}.{file_ext}"
            dest_file_path = os.path.join(target_dir, filename)

            # Prevent Filename Overwrites
            counter = 1
            b_name, ext = os.path.splitext(filename)
            while os.path.exists(dest_file_path):
                dest_file_path = os.path.join(target_dir, f"{b_name}_{counter}{ext}")
                counter += 1

            # 3. Perform Extraction/Restoration
            try:
                if item.get("status") == "Carved (Deleted Candidate)":
                    offset = item.get("offset", 0)
                    size = item.get("size_bytes", 0)
                    with open(source_path, "rb") as f_in:
                        f_in.seek(offset)
                        data = f_in.read(size)
                    with open(dest_file_path, "wb") as f_out:
                        f_out.write(data)
                else:
                    shutil.copy2(source_path, dest_file_path)

                # 4. Calculate File Integrity & Restoration Accuracy
                val_result = FileIntegrityValidator.calculate_accuracy(
                    dest_file_path,
                    expected_type=file_ext,
                    expected_size=item.get("size_bytes", 0)
                )

                file_size = os.path.getsize(dest_file_path)
                total_bytes_restored += file_size
                accuracy_scores.append(val_result["accuracy_score"])

                recovered_files.append({
                    "original_source": source_path,
                    "restored_path": dest_file_path,
                    "size_bytes": file_size,
                    "accuracy_score": val_result["accuracy_score"],
                    "status": val_result["status"]
                })

            except Exception as err:
                failed_items.append({
                    "item": source_path,
                    "reason": str(err)
                })

        # 5. Compile Final Forensic Accuracy Report
        avg_accuracy = round(sum(accuracy_scores) / len(accuracy_scores), 2) if accuracy_scores else 0.0

        report = {
            "recovery_summary": {
                "timestamp": datetime.datetime.now().isoformat(),
                "cutoff_date_applied": cutoff_date.isoformat() if cutoff_date else "None (All Dates)",
                "nested_folders_restored": len(created_folders),
                "total_files_recovered": len(recovered_files),
                "total_failed_items": len(failed_items),
                "total_data_bytes_restored": total_bytes_restored,
                "overall_restoration_accuracy": f"{avg_accuracy}%"
            },
            "recovered_artifacts": recovered_files,
            "failed_recoveries": failed_items
        }

        report_path = os.path.join(self.destination_root, "recovery_audit_report.json")
        with open(report_path, "w") as rf:
            json.dump(report, rf, indent=4)

        report["report_file_path"] = report_path
        return report