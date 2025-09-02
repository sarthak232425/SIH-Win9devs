import { useState, useRef, useEffect } from "react";
import Chatbot from "./components/Chatbot";

export default function App() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSystems, setSelectedSystems] = useState(["ALL"]);
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setError("");
    
    try {
      const response = await fetch("http://localhost:8000/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          query: searchQuery,
          systems: selectedSystems
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setSearchResults(data);
    } catch (err) {
      setError("Failed to fetch search results. Please try again.");
      console.error("Search error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const toggleSystem = (system) => {
    if (system === "ALL") {
      setSelectedSystems(["ALL"]);
    } else {
      const newSystems = selectedSystems.includes("ALL") 
        ? [system]
        : selectedSystems.includes(system)
        ? selectedSystems.filter(s => s !== system)
        : [...selectedSystems, system];
      
      setSelectedSystems(newSystems.length > 0 ? newSystems : ["ALL"]);
    }
  };

  // Format NAMASTE results for display
  const formatNamasteResults = (results) => {
    if (!results || results.length === 0) return null;
    
    return results.map((result, index) => (
      <div key={index} className="p-4 bg-white rounded-lg border border-gray-200 shadow-xs mb-3">
        <div className="flex justify-between items-start mb-2">
          <h4 className="font-semibold text-blue-700">Result {index + 1}</h4>
          {result.Source_Database && (
            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
              {result.Source_Database}
            </span>
          )}
        </div>
        <div className="text-sm space-y-1">
          {/* Prioritize important fields at the top */}
          {['NAMC_CODE', 'NAMC_TERM', 'Short_definition'].map(field => 
            result[field] && (
              <div key={field} className="flex">
                <span className="font-medium text-gray-600 min-w-[120px]">
                  {field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                </span>
                <span className="text-gray-800 flex-1 font-medium">{result[field]}</span>
              </div>
            )
          )}
          
          {/* Show other fields */}
          {Object.entries(result).map(([key, value]) => {
            if (['NAMC_CODE', 'NAMC_TERM', 'Short_definition', 'matched_columns', 'Source_Database'].includes(key)) 
              return null;
            
            if (value && String(value).trim() !== '') {
              const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
              return (
                <div key={key} className="flex">
                  <span className="font-medium text-gray-600 min-w-[120px]">{displayKey}:</span>
                  <span className="text-gray-800 flex-1">{value}</span>
                </div>
              );
            }
            return null;
          })}
          
          {/* Show which columns matched the search */}
          {result.matched_columns && result.matched_columns.length > 0 && (
            <div className="flex mt-2 pt-2 border-t border-gray-100">
              <span className="font-medium text-green-600 min-w-[120px]">Matched In:</span>
              <span className="text-green-700 flex-1">
                {result.matched_columns.join(', ')}
              </span>
            </div>
          )}
        </div>
      </div>
    ));
  };

  // Clear results when search query is cleared
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
    }
  }, [searchQuery]);

  return (
    <div className="min-h-screen w-full bg-gray-50 text-gray-900 flex flex-col">
      {/* Header / Banner */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-2xl font-bold text-blue-800">
            National Medical Coding Portal
          </h1>
          <nav className="mt-2 sm:mt-0">
            <ul className="flex space-x-6 text-sm text-gray-700">
              <li className="hover:text-blue-700 cursor-pointer transition-colors">Home</li>
              <li className="hover:text-blue-700 cursor-pointer transition-colors">About</li>
              <li className="hover:text-blue-700 cursor-pointer transition-colors">Help</li>
            </ul>
          </nav>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 py-8 grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Left: Main App (3/4) */}
        <main className="lg:col-span-3 bg-white border border-gray-200 rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-6 text-blue-800 border-b pb-3">
            Search and Map Diagnoses
          </h2>

          {/* System Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Medical Systems to Search:
            </label>
            <div className="flex flex-wrap gap-2">
              {["ALL", "AYURVEDA", "UNANI", "SIDDHA"].map((system) => (
                <button
                  key={system}
                  onClick={() => toggleSystem(system)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    selectedSystems.includes(system)
                      ? "bg-blue-600 text-white"
                      : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                  }`}
                >
                  {system}
                </button>
              ))}
            </div>
          </div>

          {/* Search Section */}
          <div className="mb-8">
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Enter disease name, code, or term..."
                className="flex-1 border border-gray-300 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                disabled={loading}
              />
              <button 
                onClick={handleSearch}
                disabled={loading}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg text-base font-medium hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors shadow-md"
              >
                {loading ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Searching...
                  </span>
                ) : "Search"}
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              <div className="flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            </div>
          )}

          {/* Results */}
          {searchResults && (
            <section className="space-y-6">
              {/* Search Info */}
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">
                  Searching in: <span className="font-medium">{searchResults.systems.join(", ")}</span>
                </p>
              </div>

              {/* NAMASTE Results */}
              {searchResults.namaste_matches && searchResults.namaste_matches.length > 0 && (
                <div className="border border-blue-100 rounded-lg p-5 bg-blue-50 shadow-sm">
                  <h3 className="font-semibold text-blue-800 mb-3 text-lg flex items-center">
                    <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                    </svg>
                    NAMASTE Results ({searchResults.namaste_matches.length} found)
                  </h3>
                  <div className="text-sm">
                    {formatNamasteResults(searchResults.namaste_matches)}
                  </div>
                </div>
              )}

              {/* ICD-11 Results */}
              {searchResults.icd11_matches && searchResults.icd11_matches !== "No ICD-11 matches found" && (
                <div className="border border-green-100 rounded-lg p-5 bg-green-50 shadow-sm">
                  <h3 className="font-semibold text-green-800 mb-3 text-lg flex items-center">
                    <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v4a2 2 0 002 2V6h10a2 2 0 00-2-2H4zm2 6a2 2 0 012-2h8a2 2 0 012 2v4a2 2 0 01-2 2H8a2 2 0 01-2-2v-4z" clipRule="evenodd" />
                    </svg>
                    ICD-11 Results
                  </h3>
                  <div className="text-sm text-gray-700 space-y-2">
                    {searchResults.icd11_matches.split('\n').map((line, index) => (
                      <div key={index} className="p-3 bg-white rounded-lg border border-gray-100 shadow-xs">
                        {line}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* No Results Message */}
              {((!searchResults.namaste_matches || searchResults.namaste_matches.length === 0) &&
               (!searchResults.icd11_matches || searchResults.icd11_matches === "No ICD-11 matches found")) && (
                <div className="border border-yellow-100 rounded-lg p-5 bg-yellow-50 shadow-sm">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 mr-2 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <span className="text-yellow-800 font-medium">No results found for "{searchResults.query}"</span>
                  </div>
                  <p className="text-yellow-700 text-sm mt-2">Try different search terms or check the spelling.</p>
                </div>
              )}
            </section>
          )}

          {/* Example Result (shown only when no search has been performed) */}
          {!searchResults && !loading && (
            <section className="border border-gray-200 rounded-lg p-5 bg-gray-50 shadow-sm">
              <h3 className="font-semibold text-gray-800 mb-3 text-lg">Example Result</h3>
              <div className="text-sm text-gray-700 space-y-2">
                <div className="p-3 bg-white rounded-lg border border-gray-100 shadow-xs">
                  <span className="font-medium">Disease:</span> Jwara (Fever)
                </div>
                <div className="p-3 bg-white rounded-lg border border-gray-100 shadow-xs">
                  <span className="font-medium">NAMASTE Code:</span> NAM-1023
                </div>
                <div className="p-3 bg-white rounded-lg border border-gray-100 shadow-xs">
                  <span className="font-medium">ICD-11 Code:</span> ICD11-AX23
                </div>
              </div>
            </section>
          )}
        </main>

        {/* Right: Sidebar (1/4) - Sticky */}
        <aside className="lg:col-span-1 flex flex-col space-y-6">
          {/* Instructions - Sticky */}
          <div className="sticky top-6 bg-white border border-gray-200 rounded-lg shadow-sm p-5">
            <h3 className="text-lg font-semibold text-blue-800 mb-3 border-b pb-2">
              Instructions
            </h3>
            <ol className="list-decimal list-inside text-sm text-gray-700 space-y-2">
              <li className="pb-1">Select medical systems to search</li>
              <li className="pb-1">Enter search term, code, or disease name</li>
              <li className="pb-1">View mapped NAMASTE & ICD-11 codes</li>
              <li>Consult AI assistant for detailed information</li>
            </ol>
          </div>

          {/* Chatbot (dynamic) - Sticky with scroll */}
          <div className="sticky top-[calc(6rem+1.5rem)] bg-white border border-gray-200 rounded-lg shadow-sm p-5 flex flex-col" style={{ height: '500px' }}>
            <h3 className="text-lg font-semibold text-blue-800 mb-3 border-b pb-2">
              AI Assistant
            </h3>
            <div className="flex-1 min-h-0">
              <Chatbot />
            </div>
          </div>
        </aside>
      </div>

      {/* Footer */}
      <footer className="bg-gray-100 border-t border-gray-200 text-gray-600 text-sm py-4 text-center mt-auto">
        <div className="max-w-7xl mx-auto px-4">
          © 2025 National Health Informatics. All Rights Reserved.
        </div>
      </footer>
    </div>
  );
}