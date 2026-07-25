# -*- coding: utf-8 -*-
"""Bloque 14 completo: re-zonifica cada DIVISION (3 ambientes, score compuesto
skill), puntos (principal en CENTRO=pole of inaccessibility + submuestras
distribuidas, buffer borde), nomenclatura nueva, y GeoJSON APK con colores."""
import os, sys, math, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, pandas as pd, numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize, shapes
from scipy.ndimage import median_filter, gaussian_filter, distance_transform_edt
from shapely.geometry import shape, Point, MultiPoint, mapping
from shapely.ops import unary_union, nearest_points
from shapely import ops as shops
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import warnings; warnings.filterwarnings('ignore')

D = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUT = os.path.join(D, '_analisis_canadas'); PNGD = os.path.join(OUT, 'B14_muestreo_png'); os.makedirs(PNGD, exist_ok=True)
APKD = os.path.join(D, 'APK_muestreo_por_lote'); os.makedirs(APKD, exist_ok=True)
W = dict(ndvi=0.25, ndre=0.15, estab=0.15, twi=0.10, flujo_inv=0.10, pend_inv=0.10, elev=0.05, distdren=0.10)
CLASE = {1: 'Baja', 2: 'Media', 3: 'Alta'}; COLOR = {'Baja': '#F44336', 'Media': '#FFEB3B', 'Alta': '#4CAF50'}
EDGE_BUF = 20.0; SUBPTS_MINY = 8

fsrc = rasterio.open(os.path.join(OUT, 'zm_features_veg.tif'))
REF_T, REF_CRS, H, Wd = fsrc.transform, fsrc.crs, fsrc.height, fsrc.width
ndvi = fsrc.read(1).astype('float32'); ndstd = fsrc.read(2).astype('float32'); ndre = fsrc.read(3).astype('float32')
pxh = abs(REF_T.a*REF_T.e)/1e4

def resample(p, b=1):
    with rasterio.open(p) as s:
        dst = np.full((H, Wd), np.nan, 'float32')
        reproject(rasterio.band(s, b), dst, src_transform=s.transform, src_crs=s.crs, dst_transform=REF_T, dst_crs=REF_CRS, resampling=Resampling.bilinear)
    return dst
twi = resample(os.path.join(OUT, 'hydro_twi.tif')); twi[twi < -50] = np.nan
flow = np.log10(np.clip(resample(os.path.join(OUT, 'hydro_flowacc.tif')), 1, None))
dem = resample(os.path.join(OUT, 'dem_fabdem.tif')); dem[dem < -50] = np.nan
gy, gx = np.gradient(np.nan_to_num(dem, nan=np.nanmedian(dem)), abs(REF_T.a), abs(REF_T.a))
slope = np.degrees(np.arctan(np.hypot(gx, gy)))
dren = gpd.read_file(os.path.join(D, 'DRENAJES_FINAL_SerroAlto.geojson')).to_crs(REF_CRS)
drm = rasterize([(g, 1) for g in dren.geometry], out_shape=(H, Wd), transform=REF_T, fill=0).astype(bool)
distdren = distance_transform_edt(~drm)*abs(REF_T.a)

lotes = gpd.read_file(os.path.join(D, 'Lotes_B14_divisiones.geojson')).to_crs(31981)

def norm(a, m):
    v = a[m & np.isfinite(a)]
    if v.size < 5: return np.zeros_like(a, 'float32')
    lo, hi = np.percentile(v, 5), np.percentile(v, 95)
    return np.clip((a-lo)/(hi-lo), 0, 1).astype('float32') if hi-lo > 1e-9 else np.full_like(a, .5, 'float32')

def center(poly):
    p = poly if poly.geom_type == 'Polygon' else max(poly.geoms, key=lambda g: g.area)
    try: return shops.polylabel(p, tolerance=2)
    except Exception: return p.representative_point()

def densidad(a):
    return (1, 5) if a < 3 else (1, 7) if a < 10 else (1, 10) if a < 20 else (2, 8)

def core_of(poly):
    for b in (EDGE_BUF, 12, 6, 0):
        c = poly.buffer(-b)
        if (not c.is_empty) and c.area >= max(0.1*poly.area, 1200): return c
    return poly

def grid_pts(g, sp):
    mnx, mny, mxx, mxy = g.bounds; o = []; y = mny
    while y <= mxy:
        x = mnx
        while x <= mxx:
            if g.contains(Point(x, y)): o.append(Point(x, y))
            x += sp
        y += sp
    return o

def cand(g, n):
    sp = max(math.sqrt(max(g.area, 1)/(n*6)), 4); c = grid_pts(g, sp)
    while len(c) < n*2 and sp > 2.5: sp *= .6; c = grid_pts(g, sp)
    return c or [g.representative_point()]

def fps(cs, n, seed=None):
    if not cs: return []
    sel = [seed or cs[0]]; pool = [p for p in cs if p.distance(sel[0]) > .1]
    while len(sel) < n and pool:
        d = [min(p.distance(s) for s in sel) for p in pool]; nx = pool[int(np.argmax(d))]; sel.append(nx); pool.remove(nx)
    return sel[:n]

zrecs = []; precs = []; zone_feats_all = []
for _, lr in lotes.iterrows():
    lote = lr['lote']; geom = lr.geometry
    m = rasterize([(geom, 1)], out_shape=(H, Wd), transform=REF_T, fill=0).astype(bool) & np.isfinite(ndvi)
    if m.sum() < SUBPTS_MINY:
        continue
    score = (W['ndvi']*norm(ndvi, m)+W['ndre']*norm(ndre, m)+W['estab']*(1-norm(ndstd, m))+W['twi']*norm(twi, m)
             + W['flujo_inv']*(1-norm(flow, m))+W['pend_inv']*(1-norm(slope, m))+W['elev']*norm(dem, m)+W['distdren']*norm(distdren, m))
    score = gaussian_filter(np.where(m, score, np.nanmean(score[m])), sigma=2.5)
    c1, c2 = np.percentile(score[m], [33.3, 66.7])
    z = np.zeros((H, Wd), 'int16'); z[m] = np.digitize(score[m], [c1, c2])+1; z[m] = median_filter(z, 5)[m]
    apk_feats = []
    for zz in (1, 2, 3):
        mm = (z == zz).astype('uint8')
        polys = [shape(g) for g, v in shapes(mm, mask=(z == zz), transform=REF_T) if v == 1]
        if not polys: continue
        zg = unary_union(polys).buffer(20).buffer(-20).intersection(geom)
        if zg.is_empty or zg.area < 4000: continue
        clase = CLASE[zz]; zarea = zg.area/1e4
        zrecs.append(dict(lote=lote, bloque='14', zona=zz, clase=clase, area_ha=round(zarea, 2)))
        zone_feats_all.append(dict(lote=lote, zona=zz, clase=clase, geometry=zg))
        apk_feats.append({'type': 'Feature', 'properties': {'name': 'Zona %d' % zz, 'zona': zz, 'clase': clase,
                          'color': COLOR[clase], 'area_ha': round(zarea, 2), 'type': 'zona'}, 'geometry': mapping(gpd.GeoSeries([zg], crs=31981).to_crs(4326).iloc[0])})
        # --- muestreo: principal(es) al CENTRO + submuestras distribuidas ---
        nP, nS = densidad(zarea); core = core_of(zg)
        cc = cand(core, max(nP*nS, 6)); seeds = fps(cc, nP, seed=center(core))
        groups = {i: [] for i in range(nP)}
        for p in cc: groups[int(np.argmin([p.distance(s) for s in seeds]))].append(p)
        for ip in range(nP):
            sub_c = groups[ip] or cc
            subreg = unary_union([p.buffer(EDGE_BUF) for p in sub_c]).intersection(core) if nP > 1 else core
            prin = center(subreg if not subreg.is_empty else core)
            subs = fps(sub_c, nS, seed=prin)
            pid = '%s-B14-P%d-Z%d' % (lote, ip+1, zz)
            precs.append(dict(punto_id=pid, tipo='PRINCIPAL', lote=lote, bloque='14', zona=zz, clase=clase, geometry=prin))
            for ms, sp in enumerate(subs, 1):
                precs.append(dict(punto_id='%s-B14-P%d-%02d' % (lote, ip+1, ms), tipo='SUBMUESTRA', lote=lote, bloque='14', zona=zz, clase=clase, geometry=sp))
    # --- APK geojson por lote (SIN boundary; zonas con zona/clase/color; puntos coloreados) ---
    pl = [p for p in precs if p['lote'] == lote]
    for p in pl:
        p4 = gpd.GeoSeries([p['geometry']], crs=31981).to_crs(4326).iloc[0]
        short = 'Z%d-P%s' % (p['zona'], p['punto_id'].split('-P')[1])
        apk_feats.append({'type': 'Feature', 'properties': {'id': p['punto_id'], 'name': p['punto_id'].split('-', 1)[1] if False else p['punto_id'],
                          'tipo': p['tipo'].lower(), 'zona': p['zona'], 'clase': p['clase'], 'status': 'pendiente',
                          'marker-color': COLOR[p['clase']], 'type': 'point'}, 'geometry': mapping(p4)})
    with open(os.path.join(APKD, 'Bloque-14-%s_muestreo.geojson' % lote), 'w', encoding='utf-8') as f:
        json.dump({'type': 'FeatureCollection', 'name': 'B14-%s_muestreo' % lote, 'features': apk_feats}, f, ensure_ascii=False)

# exports
zg_gdf = gpd.GeoDataFrame(zone_feats_all, crs=31981)
zg_gdf['color'] = zg_gdf['clase'].map(COLOR)
zg_gdf.to_crs(4326).to_file(os.path.join(D, 'ZONAS_B14_GLOBAL.geojson'), driver='GeoJSON')
pg = gpd.GeoDataFrame(precs, crs=31981).to_crs(4326)
pg['lon'] = pg.geometry.x.round(6); pg['lat'] = pg.geometry.y.round(6)
pg.to_file(os.path.join(D, 'PUNTOS_B14.geojson'), driver='GeoJSON')
pg.drop(columns='geometry').to_csv(os.path.join(OUT, 'B14_puntos.csv'), index=False, encoding='utf-8-sig')
pd.DataFrame(zrecs).to_csv(os.path.join(OUT, 'B14_zonas.csv'), index=False, encoding='utf-8-sig')

nP = (pg.tipo == 'PRINCIPAL').sum(); nS = (pg.tipo == 'SUBMUESTRA').sum()
print('Bloque 14: %d divisiones-lote | %d zonas | %d principales + %d submuestras' % (lotes['lote'].nunique(), len(zg_gdf), nP, nS))
print('APK geojson:', len([x for x in os.listdir(APKD) if x.startswith('Bloque-14')]))
print('Ejemplo nomenclatura:', list(pg['punto_id'].head(6)))
print('DONE')
