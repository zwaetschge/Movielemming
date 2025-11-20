"""
Database models for caching scan results
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pathlib import Path

Base = declarative_base()


class MediaFile(Base):
    """Represents a scanned media file with metadata"""

    __tablename__ = "media_files"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, unique=True, nullable=False, index=True)
    folder_path = Column(String, nullable=False, index=True)
    folder_name = Column(String, nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_size_mb = Column(Float, nullable=False)

    # Video metadata
    width = Column(Integer)
    height = Column(Integer)
    resolution = Column(String)  # e.g., "1920x1080"
    bitrate_kbps = Column(Integer)
    codec = Column(String)
    duration_seconds = Column(Float)

    # Thumbnail
    thumbnail_path = Column(String)
    thumbnail_generated = Column(Boolean, default=False)

    # Metadata
    last_scanned = Column(DateTime, default=datetime.utcnow)
    file_modified = Column(DateTime)
    scan_error = Column(String, nullable=True)  # Store any errors during scanning

    def __repr__(self):
        return f"<MediaFile {self.file_name} ({self.resolution})>"


class ScanJob(Base):
    """Tracks scan job status"""

    __tablename__ = "scan_jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, nullable=False)  # pending, running, completed, failed
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    duplicates_found = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

    def __repr__(self):
        return f"<ScanJob {self.id} - {self.status}>"


# Database initialization
def init_db(db_path: Path):
    """Initialize the database"""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal


def get_db_session(SessionLocal):
    """Get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
