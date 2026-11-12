#!/usr/bin/env python3
"""
Extract EXACT congressional district and county boundaries
Maintains full precision for accurate representation
"""

import json
import subprocess
import sys
from pathlib import Path

class BoundaryExtractor:
    def __init__(self, state_fips="21", district_num="06"):
        """
        Initialize extractor for a specific district
        
        Args:
            state_fips: State FIPS code (21 for Kentucky)
            district_num: District number (06 for KY-06)
        """
        self.state_fips = state_fips
        self.district_num = district_num
        self.district_code = f"KY-{district_num}"
        
    def download_district_shapefile(self):
        """Download congressional district shapefile from Census"""
        print(f"Downloading congressional districts for state {self.state_fips}...")
        
        # Try multiple years in case one fails
        urls = [
            f"https://www2.census.gov/geo/tiger/TIGER2024/CD/tl_2024_{self.state_fips}_cd119.zip",
            f"https://www2.census.gov/geo/tiger/TIGER2023/CD/tl_2023_{self.state_fips}_cd118.zip",
        ]
        
        for url in urls:
            try:
                subprocess.run(["wget", "-q", "-O", "temp_cd.zip", url], check=True)
                subprocess.run(["unzip", "-q", "-o", "temp_cd.zip"], check=True)
                return True
            except:
                continue
        
        return False
    
    def extract_exact_district(self):
        """Extract district with FULL precision"""
        # Find the shapefile
        shapefiles = list(Path(".").glob("*.shp"))
        if not shapefiles:
            print("No shapefile found")
            return None
            
        shapefile = shapefiles[0]
        print(f"Processing {shapefile}")
        
        # Extract with FULL precision using ogr2ogr
        # Note: We do NOT simplify here
        cmd = [
            "ogr2ogr",
            "-f", "GeoJSON",
            "-t_srs", "EPSG:4326",
            "-where", f"CD119FP = '{self.district_num}' OR CD118FP = '{self.district_num}'",
            "-lco", "COORDINATE_PRECISION=7",  # Keep 7 decimal places
            "district_exact.geojson",
            str(shapefile)
        ]
        
        subprocess.run(cmd, check=True)
        
        # Read and verify
        with open("district_exact.geojson", "r") as f:
            data = json.load(f)
            
        if not data.get("features"):
            print(f"No district {self.district_num} found")
            return None
            
        print(f"✓ Extracted district {self.district_num}")
        
        # Check complexity
        feature = data["features"][0]
        geom = feature["geometry"]
        if geom["type"] == "Polygon":
            points = len(geom["coordinates"][0])
        else:
            points = sum(len(p[0]) for p in geom["coordinates"])
        
        print(f"  Exact boundary has {points:,} coordinate points")
        
        return data
    
    def download_county_shapefile(self):
        """Download county boundaries"""
        print(f"Downloading counties...")
        
        urls = [
            "https://www2.census.gov/geo/tiger/TIGER2024/COUNTY/tl_2024_us_county.zip",
            "https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_us_county.zip",
        ]
        
        for url in urls:
            try:
                subprocess.run(["wget", "-q", "-O", "temp_county.zip", url], check=True)
                subprocess.run(["unzip", "-q", "-o", "temp_county.zip"], check=True)
                return True
            except:
                continue
        
        return False
    
    def extract_exact_counties(self):
        """Extract counties that intersect with district"""
        # Extract all counties for the state first
        shapefiles = list(Path(".").glob("tl_*_county.shp"))
        if not shapefiles:
            print("No county shapefile found")
            return None
            
        shapefile = shapefiles[0]
        
        cmd = [
            "ogr2ogr",
            "-f", "GeoJSON",
            "-t_srs", "EPSG:4326",
            "-where", f"STATEFP = '{self.state_fips}'",
            "-lco", "COORDINATE_PRECISION=7",
            "counties_exact.geojson",
            str(shapefile)
        ]
        
        subprocess.run(cmd, check=True)
        
        with open("counties_exact.geojson", "r") as f:
            counties = json.load(f)
        
        print(f"✓ Extracted {len(counties['features'])} counties for state")
        
        # For KY-06, we know these counties are included
        # In a production system, we'd calculate intersection
        KY06_COUNTIES = [
            "Anderson", "Bourbon", "Clark", "Fayette",
            "Franklin", "Harrison", "Jessamine",
            "Nicholas", "Scott", "Woodford"
        ]
        
        district_counties = {
            "type": "FeatureCollection",
            "features": []
        }
        
        for feature in counties["features"]:
            name = feature["properties"].get("NAME", "")
            if name in KY06_COUNTIES:
                district_counties["features"].append(feature)
                print(f"  Including {name} County")
        
        return district_counties
    
    def create_simplified_versions(self, data, output_base):
        """Create simplified versions for faster loading"""
        # Save exact version
        exact_path = f"{output_base}_exact.geojson"
        with open(exact_path, "w") as f:
            json.dump(data, f, separators=(',', ':'))
        
        # Create moderately simplified (reduce points by 50%)
        import copy
        simplified = copy.deepcopy(data)
        for feature in simplified["features"]:
            geom = feature["geometry"]
            if geom["type"] == "Polygon":
                # Keep every other point
                geom["coordinates"][0] = geom["coordinates"][0][::2]
            elif geom["type"] == "MultiPolygon":
                for i, polygon in enumerate(geom["coordinates"]):
                    geom["coordinates"][i][0] = polygon[0][::2]
        
        simple_path = f"{output_base}_simplified.geojson"
        with open(simple_path, "w") as f:
            json.dump(simplified, f, separators=(',', ':'))
        
        # Check file sizes
        import os
        exact_size = os.path.getsize(exact_path) / 1024
        simple_size = os.path.getsize(simple_path) / 1024
        
        print(f"  Exact: {exact_size:.1f} KB")
        print(f"  Simplified: {simple_size:.1f} KB")
        
        return exact_path, simple_path

def main():
    """Extract exact boundaries for KY-06"""
    import tempfile
    import shutil
    
    extractor = BoundaryExtractor(state_fips="21", district_num="06")
    
    # Work in temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        original_dir = Path.cwd()
        tmp_path = Path(tmpdir)
        
        try:
            import os
            os.chdir(tmp_path)
            
            # Extract district
            if extractor.download_district_shapefile():
                district_data = extractor.extract_exact_district()
                if district_data:
                    # Save to data directory
                    output_dir = original_dir / "data" / "boundaries" / "ky_06"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    exact, simple = extractor.create_simplified_versions(
                        district_data, 
                        str(output_dir / "boundary")
                    )
                    
                    # Also save as the main files
                    shutil.copy(simple, output_dir / "boundary.geojson")
                    shutil.copy(simple, output_dir / "boundary_simplified.geojson")
            
            # Clean temp files
            for f in Path(".").glob("tl_*"):
                f.unlink()
            
            # Extract counties
            if extractor.download_county_shapefile():
                counties_data = extractor.extract_exact_counties()
                if counties_data:
                    output_dir = original_dir / "data" / "boundaries" / "ky_06"
                    
                    with open(output_dir / "counties.geojson", "w") as f:
                        json.dump(counties_data, f, separators=(',', ':'))
                    
                    print(f"✓ Saved {len(counties_data['features'])} counties")
        
        finally:
            os.chdir(original_dir)

if __name__ == "__main__":
    main()
