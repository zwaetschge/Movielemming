# MediaCleaner Frontend

React-based web interface for MediaCleaner duplicate movie manager.

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API communication

## Features

- **Dashboard** - Browse duplicate movie groups
- **Comparison View** - Side-by-side file comparison with thumbnails
- **Smart Selection** - Auto-suggests keeping largest file
- **Scan Progress** - Real-time scan status updates
- **Safe Deletion** - Dry-run mode before actual deletion
- **Responsive Design** - Works on desktop and mobile

## Development

### Prerequisites

- Node.js 18+ and npm

### Setup

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000` and will proxy API requests to the backend at `http://localhost:8000`.

### Build for Production

```bash
npm run build
```

The production build will be output to `dist/`.

### Lint

```bash
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.jsx          # Main list view
│   │   ├── ComparisonModal.jsx    # Side-by-side comparison
│   │   ├── FileCard.jsx           # Individual file display
│   │   ├── ScanProgress.jsx       # Scan status indicator
│   │   └── DeleteConfirmation.jsx # Deletion workflow
│   ├── services/
│   │   └── api.js                 # API client and helpers
│   ├── App.jsx                    # Main app component
│   ├── main.jsx                   # Entry point
│   └── index.css                  # Global styles
├── public/
├── index.html
├── vite.config.js
├── tailwind.config.js
└── package.json
```

## API Integration

The frontend communicates with the backend API through the `mediaCleanerAPI` service:

- `startScan()` - Initiate a new scan
- `getScanStatus(jobId)` - Poll scan progress
- `getDuplicates()` - Fetch duplicate groups
- `deleteFiles(paths, dryRun)` - Delete selected files

## Components

### Dashboard
- Displays list of duplicate movie groups
- Shows statistics (total groups, files, size)
- Clickable cards to open comparison view

### ComparisonModal
- Full-screen modal with file grid
- Shows thumbnails, metadata, and file details
- Toggle KEEP/DELETE for each file
- Displays space savings

### FileCard
- Individual file display with thumbnail
- Video metadata (resolution, bitrate, codec, duration)
- KEEP/DELETE toggle buttons
- Error handling for corrupt files

### ScanProgress
- Real-time progress bar
- Files processed counter
- Duplicate groups found counter

### DeleteConfirmation
- Three-step deletion workflow:
  1. Confirm - Review files to delete
  2. Dry-run - Test without deleting
  3. Execute - Actual deletion with confirmation

## Environment Variables

Create `.env` file (optional):

```env
VITE_API_URL=/api
```

## Building with Docker

The frontend is automatically built as part of the Docker multi-stage build:

```bash
# From project root
docker build -t mediacleaner .
```

The React app is served by FastAPI as static files.
