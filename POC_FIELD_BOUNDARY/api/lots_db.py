"""Persistencia SQLite de lotes (cadastro) con audit trail."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "output" / "pixadvisor_lots.db"


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS farms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL REFERENCES clients(id),
        name TEXT NOT NULL,
        country TEXT, state TEXT, city TEXT,
        notes TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(client_id, name)
    );
    CREATE TABLE IF NOT EXISTS lots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farm_id INTEGER NOT NULL REFERENCES farms(id),
        name TEXT NOT NULL,
        crop TEXT,
        geometry_geojson TEXT NOT NULL,    -- FeatureCollection con 1 feature
        area_ha REAL NOT NULL,
        useful_area_ha REAL,
        useful_pct REAL,
        mean_ndvi REAL,
        std_ndvi REAL,
        quality_score REAL,
        quality_tag TEXT,
        temporal_stability REAL,
        n_periods_detected INTEGER,
        source TEXT,                        -- 'AI_DELINEATE' / 'MANUAL_DRAW' / 'EDITED'
        s2_period_start TEXT, s2_period_end TEXT,
        version INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        deleted_at TEXT,
        UNIQUE(farm_id, name, version)
    );
    CREATE TABLE IF NOT EXISTS lot_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER NOT NULL REFERENCES lots(id),
        action TEXT NOT NULL,               -- 'CREATE' / 'EDIT' / 'DELETE'
        snapshot_json TEXT NOT NULL,
        actor TEXT,
        at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_lots_farm ON lots(farm_id) WHERE deleted_at IS NULL;
    CREATE INDEX IF NOT EXISTS idx_history_lot ON lot_history(lot_id);
    """)
    conn.commit()
    conn.close()


def get_or_create_client(name: str, notes: str = "") -> int:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.execute("SELECT id FROM clients WHERE name = ?", (name,)).fetchone()
        if c: return c[0]
        cur = conn.execute("INSERT INTO clients(name, notes) VALUES(?, ?)", (name, notes))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_or_create_farm(client_id: int, name: str, country=None, state=None, city=None) -> int:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.execute("SELECT id FROM farms WHERE client_id=? AND name=?",
                         (client_id, name)).fetchone()
        if c: return c[0]
        cur = conn.execute(
            "INSERT INTO farms(client_id, name, country, state, city) VALUES(?,?,?,?,?)",
            (client_id, name, country, state, city)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def save_lot(farm_id: int, name: str, geometry_geojson: dict, area_ha: float,
             crop: str = None, useful_area_ha: float = None, useful_pct: float = None,
             mean_ndvi: float = None, std_ndvi: float = None,
             quality_score: float = None, quality_tag: str = None,
             temporal_stability: float = None, n_periods_detected: int = None,
             source: str = "AI_DELINEATE",
             s2_period_start: str = None, s2_period_end: str = None,
             actor: str = None) -> int:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        # Soft-delete previas con mismo nombre antes de crear nueva version
        prev = conn.execute(
            "SELECT id, version FROM lots WHERE farm_id=? AND name=? AND deleted_at IS NULL "
            "ORDER BY version DESC LIMIT 1", (farm_id, name)).fetchone()
        version = (prev[1] + 1) if prev else 1
        if prev:
            conn.execute("UPDATE lots SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?", (prev[0],))

        geo_json = json.dumps(geometry_geojson)
        cur = conn.execute("""
            INSERT INTO lots(farm_id, name, crop, geometry_geojson, area_ha,
                             useful_area_ha, useful_pct, mean_ndvi, std_ndvi,
                             quality_score, quality_tag, temporal_stability,
                             n_periods_detected, source,
                             s2_period_start, s2_period_end, version)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (farm_id, name, crop, geo_json, area_ha,
              useful_area_ha, useful_pct, mean_ndvi, std_ndvi,
              quality_score, quality_tag, temporal_stability,
              n_periods_detected, source, s2_period_start, s2_period_end, version))
        lot_id = cur.lastrowid

        conn.execute("""
            INSERT INTO lot_history(lot_id, action, snapshot_json, actor)
            VALUES(?, 'CREATE', ?, ?)
        """, (lot_id, geo_json, actor))
        conn.commit()
        return lot_id
    finally:
        conn.close()


def list_clients() -> list[dict]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute("""
            SELECT c.*, COUNT(DISTINCT f.id) AS n_farms,
                   COUNT(DISTINCT l.id) AS n_lots,
                   COALESCE(SUM(l.area_ha),0) AS total_ha
            FROM clients c
            LEFT JOIN farms f ON f.client_id = c.id
            LEFT JOIN lots l ON l.farm_id = f.id AND l.deleted_at IS NULL
            GROUP BY c.id
            ORDER BY c.name
        """)]
    finally:
        conn.close()


def list_farms(client_id: int = None) -> list[dict]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        sql = """SELECT f.*, c.name AS client_name,
                        COUNT(l.id) AS n_lots,
                        COALESCE(SUM(l.area_ha),0) AS total_ha
                 FROM farms f JOIN clients c ON c.id = f.client_id
                 LEFT JOIN lots l ON l.farm_id = f.id AND l.deleted_at IS NULL"""
        if client_id is not None:
            sql += " WHERE f.client_id = ?"; params = (client_id,)
        else:
            params = ()
        sql += " GROUP BY f.id ORDER BY c.name, f.name"
        return [dict(r) for r in conn.execute(sql, params)]
    finally:
        conn.close()


def list_lots(farm_id: int = None) -> list[dict]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        sql = """SELECT l.*, f.name AS farm_name, c.name AS client_name
                 FROM lots l JOIN farms f ON f.id = l.farm_id
                             JOIN clients c ON c.id = f.client_id
                 WHERE l.deleted_at IS NULL"""
        if farm_id is not None:
            sql += " AND l.farm_id = ?"; params = (farm_id,)
        else:
            params = ()
        sql += " ORDER BY c.name, f.name, l.name"
        rows = [dict(r) for r in conn.execute(sql, params)]
        for r in rows:
            r["geometry"] = json.loads(r.pop("geometry_geojson"))
        return rows
    finally:
        conn.close()


def export_farm_geojson(farm_id: int) -> dict:
    """Exporta todos los lotes activos de una finca como FeatureCollection."""
    lots = list_lots(farm_id=farm_id)
    feats = []
    for lot in lots:
        geom = lot["geometry"]
        # Si guardamos FeatureCollection, tomar la primera feature; si es un Feature, usar
        if geom.get("type") == "FeatureCollection":
            f = geom["features"][0] if geom["features"] else None
            if not f: continue
            feature = {
                "type": "Feature",
                "geometry": f["geometry"],
                "properties": {k: lot[k] for k in [
                    "name","crop","area_ha","useful_area_ha","useful_pct",
                    "quality_score","quality_tag","temporal_stability",
                    "version","source","client_name","farm_name"
                ] if k in lot}
            }
        elif geom.get("type") == "Feature":
            feature = {
                "type": "Feature",
                "geometry": geom["geometry"],
                "properties": {k: lot[k] for k in [
                    "name","crop","area_ha","useful_area_ha","useful_pct",
                    "quality_score","quality_tag","temporal_stability",
                    "version","source","client_name","farm_name"
                ] if k in lot}
            }
        else:
            feature = {"type": "Feature", "geometry": geom, "properties": {"name": lot["name"]}}
        feats.append(feature)
    return {"type": "FeatureCollection", "features": feats}
