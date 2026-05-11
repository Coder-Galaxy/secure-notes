import os
import jwt
import bcrypt
import datetime
from flask import Flask, request, jsonify
from models import db, User
from vault_client import get_secret

app = Flask(__name__)

# Config
DB_PATH = os.environ.get('DB_PATH', 'sqlite:///auth.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Fetch secrets
JWT_SECRET = get_secret('auth-service', 'JWT_SECRET') or 'fallback_super_secret_key'

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "User already exists"}), 400

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    new_user = User(username=username, hashed_password=hashed)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, JWT_SECRET, algorithm='HS256')

    return jsonify({"token": token}), 200

@app.route('/validate', methods=['POST'])
def validate():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return jsonify({"valid": True, "user_id": decoded['user_id'], "username": decoded['username']}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired", "valid": False}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token", "valid": False}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
