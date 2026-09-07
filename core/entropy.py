import math
from typing import Dict, List

def calculate_entropy(data: bytes) -> float:
    """Calculate Shannon entropy using native C byte counting."""
    if not data:
        return 0.0

    length = len(data)
    entropy = 0.0
    
    # 256 C-level passes instead of len(data) Python loops
    for byte_val in range(256):
        count = data.count(byte_val)
        if count > 0:
            p = count / length
            entropy -= p * math.log2(p)

    return entropy

def calculate_sector_entropy_map(data: bytes, sector_size: int = 512) -> List[float]:
    """Calculate Shannon entropy for each sector within a block of data."""
    num_sectors = len(data) // sector_size
    return [
        calculate_entropy(data[i * sector_size : (i + 1) * sector_size])
        for i in range(num_sectors)
    ]

def classify_entropy(entropy: float) -> str:
    """Classify entropy into standard data categories."""
    if entropy < 1.0:
        return "Low (Zeroed/Text)"
    elif 1.0 <= entropy <= 6.8:
        return "Medium (Uncompressed Binary)"
    elif entropy > 7.2:
        return "High (Compressed/Encrypted)"
    else:
        return "Medium-High (Structured Binary)"

def calculate_file_entropy(file_path: str, chunk_size: int = 65536) -> float:
    """Stream file in chunks and calculate global entropy via byte frequency array."""
    counts = [0] * 256
    total_bytes = 0

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            total_bytes += len(chunk)
            for byte_val in range(256):
                counts[byte_val] += chunk.count(byte_val)

    if total_bytes == 0:
        return 0.0

    entropy = 0.0
    for count in counts:
        if count > 0:
            p = count / total_bytes
            entropy -= p * math.log2(p)

    return entropy