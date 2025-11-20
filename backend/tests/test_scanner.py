"""
Basic tests for the scanner module
"""
import pytest
from pathlib import Path
import tempfile
import os

from app.services.scanner import MediaScanner


def create_test_video(directory: Path, filename: str, size_mb: int = 400):
    """Create a dummy video file for testing"""
    file_path = directory / filename
    # Create a file of specified size
    with open(file_path, 'wb') as f:
        f.write(b'0' * (size_mb * 1024 * 1024))
    return file_path


def test_scanner_initialization():
    """Test that scanner initializes correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        scanner = MediaScanner(Path(tmpdir))
        assert scanner.root_dir == Path(tmpdir)
        assert scanner.min_file_size_bytes == 300 * 1024 * 1024


def test_is_video_file():
    """Test video file detection"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        scanner = MediaScanner(tmpdir_path)

        # Create a valid video file
        video_file = create_test_video(tmpdir_path, "movie.mkv", 400)
        assert scanner.is_video_file(video_file) == True

        # Create a file that's too small
        small_file = create_test_video(tmpdir_path, "sample.mkv", 100)
        assert scanner.is_video_file(small_file) == False

        # Create a non-video file
        text_file = tmpdir_path / "readme.txt"
        text_file.write_text("Not a video")
        assert scanner.is_video_file(text_file) == False


def test_scan_for_duplicates():
    """Test duplicate detection"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a folder with duplicate movies
        movie_dir = tmpdir_path / "Avatar"
        movie_dir.mkdir()

        create_test_video(movie_dir, "Avatar.2160p.mkv", 500)
        create_test_video(movie_dir, "Avatar.1080p.mkv", 400)

        # Create a folder with single movie (should be ignored)
        single_dir = tmpdir_path / "Inception"
        single_dir.mkdir()
        create_test_video(single_dir, "Inception.1080p.mkv", 450)

        # Scan for duplicates
        scanner = MediaScanner(tmpdir_path)
        duplicates = scanner.scan_for_duplicates()

        # Should find only the Avatar folder
        assert len(duplicates) == 1
        assert str(movie_dir) in duplicates
        assert duplicates[str(movie_dir)]["file_count"] == 2


def test_get_file_info():
    """Test file info extraction"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        scanner = MediaScanner(tmpdir_path)

        video_file = create_test_video(tmpdir_path, "test.mkv", 500)
        info = scanner.get_file_info(video_file)

        assert info["file_name"] == "test.mkv"
        assert info["file_path"] == str(video_file)
        assert info["file_size_mb"] == pytest.approx(500, rel=0.1)
        assert "file_modified" in info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
