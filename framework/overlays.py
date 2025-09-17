"""
Overlay Management System

Handles Git branch-based overlay management and overlay processing.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class OverlayManager:
    """
    Manages Git branch-based overlays for different data types.
    """

    def __init__(self, repo_path: str = "."):
        """
        Initialize overlay manager.

        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = Path(repo_path).resolve()
        self.overlays_dir = self.repo_path / "overlays"
        self.overlays_dir.mkdir(exist_ok=True)

    def create_overlay_branch(self, overlay_name: str, description: str = "") -> str:
        """
        Create a new Git branch for an overlay.

        Args:
            overlay_name: Name of the overlay (e.g., 'healthcare', 'distilleries')
            description: Optional description of the overlay

        Returns:
            Name of the created branch

        Raises:
            RuntimeError: If Git operations fail
        """
        branch_name = f"overlay/{overlay_name}"

        try:
            # Check if branch already exists
            result = subprocess.run(
                ["git", "branch", "--list", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                logger.warning(f"Branch {branch_name} already exists")
                return branch_name

            # Create new branch from main
            subprocess.run(
                ["git", "checkout", "main"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            # Create overlay configuration
            overlay_config = {
                "name": overlay_name,
                "description": description,
                "branch": branch_name,
                "created": "auto-generated",
                "data_schema": {
                    "required_columns": ["name", "address1", "city", "county", "state", "zip"],
                    "optional_columns": ["address2", "notes"]
                }
            }

            config_path = self.overlays_dir / f"{overlay_name}.json"
            with open(config_path, 'w') as f:
                json.dump(overlay_config, f, indent=2)

            # Commit the new overlay configuration
            subprocess.run(
                ["git", "add", str(config_path)],
                cwd=self.repo_path,
                check=True
            )

            subprocess.run(
                ["git", "commit", "-m", f"Create {overlay_name} overlay branch"],
                cwd=self.repo_path,
                check=True
            )

            logger.info(f"Created overlay branch: {branch_name}")
            return branch_name

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e}")
            raise RuntimeError(f"Failed to create overlay branch: {e}")

    def switch_to_overlay(self, overlay_name: str) -> str:
        """
        Switch to an overlay branch.

        Args:
            overlay_name: Name of the overlay

        Returns:
            Name of the branch switched to

        Raises:
            RuntimeError: If Git operations fail
        """
        branch_name = f"overlay/{overlay_name}"

        try:
            subprocess.run(
                ["git", "checkout", branch_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            logger.info(f"Switched to overlay branch: {branch_name}")
            return branch_name

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to switch to overlay branch {branch_name}: {e}")
            raise RuntimeError(f"Failed to switch to overlay branch: {e}")

    def list_overlays(self) -> List[Dict[str, str]]:
        """
        List all available overlay branches.

        Returns:
            List of overlay information dictionaries
        """
        try:
            # Get all overlay branches
            result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            overlays = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if 'overlay/' in line:
                    # Remove asterisk and remotes/origin/ prefix
                    branch_name = line.replace('*', '').strip()
                    if branch_name.startswith('remotes/origin/'):
                        branch_name = branch_name.replace('remotes/origin/', '')

                    overlay_name = branch_name.split('overlay/')[-1]

                    # Try to load overlay configuration
                    config_path = self.overlays_dir / f"{overlay_name}.json"
                    description = ""
                    if config_path.exists():
                        try:
                            with open(config_path, 'r') as f:
                                config = json.load(f)
                                description = config.get('description', '')
                        except:
                            pass

                    overlays.append({
                        'name': overlay_name,
                        'branch': branch_name,
                        'description': description
                    })

            return overlays

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list overlay branches: {e}")
            return []

    def get_current_overlay(self) -> Optional[str]:
        """
        Get the currently active overlay.

        Returns:
            Name of current overlay or None if on main branch
        """
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            current_branch = result.stdout.strip()

            if current_branch.startswith('overlay/'):
                return current_branch.split('overlay/')[-1]

            return None

        except subprocess.CalledProcessError:
            return None

    def save_overlay_data(self, overlay_name: str, data: Dict, sheet_url: str = "") -> str:
        """
        Save overlay data to the current overlay branch.

        Args:
            overlay_name: Name of the overlay
            data: Overlay data dictionary
            sheet_url: Source Google Sheets URL

        Returns:
            Path to saved data file

        Raises:
            RuntimeError: If not on correct overlay branch
        """
        current_overlay = self.get_current_overlay()
        if current_overlay != overlay_name:
            raise RuntimeError(f"Must be on overlay/{overlay_name} branch to save data")

        # Save data file
        data_path = self.overlays_dir / f"{overlay_name}_data.json"

        # Add metadata
        data_with_metadata = {
            "overlay_name": overlay_name,
            "source_sheet": sheet_url,
            "last_updated": data.get('last_updated'),
            "record_count": data.get('record_count', 0),
            "data": data.get('data', [])
        }

        with open(data_path, 'w') as f:
            json.dump(data_with_metadata, f, indent=2)

        logger.info(f"Saved overlay data: {data_path}")
        return str(data_path)

    def load_overlay_data(self, overlay_name: str) -> Optional[Dict]:
        """
        Load overlay data from the current branch.

        Args:
            overlay_name: Name of the overlay

        Returns:
            Overlay data dictionary or None if not found
        """
        data_path = self.overlays_dir / f"{overlay_name}_data.json"

        if not data_path.exists():
            logger.warning(f"Overlay data not found: {data_path}")
            return None

        try:
            with open(data_path, 'r') as f:
                data = json.load(f)

            logger.info(f"Loaded overlay data: {overlay_name}")
            return data

        except Exception as e:
            logger.error(f"Error loading overlay data: {e}")
            return None

    def commit_overlay_changes(self, overlay_name: str, message: str = "") -> bool:
        """
        Commit changes to the current overlay branch.

        Args:
            overlay_name: Name of the overlay
            message: Optional commit message

        Returns:
            True if commit successful, False otherwise
        """
        try:
            # Add all overlay-related files
            subprocess.run(
                ["git", "add", "overlays/"],
                cwd=self.repo_path,
                check=True
            )

            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if not result.stdout.strip():
                logger.info("No changes to commit")
                return True

            # Commit changes
            commit_message = message or f"Update {overlay_name} overlay data"
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_path,
                check=True
            )

            logger.info(f"Committed overlay changes: {overlay_name}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit overlay changes: {e}")
            return False

    def merge_overlay_to_main(self, overlay_name: str) -> bool:
        """
        Merge overlay branch back to main (use with caution).

        Args:
            overlay_name: Name of the overlay

        Returns:
            True if merge successful, False otherwise
        """
        branch_name = f"overlay/{overlay_name}"

        try:
            # Switch to main
            subprocess.run(
                ["git", "checkout", "main"],
                cwd=self.repo_path,
                check=True
            )

            # Merge overlay branch
            subprocess.run(
                ["git", "merge", branch_name, "--no-ff"],
                cwd=self.repo_path,
                check=True
            )

            logger.info(f"Merged overlay {overlay_name} to main")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to merge overlay to main: {e}")
            return False