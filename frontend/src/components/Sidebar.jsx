import Chatbot from "./Chatbot";

export default function Sidebar({ activeTab }) {
  return (
    <aside className="lg:col-span-1 relative">
      <div className="sticky top-6 flex flex-col space-y-6">
        {/* Instructions */}
        <div className="bg-white border border-green-200 rounded-xl shadow-md p-5">
          <h3 className="text-lg font-semibold text-green-800 mb-3 border-b border-green-200 pb-2 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
            {activeTab === "search" ? "Search Instructions" : 
             activeTab === "map" ? "Mapping Instructions" : "Problem List Instructions"}
          </h3>
          {activeTab === "search" ? (
            <ol className="list-decimal list-inside text-sm text-gray-700 space-y-2">
              <li className="pb-1">Select medical systems to search</li>
              <li className="pb-1">Enter search term, code, or disease name</li>
              <li className="pb-1">View results from both NAMASTE and ICD-11</li>
              <li>Use AI assistant for detailed information</li>
            </ol>
          ) : activeTab === "map" ? (
            <ol className="list-decimal list-inside text-sm text-gray-700 space-y-2">
              <li className="pb-1">Enter a NAMASTE code from any system</li>
              <li className="pb-1">Get corresponding ICD-11 codes</li>
              <li className="pb-1">View detailed comparison information</li>
              <li>Use AI assistant for mapping explanations</li>
            </ol>
          ) : (
            <ol className="list-decimal list-inside text-sm text-gray-700 space-y-2">
              <li className="pb-1">Click "Add New Entry" to create a problem list entry</li>
              <li className="pb-1">Enter patient ABHA ID and condition description</li>
              <li className="pb-1">Search and select appropriate medical codes</li>
              <li className="pb-1">Set clinical and verification status</li>
              <li>Add dates and clinical notes as needed</li>
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
  );
}
