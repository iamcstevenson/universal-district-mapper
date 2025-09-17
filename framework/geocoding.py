"""
Address Geocoding

Converts addresses to coordinates and validates they fall within district boundaries.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import logging

logger = logging.getLogger(__name__)


class AddressGeocoder:
    """
    Geocodes addresses and validates they fall within district boundaries.
    """

    def __init__(self, user_agent: str = "congressional-district-mapper"):
        """
        Initialize address geocoder.

        Args:
            user_agent: User agent string for geocoding service
        """
        self.geocoder = Nominatim(user_agent=user_agent)
        self.cache = {}  # Simple in-memory cache for repeated addresses

    def geocode_address(self, address: str, timeout: int = 10) -> Optional[Tuple[float, float]]:
        """
        Geocode a single address to lat/lng coordinates.

        Args:
            address: Full address string
            timeout: Timeout in seconds for geocoding request

        Returns:
            Tuple of (latitude, longitude) or None if geocoding fails
        """
        # Check cache first
        if address in self.cache:
            return self.cache[address]

        try:
            # Add rate limiting to be respectful to the service
            time.sleep(1)

            logger.debug(f"Geocoding address: {address}")

            location = self.geocoder.geocode(address, timeout=timeout)

            if location:
                coords = (location.latitude, location.longitude)
                self.cache[address] = coords
                logger.debug(f"Successfully geocoded: {address} -> {coords}")
                return coords
            else:
                logger.warning(f"Could not geocode address: {address}")
                self.cache[address] = None
                return None

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.error(f"Geocoding service error for {address}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error geocoding {address}: {e}")
            return None

    def geocode_dataframe(self, df: pd.DataFrame, address_column: str = 'full_address') -> pd.DataFrame:
        """
        Geocode all addresses in a DataFrame.

        Args:
            df: DataFrame containing addresses
            address_column: Name of column containing full addresses

        Returns:
            DataFrame with added latitude and longitude columns
        """
        logger.info(f"Geocoding {len(df)} addresses...")

        df = df.copy()
        df['latitude'] = None
        df['longitude'] = None
        df['geocoding_status'] = 'pending'

        successful_count = 0
        failed_count = 0

        for idx, row in df.iterrows():
            address = row.get(address_column, '')

            if not address or pd.isna(address):
                df.loc[idx, 'geocoding_status'] = 'missing_address'
                failed_count += 1
                continue

            coords = self.geocode_address(str(address))

            if coords:
                df.loc[idx, 'latitude'] = coords[0]
                df.loc[idx, 'longitude'] = coords[1]
                df.loc[idx, 'geocoding_status'] = 'success'
                successful_count += 1
            else:
                df.loc[idx, 'geocoding_status'] = 'failed'
                failed_count += 1

            # Progress logging
            if (idx + 1) % 10 == 0:
                logger.info(f"Geocoded {idx + 1}/{len(df)} addresses...")

        logger.info(f"Geocoding complete: {successful_count} successful, {failed_count} failed")

        return df

    def validate_district_membership(self, df: pd.DataFrame, boundary_processor) -> pd.DataFrame:
        """
        Validate which geocoded addresses fall within the district boundary.

        Args:
            df: DataFrame with latitude and longitude columns
            boundary_processor: DistrictBoundaryProcessor instance

        Returns:
            DataFrame with added in_district column
        """
        logger.info("Validating district membership for geocoded addresses...")

        df = df.copy()
        df['in_district'] = False
        df['boundary_check_status'] = 'pending'

        validated_count = 0

        for idx, row in df.iterrows():
            if pd.isna(row.get('latitude')) or pd.isna(row.get('longitude')):
                df.loc[idx, 'boundary_check_status'] = 'no_coordinates'
                continue

            try:
                lat = float(row['latitude'])
                lng = float(row['longitude'])

                in_district = boundary_processor.point_in_district(lat, lng)

                df.loc[idx, 'in_district'] = in_district
                df.loc[idx, 'boundary_check_status'] = 'checked'
                validated_count += 1

            except Exception as e:
                logger.error(f"Error checking boundary for row {idx}: {e}")
                df.loc[idx, 'boundary_check_status'] = 'error'

        logger.info(f"District validation complete: {validated_count} addresses checked")

        # Summary statistics
        in_district_count = df['in_district'].sum()
        out_district_count = len(df[df['in_district'] == False]) - len(df[df['boundary_check_status'] != 'checked'])

        logger.info(f"Results: {in_district_count} in district, {out_district_count} outside district")

        return df

    def create_geocoding_report(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Create a report summarizing geocoding and validation results.

        Args:
            df: DataFrame with geocoding and validation results

        Returns:
            Dictionary with summary statistics
        """
        total_records = len(df)

        # Geocoding statistics
        geocoding_success = len(df[df['geocoding_status'] == 'success'])
        geocoding_failed = len(df[df['geocoding_status'] == 'failed'])
        missing_address = len(df[df['geocoding_status'] == 'missing_address'])

        # District validation statistics
        in_district = len(df[df['in_district'] == True])
        out_district = len(df[(df['in_district'] == False) & (df['boundary_check_status'] == 'checked')])
        not_validated = len(df[df['boundary_check_status'] != 'checked'])

        # Failed geocoding examples
        failed_addresses = df[df['geocoding_status'] == 'failed']['full_address'].head(5).tolist()

        # Out of district examples
        out_district_examples = df[df['in_district'] == False].head(5)[['name', 'full_address']].to_dict('records')

        report = {
            'total_records': total_records,
            'geocoding': {
                'successful': geocoding_success,
                'failed': geocoding_failed,
                'missing_address': missing_address,
                'success_rate': round((geocoding_success / total_records) * 100, 1) if total_records > 0 else 0
            },
            'district_validation': {
                'in_district': in_district,
                'out_district': out_district,
                'not_validated': not_validated,
                'validation_rate': round(((in_district + out_district) / total_records) * 100, 1) if total_records > 0 else 0
            },
            'examples': {
                'failed_geocoding': failed_addresses,
                'out_of_district': out_district_examples
            }
        }

        return report

    def export_geocoded_data(self, df: pd.DataFrame, output_path: str,
                           include_failed: bool = True) -> str:
        """
        Export geocoded data to CSV file.

        Args:
            df: DataFrame with geocoded data
            output_path: Path for output CSV file
            include_failed: Whether to include failed geocoding attempts

        Returns:
            Path to exported file
        """
        export_df = df.copy()

        if not include_failed:
            export_df = export_df[export_df['geocoding_status'] == 'success']

        export_df.to_csv(output_path, index=False)

        logger.info(f"Exported {len(export_df)} records to {output_path}")

        return output_path