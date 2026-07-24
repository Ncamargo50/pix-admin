# (a) control nulo: mismo test sobre el campo con valores barajados espacialmente
# (b) el 28% marcado, cae al estratificar por zona de suelo (como hace el motor)?
import ee, io, requests, numpy as np, rasterio
from esda import G_Local, fdr
from libpysal.weights import KNN
from sklearn.cluster import KMeans
ee.Initialize()

LOTE = ee.Geometry.Rectangle([-62.860, -17.450, -62.800, -17.400])
BAD = [3, 8, 9, 10]
img = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
       .filterDate('2026-01-01', '2026-03-01').filterBounds(LOTE)
       .sort('CLOUDY_PIXEL_PERCENTAGE').first())
b = lambda n: img.select(n).divide(10000)
B4, B5, B7, B8, B11 = b('B4'), b('B5'), b('B7'), b('B8'), b('B11')
CIre = B7.divide(B5).subtract(1).rename('CIre')
NDVI = B8.subtract(B4).divide(B8.add(B4))
SUELO = B11.rename('B11')   # proxy de zona de suelo
clear = img.select('SCL').remap(BAD, [0]*len(BAD), 1)
st = CIre.addBands(SUELO).updateMask(clear.And(NDVI.gt(0.5)))
url = st.getDownloadURL({'region': LOTE, 'scale': 20, 'format': 'GEO_TIFF'})
with rasterio.open(io.BytesIO(requests.get(url, timeout=600).content)) as ds:
    D = ds.read().astype('float64'); D[D == ds.nodata] = np.nan
CI, SU = D[0], D[1]
m = np.isfinite(CI) & np.isfinite(SU)
print('unidades de 20 m:', int(m.sum()), f'= {m.sum()*400/10000:.0f} ha')


def gi(vals, coords, etiqueta, alpha=0.05):
    w = KNN.from_array(coords, k=8); w.transform = 'r'
    g = G_Local(vals, w, star=True, permutations=999, seed=42)
    cut = fdr(g.p_sim, alpha)
    cold = (g.p_sim <= cut) & (g.Zs < 0) if cut > 0 else np.zeros(len(vals), bool)
    print(f'  {etiqueta:<42} coldspot {100*cold.mean():5.1f}%  (corte FDR {cut:.4f})')
    return cold


rr, cc = np.where(m)
coords = np.column_stack([cc*20., rr*20.])
v = CI[m]

print('\n(a) CONTROL — el test frente a una nula real')
gi(v, coords, 'campo real (autocorrelacion presente)')
rng = np.random.default_rng(42)
gi(rng.permutation(v), coords, 'MISMOS valores barajados en el espacio')

print('\n(b) El motor estratifica por zona de suelo. Cambia algo?')
z = KMeans(n_clusters=3, n_init=10, random_state=0).fit_predict(SU[m].reshape(-1, 1))
tot_cold = 0
for k in range(3):
    s = z == k
    if s.sum() < 100:
        continue
    c = gi(v[s], coords[s], f'zona de suelo {k+1} (n={s.sum()}, B11 med={np.median(SU[m][s]):.3f})')
    tot_cold += c.sum()
print(f'  {"TOTAL estratificado":<42} coldspot {100*tot_cold/m.sum():5.1f}%')
