"""Configuracion de sitios. Nada de esto va en el codigo del motor.

Agregar una hacienda = agregar una entrada aca. No se toca ningun otro archivo.
Es la correccion al hardcode del pipeline actual, donde el diccionario de haciendas
esta duplicado en tres modulos.
"""
from dataclasses import dataclass, field


@dataclass
class Sitio:
    clave: str
    titulo: str
    lotes_geojson: str
    campo_id: str                  # propiedad del GeoJSON que es el ID estable del lote
    campo_area: str = 'area_ha'
    # Cultivo del sitio, con la clave del banco de fichas de la app (soya, trigo, maiz,
    # sorgo, girasol, cana_de_azucar, pastura). Sin esto la app cae a su default 'trigo'
    # y abre el banco de TRIGO para diagnosticar una soya.
    cultivo: str = ''
    epsg_metrico: str = 'EPSG:32720'
    buffer_negativo_m: float = 5.0  # ESPECIFICACION.md paso 1 (JRC 10.3390/rs12142195)
    # Ventanas de campaña. Sin esto no hay cohorte ni trayectoria esperada.
    campanas: dict = field(default_factory=dict)
    # Filtro de unidades: el inventario de lotes trae pistas, montes y caminos.
    # Sin este filtro el ranking manda al tecnico a la pista de aterrizaje —
    # paso de verdad: "PISTA" (2,78 ha) salio primera en la corrida del 2026-05-06.
    unidades_csv: str = ''
    unidades_col_id: str = 'lote_id'
    unidades_col_cat: str = 'categoria'
    categorias_excluidas: tuple = ()


HDS = Sitio(
    clave='HDS',
    titulo='Hacienda del Señor',
    lotes_geojson=(r'C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS'
                   r'\Hacienda-Del-Senor\HACIENDA-DEL-SENOR-PIX-MUESTREO'
                   r'\HACIENDA_TODOS_LOTES_OVERVIEW.geojson'),
    campo_id='lote',
    cultivo='soya',
    epsg_metrico='EPSG:32720',
    campanas={'2025/2026': ('2025-10-01', '2026-04-30'),
              '2024/2025': ('2024-10-01', '2025-04-30'),
              '2023/2024': ('2023-10-01', '2024-04-30')},
    unidades_csv=(r'C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS'
                  r'\Hacienda-Del-Senor\04-Sacarosa-Sentinel2'
                  r'\clasificacion_lotes_2026-05-13.csv'),
    categorias_excluidas=('MONTE_FOREST', 'PASTO_O_COBERTURA', 'OTRO_REVISAR'),
)

SITIOS = {s.clave: s for s in [HDS]}


def unidades_validas(sitio):
    """IDs de lote que son cultivo. None si el sitio no declara filtro.

    Un lote que no esta en la clasificacion NO se incluye: si no se sabe que es,
    no se manda a nadie. Es preferible perder un lote a mandar al tecnico al monte.
    """
    if not sitio.unidades_csv:
        return None
    import pandas as pd
    d = pd.read_csv(sitio.unidades_csv, encoding='utf-8')
    ok = d[~d[sitio.unidades_col_cat].isin(sitio.categorias_excluidas)]
    return set(ok[sitio.unidades_col_id].astype(str))

# --- Parametros del criterio, todos declarados y todos barribles ---------------
# Dos ejes de dosel, no siete. Dimensionalidad efectiva medida de los 7 indices
# del motor v7: 1,87-2,40 (PIX_ALERTA/medicion/dimensionalidad_indices.py).
EJES = ('NDMI', 'PSRI')          # humedad de dosel, senescencia/pigmentos

# Calidad de observacion por lote y fecha. La etiqueta viaja DENTRO del dato:
# sin esto no se puede distinguir un falso negativo real de una dekada nublada.
UMBRAL_PLENO = 0.80
UMBRAL_PARCIAL = 0.40

# SCL a descartar: 3 = SOMBRA DE NUBE. El motor de produccion hoy no la excluye,
# y es el artefacto que mas se parece a un foco.
SCL_MALAS = [1, 3, 8, 9, 10, 11]
DILATAR_NUBE_PX = 2              # a 20 m = 40 m de dilatacion

# Compuerta de vegetacion por FVC, no por NDVI absoluto. Los extremos salen de la
# propia escena (p2/p98), no de una tabla: un umbral absoluto no transfiere.
FVC_MINIMA = 0.35
