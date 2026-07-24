# Paso 0 - Disponibilidad real de escena limpia por ventana de 10 dias.
# Mide, sobre un AOI real y N campanas, que fraccion de dekadas tuvo >=1 observacion
# con cobertura util suficiente. Nube Y SOMBRA via SCL (clases 3,8,9,10).
import ee, sys, json
from datetime import date, timedelta

ee.Initialize()

# AOI: se pasa como bbox o path a geojson
AOI = ee.Geometry.Rectangle([-62.95, -17.55, -62.70, -17.30])  # ~26 x 28 km zona este Santa Cruz

BAD = [3, 8, 9, 10]  # sombra de nube, nube media, nube alta, cirrus
UMBRAL_UTIL = 0.80   # >=80% del AOI con pixel valido = escena utilizable


def frac_util(img):
    scl = img.select('SCL')
    good = scl.remap(BAD, [0] * len(BAD), 1).rename('good')
    f = good.reduceRegion(ee.Reducer.mean(), AOI, 60, maxPixels=1e9, bestEffort=True).get('good')
    return img.set('frac_util', f)


def campana(y0):
    """Campana de verano: 1-oct-y0 a 30-abr-(y0+1) -- soya/maiz Santa Cruz."""
    return date(y0, 10, 1), date(y0 + 1, 4, 30)


resultados = {}
for y0 in [2021, 2022, 2023, 2024, 2025]:
    ini, fin = campana(y0)
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterDate(str(ini), str(fin))
           .filterBounds(AOI)
           .map(frac_util))
    feats = col.select([]).getInfo()  # metadata only
    obs = []
    for f in feats['features']:
        p = f['properties']
        if p.get('frac_util') is not None:
            obs.append((p['system:time_start'], p['frac_util']))

    # agrupar en dekadas
    dekadas = {}
    d = ini
    idx = 0
    while d < fin:
        dekadas[idx] = []
        idx += 1
        d += timedelta(days=10)
    total_dek = idx

    import datetime as dt
    for ts, fu in obs:
        fecha = dt.datetime.utcfromtimestamp(ts / 1000).date()
        k = (fecha - ini).days // 10
        if 0 <= k < total_dek:
            dekadas[k].append(fu)

    con_escena = sum(1 for k in dekadas if any(v >= UMBRAL_UTIL for v in dekadas[k]))
    mejor = {k: (max(v) if v else 0.0) for k, v in dekadas.items()}
    resultados[f'{y0}/{y0+1}'] = {
        'dekadas_totales': total_dek,
        'dekadas_con_escena_util': con_escena,
        'pct': round(100 * con_escena / total_dek, 1),
        'n_escenas': len(obs),
        'mejor_por_dekada': [round(mejor[k], 2) for k in sorted(mejor)],
        'ini': str(ini), 'fin': str(fin),
    }
    print(f"{y0}/{y0+1}: {con_escena}/{total_dek} dekadas ({resultados[f'{y0}/{y0+1}']['pct']}%) "
          f"con escena >={int(UMBRAL_UTIL*100)}% util | {len(obs)} escenas S2", flush=True)

print()
print(json.dumps(resultados, indent=1))
