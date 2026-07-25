"""Capa de CLIENTES sobre los sitios. Alta de cliente = un archivo, cero codigo.

El motor ya trabajaba por sitio, pero el sitio no es la unidad de negocio: un cliente
puede tener varias haciendas, y dos clientes distintos no pueden compartir carpeta de
salida ni capacidad de scouting. Sin esta capa, dar de alta al segundo cliente era
forkear el repositorio (que es exactamente lo que pasa hoy con el pipeline de rasteres).

Un cliente se declara en `clientes/<clave>.json`:

    {
      "clave": "HDS",
      "titulo": "Hacienda del Senor",
      "activo": true,
      "K": 10,
      "sitios_ref": ["HDS"],
      "entrega": {"cadencia_dias": 10},
      "marca": {"nombre": "Pixadvisor", "color": "#0D9488"}
    }

`sitios_ref` reutiliza sitios ya definidos en config.py. Para una hacienda nueva se usa
`sitios` con la definicion completa y NO se toca ningun .py:

    "sitios": [{"clave": "SA", "titulo": "Santo Antonio",
                "lotes_geojson": "lotes/santo_antonio.geojson",
                "campo_id": "lote", "epsg_metrico": "EPSG:32721",
                "campanas": {"2026": ["2026-05-01", "2026-10-31"]}}]

Las rutas relativas se resuelven contra la carpeta del propio archivo de cliente, para
que un cliente sea una carpeta portable y no un conjunto de rutas absolutas del
Escritorio de alguien.

REGLA DE AISLAMIENTO: cada cliente escribe SOLO en `<salida>/<clave_cliente>/`. Un
entregable de un cliente que aparece en la carpeta de otro no es un bug de formato: es
mandarle a un productor los datos de su vecino.
"""
import dataclasses
import json
import os
from dataclasses import dataclass, field

from . import config as cfg

# Campos que el JSON puede setear en un Sitio. Cualquier otro es error: un typo como
# "epsg" en vez de "epsg_metrico" se aceptaria en silencio y el sitio saldria
# proyectado en la zona equivocada.
#
# Se DERIVA del dataclass, no se lista a mano. La lista escrita a mano se desincronizo
# apenas se agrego `cultivo` al Sitio: el alta de cliente lo escribia y el cargador lo
# rechazaba como campo desconocido. Un campo nuevo no tiene que acordarse de dos lugares.
CAMPOS_SITIO = {f.name for f in dataclasses.fields(cfg.Sitio)}
CAMPOS_CLIENTE = {
    'clave', 'titulo', 'activo', 'K', 'sitios', 'sitios_ref', 'entrega', 'marca', 'nota',
}
RUTAS_SITIO = ('lotes_geojson', 'unidades_csv')


@dataclass
class Cliente:
    clave: str
    titulo: str
    sitios: list = field(default_factory=list)
    K: int = None                  # capacidad de scouting declarada POR EL CLIENTE
    activo: bool = True
    entrega: dict = field(default_factory=dict)
    marca: dict = field(default_factory=dict)
    nota: str = ''
    origen: str = ''               # de que archivo salio, para poder auditarlo

    def salida(self, base):
        """Carpeta propia. Ver REGLA DE AISLAMIENTO en el encabezado."""
        return os.path.join(base, self.clave)


def _sitio_desde_dict(d, base_dir):
    extra = set(d) - CAMPOS_SITIO
    if extra:
        raise ValueError('campos desconocidos en el sitio %r: %s'
                         % (d.get('clave', '?'), ', '.join(sorted(extra))))
    faltan = {'clave', 'titulo', 'lotes_geojson', 'campo_id'} - set(d)
    if faltan:
        raise ValueError('al sitio %r le faltan campos obligatorios: %s'
                         % (d.get('clave', '?'), ', '.join(sorted(faltan))))
    d = dict(d)
    for k in RUTAS_SITIO:
        if d.get(k) and not os.path.isabs(d[k]):
            d[k] = os.path.normpath(os.path.join(base_dir, d[k]))
    # el JSON no tiene tuplas
    if 'categorias_excluidas' in d:
        d['categorias_excluidas'] = tuple(d['categorias_excluidas'])
    if 'campanas' in d:
        d['campanas'] = {k: tuple(v) for k, v in d['campanas'].items()}
    return cfg.Sitio(**d)


def cargar(ruta):
    """Lee un archivo de cliente. Falla ruidoso: un cliente mal declarado no corre."""
    with open(ruta, encoding='utf-8') as fh:
        d = json.load(fh)
    extra = set(d) - CAMPOS_CLIENTE
    if extra:
        raise ValueError('%s: campos desconocidos: %s' % (ruta, ', '.join(sorted(extra))))
    for k in ('clave', 'titulo'):
        if not d.get(k):
            raise ValueError('%s: falta "%s"' % (ruta, k))

    sitios = [_sitio_desde_dict(s, os.path.dirname(os.path.abspath(ruta)))
              for s in d.get('sitios', [])]
    for ref in d.get('sitios_ref', []):
        if ref not in cfg.SITIOS:
            raise ValueError('%s: sitios_ref apunta a "%s", que no existe. '
                             'Definilo en config.py o declaralo completo en "sitios".'
                             % (ruta, ref))
        sitios.append(cfg.SITIOS[ref])
    if not sitios:
        raise ValueError('%s: el cliente no tiene ningun sitio' % ruta)

    claves = [s.clave for s in sitios]
    if len(set(claves)) != len(claves):
        raise ValueError('%s: sitios repetidos dentro del cliente: %s' % (ruta, claves))

    K = d.get('K')
    if K is not None and (not isinstance(K, int) or K < 1):
        # K es la capacidad real de scouting del cliente, no un adorno: con K malo el
        # corte del ranking pierde sentido.
        raise ValueError('%s: K debe ser un entero >= 1, es %r' % (ruta, K))

    return Cliente(clave=d['clave'], titulo=d['titulo'], sitios=sitios, K=K,
                   activo=bool(d.get('activo', True)), entrega=d.get('entrega', {}),
                   marca=d.get('marca', {}), nota=d.get('nota', ''),
                   origen=os.path.abspath(ruta))


def cargar_todos(carpeta=None, solo_activos=True):
    """Todos los clientes declarados, ordenados por clave.

    Un archivo roto NO se saltea en silencio: si un cliente no se puede leer, o se corre
    sin el sabiendolo, o no se corre. Saltearlo callado significa que un cliente deja de
    recibir su informe y nadie se entera hasta que reclama.
    """
    carpeta = carpeta or os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'clientes')
    if not os.path.isdir(carpeta):
        return []
    out, errores = [], []
    for nom in sorted(os.listdir(carpeta)):
        if not nom.endswith('.json'):
            continue
        try:
            out.append(cargar(os.path.join(carpeta, nom)))
        except Exception as e:
            errores.append('%s: %s' % (nom, e))
    if errores:
        raise ValueError('clientes mal declarados:\n  - ' + '\n  - '.join(errores))

    claves = [c.clave for c in out]
    dup = {k for k in claves if claves.count(k) > 1}
    if dup:
        # Dos clientes con la misma clave comparten carpeta de salida: el informe de uno
        # pisa al del otro. Es fuga de datos entre clientes, no un choque de nombres.
        raise ValueError('clave de cliente repetida en mas de un archivo: %s'
                         % ', '.join(sorted(dup)))
    return [c for c in out if c.activo] if solo_activos else out


def registrar_sitios(clientes):
    """Mete los sitios declarados por archivo en cfg.SITIOS, para que `--sitio` los vea.

    Devuelve las claves agregadas. Un sitio de un cliente NO puede pisar a uno ya
    definido: se lanza error en vez de resolver por orden de lectura.
    """
    nuevas = []
    for c in clientes:
        for s in c.sitios:
            ya = cfg.SITIOS.get(s.clave)
            if ya is not None and ya is not s:
                raise ValueError('el sitio "%s" del cliente %s choca con otro ya '
                                 'definido. Usa una clave distinta.' % (s.clave, c.clave))
            if s.clave not in cfg.SITIOS:
                cfg.SITIOS[s.clave] = s
                nuevas.append(s.clave)
    return nuevas


def de_sitio(clave_sitio, clientes=None):
    """Que cliente es dueño de un sitio. None si ninguno lo declara."""
    for c in (clientes if clientes is not None else cargar_todos()):
        for s in c.sitios:
            if s.clave == clave_sitio:
                return c
    return None
