# Reproduce la cadena del motor v7 (coldspot Gi*+FDR  INTERSECT  Mahalanobis-MCD vs chi2)
# sobre una escena real de Santa Cruz, para medir que fraccion de superficie termina
# clasificada PRIORITARIO / VIGILANCIA. Compara df=7 (motor actual) vs df=2 (spec).
import ee, io, requests, numpy as np, rasterio
from esda import G_Local, fdr
from libpysal.weights import KNN
from sklearn.covariance import MinCovDet
from scipy.stats import chi2
ee.Initialize()

LOTE = ee.Geometry.Rectangle([-62.860, -17.450, -62.800, -17.400])
BAD = [3, 8, 9, 10]
ALPHA_FDR, ALPHA_MAHAL = 0.05, 0.01

img = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
       .filterDate('2026-01-01', '2026-03-01').filterBounds(LOTE)
       .sort('CLOUDY_PIXEL_PERCENTAGE').first())
b = lambda n: img.select(n).divide(10000)
B2, B3, B4, B5, B6, B7, B8, B11 = (b('B2'), b('B3'), b('B4'), b('B5'),
                                   b('B6'), b('B7'), b('B8'), b('B11'))
NDVI = B8.subtract(B4).divide(B8.add(B4))
CIre = B7.divide(B5).subtract(1)
NDRE = B8.subtract(B5).divide(B8.add(B5))
REDSI = (B7.multiply(40).subtract(B4.multiply(118)).add(B5.multiply(78))).multiply(.5).divide(B5)
PSRI = B4.subtract(B2).divide(B6)
ARI = B3.pow(-1).subtract(B5.pow(-1))
TCARI = (B5.subtract(B4).subtract(B5.subtract(B3).multiply(.2)).multiply(B5.divide(B4))).multiply(3)
OSAVI = B8.subtract(B4).multiply(1.16).divide(B8.add(B4).add(.16))
TO = TCARI.divide(OSAVI)
MCARI = B5.subtract(B4).subtract(B5.subtract(B3).multiply(.2)).multiply(B5.divide(B4))
NDMI = B8.subtract(B11).divide(B8.add(B11))

clear = img.select('SCL').remap(BAD, [0]*len(BAD), 1)
stack = (CIre.rename('CIre').addBands(NDRE.rename('NDRE')).addBands(REDSI.rename('REDSI'))
         .addBands(PSRI.rename('PSRI')).addBands(ARI.rename('ARI'))
         .addBands(TO.rename('TO')).addBands(MCARI.rename('MCARI'))
         .addBands(NDMI.rename('NDMI'))).updateMask(clear.And(NDVI.gt(0.5)))

url = stack.getDownloadURL({'region': LOTE, 'scale': 10, 'format': 'GEO_TIFF'})
with rasterio.open(io.BytesIO(requests.get(url, timeout=600).content)) as ds:
    names = list(ds.descriptions)
    D = ds.read().astype('float64')
    D[D == ds.nodata] = np.nan
print('bandas:', names, '| forma', D.shape)

ORDEN = ['CIre', 'NDRE', 'REDSI', 'PSRI', 'ARI', 'TO', 'MCARI', 'NDMI']
idx = {n: i for i, n in enumerate(ORDEN)}
CI = D[idx['CIre']]
m = np.all(np.isfinite(D), axis=0)
print('pixeles de dosel validos:', int(m.sum()), f'= {m.sum()*100/10000:.0f} ha')

# --- 1. coldspot Gi* + FDR sobre CIre (agregado a 20 m como pide la spec) ---
def agg(A, f=2):
    h, w = (A.shape[0]//f)*f, (A.shape[1]//f)*f
    return np.nanmean(A[:h, :w].reshape(h//f, f, w//f, f), axis=(1, 3))

CI2 = agg(CI); D2 = np.stack([agg(D[i]) for i in range(D.shape[0])])
m2 = np.isfinite(CI2) & np.all(np.isfinite(D2), axis=0)
rr, cc = np.where(m2)
w = KNN.from_array(np.column_stack([cc*20., rr*20.]), k=8); w.transform = 'r'
g = G_Local(CI2[m2], w, star=True, permutations=999, seed=42)
cut = fdr(g.p_sim, ALPHA_FDR)
cold = (g.p_sim <= cut) & (g.Zs < 0) if cut > 0 else np.zeros(m2.sum(), bool)
ha_u = 20*20/10000
print(f'\ncoldspot Gi*+FDR (a=0.05, corte={cut:.4f}): {cold.sum()} u = '
      f'{cold.sum()*ha_u:.0f} ha = {100*cold.mean():.1f}% del dosel')

# --- 2. Mahalanobis MCD, df=7 (motor) vs df=2 (spec: humedad + senescencia) ---
for etiqueta, feats in [('df=7 (motor v7)', ['CIre','NDRE','REDSI','PSRI','ARI','TO','MCARI']),
                        ('df=2 (spec)',     ['NDMI', 'PSRI'])]:
    X = np.column_stack([D2[idx[f]][m2] for f in feats])
    mcd = MinCovDet(support_fraction=0.75, random_state=0).fit(X)
    md = mcd.mahalanobis(X)
    thr = chi2.ppf(1-ALPHA_MAHAL, df=len(feats))
    out = md > thr
    pri = cold & out
    vig = cold & ~out
    print(f'\n{etiqueta}: umbral chi2={thr:.2f}')
    print(f'  outliers Mahalanobis : {100*out.mean():5.1f}% del dosel')
    print(f'  PRIORITARIO (cold&out): {100*pri.mean():5.1f}%  = {pri.sum()*ha_u:6.0f} ha')
    print(f'  VIGILANCIA  (cold&~out): {100*vig.mean():5.1f}%  = {vig.sum()*ha_u:6.0f} ha')
    print(f'  TOTAL marcado         : {100*cold.mean():5.1f}%  = {cold.sum()*ha_u:6.0f} ha')
