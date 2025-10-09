// Displays search and mapping results
import React from "react";

export default function ResultsSection({
  searchResults,
  mappingResults,
  activeTab,
  selectedSystems,
  formatSemanticResults,
  formatICD11Results,
  copyToClipboard
}) {
  return (
    <>
      {/* Search Results */}
      {searchResults && activeTab === "search" && (
        <section className="space-y-6">
          <div className="bg-green-50 p-3 rounded-lg border border-green-200">
            <p className="text-sm text-green-800">
              Searching for: <span className="font-medium">{searchResults.query}</span>
            </p>
          </div>
          {(selectedSystems.includes('AYURVEDA') || selectedSystems.includes('ALL')) && 
            (<div className="border border-green-200 rounded-lg p-5 bg-green-50 shadow-sm">
              <h3 className="font-semibold text-green-800 mb-3 text-lg flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                </svg>
                Ayurveda Results ({searchResults.ayurveda.total_results} found)
              </h3>
              <div className="text-sm">
                {formatSemanticResults(searchResults.ayurveda.results)}
              </div>
            </div>)}
          {(selectedSystems.includes('ICD-11') || selectedSystems.includes('ALL')) && (<div className="border border-green-200 rounded-lg p-5 bg-green-50 shadow-sm">
              <h3 className="font-semibold text-green-800 mb-3 text-lg flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                </svg>
                ICD-11 Results ({searchResults.icd.total_results} found)
              </h3>
              <div className="text-sm">
                {formatICD11Results(searchResults.icd.results)}
              </div>
            </div>)}
        </section>
      )}
      {/* Mapping Results */}
      {mappingResults && activeTab === "map" && (
        <section className="space-y-6">
          <div className="bg-green-50 p-3 rounded-lg border border-green-200">
            <p className="text-sm text-green-800">
              Mapping for: <span className="font-medium">{mappingResults.namaste_code}</span>
            </p>
          </div>
          {/* Ayurveda Mapping Results */}
          {mappingResults.ayurvedic_text && (
            <div className="border border-green-200 rounded-lg p-5 bg-green-50 shadow-sm">
              <h3 className="font-semibold text-green-800 mb-3 text-lg flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                </svg>
                Ayurveda Mapping
              </h3>
              <div className="text-sm">
                {typeof mappingResults.ayurvedic_text === 'string' ? mappingResults.ayurvedic_text : JSON.stringify(mappingResults.ayurvedic_text)}
              </div>
            </div>
          )}
          {/* ICD-11 Mapping Results */}
          {mappingResults.icd11_matches && mappingResults.icd11_matches.length > 0 && (
            <div className="border border-green-200 rounded-lg p-5 bg-green-50 shadow-sm">
              <h3 className="font-semibold text-green-800 mb-3 text-lg flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                </svg>
                ICD-11 Mapping Results ({mappingResults.icd11_matches.length} found)
              </h3>
              <div className="text-sm">
                {formatICD11Results(mappingResults.icd11_matches)}
              </div>
            </div>
          )}
        </section>
      )}
    </>
  );
}
