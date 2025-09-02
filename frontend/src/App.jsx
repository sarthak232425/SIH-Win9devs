export default function App() {
  return (
    <div className="min-h-screen w-full bg-gray-100 text-gray-900 flex flex-col">
      {/* Header / Banner */}
      <header className="bg-white border-b border-gray-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-xl sm:text-2xl font-semibold text-blue-900">
            National Medical Coding Portal
          </h1>
          <nav className="mt-2 sm:mt-0">
            <ul className="flex space-x-4 text-sm text-gray-700">
              <li className="hover:underline cursor-pointer">Home</li>
              <li className="hover:underline cursor-pointer">About</li>
              <li className="hover:underline cursor-pointer">Help</li>
            </ul>
          </nav>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 py-6 grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left: Main App (3/4) */}
        <main className="lg:col-span-3 bg-white border rounded-md p-6">
          <h2 className="text-lg font-semibold mb-4 text-blue-800">
            Search and Map Diagnoses
          </h2>

          {/* Search Section */}
          <div className="mb-6 flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              placeholder="Enter disease name (Hindi / English / Traditional)"
              className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-600"
            />
            <button className="bg-blue-700 text-white px-4 py-2 rounded text-sm hover:bg-blue-800">
              Search
            </button>
          </div>

          {/* Results */}
          <section className="border rounded p-4 bg-gray-50 text-sm">
            <h3 className="font-semibold text-gray-800">Example Result</h3>
            <p className="mt-2">
              <span className="font-medium">Disease:</span> Jwara (Fever)
            </p>
            <p>
              <span className="font-medium">NAMASTE Code:</span> NAM-1023
            </p>
            <p>
              <span className="font-medium">ICD-11 Code:</span> ICD11-AX23
            </p>
          </section>
        </main>

        {/* Right: Sidebar (1/4) */}
        <aside className="lg:col-span-1 flex flex-col">
          {/* Instructions */}
          <div className="bg-white border rounded-md p-4 mb-4">
            <h3 className="text-md font-semibold text-blue-800 mb-2">
              Instructions
            </h3>
            <ol className="list-decimal list-inside text-sm text-gray-700 space-y-1">
              <li>Enter a disease name in the search box.</li>
              <li>View mapped NAMASTE & ICD-11 codes.</li>
              <li>Consult the AI assistant for AYUSH, Unani, Siddha details.</li>
            </ol>
          </div>

          {/* Chatbot */}
          <div className="bg-white border rounded-md p-4 flex-1 flex flex-col">
            <h3 className="text-md font-semibold text-blue-800 mb-2">
              AI Assistant
            </h3>
            
            {/* Chat Area */}
            <div className="flex-1 border rounded bg-gray-50 p-3 overflow-y-auto text-sm space-y-2">
              <div className="text-gray-800">
                <span className="font-medium">AI:</span> Welcome. How can I assist?
              </div>
              <div className="text-blue-800 text-right">
                <span className="font-medium">You:</span> What is Jwara?
              </div>
              <div className="text-gray-800">
                <span className="font-medium">AI:</span> Jwara refers to fever.  
                NAMASTE: NAM-1023, ICD-11: AX23.
              </div>
            </div>

            {/* Input */}
            <div className="mt-3 flex">
              <input
                type="text"
                placeholder="Ask the AI..."
                className="flex-1 border border-gray-300 rounded-l px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-600"
              />
              <button className="bg-blue-700 text-white px-4 py-2 rounded-r text-sm hover:bg-blue-800">
                Send
              </button>
            </div>
          </div>
        </aside>
      </div>

      {/* Footer */}
      <footer className="bg-gray-200 text-gray-700 text-sm py-3 text-center border-t border-gray-300">
        © 2025 National Health Informatics. All Rights Reserved.
      </footer>
    </div>
  )
}
