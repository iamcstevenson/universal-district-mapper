#!/usr/bin/env python3
"""
Enhanced Congressional District Map Generator with Accurate County Integration
Performs spatial analysis to identify counties within districts
"""

import os
import sys
import json
import argparse
import zipfile
import requests
from pathlib import Path
import folium
import geopandas as gpd
from shapely.geometry import Point, Polygon
import pandas as pd

class CongressionalMapGenerator:
    def __init__(self, district_code):
        self.district_code = district_code.upper()
        self.state_fips = self._get_state_fips()
        self.district_num = self._get_district_number()
        self.output_dir = Path(f"data/boundaries/{district_code.lower()}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Debug output
        print(f"Initialized with district_code: {self.district_code}")
        print(f"Extracted district_num: {self.district_num}")
        print(f"State FIPS: {self.state_fips}")
        
    def _get_state_fips(self):
        """Extract state FIPS code from district code"""
        state_abbrev = self.district_code[:2]
        fips_map = {
            'KY': '21', 'CA': '06', 'TX': '48', 'NY': '36', 'FL': '12',
            'PA': '42', 'IL': '17', 'OH': '39', 'GA': '13', 'NC': '37',
            'MI': '26', 'NJ': '34', 'VA': '51', 'WA': '53', 'AZ': '04',
            'MA': '25', 'TN': '47', 'IN': '18', 'MO': '29', 'MD': '24',
            'WI': '55', 'CO': '08', 'MN': '27', 'SC': '45', 'AL': '01',
            'LA': '22', 'OR': '41', 'OK': '40', 'CT': '09', 'IA': '19',
            'MS': '28', 'AR': '05', 'UT': '49', 'KS': '20', 'NV': '32',
            'NM': '35', 'WV': '54', 'NE': '31', 'ID': '16', 'HI': '15',
            'NH': '33', 'ME': '23', 'RI': '44', 'MT': '30', 'DE': '10',
            'SD': '46', 'ND': '38', 'AK': '02', 'VT': '50', 'WY': '56'
        }
        return fips_map.get(state_abbrev)
    
    def _get_district_number(self):
    """Extract district number from district code, preserving leading zeros"""
    print(f"DEBUG: Original district_code: '{self.district_code}'")
    print(f"DEBUG: Length: {len(self.district_code)}")
    print(f"DEBUG: After position 3: '{self.district_code[3:]}'")
    
    district_part = self.district_code[3:]
    result = district_part.zfill(2)
    print(f"DEBUG: Final result: '{result}'")
    return result
    
    def download_census_data(self):
        """Download Census TIGER shapefiles for districts and counties"""
        print(f"Downloading Census data for {self.district_code}...")
        
        # URLs for Census TIGER shapefiles
        district_url = f"https://www2.census.gov/geo/tiger/TIGER2024/CD/tl_2024_{self.state_fips}_cd119.zip"
        county_url = "https://www2.census.gov/geo/tiger/TIGER2024/COUNTY/tl_2024_us_county.zip"
        
        # Download and extract district shapefile
        district_zip = self.output_dir / "districts.zip"
        self._download_file(district_url, district_zip)
        self._extract_zip(district_zip, self.output_dir / "districts_raw")
        
        # Download and extract county shapefile
        county_zip = self.output_dir / "counties.zip"
        self._download_file(county_url, county_zip)
        self._extract_zip(county_zip, self.output_dir / "counties_raw")
        
        # Clean up zip files
        district_zip.unlink()
        county_zip.unlink()
    
    def _download_file(self, url, filepath):
        """Download a file with progress indication and SSL handling"""
        # Create a session with SSL verification disabled for CI environments
        session = requests.Session()
        session.verify = False  # Disable SSL verification for CI
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            print(f"Downloading {url}...")
            response = session.get(url, stream=True, headers=headers, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f"\rProgress: {progress:.1f}%", end='', flush=True)
            
            print(f"\nDownloaded {filepath.name} ({downloaded_size:,} bytes)")
            
        except Exception as e:
            print(f"\nError downloading {url}: {e}")
            # Try alternative URL format if available
            if 'www2.census.gov' in url:
                alt_url = url.replace('www2.census.gov', 'www.census.gov')
                print(f"Trying alternative URL: {alt_url}")
                try:
                    response = session.get(alt_url, stream=True, headers=headers, timeout=300)
                    response.raise_for_status()
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    print(f"Successfully downloaded from alternative URL")
                except Exception as alt_e:
                    raise Exception(f"Both primary and alternative downloads failed. Primary: {e}, Alternative: {alt_e}")
            else:
                raise
    
    def _extract_zip(self, zip_path, extract_dir):
        """Extract zip file to directory"""
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    
    def process_district_boundary(self):
        """Process district boundary from Census shapefile"""
        print(f"Processing district boundary for {self.district_code}...")
        
        # Find the district shapefile
        district_files = list((self.output_dir / "districts_raw").glob("*.shp"))
        if not district_files:
            raise FileNotFoundError("District shapefile not found")
        
        # Load district data
        districts_gdf = gpd.read_file(district_files[0])
        
        # Debug: Print available districts
        print(f"Available districts in shapefile: {sorted(districts_gdf['CD119FP'].unique())}")
        print(f"Looking for district: '{self.district_num}'")
        
        # Filter for our specific district
        district_row = districts_gdf[districts_gdf['CD119FP'] == self.district_num]
        
        if district_row.empty:
            available = sorted(districts_gdf['CD119FP'].unique())
            raise ValueError(f"District {self.district_num} not found in shapefile. Available districts: {available}")
        
        print(f"Found district {self.district_num} in shapefile")
        
        # Save full precision boundary
        district_geojson = district_row.to_json()
        with open(self.output_dir / "boundary.geojson", 'w') as f:
            f.write(district_geojson)
        
        # Create simplified version for web display
        district_simplified = district_row.copy()
        district_simplified['geometry'] = district_simplified['geometry'].simplify(0.001)
        simplified_geojson = district_simplified.to_json()
        with open(self.output_dir / "boundary_simplified.geojson", 'w') as f:
            f.write(simplified_geojson)
        
        return district_row
    
    def analyze_counties(self, district_gdf):
        """Perform spatial analysis to identify counties in district"""
        print("Analyzing county intersections...")
        
        # Find county shapefile
        county_files = list((self.output_dir / "counties_raw").glob("*.shp"))
        if not county_files:
            raise FileNotFoundError("County shapefile not found")
        
        # Load county data - filter to state first for performance
        counties_gdf = gpd.read_file(county_files[0])
        state_counties = counties_gdf[counties_gdf['STATEFP'] == self.state_fips].copy()
        
        # Ensure same CRS
        district_gdf = district_gdf.to_crs(state_counties.crs)
        district_geom = district_gdf.geometry.iloc[0]
        
        # Find intersecting counties
        intersecting_counties = []
        
        for idx, county in state_counties.iterrows():
            county_geom = county.geometry
            
            # Check if county intersects with district
            if county_geom.intersects(district_geom):
                # Calculate intersection area
                intersection = county_geom.intersection(district_geom)
                county_area = county_geom.area
                intersection_area = intersection.area
                
                # Determine if full or partial
                coverage_ratio = intersection_area / county_area
                is_full = coverage_ratio > 0.95  # 95% threshold for "full"
                
                county_info = {
                    'GEOID': county['GEOID'],
                    'NAME': county['NAME'],
                    'STATEFP': county['STATEFP'],
                    'geometry': county_geom,
                    'coverage_ratio': coverage_ratio,
                    'is_full': is_full,
                    'area_sq_km': county_area * 111000**2  # Rough conversion to sq km
                }
                intersecting_counties.append(county_info)
        
        # Sort by coverage ratio (descending)
        intersecting_counties.sort(key=lambda x: x['coverage_ratio'], reverse=True)
        
        print(f"\nFound {len(intersecting_counties)} counties in {self.district_code}:")
        full_counties = sum(1 for c in intersecting_counties if c['is_full'])
        partial_counties = len(intersecting_counties) - full_counties
        print(f"  - {full_counties} full counties")
        print(f"  - {partial_counties} partial counties")
        
        # Create GeoDataFrame for counties
        counties_data = []
        geometries = []
        for county in intersecting_counties:
            counties_data.append({
                'GEOID': county['GEOID'],
                'NAME': county['NAME'],
                'coverage_ratio': county['coverage_ratio'],
                'is_full': county['is_full']
            })
            geometries.append(county['geometry'])
        
        counties_gdf = gpd.GeoDataFrame(counties_data, geometry=geometries, crs=state_counties.crs)
        
        # Save counties GeoJSON
        counties_geojson = counties_gdf.to_json()
        with open(self.output_dir / "counties.geojson", 'w') as f:
            f.write(counties_geojson)
        
        # Save county analysis report
        self._save_county_report(intersecting_counties)
        
        return intersecting_counties
    
    def _save_county_report(self, counties):
        """Save detailed county analysis report"""
        report = {
            'district': self.district_code,
            'total_counties': len(counties),
            'full_counties': sum(1 for c in counties if c['is_full']),
            'partial_counties': sum(1 for c in counties if not c['is_full']),
            'counties': [
                {
                    'name': c['NAME'],
                    'geoid': c['GEOID'],
                    'coverage_ratio': round(c['coverage_ratio'], 4),
                    'type': 'full' if c['is_full'] else 'partial',
                    'area_sq_km': round(c['area_sq_km'], 2)
                }
                for c in counties
            ]
        }
        
        with open(self.output_dir / "county_analysis.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nCounty Analysis for {self.district_code}:")
        for county in report['counties']:
            coverage_pct = county['coverage_ratio'] * 100
            print(f"  {county['name']}: {coverage_pct:.1f}% ({county['type']})")
    
    def generate_map(self, counties_data):
        """Generate interactive Folium map"""
        print("Generating interactive map...")
        
        # Load district boundary
        with open(self.output_dir / "boundary_simplified.geojson") as f:
            district_geojson = json.load(f)
        
        # Calculate map center
        district_bounds = self._get_geojson_bounds(district_geojson)
        center_lat = (district_bounds['north'] + district_bounds['south']) / 2
        center_lon = (district_bounds['east'] + district_bounds['west']) / 2
        
        # Create map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=9,
            tiles='OpenStreetMap'
        )
        
        # Add district boundary
        folium.GeoJson(
            district_geojson,
            style_function=lambda x: {
                'fillColor': 'blue',
                'color': 'darkblue',
                'weight': 3,
                'fillOpacity': 0.1
            },
            popup=f"Congressional District {self.district_code}",
            tooltip=f"District {self.district_code}"
        ).add_to(m)
        
        # Add counties with different colors for full/partial
        if os.path.exists(self.output_dir / "counties.geojson"):
            with open(self.output_dir / "counties.geojson") as f:
                counties_geojson = json.load(f)
            
            for feature in counties_geojson['features']:
                is_full = feature['properties']['is_full']
                coverage = feature['properties']['coverage_ratio']
                county_name = feature['properties']['NAME']
                
                folium.GeoJson(
                    feature,
                    style_function=lambda x, is_full=is_full: {
                        'fillColor': 'green' if is_full else 'orange',
                        'color': 'darkgreen' if is_full else 'darkorange',
                        'weight': 2,
                        'fillOpacity': 0.3
                    },
                    popup=f"{county_name} County<br>{'Full' if is_full else 'Partial'} ({coverage*100:.1f}%)",
                    tooltip=f"{county_name} County"
                ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <b>Legend</b><br>
        <i class="fa fa-square" style="color:blue"></i> District Boundary<br>
        <i class="fa fa-square" style="color:green"></i> Full Counties<br>
        <i class="fa fa-square" style="color:orange"></i> Partial Counties
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        map_path = "index.html"
        m.save(map_path)
        print(f"Map saved to {map_path}")
        
        return map_path
    
    def _get_geojson_bounds(self, geojson):
        """Calculate bounds of GeoJSON"""
        coords = []
        for feature in geojson['features']:
            if feature['geometry']['type'] == 'Polygon':
                for ring in feature['geometry']['coordinates']:
                    coords.extend(ring)
            elif feature['geometry']['type'] == 'MultiPolygon':
                for polygon in feature['geometry']['coordinates']:
                    for ring in polygon:
                        coords.extend(ring)
        
        lons = [coord[0] for coord in coords]
        lats = [coord[1] for coord in coords]
        
        return {
            'north': max(lats),
            'south': min(lats),
            'east': max(lons),
            'west': min(lons)
        }
    
    def cleanup_temp_files(self):
        """Clean up temporary files to keep repo size down"""
        import shutil
        
        temp_dirs = ['districts_raw', 'counties_raw']
        for temp_dir in temp_dirs:
            temp_path = self.output_dir / temp_dir
            if temp_path.exists():
                shutil.rmtree(temp_path)
    
    def run(self):
        """Run the complete map generation process"""
        try:
            # Step 1: Download Census data
            self.download_census_data()
            
            # Step 2: Process district boundary
            district_gdf = self.process_district_boundary()
            
            # Step 3: Analyze counties with spatial intersection
            counties_data = self.analyze_counties(district_gdf)
            
            # Step 4: Generate interactive map
            self.generate_map(counties_data)
            
            # Step 5: Cleanup temporary files
            self.cleanup_temp_files()
            
            print(f"\n✅ Successfully generated map for {self.district_code}")
            print(f"📁 Output directory: {self.output_dir}")
            print(f"🗺️  Map available at: index.html")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating map: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Generate congressional district map with accurate county analysis')
    parser.add_argument('--district', required=True, help='District code (e.g., KY-06)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    generator = CongressionalMapGenerator(args.district)
    success = generator.run()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()