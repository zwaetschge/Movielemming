import { formatFileSize } from '../services/api';
import FileCard from './FileCard';

function ComparisonModal({ group, selections, onToggleSelection, onClose, onProcessDeletion }) {
  // Calculate statistics
  const filesToDelete = group.files.filter(f => selections[f.file_path] === 'delete');
  const spaceToFree = filesToDelete.reduce((sum, f) => sum + f.file_size_mb, 0);

  // Sort files by size (largest first)
  const sortedFiles = [...group.files].sort((a, b) => b.file_size_mb - a.file_size_mb);

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      ></div>

      {/* Modal */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="flex items-center justify-center min-h-screen p-4">
          <div className="relative bg-white rounded-lg shadow-xl w-full max-w-7xl max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{group.title}</h2>
                <p className="text-sm text-gray-500 mt-1">{group.folder_path}</p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            {/* File Grid */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {sortedFiles.map((file) => (
                  <FileCard
                    key={file.file_path}
                    file={file}
                    selection={selections[file.file_path]}
                    onToggleSelection={(action) => onToggleSelection(file.file_path, action)}
                  />
                ))}
              </div>
            </div>

            {/* Footer Action Bar */}
            <div className="border-t border-gray-200 p-6 bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-600">
                    {filesToDelete.length} file(s) marked for deletion
                  </div>
                  {spaceToFree > 0 && (
                    <div className="text-lg font-semibold text-green-600 mt-1">
                      Freeing up {formatFileSize(spaceToFree)}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  <button onClick={onClose} className="btn btn-secondary">
                    Cancel
                  </button>
                  <button
                    onClick={onProcessDeletion}
                    disabled={filesToDelete.length === 0}
                    className="btn btn-danger disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Process Deletion Queue
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ComparisonModal;
