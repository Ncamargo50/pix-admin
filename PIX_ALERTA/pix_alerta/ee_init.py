"""Inicializacion de Earth Engine que funciona TANTO en la PC como en la nube.

    from .ee_init import inicializar
    inicializar()

POR QUE EXISTE
--------------
El motor llamaba a `ee.Initialize()` a secas. En la maquina del usuario eso anda, porque
tiene su credencial personal guardada. En un runner de GitHub Actions NO hay credencial
personal, y la primera corrida real en la nube murio con:

    EEException: Please authorize access to your Earth Engine account by running
    earthengine authenticate

El servidor tiene que autenticarse con la CUENTA DE SERVICIO, cuya clave llega por el
secreto `GEE_SA_JSON` y el workflow deja en el archivo que apunta `GEE_SA_KEY`.

Es el tipo de defecto que solo aparece corriendo de verdad en la nube: en local todo
pasaba, incluido el chequeo de puesta en marcha.
"""
import json
import os

_LISTO = False


def inicializar(forzar=False):
    """Autentica contra Earth Engine. Devuelve como lo hizo, para poder declararlo.

    Orden: cuenta de servicio (nube) -> credencial local del usuario (PC). Si falla,
    lanza con un mensaje que dice QUE hacer, no solo que fallo.
    """
    global _LISTO
    import ee
    if _LISTO and not forzar:
        return 'ya inicializado'

    key = os.environ.get('GEE_SA_KEY', '').strip()
    if key and os.path.exists(key):
        try:
            with open(key, encoding='utf-8') as fh:
                sa = json.load(fh)
            correo = sa.get('client_email')
            if not correo:
                raise ValueError('el JSON no tiene client_email: no es una clave de '
                                 'cuenta de servicio')
            ee.Initialize(ee.ServiceAccountCredentials(correo, key))
            _LISTO = True
            return 'cuenta de servicio %s' % correo
        except Exception as e:
            # No se cae en silencio a la credencial local: en la nube no existe, y el
            # mensaje de "autenticate" no dice nada sobre la causa real.
            raise RuntimeError(
                'No se pudo autenticar con la cuenta de servicio (%s).\n'
                '  archivo: %s\n'
                '  %s: %s' % ('GEE_SA_KEY', key, type(e).__name__, e))

    if key:
        raise RuntimeError(
            'GEE_SA_KEY apunta a un archivo que no existe: %s\n'
            '  En la nube lo escribe el workflow desde el secreto GEE_SA_JSON.' % key)

    try:
        ee.Initialize()
        _LISTO = True
        return 'credencial local del usuario'
    except Exception as e:
        raise RuntimeError(
            'Earth Engine no esta autenticado.\n'
            '  En tu PC:    earthengine authenticate\n'
            '  En la nube:  cargar el secreto GEE_SA_JSON (ver ARRANQUE.md)\n'
            '  detalle: %s: %s' % (type(e).__name__, e))
