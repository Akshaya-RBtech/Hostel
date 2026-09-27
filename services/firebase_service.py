import os
import json
import requests
import firebase_admin
from firebase_admin import credentials, auth

firebase_app = None

def init_firebase():
    global firebase_app
    if firebase_app:
        return firebase_app
    
    cred_json = os.environ.get('FIREBASE_CREDENTIALS')
    
    if cred_json:
        try:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_app = firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            print(f"ERROR initializing Firebase: {e}")
    else:
        print("WARNING: FIREBASE_CREDENTIALS env var not set. Firebase verification will use REST API fallback.")
    
    return firebase_app

def verify_id_token(id_token):
    """Verifies a Firebase ID token and returns the decoded claims."""
    # MOCK MODE Fallback
    if id_token and id_token.startswith('mock_token_'):
        email = id_token.replace('mock_token_', '')
        return {'email': email, 'uid': 'mock_uid_' + email}

    # Attempt Admin SDK First
    if firebase_app:
        try:
            decoded_token = auth.verify_id_token(id_token, check_revoked=True)
            return decoded_token
        except Exception as e:
            print(f"Firebase token verification failed (Admin): {e}")
            return None

    # Fallback to Identity Toolkit REST API
    api_key = os.environ.get('FIREBASE_API_KEY')
    if not api_key:
        print("Both FIREBASE_CREDENTIALS and FIREBASE_API_KEY are missing.")
        return None

    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}"
        resp = requests.post(url, json={"idToken": id_token})
        data = resp.json()

        if "users" in data and len(data["users"]) > 0:
            user_data = data["users"][0]
            # Map identity provider fields to match Admin SDK shape
            return {
                'email': user_data.get('email'),
                'uid': user_data.get('localId'),
                'email_verified': user_data.get('emailVerified')
            }
        else:
            print(f"Firebase token verification failed (REST): {data}")
            return None
    except Exception as e:
        print(f"Firebase REST token verification exception: {e}")
        return None
