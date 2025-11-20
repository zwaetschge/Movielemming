import { formatFileSize } from '../services/api';

function Dashboard({ duplicates, loading, onSelectGroup, onRefresh }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading duplicates...</p>
        </div>
      </div>
    );
  }

  if (duplicates.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 className="mt-2 text-lg font-medium text-gray-900">No duplicates found</h3>
        <p className="mt-1 text-sm text-gray-500">
          Start a new scan to find duplicate movie files
        </p>
        <button
          onClick={onRefresh}
          className="mt-4 btn btn-primary"
        >
          Refresh
        </button>
      </div>
    );
  }

  // Calculate total statistics
  const totalFiles = duplicates.reduce((sum, group) => sum + group.file_count, 0);
  const totalSize = duplicates.reduce((sum, group) => {
    return sum + group.files.reduce((s, f) => s + f.file_size_mb, 0);
  }, 0);

  return (
    <div>
      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="card p-4">
          <div className="text-sm text-gray-600">Duplicate Groups</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {duplicates.length}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">Total Files</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {totalFiles}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-sm text-gray-600">Total Size</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {formatFileSize(totalSize)}
          </div>
        </div>
      </div>

      {/* Duplicate Groups List */}
      <div className="space-y-3">
        {duplicates.map((group) => (
          <DuplicateGroupCard
            key={group.folder_path}
            group={group}
            onSelect={() => onSelectGroup(group)}
          />
        ))}
      </div>
    </div>
  );
}

function DuplicateGroupCard({ group, onSelect }) {
  // Calculate potential space savings (delete all but largest)
  const sortedFiles = [...group.files].sort((a, b) => b.file_size_mb - a.file_size_mb);
  const potentialSavings = sortedFiles.slice(1).reduce((sum, f) => sum + f.file_size_mb, 0);

  // Get unique resolutions
  const resolutions = [...new Set(group.files.map(f => f.resolution).filter(Boolean))];

  return (
    <div
      className="card p-5 hover:shadow-lg transition-shadow cursor-pointer"
      onClick={onSelect}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{group.title}</h3>
          <p className="text-sm text-gray-500 mt-1">{group.folder_path}</p>

          <div className="flex items-center gap-3 mt-3">
            <span className="badge bg-primary-100 text-primary-800">
              {group.file_count} versions
            </span>

            {resolutions.length > 0 && (
              <span className="badge bg-gray-100 text-gray-700">
                {resolutions.join(', ')}
              </span>
            )}

            {potentialSavings > 0 && (
              <span className="badge bg-green-100 text-green-800">
                Save {formatFileSize(potentialSavings)}
              </span>
            )}
          </div>
        </div>

        <div className="ml-4">
          <svg
            className="h-6 w-6 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
