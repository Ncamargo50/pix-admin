# Paso 0b - misma medicion a ESCALA DE LOTE (~100 ha) y desglose por MES.
import ee, datetime as dt, json
from datetime import date, timedelta
ee.Initialize()

BAD = [3, 8, 9, 10]
UMBRAL = 0.80

# lote sintetico de ~100 ha (1 km x 1 km) en el centro del AOI anterior
LOTE = ee.Geometry.Rectangle([-62.830, -17.430, -62.820, -17.421])
AOI_G = ee.Geometry.Rectangle([-62.95, -17.55, -62.70, -17.30])

def medir(geom, etiqueta):
    def frac(img):
        scl = img.select('SCL')
        good = scl.remap(BAD, [0]*len(BAD), 1).rename('good')
        f = good.reduceRegion(ee.Reducer.mean(), geom, 20, maxPixels=1e9, bestEffort=True).get('good')
        return img.set('fu', f)

    por_mes = {m: [0, 0] for m in [10, 11, 12, 1, 2, 3, 4]}   # [dekadas_ok, dekadas_totales]
    tot_ok = tot = 0
    for y0 in [2021, 2022, 2023, 2024, 2025]:
        ini, fin = date(y0, 10, 1), date(y0+1, 4, 30)
        col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
               .filterDate(str(ini), str(fin)).filterBounds(geom).map(frac))
        obs = [(f['properties']['system:time_start'], f['properties'].get('fu'))
               for f in col.select([]).getInfo()['features']]
        obs = [(t, v) for t, v in obs if v is not None]

        n_dek = 0
        d = ini
        while d < fin:
            n_dek += 1
            d += timedelta(days=10)
        dek = {k: [] for k in range(n_dek)}
        for ts, v in obs:
            f = dt.datetime.utcfromtimestamp(ts/1000).date()
            k = (f - ini).days // 10
            if 0 <= k < n_dek:
                dek[k].append(v)
        for k in range(n_dek):
            mes = (ini + timedelta(days=10*k)).month
            ok = any(v >= UMBRAL for v in dek[k])
            por_mes[mes][1] += 1
            tot += 1
            if ok:
                por_mes[mes][0] += 1
                tot_ok += 1
    print(f"\n=== {etiqueta} ===")
    print(f"GLOBAL 5 campanas: {tot_ok}/{tot} dekadas con escena >={int(UMBRAL*100)}% util = {100*tot_ok/tot:.1f}%")
    for m in [10, 11, 12, 1, 2, 3, 4]:
        ok, t = por_mes[m]
        print(f"  mes {m:2d}: {ok:2d}/{t:2d} = {100*ok/t:5.1f}%")
    return tot_ok/tot

medir(LOTE, "LOTE ~100 ha")
medir(AOI_G, "AOI ~700 km2 (referencia)")
