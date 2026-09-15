"""
SectorScanner: Cross-platform raw volume carver supporting Windows drive letters 
and macOS/Linux BSD device nodes (/dev/rdiskX) with directory fallbacks.
"""

import os
import sys
import hashlib
import datetime
import subprocess
from typing import List, Dict, Any, Callable, Optional


class SectorScanner:
    """Carves raw storage volumes and accurately measures file boundaries on Windows and macOS."""

    def __init__(self, target_input: str):
        self.original_target = target_input.strip()
        self.raw_path = self._format_raw_target(self.original_target)

    def _format_raw_target(self, target: str) -> str:
        target = target.strip()
        
        # Windows formatting
        if sys.platform == "win32":
            if os.path.isfile(target) or target.startswith("\\\\.\\"):
                return target
            drive, _ = os.path.splitdrive(target)
            drive_letter = drive.rstrip(":").strip("\\").strip("/")
            if drive_letter and len(drive_letter) == 1 and drive_letter.isalpha():
                return f"\\\\.\\{drive_letter.upper()}:"
            return target

        # macOS / Linux formatting
        if sys.platform == "darwin" or sys.platform.startswith("linux"):
            if target.startswith("/dev/"):
                if target.startswith("/dev/disk"):
                    return target.replace("/dev/disk", "/dev/rdisk")
                return target

            # Resolve mounted volume path (e.g. /Volumes/USB) to raw device node (/dev/rdiskX)
            if os.path.exists(target):
                try:
                    res = subprocess.run(["df", "-P", target], capture_output=True, text=True)
                    lines = res.stdout.strip().split("\n")
                    if len(lines) >= 2:
                        dev_node = lines[1].split()[0]
                        if dev_node.startswith("/dev/disk"):
                            return dev_node.replace("/dev/disk", "/dev/rdisk")
                        elif dev_node.startswith("/dev/"):
                            return dev_node
                except Exception:
                    pass

        return target

    def _calculate_exact_length(self, data: bytes, start_pos: int, ftype: str) -> int:
        total_len = len(data)

        if ftype == "png":
            iend = data.find(b"\x49\x45\x4e\x44\xae\x42\x60\x82", start_pos)
            if iend != -1:
                return (iend + 8) - start_pos

        elif ftype == "jpeg":
            eoi = data.find(b"\xff\xd9", start_pos)
            if eoi != -1:
                return (eoi + 2) - start_pos

        elif ftype in ("zip", "docx"):
            eocd = data.find(b"PK\x05\x06", start_pos)
            if eocd != -1 and eocd + 22 <= total_len:
                comment_len = int.from_bytes(data[eocd + 20 : eocd + 22], "little")
                return (eocd + 22 + comment_len) - start_pos

        elif ftype == "mp4":
            offset = start_pos
            while offset + 8 <= total_len:
                box_size = int.from_bytes(data[offset : offset + 4], "big")
                box_type = data[offset + 4 : offset + 8]

                if not all(32 <= b <= 126 for b in box_type):
                    break

                if box_size == 1:
                    if offset + 16 > total_len:
                        break
                    box_size = int.from_bytes(data[offset + 8 : offset + 16], "big")
                elif box_size == 0:
                    offset = total_len
                    break

                if box_size < 8 or (offset + box_size) > total_len:
                    break

                offset += box_size
                if offset - start_pos > 1024 * 1024 * 1024:
                    break

            parsed_len = offset - start_pos
            if parsed_len > 16:
                return parsed_len

        elif ftype == "pdf":
            eof = data.find(b"%%EOF", start_pos)
            if eof != -1:
                return (eof + 5) - start_pos

        return 5 * 1024 * 1024

    def scan(
        self, 
        recursive: bool = True, 
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Dict[str, Any]]:
        if not self.raw_path:
            raise ValueError("Invalid target drive letter or path.")

        # If target path is a standard directory and not mapped to raw block device, walk directory
        if os.path.isdir(self.raw_path) and not self.raw_path.startswith("/dev/"):
            return self._scan_directory_tree(self.raw_path, progress_callback)

        carved_artifacts = []
        signatures = {
            "png": {"header": b"\x89PNG\r\n\x1a\n", "category": "Images"},
            "jpeg": {"header": b"\xff\xd8\xff", "category": "Images"},
            "docx": {"header": b"PK\x03\x04", "category": "Documents"},
            "zip": {"header": b"PK\x03\x04", "category": "Archives"},
            "pdf": {"header": b"%PDF-", "category": "Documents"},
            "mp4": {"header": b"\x00\x00\x00\x20ftyp", "category": "Videos"},
        }

        try:
            with open(self.raw_path, "rb", buffering=0) as raw_disk:
                try:
                    raw_disk.seek(0, os.SEEK_END)
                    total_bytes = raw_disk.tell()
                    raw_disk.seek(0)
                except (OSError, OverflowError):
                    total_bytes = 10 * 1024 * 1024 * 1024

                chunk_size = 8 * 1024 * 1024
                bytes_processed = 0

                while True:
                    buffer = raw_disk.read(chunk_size)
                    if not buffer:
                        break

                    for ftype, sigs in signatures.items():
                        header = sigs["header"]
                        offset = 0

                        while True:
                            pos = buffer.find(header, offset)
                            if pos == -1:
                                break

                            abs_offset = bytes_processed + pos
                            exact_size = self._calculate_exact_length(buffer, pos, ftype)
                            sha_hash = hashlib.sha256(buffer[pos : pos + min(512, len(buffer) - pos)]).hexdigest()[:8]
                            category = sigs["category"]

                            filename = f"Recovered_{ftype.upper()}_{abs_offset:08X}_{sha_hash}.{ftype}"
                            rel_path = f"Unallocated_Sectors/{category}/{ftype.upper()}/{filename}"

                            carved_artifacts.append({
                                "source_file": self.raw_path,
                                "original_name": filename,
                                "relative_path": rel_path,
                                "type": ftype,
                                "offset": abs_offset,
                                "size_bytes": exact_size,
                                "timestamp": 0.0,
                                "date_str": "Unallocated Sector",
                                "sha256": sha_hash,
                                "status": "Ready for Extraction"
                            })

                            offset = pos + max(len(header), exact_size)

                    bytes_processed += len(buffer)
                    if progress_callback and total_bytes > 0:
                        progress_callback(min(100.0, (bytes_processed / total_bytes) * 100.0))

        except (PermissionError, IsADirectoryError):
            if os.path.isdir(self.original_target):
                return self._scan_directory_tree(self.original_target, progress_callback)
            raise PermissionError(
                f"Access Denied on '{self.raw_path}'.\nRun terminal with root privileges (sudo python main.py) and grant Full Disk Access."
            )
        except Exception:
            if os.path.isfile(self.raw_path):
                return self._scan_disk_image_file(self.raw_path, progress_callback)
            elif os.path.isdir(self.original_target):
                return self._scan_directory_tree(self.original_target, progress_callback)

        return carved_artifacts

    def _scan_directory_tree(self, dir_path: str, progress_callback) -> List[Dict[str, Any]]:
        """Scans standard file system trees when direct sector access is unavailable."""
        artifacts = []
        all_files = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                all_files.append(os.path.join(root, file))

        total = len(all_files)
        for idx, file_path in enumerate(all_files):
            try:
                size = os.path.getsize(file_path)
                ext = file_path.split(".")[-1].lower() if "." in file_path else "bin"
                rel_path = os.path.relpath(file_path, dir_path)
                mtime = os.path.getmtime(file_path)
                date_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

                artifacts.append({
                    "source_file": file_path,
                    "original_name": os.path.basename(file_path),
                    "relative_path": rel_path,
                    "type": ext,
                    "offset": 0,
                    "size_bytes": size,
                    "timestamp": mtime,
                    "date_str": date_str,
                    "sha256": "FS_ENTRY",
                    "status": "Ready for Extraction"
                })
            except Exception:
                continue

            if progress_callback and total > 0:
                progress_callback(min(100.0, ((idx + 1) / total) * 100.0))

        return artifacts

    def _scan_disk_image_file(self, image_path: str, progress_callback) -> List[Dict[str, Any]]:
        carved_artifacts = []
        file_size = os.path.getsize(image_path)
        chunk_size = 8 * 1024 * 1024

        signatures = {
            "png": {"header": b"\x89PNG\r\n\x1a\n", "category": "Images"},
            "jpeg": {"header": b"\xff\xd8\xff", "category": "Images"},
            "docx": {"header": b"PK\x03\x04", "category": "Documents"},
            "zip": {"header": b"PK\x03\x04", "category": "Archives"},
            "pdf": {"header": b"%PDF-", "category": "Documents"},
            "mp4": {"header": b"\x00\x00\x00\x20ftyp", "category": "Videos"},
        }

        bytes_processed = 0
        with open(image_path, "rb") as f:
            while bytes_processed < file_size:
                buffer = f.read(chunk_size)
                if not buffer:
                    break

                for ftype, sigs in signatures.items():
                    header = sigs["header"]
                    pos = buffer.find(header)
                    if pos != -1:
                        abs_offset = bytes_processed + pos
                        exact_size = self._calculate_exact_length(buffer, pos, ftype)
                        sha_hash = hashlib.sha256(buffer[pos : pos + min(512, len(buffer) - pos)]).hexdigest()[:8]
                        category = sigs["category"]

                        mtime = os.path.getmtime(image_path)
                        date_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

                        filename = f"Recovered_{ftype.upper()}_{abs_offset:08X}_{sha_hash}.{ftype}"
                        rel_path = f"Disk_Image/{category}/{ftype.upper()}/{filename}"

                        carved_artifacts.append({
                            "source_file": image_path,
                            "original_name": filename,
                            "relative_path": rel_path,
                            "type": ftype,
                            "offset": abs_offset,
                            "size_bytes": exact_size,
                            "timestamp": mtime,
                            "date_str": date_str,
                            "sha256": sha_hash,
                            "status": "Ready for Extraction"
                        })

                bytes_processed += len(buffer)
                if progress_callback and file_size > 0:
                    progress_callback(min(100.0, (bytes_processed / file_size) * 100.0))

        return carved_artifacts