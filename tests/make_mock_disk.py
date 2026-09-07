#!/usr/bin/env python3
"""
make_mock_disk.py: Generates synthetic raw .img disk datasets containing valid file signatures (JPEG, PNG, PDF, ZIP, MP4, SQLite),
slack space, and unallocated sector padding for testing sanitization and carving algorithms.
"""

import os
import zlib
import struct
import argparse

SECTOR_SIZE = 512

def build_valid_jpeg() -> bytes:
    """Construct minimal valid JPEG byte stream with SOI, APP0, DQT, SOS, and EOI."""
    soi = b"\xFF\xD8"
    app0 = b"\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    dqt = b"\xFF\xDB\x00\x43" + (b"\x01" * 67)
    sos = b"\xFF\xDA\x00\x08\x01\x01\x00\x00\x3F\x00" + b"\x00"  # Start of Scan + payload
    eoi = b"\xFF\xD9"
    return soi + app0 + dqt + sos + eoi

def build_valid_png() -> bytes:
    """Construct minimal valid PNG byte stream with correct CRC checksums."""
    header = b"\x89PNG\r\n\x1A\n"
    
    # IHDR Chunk
    ihdr_type = b"IHDR"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr_crc = struct.pack(">I", zlib.crc32(ihdr_type + ihdr_data) & 0xFFFFFFFF)
    ihdr_chunk = struct.pack(">I", len(ihdr_data)) + ihdr_type + ihdr_data + ihdr_crc

    # IEND Chunk
    iend_type = b"IEND"
    iend_data = b""
    iend_crc = struct.pack(">I", zlib.crc32(iend_type + iend_data) & 0xFFFFFFFF)
    iend_chunk = struct.pack(">I", 0) + iend_type + iend_data + iend_crc

    return header + ihdr_chunk + iend_chunk

def build_valid_pdf() -> bytes:
    """Construct minimal valid PDF byte stream."""
    header = b"%PDF-1.4\n"
    body = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    xref = b"xref\n0 1\n0000000000 65535 f \n"
    trailer = b"trailer\n<< /Size 1 /Root 1 0 R >>\nstartxref\n50\n%%EOF\n"
    return header + body + xref + trailer

def build_valid_zip() -> bytes:
    """Construct minimal valid ZIP archive byte stream."""
    local_header = b"PK\x03\x04\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00test.txt"
    central_dir = b"PK\x01\x02\x14\x00\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00test.txt"
    eocd = b"PK\x05\x06\x00\x00\x00\x00\x01\x00\x01\x00\x37\x00\x00\x00\x1E\x00\x00\x00\x00\x00"
    return local_header + central_dir + eocd

def build_valid_mp4() -> bytes:
    """Construct minimal valid MP4 stream with ftyp and moov boxes."""
    ftyp_box = struct.pack(">I", 16) + b"ftypisom" + b"\x00\x00\x02\x00"
    moov_box = struct.pack(">I", 8) + b"moov"
    return ftyp_box + moov_box

def build_valid_sqlite() -> bytes:
    """Construct minimal valid SQLite database with valid header and B-tree page byte at offset 100."""
    header = b"SQLite format 3\x00"            # 16 bytes (offsets 0..15)
    page_size = struct.pack(">H", 4096)        # 2 bytes (offsets 16..17)
    file_format = b"\x01\x01" + b"\x00" * 8   # 10 bytes (offsets 18..27)
    page_count = struct.pack(">I", 2)          # 4 bytes (offsets 28..31)
    padding = b"\x00" * 24                     # 24 bytes (offsets 32..55)
    encoding = struct.pack(">I", 1)            # 4 bytes (offsets 56..59)
    rest_header = b"\x00" * 40                 # 40 bytes (offsets 60..99)
    btree_leaf_flag = b"\x0D"                  # Offset 100: Table Leaf Page marker
    
    total_hdr = header + page_size + file_format + page_count + padding + encoding + rest_header + btree_leaf_flag
    remaining_bytes = (4096 * 2) - len(total_hdr)
    return total_hdr + (b"\x00" * remaining_bytes)

def build_corrupt_header() -> bytes:
    """Construct corrupt header to verify false-positive elimination."""
    return b"\xFF\xD8\xFF\x00CORRUPTED_HEADER_DATA_NO_EOI" + (b"\xFF" * 100)

def generate_mock_disk(output_path: str, size_mb: int = 2):
    """Generate raw disk image populated with synthetic file structures placed at sector boundaries."""
    total_bytes = size_mb * 1024 * 1024
    total_sectors = total_bytes // SECTOR_SIZE
    disk_data = bytearray(b"\x00" * total_bytes)

    def write_at_sector(sector_idx: int, content: bytes):
        start = sector_idx * SECTOR_SIZE
        disk_data[start : start + len(content)] = content

    # Sector 2: JPEG file
    write_at_sector(2, build_valid_jpeg())

    # Sector 10: PNG file
    write_at_sector(10, build_valid_png())

    # Sector 20: PDF file
    write_at_sector(20, build_valid_pdf())

    # Sector 30: ZIP file
    write_at_sector(30, build_valid_zip())

    # Sector 40: MP4 file
    write_at_sector(40, build_valid_mp4())

    # Sector 50: SQLite DB
    write_at_sector(50, build_valid_sqlite())

    # Sector 70: Corrupt false-positive header
    write_at_sector(70, build_corrupt_header())

    with open(output_path, "wb") as f:
        f.write(disk_data)

    print(f"Generated synthetic disk image: '{output_path}' ({size_mb} MB, {total_sectors} sectors).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic Mock Disk Generator")
    parser.add_argument("--output", type=str, default="mock_disk.img", help="Output path for raw .img disk dataset")
    parser.add_argument("--size-mb", type=int, default=2, help="Size of raw disk image in megabytes")
    args = parser.parse_args()

    generate_mock_disk(args.output, args.size_mb)