import os
import requests
import threading
from flask import Flask, request, jsonify, g
from models import db, Note
from vault_client import get_secret
from sqlalchemy import text

app = Flask(__name__)

# Vulnerability 2: Hardcoded secret (SonarQube/Trivy should catch this)
HARDCODED_SECRET_KEY = "my_super_secret_dev_key_123"

DB_PATH = os.environ.get('DB_PATH', 'sqlite:///notes.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL', 'http://localhost:5001')
AUDIT_SERVICE_URL = os.environ.get('AUDIT_SERVICE_URL', 'http://localhost:5002')

with app.app_context():
    db.create_all()

def send_audit_log(action, username, details):
    def _send():
        try:
            payload = {"action": action, "username": username, "details": details}
            requests.post(f"{AUDIT_SERVICE_URL}/log", json=payload, timeout=2)
        except Exception as e:
            print(f"Failed to send audit log: {e}")
    threading.Thread(target=_send).start()

@app.before_request
def require_auth():
    if request.endpoint == 'health':
        return

    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        resp = requests.post(f"{AUTH_SERVICE_URL}/validate", headers={'Authorization': auth_header}, timeout=2)
        if resp.status_code != 200:
            return jsonify({"error": "Unauthorized"}), 401
        
        user_data = resp.json()
        g.user_id = user_data.get('user_id')
        g.username = user_data.get('username')
    except Exception as e:
        print(f"Auth service error: {e}")
        return jsonify({"error": "Auth service unavailable"}), 503

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({"error": "Missing title or content"}), 400

    new_note = Note(user_id=g.user_id, title=title, content=content)
    db.session.add(new_note)
    db.session.commit()

    send_audit_log("CREATE_NOTE", g.username, f"Created note {new_note.id}")
    return jsonify({"message": "Note created", "id": new_note.id}), 201

@app.route('/notes', methods=['GET'])
def get_notes():
    notes = Note.query.filter_by(user_id=g.user_id).all()
    result = [{"id": n.id, "title": n.title, "content": n.content} for n in notes]
    send_audit_log("LIST_NOTES", g.username, "Listed notes")
    return jsonify(result), 200

@app.route('/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    # Vulnerability 1: SQL Injection
    # Using raw SQL with string interpolation instead of parameterized queries
    # ZAP or SonarQube should catch this.
    try:
        query = text(f"SELECT * FROM notes WHERE id = {note_id} AND user_id = {g.user_id}")
        result = db.session.execute(query).fetchone()
        
        if not result:
            return jsonify({"error": "Note not found"}), 404

        note_data = {
            "id": result[0],
            "user_id": result[1],
            "title": result[2],
            "content": result[3]
        }
        send_audit_log("READ_NOTE", g.username, f"Read note {note_id}")
        return jsonify(note_data), 200
    except Exception as e:
        return jsonify({"error": "Database error"}), 500

@app.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.get_json()
    note = Note.query.filter_by(id=note_id, user_id=g.user_id).first()
    
    if not note:
        return jsonify({"error": "Note not found"}), 404
        
    note.title = data.get('title', note.title)
    note.content = data.get('content', note.content)
    db.session.commit()
    
    send_audit_log("UPDATE_NOTE", g.username, f"Updated note {note_id}")
    return jsonify({"message": "Note updated"}), 200

@app.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = Note.query.filter_by(id=note_id, user_id=g.user_id).first()
    if not note:
        return jsonify({"error": "Note not found"}), 404

    db.session.delete(note)
    db.session.commit()
    send_audit_log("DELETE_NOTE", g.username, f"Deleted note {note_id}")
    return jsonify({"message": "Note deleted"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
