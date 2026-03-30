"""
PIX Monitor — Crop Monitoring API Server
Satellite-based crop health monitoring with automatic anomaly detection.

Port: 9102
Auth: Service account via GEE token proxy (9101)
Credentials: Shared with user-api.py (9105)
Storage: monitoring.db.json (local JSON)

Endpoints:
  POST /api/clients              → Create client
  GET  /api/clients              → List clients
  POST /api/fields               → Register field with boundary
  GET  /api/fields               → List fields
  PUT  /api/fields/{id}          → Update field
  POST /api/fields/{id}/activate → Activate monitoring
  POST /api/fields/{id}/check    → Run anomaly check (GEE)
  GET  /api/alerts               → List all alerts
  GET  /api/timeseries/{id}      → Get time series for field
  POST /api/reports/{id}         → Generate PDF + KMZ
  GET  /api/health               → Health check
"""

import json
import os
import sys
import time
import random
import string
import hashlib
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PORT = 9102
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'monitoring.db.json')

# GEE Service Account Key
GEE_KEY_PATH = r'C:\Users\Usuario\Desktop\PIXADVISOR\ee-gisagronomico-key.json'
GEE_PROJECT = 'ee-gisagronomico'

# ============================================================
# CROP PHENOLOGY CONFIGURATION
# ============================================================

CROP_PHENOLOGY = {
    "soja": {
        "name": "Soja",
        "cycle_days": 130,
        "stages": {
            "VE_V3":  {"days": [0, 25],    "indices": ["MSAVI2","NDVI","SAVI","OSAVI"],            "desc": "Emergencia (VE-V3)"},
            "V4_V8":  {"days": [25, 50],   "indices": ["NDVI","NDRE","GNDVI","MTCI"],              "desc": "Desarrollo vegetativo (V4-V8)"},
            "R1_R2":  {"days": [50, 70],   "indices": ["NDRE","MTCI","kNDVI","EVI","NDMI"],        "desc": "Floracion (R1-R2)"},
            "R3_R5":  {"days": [70, 100],  "indices": ["NDRE","kNDVI","S2REP","CCCI","NDMI"],      "desc": "Llenado de grano (R3-R5)"},
            "R6_R8":  {"days": [100, 130], "indices": ["NDMI","PSRI","NBR2","NDRE"],               "desc": "Maduracion (R6-R8)"},
        },
        "critical_stages": ["R1_R2", "R3_R5"],
    },
    "maiz": {
        "name": "Maiz",
        "cycle_days": 150,
        "stages": {
            "VE_V6":  {"days": [0, 30],    "indices": ["MSAVI2","NDVI","SAVI","OSAVI"],            "desc": "Emergencia (VE-V6)"},
            "V8_V12": {"days": [30, 55],   "indices": ["NDVI","NDRE","GNDVI","MTCI"],              "desc": "Crecimiento rapido (V8-V12)"},
            "VT_R1":  {"days": [55, 75],   "indices": ["kNDVI","NDRE","MTCI","EVI","S2REP"],       "desc": "Floracion (VT-R1)"},
            "R2_R4":  {"days": [75, 105],  "indices": ["kNDVI","NDRE","S2REP","CCCI","NDMI"],      "desc": "Llenado (R2-R4)"},
            "R5_R6":  {"days": [105, 150], "indices": ["NDMI","PSRI","NBR2","MSI"],                "desc": "Maduracion (R5-R6)"},
        },
        "critical_stages": ["VT_R1", "R2_R4"],
    },
    "cana": {
        "name": "Cana de Azucar",
        "cycle_days": 365,
        "stages": {
            "BROTACION":       {"days": [0, 90],    "indices": ["MSAVI2","OSAVI","BSI","NDVI","SAVI","NDRE","EVI2","NBR2"], "desc": "Brotacion (0-3 meses)"},
            "MACOLLAJE":       {"days": [90, 150],  "indices": ["NDRE","NDVI","RECI","CIre","MTCI","CCCI","OSAVI","GNDVI"],"desc": "Macollaje (3-5 meses)"},
            "GRAN_CRECIMIENTO":{"days": [150, 240], "indices": ["NDRE","RECI","CIre","IRECI","MTCI","S2REP","kNDVI","EVI","NDMI"], "desc": "Gran crecimiento (5-8 meses)"},
            "ELONGACION":      {"days": [240, 330], "indices": ["NDRE","RECI","CIre","IRECI","MTCI","S2REP","kNDVI","CCCI","NDMI","MSI"], "desc": "Elongacion (8-11 meses)"},
            "MADURACION":      {"days": [330, 365], "indices": ["NDMI","NDRE","RECI","PSRI","MSI","NBR2","S2REP","EVI2"], "desc": "Maduracion (11-12 meses)"},
        },
        "critical_stages": ["GRAN_CRECIMIENTO", "ELONGACION"],
    },
    "trigo": {
        "name": "Trigo",
        "cycle_days": 140,
        "stages": {
            "EMERGENCIA":  {"days": [0, 20],    "indices": ["MSAVI2","NDVI","SAVI"],               "desc": "Emergencia"},
            "MACOLLAJE":   {"days": [20, 50],   "indices": ["NDVI","NDRE","GNDVI","MTCI"],         "desc": "Macollaje"},
            "ENCANADO":    {"days": [50, 80],   "indices": ["NDRE","kNDVI","EVI","MTCI","S2REP"],  "desc": "Encañazon"},
            "ESPIGADO":    {"days": [80, 100],  "indices": ["NDRE","kNDVI","S2REP","CCCI","NDMI"], "desc": "Espigado-floracion"},
            "LLENADO":     {"days": [100, 130], "indices": ["NDMI","PSRI","NDRE","NBR2"],          "desc": "Llenado de grano"},
            "MADURACION":  {"days": [130, 140], "indices": ["NDMI","PSRI","NBR2","MSI"],           "desc": "Maduracion"},
        },
        "critical_stages": ["ESPIGADO", "LLENADO"],
    },
    "arroz": {
        "name": "Arroz",
        "cycle_days": 140,
        "stages": {
            "EMERGENCIA":  {"days": [0, 25],    "indices": ["MSAVI2","NDVI","SAVI"],               "desc": "Emergencia"},
            "MACOLLAJE":   {"days": [25, 55],   "indices": ["NDVI","NDRE","EVI","GNDVI"],          "desc": "Macollaje"},
            "PANICULACION":{"days": [55, 80],   "indices": ["NDRE","kNDVI","MTCI","EVI","NDMI"],   "desc": "Paniculacion"},
            "FLORACION":   {"days": [80, 100],  "indices": ["NDRE","kNDVI","S2REP","CCCI","NDMI"], "desc": "Floracion"},
            "LLENADO":     {"days": [100, 140], "indices": ["NDMI","PSRI","NDRE","NBR2"],          "desc": "Llenado-maduracion"},
        },
        "critical_stages": ["FLORACION", "LLENADO"],
    },
    "girasol": {
        "name": "Girasol",
        "cycle_days": 120,
        "stages": {
            "EMERGENCIA": {"days": [0, 20],   "indices": ["MSAVI2","NDVI","SAVI"],                 "desc": "Emergencia"},
            "VEGETATIVO": {"days": [20, 50],  "indices": ["NDVI","NDRE","GNDVI","EVI"],            "desc": "Crecimiento vegetativo"},
            "FLORACION":  {"days": [50, 75],  "indices": ["NDRE","kNDVI","EVI2","NDMI","OSAVI"],   "desc": "Floracion (R1-R4)"},
            "LLENADO":    {"days": [75, 100], "indices": ["NDRE","NDMI","NBR2","PSRI"],            "desc": "Llenado"},
            "MADURACION": {"days": [100, 120],"indices": ["NDMI","PSRI","NBR2","MSI"],             "desc": "Maduracion"},
        },
        "critical_stages": ["FLORACION", "LLENADO"],
    },
}

# ============================================================
# DATABASE HELPERS
# ============================================================

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"clients": [], "fields": [], "alerts": [], "timeseries": {}, "version": 0}

def save_db(db):
    db['version'] = db.get('version', 0) + 1
    db['updatedAt'] = now_iso()
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def gen_id(prefix=''):
    ts = str(int(time.time() * 1000))
    rnd = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f'{prefix}{ts}-{rnd}'

# ============================================================
# PHENOLOGY ENGINE
# ============================================================

def detect_stage(crop, planting_date_str):
    """Detect current phenological stage based on planting date."""
    try:
        planting = datetime.fromisoformat(planting_date_str.replace('Z', '+00:00'))
    except:
        planting = datetime.strptime(planting_date_str[:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)

    days_since = (datetime.now(timezone.utc) - planting).days
    config = CROP_PHENOLOGY.get(crop)
    if not config:
        return None, None, None

    for stage_key, stage_cfg in config['stages'].items():
        d0, d1 = stage_cfg['days']
        if d0 <= days_since <= d1:
            return stage_key, stage_cfg, days_since

    # Beyond cycle
    last_stage = list(config['stages'].keys())[-1]
    return last_stage, config['stages'][last_stage], days_since

# ============================================================
# GEE ENGINE (Python Earth Engine API)
# ============================================================

_ee_initialized = False

def init_gee():
    global _ee_initialized
    if _ee_initialized:
        return True
    try:
        import ee
        if os.path.exists(GEE_KEY_PATH):
            credentials = ee.ServiceAccountCredentials(None, GEE_KEY_PATH)
            ee.Initialize(credentials, project=GEE_PROJECT)
        else:
            ee.Authenticate()
            ee.Initialize(project=GEE_PROJECT)
        _ee_initialized = True
        print(f'[GEE] Initialized: project={GEE_PROJECT}')
        return True
    except Exception as e:
        print(f'[GEE] Init failed: {e}')
        return False

def compute_monitoring(field):
    """
    Run full monitoring check for a field using GEE.
    Returns: { stage, indices, timeseries, anomalies, cloudFree }
    """
    import ee

    if not init_gee():
        return {"error": "GEE not available"}

    boundary = field['boundary']
    crop = field.get('crop', 'soja')
    planting_date = field.get('plantingDate', '2025-11-15')

    # Detect current phenological stage
    stage_key, stage_cfg, days = detect_stage(crop, planting_date)
    if not stage_cfg:
        return {"error": f"Unknown crop: {crop}"}

    indices_needed = stage_cfg['indices']

    # Build GEE geometry
    coords = boundary['coordinates'] if boundary['type'] == 'Polygon' else boundary['coordinates'][0]
    aoi = ee.Geometry.Polygon(coords)

    # Date range: last 30 days for current check, 2 years for baseline
    now = ee.Date(datetime.now(timezone.utc).strftime('%Y-%m-%d'))
    recent_start = now.advance(-30, 'day')
    baseline_start = now.advance(-730, 'day')  # 2 years
    baseline_end = now.advance(-30, 'day')

    # Cloud mask function
    def mask_clouds(img):
        scl = img.select('SCL')
        mask = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6))  # Only veg, soil, water
        return img.updateMask(mask)

    # ── STRICT CLOUD FILTER: 100% coverage required ──
    def is_cloud_free(img):
        """Check if image has 0% clouds within the field boundary."""
        scl = img.select('SCL')
        cloud_mask = scl.eq(8).Or(scl.eq(9)).Or(scl.eq(10)).Or(scl.eq(3)).Or(scl.eq(11))
        cloud_pct = cloud_mask.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=aoi,
            scale=20,
            bestEffort=True
        ).get('SCL')
        return img.set('cloud_pct', cloud_pct)

    # Get recent cloud-free images
    s2_recent = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(aoi)
        .filterDate(recent_start, now)
        .map(is_cloud_free)
        .filter(ee.Filter.eq('cloud_pct', 0))  # 100% cloud-free only
        .map(mask_clouds)
        .sort('system:time_start', False))  # newest first

    recent_count = s2_recent.size().getInfo()

    if recent_count == 0:
        # Fallback: relax to <5% clouds
        s2_recent = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(aoi)
            .filterDate(recent_start, now)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 5))
            .map(mask_clouds)
            .sort('system:time_start', False))
        recent_count = s2_recent.size().getInfo()

    # Compute indices on latest image
    def compute_indices(img):
        b2 = img.select('B2').divide(10000)
        b3 = img.select('B3').divide(10000)
        b4 = img.select('B4').divide(10000)
        b5 = img.select('B5').divide(10000)
        b6 = img.select('B6').divide(10000)
        b7 = img.select('B7').divide(10000)
        b8 = img.select('B8').divide(10000)
        b8a = img.select('B8A').divide(10000)
        b11 = img.select('B11').divide(10000)
        b12 = img.select('B12').divide(10000)

        ndvi = b8.subtract(b4).divide(b8.add(b4)).rename('NDVI')
        ndre = b8a.subtract(b5).divide(b8a.add(b5)).rename('NDRE')
        evi = b8.subtract(b4).multiply(2.5).divide(b8.add(b4.multiply(6)).subtract(b2.multiply(7.5)).add(1)).rename('EVI')
        ndmi = b8a.subtract(b11).divide(b8a.add(b11)).rename('NDMI')
        mtci = b6.subtract(b5).divide(b5.subtract(b4).max(ee.Image(0.001))).rename('MTCI')
        gndvi = b8.subtract(b3).divide(b8.add(b3)).rename('GNDVI')
        savi = b8.subtract(b4).multiply(1.5).divide(b8.add(b4).add(0.5)).rename('SAVI')
        kndvi = ndvi.pow(2).tanh().rename('kNDVI')
        psri = b4.subtract(b3).divide(b6.max(ee.Image(0.001))).rename('PSRI')
        nbr2 = b11.subtract(b12).divide(b11.add(b12)).rename('NBR2')
        msi = b11.divide(b8a.max(ee.Image(0.001))).rename('MSI')
        osavi = b8.subtract(b4).multiply(1.16).divide(b8.add(b4).add(0.16)).rename('OSAVI')
        msavi2 = b8.multiply(2).add(1).subtract(
            b8.multiply(2).add(1).pow(2).subtract(b8.subtract(b4).multiply(8)).sqrt()
        ).divide(2).rename('MSAVI2')

        s2rep_denom = b6.subtract(b5).where(b6.subtract(b5).abs().lt(0.001), 0.001)
        s2rep = ee.Image(705).add(ee.Image(35).multiply(
            b4.add(b7).divide(2).subtract(b5).divide(s2rep_denom)
        )).rename('S2REP')

        ccci = ndre.divide(ndvi.max(ee.Image(0.001))).rename('CCCI')
        cire = b8a.divide(b6.max(ee.Image(0.001))).subtract(1).rename('CIre')
        reci = b8a.divide(b5.max(ee.Image(0.001))).subtract(1).rename('RECI')
        ireci = b7.subtract(b4).divide(b5.divide(b6.max(ee.Image(0.001)))).rename('IRECI')
        evi2 = b8.subtract(b4).multiply(2.5).divide(b8.add(b4.multiply(2.4)).add(1)).rename('EVI2')

        return img.addBands([ndvi, ndre, evi, ndmi, mtci, gndvi, savi, kndvi, psri,
                            nbr2, msi, osavi, msavi2, s2rep, ccci, cire, reci, ireci, evi2])

    # Current values (mean of latest cloud-free image)
    current_values = {}
    if recent_count > 0:
        latest = compute_indices(s2_recent.first())
        for idx in indices_needed:
            try:
                val = latest.select(idx).reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=aoi,
                    scale=10,
                    bestEffort=True
                ).get(idx).getInfo()
                current_values[idx] = round(val, 4) if val is not None else None
            except:
                current_values[idx] = None

    # Baseline (historical mean + stddev for primary index)
    primary_idx = indices_needed[0] if indices_needed else 'NDVI'
    baseline_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(aoi)
        .filterDate(baseline_start, baseline_end)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15))
        .map(mask_clouds)
        .map(compute_indices))

    baseline_mean_val = None
    baseline_std_val = None
    z_score = None
    anomalies = []

    try:
        baseline_mean = baseline_col.select(primary_idx).mean()
        baseline_std = baseline_col.select(primary_idx).reduce(ee.Reducer.stdDev())

        baseline_mean_val = baseline_mean.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi, scale=20, bestEffort=True
        ).get(primary_idx).getInfo()

        baseline_std_val = baseline_std.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi, scale=20, bestEffort=True
        ).values().get(0).getInfo()

        # Z-score anomaly detection
        if current_values.get(primary_idx) is not None and baseline_mean_val and baseline_std_val and baseline_std_val > 0.01:
            z_score = round((current_values[primary_idx] - baseline_mean_val) / baseline_std_val, 2)

            if abs(z_score) > 2.0:
                severity = 'critical' if abs(z_score) > 3.0 else 'warning'
                anomalies.append({
                    "id": gen_id('anomaly-'),
                    "fieldId": field['id'],
                    "date": now_iso(),
                    "type": "anomaly",
                    "severity": severity,
                    "zScore": z_score,
                    "index": primary_idx,
                    "currentValue": current_values[primary_idx],
                    "baselineMean": round(baseline_mean_val, 4),
                    "baselineStd": round(baseline_std_val, 4),
                    "description": f"{primary_idx} Z-score={z_score} ({'caida' if z_score < 0 else 'exceso'} vs baseline)",
                    "status": "active"
                })
    except Exception as e:
        print(f'[GEE] Baseline error: {e}')

    return {
        "stage": stage_key,
        "stageDesc": stage_cfg['desc'],
        "daysSincePlanting": days,
        "indicesUsed": indices_needed,
        "currentValues": current_values,
        "baseline": {
            "mean": round(baseline_mean_val, 4) if baseline_mean_val else None,
            "std": round(baseline_std_val, 4) if baseline_std_val else None,
        },
        "zScore": z_score,
        "anomalies": anomalies,
        "imagesFound": recent_count,
        "cloudFree": recent_count > 0,
        "checkedAt": now_iso()
    }

# ============================================================
# REPORT GENERATOR (PDF + KMZ)
# ============================================================

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')

def generate_report(field, client, alerts, timeseries):
    """Generate PDF report + KMZ file with anomaly waypoints for Avenza Maps."""
    import io
    os.makedirs(REPORTS_DIR, exist_ok=True)

    field_name = field.get('name', 'Lote')
    crop = field.get('crop', 'soja')
    date_str = datetime.now().strftime('%Y-%m-%d')
    stage = field.get('monitoring', {}).get('currentStage', '—')
    client_name = client.get('name', '—') if client else '—'

    # ── KMZ (KML zipped) for Avenza Maps ──
    kml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>PIX Monitor - {field_name} - Anomalias {date_str}</name>
  <description>Reporte de anomalias para navegacion en campo (Avenza Maps)</description>

  <Style id="alertCritical">
    <IconStyle><color>ff0000ff</color><scale>1.4</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png</href></Icon>
    </IconStyle>
  </Style>
  <Style id="alertWarning">
    <IconStyle><color>ff00aaff</color><scale>1.2</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png</href></Icon>
    </IconStyle>
  </Style>

  <Folder>
    <name>Perimetro del Lote</name>
    <Placemark>
      <name>{field_name}</name>
      <description>Cultivo: {crop} | Area: {field.get("areaHa", 0)} ha | Etapa: {stage}</description>
      <Style><LineStyle><color>ff33d67f</color><width>3</width></LineStyle><PolyStyle><color>3033d67f</color></PolyStyle></Style>
      <Polygon><outerBoundaryIs><LinearRing><coordinates>
'''

    # Add boundary coordinates
    boundary = field.get('boundary', {})
    coords = boundary.get('coordinates', [[]])[0] if boundary.get('type') == 'Polygon' else boundary.get('coordinates', [[[]]])[0][0]
    for c in coords:
        if len(c) >= 2:
            kml_content += f'        {c[0]},{c[1]},0\n'

    kml_content += '''      </coordinates></LinearRing></outerBoundaryIs></Polygon>
    </Placemark>
  </Folder>

  <Folder>
    <name>Anomalias Detectadas</name>
'''

    # Add anomaly waypoints
    for i, alert in enumerate(alerts):
        severity = alert.get('severity', 'warning')
        style = 'alertCritical' if severity == 'critical' else 'alertWarning'
        z = alert.get('zScore', 0)
        idx = alert.get('index', 'NDVI')
        desc = alert.get('description', 'Anomalia detectada')
        centroid = alert.get('centroid', [0, 0])

        # Use field center if no centroid
        if centroid == [0, 0] and coords:
            lats = [c[1] for c in coords if len(c) >= 2]
            lngs = [c[0] for c in coords if len(c) >= 2]
            centroid = [sum(lngs)/len(lngs), sum(lats)/len(lats)] if lats else [0, 0]

        kml_content += f'''    <Placemark>
      <name>Anomalia-{i+1} (Z={z})</name>
      <description>{desc}
Indice: {idx} = {alert.get("currentValue", "—")}
Baseline: {alert.get("baselineMean", "—")}
Severidad: {severity.upper()}
Fecha: {alert.get("date", "—")[:10]}</description>
      <styleUrl>#{style}</styleUrl>
      <Point><coordinates>{centroid[0]},{centroid[1]},0</coordinates></Point>
    </Placemark>
'''

    kml_content += '''  </Folder>
</Document>
</kml>'''

    # Save KMZ (zipped KML)
    import zipfile
    kmz_filename = f'PIX_Monitor_{field_name}_{date_str}.kmz'
    kmz_path = os.path.join(REPORTS_DIR, kmz_filename)
    with zipfile.ZipFile(kmz_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('doc.kml', kml_content)

    # ── PDF Report ──
    pdf_filename = f'PIX_Monitor_{field_name}_{date_str}.pdf'
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.colors import HexColor
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

        doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=20*mm, bottomMargin=15*mm, leftMargin=15*mm, rightMargin=15*mm)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='PIXTitle', fontSize=18, spaceAfter=6, textColor=HexColor('#7FD633'), fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='PIXSub', fontSize=11, spaceAfter=12, textColor=HexColor('#94A3B8')))
        styles.add(ParagraphStyle(name='PIXBody', fontSize=10, spaceAfter=6, leading=14))
        styles.add(ParagraphStyle(name='PIXH2', fontSize=14, spaceAfter=8, textColor=HexColor('#00A4CC'), fontName='Helvetica-Bold'))

        story = []

        # Header
        story.append(Paragraph('PIX Monitor — Reporte de Monitoreo', styles['PIXTitle']))
        story.append(Paragraph(f'Cliente: {client_name} | Lote: {field_name} | Cultivo: {crop} | Fecha: {date_str}', styles['PIXSub']))
        story.append(Spacer(1, 10))

        # Field info
        story.append(Paragraph('1. Informacion del Lote', styles['PIXH2']))
        info_data = [
            ['Propiedad', 'Valor'],
            ['Lote', field_name],
            ['Cultivo', f'{crop} ({CROP_PHENOLOGY.get(crop, {}).get("name", crop)})'],
            ['Area', f'{field.get("areaHa", 0)} ha'],
            ['Fecha siembra', field.get('plantingDate', '—')],
            ['Etapa actual', f'{stage} ({field.get("monitoring", {}).get("currentStage", "—")})'],
            ['Ultimo chequeo', field.get('monitoring', {}).get('lastCheck', '—')[:10] if field.get('monitoring', {}).get('lastCheck') else 'Nunca'],
        ]
        t = Table(info_data, colWidths=[50*mm, 120*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a2b3f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#334155')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#0F1B2D'), HexColor('#162236')]),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 16))

        # Alerts
        story.append(Paragraph('2. Anomalias Detectadas', styles['PIXH2']))
        if alerts:
            alert_data = [['#', 'Indice', 'Valor', 'Baseline', 'Z-Score', 'Severidad', 'Fecha']]
            for i, a in enumerate(alerts):
                alert_data.append([
                    str(i+1),
                    a.get('index', '—'),
                    str(a.get('currentValue', '—')),
                    str(a.get('baselineMean', '—')),
                    str(a.get('zScore', '—')),
                    a.get('severity', '—').upper(),
                    a.get('date', '—')[:10]
                ])
            at = Table(alert_data, colWidths=[10*mm, 20*mm, 22*mm, 22*mm, 22*mm, 28*mm, 28*mm])
            at.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#7F1D1D')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#334155')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#1C1917'), HexColor('#292524')]),
                ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#FBBF24')),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(at)
        else:
            story.append(Paragraph('Sin anomalias detectadas. Cultivo en estado normal.', styles['PIXBody']))
        story.append(Spacer(1, 16))

        # Time series
        story.append(Paragraph('3. Serie Temporal', styles['PIXH2']))
        if timeseries:
            ts_data = [['Fecha', 'Etapa', 'NDVI', 'NDRE', 'Z-Score']]
            for t_entry in timeseries[-10:]:  # Last 10 entries
                vals = t_entry.get('values', {})
                ts_data.append([
                    t_entry.get('date', '—')[:10],
                    t_entry.get('stage', '—'),
                    f'{vals.get("NDVI", 0):.3f}' if vals.get('NDVI') else '—',
                    f'{vals.get("NDRE", 0):.3f}' if vals.get('NDRE') else '—',
                    str(t_entry.get('zScore', '—'))
                ])
            tst = Table(ts_data, colWidths=[30*mm, 35*mm, 25*mm, 25*mm, 25*mm])
            tst.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a2b3f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#334155')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#0F1B2D'), HexColor('#162236')]),
                ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#E2E8F0')),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(tst)
        else:
            story.append(Paragraph('Sin datos de serie temporal disponibles.', styles['PIXBody']))
        story.append(Spacer(1, 16))

        # Navigation instructions
        story.append(Paragraph('4. Navegacion a Campo', styles['PIXH2']))
        story.append(Paragraph(
            f'Para llegar a las anomalias detectadas, importe el archivo <b>{kmz_filename}</b> en Avenza Maps '
            'o cualquier app GPS compatible con KMZ/KML. Los waypoints estan marcados con la severidad '
            'correspondiente (rojo=critico, amarillo=warning).',
            styles['PIXBody']
        ))
        story.append(Spacer(1, 8))

        if alerts:
            story.append(Paragraph('Coordenadas de anomalias:', styles['PIXBody']))
            for i, a in enumerate(alerts):
                centroid = a.get('centroid', [0, 0])
                if centroid == [0, 0]:
                    bcoords = field.get('boundary', {}).get('coordinates', [[]])[0]
                    if bcoords:
                        centroid = [sum(c[0] for c in bcoords)/len(bcoords), sum(c[1] for c in bcoords)/len(bcoords)]
                story.append(Paragraph(
                    f'  Anomalia-{i+1}: Lat {centroid[1]:.6f}, Lng {centroid[0]:.6f} | Z={a.get("zScore","—")} | {a.get("severity","").upper()}',
                    styles['PIXBody']
                ))

        # Footer
        story.append(Spacer(1, 24))
        story.append(Paragraph(
            f'Generado por PIX Monitor — Pixadvisor Agricultura de Precision | {date_str}',
            ParagraphStyle(name='Footer', fontSize=8, textColor=HexColor('#64748B'))
        ))

        doc.build(story)
        print(f'[Report] PDF generated: {pdf_path}')

    except ImportError:
        # reportlab not installed — generate text report instead
        with open(pdf_path.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
            f.write(f'PIX Monitor — Reporte de Monitoreo\n')
            f.write(f'Cliente: {client_name} | Lote: {field_name} | Cultivo: {crop}\n')
            f.write(f'Fecha: {date_str} | Etapa: {stage}\n\n')
            f.write(f'Anomalias: {len(alerts)}\n')
            for i, a in enumerate(alerts):
                f.write(f'  {i+1}. {a.get("description","—")} | Z={a.get("zScore","—")}\n')
        pdf_filename = pdf_filename.replace('.pdf', '.txt')
        pdf_path = pdf_path.replace('.pdf', '.txt')
        print(f'[Report] Text report generated (reportlab not installed): {pdf_path}')

    print(f'[Report] KMZ generated: {kmz_path}')

    return {
        'pdf': pdf_filename,
        'kmz': kmz_filename,
        'pdfPath': pdf_path,
        'kmzPath': kmz_path,
        'alerts': len(alerts),
        'field': field_name,
        'date': date_str
    }


# ============================================================
# HTTP HANDLER
# ============================================================

class MonitorHandler(BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def _json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _error(self, msg, status=400):
        self._json({'error': msg}, status)

    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length).decode('utf-8')) if length > 0 else {}

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path.rstrip('/')

        if path == '/api/health':
            self._json({'status': 'ok', 'service': 'pix-monitor-api', 'port': PORT,
                        'gee': _ee_initialized, 'crops': list(CROP_PHENOLOGY.keys())})

        elif path == '/api/clients':
            db = load_db()
            self._json({'clients': db['clients']})

        elif path == '/api/fields':
            db = load_db()
            self._json({'fields': db['fields']})

        elif path == '/api/alerts':
            db = load_db()
            self._json({'alerts': db['alerts']})

        elif path == '/api/crops':
            crops = {}
            for key, cfg in CROP_PHENOLOGY.items():
                crops[key] = {
                    'name': cfg['name'],
                    'cycle_days': cfg['cycle_days'],
                    'stages': {k: v['desc'] for k, v in cfg['stages'].items()},
                    'critical_stages': cfg['critical_stages']
                }
            self._json({'crops': crops})

        elif path.startswith('/api/timeseries/'):
            field_id = path.split('/')[-1]
            db = load_db()
            ts = db.get('timeseries', {}).get(field_id, [])
            self._json({'fieldId': field_id, 'timeseries': ts})

        else:
            self._error('Not found', 404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip('/')

        if path == '/api/clients':
            body = self._body()
            if not body.get('name'):
                self._error('name required')
                return
            db = load_db()
            client = {
                'id': gen_id('cli-'),
                'name': body['name'],
                'contact': body.get('contact', ''),
                'email': body.get('email', ''),
                'createdAt': now_iso()
            }
            db['clients'].append(client)
            save_db(db)
            print(f'[Monitor] Client created: {client["name"]}')
            self._json(client, 201)

        elif path == '/api/fields':
            body = self._body()
            if not body.get('name') or not body.get('boundary'):
                self._error('name and boundary required')
                return
            db = load_db()
            field = {
                'id': gen_id('field-'),
                'clientId': body.get('clientId', ''),
                'name': body['name'],
                'boundary': body['boundary'],
                'areaHa': body.get('areaHa', 0),
                'crop': body.get('crop', 'soja'),
                'plantingDate': body.get('plantingDate', ''),
                'monitoring': {
                    'active': False,
                    'activatedAt': None,
                    'lastCheck': None,
                    'currentStage': None,
                    'checkCount': 0
                },
                'createdAt': now_iso()
            }
            db['fields'].append(field)
            save_db(db)
            print(f'[Monitor] Field created: {field["name"]} ({field["crop"]})')
            self._json(field, 201)

        elif path.endswith('/activate'):
            field_id = path.split('/')[-2]
            db = load_db()
            field = next((f for f in db['fields'] if f['id'] == field_id), None)
            if not field:
                self._error('Field not found', 404)
                return
            field['monitoring']['active'] = True
            field['monitoring']['activatedAt'] = now_iso()

            # Detect initial stage
            stage_key, stage_cfg, days = detect_stage(field.get('crop', 'soja'), field.get('plantingDate', ''))
            if stage_key:
                field['monitoring']['currentStage'] = stage_key

            save_db(db)
            print(f'[Monitor] Monitoring activated: {field["name"]} (stage: {stage_key})')
            self._json({'activated': True, 'field': field})

        elif path.endswith('/check'):
            field_id = path.split('/')[-2]
            db = load_db()
            field = next((f for f in db['fields'] if f['id'] == field_id), None)
            if not field:
                self._error('Field not found', 404)
                return

            print(f'[Monitor] Running check for: {field["name"]}...')
            try:
                result = compute_monitoring(field)
            except Exception as e:
                traceback.print_exc()
                self._error(f'GEE error: {str(e)}', 500)
                return

            # Update field status
            field['monitoring']['lastCheck'] = now_iso()
            field['monitoring']['currentStage'] = result.get('stage')
            field['monitoring']['checkCount'] = field['monitoring'].get('checkCount', 0) + 1

            # Save anomalies
            if result.get('anomalies'):
                for a in result['anomalies']:
                    db['alerts'].append(a)

            # Save time series point
            ts_key = field['id']
            if ts_key not in db.get('timeseries', {}):
                db['timeseries'][ts_key] = []
            db['timeseries'][ts_key].append({
                'date': now_iso(),
                'stage': result.get('stage'),
                'values': result.get('currentValues', {}),
                'zScore': result.get('zScore'),
                'images': result.get('imagesFound', 0)
            })

            save_db(db)
            print(f'[Monitor] Check complete: stage={result.get("stage")}, Z={result.get("zScore")}, anomalies={len(result.get("anomalies", []))}')
            self._json(result)

        elif path.startswith('/api/reports/'):
            field_id = path.split('/')[-1]
            db = load_db()
            field = next((f for f in db['fields'] if f['id'] == field_id), None)
            if not field:
                self._error('Field not found', 404)
                return
            client = next((c for c in db['clients'] if c['id'] == field.get('clientId')), None)
            alerts = [a for a in db['alerts'] if a.get('fieldId') == field_id and a.get('status') == 'active']
            ts = db.get('timeseries', {}).get(field_id, [])

            try:
                result = generate_report(field, client, alerts, ts)
                self._json(result)
            except Exception as e:
                traceback.print_exc()
                self._error(f'Report error: {str(e)}', 500)

        else:
            self._error('Not found', 404)

    def do_PUT(self):
        path = urlparse(self.path).path.rstrip('/')

        if path.startswith('/api/fields/'):
            field_id = path.split('/')[-1]
            body = self._body()
            db = load_db()
            field = next((f for f in db['fields'] if f['id'] == field_id), None)
            if not field:
                self._error('Field not found', 404)
                return
            for k in ['name', 'crop', 'plantingDate', 'areaHa', 'clientId']:
                if k in body:
                    field[k] = body[k]
            if 'boundary' in body:
                field['boundary'] = body['boundary']
            save_db(db)
            self._json(field)
        else:
            self._error('Not found', 404)

    def do_DELETE(self):
        path = urlparse(self.path).path.rstrip('/')
        if path.startswith('/api/alerts/'):
            alert_id = path.split('/')[-1]
            db = load_db()
            db['alerts'] = [a for a in db['alerts'] if a['id'] != alert_id]
            save_db(db)
            self._json({'deleted': True})
        else:
            self._error('Not found', 404)

    def log_message(self, format, *args):
        pass

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print('=== PIX Monitor API — Crop Monitoring Engine ===')
    print(f'Port: {PORT}')
    print(f'DB: {DB_FILE}')
    print(f'GEE Key: {"OK" if os.path.exists(GEE_KEY_PATH) else "NOT FOUND"}')
    print(f'Crops: {", ".join(CROP_PHENOLOGY.keys())}')
    print()

    # Pre-initialize GEE
    if os.path.exists(GEE_KEY_PATH):
        init_gee()

    db = load_db()
    print(f'Loaded: {len(db["clients"])} clients, {len(db["fields"])} fields, {len(db["alerts"])} alerts')
    print(f'Listening on http://localhost:{PORT}/api/')
    print()

    server = HTTPServer(('0.0.0.0', PORT), MonitorHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...')
        server.server_close()
