# -*- coding: utf-8 -*-
"""Hoja de ruta imprimible para la ronda de campo. El respaldo de papel del telefono.

POR QUE EN PAPEL, SI YA ESTA LA APP
-----------------------------------
Porque el telefono se queda sin bateria, pierde senal en el lote o simplemente falla, y
una ronda perdida por eso cuesta la unica ventana de imagen limpia que hubo en dos
semanas. La hoja lleva las coordenadas, el orden y espacio para anotar a mano; despues se
carga en la app.

    python -u -m scripts.hoja_de_ruta --entrada "C:/.../PARA_EL_TELEFONO" --salida ruta.pdf

⚠️ LA HOJA ES CIEGA, IGUAL QUE EL PAQUETE DIGITAL
-------------------------------------------------
No dice cual punto marco el satelite y cual es control. Si lo dijera, el tecnico buscaria
mas donde espera encontrar y la ronda mediria su expectativa en vez del motor — que es
exactamente el sesgo de verificacion que la campaña entera existe para evitar.

Por eso lee **solo** los `validacion_*.geojson`. Nunca los `CLAVE_*.json`, y si alguien le
pasa uno por error, lo rechaza.
"""
import argparse
import glob
import json
import os
import sys


def _centro(geom):
    """(lat, lon) del centro del punto. Es adonde lleva el GPS."""
    t, c = geom.get('type'), geom.get('coordinates')
    if t == 'Point':
        return float(c[1]), float(c[0])
    anillo = c[0] if t == 'Polygon' else c[0][0]
    pts = [p for p in anillo if isinstance(p, (list, tuple)) and len(p) >= 2]
    return (sum(float(p[1]) for p in pts) / len(pts),
            sum(float(p[0]) for p in pts) / len(pts))


def _gms(dec, pos, neg):
    """Grados decimales -> grados/minutos/segundos. Muchos GPS de mano piden GMS."""
    h = pos if dec >= 0 else neg
    dec = abs(dec)
    g = int(dec)
    m_f = (dec - g) * 60
    m = int(m_f)
    s = (m_f - m) * 60
    return "%d°%02d'%05.2f\" %s" % (g, m, s, h)


def leer(carpeta):
    """Puntos de todos los validacion_*.geojson de la carpeta."""
    filas = []
    archivos = sorted(glob.glob(os.path.join(carpeta, 'validacion_*.geojson')))
    if not archivos:
        raise SystemExit('no hay validacion_*.geojson en %s' % carpeta)
    for ruta in archivos:
        if 'CLAVE' in os.path.basename(ruta).upper():
            raise SystemExit('ese archivo es una CLAVE y no puede entrar acá: %s' % ruta)
        with open(ruta, encoding='utf-8') as fh:
            gj = json.load(fh)
        for f in gj['features']:
            p = f['properties']
            if p.get('tipo') == 'perimetro':
                continue
            # Defensa en profundidad: si algun dia un campo revelador se cuela en el
            # paquete, la hoja no lo imprime igual.
            for prohibido in ('clase', 'sev', 'z_sev', 'nivel', 'estrato'):
                if p.get(prohibido) is not None:
                    raise SystemExit(
                        'el punto %s trae `%s`, que revela la clase. El paquete ciego '
                        'esta roto: revisar controles.CAMPOS_DEL_PUNTO'
                        % (p.get('id'), prohibido))
            lat, lon = _centro(f['geometry'])
            filas.append({
                'id': p.get('id'), 'etq': p.get('etiqueta'),
                'lote': p.get('lote_id'), 'hacienda': p.get('hacienda'),
                'cultivo': p.get('cultivo'), 'fecha_img': p.get('fecha_img'),
                'orden': p.get('orden') or 0, 'lat': lat, 'lon': lon,
            })
    return sorted(filas, key=lambda r: (r['hacienda'] or '', r['orden']))


def construir(filas, salida, logo):
    from reportlab.lib.units import cm
    from reportlab.platypus import Spacer

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'marca'))
    from pix_branding import Brand, LIMA        # noqa: E402

    B = Brand(logo=logo)
    st = []
    st += B.cover_filler()

    img = sorted({r['fecha_img'] for r in filas if r['fecha_img']})
    hac = sorted({r['hacienda'] for r in filas if r['hacienda']})
    cult = sorted({r['cultivo'] for r in filas if r['cultivo']})

    st += [B.kpi_strip([
        (str(len(filas)), 'puntos'),
        (str(len(hac)), 'propiedades'),
        (', '.join(img)[5:] if img else '—', 'imagen'),
        ((cult[0] or '—').capitalize() if cult else '—', 'cultivo'),
    ]), Spacer(1, 0.4 * cm)]

    st += [B.P('Cómo se usa esta hoja', 'H2')]
    st += [B.P(
        'Es el respaldo en papel del teléfono. Cargá la coordenada en el GPS, caminá '
        'hasta entrar en el punto y anotá lo que ves en la fila. Después se pasa a la '
        'app. <b>Anotá también cuando no encuentres nada</b>: «sin novedad» es un dato, '
        'y es el que permite saber si el motor está dejando pasar problemas.')]
    st += [Spacer(1, 0.3 * cm)]

    for h in hac:
        sub = [r for r in filas if r['hacienda'] == h]
        st += [B.sec(hac.index(h) + 1, h)]
        datos = [['#', 'Punto', 'Lote', 'Latitud, Longitud', 'GMS (para GPS de mano)']]
        for r in sub:
            # ⚠️ Solo el SUFIJO del lote. La propiedad ya es el titulo de la seccion, y
            # repetirla entera desborda la columna sobre la de coordenadas.
            #
            # La primera version comparaba el lote contra el nombre de la propiedad con
            # `startswith`, y fallaba: el titulo trae acento («São Francisco») y el
            # lote_id no («SAO_FRANCISCO-02»). Se toma el sufijo directo, sin comparar.
            lote = (r['lote'] or '').replace('_', ' ')
            lote = lote.rsplit('-', 1)[-1] if '-' in lote else lote
            datos.append([
                str(r['orden']), r['etq'], lote,
                '%.5f, %.5f' % (r['lat'], r['lon']),
                '%s   %s' % (_gms(r['lat'], 'S', 'S') if r['lat'] < 0
                             else _gms(r['lat'], 'N', 'N'),
                             _gms(r['lon'], 'E', 'W')),
            ])
        st += [B.tbl(datos, [0.9 * cm, 1.5 * cm, 1.6 * cm, 4.2 * cm, 6.8 * cm]),
               Spacer(1, 0.35 * cm)]

        st += [B.P('Para anotar en el campo', 'H2')]
        anot = [['Punto', '¿Encontró algo?', 'Qué / conteo', 'Hora']]
        for r in sub:
            # ⚠️ NO usar ☐ (U+2610): Helvetica/WinAnsi no lo tiene y ReportLab lo
            # sustituye por un CUADRADO NEGRO RELLENO — que en una casilla para tildar
            # se lee como "ya marcado". Paso al generar la primera version.
            anot.append([r['etq'], 'Si  (   )      No  (   )', '', ''])
        st += [B.tbl(anot, [1.6 * cm, 4.2 * cm, 6.2 * cm, 3.0 * cm]),
               Spacer(1, 0.5 * cm)]

    st += [B.P('Lo que esta hoja NO dice, y es a propósito', 'H2')]
    st += [B.P(
        'No indica cuáles puntos marcó el satélite y cuáles son de control. Si lo '
        'dijera, el recorrido buscaría más donde espera encontrar, y la ronda mediría '
        'esa expectativa en vez de medir el motor. La correspondencia está en un '
        'archivo aparte que se abre <b>después</b> de que vuelvan los registros.')]

    B.build(salida, st,
            cover_title='Hoja de ruta — ronda de campo',
            cover_subtitle='%s · imagen del %s'
                           % (' / '.join(hac), ', '.join(img) if img else '—'))
    return salida


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--entrada', required=True,
                    help='carpeta con los validacion_*.geojson')
    ap.add_argument('--salida', required=True, help='PDF a escribir')
    a = ap.parse_args(argv)

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo = os.path.join(raiz, 'marca', 'logo_pix_azulnegro_trim.png')

    filas = leer(a.entrada)
    construir(filas, a.salida, logo)
    print('%d punto(s) en %d propiedad(es) -> %s'
          % (len(filas), len({r['hacienda'] for r in filas}), a.salida))
    return 0


if __name__ == '__main__':
    sys.exit(main())
