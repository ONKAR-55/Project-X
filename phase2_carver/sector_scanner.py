"""
SectorScanner: Carves raw volume sectors and maps artifacts to virtual folder 
structures with formatted modification/deletion timestamps.
"""

import os
import sys
import hashlib
import datetime
from typing import List, Dict, Any, Callable, Optional

FILE_SIGNATURES = {
    "png":  {"header": b"\x89PNG\r\n\x1a\n", "footer": b"\x49\x45\x4e\x44\xae\x42\x60\x82", "category": "Images", "max_size": 20 * 1024 * 1024},
    "jpeg": {"header": b"\xff\xd8\xff",       "footer": b"\xff\xd9",                         "category": "Images", "max_size": 15 * 1024 * 1024},
    "pdf":  {"header": b"%PDF-",              "footer": b"%%EOF",                            "category": "Documents", "max_size": 50 * 1024 * 1024},
    "zip":  {"header": b"PK\x03\x04",         "footer": b"PK\x05\x06",                       "category": "Archives", "max_size": 100 * 1024 * 1024},
    "docx": {"header": b"PK\x03\x04",         "footer": b"PK\x05\x06",                       "category": "Documents", "max_size": 50 * 1024 * 1024},
    "mp4":  {"header": b"\x00\x00\x00\x20ftyp", "footer": None,                              "category": "Videos", "max_size": 500 * 1024 * 1024},
}


class SectorScanner:
    """Carves raw storage volumes and organizes deleted file candidates."""

    def __init__(self, target_input: str):
        self.raw_path = self._format_raw_target(target_input)

    def _format_raw_target(self, target: str) -> str:
        target = target.strip()
        if sys.platform == "win32":
            if os.path.isfile(target) or target.startswith("\\\\.\\"):
                return target
            drive, _ = os.path.splitdrive(target)
            drive_letter = drive.rstrip(":").strip("\\").strip("/")
            if drive_letter and len(drive_letter) == 1 and drive_letter.isalpha():
                return f"\\\\.\\{drive_letter.upper()}:"
        return target

    def scan(
        self, 
        recursive: bool = True, 
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Dict[str, Any]]:
        carved_artifacts = []
        if not self.raw_path:
            raise ValueError("Invalid target drive letter or path.")

        try:
            with open(self.raw_path, "rb", buffering=0) as raw_disk:
                try:
                    raw_disk.seek(0, os.SEEK_END)
                    total_bytes = raw_disk.tell()
                    raw_disk.seek(0)
                except (OSError, OverflowError):
                    total_bytes = 10 * 1024 * 1024 * 1024

                chunk_size = 2 * 1024 * 1024
                bytes_processed = 0

                while True:
                    buffer = raw_disk.read(chunk_size)
                    if not buffer:
                        break

                    for ftype, sigs in FILE_SIGNATURES.items():
                        header = sigs["header"]
                        offset = 0

                        while True:
                            pos = buffer.find(header, offset)
                            if pos == -1:
                                break

                            abs_sector_offset = bytes_processed + pos
                            sha_hash = hashlib.sha256(buffer[pos:pos + 512]).hexdigest()[:8]
                            estimated_size = sigs.get("max_size", 5 * 1024 * 1024)
                            category = sigs.get("category", "Unclassified")

                            filename = f"Deleted_{ftype.upper()}_{abs_sector_offset:08X}_{sha_hash}.{ftype}"
                            rel_path = f"Unallocated_Sectors/{category}/{ftype.upper()}/{filename}"

                            carved_artifacts.append({
                                "source_file": self.raw_path,
                                "original_name": filename,
                                "relative_path": rel_path,
                                "type": ftype,
                                "offset": abs_sector_offset,
                                "size_bytes": estimated_size,
                                "timestamp": 0.0,
                                "date_str": "Unallocated (Sector Carved)",
                                "sha256": sha_hash,
                                "status": "Deleted (Carved from Sector)"
                            })

                            offset = pos + len(header)

                    bytes_processed += len(buffer)
                    if progress_callback and total_bytes > 0:
                        progress_callback(min(100.0, (bytes_processed / total_bytes) * 100.0))

        except PermissionError:
            raise PermissionError(
                f"Access Denied on '{self.raw_path}'.\nReopen Terminal / VS Code using 'Run as Administrator'."
            )
        except Exception:
            if os.path.isfile(self.raw_path):
                return self._scan_disk_image_file(self.raw_path, progress_callback)

        return carved_artifacts

    def _scan_disk_image_file(self, image_path: str, progress_callback) -> List[Dict[str, Any]]:
        carved_artifacts = []
        file_size = os.path.getsize(image_path)
        chunk_size = 2 * 1024 * 1024

        bytes_processed = 0
        with open(image_path, "rb") as f:
            while bytes_processed < file_size:
                buffer = f.read(chunk_size)
                if not buffer:
                    break

                for ftype, sigs in FILE_SIGNATURES.items():
                    header = sigs["header"]
                    pos = buffer.find(header)
                    if pos != -1:
                        abs_offset = bytes_processed + pos
                        sha_hash = hashlib.sha256(buffer[pos:pos + 512]).hexdigest()[:8]
                        category = sigs.get("category", "Unclassified")

                        mtime = os.path.getmtime(image_path)
                        date_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

                        filename = f"Deleted_{ftype.upper()}_{abs_offset:08X}_{sha_hash}.{ftype}"
                        rel_path = f"Disk_Image/{category}/{ftype.upper()}/{filename}"

                        carved_artifacts.append({
                            "source_file": image_path,
                            "original_name": filename,
                            "relative_path": rel_path,
                            "type": ftype,
                            "offset": abs_offset,
                            "size_bytes": sigs.get("max_size", 1024 * 1024),
                            "timestamp": mtime,
                            "date_str": date_str,
                            "sha256": sha_hash,
                            "status": "Deleted (Carved from Image)"
                        })

                bytes_processed += len(buffer)
                if progress_callback and file_size > 0:
                    progress_callback(min(100.0, (bytes_processed / file_size) * 100.0))

        return carved_artifacts