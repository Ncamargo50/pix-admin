"""
PIX Monitor — SQLite Storage Layer
Replaces JSON file storage with SQLite for reliability and concurrent access.
Tables: monitoring_results, monitoring_config, alerts, scheduler_jobs
"""

import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pix_monitor.db')

def _connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    return conn

def init_db():
    """Create tables if they don't exist. Safe to call on every startup."""
    conn = _connect()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS fields (
            id TEXT PRIMARY KEY,
            client_id TEXT,
            name TEXT NOT NULL,
            crop TEXT DEFAULT 'soja',
            area_ha REAL,
            planting_date TEXT,
            boundary TEXT,
            monitoring_active INTEGER DEFAULT 0,
            last_check TEXT,
            last_result TEXT,
            check_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (client_id) REFERENCES clients(id)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            field_id TEXT,
            type TEXT NOT NULL,
            severity TEXT DEFAULT 'warning',
            description TEXT,
            data TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now')),
            read_at TEXT,
            actioned_at TEXT,
            FOREIGN KEY (field_id) REFERENCES fields(id)
        );

        CREATE TABLE IF NOT EXISTS monitoring_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id TEXT NOT NULL,
            checked_at TEXT DEFAULT (datetime('now')),
            stage TEXT,
            data_source TEXT DEFAULT 'S2_SR',
            result_json TEXT,
            FOREIGN KEY (field_id) REFERENCES fields(id)
        );

        CREATE TABLE IF NOT EXISTS timeseries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id TEXT NOT NULL,
            date TEXT NOT NULL,
            values_json TEXT,
            image_date TEXT,
            FOREIGN KEY (field_id) REFERENCES fields(id)
        );

        CREATE TABLE IF NOT EXISTS scheduler_jobs (
            id TEXT PRIMARY KEY,
            field_id TEXT NOT NULL,
            interval_days INTEGER DEFAULT 14,
            enabled INTEGER DEFAULT 1,
            last_run TEXT,
            next_run TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (field_id) REFERENCES fields(id)
        );

        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_fields_client ON fields(client_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_field ON alerts(field_id);
        CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
        CREATE INDEX IF NOT EXISTS idx_results_field ON monitoring_results(field_id);
        CREATE INDEX IF NOT EXISTS idx_timeseries_field ON timeseries(field_id);
        CREATE INDEX IF NOT EXISTS idx_scheduler_next ON scheduler_jobs(next_run);
    ''')
    conn.close()
    print(f'[DB] SQLite initialized: {DB_PATH}')


# ── Client CRUD ──

def get_clients():
    conn = _connect()
    rows = conn.execute('SELECT * FROM clients ORDER BY name').fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_client(client_id):
    conn = _connect()
    row = conn.execute('SELECT * FROM clients WHERE id=?', (client_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def save_client(client):
    conn = _connect()
    conn.execute('''INSERT OR REPLACE INTO clients (id, name, phone, email, notes, updated_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))''',
        (client['id'], client['name'], client.get('phone'), client.get('email'), client.get('notes')))
    conn.commit()
    conn.close()

def delete_client(client_id):
    conn = _connect()
    conn.execute('DELETE FROM clients WHERE id=?', (client_id,))
    conn.commit()
    conn.close()


# ── Field CRUD ──

def get_fields(client_id=None):
    conn = _connect()
    if client_id:
        rows = conn.execute('SELECT * FROM fields WHERE client_id=? ORDER BY name', (client_id,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM fields ORDER BY name').fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get('boundary'):
            d['boundary'] = json.loads(d['boundary'])
        if d.get('last_result'):
            d['last_result'] = json.loads(d['last_result'])
        d['monitoring'] = {'active': bool(d.pop('monitoring_active', 0)),
                           'checkCount': d.pop('check_count', 0),
                           'lastCheck': d.pop('last_check', None)}
        d['plantingDate'] = d.pop('planting_date', None)
        d['clientId'] = d.pop('client_id', None)
        d['areaHa'] = d.pop('area_ha', None)
        result.append(d)
    return result

def get_field(field_id):
    conn = _connect()
    row = conn.execute('SELECT * FROM fields WHERE id=?', (field_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    if d.get('boundary'):
        d['boundary'] = json.loads(d['boundary'])
    if d.get('last_result'):
        d['last_result'] = json.loads(d['last_result'])
    return d

def save_field(field):
    conn = _connect()
    boundary_json = json.dumps(field.get('boundary')) if field.get('boundary') else None
    last_result_json = json.dumps(field.get('last_result')) if field.get('last_result') else None
    monitoring = field.get('monitoring', {})
    conn.execute('''INSERT OR REPLACE INTO fields
        (id, client_id, name, crop, area_ha, planting_date, boundary,
         monitoring_active, last_check, last_result, check_count, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))''',
        (field['id'], field.get('clientId'), field.get('name'), field.get('crop', 'soja'),
         field.get('areaHa'), field.get('plantingDate'), boundary_json,
         1 if monitoring.get('active') else 0, monitoring.get('lastCheck'),
         last_result_json, monitoring.get('checkCount', 0)))
    conn.commit()
    conn.close()

def delete_field(field_id):
    conn = _connect()
    conn.execute('DELETE FROM timeseries WHERE field_id=?', (field_id,))
    conn.execute('DELETE FROM alerts WHERE field_id=?', (field_id,))
    conn.execute('DELETE FROM monitoring_results WHERE field_id=?', (field_id,))
    conn.execute('DELETE FROM scheduler_jobs WHERE field_id=?', (field_id,))
    conn.execute('DELETE FROM fields WHERE id=?', (field_id,))
    conn.commit()
    conn.close()


# ── Alerts ──

def get_alerts(field_id=None, status=None):
    conn = _connect()
    query = 'SELECT * FROM alerts'
    params = []
    clauses = []
    if field_id:
        clauses.append('field_id=?')
        params.append(field_id)
    if status:
        clauses.append('status=?')
        params.append(status)
    if clauses:
        query += ' WHERE ' + ' AND '.join(clauses)
    query += ' ORDER BY created_at DESC'
    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get('data'):
            d['data'] = json.loads(d['data'])
        result.append(d)
    return result

def save_alert(alert):
    conn = _connect()
    data_json = json.dumps(alert.get('data')) if alert.get('data') else None
    conn.execute('''INSERT OR REPLACE INTO alerts
        (id, field_id, type, severity, description, data, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (alert['id'], alert.get('fieldId') or alert.get('field_id'),
         alert['type'], alert.get('severity', 'warning'),
         alert.get('description'), data_json, alert.get('status', 'active')))
    conn.commit()
    conn.close()

def update_alert(alert_id, updates):
    conn = _connect()
    sets = []
    params = []
    for key, val in updates.items():
        if key in ('status', 'read_at', 'actioned_at'):
            sets.append(f'{key}=?')
            params.append(val)
    if sets:
        params.append(alert_id)
        conn.execute(f'UPDATE alerts SET {", ".join(sets)} WHERE id=?', params)
        conn.commit()
    conn.close()

def delete_alert(alert_id):
    conn = _connect()
    conn.execute('DELETE FROM alerts WHERE id=?', (alert_id,))
    conn.commit()
    conn.close()


# ── Monitoring Results ──

def save_monitoring_result(field_id, stage, result_data, data_source='S2_SR'):
    conn = _connect()
    conn.execute('''INSERT INTO monitoring_results (field_id, stage, data_source, result_json)
        VALUES (?, ?, ?, ?)''',
        (field_id, stage, data_source, json.dumps(result_data, ensure_ascii=False)))
    conn.commit()
    conn.close()

def get_monitoring_history(field_id, limit=50):
    conn = _connect()
    rows = conn.execute('''SELECT * FROM monitoring_results WHERE field_id=?
        ORDER BY checked_at DESC LIMIT ?''', (field_id, limit)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get('result_json'):
            d['result'] = json.loads(d['result_json'])
            del d['result_json']
        result.append(d)
    return result


# ── Timeseries ──

def save_timeseries_entry(field_id, date, values, image_date=None):
    conn = _connect()
    conn.execute('''INSERT INTO timeseries (field_id, date, values_json, image_date)
        VALUES (?, ?, ?, ?)''',
        (field_id, date, json.dumps(values), image_date))
    conn.commit()
    conn.close()

def get_timeseries(field_id, limit=200):
    conn = _connect()
    rows = conn.execute('''SELECT * FROM timeseries WHERE field_id=?
        ORDER BY date ASC LIMIT ?''', (field_id, limit)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get('values_json'):
            d['values'] = json.loads(d['values_json'])
            del d['values_json']
        result.append(d)
    return result


# ── Scheduler Jobs ──

def get_scheduler_jobs(enabled_only=False):
    conn = _connect()
    query = 'SELECT * FROM scheduler_jobs'
    if enabled_only:
        query += ' WHERE enabled=1'
    query += ' ORDER BY next_run ASC'
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_scheduler_job(job):
    conn = _connect()
    conn.execute('''INSERT OR REPLACE INTO scheduler_jobs
        (id, field_id, interval_days, enabled, last_run, next_run)
        VALUES (?, ?, ?, ?, ?, ?)''',
        (job['id'], job['field_id'], job.get('interval_days', 14),
         1 if job.get('enabled', True) else 0,
         job.get('last_run'), job.get('next_run')))
    conn.commit()
    conn.close()

def delete_scheduler_job(job_id):
    conn = _connect()
    conn.execute('DELETE FROM scheduler_jobs WHERE id=?', (job_id,))
    conn.commit()
    conn.close()


# ── Config ──

def get_config(key, default=None):
    conn = _connect()
    row = conn.execute('SELECT value FROM config WHERE key=?', (key,)).fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row['value'])
        except (json.JSONDecodeError, TypeError):
            return row['value']
    return default

def set_config(key, value):
    conn = _connect()
    conn.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)',
        (key, json.dumps(value) if not isinstance(value, str) else value))
    conn.commit()
    conn.close()

def get_all_config():
    conn = _connect()
    rows = conn.execute('SELECT * FROM config').fetchall()
    conn.close()
    result = {}
    for r in rows:
        try:
            result[r['key']] = json.loads(r['value'])
        except (json.JSONDecodeError, TypeError):
            result[r['key']] = r['value']
    return result


# ── Migration from JSON ──

def migrate_from_json(json_db_path):
    """One-time migration from monitoring.db.json to SQLite."""
    if not os.path.exists(json_db_path):
        return False
    try:
        with open(json_db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        init_db()
        conn = _connect()

        for client in data.get('clients', []):
            conn.execute('''INSERT OR IGNORE INTO clients (id, name, phone, email, notes)
                VALUES (?, ?, ?, ?, ?)''',
                (client['id'], client.get('name', ''), client.get('phone'),
                 client.get('email'), client.get('notes')))

        for field in data.get('fields', []):
            monitoring = field.get('monitoring', {})
            conn.execute('''INSERT OR IGNORE INTO fields
                (id, client_id, name, crop, area_ha, planting_date, boundary,
                 monitoring_active, last_check, check_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (field['id'], field.get('clientId'), field.get('name', ''),
                 field.get('crop', 'soja'), field.get('areaHa'),
                 field.get('plantingDate'),
                 json.dumps(field.get('boundary')) if field.get('boundary') else None,
                 1 if monitoring.get('active') else 0,
                 monitoring.get('lastCheck'), monitoring.get('checkCount', 0)))

        for alert in data.get('alerts', []):
            conn.execute('''INSERT OR IGNORE INTO alerts (id, field_id, type, severity, description, status)
                VALUES (?, ?, ?, ?, ?, ?)''',
                (alert['id'], alert.get('fieldId'), alert.get('type', 'anomaly'),
                 alert.get('severity', 'warning'), alert.get('description'),
                 alert.get('status', 'active')))

        for field_id, entries in data.get('timeseries', {}).items():
            for entry in entries:
                conn.execute('''INSERT INTO timeseries (field_id, date, values_json, image_date)
                    VALUES (?, ?, ?, ?)''',
                    (field_id, entry.get('date', ''), json.dumps(entry.get('values', {})),
                     entry.get('imageDate')))

        conn.commit()
        conn.close()
        print(f'[DB] Migrated from JSON: {len(data.get("clients",[]))} clients, {len(data.get("fields",[]))} fields')
        return True
    except Exception as e:
        print(f'[DB] Migration error: {e}')
        return False
