"""
TraceFinder Module: Scans system locations (Temp, Recent, Prefetch, Logs) 
for residual traces or duplicate copies matching a target filename.
"""

import os
import glob
from typing import List, Dict, Any


class TraceFinder:
    """Discovers system artifacts, shortcuts, and temporary copies related to a target file."""

    def __init__(self, target_filepath: str):
        self.target_path = os.path.abspath(target_filepath)
        self.filename = os.path.basename(self.target_path)
        self.file_stem, self.file_ext = os.path.splitext(self.filename)

    def locate_all_traces(self) -> Dict[str, List[Dict[str, Any]]]:
        """Scans standard system locations for traces."""
        found_traces = []
        locked_or_system_traces = []

        search_directories = self._get_system_search_paths()

        for search_dir in search_directories:
            if not os.path.exists(search_dir):
                continue

            try:
                # Look for exact or fuzzy matches (e.g., shortcuts, temp files, prefetch)
                pattern = os.path.join(search_dir, f"*{self.file_stem}*")
                matches = glob.glob(pattern, recursive=False)

                for match in matches:
                    if os.path.abspath(match) == self.target_path:
                        continue  # Skip main target file here

                    try:
                        is_writable = os.access(match, os.W_OK)
                        trace_info = {
                            "path": match,
                            "type": self._classify_trace_type(match),
                            "size_bytes": os.path.getsize(match) if os.path.isfile(match) else 0,
                            "writable": is_writable
                        }

                        if is_writable:
                            found_traces.append(trace_info)
                        else:
                            locked_or_system_traces.append(trace_info)
                    except Exception as e:
                        locked_or_system_traces.append({
                            "path": match,
                            "type": "Protected Artifact",
                            "error": str(e),
                            "writable": False
                        })

            except Exception:
                pass

        return {
            "removable_traces": found_traces,
            "locked_traces": locked_or_system_traces
        }

    def _get_system_search_paths(self) -> List[str]:
        """Returns OS-specific trace locations."""
        paths = []
        if os.name == "nt":  # Windows
            appdata = os.getenv("APPDATA", "")
            localappdata = os.getenv("LOCALAPPDATA", "")
            windir = os.getenv("WINDIR", "C:\\Windows")
            temp = os.getenv("TEMP", "")

            paths.extend([
                temp,
                os.path.join(appdata, r"Microsoft\Windows\Recent"),
                os.path.join(localappdata, r"Microsoft\Windows\Explorer"),
                os.path.join(localappdata, "Temp"),
                os.path.join(windir, "Prefetch"),
                os.path.join(windir, "Temp")
            ])
        else:  # Linux / Unix
            paths.extend([
                "/tmp",
                "/var/tmp",
                os.path.expanduser("~/.local/share/Trash"),
                os.path.expanduser("~/.cache")
            ])
        return [p for p in paths if p]

    def _classify_trace_type(self, path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".lnk":
            return "Windows Shortcut (Recent Items)"
        elif ext == ".pf":
            return "Windows Prefetch Execution Artifact"
        elif "temp" in path.lower() or ext == ".tmp":
            return "Temporary Working File"
        return "System Artifact Copy"