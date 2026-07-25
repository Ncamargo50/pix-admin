# -*- coding: utf-8 -*-
"""Bloques 2 y 3: capa de lotes por DIVISION, numeración Sur->Norte (L01 al Sur),
divisiones por letra A/B/C Oeste->Este. Mapas para confirmar."""
import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, numpy as np, rasterio
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import matplotlib.cm as cm
import warnings; warnings.filterwarnings('ignore')

D = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
lot = gpd.read_file(os.path.join(D, 'Lotes_SerroAlto_LIMPIOS.geojson')).to_crs(31981)

def parts_we(geom):
    ps = [geom] if geom.geom_type == 'Polygon' else list(geom.geoms)
    return sorted(ps, key=lambda p: p.centroid.x)

for B in ['2', '3']:
    b = lot[lot.bloque.astype(str) == B].copy()
    b['cy'] = b.geometry.centroid.y
    b = b.sort_values('cy').reset_index(drop=True)   # Sur(min y)->Norte = L01 al Sur
    recs = []
    for i, (_, r) in enumerate(b.iterrows(), 1):
        ps = parts_we(r.geometry)
        for j, p in enumerate(ps):
            letter = chr(65+j) if len(ps) > 1 else ''
            recs.append(dict(lote='L%02d%s' % (i, letter), lote_id='Bloque-%s-L%02d%s' % (B, i, letter),
                             bloque=B, area_ha=round(p.area/1e4, 2), geometry=p))
    gd = gpd.GeoDataFrame(recs, crs=31981)
    gd.to_crs(4326).to_file(os.path.join(D, 'Lotes_B%s_divisiones.geojson' % B), driver='GeoJSON')
    small = gd[gd.area_ha < 5]['lote'].tolist()
    print('Bloque %s: %d lotes base -> %d divisiones | área %.1f ha | chicas(<5ha): %s'
          % (B, len(b), len(gd), gd['area_ha'].sum(), small or 'ninguna'))
    print('  Lotes:', ', '.join(gd['lote'].tolist()))
    # mapa
    gd4 = gd.to_crs(4326); bb = gd4.total_bounds
    fig, ax = plt.subplots(figsize=(12, 11))
    with rasterio.open(os.path.join(D, '_analisis_canadas', 's2_rgb_lotes.tif')) as r:
        win = rasterio.windows.from_bounds(bb[0]-0.002, bb[1]-0.002, bb[2]+0.002, bb[3]+0.002, r.transform)
        img = r.read(window=win); ext = rasterio.windows.bounds(win, r.transform)
    ax.imshow(np.transpose(img, (1, 2, 0)), extent=[ext[0], ext[2], ext[1], ext[3]])
    cmap = cm.get_cmap('tab20')
    for i, (_, rr) in enumerate(gd4.iterrows()):
        gpd.GeoSeries([rr.geometry]).plot(ax=ax, facecolor=cmap(i % 20), alpha=0.45, edgecolor='yellow', linewidth=1.0)
        c = rr.geometry.centroid; ax.annotate(rr['lote'], (c.x, c.y), fontsize=7, weight='bold', color='white', ha='center', va='center')
    ax.set_title('BLOQUE %s — nomenclatura propuesta (Sur→Norte, L01 al Sur; divisiones A/B/C Oeste→Este) — %d divisiones' % (B, len(gd)), fontsize=11)
    ax.set_xlim(ext[0], ext[2]); ax.set_ylim(ext[1], ext[3]); ax.set_axis_off(); plt.tight_layout()
    plt.savefig(os.path.join(D, '_analisis_canadas', 'PROPUESTA_nomenclatura_B%s.png' % B), dpi=140, bbox_inches='tight'); plt.close()
print('DONE')
