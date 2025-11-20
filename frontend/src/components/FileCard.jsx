import {
  getThumbnailUrl,
  formatFileSize,
  getResolutionLabel,
  formatBitrate,
  formatDuration,
} from '../services/api';

function FileCard({ file, selection, onToggleSelection }) {
  const thumbnailUrl = getThumbnailUrl(file.thumbnail_path);
  const isKeep = selection === 'keep';
  const isDelete = selection === 'delete';

  return (
    <div
      className={`card overflow-hidden transition-all ${
        isDelete ? 'ring-2 ring-red-500' : isKeep ? 'ring-2 ring-green-500' : ''
      }`}
    >
      {/* Thumbnail */}
      <div className="relative bg-gray-900 aspect-video">
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={file.file_name}
            className="w-full h-full object-contain"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'flex';
            }}
          />
        ) : null}

        {/* Fallback / Error State */}
        <div
          className="absolute inset-0 flex items-center justify-center bg-gray-800"
          style={{ display: thumbnailUrl ? 'none' : 'flex' }}
        >
          {file.scan_error ? (
            <div className="text-center p-4">
              <svg
                className="mx-auto h-12 w-12 text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <p className="text-red-300 text-sm mt-2">Error scanning file</p>
            </div>
          ) : (
            <div className="text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
              <p className="text-gray-400 text-sm mt-2">No preview</p>
            </div>
          )}
        </div>

        {/* Selection Badge */}
        {isKeep && (
          <div className="absolute top-3 right-3 bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium">
            KEEP
          </div>
        )}
        {isDelete && (
          <div className="absolute top-3 right-3 bg-red-500 text-white px-3 py-1 rounded-full text-sm font-medium">
            DELETE
          </div>
        )}
      </div>

      {/* File Information */}
      <div className="p-4">
        <h4 className="font-medium text-gray-900 truncate" title={file.file_name}>
          {file.file_name}
        </h4>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-3 mt-3 text-sm">
          <div>
            <div className="text-gray-500">Resolution</div>
            <div className="font-medium text-gray-900">
              {file.resolution ? getResolutionLabel(file.resolution) : 'Unknown'}
            </div>
          </div>

          <div>
            <div className="text-gray-500">File Size</div>
            <div className="font-medium text-gray-900">
              {formatFileSize(file.file_size_mb)}
            </div>
          </div>

          <div>
            <div className="text-gray-500">Bitrate</div>
            <div className="font-medium text-gray-900">
              {formatBitrate(file.bitrate_kbps)}
            </div>
          </div>

          <div>
            <div className="text-gray-500">Codec</div>
            <div className="font-medium text-gray-900 uppercase">
              {file.codec || 'Unknown'}
            </div>
          </div>

          {file.duration_seconds && (
            <div className="col-span-2">
              <div className="text-gray-500">Duration</div>
              <div className="font-medium text-gray-900">
                {formatDuration(file.duration_seconds)}
              </div>
            </div>
          )}
        </div>

        {/* Error Message */}
        {file.scan_error && (
          <div className="mt-3 text-xs text-red-600 bg-red-50 p-2 rounded">
            {file.scan_error}
          </div>
        )}

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-2 mt-4">
          <button
            onClick={() => onToggleSelection('keep')}
            className={`btn ${
              isKeep
                ? 'btn-success'
                : 'bg-green-50 text-green-700 hover:bg-green-100 border border-green-300'
            }`}
          >
            Keep
          </button>
          <button
            onClick={() => onToggleSelection('delete')}
            className={`btn ${
              isDelete
                ? 'btn-danger'
                : 'bg-red-50 text-red-700 hover:bg-red-100 border border-red-300'
            }`}
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

export default FileCard;
