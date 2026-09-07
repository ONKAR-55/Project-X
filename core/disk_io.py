"""
DiskIO: Raw sector access handles for block devices, disk images, and files.
Handles cross-platform raw I/O for Windows (win32 API) and Linux block devices/images.
"""

import os
import sys
import logging

logger = logging.getLogger("ProjectX.Core.DiskIO")

SECTOR_SIZE = 512

class DiskIO:
    """Provides raw sector read/write access to block devices and raw disk images."""

    def __init__(self, device_path: str, sector_size: int = SECTOR_SIZE, read_only: bool = False):
        self.device_path = device_path
        self.sector_size = sector_size
        self.read_only = read_only
        self.handle = None
        self._is_win32 = sys.platform == "win32"

    def open(self):
        """Open raw device/file handle."""
        if self._is_win32:
            import win32file
            import win32con
            access = win32con.GENERIC_READ if self.read_only else (win32con.GENERIC_READ | win32con.GENERIC_WRITE)
            share_mode = win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE
            creation = win32con.OPEN_EXISTING
            flags = win32con.FILE_ATTRIBUTE_NORMAL
            
            try:
                self.handle = win32file.CreateFile(
                    self.device_path, access, share_mode, None, creation, flags, None
                )
                logger.info(f"Opened Win32 physical handle: {self.device_path}")
            except Exception as e:
                logger.error(f"Failed to open Win32 handle for {self.device_path}: {e}")
                raise
        else:
            mode = "rb" if self.read_only else "rb+"
            try:
                self.handle = open(self.device_path, mode, buffering=0)
                logger.info(f"Opened POSIX unbuffered handle: {self.device_path}")
            except Exception as e:
                logger.error(f"Failed to open handle for {self.device_path}: {e}")
                raise

    def close(self):
        """Close the device handle."""
        if self.handle:
            if self._is_win32:
                import win32file
                win32file.CloseHandle(self.handle)
            else:
                self.handle.close()
            self.handle = None
            logger.info(f"Closed handle: {self.device_path}")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_size(self) -> int:
        """Return total size of the block device or image file in bytes."""
        if self._is_win32:
            import win32file
            # Standard seek to end to obtain byte size for image files / physical drives
            pos = win32file.SetFilePointer(self.handle, 0, win32file.FILE_END)
            win32file.SetFilePointer(self.handle, 0, win32file.FILE_BEGIN)
            return pos
        else:
            self.handle.seek(0, os.SEEK_END)
            size = self.handle.tell()
            self.handle.seek(0, os.SEEK_SET)
            return size

    def read_sector(self, sector_num: int, num_sectors: int = 1) -> bytes:
        """Read one or more sectors starting at sector_num."""
        offset = sector_num * self.sector_size
        bytes_to_read = num_sectors * self.sector_size

        if self._is_win32:
            import win32file
            win32file.SetFilePointer(self.handle, offset, win32file.FILE_BEGIN)
            hr, data = win32file.ReadFile(self.handle, bytes_to_read)
            return data
        else:
            self.handle.seek(offset)
            return self.handle.read(bytes_to_read)

    def write_sector(self, sector_num: int, data: bytes) -> int:
        """Write binary data to sector_num. Data length should match sector_size standard."""
        if self.read_only:
            raise PermissionError("Attempted to write to read-only DiskIO handle.")

        offset = sector_num * self.sector_size

        if self._is_win32:
            import win32file
            win32file.SetFilePointer(self.handle, offset, win32file.FILE_BEGIN)
            hr, written = win32file.WriteFile(self.handle, data)
            return written
        else:
            self.handle.seek(offset)
            written = self.handle.write(data)
            self.handle.flush()
            return written
