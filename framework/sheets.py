"""
Google Sheets Integration

Handles reading overlay data from Google Sheets with standard format:
name, address1, address2, city, county, state, zip, notes
"""

import pandas as pd
import requests
from typing import Dict, List, Optional
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


class GoogleSheetsReader:
    """
    Reads overlay data from Google Sheets.

    Supports public Google Sheets via CSV export URL or
    authenticated access via Google Sheets API.
    """

    def __init__(self, api_credentials: Optional[str] = None):
        """
        Initialize Google Sheets reader.

        Args:
            api_credentials: Optional path to Google API credentials JSON
        """
        self.api_credentials = api_credentials
        self.required_columns = [
            'name', 'address1', 'city', 'county', 'state', 'zip'
        ]
        self.optional_columns = ['address2', 'notes']

    def read_sheet_from_url(self, sheet_url: str, sheet_name: str = None) -> pd.DataFrame:
        """
        Read Google Sheet data from a sharing URL.

        Args:
            sheet_url: Google Sheets sharing URL
            sheet_name: Optional specific sheet name/tab

        Returns:
            DataFrame with overlay data

        Raises:
            ValueError: If URL is invalid or data cannot be read
        """
        try:
            # Convert sharing URL to CSV export URL
            csv_url = self._convert_to_csv_url(sheet_url, sheet_name)

            logger.info(f"Reading Google Sheet: {csv_url}")

            # Read CSV data
            df = pd.read_csv(csv_url)

            # Validate and clean data
            df = self._validate_and_clean_data(df)

            logger.info(f"Successfully read {len(df)} rows from Google Sheet")
            return df

        except Exception as e:
            logger.error(f"Error reading Google Sheet: {e}")
            raise ValueError(f"Could not read Google Sheet: {e}")

    def _convert_to_csv_url(self, sheet_url: str, sheet_name: str = None) -> str:
        """
        Convert Google Sheets sharing URL to CSV export URL.

        Args:
            sheet_url: Original Google Sheets URL
            sheet_name: Optional sheet name for specific tab

        Returns:
            CSV export URL
        """
        # Extract sheet ID from URL
        if '/d/' in sheet_url:
            sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        elif 'spreadsheets/d/' in sheet_url:
            sheet_id = sheet_url.split('spreadsheets/d/')[1].split('/')[0]
        else:
            raise ValueError("Invalid Google Sheets URL format")

        # Build CSV export URL
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

        # Add sheet name if specified
        if sheet_name:
            csv_url += f"&gid={sheet_name}"

        return csv_url

    def _validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean overlay data.

        Args:
            df: Raw DataFrame from Google Sheets

        Returns:
            Cleaned and validated DataFrame

        Raises:
            ValueError: If required columns are missing
        """
        # Convert column names to lowercase and strip whitespace
        df.columns = df.columns.str.lower().str.strip()

        # Check for required columns
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Add optional columns if missing
        for col in self.optional_columns:
            if col not in df.columns:
                df[col] = ''

        # Clean data
        df = df.copy()

        # Remove completely empty rows
        df = df.dropna(how='all')

        # Remove rows where name is empty (required field)
        df = df[df['name'].notna() & (df['name'].str.strip() != '')]

        # Clean string fields
        string_columns = ['name', 'address1', 'address2', 'city', 'county', 'state', 'notes']
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace('nan', '')

        # Clean ZIP codes (handle both string and numeric)
        if 'zip' in df.columns:
            df['zip'] = df['zip'].astype(str).str.strip()
            df['zip'] = df['zip'].str.replace('.0', '')  # Remove .0 from numeric ZIP codes
            df['zip'] = df['zip'].replace('nan', '')

        # Standardize state to uppercase
        if 'state' in df.columns:
            df['state'] = df['state'].str.upper()

        # Create full address field for geocoding
        df['full_address'] = self._build_full_address(df)

        return df

    def _build_full_address(self, df: pd.DataFrame) -> pd.Series:
        """
        Build full address string for geocoding.

        Args:
            df: DataFrame with address components

        Returns:
            Series with full addresses
        """
        addresses = []

        for _, row in df.iterrows():
            address_parts = []

            # Add address1 (required)
            if row.get('address1'):
                address_parts.append(str(row['address1']))

            # Add address2 if present
            if row.get('address2') and str(row['address2']).strip():
                address_parts.append(str(row['address2']))

            # Add city (required)
            if row.get('city'):
                address_parts.append(str(row['city']))

            # Add state (required)
            if row.get('state'):
                address_parts.append(str(row['state']))

            # Add ZIP if present
            if row.get('zip') and str(row['zip']).strip():
                address_parts.append(str(row['zip']))

            addresses.append(', '.join(address_parts))

        return pd.Series(addresses)

    def validate_sheet_format(self, sheet_url: str, sheet_name: str = None) -> Dict[str, any]:
        """
        Validate that a Google Sheet has the correct format.

        Args:
            sheet_url: Google Sheets sharing URL
            sheet_name: Optional specific sheet name/tab

        Returns:
            Dictionary with validation results
        """
        try:
            # Try to read the sheet
            df = self.read_sheet_from_url(sheet_url, sheet_name)

            validation = {
                'valid': True,
                'row_count': len(df),
                'columns_found': list(df.columns),
                'required_columns_present': all(col in df.columns for col in self.required_columns),
                'sample_data': df.head(3).to_dict('records') if len(df) > 0 else [],
                'issues': []
            }

            # Check for potential issues
            if len(df) == 0:
                validation['issues'].append("No data rows found")

            # Check for empty required fields
            for col in self.required_columns:
                if col in df.columns:
                    empty_count = df[col].isna().sum() + (df[col] == '').sum()
                    if empty_count > 0:
                        validation['issues'].append(f"{empty_count} empty values in required column '{col}'")

            return validation

        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'row_count': 0,
                'columns_found': [],
                'required_columns_present': False,
                'sample_data': [],
                'issues': [f"Could not read sheet: {e}"]
            }

    def create_sample_sheet_data(self) -> pd.DataFrame:
        """
        Create sample data for Google Sheets template.

        Returns:
            DataFrame with sample overlay data
        """
        sample_data = [
            {
                'name': 'Example Hospital',
                'address1': '123 Main Street',
                'address2': 'Suite 100',
                'city': 'Lexington',
                'county': 'Fayette',
                'state': 'KY',
                'zip': '40507',
                'notes': 'Major medical center'
            },
            {
                'name': 'Community Health Center',
                'address1': '456 Oak Avenue',
                'address2': '',
                'city': 'Georgetown',
                'county': 'Scott',
                'state': 'KY',
                'zip': '40324',
                'notes': 'Primary care facility'
            },
            {
                'name': 'Rural Clinic',
                'address1': '789 County Road 15',
                'address2': '',
                'city': 'Irvine',
                'county': 'Estill',
                'state': 'KY',
                'zip': '40336',
                'notes': 'Serves rural communities'
            }
        ]

        return pd.DataFrame(sample_data)


class OverlayDataProcessor:
    """
    Processes overlay data for map generation.
    """

    def __init__(self, sheets_reader: GoogleSheetsReader):
        """
        Initialize overlay data processor.

        Args:
            sheets_reader: Configured GoogleSheetsReader instance
        """
        self.sheets_reader = sheets_reader

    def process_overlay_data(self, sheet_url: str, overlay_name: str,
                           sheet_name: str = None) -> Dict[str, any]:
        """
        Process overlay data from Google Sheets.

        Args:
            sheet_url: Google Sheets sharing URL
            overlay_name: Name of the overlay (e.g., 'healthcare', 'distilleries')
            sheet_name: Optional specific sheet name/tab

        Returns:
            Dictionary with processed overlay data
        """
        try:
            # Read data from sheet
            df = self.sheets_reader.read_sheet_from_url(sheet_url, sheet_name)

            # Process the data
            overlay_data = {
                'name': overlay_name,
                'source': sheet_url,
                'last_updated': pd.Timestamp.now().isoformat(),
                'record_count': len(df),
                'data': df.to_dict('records')
            }

            logger.info(f"Processed {len(df)} records for {overlay_name} overlay")

            return overlay_data

        except Exception as e:
            logger.error(f"Error processing overlay data: {e}")
            raise