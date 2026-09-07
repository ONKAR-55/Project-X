"""
SectorScanner: Physical sector header/footer scanner for file carving.
Scans disk images or block devices for magic byte signatures.
"""

import logging
from typing import List, Dict, Any
from core.disk_io import DiskIO, SECTOR_SIZE
from phase2_carver.parsers.jpeg_parser import JPEGParser
from phase2_carver.parsers.png_parser import PNGParser
from phase2_carver.parsers.pdf_parser import PDFParser
from phase2_carver.parsers.zip_parser import ZIPParser
from phase2_carver.validator import CarveValidator

logger = logging.getLogger("ProjectX.Phase2.SectorScanner")

# Standard file format magic signatures
SIGNATURES = {
    "JPEG": b"\xFF\xD8\xFF",
    "PNG": b"\x89PNG\r\n\x1A\n",
    "PDF": b"%PDF-",
    "ZIP": b"PK\x03\x04"
}

class SectorScanner:
    """Scans physical sector boundaries for file headers and invokes format parsers to extract candidates."""

    def __init__(self, target_path: str, sector_size: int = SECTOR_SIZE):
        self.target_path = target_path
        self.sector_size = sector_size
        self.parsers = {
            "JPEG": JPEGParser(),
            "PNG": PNGParser(),
            "PDF": PDFParser(),
            "ZIP": ZIPParser()
        }
        self.validator = CarveValidator()

    def scan(self) -> List[Dict[str, Any]]:
        """
        Scan target image/device sector by sector for candidate files.
        Returns list of dictionary descriptors of carved files.
        """
        logger.info(f"Initiating sector signature scan on {self.target_path}...")
        results = []

        with DiskIO(self.target_path, read_only=True) as disk:
            total_size = disk.get_size()
            total_sectors = total_size // self.sector_size

            for sector_num in range(total_sectors):
                sector_data = disk.read_sector(sector_num, num_sectors=1)

                for ftype, sig in SIGNATURES.items():
                    if sector_data.startswith(sig):
                        logger.info(f"Header signature for {ftype} detected at sector {sector_num}")
                        # Read candidate data stream (up to 10MB max candidate buffer)
                        max_bytes = min(10 * 1024 * 1024, total_size - (sector_num * self.sector_size))
                        max_sectors = (max_bytes + self.sector_size - 1) // self.sector_size
                        candidate_stream = disk.read_sector(sector_num, num_sectors=max_sectors)

                        parser = self.parsers[ftype]
                        parse_res = parser.parse(candidate_stream)

                        if parse_res["valid"]:
                            carved_bytes = candidate_stream[:parse_res["length"]]
                            confidence = self.validator.calculate_confidence(ftype, carved_bytes, parse_res)
                            
                            res_entry = {
                                "type": ftype,
                                "sector": sector_num,
                                "offset": sector_num * self.sector_size,
                                "size_bytes": parse_res["length"],
                                "confidence_score": confidence,
                                "metadata": parse_res.get("metadata", {}),
                                "data": carved_bytes
                            }
                            results.append(res_entry)
                            logger.info(f"Successfully carved candidate {ftype} ({parse_res['length']} bytes, confidence: {confidence}%)")

        return results
