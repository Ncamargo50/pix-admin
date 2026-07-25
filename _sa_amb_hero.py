# -*- coding: utf-8 -*-
"""Hero landscape (portada propuesta) con ambientes v2.1 de los 3 bloques."""
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import matplotlib.patches as mp
import warnings; warnings.filterwarnings('ignore')

BASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
CAN = os.path.join(BASE, '_analisis_canadas'); OUT = os.path.join(CAN, 'AMBIENTES_V2')
COLOR = {'Bajura negra': '#3E2723', 'Transicion': '#FFB300', 'Altura roja': '#D84315'}
rgb_src = rasterio.open(os.path.join(CAN, 's2_rgb_lotes.tif'))
dt, w, h = calculate_default_transform(rgb_src.crs, 'EPSG:3857', rgb_src.width, rgb_src.height, *rgb_src.bounds)
rgb = np.zeros((3, h, w), 'uint8')
for i in range(3):
    reproject(rgb_src.read(i+1), rgb[i], src_transform=rgb_src.transform, src_crs=rgb_src.crs,
              dst_transform=dt, dst_crs='EPSG:3857', resampling=Resampling.bilinear)
rgb = np.transpose(rgb, (1, 2, 0)); ext = [dt.c, dt.c+dt.a*w, dt.f+dt.e*h, dt.f]
allz = gpd.read_file(os.path.join(OUT, 'ZONAS_SerroAlto_V2.geojson')).to_crs(3857)

fig, ax = plt.subplots(figsize=(13, 6.2)); ax.imshow(rgb, extent=ext, origin='upper')
for cl, col in COLOR.items():
    s = allz[allz.ambiente == cl]
    if len(s): s.plot(ax=ax, color=col, alpha=0.6, edgecolor='white', linewidth=0.2)
b = allz.total_bounds; padx = (b[2]-b[0])*0.04; pady = (b[3]-b[1])*0.04
ax.set_xlim(b[0]-padx, b[2]+padx); ax.set_ylim(b[1]-pady, b[3]+pady); ax.set_axis_off()
ha = lambda c: allz[allz.ambiente == c].to_crs(31981).area.sum()/1e4
ax.legend(handles=[mp.Patch(color=COLOR['Altura roja'], label='Altura roja — %.0f ha' % ha('Altura roja')),
                   mp.Patch(color=COLOR['Transicion'], label='Transicion — %.0f ha' % ha('Transicion')),
                   mp.Patch(color=COLOR['Bajura negra'], label='Bajura negra — %.0f ha' % ha('Bajura negra'))],
          loc='lower left', fontsize=10, framealpha=0.9)
plt.tight_layout(pad=0.2)
dst = os.path.join(OUT, 'hero_propuesta_v2.png')
plt.savefig(dst, dpi=140, bbox_inches='tight'); plt.close()
print('hero ->', dst)
