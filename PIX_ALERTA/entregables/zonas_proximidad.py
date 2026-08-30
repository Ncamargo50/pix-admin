# -*- coding: utf-8 -*-
"""Mapa de PROXIMIDAD A COSECHA en 5 zonas, desde los resultados persistidos de
orden_cosecha (sin GEE): clasifica el raster NDMI de cada lote con el nivel anclado
en la referencia seca de ESA corrida (p90) y bordes 0,12/0,20/0,35, con hectareas
por zona normalizadas al area oficial del lote (el raster recortado trae halo de
borde que infla 13-17 % en lotes angostos).

Anclas de campo (29-ago-2026): 'trillable' (<= ref p90) salio a 15 % de humedad;
NDMI ~0,16 ('cerca') estaba a 23 %. Los 'dias' asumen la tasa de secado medida
(~0,025-0,03 NDMI/dia) y SIN lluvia. Estado espectral: la humedad de grano decide.

Uso suelto:  python zonas_proximidad.py ../salida/resultados_SA_SF_2026-08-29.json [es|pt]
Desde orden_cosecha: render(res, z, out, idioma) — mismo JSON+npz, para el PDF.
"""
import json, sys, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, PathPatch, Rectangle
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.path import Path
from scipy.ndimage import gaussian_filter
import matplotlib.patheffects as pe

COLS = ['#7A4A1F', '#D2691E', '#E8C547', '#9CCB86', '#2E7F8F']
TXT_Z = {
 'es': dict(
    noms=['Trillable (≤ ref. seca) · 0 d', 'A días (~1-3 d)', 'Cerca (~3-6 d) · aún húmedo',
          'En secado (~1-2 sem)', 'Lejos (dosel con agua)'],
    chip=' %s · %.0f ha — trillable YA: %.0f ha (%.0f %%) · a días: %.0f ha ',
    leyenda='Zonas de proximidad (NDMI, nivel = ref. seca %.3f) · barra inferior = ha por zona',
    titulo='Proximidad a cosecha por zonas · %s · escena %s (S2 + Landsat, eje de agua)\n'
           'Estado espectral, NO fecha de cosecha: la humedad de grano decide · '
           '"días" a la tasa de secado medida, sin lluvia'),
 'pt': dict(
    noms=['Trilhável (≤ ref. seca) · 0 d', 'Em dias (~1-3 d)', 'Perto (~3-6 d) · ainda úmido',
          'Secando (~1-2 sem)', 'Longe (dossel com água)'],
    chip=' %s · %.0f ha — trilhável JÁ: %.0f ha (%.0f %%) · em dias: %.0f ha ',
    leyenda='Zonas de proximidade (NDMI, nível = ref. seca %.3f) · barra inferior = ha por zona',
    titulo='Proximidade à colheita por zonas · %s · cena %s (S2 + Landsat, eixo de água)\n'
           'Estado espectral, NÃO data de colheita: a umidade do grão decide · '
           '"dias" na taxa de secagem medida, sem chuva'),
}


def _suave(a, s=1.2):
    fin = np.isfinite(a)
    num = gaussian_filter(np.where(fin, a, 0.0), s, mode='nearest')
    den = gaussian_filter(fin.astype(float), s, mode='nearest')
    return np.where(den > 0.35, num / np.maximum(den, 1e-9), np.nan)


def _anillos(ring):
    if isinstance(ring[0][0], (int, float)):
        return [ring]
    if isinstance(ring[0][0][0], (int, float)):
        return ring
    return [rr for p in ring for rr in _anillos(p)]


def render(res, z, out, idioma='es'):
    """res = dict de resultados_… .json · z = np.load(npz) o dict {lid|banda: array}."""
    T = TXT_Z[idioma]
    nivel = res['ref']['ndmi_p90']
    bordes = [-1.0, nivel, 0.12, 0.20, 0.35, 1.0]
    cmap = ListedColormap(COLS); norm = BoundaryNorm(bordes, 5)
    lotes = res['lotes']
    n = len(lotes); cols = 2; rows = (n + 1) // 2
    fig, axs = plt.subplots(rows, cols, figsize=(13.5, 5.7 * rows), facecolor='white')
    axs = np.atleast_1d(axs).ravel()
    for ax in axs[n:]:
        ax.axis('off')
    resumen = {}
    for ax, r in zip(axs, lotes):
        lid = r['id']
        nd, ext = z[f'{lid}|ndmi'], list(z[f'{lid}|ndmi_ext'])
        rgb, extr = z[f'{lid}|rgb'], list(z[f'{lid}|rgb_ext'])
        lat = (ext[2] + ext[3]) / 2
        fin = np.isfinite(nd)
        # fracciones en pixeles CRUDOS; ha = fraccion x area oficial (halo de borde)
        fr = np.array([(((nd >= a) & (nd < b) & fin).sum())
                       for a, b in zip(bordes[:-1], bordes[1:])], float)
        fr /= max(fr.sum(), 1e-9)
        ha = fr * r['area']
        resumen[lid] = ha
        if rgb.ndim == 3 and rgb.shape[2] in (3, 4):
            ax.imshow(rgb, extent=extr, origin='upper', zorder=0)   # ya HxWx4 en 0-1
        im = ax.imshow(np.ma.masked_invalid(_suave(nd)), extent=ext, origin='upper',
                       cmap=cmap, norm=norm, interpolation='nearest', zorder=2, alpha=0.95)
        ans = _anillos(r['ring'])
        rec = Path.make_compound_path(*[Path(np.asarray(rr)) for rr in ans])
        im.set_clip_path(PathPatch(rec, transform=ax.transData))
        for rr in ans:
            xy = np.asarray(rr)
            ax.plot(xy[:, 0], xy[:, 1], color='white', lw=2.0, zorder=4)
            ax.plot(xy[:, 0], xy[:, 1], color='#1a1a1a', lw=0.8, zorder=5)
        for bq in r.get('bloques', []):
            for rr in _anillos(bq['ring']):
                xy = np.asarray(rr)
                ax.plot(xy[:, 0], xy[:, 1], color='white', lw=1.2, ls=(0, (4, 3)), zorder=5)
        xs = [p[0] for rr in ans for p in rr]; ys = [p[1] for rr in ans for p in rr]
        mx = 220 / (111320 * np.cos(np.radians(lat))); my = 220 / 110540
        ax.set_xlim(max(extr[0], min(xs) - mx), min(extr[1], max(xs) + mx))
        ax.set_ylim(max(extr[2], min(ys) - my), min(extr[3], max(ys) + my))
        ax.set_aspect(1.0 / np.cos(np.radians(lat)))
        ax.set_facecolor('#E8EDEA'); ax.set_xticks([]); ax.set_yticks([])
        tot = r['area']
        ax.set_title(T['chip'] % (lid, tot, ha[0], 100 * ha[0] / tot, ha[1]),
                     fontsize=11, fontweight='bold', color='white', loc='left',
                     bbox=dict(boxstyle='square,pad=0.4', fc='#0D9488', ec='none'), pad=6)
        x0 = 0.03
        for c, h in zip(COLS, ha):
            w = 0.94 * h / tot
            ax.add_patch(Rectangle((x0, 0.022), w, 0.035, transform=ax.transAxes,
                                   facecolor=c, edgecolor='white', lw=0.5, zorder=8))
            if h / tot > 0.08:
                ax.text(x0 + w / 2, 0.040, '%.0f' % h, transform=ax.transAxes, ha='center',
                        va='center', fontsize=8, fontweight='bold', color='white', zorder=9,
                        path_effects=[pe.withStroke(linewidth=2, foreground='#00000090')])
            x0 += w
    fig.legend(handles=[Patch(facecolor=c, label=nm) for c, nm in zip(COLS, T['noms'])],
               loc='lower center', ncol=3, fontsize=10, frameon=False,
               bbox_to_anchor=(0.5, 0.005), title=T['leyenda'] % nivel, title_fontsize=9.5)
    fig.suptitle(T['titulo'] % (res['nombre'], res['fecha']),
                 fontsize=13, fontweight='bold', y=0.985)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.10, wspace=0.05, hspace=0.14)
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='white'); plt.close()
    return resumen


def run(jpath, idioma='es'):
    res = json.load(open(jpath, encoding='utf-8'))
    z = np.load(res['npz'])
    suf = '' if idioma == 'es' else f'_{idioma}'
    out = f"{RAIZ_MED}/zonas_proximidad_{res['hkey']}_{res['fecha']}{suf}.png"
    resumen = render(res, z, out, idioma)
    for lid, ha in resumen.items():
        print('%s: ' % lid + ' · '.join('%s %.1f ha' % (nm.split(' (')[0], h)
                                        for nm, h in zip(TXT_Z[idioma]['noms'], ha)))
    print('PNG ->', out)
    return out


import os
RAIZ_MED = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "medicion").replace("\\", "/")

if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else '../salida/resultados_SA_SF_2026-08-29.json',
        sys.argv[2] if len(sys.argv) > 2 else 'es')
