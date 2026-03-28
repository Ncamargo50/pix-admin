"""
GEE Backend v2 — Serves REAL production results from pixadvisor_zonas_master_v4.1.

Two modes:
1. LOAD: Load existing production results (shapefiles already generated)
2. PROCESS: Run the full v4.1 pipeline from rasters (if rasters exist)

Endpoint: POST http://localhost:9103/process
"""
import json
import http.server
import os
import traceback
import numpy as np

# Base path for Hacienda Del Señor data
HDS_BASE = r'C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS\Hacienda-Del-Senor'
ZONAS_BASE = os.path.join(HDS_BASE, '03-Zonas-Manejo')

print(f'Data path: {ZONAS_BASE}')
print(f'Available lots: {len([d for d in os.listdir(ZONAS_BASE) if os.path.isdir(os.path.join(ZONAS_BASE, d)) and d != "00-Rasters-Globales"])}')


def load_production_results(lote_name):
    """
    Load existing production results (zonas shapefile + puntos shapefile)
    and convert to GeoJSON for the admin frontend.
    These are the EXACT same results shown in the PDF reports.
    """
    import geopandas as gpd

    lote_dir = os.path.join(ZONAS_BASE, lote_name, 'PRO')
    if not os.path.exists(lote_dir):
        raise FileNotFoundError(f'No production data for lot: {lote_name}')

    # Load zones shapefile
    zones_shp = os.path.join(lote_dir, f'zonas_manejo_{lote_name}_PRO.shp')
    if not os.path.exists(zones_shp):
        raise FileNotFoundError(f'Zones shapefile not found: {zones_shp}')

    zones_gdf = gpd.read_file(zones_shp)
    zones_wgs = zones_gdf.to_crs('EPSG:4326')

    # Load sampling points
    points_shp = os.path.join(lote_dir, f'puntos_muestreo_{lote_name}.shp')
    sampling_points = []
    if os.path.exists(points_shp):
        pts_gdf = gpd.read_file(points_shp)
        pts_wgs = pts_gdf.to_crs('EPSG:4326')
        for _, row in pts_wgs.iterrows():
            pt = row.geometry
            codigo = row.get('codigo', row.get('Codigo', row.get('id', '')))
            tipo = row.get('tipo', row.get('Tipo', 'Submuestra'))
            zona = row.get('zona', row.get('Zona', 0))
            sampling_points.append({
                'id': str(codigo),
                'type': 'principal' if 'P' in str(codigo).split('-')[-1] else 'submuestra',
                'zona': int(zona) if zona else 0,
                'lat': pt.y,
                'lng': pt.x
            })

    # Load stats CSV
    stats = []
    stats_csv = os.path.join(lote_dir, f'estadisticas_PRO_{lote_name}.csv')
    if os.path.exists(stats_csv):
        import csv
        with open(stats_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats.append({
                    'zona': int(row.get('zona', 0)),
                    'clase': row.get('nombre', row.get('clase', '')),
                    'area_ha': float(row.get('area_ha', 0)),
                    'porcentaje': float(row.get('pct_lote', row.get('pct', row.get('porcentaje', 0)))),
                    'score_prom': float(row.get('score_prom', 0)),
                    'puntos': int(row.get('puntos_principales', 1)),
                    'submuestras': int(row.get('submuestras', 0)),
                })

    # Build GeoJSON with production colors
    # Convert entire GeoDataFrame to GeoJSON at once (most reliable)
    zone_colors = ['#CC0000', '#FF8C00', '#FFD700', '#228B22']
    zones_json = json.loads(zones_wgs.to_json())

    features = []
    for feat in zones_json['features']:
        props = feat['properties']
        zona = int(props.get('zona', 0))
        features.append({
            'type': 'Feature',
            'geometry': feat['geometry'],
            'properties': {
                'zona': zona,
                'clase': props.get('nombre', ''),
                'color': zone_colors[zona - 1] if zona <= len(zone_colors) else '#888',
                'area_ha': round(float(props.get('area_ha', 0)), 1),
                'porcentaje': round(float(props.get('pct', 0)), 1),
                'score_prom': 0,
            }
        })

    num_zones = len(features)
    if not stats:
        stats = [f['properties'] for f in features]

    print(f'Loaded production results for {lote_name}: {num_zones} zones, {len(sampling_points)} points')

    return {
        'zonesGeoJSON': {'type': 'FeatureCollection', 'features': features},
        'samplingPoints': sampling_points,
        'stats': stats,
        'numZones': num_zones,
        'gridSize': [0, 0],
        'scale': 2,
        'campaigns': 5,
        'method': 'PRODUCTION_v4.1_REAL'
    }


def list_available_lots():
    """List all lots that have production results."""
    lots = []
    if not os.path.exists(ZONAS_BASE):
        return lots
    for d in sorted(os.listdir(ZONAS_BASE)):
        lote_dir = os.path.join(ZONAS_BASE, d, 'PRO')
        if os.path.isdir(lote_dir):
            has_zones = any(f.endswith('_PRO.shp') for f in os.listdir(lote_dir))
            has_points = any('puntos_muestreo' in f and f.endswith('.shp') for f in os.listdir(lote_dir))
            if has_zones:
                lots.append({
                    'name': d,
                    'hasZones': has_zones,
                    'hasPoints': has_points,
                    'path': lote_dir
                })
    return lots


class GEEHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/process':
            try:
                length = int(self.headers['Content-Length'])
                body = json.loads(self.rfile.read(length))
                lote = body.get('loteName', body.get('lote', ''))

                if not lote:
                    raise ValueError('Missing loteName in request')

                result = load_production_results(lote)

                response = json.dumps(result, ensure_ascii=False)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response.encode('utf-8'))
            except Exception as e:
                traceback.print_exc()
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
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/status':
            lots = list_available_lots()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'ready',
                'project': 'ee-gisagronomico',
                'mode': 'PRODUCTION_v4.1',
                'availableLots': len(lots),
                'lots': [l['name'] for l in lots[:20]]
            }).encode())
        elif self.path == '/lots':
            lots = list_available_lots()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(lots, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f'[GEE Backend] {args[0]}')


if __name__ == '__main__':
    PORT = 9104
    server = http.server.HTTPServer(('localhost', PORT), GEEHandler)
    lots = list_available_lots()
    print(f'GEE Backend v2 (PRODUCTION) running on http://localhost:{PORT}')
    print(f'Available lots: {len(lots)}')
    print(f'POST /process {{loteName: "4A1"}} — load production results')
    print(f'GET /lots — list all available lots')
    server.serve_forever()
