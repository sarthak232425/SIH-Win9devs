export default function TabNavigation({ activeTab, setActiveTab }) {
  return (
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
        <button
          onClick={() => setActiveTab("problemList")}
          className={`py-2 px-4 font-medium text-sm flex items-center ${
            activeTab === "problemList"
              ? "border-b-2 border-green-600 text-green-700"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" clipRule="evenodd" />
            <path fillRule="evenodd" d="M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6h-3a2 2 0 00-2 2v3H6a2 2 0 01-2-2V5zM14 17v-3a1 1 0 011-1h3v3a2 2 0 01-2 2h-1a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
          Problem List Entry
        </button>
      </div>
    </div>
  );
}
