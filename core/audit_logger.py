"""
AuditLogger: Cryptographically signed HMAC-SHA256 audit logger for data sanitization and carving operations.
Generates structured JSON and PDF compliance reports.
"""

import os
import json
import hmac
import hashlib
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ProjectX.Core.AuditLogger")

class AuditLogger:
    """Generates tamper-evident audit logs signed with HMAC-SHA256."""

    def __init__(self, secret_key: bytes = b"ProjectX_Default_HMAC_Secret_2026"):
        self.secret_key = secret_key
        self.entries: List[Dict[str, Any]] = []
        self.session_id = hashlib.sha256(str(time.time()).encode('utf-8')).hexdigest()[:16]

    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Record an operation event with timestamp and payload."""
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        entry = {
            "session_id": self.session_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "details": details
        }
        self.entries.append(entry)
        logger.info(f"Audit Log [{event_type}]: {details.get('target', '')} - {details.get('status', 'OK')}")

    def compute_signature(self) -> str:
        """Compute HMAC-SHA256 over all logged entries."""
        data_str = json.dumps(self.entries, sort_keys=True)
        return hmac.new(self.secret_key, data_str.encode("utf-8"), hashlib.sha256).hexdigest()

    def export_json(self, file_path: str) -> str:
        """Export signed audit report as JSON."""
        signature = self.compute_signature()
        report = {
            "title": "Project-X Audit Compliance Report",
            "session_id": self.session_id,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "signature_hmac_sha256": signature,
            "events_count": len(self.entries),
            "events": self.entries
        }

        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Exported signed JSON audit report to {file_path}")
        return file_path

    def export_pdf(self, file_path: str) -> Optional[str]:
        """Export signed audit report as a PDF document using reportlab."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
        except ImportError:
            logger.warning("ReportLab library not available. Skipping PDF audit export.")
            return None

        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        doc = SimpleDocTemplate(
            file_path, 
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f"<b>Project-X Audit Compliance Report</b>", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"<b>Session ID:</b> {self.session_id}", styles['Normal']))
        elements.append(Paragraph(f"<b>Generated At:</b> {time.strftime('%Y-%m-%d %H:%M:%S UTC')}", styles['Normal']))
        elements.append(Paragraph(f"<b>HMAC-SHA256 Signature:</b> <font size=7>{self.compute_signature()}</font>", styles['Normal']))
        elements.append(Spacer(1, 18))

        # Build table of logged events / carved artifacts
        table_data = [["Timestamp", "Type / Event", "Offset / Target", "Score / Status", "SHA-256 Hash"]]
        for entry in self.entries:
            ts = entry["timestamp"]
            etype = entry["event_type"]
            details = entry.get("details", {})
            
            target = str(details.get("target", details.get("offset", "N/A")))[:20]
            status = str(details.get("status", f"Score: {details.get('confidence_score', 'N/A')}%"))[:18]
            file_hash = str(details.get("sha256", "N/A"))[:16] + "..." if details.get("sha256") else "N/A"
            table_data.append([ts, etype, target, status, file_hash])

        t = Table(table_data, colWidths=[100, 100, 100, 100, 120])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(t)

        doc.build(elements)
        logger.info(f"Exported PDF audit report to {file_path}")
        return file_path


    @staticmethod
    def verify_report(json_report_path: str, secret_key: bytes = b"ProjectX_Default_HMAC_Secret_2026") -> bool:
        """Verify HMAC-SHA256 signature of a JSON audit report."""
        with open(json_report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        signature = report.get("signature_hmac_sha256")
        events = report.get("events", [])
        data_str = json.dumps(events, sort_keys=True)
        computed = hmac.new(secret_key, data_str.encode("utf-8"), hashlib.sha256).hexdigest()

        is_valid = hmac.compare_digest(signature, computed)
        logger.info(f"Audit report verification for {json_report_path}: {'VALID' if is_valid else 'TAMPERED/INVALID'}")
        return is_valid
