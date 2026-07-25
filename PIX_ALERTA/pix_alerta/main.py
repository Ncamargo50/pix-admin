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


def _geojson_salida(sitio, rank, ruta):
    """Poligonos de los lotes priorizados, con ID estable y estrato oculto."""
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
        feats.append({
            'type': 'Feature',
            'geometry': f['geometry'],
            'properties': {
                'lote_id': lid,
                'orden': int(r['orden']),
                'estrato': r['estado'],        # la app lo GUARDA y no lo muestra
                'fecha_dato': str(r['fecha_dato'])[:10],
                'dias_atras': int(r['dias_atras']),
                'area_ha': float(r['area_ha']),
                'status': 'pending',
            },
        })
    with open(ruta, 'w', encoding='utf-8') as fh:
        json.dump({'type': 'FeatureCollection', 'features': feats}, fh,
                  ensure_ascii=False)
    return len(feats)


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
    desde = a.desde or str(pd.Timestamp(a.hasta) - pd.Timedelta(days=150))[:10]

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
        import ee
        ee.Initialize()
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

    rank = rk.ranking(car, fecha=a.hasta, K=a.K)
    n_at = int((rank['estado'] == 'ATENCION').sum())
    n_vi = int((rank['estado'] == 'VIGILANCIA').sum())

    csv = os.path.join(a.salida, f'ranking_{sitio.clave}_{a.hasta}.csv')
    rank.to_csv(csv, index=False)
    gj = os.path.join(a.salida, f'lotes_{sitio.clave}_{a.hasta}.geojson')
    n = _geojson_salida(sitio, rank, gj)

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

    if a.control_nulo:
        t = rk.control_nulo(df, n_rep=10)
        print(f'\n  PUERTA 2.1 control nulo: tasa de alarma {100*t:.1f}%')
        print('  (referencia: Gi* sobre el indice crudo marca ~30%)')

    return 10


if __name__ == '__main__':
    sys.exit(main())
