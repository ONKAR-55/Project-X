"""
GalleryWidget: PyQt6 visual thumbnail grid preview and metadata inspector for carved image and document artifacts.
"""

import os
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget, QListWidgetItem,
    QLabel, QTextEdit, QPushButton, QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtGui import QPixmap, QImage, QFont
from PyQt6.QtCore import Qt

class GalleryWidget(QWidget):
    """Gallery browser for viewing carved images and itemized forensic artifacts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.carved_artifacts: List[Dict[str, Any]] = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left Panel: Artifact List
        left_box = QGroupBox("Recovered Forensic Artifacts")
        left_layout = QVBoxLayout()
        left_box.setLayout(left_layout)

        self.artifact_list = QListWidget()
        self.artifact_list.itemSelectionChanged.connect(self.on_selection_changed)
        left_layout.addWidget(self.artifact_list)

        splitter.addWidget(left_box)

        # Right Panel: Image Preview & Detail Breakdown
        right_box = QGroupBox("Artifact Preview & Inspection")
        right_layout = QVBoxLayout()
        right_box.setLayout(right_layout)

        self.preview_label = QLabel("Select an artifact to preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(320, 240)
        self.preview_label.setStyleSheet("background-color: #0F172A; color: #64748B; border: 1px solid #334155; border-radius: 6px;")
        right_layout.addWidget(self.preview_label)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        font = QFont("Courier New", 9)
        self.details_text.setFont(font)
        self.details_text.setStyleSheet("background-color: #0F172A; color: #38BDF8; border: 1px solid #334155; border-radius: 6px;")
        right_layout.addWidget(self.details_text)

        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export Recovered Artifact...")
        self.export_btn.setStyleSheet("background-color: #3B82F6; color: white; font-weight: bold; padding: 6px;")
        self.export_btn.clicked.connect(self.export_artifact)
        btn_layout.addWidget(self.export_btn)
        right_layout.addLayout(btn_layout)

        splitter.addWidget(right_box)
        splitter.setSizes([350, 650])

    def load_artifacts(self, artifacts: List[Dict[str, Any]]):
        """Populate gallery list with carved file descriptors."""
        self.carved_artifacts = artifacts
        self.artifact_list.clear()

        for idx, item in enumerate(artifacts):
            score = item.get("confidence_score", 0.0)
            label_str = f"[{item['type']}] Sector {item['sector']} ({item['size_bytes']} bytes) - {score:.1f}% Confidence"
            list_item = QListWidgetItem(label_str)
            list_item.setData(Qt.ItemDataRole.UserRole, idx)
            self.artifact_list.addItem(list_item)

        if artifacts:
            self.artifact_list.setCurrentRow(0)

    def on_selection_changed(self):
        items = self.artifact_list.selectedItems()
        if not items:
            return

        idx = items[0].data(Qt.ItemDataRole.UserRole)
        artifact = self.carved_artifacts[idx]
        data = artifact.get("data", b"")
        ftype = artifact.get("type", "UNKNOWN")

        # Update metadata details view
        details = (
            f"Artifact Category: {artifact.get('category', 'Unclassified')}\n"
            f"File Format:       {ftype}\n"
            f"Sector Index:      {artifact.get('sector')}\n"
            f"Disk Byte Offset:  {artifact.get('offset')} bytes\n"
            f"Stream Length:     {artifact.get('size_bytes')} bytes\n"
            f"Confidence Score:  {artifact.get('confidence_score'):.2f}%\n"
            f"SHA-256 Hash:      {artifact.get('sha256')}\n"
            f"Parser Metadata:   {artifact.get('metadata')}\n"
        )
        self.details_text.setText(details)

        # Image Preview Handling for JPEG/PNG
        if ftype in ["JPEG", "PNG"] and data:
            qimg = QImage()
            if qimg.loadFromData(data):
                pixmap = QPixmap.fromImage(qimg).scaled(
                    320, 240,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_label.setPixmap(pixmap)
            else:
                self.preview_label.setText("Invalid Image Binary Data")
        else:
            self.preview_label.setText(f"Preview unavailable for format '{ftype}'\n(Binary artifact inspection standard)")

    def export_artifact(self):
        items = self.artifact_list.selectedItems()
        if not items:
            return

        idx = items[0].data(Qt.ItemDataRole.UserRole)
        artifact = self.carved_artifacts[idx]
        ext = artifact.get("type", "bin").lower()

        default_name = f"recovered_sector_{artifact.get('sector')}.{ext}"
        path, _ = QFileDialog.getSaveFileName(self, "Export Recovered Artifact", default_name, f"All Files (*.{ext})")

        if path:
            try:
                with open(path, "wb") as f:
                    f.write(artifact.get("data", b""))
                QMessageBox.information(self, "Export Successful", f"Saved carved artifact to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to save artifact: {e}")
