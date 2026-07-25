# -*- coding: utf-8 -*-
"""E2: Zonas de manejo (3 ambientes Baja/Media/Alta) por lote sobre area util.
Score compuesto = NDVI med + estabilidad + NDRE + TWI + elev rel. Vectoriza."""
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, pandas as pd, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize, shapes
from scipy.ndimage import median_filter, gaussian_filter
from shapely.geometry import shape
from shapely.ops import unary_union
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import matplotlib.patches as mp
import warnings; warnings.filterwarnings('ignore')

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUTDIR = os.path.join(DIRBASE, '_analisis_canadas')
ZMDIR = os.path.join(DIRBASE, 'Zonas_manejo_por_lote'); os.makedirs(ZMDIR, exist_ok=True)
WEIGHTS = dict(ndvi=0.45, estab=0.20, ndre=0.15, twi=0.10, elev=0.10)
PAL = {1: '#CC0000', 2: '#FFD700', 3: '#228B22'}; CLASE = {1: 'Baja', 2: 'Media', 3: 'Alta'}

# referencia: grid de features veg (10m, 31981)
fsrc = rasterio.open(os.path.join(OUTDIR, 'zm_features_veg.tif'))
REF_T, REF_CRS, H, W = fsrc.transform, fsrc.crs, fsrc.height, fsrc.width
bands = {d: i+1 for i, d in enumerate(fsrc.descriptions) if d} or {'ndvi_med': 1, 'ndvi_std': 2, 'ndre_med': 3}
ndvi = fsrc.read(1).astype('float32'); ndstd = fsrc.read(2).astype('float32'); ndre = fsrc.read(3).astype('float32')

def resample_to_ref(path, band=1):
    with rasterio.open(path) as s:
        dst = np.full((H, W), np.nan, 'float32')
        reproject(rasterio.band(s, band), dst, src_transform=s.transform, src_crs=s.crs,
                  dst_transform=REF_T, dst_crs=REF_CRS, resampling=Resampling.bilinear)
    return dst
twi = resample_to_ref(os.path.join(OUTDIR, 'hydro_twi.tif'))
dem = resample_to_ref(os.path.join(OUTDIR, 'dem_fabdem.tif'))
twi[twi < -50] = np.nan; dem[dem < -50] = np.nan

lot = gpd.read_file(os.path.join(DIRBASE, 'Lotes_SerroAlto_LIMPIOS.geojson')).to_crs(31981)
util = gpd.read_file(os.path.join(DIRBASE, 'AREA_UTIL_GLOBAL_SerroAlto.geojson')).to_crs(31981)

def norm(a, m):  # normaliza 0-1 dentro de la mascara (clip 5-95)
    v = a[m & np.isfinite(a)]
    if v.size < 5: return np.zeros_like(a)
    lo, hi = np.percentile(v, 5), np.percentile(v, 95)
    if hi - lo < 1e-9: return np.zeros_like(a)
    return np.clip((a - lo) / (hi - lo), 0, 1)

zone_glob = np.zeros((H, W), 'int16'); lid_arr = np.empty((H, W), object)
records = []
util_by = {r['lote_id']: r.geometry for _, r in util.iterrows()}
px_area = abs(REF_T.a * REF_T.e) / 1e4  # ha por pixel

for lid, sub in lot.groupby('lote_id'):
    ug = util_by.get(lid)
    if ug is None or ug.is_empty: continue
    m = rasterize([(ug, 1)], out_shape=(H, W), transform=REF_T, fill=0).astype(bool)
    m &= np.isfinite(ndvi)
    if m.sum() < 8: continue
    estab = 1 - norm(ndstd, m)          # baja variabilidad = estable
    score = (WEIGHTS['ndvi']*norm(ndvi, m) + WEIGHTS['estab']*estab +
             WEIGHTS['ndre']*norm(ndre, m) + WEIGHTS['twi']*norm(twi, m) +
             WEIGHTS['elev']*norm(dem, m))
    filled = np.where(m, score, np.nanmean(score[m]))
    score = gaussian_filter(filled, sigma=4)      # zonas SUAVES y estables (~40 m)
    sv = score[m]
    c1, c2 = np.percentile(sv, [33.3, 66.7])
    z = np.zeros((H, W), 'int16')
    z[m] = np.digitize(score[m], [c1, c2]) + 1   # 1..3
    z[m] = median_filter(z, size=7)[m]            # mayoria fuerte (despeckle)
    zone_glob[m] = z[m]; lid_arr[m] = lid
    for zz in (1, 2, 3):
        mm = m & (zone_glob == zz)  # nota: usar z local
    # estadisticas por zona (con z local)
    for zz in (1, 2, 3):
        mm = m & (z == zz)
        if mm.sum() == 0: continue
        records.append(dict(lote_id=lid, bloque=sub['bloque'].iloc[0], zona=zz, clase=CLASE[zz],
                            area_ha=round(mm.sum()*px_area, 2), ndvi_prom=round(np.nanmean(ndvi[mm]), 3),
                            ndre_prom=round(np.nanmean(ndre[mm]), 3), twi_prom=round(np.nanmean(twi[mm]), 2),
                            elev_prom=round(np.nanmean(dem[mm]), 1), score_prom=round(np.nanmean(score[mm]), 3)))
    # vectorizar este lote
    polys = []
    for zz in (1, 2, 3):
        mask_z = (z == zz).astype('uint8')
        for g, v in shapes(mask_z, mask=mask_z > 0, transform=REF_T):
            if v == 1: polys.append((zz, shape(g)))
    if polys:
        gz = gpd.GeoDataFrame([{'lote_id': lid, 'bloque': sub['bloque'].iloc[0], 'zona': z_, 'clase': CLASE[z_]} for z_, _ in polys],
                              geometry=[g for _, g in polys], crs=31981)
        gz = gz.dissolve(['lote_id', 'bloque', 'zona', 'clase']).reset_index()
        gz['geometry'] = gz.geometry.buffer(20).buffer(-20)   # suaviza bordes
        gz['geometry'] = gz.geometry.intersection(ug)          # recorta al area util
        gz = gz[~gz.geometry.is_empty & (gz.area >= 5000)]     # quita <0.5 ha
        gz['area_ha'] = (gz.area/1e4).round(2)
        if len(gz):
            gz.to_crs(4326).to_file(os.path.join(ZMDIR, '%s_zonas.geojson' % lid), driver='GeoJSON')

# tabla + global
df = pd.DataFrame(records)
dfz = df.groupby(['lote_id', 'bloque', 'zona', 'clase'], as_index=False).agg(
    area_ha=('area_ha', 'sum'), ndvi_prom=('ndvi_prom', 'mean'), score_prom=('score_prom', 'mean'))
dfz.sort_values(['bloque', 'lote_id', 'zona']).to_csv(os.path.join(DIRBASE, 'Zonas_manejo_estadisticas.csv'), index=False, encoding='utf-8-sig')

# unir todos los geojson por lote en uno global
import glob
allz = pd.concat([gpd.read_file(f) for f in glob.glob(os.path.join(ZMDIR, '*_zonas.geojson'))], ignore_index=True)
allz = gpd.GeoDataFrame(allz, crs=4326)
allz.to_file(os.path.join(DIRBASE, 'ZONAS_MANEJO_GLOBAL_SerroAlto.geojson'), driver='GeoJSON')

print('Zonas generadas: %d lotes | %d poligonos' % (df['lote_id'].nunique(), len(allz)))
print('Por clase (ha):')
for c in ['Baja', 'Media', 'Alta']:
    print('  %-6s %.1f ha' % (c, dfz[dfz.clase == c]['area_ha'].sum()))

# mapa overview
ag = allz.to_crs(31981)
fig, ax = plt.subplots(figsize=(11, 11))
for zz in (1, 2, 3):
    s = ag[ag.zona == zz]
    if len(s): s.plot(ax=ax, color=PAL[zz], edgecolor='none')
lot.boundary.plot(ax=ax, color='black', linewidth=0.5)
ax.legend(handles=[mp.Patch(color=PAL[1], label='Baja'), mp.Patch(color=PAL[2], label='Media'), mp.Patch(color=PAL[3], label='Alta')], loc='upper right', fontsize=11)
ax.set_title('Cerro Alto — Zonas de manejo (3 ambientes) sobre area util\n3 años S2 sin nubes + estabilidad + terreno', fontsize=12)
ax.set_axis_off(); plt.tight_layout()
plt.savefig(os.path.join(DIRBASE, 'MAPA_Zonas_Manejo_SerroAlto.png'), dpi=145, bbox_inches='tight')
print('mapa -> MAPA_Zonas_Manejo_SerroAlto.png')
print('DONE')
