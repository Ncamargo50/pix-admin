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
import json
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

from pix_alerta import ciclos  # noqa: E402
from pix_alerta import clientes as cl  # noqa: E402
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
.cartera{border:1px solid var(--line);background:var(--card);padding:.8rem 1.1rem;margin-bottom:1.2rem}
.cartera summary{cursor:pointer;color:var(--teal)}
.cli{margin:.8rem 0 0}.cli h4{margin:0 0 .25rem;font-size:.95rem}
.cli ul{margin:.2rem 0 0;padding-left:1.1rem;font-size:.86rem;color:var(--ink2)}
.mono{font-family:ui-monospace,Consolas,monospace;font-size:.82em;color:var(--ink2)}
"""


def _cartera():
    """Lo que ya esta dado de alta, para no cadastrar dos veces ni pisar nada.

    Sin esta lista el operador no tiene forma de saber que clientes existen ni con
    que clave, y termina inventando una nueva — que es como un mismo campo entra
    dos veces con dos nombres.
    """
    try:
        todos = cl.cargar_todos(solo_activos=False)
    except Exception as e:
        return ('<div class="msg err"><h3>Hay clientes mal declarados</h3>'
                '<pre>%s</pre></div>' % html.escape(str(e)))
    if not todos:
        return ''
    filas = []
    for c in todos:
        props = ''.join(
            '<li><b>%s</b> <span class="mono">%s</span> · %s%s</li>'
            % (html.escape(s.titulo), html.escape(s.clave),
               html.escape(s.cultivo or 'sin cultivo'),
               ' · siembra %s' % html.escape(s.siembra) if s.siembra else '')
            for s in c.sitios)
        filas.append(
            '<div class="cli"><h4>%s <span class="mono">%s</span>%s</h4><ul>%s</ul></div>'
            % (html.escape(c.titulo), html.escape(c.clave),
               '' if c.activo else ' <em>(inactivo)</em>', props))
    return ('<details class="cartera" open><summary><b>Cartera actual</b> — %d '
            'cliente(s)</summary>%s<p class="hint">Para agregarle una propiedad a '
            'uno de estos, usa su misma clave y ponele otro nombre de propiedad.</p>'
            '</details>' % (len(todos), ''.join(filas)))


def _pagina(cuerpo, msg=''):
    return ("""<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pixadvisor — cadastro de cliente</title><style>%s</style>
<div class="w"><header><h1>Cadastro de cliente</h1>
<p class="sub">El cliente, sus propiedades y sus lotes. Despues de esto la maquina corre sola.</p>
</header>%s%s%s</div>""" % (CSS, _cartera(), msg, cuerpo))


FORM = """
<form method="post" enctype="multipart/form-data">
 <fieldset><legend>1 · El cliente</legend>
  <div class="row">
   <div><label>Clave <span class="hint">Corto, MAYUSCULAS. Da nombre a su carpeta de entregas.</span>
    <input name="clave" required pattern="[A-Z][A-Z0-9_]{1,15}" placeholder="CERRO"></label></div>
   <div><label>Nombre del cliente <span class="hint">Quien contrata. Encabeza el informe.
    Sus propiedades se cargan abajo, una por vez.</span>
    <input name="titulo" required placeholder="Cerro Alto"></label></div>
  </div>
  <div class="row">
   <div><label>Persona de contacto <input name="contacto" placeholder="Marcelo Aguilera"></label></div>
   <div><label>Documento <span class="hint">CNPJ, NIT o equivalente.</span>
    <input name="documento" placeholder="41.196.481/0001-30"></label></div>
  </div>
  <div class="row">
   <div><label>WhatsApp <span class="hint">Formato internacional. Es el numero al que el
     cron le manda el aviso a ESTE cliente.</span>
    <input name="whatsapp" placeholder="+59170000000"></label></div>
   <div><label>Email <input type="email" name="email" placeholder="cliente@ejemplo.com"></label></div>
  </div>
 </fieldset>

 <fieldset><legend>2 · La propiedad y sus lotes</legend>
  <label>Nombre de la propiedad
   <span class="hint">La hacienda. Un cliente puede tener varias: para agregar la
    segunda, repeti el alta con la MISMA clave de cliente y otro nombre de propiedad.
    Vacio = se llama como el cliente.</span>
   <input name="propiedad" placeholder="Los Angeles"></label>
  <label>Clave de la propiedad <span class="hint">Vacio = se deriva del nombre.
    Ponela a mano si dos haciendas tuyas empiezan igual: la derivada se recorta y
    dos nombres parecidos dan la MISMA clave.</span>
   <input name="sitio_clave" placeholder="CERRO_NORTE" pattern="[A-Z][A-Z0-9_]{1,31}"></label>
  <label><input type="checkbox" name="reemplazar" value="1" style="width:auto;margin-right:.4rem">
   Actualizar esta propiedad si ya existe
   <span class="hint">Sin esto, una propiedad repetida se rechaza en vez de pisarse.
    Las demas propiedades del cliente nunca se tocan.</span></label>
  <label>Archivo de lotes <span class="hint">KMZ, KML, SHP (zip), GeoJSON o GPKG — lo que mande el cliente.
   Entran todos de una vez, con su nombre y su area. Uno por propiedad.</span>
   <input type="file" name="lotes" required accept=".kmz,.kml,.shp,.geojson,.json,.gpkg,.zip"></label>
  <label>Columna con el identificador del lote
   <span class="hint">El nombre del lote dentro del archivo. Si no sabes cual es, mandalo igual: te va a decir cuales hay.</span>
   <input name="campo_id" value="lote"></label>
  <label>Sistema de coordenadas metrico de la zona
   <span class="hint">Para medir areas. Santa Cruz: EPSG:32720 · Parana/SP: EPSG:31981 · Mato Grosso: EPSG:31981</span>
   <input name="epsg" value="EPSG:32720"></label>
 </fieldset>

 <fieldset><legend>3 · Cultivo y cuanto se monitorea</legend>
  <div class="row">
   <div><label>Cultivo <span class="hint">Define que banco de fichas abre la app de campo.</span>
    <select name="cultivo" id="cultivo">%(opts)s</select></label></div>
   <div><label>Fecha de siembra <span class="hint">De aca sale sola la ventana.</span>
    <input type="date" name="siembra" id="siembra" required></label></div>
  </div>
  <div id="preview" class="msg av" style="margin:.9rem 0 0"><h3>Ventana de monitoreo</h3>
   <p id="pv">Elegi cultivo y fecha de siembra.</p></div>
  <label>Dias de ciclo <span class="hint">Solo si el cultivar no es el tipico. Vacio = el
    valor por defecto del cultivo.</span>
   <input type="number" name="ciclo_dias" id="ciclo" min="30" max="600" placeholder="por defecto"></label>
  <label>Lotes que el cliente puede recorrer por vez (K)
   <span class="hint">Su capacidad real de scouting. Es donde se corta la lista.</span>
   <input type="number" name="K" min="1" value="10"></label>
  <span class="hint">Fuera de la ventana el motor no emite: en madurez el cultivo se seca y
   senesce, que es la misma firma que busca el criterio, y no puede distinguir cosecha de deterioro.</span>
 </fieldset>

 <button type="submit">Dar de alta</button>
</form>
<script>
const CICLOS = %(ciclos)s;
function pv(){
  const c=document.getElementById('cultivo').value,
        s=document.getElementById('siembra').value,
        o=parseInt(document.getElementById('ciclo').value||'0',10),
        el=document.getElementById('pv');
  if(!s){el.textContent='Elegi cultivo y fecha de siembra.';return}
  const n=o>0?o:CICLOS[c];
  const d=new Date(s+'T00:00:00'); const f=new Date(d.getTime()+n*86400000);
  const iso=x=>x.toISOString().slice(0,10);
  el.innerHTML='Se monitorea del <b>'+iso(d)+'</b> al <b>'+iso(f)+'</b> ('+n+' dias de ciclo).';
}
for(const id of ['cultivo','siembra','ciclo'])
  document.getElementById(id).addEventListener('input',pv);
pv();
</script>
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

    def _form(self, sel=''):
        opts = ''.join('<option value="%s"%s>%s</option>'
                       % (c, ' selected' if c == sel else '', c.replace('_', ' '))
                       for c in CULTIVOS)
        # La tabla de ciclos viaja al navegador para que la vista previa de la
        # ventana sea la MISMA que va a calcular el servidor. Dos tablas distintas
        # es como el formulario empieza a mentir.
        return FORM % {'opts': opts,
                       'ciclos': json.dumps({c: ciclos.ciclo_dias(c)
                                             for c in CULTIVOS})}

    def do_GET(self):
        self._html(_pagina(self._form()))

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        campos, archivos = _multipart(self.headers, self.rfile.read(n))
        g = lambda k, d='': campos.get(k, d) or d
        form = self._form(g('cultivo'))

        # El archivo subido va a un temporal: la validacion es la MISMA de alta_cliente.
        if 'lotes' not in archivos or not archivos['lotes'][1]:
            return self._html(_pagina(form,
                                      _msg('err', 'Falta el archivo de lotes.')))
        fn, datos = archivos['lotes']
        tmp = os.path.join(tempfile.gettempdir(), fn)
        with open(tmp, 'wb') as fh:
            fh.write(datos)

        # OJO: NADA de --forzar. El panel lo mandaba siempre, y con eso dar de alta
        # la segunda hacienda de un cliente le BORRABA la primera sin decir nada.
        # Sin la bandera, el alta agrega la propiedad y conserva las demas.
        argv = ['--clave', g('clave'), '--titulo', g('titulo'), '--lotes', tmp,
                '--campo-id', g('campo_id', 'lote'), '--cultivo', g('cultivo', 'soya'),
                '--epsg', g('epsg', 'EPSG:32720')]
        if g('propiedad'):
            argv += ['--propiedad', g('propiedad')]
        if g('sitio_clave'):
            argv += ['--sitio-clave', g('sitio_clave')]
        if g('reemplazar'):
            argv += ['--reemplazar-propiedad']
        if g('siembra'):
            argv += ['--siembra', g('siembra')]
        if g('ciclo_dias'):
            argv += ['--ciclo-dias', g('ciclo_dias')]
        for flag, campo in (('--contacto', 'contacto'), ('--whatsapp', 'whatsapp'),
                            ('--email', 'email'), ('--documento', 'documento')):
            if g(campo):
                argv += [flag, g(campo)]
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
        self._html(_pagina(form, m))


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
