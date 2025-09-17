"""
Universal Congressional District Mapper Framework

A flexible framework for creating interactive maps of any US Congressional District
with customizable data overlays.
"""

__version__ = "1.0.0"
__author__ = "Congressional District Mapper"

from .boundaries import DistrictBoundaryProcessor
from .overlays import OverlayManager
from .geocoding import AddressGeocoder
from .generator import MapGenerator

__all__ = [
    "DistrictBoundaryProcessor",
    "OverlayManager",
    "AddressGeocoder",
    "MapGenerator"
]