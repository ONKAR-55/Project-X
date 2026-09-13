"""
test_erasure.py: Integration & unit tests for Phase 1 sanitization engine modules.
"""

import os
import pytest
from core.entropy import calculate_entropy, calculate_file_entropy
from core.audit_logger import AuditLogger
from phase1_eraser.block_overwriter import BlockOverwriter
from tests.make_mock_disk import generate_mock_disk

@pytest.fixture
def mock_disk(tmp_path):
    disk_path = str(tmp_path / "test_wipe_disk.img")
    generate_mock_disk(disk_path, size_mb=1)
    return disk_path

def test_entropy_calculation():
    zero_bytes = b"\x00" * 512
    assert calculate_entropy(zero_bytes) == 0.0

    pattern_bytes = bytes(range(256)) * 2
    assert calculate_entropy(pattern_bytes) == 8.0

def test_single_pass_zero_wipe(mock_disk):
    overwriter = BlockOverwriter(mock_disk)
    overwriter.wipe(method="zero")
    
    entropy = calculate_file_entropy(mock_disk)
    assert entropy == 0.0

def test_nist_800_88_wipe(mock_disk):
    overwriter = BlockOverwriter(mock_disk)
    overwriter.wipe(method="nist_800_88")
    
    entropy = calculate_file_entropy(mock_disk)
    assert entropy > 7.5

def test_dod_5220_3pass_wipe(mock_disk):
    overwriter = BlockOverwriter(mock_disk)
    overwriter.wipe(method="dod_5220_3pass")
    
    entropy = calculate_file_entropy(mock_disk)
    assert entropy > 7.5

def test_audit_logger_signature(tmp_path):
    json_path = str(tmp_path / "audit_report.json")
    logger = AuditLogger()
    logger.log_event("TEST_WIPE", {"target": "mock_disk.img", "status": "SUCCESS"})
    
    logger.export_json(json_path)
    assert os.path.exists(json_path)
    assert AuditLogger.verify_report(json_path) is True