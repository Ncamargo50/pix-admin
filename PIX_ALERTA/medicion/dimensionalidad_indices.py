# Dimensionalidad efectiva de las 7 features del Mahalanobis del motor v7,
# medida sobre una escena S2 real de la zona de Santa Cruz.
import ee, numpy as np
ee.Initialize()

AOI = ee.Geometry.Rectangle([-62.95, -17.55, -62.70, -17.30])
BAD = [3, 8, 9, 10]

col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
       .filterDate('2026-01-01', '2026-03-01').filterBounds(AOI)
       .sort('CLOUDY_PIXEL_PERCENTAGE'))
img = col.first()
print('escena:', img.get('system:index').getInfo(),
      '| nube:', round(img.get('CLOUDY_PIXEL_PERCENTAGE').getInfo(), 1), '%')

scl = img.select('SCL')
clear = scl.remap(BAD, [0]*len(BAD), 1)

def b(n): return img.select(n).divide(10000)
B2, B3, B4 = b('B2'), b('B3'), b('B4')
B5, B6, B7 = b('B5'), b('B6'), b('B7')
B8, B8A, B11 = b('B8'), b('B8A'), b('B11')

NDVI = B8.subtract(B4).divide(B8.add(B4))
CIre = B7.divide(B5).subtract(1)
NDRE = B8.subtract(B5).divide(B8.add(B5))
REDSI = (B7.multiply(705 - 665).subtract(B4.multiply(783 - 665))
         .add(B5.multiply(783 - 705))).multiply(0.5).divide(B5)
PSRI = B4.subtract(B2).divide(B6)
ARI = B3.pow(-1).subtract(B5.pow(-1))
TCARI = (B5.subtract(B4).subtract(B5.subtract(B3).multiply(0.2))
         .multiply(B5.divide(B4))).multiply(3)
OSAVI = B8.subtract(B4).multiply(1.16).divide(B8.add(B4).add(0.16))
TCARI_OSAVI = TCARI.divide(OSAVI)
MCARI = (B5.subtract(B4).subtract(B5.subtract(B3).multiply(0.2))).multiply(B5.divide(B4))

feats = ['CIre', 'NDRE', 'REDSI', 'PSRI', 'ARI', 'TCARI_OSAVI', 'MCARI']
stack = (CIre.rename('CIre').addBands(NDRE.rename('NDRE'))
         .addBands(REDSI.rename('REDSI')).addBands(PSRI.rename('PSRI'))
         .addBands(ARI.rename('ARI')).addBands(TCARI_OSAVI.rename('TCARI_OSAVI'))
         .addBands(MCARI.rename('MCARI')))

# solo dosel cerrado y pixel limpio
mask = clear.And(NDVI.gt(0.5))
stack = stack.updateMask(mask)

samp = stack.sample(region=AOI, scale=20, numPixels=6000, seed=42, dropNulls=True).getInfo()
X = np.array([[f['properties'][k] for k in feats] for f in samp['features']], dtype=float)
X = X[np.all(np.isfinite(X), axis=1)]
print('n pixeles de dosel muestreados:', len(X))

Xs = (X - X.mean(0)) / X.std(0)
C = np.corrcoef(Xs.T)
ev = np.linalg.eigvalsh(np.cov(Xs.T))[::-1]
var = ev / ev.sum()

print('\nMatriz de correlacion (|r|):')
print('            ' + ' '.join(f'{k[:6]:>7}' for k in feats))
for i, k in enumerate(feats):
    print(f'{k:>11} ' + ' '.join(f'{abs(C[i,j]):7.2f}' for j in range(len(feats))))

print('\nVarianza explicada por componente:')
for i, v in enumerate(var):
    print(f'  PC{i+1}: {100*v:5.1f}%  (acum {100*var[:i+1].sum():5.1f}%)')

# numero efectivo de indices independientes (entropia de los autovalores)
p = var[var > 0]
n_eff = float(np.exp(-(p * np.log(p)).sum()))
print(f'\nNumero efectivo de indices independientes (exp de entropia): {n_eff:.2f} de {len(feats)}')
n_eff2 = float((ev.sum() ** 2) / (ev ** 2).sum())
print(f'Dimension participativa (participation ratio):               {n_eff2:.2f} de {len(feats)}')
print(f'\nPC1 solo explica {100*var[0]:.1f}% -> df del chi2 usado por el motor: {len(feats)}')
