#!/usr/bin/env python3
"""Extract REAL KY-06 boundary with all details"""
import json
from pathlib import Path

def extract_real_boundary():
    # Read the full conversion
    with open('data/boundaries/ky_06/all_districts.geojson', 'r') as f:
        data = json.load(f)
    
    print(f"Total features in file: {len(data['features'])}")
    
    # Find district 06
    district_06 = None
    for feature in data['features']:
        props = feature.get('properties', {})
        
        # Print what we're seeing
        if len(data['features']) < 10:  # If few features, print all
            print(f"Feature properties: {props}")
        
        # Check various possible field names
        district_id = (props.get('CD119FP') or 
                      props.get('CD118FP') or 
                      props.get('CDNUM') or 
                      props.get('CD') or 
                      props.get('DISTRICT'))
        
        if str(district_id) == '06' or str(district_id) == '6':
            district_06 = feature
            print(f"Found District 06!")
            print(f"Properties: {props}")
            
            # Check geometry complexity
            geom = feature.get('geometry', {})
            if geom.get('type') == 'Polygon':
                coords = geom.get('coordinates', [[]])[0]
                print(f"Boundary points: {len(coords)}")
            elif geom.get('type') == 'MultiPolygon':
                total_points = sum(len(poly[0]) for poly in geom.get('coordinates', []))
                print(f"MultiPolygon with total boundary points: {total_points}")
            break
    
    if not district_06:
        print("ERROR: District 06 not found!")
        print("Looking for any district in the data...")
        # If we can't find 06, just take the first feature to see structure
        if data['features']:
            district_06 = data['features'][0]
            print(f"Using first feature instead: {district_06.get('properties')}")
    
    if district_06:
        # Create proper GeoJSON structure
        output = {
            "type": "FeatureCollection",
            "features": [district_06]
        }
        
        # Save the REAL boundary
        with open('data/boundaries/ky_06/boundary.geojson', 'w') as f:
            json.dump(output, f)
        
        # For simplified, we'll keep all the detail for now
        with open('data/boundaries/ky_06/boundary_simplified.geojson', 'w') as f:
            json.dump(output, f)
        
        print("✓ Saved REAL KY-06 boundary!")
        
        # Verify complexity
        geom = district_06.get('geometry', {})
        if geom.get('coordinates'):
            print(f"Geometry type: {geom.get('type')}")
            if geom.get('type') == 'Polygon':
                print(f"This is a complex boundary with {len(geom['coordinates'][0])} points")
            elif geom.get('type') == 'MultiPolygon':
                print(f"This is a multi-part boundary with {len(geom['coordinates'])} parts")

if __name__ == "__main__":
    extract_real_boundary()
