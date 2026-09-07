# -*- coding: utf-8 -*-
"""Paso 4: abrir TODO lo bajado con rasterio y fallar ruidoso si algo esta mal.

    python verificar_datos.py        (exit 0 = todo dentro de rango; 1 = hay fallas)

Que se controla por archivo:
- CRS EPSG:31982 y origen de la transformada multiplo de 10 m (grid comun).
- Por banda: n, min, max, media, % nodata. Falla si la capa esta vacia
  (100% nodata) o degenerada (min == max), o si sale del rango FISICO:
    reflectancia S2      -0.10 .. 1.20 (el -0.0999 es el recorte de Sen2Cor;
                         >1 ocurre en techos y nube brillante) y media 0..1
    NDVI/NDWI/MNDWI/NDMI/NDRE   -1 .. 1
    AWEInsh              finito; rango tipico -3 .. 3 con reflectancia 0..1
    SCL 0..11, cs_cdf 0..1
    DEM (GLO30/FABDEM/NASADEM)  200 .. 1000 m para el norte de Parana
    MERIT upa >= 0 km2, hnd 0 .. 500 m
    MapBiomas: valores dentro de la leyenda oficial
    Dynamic World label 0..8, n_obs >= 1; WorldCover en {10..100}
    Hansen treecover 0..100, lossyear 0..25, gain 0..1
    JRC occurrence 0..100, max_extent 0..1
Los rangos absolutos aca sirven para detectar ERRORES DE PROCESAMIENTO, no
como criterio agronomico (regla de la casa).
"""
import glob
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import EPSG_METRICO, GRID_M, SALIDA, log

CLASES_MAPBIOMAS = {0, 1, 3, 4, 5, 6, 49, 10, 11, 12, 32, 29, 50, 14, 15, 18, 19, 39, 20, 40, 62,
                    41, 36, 46, 47, 35, 48, 9, 21, 22, 23, 24, 30, 25, 26, 33, 31, 27}
CLASES_WORLDCOVER = {10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100}


def regla(nombre_archivo, banda):
    """Devuelve (min_permitido, max_permitido, conjunto_permitido, media_rango) o None."""
    f = nombre_archivo.upper()
    b = banda
    if f.startswith('S2_') and '_AOI_10M' in f:
        if b.startswith('B'):
            return (-0.10, 1.20, None, (0.0, 1.0))
        if b == 'SCL':
            return (0, 11, None, None)
        if b == 'cs_cdf':
            return (0, 1, None, None)
    if f.startswith('S2_') and '_SCL_' in f:
        return (0, 11, None, None)
    if f.startswith('S2_') and '_RGB' in f:
        return (0, 255, None, None)
    if f.startswith('S2_') and '_INDICES_' in f:
        if b == 'AWEInsh':
            return (-3.0, 3.0, None, None)
        return (-1.0, 1.0, None, None)
    if f.startswith('DEM_'):
        return (200.0, 1000.0, None, None)
    if f.startswith('HIDRO_MERIT'):
        return {'upa': (0.0, 1e6, None, None), 'hnd': (0.0, 500.0, None, None)}.get(b)
    if f.startswith('LULC_MAPBIOMAS'):
        return (None, None, CLASES_MAPBIOMAS, None)
    if f.startswith('LULC_DYNAMICWORLD'):
        return {'label_moda': (0, 8, None, None), 'n_obs': (1, 255, None, None)}.get(b)
    if f.startswith('LULC_ESA_WORLDCOVER'):
        return (None, None, CLASES_WORLDCOVER, None)
    if f.startswith('BOSQUE_HANSEN'):
        return {'treecover2000': (0, 100, None, None), 'lossyear': (0, 25, None, None),
                'gain': (0, 1, None, None)}.get(b)
    if f.startswith('AGUA_JRC'):
        return {'occurrence': (0, 100, None, None), 'max_extent': (0, 1, None, None)}.get(b)
    return None


def verificar(ruta):
    import rasterio
    fallas = []
    nombre = os.path.basename(ruta)
    with rasterio.open(ruta) as src:
        if src.crs is None or src.crs.to_epsg() != EPSG_METRICO:
            fallas.append('CRS %s != EPSG:%d' % (src.crs, EPSG_METRICO))
        t = src.transform
        if abs(t.c / GRID_M - round(t.c / GRID_M)) > 1e-6 or abs(t.f / GRID_M - round(t.f / GRID_M)) > 1e-6:
            fallas.append('origen (%.2f, %.2f) no es multiplo de %d m' % (t.c, t.f, GRID_M))
        log('%s' % nombre)
        log('  %dx%d px, %d banda(s), %s, res %.1f m, nodata %s, %.1f MB'
            % (src.width, src.height, src.count, src.crs, src.res[0], src.nodata,
               os.path.getsize(ruta) / 1e6))
        for i in range(1, src.count + 1):
            b = src.descriptions[i - 1] or 'b%d' % i
            a = src.read(i).astype('float64')
            valido = np.isfinite(a)
            if src.nodata is not None:
                valido &= a != src.nodata
            n = int(valido.sum())
            pct_nd = 100.0 * (1 - n / a.size)
            if n == 0:
                log('    %-16s VACIA (100%% nodata)' % b)
                fallas.append('%s: vacia' % b)
                continue
            v = a[valido]
            mn, mx, me = float(v.min()), float(v.max()), float(v.mean())
            r = regla(nombre, b)
            problemas = []
            if mn == mx:
                problemas.append('degenerada (min == max)')
            if r is None:
                problemas.append('SIN REGLA de rango para esta banda')
            else:
                lo, hi, conjunto, media_rango = r
                if lo is not None and mn < lo:
                    problemas.append('min %.4f < %.4f' % (mn, lo))
                if hi is not None and mx > hi:
                    problemas.append('max %.4f > %.4f' % (mx, hi))
                if conjunto is not None:
                    fuera = sorted(set(np.unique(v).astype(int).tolist()) - conjunto)
                    if fuera:
                        problemas.append('clases fuera de leyenda %s' % fuera)
                if media_rango is not None and not (media_rango[0] < me < media_rango[1]):
                    problemas.append('media %.4f fuera de %s' % (me, media_rango))
            if not np.all(np.isfinite(v)):
                problemas.append('NaN/inf')
            marca = '  FALLA: ' + '; '.join(problemas) if problemas else ''
            log('    %-16s n=%-8d min=%11.4f max=%11.4f media=%11.4f nodata=%5.1f%%%s'
                % (b, n, mn, mx, me, pct_nd, marca))
            fallas.extend('%s: %s' % (b, q) for q in problemas)
    return fallas


def main():
    rutas = sorted(glob.glob(os.path.join(SALIDA, '*.tif')))
    if not rutas:
        log('No hay GeoTIFF en %s' % SALIDA)
        sys.exit(1)
    log('=== verificar_datos: %d GeoTIFF en %s ===' % (len(rutas), SALIDA))
    todas = {}
    for r in rutas:
        f = verificar(r)
        if f:
            todas[os.path.basename(r)] = f
    otros = sorted(glob.glob(os.path.join(SALIDA, '*.json')) + glob.glob(os.path.join(SALIDA, '*.geojson')))
    log('')
    log('Otros archivos: %s' % ', '.join('%s (%.0f kB)' % (os.path.basename(o), os.path.getsize(o) / 1e3) for o in otros))
    log('')
    if todas:
        log('FALLAS en %d archivo(s):' % len(todas))
        for k, v in todas.items():
            for q in v:
                log('  %s :: %s' % (k, q))
        sys.exit(1)
    log('OK: %d archivos, todas las bandas dentro de rango fisico, CRS y grid correctos.' % len(rutas))


if __name__ == '__main__':
    main()
