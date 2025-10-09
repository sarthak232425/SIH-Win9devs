# query_server.py
from flask import Flask, request, jsonify
from query import search_icd  # directly use the function you already wrote

app = Flask(__name__)

@app.route("/search_icd", methods=["POST"])
def search_icd_endpoint():
    data = request.get_json()
    query = data.get("query", "")
    ann_top_k = data.get("ann_top_k", 50)
    final_top_k = data.get("final_top_k", 5)

    if not query:
        return jsonify({"success": False, "error": "Query text required"}), 400

    results = search_icd(query, ann_top_k, final_top_k)
    return jsonify({"success": True, "results": results})

if __name__ == "__main__":
    app.run(port=5001, debug=True)
