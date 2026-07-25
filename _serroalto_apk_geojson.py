# -*- coding: utf-8 -*-
"""G: GeoJSON coloridos POR LOTE en formato nativo PIX Muestreo APK
(boundary + zonas + puntos principal/submuestra) + PNG de campo por lote."""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, pandas as pd, numpy as np, rasterio
from shapely.geometry import mapping
from shapely.ops import unary_union
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import warnings; warnings.filterwarnings('ignore')

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUTDIR = os.path.join(DIRBASE, '_analisis_canadas')
APKDIR = os.path.join(DIRBASE, 'APK_muestreo_por_lote'); os.makedirs(APKDIR, exist_ok=True)
PNGDIR = os.path.join(OUTDIR, 'muestreo_png'); os.makedirs(PNGDIR, exist_ok=True)
COLOR = {'Baja': '#F44336', 'Media': '#FFEB3B', 'Alta': '#4CAF50'}   # = APK _getZonaColor

zon = gpd.read_file(os.path.join(DIRBASE, 'ZONAS_MANEJO_GLOBAL_SerroAlto.geojson')).to_crs(4326)
pts = gpd.read_file(os.path.join(DIRBASE, 'PUNTOS_MUESTREO_GLOBAL_SerroAlto.geojson')).to_crs(4326)
lot = gpd.read_file(os.path.join(DIRBASE, 'Lotes_SerroAlto_LIMPIOS.geojson')).to_crs(4326)
util = gpd.read_file(os.path.join(DIRBASE, 'AREA_UTIL_GLOBAL_SerroAlto.geojson')).to_crs(4326)
tab = pd.read_csv(os.path.join(DIRBASE, 'AREA_UTIL_por_lote.csv')).set_index('lote_id')
rsrc = rasterio.open(os.path.join(OUTDIR, 's2_rgb_lotes.tif'))

allfeats = []
for lid in sorted(lot['lote_id'].unique()):
    lg = unary_union(lot[lot.lote_id == lid].geometry.values)
    zl = zon[zon.lote_id == lid].sort_values('zona')
    pl = pts[pts.lote_id == lid]
    bloque = tab.loc[lid, 'bloque'] if lid in tab.index else ''
    gross = float(tab.loc[lid, 'gross_ha']) if lid in tab.index else round(lg.area, 2)
    feats = []
    # boundary
    feats.append({'type': 'Feature', 'properties': {'name': lid, 'type': 'boundary', 'area_ha': round(gross, 2)},
                  'geometry': mapping(lg)})
    # zonas
    for _, z in zl.iterrows():
        cl = z['clase']
        feats.append({'type': 'Feature', 'properties': {
            'name': 'Zona %d' % int(z['zona']), 'clase': cl, 'color': COLOR.get(cl, '#00BFA5'),
            'area_ha': round(float(z['area_ha']), 2), 'type': 'zona'}, 'geometry': mapping(z.geometry)})
    # puntos
    for _, p in pl.iterrows():
        short = 'Z' + p['punto_id'].split('-Z', 1)[1]
        feats.append({'type': 'Feature', 'properties': {
            'id': p['punto_id'], 'name': short, 'tipo': p['tipo'].lower(),
            'zona': 'Zona %d' % int(p['zona']), 'clase': p['clase'], 'status': 'pendiente', 'type': 'point'},
            'geometry': mapping(p.geometry)})
    fc = {'type': 'FeatureCollection', 'name': '%s_muestreo' % lid, 'features': feats}
    with open(os.path.join(APKDIR, '%s_muestreo.geojson' % lid), 'w', encoding='utf-8') as f:
        json.dump(fc, f, ensure_ascii=False)
    allfeats += feats

    # --- PNG campo ---
    b = lg.bounds; mx = (b[2]-b[0])*0.06+0.0008; my = (b[3]-b[1])*0.06+0.0008
    win = rasterio.windows.from_bounds(b[0]-mx, b[1]-my, b[2]+mx, b[3]+my, rsrc.transform)
    img = rsrc.read(window=win); ext = rasterio.windows.bounds(win, rsrc.transform)
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.imshow(np.transpose(img, (1, 2, 0)), extent=[ext[0], ext[2], ext[1], ext[3]])
    for _, z in zl.iterrows():
        gpd.GeoSeries([z.geometry]).plot(ax=ax, color=COLOR.get(z['clase'], '#888'), alpha=0.4, edgecolor='white', linewidth=0.6)
    gpd.GeoSeries([lg]).boundary.plot(ax=ax, color='cyan', linewidth=1.5)
    pp = pl[pl.tipo == 'PRINCIPAL']; ss = pl[pl.tipo == 'SUBMUESTRA']
    ax.scatter(ss.geometry.x, ss.geometry.y, s=10, c='#FFA726', edgecolor='k', linewidth=0.2, label='Submuestra (%d)' % len(ss), zorder=4)
    ax.scatter(pp.geometry.x, pp.geometry.y, s=70, c='#E53935', edgecolor='white', linewidth=1.0, marker='o', label='Principal (%d)' % len(pp), zorder=5)
    for _, p in pp.iterrows():
        ax.annotate('Z' + p['punto_id'].split('-Z', 1)[1], (p.geometry.x, p.geometry.y), fontsize=6, color='white', weight='bold', ha='center', va='bottom', xytext=(0, 4), textcoords='offset points')
    nz = len(zl)
    ax.set_title('%s (Bloque %s) — Muestreo de suelo\nÚtil %.1f ha · %d zonas · %d principales + %d submuestras' %
                 (lid, bloque, float(tab.loc[lid, 'util_ha']) if lid in tab.index else 0, nz, len(pp), len(ss)), fontsize=10)
    ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
    ax.set_xlim(ext[0], ext[2]); ax.set_ylim(ext[1], ext[3]); ax.set_axis_off()
    plt.tight_layout(); plt.savefig(os.path.join(PNGDIR, '%s_muestreo.png' % lid), dpi=115, bbox_inches='tight'); plt.close()

# global combinado
with open(os.path.join(DIRBASE, 'MUESTREO_APK_GLOBAL_SerroAlto.geojson'), 'w', encoding='utf-8') as f:
    json.dump({'type': 'FeatureCollection', 'name': 'SerroAlto_muestreo', 'features': allfeats}, f, ensure_ascii=False)

print('GeoJSON APK por lote:', len(list(os.listdir(APKDIR))), '->', APKDIR)
print('PNG campo por lote:', len(os.listdir(PNGDIR)))
print('Global -> MUESTREO_APK_GLOBAL_SerroAlto.geojson (%d features)' % len(allfeats))
print('Formato: boundary + zonas(clase/color) + points(tipo/zona/clase/status) = nativo PIX Muestreo')
print('DONE')
