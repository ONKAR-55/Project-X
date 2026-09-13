"""
test_carving.py: Integration & unit tests for Phase 2 forensic recovery & parser modules.
"""

import pytest
from phase2_carver.sector_scanner import SectorScanner
from phase2_carver.parsers.jpeg_parser import JPEGParser
from phase2_carver.parsers.png_parser import PNGParser
from phase2_carver.parsers.pdf_parser import PDFParser
from phase2_carver.parsers.zip_parser import ZIPParser
from phase2_carver.parsers.mp4_parser import MP4Parser
from phase2_carver.parsers.sqlite_parser import SQLiteParser
from phase2_carver.classifier import ArtifactClassifier
from core.entropy import classify_entropy, calculate_entropy
from tests.make_mock_disk import (
    generate_mock_disk, build_valid_jpeg, build_valid_png,
    build_valid_pdf, build_valid_zip, build_valid_mp4, build_valid_sqlite
)

@pytest.fixture
def mock_disk(tmp_path):
    disk_path = str(tmp_path / "test_carve_disk.img")
    generate_mock_disk(disk_path, size_mb=1)
    return disk_path

def test_jpeg_parser():
    parser = JPEGParser()
    valid_data = build_valid_jpeg()
    res = parser.parse(valid_data)
    assert res["valid"] is True
    assert res["metadata"]["format"] == "JPEG"

def test_png_parser():
    parser = PNGParser()
    valid_data = build_valid_png()
    res = parser.parse(valid_data)
    assert res["valid"] is True
    assert res["metadata"]["format"] == "PNG"
    assert res["metadata"]["valid_crc_count"] > 0
    assert res["metadata"]["invalid_crc_count"] == 0

def test_pdf_parser():
    parser = PDFParser()
    valid_data = build_valid_pdf()
    res = parser.parse(valid_data)
    assert res["valid"] is True
    assert res["metadata"]["format"] == "PDF"
    assert res["metadata"]["has_catalog"] is True

def test_zip_parser():
    parser = ZIPParser()
    valid_data = build_valid_zip()
    res = parser.parse(valid_data)
    assert res["valid"] is True
    assert res["metadata"]["format"] == "ZIP"
    assert res["metadata"]["local_files_count"] == 1

def test_mp4_parser():
    parser = MP4Parser()
    valid_data = build_valid_mp4()
    res = parser.parse(valid_data)
    assert res["valid"] is True
    assert res["metadata"]["format"] == "MP4"

def test_sqlite_parser():
    parser = SQLiteParser()
    valid_data = build_valid_sqlite()
    res = parser.parse(valid_data)
    assert res["valid"] is True
    assert res["metadata"]["format"] == "SQLITE"
    assert res["metadata"]["page_size"] == 4096

def test_entropy_classification():
    zeroes = b"\x00" * 512
    low_ent = calculate_entropy(zeroes)
    assert low_ent == 0.0
    assert "Low" in classify_entropy(low_ent)

def test_carve_validator():
    png_data = build_valid_png()
    png_res = PNGParser().parse(png_data)
    score = validator.calculate_confidence("PNG", png_data, png_res)
    assert score >= 90.0

def test_artifact_classifier():
    classifier = ArtifactClassifier()
    assert classifier.classify("JPEG") == "Images"
    assert classifier.classify("PDF") == "Documents"
    assert classifier.classify("ZIP") == "Archives"
    assert classifier.classify("SQLITE") == "System Databases"
    assert classifier.classify("MP4") == "Media Streams"

def test_sector_scanner(mock_disk):
    scanner = SectorScanner(mock_disk)
    results = scanner.scan()
    
    types_found = {r["type"] for r in results}
    assert "JPEG" in types_found
    assert "PNG" in types_found
    assert "PDF" in types_found
    assert "ZIP" in types_found
    assert "MP4" in types_found
    assert "SQLITE" in types_found

    for r in results:
        assert r["confidence_score"] > 50.0
        assert "sha256" in r
        assert len(r["sha256"]) == 64