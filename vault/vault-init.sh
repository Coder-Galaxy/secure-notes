#!/bin/bash
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root'

echo "Waiting for vault to start..."
sleep 5

echo "Enabling KV v2 secrets engine..."
vault secrets enable -path=secret kv-v2 || true

echo "Storing secrets..."

# notes-api
vault kv put secret/notes-api DB_PASSWORD=supersecure_db_pass FLASK_SECRET=shared_secret_123

# auth-service
vault kv put secret/auth-service JWT_SECRET=super_secret_jwt_key

# audit-service
vault kv put secret/audit-service ES_PASSWORD=changeme

# sonarqube
vault kv put secret/sonarqube SONAR_TOKEN=sqa_b2a1a8c3e8...

echo "Vault initialization complete."
