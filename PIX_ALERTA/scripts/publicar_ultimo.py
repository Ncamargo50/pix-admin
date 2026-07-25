# -*- coding: utf-8 -*-
"""Deja la ultima entrega de cada cliente en una ruta ESTABLE.

    python scripts/publicar_ultimo.py entregas

POR QUE HACE FALTA
------------------
La APK descarga los focos de una URL fija (`FOCOS_ENDPOINT`). Si el archivo se llamara
`lotes_HDS_2026-11-12.geojson`, el telefono tendria que adivinar la fecha de la ultima
corrida — y el dia que hay nubes y no se emite nada, adivinaria mal y bajaria un mapa
viejo creyendolo de hoy.

Con esto queda:

    entregas/<CLIENTE>/2026-11-12/...      historico, no se toca
    entregas/<CLIENTE>/ultimo/<SITIO>.geojson   <- lo que baja el telefono
    entregas/<CLIENTE>/ultimo/informe.pdf
    entregas/<CLIENTE>/ultimo/META.json    fecha real de lo publicado

META.json existe para que se pueda AUDITAR que se publico y de cuando es. Un archivo
"ultimo" sin fecha adentro es exactamente el problema que se queria evitar.
"""
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone

RE_FECHA = re.compile(r'(\d{4}-\d{2}-\d{2})')


def publicar(base):
    if not os.path.isdir(base):
        print('no existe la carpeta %s' % base)
        return 0
    n_pub = 0
    for cliente in sorted(os.listdir(base)):
        dcli = os.path.join(base, cliente)
        if not os.path.isdir(dcli) or cliente.startswith('.'):
            continue
        # Archivos con fecha en el nombre, del mas nuevo al mas viejo.
        cand = []
        for nom in os.listdir(dcli):
            ruta = os.path.join(dcli, nom)
            if not os.path.isfile(ruta):
                continue
            m = RE_FECHA.search(nom)
            if m:
                cand.append((m.group(1), nom))
        if not cand:
            continue
        ultima = max(f for f, _ in cand)
        dest = os.path.join(dcli, 'ultimo')
        # Se limpia antes: si la corrida de hoy no emitio GeoJSON, dejar el de la semana
        # pasada dentro de "ultimo" haria que el telefono lo baje como si fuera de hoy.
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        os.makedirs(dest)

        publicados = []
        for fecha, nom in cand:
            if fecha != ultima:
                continue
            src = os.path.join(dcli, nom)
            if nom.endswith('.geojson'):
                # nombre estable = clave del sitio, sin la fecha
                sitio = nom.replace('lotes_', '').replace('_%s.geojson' % fecha, '')
                nuevo = '%s.geojson' % sitio
            elif nom.endswith('.pdf'):
                nuevo = 'informe.pdf'
            elif nom.endswith('.csv') and nom.startswith('ranking_'):
                nuevo = 'ranking.csv'
            else:
                continue
            shutil.copy2(src, os.path.join(dest, nuevo))
            publicados.append(nuevo)

        with open(os.path.join(dest, 'META.json'), 'w', encoding='utf-8') as fh:
            json.dump({'cliente': cliente, 'fecha_entrega': ultima,
                       'publicado_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
                       'archivos': sorted(publicados)}, fh, ensure_ascii=False, indent=2)
        print('  %-12s -> ultimo/ (%s) %s' % (cliente, ultima, ', '.join(sorted(publicados))))
        n_pub += 1
    return n_pub


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else 'entregas'
    print('Publicando la ultima entrega de cada cliente...')
    n = publicar(base)
    print('%d cliente(s) publicados.' % n)
