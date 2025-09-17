"""
Map Generation Engine

Generates interactive congressional district maps with overlays using Folium.
"""

import folium
from folium import plugins
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MapGenerator:
    """
    Generates interactive congressional district maps with overlays.
    """

    def __init__(self, district_path: str, template_path: str = None):
        """
        Initialize map generator.

        Args:
            district_path: Path to district configuration directory
            template_path: Optional path to custom HTML template
        """
        self.district_path = Path(district_path)
        self.template_path = Path(template_path) if template_path else None

        # Load district configuration
        self.district_config = self._load_district_config()

    def _load_district_config(self) -> Dict:
        """Load district configuration from config.json."""
        config_path = self.district_path / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"District config not found: {config_path}")

        with open(config_path, 'r') as f:
            return json.load(f)

    def create_base_map(self) -> folium.Map:
        """
        Create base map with district boundaries.

        Returns:
            Folium map instance with district boundaries
        """
        # Get district center and bounds
        center = self.district_config.get('center', [38.0, -84.5])
        zoom = self.district_config.get('default_zoom', 9)

        # Create base map
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )

        # Add district boundary
        self._add_district_boundary(m)

        # Add county boundaries for context (if available)
        self._add_county_boundaries(m)

        return m

    def _add_district_boundary(self, m: folium.Map):
        """Add district boundary to map."""
        boundary_file = self.district_path / "boundaries" / "district.geojson"

        if boundary_file.exists():
            # Load and add district boundary
            folium.GeoJson(
                str(boundary_file),
                style_function=lambda x: {
                    'fillColor': 'rgba(59, 130, 246, 0.1)',
                    'color': '#3B82F6',
                    'weight': 3,
                    'fillOpacity': 0.1
                },
                popup=folium.Popup(self._create_district_popup(), max_width=400)
            ).add_to(m)

            logger.info("Added district boundary to map")
        else:
            logger.warning(f"District boundary file not found: {boundary_file}")

    def _add_county_boundaries(self, m: folium.Map):
        """Add county boundaries to map for context."""
        counties_file = self.district_path / "boundaries" / "counties.geojson"

        if counties_file.exists():
            folium.GeoJson(
                str(counties_file),
                style_function=lambda x: {
                    'color': '#9CA3AF',
                    'weight': 1,
                    'fillOpacity': 0
                }
            ).add_to(m)

            logger.info("Added county boundaries to map")

    def _create_district_popup(self) -> str:
        """Create popup content for district boundary."""
        config = self.district_config

        return f"""
        <div style="font-family: 'Segoe UI', sans-serif; padding: 15px; min-width: 250px;">
            <div style="background: linear-gradient(135deg, #3B82F6 0%, #1E40AF 100%);
                         color: white; padding: 12px; margin: -15px -15px 15px -15px;
                         border-radius: 8px 8px 0 0;">
                <h3 style="margin: 0; font-size: 16px; font-weight: 600;">
                    {config.get('name', 'Congressional District')}
                </h3>
            </div>
            <div style="color: #374151; font-size: 14px; line-height: 1.5;">
                <p style="margin: 0 0 10px 0;">
                    <strong>Representative:</strong> {config.get('representative', 'N/A')}
                </p>
                <p style="margin: 0 0 10px 0;">
                    <strong>Population:</strong> {config.get('population', 'N/A')}
                </p>
                <p style="margin: 0;">
                    <strong>Counties:</strong> {config.get('counties_description', 'Multiple counties')}
                </p>
            </div>
        </div>
        """

    def add_overlay(self, m: folium.Map, overlay_data: Dict, overlay_config: Dict = None):
        """
        Add an overlay to the map.

        Args:
            m: Folium map instance
            overlay_data: Overlay data from JSON
            overlay_config: Optional overlay-specific configuration
        """
        overlay_name = overlay_data.get('overlay_name', 'Unknown')
        data_records = overlay_data.get('data', [])

        logger.info(f"Adding {overlay_name} overlay with {len(data_records)} records")

        # Default overlay configuration
        default_config = {
            'marker_color': '#DC2626',
            'marker_icon': '📍',
            'marker_size': 12
        }

        if overlay_config:
            default_config.update(overlay_config)

        # Add markers for each data point
        for record in data_records:
            self._add_overlay_marker(m, record, default_config, overlay_name)

    def _add_overlay_marker(self, m: folium.Map, record: Dict, config: Dict, overlay_name: str):
        """Add a single overlay marker to the map."""
        # Skip if no coordinates
        if not record.get('latitude') or not record.get('longitude'):
            return

        try:
            lat = float(record['latitude'])
            lng = float(record['longitude'])
        except (ValueError, TypeError):
            logger.warning(f"Invalid coordinates for {record.get('name', 'Unknown')}")
            return

        # Create popup content
        popup_html = self._create_overlay_popup(record, overlay_name)

        # Create marker icon
        icon_html = f"""
        <div style="
            background: {config['marker_color']};
            color: white;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 3px solid white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-size: 12px;
        ">{config['marker_icon']}</div>
        """

        icon = folium.DivIcon(
            html=icon_html,
            icon_size=(24, 24),
            icon_anchor=(12, 12)
        )

        # Add marker to map
        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_html, max_width=350),
            icon=icon
        ).add_to(m)

    def _create_overlay_popup(self, record: Dict, overlay_name: str) -> str:
        """Create popup content for overlay markers."""
        name = record.get('name', 'Unknown')

        # Build address
        address_parts = []
        if record.get('address1'):
            address_parts.append(record['address1'])
        if record.get('address2'):
            address_parts.append(record['address2'])
        if record.get('city'):
            address_parts.append(record['city'])
        if record.get('state'):
            address_parts.append(record['state'])
        if record.get('zip'):
            address_parts.append(record['zip'])

        address = ', '.join(address_parts)
        notes = record.get('notes', '')

        # District status
        in_district = record.get('in_district', None)
        status_color = '#059669' if in_district else '#DC2626'
        status_text = '✓ In District' if in_district else '✗ Outside District'

        popup_html = f"""
        <div style="font-family: 'Segoe UI', sans-serif; min-width: 300px;">
            <h4 style="color: #DC2626; margin: 0 0 8px 0;">
                {overlay_name.title()}: {name}
            </h4>
            <p style="margin: 0 0 8px 0; font-size: 12px;">
                <strong>Address:</strong> {address}
            </p>
        """

        if in_district is not None:
            popup_html += f"""
            <p style="margin: 0 0 8px 0; font-size: 12px;">
                <strong>Status:</strong>
                <span style="color: {status_color};">{status_text}</span>
            </p>
            """

        if notes:
            popup_html += f"""
            <p style="margin: 0; font-size: 11px; color: #6B7280;">
                {notes}
            </p>
            """

        popup_html += "</div>"

        return popup_html

    def add_search_controls(self, m: folium.Map):
        """Add search and control panel to map."""
        district_bounds = self.district_config.get('bounds', {})
        district_name = self.district_config.get('name', 'Congressional District')

        control_html = f"""
        <div id="map-controls" style="
            position: fixed; top: 20px; left: 20px; width: 400px;
            background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(20px);
            border-radius: 16px; z-index: 9999; font-family: 'Segoe UI', sans-serif;
            padding: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        ">
            <div style="border-bottom: 1px solid rgba(59, 130, 246, 0.2); padding-bottom: 20px; margin-bottom: 20px;">
                <h3 style="margin: 0; color: #1E40AF; font-size: 20px; font-weight: 700;">
                    {district_name}
                </h3>
                <p style="margin: 0; color: #6B7280; font-size: 13px;">
                    Interactive District Map
                </p>
            </div>

            <div style="margin-bottom: 20px;">
                <input type="text" id="address-search" placeholder="Search your address..."
                       style="width: 100%; padding: 14px 16px; border: 2px solid #E5E7EB;
                       border-radius: 12px; font-size: 14px; box-sizing: border-box;">
                <div style="display: flex; gap: 12px; margin-top: 12px;">
                    <button onclick="searchAddress()" style="
                        flex: 1; padding: 12px 18px; background: #3B82F6; color: white;
                        border: none; border-radius: 10px; cursor: pointer; font-size: 14px;
                    ">Search</button>
                    <button onclick="resetMap()" style="
                        flex: 1; padding: 12px 18px; background: #6B7280; color: white;
                        border: none; border-radius: 10px; cursor: pointer; font-size: 14px;
                    ">Reset</button>
                </div>
                <div id="search-message" style="margin-top: 8px; padding: 8px; border-radius: 8px; font-size: 12px;"></div>
            </div>
        </div>

        <script>
            var districtBounds = {json.dumps(district_bounds)};
            var mapInstance = null;
            var searchMarker = null;

            function findMapInstance() {{
                if (window.map) return window.map;
                var maps = document.querySelectorAll('.folium-map');
                if (maps.length > 0) {{
                    var mapId = maps[0].id;
                    return window[mapId];
                }}
                return null;
            }}

            function searchAddress() {{
                var address = document.getElementById('address-search').value.trim();
                if (!address) return;

                if (!mapInstance) mapInstance = findMapInstance();
                if (!mapInstance) return;

                fetch('https://nominatim.openstreetmap.org/search?format=json&q=' +
                      encodeURIComponent(address) + '&limit=1&countrycodes=us')
                    .then(response => response.json())
                    .then(data => {{
                        if (data.length > 0) {{
                            var lat = parseFloat(data[0].lat);
                            var lon = parseFloat(data[0].lon);

                            if (searchMarker) mapInstance.removeLayer(searchMarker);

                            searchMarker = L.marker([lat, lon])
                                .bindPopup('Search Result: ' + data[0].display_name)
                                .addTo(mapInstance);

                            mapInstance.panTo([lat, lon]);
                            showMessage('✅ Address found', '#059669');
                        }} else {{
                            showMessage('❌ Address not found', '#DC2626');
                        }}
                    }})
                    .catch(() => showMessage('❌ Search failed', '#DC2626'));
            }}

            function resetMap() {{
                if (!mapInstance) mapInstance = findMapInstance();
                if (mapInstance && searchMarker) {{
                    mapInstance.removeLayer(searchMarker);
                    searchMarker = null;
                }}
                document.getElementById('address-search').value = '';
                showMessage('🔄 Map reset', '#6B7280');
            }}

            function showMessage(text, color) {{
                var div = document.getElementById('search-message');
                div.innerHTML = '<span style="color: ' + color + ';">' + text + '</span>';
                setTimeout(() => div.innerHTML = '', 3000);
            }}

            document.getElementById('address-search').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') searchAddress();
            }});

            window.addEventListener('load', function() {{
                setTimeout(() => mapInstance = findMapInstance(), 500);
            }});
        </script>
        """

        m.get_root().html.add_child(folium.Element(control_html))

    def generate_map(self, overlays: List[str] = None, output_path: str = None) -> str:
        """
        Generate complete map with specified overlays.

        Args:
            overlays: List of overlay names to include
            output_path: Path for output HTML file

        Returns:
            Path to generated map file
        """
        try:
            # Create base map
            m = self.create_base_map()

            # Add overlays if specified
            if overlays:
                from .overlays import OverlayManager
                overlay_manager = OverlayManager()

                for overlay_name in overlays:
                    overlay_data = overlay_manager.load_overlay_data(overlay_name)
                    if overlay_data:
                        self.add_overlay(m, overlay_data)
                        logger.info(f"Added {overlay_name} overlay")
                    else:
                        logger.warning(f"Could not load {overlay_name} overlay data")

            # Add search controls
            self.add_search_controls(m)

            # Determine output path
            if not output_path:
                district_name = self.district_config.get('short_name', 'district')
                overlay_suffix = '-'.join(overlays) if overlays else 'base'
                output_path = f"output/{district_name}-{overlay_suffix}.html"

            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Save map
            m.save(str(output_file))

            logger.info(f"Generated map: {output_file}")
            return str(output_file)

        except Exception as e:
            logger.error(f"Error generating map: {e}")
            raise