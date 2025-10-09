export default function Header() {
  return (
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
  );
}
