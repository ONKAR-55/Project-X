"""
test_erasure.py: Integration & unit tests for Phase 1 sanitization engine modules.
"""

import os
import pytest
from core.entropy import calculate_entropy, calculate_file_entropy
from core.audit_logger import AuditLogger
from phase1_eraser.block_overwriter import BlockOverwriter
from phase1_eraser.slack_scrubber import SlackScrubber
from phase1_eraser.metadata_wiper import MetadataWiper
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
    # NIST pseudorandom pass should result in high entropy (> 7.5)
    assert entropy > 7.5

def test_dod_5220_3pass_wipe(mock_disk):
    overwriter = BlockOverwriter(mock_disk)
    overwriter.wipe(method="dod_5220_3pass")
    
    entropy = calculate_file_entropy(mock_disk)
    assert entropy > 7.5

def test_slack_scrubber(tmp_path):
    test_file = tmp_path / "slack_test.dat"
    # Write 100 bytes (cluster size 4096 => 3996 slack bytes)
    test_file.write_bytes(b"A" * 100)
    
    scrubber = SlackScrubber(cluster_size=4096)
    scrubbed_bytes = scrubber.scrub_file_slack(str(test_file))
    
    assert scrubbed_bytes == 3996
    assert os.path.getsize(str(test_file)) == 4096
    
    data = test_file.read_bytes()
    assert data[:100] == b"A" * 100
    assert data[100:] == b"\x00" * 3996

def test_metadata_wiper(tmp_path):
    test_file = tmp_path / "sensitive.txt"
    test_file.write_text("Confidential Data")
    
    wiper = MetadataWiper()
    wiper.sanitize_and_delete(str(test_file))
    
    assert not os.path.exists(str(test_file))

def test_audit_logger_signature(tmp_path):
    json_path = str(tmp_path / "audit_report.json")
    logger = AuditLogger()
    logger.log_event("TEST_WIPE", {"target": "mock_disk.img", "status": "SUCCESS"})
    
    logger.export_json(json_path)
    assert os.path.exists(json_path)
    assert AuditLogger.verify_report(json_path) is True
