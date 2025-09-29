const express = require('express');
const dao = require('../database/dao');
const app = express();

app.use(express.json());

// FHIR ConceptMap $translate operation
app.post('/ConceptMap/$translate', async (req, res) => {
  try {
    const params = req.body.parameter || [];
    const codeParam = params.find(p => p.name === 'code');
    const systemParam = params.find(p => p.name === 'system');
    
    if (!codeParam || !systemParam) {
      return res.status(400).json({
        "resourceType": "OperationOutcome",
        "issue": [{
          "severity": "error",
          "code": "required",
          "details": {"text": "Missing required parameters: code, system"}
        }]
      });
    }
    
    const sourceCode = codeParam.valueString;
    const sourceSystem = systemParam.valueUri;
    
    let matches = [];
    
    if (sourceSystem.includes('namaste-ayurveda')) {
      // NAMASTE → ICD-11
      matches = await dao.translateNamasteToIcd11(sourceCode);
    } else if (sourceSystem.includes('icd11')) {
      // ICD-11 → NAMASTE  
      matches = await dao.translateIcd11ToNamaste(sourceCode);
    }
    
    const parameters = matches.map(match => ({
      "name": "match",
      "part": [
        {"name": "equivalence", "valueCode": match.equivalence},
        {"name": "concept", "valueCoding": {
          "system": sourceSystem.includes('namaste') ? 
            "http://id.who.int/icd/release/11/tm2" : 
            "http://example.org/fhir/CodeSystem/namaste-ayurveda",
          "code": match.icd11_code || match.namaste_code,
          "display": match.icd11_display || match.namaste_display
        }}
      ]
    }));
    
    res.json({
      "resourceType": "Parameters",
      "parameter": parameters
    });
    
  } catch (error) {
    console.error('Translation error:', error);
    res.status(500).json({
      "resourceType": "OperationOutcome",
      "issue": [{
        "severity": "error",
        "code": "exception",
        "details": {"text": error.message}
      }]
    });
  }
});

// ValueSet $lookup operation (autocomplete)
app.get('/ValueSet/$lookup', async (req, res) => {
  try {
    const { code, system, filter } = req.query;
    
    let results = [];
    
    if (filter) {
      results = await dao.searchNamasteCodes(filter);
    } else if (code) {
      // Exact lookup
      results = await dao.searchNamasteCodes(code, 1);
    }
    
    const parameters = results.map(result => ({
      "name": "match",
      "part": [
        {"name": "code", "valueString": result.code},
        {"name": "display", "valueString": result.display},
        {"name": "system", "valueUri": "http://example.org/fhir/CodeSystem/namaste-ayurveda"}
      ]
    }));
    
    res.json({
      "resourceType": "Parameters", 
      "parameter": parameters
    });
    
  } catch (error) {
    console.error('Lookup error:', error);
    res.status(500).json({"error": error.message});
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 FHIR Terminology Service running on port ${PORT}`);
});
