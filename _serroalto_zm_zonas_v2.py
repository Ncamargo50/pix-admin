# -*- coding: utf-8 -*-
"""E2 v2 — ZONAS DE MANEJO segun skill gis-precision-agro (Score Compuesto
Ponderado 8 variables, pesos fijos). 3 ambientes por lote sobre area util."""
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, pandas as pd, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize, shapes
from scipy.ndimage import median_filter, gaussian_filter, distance_transform_edt
from shapely.geometry import shape
from shapely.ops import unary_union
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import matplotlib.patches as mp
import warnings; warnings.filterwarnings('ignore')

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUTDIR = os.path.join(DIRBASE, '_analisis_canadas')
ZMDIR = os.path.join(DIRBASE, 'Zonas_manejo_por_lote'); os.makedirs(ZMDIR, exist_ok=True)
# === PESOS EXACTOS DEL SKILL (suma=1.0) ===
W = dict(ndvi=0.25, ndre=0.15, estab=0.15, twi=0.10, flujo_inv=0.10, pend_inv=0.10, elev=0.05, distdren=0.10)
assert abs(sum(W.values()) - 1.0) < 1e-6, 'PESOS NO SUMAN 1.0'
PAL = {1: '#CC0000', 2: '#FFD700', 3: '#228B22'}; CLASE = {1: 'Baja', 2: 'Media', 3: 'Alta'}

# grid referencia (features veg 10m)
fsrc = rasterio.open(os.path.join(OUTDIR, 'zm_features_veg.tif'))
REF_T, REF_CRS, H, W_ = fsrc.transform, fsrc.crs, fsrc.height, fsrc.width
ndvi = fsrc.read(1).astype('float32'); ndstd = fsrc.read(2).astype('float32'); ndre = fsrc.read(3).astype('float32')
px = abs(REF_T.a); px_ha = (px*px)/1e4

def resample(path, b=1):
    with rasterio.open(path) as s:
        dst = np.full((H, W_), np.nan, 'float32')
        reproject(rasterio.band(s, b), dst, src_transform=s.transform, src_crs=s.crs,
                  dst_transform=REF_T, dst_crs=REF_CRS, resampling=Resampling.bilinear)
    return dst
twi = resample(os.path.join(OUTDIR, 'hydro_twi.tif')); twi[twi < -50] = np.nan
flow = resample(os.path.join(OUTDIR, 'hydro_flowacc.tif')); flow[flow < -50] = np.nan
flow = np.log10(np.clip(flow, 1, None))          # log para acumulacion
dem = resample(os.path.join(OUTDIR, 'dem_fabdem.tif')); dem[dem < -50] = np.nan
gy, gx = np.gradient(np.nan_to_num(dem, nan=np.nanmedian(dem)), px, px)
slope = np.degrees(np.arctan(np.hypot(gx, gy)))  # pendiente grados
# distancia a drenaje FINAL (tuyo ∪ satelital)
dren = gpd.read_file(os.path.join(DIRBASE, 'DRENAJES_FINAL_SerroAlto.geojson')).to_crs(REF_CRS)
drmask = rasterize([(g, 1) for g in dren.geometry], out_shape=(H, W_), transform=REF_T, fill=0).astype(bool)
distdren = distance_transform_edt(~drmask) * px   # metros a la linea de drenaje

lot = gpd.read_file(os.path.join(DIRBASE, 'Lotes_SerroAlto_LIMPIOS.geojson')).to_crs(31981)
util = gpd.read_file(os.path.join(DIRBASE, 'AREA_UTIL_GLOBAL_SerroAlto.geojson')).to_crs(31981)
util_by = {r['lote_id']: r.geometry for _, r in util.iterrows()}
gross_by = {r['lote_id']: r.geometry.area/1e4 for _, r in lot.groupby('lote_id').geometry.apply(lambda s: unary_union(s.values)).reset_index().rename(columns={'geometry':'g'}).assign(geometry=lambda d:d['g']).iterrows()} if False else {lid: unary_union(s.geometry.values).area/1e4 for lid, s in lot.groupby('lote_id')}

def norm(a, m):  # 0-1 dentro de mascara, clip percentil 5-95
    v = a[m & np.isfinite(a)]
    if v.size < 5: return np.zeros_like(a, 'float32')
    lo, hi = np.percentile(v, 5), np.percentile(v, 95)
    if hi-lo < 1e-9: return np.full_like(a, 0.5, 'float32')
    return np.clip((a-lo)/(hi-lo), 0, 1).astype('float32')

records = []
for lid, sub in lot.groupby('lote_id'):
    ug = util_by.get(lid)
    if ug is None or ug.is_empty: continue
    m = rasterize([(ug, 1)], out_shape=(H, W_), transform=REF_T, fill=0).astype(bool) & np.isfinite(ndvi)
    if m.sum() < 8: continue
    # SCORE COMPUESTO PONDERADO (skill)
    score = (W['ndvi']*norm(ndvi, m) + W['ndre']*norm(ndre, m) + W['estab']*(1-norm(ndstd, m)) +
             W['twi']*norm(twi, m) + W['flujo_inv']*(1-norm(flow, m)) + W['pend_inv']*(1-norm(slope, m)) +
             W['elev']*norm(dem, m) + W['distdren']*norm(distdren, m))
    filled = np.where(m, score, np.nanmean(score[m]))
    score = gaussian_filter(filled, sigma=2.5)     # coherencia espacial (zonas estables)
    c1, c2 = np.percentile(score[m], [33.3, 66.7])
    z = np.zeros((H, W_), 'int16'); z[m] = np.digitize(score[m], [c1, c2]) + 1
    z[m] = median_filter(z, size=5)[m]
    gha = gross_by.get(lid, ug.area/1e4)
    # estadisticas por zona
    for zz in (1, 2, 3):
        mm = m & (z == zz)
        if mm.sum() == 0: continue
        records.append(dict(lote_id=lid, bloque=sub['bloque'].iloc[0], zona=zz, clase=CLASE[zz],
                            area_ha=round(mm.sum()*px_ha, 2), porcentaje=round(mm.sum()*px_ha/gha*100, 1),
                            ndvi_prom=round(np.nanmean(ndvi[mm]), 3), ndre_prom=round(np.nanmean(ndre[mm]), 3),
                            twi_prom=round(np.nanmean(twi[mm]), 2), elevacion_prom=round(np.nanmean(dem[mm]), 1),
                            pendiente_prom=round(np.nanmean(slope[mm]), 2), score_prom=round(np.nanmean(score[mm]), 3)))
    # vectorizar + limpiar (skill 8.2: buffer(20).buffer(-20) + area)
    polys = [(zz, shape(g)) for zz in (1, 2, 3) for g, v in shapes((z == zz).astype('uint8'), mask=(z == zz), transform=REF_T) if v == 1]
    if not polys: continue
    gz = gpd.GeoDataFrame([{'lote_id': lid, 'bloque': sub['bloque'].iloc[0], 'zona': zz, 'clase': CLASE[zz]} for zz, _ in polys],
                          geometry=[g for _, g in polys], crs=31981)
    gz = gz.dissolve(['lote_id', 'bloque', 'zona', 'clase']).reset_index()
    gz['geometry'] = gz.geometry.buffer(20).buffer(-20).intersection(ug)
    gz = gz[~gz.geometry.is_empty & (gz.geometry.area >= 5000)]
    if not gz.is_valid.all(): gz['geometry'] = gz.geometry.buffer(0)
    if len(gz):
        st = {(r['zona']): r for r in records if r['lote_id'] == lid}
        gz['area_ha'] = (gz.geometry.area/1e4).round(2)
        gz['porcentaje'] = (gz['area_ha']/gha*100).round(1)
        for col in ['ndvi_prom', 'ndre_prom', 'twi_prom', 'elevacion_prom', 'pendiente_prom', 'score_prom']:
            gz[col] = gz['zona'].map(lambda z_: st[z_][col] if z_ in st else None)
        gz.to_crs(4326).to_file(os.path.join(ZMDIR, '%s_zonas.geojson' % lid), driver='GeoJSON')

df = pd.DataFrame(records)
df.sort_values(['bloque', 'lote_id', 'zona']).to_csv(os.path.join(DIRBASE, 'Zonas_manejo_estadisticas.csv'), index=False, encoding='utf-8-sig')
import glob
allz = gpd.GeoDataFrame(pd.concat([gpd.read_file(f) for f in glob.glob(os.path.join(ZMDIR, '*_zonas.geojson'))], ignore_index=True), crs=4326)
assert allz.is_valid.all(), 'GEOMETRIAS INVALIDAS'
allz.to_file(os.path.join(DIRBASE, 'ZONAS_MANEJO_GLOBAL_SerroAlto.geojson'), driver='GeoJSON')
print('Zonas: %d lotes | %d poligonos | geometrias validas: %s' % (df['lote_id'].nunique(), len(allz), allz.is_valid.all()))
print('Pesos suman:', round(sum(W.values()), 3), '| variables:', list(W.keys()))
for c in ['Baja', 'Media', 'Alta']:
    print('  %-6s %.1f ha' % (c, df[df.clase == c]['area_ha'].sum()))

ag = allz.to_crs(31981)
fig, ax = plt.subplots(figsize=(11, 11))
for zz in (1, 2, 3):
    s = ag[ag.zona == zz]
    if len(s): s.plot(ax=ax, color=PAL[zz], edgecolor='white', linewidth=0.2)
lot.boundary.plot(ax=ax, color='black', linewidth=0.6)
ax.legend(handles=[mp.Patch(color=PAL[1], label='Baja'), mp.Patch(color=PAL[2], label='Media'), mp.Patch(color=PAL[3], label='Alta')], loc='upper right', fontsize=11)
ax.set_title('Cerro Alto — Zonas de manejo (3 ambientes)\nScore compuesto ponderado 8 var (NDVI/NDRE/estabilidad/TWI/flujo/pendiente/elev/dist-drenaje)', fontsize=10)
ax.set_axis_off(); plt.tight_layout()
plt.savefig(os.path.join(DIRBASE, 'MAPA_Zonas_Manejo_SerroAlto.png'), dpi=150, bbox_inches='tight')
print('mapa -> MAPA_Zonas_Manejo_SerroAlto.png'); print('DONE')
