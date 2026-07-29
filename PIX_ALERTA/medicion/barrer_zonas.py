# -*- coding: utf-8 -*-
"""¿La capa de zonas entrega alguna vez, o el umbral la deja muda?

Corre `capas.zonas_lote` sobre todos los lotes de un cliente y varias fechas, **con
la unidad minima en cero**. Sin poner el umbral en cero no se puede distinguir
"no hay zonas" de "las hay pero el umbral las corta", que son dos conclusiones
opuestas: la primera es informacion para el productor y la segunda es un parametro
mal puesto.

    python -m medicion.barrer_zonas --cliente TRIGO --fechas 2026-06-05,2026-07-15

Resultado del 2026-07-29 sobre TRIGO (4 lotes x 5 fechas): 4 de 20 combinaciones con
alguna zona, la mayor de 0,16 ha. Ver el bloque de `capas.py`.
"""
import argparse
import json
import sys


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cliente', required=True)
    ap.add_argument('--fechas', required=True,
                    help='lista separada por comas, YYYY-MM-DD')
    ap.add_argument('--mmu', type=float, default=0.0,
                    help='unidad minima en ha. 0 = sin corte (lo correcto para medir)')
    a = ap.parse_args(argv)

    from pix_alerta.ee_init import inicializar
    print('[GEE] %s' % inicializar())
    from pix_alerta import capas as cp
    from pix_alerta import clientes as cl
    from pix_alerta import config as cfg
    clientes = cl.cargar_todos()
    cl.registrar_sitios(clientes)
    cliente = next((c for c in clientes if c.clave == a.cliente), None)
    if cliente is None:
        print('no existe el cliente %s' % a.cliente)
        return 1

    fechas = [f.strip() for f in a.fechas.split(',') if f.strip()]
    print('%-20s %-12s %5s %9s %9s  %s'
          % ('lote', 'fecha', 'n', 'ha total', 'mayor', 'nota'))
    vivos = n_comb = 0
    mayor_global = 0.0
    for s in cliente.sitios:
        with open(s.lotes_geojson, encoding='utf-8') as fh:
            gj = json.load(fh)
        for f in gj['features']:
            lid = str(f['properties'].get(s.campo_id))
            for fe in fechas:
                r = cp.zonas_lote(s, f, fe, mmu_ha=a.mmu)
                nota = ''
                if r.get('sin_escena'):
                    nota = 'sin escena ese dia'          # NO cuenta como combinacion
                elif r.get('error'):
                    nota = 'AVERIA ' + r['error'][:50]
                else:
                    n_comb += 1
                ar = sorted((z['properties']['area_ha'] for z in r.get('zonas', [])),
                            reverse=True)
                if ar:
                    vivos += 1
                    mayor_global = max(mayor_global, ar[0])
                print('%-20s %-12s %5d %9.2f %9.2f  %s'
                      % (lid, fe, len(ar), sum(ar), ar[0] if ar else 0.0, nota))
    print('\ncombinaciones EVALUABLES: %d' % n_comb)
    print('con al menos una zona:    %d' % vivos)
    print('zona mas grande:          %.2f ha' % mayor_global)
    print('\nSi la mayor esta muy por debajo de criterio.MMU_ZONA_HA (%.2f ha), la capa '
          'NO entrega\nen este campo. Bajar el umbral para que salga algo es elegir el '
          'parametro por la\nsalida que produce: no se hace.' % _mmu())
    return 0


def _mmu():
    from pix_alerta import criterio as cri
    return cri.MMU_ZONA_HA


if __name__ == '__main__':
    sys.exit(main())
