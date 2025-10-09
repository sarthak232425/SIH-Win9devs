import React from 'react';

export default function MappingResults({ mappingResults, onCopy = () => {} }) {
  if (!mappingResults) return null;

  return (
    <div className="space-y-6">
      <div className="border border-green-200 rounded-lg p-5 bg-green-50 shadow-sm">
        <h3 className="font-semibold text-green-800 mb-3 text-lg">NAMASTE Code: {mappingResults.namaste_code}</h3>
        <div className="text-sm space-y-2">
          {mappingResults.ayurvedic_text && (
            <div className="flex">
              <span className="font-medium text-gray-600 min-w-[120px]">Ayurvedic:</span>
              <span className="text-gray-800 flex-1">{mappingResults.ayurvedic_text}</span>
            </div>
          )}
        </div>
      </div>

      <div className="border border-green-200 rounded-lg p-5 bg-green-50 shadow-sm">
        <h3 className="font-semibold text-green-800 mb-3 text-lg">Corresponding ICD-11 Codes ({mappingResults.icd11_matches.length})</h3>
        <div className="text-sm space-y-3">
          {mappingResults.icd11_matches.map((m, idx) => (
            <div key={idx} className="p-3 bg-white rounded-lg border border-green-100 shadow-xs flex justify-between items-start">
              <div>
                <div className="text-sm font-medium text-gray-700">{m.code || '—'}</div>
                {m.title && <div className="text-xs text-gray-600 mt-1">{m.title}</div>}
                <div className="text-xs text-green-700 mt-2">Rank: {m.rank}</div>                
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
