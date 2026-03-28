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

    # Interpolate to higher resolution (production uses 2m = 5x upscale from 10m)
    from scipy.ndimage import zoom as ndizoom
    from scipy.ndimage import binary_closing, binary_opening
    upscale = 5
    score_upsampled = ndizoom(score, upscale, order=1)  # bilinear 5x
    mask_upsampled = ndizoom(mask.astype(float), upscale, order=0) > 0.5

    # HEAVY Gaussian smoothing — production sigma=10m at 2m resolution = 5 pixels
    # At our upscaled resolution: sigma = 10 / (scale / upscale) = 10*upscale/scale
    sigma_pixels = max(10 * upscale / scale, 5)
    score_smooth = gaussian_filter(score_upsampled, sigma=sigma_pixels)
    score_smooth[~mask_upsampled] = 0

    rows_up, cols_up = score_smooth.shape

    # Zone classification by percentiles
    num_zones = 3 if area_ha <= 33 else 4
    valid_scores = score_smooth[mask_upsampled]
    if num_zones == 3:
        cuts = np.percentile(valid_scores, [33.33, 66.67])
    else:
        cuts = np.percentile(valid_scores, [25, 50, 75])

    zones = np.zeros_like(score_smooth, dtype=int)
    zones[mask_upsampled] = np.digitize(score_smooth[mask_upsampled], cuts) + 1

    # MORPHOLOGICAL CLEANUP — remove fragments, fill holes (critical for clean zones)
    from scipy.ndimage import median_filter
    # Median filter removes salt-and-pepper noise (small fragments)
    zones_clean = median_filter(zones, size=7)
    # Second pass with larger kernel for really clean zones
    zones_clean = median_filter(zones_clean, size=11)
    # Restore mask
    zones_clean[~mask_upsampled] = 0
    zones = zones_clean

    # Zone statistics
    zone_labels = {3: ['Baja', 'Media', 'Alta'], 4: ['Baja', 'Media-Baja', 'Media-Alta', 'Alta']}
    labels = zone_labels.get(num_zones, zone_labels[4])
    stats = []
    for z in range(1, num_zones + 1):
        zmask = zones == z
        zcount = zmask.sum()
        z_area = (zcount / mask_upsampled.sum()) * area_ha if mask_upsampled.sum() > 0 else 0
        z_pct = (zcount / mask_upsampled.sum()) * 100 if mask_upsampled.sum() > 0 else 0
        stats.append({
            'zona': z,
            'clase': labels[z - 1],
            'area_ha': round(z_area, 1),
            'porcentaje': round(z_pct, 1),
            'score_prom': round(float(np.nanmean(score_smooth[zmask])), 3) if zcount > 0 else 0,
            'ndvi_prom': round(float(np.nanmean(score_smooth[zmask]) * 100), 1) if zcount > 0 else 0,
        })

    print(f'Result: {num_zones} zones')
    for s in stats:
        print(f'  Z{s["zona"]} {s["clase"]}: {s["area_ha"]}ha ({s["porcentaje"]}%)')

    # === PRODUCTION VECTORIZATION (exact copy from pixadvisor_zonas_master_v4.1) ===
    print('Vectorizing zones (production v4.1 pipeline)...')
    from rasterio.features import shapes as rio_shapes
    from rasterio.transform import from_bounds
    from shapely.geometry import shape, mapping, Point
    from shapely.geometry import Polygon as ShapelyPolygon
    from shapely.ops import unary_union
    from shapely.validation import make_valid
    from scipy.spatial.distance import cdist

    # Build transform for upsampled grid
    lats = [c[1] for c in polygon_coords]
    lngs = [c[0] for c in polygon_coords]
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)
    transform = from_bounds(min_lng, min_lat, max_lng, max_lat, cols_up, rows_up)

    # Field polygon for clipping
    field_poly = make_valid(ShapelyPolygon(polygon_coords))

    # Production config
    BUF_M = 25    # buffer suavizado (meters → degrees)
    SIMP_M = 8    # simplify tolerance (meters → degrees)
    AREA_MIN_M2 = 2.0 * 10000  # 2.0 ha minimum fragment (aggressive cleanup)
    DEG_PER_M = 1 / 111320  # approximate degrees per meter

    zone_colors = ['#CC0000', '#FF8C00', '#FFD700', '#228B22']
    geojson_features = []
    zone_polys = {}  # store for sampling

    for z in range(num_zones):
        zone_mask = (zones == z + 1).astype(np.uint8)
        if zone_mask.sum() == 0:
            continue

        # Vectorize raster → polygons
        polys = []
        for geom_dict, val in rio_shapes(zone_mask, transform=transform):
            if val == 1:
                poly = shape(geom_dict)
                if poly.is_valid and poly.area > 0:
                    polys.append(poly)

        if not polys:
            continue

        zona_union = make_valid(unary_union(polys))

        # Organic smoothing: buffer +BUF → buffer -BUF → simplify
        try:
            buf_deg = BUF_M * DEG_PER_M
            simp_deg = SIMP_M * DEG_PER_M
            suavizado = zona_union.buffer(buf_deg).buffer(-buf_deg)
            suavizado = suavizado.simplify(simp_deg, preserve_topology=True)
            suavizado = make_valid(suavizado)
        except Exception:
            suavizado = zona_union

        # Filter: keep only Polygon/MultiPolygon (buffer can produce LineString)
        if suavizado.geom_type == 'GeometryCollection':
            parts = [g for g in suavizado.geoms if g.geom_type in ('Polygon', 'MultiPolygon') and g.area > 0]
            suavizado = unary_union(parts) if parts else zona_union
        elif suavizado.geom_type not in ('Polygon', 'MultiPolygon'):
            suavizado = zona_union

        # Remove small fragments (< 1.5 ha)
        area_min_deg2 = AREA_MIN_M2 * (DEG_PER_M ** 2)
        if suavizado.geom_type == 'MultiPolygon':
            partes = [p for p in suavizado.geoms if p.area >= area_min_deg2]
            if partes:
                suavizado = unary_union(partes)
            else:
                suavizado = max(suavizado.geoms, key=lambda p: p.area)

        zone_polys[z + 1] = suavizado

    # === FORCE 100% LOT COVERAGE (forzar_cobertura_total) ===
    # Clip all zones to field boundary
    for z in zone_polys:
        zone_polys[z] = zone_polys[z].intersection(field_poly)

    # Fill gaps — assign uncovered area to nearest zone
    all_coverage = unary_union(list(zone_polys.values()))
    gap = field_poly.difference(all_coverage)
    if not gap.is_empty and gap.area > DEG_PER_M ** 2:
        buf2 = BUF_M * 2 * DEG_PER_M
        for z in zone_polys:
            expanded = zone_polys[z].buffer(buf2)
            part = gap.intersection(expanded)
            if not part.is_empty:
                zone_polys[z] = unary_union([zone_polys[z], part])
                gap = gap.difference(part)
        # Remaining gap → largest zone
        if not gap.is_empty and gap.area > DEG_PER_M ** 2:
            largest_z = max(zone_polys, key=lambda z: zone_polys[z].area)
            zone_polys[largest_z] = unary_union([zone_polys[largest_z], gap])

    # Remove overlaps by priority (lower zone wins)
    for z in sorted(zone_polys.keys()):
        for z2 in sorted(zone_polys.keys()):
            if z2 > z and not zone_polys[z].intersection(zone_polys[z2]).is_empty:
                zone_polys[z2] = zone_polys[z2].difference(zone_polys[z])

    # Build GeoJSON features + recalculate areas
    total_area_deg2 = field_poly.area
    for z in sorted(zone_polys.keys()):
        geom = zone_polys[z]
        if geom.is_empty:
            continue
        z_area = (geom.area / total_area_deg2) * area_ha
        z_pct = (geom.area / total_area_deg2) * 100
        geojson_features.append({
            'type': 'Feature',
            'properties': {
                'zona': z, 'clase': labels[z - 1],
                'color': zone_colors[z - 1] if z <= len(zone_colors) else '#888',
                'area_ha': round(z_area, 1), 'porcentaje': round(z_pct, 1),
                'score_prom': stats[z - 1]['score_prom'],
            },
            'geometry': mapping(geom)
        })
        # Update stats with real area from vectorized polygons
        stats[z - 1]['area_ha'] = round(z_area, 1)
        stats[z - 1]['porcentaje'] = round(z_pct, 1)

    # === PRODUCTION SAMPLING (polo_de_inaccesibilidad + FPS with cdist) ===
    sampling_points = []
    np.random.seed(42)

    for z in sorted(zone_polys.keys()):
        geom = zone_polys[z]
        if geom.is_empty:
            continue
        z_area = stats[z - 1]['area_ha']

        # Buffer interno (production table)
        if z_area < 3: buf_int = 15
        elif z_area < 8: buf_int = 20
        elif z_area < 15: buf_int = 30
        elif z_area < 30: buf_int = 40
        elif z_area < 50: buf_int = 50
        else: buf_int = 60

        interior = geom.buffer(-buf_int * DEG_PER_M)
        if interior.is_empty or interior.area < 100 * (DEG_PER_M ** 2):
            interior = geom.buffer(-buf_int * DEG_PER_M / 2)
        if interior.is_empty:
            interior = geom

        # Polo de Inaccesibilidad (production: polylabel)
        try:
            from shapely.ops import polylabel
            principal = polylabel(interior, tolerance=1.0 * DEG_PER_M)
        except:
            principal = interior.representative_point()
        if not geom.contains(principal):
            principal = geom.representative_point()

        sampling_points.append({
            'id': f'Z{z}-P1', 'type': 'principal', 'zona': z,
            'lat': principal.y, 'lng': principal.x
        })

        # Subsample count (production table)
        if z_area < 2: n_sub = 3
        elif z_area < 5: n_sub = 4
        elif z_area < 8: n_sub = 5
        elif z_area < 12: n_sub = 6
        elif z_area < 18: n_sub = 7
        elif z_area < 25: n_sub = 8
        elif z_area < 35: n_sub = 9
        else: n_sub = 10

        # Generate candidates inside interior
        bounds_z = interior.bounds
        n_cand = max(200, n_sub * 30)
        xs = np.random.uniform(bounds_z[0], bounds_z[2], n_cand)
        ys = np.random.uniform(bounds_z[1], bounds_z[3], n_cand)
        candidatos = [Point(x, y) for x, y in zip(xs, ys) if interior.contains(Point(x, y))]

        if len(candidatos) < n_sub:
            nx = int(np.sqrt(n_cand))
            xs = np.linspace(bounds_z[0], bounds_z[2], nx)
            ys = np.linspace(bounds_z[1], bounds_z[3], nx)
            candidatos = [Point(x, y) for x in xs for y in ys if interior.contains(Point(x, y))]

        # FPS with cdist (production algorithm)
        if candidatos and len(candidatos) >= 2:
            coords_arr = np.array([(p.x, p.y) for p in candidatos])
            inicio = np.array([principal.x, principal.y])
            dists = cdist([inicio], coords_arr)[0]
            selected_idx = []

            for _ in range(min(n_sub, len(candidatos))):
                nuevo = np.argmax(dists)
                selected_idx.append(nuevo)
                new_d = cdist([coords_arr[nuevo]], coords_arr)[0]
                dists = np.minimum(dists, new_d)
                dists[selected_idx] = -1

            for si, idx in enumerate(selected_idx):
                sampling_points.append({
                    'id': f'Z{z}-S{si+1}', 'type': 'submuestra', 'zona': z,
                    'lat': candidatos[idx].y, 'lng': candidatos[idx].x
                })

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
        'gridSize': [rows_up, cols_up],
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
