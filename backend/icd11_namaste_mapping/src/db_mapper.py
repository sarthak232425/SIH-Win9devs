# import psycopg2
# from psycopg2.extras import execute_values
# from query import search_icd  # reuse your hybrid search

# # -------------------
# # DB Connection
# # -------------------
# conn = psycopg2.connect(
#     dbname="SIH_ICD11-NAMASTE_mapping",
#     user="postgres",
#     password="Aadya@120305",
#     host="localhost",
#     port="5432"
# )
# cur = conn.cursor()

# # -------------------
# # Fetch NAMASTE codes
# # -------------------
# cur.execute("SELECT code, definition FROM namaste_codes")
# namaste_rows = cur.fetchall()

# print(f"🔄 Found {len(namaste_rows)} NAMASTE codes")

# # -------------------
# # Build mappings
# # -------------------
# batch = []
# for idx, (code, definition) in enumerate(namaste_rows, start=1):
#     query_text = definition if definition else code
#     results = search_icd(query_text, ann_top_k=50, final_top_k=3)

#     for r in results:
#         batch.append((
#             code,
#             definition,
#             r["code"],
#             r["title"],
#             r["score"]
#         ))

#     if idx % 100 == 0:  # commit every 100 NAMASTE codes to reduce memory load
#         insert_sql = """
#             INSERT INTO mappings
#             (namaste_code, namaste_definition, icd_code, icd_title, score)
#             VALUES %s
#             ON CONFLICT (namaste_code, icd_code) DO NOTHING;
#         """
#         execute_values(cur, insert_sql, batch)
#         conn.commit()
#         print(f"✅ Inserted batch up to row {idx}")
#         batch = []

# # Insert any leftovers
# if batch:
#     insert_sql = """
#         INSERT INTO mappings
#         (namaste_code, namaste_definition, icd_code, icd_title, score)
#         VALUES %s
#         ON CONFLICT (namaste_code, icd_code) DO NOTHING;
#     """
#     execute_values(cur, insert_sql, batch)
#     conn.commit()
#     print(f"✅ Inserted final batch")

# cur.close()
# conn.close()
# print("🎉 All mappings processed successfully!")

# src/batch_mapper.py
import psycopg2
from query import search_icd

DB_CONFIG = {
    "dbname": "SIH_ICD11-NAMASTE_mapping",
    "user": "your_user",
    "password": "your_password",
    "host": "localhost",
    "port": 5432,
}

# conn = psycopg2.connect(
#     dbname="SIH_ICD11-NAMASTE_mapping",
#     user="postgres",
#     password="Aadya@120305",
#     host="localhost",
#     port="5432"
# )

BATCH_SIZE = 100  # process 100 namaste codes per slot

def fetch_namaste_codes(offset, limit):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT code, definition
        FROM namaste_codes
        ORDER BY code
        OFFSET %s LIMIT %s
    """, (offset, limit))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def mappings_exist(namaste_code):
    """Check if the namaste_code already has 3 mappings stored."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM mappings
        WHERE namaste_code = %s
    """, (namaste_code,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count >= 3

def insert_mappings(namaste_code, namaste_definition, icd_results):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for r in icd_results[:3]:  # only top 3 matches
        cur.execute("""
            INSERT INTO mappings (namaste_code, namaste_definition, icd_code, icd_title, score)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (namaste_code, icd_code) DO UPDATE
            SET score = EXCLUDED.score,
                icd_title = EXCLUDED.icd_title,
                namaste_definition = EXCLUDED.namaste_definition
        """, (namaste_code, namaste_definition, r["code"], r["title"], r["score"]))

    conn.commit()
    cur.close()
    conn.close()

def process_all():
    offset = 0
    while True:
        rows = fetch_namaste_codes(offset, BATCH_SIZE)
        if not rows:
            break

        print(f"🔎 Processing slot {offset} → {offset+len(rows)}")
        for code, definition in rows:
            if mappings_exist(code):
                print(f"⏩ Skipping {code}, already mapped.")
                continue

            icd_matches = search_icd(definition, ann_top_k=50, final_top_k=5)
            insert_mappings(code, definition, icd_matches)
            print(f"✅ Inserted/Updated mappings for {code}")

        offset += BATCH_SIZE
        print(f"✅ Completed slot up to {offset}")

if __name__ == "__main__":
    process_all()
