import os
import sys
import mmap
import ctypes
import logging
from typing import Generator, Optional, Tuple

logger = logging.getLogger("ProjectX.Core.DiskIO")
SECTOR_SIZE = 512

def is_admin_or_root() -> bool:
    """Check if current process has root (Linux) or Administrator (Windows) privileges."""
    if sys.platform == "win32":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    else:
        return os.geteuid() == 0

def is_system_partition(device_path: str) -> bool:
    """Check if device path corresponds to a primary system OS partition."""
    norm_path = device_path.strip().lower()
    if sys.platform == "win32":
        system_drive = os.environ.get("SystemDrive", "C:").lower()
        return system_drive in norm_path or r"\\.\c:" in norm_path
    else:
        if norm_path in ["/dev/sda1", "/dev/nvme0n1p2", "/dev/root"]:
            return True
        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "/" and parts[0] == norm_path:
                        return True
        except Exception:
            pass
    return False

class DiskIO:
    """Provides raw sector read/write access to block devices and raw disk images."""

    def __init__(self, device_path: str, sector_size: int = SECTOR_SIZE, read_only: bool = False):
        self.device_path = device_path
        self.sector_size = sector_size
        self.read_only = read_only
        self.handle = None
        self.mmap_obj: Optional[mmap.mmap] = None
        self._is_win32 = sys.platform == "win32"
        self.is_system = is_system_partition(device_path)
        self.has_admin = is_admin_or_root()

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
                logger.info(f"Opened Win32 handle: {self.device_path}")
            except Exception as e:
                logger.error(f"Failed to open Win32 handle for {self.device_path}: {e}")
                raise
        else:
            mode = "rb" if self.read_only else "rb+"
            try:
                self.handle = open(self.device_path, mode, buffering=0)
                logger.info(f"Opened POSIX handle: {self.device_path}")
            except Exception as e:
                logger.error(f"Failed to open handle for {self.device_path}: {e}")
                raise

        if os.path.isfile(self.device_path):
            try:
                access = mmap.ACCESS_READ if self.read_only else mmap.ACCESS_WRITE
                fd = self.handle.fileno() if hasattr(self.handle, "fileno") else -1
                if fd != -1:
                    self.mmap_obj = mmap.mmap(fd, 0, access=access)
                    logger.info(f"Memory mapping created for {self.device_path}")
            except Exception as e:
                logger.debug(f"mmap fallback to file I/O for {self.device_path}: {e}")
                self.mmap_obj = None

    def close(self):
        """Close device handle and mmap object."""
        if self.mmap_obj:
            try:
                self.mmap_obj.flush()
                self.mmap_obj.close()
            except Exception:
                pass
            self.mmap_obj = None

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
        """Return total capacity in bytes with physical disk fallbacks."""
        if self.mmap_obj:
            return self.mmap_obj.size()

        if os.path.isfile(self.device_path):
            return os.path.getsize(self.device_path)

        if self._is_win32:
            import win32file
            try:
                # Query physical drive size via IOCTL
                import win32ioctl
                import struct
                # IOCTL_DISK_GET_DRIVE_GEOMETRY_EX
                buf = win32file.DeviceIoControl(self.handle, 0x000700A0, None, 32)
                disk_size = struct.unpack("<q", buf[:8])[0]
                return disk_size
            except Exception:
                pos = win32file.SetFilePointer(self.handle, 0, win32file.FILE_END)
                win32file.SetFilePointer(self.handle, 0, win32file.FILE_BEGIN)
                return pos
        else:
            try:
                import fcntl, struct
                # BLKGETSIZE64 ioctl for Linux physical block devices
                buf = fcntl.ioctl(self.handle.fileno(), 0x80081272, struct.pack('L', 0))
                return struct.unpack('L', buf)[0]
            except Exception:
                self.handle.seek(0, os.SEEK_END)
                size = self.handle.tell()
                self.handle.seek(0, os.SEEK_SET)
                return size

    def read_sector(self, sector_num: int, num_sectors: int = 1) -> bytes:
        """Read sectors starting at sector_num."""
        offset = sector_num * self.sector_size
        bytes_to_read = num_sectors * self.sector_size

        if self.mmap_obj:
            if offset >= len(self.mmap_obj):
                return b""
            return self.mmap_obj[offset : offset + bytes_to_read]

        if self._is_win32:
            import win32file
            win32file.SetFilePointer(self.handle, offset, win32file.FILE_BEGIN)
            _, data = win32file.ReadFile(self.handle, bytes_to_read)
            return data
        else:
            self.handle.seek(offset)
            return self.handle.read(bytes_to_read)

    def write_sector(self, sector_num: int, data: bytes) -> int:
        """Write binary data to sector_num and flush buffers immediately."""
        if self.read_only:
            raise PermissionError("Attempted write on read-only DiskIO handle.")

        offset = sector_num * self.sector_size

        if self.mmap_obj:
            self.mmap_obj[offset : offset + len(data)] = data
            self.mmap_obj.flush()  # Force RAM write to disk hardware
            return len(data)

        if self._is_win32:
            import win32file
            win32file.SetFilePointer(self.handle, offset, win32file.FILE_BEGIN)
            _, written = win32file.WriteFile(self.handle, data)
            win32file.FlushFileBuffers(self.handle)
            return written
        else:
            self.handle.seek(offset)
            written = self.handle.write(data)
            self.handle.flush()
            os.fsync(self.handle.fileno())
            return written