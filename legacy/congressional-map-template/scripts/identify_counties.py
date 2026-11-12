#!/usr/bin/env python3
"""Identify counties within KY-06"""
import json

def identify_ky06_counties():
    # These are the counties typically in KY-06
    # Based on the current 119th Congress district
    ky06_counties = [
        "Anderson",
        "Bourbon", 
        "Clark",
        "Fayette",  # Lexington
        "Franklin", # Frankfort
        "Harrison",
        "Jessamine",
        "Nicholas",
        "Scott",
        "Woodford"
    ]
    
    print("Counties in Kentucky's 6th Congressional District:")
    for county in ky06_counties:
        print(f"  - {county} County")
    
    # Save for reference
    with open('data/boundaries/ky_06_counties.json', 'w') as f:
        json.dump({
            "district": "KY-06",
            "counties": ky06_counties,
            "notes": "119th Congress boundaries"
        }, f, indent=2)
    
    return ky06_counties

if __name__ == "__main__":
    identify_ky06_counties()
