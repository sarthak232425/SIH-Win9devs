/**
 * MongoDB Problem List Service
 * Handles storing problem list entries in MongoDB database
 */

import { convertToFhirCondition, validateFhirCondition } from '../utils/fhirUtils.js';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

/**
 * Save problem list entry to MongoDB
 * @param {Object} entry - Problem list entry from the application
 * @returns {Promise<Object>} - Result with success status and saved entry
 */
export async function saveProblemListToMongoDB(entry) {
  try {
    // Convert to FHIR format
    const fhirCondition = convertToFhirCondition(entry);
    
    // Validate the FHIR resource
    const validation = validateFhirCondition(fhirCondition);
    if (!validation.isValid) {
      throw new Error(`FHIR validation failed: ${validation.errors.join(', ')}`);
    }
    
    // Create the document to store in MongoDB
    const mongoDocument = {
      // Original entry data
      patientId: entry.patientId,
      condition: entry.condition,
      selectedNamasteCode: entry.selectedNamasteCode,
      selectedIcd11Code: entry.selectedIcd11Code,
      clinicalStatus: entry.clinicalStatus,
      verificationStatus: entry.verificationStatus,
      onsetDate: entry.onsetDate,
      recordedDate: entry.recordedDate || new Date().toISOString().split('T')[0],
      notes: entry.notes,
      
      // FHIR data
      fhirCondition: fhirCondition,
      
      // Metadata
      createdAt: new Date(),
      updatedAt: new Date(),
      fhirId: fhirCondition.id,
      version: "1.0"
    };

    // Send to backend API
    const response = await fetch(`${API_BASE_URL}/api/problem-list`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(mongoDocument)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP ${response.status}: Failed to save to database`);
    }

    const savedEntry = await response.json();

    return {
      success: true,
      entry: savedEntry,
      fhirCondition: fhirCondition,
      message: `Problem list entry saved to MongoDB successfully`,
      mongoId: savedEntry._id
    };
  } catch (error) {
    console.error('Error saving to MongoDB:', error);
    return {
      success: false,
      error: error.message,
      message: `Failed to save to database: ${error.message}`
    };
  }
}

/**
 * Get all problem list entries from MongoDB
 * @returns {Promise<Object>} - Result with entries array
 */
export async function getAllProblemListEntries() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/problem-list`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP ${response.status}: Failed to fetch from database`);
    }

    const entries = await response.json();

    return {
      success: true,
      entries: entries,
      total: entries.length,
      message: `Retrieved ${entries.length} entries from MongoDB`
    };
  } catch (error) {
    console.error('Error fetching from MongoDB:', error);
    return {
      success: false,
      error: error.message,
      entries: [],
      message: `Failed to fetch from database: ${error.message}`
    };
  }
}

/**
 * Get problem list entries for a specific patient
 * @param {string} patientId - Patient ABHA ID
 * @returns {Promise<Object>} - Result with entries array
 */
export async function getPatientProblemList(patientId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/problem-list/patient/${encodeURIComponent(patientId)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP ${response.status}: Failed to fetch patient data`);
    }

    const entries = await response.json();

    return {
      success: true,
      entries: entries,
      patientId: patientId,
      total: entries.length,
      message: `Retrieved ${entries.length} entries for patient ${patientId}`
    };
  } catch (error) {
    console.error('Error fetching patient data from MongoDB:', error);
    return {
      success: false,
      error: error.message,
      entries: [],
      message: `Failed to fetch patient data: ${error.message}`
    };
  }
}

/**
 * Delete a problem list entry from MongoDB
 * @param {string} entryId - MongoDB ObjectId of the entry
 * @returns {Promise<Object>} - Result with success status
 */
export async function deleteProblemListEntry(entryId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/problem-list/${entryId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP ${response.status}: Failed to delete entry`);
    }

    return {
      success: true,
      message: `Entry deleted successfully`
    };
  } catch (error) {
    console.error('Error deleting from MongoDB:', error);
    return {
      success: false,
      error: error.message,
      message: `Failed to delete entry: ${error.message}`
    };
  }
}

/**
 * Get statistics about stored entries
 * @returns {Promise<Object>} - Statistics object
 */
export async function getProblemListStats() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/problem-list/stats`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP ${response.status}: Failed to fetch stats`);
    }

    const stats = await response.json();

    return {
      success: true,
      stats: stats,
      message: 'Statistics retrieved successfully'
    };
  } catch (error) {
    console.error('Error fetching stats from MongoDB:', error);
    return {
      success: false,
      error: error.message,
      stats: {
        totalEntries: 0,
        patientsCount: 0,
        codesUsed: { namaste: 0, icd11: 0 },
        statusBreakdown: {}
      },
      message: `Failed to fetch statistics: ${error.message}`
    };
  }
}

/**
 * Create a preview of the FHIR Condition JSON (doesn't save to database)
 * @param {Object} entry - Problem list entry from the application
 * @returns {Object} - Preview object with formatted JSON and metadata
 */
export function previewFhirCondition(entry) {
  try {
    const fhirCondition = convertToFhirCondition(entry);
    const validation = validateFhirCondition(fhirCondition);
    const jsonString = JSON.stringify(fhirCondition, null, 2);
    
    return {
      success: true,
      fhirCondition,
      jsonString,
      validation,
      metadata: {
        resourceType: fhirCondition.resourceType,
        id: fhirCondition.id,
        patientRef: fhirCondition.subject.reference,
        clinicalStatus: fhirCondition.clinicalStatus.coding[0].code,
        verificationStatus: fhirCondition.verificationStatus.coding[0].code,
        codeCount: fhirCondition.code.coding.length,
        hasNotes: !!fhirCondition.note,
        hasOnset: !!fhirCondition.onsetDateTime,
        willBeSavedTo: "MongoDB Database"
      }
    };
  } catch (error) {
    console.error('Error creating FHIR Condition preview:', error);
    return {
      success: false,
      error: error.message,
      message: `Failed to create FHIR preview: ${error.message}`
    };
  }
}