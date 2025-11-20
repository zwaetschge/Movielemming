"""
Media processing module using FFmpeg and FFprobe
"""
import asyncio
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import hashlib

from ..core.config import settings

logger = logging.getLogger(__name__)


class MediaProcessor:
    """Handles FFprobe metadata extraction and FFmpeg thumbnail generation"""

    def __init__(self):
        self.ffprobe_path = settings.FFPROBE_PATH
        self.ffmpeg_path = settings.FFMPEG_PATH
        self.thumbnail_dir = settings.THUMBNAIL_DIR
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)

        # Thread pool for CPU-intensive operations
        self.executor = ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_THUMBNAILS)

    def _run_ffprobe(self, file_path: Path) -> Optional[Dict]:
        """
        Run ffprobe to extract video metadata.
        Returns dict with video info or None if failed.
        """
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(file_path)
            ]

            logger.debug(f"Running ffprobe on {file_path.name}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )

            if result.returncode != 0:
                logger.error(f"FFprobe failed for {file_path}: {result.stderr}")
                return None

            return json.loads(result.stdout)

        except subprocess.TimeoutExpired:
            logger.error(f"FFprobe timeout for {file_path}")
            return None
        except Exception as e:
            logger.error(f"FFprobe error for {file_path}: {e}")
            return None

    def extract_metadata(self, file_path: Path) -> Dict:
        """
        Extract video metadata using ffprobe.

        Returns:
            Dict with width, height, resolution, bitrate, codec, duration
        """
        probe_data = self._run_ffprobe(file_path)

        metadata = {
            "width": None,
            "height": None,
            "resolution": None,
            "bitrate_kbps": None,
            "codec": None,
            "duration_seconds": None,
            "error": None
        }

        if not probe_data:
            metadata["error"] = "Failed to probe video file"
            return metadata

        try:
            # Extract video stream info
            video_stream = None
            for stream in probe_data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break

            if not video_stream:
                metadata["error"] = "No video stream found"
                return metadata

            # Extract dimensions
            metadata["width"] = video_stream.get("width")
            metadata["height"] = video_stream.get("height")

            if metadata["width"] and metadata["height"]:
                metadata["resolution"] = f"{metadata['width']}x{metadata['height']}"

            # Extract codec
            metadata["codec"] = video_stream.get("codec_name")

            # Extract duration (try stream first, then format)
            duration = video_stream.get("duration")
            if not duration:
                format_info = probe_data.get("format", {})
                duration = format_info.get("duration")

            if duration:
                try:
                    metadata["duration_seconds"] = float(duration)
                except (ValueError, TypeError):
                    pass

            # Extract bitrate (try format first for overall bitrate)
            format_info = probe_data.get("format", {})
            bitrate = format_info.get("bit_rate")

            if bitrate:
                try:
                    metadata["bitrate_kbps"] = int(bitrate) // 1000
                except (ValueError, TypeError):
                    pass

            logger.info(f"Extracted metadata for {file_path.name}: {metadata['resolution']} @ {metadata['bitrate_kbps']} kbps")

        except Exception as e:
            logger.error(f"Error parsing ffprobe data for {file_path}: {e}")
            metadata["error"] = str(e)

        return metadata

    async def extract_metadata_async(self, file_path: Path) -> Dict:
        """Async wrapper for metadata extraction"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.extract_metadata, file_path)

    def _generate_thumbnail_sync(self, file_path: Path, duration_seconds: float) -> Optional[str]:
        """
        Generate a thumbnail at 25% of video duration (synchronous).

        Returns:
            Path to thumbnail relative to thumbnail directory, or None if failed
        """
        try:
            # Calculate timestamp (25% of duration)
            timestamp = duration_seconds * settings.THUMBNAIL_TIMESTAMP_RATIO

            # Generate unique filename based on file path
            file_hash = hashlib.md5(str(file_path).encode()).hexdigest()
            thumbnail_filename = f"{file_hash}.jpg"
            thumbnail_path = self.thumbnail_dir / thumbnail_filename

            # Skip if already exists
            if thumbnail_path.exists():
                logger.debug(f"Thumbnail already exists for {file_path.name}")
                return thumbnail_filename

            # FFmpeg command to extract frame
            cmd = [
                self.ffmpeg_path,
                "-ss", str(timestamp),  # Seek to timestamp
                "-i", str(file_path),  # Input file
                "-vframes", "1",  # Extract 1 frame
                "-vf", f"scale={settings.THUMBNAIL_WIDTH}:-1",  # Scale to width, maintain aspect ratio
                "-q:v", "2",  # Quality (2-5 is good, 2 is high quality)
                "-y",  # Overwrite output file
                str(thumbnail_path)
            ]

            logger.debug(f"Generating thumbnail for {file_path.name} at {timestamp:.1f}s")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg thumbnail generation failed for {file_path}: {result.stderr}")
                return None

            if thumbnail_path.exists():
                logger.info(f"Generated thumbnail for {file_path.name}")
                return thumbnail_filename
            else:
                logger.error(f"Thumbnail file not created for {file_path}")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"FFmpeg timeout for {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error generating thumbnail for {file_path}: {e}")
            return None

    async def generate_thumbnail(self, file_path: Path, duration_seconds: float) -> Optional[str]:
        """
        Async thumbnail generation using thread pool.

        Returns:
            Relative path to thumbnail or None if failed
        """
        if not duration_seconds or duration_seconds <= 0:
            logger.warning(f"Invalid duration for {file_path}, cannot generate thumbnail")
            return None

        loop = asyncio.get_event_loop()
        try:
            thumbnail_path = await loop.run_in_executor(
                self.executor,
                self._generate_thumbnail_sync,
                file_path,
                duration_seconds
            )
            return thumbnail_path
        except Exception as e:
            logger.error(f"Async thumbnail generation error for {file_path}: {e}")
            return None

    async def process_file_complete(self, file_path: Path) -> Dict:
        """
        Complete processing: extract metadata AND generate thumbnail.

        Returns:
            Dict with all metadata including thumbnail path
        """
        # First extract metadata
        metadata = await self.extract_metadata_async(file_path)

        # Then generate thumbnail if we have duration
        if metadata.get("duration_seconds") and not metadata.get("error"):
            thumbnail = await self.generate_thumbnail(
                file_path,
                metadata["duration_seconds"]
            )
            metadata["thumbnail_path"] = thumbnail
        else:
            metadata["thumbnail_path"] = None

        return metadata

    def cleanup_thumbnails(self):
        """Remove all generated thumbnails"""
        try:
            for thumb in self.thumbnail_dir.glob("*.jpg"):
                thumb.unlink()
            logger.info("Cleaned up all thumbnails")
        except Exception as e:
            logger.error(f"Error cleaning up thumbnails: {e}")
