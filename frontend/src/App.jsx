import { useState, useRef, useEffect } from "react";
import { mapAPI } from "../services/api";
import { 
  saveProblemListToMongoDB, 
  getAllProblemListEntries, 
  previewFhirCondition 
} from "./services/mongoDBService";
import Header from "./components/Header";
import Footer from "./components/Footer";
import TabNavigation from "./components/TabNavigation";
import SearchSection from "./components/SearchSection";
import Sidebar from "./components/Sidebar";
import MappingSection from "./components/MappingSection";
import ProblemListSection from "./components/ProblemListSection";
import ProblemListModal from "./components/ProblemListModal";
import ErrorMessage from "./components/ErrorMessage";
import ResultsSection from "./components/ResultsSection";

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

  // Problem List Entry state variables
  const [showProblemListModal, setShowProblemListModal] = useState(false);
  const [problemListEntry, setProblemListEntry] = useState({
    patientId: "",
    condition: "",
    selectedNamasteCode: null,
    selectedIcd11Code: null,
    clinicalStatus: "active",
    verificationStatus: "unconfirmed",
    onsetDate: "",
    recordedDate: "",
    notes: ""
  });
  const [problemList, setProblemList] = useState([]);
  const [codeSearchQuery, setCodeSearchQuery] = useState("");
  const [codeSearchResults, setCodeSearchResults] = useState(null);
  const [codeSearchLoading, setCodeSearchLoading] = useState(false);
  
  // ICD-11 mapping state for problem list
  const [icd11MappingResults, setIcd11MappingResults] = useState(null);
  const [icd11MappingLoading, setIcd11MappingLoading] = useState(false);
  const [selectedNamasteCode, setSelectedNamasteCode] = useState(null);

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
    setSearchResults(null);
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
          </div>
        </div>
      );
    });
  };

  // Format ICD-11 results for display
    const formatICD11Results = (results) => {
    if (!results || results.length === 0) return null;

    // Support two shapes: mapping results (with fields like Code/Title) and search results (with .data.code/.data.title)
    return results.map((result, index) => {
      const data = result.data || {};
      const code = data.code || result.Code || result.code || data.Code;
      const title = data.title || result.Title || result.title || data.Title;
      const rank = result.rank ?? result.index ?? null;
      const similarity = result.similarity_score ?? null;

      return (
        <div key={index} className="p-4 bg-white rounded-lg border border-green-200 shadow-xs mb-3">
          <h4 className="font-semibold text-green-700 mb-2">ICD-11 Result {index + 1}</h4>
          <div className="text-sm space-y-1">
            {code && (
              <div className="flex">
                <span className="font-medium text-gray-600 min-w-[120px]">Code:</span>
                <span className="text-gray-800 flex-1">{code}</span>
              </div>
            )}
            {title && (
              <div className="flex">
                <span className="font-medium text-gray-600 min-w-[120px]">Title:</span>
                <span className="text-gray-800 flex-1">{title}</span>
              </div>
            )}
          </div>
        </div>
      );
    });
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

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      if (activeTab === "search") {
        handleCodeSearch();
      } else {
        handleMapping();
      }
    }
  };

  // Problem List Entry handlers
  const handleCodeSearch = async () => {
    if (!codeSearchQuery.trim()) return;
    
    setCodeSearchLoading(true);
    setError("");
    
    try {
      // Only search NAMASTE codes for problem list
      const response = await fetch(`http://127.0.0.1:5000/search_ayurvedic?q=${encodeURIComponent(codeSearchQuery)}&k=5`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `NAMASTE search HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      const newResults = {
        query: codeSearchQuery,
        total_results: data.total_results || (data.results && data.results.length) || 0,
        ayurveda: {
          query: data.query || codeSearchQuery,
          total_results: data.total_results || (data.results && data.results.length) || 0,
          results: data.results || [],
        }
      };

      setCodeSearchResults(newResults);
    } catch (err) {
      setError(err.message || "Failed to search NAMASTE codes. Please try again.");
      console.error("NAMASTE search error:", err);
    } finally {
      setCodeSearchLoading(false);
    }
  };

  // Handle NAMASTE code selection and mapping to ICD-11
  const handleNamasteCodeSelection = async (namasteCode, namasteTitle, namasteDescription) => {
    setSelectedNamasteCode({
      code: namasteCode,
      title: namasteTitle,
      description: namasteDescription
    });
    
    // Auto-map to ICD-11
    setIcd11MappingLoading(true);
    setError("");
    
    try {
      const data = await mapAPI(namasteDescription, 5); // Get top 5 ICD-11 mappings
      
      const icd11Results = (data.icd11_results || data.icd_results || []).map((r, i) => ({
        code: r.code || r.Code || 'N/A',
        title: r.title || r.Title || 'N/A',
        rank: r.rank ?? i + 1,
        similarity_score: r.score ?? r.similarity_score ?? r.similarity ?? null,
        data: r,
      }));
      
      setIcd11MappingResults(icd11Results);
    } catch (err) {
      setError(`Failed to map to ICD-11: ${err.message}`);
      console.error("ICD-11 mapping error:", err);
    } finally {
      setIcd11MappingLoading(false);
    }
  };

  const handleAddToProblemList = async () => {
    if (!problemListEntry.patientId || !problemListEntry.condition) {
      setError("Patient ID and condition are required.");
      return;
    }

    if (!problemListEntry.selectedNamasteCode) {
      setError("Please select a NAMASTE code.");
      return;
    }

    try {
      // Set recorded date to today if not specified
      const newEntry = {
        ...problemListEntry,
        recordedDate: problemListEntry.recordedDate || new Date().toISOString().split('T')[0]
      };

      // Save to MongoDB database
      const saveResult = await saveProblemListToMongoDB(newEntry);
      if (!saveResult.success) {
        throw new Error(saveResult.message);
      }

      // Refresh the problem list from MongoDB
      await loadProblemListFromDatabase();
      
      // Show success message
      console.log(`✅ Problem list entry saved to MongoDB successfully`);
      
      // Reset form and all related state
      setProblemListEntry({
        patientId: "",
        condition: "",
        selectedNamasteCode: null,
        selectedIcd11Code: null,
        clinicalStatus: "active",
        verificationStatus: "unconfirmed",
        onsetDate: "",
        recordedDate: "",
        notes: ""
      });
      setCodeSearchQuery("");
      setCodeSearchResults(null);
      setSelectedNamasteCode(null);
      setIcd11MappingResults(null);
      setShowProblemListModal(false);
      setError("");

    } catch (error) {
      console.error("Error adding to problem list:", error);
      setError(`Failed to add entry: ${error.message}`);
    }
  };

  const handleMapping = async () => {
    if (!mappingCode.trim()) return;
    
    setMappingLoading(true);
    setSearchLoading(false);
    setError("");
    setSearchResults(null);
    
    try {
      // Use centralized API helper which supports GET fallback
      const data = await mapAPI(mappingCode, 3);

      // Normalize different possible response shapes into a single mappingResults object
      // Example server response (from user): { ann_k, ayurvedic_results, icd11_results, k, namaste_code, success }
      const normalized = {
        success: data.success ?? true,
        namaste_code: data.namaste_code ?? mappingCode,
        ann_k: data.ann_k ?? data.k ?? null,
        ayurvedic_text: data.ayurvedic_results ?? data.ayurveda_results ?? null,
        // prefer icd11_results (array of {code, rank, score, title})
        icd11_matches: (data.icd11_results || data.icd_results || data.icd11_matches || []).map((r, i) => {
          // normalize keys
          return {
            code: r.code || r.Code || r.C || null,
            title: r.title || r.Title || r.name || null,
            rank: r.rank ?? i + 1,
            similarity_score: r.score ?? r.similarity_score ?? r.similarity ?? null,
            data: r,
          };
        }),
        // raw payload for debugging
        raw: data,
      };

      setMappingResults(normalized);
    } catch (err) {
      setError(err.message || "Failed to fetch mapping results. Please try again.");
      console.error("Mapping error:", err);
    } finally {
      setMappingLoading(false);
    }
  };

    const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    setMappingLoading(false);
    setError("");
    setMappingResults(null);
    try {
      // Determine which systems to call
      const wantAyurveda = selectedSystems.includes("ALL") || selectedSystems.includes("AYURVEDA");
      const wantICD = selectedSystems.includes("ALL") || selectedSystems.includes("ICD-11");

      // Prepare named promises so we can map results reliably
      const promises = [];
      if (wantAyurveda) {
        promises.push(
          fetch(`http://127.0.0.1:5000/search_ayurvedic?q=${encodeURIComponent(searchQuery)}&k=3`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
          }).then(async (r) => {
            if (!r.ok) {
              const err = await r.json().catch(() => ({}));
              throw new Error(err.detail || `Ayurveda search HTTP ${r.status}`);
            }
            const json = await r.json();
            return { system: 'ayurveda', data: json };
          })
        );
      }
      if (wantICD) {
        promises.push(
          fetch(`http://127.0.0.1:5000/search_icd?q=${encodeURIComponent(searchQuery)}&k=3`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
          }).then(async (r) => {
            if (!r.ok) {
              const err = await r.json().catch(() => ({}));
              throw new Error(err.detail || `ICD search HTTP ${r.status}`);
            }
            const json = await r.json();
            return { system: 'icd', data: json };
          })
        );
      }

      const settled = await Promise.allSettled(promises);

      const newResults = { query: searchQuery, total_results: 0 };
      // initialize empty shapes
      if (wantAyurveda) newResults.ayurveda = { query: searchQuery, total_results: 0, results: [] };
      if (wantICD) newResults.icd = { query: searchQuery, total_results: 0, results: [] };

      for (const res of settled) {
        if (res.status === 'fulfilled' && res.value) {
          const { system, data } = res.value;
          if (system === 'ayurveda') {
            newResults.ayurveda = {
              query: data.query || searchQuery,
              total_results: data.total_results || (data.results && data.results.length) || 0,
              results: data.results || [],
            };
            newResults.total_results += newResults.ayurveda.total_results;
          } else if (system === 'icd') {
            newResults.icd = {
              query: data.query || searchQuery,
              total_results: data.total_results || (data.results && data.results.length) || 0,
              results: data.results || [],
            };
            newResults.total_results += newResults.icd.total_results;
          }
        } else if (res.status === 'rejected') {
          // Collect error but don't block other results
          console.warn('Search promise rejected:', res.reason);
        }
      }

      setSearchResults(newResults);
    } catch (err) {
      setError(err.message || "Failed to fetch search results. Please try again.");
      console.error("Search error:", err);
    } finally {
      setSearchLoading(false);
    }
  };


  // Load problem list entries from MongoDB
  const loadProblemListFromDatabase = async () => {
    try {
      const result = await getAllProblemListEntries();
      if (result.success) {
        // Handle pagination structure if returned
        const entries = result.entries?.entries || result.entries || [];
        setProblemList(entries);
      } else {
        console.error("Failed to load problem list:", result.message);
        setError(`Failed to load problem list: ${result.message}`);
      }
    } catch (error) {
      console.error("Error loading problem list:", error);
      setError(`Failed to load problem list: ${error.message}`);
    }
  };

  // Load stored problem list entries on component mount
  useEffect(() => {
    loadProblemListFromDatabase();
  }, []);

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
      
      <Header />

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
          <TabNavigation activeTab={activeTab} setActiveTab={setActiveTab} />

          {/* Search Tab */}
          {activeTab === "search" && (
            <SearchSection
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
              handleSearch={handleSearch}
              searchLoading={searchLoading}
              selectedSystems={selectedSystems}
              toggleSystem={toggleSystem}
              handleKeyPress={handleKeyPress}
            />
          )}

          {/* Mapping Tab */}
          {activeTab === "map" && (
            <MappingSection
              mappingCode={mappingCode}
              setMappingCode={setMappingCode}
              handleMapping={handleMapping}
              mappingLoading={mappingLoading}
              handleKeyPress={handleKeyPress}
            />
          )}

          {/* Problem List Entry Tab */}
          {activeTab === "problemList" && (
            <ProblemListSection
              problemList={problemList}
              setShowProblemListModal={setShowProblemListModal}
              setProblemList={setProblemList}
            />
          )}

          {/* Error Message */}
          <ErrorMessage error={error} />

          {/* Results Section */}
          <ResultsSection
            searchResults={searchResults}
            mappingResults={mappingResults}
            activeTab={activeTab}
            selectedSystems={selectedSystems}
            formatSemanticResults={formatSemanticResults}
            formatICD11Results={formatICD11Results}
            copyToClipboard={copyToClipboard}
          />

          {/* Example Result (shown only when no search has been performed) */}
          {!searchResults && !mappingResults && !searchLoading && !mappingLoading && activeTab !== "problemList" && (
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
        <Sidebar activeTab={activeTab} />
      </div>

      {/* Problem List Modal */}
      <ProblemListModal
        showProblemListModal={showProblemListModal}
        setShowProblemListModal={setShowProblemListModal}
        problemListEntry={problemListEntry}
        setProblemListEntry={setProblemListEntry}
        codeSearchQuery={codeSearchQuery}
        setCodeSearchQuery={setCodeSearchQuery}
        codeSearchResults={codeSearchResults}
        setCodeSearchResults={setCodeSearchResults}
        codeSearchLoading={codeSearchLoading}
        handleCodeSearch={handleCodeSearch}
        handleAddToProblemList={handleAddToProblemList}
        selectedNamasteCode={selectedNamasteCode}
        setSelectedNamasteCode={setSelectedNamasteCode}
        icd11MappingResults={icd11MappingResults}
        setIcd11MappingResults={setIcd11MappingResults}
        icd11MappingLoading={icd11MappingLoading}
        handleNamasteCodeSelection={handleNamasteCodeSelection}
      />

      {/* Footer */}
      <Footer />

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