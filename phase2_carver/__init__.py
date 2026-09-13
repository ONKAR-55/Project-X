"""
Phase 2 Carver: Forensic Recovery Engine.
Implements raw physical sector scanning, structure-aware file format chunk parsers (JPEG, PNG, PDF, ZIP), and confidence scoring.
"""

from phase2_carver.sector_scanner import SectorScanner

__all__ = ["SectorScanner"]
