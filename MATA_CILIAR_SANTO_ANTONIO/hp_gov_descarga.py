# -*- coding: utf-8 -*-
"""Helper de an_11: descarga de capas de GOBIERNO adicionales para el bbox del proyecto.

Guarda todo en datos_externos/gov_pro/ con un log JSON (URL, fecha, n, campos, escala
declarada por el servicio). Politica TLS: NUNCA verify=False. Para *.pr.gov.br se usa el
bundle con la CA ICP-Brasil si existe (C:/certs/certifi_icpbrasil.pem); si no existe se
usa el bundle certifi por defecto (medido 2026-09-06: la cadena de geopr.iat.pr.gov.br y
geoserver.pr.gov.br valida con certifi, no hizo falta la CA extra).

Para car.gov.br (SICAR) el servidor solo negocia TLS con SECLEVEL=1 (cifrados legacy):
se relaja el nivel de seguridad de los cifrados, NO la verificacion del certificado.
"""
import json
import os
import ssl
import time

import requests
from requests.adapters import HTTPAdapter

from an_00_config import DATOS_EXT, log

GOV_PRO = os.path.join(DATOS_EXT, 'gov_pro')
os.makedirs(GOV_PRO, exist_ok=True)
LOG_JSON = os.path.join(GOV_PRO, '_download_log_gov_pro.json')

CA_ICP = 'C:/certs/certifi_icpbrasil.pem'
VERIFY_PR = CA_ICP if os.path.exists(CA_ICP) else True   # True = bundle certifi (nunca False)

BBOX_WGS84 = '-50.70,-23.52,-50.62,-23.45'   # xmin,ymin,xmax,ymax; mismo bbox que datos_externos/

IAT_REST = 'https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/%s/FeatureServer/%d'
ANA_REST = 'https://www.snirh.gov.br/arcgis/rest/services/SPR/%s/FeatureServer/%d'


class _LegacyTLS(HTTPAdapter):
    """Cifrados legacy (SECLEVEL=1) manteniendo la verificacion del certificado."""
    def init_poolmanager(self, *a, **k):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT:@SECLEVEL=1')
        ctx.options |= getattr(ssl, 'OP_LEGACY_SERVER_CONNECT', 0x4)
        k['ssl_context'] = ctx
        return super().init_poolmanager(*a, **k)


def sesion_legacy():
    s = requests.Session()
    s.mount('https://', _LegacyTLS())
    return s


def _leer_log():
    if os.path.exists(LOG_JSON):
        with open(LOG_JSON, encoding='utf-8') as f:
            return json.load(f)
    return {}


def _escribir_log(d):
    with open(LOG_JSON, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def arcgis_query_geojson(url_layer, nombre, verify=True, where='1=1', bbox=BBOX_WGS84,
                         timeout=180, reintentos=3, forzar=False):
    """Descarga (paginada) una capa ArcGIS REST FeatureServer como GeoJSON WGS84.

    Devuelve la ruta del archivo o None si el servicio no respondio.
    """
    destino = os.path.join(GOV_PRO, nombre + '.geojson')
    reg = _leer_log()
    if os.path.exists(destino) and not forzar and nombre in reg and reg[nombre].get('ok'):
        log('  [gov_pro] %s ya descargado (%d feats) - se reutiliza' % (nombre, reg[nombre]['n']))
        return destino
    meta = {}
    try:
        m = requests.get(url_layer, params={'f': 'json'}, timeout=timeout, verify=verify).json()
        meta = {'nombre_capa': m.get('name'), 'geometria': m.get('geometryType'),
                'descripcion': (m.get('description') or '')[:600],
                'copyright': m.get('copyrightText'), 'campos': [f['name'] for f in m.get('fields', [])],
                'maxRecordCount': m.get('maxRecordCount')}
    except Exception as e:
        log('  [gov_pro] %s: metadata no disponible (%s)' % (nombre, str(e)[:100]))
    feats, offset, paso = [], 0, min(int(meta.get('maxRecordCount') or 1000), 1000)
    ok = True
    while True:
        p = dict(where=where, geometry=bbox, geometryType='esriGeometryEnvelope', inSR=4326,
                 spatialRel='esriSpatialRelIntersects', outFields='*', outSR=4326, f='geojson',
                 resultOffset=offset, resultRecordCount=paso)
        r = None
        for i in range(reintentos):
            try:
                r = requests.get(url_layer + '/query', params=p, timeout=timeout, verify=verify)
                r.raise_for_status()
                break
            except Exception as e:
                log('  [gov_pro] %s intento %d: %s' % (nombre, i + 1, str(e)[:120]))
                time.sleep(3 * (i + 1))
        if r is None:
            ok = False
            break
        try:
            j = r.json()
        except Exception:
            log('  [gov_pro] %s: respuesta no JSON' % nombre); ok = False; break
        if 'error' in j:
            log('  [gov_pro] %s: error del servicio %s' % (nombre, j['error'])); ok = False; break
        fs = j.get('features', [])
        feats.extend(fs)
        if not j.get('exceededTransferLimit') and len(fs) < paso:
            break
        if not fs:
            break
        offset += len(fs)
    if not ok and not feats:
        reg[nombre] = {'url': url_layer, 'ok': False, 'n': 0, 'fecha': time.strftime('%Y-%m-%d'), **meta}
        _escribir_log(reg)
        return None
    fc = {'type': 'FeatureCollection', 'features': feats}
    with open(destino, 'w', encoding='utf-8') as f:
        json.dump(fc, f, ensure_ascii=False)
    reg[nombre] = {'url': url_layer, 'ok': ok, 'n': len(feats), 'bbox': bbox,
                   'fecha': time.strftime('%Y-%m-%d'), **meta}
    _escribir_log(reg)
    log('  [gov_pro] %-42s %5d feats  <- %s' % (nombre, len(feats), url_layer))
    return destino


# --- catalogo de lo que se pide en an_11 --------------------------------------
CAPAS_IAT_CAR = {  # servicio Base_Geo_Cadastro_Ambiental_rural (CAR/SICAR replicado por el IAT)
    0: 'IAT_CAR_hidrografia', 1: 'IAT_CAR_app_total', 2: 'IAT_CAR_reserva_legal',
    3: 'IAT_CAR_vegetacao_nativa', 4: 'IAT_CAR_area_consolidada', 5: 'IAT_CAR_area_pousio',
    6: 'IAT_CAR_servidao_administrativa', 7: 'IAT_CAR_uso_restrito', 8: 'IAT_CAR_area_imovel'}

CAPAS_IAT_OTRAS = [  # (servicio, layer, nombre)
    ('imoveis_certificados_sigef_incra', 0, 'INCRA_SIGEF_imoveis_certificados'),
    ('imoveis_certificados_snci_incra', 0, 'INCRA_SNCI_imoveis_certificados'),
    ('curvas_de_nivel_1_50000_20m', 0, 'IAT_curvas_nivel_50k_20m'),
    ('enquadramento_base_hidrografica', 0, 'IAT_enquadramento_hidrografia_otto'),
    ('hidro_50k_massa_dagua_prcidade', 0, 'IAT_hidro50k_massa_dagua_paranacidade'),
    ('map_uso_cobertura_terra_2012', 0, 'IAT_uso_cobertura_terra_2012_wv2'),
    ('fragmentos_florestais_prioritarios_iatpr', 0, 'IAT_fragmentos_florestais_prioritarios'),
    ('outorgas_sigarh', 0, 'IAT_outorgas_sigarh'),
    ('out_captacao_crh', 0, 'IAT_outorgas_captacao_crh'),
    ('mananciais_2023_iat', 0, 'IAT_mananciais_2023'),
    ('Mananciais_Superficiais_IAT_2026', 0, 'IAT_mananciais_superficiais_2026'),
    ('grandes_bacias_50k', 0, 'IAT_grandes_bacias_50k'),
    ('fbds_nascentes', 0, 'IAT_FBDS_nascentes_recheck'),
]

CAPAS_ANA = [  # SNIRH SPR
    ('Massa_dagua', 0, 'ANA_massa_dagua'),
    ('Armazena_Reservatorio_UGRH', 0, 'ANA_reservatorios_UGRH'),
]


def descargar_todo(forzar=False):
    """Descarga el catalogo completo. Devuelve dict nombre -> ruta (None si fallo)."""
    out = {}
    for lid, nombre in CAPAS_IAT_CAR.items():
        out[nombre] = arcgis_query_geojson(IAT_REST % ('Base_Geo_Cadastro_Ambiental_rural', lid),
                                           nombre, verify=VERIFY_PR, forzar=forzar)
    for serv, lid, nombre in CAPAS_IAT_OTRAS:
        out[nombre] = arcgis_query_geojson(IAT_REST % (serv, lid), nombre, verify=VERIFY_PR, forzar=forzar)
    for serv, lid, nombre in CAPAS_ANA:
        out[nombre] = arcgis_query_geojson(ANA_REST % (serv, lid), nombre, verify=True, forzar=forzar)
    return out


if __name__ == '__main__':
    r = descargar_todo(forzar='--forzar' in os.sys.argv)
    log('descargadas: %d ok / %d' % (sum(1 for v in r.values() if v), len(r)))
