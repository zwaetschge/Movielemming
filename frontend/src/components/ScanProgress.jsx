function ScanProgress({ status }) {
  const { progress_percent, processed_files, total_files, duplicates_found, status: jobStatus } = status;

  return (
    <div className="bg-primary-50 border-b border-primary-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
            <span className="font-medium text-primary-900">
              {jobStatus === 'pending' ? 'Starting scan...' : 'Scanning in progress'}
            </span>
          </div>
          <span className="text-sm text-primary-700">
            {processed_files} / {total_files} files processed
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-primary-200 rounded-full h-2.5">
          <div
            className="bg-primary-600 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${progress_percent}%` }}
          ></div>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-6 mt-2 text-sm text-primary-700">
          <span>{progress_percent.toFixed(1)}% complete</span>
          {duplicates_found > 0 && (
            <span>{duplicates_found} duplicate groups found</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default ScanProgress;
