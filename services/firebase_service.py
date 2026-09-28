"""
Firebase Authentication Service for WasteZero
=============================================
Handles Firebase initialization and ID token verification.
Uses Firebase REST API verification (no Admin SDK dependency required).
Falls back gracefully when Firebase credentials are not configured.
"""

import os
import json
import requests

# Firebase configuration from environment
FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', '')
FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID', '')

# Google's public key endpoint for verifying Firebase ID tokens
GOOGLE_CERTS_URL = 'https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com'
FIREBASE_VERIFY_URL = 'https://identitytoolkit.googleapis.com/v1/accounts:lookup'


def init_firebase():
    """Initialize Firebase configuration. Logs status."""
    if FIREBASE_API_KEY and FIREBASE_PROJECT_ID:
        print(f"[Firebase] Configured for project: {FIREBASE_PROJECT_ID}")
    else:
        print("[Firebase] WARNING: Firebase API key or project ID not set. Auth will be limited.")


def verify_id_token(id_token):
    """
    Verify a Firebase ID token using Google's Identity Toolkit REST API.
    Returns the user claims dict if valid, or None if invalid/missing config.
    """
    if not id_token:
        return None
    
    if not FIREBASE_API_KEY:
        print("[Firebase] Cannot verify token: FIREBASE_API_KEY not configured.")
        return None
    
    try:
        # Use Firebase's REST API to look up account info by idToken
        response = requests.post(
            f'{FIREBASE_VERIFY_URL}?key={FIREBASE_API_KEY}',
            json={'idToken': id_token},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('users', [])
            if users:
                user = users[0]
                return {
                    'uid': user.get('localId', ''),
                    'email': user.get('email', ''),
                    'email_verified': user.get('emailVerified', False),
                    'display_name': user.get('displayName', ''),
                    'provider_id': user.get('providerUserInfo', [{}])[0].get('providerId', ''),
                }
        else:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"[Firebase] Token verification failed: {error_msg}")
            return None
            
    except requests.exceptions.Timeout:
        print("[Firebase] Token verification timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[Firebase] Network error during token verification: {e}")
        return None
    except Exception as e:
        print(f"[Firebase] Unexpected error during token verification: {e}")
        return None


def get_firebase_config():
    """
    Return Firebase client configuration for the frontend.
    Only includes public configuration fields (safe to expose).
    """
    return {
        'apiKey': FIREBASE_API_KEY,
        'authDomain': os.environ.get('FIREBASE_AUTH_DOMAIN', ''),
        'projectId': FIREBASE_PROJECT_ID,
        'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET', ''),
        'messagingSenderId': os.environ.get('FIREBASE_MESSAGING_SENDER_ID', ''),
        'appId': os.environ.get('FIREBASE_APP_ID', ''),
        'measurementId': os.environ.get('FIREBASE_MEASUREMENT_ID', ''),
    }
