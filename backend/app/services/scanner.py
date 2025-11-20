"""
File scanning module to identify duplicate movies
"""
import os
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


class MediaScanner:
    """Scans directories for duplicate media files"""

    def __init__(self, root_dir: Path = None):
        self.root_dir = root_dir or settings.DATA_DIR
        self.min_file_size_bytes = settings.MIN_FILE_SIZE_MB * 1024 * 1024
        self.video_extensions = tuple(settings.VIDEO_EXTENSIONS)

    def is_video_file(self, file_path: Path) -> bool:
        """Check if file is a video based on extension and size"""
        if not file_path.is_file():
            return False

        # Check extension
        if not file_path.suffix.lower() in self.video_extensions:
            return False

        # Check minimum file size to exclude samples/trailers
        try:
            file_size = file_path.stat().st_size
            if file_size < self.min_file_size_bytes:
                logger.debug(f"Skipping {file_path.name} - too small ({file_size / 1024 / 1024:.1f} MB)")
                return False
        except OSError as e:
            logger.warning(f"Could not stat file {file_path}: {e}")
            return False

        return True

    def get_file_info(self, file_path: Path) -> Dict:
        """Get basic file information without FFprobe"""
        stat = file_path.stat()
        return {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_size_mb": stat.st_size / (1024 * 1024),
            "file_modified": datetime.fromtimestamp(stat.st_mtime),
        }

    def scan_for_duplicates(self) -> Dict[str, List[Dict]]:
        """
        Scan directory tree and group files by parent folder.
        Returns folders that contain more than one video file.

        Returns:
            Dict with folder paths as keys, list of file info as values
        """
        logger.info(f"Starting scan of {self.root_dir}")

        if not self.root_dir.exists():
            logger.error(f"Root directory does not exist: {self.root_dir}")
            raise FileNotFoundError(f"Directory not found: {self.root_dir}")

        # Dictionary to group files by parent folder
        folder_groups: Dict[str, List[Path]] = {}

        # Walk through directory tree
        try:
            for root, dirs, files in os.walk(self.root_dir):
                root_path = Path(root)

                # Find all video files in this directory
                video_files = []
                for file in files:
                    file_path = root_path / file
                    if self.is_video_file(file_path):
                        video_files.append(file_path)

                # Only interested in folders with multiple videos
                if len(video_files) > 1:
                    folder_key = str(root_path)
                    folder_groups[folder_key] = video_files
                    logger.info(f"Found {len(video_files)} videos in: {root_path.name}")

        except Exception as e:
            logger.error(f"Error during scan: {e}")
            raise

        logger.info(f"Scan complete. Found {len(folder_groups)} folders with duplicates")

        # Convert to output format with basic file info
        result = {}
        for folder_path, files in folder_groups.items():
            folder_path_obj = Path(folder_path)
            result[folder_path] = {
                "folder_name": folder_path_obj.name,
                "folder_path": folder_path,
                "file_count": len(files),
                "files": [self.get_file_info(f) for f in files]
            }

        return result

    def get_all_video_files(self) -> List[Path]:
        """Get a flat list of all video files in the root directory"""
        video_files = []

        try:
            for root, dirs, files in os.walk(self.root_dir):
                root_path = Path(root)
                for file in files:
                    file_path = root_path / file
                    if self.is_video_file(file_path):
                        video_files.append(file_path)
        except Exception as e:
            logger.error(f"Error getting video files: {e}")
            raise

        logger.info(f"Found {len(video_files)} total video files")
        return video_files

    def count_total_videos(self) -> int:
        """Count total number of video files"""
        return len(self.get_all_video_files())
