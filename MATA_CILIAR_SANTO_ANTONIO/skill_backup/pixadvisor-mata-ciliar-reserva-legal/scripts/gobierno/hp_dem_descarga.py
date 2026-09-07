# -*- coding: utf-8 -*-
"""Helper de an_11: baja los DEM que faltan para el ensamble (SRTMGL1 y ALOS AW3D30 V4.1)
al mismo grid de 30 m del AOI DEM (aoi_dem_31982) que ya usan GLO30/NASADEM/FABDEM.

INPE TOPODATA (www.dsr.inpe.br/topodata): el host no resuelve DNS el 2026-09-06 y el
espejo webmapit devuelve 404; TOPODATA es un SRTM 90 m refinado a 30 m por krigeado, de
modo que USGS/SRTMGL1_003 (SRTM 1 arc-sec real) lo reemplaza con ventaja.
"""
import os

from an_00_config import DATOS_SAT as SALIDA, log
from comun import cargar_propiedad, descargar_geotiff, inicializar_ee, verificar_raster

DEMS_GEE = {
    'SRTMGL1': ('USGS/SRTMGL1_003', 'elevation', 'img'),
    'AW3D30': ('JAXA/ALOS/AW3D30/V4_1', 'DSM', 'ic'),
}


def descargar_dems(p, forzar=False):
    ee = inicializar_ee()
    rutas = {}
    bbox = p['aoi_dem_31982']
    for nombre, (aid, banda, tipo) in DEMS_GEE.items():
        destino = os.path.join(SALIDA, 'DEM_%s_AOIdem_30m.tif' % nombre)
        rutas[nombre] = destino
        if os.path.exists(destino) and not forzar:
            log('  DEM %s ya existe' % nombre); continue
        if tipo == 'img':
            img = ee.Image(aid).select(banda)
        else:
            col = ee.ImageCollection(aid).select(banda)
            # mosaic() pierde la proyeccion nativa (queda WGS84 a 1 grado) y el resample
            # bajaria un DEM degradado (MEDIDO: AW3D30 salio 723-750 m en vez de 543-772):
            # se fija la proyeccion del primer tile antes de reproyectar
            img = col.mosaic().setDefaultProjection(col.first().projection())
        img = img.rename('DEM').resample('bilinear')
        descargar_geotiff(img, bbox, 30, destino, ['DEM'], descripcion='DEM %s 30 m' % nombre)
        verificar_raster(destino, rotulo='DEM %s' % nombre)
    return rutas


if __name__ == '__main__':
    p = cargar_propiedad()
    print(descargar_dems(p))
