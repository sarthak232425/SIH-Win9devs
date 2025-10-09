/**
 * FHIR Condition Resource Utilities
 * Functions to convert problem list entries to FHIR R4 Condition resources
 */

/**
 * Generate a unique ID for FHIR resources
 * @returns {string} - Unique identifier
 */
export function generateFhirId() {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substr(2, 9);
  return `condition-${timestamp}-${random}`;
}

/**
 * Format ABHA ID to proper patient reference format
 * @param {string} abhaId - Patient ABHA ID
 * @returns {string} - Formatted patient reference
 */
export function formatPatientReference(abhaId) {
  // Remove any existing formatting and add proper format
  const cleanId = abhaId.replace(/[^0-9]/g, '');
  if (cleanId.length >= 12) {
    const formatted = `${cleanId.substr(0, 2)}-${cleanId.substr(2, 4)}-${cleanId.substr(6, 4)}-${cleanId.substr(10, 4)}`;
    return `Patient/abha-${formatted}`;
  }
  return `Patient/abha-${abhaId}`;
}

/**
 * Convert problem list entry to FHIR Condition resource
 * @param {Object} entry - Problem list entry from the application
 * @returns {Object} - FHIR Condition resource
 */
export function convertToFhirCondition(entry) {
  const fhirId = generateFhirId();
  const patientRef = formatPatientReference(entry.patientId);
  
  // Base FHIR Condition resource structure
  const fhirCondition = {
    resourceType: "Condition",
    id: fhirId,
    clinicalStatus: {
      coding: [
        {
          system: "http://terminology.hl7.org/CodeSystem/condition-clinical",
          code: entry.clinicalStatus || "active",
          display: capitalizeFirst(entry.clinicalStatus || "active")
        }
      ]
    },
    verificationStatus: {
      coding: [
        {
          system: "http://terminology.hl7.org/CodeSystem/condition-ver-status",
          code: entry.verificationStatus || "unconfirmed",
          display: capitalizeFirst(entry.verificationStatus || "unconfirmed")
        }
      ]
    },
    category: [
      {
        coding: [
          {
            system: "http://terminology.hl7.org/CodeSystem/condition-category",
            code: "problem-list-item",
            display: "Problem List Item"
          }
        ]
      }
    ],
    code: {
      coding: [],
      text: entry.condition
    },
    subject: {
      reference: patientRef
    },
    recordedDate: entry.recordedDate || new Date().toISOString().split('T')[0]
  };

  // Add NAMASTE code if available
  if (entry.selectedNamasteCode) {
    fhirCondition.code.coding.push({
      system: "http://namaste.ayush.gov.in/ayurveda",
      code: entry.selectedNamasteCode.code,
      display: entry.selectedNamasteCode.title || entry.selectedNamasteCode.description
    });
  }

  // Add ICD-11 code if available
  if (entry.selectedIcd11Code) {
    fhirCondition.code.coding.push({
      system: "http://id.who.int/icd/release/11/mms",
      code: entry.selectedIcd11Code.code,
      display: entry.selectedIcd11Code.title
    });
  }

  // Add onset date if available
  if (entry.onsetDate) {
    fhirCondition.onsetDateTime = entry.onsetDate;
  }

  // Add notes if available
  if (entry.notes && entry.notes.trim()) {
    fhirCondition.note = [
      {
        text: entry.notes.trim()
      }
    ];
  }

  return fhirCondition;
}

/**
 * Capitalize first letter of a string
 * @param {string} str - String to capitalize
 * @returns {string} - Capitalized string
 */
function capitalizeFirst(str) {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1).replace(/-/g, ' ');
}

/**
 * Validate FHIR Condition resource
 * @param {Object} condition - FHIR Condition resource
 * @returns {Object} - Validation result with isValid boolean and errors array
 */
export function validateFhirCondition(condition) {
  const errors = [];
  
  if (!condition.resourceType || condition.resourceType !== "Condition") {
    errors.push("Missing or invalid resourceType");
  }
  
  if (!condition.id) {
    errors.push("Missing required id field");
  }
  
  if (!condition.subject?.reference) {
    errors.push("Missing required subject reference");
  }
  
  if (!condition.code?.coding?.length && !condition.code?.text) {
    errors.push("Missing required code information");
  }
  
  if (!condition.clinicalStatus?.coding?.length) {
    errors.push("Missing required clinicalStatus");
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}

/**
 * Generate filename for FHIR Condition JSON file
 * @param {Object} condition - FHIR Condition resource
 * @returns {string} - Filename for the JSON file
 */
export function generateConditionFilename(condition) {
  const date = condition.recordedDate || new Date().toISOString().split('T')[0];
  const id = condition.id;
  const patientId = condition.subject.reference.replace('Patient/abha-', '').replace(/-/g, '');
  
  return `condition_${patientId}_${date}_${id}.json`;
}

/**
 * Pretty print FHIR Condition as JSON string
 * @param {Object} condition - FHIR Condition resource
 * @returns {string} - Formatted JSON string
 */
export function formatConditionJson(condition) {
  return JSON.stringify(condition, null, 2);
}