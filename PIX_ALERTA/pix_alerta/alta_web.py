# -*- coding: utf-8 -*-
"""Pantalla de cadastro de clientes. Corre en tu PC, se abre en el navegador.

    python -m pix_alerta.alta_web

Es la misma alta que `alta_cliente`, con formulario en vez de banderas. Usa EXACTAMENTE
la misma validacion: no hay dos caminos que puedan diverger.

POR QUE LOCAL Y NO UN PANEL EN INTERNET
---------------------------------------
El cadastro se hace una vez por cliente y desde tu maquina, que es donde estan los
archivos que manda el cliente. Un panel hosteado obligaria a subir la geometria del
campo a un servidor, autenticar, y mantener eso andando — para una operacion que hacen
una persona y cinco clientes. Esto no necesita internet ni cuenta.

Al terminar deja el cliente escrito en el repo y te dice el comando para publicarlo.
"""
import html
import io
import os
import sys
import tempfile
import threading
import webbrowser
from email.parser import BytesParser
from email.policy import HTTP
from http.server import BaseHTTPRequestHandler, HTTPServer


def _multipart(headers, cuerpo):
    """Parsea multipart/form-data sin `cgi`, que Python 3.13 removio.

    Devuelve (campos, archivos) donde archivos es {nombre: (filename, bytes)}.
    Se usa `email`, que es stdlib y no se va a ir a ningun lado.
    """
    crudo = (b'Content-Type: ' + headers['Content-Type'].encode() +
             b'\r\nMIME-Version: 1.0\r\n\r\n' + cuerpo)
    msg = BytesParser(policy=HTTP).parsebytes(crudo)
    campos, archivos = {}, {}
    for parte in msg.iter_parts() if msg.is_multipart() else []:
        disp = parte.get('Content-Disposition', '')
        nombre = parte.get_param('name', header='Content-Disposition')
        if not nombre:
            continue
        fn = parte.get_param('filename', header='Content-Disposition')
        datos = parte.get_payload(decode=True) or b''
        if fn:
            archivos[nombre] = (os.path.basename(fn), datos)
        else:
            campos[nombre] = datos.decode('utf-8', 'replace').strip()
    return campos, archivos

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from pix_alerta.alta_cliente import CULTIVOS, leer_lotes, main as alta_main  # noqa: E402

CSS = """
:root{--teal:#0D9488;--azul:#1E40AF;--lima:#5DBB2E;--mal:#B4322A;--av:#B4740A;
 --ink:#11201F;--ink2:#4A625E;--line:#DCE4E2;--bg:#F7F9F9;--card:#fff}
@media(prefers-color-scheme:dark){:root{--ink:#E5EFED;--ink2:#9DB4B0;--line:#22322F;
 --bg:#0B1413;--card:#111D1C;--teal:#2FBFB0;--azul:#7C9BF5;--mal:#E8776C;--av:#DFA33C}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 "Segoe UI",system-ui,sans-serif}
.w{max-width:44rem;margin:0 auto;padding:0 1.3rem 4rem}
header{padding:2.2rem 0 1rem;border-bottom:2px solid var(--ink);margin-bottom:1.4rem}
h1{font-size:1.7rem;margin:0 0 .25rem;letter-spacing:-.02em}
.sub{color:var(--ink2);margin:0;font-size:.92rem}
fieldset{border:1px solid var(--line);background:var(--card);margin:0 0 1rem;padding:1rem 1.2rem}
legend{font-weight:650;color:var(--teal);padding:0 .4rem;font-size:.95rem}
label{display:block;margin:.7rem 0 .2rem;font-size:.87rem;font-weight:600}
.hint{font-weight:400;color:var(--ink2);font-size:.8rem;display:block;margin-top:.15rem}
input,select{width:100%;padding:.5rem .6rem;border:1px solid var(--line);background:var(--bg);
 color:var(--ink);font:inherit;font-size:.92rem}
.row{display:flex;gap:.8rem}.row>*{flex:1}
button{background:var(--lima);color:#08140A;border:0;padding:.7rem 1.4rem;font:inherit;
 font-weight:650;cursor:pointer;font-size:1rem}
button.sec{background:transparent;color:var(--ink2);border:1px solid var(--line)}
.msg{padding:1rem 1.2rem;border-left:4px solid;margin-bottom:1.2rem;background:var(--card)}
.ok{border-color:var(--lima)}.err{border-color:var(--mal)}.av{border-color:var(--av)}
.msg h3{margin:0 0 .5rem;font-size:1rem}
.msg ul{margin:.4rem 0 0;padding-left:1.2rem}
code{background:var(--bg);border:1px solid var(--line);padding:.08em .35em;font-family:ui-monospace,Consolas,monospace;font-size:.86em}
pre{background:var(--bg);border:1px solid var(--line);padding:.7rem .9rem;overflow-x:auto;font-size:.82rem}
"""


def _pagina(cuerpo, msg=''):
    return ("""<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pixadvisor — cadastro de cliente</title><style>%s</style>
<div class="w"><header><h1>Cadastro de cliente</h1>
<p class="sub">La propiedad, los lotes y el cultivo. Despues de esto la maquina corre sola.</p>
</header>%s%s</div>""" % (CSS, msg, cuerpo))


FORM = """
<form method="post" enctype="multipart/form-data">
 <fieldset><legend>Cliente</legend>
  <div class="row">
   <div><label>Clave <span class="hint">Corto, MAYUSCULAS. Da nombre a su carpeta de entregas.</span>
    <input name="clave" required pattern="[A-Z][A-Z0-9_]{1,15}" placeholder="CERRO"></label></div>
   <div><label>Nombre <span class="hint">Como va en el informe del cliente.</span>
    <input name="titulo" required placeholder="Cerro Alto"></label></div>
  </div>
 </fieldset>

 <fieldset><legend>Los lotes</legend>
  <label>Archivo de lotes <span class="hint">KMZ, KML, SHP (zip), GeoJSON o GPKG — lo que mande el cliente.</span>
   <input type="file" name="lotes" required accept=".kmz,.kml,.shp,.geojson,.json,.gpkg,.zip"></label>
  <label>Columna con el identificador del lote
   <span class="hint">El nombre del lote dentro del archivo. Si no sabes cual es, mandalo igual: te va a decir cuales hay.</span>
   <input name="campo_id" value="lote"></label>
  <label>Sistema de coordenadas metrico de la zona
   <span class="hint">Para medir areas. Santa Cruz: EPSG:32720 · Parana/SP: EPSG:31981 · Mato Grosso: EPSG:31981</span>
   <input name="epsg" value="EPSG:32720"></label>
 </fieldset>

 <fieldset><legend>Cultivo y campaña</legend>
  <label>Cultivo <span class="hint">Define que banco de fichas abre la app para diagnosticar.</span>
   <select name="cultivo">%s</select></label>
  <div class="row">
   <div><label>La campaña arranca <input type="date" name="desde" required></label></div>
   <div><label>y termina <input type="date" name="hasta" required></label></div>
  </div>
  <span class="hint">Fuera de esta ventana el motor no emite: en madurez el cultivo se seca y
   senesce, que es la misma firma que busca el criterio, y no puede distinguir cosecha de deterioro.</span>
  <label>Lotes que el cliente puede recorrer por vez (K)
   <span class="hint">Su capacidad real de scouting. Es donde se corta la lista.</span>
   <input type="number" name="K" min="1" value="10"></label>
 </fieldset>

 <button type="submit">Dar de alta</button>
</form>
"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _html(self, s, code=200):
        b = s.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        opts = ''.join('<option value="%s">%s</option>' % (c, c.replace('_', ' '))
                       for c in CULTIVOS)
        self._html(_pagina(FORM % opts))

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        campos, archivos = _multipart(self.headers, self.rfile.read(n))
        g = lambda k, d='': campos.get(k, d) or d
        opts = ''.join('<option value="%s"%s>%s</option>'
                       % (c, ' selected' if c == g('cultivo') else '', c.replace('_', ' '))
                       for c in CULTIVOS)

        # El archivo subido va a un temporal: la validacion es la MISMA de alta_cliente.
        if 'lotes' not in archivos or not archivos['lotes'][1]:
            return self._html(_pagina(FORM % opts,
                                      _msg('err', 'Falta el archivo de lotes.')))
        fn, datos = archivos['lotes']
        tmp = os.path.join(tempfile.gettempdir(), fn)
        with open(tmp, 'wb') as fh:
            fh.write(datos)

        argv = ['--clave', g('clave'), '--titulo', g('titulo'), '--lotes', tmp,
                '--campo-id', g('campo_id', 'lote'), '--cultivo', g('cultivo', 'soya'),
                '--epsg', g('epsg', 'EPSG:32720'), '--forzar']
        if g('desde') and g('hasta'):
            argv += ['--campana', '%s/%s' % (g('desde')[:4], g('hasta')[:4]),
                     g('desde'), g('hasta')]
        if g('K'):
            argv += ['--K', g('K')]

        buf = io.StringIO()
        viejo = sys.stdout
        sys.stdout = buf
        try:
            rc = alta_main(argv)
        except SystemExit as e:
            rc, _ = 1, buf.write('\n%s' % e)
        except Exception as e:
            rc = 1
            buf.write('\n[ERROR] %s: %s' % (type(e).__name__, e))
        finally:
            sys.stdout = viejo
        salida = buf.getvalue()
        try:
            os.remove(tmp)
        except Exception:
            pass

        if rc == 0:
            m = _msg('ok', 'Cliente dado de alta', salida,
                     'Ya podes publicarlo. Desde la carpeta del workspace:',
                     'bash PIX_ALERTA/scripts/publicar_repo.sh')
        else:
            m = _msg('err', 'No se dio de alta', salida,
                     'Corregi lo de arriba y volve a mandar el archivo. Estos errores no '
                     'fallan ahora: fallan dentro de la corrida programada, semanas '
                     'despues, sin nadie mirando.')
        self._html(_pagina(FORM % opts, m))


def _msg(tipo, titulo, detalle='', nota='', cmd=''):
    p = ['<div class="msg %s"><h3>%s</h3>' % (tipo, html.escape(titulo))]
    if detalle:
        p.append('<pre>%s</pre>' % html.escape(detalle.strip()))
    if nota:
        p.append('<p>%s</p>' % html.escape(nota))
    if cmd:
        p.append('<pre>%s</pre>' % html.escape(cmd))
    p.append('</div>')
    return ''.join(p)


def main():
    puerto = int(os.environ.get('PIX_ALTA_PORT', '8777'))
    srv = HTTPServer(('127.0.0.1', puerto), H)
    url = 'http://127.0.0.1:%d/' % puerto
    print('Cadastro de clientes abierto en %s' % url)
    print('(solo en esta maquina — no queda expuesto a la red)')
    print('Ctrl+C para cerrar.')
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\nCerrado.')


if __name__ == '__main__':
    main()
