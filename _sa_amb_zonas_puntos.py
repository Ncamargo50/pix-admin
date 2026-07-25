# -*- coding: utf-8 -*-
"""SERRO ALTO (HACIENDA COMPLETA) — AMBIENTES v2.1 validados aplicados a TODOS los bloques.
Metodologia identica a la validada en B14: color de suelo (redness suelo desnudo seco) dominante
+ arcilla + drenaje/topografia + vigor verano; clasificacion BLOCK-WIDE por bloque; zonas
excluyentes; puntos mismo patron (_b14_full); IDs unicos con zona. Loop bloques 2,3,14."""
import os, sys, math, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, pandas as pd, numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize, shapes
from scipy.ndimage import median_filter, gaussian_filter, distance_transform_edt
from shapely.geometry import shape, Point, mapping
from shapely.ops import unary_union
from shapely import ops as shops
from sklearn.cluster import KMeans
import warnings; warnings.filterwarnings('ignore')

BASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
CAN = os.path.join(BASE, '_analisis_canadas'); OUT = os.path.join(CAN, 'AMBIENTES_V2')
APKD = os.path.join(OUT, 'APK_muestreo_por_lote'); os.makedirs(APKD, exist_ok=True)
BLOCKS = ['2', '3', '14']; MIN_BARE = 4
W = dict(redness=0.36, clay_inv=0.10, twi_inv=0.10, elev=0.08, flow_inv=0.06, distdren=0.06, ndvi=0.16, estab=0.08)
assert abs(sum(W.values())-1.0) < 1e-6
CLASE = {1: 'Bajura negra', 2: 'Transicion', 3: 'Altura roja'}
COLOR = {'Bajura negra': '#3E2723', 'Transicion': '#FFB300', 'Altura roja': '#D84315'}
# clase que el APK PIX Muestreo reconoce para colorear zonas (_getZonaColor: baja/media/alta).
# El nombre descriptivo del ambiente va en 'ambiente'/'name'; 'clase' habilita el color en la app.
CLA_APK = {1: 'Baja', 2: 'Media', 3: 'Alta'}
EDGE_BUF = 20.0

# ---------- grid de referencia = veg_summer_full ----------
veg = rasterio.open(os.path.join(OUT, 'veg_summer_full.tif'))
REF_T, REF_CRS, H, Wd = veg.transform, veg.crs, veg.height, veg.width
ndvi = veg.read(1).astype('float32'); ndstd = veg.read(2).astype('float32')

def resample(path, b=1, how=Resampling.bilinear):
    with rasterio.open(path) as s:
        dst = np.full((H, Wd), np.nan, 'float32')
        reproject(rasterio.band(s, b), dst, src_transform=s.transform, src_crs=s.crs,
                  dst_transform=REF_T, dst_crs=REF_CRS, resampling=how)
    return dst

# ---------- indices de SUELO (suelo desnudo seco, enmascarado a bare_count>=MIN_BARE) ----------
soil = rasterio.open(os.path.join(OUT, 'soil_bare_full.tif'))
sidx = {n: i+1 for i, n in enumerate(['B2','B3','B4','B8','B11','B12','bare_count'])}
def sread(n):
    dst = np.full((H, Wd), np.nan, 'float32')
    reproject(rasterio.band(soil, sidx[n]), dst, src_transform=soil.transform, src_crs=soil.crs,
              dst_transform=REF_T, dst_crs=REF_CRS, resampling=Resampling.nearest)
    return dst
B2, B3, B4, B11, B12, bcount = sread('B2'), sread('B3'), sread('B4'), sread('B11'), sread('B12'), sread('bare_count')
reliable = np.isfinite(B4) & (B4 > 0) & (bcount >= MIN_BARE)
clay = np.where(reliable & (B12 > 0), B11/B12, np.nan).astype('float32')
redness = np.where(reliable & (B2 > 0), B4/B2, np.nan).astype('float32')

# ---------- topografia / hidrologia (reuso, cubren la hacienda) ----------
twi = resample(os.path.join(CAN, 'hydro_twi.tif')); twi[twi < -50] = np.nan
flow = np.log10(np.clip(resample(os.path.join(CAN, 'hydro_flowacc.tif')), 1, None))
dem = resample(os.path.join(CAN, 'dem_fabdem.tif')); dem[dem < -50] = np.nan
dren = gpd.read_file(os.path.join(BASE, 'DRENAJES_FINAL_SerroAlto.geojson')).to_crs(REF_CRS)
drm = rasterize([(g, 1) for g in dren.geometry], out_shape=(H, Wd), transform=REF_T, fill=0).astype(bool)
distdren = distance_transform_edt(~drm)*abs(REF_T.a)

def norm(a, m):
    v = a[m & np.isfinite(a)]
    if v.size < 5: return np.zeros_like(a, 'float32')
    lo, hi = np.percentile(v, 5), np.percentile(v, 95)
    return np.clip((a-lo)/(hi-lo), 0, 1).astype('float32') if hi-lo > 1e-9 else np.full_like(a, .5, 'float32')

def gapfill(a, mask):
    src = mask & np.isfinite(a)
    if src.sum() < 5: return a
    _, (iy, ix) = distance_transform_edt(~src, return_indices=True)
    out = a.copy(); need = mask & ~np.isfinite(a); out[need] = a[iy[need], ix[need]]
    return out

# ---------- patron de puntos IDENTICO al original _b14_points_v2.py ----------
# 1 PRINCIPAL por ambiente al centro (polylabel); P{zona}; submuestras FPS {pid}-{NN}
def center(poly):
    p = poly if poly.geom_type == 'Polygon' else max(poly.geoms, key=lambda g: g.area)
    try: return shops.polylabel(p, tolerance=2)
    except Exception: return p.representative_point()
def dens(a): return 5 if a < 3 else 7 if a < 10 else 10 if a < 20 else 12   # submuestras por ambiente
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
def fps(g, n, seed):
    sp = max(math.sqrt(max(g.area, 1)/(n*6)), 4); cs = grid_pts(g, sp)
    while len(cs) < n*2 and sp > 2.5: sp *= .6; cs = grid_pts(g, sp)
    if not cs: cs = [g.representative_point()]
    sel = [seed]; pool = [p for p in cs if p.distance(seed) > .1]
    while len(sel) < n+1 and pool:
        d = [min(p.distance(s) for s in sel) for p in pool]; nx = pool[int(np.argmax(d))]; sel.append(nx); pool.remove(nx)
    return sel[1:n+1]

ALL_Z = []; ALL_P = []; ALL_ZREC = []
for BK in BLOCKS:
    lotes = gpd.read_file(os.path.join(CAN, 'Lotes_B%s_divisiones.geojson' % BK)).to_crs(31981)
    LOTE_M = rasterize([(g, 1) for g in lotes.geometry], out_shape=(H, Wd), transform=REF_T, fill=0).astype(bool)
    red_b = gapfill(redness, LOTE_M); clay_b = gapfill(clay, LOTE_M)
    M = LOTE_M & np.isfinite(ndvi) & np.isfinite(red_b) & np.isfinite(dem)
    if M.sum() < 20:
        print('Bloque %s sin datos suficientes' % BK); continue
    SCORE = (W['redness']*norm(red_b, M) + W['clay_inv']*(1-norm(clay_b, M)) + W['twi_inv']*(1-norm(twi, M)) +
             W['elev']*norm(dem, M) + W['flow_inv']*(1-norm(flow, M)) + W['distdren']*norm(distdren, M) +
             W['ndvi']*norm(ndvi, M) + W['estab']*(1-norm(ndstd, M)))
    SCORE = gaussian_filter(np.where(M, SCORE, float(np.nanmean(SCORE[M]))), sigma=2.0)
    sv = SCORE[M].reshape(-1, 1)
    km = KMeans(n_clusters=3, n_init=10, random_state=42).fit(sv)
    order = np.argsort([sv[km.labels_ == k].mean() for k in range(3)])
    remap = {order[0]: 1, order[1]: 2, order[2]: 3}
    ZR = np.zeros((H, Wd), 'int16'); ZR[M] = np.vectorize(remap.get)(km.labels_).astype('int16')
    ZR[M] = median_filter(ZR, 5)[M]

    zrecs = []; precs = []; zfeats = []
    for _, lr in lotes.iterrows():
        lote = lr['lote']; geom = lr.geometry
        m = rasterize([(geom, 1)], out_shape=(H, Wd), transform=REF_T, fill=0).astype(bool) & M
        if m.sum() < 8: continue
        z = np.where(m, ZR, 0); apk = []; taken = None
        for zz in (1, 2, 3):
            mm = m & (z == zz)
            if mm.sum() == 0: continue
            polys = [shape(g) for g, v in shapes((z == zz).astype('uint8'), mask=(z == zz), transform=REF_T) if v == 1]
            if not polys: continue
            zg = unary_union(polys).buffer(15).buffer(-15).intersection(geom)
            if taken is not None and not zg.is_empty: zg = zg.difference(taken)
            if not zg.is_valid: zg = zg.buffer(0)          # repara self-intersections de difference()
            if zg.is_empty or zg.area < 4000: continue
            taken = zg if taken is None else unary_union([taken, zg])
            clase = CLASE[zz]; zarea = zg.area/1e4
            zrecs.append(dict(lote=lote, bloque=BK, zona=zz, ambiente=clase, area_ha=round(zarea, 2),
                              redness=round(float(np.nanmean(red_b[mm])), 3), clay=round(float(np.nanmean(clay_b[mm])), 3),
                              elev_m=round(float(np.nanmean(dem[mm])), 1), twi=round(float(np.nanmean(twi[mm])), 2),
                              ndvi_verano=round(float(np.nanmean(ndvi[mm])), 3)))
            zfeats.append(dict(lote=lote, bloque=BK, zona=zz, ambiente=clase, clase=CLA_APK[zz], geometry=zg))
            apk.append({'type': 'Feature', 'properties': {'name': clase, 'zona': zz, 'ambiente': clase, 'clase': CLA_APK[zz],
                        'color': COLOR[clase], 'fill': COLOR[clase], 'area_ha': round(zarea, 2), 'type': 'zona'},
                        'geometry': mapping(gpd.GeoSeries([zg], crs=31981).to_crs(4326).iloc[0])})
            # UN principal por ambiente al centro + submuestras FPS (nomenclatura original P{zona})
            core = core_of(zg); prin = center(core)
            pid = '%s-B%s-P%d' % (lote, BK, zz)
            precs.append(dict(punto_id=pid, name='P%d' % zz, tipo='PRINCIPAL', lote=lote, bloque=BK, zona=zz,
                              ambiente=clase, clase=CLA_APK[zz], principal=pid, geometry=prin))
            for ms, sp in enumerate(fps(core, dens(zarea), prin), 1):
                precs.append(dict(punto_id='%s-%02d' % (pid, ms), name='P%d-%02d' % (zz, ms), tipo='SUBMUESTRA',
                                  lote=lote, bloque=BK, zona=zz, ambiente=clase, clase=CLA_APK[zz], principal=pid, geometry=sp))
        pl = [p for p in precs if p['lote'] == lote]
        for p in pl:
            p4 = gpd.GeoSeries([p['geometry']], crs=31981).to_crs(4326).iloc[0]
            apk.append({'type': 'Feature', 'properties': {'id': p['punto_id'], 'name': p['name'], 'tipo': p['tipo'].lower(),
                        'zona': p['zona'], 'ambiente': p['ambiente'], 'clase': p['clase'], 'principal': p['principal'],
                        'status': 'pendiente', 'marker-color': COLOR[p['ambiente']], 'type': 'point'}, 'geometry': mapping(p4)})
        with open(os.path.join(APKD, 'Bloque-%s-%s_muestreo.geojson' % (BK, lote)), 'w', encoding='utf-8') as f:
            json.dump({'type': 'FeatureCollection', 'name': 'B%s-%s_muestreo' % (BK, lote), 'features': apk}, f, ensure_ascii=False)

    zg_gdf = gpd.GeoDataFrame(zfeats, crs=31981); zg_gdf['color'] = zg_gdf['ambiente'].map(COLOR)
    zg_gdf = zg_gdf.to_crs(4326); zg_gdf['geometry'] = zg_gdf.geometry.buffer(0)   # valida en el CRS de salida
    zg_gdf.to_file(os.path.join(OUT, 'ZONAS_B%s_V2.geojson' % BK), driver='GeoJSON')
    pg = gpd.GeoDataFrame(precs, crs=31981)
    dups = pg['punto_id'].duplicated().sum(); assert dups == 0, 'DUP %s' % BK
    zj = gpd.sjoin(pg[['punto_id', 'zona', 'geometry']], zg_gdf.to_crs(31981)[['zona', 'geometry']].rename(columns={'zona': 'zp'}), predicate='within', how='left').drop_duplicates('punto_id')
    fuera = int(zj['zp'].isna().sum())
    pg4 = pg.to_crs(4326); pg4['lon'] = pg4.geometry.x.round(6); pg4['lat'] = pg4.geometry.y.round(6)
    pg4.to_file(os.path.join(OUT, 'PUNTOS_B%s_V2.geojson' % BK), driver='GeoJSON')
    nP = int((pg.tipo == 'PRINCIPAL').sum()); nS = int((pg.tipo == 'SUBMUESTRA').sum())
    print('Bloque %-3s: %2d lotes | %2d zonas | %3d princ + %3d sub | dups=%d fuera=%d | %.0f ha' % (
        BK, lotes['lote'].nunique(), len(zg_gdf), nP, nS, dups, fuera, sum(r['area_ha'] for r in zrecs)))
    ALL_Z.append(zg_gdf.to_crs(4326)); ALL_P.append(pg4); ALL_ZREC += zrecs

# combinados hacienda
allz = gpd.GeoDataFrame(pd.concat(ALL_Z, ignore_index=True), crs=4326)
allz['geometry'] = allz.geometry.buffer(0)                # repara self-intersections (0% cambio de area)
assert allz.is_valid.all(), 'ZONAS INVALIDAS TRAS REPARACION'
allz.to_file(os.path.join(OUT, 'ZONAS_SerroAlto_V2.geojson'), driver='GeoJSON')
allp = gpd.GeoDataFrame(pd.concat(ALL_P, ignore_index=True), crs=4326)
allp.to_file(os.path.join(OUT, 'PUNTOS_SerroAlto_V2.geojson'), driver='GeoJSON')
allp.drop(columns='geometry').to_csv(os.path.join(OUT, 'SerroAlto_puntos_V2.csv'), index=False, encoding='utf-8-sig')
pd.DataFrame(ALL_ZREC).to_csv(os.path.join(OUT, 'SerroAlto_zonas_V2.csv'), index=False, encoding='utf-8-sig')
zdf = pd.DataFrame(ALL_ZREC)
print('\n=== HACIENDA SERRO ALTO — TOTAL ===')
print('IDs unicos global:', allp['punto_id'].is_unique, '| duplicados:', int(allp['punto_id'].duplicated().sum()))
print('Zonas:', len(allz), '| Principales:', int((allp.tipo=='PRINCIPAL').sum()), '| Submuestras:', int((allp.tipo=='SUBMUESTRA').sum()))
for amb in ['Altura roja', 'Transicion', 'Bajura negra']:
    s = zdf[zdf.ambiente == amb]
    print('  %-13s %6.1f ha | redness=%.2f clay=%.3f elev=%.1f twi=%.2f ndvi=%.2f' % (
        amb, s.area_ha.sum(), s.redness.mean(), s.clay.mean(), s.elev_m.mean(), s.twi.mean(), s.ndvi_verano.mean()))
print('DONE zonas+puntos hacienda')
