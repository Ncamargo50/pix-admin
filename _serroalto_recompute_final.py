# -*- coding: utf-8 -*-
"""RECOMPUTE FINAL: lotes limpios (compactos) + drenajes = TUS dibujados ∪ satelital.
Area util corregida. Re-exporta lotes, individuales, global, CSV."""
import os, sys, glob, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, pandas as pd, numpy as np
from shapely.ops import unary_union
from shapely.validation import make_valid
import warnings; warnings.filterwarnings('ignore')

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUTDIR = os.path.join(DIRBASE, '_analisis_canadas')
INDIV = os.path.join(DIRBASE, 'Lotes_individuales_area_util')
os.makedirs(INDIV, exist_ok=True)

def comp(g):
    p = g.length; return 4*np.pi*g.area/(p*p) if p > 0 else 0

lote_feats = {}; dren_feats = []
for f in sorted(glob.glob(r'C:\Users\Usuario\Documents\B*L*.shp')):
    stem = os.path.splitext(os.path.basename(f))[0]
    m = re.match(r'B[loque]*-?(\d+)-L0*([\d\-]+)', stem, re.I)
    if not m: continue
    bloque = str(int(m.group(1))); ln = m.group(2).replace('-', '')
    lote = 'L%02d' % int(ln) if ln.isdigit() else 'L' + ln
    lid = 'Bloque-%s-%s' % (bloque, lote)
    g = gpd.read_file(f); g = g[g.geometry.notna() & ~g.geometry.is_empty].to_crs(31981)
    for geom in g.geometry:
        a = geom.area/1e4; c = comp(geom)
        if c < 0.20 and a < 5:
            dren_feats.append(geom)
        else:
            lote_feats.setdefault((lid, bloque), []).append(geom)

# lotes limpios (dissolve por lote)
rows = []
for (lid, bloque), geoms in lote_feats.items():
    rows.append(dict(lote_id=lid, bloque=bloque, geometry=make_valid(unary_union(geoms))))
L = gpd.GeoDataFrame(rows, crs=31981)
L['gross_ha'] = L.area/1e4
user_dren = make_valid(unary_union(dren_feats))
print('Lotes: %d | bruta total %.1f ha | TUS drenajes %.1f ha (%d features)' % (len(L), L['gross_ha'].sum(), user_dren.area/1e4, len(dren_feats)))

# satelital (mi deteccion consolidada)
sat = make_valid(unary_union(gpd.read_file(os.path.join(DIRBASE, 'CANADAS_consolidado_SerroAlto.geojson')).to_crs(31981).geometry.values))
lot_u = unary_union(L.geometry.values)
dren_final = make_valid(unary_union([user_dren, sat])).intersection(lot_u)
print('Drenaje FINAL (tuyo ∪ satelital): %.1f ha (%.1f%%)' % (dren_final.area/1e4, dren_final.area/lot_u.area*100))

# por lote
recs = []
for _, r in L.iterrows():
    geom = r.geometry; gha = r['gross_ha']
    can_l = make_valid(geom.intersection(dren_final)); util_l = make_valid(geom.difference(dren_final))
    cha, uha = can_l.area/1e4, util_l.area/1e4
    recs.append(dict(lote_id=r['lote_id'], bloque=r['bloque'], gross_ha=round(gha, 2),
                     dren_ha=round(cha, 2), util_ha=round(uha, 2), dren_pct=round(cha/gha*100, 1) if gha else 0))
    gu = gpd.GeoDataFrame([{'lote_id': r['lote_id'], 'bloque': r['bloque'], 'tipo': 'AREA_UTIL', 'ha': round(uha, 2)}], geometry=[util_l], crs=31981)
    parts = [gu]
    if not can_l.is_empty:
        parts.append(gpd.GeoDataFrame([{'lote_id': r['lote_id'], 'bloque': r['bloque'], 'tipo': 'DRENAJE', 'ha': round(cha, 2)}], geometry=[can_l], crs=31981))
    pd.concat(parts).set_crs(31981).to_crs(4326).to_file(os.path.join(INDIV, '%s_area_util.geojson' % r['lote_id']), driver='GeoJSON')

df = pd.DataFrame(recs).sort_values(['bloque', 'lote_id'])
df.to_csv(os.path.join(DIRBASE, 'AREA_UTIL_por_lote.csv'), index=False, encoding='utf-8-sig')

# exports globales
L.to_crs(4326).to_file(os.path.join(DIRBASE, 'Lotes_SerroAlto_LIMPIOS.geojson'), driver='GeoJSON')
gpd.GeoDataFrame(geometry=[dren_final], crs=31981).explode(index_parts=False).to_crs(4326).to_file(os.path.join(DIRBASE, 'DRENAJES_FINAL_SerroAlto.geojson'), driver='GeoJSON')
glob_rows = []
for _, r in L.iterrows():
    util_l = make_valid(r.geometry.difference(dren_final))
    rr = df[df.lote_id == r['lote_id']].iloc[0]
    glob_rows.append({'lote_id': r['lote_id'], 'bloque': r['bloque'], 'gross_ha': rr['gross_ha'], 'dren_ha': rr['dren_ha'], 'util_ha': rr['util_ha'], 'geometry': util_l})
gpd.GeoDataFrame(glob_rows, crs=31981).to_crs(4326).to_file(os.path.join(DIRBASE, 'AREA_UTIL_GLOBAL_SerroAlto.geojson'), driver='GeoJSON')

print('\n=== RESUMEN POR BLOQUE (CORREGIDO con tus drenajes) ===')
bl = df.groupby('bloque').agg(lotes=('lote_id', 'nunique'), g=('gross_ha', 'sum'), d=('dren_ha', 'sum'), u=('util_ha', 'sum'))
for b, r in bl.sort_index(key=lambda x: x.astype(int)).iterrows():
    print('  Bloque %-3s: %2d lotes | bruta %7.1f | drenaje %5.1f (%.1f%%) | UTIL %7.1f ha' % (b, r['lotes'], r['g'], r['d'], r['d']/r['g']*100, r['u']))
t = df[['gross_ha', 'dren_ha', 'util_ha']].sum()
print('  TOTAL    : %2d lotes | bruta %7.1f | drenaje %5.1f (%.1f%%) | UTIL %7.1f ha' % (len(df), t['gross_ha'], t['dren_ha'], t['dren_ha']/t['gross_ha']*100, t['util_ha']))
print('DONE')
