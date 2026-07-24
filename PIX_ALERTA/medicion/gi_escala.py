# Efecto de la escala del test Gi* (10 m nativo vs agregado 20/30 m) sobre
# el numero de pixeles declarados significativos tras FDR.
import ee, numpy as np, requests, io, rasterio
from esda import G_Local, fdr
from libpysal.weights import KNN
ee.Initialize()

LOTE = ee.Geometry.Rectangle([-62.860, -17.450, -62.800, -17.400])  # ~640 ha
BAD = [3, 8, 9, 10]

img = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
       .filterDate('2026-01-01', '2026-03-01').filterBounds(LOTE)
       .sort('CLOUDY_PIXEL_PERCENTAGE').first())
B4, B5, B7, B8 = [img.select(b).divide(10000) for b in ['B4', 'B5', 'B7', 'B8']]
CIre = B7.divide(B5).subtract(1).rename('CIre')
NDVI = B8.subtract(B4).divide(B8.add(B4))
clear = img.select('SCL').remap(BAD, [0]*len(BAD), 1)
out = CIre.updateMask(clear.And(NDVI.gt(0.5)))

url = out.getDownloadURL({'region': LOTE, 'scale': 10, 'format': 'GEO_TIFF'})
with rasterio.open(io.BytesIO(requests.get(url, timeout=300).content)) as ds:
    A = ds.read(1).astype('float64')
    A[A == ds.nodata] = np.nan
print('raster', A.shape, '| pixeles validos', int(np.isfinite(A).sum()))


def agregar(A, f):
    if f == 1:
        return A
    h, w = (A.shape[0] // f) * f, (A.shape[1] // f) * f
    B = A[:h, :w].reshape(h // f, f, w // f, f)
    return np.nanmean(B, axis=(1, 3))


def correr(A, res, k=8, perms=999, alpha=0.05):
    m = np.isfinite(A)
    rr, cc = np.where(m)
    if m.sum() < 50:
        return None
    coords = np.column_stack([cc * res, rr * res]).astype('float64')
    w = KNN.from_array(coords, k=k)
    w.transform = 'r'
    g = G_Local(A[m], w, star=True, permutations=perms, seed=42)
    cut = fdr(g.p_sim, alpha)
    sig = g.p_sim <= cut if cut > 0 else np.zeros_like(g.p_sim, dtype=bool)
    cold = sig & (g.Zs < 0)
    return {
        'res_m': res, 'n_unid': int(m.sum()),
        'ha_por_unid': round(res * res / 10000, 3),
        'corte_fdr': float(cut),
        'sig': int(sig.sum()), 'pct_sig': round(100 * sig.sum() / m.sum(), 2),
        'coldspot': int(cold.sum()), 'pct_cold': round(100 * cold.sum() / m.sum(), 2),
        'ha_cold': round(cold.sum() * res * res / 10000, 1),
    }


print(f"\n{'escala':>8} {'unidades':>9} {'corte FDR':>11} {'signif':>8} {'%':>7} {'coldspot':>9} {'%':>7} {'ha frias':>9}")
for f, res in [(1, 10), (2, 20), (3, 30)]:
    r = correr(agregar(A, f), res)
    if r:
        print(f"{r['res_m']:>6} m {r['n_unid']:>9} {r['corte_fdr']:>11.5f} "
              f"{r['sig']:>8} {r['pct_sig']:>6.2f}% {r['coldspot']:>9} {r['pct_cold']:>6.2f}% "
              f"{r['ha_cold']:>8} ha")
