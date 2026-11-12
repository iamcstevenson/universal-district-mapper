#!/usr/bin/env python3
"""Simplify boundary to reduce file size while maintaining accuracy"""
import json
from pathlib import Path

def simplify_boundary():
    # Load the full boundary
    with open('data/boundaries/ky_06/all_districts.geojson', 'r') as f:
        data = json.load(f)
    
    # Find district 06
    district_06 = None
    for feature in data['features']:
        props = feature.get('properties', {})
        if props.get('CD119FP') == '06':
            district_06 = feature
            break
    
    if not district_06:
        print("Error: District 06 not found")
        return
    
    # Simplify coordinates by reducing precision
    def round_coords(coords, precision=5):
        if isinstance(coords[0], list):
            return [round_coords(c, precision) for c in coords]
        else:
            return [round(c, precision) for c in coords]
    
    # Simplify geometry
    geom = district_06['geometry']
    geom['coordinates'] = round_coords(geom['coordinates'])
    
    # Create clean output
    output = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {
                "district": "KY-06",
                "state": "Kentucky",
                "cd_fips": "2106"
            },
            "geometry": geom
        }]
    }
    
    # Save simplified version
    with open('data/boundaries/ky_06/boundary.geojson', 'w') as f:
        json.dump(output, f, separators=(',', ':'))
    
    # Create ultra-simplified for faster loading
    # Skip every other coordinate point
    if geom['type'] == 'Polygon':
        geom['coordinates'][0] = geom['coordinates'][0][::2]
    elif geom['type'] == 'MultiPolygon':
        for i, polygon in enumerate(geom['coordinates']):
            geom['coordinates'][i][0] = polygon[0][::2]
    
    with open('data/boundaries/ky_06/boundary_simplified.geojson', 'w') as f:
        json.dump(output, f, separators=(',', ':'))
    
    # Check file sizes
    import os
    size = os.path.getsize('data/boundaries/ky_06/boundary.geojson') / (1024*1024)
    size_simple = os.path.getsize('data/boundaries/ky_06/boundary_simplified.geojson') / (1024*1024)
    
    print(f"✓ Boundary saved: {size:.2f} MB")
    print(f"✓ Simplified saved: {size_simple:.2f} MB")

if __name__ == "__main__":
    simplify_boundary()
