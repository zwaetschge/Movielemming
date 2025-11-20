"""
API routes for MediaCleaner
"""
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.database import MediaFile, ScanJob, get_db_session
from ..services.scanner import MediaScanner
from ..services.media_processor import MediaProcessor

logger = logging.getLogger(__name__)

router = APIRouter()

# Global state for scan jobs
current_scan_job: Optional[Dict] = None
media_processor = MediaProcessor()


# Pydantic models for API
class ScanResponse(BaseModel):
    job_id: int
    status: str
    message: str


class ScanStatus(BaseModel):
    job_id: int
    status: str
    total_files: int
    processed_files: int
    duplicates_found: int
    progress_percent: float
    error_message: Optional[str] = None


class FileMetadata(BaseModel):
    file_path: str
    file_name: str
    file_size_mb: float
    width: Optional[int]
    height: Optional[int]
    resolution: Optional[str]
    bitrate_kbps: Optional[int]
    codec: Optional[str]
    duration_seconds: Optional[float]
    thumbnail_path: Optional[str]
    scan_error: Optional[str]


class DuplicateGroup(BaseModel):
    title: str
    folder_path: str
    file_count: int
    files: List[FileMetadata]


class DeleteRequest(BaseModel):
    file_paths: List[str]
    dry_run: bool = True


class DeleteResponse(BaseModel):
    success: bool
    deleted_count: int
    space_freed_mb: float
    errors: List[str]
    dry_run: bool


async def scan_background_task(job_id: int, db_path: Path):
    """Background task to scan for duplicates and process metadata"""
    from ..models.database import init_db

    global current_scan_job

    # Initialize database connection for this thread
    engine, SessionLocal = init_db(db_path)
    db = SessionLocal()

    try:
        # Update job status
        job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
        job.status = "running"
        db.commit()

        logger.info(f"Starting scan job {job_id}")

        # Phase 1: Scan for duplicate folders
        scanner = MediaScanner(settings.DATA_DIR)
        duplicate_groups = scanner.scan_for_duplicates()

        total_files = sum(group["file_count"] for group in duplicate_groups.values())
        job.total_files = total_files
        job.duplicates_found = len(duplicate_groups)
        db.commit()

        logger.info(f"Found {len(duplicate_groups)} duplicate groups with {total_files} total files")

        # Phase 2: Process each file with FFprobe and FFmpeg
        processed = 0

        for folder_path, group_data in duplicate_groups.items():
            folder_path_obj = Path(folder_path)

            # Process files with limited concurrency
            semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_SCANS)

            async def process_file_with_semaphore(file_info: Dict):
                async with semaphore:
                    file_path = Path(file_info["file_path"])

                    # Check if already in database and up to date
                    existing = db.query(MediaFile).filter(
                        MediaFile.file_path == str(file_path)
                    ).first()

                    if existing and existing.file_modified == file_info["file_modified"]:
                        logger.debug(f"Using cached data for {file_path.name}")
                        return existing

                    # Process with FFprobe and FFmpeg
                    try:
                        metadata = await media_processor.process_file_complete(file_path)

                        # Create or update database entry
                        if existing:
                            media_file = existing
                        else:
                            media_file = MediaFile()

                        media_file.file_path = str(file_path)
                        media_file.folder_path = str(folder_path_obj)
                        media_file.folder_name = folder_path_obj.name
                        media_file.file_name = file_path.name
                        media_file.file_size_mb = file_info["file_size_mb"]
                        media_file.file_modified = file_info["file_modified"]

                        media_file.width = metadata.get("width")
                        media_file.height = metadata.get("height")
                        media_file.resolution = metadata.get("resolution")
                        media_file.bitrate_kbps = metadata.get("bitrate_kbps")
                        media_file.codec = metadata.get("codec")
                        media_file.duration_seconds = metadata.get("duration_seconds")
                        media_file.thumbnail_path = metadata.get("thumbnail_path")
                        media_file.thumbnail_generated = metadata.get("thumbnail_path") is not None
                        media_file.scan_error = metadata.get("error")
                        media_file.last_scanned = datetime.utcnow()

                        if not existing:
                            db.add(media_file)

                        db.commit()
                        logger.info(f"Processed {file_path.name}")

                        return media_file

                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        # Still save to database with error
                        if not existing:
                            media_file = MediaFile(
                                file_path=str(file_path),
                                folder_path=str(folder_path_obj),
                                folder_name=folder_path_obj.name,
                                file_name=file_path.name,
                                file_size_mb=file_info["file_size_mb"],
                                file_modified=file_info["file_modified"],
                                scan_error=str(e)
                            )
                            db.add(media_file)
                            db.commit()
                        return None

            # Process all files in this group
            tasks = [process_file_with_semaphore(f) for f in group_data["files"]]
            await asyncio.gather(*tasks)

            processed += len(group_data["files"])
            job.processed_files = processed
            db.commit()

            logger.info(f"Progress: {processed}/{total_files} files processed")

        # Mark job as complete
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

        current_scan_job = None
        logger.info(f"Scan job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Scan job {job_id} failed: {e}")
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()
        current_scan_job = None

    finally:
        db.close()


@router.post("/scan", response_model=ScanResponse)
async def start_scan(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """Start a new scan for duplicate files"""
    global current_scan_job

    # Check if scan already running
    if current_scan_job and current_scan_job["status"] == "running":
        raise HTTPException(status_code=409, detail="Scan already in progress")

    # Create new scan job
    job = ScanJob(status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)

    current_scan_job = {"id": job.id, "status": "running"}

    # Start background task
    background_tasks.add_task(scan_background_task, job.id, settings.DATABASE_PATH)

    return ScanResponse(
        job_id=job.id,
        status="pending",
        message=f"Scan job {job.id} started"
    )


@router.get("/status/{job_id}", response_model=ScanStatus)
async def get_scan_status(job_id: int, db: Session = Depends(get_db_session)):
    """Get status of a scan job"""
    job = db.query(ScanJob).filter(ScanJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    progress = 0.0
    if job.total_files > 0:
        progress = (job.processed_files / job.total_files) * 100

    return ScanStatus(
        job_id=job.id,
        status=job.status,
        total_files=job.total_files,
        processed_files=job.processed_files,
        duplicates_found=job.duplicates_found,
        progress_percent=round(progress, 2),
        error_message=job.error_message
    )


@router.get("/duplicates", response_model=List[DuplicateGroup])
async def get_duplicates(db: Session = Depends(get_db_session)):
    """Get all duplicate groups from the most recent scan"""
    # Get all folders that have multiple files
    folders = db.query(MediaFile.folder_path, MediaFile.folder_name).distinct().all()

    duplicate_groups = []

    for folder_path, folder_name in folders:
        files = db.query(MediaFile).filter(
            MediaFile.folder_path == folder_path
        ).all()

        if len(files) > 1:  # Only folders with duplicates
            file_list = [
                FileMetadata(
                    file_path=f.file_path,
                    file_name=f.file_name,
                    file_size_mb=round(f.file_size_mb, 2),
                    width=f.width,
                    height=f.height,
                    resolution=f.resolution,
                    bitrate_kbps=f.bitrate_kbps,
                    codec=f.codec,
                    duration_seconds=f.duration_seconds,
                    thumbnail_path=f.thumbnail_path,
                    scan_error=f.scan_error
                )
                for f in files
            ]

            duplicate_groups.append(
                DuplicateGroup(
                    title=folder_name,
                    folder_path=folder_path,
                    file_count=len(files),
                    files=file_list
                )
            )

    # Sort by title
    duplicate_groups.sort(key=lambda x: x.title)

    return duplicate_groups


@router.post("/delete", response_model=DeleteResponse)
async def delete_files(request: DeleteRequest, db: Session = Depends(get_db_session)):
    """Delete specified files (or perform dry run)"""
    deleted_count = 0
    space_freed = 0.0
    errors = []

    for file_path_str in request.file_paths:
        file_path = Path(file_path_str)

        try:
            # Check if file exists
            if not file_path.exists():
                errors.append(f"File not found: {file_path_str}")
                continue

            # Get file size before deletion
            file_size_mb = file_path.stat().st_size / (1024 * 1024)

            if not request.dry_run:
                # Actually delete the file
                file_path.unlink()
                logger.info(f"Deleted: {file_path_str}")

                # Remove from database
                db.query(MediaFile).filter(MediaFile.file_path == file_path_str).delete()
                db.commit()

            deleted_count += 1
            space_freed += file_size_mb

        except Exception as e:
            error_msg = f"Error deleting {file_path_str}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    return DeleteResponse(
        success=len(errors) == 0,
        deleted_count=deleted_count,
        space_freed_mb=round(space_freed, 2),
        errors=errors,
        dry_run=request.dry_run
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "app": settings.APP_NAME}
