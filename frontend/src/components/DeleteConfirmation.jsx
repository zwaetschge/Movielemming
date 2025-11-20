import { useState } from 'react';
import { formatFileSize } from '../services/api';

function DeleteConfirmation({ filesToDelete, fileSelections, selectedGroup, onClose, onExecute }) {
  const [step, setStep] = useState('confirm'); // confirm, dry-run, executing, complete
  const [dryRunResult, setDryRunResult] = useState(null);
  const [finalResult, setFinalResult] = useState(null);
  const [error, setError] = useState(null);

  // Get files that will be deleted
  const filesToDeleteDetails = selectedGroup.files.filter(f =>
    filesToDelete.includes(f.file_path)
  );

  const totalSize = filesToDeleteDetails.reduce((sum, f) => sum + f.file_size_mb, 0);

  // Run dry-run
  const handleDryRun = async () => {
    setStep('executing');
    setError(null);

    try {
      const result = await onExecute(true); // dry_run = true
      setDryRunResult(result);
      setStep('dry-run');
    } catch (err) {
      setError(err.message);
      setStep('confirm');
    }
  };

  // Execute actual deletion
  const handleActualDelete = async () => {
    setStep('executing');
    setError(null);

    try {
      const result = await onExecute(false); // dry_run = false
      setFinalResult(result);
      setStep('complete');
    } catch (err) {
      setError(err.message);
      setStep('dry-run');
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-50"></div>

      {/* Modal */}
      <div className="absolute inset-0 overflow-hidden flex items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl">
          {/* Confirm Step */}
          {step === 'confirm' && (
            <>
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-10 w-10 text-yellow-500"
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
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Confirm Deletion</h3>
                    <p className="text-gray-600 mt-1">
                      You are about to delete {filesToDelete.length} file(s)
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-6 max-h-96 overflow-y-auto">
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <div className="text-sm text-gray-600">Total space to be freed</div>
                  <div className="text-2xl font-bold text-green-600">
                    {formatFileSize(totalSize)}
                  </div>
                </div>

                <h4 className="font-medium text-gray-900 mb-3">Files to be deleted:</h4>
                <ul className="space-y-2">
                  {filesToDeleteDetails.map((file) => (
                    <li key={file.file_path} className="text-sm">
                      <div className="flex items-start gap-2">
                        <svg
                          className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-gray-900 truncate">
                            {file.file_name}
                          </div>
                          <div className="text-gray-500">
                            {file.resolution || 'Unknown'} • {formatFileSize(file.file_size_mb)}
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>

                {error && (
                  <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                )}
              </div>

              <div className="p-6 border-t border-gray-200 bg-gray-50">
                <div className="flex items-center justify-end gap-3">
                  <button onClick={onClose} className="btn btn-secondary">
                    Cancel
                  </button>
                  <button onClick={handleDryRun} className="btn btn-primary">
                    Run Dry-Run Test
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Executing Step */}
          {step === 'executing' && (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Processing...</p>
            </div>
          )}

          {/* Dry-Run Result Step */}
          {step === 'dry-run' && dryRunResult && (
            <>
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-10 w-10 text-blue-500"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Dry-Run Complete</h3>
                    <p className="text-gray-600 mt-1">
                      No files were deleted. This was a test run.
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-6">
                <div className="bg-blue-50 rounded-lg p-4 mb-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-blue-700">Files to delete</div>
                      <div className="text-2xl font-bold text-blue-900">
                        {dryRunResult.deleted_count}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-blue-700">Space to free</div>
                      <div className="text-2xl font-bold text-blue-900">
                        {formatFileSize(dryRunResult.space_freed_mb)}
                      </div>
                    </div>
                  </div>
                </div>

                {dryRunResult.errors && dryRunResult.errors.length > 0 && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                    <h4 className="font-medium text-red-900 mb-2">Errors:</h4>
                    <ul className="text-sm text-red-800 space-y-1">
                      {dryRunResult.errors.map((err, i) => (
                        <li key={i}>{err}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-sm text-yellow-800">
                    <strong>Warning:</strong> This action cannot be undone. The files will be
                    permanently deleted from your system.
                  </p>
                </div>

                {error && (
                  <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                )}
              </div>

              <div className="p-6 border-t border-gray-200 bg-gray-50">
                <div className="flex items-center justify-end gap-3">
                  <button onClick={onClose} className="btn btn-secondary">
                    Cancel
                  </button>
                  <button
                    onClick={handleActualDelete}
                    className="btn btn-danger"
                    disabled={dryRunResult.errors && dryRunResult.errors.length > 0}
                  >
                    Confirm & Delete Files
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Complete Step */}
          {step === 'complete' && finalResult && (
            <>
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-10 w-10 text-green-500"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Deletion Complete</h3>
                    <p className="text-gray-600 mt-1">
                      Files have been successfully deleted
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-6">
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-green-700">Files deleted</div>
                      <div className="text-2xl font-bold text-green-900">
                        {finalResult.deleted_count}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-green-700">Space freed</div>
                      <div className="text-2xl font-bold text-green-900">
                        {formatFileSize(finalResult.space_freed_mb)}
                      </div>
                    </div>
                  </div>
                </div>

                {finalResult.errors && finalResult.errors.length > 0 && (
                  <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
                    <h4 className="font-medium text-red-900 mb-2">Some errors occurred:</h4>
                    <ul className="text-sm text-red-800 space-y-1">
                      {finalResult.errors.map((err, i) => (
                        <li key={i}>{err}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div className="p-6 border-t border-gray-200 bg-gray-50">
                <button onClick={onClose} className="btn btn-primary w-full">
                  Done
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default DeleteConfirmation;
