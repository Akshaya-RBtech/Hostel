import urllib.request
import json
import socket

def check():
    try:
        # Check if server is up
        health = urllib.request.urlopen('http://127.0.0.1:5000/api/health')
        print("[SUCCESS] Platform is reachable (Health OK).")
        
        # Check config fetch
        conf = urllib.request.urlopen('http://127.0.0.1:5000/api/firebase-config')
        data = json.loads(conf.read().decode())
        print(f"[SUCCESS] Firebase Config provided dynamically. Project: {data['projectId']}")
        
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == '__main__':
    check()
