import { useState, useRef, useEffect } from "react";
import Chatbot from "./components/Chatbot";

export default function App() {
  const [searchQuery, setSearchQuery] = useState("");
  const [mappingCode, setMappingCode] = useState("");
  const [selectedSystems, setSelectedSystems] = useState(["ALL"]);
  const [searchResults, setSearchResults] = useState(null);
  const [mappingResults, setMappingResults] = useState(null);
  const [activeTab, setActiveTab] = useState("search");
  const [searchLoading, setSearchLoading] = useState(false);
  const [mappingLoading, setMappingLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    setMappingLoading(false);
    setError("");
    setMappingResults(null);
    try {
      const response = await fetch(
        `http://127.0.0.1:5000/search?q=${encodeURIComponent(searchQuery)}&k=3`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      // Transform the API response to match the expected format for rendering
      setSearchResults({
        query: data.query,
        total_results: data.total_results,
        semantic_results: data.results,
      });
    } catch (err) {
      setError(err.message || "Failed to fetch search results. Please try again.");
      console.error("Search error:", err);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleMapping = async () => {
    if (!mappingCode.trim()) return;
    
    setMappingLoading(true);
    setSearchLoading(false);
    setError("");
    setSearchResults(null);
    
    try {
      const response = await fetch("http://localhost:8000/map", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          namaste_code: mappingCode
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setMappingResults(data);
    } catch (err) {
      setError(err.message || "Failed to fetch mapping results. Please try again.");
      console.error("Mapping error:", err);
    } finally {
      setMappingLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      if (activeTab === "search") {
        handleSearch();
      } else {
        handleMapping();
      }
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

  // Format semantic results for display
  const formatSemanticResults = (results) => {
    if (!results || results.length === 0) return null;
    return results.map((result, index) => {
      const { data, match_type, rank, similarity_score } = result;
      return (
        <div key={index} className="p-4 bg-white rounded-lg border border-green-200 shadow-xs mb-3">
          <div className="flex justify-between items-start mb-2">
            <h4 className="font-semibold text-green-700">Result {index + 1}</h4>
            <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
              {match_type.replace(/_/g, ' ')}
            </span>
          </div>
          <div className="text-sm space-y-1">
            {Object.entries(data).map(([key, value]) => (
              <div key={key} className="flex">
                <span className="font-medium text-gray-600 min-w-[120px]">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</span>
                <span className="text-gray-800 flex-1">{value}</span>
              </div>
            ))}
            <div className="flex mt-2 pt-2 border-t border-green-100">
              <span className="font-medium text-green-600 min-w-[120px]">Rank:</span>
              <span className="text-green-700 flex-1">{rank}</span>
            </div>
            <div className="flex mt-1">
              <span className="font-medium text-green-600 min-w-[120px]">Similarity Score:</span>
              <span className="text-green-700 flex-1">{similarity_score.toFixed(3)}</span>
            </div>
          </div>
        </div>
      );
    });
  };

  // Format ICD-11 results for display
  const formatICD11Results = (results) => {
    if (!results || results.length === 0) return null;
    
    return results.map((result, index) => (
      <div key={index} className="p-4 bg-white rounded-lg border border-green-200 shadow-xs mb-3">
        <h4 className="font-semibold text-green-700 mb-2">ICD-11 Result {index + 1}</h4>
        <div className="text-sm space-y-1">
          {['Code', 'Title', 'ChapterTitle', 'ChapterNr', 'Version', 'FullDescription'].map(field => 
            result[field] && (
              <div key={field} className="flex">
                <span className="font-medium text-gray-600 min-w-[120px]">
                  {field.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}:
                </span>
                <span className="text-gray-800 flex-1">{result[field]}</span>
              </div>
            )
          )}
          
          {result.match_reason && (
            <div className="flex mt-2 pt-2 border-t border-green-100">
              <span className="font-medium text-blue-600 min-w-[120px]">Match Reason:</span>
              <span className="text-blue-700 flex-1">{result.match_reason}</span>
            </div>
          )}
          
          {result.matched_columns && result.matched_columns.length > 0 && (
            <div className="flex mt-2 pt-2 border-t border-green-100">
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

  // Copy to clipboard functionality
  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      console.log('Copied to clipboard:', text);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Clear results when inputs are cleared
  useEffect(() => {
    if (!searchQuery.trim() && !mappingCode.trim()) {
      setSearchResults(null);
      setMappingResults(null);
    }
  }, [searchQuery, mappingCode]);

  return (
    <div className="min-h-screen w-full bg-gray-50 text-gray-900 flex flex-col relative overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-green-100 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob"></div>
      <div className="absolute top-1/4 left-10 w-80 h-80 bg-teal-100 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-2000"></div>
      <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-green-100 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-4000"></div>
      
      <header className="bg-gradient-to-r from-green-700 to-green-600 text-white border-b-4 border-green-900 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center">
            <div className="bg-white p-2 rounded-full mr-3 shadow-md">
              <svg className="w-8 h-8 text-green-700" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 9h-2V7h2v5zm0 4h-2v-2h2v2z"/>
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-bold">राष्ट्रीय आयुर्विज्ञान कोडिंग पोर्टल</h1>
              <p className="text-green-200 text-sm">National Medical Coding Portal</p>
            </div>
          </div>

          <nav className="mt-2 sm:mt-0">
            <ul className="flex space-x-6 text-sm font-medium">
              <li className="hover:text-white cursor-pointer transition-colors duration-200 border-b-2 border-transparent hover:border-green-200 pb-1">Home</li>
              <li className="hover:text-white cursor-pointer transition-colors duration-200 border-b-2 border-transparent hover:border-green-200 pb-1">About</li>
              <li className="hover:text-white cursor-pointer transition-colors duration-200 border-b-2 border-transparent hover:border-green-200 pb-1">Help</li>
            </ul>
          </nav>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 py-8 grid grid-cols-1 lg:grid-cols-4 gap-8 relative z-10">
        {/* Left: Main App (3/4) */}
        <main className="lg:col-span-3 bg-white border border-green-200 rounded-xl shadow-md p-6 relative overflow-hidden">
          {/* Decorative corner elements */}
          <div className="absolute top-0 right-0 w-24 h-24 overflow-hidden">
            <div className="absolute transform rotate-45 bg-green-100 text-white shadow-md w-40 h-10 -right-12 top-5"></div>
          </div>
          
          <div className="absolute bottom-0 left-0 w-24 h-24 overflow-hidden">
            <div className="absolute transform rotate-45 bg-green-100 text-white shadow-md w-40 h-10 -left-12 -bottom-5"></div>
          </div>
          
          <h2 className="text-xl font-semibold mb-6 text-green-800 border-b-2 border-green-200 pb-3 flex items-center">
            <svg className="w-5 h-5 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
            </svg>
            Medical Coding System
          </h2>

          {/* Tab Navigation */}
          <div className="mb-6">
            <div className="flex border-b border-green-200">
              <button
                onClick={() => setActiveTab("search")}
                className={`py-2 px-4 font-medium text-sm flex items-center ${
                  activeTab === "search"
                    ? "border-b-2 border-green-600 text-green-700"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                </svg>
                Search Databases
              </button>
              <button
                onClick={() => setActiveTab("map")}
                className={`py-2 px-4 font-medium text-sm flex items-center ${
                  activeTab === "map"
                    ? "border-b-2 border-green-600 text-green-700"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M12 1.586l-4 4v12.828l4-4V1.586zM3.707 3.707A1 1 0 002 4.414V17a1 1 0 001.707.707L6 16.414V5.586L3.707 3.707zM17.707 15.707A1 1 0 0018 15.586V3a1 1 0 00-1.707-.707L14 3.586v10.828l3.707 3.707z" clipRule="evenodd" />
                </svg>
                Map NAMASTE to ICD-11
              </button>
            </div>
          </div>

          {/* Search Tab */}
          {activeTab === "search" && (
            <>
              {/* System Selection */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                  </svg>
                  Select Medical Systems to Search:
                </label>
                <div className="flex flex-wrap gap-2">
                  {["ALL", "AYURVEDA", "UNANI", "SIDDHA"].map((system) => (
                    <button
                      key={system}
                      onClick={() => toggleSystem(system)}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition-colors flex items-center ${
                        selectedSystems.includes(system)
                          ? "bg-green-600 text-white shadow-md"
                          : "bg-green-100 text-green-800 hover:bg-green-200"
                      }`}
                    >
                      {system === "ALL" ? (
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      )}
                      {system}
                    </button>
                  ))}
                </div>
              </div>

              {/* Search Section */}
              <div className="mb-8">
                <div className="flex flex-col sm:flex-row gap-3">
                  <div className="flex-1 relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Enter disease name, code, or term..."
                      className="pl-10 w-full border border-green-300 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all bg-white"
                      disabled={searchLoading}
                    />
                  </div>
                  <button 
                    onClick={handleSearch}
                    disabled={searchLoading}
                    className="bg-gradient-to-r from-green-600 to-green-700 text-white px-6 py-3 rounded-lg text-base font-medium hover:from-green-700 hover:to-green-800 disabled:opacity-70 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg flex items-center justify-center"
                  >
                    {searchLoading ? (
                      <span className="flex items-center">
                        <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Searching...
                      </span>
                    ) : (
                      <>
                        <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                        </svg>
                        Search
                      </>
                    )}
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Mapping Tab */}
          {activeTab === "map" && (
            <div className="mb-8">
              <div className="bg-green-50 p-4 rounded-lg mb-4 border border-green-200">
                <p className="text-sm text-green-800 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  Enter a NAMASTE code to find corresponding ICD-11 codes and information.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="flex-1 relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <input
                    type="text"
                    value={mappingCode}
                    onChange={(e) => setMappingCode(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Enter NAMASTE code (e.g., AYU-001)"
                    className="pl-10 w-full border border-green-300 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all bg-white"
                    disabled={mappingLoading}
                  />
                </div>
                <button 
                  onClick={handleMapping}
                  disabled={mappingLoading}
                  className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-3 rounded-lg text-base font-medium hover:from-green-700 hover:to-emerald-700 disabled:opacity-70 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg flex items-center justify-center"
                >
                  {mappingLoading ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Mapping...
                    </span>
                  ) : (
                    <>
                      <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                      </svg>
                      Map to ICD-11
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

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

          {/* Search Results */}
          {searchResults && activeTab === "search" && (
            <section className="space-y-6">
              <div className="bg-green-50 p-3 rounded-lg border border-green-200">
                <p className="text-sm text-green-800">
                  Searching for: <span className="font-medium">{searchResults.query}</span>
                </p>
              </div>
              {/* Semantic Results */}
              {searchResults.semantic_results && searchResults.semantic_results.length > 0 ? (
                <div className="border border-green-200 rounded-lg p-5 bg-green-50 shadow-sm">
                  <h3 className="font-semibold text-green-800 mb-3 text-lg flex items-center">
                    <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                    </svg>
                    Semantic Results ({searchResults.total_results} found)
                  </h3>
                  <div className="text-sm">
                    {formatSemanticResults(searchResults.semantic_results)}
                  </div>
                </div>
              ) : (
                <div className="border border-green-200 rounded-lg p-5 bg-green-50 shadow-sm">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <span className="text-green-800 font-medium">No results found for "{searchResults.query}"</span>
                  </div>
                  <p className="text-green-700 text-sm mt-2">Try different search terms or check the spelling.</p>
                </div>
              )}
            </section>
          )}

          {/* Mapping Results */}
          {mappingResults && activeTab === "map" && (
            <section className="space-y-6">
              {/* NAMASTE Information */}
              {mappingResults.namaste_info && Object.keys(mappingResults.namaste_info).length > 0 && (
                <div className="border border-green-200 rounded-lg p-5 bg-green-50 shadow-sm">
                  <h3 className="font-semibold text-green-800 mb-3 text-lg">
                    NAMASTE Code: {mappingResults.namaste_code}
                  </h3>
                  <div className="text-sm space-y-2">
                    {Object.entries(mappingResults.namaste_info).map(([key, value]) => {
                      if (key === 'matched_columns') return null;
                      const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                      return (
                        <div key={key} className="flex">
                          <span className="font-medium text-gray-600 min-w-[120px]">{displayKey}:</span>
                          <span className="text-gray-800 flex-1">{value}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* ICD-11 Mapping Results */}
              {mappingResults.icd11_matches && mappingResults.icd11_matches.length > 0 && (
                <div className="border border-green-200 rounded-lg p-5 bg-green-50 shadow-sm">
                  <h3 className="font-semibold text-green-800 mb-3 text-lg">
                    Corresponding ICD-11 Codes ({mappingResults.icd11_matches.length} found)
                  </h3>
                  <div className="text-sm">
                    {formatICD11Results(mappingResults.icd11_matches)}
                  </div>
                </div>
              )}

              {/* No Mapping Results */}
              {(!mappingResults.icd11_matches || mappingResults.icd11_matches.length === 0) && (
                <div className="border border-green-200 rounded-lg p-5 bg-green-50 shadow-sm">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <span className="text-green-800 font-medium">No ICD-11 matches found for "{mappingResults.namaste_code}"</span>
                  </div>
                  <p className="text-green-700 text-sm mt-2">Try a different NAMASTE code or check the format.</p>
                </div>
              )}
            </section>
          )}

          {/* Example Result (shown only when no search has been performed) */}
          {!searchResults && !mappingResults && !searchLoading && !mappingLoading && (
            <section className="border border-green-200 rounded-lg p-5 bg-green-50 shadow-sm">
              <h3 className="font-semibold text-green-800 mb-3 text-lg flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                Example
              </h3>
              <div className="text-sm text-green-800 space-y-2">
                {activeTab === "search" ? (
                  <>
                    <div className="p-3 bg-white rounded-lg border border-green-100 shadow-xs">
                      <span className="font-medium">Search:</span> Enter terms like "fever", "AYU-001", or "diabetes"
                    </div>
                    <div className="p-3 bg-white rounded-lg border border-green-100 shadow-xs">
                      <span className="font-medium">Systems:</span> Select AYURVEDA, UNANI, SIDDHA, or ALL
                    </div>
                  </>
                ) : (
                  <>
                    <div className="p-3 bg-white rounded-lg border border-green-100 shadow-xs">
                      <span className="font-medium">NAMASTE Code:</span> Enter codes like "AYU-001", "SID-102", "UNA-045"
                    </div>
                    <div className="p-3 bg-white rounded-lg border border-green-100 shadow-xs">
                      <span className="font-medium">Result:</span> Get corresponding ICD-11 codes and information
                    </div>
                  </>
                )}
              </div>
            </section>
          )}
        </main>

        {/* Right: Sidebar (1/4) */}
        <aside className="lg:col-span-1 relative">
          <div className="sticky top-6 flex flex-col space-y-6">
            {/* Instructions */}
            <div className="bg-white border border-green-200 rounded-xl shadow-md p-5">
              <h3 className="text-lg font-semibold text-green-800 mb-3 border-b border-green-200 pb-2 flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                </svg>
                {activeTab === "search" ? "Search Instructions" : "Mapping Instructions"}
              </h3>
              {activeTab === "search" ? (
                <ol className="list-decimal list-inside text-sm text-gray-700 space-y-2">
                  <li className="pb-1">Select medical systems to search</li>
                  <li className="pb-1">Enter search term, code, or disease name</li>
                  <li className="pb-1">View results from both NAMASTE and ICD-11</li>
                  <li>Use AI assistant for detailed information</li>
                </ol>
              ) : (
                <ol className="list-decimal list-inside text-sm text-gray-700 space-y-2">
                  <li className="pb-1">Enter a NAMASTE code from any system</li>
                  <li className="pb-1">Get corresponding ICD-11 codes</li>
                  <li className="pb-1">View detailed comparison information</li>
                  <li>Use AI assistant for mapping explanations</li>
                </ol>
              )}
            </div>

            {/* Chatbot */}
            <div className="bg-white border border-green-200 rounded-xl shadow-md p-5">
              <h3 className="text-lg font-semibold text-green-800 mb-3 border-b border-green-200 pb-2 flex items-center">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zM7 8H5v2h2V8zm2 0h2v2H9V8zm6 0h-2v2h2V8z" clipRule="evenodd" />
                </svg>
                AI Assistant
              </h3>
              <div style={{ height: '400px' }}>
                <Chatbot />
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* Footer */}
      <footer className="bg-gradient-to-r from-green-800 to-green-700 text-white border-t-4 border-green-900 py-5 text-center mt-auto relative z-10">
        <div className="max-w-7xl mx-auto px-4">
          <p className="text-sm">© 2025 राष्ट्रीय स्वास्थ्य सूचना विज्ञान. सर्वाधिकार सुरक्षित.</p>
          <p className="text-green-200 text-xs mt-1">© 2025 National Health Informatics. All Rights Reserved.</p>
        </div>
      </footer>

      {/* Add custom styles for animations and patterns */}
      <style jsx>{`
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
}