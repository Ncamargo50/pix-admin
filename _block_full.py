# -*- coding: utf-8 -*-
"""Pipeline completo por bloque (arg). Divisiones S->N (L01 al Sur) + fusiona
<5ha + letras W->E; re-zonifica cada division (3 ambientes); puntos P{zona}
(P1=Baja/P2=Media/P3=Alta) centrados + submuestras; APK colores; PNGs."""
import os, sys, math, json, glob
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, pandas as pd, numpy as np, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize, shapes
from scipy.ndimage import median_filter, gaussian_filter, distance_transform_edt
from shapely.geometry import shape, Point, mapping
from shapely.ops import unary_union
from shapely import ops as shops
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import warnings; warnings.filterwarnings('ignore')

B = sys.argv[1]
D = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUT = os.path.join(D, '_analisis_canadas'); PNGD = os.path.join(OUT, 'B%s_muestreo_png' % B); os.makedirs(PNGD, exist_ok=True)
APKD = os.path.join(D, 'APK_muestreo_por_lote')
W = dict(ndvi=0.25, ndre=0.15, estab=0.15, twi=0.10, flujo_inv=0.10, pend_inv=0.10, elev=0.05, distdren=0.10)
CLASE = {1: 'Baja', 2: 'Media', 3: 'Alta'}; COLOR = {'Baja': '#F44336', 'Media': '#FFEB3B', 'Alta': '#4CAF50'}

# ---- divisiones S->N + fusion <5ha + letras ----
lot = gpd.read_file(os.path.join(D, 'Lotes_SerroAlto_LIMPIOS.geojson')).to_crs(31981)
bl = lot[lot.bloque.astype(str) == B].copy(); bl['cy'] = bl.geometry.centroid.y
bl = bl.sort_values('cy').reset_index(drop=True)
recs = []
for i, (_, r) in enumerate(bl.iterrows(), 1):
    ps = [r.geometry] if r.geometry.geom_type == 'Polygon' else sorted(list(r.geometry.geoms), key=lambda p: p.centroid.x)
    # fusionar partes <5ha en el vecino mas contiguo
    while len(ps) > 1 and min(p.area/1e4 for p in ps) < 5:
        si = int(np.argmin([p.area for p in ps])); s = ps[si]; others = [p for k, p in enumerate(ps) if k != si]
        def contig(o): return s.boundary.intersection(o.buffer(1)).length
        best = max(others, key=contig)
        if contig(best) < 1: best = min(others, key=lambda o: s.distance(o))
        ps = [unary_union([o, s]) if o is best else o for o in others]
        ps = sorted(ps, key=lambda p: p.centroid.x)
    for j, p in enumerate(ps):
        letter = chr(65+j) if len(ps) > 1 else ''
        recs.append(dict(lote='L%02d%s' % (i, letter), bloque=B, area_ha=round(p.area/1e4, 2), geometry=p))
div = gpd.GeoDataFrame(recs, crs=31981)
div.to_crs(4326).to_file(os.path.join(D, 'Lotes_B%s_divisiones.geojson' % B), driver='GeoJSON')
print('Bloque %s: %d divisiones | área %.1f ha' % (B, len(div), div.area_ha.sum()))

# ---- rasters ----
fsrc = rasterio.open(os.path.join(OUT, 'zm_features_veg.tif'))
REF_T, REF_CRS, H, Wd = fsrc.transform, fsrc.crs, fsrc.height, fsrc.width
ndvi = fsrc.read(1).astype('float32'); ndstd = fsrc.read(2).astype('float32'); ndre = fsrc.read(3).astype('float32')
pxh = abs(REF_T.a*REF_T.e)/1e4
def resample(p, bd=1):
    with rasterio.open(p) as s:
        d = np.full((H, Wd), np.nan, 'float32')
        reproject(rasterio.band(s, bd), d, src_transform=s.transform, src_crs=s.crs, dst_transform=REF_T, dst_crs=REF_CRS, resampling=Resampling.bilinear)
    return d
twi = resample(os.path.join(OUT, 'hydro_twi.tif')); twi[twi < -50] = np.nan
flow = np.log10(np.clip(resample(os.path.join(OUT, 'hydro_flowacc.tif')), 1, None))
dem = resample(os.path.join(OUT, 'dem_fabdem.tif')); dem[dem < -50] = np.nan
gy, gx = np.gradient(np.nan_to_num(dem, nan=np.nanmedian(dem)), abs(REF_T.a), abs(REF_T.a)); slope = np.degrees(np.arctan(np.hypot(gx, gy)))
dren = gpd.read_file(os.path.join(D, 'DRENAJES_FINAL_SerroAlto.geojson')).to_crs(REF_CRS)
drm = rasterize([(g, 1) for g in dren.geometry], out_shape=(H, Wd), transform=REF_T, fill=0).astype(bool)
distdren = distance_transform_edt(~drm)*abs(REF_T.a)
def norm(a, m):
    v = a[m & np.isfinite(a)]
    if v.size < 5: return np.zeros_like(a, 'float32')
    lo, hi = np.percentile(v, 5), np.percentile(v, 95)
    return np.clip((a-lo)/(hi-lo), 0, 1).astype('float32') if hi-lo > 1e-9 else np.full_like(a, .5, 'float32')

# ---- helpers puntos ----
def center(poly):
    p = poly if poly.geom_type == 'Polygon' else max(poly.geoms, key=lambda g: g.area)
    try: return shops.polylabel(p, tolerance=2)
    except Exception: return p.representative_point()
def core_of(poly):
    for b in (20, 12, 6, 0):
        c = poly.buffer(-b)
        if (not c.is_empty) and c.area >= max(0.1*poly.area, 1200): return c
    return poly
def gridp(g, sp):
    mnx, mny, mxx, mxy = g.bounds; o = []; y = mny
    while y <= mxy:
        x = mnx
        while x <= mxx:
            if g.contains(Point(x, y)): o.append(Point(x, y))
            x += sp
        y += sp
    return o
def fps(g, n, seed):
    sp = max(math.sqrt(max(g.area, 1)/(n*6)), 4); cs = gridp(g, sp)
    while len(cs) < n*2 and sp > 2.5: sp *= .6; cs = gridp(g, sp)
    if not cs: cs = [g.representative_point()]
    sel = [seed]; pool = [p for p in cs if p.distance(seed) > .1]
    while len(sel) < n+1 and pool:
        d = [min(p.distance(s) for s in sel) for p in pool]; nx = pool[int(np.argmax(d))]; sel.append(nx); pool.remove(nx)
    return sel[1:n+1]
def dens(a): return 5 if a < 3 else 7 if a < 10 else 10 if a < 20 else 12

# ---- zonificar + puntos + APK ----
zone_feats = []; precs = []
for _, lr in div.iterrows():
    lote = lr['lote']; geom = lr.geometry
    m = rasterize([(geom, 1)], out_shape=(H, Wd), transform=REF_T, fill=0).astype(bool) & np.isfinite(ndvi)
    if m.sum() < 8: continue
    score = (W['ndvi']*norm(ndvi, m)+W['ndre']*norm(ndre, m)+W['estab']*(1-norm(ndstd, m))+W['twi']*norm(twi, m)
             + W['flujo_inv']*(1-norm(flow, m))+W['pend_inv']*(1-norm(slope, m))+W['elev']*norm(dem, m)+W['distdren']*norm(distdren, m))
    score = gaussian_filter(np.where(m, score, np.nanmean(score[m])), sigma=2.5)
    c1, c2 = np.percentile(score[m], [33.3, 66.7]); z = np.zeros((H, Wd), 'int16')
    z[m] = np.digitize(score[m], [c1, c2])+1; z[m] = median_filter(z, 5)[m]
    for zz in (1, 2, 3):
        polys = [shape(g) for g, v in shapes((z == zz).astype('uint8'), mask=(z == zz), transform=REF_T) if v == 1]
        if not polys: continue
        zg = unary_union(polys).buffer(20).buffer(-20).intersection(geom)
        if zg.is_empty or zg.area < 4000: continue
        clase = CLASE[zz]; zone_feats.append(dict(lote=lote, zona=zz, clase=clase, geometry=zg))
        core = core_of(zg); prin = center(core); pid = '%s-B%s-P%d' % (lote, B, zz)
        precs.append(dict(punto_id=pid, tipo='PRINCIPAL', lote=lote, bloque=B, zona=zz, clase=clase, principal=pid, geometry=prin))
        for ms, sp in enumerate(fps(core, dens(zg.area/1e4), prin), 1):
            precs.append(dict(punto_id='%s-%02d' % (pid, ms), tipo='SUBMUESTRA', lote=lote, bloque=B, zona=zz, clase=clase, principal=pid, geometry=sp))

zg_gdf = gpd.GeoDataFrame(zone_feats, crs=31981); zg_gdf['color'] = zg_gdf['clase'].map(COLOR)
zg_gdf.to_crs(4326).to_file(os.path.join(D, 'ZONAS_B%s_GLOBAL.geojson' % B), driver='GeoJSON')
pg = gpd.GeoDataFrame(precs, crs=31981).to_crs(4326); pg['lon'] = pg.geometry.x.round(6); pg['lat'] = pg.geometry.y.round(6)
pg.to_file(os.path.join(D, 'PUNTOS_B%s.geojson' % B), driver='GeoJSON')
pg.drop(columns='geometry').to_csv(os.path.join(OUT, 'B%s_puntos.csv' % B), index=False, encoding='utf-8-sig')

# limpiar APK viejos del bloque + generar nuevos
valid = set('Bloque-%s-%s' % (B, l) for l in div['lote'])
for f in glob.glob(os.path.join(APKD, 'Bloque-%s-*_muestreo.geojson' % B)):
    if os.path.basename(f).replace('_muestreo.geojson', '') not in valid: os.remove(f)
zg4 = zg_gdf.to_crs(4326)
for lote in div['lote']:
    feats = []
    for _, zr in zg4[zg4.lote == lote].iterrows():
        feats.append({'type': 'Feature', 'properties': {'name': 'Zona %d' % int(zr['zona']), 'zona': int(zr['zona']), 'clase': zr['clase'],
                      'color': COLOR[zr['clase']], 'area_ha': round(zr.geometry.area, 1), 'type': 'zona'}, 'geometry': mapping(zr.geometry)})
    for _, pr in pg[pg.lote == lote].iterrows():
        feats.append({'type': 'Feature', 'properties': {'id': pr['punto_id'], 'name': pr['punto_id'], 'tipo': pr['tipo'].lower(), 'zona': int(pr['zona']),
                      'clase': pr['clase'], 'principal': pr['principal'], 'status': 'pendiente', 'marker-color': COLOR[pr['clase']], 'type': 'point'}, 'geometry': mapping(pr.geometry)})
    with open(os.path.join(APKD, 'Bloque-%s-%s_muestreo.geojson' % (B, lote)), 'w', encoding='utf-8') as f:
        json.dump({'type': 'FeatureCollection', 'name': 'B%s-%s' % (B, lote), 'features': feats}, f, ensure_ascii=False)

# PNGs
rs = rasterio.open(os.path.join(OUT, 's2_rgb_lotes.tif')); divv = div.to_crs(4326)
for _, lr in divv.iterrows():
    lote = lr['lote']; geom = lr.geometry; b = geom.bounds; mx = (b[2]-b[0])*0.08+6e-4; my = (b[3]-b[1])*0.08+6e-4
    win = rasterio.windows.from_bounds(b[0]-mx, b[1]-my, b[2]+mx, b[3]+my, rs.transform)
    img = rs.read(window=win); ext = rasterio.windows.bounds(win, rs.transform)
    fig, ax = plt.subplots(figsize=(8, 6.5)); ax.imshow(np.transpose(img, (1, 2, 0)), extent=[ext[0], ext[2], ext[1], ext[3]])
    for cl in ['Baja', 'Media', 'Alta']:
        s = zg4[(zg4.lote == lote) & (zg4.clase == cl)]
        if len(s): s.plot(ax=ax, color=COLOR[cl], alpha=0.45, edgecolor='white', linewidth=0.4)
    gpd.GeoSeries([geom]).boundary.plot(ax=ax, color='cyan', linewidth=1.3)
    pl = pg[pg.lote == lote]; sub = pl[pl.tipo == 'SUBMUESTRA']; pri = pl[pl.tipo == 'PRINCIPAL']
    ax.scatter(sub.geometry.x, sub.geometry.y, s=10, c='black', alpha=0.6, zorder=4)
    ax.scatter(pri.geometry.x, pri.geometry.y, s=110, c=[COLOR[c] for c in pri.clase], edgecolor='white', linewidth=1.3, zorder=5)
    for _, r in pri.iterrows():
        ax.annotate('P%d' % r['zona'], (r.geometry.x, r.geometry.y), fontsize=7, color='white', weight='bold', ha='center', va='center', zorder=6)
    ar = div[div.lote == lote]['area_ha'].iloc[0]
    ax.set_title('Bloque %s — %s (%.1f ha)\nP1=Baja  P2=Media  P3=Alta  ·  %d principales + %d submuestras' % (B, lote, ar, len(pri), len(sub)), fontsize=10)
    ax.set_xlim(ext[0], ext[2]); ax.set_ylim(ext[1], ext[3]); ax.set_axis_off(); plt.tight_layout()
    plt.savefig(os.path.join(PNGD, '%s.png' % lote), dpi=110, bbox_inches='tight'); plt.close()

print('Bloque %s: %d zonas | %d principales + %d submuestras | %d APK | %d PNG'
      % (B, len(zg_gdf), (pg.tipo == 'PRINCIPAL').sum(), (pg.tipo == 'SUBMUESTRA').sum(), len(valid), len(divv)))
print('DONE')
