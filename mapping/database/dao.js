import { pool } from './init.js';

class TerminologyDAO {
  
  // Insert NAMASTE codes from CSV
  async insertNamasteCode(code, display, definition, category = null) {
    const client = await pool.connect();
    try {
      const query = `
        INSERT INTO namaste_codesystem (code, display, definition, category) 
        VALUES ($1, $2, $3, $4) 
        ON CONFLICT (code) DO UPDATE SET 
          display = EXCLUDED.display,
          definition = EXCLUDED.definition,
          category = EXCLUDED.category
      `;
      await client.query(query, [code, display, definition, category]);
    } catch (err) {
      console.error('Error inserting NAMASTE code:', err);
      throw err;
    } finally {
      client.release();
    }
  }

  // Insert ICD-11 TM2 codes
  async insertIcd11Code(code, display, definition, URI, parentCode = null) {
    const client = await pool.connect();
    try {
      const query = `
        INSERT INTO icd11_tm2_codesystem (code, display, definition, parent_code, URI) 
        VALUES ($1, $2, $3, $4, $5) 
        ON CONFLICT (code) DO UPDATE SET 
          display = EXCLUDED.display,
          definition = EXCLUDED.definition,
          parent_code = EXCLUDED.parent_code,
          URI = EXCLUDED.URI
      `;
      await client.query(query, [code, display, definition, parentCode, URI]);
    } catch (err) {
      console.error('Error inserting ICD-11 TM2 code:', err);
      throw err;
    } finally {
      client.release();
    }
  }

  // Insert mapping (from LLM or manual)
  async insertMapping(namasteCode, icd11Code, equivalence, confidence, method, rationale = null) {
    const client = await pool.connect();
    try {
      const query = `
        INSERT INTO concept_mappings 
        (namaste_code, icd11_code, equivalence, confidence_score, mapping_method, llm_rationale)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (namaste_code, icd11_code) DO UPDATE SET
          equivalence = EXCLUDED.equivalence,
          confidence_score = EXCLUDED.confidence_score,
          mapping_method = EXCLUDED.mapping_method,
          llm_rationale = EXCLUDED.llm_rationale
      `;
      await client.query(query, [namasteCode, icd11Code, equivalence, confidence, method, rationale]);
    } catch (err) {
      console.error('Error inserting mapping:', err);
      throw err;
    } finally {
      client.release();
    }
  }

  // FHIR $translate operation: NAMASTE → ICD-11 TM2
  async translateNamasteToIcd11(namasteCode) {
    const client = await pool.connect();
    try {
      const query = `
        SELECT 
          cm.icd11_code,
          icd.display as icd11_display,
          cm.equivalence,
          cm.confidence_score,
          cm.status
        FROM concept_mappings cm
        JOIN icd11_tm2_codesystem icd ON cm.icd11_code = icd.code
        WHERE cm.namaste_code = $1 AND cm.status = 'approved'
        ORDER BY cm.confidence_score DESC
      `;
      const result = await client.query(query, [namasteCode]);
      return result.rows;
    } catch (err) {
      console.error('Error translating NAMASTE to ICD-11:', err);
      return [];
    } finally {
      client.release();
    }
  }

  // Reverse translation: ICD-11 → NAMASTE
  async translateIcd11ToNamaste(icd11Code) {
    const client = await pool.connect();
    try {
      const query = `
        SELECT 
          cm.namaste_code,
          nc.display as namaste_display,
          cm.equivalence,
          cm.confidence_score
        FROM concept_mappings cm
        JOIN namaste_codesystem nc ON cm.namaste_code = nc.code
        WHERE cm.icd11_code = $1 AND cm.status = 'approved'
        ORDER BY cm.confidence_score DESC
      `;
      const result = await client.query(query, [icd11Code]);
      return result.rows;
    } catch (err) {
      console.error('Error translating ICD-11 to NAMASTE:', err);
      return [];
    } finally {
      client.release();
    }
  }

  // Autocomplete search for NAMASTE codes
  async searchNamasteCodes(searchTerm, limit = 20) {
    const client = await pool.connect();
    try {
      const query = `
        SELECT code, display, definition
        FROM namaste_codesystem 
        WHERE display ILIKE $1 OR code ILIKE $1
        ORDER BY 
          CASE WHEN code ILIKE $1 THEN 1 ELSE 2 END,
          display
        LIMIT $2
      `;
      const result = await client.query(query, [`%${searchTerm}%`, limit]);
      return result.rows;
    } catch (err) {
      console.error('Error searching NAMASTE codes:', err);
      return [];
    } finally {
      client.release();
    }
  }

  // Get unmapped NAMASTE codes for LLM processing
  async getUnmappedNamasteCodes(limit = 100) {
    const client = await pool.connect();
    try {
      const query = `
        SELECT nc.code, nc.display, nc.definition
        FROM namaste_codesystem nc
        LEFT JOIN concept_mappings cm ON nc.code = cm.namaste_code
        WHERE cm.namaste_code IS NULL
        ORDER BY nc.code
        LIMIT $1
      `;
      const result = await client.query(query, [limit]);
      return result.rows;
    } catch (err) {
      console.error('Error getting unmapped codes:', err);
      return [];
    } finally {
      client.release();
    }
  }
}

export default new TerminologyDAO();
