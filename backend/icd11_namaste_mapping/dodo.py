import re
import pandas as pd

# Config
INPUT_XLSX = "NATIONAL_AYURVEDA_MORBIDITY_CODES.xlsx"
SHEET_NAME = "NATIONAL-AYURVEDA-MORBIDITY-COD"
OUTPUT_XLSX = "NATIONAL_AYURVEDA_MORBIDITY_CODES_filled.xlsx"
OUTPUT_CSV  = "missing_descriptions_filled.csv"

# Load
df = pd.read_excel(INPUT_XLSX, sheet_name=SHEET_NAME)

# Normalize column names (some files may vary slightly)
def norm(col):
    return col.strip().replace("\u00a0"," ").replace("\u200b"," ").strip()
df.columns = [norm(c) for c in df.columns]

# Expected columns
col_term = "NAMC_term"
col_short = "Short_definition"

assert col_term in df.columns, f"Missing column: {col_term}"
assert col_short in df.columns, f"Missing column: {col_short}"

# Utility
def empty(x):
    if pd.isna(x):
        return True
    if isinstance(x, str) and x.strip()=="":
        return True
    return False

# Dictionaries for heuristic translation of common stems
DOSHAS = {
    "vata": "vata",
    "pitta": "pitta",
    "kapha": "kapha",
    "sleshma": "kapha",
    "śleṣma": "kapha",
}

STATE_STEMS = [
    ("kopa", "aggravation"),
    ("prakopa", "aggravation"),
    ("vriddhi", "increase"),
    ("vṛddhi", "increase"),
    ("vruddhi", "increase"),
    ("kshaya", "decrease"),
    ("kṣaya", "decrease"),
    ("sanchaya", "accumulation"),
    ("sañcaya", "accumulation"),
    ("prasara", "spreading"),
    ("prāsara", "spreading"),
    ("avastha", "state"),
]

SYSTEM_STEMS = [
    ("srotas", "channels"),
    ("srotovik", "channel disorder"),
    ("vaha", "carrying"),
    ("grahani", "duodenal/intestinal function"),
    ("udara", "abdomen"),
    ("hrid", "heart region"),
    ("hṛd", "heart region"),
    ("prana", "respiratory/vital function"),
    ("prāṇa", "respiratory/vital function"),
]

SYMPTOM_STEMS = [
    ("kasa", "cough"),
    ("kāsa", "cough"),
    ("svasa", "breathlessness"),
    ("śvāsa", "breathlessness"),
    ("jvara", "fever"),
    ("daaha", "burning sensation"),
    ("dāha", "burning sensation"),
    ("shula", "colicky pain"),
    ("śūla", "colicky pain"),
    ("arocaka", "loss of appetite"),
    ("atisara", "diarrhoea"),
    ("atisāra", "diarrhoea"),
    ("chardi", "vomiting"),
    ("chardī", "vomiting"),
    ("ruk", "pain"),
    ("ruja", "pain"),
]

# Simple de-diacritic to ease matching
def ascii_fold(s):
    mappings = {
        "ā":"a","ī":"i","ū":"u","ṛ":"r","ṝ":"r","ḷ":"l","ḹ":"l",
        "ṅ":"n","ñ":"n","ṇ":"n","ṭ":"t","ḍ":"d","ś":"s","ṣ":"s","ḥ":"h","ṃ":"m","ṁ":"m","ŗ":"r"
    }
    out=[]
    for ch in s:
        out.append(mappings.get(ch, ch))
    return "".join(out)

def tokenize(term):
    t = term.lower().strip()
    t = re.sub(r"[^a-zA-ZāĀīĪūŪṛṝḷḹṅÑñṇṭḍśṣḥṃṁŗ\- ]", " ", t)
    t = re.sub(r"[_\-]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def describe_from_term(term):
    if not isinstance(term, str) or term.strip()=="":
        return None

    raw = term.strip()
    t = tokenize(raw)
    ta = ascii_fold(t)

    found_dosha = None
    for k,v in DOSHAS.items():
        if re.search(rf"\b{k}\b", ta):
            found_dosha = v
            break

    found_state = None
    for stem,label in STATE_STEMS:
        if stem in ta:
            found_state = label
            break

    system_hits = []
    for stem,label in SYSTEM_STEMS:
        if stem in ta:
            system_hits.append(label)
    system_text = None
    if system_hits:
        # de-duplicate and join
        system_text = ", ".join(sorted(set(system_hits)))

    # symptom cues
    symptom_hits = []
    for stem,label in SYMPTOM_STEMS:
        if ascii_fold(stem) in ta:
            symptom_hits.append(label)
    symptom_text = None
    if symptom_hits:
        symptom_text = ", ".join(sorted(set(symptom_hits)))

    # Build a compact sentence
    parts = []

    # Primary: dosha + state
    if found_dosha and found_state:
        parts.append(f"{found_state.capitalize()} of {found_dosha} dosha.")
    elif found_dosha:
        parts.append(f"Disorder related to {found_dosha} dosha.")
    elif found_state:
        parts.append(f"{found_state.capitalize()} state of a dosha or tissue.")

    # System scope
    if system_text:
        parts.append(f"Involves {system_text}.")

    # Symptom scope
    if symptom_text:
        parts.append(f"Associated with {symptom_text}.")

    # If nothing matched, use a general fallback by splitting term chunks
    if not parts:
        # Try to split by hyphen/space and produce a plain gloss
        words = [w for w in re.split(r"[\s\-]+", t) if w]
        if words:
            # Use first 1-2 tokens as title-ish
            title = " ".join(words[:2])
            parts.append(f"A condition described in Ayurveda related to '{title}'.")
        else:
            parts.append("Ayurvedic morbid condition as per NAMC classification.")

    # Keep it short and neutral
    sent = " ".join(parts)
    # Ensure reasonable length
    sent = re.sub(r"\s+", " ", sent).strip()
    return sent

# Fill missing short definitions
filled_rows = []
for idx, row in df.iterrows():
    if empty(row.get(col_short, None)):
        desc = describe_from_term(str(row.get(col_term, "") or ""))
        if desc:
            df.at[idx, col_short] = desc
            filled_rows.append(idx)

# Save outputs
with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

if filled_rows:
    df.loc[filled_rows].to_csv(OUTPUT_CSV, index=False)
else:
    # still create an empty file for pipeline consistency
    pd.DataFrame(columns=df.columns).to_csv(OUTPUT_CSV, index=False)

print(f"Filled {len(filled_rows)} rows with generated Short_definition.")
print(f"Wrote: {OUTPUT_XLSX}")
print(f"Wrote: {OUTPUT_CSV}")
