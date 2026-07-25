"""
Drop-in replacement de lots_db.py usando Supabase (PostgreSQL) en lugar de SQLite.

Para activar:
    pip install supabase psycopg[binary]
    export SUPABASE_URL='https://xxxx.supabase.co'
    export SUPABASE_KEY='tu-service-role-key'
    En main.py: cambiar `import lots_db` por `import lots_db_supabase as lots_db`

Tablas SQL (correr UNA VEZ en Supabase SQL Editor):

    CREATE TABLE clients (
        id BIGSERIAL PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE TABLE farms (
        id BIGSERIAL PRIMARY KEY,
        client_id BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        country TEXT, state TEXT, city TEXT,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(client_id, name)
    );
    CREATE TABLE lots (
        id BIGSERIAL PRIMARY KEY,
        farm_id BIGINT NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        crop TEXT,
        geometry_geojson JSONB NOT NULL,
        area_ha REAL NOT NULL,
        useful_area_ha REAL, useful_pct REAL,
        mean_ndvi REAL, std_ndvi REAL,
        quality_score REAL, quality_tag TEXT,
        temporal_stability REAL, n_periods_detected INT,
        source TEXT,
        s2_period_start DATE, s2_period_end DATE,
        version INT NOT NULL DEFAULT 1,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at TIMESTAMPTZ,
        UNIQUE(farm_id, name, version)
    );
    CREATE TABLE lot_history (
        id BIGSERIAL PRIMARY KEY,
        lot_id BIGINT NOT NULL REFERENCES lots(id) ON DELETE CASCADE,
        action TEXT NOT NULL,
        snapshot_json JSONB NOT NULL,
        actor TEXT,
        at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX idx_lots_farm ON lots(farm_id) WHERE deleted_at IS NULL;
    CREATE INDEX idx_history_lot ON lot_history(lot_id);

    -- RLS opcional (recomendado en produccion):
    ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
    ALTER TABLE farms ENABLE ROW LEVEL SECURITY;
    ALTER TABLE lots ENABLE ROW LEVEL SECURITY;
    -- Policy ejemplo (ajusta a tu modelo de auth):
    CREATE POLICY "lots_owner" ON lots FOR ALL TO authenticated USING (true);
"""
from __future__ import annotations

import json
import os

try:
    from supabase import create_client, Client
    SB: Client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_KEY"],
    )
except Exception as e:
    SB = None
    _IMPORT_ERR = str(e)


def _sb():
    if SB is None:
        raise RuntimeError(f"Supabase no inicializado. Setear SUPABASE_URL y SUPABASE_KEY. Error: {_IMPORT_ERR}")
    return SB


def init_db():
    # No-op: las tablas se crean manualmente en Supabase SQL Editor (ver docstring)
    return


def get_or_create_client(name: str, notes: str = "") -> int:
    sb = _sb()
    res = sb.table("clients").select("id").eq("name", name).limit(1).execute()
    if res.data:
        return res.data[0]["id"]
    res = sb.table("clients").insert({"name": name, "notes": notes}).execute()
    return res.data[0]["id"]


def get_or_create_farm(client_id: int, name: str, country=None, state=None, city=None) -> int:
    sb = _sb()
    res = sb.table("farms").select("id").eq("client_id", client_id).eq("name", name).limit(1).execute()
    if res.data:
        return res.data[0]["id"]
    res = sb.table("farms").insert({
        "client_id": client_id, "name": name,
        "country": country, "state": state, "city": city,
    }).execute()
    return res.data[0]["id"]


def save_lot(farm_id, name, geometry_geojson, area_ha, crop=None,
             useful_area_ha=None, useful_pct=None, mean_ndvi=None, std_ndvi=None,
             quality_score=None, quality_tag=None,
             temporal_stability=None, n_periods_detected=None,
             source="AI_DELINEATE", s2_period_start=None, s2_period_end=None,
             actor=None):
    sb = _sb()
    # Soft-delete versiones previas con mismo nombre
    prev = sb.table("lots").select("id, version").eq("farm_id", farm_id) \
        .eq("name", name).is_("deleted_at", "null").order("version", desc=True).limit(1).execute()
    version = (prev.data[0]["version"] + 1) if prev.data else 1
    if prev.data:
        sb.table("lots").update({"deleted_at": "now()"}).eq("id", prev.data[0]["id"]).execute()

    res = sb.table("lots").insert({
        "farm_id": farm_id, "name": name, "crop": crop,
        "geometry_geojson": geometry_geojson, "area_ha": area_ha,
        "useful_area_ha": useful_area_ha, "useful_pct": useful_pct,
        "mean_ndvi": mean_ndvi, "std_ndvi": std_ndvi,
        "quality_score": quality_score, "quality_tag": quality_tag,
        "temporal_stability": temporal_stability, "n_periods_detected": n_periods_detected,
        "source": source,
        "s2_period_start": s2_period_start, "s2_period_end": s2_period_end,
        "version": version,
    }).execute()
    lot_id = res.data[0]["id"]

    sb.table("lot_history").insert({
        "lot_id": lot_id, "action": "CREATE",
        "snapshot_json": geometry_geojson, "actor": actor,
    }).execute()
    return lot_id


def list_clients() -> list[dict]:
    sb = _sb()
    # Supabase no soporta JOINs complejos en API REST sin RPC. Usar 2 queries.
    clients = sb.table("clients").select("*").order("name").execute().data
    farms = sb.table("farms").select("client_id").execute().data
    lots = sb.table("lots").select("farm_id, area_ha").is_("deleted_at", "null").execute().data
    farms_by_client = {}
    for f in farms:
        farms_by_client.setdefault(f["client_id"], []).append(None)
    farm_ids_by_client = {}
    for f in sb.table("farms").select("id, client_id").execute().data:
        farm_ids_by_client.setdefault(f["client_id"], []).append(f["id"])
    for c in clients:
        farm_ids = farm_ids_by_client.get(c["id"], [])
        c["n_farms"] = len(farm_ids)
        c_lots = [l for l in lots if l["farm_id"] in farm_ids]
        c["n_lots"] = len(c_lots)
        c["total_ha"] = sum(l["area_ha"] for l in c_lots)
    return clients


def list_farms(client_id: int = None) -> list[dict]:
    sb = _sb()
    q = sb.table("farms").select("*, clients(name)").order("name")
    if client_id is not None:
        q = q.eq("client_id", client_id)
    farms = q.execute().data
    lots = sb.table("lots").select("farm_id, area_ha").is_("deleted_at", "null").execute().data
    for f in farms:
        f_lots = [l for l in lots if l["farm_id"] == f["id"]]
        f["n_lots"] = len(f_lots)
        f["total_ha"] = sum(l["area_ha"] for l in f_lots)
        f["client_name"] = f.pop("clients")["name"] if f.get("clients") else None
    return farms


def list_lots(farm_id: int = None) -> list[dict]:
    sb = _sb()
    q = sb.table("lots").select("*, farms(name, clients(name))").is_("deleted_at", "null")
    if farm_id is not None:
        q = q.eq("farm_id", farm_id)
    lots = q.execute().data
    for l in lots:
        farm = l.pop("farms", None)
        l["farm_name"] = farm["name"] if farm else None
        l["client_name"] = farm["clients"]["name"] if farm and farm.get("clients") else None
        l["geometry"] = l.pop("geometry_geojson")
    return lots


def export_farm_geojson(farm_id: int) -> dict:
    lots = list_lots(farm_id=farm_id)
    feats = []
    for lot in lots:
        geom = lot["geometry"]
        if geom and geom.get("type") == "FeatureCollection" and geom["features"]:
            f = geom["features"][0]
            feats.append({
                "type": "Feature",
                "geometry": f["geometry"],
                "properties": {k: lot.get(k) for k in [
                    "name","crop","area_ha","useful_area_ha","useful_pct",
                    "quality_score","quality_tag","temporal_stability",
                    "version","source","client_name","farm_name"
                ]}
            })
    return {"type": "FeatureCollection", "features": feats}
