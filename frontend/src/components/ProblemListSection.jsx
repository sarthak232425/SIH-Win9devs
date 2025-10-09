// Handles the problem list entry tab and modal
import React, { useState, useEffect } from "react";
import { getProblemListStats, getAllProblemListEntries, deleteProblemListEntry } from "../services/mongoDBService";

export default function ProblemListSection({
  problemList,
  setShowProblemListModal,
  setProblemList
}) {
  
  const [stats, setStats] = useState({
    totalEntries: 0,
    patientsCount: 0,
    codesUsed: { namaste: 0, icd11: 0 },
    statusBreakdown: {}
  });
  const [statsLoading, setStatsLoading] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState({ show: false, entryId: null, entryIndex: null });
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Load statistics from MongoDB
  const loadStats = async () => {
    setStatsLoading(true);
    try {
      const result = await getProblemListStats();
      if (result.success) {
        setStats(result.stats);
      }
    } catch (error) {
      console.error("Error loading statistics:", error);
    } finally {
      setStatsLoading(false);
    }
  };

  // Load stats on component mount
  useEffect(() => {
    loadStats();
  }, [problemList.length]); // Reload when problem list changes

  // Handle viewing storage info
  const handleViewStorageInfo = () => {
    const dateRange = stats.dateRange ? 
      `\nDate Range: ${new Date(stats.dateRange.oldest).toLocaleDateString()} to ${new Date(stats.dateRange.newest).toLocaleDateString()}` : 
      '';
      
    alert(`Problem List Database Info:
    
Total Entries: ${stats.totalEntries}
Unique Patients: ${stats.patientsCount}
NAMASTE Codes Used: ${stats.codesUsed.namaste}
ICD-11 Codes Used: ${stats.codesUsed.icd11}${dateRange}

Data is stored in:
- MongoDB Database (persistent)
- FHIR R4 Condition format
- Express API Server (Port 5001)

All entries are fully persistent and FHIR-compliant.`);
  };

  // Handle exporting all entries from MongoDB
  const handleExportFromDatabase = async () => {
    try {
      const result = await getAllProblemListEntries();
      if (result.success) {
        const entries = result.entries?.entries || result.entries || [];
        const jsonData = JSON.stringify(entries, null, 2);
        
        // Create and download file
        const blob = new Blob([jsonData], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `problem-list-export-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        alert(`✅ Exported ${entries.length} entries from MongoDB database`);
      } else {
        alert(`❌ Export failed: ${result.message}`);
      }
    } catch (error) {
      console.error("Export error:", error);
      alert(`❌ Export failed: ${error.message}`);
    }
  };

  // Handle delete confirmation dialog
  const handleDeleteClick = (entry, index) => {
    setDeleteConfirm({
      show: true,
      entryId: entry._id,
      entryIndex: index,
      entryData: entry
    });
  };

  // Handle delete cancellation
  const handleDeleteCancel = () => {
    setDeleteConfirm({ show: false, entryId: null, entryIndex: null });
  };

  // Handle delete confirmation
  const handleDeleteConfirm = async () => {
    if (!deleteConfirm.entryId) return;

    setDeleteLoading(true);
    try {
      const result = await deleteProblemListEntry(deleteConfirm.entryId);
      
      if (result.success) {
        // Remove from local state
        const updatedProblemList = problemList.filter((_, index) => index !== deleteConfirm.entryIndex);
        setProblemList(updatedProblemList);
        
        // Reload stats
        loadStats();
        
        alert(`✅ Problem list entry deleted successfully`);
      } else {
        alert(`❌ Delete failed: ${result.message}`);
      }
    } catch (error) {
      console.error("Delete error:", error);
      alert(`❌ Delete failed: ${error.message}`);
    } finally {
      setDeleteLoading(false);
      setDeleteConfirm({ show: false, entryId: null, entryIndex: null });
    }
  };
  return (
    <>
      <div className="bg-green-50 p-4 rounded-lg mb-4 border border-green-200">
        <p className="text-sm text-green-800 flex items-center">
          <svg className="w-4 h-4 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          Create and manage patient problem lists with standardized medical codes and clinical information.
        </p>
      </div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-green-800">Current Problem List ({problemList.length} entries)</h3>
        <div className="flex gap-2">
          {problemList.length > 0 && (
            <>
              <button
                onClick={handleViewStorageInfo}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-all shadow-md hover:shadow-lg flex items-center"
              >
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                Storage Info
              </button>
              <button
                onClick={handleExportFromDatabase}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-purple-700 transition-all shadow-md hover:shadow-lg flex items-center"
              >
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                Export from DB
              </button>
            </>
          )}
          <button
            onClick={() => setShowProblemListModal(true)}
            className="bg-gradient-to-r from-green-600 to-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium hover:from-green-700 hover:to-green-800 transition-all shadow-md hover:shadow-lg flex items-center"
          >
            <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            Add New Entry
          </button>
        </div>
      </div>
      {/* Problem List Display */}
      {problemList.length > 0 ? (
        <div className="space-y-4 mb-6">
          {problemList.map((entry, index) => (
            <div key={index} className="bg-white border border-green-200 rounded-lg p-4 shadow-sm">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <h4 className="font-semibold text-green-800">{entry.condition}</h4>
                  <div className="text-sm text-gray-600 mt-1">
                    <span className="font-medium">Patient ID:</span> {entry.patientId}
                  </div>
                </div>
                <div className="flex gap-2 items-center">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    entry.clinicalStatus === 'active' ? 'bg-red-100 text-red-800' :
                    entry.clinicalStatus === 'inactive' ? 'bg-gray-100 text-gray-800' :
                    entry.clinicalStatus === 'resolved' ? 'bg-green-100 text-green-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {entry.clinicalStatus}
                  </span>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    entry.verificationStatus === 'confirmed' ? 'bg-green-100 text-green-800' :
                    entry.verificationStatus === 'refuted' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {entry.verificationStatus}
                  </span>
                  <button
                    onClick={() => handleDeleteClick(entry, index)}
                    className="ml-2 text-red-600 hover:text-red-800 hover:bg-red-50 p-1 rounded transition-colors"
                    title="Delete this entry"
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>
              </div>
              {/* Display both NAMASTE and ICD-11 codes */}
              {(entry.selectedNamasteCode || entry.selectedIcd11Code) && (
                <div className="text-sm mb-2 space-y-1">
                  {entry.selectedNamasteCode && (
                    <div className="flex items-center">
                      <span className="font-medium text-gray-700">NAMASTE:</span>
                      <span className="ml-2 text-gray-600">{entry.selectedNamasteCode.code} - {entry.selectedNamasteCode.title}</span>
                      <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">NAMASTE</span>
                    </div>
                  )}
                  {entry.selectedIcd11Code && (
                    <div className="flex items-center">
                      <span className="font-medium text-gray-700">ICD-11:</span>
                      <span className="ml-2 text-gray-600">{entry.selectedIcd11Code.code} - {entry.selectedIcd11Code.title}</span>
                      <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">ICD-11</span>
                    </div>
                  )}
                </div>
              )}
              
              {/* Fallback for old entries with selectedCode */}
              {entry.selectedCode && !entry.selectedNamasteCode && !entry.selectedIcd11Code && (
                <div className="text-sm text-gray-700 mb-2">
                  <span className="font-medium">Code:</span> {entry.selectedCode.code} - {entry.selectedCode.title}
                </div>
              )}
              <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                <div>
                  <span className="font-medium">Onset Date:</span> {entry.onsetDate || 'Not specified'}
                </div>
                <div>
                  <span className="font-medium">Recorded Date:</span> {entry.recordedDate || 'Not specified'}
                </div>
              </div>
              {entry.notes && (
                <div className="mt-2 text-sm text-gray-700">
                  <span className="font-medium">Notes:</span> {entry.notes}
                </div>
              )}
              
              {/* FHIR Status Badge */}
              {entry.fhirCondition && (
                <div className="mt-3 flex items-center gap-2">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                    </svg>
                    FHIR Condition in MongoDB
                  </span>
                  <span className="text-xs text-gray-500">
                    Created: {entry.createdAt ? new Date(entry.createdAt).toLocaleDateString() : (entry.storedAt ? new Date(entry.storedAt).toLocaleDateString() : 'N/A')}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="border border-green-200 rounded-lg p-8 text-center bg-green-50">
          <svg className="w-12 h-12 mx-auto text-green-400 mb-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clipRule="evenodd" />
            <path fillRule="evenodd" d="M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6h-3a2 2 0 00-2 2v3H6a2 2 0 01-2-2V5zM14 17v-3a1 1 0 011-1h3v3a2 2 0 01-2 2h-1a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
          <p className="text-green-800 font-medium">No problem list entries yet</p>
          <p className="text-green-600 text-sm mt-1">Click "Add New Entry" to create your first problem list entry</p>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {deleteConfirm.show && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" onClick={handleDeleteCancel}>
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white" onClick={(e) => e.stopPropagation()}>
            <div className="mt-3 text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <svg className="h-6 w-6 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-2">Delete Problem List Entry</h3>
              <div className="mt-2 px-7 py-3">
                <p className="text-sm text-gray-500 mb-4">
                  Are you sure you want to delete this problem list entry? This action cannot be undone.
                </p>
                {deleteConfirm.entryData && (
                  <div className="bg-gray-50 p-3 rounded-lg text-left mb-4">
                    <p className="text-sm font-medium text-gray-900">{deleteConfirm.entryData.condition}</p>
                    <p className="text-xs text-gray-600">Patient ID: {deleteConfirm.entryData.patientId}</p>
                    {deleteConfirm.entryData.selectedNamasteCode && (
                      <p className="text-xs text-gray-600">Code: {deleteConfirm.entryData.selectedNamasteCode.code}</p>
                    )}
                  </div>
                )}
              </div>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={handleDeleteCancel}
                  disabled={deleteLoading}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteConfirm}
                  disabled={deleteLoading}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
                >
                  {deleteLoading ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Deleting...
                    </>
                  ) : (
                    'Delete'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
