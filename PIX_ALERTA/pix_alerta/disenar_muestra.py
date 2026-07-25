"""Arma la muestra de validacion de una campaña. Se corre UNA VEZ, antes de sembrar.

    python -m pix_alerta.disenar_muestra --ranking salida/HDS/ranking_HDS_2026-04-30.csv \
        --sitio HDS --prevalencia 0.30 --semiancho 0.10 --K 10 --rondas 20

Emite:
    muestra_<sitio>_<fecha>.csv       la muestra con probabilidad de inclusion y peso
    muestra_<sitio>_<fecha>.geojson   lo que carga la APK, CIEGO (sin estrato visible)
    dimensionamiento_<sitio>.txt      el calculo del n, para que quede auditable

POR QUE ANTES DE SEMBRAR: una vez que la campaña arranca, elegir a donde va el tecnico
en funcion de lo que ya se vio sesga el resultado. El sorteo tiene que estar hecho y
guardado antes de que haya nada que mirar.
"""
import argparse
import json
import os
import sys
from datetime import date

import pandas as pd

from . import config as cfg
from . import muestreo as ms


def geoms_del_sitio(sitio):
    with open(sitio.lotes_geojson, encoding='utf-8') as fh:
        gj = json.load(fh)
    return {str(f['properties'].get(sitio.campo_id)): f['geometry']
            for f in gj['features']}


def main(argv=None):
    p = argparse.ArgumentParser(description='PIX ALERTA — muestra de validacion')
    p.add_argument('--ranking', required=True, help='CSV de ranking SIN cortar por K')
    p.add_argument('--sitio', default=None, help='clave del sitio (para el GeoJSON)')
    p.add_argument('--prevalencia', type=float, default=0.30,
                   help='prevalencia esperada de problema real (0-1)')
    p.add_argument('--semiancho', type=float, default=0.10, help='medio ancho del IC')
    p.add_argument('--confianza', type=float, default=0.95)
    p.add_argument('--K', type=int, default=None, help='capacidad de scouting por ronda')
    p.add_argument('--rondas', type=int, default=None, help='rondas de la campaña')
    p.add_argument('--semilla', type=int, default=0, help='sorteo REPRODUCIBLE')
    p.add_argument('--salida', default='salida')
    a = p.parse_args(argv)

    rank = pd.read_csv(a.ranking)
    if 'estado' not in rank.columns:
        print('[ERROR] el CSV no tiene columna "estado": no es un ranking.')
        return 1

    N_por_estrato = (rank[~rank['estado'].isin(ms.EXCLUIDOS)]
                     .groupby('estado')['lote_id'].nunique().to_dict())
    sin_dato = int((rank['estado'] == 'SIN DATO').sum())

    # GUARDA CRITICA. `main.py --K` recorta el ranking a los lotes que salen de control,
    # asi que un CSV generado con K NO contiene el estrato verde. Sortear sobre eso
    # produce exactamente el sesgo de verificacion que este modulo existe para evitar:
    # solo se visitan rojos, la precision sale alta por construccion y la campaña entera
    # queda sin valor. Se detecto emitiendo una muestra real de HDS con 0 lotes en verde.
    if not N_por_estrato.get('SIN SEÑAL'):
        print('')
        print('[ERROR] el ranking no tiene NINGUN lote en "SIN SEÑAL" (el estrato verde).')
        print('        Casi seguro se genero con --K, que recorta a los lotes que salen')
        print('        de control. Sortear sobre eso da el SESGO DE VERIFICACION: se')
        print('        visitan solo rojos, la precision sale alta por construccion y la')
        print('        campaña no mide nada.')
        print('')
        print('        Regenerar el ranking SIN --K:')
        print('          python -m pix_alerta.main --sitio %s --hasta <fecha> --salida <dir>'
              % (a.sitio or '<SITIO>'))
        return 1

    tab, ver = ms.dimensionar(N_por_estrato, a.prevalencia, a.semiancho,
                              a.confianza, a.K, a.rondas)
    n_por_estrato = dict(zip(tab['estrato'], tab['n']))

    os.makedirs(a.salida, exist_ok=True)
    hoy = str(date.today())
    clave = a.sitio or 'SITIO'

    lineas = ['DIMENSIONAMIENTO DE LA MUESTRA DE VALIDACION',
              '=' * 60,
              'sitio            : %s' % clave,
              'ranking de base  : %s' % a.ranking,
              'prevalencia esp. : %.0f%%' % (100 * a.prevalencia),
              'IC pedido        : +-%.0f pp al %.0f%%' % (100 * a.semiancho, 100 * a.confianza),
              'semilla          : %d  (el sorteo es reproducible)' % a.semilla,
              '']
    if sin_dato:
        lineas.append('%d lotes en SIN DATO quedan FUERA: es ausencia de observacion, '
                      'no un veredicto.' % sin_dato)
        lineas.append('')
    lineas.append(tab[['estrato', 'N', 'n']].to_string(index=False))
    lineas.append('')
    lineas.append('n total          : %d visitas' % ver['n_total'])
    lineas.append('error relativo   : %.0f%% del valor estimado' % (100 * ver['error_relativo']))
    if 'capacidad_campaña' in ver:
        lineas.append('capacidad        : %d (K=%d x %d rondas) -> %s'
                      % (ver['capacidad_campaña'], a.K, a.rondas,
                         'ALCANZA' if ver['alcanza'] else 'NO ALCANZA'))
    for av in ver['avisos']:
        lineas.append('')
        lineas.append('! ' + av)
    txt = '\n'.join(lineas)
    ruta_dim = os.path.join(a.salida, 'dimensionamiento_%s.txt' % clave)
    with open(ruta_dim, 'w', encoding='utf-8') as fh:
        fh.write(txt + '\n')
    print(txt)

    muestra = ms.sortear(rank, n_por_estrato=n_por_estrato, semilla=a.semilla)
    if muestra.empty:
        print('\n[NO-OP] no se pudo sortear: no hay lotes en los estratos pedidos.')
        return 0

    ruta_csv = os.path.join(a.salida, 'muestra_%s_%s.csv' % (clave, hoy))
    muestra.to_csv(ruta_csv, index=False)

    ruta_gj = None
    if a.sitio and a.sitio in cfg.SITIOS:
        try:
            n = ms.a_geojson_ciego(muestra, geoms_del_sitio(cfg.SITIOS[a.sitio]),
                                   os.path.join(a.salida, 'muestra_%s_%s.geojson' % (clave, hoy)))
            ruta_gj = os.path.join(a.salida, 'muestra_%s_%s.geojson' % (clave, hoy))
            print('\n  -> %s (%d lotes, CIEGO)' % (ruta_gj, n))
        except Exception as e:
            print('\n  [AVISO] no se pudo emitir el GeoJSON: %s' % e)

    print('  -> %s (%d visitas)' % (ruta_csv, len(muestra)))
    print('  -> %s' % ruta_dim)
    print('\nRECORDAR: encender MODO_CIEGO en la APK antes de repartir esta muestra.')
    return 10


if __name__ == '__main__':
    sys.exit(main())
