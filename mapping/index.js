import { initializeDatabase } from './database/init.js';
import csvLoader from './data-loader/csv-loader.js';

async function setup() {
  try {
    console.log('🚀 Starting NAMASTE-ICD11 Terminology Service setup...');
    
    // 1. Initialize database
    await initializeDatabase();
    
    // 2. Load data (update paths to your CSV files)
    await csvLoader.loadNamasteCodes('public/NAMASTE.csv');
    await csvLoader.loadIcd11Codes('public/ICD-11.csv');
    
    console.log('✅ Setup completed successfully!');
    console.log('💡 Next steps:');
    console.log('  1. Run: python llm-mapper/mapping-generator.py');
    console.log('  2. Review mappings in database');
    console.log('  3. Start server: node server/app.js');
    
  } catch (error) {
    console.error('❌ Setup failed:', error);
    process.exit(1);
  }
}

setup();
