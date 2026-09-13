"""
EraserOrchestrator: Coordinates target file hashing, system trace scanning, 
secure multi-pass sanitization, trace scrubbing, and audit report generation.
"""

import os
import json
import hashlib
import datetime
from typing import Dict, Any
from phase1_eraser.trace_finder import TraceFinder
from phase1_eraser.block_overwriter import BlockOverwriter


class EraserOrchestrator:
    """Executes full destruction workflow and generates audit records."""

    def __init__(self, target_filepath: str):
        self.target_path = os.path.abspath(target_filepath)

    def execute_full_erasure(self, output_report_dir: str = "reports") -> Dict[str, Any]:
        report: Dict[str, Any] = {
            "operation": "Permanent File Destruction & System Trace Scrubbing",
            "timestamp": datetime.datetime.now().isoformat(),
            "target_file": {
                "original_path": self.target_path,
                "filename": os.path.basename(self.target_path),
                "sha256_before_wipe": None,
                "size_bytes": 0,
                "status": "Pending"
            },
            "sanitization_details": {},
            "trace_scrubbing": {
                "removed_traces": [],
                "locked_or_remaining_traces": []
            }
        }

        if not os.path.exists(self.target_path):
            report["target_file"]["status"] = "Failed: File Not Found"
            return report

        # Step 1: Pre-Wipe Metadata & SHA256 Hash Record
        try:
            report["target_file"]["size_bytes"] = os.path.getsize(self.target_path)
            with open(self.target_path, "rb") as f:
                report["target_file"]["sha256_before_wipe"] = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            report["target_file"]["status"] = f"Failed to compute initial hash: {e}"
            return report

        # Step 2: System Trace Discovery
        finder = TraceFinder(self.target_path)
        traces = finder.locate_all_traces()

        # Step 3: Secure Target File Destruction
        wipe_result = BlockOverwriter.sanitize_and_delete(self.target_path, passes=3)
        report["sanitization_details"] = wipe_result

        if wipe_result.get("success"):
            report["target_file"]["status"] = "Successfully Sanitized & Deleted"
        else:
            report["target_file"]["status"] = f"Wipe Failed: {wipe_result.get('error')}"

        # Step 4: Scrub Removable System Traces
        for trace in traces["removable_traces"]:
            t_path = trace["path"]
            scrub_res = BlockOverwriter.sanitize_and_delete(t_path, passes=1)
            if scrub_res.get("success"):
                report["trace_scrubbing"]["removed_traces"].append({
                    "path": t_path,
                    "type": trace["type"],
                    "status": "Scrubbed Successfully"
                })
            else:
                report["trace_scrubbing"]["locked_or_remaining_traces"].append({
                    "path": t_path,
                    "type": trace["type"],
                    "reason": scrub_res.get("error")
                })

        for locked in traces["locked_traces"]:
            report["trace_scrubbing"]["locked_or_remaining_traces"].append({
                "path": locked.get("path"),
                "type": locked.get("type"),
                "reason": locked.get("error", "Access Denied / System Locked")
            })

        # Step 5: Save JSON Audit Report
        os.makedirs(output_report_dir, exist_ok=True)
        report_filename = f"erasure_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = os.path.join(output_report_dir, report_filename)

        with open(report_path, "w") as rf:
            json.dump(report, rf, indent=4)

        report["saved_report_path"] = report_path
        return report