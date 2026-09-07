"""
test_recovery_engine.py: Unit tests for batch recovery extraction and directory tree carving.
"""

import os
import pytest
try:
    from phase2_carver.batch_recovery import BatchRecoveryEngine
except ImportError:
    from phase2_carver.recovery_engine import BatchRecoveryEngine

from phase2_carver.sector_scanner import SectorScanner
from tests.make_mock_disk import build_valid_jpeg, build_valid_png, build_valid_pdf

def test_batch_recovery_engine(tmp_path):
    output_dir = str(tmp_path / "recovered_out")
    engine = BatchRecoveryEngine()

    jpeg_bytes = build_valid_jpeg()
    pdf_bytes = build_valid_pdf()

    artifacts = [
        {
            "type": "JPEG",
            "category": "Images",
            "sector": 2,
            "offset": 1024,
            "size_bytes": len(jpeg_bytes),
            "sha256": "fake_hash_1",
            "data": jpeg_bytes
        },
        {
            "type": "PDF",
            "category": "Documents",
            "sector": 10,
            "offset": 5120,
            "size_bytes": len(pdf_bytes),
            "sha256": "fake_hash_2",
            "data": pdf_bytes
        }
    ]

    res = engine.recover_artifacts(artifacts, output_dir)

    assert res["total_recovered"] == 2
    assert res["failed"] == 0
    assert os.path.exists(os.path.join(output_dir, "Images"))
    assert os.path.exists(os.path.join(output_dir, "Documents"))

    # Verify extracted file contents
    saved_files = res["saved_paths"]
    assert len(saved_files) == 2
    for p in saved_files:
        assert os.path.exists(p)
        assert os.path.getsize(p) > 0

def test_directory_tree_scanner(tmp_path):
    # Create synthetic directory tree with nested subdirectories
    parent_dir = tmp_path / "parent_folder"
    nested_dir = parent_dir / "nested" / "deep_folder"
    nested_dir.mkdir(parents=True, exist_ok=True)

    file1 = parent_dir / "sample1.jpg"
    file2 = nested_dir / "sample2.png"

    file1.write_bytes(build_valid_jpeg())
    file2.write_bytes(build_valid_png())

    scanner = SectorScanner(str(parent_dir))
    results = scanner.scan(recursive=True)

    types_found = {r["type"] for r in results}
    assert "JPEG" in types_found
    assert "PNG" in types_found
    assert len(results) == 2