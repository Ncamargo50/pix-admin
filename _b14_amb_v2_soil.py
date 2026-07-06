# -*- coding: utf-8 -*-
"""BLOQUE 14 v2 — indices de SUELO desde compuesto de suelo desnudo + VALIDACION rangos.
Arcilla=B11/B12 ; Materia organica=inverso brillo ; Color/redness RI=B4/B2 (roja altura vs negra bajura).
Valida (feedback_verify_layer_ranges): min/max/mean/std por capa en B14 + correlacion vs elevacion.
Guarda soil_indices.tif y PNG de validacion (suelo desnudo RGB + capas)."""
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, rasterio
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import warnings; warnings.filterwarnings('ignore')

BASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
CAN = os.path.join(BASE, '_analisis_canadas'); OUT = os.path.join(CAN, 'AMBIENTES_V2')

soil = rasterio.open(os.path.join(OUT, 'soil_bare.tif'))
T, C, H, Wd = soil.transform, soil.crs, soil.height, soil.width
bnames = list(soil.descriptions) or ['B2','B3','B4','B8','B11','B12','bare_count']
idx = {n: i+1 for i, n in enumerate(['B2','B3','B4','B8','B11','B12','bare_count'])}
def rd(n): return soil.read(idx[n]).astype('float32')
B2,B3,B4,B8,B11,B12 = (rd('B2'),rd('B3'),rd('B4'),rd('B8'),rd('B11'),rd('B12'))
bcount = rd('bare_count')

# mascara B14 (union de divisiones)
lot = gpd.read_file(os.path.join(CAN,'Lotes_B14_divisiones.geojson')).to_crs(C)
m14 = rasterize([(g,1) for g in lot.geometry], out_shape=(H,Wd), transform=T, fill=0).astype(bool)
# pixel valido: dentro de B14, con datos y >=4 obs desnudas de ESTACION SECA (calidad por
# observacion ya asegurada por el filtro seco; I2 auditoria). Se enmascaran los indices a
# estos pixeles y aguas abajo se rellenan huecos con el confiable mas cercano.
MIN_BARE = 4
valid = m14 & np.isfinite(B4) & (B4>0) & (bcount>=MIN_BARE)

# --- INDICES DE SUELO (solo suelo desnudo) ---
clay = np.where(B12>0, B11/B12, np.nan)                    # arcilla (SWIR1/SWIR2) alto=+arcilla
# ALBEDO espectro completo: negro (MO alta) = oscuro en TODAS las bandas incl SWIR;
# rojo oxidico = brillante en SWIR -> albedo total separa negro-bajura sin confundir con hue rojo.
albedo = (B2+B3+B4+B8+B11+B12)/6.0
om = -albedo                                               # materia organica proxy: alto=negro/+MO
bright = np.sqrt((B2**2+B3**2+B4**2)/3.0)                  # brillo visible (referencia, confundido por rojo)
redness = np.where(B2>0, B4/B2, np.nan)                    # rojo/azul: alto=tierra roja (altura)
ferric = np.where((B4+B2)>0, (B4-B2)/(B4+B2), np.nan)      # oxidos de hierro (confirmacion redness)

# reproyectar DEM FABDEM al grid del suelo para correlacion
def resample_to(path, b=1):
    with rasterio.open(path) as s:
        dst=np.full((H,Wd), np.nan,'float32')
        reproject(rasterio.band(s,b),dst,src_transform=s.transform,src_crs=s.crs,
                  dst_transform=T,dst_crs=C,resampling=Resampling.bilinear)
    return dst
dem = resample_to(os.path.join(CAN,'dem_fabdem.tif')); dem[dem<-50]=np.nan

def stats(name, a):
    v=a[valid & np.isfinite(a)]
    if v.size<5: print('  %-10s DEGENERADA n=%d'%(name,v.size)); return
    print('  %-10s min=%.3f  p5=%.3f  mean=%.3f  p95=%.3f  max=%.3f  std=%.4f  n=%d'%(
        name, np.nanmin(v), np.percentile(v,5), np.nanmean(v), np.percentile(v,95),
        np.nanmax(v), np.nanstd(v), v.size))

def corr(a, b):
    mm=valid & np.isfinite(a) & np.isfinite(b)
    if mm.sum()<20: return float('nan')
    return float(np.corrcoef(a[mm], b[mm])[0,1])

print('=== VALIDACION SUELO DESNUDO B14 ===')
print('Pixeles B14:', int(m14.sum()), '| validos (bare_count>=4):', int(valid.sum()),
      '(%.0f%%)'%(100*valid.sum()/max(m14.sum(),1)))
print('bare_count dentro B14: min=%d mean=%.1f max=%d'%(np.nanmin(bcount[m14]),np.nanmean(bcount[m14]),np.nanmax(bcount[m14])))
print('\n--- rangos por capa ---')
for n,a in [('clay',clay),('albedo',albedo),('om(-alb)',om),('redness',redness),('ferric',ferric),('bright_vis',bright),('dem',dem)]:
    stats(n,a)
print('\n--- correlacion vs ELEVACION (altura=roja seca ; bajura=negra humeda) ---')
print('  redness  vs dem : %+.3f  (esperado + : altura roja mas alta)'%corr(redness,dem))
print('  ferric   vs dem : %+.3f  (esperado +)'%corr(ferric,dem))
print('  albedo   vs dem : %+.3f  (esperado + : altura brillante SWIR ; bajura negra oscura baja)'%corr(albedo,dem))
print('  clay     vs dem : %+.3f  (esperado - : bajura mas arcilla)'%corr(clay,dem))
print('  bright_v vs dem : %+.3f  (confundido por rojo)'%corr(bright,dem))
print('  redness vs albedo: %+.3f'%corr(redness,albedo))
print('  clay    vs albedo: %+.3f'%corr(clay,albedo))

# guardar indices ENMASCARADOS a pixeles confiables (bare_count>=MIN_BARE); NaN en no confiables
prof = soil.profile.copy(); prof.update(count=6, dtype='float32', nodata=np.nan)
def msk(a): return np.where(valid, a, np.nan).astype('float32')
with rasterio.open(os.path.join(OUT,'soil_indices.tif'),'w',**prof) as dst:
    for i,(n,a) in enumerate([('clay',msk(clay)),('om',msk(om)),('redness',msk(redness)),
                              ('ferric',msk(ferric)),('albedo',msk(albedo)),('bare_count',bcount)],1):
        dst.write(a.astype('float32'), i); dst.set_band_description(i,n)
print('\nCobertura suelo confiable (bare>=%d): %.0f%% de B14' % (MIN_BARE, 100*valid.sum()/max(m14.sum(),1)))

# ---- PNG validacion: suelo desnudo RGB + capas ----
rgb = rasterio.open(os.path.join(OUT,'soil_bare_rgb.tif')).read().astype('float32')
def stre(b):
    v=b[b>0];
    if v.size<5: return np.zeros_like(b)
    lo,hi=np.percentile(v,2),np.percentile(v,98)
    o=np.clip((b-lo)/(hi-lo+1e-9),0,1); o[b<=0]=1; return o
rgbv=np.dstack([stre(rgb[0]),stre(rgb[1]),stre(rgb[2])])
# extent METRICO (raster en EPSG:31981); limites de lote en el MISMO CRS
ext=[T.c, T.c+T.a*Wd, T.f+T.e*H, T.f]
lot_m = lot.to_crs(C)
fig,ax=plt.subplots(2,3,figsize=(19,12))
ax[0,0].imshow(rgbv,extent=ext,origin='upper'); ax[0,0].set_title('SUELO DESNUDO RGB (verificar SIN cultivos)',fontsize=11)
def show(a,axi,ttl,cmap):
    d=np.where(valid,a,np.nan); im=axi.imshow(d,extent=ext,origin='upper',cmap=cmap); axi.set_title(ttl,fontsize=11); plt.colorbar(im,ax=axi,shrink=.7)
show(bcount,ax[0,1],'bare_count (# fechas suelo desnudo)','viridis')
show(redness,ax[0,2],'REDNESS B4/B2 (alto=tierra ROJA altura)','RdYlBu_r')
show(albedo,ax[1,0],'ALBEDO total (bajo=tierra NEGRA/+MO bajura)','Greys_r')
show(clay,ax[1,1],'ARCILLA B11/B12 (alto=+arcilla)','YlOrBr')
show(dem,ax[1,2],'ELEVACION FABDEM (m)','terrain')
for a_ in ax.ravel():
    lot_m.boundary.plot(ax=a_,color='k',linewidth=.4)
    a_.set_xlim(ext[0],ext[1]); a_.set_ylim(ext[2],ext[3]); a_.set_axis_off()
plt.suptitle('BLOQUE 14 — Validacion capas de SUELO DESNUDO (v2 textura)',fontsize=14,weight='bold')
plt.tight_layout(); plt.savefig(os.path.join(OUT,'VALID_suelo_desnudo_B14.png'),dpi=130,bbox_inches='tight')
print('\nPNG -> VALID_suelo_desnudo_B14.png'); print('DONE soil')
