import os
import json
import firebase_admin
from firebase_admin import credentials, auth

firebase_app = None

def init_firebase():
    global firebase_app
    if firebase_app:
        return firebase_app
    
    cred_json = os.environ.get('FIREBASE_CREDENTIALS')
    
    # To support local development without real credentials, we just warn if missing.
    if cred_json:
        try:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_app = firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            print(f"ERROR initializing Firebase: {e}")
    else:
        print("WARNING: FIREBASE_CREDENTIALS env var not set. Firebase verification disabled.")
    
    return firebase_app

def verify_id_token(id_token):
    """Verifies a Firebase ID token and returns the decoded claims."""
    # MOCK MODE
    if id_token and id_token.startswith('mock_token_'):
        email = id_token.replace('mock_token_', '')
        return {'email': email, 'uid': 'mock_uid_' + email}

    if not firebase_app:
        return None

    try:
        decoded_token = auth.verify_id_token(id_token, check_revoked=True)
        return decoded_token
    except Exception as e:
        print(f"Firebase token verification failed: {e}")
        return None
