# -*- coding: utf-8 -*-
"""BLOQUE 14 v2.1 — ENTREGA: copia GeoJSON APK a carpeta de entrega + PNG por lote p/ informe."""
import os, sys, shutil, glob
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, pandas as pd, numpy as np, rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import matplotlib.patches as mp
import warnings; warnings.filterwarnings('ignore')

BASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
CAN = os.path.join(BASE, '_analisis_canadas'); OUT = os.path.join(CAN, 'AMBIENTES_V2')
DELIV = os.path.join(BASE, 'APK_muestreo_B14_v2'); os.makedirs(DELIV, exist_ok=True)
PNGD = os.path.join(OUT, 'informe_png_lote'); os.makedirs(PNGD, exist_ok=True)
COLOR = {'Bajura negra': '#3E2723', 'Transicion': '#FFB300', 'Altura roja': '#D84315'}

# 1) copiar los 31 geojson APK a la carpeta de entrega
src = glob.glob(os.path.join(OUT, 'APK_muestreo_por_lote', 'Bloque-14-*_muestreo.geojson'))
for f in src: shutil.copy2(f, os.path.join(DELIV, os.path.basename(f)))
# geojson combinado del bloque (todos los puntos + zonas) para carga unica opcional
shutil.copy2(os.path.join(OUT, 'PUNTOS_B14_V2.geojson'), os.path.join(DELIV, 'PUNTOS_B14_TODOS.geojson'))
shutil.copy2(os.path.join(OUT, 'ZONAS_B14_V2.geojson'), os.path.join(DELIV, 'ZONAS_B14_TODAS.geojson'))
print('APK geojson entregados en APK_muestreo_B14_v2:', len(src), '+ 2 combinados')

# 2) PNG por lote para el informe (ambientes + puntos sobre RGB)
lotes = gpd.read_file(os.path.join(CAN, 'Lotes_B14_divisiones.geojson')).to_crs(3857)
z2 = gpd.read_file(os.path.join(OUT, 'ZONAS_B14_V2.geojson')).to_crs(3857)
pts = gpd.read_file(os.path.join(OUT, 'PUNTOS_B14_V2.geojson')).to_crs(3857)
rgb_src = rasterio.open(os.path.join(CAN, 's2_rgb_lotes.tif'))
dt, w, h = calculate_default_transform(rgb_src.crs, 'EPSG:3857', rgb_src.width, rgb_src.height, *rgb_src.bounds)
rgb = np.zeros((3, h, w), 'uint8')
for i in range(3):
    reproject(rgb_src.read(i+1), rgb[i], src_transform=rgb_src.transform, src_crs=rgb_src.crs,
              dst_transform=dt, dst_crs='EPSG:3857', resampling=Resampling.bilinear)
rgb = np.transpose(rgb, (1, 2, 0)); ext = [dt.c, dt.c+dt.a*w, dt.f+dt.e*h, dt.f]

for lote in sorted(lotes['lote'].unique()):
    lg = lotes[lotes.lote == lote]; b = lg.total_bounds; pad = 60
    fig, ax = plt.subplots(figsize=(9, 6.2))
    ax.imshow(rgb, extent=ext, origin='upper')
    for cl, col in COLOR.items():
        s = z2[(z2.lote == lote) & (z2.ambiente == cl)]
        if len(s): s.plot(ax=ax, color=col, alpha=0.55, edgecolor='white', linewidth=0.4)
    lg.boundary.plot(ax=ax, color='yellow', linewidth=1.2)
    pl = pts[pts.lote == lote]
    pl[pl.tipo == 'SUBMUESTRA'].plot(ax=ax, color='white', markersize=13, marker='o', alpha=0.85, edgecolor='gray', linewidth=0.4)
    pl[pl.tipo == 'PRINCIPAL'].plot(ax=ax, color='black', markersize=130, marker='*', edgecolor='white', linewidth=0.9)
    ax.set_xlim(b[0]-pad, b[2]+pad); ax.set_ylim(b[1]-pad, b[3]+pad); ax.set_axis_off()
    plt.tight_layout(pad=0.2); plt.savefig(os.path.join(PNGD, '%s.png' % lote), dpi=115, bbox_inches='tight'); plt.close()
print('PNG por lote:', len(os.listdir(PNGD)))
print('DONE deliver')
