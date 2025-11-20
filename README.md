# MediaCleaner for Unraid

A web-based application to identify, compare, and delete duplicate movie files on your Unraid server.

## Features

- 🎬 **Automatic Duplicate Detection** - Scans your movie library and identifies folders with multiple versions of the same film
- 📊 **Visual Comparison** - Side-by-side comparison with thumbnails, resolution, bitrate, and codec information
- 🗑️ **Safe Deletion** - Dry-run mode to preview deletions before committing
- 💾 **Smart Caching** - SQLite database prevents re-scanning unchanged files
- 🚀 **Fast Processing** - Concurrent FFmpeg operations for efficient thumbnail generation
- 🐳 **Docker Ready** - Easy deployment on Unraid with Docker

## Tech Stack

- **Backend**: Python 3.11 + FastAPI
- **Frontend**: React 18 + Vite + Tailwind CSS
- **Media Processing**: FFmpeg + FFprobe
- **Database**: SQLite
- **Deployment**: Docker with multi-stage build

## Project Structure

```
Movielemming/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # API endpoints
│   │   ├── core/
│   │   │   └── config.py          # Configuration settings
│   │   ├── models/
│   │   │   └── database.py        # SQLite models
│   │   ├── services/
│   │   │   ├── scanner.py         # File scanning logic
│   │   │   └── media_processor.py # FFmpeg/FFprobe wrapper
│   │   └── main.py                # FastAPI application
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/            # React components
│   │   │   ├── Dashboard.jsx      # Main list view
│   │   │   ├── ComparisonModal.jsx # File comparison
│   │   │   ├── FileCard.jsx       # Individual file display
│   │   │   ├── ScanProgress.jsx   # Progress indicator
│   │   │   └── DeleteConfirmation.jsx # Deletion workflow
│   │   ├── services/
│   │   │   └── api.js             # API client
│   │   ├── App.jsx                # Main app component
│   │   └── main.jsx               # Entry point
│   ├── package.json
│   └── vite.config.js
├── public/
│   └── thumbnails/                 # Generated thumbnails
├── data/                           # SQLite database location
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Backend API Endpoints

### Core Endpoints

- `POST /api/scan` - Start a new duplicate scan
- `GET /api/status/{job_id}` - Get scan progress
- `GET /api/duplicates` - Get all duplicate groups
- `POST /api/delete` - Delete selected files (supports dry-run)
- `GET /api/health` - Health check

### Static Files

- `/thumbnails/{filename}` - Serve generated thumbnails

## Installation & Usage

### Local Development

1. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Install FFmpeg** (if not already installed):
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

3. **Run the application**:
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Access the API**:
- API docs: http://localhost:8000/docs
- API endpoints: http://localhost:8000/api/*

### Docker Deployment (Recommended for Unraid)

1. **Build the Docker image**:
```bash
docker build -t mediacleaner:latest .
```

2. **Run with docker-compose**:
```bash
docker-compose up -d
```

3. **Access the application**:
- Web UI: http://localhost:8000
- API docs: http://localhost:8000/docs

### Unraid Installation

1. Install via **Community Applications** (once published) or manually:
   - Add a new Docker container
   - Repository: `yourusername/mediacleaner:latest`
   - Port: `8000` → `8000`
   - Volume: `/mnt/user/movies` → `/data` (your movie library path)

2. Access at `http://[unraid-ip]:8000`

## Configuration

Create a `.env` file in the backend directory (see `.env.example`):

```env
# Application
DEBUG=false

# Paths
DATA_DIR=/data
THUMBNAIL_DIR=/app/public/thumbnails
DATABASE_PATH=/app/data/mediacleaner.db

# Media Processing
MIN_FILE_SIZE_MB=300
THUMBNAIL_TIMESTAMP_RATIO=0.25
THUMBNAIL_WIDTH=640

# Performance
MAX_CONCURRENT_SCANS=4
MAX_CONCURRENT_THUMBNAILS=2
```

## How It Works

### Phase 1: Scanning
1. Walks through the mounted `/data` directory
2. Identifies folders containing multiple video files (>300MB)
3. Groups files by parent folder

### Phase 2: Metadata Extraction
1. Uses FFprobe to extract video metadata (resolution, bitrate, codec, duration)
2. Generates thumbnails at 25% of video duration using FFmpeg
3. Stores results in SQLite database for caching

### Phase 3: User Interface
1. Dashboard shows duplicate movie groups with statistics
2. Comparison modal displays side-by-side file information with thumbnails
3. Toggle files to KEEP or DELETE with smart defaults
4. Three-step deletion workflow with dry-run safety check
5. Real-time scan progress monitoring
6. Responsive design for desktop and mobile

## API Usage Examples

### Start a Scan

```bash
curl -X POST http://localhost:8000/api/scan
```

Response:
```json
{
  "job_id": 1,
  "status": "pending",
  "message": "Scan job 1 started"
}
```

### Check Scan Status

```bash
curl http://localhost:8000/api/status/1
```

Response:
```json
{
  "job_id": 1,
  "status": "running",
  "total_files": 50,
  "processed_files": 25,
  "duplicates_found": 10,
  "progress_percent": 50.0
}
```

### Get Duplicates

```bash
curl http://localhost:8000/api/duplicates
```

Response:
```json
[
  {
    "title": "Avatar",
    "folder_path": "/data/movies/Avatar",
    "file_count": 3,
    "files": [
      {
        "file_path": "/data/movies/Avatar/Avatar.2160p.mkv",
        "file_name": "Avatar.2160p.mkv",
        "file_size_mb": 15360.5,
        "width": 3840,
        "height": 2160,
        "resolution": "3840x2160",
        "bitrate_kbps": 25000,
        "codec": "hevc",
        "duration_seconds": 9720.5,
        "thumbnail_path": "abc123.jpg"
      }
    ]
  }
]
```

### Delete Files (Dry Run)

```bash
curl -X POST http://localhost:8000/api/delete \
  -H "Content-Type: application/json" \
  -d '{
    "file_paths": ["/data/movies/Avatar/Avatar.720p.mkv"],
    "dry_run": true
  }'
```

Response:
```json
{
  "success": true,
  "deleted_count": 1,
  "space_freed_mb": 2048.5,
  "errors": [],
  "dry_run": true
}
```

## Safety Features

- **Dry Run Mode**: Preview deletions without actually removing files
- **Error Handling**: Corrupt videos won't crash the application
- **Database Caching**: Avoid re-scanning unchanged files
- **Concurrent Limits**: Prevent CPU overload during processing

## Development Status

- ✅ Phase 1: Backend scaffold, scanner, metadata extraction
- ✅ Phase 2: FFmpeg thumbnail generation, API endpoints
- ✅ Phase 3: React frontend (Dashboard + Comparison UI)
- ✅ Phase 4: Delete functionality with safety checks (dry-run mode)
- ✅ Phase 5: Docker containerization with multi-stage build

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file for details

## Security Warning

⚠️ **Important**: This application can permanently delete files. Always:
- Use dry-run mode first
- Backup important files
- Double-check selections before deletion
- Test on a small subset before bulk operations

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check the API documentation at `/docs`
- Review logs for error messages
