# -*- coding: utf-8 -*-
"""BLOQUE 14 v2 — mapas: (1) ambientes v2 sobre RGB + puntos, (2) comparacion v1 vs v2."""
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, rasterio
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import matplotlib.patches as mp
import warnings; warnings.filterwarnings('ignore')

BASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
CAN = os.path.join(BASE, '_analisis_canadas'); OUT = os.path.join(CAN, 'AMBIENTES_V2')
COLOR = {'Bajura negra': '#3E2723', 'Transicion': '#FFB300', 'Altura roja': '#D84315'}

lotes = gpd.read_file(os.path.join(CAN, 'Lotes_B14_divisiones.geojson')).to_crs(3857)
z2 = gpd.read_file(os.path.join(OUT, 'ZONAS_B14_V2.geojson')).to_crs(3857)
pts = gpd.read_file(os.path.join(OUT, 'PUNTOS_B14_V2.geojson')).to_crs(3857)
z1 = gpd.read_file(os.path.join(CAN, 'ZONAS_B14_GLOBAL.geojson')).to_crs(3857)  # v1 (Baja/Media/Alta)
PAL_V1 = {'Baja': '#F44336', 'Media': '#FFEB3B', 'Alta': '#4CAF50'}

# fondo RGB
rgb_src = rasterio.open(os.path.join(CAN, 's2_rgb_lotes.tif'))
from rasterio.warp import reproject, Resampling, calculate_default_transform
def rgb_3857(bnds):
    dt, w, h = calculate_default_transform(rgb_src.crs, 'EPSG:3857', rgb_src.width, rgb_src.height, *rgb_src.bounds)
    arr = np.zeros((3, h, w), 'uint8')
    for i in range(3):
        reproject(rgb_src.read(i+1), arr[i], src_transform=rgb_src.transform, src_crs=rgb_src.crs,
                  dst_transform=dt, dst_crs='EPSG:3857', resampling=Resampling.bilinear)
    ext = [dt.c, dt.c+dt.a*w, dt.f+dt.e*h, dt.f]
    return np.transpose(arr, (1, 2, 0)), ext
rgb, ext = rgb_3857(None)
b = lotes.total_bounds; pad = 200
xlim = (b[0]-pad, b[2]+pad); ylim = (b[1]-pad, b[3]+pad)

# ---------- MAPA 1: ambientes v2 + puntos ----------
fig, ax = plt.subplots(figsize=(15, 15))
ax.imshow(rgb, extent=ext, origin='upper')
for cl, col in COLOR.items():
    s = z2[z2.ambiente == cl]
    if len(s): s.plot(ax=ax, color=col, alpha=0.55, edgecolor='white', linewidth=0.3)
lotes.boundary.plot(ax=ax, color='yellow', linewidth=0.8)
pr = pts[pts.tipo == 'PRINCIPAL']; su = pts[pts.tipo == 'SUBMUESTRA']
su.plot(ax=ax, color='white', markersize=5, marker='o', alpha=0.7)
pr.plot(ax=ax, color='black', markersize=42, marker='*', edgecolor='white', linewidth=0.6)
for _, r in lotes.iterrows():
    c = r.geometry.centroid; ax.annotate(r['lote'], (c.x, c.y), fontsize=6, color='yellow', ha='center', weight='bold')
ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_axis_off()
ha = lambda cl: z2[z2.ambiente == cl].to_crs(31981).area.sum()/1e4
handles = [mp.Patch(color=COLOR['Altura roja'], label='Altura roja (bien drenada) — %.0f ha' % ha('Altura roja')),
           mp.Patch(color=COLOR['Transicion'], label='Transicion / media ladera — %.0f ha' % ha('Transicion')),
           mp.Patch(color=COLOR['Bajura negra'], label='Bajura negra (humeda/arcillosa) — %.0f ha' % ha('Bajura negra')),
           plt.Line2D([], [], color='black', marker='*', linestyle='', markersize=13, label='Punto principal (%d)' % len(pr)),
           plt.Line2D([], [], color='white', marker='o', linestyle='', markersize=7, markeredgecolor='gray', label='Submuestra (%d)' % len(su))]
ax.legend(handles=handles, loc='lower left', fontsize=11, framealpha=0.9)
ax.set_title('BLOQUE 14 — AMBIENTES v2.1 (color de suelo + drenaje/topografia + vigor verano) + muestreo\n'
             'Color desde suelo desnudo estacion seca (sin cultivo); vigor soya Nov-Mar 24/25+25/26; clasificacion block-wide', fontsize=12, weight='bold')
plt.tight_layout(); plt.savefig(os.path.join(OUT, 'MAPA_AMBIENTES_v2_B14.png'), dpi=145, bbox_inches='tight')
plt.close()

# ---------- MAPA 2: comparacion v1 vs v2 ----------
fig, axs = plt.subplots(1, 2, figsize=(24, 13))
for ax_, title, gdf, pal, col_field in [
        (axs[0], 'ANTES (v1) — score dominado por VIGOR NDVI\n3 zonas por lote (Baja/Media/Alta)', z1, PAL_V1, 'clase'),
        (axs[1], 'AHORA (v2) — SUELO (color+textura)+TOPO dominan\nAmbientes reales: Altura roja / Transicion / Bajura negra', z2, COLOR, 'ambiente')]:
    ax_.imshow(rgb, extent=ext, origin='upper')
    for cl, cc in pal.items():
        s = gdf[gdf[col_field] == cl]
        if len(s): s.plot(ax=ax_, color=cc, alpha=0.6, edgecolor='white', linewidth=0.25)
    lotes.boundary.plot(ax=ax_, color='yellow', linewidth=0.7)
    ax_.set_xlim(*xlim); ax_.set_ylim(*ylim); ax_.set_axis_off(); ax_.set_title(title, fontsize=13, weight='bold')
    ax_.legend(handles=[mp.Patch(color=cc, label=cl) for cl, cc in pal.items()], loc='lower left', fontsize=11)
plt.suptitle('BLOQUE 14 — Comparacion zonificacion v1 (vigor) vs v2 (suelo+topografia)  |  corrige el desajuste reportado en campo', fontsize=15, weight='bold')
plt.tight_layout(); plt.savefig(os.path.join(OUT, 'COMPARA_v1_vs_v2_B14.png'), dpi=135, bbox_inches='tight')
plt.close()
print('MAPA_AMBIENTES_v2_B14.png + COMPARA_v1_vs_v2_B14.png  ->', OUT)
print('DONE mapas')
