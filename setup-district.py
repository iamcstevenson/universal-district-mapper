#!/usr/bin/env python3
"""
District Setup Wizard

Sets up a new congressional district for mapping.
"""

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent))

from framework import DistrictBoundaryProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_district_from_template(district_name: str, short_name: str = None) -> str:
    """Create a new district directory from template."""
    if not short_name:
        # Generate short name from district name
        # e.g., "Kentucky 6th" -> "ky-6"
        parts = district_name.lower().replace('congressional district', '').strip().split()
        if len(parts) >= 2:
            state = parts[0][:2]  # First 2 letters of state
            number = ''.join(filter(str.isdigit, parts[-1]))  # Extract number
            short_name = f"{state}-{number}"
        else:
            short_name = district_name.lower().replace(' ', '-')

    district_dir = Path(f"districts/{short_name}")

    if district_dir.exists():
        raise FileExistsError(f"District already exists: {district_dir}")

    # Copy template
    template_dir = Path("districts/template")
    shutil.copytree(template_dir, district_dir)

    logger.info(f"Created district directory: {district_dir}")
    return str(district_dir)


def update_district_config(district_dir: str, district_info: dict):
    """Update district configuration with provided information."""
    config_path = Path(district_dir) / "config.json"

    # Load template config
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Update with provided information
    config.update(district_info)

    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    logger.info(f"Updated district config: {config_path}")


def process_tiger_shapefile(district_dir: str, shapefile_path: str, district_id: str = None):
    """Process TIGER shapefile for the district."""
    try:
        processor = DistrictBoundaryProcessor(district_dir)

        # Process the main district boundary
        created_files = processor.process_tiger_shapefile(shapefile_path, district_id)

        logger.info(f"Processed TIGER shapefile: {created_files}")

        # Calculate district bounds and center
        bounds = processor.get_district_bounds()
        center = processor.get_district_center()

        if bounds and center:
            # Update district config with calculated bounds
            config_path = Path(district_dir) / "config.json"
            with open(config_path, 'r') as f:
                config = json.load(f)

            config['bounds'] = bounds
            config['center'] = list(center)

            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info(f"Updated config with bounds and center")

        return True

    except Exception as e:
        logger.error(f"Error processing TIGER shapefile: {e}")
        return False


def interactive_setup():
    """Interactive district setup wizard."""
    print("🗺️  Universal District Mapper - District Setup Wizard")
    print("=" * 60)

    # Get district information
    district_name = input("District name (e.g., 'Kentucky 6th Congressional District'): ").strip()
    if not district_name:
        print("❌ District name is required")
        return False

    short_name = input(f"Short name (press Enter for auto-generated): ").strip()

    state = input("State abbreviation (e.g., 'KY'): ").strip().upper()
    district_number = input("District number (e.g., '6'): ").strip()
    representative = input("Representative name (optional): ").strip()
    party = input("Representative party (R/D/I, optional): ").strip().upper()

    # Population estimate
    population_str = input("Population estimate (optional): ").strip()
    population = 0
    if population_str:
        try:
            population = int(population_str.replace(',', ''))
        except ValueError:
            print("⚠️  Invalid population number, using 0")

    # TIGER shapefile
    shapefile_path = input("\\nPath to TIGER Congressional District shapefile: ").strip()
    if not shapefile_path or not Path(shapefile_path).exists():
        print("⚠️  Shapefile not found, you'll need to add boundaries manually")
        shapefile_path = None

    district_id = None
    if shapefile_path:
        district_id = input("District ID in shapefile (e.g., '2106' for KY-6, optional): ").strip()

    # Create district
    try:
        print(f"\\n🔧 Creating district: {district_name}")

        # Create from template
        district_dir = create_district_from_template(district_name, short_name)

        # Prepare district info
        district_info = {
            "name": district_name,
            "short_name": Path(district_dir).name,
            "state": state,
            "district_number": district_number,
            "representative": representative or "TBD",
            "party": party or "TBD",
            "population": population,
            "created": "2024-09-17",
            "last_updated": "2024-09-17"
        }

        # Update config
        update_district_config(district_dir, district_info)

        # Process shapefile if provided
        if shapefile_path:
            print("🗂️  Processing TIGER shapefile...")
            if process_tiger_shapefile(district_dir, shapefile_path, district_id):
                print("✅ TIGER shapefile processed successfully")
            else:
                print("❌ Error processing TIGER shapefile")

        print(f"\\n✅ District setup complete!")
        print(f"📁 District directory: {district_dir}")
        print(f"\\nNext steps:")
        print(f"1. Validate boundaries: python generate-map.py --validate-district {Path(district_dir).name}")
        print(f"2. Create overlays: python generate-map.py --create-overlay healthcare --sheet-url 'your-sheet-url'")
        print(f"3. Generate map: python generate-map.py --district {Path(district_dir).name}")

        return True

    except Exception as e:
        print(f"❌ Error setting up district: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Congressional District Setup Wizard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive setup
  python setup-district.py

  # Command-line setup
  python setup-district.py --name "Kentucky 6th Congressional District" \\
                          --state KY --district 6 --representative "Andy Barr" \\
                          --tiger-file tl_2024_us_cd118.shp --district-id 2106

  # Setup with minimal info
  python setup-district.py --name "Texas 2nd" --state TX --district 2
        """
    )

    # District information
    parser.add_argument('--name', help='Full district name')
    parser.add_argument('--short-name', help='Short name (auto-generated if not provided)')
    parser.add_argument('--state', help='State abbreviation (e.g., KY)')
    parser.add_argument('--district', help='District number')
    parser.add_argument('--representative', help='Representative name')
    parser.add_argument('--party', help='Representative party (R/D/I)')
    parser.add_argument('--population', type=int, help='Population estimate')

    # TIGER shapefile options
    parser.add_argument('--tiger-file', help='Path to TIGER Congressional District shapefile')
    parser.add_argument('--district-id', help='District ID in shapefile (e.g., 2106 for KY-6)')

    # Options
    parser.add_argument('--interactive', action='store_true', help='Run interactive setup wizard')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run interactive setup if no arguments or --interactive flag
    if len(sys.argv) == 1 or args.interactive:
        return interactive_setup()

    # Validate required arguments for command-line setup
    if not args.name:
        print("❌ --name is required for command-line setup")
        return False

    try:
        print(f"🔧 Setting up district: {args.name}")

        # Create from template
        district_dir = create_district_from_template(args.name, args.short_name)

        # Prepare district info
        district_info = {
            "name": args.name,
            "short_name": Path(district_dir).name,
            "created": "2024-09-17",
            "last_updated": "2024-09-17"
        }

        # Add optional fields
        if args.state:
            district_info["state"] = args.state.upper()
        if args.district:
            district_info["district_number"] = args.district
        if args.representative:
            district_info["representative"] = args.representative
        if args.party:
            district_info["party"] = args.party.upper()
        if args.population:
            district_info["population"] = args.population

        # Update config
        update_district_config(district_dir, district_info)

        # Process shapefile if provided
        if args.tiger_file:
            print("🗂️  Processing TIGER shapefile...")
            if process_tiger_shapefile(district_dir, args.tiger_file, args.district_id):
                print("✅ TIGER shapefile processed successfully")
            else:
                print("❌ Error processing TIGER shapefile")

        print(f"\\n✅ District setup complete!")
        print(f"📁 District directory: {district_dir}")

        return True

    except Exception as e:
        print(f"❌ Error setting up district: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)