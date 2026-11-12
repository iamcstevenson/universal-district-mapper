# Universal Congressional District Mapper

A flexible, branch-based framework for creating interactive maps of any US Congressional District with customizable data overlays. Built for iterative development of mapping ideas with clean data separation and precise boundary handling.

## 🎯 Philosophy

This framework solves the core challenge of congressional district mapping: **maintaining clean separation between different data types while ensuring precise boundary accuracy**. Each overlay idea gets its own Git branch, allowing you to:

- Work on different overlays independently
- Switch between ideas without losing work
- Maintain clean data history and versioning
- Easily combine multiple overlays on demand

## 🏗️ Architecture Overview

### Core Components

```
universal-district-mapper/
├── framework/                    # Core reusable components
│   ├── boundaries.py            # TIGER shapefile processing & validation
│   ├── sheets.py                # Google Sheets data integration
│   ├── geocoding.py             # Address → coordinates + validation
│   ├── overlays.py              # Git branch-based overlay management
│   └── generator.py             # Interactive map generation engine
├── districts/                   # District configurations
│   ├── template/                # Template for new districts
│   └── {district-name}/         # Individual district configs
├── overlays/                    # Overlay data (branch-specific)
├── output/                      # Generated HTML maps
├── generate-map.py              # Main CLI script
└── setup-district.py            # District setup wizard
```

### Git Branch Strategy

**main branch**: Contains framework code + district boundary configurations
```
main/
├── framework/          # Core framework code
├── districts/          # District boundary configs
└── scripts/            # Generation utilities
```

**Overlay branches**: Each overlay type gets its own branch
```
overlay/healthcare      # Hospital & clinic data
overlay/distilleries    # Bourbon distillery locations
overlay/agriculture     # Farm & agricultural data
overlay/education       # Schools & education facilities
overlay/broadband       # Internet infrastructure
overlay/transportation  # Transit & infrastructure
```

This approach ensures:
- **Clean separation**: Each overlay is isolated
- **Easy switching**: `git checkout overlay/healthcare`
- **Data history**: Full version control for each overlay
- **Collaboration**: Multiple people can work on different overlays
- **Combination**: Generate maps with any combination of overlays

## 🚀 Getting Started

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/iamcstevenson/universal-district-mapper.git
cd universal-district-mapper

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Your First District

```bash
# Interactive setup (recommended)
python setup-district.py

# Or command line setup
python setup-district.py \
  --name "Kentucky 6th Congressional District" \
  --state KY \
  --district 6 \
  --representative "Andy Barr" \
  --tiger-file path/to/tl_2024_us_cd118.shp \
  --district-id 2106
```

**TIGER Shapefile Requirements:**
- Download from: https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
- Select: "Congressional Districts" for current year
- Look for files like: `tl_2024_us_cd118.shp` (118th Congress)
- District ID format: StateCode + DistrictNumber (e.g., "2106" for KY-6)

### 3. Validate District Setup

```bash
python generate-map.py --validate-district ky-6

# Should output:
# 📍 Boundary Validation for ky-6:
#   District boundary: ✅
#   Counties reference: ✅ Optional
#   Partial counties: ✅ Optional
```

### 4. Generate Base Map

```bash
python generate-map.py --district ky-6

# Output: Opens base district map in browser
# File: output/ky-6-base.html
```

## 📊 Working with Overlays: The Iterative Process

### Understanding the Overlay Workflow

Each time you have a **new mapping idea** (hospitals, schools, farms, etc.), you:

1. **Create overlay branch** - Isolated workspace for this data type
2. **Setup Google Sheet** - Standardized data collection
3. **Import & geocode data** - Convert addresses to precise coordinates
4. **Generate & review maps** - Visual validation of data
5. **Iterate & refine** - Update data, regenerate maps
6. **Combine with other overlays** - Create multi-layer visualizations

### Step-by-Step: Creating Your First Overlay

#### Example: Healthcare Facilities Overlay

**Step 1: Prepare Google Sheets Data**

Create a Google Sheet with **exactly these columns**:
```
name          | address1              | address2 | city        | county     | state | zip   | notes
------------- | --------------------- | -------- | ----------- | ---------- | ----- | ----- | ---------------------------
UK Hospital   | 800 Rose Street       |          | Lexington   | Fayette    | KY    | 40536 | Major medical center
Rural Clinic  | 123 Main Street       |          | Georgetown  | Scott      | KY    | 40324 | Primary care only
Community Med | 456 Healthcare Drive  | Suite A  | Richmond    | Madison    | KY    | 40475 | Urgent care facility
```

**Required columns**: `name`, `address1`, `city`, `county`, `state`, `zip`
**Optional columns**: `address2`, `notes`

**Step 2: Make Sheet Public & Get URL**
1. In Google Sheets: File → Share → "Anyone with the link can view"
2. Copy the full sharing URL (contains `/d/{sheet-id}/`)

**Step 3: Create Overlay Branch & Import Data**

```bash
python generate-map.py \
  --create-overlay healthcare \
  --sheet-url "https://docs.google.com/spreadsheets/d/1abc123..." \
  --description "Healthcare facilities at risk of closure"

# This will:
# 1. Create git branch "overlay/healthcare"
# 2. Switch to that branch
# 3. Import data from Google Sheets
# 4. Geocode all addresses
# 5. Validate coordinates are within district
# 6. Save processed data to overlays/healthcare_data.json
# 7. Commit changes to the overlay branch
```

**Step 4: Review Geocoding Results**

The import process will show a report:
```
✅ Created overlay: healthcare
📊 Processed 25 records
🎯 Geocoding success rate: 96.0%
🚨 Issues found:
  - 1 address failed geocoding: "123 Invalid St, Nowhere, KY"
  - 2 addresses outside district: "Hospital in Louisville, KY"
```

**Step 5: Generate & Review Map**

```bash
python generate-map.py --district ky-6 --overlay healthcare

# Output: output/ky-6-healthcare.html
# Opens automatically in browser for review
```

**Step 6: Iterate & Refine Data**

If you need to fix issues:

1. **Update Google Sheet** (fix addresses, remove invalid entries)
2. **Re-import data**:
   ```bash
   # Still on overlay/healthcare branch
   python generate-map.py \
     --create-overlay healthcare \
     --sheet-url "https://docs.google.com/spreadsheets/d/1abc123..."
   ```
3. **Regenerate map**: `python generate-map.py --district ky-6 --overlay healthcare`

### Creating Additional Overlays

#### Example: Distilleries Overlay

```bash
# Create new overlay branch
python generate-map.py \
  --create-overlay distilleries \
  --sheet-url "https://docs.google.com/spreadsheets/d/def456..." \
  --description "Bourbon distilleries and tasting rooms"

# Generate distillery map
python generate-map.py --district ky-6 --overlay distilleries
```

#### Example: Agriculture Overlay

```bash
# Create agriculture overlay
python generate-map.py \
  --create-overlay agriculture \
  --sheet-url "https://docs.google.com/spreadsheets/d/ghi789..." \
  --description "Soybean and corn farms in district"

# Generate farm map
python generate-map.py --district ky-6 --overlay agriculture
```

### Managing Multiple Overlays

#### Switching Between Overlays

```bash
# List all available overlays
python generate-map.py --list-overlays

# Switch to healthcare overlay
git checkout overlay/healthcare
python generate-map.py --district ky-6 --overlay healthcare

# Switch to distilleries overlay
git checkout overlay/distilleries
python generate-map.py --district ky-6 --overlay distilleries

# Return to main branch (no overlays)
git checkout main
python generate-map.py --district ky-6
```

#### Combining Multiple Overlays

```bash
# Generate map with multiple overlays
python generate-map.py --district ky-6 --overlays healthcare,distilleries

# Generate map with all available overlays
python generate-map.py --district ky-6 --overlays healthcare,distilleries,agriculture

# Output: ky-6-healthcare-distilleries-agriculture.html
```

## 🔄 Iterative Development Workflow

### New Overlay Idea Process

When you get a **new mapping idea**, follow this workflow:

#### 1. Research & Data Collection
```bash
# Create branch for research/testing
git checkout -b research/broadband-access

# Create Google Sheet with data
# Test addresses for geocoding accuracy
```

#### 2. Create Production Overlay
```bash
# Create official overlay branch
git checkout main
python generate-map.py \
  --create-overlay broadband \
  --sheet-url "your-google-sheet-url" \
  --description "Broadband internet access points"
```

#### 3. Iterate & Refine
```bash
# Review generated map
python generate-map.py --district ky-6 --overlay broadband

# Fix data issues in Google Sheet
# Re-import with same command:
python generate-map.py --create-overlay broadband --sheet-url "same-url"

# Regenerate map
python generate-map.py --district ky-6 --overlay broadband
```

#### 4. Integration Testing
```bash
# Test with other overlays
python generate-map.py --district ky-6 --overlays healthcare,broadband
python generate-map.py --district ky-6 --overlays distilleries,broadband,agriculture
```

#### 5. Documentation & Sharing
```bash
# Commit final changes
git add .
git commit -m "Finalize broadband overlay data and validation"

# Share branch with team
git push origin overlay/broadband
```

## 🗺️ Adding New Districts

### Process for Each New District

```bash
# 1. Setup district
python setup-district.py --name "Texas 2nd Congressional District"

# 2. Validate boundaries
python generate-map.py --validate-district tx-2

# 3. Use existing overlays
git checkout overlay/healthcare
python generate-map.py --district tx-2 --overlay healthcare

# 4. Create district-specific overlays
python generate-map.py \
  --create-overlay oil-refineries \
  --sheet-url "texas-specific-data-url"
```

### District-Specific vs Universal Overlays

**Universal Overlays** (work across districts):
- Healthcare facilities
- Educational institutions
- Broadband access points
- Agricultural operations

**District-Specific Overlays** (unique to region):
- Oil refineries (Texas districts)
- Bourbon distilleries (Kentucky districts)
- Tech companies (California districts)
- Mining operations (West Virginia districts)

## 🛠️ Advanced Usage

### Custom Overlay Configurations

Create custom overlay styling by branch:

```bash
# Switch to overlay branch
git checkout overlay/healthcare

# Edit overlay configuration
# File: overlays/healthcare.json
{
  "name": "healthcare",
  "marker_color": "#DC2626",
  "marker_icon": "🏥",
  "popup_template": "custom",
  "clustering": true
}
```

### Batch Processing Multiple Districts

```bash
# Process same overlay across multiple districts
for district in ky-6 ky-4 tx-2; do
  python generate-map.py --district $district --overlay healthcare
done
```

### Data Quality Monitoring

```bash
# Generate geocoding reports
python generate-map.py --create-overlay healthcare --sheet-url "url" --verbose

# Check boundary validation
python generate-map.py --validate-district ky-6

# Review data quality metrics in logs
```

## 📋 Google Sheets Best Practices

### Data Collection Standards

**Always use these exact column names**:
```
name          | address1         | address2 | city      | county    | state | zip   | notes
Hospital ABC  | 123 Main St      | Unit 5   | Lexington | Fayette   | KY    | 40502 | Emergency services
Clinic XYZ    | 456 Oak Ave      |          | Richmond  | Madison   | KY    | 40475 | Primary care only
```

### Address Quality Tips

**Good addresses** (geocode successfully):
- `123 Main Street, Lexington, KY 40502`
- `456 Oak Avenue, Georgetown, KY 40324`
- `789 County Road 15, Irvine, KY 40336`

**Problematic addresses** (may fail):
- `Behind the Walmart` (no street address)
- `Rural Route 1` (too vague)
- `Main Street` (missing house number)

### Data Collaboration

**Team Workflow**:
1. **Data Owner** creates and maintains Google Sheet
2. **Reviewers** can suggest edits via Google Sheets comments
3. **Technical Lead** imports data and generates maps
4. **Stakeholders** review generated maps and provide feedback
5. **Loop**: Update sheet → reimport → regenerate → review

## 🔧 Technical Reference

### Framework Components

#### `framework/boundaries.py`
- **Purpose**: TIGER shapefile processing and boundary validation
- **Key Functions**:
  - `process_tiger_shapefile()` - Convert shapefiles to GeoJSON
  - `point_in_district()` - Validate coordinates within boundaries
  - `extract_partial_counties()` - Handle partial county boundaries

#### `framework/sheets.py`
- **Purpose**: Google Sheets data integration
- **Key Functions**:
  - `read_sheet_from_url()` - Import data from public Google Sheets
  - `validate_sheet_format()` - Check data structure
  - `_build_full_address()` - Create geocoding-ready addresses

#### `framework/geocoding.py`
- **Purpose**: Address geocoding and district validation
- **Key Functions**:
  - `geocode_dataframe()` - Batch geocode addresses
  - `validate_district_membership()` - Check coordinates within district
  - `create_geocoding_report()` - Generate quality reports

#### `framework/overlays.py`
- **Purpose**: Git branch-based overlay management
- **Key Functions**:
  - `create_overlay_branch()` - Create new overlay branch
  - `save_overlay_data()` - Store processed data
  - `load_overlay_data()` - Retrieve overlay data for mapping

#### `framework/generator.py`
- **Purpose**: Interactive map generation
- **Key Functions**:
  - `create_base_map()` - Generate district base map
  - `add_overlay()` - Add overlay markers to map
  - `add_search_controls()` - Interactive address search

### CLI Reference

#### Main Generation Script
```bash
python generate-map.py [OPTIONS]

# District operations
--district DISTRICT_NAME          Generate map for district
--validate-district DISTRICT_NAME Validate district boundaries

# Overlay operations
--create-overlay OVERLAY_NAME     Create new overlay branch
--overlay OVERLAY_NAME            Include single overlay
--overlays OVERLAY1,OVERLAY2      Include multiple overlays
--list-overlays                   List available overlays

# Data sources
--sheet-url URL                   Google Sheets URL for data
--description TEXT                Overlay description

# Output options
--output PATH                     Custom output path
--verbose, -v                     Verbose logging
```

#### District Setup Script
```bash
python setup-district.py [OPTIONS]

# District information
--name "District Name"            Full district name
--state STATE_CODE               State abbreviation (KY, TX, etc.)
--district NUMBER                District number
--representative NAME            Representative name
--party PARTY                    Party affiliation (R/D/I)

# Boundary data
--tiger-file PATH                Path to TIGER shapefile
--district-id ID                 District ID in shapefile

# Modes
--interactive                    Interactive setup wizard
--verbose, -v                    Verbose logging
```

### Error Handling

**Common Issues & Solutions**:

1. **Geocoding Failures**
   ```
   Error: Could not geocode address: "123 Invalid St"
   Solution: Fix address in Google Sheet, reimport data
   ```

2. **Boundary Validation Errors**
   ```
   Error: District boundary file not found
   Solution: Run setup-district.py with proper TIGER shapefile
   ```

3. **Google Sheets Access**
   ```
   Error: Could not read Google Sheet
   Solution: Ensure sheet is public, check sharing URL
   ```

4. **Git Branch Issues**
   ```
   Error: Branch overlay/healthcare already exists
   Solution: Switch to branch or delete and recreate
   ```

## 🎯 Project Roadmap

### Current Capabilities
- ✅ Precise district boundary handling
- ✅ Google Sheets integration
- ✅ Git branch-based overlay management
- ✅ Address geocoding with validation
- ✅ Interactive map generation
- ✅ Multi-overlay combinations

### Planned Enhancements
- 🔜 Custom marker styling per overlay
- 🔜 Data quality dashboard
- 🔜 Automated data refresh workflows
- 🔜 Export capabilities (PDF, PNG)
- 🔜 Advanced analytics integration
- 🔜 Multi-state district support

## 📄 License

MIT License - Use freely for any congressional district mapping needs.

---

**Built for iterative political mapping and data visualization. Each overlay idea gets its own branch, ensuring clean development and easy collaboration.**
## Earlier versions

The two repos this framework replaced are in [`legacy/`](legacy/README.md).
