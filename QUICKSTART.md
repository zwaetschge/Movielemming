# MediaCleaner - Quick Start Guide

Get up and running with MediaCleaner in minutes!

## Prerequisites

- Docker and Docker Compose installed
- Movie library accessible on your system
- At least 2GB RAM and 2 CPU cores available

## Quick Start with Docker (Recommended)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Movielemming
```

### 2. Configure Your Movie Path

Edit `docker-compose.yml` and change the volume path:

```yaml
volumes:
  - /YOUR/MOVIE/PATH:/data:ro  # Replace with your actual path
```

**Important**:
- Use `:ro` (read-only) for initial testing
- Remove `:ro` when you're ready to delete files

### 3. Start the Application

```bash
docker-compose up -d
```

### 4. Access the Application

Open your browser to: `http://localhost:8000`

You'll see the MediaCleaner web interface!

- **Web UI**: `http://localhost:8000` (Main interface)
- **API Documentation**: `http://localhost:8000/docs` (For developers)
- **Interactive API**: `http://localhost:8000/redoc` (Alternative API docs)

### 5. Run Your First Scan

#### Option A: Using the Web UI (Easiest!)

1. Click the **"Start New Scan"** button in the top-right corner
2. Watch the progress bar as the scan runs
3. Browse the duplicate groups when complete
4. Click on any group to compare files

#### Option B: Using the API Docs

1. Go to `http://localhost:8000/docs`
2. Click on `POST /api/scan`
3. Click "Try it out" → "Execute"
4. Note the `job_id` returned

#### Option C: Using curl

```bash
# Start a scan
curl -X POST http://localhost:8000/api/scan

# Check status (replace 1 with your job_id)
curl http://localhost:8000/api/status/1

# View duplicates
curl http://localhost:8000/api/duplicates
```

### 6. Monitor Progress

Check scan progress:
```bash
curl http://localhost:8000/api/status/1
```

Wait until `status: "completed"` before viewing results.

### 7. View Duplicates

```bash
curl http://localhost:8000/api/duplicates | jq
```

This will show all duplicate movie groups with metadata.

## Local Development (Without Docker)

### 1. Install FFmpeg

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y ffmpeg

# macOS
brew install ffmpeg

# Verify installation
ffmpeg -version
```

### 2. Install Python Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set your movie directory:
```env
DATA_DIR=/path/to/your/movies
```

### 4. Run the Application

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Run Tests

```bash
cd backend
pytest tests/ -v
```

## Unraid Installation

### Method 1: Docker Run Command

```bash
docker run -d \
  --name=mediacleaner \
  -p 8000:8000 \
  -v /mnt/user/movies:/data:ro \
  -v /mnt/user/appdata/mediacleaner/data:/app/data \
  -v /mnt/user/appdata/mediacleaner/thumbnails:/app/public/thumbnails \
  -e MIN_FILE_SIZE_MB=300 \
  -e MAX_CONCURRENT_SCANS=4 \
  --restart unless-stopped \
  mediacleaner:latest
```

### Method 2: Unraid Template (Future)

Will be available through Community Applications once published.

## Testing the Delete Function (Safely!)

### 1. Dry Run First (No Files Deleted)

```bash
curl -X POST http://localhost:8000/api/delete \
  -H "Content-Type: application/json" \
  -d '{
    "file_paths": ["/data/movies/Avatar/Avatar.720p.mkv"],
    "dry_run": true
  }'
```

Response shows what WOULD be deleted and space that would be freed.

### 2. Actual Deletion (CAREFUL!)

**⚠️ WARNING: This will permanently delete files!**

1. First, ensure you removed `:ro` from your docker-compose volume
2. Restart the container: `docker-compose restart`
3. Then run with `dry_run: false`

```bash
curl -X POST http://localhost:8000/api/delete \
  -H "Content-Type: application/json" \
  -d '{
    "file_paths": ["/data/movies/Avatar/Avatar.720p.mkv"],
    "dry_run": false
  }'
```

## Useful Commands

### View Logs

```bash
# Docker
docker-compose logs -f mediacleaner

# Docker without compose
docker logs -f mediacleaner
```

### Restart Application

```bash
docker-compose restart
```

### Stop Application

```bash
docker-compose down
```

### Update Application

```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Clear Database and Thumbnails

```bash
# Stop container
docker-compose down

# Remove data
rm -rf data/*.db public/thumbnails/*.jpg

# Restart
docker-compose up -d
```

## Troubleshooting

### "Directory not found" Error

- Check your volume path in `docker-compose.yml`
- Ensure the directory exists and is readable
- Check Docker has permission to access the path

### Scan Takes Forever

- Reduce `MAX_CONCURRENT_SCANS` in environment variables
- Reduce `MAX_CONCURRENT_THUMBNAILS` to 1
- Check system resources (CPU/RAM)

### FFmpeg Errors

- Corrupt video files will be skipped (check `scan_error` in results)
- FFmpeg is included in Docker image, no separate installation needed

### Permission Errors

- Check volume mount permissions
- Ensure Docker has read access (read-write if deleting)

### Port Already in Use

Change the port in `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Use 8080 instead
```

## What's Next?

The full web interface is now available! You can:

- ✅ Browse duplicate groups in the dashboard
- ✅ Compare files side-by-side with thumbnails
- ✅ Select files to keep or delete
- ✅ Use dry-run mode to safely test deletions
- ✅ Monitor scan progress in real-time

Future enhancements:
- Automatic quality recommendations based on bitrate/resolution
- Bulk operations across multiple folders
- Advanced filtering and sorting options

## Support

- Check logs: `docker-compose logs -f`
- View API docs: `http://localhost:8000/docs`
- Check database: `sqlite3 data/mediacleaner.db`

## Safety Tips

1. **Always start with dry-run mode**
2. **Test on a small subset first**
3. **Keep backups of important files**
4. **Use read-only mode `:ro` initially**
5. **Review scan results before deletion**

Happy cleaning! 🧹
