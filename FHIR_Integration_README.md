# FHIR Condition Resource Integration

This document describes how the problem list entries are automatically converted to FHIR R4 Condition resources and stored as JSON files.

## Overview

When you add an entry to the problem list, the application:
1. Converts the entry to a FHIR R4 Condition resource
2. Validates the FHIR resource
3. Automatically downloads the JSON file to your computer
4. Displays FHIR metadata in the problem list

## FHIR Condition Structure

Each problem list entry is converted to a FHIR Condition resource with the following structure:

```json
{
  "resourceType": "Condition",
  "id": "condition-{timestamp}-{random}",
  "clinicalStatus": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
        "code": "active|inactive|resolved|...",
        "display": "Active|Inactive|Resolved|..."
      }
    ]
  },
  "verificationStatus": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "confirmed|provisional|unconfirmed|...",
        "display": "Confirmed|Provisional|Unconfirmed|..."
      }
    ]
  },
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/condition-category",
          "code": "problem-list-item",
          "display": "Problem List Item"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://namaste.ayush.gov.in/ayurveda",
        "code": "AYU-XXX",
        "display": "NAMASTE Code Description"
      },
      {
        "system": "http://id.who.int/icd/release/11/mms",
        "code": "XX.XXX",
        "display": "ICD-11 Code Description"
      }
    ],
    "text": "Human-readable condition description"
  },
  "subject": {
    "reference": "Patient/abha-12-3456-7890-1234"
  },
  "onsetDateTime": "2025-08-20",
  "recordedDate": "2025-10-05",
  "note": [
    {
      "text": "Clinical notes if provided"
    }
  ],
  "note": [
    {
      "text": "Clinical notes if provided"
    }
  ],
  "extension": [
    {
      "url": "http://namaste.ayush.gov.in/extension/mapping-confidence",
      "valueDecimal": 0.87
    }
  ]
}
```

## Key Features

### Automatic FHIR Generation
- Every problem list entry is automatically converted to FHIR format
- No manual intervention required
- Follows FHIR R4 specification

### Dual Coding System Support
- **NAMASTE System**: `http://namaste.ayush.gov.in/ayurveda`
- **ICD-11 System**: `http://id.who.int/icd/release/11/mms`
- Both codes are included when available

### Patient Reference Format
- ABHA IDs are formatted as: `Patient/abha-XX-XXXX-XXXX-XXXX`
- Automatically formats patient references correctly

### Validation
- All FHIR resources are validated before storage
- Ensures compliance with FHIR specification
- Error handling for invalid data

### File Management
- **Individual Downloads**: Each entry downloads as a separate JSON file
- **Bundle Export**: Export all entries as a FHIR Bundle
- **Filename Format**: `condition_{patientId}_{date}_{id}.json`

### Export Options
- 📥 **Download JSON**: Download individual FHIR Condition files
- 📋 **Copy to Clipboard**: Copy FHIR JSON to clipboard
- 📦 **Export Bundle**: Download all conditions as a FHIR Bundle

## Usage

### Adding a Problem List Entry

1. **Navigate to Problem List Tab**
2. **Click "Add New Entry"**
3. **Fill Required Information**:
   - Patient ABHA ID
   - Condition description
   - Search and select NAMASTE code
   - Optionally select ICD-11 mapping
4. **Preview FHIR**: Click "Preview FHIR" to see the generated JSON
5. **Add Entry**: Click "Add to Problem List & Save FHIR JSON"
6. **Automatic Download**: FHIR JSON file is automatically downloaded

### Exporting Existing Entries

For each problem list entry, you can:
- **Download**: Click the download icon to re-download the FHIR JSON
- **Copy**: Click the copy icon to copy FHIR JSON to clipboard
- **Export All**: Click "Export Bundle" to download all entries as a FHIR Bundle

## File Naming Convention

- **Individual Files**: `condition_123456789012_2025-10-05_condition-1728140400000-abc123def.json`
- **Bundle Files**: `fhir-conditions-bundle-2025-10-05.json`

## FHIR Extensions

No custom extensions are currently used in the FHIR Condition resources.

## Validation Rules

The system validates:
- ✅ Required `resourceType` = "Condition"
- ✅ Unique `id` field
- ✅ Valid `subject` reference
- ✅ At least one `code` (coding or text)
- ✅ Valid `clinicalStatus`
- ✅ FHIR R4 compliance

## Technical Implementation

### Files Structure
```
frontend/
├── src/
│   ├── utils/
│   │   └── fhirUtils.js              # FHIR conversion utilities
│   ├── services/
│   │   └── fhirStorageService.js     # JSON storage service
│   └── components/
│       ├── ProblemListModal.jsx      # Entry form with FHIR preview
│       └── ProblemListSection.jsx    # Display with export options
└── sample-fhir-condition.json        # Example FHIR JSON
```

### Key Functions
- `convertToFhirCondition()`: Converts app entry to FHIR format
- `validateFhirCondition()`: Validates FHIR compliance
- `saveFhirConditionAsJson()`: Downloads individual JSON files
- `saveFhirConditionsBundle()`: Creates and downloads FHIR Bundle

## Browser Compatibility

The FHIR integration uses modern browser APIs:
- File download via Blob API
- Clipboard API for copying JSON
- Requires modern browsers (Chrome 66+, Firefox 63+, Safari 13.1+)

## Integration Benefits

1. **Standards Compliance**: Full FHIR R4 compliance
2. **Interoperability**: Works with any FHIR-compatible system
3. **Data Portability**: JSON files can be imported into other systems
4. **Dual Coding**: Supports both traditional Indian medicine and international codes
5. **Validation**: Ensures data quality and consistency
6. **Automatic Export**: No manual steps required
7. **Bundle Support**: Easy bulk export for multiple patients

## Sample Usage Workflow

1. **Add Patient Entry**:
   - Patient ABHA ID: `12-3456-7890-1234`
   - Condition: `Pitta Vyadhi - Pitta disorder pattern`
   - NAMASTE Code: `AYU-002`
   - ICD-11 Code: `TM2.A02`

2. **Automatic FHIR Generation**:
   - Creates unique condition ID
   - Formats patient reference
   - Includes both coding systems
   - Adds clinical and verification status

3. **File Download**:
   - Downloads: `condition_123456789012_2025-10-05_condition-1728140400000-abc123def.json`
   - File contains complete FHIR Condition resource
   - Ready for import into FHIR servers or EHR systems

This integration ensures that all problem list entries are stored in a standardized, interoperable format that can be easily shared between healthcare systems while maintaining the rich semantic meaning of both NAMASTE and ICD-11 coding systems.