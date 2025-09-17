"""
District Boundary Processing

Handles precise congressional district boundaries including partial counties.
Converts TIGER shapefiles to GeoJSON and provides boundary validation.
"""

import geopandas as gpd
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from shapely.geometry import Point, Polygon
import logging

logger = logging.getLogger(__name__)


class DistrictBoundaryProcessor:
    """
    Processes congressional district boundaries for precise mapping.

    Handles:
    - TIGER shapefile conversion to GeoJSON
    - Partial county boundary extraction
    - Point-in-polygon validation for addresses
    - Boundary simplification for web mapping
    """

    def __init__(self, district_path: str):
        """
        Initialize boundary processor for a specific district.

        Args:
            district_path: Path to district directory containing boundary files
        """
        self.district_path = Path(district_path)
        self.boundaries_path = self.district_path / "boundaries"
        self.boundaries_path.mkdir(exist_ok=True)

        # Cache for loaded boundaries
        self._district_boundary = None
        self._counties_boundary = None
        self._partial_counties = None

    def process_tiger_shapefile(self, shapefile_path: str, district_id: str = None) -> Dict[str, str]:
        """
        Convert TIGER shapefile to GeoJSON files.

        Args:
            shapefile_path: Path to TIGER congressional district shapefile
            district_id: Optional district ID to filter (e.g., "2106" for KY-6)

        Returns:
            Dictionary of created GeoJSON file paths
        """
        try:
            logger.info(f"Processing TIGER shapefile: {shapefile_path}")

            # Read the shapefile
            gdf = gpd.read_file(shapefile_path)

            # Filter to specific district if provided
            if district_id:
                gdf = gdf[gdf['CD118FP'] == district_id]  # 118th Congress districts
                if len(gdf) == 0:
                    raise ValueError(f"District ID {district_id} not found in shapefile")

            # Ensure we're in WGS84 (EPSG:4326) for web mapping
            if gdf.crs != 'EPSG:4326':
                gdf = gdf.to_crs('EPSG:4326')

            # Simplify geometries for web performance (tolerance in degrees)
            gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.001)

            created_files = {}

            # Save district boundary
            district_file = self.boundaries_path / "district.geojson"
            gdf.to_file(district_file, driver='GeoJSON')
            created_files['district'] = str(district_file)

            logger.info(f"Created district boundary: {district_file}")

            return created_files

        except Exception as e:
            logger.error(f"Error processing TIGER shapefile: {e}")
            raise

    def load_county_boundaries(self, counties_shapefile: str, state_fips: str = None) -> str:
        """
        Load and save county boundaries for reference.

        Args:
            counties_shapefile: Path to TIGER county shapefile
            state_fips: Optional state FIPS code to filter (e.g., "21" for Kentucky)

        Returns:
            Path to created counties GeoJSON file
        """
        try:
            logger.info(f"Processing county boundaries: {counties_shapefile}")

            # Read county shapefile
            counties_gdf = gpd.read_file(counties_shapefile)

            # Filter to specific state if provided
            if state_fips:
                counties_gdf = counties_gdf[counties_gdf['STATEFP'] == state_fips]

            # Ensure WGS84
            if counties_gdf.crs != 'EPSG:4326':
                counties_gdf = counties_gdf.to_crs('EPSG:4326')

            # Simplify for web performance
            counties_gdf['geometry'] = counties_gdf['geometry'].simplify(tolerance=0.001)

            # Save counties
            counties_file = self.boundaries_path / "counties.geojson"
            counties_gdf.to_file(counties_file, driver='GeoJSON')

            logger.info(f"Created counties boundary: {counties_file}")

            return str(counties_file)

        except Exception as e:
            logger.error(f"Error processing county boundaries: {e}")
            raise

    def extract_partial_counties(self) -> str:
        """
        Extract partial county segments that intersect with district boundary.

        Returns:
            Path to created partial counties GeoJSON file
        """
        try:
            district_gdf = self.load_district_boundary()
            counties_gdf = self.load_counties_boundary()

            if district_gdf is None or counties_gdf is None:
                raise ValueError("District and county boundaries must be loaded first")

            # Find counties that intersect with district
            intersecting = counties_gdf[counties_gdf.intersects(district_gdf.unary_union)]

            # Calculate intersection areas
            partial_counties = []
            for idx, county in intersecting.iterrows():
                intersection = county.geometry.intersection(district_gdf.unary_union)
                if intersection.area > 0:
                    partial_counties.append({
                        'county_name': county.get('NAME', 'Unknown'),
                        'county_fips': county.get('GEOID', 'Unknown'),
                        'geometry': intersection,
                        'full_area': county.geometry.area,
                        'district_area': intersection.area,
                        'coverage_pct': round((intersection.area / county.geometry.area) * 100, 2)
                    })

            # Create GeoDataFrame for partial counties
            partial_gdf = gpd.GeoDataFrame(partial_counties, crs='EPSG:4326')

            # Save partial counties
            partial_file = self.boundaries_path / "partial-counties.geojson"
            partial_gdf.to_file(partial_file, driver='GeoJSON')

            logger.info(f"Created partial counties: {partial_file}")
            logger.info(f"Found {len(partial_counties)} counties intersecting district")

            return str(partial_file)

        except Exception as e:
            logger.error(f"Error extracting partial counties: {e}")
            raise

    def load_district_boundary(self) -> Optional[gpd.GeoDataFrame]:
        """Load district boundary GeoDataFrame."""
        if self._district_boundary is None:
            district_file = self.boundaries_path / "district.geojson"
            if district_file.exists():
                self._district_boundary = gpd.read_file(district_file)
        return self._district_boundary

    def load_counties_boundary(self) -> Optional[gpd.GeoDataFrame]:
        """Load counties boundary GeoDataFrame."""
        if self._counties_boundary is None:
            counties_file = self.boundaries_path / "counties.geojson"
            if counties_file.exists():
                self._counties_boundary = gpd.read_file(counties_file)
        return self._counties_boundary

    def point_in_district(self, lat: float, lng: float) -> bool:
        """
        Check if a point (lat, lng) falls within the district boundary.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            True if point is within district boundary
        """
        try:
            district_gdf = self.load_district_boundary()
            if district_gdf is None:
                raise ValueError("District boundary not loaded")

            point = Point(lng, lat)  # Note: Point takes (x, y) = (lng, lat)
            return district_gdf.contains(point).any()

        except Exception as e:
            logger.error(f"Error checking point in district: {e}")
            return False

    def get_district_bounds(self) -> Optional[Dict[str, float]]:
        """
        Get bounding box for the district.

        Returns:
            Dictionary with min_lat, max_lat, min_lng, max_lng
        """
        try:
            district_gdf = self.load_district_boundary()
            if district_gdf is None:
                return None

            bounds = district_gdf.total_bounds  # [minx, miny, maxx, maxy]

            return {
                'min_lng': bounds[0],
                'min_lat': bounds[1],
                'max_lng': bounds[2],
                'max_lat': bounds[3]
            }

        except Exception as e:
            logger.error(f"Error getting district bounds: {e}")
            return None

    def get_district_center(self) -> Optional[Tuple[float, float]]:
        """
        Get center point of the district.

        Returns:
            Tuple of (lat, lng) for district center
        """
        try:
            bounds = self.get_district_bounds()
            if bounds is None:
                return None

            center_lat = (bounds['min_lat'] + bounds['max_lat']) / 2
            center_lng = (bounds['min_lng'] + bounds['max_lng']) / 2

            return (center_lat, center_lng)

        except Exception as e:
            logger.error(f"Error getting district center: {e}")
            return None

    def validate_boundaries(self) -> Dict[str, bool]:
        """
        Validate that all required boundary files exist and are valid.

        Returns:
            Dictionary of validation results
        """
        results = {}

        # Check district boundary
        district_file = self.boundaries_path / "district.geojson"
        results['district_exists'] = district_file.exists()

        if results['district_exists']:
            try:
                gdf = gpd.read_file(district_file)
                results['district_valid'] = len(gdf) > 0 and not gdf.geometry.isna().all()
            except:
                results['district_valid'] = False
        else:
            results['district_valid'] = False

        # Check counties boundary (optional)
        counties_file = self.boundaries_path / "counties.geojson"
        results['counties_exists'] = counties_file.exists()

        # Check partial counties (optional)
        partial_file = self.boundaries_path / "partial-counties.geojson"
        results['partial_counties_exists'] = partial_file.exists()

        return results