import urllib.request
import json
import urllib.error
import sys

try:
    req = urllib.request.Request("http://localhost:8000/api/incidents/current")
    with urllib.request.urlopen(req) as response:
        print("Status:", response.status)
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
