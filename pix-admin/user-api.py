"""
PIX User API — Central credential management server.
Enables instant sync between PIX Admin (web) and PIX Muestreo APKs.

Endpoints:
  GET    /api/users        → List all users
  POST   /api/users        → Create user
  PUT    /api/users/{id}   → Update user
  DELETE /api/users/{id}   → Deactivate user (soft-delete)
  GET    /api/users/sync   → Sync payload for APKs (version + all active users)

Storage: data/users.db.json (no external DB required)
Port: 9105

Usage:
  python pix-admin/user-api.py
"""

import json
import os
import hashlib
import time
import random
import string
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 9105
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'users.db.json')

# ── Database helpers ──

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    # Seed with default admin
    default_hash = hashlib.sha256('pix2026'.encode()).hexdigest()
    master_hash = hashlib.sha256('pixmaster2026'.encode()).hexdigest()
    db = {
        'version': 1,
        'updatedAt': now_iso(),
        'users': [
            {
                'id': 'admin-default',
                'name': 'Administrador',
                'email': 'admin@pixadvisor.local',
                'passwordHash': default_hash,
                'role': 'admin',
                'active': True,
                'createdAt': now_iso(),
                'updatedAt': now_iso()
            }
        ]
    }
    save_db(db)
    return db

def save_db(db):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    db['version'] = db.get('version', 0) + 1
    db['updatedAt'] = now_iso()
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

def gen_id():
    ts = str(int(time.time() * 1000))
    rnd = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f'user-{ts}-{rnd}'

# ── HTTP Handler ──

class UserAPIHandler(BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def _json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _error(self, msg, status=400):
        self._json_response({'error': msg}, status)

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path.rstrip('/')

        if path == '/api/users':
            db = load_db()
            self._json_response({'users': db['users'], 'total': len(db['users'])})

        elif path == '/api/users/sync':
            db = load_db()
            # Return only active users for APK sync
            active = [u for u in db['users'] if u.get('active', True)]
            self._json_response({
                '_type': 'pix_users_sync',
                'version': db['version'],
                'updatedAt': db['updatedAt'],
                'users': db['users']  # Include all (APK needs deactivated ones too)
            })

        elif path.startswith('/api/users/'):
            user_id = path.split('/')[-1]
            db = load_db()
            user = next((u for u in db['users'] if u['id'] == user_id), None)
            if user:
                self._json_response(user)
            else:
                self._error('User not found', 404)

        elif path == '/api/health':
            self._json_response({'status': 'ok', 'service': 'pix-user-api', 'port': PORT})

        else:
            self._error('Not found', 404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip('/')

        if path == '/api/users':
            body = self._read_body()
            if not body.get('name') or not body.get('email'):
                self._error('name and email required')
                return

            db = load_db()

            # Check duplicate email
            email = body['email'].lower().strip()
            if any(u['email'] == email for u in db['users']):
                self._error('Email already exists', 409)
                return

            # Hash password if provided as plain text (not already hashed)
            pwd_hash = body.get('passwordHash', '')
            if body.get('password'):
                pwd_hash = hashlib.sha256(body['password'].encode()).hexdigest()
            if not pwd_hash:
                self._error('password or passwordHash required')
                return

            user = {
                'id': gen_id(),
                'name': body['name'].strip(),
                'email': email,
                'passwordHash': pwd_hash,
                'role': body.get('role', 'tecnico'),
                'active': True,
                'createdAt': now_iso(),
                'updatedAt': now_iso()
            }
            db['users'].append(user)
            save_db(db)
            print(f'[USER API] Created: {user["name"]} ({user["email"]}) as {user["role"]}')
            self._json_response(user, 201)

        else:
            self._error('Not found', 404)

    def do_PUT(self):
        path = urlparse(self.path).path.rstrip('/')

        if path.startswith('/api/users/'):
            user_id = path.split('/')[-1]
            body = self._read_body()
            db = load_db()

            user = next((u for u in db['users'] if u['id'] == user_id), None)
            if not user:
                self._error('User not found', 404)
                return

            if body.get('name'): user['name'] = body['name'].strip()
            if body.get('email'): user['email'] = body['email'].lower().strip()
            if body.get('password'):
                user['passwordHash'] = hashlib.sha256(body['password'].encode()).hexdigest()
            if body.get('passwordHash'):
                user['passwordHash'] = body['passwordHash']
            if body.get('role'): user['role'] = body['role']
            if 'active' in body: user['active'] = bool(body['active'])
            user['updatedAt'] = now_iso()

            save_db(db)
            print(f'[USER API] Updated: {user["name"]} ({user["email"]})')
            self._json_response(user)

        else:
            self._error('Not found', 404)

    def do_DELETE(self):
        path = urlparse(self.path).path.rstrip('/')

        if path.startswith('/api/users/'):
            user_id = path.split('/')[-1]
            db = load_db()

            user = next((u for u in db['users'] if u['id'] == user_id), None)
            if not user:
                self._error('User not found', 404)
                return

            # Soft delete — set active=false
            user['active'] = False
            user['updatedAt'] = now_iso()
            save_db(db)
            print(f'[USER API] Deactivated: {user["name"]} ({user["email"]})')
            self._json_response({'deleted': True, 'user': user})

        else:
            self._error('Not found', 404)

    def log_message(self, format, *args):
        # Cleaner logging
        pass


if __name__ == '__main__':
    import sys
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print('=== PIX User API - Credential Management ===')
    print(f'Port: {PORT}')
    print(f'DB: {DB_FILE}')

    db = load_db()
    print(f'Users loaded: {len(db["users"])}')
    print(f'Listening on http://localhost:{PORT}/api/users')
    print()

    server = HTTPServer(('0.0.0.0', PORT), UserAPIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...')
        server.server_close()
