# -*- coding: utf-8 -*-
"""CERRO ALTO v2.1 — ENTREGA: copia GeoJSON APK de los 3 bloques + PNG por lote + overview hacienda."""
import os, sys, shutil, glob
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, numpy as np, rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import matplotlib.patches as mp
import warnings; warnings.filterwarnings('ignore')

BASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
CAN = os.path.join(BASE, '_analisis_canadas'); OUT = os.path.join(CAN, 'AMBIENTES_V2')
DELIV = os.path.join(BASE, 'APK_muestreo_SerroAlto_v2'); os.makedirs(DELIV, exist_ok=True)
PNGD = os.path.join(OUT, 'informe_png_lote'); os.makedirs(PNGD, exist_ok=True)
COLOR = {'Bajura negra': '#3E2723', 'Transicion': '#FFB300', 'Altura roja': '#D84315'}

# 1) copiar TODOS los geojson APK (66 lotes) + combinados
src = sorted(glob.glob(os.path.join(OUT, 'APK_muestreo_por_lote', 'Bloque-*_muestreo.geojson')))
for f in src: shutil.copy2(f, os.path.join(DELIV, os.path.basename(f)))
shutil.copy2(os.path.join(OUT, 'PUNTOS_SerroAlto_V2.geojson'), os.path.join(DELIV, 'PUNTOS_SerroAlto_TODOS.geojson'))
shutil.copy2(os.path.join(OUT, 'ZONAS_SerroAlto_V2.geojson'), os.path.join(DELIV, 'ZONAS_SerroAlto_TODAS.geojson'))
print('APK geojson entregados:', len(src), 'lotes + 2 combinados ->', os.path.basename(DELIV))

# 2) RGB base 3857
rgb_src = rasterio.open(os.path.join(CAN, 's2_rgb_lotes.tif'))
dt, w, h = calculate_default_transform(rgb_src.crs, 'EPSG:3857', rgb_src.width, rgb_src.height, *rgb_src.bounds)
rgb = np.zeros((3, h, w), 'uint8')
for i in range(3):
    reproject(rgb_src.read(i+1), rgb[i], src_transform=rgb_src.transform, src_crs=rgb_src.crs,
              dst_transform=dt, dst_crs='EPSG:3857', resampling=Resampling.bilinear)
rgb = np.transpose(rgb, (1, 2, 0)); ext = [dt.c, dt.c+dt.a*w, dt.f+dt.e*h, dt.f]

allz = gpd.read_file(os.path.join(OUT, 'ZONAS_SerroAlto_V2.geojson')).to_crs(3857)
allp = gpd.read_file(os.path.join(OUT, 'PUNTOS_SerroAlto_V2.geojson')).to_crs(3857)

# 3) PNG por lote (66)
import glob as _g
lote_layers = {b: gpd.read_file(os.path.join(CAN, 'Lotes_B%s_divisiones.geojson' % b)).to_crs(3857) for b in ['2', '3', '14']}
n = 0
for bk, lg in lote_layers.items():
    for lote in sorted(lg['lote'].unique()):
        g = lg[lg.lote == lote]; b = g.total_bounds; pad = 60
        fig, ax = plt.subplots(figsize=(9, 6.2)); ax.imshow(rgb, extent=ext, origin='upper')
        zl = allz[(allz.bloque.astype(str) == bk) & (allz.lote == lote)]
        for cl, col in COLOR.items():
            s = zl[zl.ambiente == cl]
            if len(s): s.plot(ax=ax, color=col, alpha=0.55, edgecolor='white', linewidth=0.4)
        g.boundary.plot(ax=ax, color='yellow', linewidth=1.2)
        pl = allp[(allp.bloque.astype(str) == bk) & (allp.lote == lote)]
        pl[pl.tipo == 'SUBMUESTRA'].plot(ax=ax, color='white', markersize=13, marker='o', alpha=0.85, edgecolor='gray', linewidth=0.4)
        pri = pl[pl.tipo == 'PRINCIPAL']   # principal = circulo del color del ambiente con etiqueta P1/P2/P3 (como antes)
        ax.scatter(pri.geometry.x, pri.geometry.y, s=300, c=[COLOR[a] for a in pri['ambiente']],
                   edgecolor='white', linewidth=1.4, zorder=5)
        for _, r in pri.iterrows():
            ax.annotate('P%d' % r['zona'], (r.geometry.x, r.geometry.y), fontsize=9, color='white',
                        weight='bold', ha='center', va='center', zorder=6)
        ax.set_xlim(b[0]-pad, b[2]+pad); ax.set_ylim(b[1]-pad, b[3]+pad); ax.set_axis_off()
        plt.tight_layout(pad=0.2); plt.savefig(os.path.join(PNGD, 'B%s_%s.png' % (bk, lote)), dpi=115, bbox_inches='tight'); plt.close(); n += 1
print('PNG por lote:', n)

# 4) overview hacienda
fig, ax = plt.subplots(figsize=(15, 16)); ax.imshow(rgb, extent=ext, origin='upper')
for cl, col in COLOR.items():
    s = allz[allz.ambiente == cl]
    if len(s): s.plot(ax=ax, color=col, alpha=0.55, edgecolor='white', linewidth=0.2)
for bk, lg in lote_layers.items(): lg.boundary.plot(ax=ax, color='yellow', linewidth=0.5)
allp[allp.tipo == 'PRINCIPAL'].plot(ax=ax, color='black', markersize=14, marker='o', edgecolor='white', linewidth=0.3)
b = allz.total_bounds; pad = 300; ax.set_xlim(b[0]-pad, b[2]+pad); ax.set_ylim(b[1]-pad, b[3]+pad); ax.set_axis_off()
ha = lambda c: allz[allz.ambiente == c].to_crs(31981).area.sum()/1e4
handles = [mp.Patch(color=COLOR['Altura roja'], label='Altura roja (bien drenada) — %.0f ha' % ha('Altura roja')),
           mp.Patch(color=COLOR['Transicion'], label='Transicion — %.0f ha' % ha('Transicion')),
           mp.Patch(color=COLOR['Bajura negra'], label='Bajura negra (humeda) — %.0f ha' % ha('Bajura negra')),
           plt.Line2D([], [], color='black', marker='o', linestyle='', markersize=9, label='Punto principal / muestra compuesta (%d)' % int((allp.tipo=='PRINCIPAL').sum()))]
ax.legend(handles=handles, loc='lower left', fontsize=12, framealpha=0.9)
ax.set_title('HACIENDA CERRO ALTO — AMBIENTES v2.1 (color de suelo + drenaje + vigor verano) — Bloques 2, 3 y 14', fontsize=13, weight='bold')
plt.tight_layout(); plt.savefig(os.path.join(OUT, 'MAPA_AMBIENTES_SerroAlto_v2.png'), dpi=140, bbox_inches='tight'); plt.close()
print('overview -> MAPA_AMBIENTES_SerroAlto_v2.png'); print('DONE deliver')
