"""Orquestador: de los poligonos de lote a la lista de a donde ir hoy.

    python -m pix_alerta.main --sitio HDS --hasta 2026-04-30 --K 10

Contrato de salida (mismo patron que el pipeline de trigo, que funciona):
    0  = no habia observacion nueva, no se genero nada
    10 = se genero entregable
    !=0 y !=10 = fallo real, que se vea

Emite el CSV de ranking y el GeoJSON para la app de campo. El GeoJSON lleva
`lote_id` estable y `estrato` — que la app debe guardar y NO mostrar: si el tecnico
sabe que va a un rojo, encuentra algo.
"""
import argparse
import json
import os
import sys
from datetime import date

import pandas as pd

from . import cohorte as coh
from . import config as cfg
from . import ranking as rk
from . import series as sr


# Severidad que entiende la app a partir del veredicto del criterio. La app deriva
# color y orden de `sev`; sin este campo `deriveSev` devuelve null y TODOS los lotes
# salen "sin dato de severidad".
SEV_APP = {'ATENCION': 'alta', 'VIGILANCIA': 'media'}


# Tolerancia de simplificacion del perimetro, en grados (~0,0002 = ~22 m).
# El perimetro es SOLO para encuadrar el mapa: no se mide sobre el, asi que no hace
# falta resolucion de borde. Medido sobre HDS: el contorno crudo de los 220 lotes son
# 16.107 vertices y 776 KB de GeoJSON para 6 focos — el 97% del archivo era el marco.
# En una APK offline sobre conectividad rural eso se paga en cada descarga. Con esta
# tolerancia baja a 3.607 vertices y 192 KB. Las 148 partes que quedan NO son astillas:
# son parcelas reales (mediana 16 ha, maxima 358), o sea la forma verdadera del campo.
PERIM_TOLERANCIA = 0.0002
PERIM_AREA_MINIMA = 1e-7          # ~1 ha en grados: descarta astillas del disolvido


def _perimetro(gj):
    """Contorno del campo, disuelto de los propios lotes y simplificado.

    La app lo usa para encuadrar el mapa. Sin el, el tecnico ve poligonos flotando sin
    referencia de donde esta el campo. Si no hay shapely se sigue sin perimetro: es
    degradacion, no motivo para no entregar.
    """
    try:
        from shapely.geometry import MultiPolygon, Polygon, mapping, shape
        from shapely.ops import unary_union
    except ImportError:
        return None
    try:
        u = unary_union([shape(f['geometry']) for f in gj['features']
                         if f.get('geometry')]).buffer(0)
        u = u.simplify(PERIM_TOLERANCIA, preserve_topology=True)
        # Las astillas que deja el disolvido no son campo y son la mitad de las partes.
        if isinstance(u, MultiPolygon):
            partes = [g for g in u.geoms if g.area >= PERIM_AREA_MINIMA]
            if partes:
                u = MultiPolygon(partes) if len(partes) > 1 else partes[0]
        if u.is_empty or not isinstance(u, (Polygon, MultiPolygon)):
            return None
        return mapping(u)
    except Exception:
        return None


def _geojson_salida(sitio, rank, ruta):
    """Poligonos de los lotes priorizados, en el formato que LEE la app de campo.

    OJO: los nombres de campo no son decorativos, son la interfaz con PIX Scout.
    Medido antes de este cambio: la app cargaba los 6 lotes con id `F-1`..`F-6`
    —posicionales, se renumeran en cada corrida—, el nombre del lote como "Lote 1" en
    vez de `J1_soya`, hacienda "Campo", sin severidad y sin perimetro. Con ids
    posicionales **el lazo de retorno no existe**: una validacion registrada hoy no se
    puede rastrear al lote la semana que viene, que es justo el dato con el que se mide
    la precision del motor.
    """
    with open(sitio.lotes_geojson, encoding='utf-8') as fh:
        gj = json.load(fh)
    por_id = {str(f['properties'].get(sitio.campo_id)): f for f in gj['features']}
    feats = []
    vistos = set()
    for _, r in rank.iterrows():
        f = por_id.get(str(r['lote_id']))
        if f is None:
            continue
        lid = str(r['lote_id'])
        if lid in vistos:                      # el ID tiene que ser unico o no sirve
            raise RuntimeError(f'lote_id duplicado en la salida: {lid}')
        vistos.add(lid)
        est = r['estado']
        props = {
            # --- interfaz con la app: `id` es lo que ancla el lazo de retorno ---
            'id': lid,
            'name': lid,
            'etiqueta': lid,                   # lo que el tecnico casa con el informe
            'lote': lid,
            'hacienda': sitio.titulo,
            'fecha_img': str(r['fecha_dato'])[:10],
            'sev': SEV_APP.get(est),           # None si no esta alertado
            'cultivo': getattr(sitio, 'cultivo', '') or None,
            # Redondeado: la app lo imprime tal cual y salia "Sev 2.2025829689196113".
            # NO se reescala a 1-99: ese numero seria inventado. Es el estadistico del
            # criterio (EWMA dirigido); lo que el tecnico usa es el ORDEN.
            'score': (round(float(r['score']), 2)
                      if pd.notna(r.get('score')) else None),
            # --- criterio ---
            'lote_id': lid,
            'orden': int(r['orden']),
            'estrato': est,                    # la app lo GUARDA y no lo muestra
            'fecha_dato': str(r['fecha_dato'])[:10],
            'dias_atras': int(r['dias_atras']),
            'area_ha': float(r['area_ha']),
            'status': 'pending',
        }
        feats.append({'type': 'Feature', 'geometry': f['geometry'],
                      'properties': props})

    n_focos = len(feats)
    per = _perimetro(gj)
    if per is not None:
        # Va PRIMERO y con tipo 'perimetro': asi la app lo excluye de la lista de focos
        # y lo usa solo para encuadrar (geojson.js -> isPerimeter).
        feats.insert(0, {'type': 'Feature', 'geometry': per,
                         'properties': {'tipo': 'perimetro',
                                        'id': '%s-PERIMETRO' % sitio.clave,
                                        'hacienda': sitio.titulo}})
    with open(ruta, 'w', encoding='utf-8') as fh:
        json.dump({'type': 'FeatureCollection', 'features': feats}, fh,
                  ensure_ascii=False)
    return n_focos


def main(argv=None):
    p = argparse.ArgumentParser(description='PIX ALERTA — ranking de lotes')
    p.add_argument('--sitio', default='HDS', choices=sorted(cfg.SITIOS))
    p.add_argument('--desde', default=None, help='YYYY-MM-DD (def: 150 dias atras)')
    p.add_argument('--hasta', default=str(date.today()))
    p.add_argument('--K', type=int, default=None, help='capacidad de scouting')
    p.add_argument('--serie', default=None, help='CSV ya extraido, para no repetir GEE')
    p.add_argument('--salida', default='salida')
    p.add_argument('--control-nulo', action='store_true',
                   help='corre la puerta 2.1 y reporta la tasa de alarma')
    a = p.parse_args(argv)

    sitio = cfg.SITIOS[a.sitio]
    # Fuera de campaña el criterio no distingue cosecha de deterioro: en madurez
    # el NDMI baja y el PSRI sube, que es la firma que busca. Se para aca.
    if sitio.campanas and not rk.dentro_de_campana(a.hasta, sitio):
        vent = " · ".join("%s..%s" % v for v in sitio.campanas.values())
        print("[NO-OP] %s esta FUERA de las campañas declaradas de %s (%s). "
              "En cosecha/madurez la firma de senescencia es indistinguible del "
              "deterioro: no se emite ranking." % (a.hasta, sitio.clave, vent))
        return 0
    os.makedirs(a.salida, exist_ok=True)
    # La ventana arranca con la CAMPAÑA, no N dias atras: el estimador de cohorte
    # necesita ver la emergencia. Ver ranking.inicio_de_campana para lo que paso al
    # cortar a 150 dias (188 de 207 lotes quedaron sin ciclo y el ranking salio vacio).
    desde = a.desde or rk.inicio_de_campana(a.hasta, sitio)
    if not desde:
        desde = str(pd.Timestamp(a.hasta) - pd.Timedelta(days=150))[:10]
        print(f'[aviso] {sitio.clave} no declara campañas: se usan 150 dias hacia atras. '
              'Sin ver la emergencia, la cohorte puede salir sin ciclo.')
    print(f'[ventana] {desde} .. {a.hasta}')

    if a.serie:
        df = pd.read_csv(a.serie, parse_dates=['fecha'])
        # Una serie extraida antes de declararse el filtro trae pista y monte.
        validas = cfg.unidades_validas(sitio)
        if validas is not None:
            antes = df['lote_id'].nunique()
            df = df[df['lote_id'].astype(str).isin(validas)]
            fuera = antes - df['lote_id'].nunique()
            if fuera:
                print(f'{fuera} unidades descartadas por no ser cultivo')
    else:
        # NO usar ee.Initialize() a secas: en la nube no hay credencial personal y la
        # primera corrida real murio con "Please authorize access to your Earth Engine
        # account". Ver ee_init.
        from .ee_init import inicializar
        print('[GEE] %s' % inicializar())
        df = sr.extraer(sitio, desde, a.hasta)
        if df.empty:
            print('sin escenas en la ventana: nada que entregar')
            return 0
        df.to_csv(os.path.join(a.salida, f'serie_{sitio.clave}.csv'), index=False)

    plenas = (df['calidad'] == 'pleno').sum()
    if plenas == 0:
        # No se inventa un rojo con escena nublada: se declara y se sale limpio.
        print('ninguna observacion plena en la ventana — producto no emitido')
        return 0

    # COHORTE. La especificacion la declara obligatoria (Paso 2) y, a falta de fecha
    # de siembra declarada, manda estimarla del satelite y rotularla como estimada.
    # Medido sobre HDS: con cohorte unica el criterio marcaba 1,3% contra un nulo de
    # 2,0% — no discriminaba nada. Con cohorte estimada por fenologia pasa a 4,7%
    # contra 3,1%. No es un ajuste: sin cohorte el criterio esta ciego.
    if 'cohorte' not in df.columns:
        df = coh.estimar(df)
    car = rk.ewma(rk.residuos(df))
    if car.empty:
        print(f'ningun lote alcanza {rk.MIN_OBS_LOTE} observaciones plenas — '
              'serie insuficiente, producto no emitido')
        return 0

    # Se calcula el ranking COMPLETO y aparte el recortado por K. El informe declara
    # cuantos lotes quedaron SIN DATO, y eso desaparece en el recorte.
    rank_todos = rk.ranking(car, fecha=a.hasta, K=None)
    cob = (df['calidad'] == 'pleno').mean()
    rank = rk.ranking(car, fecha=a.hasta, K=a.K)
    n_at = int((rank['estado'] == 'ATENCION').sum())
    n_vi = int((rank['estado'] == 'VIGILANCIA').sum())

    csv = os.path.join(a.salida, f'ranking_{sitio.clave}_{a.hasta}.csv')
    rank.to_csv(csv, index=False)
    gj = os.path.join(a.salida, f'lotes_{sitio.clave}_{a.hasta}.geojson')
    n = _geojson_salida(sitio, rank, gj)

    # Informe PDF. El ranking que se le pasa es el COMPLETO (rank_todos), no el cortado
    # por K: el informe tiene que poder declarar cuantos lotes quedaron sin observacion,
    # y eso no esta en el recorte.
    pdf = os.path.join(a.salida, f'Informe_{sitio.clave}_{a.hasta}.pdf')
    try:
        from . import informe as inf
        inf.generar(sitio, sitio, rank_todos, pdf, a.hasta,
                    cobertura=cob, huecos=getattr(sitio, 'hueco_dias', None))
    except Exception as e:
        # El PDF es presentacion; el CSV y el GeoJSON son el producto. Si el informe
        # falla se avisa y se entrega igual, en vez de perder la corrida entera.
        print(f'  [AVISO] no se pudo generar el PDF: {type(e).__name__}: {e}')
        pdf = None

    cob = (df['calidad'] == 'pleno').mean()
    print(f'\n{sitio.titulo} — corte {a.hasta}')
    print(f'  observaciones plenas: {cob*100:.1f}% de las disponibles')
    print(f'  lotes evaluados     : {len(rank)}')
    print(f'  ATENCION            : {n_at}')
    print(f'  VIGILANCIA          : {n_vi}')
    if n_at == 0 and n_vi == 0:
        print('  >> ningun lote sale de control. No hay a donde mandar al tecnico.')
    print(f'  -> {csv}')
    print(f'  -> {gj} ({n} lotes)')
    if pdf:
        print(f'  -> {pdf}')

    if a.control_nulo:
        t = rk.control_nulo(df, n_rep=10)
        print(f'\n  PUERTA 2.1 control nulo: tasa de alarma {100*t:.1f}%')
        print('  (referencia: Gi* sobre el indice crudo marca ~30%)')

    return 10


if __name__ == '__main__':
    sys.exit(main())
