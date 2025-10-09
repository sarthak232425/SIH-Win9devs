// Handles the search tab UI and logic
import React from "react";

export default function SearchSection({
  searchQuery,
  setSearchQuery,
  handleSearch,
  searchLoading,
  selectedSystems,
  toggleSystem,
  handleKeyPress,
}) {
  return (
    <>
      {/* System Selection */}
      <div className="mb-4">
        <label className="text-sm font-medium text-gray-700 mb-2 flex items-center">
          <svg className="w-4 h-4 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
          </svg>
          Select Medical Systems to Search:
        </label>
        <div className="flex flex-wrap gap-2">
          {["ALL","AYURVEDA", "ICD-11"].map((system) => (
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
  );
}
