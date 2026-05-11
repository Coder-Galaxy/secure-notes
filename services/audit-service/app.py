import os
from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
from datetime import datetime
from vault_client import get_secret

app = Flask(__name__)

# Fetch ES password from vault
ES_PASSWORD = get_secret('audit-service', 'ES_PASSWORD') or 'changeme'
ES_HOST = os.environ.get('ES_HOST', 'http://localhost:9200')

es = Elasticsearch(
    [ES_HOST],
    basic_auth=("elastic", ES_PASSWORD) if ES_PASSWORD != 'changeme' else None,
    verify_certs=False
)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/log', methods=['POST'])
def log_event():
    data = request.get_json()
    action = data.get('action')
    username = data.get('username', 'anonymous')
    details = data.get('details')

    if not action:
        return jsonify({"error": "Action is required"}), 400

    doc = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "username": username,
        "details": details
    }

    try:
        es.index(index="audit-logs", document=doc)
        return jsonify({"message": "Log recorded"}), 201
    except Exception as e:
        print(f"Elasticsearch error: {e}")
        # Even if ES fails, we might just print it and not fail the request
        # to prevent breaking the main app.
        return jsonify({"error": "Failed to record log"}), 500

@app.route('/logs/<username>', methods=['GET'])
def get_logs(username):
    try:
        query = {
            "query": {
                "match": {
                    "username": username
                }
            },
            "sort": [
                {"timestamp": {"order": "desc"}}
            ]
        }
        res = es.search(index="audit-logs", body=query)
        hits = res['hits']['hits']
        logs = [hit['_source'] for hit in hits]
        return jsonify(logs), 200
    except Exception as e:
        print(f"Elasticsearch error: {e}")
        return jsonify({"error": "Failed to fetch logs"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
