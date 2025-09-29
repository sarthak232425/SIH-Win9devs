from openai import OpenAI
import psycopg2
import json
import time
from typing import List, Dict
from dotenv import load_dotenv
import os

load_dotenv()

class GeminiLLMMapper:
    def __init__(self, db_config: Dict, gemini_api_key: str, model_name: str = "gemini-2.5-flash"):
        self.db_config = db_config
        
        # Initialize Gemini client using OpenAI compatibility
        self.client = OpenAI(
            api_key=gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        self.model = model_name
        self.conn = psycopg2.connect(**db_config)

    # inside GeminiLLMMapper



    MODULE_CLASSIFY_PROMPT = """
    You are a clinical expert in Ayurveda and ICD-11 Traditional Medicine Module 2.
    Given the NAMASTE code display and definition, pick the single BEST matching high-level module from this list:

    {modules_list}

    Return EXACT JSON:
    {{"module_name": "<one of the module names above>", "confidence": <0-10>, "rationale":"brief justification"}}

    If uncertain, choose the module you think is most likely and set confidence accordingly.
    """



    def classify_module(self, namaste_code: Dict, modules: List[Dict]) -> Dict:
        """Ask Gemini to classify NAMASTE code into one of the modules."""
        modules_list = "\n".join([f"- {m['module_name']} (prefix: {m['code_prefix']})" for m in modules])
        prompt = MODULE_CLASSIFY_PROMPT.format(modules_list=modules_list)
        prompt = prompt + f"\nNAMASTE Code: {namaste_code['code']}\nDisplay: {namaste_code['display']}\nDefinition: {namaste_code['definition']}\n"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=150
            )
            response_text = response.choices[0].message.content
            parsed = json.loads(response_text)
            return parsed  # expects {"module_name": "...", "confidence": 8, "rationale": "..."}
        except Exception as e:
            print(f"Module classification error for {namaste_code['code']}: {e}")
            # fallback: return low confidence 'unknown'
            return {"module_name": None, "confidence": 0, "rationale": f"error: {e}"}



    def get_icd11_codes_for_module(self, module_name: str) -> List[Dict]:
        """Return codes limited to the module prefix; falls back to full list if module is None."""
        with self.conn.cursor() as cur:
            if module_name:
                cur.execute("""
                    SELECT c.code, c.display
                    FROM icd11_tm2_codesystem c
                    JOIN icd11_modules m ON c.code LIKE m.code_prefix || '%'
                    WHERE m.module_name = %s
                    ORDER BY c.code
                """, (module_name,))
                rows = cur.fetchall()
                if rows:
                    return [{"code": r[0], "display": r[1]} for r in rows]

            # fallback: return all TM2 codes
            cur.execute("SELECT code, display FROM icd11_tm2_codesystem ORDER BY code")
            return [{"code": r[0], "display": r[1]} for r in cur.fetchall()]



    def generate_mappings(self, batch_size: int = 10):
        """Main pipeline: classify -> restrict ICD list -> map -> save."""
        modules = []
        with self.conn.cursor() as cur:
            cur.execute("SELECT module_name, code_prefix, description FROM icd11_modules ORDER BY id")
            modules = [{"module_name": r[0], "code_prefix": r[1], "description": r[2]} for r in cur.fetchall()]

        processed = 0
        unmapped = self.get_unmapped_codes(batch_size)
        print(f"Processing batch of {len(unmapped)} unmapped NAMASTE codes...")

        for namaste_code in unmapped:
            # 1) classify module
            cls = self.classify_module(namaste_code, modules)
            module_name = cls.get("module_name")
            module_conf = float(cls.get("confidence", 0))

            print(f"Classifier: {module_name} (conf={module_conf}) — {cls.get('rationale','')}")
            # confidence threshold (tune on validation set)
            CONF_THRESH = 6.0

            # 2) fetch relevant ICD codes
            if module_conf >= CONF_THRESH and module_name:
                icd_candidates = self.get_icd11_codes_for_module(module_name)
                print(f"Using {len(icd_candidates)} ICD codes from module '{module_name}'.")
            else:
                icd_candidates = self.get_icd11_codes()  # global fallback
                print(f"Low classifier confidence ({module_conf}). Falling back to full ICD list ({len(icd_candidates)} codes).")

            # 3) map with Gemini but restrict options to icd_candidates
            mapping = self.map_single_code(namaste_code, icd_candidates)
            mapping['classifier_module'] = module_name
            mapping['classifier_confidence'] = module_conf

            self.save_mapping(mapping)
            processed += 1

            status_icon = "✅" if mapping['icd11_code'] else "⚠️"
            print(f"{status_icon} [{processed}] {namaste_code['code']} → {mapping['icd11_code']} (mapping confidence: {mapping.get('confidence')})")

            time.sleep(1)  # polite rate limit

        print(f"Completed mapping for {processed} codes.")
        self.conn.close()

        # --- Add these methods to GeminiLLMMapper (non-destructive testing utilities) ---



    def map_single_code_no_save(self, namaste_code: Dict, icd11_codes: List[Dict]) -> Dict:
        """
        Wrapper around map_single_code that ensures nothing is saved.
        Returns the mapping dict from the LLM, unmodified.
        """
        # Reuse your existing mapping routine which does not itself save
        # (map_single_code currently returns a mapping dict and save_mapping() does the DB write)
        mapping = self.map_single_code(namaste_code, icd11_codes)
        # Ensure we do not call save_mapping here — purely returns result
        return mapping



    def generate_mappings_test(self, batch_size: int = 10, use_module_classification: bool = True, conf_thresh: float = 6.0):
        """
        Dry-run mapping pipeline:
        - Fetches up to batch_size unmapped NAMASTE codes (same source as production)
        - Optionally classifies into module and restricts candidate ICD list
        - Calls the LLM mapper for each code
        - DOES NOT WRITE to any DB table; returns a list of mapping dicts for inspection

        Returns:
        List[Dict] each mapping contains fields returned by the LLM plus:
            - namaste_code, classifier_module (if used), classifier_confidence
        """
        results = []

        # load modules once
        with self.conn.cursor() as cur:
            cur.execute("SELECT module_name, code_prefix, description FROM icd11_modules ORDER BY id")
            modules = [{"module_name": r[0], "code_prefix": r[1], "description": r[2]} for r in cur.fetchall()]

        unmapped = self.get_unmapped_codes(batch_size)
        print(f"[TEST] Retrieved {len(unmapped)} unmapped codes for dry-run.")

        for namaste_code in unmapped:
            mapping_record = {"namaste_code": namaste_code['code']}

            # 1) classify module (optional)
            if use_module_classification:
                cls = self.classify_module(namaste_code, modules)
                module_name = cls.get("module_name")
                module_conf = float(cls.get("confidence", 0))
                mapping_record['classifier_module'] = module_name
                mapping_record['classifier_confidence'] = module_conf
                mapping_record['classifier_rationale'] = cls.get('rationale', '')
                print(f"[TEST] Classifier: {module_name} (conf={module_conf}) — {cls.get('rationale','')}")
            else:
                module_name = None
                module_conf = 0.0

            # 2) choose ICD candidate set
            if use_module_classification and module_name and module_conf >= conf_thresh:
                icd_candidates = self.get_icd11_codes_for_module(module_name)
                print(f"[TEST] Using {len(icd_candidates)} ICD candidates (module: {module_name}).")
            else:
                icd_candidates = self.get_icd11_codes()
                print(f"[TEST] Using full ICD list ({len(icd_candidates)} codes).")

            # 3) get LLM mapping but DO NOT save
            mapping = self.map_single_code_no_save(namaste_code, icd_candidates)
            # attach classifier metadata for traceability
            mapping['classifier_module'] = mapping_record.get('classifier_module')
            mapping['classifier_confidence'] = mapping_record.get('classifier_confidence')
            mapping['classifier_rationale'] = mapping_record.get('classifier_rationale')

            # 4) collect and print summarized info (no DB writes)
            results.append(mapping)
            status_icon = "✅" if mapping.get('icd11_code') else "⚠️"
            print(f"[TEST] {status_icon} {namaste_code['code']} -> {mapping.get('icd11_code')} (mapping_conf: {mapping.get('confidence')})")

            # Respectful pause for rate-limiting during tests
            time.sleep(0.5)

        print(f"[TEST] Completed dry-run for {len(results)} codes. No DB changes made.")
        return results



    def generate_mappings_test_to_table(self, batch_size: int = 10, table_name: str = "concept_mappings_test", drop_table_first: bool = False):
        """
        Alternative test mode that writes mapping results into a dedicated test table.
        Use ONLY if you want to inspect results by SQL. This keeps production tables untouched.

        Params:
        - batch_size: how many unmapped items to process
        - table_name: name of test table to create/insert into
        - drop_table_first: if True, DROP the test table before creating (useful during development)
        """
        with self.conn.cursor() as cur:
            if drop_table_first:
                cur.execute(f"DROP TABLE IF EXISTS {table_name};")
                self.conn.commit()

            # Create test table (idempotent)
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    namaste_code VARCHAR(50),
                    icd11_code VARCHAR(50),
                    equivalence VARCHAR(50),
                    confidence_score INTEGER,
                    mapping_method VARCHAR(50),
                    llm_rationale TEXT,
                    classifier_module VARCHAR(255),
                    classifier_confidence REAL,
                    classifier_rationale TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.conn.commit()

        # Run dry-run but insert rows into the test table instead of production table
        results = self.generate_mappings_test(batch_size=batch_size)

        with self.conn.cursor() as cur:
            for mapping in results:
                cur.execute(f"""
                    INSERT INTO {table_name} (
                        namaste_code, icd11_code, equivalence, confidence_score,
                        mapping_method, llm_rationale, classifier_module, classifier_confidence, classifier_rationale
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    mapping.get('namaste_code'),
                    mapping.get('icd11_code'),
                    mapping.get('equivalence'),
                    mapping.get('confidence'),
                    'llm_test',
                    mapping.get('rationale'),
                    mapping.get('classifier_module'),
                    mapping.get('classifier_confidence'),
                    mapping.get('classifier_rationale')
                ))
            self.conn.commit()

        print(f"[TEST] Inserted {len(results)} rows into {table_name}.")
        return results



# Usage examples
if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'namaste_terminology'),
        'user': os.getenv('DB_USER', 'your_username'),
        'password': os.getenv('DB_PASSWORD', 'your_password')
    }
    
    # Get your Gemini API key from Google AI Studio: https://aistudio.google.com/
    gemini_api_key = os.getenv('GEMINI_API_KEY', 'YOUR_GEMINI_API_KEY_HERE')

    # Option 1: Using OpenAI-compatible client (recommended)
    mapper = GeminiLLMMapper(db_config, gemini_api_key, model_name="gemini-2.5-flash")
    mapper.generate_mappings(batch_size=1)






    
    # def get_unmapped_codes(self, limit: int) -> List[Dict]:
    #     """Get NAMASTE codes that need mapping"""
    #     with self.conn.cursor() as cur:
    #         cur.execute("""
    #             SELECT nc.code, nc.display, nc.definition
    #             FROM namaste_codesystem nc
    #             LEFT JOIN concept_mappings cm ON nc.code = cm.namaste_code
    #             WHERE cm.namaste_code IS NULL
    #             LIMIT %s
    #         """, (limit,))
            
    #         return [{"code": row[0], "display": row[1], "definition": row[2]} 
    #                for row in cur.fetchall()]
    
    # def get_icd11_codes(self) -> List[Dict]:
    #     """Get all available ICD-11 TM2 codes for context"""
    #     with self.conn.cursor() as cur:
    #         cur.execute("SELECT code, display FROM icd11_tm2_codesystem ORDER BY code")
    #         return [{"code": row[0], "display": row[1]} for row in cur.fetchall()]

    # def generate_mapping_prompt(self, namaste_code: Dict, icd11_codes: List[Dict]) -> str:
    #     """Generate Gemini prompt with ALL available ICD-11 codes"""
        
    #     # Include all codes - Gemini 2.5 Flash can handle it
    #     icd11_list = "\n".join([f"- {code['code']}: {code['display']}" 
    #                         for code in icd11_codes])
        
    #     return f"""
    #         You are a medical terminology expert specializing in Ayurveda and ICD-11 Traditional Medicine Module 2.

    #         Map this NAMASTE Ayurveda code to the most appropriate ICD-11 TM2 code:

    #         NAMASTE Code: {namaste_code['code']}
    #         Display: {namaste_code['display']}
    #         Definition: {namaste_code['definition']}

    #         ALL Available ICD-11 TM2 codes ({len(icd11_codes)} total):
    #         {icd11_list}

    #         Provide your response in this exact JSON format:
    #         {{
    #         "icd11_code": "TM2.XX.XX" or null if no match,
    #         "equivalence": "equivalent|wider|narrower|inexact",
    #         "confidence": 1-10,
    #         "rationale": "Brief explanation of the mapping decision"
    #         }}

    #         If no suitable match exists, set icd11_code to null.
    #         """

    
    # def map_single_code(self, namaste_code: Dict, icd11_codes: List[Dict]) -> Dict:
    #     """Use Gemini to map a single NAMASTE code"""
    #     prompt = self.generate_mapping_prompt(namaste_code, icd11_codes)
        
    #     try:
    #         response = self.client.chat.completions.create(
    #             model=self.model,
    #             messages=[{"role": "user", "content": prompt}],
    #             temperature=0.1,
    #             max_tokens=200
    #         )
            
    #         # Extract response content
    #         response_text = response.choices[0].message.content
    #         print(f"🧠 Gemini response for {namaste_code['code']}: {response}")
    #         # Parse JSON response
    #         result = json.loads(response_text)
    #         result['namaste_code'] = namaste_code['code']
    #         return result
            
    #     except json.JSONDecodeError as e:
    #         print(f"❌ JSON parsing error for {namaste_code['code']}: {e}")
    #         print(f"Raw response: {response_text}")
    #         return {
    #             'namaste_code': namaste_code['code'],
    #             'icd11_code': None,
    #             'equivalence': 'unmatched',
    #             'confidence': 1,
    #             'rationale': f'JSON parsing error: {str(e)}'
    #         }
    #     except Exception as e:
    #         print(f"❌ Error mapping {namaste_code['code']}: {e}")
    #         return {
    #             'namaste_code': namaste_code['code'],
    #             'icd11_code': None,
    #             'equivalence': 'unmatched',
    #             'confidence': 1,
    #             'rationale': f'Gemini API error: {str(e)}'
    #         }
    
    # def save_mapping(self, mapping: Dict):
    #     """Save Gemini-generated mapping to database"""
    #     if mapping['icd11_code']:
    #         with self.conn.cursor() as cur:
    #             cur.execute("""
    #                 INSERT INTO concept_mappings 
    #                 (namaste_code, icd11_code, equivalence, confidence_score, mapping_method, llm_rationale)
    #                 VALUES (%s, %s, %s, %s, %s, %s)
    #                 ON CONFLICT (namaste_code, icd11_code) DO NOTHING
    #             """, (
    #                 mapping['namaste_code'],
    #                 mapping['icd11_code'],
    #                 mapping['equivalence'],
    #                 mapping['confidence'],
    #                 'llm_generated',
    #                 mapping['rationale']
    #             ))
    #     self.conn.commit()
    
    # def generate_mappings(self, batch_size: int = 10):
    #     """Generate mappings for all unmapped codes using Gemini"""
    #     icd11_codes = self.get_icd11_codes()
    #     processed = 0
        
    #     print(f"🚀 Starting Gemini-powered mapping generation using model: {self.model}")
    #     print(f"📊 Available ICD-11 TM2 codes: {len(icd11_codes)}")
        
    #     # while True:
    #     unmapped = self.get_unmapped_codes(batch_size)
    #     # if not unmapped: break
            
    #     print(f"🔄 Processing batch of {len(unmapped)} codes...")
        
    #     for namaste_code in unmapped:
    #         mapping = self.map_single_code(namaste_code, icd11_codes)
    #         self.save_mapping(mapping)
    #         processed += 1
            
    #         status_icon = "✅" if mapping['icd11_code'] else "⚠️"
    #         print(f"{status_icon} [{processed}] {namaste_code['code']} → {mapping['icd11_code']} "
    #                 f"(confidence: {mapping['confidence']})")
            
    #         # Rate limiting - Gemini has generous limits but good practice
    #         time.sleep(1)
        
    #     print(f"🎉 Completed Gemini mapping generation for {processed} codes")
    #     self.conn.close()
