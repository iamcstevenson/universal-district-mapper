#!/usr/bin/env python3
"""Simple extraction without geopandas"""
import json
from pathlib import Path

def extract_district_06():
    # Read the converted GeoJSON
    with open('data/boundaries/ky_06/boundary_all.geojson', 'r') as f:
        data = json.load(f)
    
    # Filter for district 06
    features_06 = []
    for feature in data['features']:
        props = feature.get('properties', {})
        # Check different possible field names
        district_num = props.get('CD119FP') or props.get('CDNUM') or props.get('CD')
        if district_num == '06':
            features_06.append(feature)
            print(f"Found district 06: {props}")
    
    if not features_06:
        print("District 06 not found. Available properties in first feature:")
        if data['features']:
            print(data['features'][0].get('properties', {}))
        return
    
    # Create new GeoJSON with just district 06
    output = {
        "type": "FeatureCollection",
        "features": features_06
    }
    
    # Save the extracted boundary
    with open('data/boundaries/ky_06/boundary.geojson', 'w') as f:
        json.dump(output, f)
    
    # Create simplified version (just copy for now)
    with open('data/boundaries/ky_06/boundary_simplified.geojson', 'w') as f:
        json.dump(output, f)
    
    print("✓ Extracted KY-06 boundary successfully")

if __name__ == "__main__":
    extract_district_06()
