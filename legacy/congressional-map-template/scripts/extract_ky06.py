#!/usr/bin/env python3
"""Extract KY-06 boundary from Census shapefile"""

import geopandas as gpd
from pathlib import Path

def extract_district():
    # Use the 2024 shapefile
    shapefile_path = Path("data/boundaries/ky_06/tl_2024_21_cd119.shp")
    if not shapefile_path.exists():
        print("Error: Shapefile not found. Please run the download command first.")
        return
    
    # Load all KY districts
    gdf = gpd.read_file(shapefile_path)
    
    # Print info for debugging
    print(f"Loaded shapefile with {len(gdf)} districts")
    print(f"Columns: {gdf.columns.tolist()}")
    
    # The column for 119th Congress should be CD119FP
    if 'CD119FP' in gdf.columns:
        district_col = 'CD119FP'
    else:
        print(f"Available columns: {gdf.columns.tolist()}")
        district_col = gdf.columns[0]  # Use first column as fallback
    
    # Filter for district 06
    ky_06 = gdf[gdf[district_col] == '06'].copy()
    
    if ky_06.empty:
        print(f"Error: KY-06 not found")
        print(f"Available values: {gdf[district_col].unique()}")
        return
    
    # Convert to WGS84
    ky_06 = ky_06.to_crs('EPSG:4326')
    
    # Save as GeoJSON
    output_path = Path("data/boundaries/ky_06/boundary.geojson")
    ky_06.to_file(output_path, driver='GeoJSON')
    
    # Save simplified version
    ky_06_simplified = ky_06.copy()
    ky_06_simplified['geometry'] = ky_06_simplified['geometry'].simplify(0.001)
    
    simplified_path = Path("data/boundaries/ky_06/boundary_simplified.geojson")
    ky_06_simplified.to_file(simplified_path, driver='GeoJSON')
    
    print(f"✓ KY-06 boundary extracted to {output_path}")
    print(f"✓ Simplified boundary saved to {simplified_path}")
    
    # Print statistics
    bounds = ky_06.total_bounds
    print(f"\nBoundary statistics:")
    print(f"  West: {bounds[0]:.4f}")
    print(f"  South: {bounds[1]:.4f}")
    print(f"  East: {bounds[2]:.4f}")
    print(f"  North: {bounds[3]:.4f}")

if __name__ == "__main__":
    extract_district()
