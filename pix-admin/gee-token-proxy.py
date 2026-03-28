"""
GEE Token Proxy — Local server that generates short-lived Earth Engine access tokens
from a service account key file. Runs on port 9101.

Usage: python gee-token-proxy.py
Then in admin: GEEZonesEngine.initGEE('http://localhost:9101/token', 'ee-gisagronomico')
"""
import json
import http.server
import time

# Google OAuth2 token endpoint
TOKEN_URI = 'https://oauth2.googleapis.com/token'
SCOPE = 'https://www.googleapis.com/auth/earthengine'
KEY_PATH = r'C:\Users\Usuario\Desktop\PIXADVISOR\ee-gisagronomico-key.json'

# Load service account key
with open(KEY_PATH) as f:
    key_data = json.load(f)

PROJECT_ID = key_data.get('project_id', 'ee-gisagronomico')

def get_access_token():
    """Generate a short-lived access token using the service account key."""
    import jwt
    import urllib.request
    import urllib.parse

    now = int(time.time())
    payload = {
        'iss': key_data['client_email'],
        'scope': SCOPE,
        'aud': TOKEN_URI,
        'iat': now,
        'exp': now + 3600
    }

    # Sign JWT with private key
    signed_jwt = jwt.encode(payload, key_data['private_key'], algorithm='RS256')

    # Exchange JWT for access token
    data = urllib.parse.urlencode({
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion': signed_jwt
    }).encode()

    req = urllib.request.Request(TOKEN_URI, data=data)
    with urllib.request.urlopen(req) as resp:
        token_data = json.loads(resp.read())
        return token_data['access_token']


class TokenHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/token':
            try:
                token = get_access_token()
                response = json.dumps({
                    'access_token': token,
                    'project': PROJECT_ID,
                    'expires_in': 3600
                })
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response.encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        print(f'[GEE Proxy] {args[0]}')


if __name__ == '__main__':
    # Check if PyJWT is available
    try:
        import jwt
    except ImportError:
        print('Installing PyJWT...')
        import subprocess
        subprocess.check_call(['pip', 'install', 'PyJWT[crypto]'])
        import jwt

    server = http.server.HTTPServer(('localhost', 9101), TokenHandler)
    print(f'GEE Token Proxy running on http://localhost:9101/token')
    print(f'Project: {PROJECT_ID}')
    print(f'Service Account: {key_data["client_email"]}')
    server.serve_forever()
