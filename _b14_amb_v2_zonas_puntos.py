# -*- coding: utf-8 -*-
"""BLOQUE 14 v2 — RE-HACE AMBIENTES con TEXTURA/COLOR de suelo + topografia + vigor verano,
y RELOCA puntos/submuestras con el MISMO PATRON que _b14_full.py (principal=centro polylabel
+ submuestras FPS, buffer borde, misma nomenclatura {lote}-B14-P{n}-Z{z}).

Score compuesto rebalanceado (suelo+topo dominan ~78%, corrige el sesgo a vigor de la v1):
  redness .22  clay(inv) .18            -> SUELO/COLOR (roja altura vs negra bajura) .40
  twi(inv).12  rel_elev .12  flow(inv).06  distdren .08 -> TOPO/HIDRO (bajura/altura/flujo) .38
  ndvi_verano .14  estabilidad .08      -> VIGOR cultivo verano Nov-Mar 24/25+25/26 .22
Zona 3=Altura roja(bien drenada) | 2=Transicion | 1=Bajura negra(humeda/arcillosa).
"""
import os, sys, math, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, pandas as pd, numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize, shapes
from scipy.ndimage import median_filter, gaussian_filter, distance_transform_edt
from shapely.geometry import shape, Point, mapping
from shapely.ops import unary_union
from shapely import ops as shops
import warnings; warnings.filterwarnings('ignore')

BASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
CAN = os.path.join(BASE, '_analisis_canadas'); OUT = os.path.join(CAN, 'AMBIENTES_V2')
APKD = os.path.join(OUT, 'APK_muestreo_por_lote'); os.makedirs(APKD, exist_ok=True)

# Pesos v2.1 (post-auditoria): COLOR de suelo domina (redness es el unico discriminador
# validado y coincide con lo que ven los tecnicos); arcilla baja (senal debil, spread 0.03,
# la textura la define el laboratorio); topo/hidro secundario pero incluye flujo de agua.
W = dict(redness=0.36, clay_inv=0.10, twi_inv=0.10, elev=0.08, flow_inv=0.06, distdren=0.06, ndvi=0.16, estab=0.08)
assert abs(sum(W.values())-1.0) < 1e-6, 'PESOS NO SUMAN 1.0'
CLASE = {1: 'Bajura negra', 2: 'Transicion', 3: 'Altura roja'}
COLOR = {'Bajura negra': '#3E2723', 'Transicion': '#FFB300', 'Altura roja': '#D84315'}
EDGE_BUF = 20.0

# ---------- grid de referencia = veg_summer (S2 10m) ----------
veg = rasterio.open(os.path.join(OUT, 'veg_summer.tif'))
REF_T, REF_CRS, H, Wd = veg.transform, veg.crs, veg.height, veg.width
ndvi = veg.read(1).astype('float32'); ndstd = veg.read(2).astype('float32')
pxh = abs(REF_T.a*REF_T.e)/1e4

def resample(path, b=1):
    with rasterio.open(path) as s:
        dst = np.full((H, Wd), np.nan, 'float32')
        reproject(rasterio.band(s, b), dst, src_transform=s.transform, src_crs=s.crs,
                  dst_transform=REF_T, dst_crs=REF_CRS, resampling=Resampling.bilinear)
    return dst

# suelo: leer con NEAREST (preserva mascara de confiabilidad), luego rellenar huecos
def resample_nn(path, b):
    with rasterio.open(path) as s:
        dst = np.full((H, Wd), np.nan, 'float32')
        reproject(rasterio.band(s, b), dst, src_transform=s.transform, src_crs=s.crs,
                  dst_transform=REF_T, dst_crs=REF_CRS, resampling=Resampling.nearest)
    return dst
si = os.path.join(OUT, 'soil_indices.tif')
clay = resample_nn(si, 1); redness = resample_nn(si, 3)

def gapfill(a, mask):
    """rellena NaN de 'a' con el valor confiable mas cercano DENTRO de mask (suelo varia suave)."""
    src = mask & np.isfinite(a)
    if src.sum() < 5: return a
    from scipy.ndimage import distance_transform_edt
    _, (iy, ix) = distance_transform_edt(~src, return_indices=True)
    out = a.copy(); need = mask & ~np.isfinite(a)
    out[need] = a[iy[need], ix[need]]
    return out
# topografia / hidrologia (reuso de la v1)
twi = resample(os.path.join(CAN, 'hydro_twi.tif')); twi[twi < -50] = np.nan
flow = np.log10(np.clip(resample(os.path.join(CAN, 'hydro_flowacc.tif')), 1, None))
dem = resample(os.path.join(CAN, 'dem_fabdem.tif')); dem[dem < -50] = np.nan
dren = gpd.read_file(os.path.join(BASE, 'DRENAJES_FINAL_SerroAlto.geojson')).to_crs(REF_CRS)
drm = rasterize([(g, 1) for g in dren.geometry], out_shape=(H, Wd), transform=REF_T, fill=0).astype(bool)
distdren = distance_transform_edt(~drm)*abs(REF_T.a)

lotes = gpd.read_file(os.path.join(CAN, 'Lotes_B14_divisiones.geojson')).to_crs(31981)

def norm(a, m):
    v = a[m & np.isfinite(a)]
    if v.size < 5: return np.zeros_like(a, 'float32')
    lo, hi = np.percentile(v, 5), np.percentile(v, 95)
    return np.clip((a-lo)/(hi-lo), 0, 1).astype('float32') if hi-lo > 1e-9 else np.full_like(a, .5, 'float32')

# ===== CLASIFICACION BLOCK-WIDE (respeta la estructura real de 2 cuerpos de suelo) =====
from sklearn.cluster import KMeans
LOTE_M = rasterize([(g, 1) for g in lotes.geometry], out_shape=(H, Wd), transform=REF_T, fill=0).astype(bool)
# rellenar color/textura de suelo con el pixel confiable mas cercano (cobertura completa)
redness = gapfill(redness, LOTE_M); clay = gapfill(clay, LOTE_M)
M14 = LOTE_M & np.isfinite(ndvi) & np.isfinite(redness) & np.isfinite(dem)
# score compuesto: ALTO = altura roja bien drenada ; BAJO = bajura negra humeda arcillosa
SCORE = (W['redness']*norm(redness, M14) + W['clay_inv']*(1-norm(clay, M14)) +
         W['twi_inv']*(1-norm(twi, M14)) + W['elev']*norm(dem, M14) +
         W['flow_inv']*(1-norm(flow, M14)) + W['distdren']*norm(distdren, M14) +
         W['ndvi']*norm(ndvi, M14) + W['estab']*(1-norm(ndstd, M14)))
_fill = float(np.nanmean(SCORE[M14]))
SCORE = gaussian_filter(np.where(M14, SCORE, _fill), sigma=2.0)   # coherencia espacial (sin NaN)
# k-means 3 clases sobre el score (block-wide), etiquetas ordenadas por score medio
sv = SCORE[M14].reshape(-1, 1)
km = KMeans(n_clusters=3, n_init=10, random_state=42).fit(sv)
order = np.argsort([sv[km.labels_ == k].mean() for k in range(3)])  # menor->mayor score
remap = {order[0]: 1, order[1]: 2, order[2]: 3}                      # 1=bajura ... 3=altura
ZG = np.zeros((H, Wd), 'int16')
ZG[M14] = np.vectorize(remap.get)(km.labels_).astype('int16')
ZG_f = ZG.copy(); ZG_f[M14] = median_filter(ZG, 5)[M14]              # suaviza bordes
ZG = ZG_f

# ---------- patron de puntos IDENTICO a _b14_full.py ----------
def center(poly):
    p = poly if poly.geom_type == 'Polygon' else max(poly.geoms, key=lambda g: g.area)
    try: return shops.polylabel(p, tolerance=2)
    except Exception: return p.representative_point()
def densidad(a): return (1, 5) if a < 3 else (1, 7) if a < 10 else (1, 10) if a < 20 else (2, 8)
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
    m = rasterize([(geom, 1)], out_shape=(H, Wd), transform=REF_T, fill=0).astype(bool) & M14
    if m.sum() < 8: continue
    z = np.where(m, ZG, 0)                     # clasificacion BLOCK-WIDE recortada al lote
    apk_feats = []
    taken = None                               # zonas MUTUAMENTE EXCLUYENTES (sin solape -> sin ambiguedad de puntos)
    for zz in (1, 2, 3):
        mm = m & (z == zz)
        if mm.sum() == 0: continue
        polys = [shape(g) for g, v in shapes((z == zz).astype('uint8'), mask=(z == zz), transform=REF_T) if v == 1]
        if not polys: continue
        zg = unary_union(polys).buffer(15).buffer(-15).intersection(geom)
        if taken is not None and not zg.is_empty:
            zg = zg.difference(taken)          # quita solape con zonas ya asignadas
        if zg.is_empty or zg.area < 4000: continue
        taken = zg if taken is None else unary_union([taken, zg])
        clase = CLASE[zz]; zarea = zg.area/1e4
        zrecs.append(dict(lote=lote, bloque='14', zona=zz, ambiente=clase, area_ha=round(zarea, 2),
                          redness=round(float(np.nanmean(redness[mm])), 3), clay=round(float(np.nanmean(clay[mm])), 3),
                          elev_m=round(float(np.nanmean(dem[mm])), 1), twi=round(float(np.nanmean(twi[mm])), 2),
                          ndvi_verano=round(float(np.nanmean(ndvi[mm])), 3), score=round(float(np.nanmean(SCORE[mm])), 3)))
        zone_feats_all.append(dict(lote=lote, zona=zz, ambiente=clase, geometry=zg))
        apk_feats.append({'type': 'Feature', 'properties': {'name': clase, 'zona': zz, 'ambiente': clase,
                          'color': COLOR[clase], 'area_ha': round(zarea, 2), 'type': 'zona'},
                          'geometry': mapping(gpd.GeoSeries([zg], crs=31981).to_crs(4326).iloc[0])})
        # --- muestreo: principal(es) al CENTRO + submuestras distribuidas (patron identico) ---
        nP, nS = densidad(zarea); core = core_of(zg)
        cc = cand(core, max(nP*nS, 6)); seeds = fps(cc, nP, seed=center(core))
        groups = {i: [] for i in range(nP)}
        for p in cc: groups[int(np.argmin([p.distance(s) for s in seeds]))].append(p)
        for ip in range(nP):
            sub_c = groups[ip] or cc
            subreg = unary_union([p.buffer(EDGE_BUF) for p in sub_c]).intersection(core) if nP > 1 else core
            prin = center(subreg if not subreg.is_empty else core)
            subs = fps(sub_c, nS, seed=prin)
            precs.append(dict(punto_id='%s-B14-P%d-Z%d' % (lote, ip+1, zz), tipo='PRINCIPAL', lote=lote,
                              bloque='14', zona=zz, ambiente=clase, geometry=prin))
            for ms, sp in enumerate(subs, 1):
                # C1 auditoria: ID incluye la ZONA -> submuestra unica (antes {lote}-P{n}-{ms} colisionaba entre zonas)
                precs.append(dict(punto_id='%s-B14-P%d-Z%d-%02d' % (lote, ip+1, zz, ms), tipo='SUBMUESTRA', lote=lote,
                                  bloque='14', zona=zz, ambiente=clase, geometry=sp))
    # APK geojson por lote
    pl = [p for p in precs if p['lote'] == lote]
    for p in pl:
        p4 = gpd.GeoSeries([p['geometry']], crs=31981).to_crs(4326).iloc[0]
        apk_feats.append({'type': 'Feature', 'properties': {'id': p['punto_id'], 'name': p['punto_id'],
                          'tipo': p['tipo'].lower(), 'zona': p['zona'], 'ambiente': p['ambiente'], 'clase': p['ambiente'],
                          'status': 'pendiente', 'marker-color': COLOR[p['ambiente']], 'type': 'point'}, 'geometry': mapping(p4)})
    with open(os.path.join(APKD, 'Bloque-14-%s_muestreo.geojson' % lote), 'w', encoding='utf-8') as f:
        json.dump({'type': 'FeatureCollection', 'name': 'B14-%s_muestreo' % lote, 'features': apk_feats}, f, ensure_ascii=False)

# exports
zg_gdf = gpd.GeoDataFrame(zone_feats_all, crs=31981)
zg_gdf['color'] = zg_gdf['ambiente'].map(COLOR)
assert zg_gdf.is_valid.all() or zg_gdf.buffer(0).is_valid.all(), 'GEOM INVALIDA'
zg_gdf.to_crs(4326).to_file(os.path.join(OUT, 'ZONAS_B14_V2.geojson'), driver='GeoJSON')
pg = gpd.GeoDataFrame(precs, crs=31981).to_crs(4326)
pg['lon'] = pg.geometry.x.round(6); pg['lat'] = pg.geometry.y.round(6)
pg.to_file(os.path.join(OUT, 'PUNTOS_B14_V2.geojson'), driver='GeoJSON')
pg.drop(columns='geometry').to_csv(os.path.join(OUT, 'B14_puntos_V2.csv'), index=False, encoding='utf-8-sig')
zdf = pd.DataFrame(zrecs).sort_values(['lote', 'zona'])
zdf.to_csv(os.path.join(OUT, 'B14_zonas_V2.csv'), index=False, encoding='utf-8-sig')

nP = (pg.tipo == 'PRINCIPAL').sum(); nS = (pg.tipo == 'SUBMUESTRA').sum()
# --- VERIFICACIONES (auditoria) ---
dups = pg['punto_id'].duplicated().sum()
assert dups == 0, 'IDS DUPLICADOS: %d' % dups
pg31 = gpd.GeoDataFrame(precs, crs=31981)[['punto_id', 'zona', 'geometry']]
zj = gpd.sjoin(pg31, zg_gdf[['zona', 'geometry']].rename(columns={'zona': 'zona_poly'}),
               predicate='within', how='left')
zj = zj.drop_duplicates('punto_id')
fuera = int(zj['zona_poly'].isna().sum()); malzona = int((zj['zona'] != zj['zona_poly']).sum() - fuera)
print('Bloque 14 v2.1: %d lotes | %d zonas | %d principales + %d submuestras' % (lotes['lote'].nunique(), len(zg_gdf), nP, nS))
print('VERIF: IDs duplicados=%d | puntos fuera de toda zona=%d | puntos en zona de otro numero=%d' % (dups, fuera, malzona))
print('APK geojson por lote:', len([x for x in os.listdir(APKD) if x.startswith('Bloque-14')]))
print('\n--- caracterizacion media por ambiente (verifica coherencia con campo) ---')
for zz in (3, 2, 1):
    s = zdf[zdf.zona == zz]
    if len(s):
        print('  Z%d %-13s: %5.1f ha | redness=%.2f clay=%.3f elev=%.1fm twi=%.2f ndvi_ver=%.2f' % (
            zz, CLASE[zz], s.area_ha.sum(), s.redness.mean(), s.clay.mean(), s.elev_m.mean(), s.twi.mean(), s.ndvi_verano.mean()))
print('Ejemplo nomenclatura:', list(pg['punto_id'].head(6)))
print('DONE zonas+puntos')
