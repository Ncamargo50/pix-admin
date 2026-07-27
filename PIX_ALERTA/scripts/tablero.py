# -*- coding: utf-8 -*-
"""Tablero de operacion. Lo regenera la MAQUINA en cada corrida.

    python scripts/tablero.py entregas

Una sola pagina con el estado de todos los clientes: cuando fue la ultima entrega, que
trajo, y que hay que hacer. Se abre con doble clic, no necesita servidor ni internet.

POR QUE ASI Y NO UN PANEL WEB
-----------------------------
Un panel es codigo que hay que mantener, desplegar y arreglar cuando se rompe — y compite
por tiempo contra la campaña de octubre. Esta pagina la escribe el mismo cron que entrega,
asi que NO SE PUEDE DESACTUALIZAR: si dice algo, es lo que hay en el repositorio.

Cuando haya suficientes clientes para que un panel valga la pena, esto sigue siendo la
fuente de verdad y el panel se apoya arriba.

LO QUE MUESTRA A PROPOSITO
--------------------------
La ANTIGUEDAD de cada entrega, en dias. Un tablero que solo muestra la ultima entrega sin
decir de cuando es deja creer que todo esta al dia cuando hace tres semanas que no entra
una escena limpia.
"""
import html
import json
import os
import sys
from datetime import date, datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Cadencia declarada: pasado esto sin entregar, algo hay que mirar.
DIAS_AVISO, DIAS_ALARMA = 14, 30


def _dias(fecha):
    try:
        d = (date.today() - date.fromisoformat(str(fecha)[:10])).days
    except Exception:
        return None
    # Una entrega con fecha futura (un `--hasta` mal puesto, el reloj del runner)
    # imprimia "hace -1 dias". No es una entrega mas fresca que hoy: es un dato raro.
    return max(d, 0)


def _clientes():
    sys.path.insert(0, RAIZ)
    from pix_alerta import clientes as cl
    try:
        return cl.cargar_todos(solo_activos=False)
    except Exception:
        return []


def _estado(base, c):
    """Lo que hay entregado para un cliente, leido del disco."""
    d = os.path.join(base, c.clave, 'ultimo')
    e = {'clave': c.clave, 'titulo': c.titulo, 'activo': c.activo,
         'K': c.K, 'sitios': [s.clave for s in c.sitios],
         'fecha': None, 'dias': None, 'archivos': [], 'alertados': None,
         'atencion': 0, 'vigilancia': 0, 'sin_dato': 0, 'lotes': None,
         'error': None}
    meta = os.path.join(d, 'META.json')
    if os.path.exists(meta):
        try:
            m = json.load(open(meta, encoding='utf-8'))
            e['fecha'] = m.get('fecha_entrega')
            e['dias'] = _dias(e['fecha'])
            e['archivos'] = m.get('archivos', [])
        except Exception:
            pass
    # UN ranking POR PROPIEDAD, y se SUMAN. Antes se leia un `ranking.csv` fijo que
    # `publicar_ultimo` ya no escribe (publica `ranking_<SITIO>.csv`), el
    # `except: pass` se tragaba el FileNotFoundError y el tablero mostraba CEROS EN
    # VERDE con lotes alertados de verdad. Medido: 4 ATENCION + 6 VIGILANCIA
    # publicados y el tablero decia "Ningun lote sale de control".
    rankings = sorted(n for n in os.listdir(d)
                      if n.startswith('ranking_') and n.endswith('.csv')) \
        if os.path.isdir(d) else []
    leidos, rotos = 0, []
    for nom in rankings:
        try:
            import pandas as pd
            r = pd.read_csv(os.path.join(d, nom))
            # Un ranking SIN columna `estado` no es un ranking con cero alertados: es
            # un archivo que no se puede interpretar. El guard `else 0` evitaba el
            # crash eligiendo la rama TRANQUILIZADORA, que es justo lo que el resto
            # de este modulo esta construido para no hacer. Va a `rotos`.
            if 'estado' not in r.columns:
                raise KeyError('sin columna estado')
            e['lotes'] = (e['lotes'] or 0) + len(r)
            for k, col in (('atencion', 'ATENCION'), ('vigilancia', 'VIGILANCIA'),
                           ('sin_dato', 'SIN DATO')):
                e[k] += int((r['estado'] == col).sum())
            leidos += 1
        except Exception as ex:
            rotos.append('%s (%s)' % (nom, type(ex).__name__))
    if leidos:
        e['alertados'] = e['atencion'] + e['vigilancia']
    # Un ranking ilegible NO puede quedar como cero silencioso: el tablero existe
    # para decir si hay a donde ir, y un cero falso en verde es lo peor que puede
    # mostrar. Se deja `alertados=None` y el semaforo lo trata como dato ausente.
    if rotos:
        e['alertados'] = None
        e['error'] = 'ranking ilegible: ' + ', '.join(rotos)
        print('  [AVISO] %s: %s' % (e.get('clave', '?'), e['error']))
    elif not rankings and e['fecha'] is not None:
        # CAMPO CHICO: un sitio `solo_focos` no emite ranking POR DISEÑO —no tiene
        # cohorte y no la va a tener— y entrega focos. Avisar "falta el ranking"
        # todos los dias sobre un cliente que esta entregando bien es la forma de
        # que el aviso se deje de leer, y el dia que falte de verdad tampoco se lea.
        focos = sorted(n for n in os.listdir(d)
                       if n.startswith('focos_') and n.endswith('.geojson')) \
            if os.path.isdir(d) else []
        n_focos = 0
        for nom in focos:
            try:
                gj = json.load(open(os.path.join(d, nom), encoding='utf-8'))
                n_focos += len([f for f in gj.get('features', [])
                                if (f.get('properties') or {}).get('tipo') != 'perimetro'])
            except Exception as ex:
                focos, n_focos = [], 0
                e['error'] = 'focos ilegibles: %s (%s)' % (nom, type(ex).__name__)
                print('  [AVISO] %s: %s' % (e.get('clave', '?'), e['error']))
                break
        if focos and not e.get('error'):
            # `alertados` es lo que mira el semaforo. Aca son focos, no lotes: se
            # rotula para que nadie lea "3 lotes alertados" donde hay 3 manchas.
            e['alertados'] = n_focos
            e['modo'] = 'acercamiento'
            e['nota'] = ('%d foco(s) intra-lote. Este cliente no emite ranking entre '
                         'lotes: el campo no llega a la cohorte minima.' % n_focos)
        elif not e.get('error'):
            e['alertados'] = None
            e['error'] = 'entrega publicada sin ranking_*.csv ni focos_*.geojson'
            print('  [AVISO] %s: %s' % (e.get('clave', '?'), e['error']))
    return e


def _semaforo(e):
    if not e['activo']:
        return 'off', 'inactivo'
    if e['fecha'] is None:
        return 'mal', 'nunca entrego'
    if e['dias'] is None:
        return 'aviso', 'fecha ilegible'
    if e['dias'] > DIAS_ALARMA:
        return 'mal', 'hace %d dias' % e['dias']
    if e['dias'] > DIAS_AVISO:
        return 'aviso', 'hace %d dias' % e['dias']
    return 'bien', 'hace %d dias' % e['dias']


CSS = """
:root{--ok:#1B7A1B;--av:#B4740A;--mal:#B4322A;--teal:#0D9488;--azul:#1E40AF;
 --ink:#11201F;--ink2:#4A625E;--line:#DCE4E2;--bg:#F7F9F9;--card:#fff}
@media(prefers-color-scheme:dark){:root{--ink:#E5EFED;--ink2:#9DB4B0;--line:#22322F;
 --bg:#0B1413;--card:#111D1C;--teal:#2FBFB0;--azul:#7C9BF5;--ok:#8CC85E;--av:#DFA33C;--mal:#E8776C}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 "Segoe UI",system-ui,sans-serif}
.w{max-width:60rem;margin:0 auto;padding:0 1.4rem 4rem}
header{padding:2.4rem 0 1.2rem;border-bottom:2px solid var(--ink)}
h1{font-size:1.9rem;letter-spacing:-.02em;margin:0 0 .3rem}
.sub{color:var(--ink2);margin:0;font-size:.92rem}
.mono{font-family:ui-monospace,Consolas,monospace;font-size:.78rem}
.cli{background:var(--card);border:1px solid var(--line);margin-top:1.1rem}
.cli-h{display:flex;align-items:center;gap:.7rem;padding:.85rem 1.1rem;border-bottom:1px solid var(--line);flex-wrap:wrap}
.dot{width:.7rem;height:.7rem;border-radius:50%;flex:none}
.bien{background:var(--ok)}.aviso{background:var(--av)}.mal{background:var(--mal)}.off{background:#8a9a97}
.cli-t{font-weight:650;font-size:1.05rem}
.cli-m{color:var(--ink2);font-size:.8rem;margin-left:auto;font-family:ui-monospace,Consolas,monospace}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(8rem,1fr));gap:1px;background:var(--line)}
.c{background:var(--card);padding:.7rem .9rem}
.c b{display:block;font-size:1.35rem;line-height:1.2;font-variant-numeric:tabular-nums}
.c span{font-size:.76rem;color:var(--ink2)}
.at b{color:var(--mal)}.vi b{color:var(--av)}.sd b{color:var(--ink2)}
.arch{padding:.7rem 1.1rem;font-size:.82rem;color:var(--ink2);border-top:1px solid var(--line)}
.arch code{background:var(--bg);border:1px solid var(--line);padding:.05em .35em;font-size:.95em}
.acc{padding:.75rem 1.1rem;border-top:1px solid var(--line);font-size:.86rem;
 background:color-mix(in srgb,var(--av) 10%,transparent);border-left:3px solid var(--av)}
.acc.ok{background:color-mix(in srgb,var(--ok) 9%,transparent);border-left-color:var(--ok)}
footer{margin-top:2.5rem;padding-top:1.1rem;border-top:1px solid var(--line);
 color:var(--ink2);font-size:.82rem}
"""


def generar(base, salida=None):
    cs = _clientes()
    ests = [_estado(base, c) for c in cs]
    salida = salida or os.path.join(base, 'TABLERO.html')
    E = html.escape
    hoy = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    P = ['<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
         '<title>Pixadvisor Monitor — tablero</title>', '<style>%s</style>' % CSS,
         '<div class="w"><header><h1>Pixadvisor Monitor</h1>',
         '<p class="sub">Estado de la operacion · generado por la maquina el %s</p>' % E(hoy),
         '</header>']

    if not ests:
        P.append('<div class="cli"><div class="acc">No hay clientes declarados. '
                 'Dar de alta con <code>python -m pix_alerta.alta_cliente</code>.</div></div>')

    for e in ests:
        cls, txt = _semaforo(e)
        P.append('<div class="cli"><div class="cli-h">'
                 '<span class="dot %s"></span><span class="cli-t">%s</span>'
                 '<span class="mono">%s</span>'
                 '<span class="cli-m">ultima entrega: %s</span></div>'
                 % (cls, E(e['titulo']), E(e['clave']), E(txt)))
        if e['fecha'] and e.get('modo') == 'acercamiento':
            # Campo chico: los contadores del ranking son cero POR DISEÑO, no porque
            # el campo este tranquilo. Mostrarlos como "0 en atencion" al lado de 3
            # focos reales es un cero falso en verde, que es justo lo que este
            # tablero existe para no hacer.
            P.append('<div class="grid">'
                     '<div class="c at"><b>%d</b><span>focos intra-lote</span></div>'
                     '<div class="c"><b>%s</b><span>escena</span></div></div>'
                     % (e['alertados'] or 0, E(str(e['fecha']))))
            P.append('<div class="arch">Este cliente NO emite ranking entre lotes: '
                     'el campo no llega a la cohorte minima. El producto es el '
                     'acercamiento dentro del lote.</div>')
        elif e['fecha']:
            P.append('<div class="grid">'
                     '<div class="c at"><b>%d</b><span>en atencion</span></div>'
                     '<div class="c vi"><b>%d</b><span>en vigilancia</span></div>'
                     '<div class="c sd"><b>%d</b><span>sin observacion</span></div>'
                     '<div class="c"><b>%s</b><span>escena</span></div></div>'
                     % (e['atencion'], e['vigilancia'], e['sin_dato'], E(str(e['fecha']))))
            if e['archivos']:
                P.append('<div class="arch">Para mandar por WhatsApp: '
                         + ' '.join('<code>%s</code>' % E(a) for a in e['archivos'])
                         + '<br>en <code>entregas/%s/ultimo/</code></div>' % E(e['clave']))
        # La accion concreta, no un estado abstracto.
        if not e['activo']:
            acc, ok = 'Cliente inactivo: no entra en la corrida.', False
        elif e['fecha'] is None:
            acc, ok = ('Todavia no entrego nada. Correr el workflow a mano con una fecha '
                       'DENTRO de la campaña declarada.'), False
        elif e['dias'] and e['dias'] > DIAS_ALARMA:
            acc, ok = ('Hace %d dias que no entrega. Revisar la pestaña Actions: puede ser '
                       'nubes persistentes (normal) o el cron fallando (no).' % e['dias']), False
        elif e.get('error'):
            # NUNCA decir "no hay nada" cuando no se pudo leer. Un cero falso en
            # verde es lo peor que puede mostrar un tablero de operacion.
            acc, ok = ('<b>No se pudo leer el ranking publicado</b> (%s). El numero de '
                       'lotes para recorrer es DESCONOCIDO, no cero: abrir la carpeta '
                       'del cliente antes de dar por buena la corrida.'
                       % E(e['error'])), False
        elif e['alertados'] and e.get('modo') == 'acercamiento':
            acc, ok = ('Mandar <code>%s</code> por WhatsApp. %d mancha(s) DENTRO de los '
                       'lotes para ir a mirar (no son lotes enteros).'
                       % (E(e['archivos'][0]) if e['archivos'] else 'el GeoJSON',
                          e['alertados'])), True
        elif e['alertados']:
            acc, ok = ('Mandar <code>%s</code> por WhatsApp. %d lote(s) para recorrer.'
                       % (E(e['archivos'][0]) if e['archivos'] else 'el GeoJSON',
                          e['alertados'])), True
        elif e.get('modo') == 'acercamiento':
            acc, ok = ('Se miro y no hay manchas sobre la unidad minima. '
                       'No hay a donde mandar al tecnico.'), True
        else:
            acc, ok = 'Ningun lote sale de control. No hay a donde mandar al tecnico.', True
        P.append('<div class="acc%s">%s</div></div>' % (' ok' if ok else '', acc))

    P.append('<footer>Esta pagina la escribe el mismo proceso que entrega, en cada corrida: '
             'si dice algo, es lo que hay en el repositorio. '
             '<b>Los dias son de la ULTIMA ENTREGA</b>, no de la ultima corrida — con nubes '
             'persistentes la maquina corre todos los dias y no entrega, y eso es correcto.'
             '</footer></div>')

    os.makedirs(os.path.dirname(salida) or '.', exist_ok=True)
    with open(salida, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(P))
    return salida, ests


if __name__ == '__main__':
    base = sys.argv[1] if len(sys.argv) > 1 else 'entregas'
    ruta, ests = generar(base)
    print('Tablero -> %s (%d cliente(s))' % (ruta, len(ests)))
    for e in ests:
        print('  %-8s %-26s %s' % (e['clave'], e['titulo'], _semaforo(e)[1]))
