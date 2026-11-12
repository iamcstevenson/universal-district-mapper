#!/usr/bin/env python3
"""Extract counties that are in KY-06"""
import json

# KY-06 counties (119th Congress)
KY06_COUNTIES = [
    "Anderson", "Bourbon", "Clark", "Fayette", 
    "Franklin", "Harrison", "Jessamine", 
    "Nicholas", "Scott", "Woodford"
]

def extract_counties():
    # Load all counties
    with open('data/boundaries/counties/all_counties.geojson', 'r') as f:
        data = json.load(f)
    
    # Filter for KY-06 counties
    ky06_counties = []
    for feature in data['features']:
        county_name = feature['properties'].get('NAME', '')
        if county_name in KY06_COUNTIES:
            print(f"Found {county_name} County")
            ky06_counties.append(feature)
    
    # Create output
    output = {
        "type": "FeatureCollection",
        "features": ky06_counties
    }
    
    # Save KY-06 counties
    with open('data/boundaries/ky_06/counties.geojson', 'w') as f:
        json.dump(output, f, separators=(',', ':'))
    
    print(f"✓ Saved {len(ky06_counties)} counties for KY-06")

if __name__ == "__main__":
    extract_counties()
