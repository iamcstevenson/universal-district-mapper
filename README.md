# Universal Congressional District Mapper

A flexible framework for creating interactive maps of any US Congressional District with customizable data overlays.

## Features

- **Precise Boundaries**: Uses official TIGER shapefiles for exact district boundaries, including partial counties
- **Overlay System**: Branch-based overlay management for different data types
- **Google Sheets Integration**: Pull overlay data from shared Google Sheets
- **Address Geocoding**: Automatic conversion of addresses to coordinates
- **Consistent Styling**: Beautiful, consistent visual design across all maps

## Quick Start

### 1. Setup New District
```bash
python setup-district.py --name "Kentucky 6th" --tiger-file path/to/ky6.shp
```

### 2. Create Overlay Branch
```bash
python generate-map.py --create-overlay healthcare --sheet-url "https://docs.google.com/spreadsheets/d/your-sheet-id"
```

### 3. Generate Map
```bash
python generate-map.py --district ky-6 --overlay healthcare
```

## Repository Structure

```
universal-district-mapper/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── generate-map.py             # Main generation script
├── setup-district.py           # District setup wizard
├── framework/                  # Core framework
│   ├── boundaries.py           # Precise boundary handling
│   ├── overlays.py            # Overlay management
│   ├── geocoding.py           # Address → coordinates
│   ├── sheets.py              # Google Sheets integration
│   └── generator.py           # Map generation engine
├── districts/                 # District configurations
│   ├── template/              # New district template
│   └── ky-6/                 # Example: Kentucky 6th
│       ├── config.json       # District metadata
│       └── boundaries/       # Exact TIGER boundaries
├── templates/                 # HTML/CSS templates
└── output/                   # Generated maps
```

## Git Branch Strategy

- **main**: Base framework + district boundaries
- **overlay/healthcare**: Healthcare facilities overlay
- **overlay/distilleries**: Bourbon distilleries overlay
- **overlay/agriculture**: Farming/agriculture overlay
- **overlay/education**: Schools/education overlay

## Data Requirements

### District Boundaries
Provide TIGER shapefile for your congressional district:
- Download from: https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
- Look for: "Congressional Districts" for the current year

### Overlay Data (Google Sheets)
Standard columns for all overlays:
- `name`: Facility/location name
- `address1`: Street address
- `address2`: Apartment/suite (optional)
- `city`: City name
- `county`: County name
- `state`: State abbreviation
- `zip`: ZIP code
- `notes`: Additional information (optional)

## Usage Examples

### Setup District
```bash
# Setup Kentucky 6th District
python setup-district.py --name "Kentucky 6th" --tiger-file tl_2024_21_cd118.shp
```

### Create Healthcare Overlay
```bash
# Create new overlay branch and pull data
python generate-map.py --create-overlay healthcare --sheet-url "https://docs.google.com/spreadsheets/d/1abc123..."

# Generate map with healthcare overlay
python generate-map.py --district ky-6 --overlay healthcare
```

### Switch Between Overlays
```bash
# Work on distilleries overlay
git checkout overlay/distilleries
python generate-map.py --district ky-6 --overlay distilleries

# Switch back to healthcare
git checkout overlay/healthcare
python generate-map.py --district ky-6 --overlay healthcare
```

### Generate Multiple Overlays
```bash
# Generate base map (no overlays)
python generate-map.py --district ky-6

# Generate with multiple overlays
python generate-map.py --district ky-6 --overlays healthcare,distilleries
```

## Technical Details

### Boundary Precision
The framework uses three types of boundary files:
- `district.geojson`: Exact congressional district boundary
- `counties.geojson`: Full county boundaries (for context)
- `partial-counties.geojson`: Partial county segments within district

### Address Geocoding
Addresses are automatically geocoded and verified to be within district boundaries:
1. Convert address to lat/lng coordinates
2. Check if coordinates fall within exact district boundary
3. Flag any addresses outside the district for review

### Google Sheets Integration
- Uses Google Sheets API for real-time data updates
- Supports collaborative editing of overlay data
- Automatic address validation and geocoding

## Requirements

- Python 3.8+
- GDAL/Fiona for shapefile processing
- Folium for map generation
- Google Sheets API access (optional)

## Installation

```bash
pip install -r requirements.txt
```

For Google Sheets integration, you'll also need:
1. Google Cloud Project with Sheets API enabled
2. Service account credentials

## Contributing

Each overlay type should be developed on its own branch:
1. Create overlay branch: `git checkout -b overlay/your-overlay-name`
2. Develop overlay logic in `framework/overlays/`
3. Test with existing districts
4. Submit pull request to merge into main

## License

MIT License - Feel free to use for any congressional district mapping needs.