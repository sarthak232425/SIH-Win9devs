// Modal for adding new problem list entries
import React, { useState } from "react";
import { previewFhirCondition } from "../services/mongoDBService";

export default function ProblemListModal({
  showProblemListModal,
  setShowProblemListModal,
  problemListEntry,
  setProblemListEntry,
  codeSearchQuery,
  setCodeSearchQuery,
  codeSearchResults,
  setCodeSearchResults,
  codeSearchLoading,
  handleCodeSearch,
  handleAddToProblemList,
  selectedNamasteCode,
  setSelectedNamasteCode,
  icd11MappingResults,
  setIcd11MappingResults,
  icd11MappingLoading,
  handleNamasteCodeSelection
}) {
  const [showFhirPreview, setShowFhirPreview] = useState(false);
  const [fhirPreview, setFhirPreview] = useState(null);

  const handleCloseModal = () => {
    // Clear search state when closing the modal
    setCodeSearchQuery("");
    setCodeSearchResults(null);
    setSelectedNamasteCode(null);
    setIcd11MappingResults(null);
    setShowFhirPreview(false);
    setFhirPreview(null);
    setShowProblemListModal(false);
  };

  // Generate FHIR preview
  const handlePreviewFhir = () => {
    if (problemListEntry.patientId && problemListEntry.condition && problemListEntry.selectedNamasteCode) {
      const preview = previewFhirCondition(problemListEntry);
      setFhirPreview(preview);
      setShowFhirPreview(true);
    }
  };

  if (!showProblemListModal) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-xl">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-green-800">Add Problem List Entry</h2>
            <button
              onClick={handleCloseModal}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        <div className="p-6 space-y-6">
          {/* Patient Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Patient ABHA ID *
            </label>
            <input
              type="text"
              value={problemListEntry.patientId}
              onChange={(e) => setProblemListEntry({...problemListEntry, patientId: e.target.value})}
              placeholder="Enter ABHA ID (e.g., 12-3456-7890-1234)"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          {/* Condition Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Condition Description *
            </label>
            <input
              type="text"
              value={problemListEntry.condition}
              onChange={(e) => setProblemListEntry({...problemListEntry, condition: e.target.value})}
              placeholder="Enter condition or diagnosis"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          {/* Code Search Section */}
          <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
            <h3 className="text-lg font-medium text-gray-800 mb-3">Search NAMASTE Codes</h3>
            <div className="flex gap-3 mb-4">
              <input
                type="text"
                value={codeSearchQuery}
                onChange={(e) => setCodeSearchQuery(e.target.value)}
                placeholder="Search for diseases or conditions (e.g., fever, headache)..."
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
              />
              <button
                onClick={handleCodeSearch}
                disabled={codeSearchLoading}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-70 flex items-center"
              >
                {codeSearchLoading ? (
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                  </svg>
                )}
                <span className="ml-2">Search</span>
              </button>
            </div>

            {/* Step 1: NAMASTE Code Search Results */}
            {codeSearchResults && !selectedNamasteCode && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select a NAMASTE code (will auto-map to ICD-11):
                </label>
                <div className="border border-gray-300 rounded-lg bg-white max-h-60 overflow-y-auto">
                  {codeSearchResults.ayurveda?.results?.length > 0 ? (
                    codeSearchResults.ayurveda.results.map((result, index) => (
                      <div
                        key={`ayur-${index}`}
                        onClick={() => handleNamasteCodeSelection(
                          result.data.NAMC_CODE || 'N/A',
                          result.data.NAMC_term || 'N/A',
                          result.data.Long_definition || 'N/A'
                        )}
                        className="p-3 hover:bg-green-50 cursor-pointer border-b border-gray-100 last:border-b-0 transition-colors"
                      >
                        <div className="font-medium text-gray-800 text-sm">
                          {result.data.NAMC_CODE} - {result.data.NAMC_term}
                          <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">NAMASTE</span>
                        </div>
                        {result.data.Long_definition && result.data.Long_definition !== 'N/A' && (
                          <div className="text-xs text-gray-600 mt-1 leading-relaxed">
                            {result.data.Long_definition}
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="p-3 text-gray-500 text-sm text-center">
                      No NAMASTE codes found
                    </div>
                  )}
                </div>
                
                <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="text-xs text-green-600 mb-1">Available NAMASTE codes:</div>
                  <div className="text-sm text-gray-600">
                    {codeSearchResults.ayurveda?.results?.length || 0} result(s) found with definitions. Click any option to auto-map to ICD-11.
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Selected NAMASTE Code */}
            {selectedNamasteCode && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="text-sm text-green-600 mb-1">Selected NAMASTE Code:</div>
                <div className="font-medium text-gray-800 mb-1">
                  {selectedNamasteCode.code} - {selectedNamasteCode.title}
                </div>
                {selectedNamasteCode.description && selectedNamasteCode.description !== 'N/A' && (
                  <div className="text-sm text-gray-600 mb-2">
                    {selectedNamasteCode.description}
                  </div>
                )}
                <button
                  onClick={() => {
                    setSelectedNamasteCode(null);
                    setIcd11MappingResults(null);
                  }}
                  className="text-xs text-green-600 hover:text-green-800 underline"
                >
                  Change NAMASTE Code
                </button>
              </div>
            )}

            {/* Step 3: ICD-11 Mapping Loading */}
            {icd11MappingLoading && (
              <div className="flex items-center justify-center py-4">
                <svg className="animate-spin h-5 w-5 text-green-600 mr-2" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="text-sm text-gray-600">Finding matching ICD-11 codes...</span>
              </div>
            )}

            {/* Step 4: ICD-11 Mapping Results */}
            {icd11MappingResults && icd11MappingResults.length > 0 && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select the best matching ICD-11 code (optional):
                </label>
                <div className="border border-gray-300 rounded-lg bg-white max-h-60 overflow-y-auto">
                  {/* Option to skip ICD-11 mapping */}
                  <div
                    onClick={() => setProblemListEntry({
                      ...problemListEntry, 
                      selectedNamasteCode: selectedNamasteCode,
                      selectedIcd11Code: null
                    })}
                    className={`p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 transition-colors ${
                      !problemListEntry.selectedIcd11Code ? 'bg-gray-50 border-l-4 border-l-gray-400' : ''
                    }`}
                  >
                    <div className="font-medium text-gray-600 text-sm">
                      No ICD-11 mapping (NAMASTE only)
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Proceed with only the NAMASTE code
                    </div>
                  </div>

                  {/* ICD-11 mapping options */}
                  {icd11MappingResults.map((result, index) => (
                    <div
                      key={`icd-${index}`}
                      onClick={() => setProblemListEntry({
                        ...problemListEntry, 
                        selectedNamasteCode: selectedNamasteCode,
                        selectedIcd11Code: {
                          code: result.code,
                          title: result.title,
                          similarity_score: result.similarity_score
                        }
                      })}
                      className={`p-3 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0 transition-colors ${
                        problemListEntry.selectedIcd11Code?.code === result.code ? 'bg-blue-50 border-l-4 border-l-blue-400' : ''
                      }`}
                    >
                      <div className="font-medium text-gray-800 text-sm flex items-center justify-between">
                        <span>{result.code} - {result.title}</span>
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">ICD-11</span>
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="text-xs text-blue-600 mb-1">ICD-11 Mapping Options:</div>
                  <div className="text-sm text-gray-600">
                    {icd11MappingResults.length} ICD-11 code(s) found that match your NAMASTE selection. 
                    Click any option or choose "No mapping" to proceed.
                  </div>
                </div>
              </div>
            )}

            {/* No ICD-11 mappings found */}
            {selectedNamasteCode && icd11MappingResults && icd11MappingResults.length === 0 && !icd11MappingLoading && (
              <div className="text-center py-4 text-gray-500">
                <p className="text-sm">No ICD-11 mappings found for this NAMASTE code.</p>
                <p className="text-xs mt-1">You can proceed without an ICD-11 code or try a different NAMASTE code.</p>
              </div>
            )}

            {/* Selected Codes Display */}
            {(problemListEntry.selectedNamasteCode || problemListEntry.selectedIcd11Code) && (
              <div className="mt-4 p-3 bg-white border border-green-200 rounded-lg">
                <div className="text-sm text-gray-600 mb-2">Selected Codes for Problem List:</div>
                
                {/* NAMASTE Code */}
                {problemListEntry.selectedNamasteCode && (
                  <div className="mb-3 p-2 bg-green-50 rounded border border-green-200">
                    <div className="font-medium text-gray-800 mb-1">
                      {problemListEntry.selectedNamasteCode.code} - {problemListEntry.selectedNamasteCode.title}
                      <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                        NAMASTE
                      </span>
                    </div>
                    {problemListEntry.selectedNamasteCode.description && problemListEntry.selectedNamasteCode.description !== 'N/A' && (
                      <div className="text-sm text-gray-600">
                        {problemListEntry.selectedNamasteCode.description}
                      </div>
                    )}
                  </div>
                )}

                {/* ICD-11 Code */}
                {problemListEntry.selectedIcd11Code && (
                  <div className="p-2 bg-blue-50 rounded border border-blue-200">
                    <div className="font-medium text-gray-800 mb-1">
                      {problemListEntry.selectedIcd11Code.code} - {problemListEntry.selectedIcd11Code.title}
                      <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                        ICD-11
                      </span>
                    </div>
                  </div>
                )}

                {/* Option to proceed with only NAMASTE code */}
                {problemListEntry.selectedNamasteCode && !problemListEntry.selectedIcd11Code && selectedNamasteCode && (
                  <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
                    <div className="text-sm text-yellow-800">
                      <strong>Note:</strong> You can add this entry with only the NAMASTE code, or select an ICD-11 mapping above.
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Clinical Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Clinical Status *
              </label>
              <select
                value={problemListEntry.clinicalStatus}
                onChange={(e) => setProblemListEntry({...problemListEntry, clinicalStatus: e.target.value})}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              >
                <option value="active">Active</option>
                <option value="recurrence">Recurrence</option>
                <option value="relapse">Relapse</option>
                <option value="inactive">Inactive</option>
                <option value="remission">Remission</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>

            {/* Verification Status */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Verification Status *
              </label>
              <select
                value={problemListEntry.verificationStatus}
                onChange={(e) => setProblemListEntry({...problemListEntry, verificationStatus: e.target.value})}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              >
                <option value="unconfirmed">Unconfirmed</option>
                <option value="provisional">Provisional</option>
                <option value="differential">Differential</option>
                <option value="confirmed">Confirmed</option>
                <option value="refuted">Refuted</option>
                <option value="entered-in-error">Entered in Error</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Onset Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Onset Date
              </label>
              <input
                type="date"
                value={problemListEntry.onsetDate}
                onChange={(e) => setProblemListEntry({...problemListEntry, onsetDate: e.target.value})}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>

            {/* Recorded Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Recorded Date
              </label>
              <input
                type="date"
                value={problemListEntry.recordedDate}
                onChange={(e) => setProblemListEntry({...problemListEntry, recordedDate: e.target.value})}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>
          </div>

          {/* Clinical Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Clinical Notes
            </label>
            <textarea
              value={problemListEntry.notes}
              onChange={(e) => setProblemListEntry({...problemListEntry, notes: e.target.value})}
              placeholder="Additional clinical information, observations, or notes..."
              rows={4}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>

          {/* FHIR Preview Section */}
          {showFhirPreview && fhirPreview && fhirPreview.success && (
            <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-medium text-blue-800">FHIR Condition Preview</h3>
                <button
                  onClick={() => setShowFhirPreview(false)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="bg-white rounded border p-3 mb-3">
                <div className="text-sm text-gray-600 mb-2">
                  <strong>Resource ID:</strong> {fhirPreview.fhirCondition.id}
                </div>
                <div className="text-sm text-gray-600 mb-2">
                  <strong>Patient Reference:</strong> {fhirPreview.fhirCondition.subject.reference}
                </div>
                <div className="text-sm text-gray-600">
                  <strong>Storage:</strong> Will be saved to MongoDB database
                </div>
              </div>
              <details className="bg-white rounded border">
                <summary className="p-3 cursor-pointer text-sm font-medium text-gray-700 hover:bg-gray-50">
                  View Full FHIR JSON
                </summary>
                <div className="p-3 border-t">
                  <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto max-h-60">
                    {fhirPreview.jsonString}
                  </pre>
                </div>
              </details>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              onClick={handleCloseModal}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            {problemListEntry.patientId && problemListEntry.condition && problemListEntry.selectedNamasteCode && (
              <button
                onClick={handlePreviewFhir}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center"
              >
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                  <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                </svg>
                Preview FHIR
              </button>
            )}
            <button
              onClick={handleAddToProblemList}
              disabled={!problemListEntry.patientId || !problemListEntry.condition || !problemListEntry.selectedNamasteCode}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-70 disabled:cursor-not-allowed transition-colors flex items-center"
            >
              <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
              </svg>
              Add to Problem List & Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}