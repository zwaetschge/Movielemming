import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Methods
export const mediaCleanerAPI = {
  // Start a new scan
  startScan: async () => {
    const response = await api.post('/scan');
    return response.data;
  },

  // Get scan status
  getScanStatus: async (jobId) => {
    const response = await api.get(`/status/${jobId}`);
    return response.data;
  },

  // Get all duplicate groups
  getDuplicates: async () => {
    const response = await api.get('/duplicates');
    return response.data;
  },

  // Delete files
  deleteFiles: async (filePaths, dryRun = true) => {
    const response = await api.post('/delete', {
      file_paths: filePaths,
      dry_run: dryRun,
    });
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

// Helper to get thumbnail URL
export const getThumbnailUrl = (thumbnailPath) => {
  if (!thumbnailPath) return null;
  return `/thumbnails/${thumbnailPath}`;
};

// Helper to format file size
export const formatFileSize = (sizeMb) => {
  if (sizeMb >= 1024) {
    return `${(sizeMb / 1024).toFixed(2)} GB`;
  }
  return `${sizeMb.toFixed(2)} MB`;
};

// Helper to format resolution
export const getResolutionLabel = (resolution) => {
  if (!resolution) return 'Unknown';

  const resMap = {
    '3840x2160': '4K UHD',
    '2560x1440': '2K QHD',
    '1920x1080': '1080p FHD',
    '1280x720': '720p HD',
    '854x480': '480p SD',
    '640x480': '480p',
  };

  return resMap[resolution] || resolution;
};

// Helper to format bitrate
export const formatBitrate = (bitrateKbps) => {
  if (!bitrateKbps) return 'Unknown';

  if (bitrateKbps >= 1000) {
    return `${(bitrateKbps / 1000).toFixed(1)} Mbps`;
  }
  return `${bitrateKbps} Kbps`;
};

// Helper to format duration
export const formatDuration = (seconds) => {
  if (!seconds) return 'Unknown';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
};

export default api;
