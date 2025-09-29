import { Pool } from'pg'; 
import dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  user: process.env.DB_USER || 'postgres',
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || 'SIH_ICD11-NAMASTE_mapping',
  password: process.env.DB_PASSWORD || 'Aadya@120305',
  port: process.env.DB_PORT || 5432,
});

async function initializeDatabase() {
  const client = await pool.connect();
  
  try {
    await client.query('BEGIN');

    // NAMASTE CodeSystem table

    await client.query(`
      CREATE TABLE IF NOT EXISTS namaste_codesystem (
        code VARCHAR(50) PRIMARY KEY,
        display VARCHAR(255) NOT NULL,
        definition TEXT,
        category VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // ICD-11 TM2 CodeSystem table
    await client.query(`
      CREATE TABLE IF NOT EXISTS icd11_tm2_codesystem (
        code VARCHAR(50) PRIMARY KEY,
        display VARCHAR(255) NOT NULL,
        definition TEXT,
        parent_code VARCHAR(50),
        URI VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    `);

    // Concept mappings table
    await client.query(`
      CREATE TABLE IF NOT EXISTS concept_mappings (
        id SERIAL PRIMARY KEY,
        namaste_code VARCHAR(50) REFERENCES namaste_codesystem(code),
        icd11_code VARCHAR(50) REFERENCES icd11_tm2_codesystem(code),
        equivalence VARCHAR(20) CHECK (equivalence IN ('equivalent', 'wider', 'narrower', 'inexact', 'unmatched')),
        confidence_score INTEGER CHECK (confidence_score BETWEEN 1 AND 10),
        mapping_method VARCHAR(50) CHECK (mapping_method IN ('llm_generated', 'expert_reviewed', 'manual')),
        llm_rationale TEXT,
        expert_comments TEXT,
        status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        validated_at TIMESTAMP,
        validator_id VARCHAR(100)
      );
    `);

    // Performance indexes
    await client.query('CREATE INDEX IF NOT EXISTS idx_mappings_namaste ON concept_mappings(namaste_code);');
    await client.query('CREATE INDEX IF NOT EXISTS idx_mappings_icd11 ON concept_mappings(icd11_code);');
    await client.query('CREATE INDEX IF NOT EXISTS idx_mappings_status ON concept_mappings(status);');
    await client.query('CREATE INDEX IF NOT EXISTS idx_namaste_display ON namaste_codesystem USING gin(to_tsvector(\'english\', display));');

    await client.query('COMMIT');
    console.log('✅ Database tables created successfully');
    
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('❌ Error creating tables:', err);
    throw err;
  } finally {
    client.release();
  }
}

export { pool, initializeDatabase };
