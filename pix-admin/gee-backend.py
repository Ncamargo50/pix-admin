"""
GEE Backend — Real Earth Engine processing server for PIX Admin.
Runs the EXACT same methodology as pixadvisor_zonas_master_v4.1.
Endpoint: POST http://localhost:9101/process
"""
import json
import http.server
import ee
import numpy as np
from scipy.stats import rankdata
from scipy.ndimage import gaussian_filter
import traceback

# ===== INIT GEE =====
KEY_PATH = r'C:\Users\Usuario\Desktop\PIXADVISOR\ee-gisagronomico-key.json'
PROJECT = 'ee-gisagronomico'

credentials = ee.ServiceAccountCredentials(None, KEY_PATH)
ee.Initialize(credentials, project=PROJECT)
print(f'GEE initialized: {PROJECT}')

# ===== PRODUCTION CONFIG (v4.1) =====
INDICES_CANA = {
    'NDRE': 0.25, 'RECI': 0.15, 'CIre': 0.10,
    'IRECI': 0.08, 'EVI': 0.07, 'NDMI': 0.05, 'MSI': 0.05
}

PESOS_SCORE = {
    'rank_medio': 0.40, 'rank_std': 0.20, 'rank_min': 0.10,
    'twi': 0.10, 'flow_accum': 0.06, 'pendiente': 0.06,
    'elevacion': 0.04, 'dist_drenaje': 0.04
}

CAMPANAS_CANA = [
    {'nombre': 'Zafra 2020-2021', 'ini': '2021-05-01', 'fin': '2021-09-30'},
    {'nombre': 'Zafra 2021-2022', 'ini': '2022-05-01', 'fin': '2022-09-30'},
    {'nombre': 'Zafra 2022-2023', 'ini': '2023-05-01', 'fin': '2023-09-30'},
    {'nombre': 'Zafra 2023-2024', 'ini': '2024-05-01', 'fin': '2024-09-30'},
    {'nombre': 'Zafra 2024-2025', 'ini': '2025-05-01', 'fin': '2025-09-30'},
]


def compute_index(img, name):
    """Compute vegetation index on S2 SR image."""
    formulas = {
        'NDVI': lambda: img.normalizedDifference(['B8', 'B4']),
        'NDRE': lambda: img.normalizedDifference(['B8', 'B5']),
        'EVI': lambda: img.expression('2.5*((NIR-RED)/(NIR+6*RED-7.5*BLUE+1))',
            {'NIR': img.select('B8'), 'RED': img.select('B4'), 'BLUE': img.select('B2')}),
        'RECI': lambda: img.expression('NIR/RE1-1', {'NIR': img.select('B8'), 'RE1': img.select('B5')}),
        'CIre': lambda: img.expression('NIR/RE2-1', {'NIR': img.select('B8'), 'RE2': img.select('B7')}),
        'IRECI': lambda: img.expression('(RE3-RED)/(RE1/RE2)',
            {'RE3': img.select('B7'), 'RED': img.select('B4'), 'RE1': img.select('B5'), 'RE2': img.select('B6')}),
        'NDMI': lambda: img.normalizedDifference(['B8A', 'B11']),
        'MSI': lambda: img.expression('SWIR/NIR', {'SWIR': img.select('B11'), 'NIR': img.select('B8A')}),
    }
    return formulas[name]().rename(name)


def mask_s2(img):
    """SCL cloud mask."""
    scl = img.select('SCL')
    mask = scl.neq(0).And(scl.neq(1)).And(scl.neq(3)).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
    return img.updateMask(mask)


def ranking_percentil(arr, mask):
    """Compute percentile ranking (0-100) for valid pixels."""
    result = np.full_like(arr, np.nan)
    valid = mask & ~np.isnan(arr)
    if valid.sum() < 2:
        return result
    ranks = rankdata(arr[valid], method='average')
    n = len(ranks)
    result[valid] = (ranks - 1) / (n - 1) * 100
    return result


def normalizar_0_1(arr, mask, invertir=False):
    """Normalize array to 0-1 using 2-98 percentile stretch."""
    valid = arr[mask & ~np.isnan(arr)]
    if len(valid) < 2:
        return np.zeros_like(arr)
    vmin = np.nanpercentile(valid, 2)
    vmax = np.nanpercentile(valid, 98)
    if vmax - vmin < 1e-10:
        return np.zeros_like(arr)
    norm = np.clip((arr - vmin) / (vmax - vmin), 0, 1)
    if invertir:
        norm = 1.0 - norm
    norm[~mask] = 0
    return norm


def process_field(polygon_coords, area_ha, num_campaigns=5):
    """
    Full GEE processing pipeline — production v4.1 methodology.
    Returns zone grid, stats, and sampling data as JSON-serializable dict.
    """
    # Build geometry
    geometry = ee.Geometry.Polygon([polygon_coords])

    # Scale by area
    scale = 10
    if area_ha > 500: scale = 30
    elif area_ha > 100: scale = 20

    # Select campaigns
    campanas = CAMPANAS_CANA[-num_campaigns:]

    # Process each campaign
    print(f'Processing {len(campanas)} campaigns for {area_ha:.1f} ha...')
    campaign_rankings = []

    for camp in campanas:
        print(f'  Campaign: {camp["nombre"]}...')
        s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
              .filterBounds(geometry)
              .filterDate(camp['ini'], camp['fin'])
              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15))
              .map(mask_s2))

        count = s2.size().getInfo()
        if count < 5:
            s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                  .filterBounds(geometry)
                  .filterDate(camp['ini'], camp['fin'])
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
                  .map(mask_s2))
            count = s2.size().getInfo()

        print(f'    {count} images')

        # Compute weighted index composite
        def add_indices(img):
            result = img
            for idx_name in INDICES_CANA.keys():
                result = result.addBands(compute_index(img, idx_name))
            return result

        with_indices = s2.map(add_indices)

        # Weighted composite: sum(index * weight) for primary ranking
        idx_names = list(INDICES_CANA.keys())
        idx_weights = list(INDICES_CANA.values())
        composite = with_indices.select(idx_names).median().clip(geometry)

        # Compute weighted sum as single band
        weighted = composite.select(idx_names[0]).multiply(idx_weights[0])
        for i in range(1, len(idx_names)):
            weighted = weighted.add(composite.select(idx_names[i]).multiply(idx_weights[i]))
        weighted = weighted.rename('weighted_index')

        # Download as array
        arr = weighted.reproject(crs='EPSG:4326', scale=scale).sampleRectangle(
            region=geometry, defaultValue=0).getInfo()
        grid = np.array(arr['properties']['weighted_index'], dtype=np.float64)

        # Compute ranking percentile
        mask = grid != 0
        ranking = ranking_percentil(grid, mask)
        campaign_rankings.append(ranking)

    # Multi-campaign statistics
    print('Computing multi-campaign statistics...')
    stack = np.array(campaign_rankings)
    rank_medio = np.nanmean(stack, axis=0)
    rank_std = np.nanstd(stack, axis=0)
    rank_min = np.nanmin(stack, axis=0)
    mask = ~np.isnan(rank_medio) & (rank_medio != 0)

    # DEM and terrain
    print('Processing DEM and terrain...')
    dem = ee.ImageCollection('COPERNICUS/DEM/GLO30').mosaic().select('DEM').clip(geometry)
    terrain = ee.Terrain.products(dem)
    slope = terrain.select('slope')

    dem_arr = np.array(dem.reproject(crs='EPSG:4326', scale=scale).sampleRectangle(
        region=geometry, defaultValue=0).getInfo()['properties']['DEM'], dtype=np.float64)
    slope_arr = np.array(slope.reproject(crs='EPSG:4326', scale=scale).sampleRectangle(
        region=geometry, defaultValue=0).getInfo()['properties']['slope'], dtype=np.float64)

    # TWI
    slope_rad = np.deg2rad(slope_arr)
    twi_arr = np.log((scale * scale * 10) / np.tan(slope_rad + 0.001))

    # Flow accumulation (simple D8)
    rows, cols = dem_arr.shape
    flow_acc = np.ones((rows, cols))
    flat = dem_arr.flatten()
    order = np.argsort(-flat)
    for idx in order:
        r, c = divmod(idx, cols)
        min_elev = float('inf')
        min_r, min_c = r, c
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if dem_arr[nr, nc] < min_elev:
                        min_elev = dem_arr[nr, nc]
                        min_r, min_c = nr, nc
        if min_elev < dem_arr[r, c]:
            flow_acc[min_r, min_c] += flow_acc[r, c]

    # Normalize all layers
    rank_medio_n = normalizar_0_1(rank_medio, mask)
    rank_std_n = normalizar_0_1(rank_std, mask, invertir=True)
    rank_min_n = normalizar_0_1(rank_min, mask)
    twi_n = normalizar_0_1(twi_arr, mask)
    flow_n = normalizar_0_1(flow_acc, mask, invertir=True)
    slope_n = normalizar_0_1(slope_arr, mask, invertir=True)
    elev_n = normalizar_0_1(dem_arr, mask)
    # Distance to drainage (simplified)
    drain_threshold = np.nanpercentile(flow_acc[mask], 95)
    drain_mask = flow_acc > drain_threshold
    from scipy.ndimage import distance_transform_edt
    dist_drain = distance_transform_edt(~drain_mask).astype(float)
    dist_drain_n = normalizar_0_1(dist_drain, mask)

    # Score Compuesto
    print('Computing Score Compuesto...')
    score = (
        PESOS_SCORE['rank_medio'] * rank_medio_n +
        PESOS_SCORE['rank_std'] * rank_std_n +
        PESOS_SCORE['rank_min'] * rank_min_n +
        PESOS_SCORE['twi'] * twi_n +
        PESOS_SCORE['flow_accum'] * flow_n +
        PESOS_SCORE['pendiente'] * slope_n +
        PESOS_SCORE['elevacion'] * elev_n +
        PESOS_SCORE['dist_drenaje'] * dist_drain_n
    )

    # Gaussian smoothing (production sigma=10)
    score_smooth = gaussian_filter(score, sigma=3)
    score_smooth[~mask] = 0

    # Zone classification by percentiles
    num_zones = 3 if area_ha <= 33 else 4
    valid_scores = score_smooth[mask]
    if num_zones == 3:
        cuts = np.percentile(valid_scores, [33.33, 66.67])
    else:
        cuts = np.percentile(valid_scores, [25, 50, 75])

    zones = np.zeros_like(score_smooth, dtype=int)
    zones[mask] = np.digitize(score_smooth[mask], cuts) + 1

    # Zone statistics
    zone_labels = {3: ['Baja', 'Media', 'Alta'], 4: ['Baja', 'Media-Baja', 'Media-Alta', 'Alta']}
    labels = zone_labels.get(num_zones, zone_labels[4])
    stats = []
    for z in range(1, num_zones + 1):
        zmask = zones == z
        zcount = zmask.sum()
        z_area = (zcount / mask.sum()) * area_ha if mask.sum() > 0 else 0
        z_pct = (zcount / mask.sum()) * 100 if mask.sum() > 0 else 0
        stats.append({
            'zona': z,
            'clase': labels[z - 1],
            'area_ha': round(z_area, 1),
            'porcentaje': round(z_pct, 1),
            'score_prom': round(float(np.nanmean(score_smooth[zmask])), 3) if zcount > 0 else 0,
            'ndvi_prom': round(float(np.nanmean(rank_medio[zmask])), 3) if zcount > 0 else 0,
        })

    print(f'Result: {num_zones} zones')
    for s in stats:
        print(f'  Z{s["zona"]} {s["clase"]}: {s["area_ha"]}ha ({s["porcentaje"]}%)')

    # === VECTORIZE ZONES AS GEOJSON (organic polygons like production PDF) ===
    print('Vectorizing zones to GeoJSON polygons...')
    import rasterio.features
    from shapely.geometry import shape, mapping
    from shapely.ops import unary_union
    from shapely.validation import make_valid

    # Build affine transform from polygon bounds
    lats = [c[1] for c in polygon_coords]
    lngs = [c[0] for c in polygon_coords]
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)
    pixel_w = (max_lng - min_lng) / cols
    pixel_h = (max_lat - min_lat) / rows
    from rasterio.transform import from_bounds
    transform = from_bounds(min_lng, min_lat, max_lng, max_lat, cols, rows)

    # Create field polygon for clipping
    from shapely.geometry import Polygon as ShapelyPolygon
    field_poly = ShapelyPolygon(polygon_coords)
    if not field_poly.is_valid:
        field_poly = make_valid(field_poly)

    zone_colors = ['#CC0000', '#FF8C00', '#FFD700', '#228B22']
    geojson_features = []
    sampling_points = []

    for z in range(1, num_zones + 1):
        zone_mask = (zones == z).astype(np.int16)
        if zone_mask.sum() == 0:
            continue

        # Vectorize zone raster to polygons
        shapes_gen = rasterio.features.shapes(zone_mask, mask=zone_mask > 0, transform=transform)
        polys = []
        for geom, val in shapes_gen:
            if val > 0:
                poly = shape(geom)
                if poly.is_valid:
                    polys.append(poly)

        if not polys:
            continue

        # Merge all polygons for this zone
        merged = unary_union(polys)
        if not merged.is_valid:
            merged = make_valid(merged)

        # Smooth edges: buffer +20m then -20m (production v4.1)
        buf_deg = 20 / 111320  # ~20m in degrees
        smoothed = merged.buffer(buf_deg).buffer(-buf_deg)
        if smoothed.is_empty:
            smoothed = merged

        # Simplify (5m tolerance)
        simp_deg = 5 / 111320
        smoothed = smoothed.simplify(simp_deg, preserve_topology=True)

        # Clip to field boundary
        clipped = smoothed.intersection(field_poly)
        if clipped.is_empty:
            clipped = merged.intersection(field_poly)

        # Add to GeoJSON
        geojson_features.append({
            'type': 'Feature',
            'properties': {
                'zona': z,
                'clase': labels[z - 1],
                'color': zone_colors[z - 1] if z <= len(zone_colors) else '#888',
                'area_ha': stats[z - 1]['area_ha'],
                'porcentaje': stats[z - 1]['porcentaje'],
                'score_prom': stats[z - 1]['score_prom'],
            },
            'geometry': mapping(clipped)
        })

        # === SAMPLING POINTS (Polo de Inaccesibilidad + FPS) ===
        from shapely.ops import polylabel
        try:
            main_pt = polylabel(clipped, tolerance=10 / 111320)
        except:
            main_pt = clipped.representative_point()

        z_area = stats[z - 1]['area_ha']
        # Subsample count (production v4.1 table)
        if z_area < 2: n_sub = 3
        elif z_area < 5: n_sub = 4
        elif z_area < 8: n_sub = 5
        elif z_area < 12: n_sub = 6
        elif z_area < 18: n_sub = 7
        elif z_area < 25: n_sub = 8
        elif z_area < 35: n_sub = 9
        else: n_sub = 10

        prefix = 'PIX'  # Will be overridden by frontend
        sampling_points.append({
            'id': f'Z{z}-P1', 'type': 'principal', 'zona': z,
            'lat': main_pt.y, 'lng': main_pt.x
        })

        # FPS subsamples
        try:
            # Buffer interior
            if z_area < 3: buf_int = 15
            elif z_area < 8: buf_int = 20
            elif z_area < 15: buf_int = 30
            elif z_area < 30: buf_int = 40
            elif z_area < 50: buf_int = 50
            else: buf_int = 60
            interior = clipped.buffer(-buf_int / 111320)
            if interior.is_empty or interior.area < 1e-10:
                interior = clipped

            # Generate random candidates
            import random
            random.seed(42 + z)
            bounds_z = interior.bounds
            candidates = []
            for _ in range(300):
                px = random.uniform(bounds_z[0], bounds_z[2])
                py = random.uniform(bounds_z[1], bounds_z[3])
                from shapely.geometry import Point
                if interior.contains(Point(px, py)):
                    candidates.append((px, py))

            # FPS: select n_sub points maximizing min distance
            selected = []
            if candidates:
                # Start with farthest from main point
                dists = [((c[0]-main_pt.x)**2 + (c[1]-main_pt.y)**2)**0.5 for c in candidates]
                first = candidates[dists.index(max(dists))]
                selected.append(first)
                used = {dists.index(max(dists))}

                while len(selected) < n_sub and len(selected) < len(candidates):
                    best_idx, best_min = -1, -1
                    for i, c in enumerate(candidates):
                        if i in used:
                            continue
                        min_d = min(((c[0]-s[0])**2 + (c[1]-s[1])**2)**0.5 for s in selected)
                        if min_d > best_min:
                            best_min = min_d
                            best_idx = i
                    if best_idx < 0:
                        break
                    selected.append(candidates[best_idx])
                    used.add(best_idx)

            for si, sp in enumerate(selected):
                sampling_points.append({
                    'id': f'Z{z}-S{si+1}', 'type': 'submuestra', 'zona': z,
                    'lat': sp[1], 'lng': sp[0]
                })
        except Exception as e:
            print(f'  Warning: FPS failed for Z{z}: {e}')

    zones_geojson = {
        'type': 'FeatureCollection',
        'features': geojson_features
    }

    print(f'Vectorized: {len(geojson_features)} zone polygons, {len(sampling_points)} sampling points')

    return {
        'zonesGeoJSON': zones_geojson,
        'samplingPoints': sampling_points,
        'stats': stats,
        'numZones': num_zones,
        'gridSize': [rows, cols],
        'scale': scale,
        'campaigns': len(campanas),
        'method': 'REAL_GEE_v4.1'
    }


class GEEHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/process':
            try:
                length = int(self.headers['Content-Length'])
                body = json.loads(self.rfile.read(length))

                polygon = body['polygon']
                area_ha = body.get('areaHa', 50)
                num_campaigns = body.get('numCampaigns', 5)

                result = process_field(polygon, area_ha, num_campaigns)

                response = json.dumps(result)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response.encode())
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
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ready', 'project': PROJECT}).encode())
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == '__main__':
    server = http.server.HTTPServer(('localhost', 9103), GEEHandler)
    print(f'GEE Backend running on http://localhost:9103')
    print(f'POST /process — process field with real GEE data')
    print(f'GET /status — check server status')
    server.serve_forever()
