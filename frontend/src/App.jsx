import { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import ScanProgress from './components/ScanProgress';
import ComparisonModal from './components/ComparisonModal';
import DeleteConfirmation from './components/DeleteConfirmation';
import { mediaCleanerAPI } from './services/api';

function App() {
  // State management
  const [duplicates, setDuplicates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [scanJobId, setScanJobId] = useState(null);
  const [scanStatus, setScanStatus] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [fileSelections, setFileSelections] = useState({});
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Load duplicates on mount
  useEffect(() => {
    loadDuplicates();
  }, []);

  // Poll scan status when a job is active
  useEffect(() => {
    if (scanJobId && scanStatus?.status === 'running') {
      const interval = setInterval(async () => {
        try {
          const status = await mediaCleanerAPI.getScanStatus(scanJobId);
          setScanStatus(status);

          if (status.status === 'completed') {
            setScanJobId(null);
            await loadDuplicates();
          } else if (status.status === 'failed') {
            setScanJobId(null);
            setError(status.error_message || 'Scan failed');
          }
        } catch (err) {
          console.error('Error polling scan status:', err);
        }
      }, 2000); // Poll every 2 seconds

      return () => clearInterval(interval);
    }
  }, [scanJobId, scanStatus]);

  // Load duplicates from API
  const loadDuplicates = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await mediaCleanerAPI.getDuplicates();
      setDuplicates(data);
    } catch (err) {
      setError('Failed to load duplicates: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Start a new scan
  const startScan = async () => {
    setError(null);
    try {
      const response = await mediaCleanerAPI.startScan();
      setScanJobId(response.job_id);
      setScanStatus({ status: 'pending', ...response });
    } catch (err) {
      setError('Failed to start scan: ' + err.message);
    }
  };

  // Open comparison modal for a group
  const openComparison = (group) => {
    setSelectedGroup(group);

    // Initialize selections: mark largest file as KEEP, others as DELETE
    const selections = {};
    const sortedFiles = [...group.files].sort((a, b) => b.file_size_mb - a.file_size_mb);

    sortedFiles.forEach((file, index) => {
      selections[file.file_path] = index === 0 ? 'keep' : 'delete';
    });

    setFileSelections(selections);
  };

  // Close comparison modal
  const closeComparison = () => {
    setSelectedGroup(null);
    setFileSelections({});
  };

  // Toggle file selection
  const toggleSelection = (filePath, action) => {
    setFileSelections((prev) => ({
      ...prev,
      [filePath]: action,
    }));
  };

  // Get files marked for deletion
  const getFilesToDelete = () => {
    return Object.entries(fileSelections)
      .filter(([_, action]) => action === 'delete')
      .map(([path]) => path);
  };

  // Show delete confirmation
  const handleProcessDeletion = () => {
    const filesToDelete = getFilesToDelete();
    if (filesToDelete.length === 0) {
      alert('No files selected for deletion');
      return;
    }
    setShowDeleteConfirm(true);
  };

  // Execute deletion
  const executeDelete = async (dryRun = true) => {
    const filesToDelete = getFilesToDelete();

    try {
      const result = await mediaCleanerAPI.deleteFiles(filesToDelete, dryRun);

      if (!dryRun && result.success) {
        // Refresh duplicates list after actual deletion
        await loadDuplicates();
        closeComparison();
      }

      return result;
    } catch (err) {
      throw new Error('Failed to delete files: ' + err.message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">MediaCleaner</h1>
              <p className="text-sm text-gray-600 mt-1">
                Identify and remove duplicate movie files
              </p>
            </div>
            <button
              onClick={startScan}
              disabled={scanJobId !== null}
              className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {scanJobId ? 'Scanning...' : 'Start New Scan'}
            </button>
          </div>
        </div>
      </header>

      {/* Scan Progress */}
      {scanJobId && scanStatus && (
        <ScanProgress status={scanStatus} />
      )}

      {/* Error Display */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Dashboard
          duplicates={duplicates}
          loading={loading}
          onSelectGroup={openComparison}
          onRefresh={loadDuplicates}
        />
      </main>

      {/* Comparison Modal */}
      {selectedGroup && (
        <ComparisonModal
          group={selectedGroup}
          selections={fileSelections}
          onToggleSelection={toggleSelection}
          onClose={closeComparison}
          onProcessDeletion={handleProcessDeletion}
        />
      )}

      {/* Delete Confirmation */}
      {showDeleteConfirm && (
        <DeleteConfirmation
          filesToDelete={getFilesToDelete()}
          fileSelections={fileSelections}
          selectedGroup={selectedGroup}
          onClose={() => setShowDeleteConfirm(false)}
          onExecute={executeDelete}
        />
      )}
    </div>
  );
}

export default App;
