# -*- coding: utf-8 -*-
"""Aviso de WhatsApp POR CLIENTE, no uno global para todos.

    python scripts/avisar.py entregas

POR QUE HACIA FALTA
-------------------
El workflow mandaba UN aviso a UN numero (`WHATSAPP_PHONE`) para toda la corrida.
Con un cliente alcanzaba. Con varios, el operador recibe un mensaje que dice "hubo
entrega" sin saber de quien, tiene que abrir el repositorio para averiguarlo, y el
aviso pierde el unico valor que tenia: que se pueda actuar sin abrir nada.

Ahora cada cliente declara su numero en su ficha (`contacto.whatsapp`) y el mensaje
se arma con SUS numeros: cuantos lotes tiene para recorrer y de que fecha es la
escena.

SOBRE LA CLAVE DE CALLMEBOT — leer antes de configurar
------------------------------------------------------
CallMeBot NO permite mandarle a cualquier numero: **cada destinatario tiene que
autorizar al bot y recibe SU PROPIA apikey**. O sea que mandarle directo al
productor exige una clave por productor. Y una apikey es un secreto: no puede vivir
en el JSON del cliente, que se commitea al repositorio.

Por eso:
  · la ficha del cliente declara SOLO el telefono (no es secreto);
  · la clave se busca en el entorno como `CALLMEBOT_<CLAVE_CLIENTE>` (un secreto de
    GitHub por cliente);
  · si esa clave NO esta, el aviso va al numero del ADMIN con la leyenda de a quien
    hay que reenviarlo. Eso NO es un parche: es el flujo real de hoy, donde el admin
    baja el GeoJSON y se lo pasa al tecnico por WhatsApp.

Nunca se manda a un numero sin su clave: CallMeBot lo rechazaria y el aviso se
perderia en silencio, que es peor que no tenerlo.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from pix_alerta import clientes as cl   # noqa: E402

API = 'https://api.callmebot.com/whatsapp.php'
TIMEOUT = 25


def _meta(base, clave):
    """Lo que se publico para ese cliente en la ultima corrida, o None."""
    ruta = os.path.join(base, clave, 'ultimo', 'META.json')
    if not os.path.exists(ruta):
        return None
    try:
        with open(ruta, encoding='utf-8') as fh:
            return json.load(fh)
    except Exception:
        return None


def _mensaje(c, meta):
    """Texto del aviso. Corto: se lee en la pantalla de bloqueo o no se lee."""
    fecha = (meta or {}).get('fecha_entrega') or 'sin fecha'
    n = (meta or {}).get('lotes_alertados')
    # CAMPO CHICO: lo que se entrega son manchas DENTRO del lote, no lotes enteros.
    # Decirle al productor "3 lotes para recorrer" cuando son 3 manchas de 0,4 ha en
    # un lote es mandar al tecnico a caminar el campo entero.
    arch = (meta or {}).get('archivos') or []
    acercamiento = (any(str(x).startswith('focos_') for x in arch)
                    and not any(str(x).startswith('ranking_') for x in arch))
    partes = ['PIXADVISOR — %s' % c.titulo, 'Escena del %s.' % fecha]
    if n is None:
        partes.append('Hay entrega nueva.')
    elif n == 0:
        # Un informe que dice "no hay nada" CONSERVA la confianza. Uno que se calla
        # deja al productor sin saber si el servicio corrio.
        partes.append('Se miro y no hay manchas para revisar esta ronda.'
                      if acercamiento else 'Ningun lote fuera de control esta ronda.')
    elif acercamiento:
        partes.append('%d mancha(s) dentro de los lotes para ir a mirar.' % n)
    else:
        partes.append('%d lote(s) para recorrer.' % n)
    partes.append('Informe y mapa de focos en la carpeta del cliente.')
    return ' '.join(partes)


def _enviar(telefono, apikey, texto, seco=False):
    url = '%s?%s' % (API, urllib.parse.urlencode(
        {'phone': telefono, 'text': texto, 'apikey': apikey}))
    if seco:
        print('    [SECO] no se envia nada')
        return True
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            r.read()
        return True
    except Exception as e:
        # Se avisa y se sigue: que falle el aviso de un cliente no puede impedir el
        # de los demas, y el entregable ya esta publicado igual.
        print('    [ERROR] no se pudo enviar: %s: %s' % (type(e).__name__, e))
        return False


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    base = argv[0] if argv else 'entregas'
    seco = '--seco' in argv or os.environ.get('AVISAR_SECO') == '1'

    admin_tel = os.environ.get('WHATSAPP_PHONE', '').strip()
    admin_key = os.environ.get('CALLMEBOT_APIKEY', '').strip()

    try:
        todos = cl.cargar_todos(solo_activos=True)
    except Exception as e:
        print('[ERROR] clientes mal declarados: %s' % e)
        return 1

    enviados, pendientes, sin_entrega = 0, [], 0
    for c in todos:
        meta = _meta(base, c.clave)
        if meta is None:
            sin_entrega += 1
            continue
        texto = _mensaje(c, meta)
        clave_env = 'CALLMEBOT_%s' % c.clave.upper()
        key_cli = os.environ.get(clave_env, '').strip()

        if c.whatsapp and key_cli:
            print('  %s -> %s (numero del cliente)' % (c.clave, c.whatsapp))
            if _enviar(c.whatsapp, key_cli, texto, seco):
                enviados += 1
        elif admin_tel and admin_key:
            destino = c.whatsapp or 'sin numero declarado'
            aviso = '%s [REENVIAR a %s: %s]' % (texto, c.titulo, destino)
            motivo = ('falta el secreto %s' % clave_env if c.whatsapp
                      else 'el cliente no declara whatsapp')
            print('  %s -> admin (%s)' % (c.clave, motivo))
            if _enviar(admin_tel, admin_key, aviso, seco):
                enviados += 1
            pendientes.append((c.clave, motivo))
        else:
            print('  %s -> NO SE AVISO: no hay numero del cliente ni del admin'
                  % c.clave)
            pendientes.append((c.clave, 'sin destino'))

    print('\n%d aviso(s) enviado(s) · %d cliente(s) sin entrega esta corrida'
          % (enviados, sin_entrega))
    if pendientes:
        print('Para que el aviso llegue directo al cliente, cargar el secreto:')
        for clave, motivo in pendientes:
            print('   CALLMEBOT_%s   (%s)' % (clave.upper(), motivo))
    # Que no se pueda avisar NO es motivo para marcar la corrida como fallida: el
    # entregable ya esta publicado y commiteado.
    return 0


if __name__ == '__main__':
    sys.exit(main())
