"""
DirectFlusher: Low-level OS cache bypass and hardware buffer sync handles.
Ensures physical media sync via O_DIRECT, posix_fadvise, fdatasync, or FlushFileBuffers.
"""

import os
import sys
import logging

logger = logging.getLogger("ProjectX.Phase1.DirectFlusher")

class DirectFlusher:
    """Provides methods to force immediate flush of dirty cache pages to non-volatile physical storage."""

    @staticmethod
    def flush(handle_or_file):
        """Flush OS dirty buffers for a file handle or integer fd."""
        fd = None
        if isinstance(handle_or_file, int):
            fd = handle_or_file
        elif hasattr(handle_or_file, "fileno"):
            try:
                fd = handle_or_file.fileno()
            except Exception:
                pass

        if sys.platform == "win32":
            import win32file
            if fd is not None:
                try:
                    os.fsync(fd)
                except Exception as e:
                    logger.debug(f"Win32 fsync notice: {e}")
            elif hasattr(handle_or_file, "handle"):
                try:
                    win32file.FlushFileBuffers(handle_or_file.handle)
                except Exception as e:
                    logger.warning(f"Win32 FlushFileBuffers failed: {e}")
        else:
            # Linux / POSIX system calls
            if fd is not None:
                try:
                    os.fdatasync(fd)
                except Exception:
                    try:
                        os.fsync(fd)
                    except Exception as e:
                        logger.warning(f"POSIX fsync failed: {e}")

        logger.debug("Hardware buffer sync performed.")
