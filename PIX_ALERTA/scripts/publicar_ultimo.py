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

# prefijo del motor -> (extension, plantilla del nombre estable publicado).
# EL NOMBRE ESTABLE LLEVA SIEMPRE LA PROPIEDAD. Con nombres fijos por cliente
# (`informe.pdf`, `ranking.csv`), un cliente con dos haciendas publicaba UNA SOLA,
# elegida por el orden de os.listdir: el productor recibia el informe de un campo
# creyendo que era del otro.
_PUBLICA = (('focos_', '.geojson', 'focos_%s.geojson'),
            ('lotes_', '.geojson', 'lotes_%s.geojson'),
            ('ranking_', '.csv', 'ranking_%s.csv'),
            ('Informe_', '.pdf', 'Informe_%s.pdf'))


def _sitio_de(nom, fecha):
    """Clave de la propiedad a partir del nombre del entregable. None si no lo es."""
    for pref, ext, _ in _PUBLICA:
        if nom.startswith(pref) and nom.endswith(ext):
            return nom[len(pref):].replace('_%s%s' % (fecha, ext), '')
    return None


def _nombre_estable(nom, fecha):
    """Como se llama ese entregable dentro de `ultimo/`. None si no se publica."""
    for pref, ext, plantilla in _PUBLICA:
        if nom.startswith(pref) and nom.endswith(ext):
            return plantilla % nom[len(pref):].replace('_%s%s' % (fecha, ext), '')
    return None


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
        # UNA FECHA POR PROPIEDAD, no una para todo el cliente. Con `max()` global,
        # la hacienda que no emitio hoy DESAPARECIA de `ultimo/`: la APK pedia su
        # GeoJSON y recibia 404, y el WhatsApp contaba solo los lotes de la otra.
        # Pasa siempre que una propiedad emite y la otra no — nubes en una zona y no
        # en la otra, o ventanas de campaña distintas, que es justo lo que el alta
        # web fomenta al pedir una fecha de siembra POR PROPIEDAD.
        ultima_de = {}
        for fecha, nom in cand:
            sitio = _sitio_de(nom, fecha)
            if sitio is None:
                continue
            if sitio not in ultima_de or fecha > ultima_de[sitio]:
                ultima_de[sitio] = fecha
        if not ultima_de:
            continue
        ultima = max(ultima_de.values())       # la mas reciente, para el META
        dest = os.path.join(dcli, 'ultimo')
        # Se limpia antes: si la corrida de hoy no emitio GeoJSON, dejar el de la semana
        # pasada dentro de "ultimo" haria que el telefono lo baje como si fuera de hoy.
        if os.path.isdir(dest):
            shutil.rmtree(dest)
        os.makedirs(dest)

        publicados = []
        for fecha, nom in cand:
            sitio_nom = _sitio_de(nom, fecha)
            # Cada propiedad publica SU ultima fecha, no la del cliente.
            if sitio_nom is None or fecha != ultima_de.get(sitio_nom):
                continue
            src = os.path.join(dcli, nom)
            # EL NOMBRE ESTABLE LLEVA LA PROPIEDAD, SIEMPRE. Con nombres fijos por
            # cliente (`informe.pdf`, `ranking.csv`, `focos.geojson`), un cliente con
            # dos haciendas publicaba el informe y el ranking de UNA SOLA, la ultima
            # que devolviera os.listdir — orden no determinista. El productor recibia
            # el informe de un campo y creia que era del otro. Con multipropiedad
            # recien habilitada, esto pasaba de ser teorico a seguro.
            nuevo = _nombre_estable(nom, fecha)
            if nuevo is None:
                continue
            shutil.copy2(src, os.path.join(dest, nuevo))
            publicados.append(nuevo)

        # Cuantos lotes hay para recorrer. Va en el META para que el aviso de
        # WhatsApp pueda decirlo sin abrir el CSV, y para poder auditar despues
        # cuantos se mandaron sin depender de que el archivo siga ahi.
        # Se suman TODAS las propiedades del cliente: el aviso habla del cliente,
        # no de una hacienda. Con un solo ranking.csv se contaba una sola.
        alertados = None
        import csv as _csv
        for nom_r in sorted(os.listdir(dest)):
            if not (nom_r.startswith('ranking_') and nom_r.endswith('.csv')):
                continue
            try:
                with open(os.path.join(dest, nom_r), encoding='utf-8') as fh:
                    filas = list(_csv.DictReader(fh))
                n = sum(1 for r in filas
                        if r.get('estado') in ('ATENCION', 'VIGILANCIA'))
                alertados = n if alertados is None else alertados + n
            except Exception:
                alertados = None      # no se inventa: queda None y el aviso lo dice
                break

        # CAMPO CHICO: un cliente `solo_focos` no emite ranking POR DISEÑO, asi que
        # `alertados` quedaba None SIEMPRE y el aviso caia invariablemente en la rama
        # "Hay entrega nueva" — sin numero, y sin poder decir nunca "esta ronda no
        # hay nada". Se cuentan los focos, que es lo que ese cliente entrega.
        if alertados is None:
            focos = [n for n in sorted(os.listdir(dest))
                     if n.startswith('focos_') and n.endswith('.geojson')]
            if focos:
                try:
                    total = 0
                    for nom_f in focos:
                        with open(os.path.join(dest, nom_f), encoding='utf-8') as fh:
                            gjf = json.load(fh)
                        total += len([f for f in gjf.get('features', [])
                                      if (f.get('properties') or {}).get('tipo')
                                      != 'perimetro'])
                    alertados = total
                except Exception:
                    alertados = None

        # FECHA DE LA IMAGEN, que NO es la fecha de la entrega.
        #
        # `fecha_entrega` es el dia en que corrio el motor: cambia TODOS LOS DIAS,
        # porque el cron corre todos los dias. La fecha de la ESCENA es la de la foto
        # que se uso, y con revisita de 5 dias —mas nubes— puede quedarse quieta una
        # semana o mas. Confundirlas tenia dos consecuencias, las dos malas:
        #   · el WhatsApp decia "Escena del 27/07" cuando la imagen era del 20/07;
        #   · cualquier freno de repeticion basado en `fecha_entrega` era inutil,
        #     porque ese campo cambia solo, sin que haya nada nuevo que mirar.
        fecha_img = None
        for nom_f in sorted(os.listdir(dest)):
            if not (nom_f.startswith('focos_') and nom_f.endswith('.geojson')):
                continue
            try:
                with open(os.path.join(dest, nom_f), encoding='utf-8') as fh:
                    gjf = json.load(fh)
                for f in gjf.get('features', []):
                    fi = (f.get('properties') or {}).get('fecha_img')
                    if fi and (fecha_img is None or str(fi) > fecha_img):
                        fecha_img = str(fi)
            except Exception:
                pass
        if fecha_img is None:
            for nom_r in sorted(os.listdir(dest)):
                if not (nom_r.startswith('ranking_') and nom_r.endswith('.csv')):
                    continue
                try:
                    with open(os.path.join(dest, nom_r), encoding='utf-8') as fh:
                        for fila in _csv.DictReader(fh):
                            fd = (fila.get('fecha_dato') or '')[:10]
                            if fd and (fecha_img is None or fd > fecha_img):
                                fecha_img = fd
                except Exception:
                    pass

        with open(os.path.join(dest, 'META.json'), 'w', encoding='utf-8') as fh:
            json.dump({'cliente': cliente, 'fecha_entrega': ultima,
                       'fecha_imagen': fecha_img,
                       'lotes_alertados': alertados,
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
