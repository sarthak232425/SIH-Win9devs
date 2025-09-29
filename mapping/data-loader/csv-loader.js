import fs from 'fs';
import csv from 'csv-parser';
import dao from '../database/dao.js';

class CSVLoader {
  
  // Load NAMASTE codes from CSV
  async loadNamasteCodes(filePath) {
    console.log('📥 Loading NAMASTE codes from CSV...');
    let count = 0;
    
    return new Promise((resolve, reject) => {
      fs.createReadStream(filePath)
        .pipe(csv())
        .on('data', async (row) => {
          try {
            if(row.Long_definition === '' || row.Long_definition === null) return;
            
            let namasteCode = row.NAMC_CODE.trim();
            
            // Function to check if a code is ICD-11 (starts with S, length 4, no dashes)
            const isIcd11Code = (code) => {
              return code.startsWith('S') && code.length === 4 && !code.includes('-');
            };
            
            // Extract main code (before brackets) and bracket content
            const bracketMatch = namasteCode.match(/^([^(]+)(?:\(([^)]+)\))?/);
            const mainCode = bracketMatch ? bracketMatch[1].trim() : namasteCode;
            const bracketContent = bracketMatch ? bracketMatch[2] : null;
            
            if (isIcd11Code(mainCode)) {
              // Main code is ICD-11, extract NAMASTE code from brackets
              if (bracketContent) {
                namasteCode = bracketContent.trim();
              } else {
                // No NAMASTE code found in brackets, skip this row
                return;
              }
            } else {
              // Main code is already NAMASTE, use it directly
              namasteCode = mainCode;
            }
            
            await dao.insertNamasteCode(
              namasteCode,
              row.NAMC_term_DEVANAGARI,
              row.Long_definition,
              row.category
            );
            count++;
            if (count % 100 === 0) {
              console.log(`📊 Loaded ${count} NAMASTE codes...`);
            }
          } catch (err) {
            console.error(`❌ Error loading row: ${JSON.stringify(row)}`, err);
          }
        })
        .on('end', () => {
          console.log(`✅ Finished loading ${count} NAMASTE codes`);
          resolve(count);
        })
        .on('error', reject);
    });
  }
  

  // Load ICD-11 TM2 codes from CSV
  async loadIcd11Codes(filePath) {
    console.log('📥 Loading ICD-11 TM2 codes from CSV...');
    let count = 0;
  
    return new Promise((resolve, reject) => {
      fs.createReadStream(filePath)
        .pipe(csv())
        .on('data', async (row) => {
          try {
            
            // Reject rows with missing code field (non-leaf nodes)
            if (!row.Code || row.Code.trim() === '') {
              return; // Skip this row
            }

  
            // Remove leading dashes from display/title
            // This regex removes any number of leading "- " (dash and space)
            const cleanTitle = row.Title.replace(/^(-\s*)+/, '');
  
            await dao.insertIcd11Code(
              row.Code,
              cleanTitle,
              row.definition,
              row['Foundation URI'],
              row.parent_code
            );
            count++;
            if (count % 50 === 0) {
              console.log(`📊 Loaded ${count} ICD-11 codes...`);
            }
          } catch (err) {
            console.error(`❌ Error loading row: ${JSON.stringify(row)}`, err);
          }
        })
        .on('end', () => {
          console.log(`✅ Finished loading ${count} ICD-11 TM2 codes`);
          resolve(count);
        })
        .on('error', reject);
    });
  }
  
}

export default new CSVLoader();
