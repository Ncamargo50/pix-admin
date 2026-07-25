# -*- coding: utf-8 -*-
"""Ruteo hidrologico real (pysheds) sobre FABDEM bare-earth: red de drenaje por
acumulacion de flujo + plani-altimetria (hillshade+curvas) + TWI sobre los lotes."""
import os, numpy as np, json
import geopandas as gpd, rasterio
from pysheds.grid import Grid
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
import warnings; warnings.filterwarnings('ignore')

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUTDIR = os.path.join(DIRBASE, '_analisis_canadas')
DEM = os.path.join(OUTDIR, 'dem_fabdem.tif')
LOT = os.path.join(DIRBASE, 'Lotes_SerroAlto_Muestreo_Soya_26-27.geojson')
lot = gpd.read_file(LOT).to_crs(31981)

# --- pysheds: condicionar y rutear ---
grid = Grid.from_raster(DEM)
dem = grid.read_raster(DEM)
pit = grid.fill_pits(dem); dep = grid.fill_depressions(pit); inf = grid.resolve_flats(dep)
fdir = grid.flowdir(inf)
acc = grid.accumulation(fdir)
print('flow-acc max (celdas):', int(np.nanmax(acc)), '= %.1f km2' % (np.nanmax(acc)*900/1e6))

demarr = np.array(dem, dtype='float32'); demarr[demarr <= 0] = np.nan
accarr = np.array(acc, dtype='float32')
# pendiente y TWI
dzdy, dzdx = np.gradient(np.nan_to_num(demarr, nan=np.nanmin(demarr)), 30, 30)
slope = np.arctan(np.hypot(dzdx, dzdy))
twi = np.log(((accarr + 1) * 900) / (np.tan(slope) + 1e-3))
# red de drenaje a 2 umbrales
extent = grid.extent  # (xmin,xmax,ymin,ymax)
trans = rasterio.open(DEM).transform

def to_geo(thr):
    return accarr > thr
streams_main = to_geo(2000)   # >1.8 km2
streams_fine = to_geo(300)    # >0.27 km2

minx, miny, maxx, maxy = lot.total_bounds; pad = 800
def setlim(ax):
    ax.set_xlim(minx-pad, maxx+pad); ax.set_ylim(miny-pad, maxy+pad); ax.set_axis_off()

# PANEL 1: acumulacion + red + lotes
fig, ax = plt.subplots(figsize=(11, 11))
ax.imshow(np.log10(accarr + 1), extent=extent, cmap='cubehelix_r', alpha=0.9)
sm = np.where(streams_fine, 1, np.nan); ax.imshow(sm, extent=extent, cmap='autumn', alpha=0.5)
sm2 = np.where(streams_main, 1, np.nan); ax.imshow(sm2, extent=extent, cmap='cool', alpha=0.9)
lot.boundary.plot(ax=ax, color='lime', linewidth=0.8)
ax.set_title('Cerro Alto - Red de drenaje por ACUMULACION DE FLUJO (FABDEM 30m)\nazul=cauce principal >1.8km2 | naranja=drenaje fino >0.27km2'); setlim(ax)
plt.savefig(os.path.join(OUTDIR, '11_flowacc_drenaje.png'), dpi=140, bbox_inches='tight'); plt.close()
print('panel -> 11_flowacc_drenaje.png')

# PANEL 2: PLANI-ALTIMETRIA (hillshade + curvas de nivel)
fig, ax = plt.subplots(figsize=(11, 11))
ls = LightSource(azdeg=315, altdeg=45)
hs = ls.hillshade(np.nan_to_num(demarr, nan=np.nanmedian(demarr)), vert_exag=3, dx=30, dy=30)
ax.imshow(hs, extent=extent, cmap='gray', alpha=0.8)
lv = np.arange(np.floor(np.nanmin(demarr)/5)*5, np.nanmax(demarr), 5)  # curvas cada 5 m
ny, nx = demarr.shape
xs = np.linspace(extent[0], extent[1], nx); ys = np.linspace(extent[3], extent[2], ny)
X, Y = np.meshgrid(xs, ys)
cs = ax.contour(X, Y, demarr, levels=lv, colors='saddlebrown', linewidths=0.3, alpha=0.7)
ax.clabel(cs, lv[::2], fontsize=4, fmt='%d')
lot.boundary.plot(ax=ax, color='red', linewidth=0.9)
ax.set_title('Cerro Alto - PLANI-ALTIMETRIA (FABDEM): sombreado + curvas cada 5 m'); setlim(ax)
plt.savefig(os.path.join(OUTDIR, '12_planialtimetria.png'), dpi=150, bbox_inches='tight'); plt.close()
print('panel -> 12_planialtimetria.png')

# PANEL 3: TWI
fig, ax = plt.subplots(figsize=(11, 11))
im = ax.imshow(np.clip(twi, 2, 14), extent=extent, cmap='Spectral_r')
lot.boundary.plot(ax=ax, color='black', linewidth=0.7)
ax.set_title('Cerro Alto - TWI (indice de humedad topografica) - alto=convergencia/humedo'); setlim(ax)
plt.colorbar(im, ax=ax, shrink=0.5)
plt.savefig(os.path.join(OUTDIR, '13_TWI.png'), dpi=140, bbox_inches='tight'); plt.close()
print('panel -> 13_TWI.png')

# guardar rasters derivados (para QGIS / paso siguiente)
prof = rasterio.open(DEM).profile; prof.update(dtype='float32', count=1, nodata=-9999)
for nm, arr in [('flowacc', accarr), ('twi', twi.astype('float32'))]:
    prof2 = prof.copy()
    with rasterio.open(os.path.join(OUTDIR, 'hydro_%s.tif' % nm), 'w', **prof2) as d:
        d.write(np.nan_to_num(arr, nan=-9999).astype('float32'), 1)
print('rasters hydro_flowacc.tif / hydro_twi.tif guardados')
print('DONE')
