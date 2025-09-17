#!/usr/bin/env python3
"""
Universal Congressional District Map Generator

Main script for generating interactive congressional district maps with overlays.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent))

from framework import DistrictBoundaryProcessor, OverlayManager, MapGenerator, AddressGeocoder
from framework.sheets import GoogleSheetsReader, OverlayDataProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_overlay(overlay_name: str, sheet_url: str, description: str = ""):
    """Create a new overlay branch and process data from Google Sheets."""
    try:
        logger.info(f"Creating overlay: {overlay_name}")

        # Initialize components
        overlay_manager = OverlayManager()
        sheets_reader = GoogleSheetsReader()
        data_processor = OverlayDataProcessor(sheets_reader)

        # Create overlay branch
        branch_name = overlay_manager.create_overlay_branch(overlay_name, description)
        logger.info(f"Created branch: {branch_name}")

        # Switch to overlay branch
        overlay_manager.switch_to_overlay(overlay_name)

        # Process data from Google Sheets
        overlay_data = data_processor.process_overlay_data(sheet_url, overlay_name)

        # Initialize geocoder
        geocoder = AddressGeocoder()

        # Convert overlay data to DataFrame for geocoding
        import pandas as pd
        df = pd.DataFrame(overlay_data['data'])

        # Geocode addresses
        df = geocoder.geocode_dataframe(df)

        # Update overlay data with geocoded results
        overlay_data['data'] = df.to_dict('records')

        # Save overlay data
        data_path = overlay_manager.save_overlay_data(overlay_name, overlay_data, sheet_url)

        # Commit changes
        overlay_manager.commit_overlay_changes(
            overlay_name,
            f"Add {overlay_name} overlay data from Google Sheets"
        )

        # Create geocoding report
        report = geocoder.create_geocoding_report(df)

        logger.info(f"Overlay created successfully: {overlay_name}")
        logger.info(f"Geocoding report: {report['geocoding']['success_rate']}% success rate")

        print(f"\\n✅ Created overlay: {overlay_name}")
        print(f"📊 Processed {len(df)} records")
        print(f"🎯 Geocoding success rate: {report['geocoding']['success_rate']}%")
        print(f"💾 Data saved to: {data_path}")

        return True

    except Exception as e:
        logger.error(f"Error creating overlay: {e}")
        print(f"❌ Error creating overlay: {e}")
        return False


def generate_map(district: str, overlays: list = None, output: str = None):
    """Generate a map for the specified district with optional overlays."""
    try:
        logger.info(f"Generating map for district: {district}")

        # Find district directory
        district_dir = Path(f"districts/{district}")
        if not district_dir.exists():
            raise FileNotFoundError(f"District not found: {district}")

        # Initialize map generator
        generator = MapGenerator(str(district_dir))

        # Generate map with overlays
        output_path = generator.generate_map(overlays, output)

        logger.info(f"Map generated successfully: {output_path}")

        print(f"\\n✅ Map generated: {output_path}")
        if overlays:
            print(f"📍 Overlays included: {', '.join(overlays)}")

        # Open map in browser (optional)
        import webbrowser
        webbrowser.open(f"file://{Path(output_path).absolute()}")

        return True

    except Exception as e:
        logger.error(f"Error generating map: {e}")
        print(f"❌ Error generating map: {e}")
        return False


def validate_district_boundaries(district: str):
    """Validate district boundary files."""
    try:
        district_dir = Path(f"districts/{district}")
        if not district_dir.exists():
            raise FileNotFoundError(f"District not found: {district}")

        processor = DistrictBoundaryProcessor(str(district_dir))
        validation = processor.validate_boundaries()

        print(f"\\n📍 Boundary Validation for {district}:")
        print(f"  District boundary: {'✅' if validation['district_valid'] else '❌'}")
        print(f"  Counties reference: {'✅' if validation['counties_exists'] else '⚠️  Optional'}")
        print(f"  Partial counties: {'✅' if validation['partial_counties_exists'] else '⚠️  Optional'}")

        return validation['district_valid']

    except Exception as e:
        logger.error(f"Error validating boundaries: {e}")
        print(f"❌ Error validating boundaries: {e}")
        return False


def list_overlays():
    """List all available overlay branches."""
    try:
        overlay_manager = OverlayManager()
        overlays = overlay_manager.list_overlays()

        if overlays:
            print("\\n📋 Available Overlays:")
            for overlay in overlays:
                print(f"  • {overlay['name']}: {overlay['description']}")
        else:
            print("\\n📋 No overlays found. Create one with --create-overlay")

        current = overlay_manager.get_current_overlay()
        if current:
            print(f"\\n🎯 Current overlay: {current}")

        return True

    except Exception as e:
        logger.error(f"Error listing overlays: {e}")
        print(f"❌ Error listing overlays: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Universal Congressional District Map Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate base map for Kentucky 6th District
  python generate-map.py --district ky-6

  # Create healthcare overlay from Google Sheet
  python generate-map.py --create-overlay healthcare --sheet-url "https://docs.google.com/spreadsheets/d/..."

  # Generate map with healthcare overlay
  python generate-map.py --district ky-6 --overlay healthcare

  # Generate map with multiple overlays
  python generate-map.py --district ky-6 --overlays healthcare,distilleries

  # List available overlays
  python generate-map.py --list-overlays

  # Validate district boundaries
  python generate-map.py --validate-district ky-6
        """
    )

    # Main actions (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--district', help='District to generate map for (e.g., ky-6)')
    action_group.add_argument('--create-overlay', help='Create new overlay branch')
    action_group.add_argument('--list-overlays', action='store_true', help='List available overlays')
    action_group.add_argument('--validate-district', help='Validate district boundary files')

    # Overlay options
    parser.add_argument('--overlay', help='Single overlay to include in map')
    parser.add_argument('--overlays', help='Comma-separated list of overlays to include')
    parser.add_argument('--sheet-url', help='Google Sheets URL for overlay data')
    parser.add_argument('--description', default='', help='Description for new overlay')

    # Output options
    parser.add_argument('--output', help='Output path for generated map')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle different actions
    if args.list_overlays:
        return list_overlays()

    elif args.validate_district:
        return validate_district_boundaries(args.validate_district)

    elif args.create_overlay:
        if not args.sheet_url:
            print("❌ --sheet-url required when creating overlay")
            return False
        return create_overlay(args.create_overlay, args.sheet_url, args.description)

    elif args.district:
        # Determine overlays to include
        overlays = []
        if args.overlay:
            overlays = [args.overlay]
        elif args.overlays:
            overlays = [o.strip() for o in args.overlays.split(',')]

        return generate_map(args.district, overlays, args.output)

    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)