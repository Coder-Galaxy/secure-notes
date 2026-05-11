import os
import requests

VAULT_ADDR = os.environ.get('VAULT_ADDR', 'http://vault:8200')
VAULT_TOKEN = os.environ.get('VAULT_TOKEN', 'root')

def get_secret(secret_path, key):
    # e.g. path: secret/data/auth-service
    # If Vault is not reachable or disabled, fallback to env for local dev
    if os.environ.get('DISABLE_VAULT') == 'true':
        return os.environ.get(key)

    try:
        url = f"{VAULT_ADDR}/v1/secret/data/{secret_path}"
        headers = {"X-Vault-Token": VAULT_TOKEN}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data['data']['data'].get(key)
    except Exception as e:
        print(f"Error fetching from vault: {e}")
        # fallback to env
        return os.environ.get(key)
