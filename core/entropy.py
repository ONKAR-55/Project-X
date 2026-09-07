"""
Shannon entropy calculation module for analyzing data randomness across disk sectors and block ranges.
"""

import math
from typing import Dict, List

def calculate_entropy(data: bytes) -> float:
    """
    Calculate Shannon entropy of a byte sequence.
    Returns float value between 0.0 (completely uniform) and 8.0 (maximum entropy / random).
    """
    if not data:
        return 0.0

    length = len(data)
    frequency: Dict[int, int] = {}
    for byte in data:
        frequency[byte] = frequency.get(byte, 0) + 1

    entropy = 0.0
    for count in frequency.values():
        p = count / length
        entropy -= p * math.log2(p)

    return entropy

def calculate_sector_entropy_map(data: bytes, sector_size: int = 512) -> List[float]:
    """Calculate Shannon entropy for each sector within a block of data."""
    entropy_map = []
    num_sectors = len(data) // sector_size
    for i in range(num_sectors):
        sector_data = data[i * sector_size : (i + 1) * sector_size]
        entropy_map.append(calculate_entropy(sector_data))
    return entropy_map

def calculate_file_entropy(file_path: str, chunk_size: int = 65536) -> float:
    """Calculate overall Shannon entropy of an entire file or disk image."""
    frequency: Dict[int, int] = {}
    total_bytes = 0

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            total_bytes += len(chunk)
            for byte in chunk:
                frequency[byte] = frequency.get(byte, 0) + 1

    if total_bytes == 0:
        return 0.0

    entropy = 0.0
    for count in frequency.values():
        p = count / total_bytes
        entropy -= p * math.log2(p)

    return entropy
