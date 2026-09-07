"""
SectorScanner Engine: Supports deep recursive folder scanning and 
signature-based raw file carving across all major artifact types.
"""

import os
import hashlib
from typing import List, Dict, Any, Callable, Optional

# Comprehensive Signature Database for Multi-Format File Carving
FILE_SIGNATURES = [
    # --- IMAGES ---
    {"type": "PNG", "category": "Images", "header": b"\x89PNG\r\n\x1a\n", "footer": b"\x49\x45\x4e\x44\xae\x42\x60\x82", "max_size": 25000000},
    {"type": "JPEG", "category": "Images", "header": b"\xff\xd8\xff", "footer": b"\xff\xd9", "max_size": 30000000},
    {"type": "GIF", "category": "Images", "header": b"GIF89a", "footer": b"\x00\x3b", "max_size": 15000000},
    {"type": "BMP", "category": "Images", "header": b"BM", "footer": None, "max_size": 20000000},
    
    # --- DOCUMENTS ---
    {"type": "PDF", "category": "Documents", "header": b"%PDF-", "footer": b"%%EOF", "max_size": 50000000},
    {"type": "DOCX/XLSX", "category": "Documents", "header": b"PK\x03\x04\x14\x00\x06\x00", "footer": b"PK\x05\x06", "max_size": 50000000},
    {"type": "DOC", "category": "Documents", "header": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "footer": None, "max_size": 30000000},
    {"type": "RTF", "category": "Documents", "header": b"{\\rtf1", "footer": b"}", "max_size": 20000000},

    # --- ARCHIVES ---
    {"type": "ZIP", "category": "Archives", "header": b"PK\x03\x04", "footer": b"PK\x05\x06", "max_size": 100000000},
    {"type": "7Z", "category": "Archives", "header": b"7z\xbc\xaf\x27\x1c", "footer": None, "max_size": 100000000},
    {"type": "RAR", "category": "Archives", "header": b"Rar!\x1a\x07", "footer": None, "max_size": 100000000},
    {"type": "GZ", "category": "Archives", "header": b"\x1f\x8b\x08", "footer": None, "max_size": 100000000},

    # --- SYSTEM DATABASES ---
    {"type": "SQLITE", "category": "System Databases", "header": b"SQLite format 3\x00", "footer": None, "max_size": 150000000},
    {"type": "EDB", "category": "System Databases", "header": b"\xef\xcd\xab\x89", "footer": None, "max_size": 200000000},

    # --- MEDIA STREAMS ---
    {"type": "MP4", "category": "Media Streams", "header": b"\x00\x00\x00", "footer": None, "max_size": 300000000},
    {"type": "MP3", "category": "Media Streams", "header": b"\xff\xfb", "footer": None, "max_size": 30000000},
    {"type": "WAV", "category": "Media Streams", "header": b"RIFF", "footer": None, "max_size": 100000000},
    {"type": "AVI", "category": "Media Streams", "header": b"RIFF", "footer": None, "max_size": 300000000},
]


class SectorScanner:
    """Forensic scanner handling directory traversal and raw byte file carving."""

    def __init__(self, target_path: str):
        self.target_path = target_path

    def scan(self, recursive: bool = True, progress_callback: Optional[Callable[[float], None]] = None) -> List[Dict[str, Any]]:
        if os.path.isdir(self.target_path):
            return self._scan_directory(recursive, progress_callback)
        elif os.path.isfile(self.target_path):
            return self._scan_raw_media(progress_callback)
        return []

    def _classify_header(self, header_bytes: bytes) -> tuple:
        for sig in FILE_SIGNATURES:
            if header_bytes.startswith(sig["header"]):
                return sig["type"], sig["category"]
        return "UNKNOWN", "Unclassified"

    def _scan_directory(self, recursive: bool, progress_callback: Optional[Callable[[float], None]]) -> List[Dict[str, Any]]:
        results = []
        file_paths = []

        if recursive:
            for root, _, files in os.walk(self.target_path):
                for f in files:
                    file_paths.append(os.path.join(root, f))
        else:
            for f in os.listdir(self.target_path):
                full = os.path.join(self.target_path, f)
                if os.path.isfile(full):
                    file_paths.append(full)

        total_files = len(file_paths)
        if total_files == 0:
            return results

        for idx, path in enumerate(file_paths, start=1):
            try:
                size_bytes = os.path.getsize(path)
                with open(path, "rb") as fp:
                    header = fp.read(32)
                    fp.seek(0)
                    file_hash = hashlib.sha256(fp.read()).hexdigest()

                file_type, category = self._classify_header(header)
                if file_type == "UNKNOWN":
                    ext = os.path.splitext(path)[1].replace(".", "").upper()
                    file_type = ext if ext else "RAW"

                results.append({
                    "type": file_type,
                    "category": category,
                    "original_name": os.path.basename(path),
                    "source_file": path,
                    "drive_path": self.target_path,
                    "sector": idx,
                    "offset": 0,
                    "size_bytes": size_bytes,
                    "confidence_score": 100.0 if category != "Unclassified" else 85.0,
                    "sha256": file_hash
                })
            except Exception:
                pass

            if progress_callback:
                progress_callback((idx / total_files) * 100.0)

        return results

    def _scan_raw_media(self, progress_callback: Optional[Callable[[float], None]]) -> List[Dict[str, Any]]:
        results = []
        file_size = os.path.getsize(self.target_path)
        chunk_size = 1024 * 1024  # 1MB
        offset = 0

        with open(self.target_path, "rb") as f:
            while offset < file_size:
                f.seek(offset)
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                for sig in FILE_SIGNATURES:
                    header_idx = chunk.find(sig["header"])
                    if header_idx != -1:
                        found_offset = offset + header_idx
                        extracted_size = sig["max_size"]
                        
                        f.seek(found_offset)
                        data_sample = f.read(min(extracted_size, file_size - found_offset))
                        file_hash = hashlib.sha256(data_sample).hexdigest()

                        results.append({
                            "type": sig["type"],
                            "category": sig["category"],
                            "original_name": None,
                            "source_file": self.target_path,
                            "drive_path": self.target_path,
                            "sector": found_offset // 512,
                            "offset": found_offset,
                            "size_bytes": len(data_sample),
                            "confidence_score": 98.5,
                            "sha256": file_hash
                        })

                offset += chunk_size
                if progress_callback and file_size > 0:
                    progress_callback(min((offset / file_size) * 100.0, 100.0))

        return results