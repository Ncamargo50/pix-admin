# -*- coding: utf-8 -*-
"""Mapa de PROXIMIDAD A COSECHA en 5 zonas, desde los resultados persistidos de
orden_cosecha (sin GEE): clasifica el raster NDMI de cada lote con el nivel anclado
en la referencia seca de ESA corrida (p90) y bordes 0,12/0,20/0,35, con hectareas
por zona normalizadas al area oficial del lote (el raster recortado trae halo de
borde que infla 13-17 % en lotes angostos).

Anclas de campo (29-ago-2026, corregidas 30-ago por el cliente): 'trillable'
(<= ref p90) salio a ~18 % de humedad = INICIO de ventana de trilla (16-18 %
Embrapa), PH 78; NDMI ~0,16 ('cerca') estaba a 23 %; promedio de la parte alta
de Sao Francisco: 20 %. Los 'dias' asumen la tasa de secado medida
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


# ================================================================= variabilidad FINA
# Correccion de campo 02-sep-2026: en zonas pintadas de un solo 'marron' el cliente midio
# 24 % de humedad donde el mapa sugeria ~18 %. Dos defectos: (1) una sola clase bajo el
# nivel de referencia aplastaba toda la variabilidad del rango seco; (2) el suavizado
# 'para lectura' borraba el pixel. Y un LIMITE FISICO: la banda de agua ve el DOSEL/paja,
# no el grano — en el extremo seco pierde sensibilidad (18-24 % de grano caben en el
# mismo 'seco espectral'). Este mapa ORDENA (mas oscuro = mas seco = primero); el
# humedimetro certifica. Escalon = 0,02 = repetibilidad medida (pixeles iguales dentro
# del ruido se unifican; los distintos conservan su tono). 20 m NATIVOS (B8A/B11), sin
# suavizar: los 10 m son solo de las bandas visibles.
BORDES_FINO = [-0.30, -0.06, -0.04, -0.02, 0.00, 0.02, 0.04, 0.068,
               0.09, 0.11, 0.13, 0.16, 0.20, 0.25, 0.30, 0.35, 0.45, 1.0]
COLS_FINO = ['#2B1704', '#4A2A0C', '#6B3E14', '#8A5522', '#A56E33', '#BE8A4C', '#D3A76B',
             '#E0781E', '#F0A030', '#F4C542', '#E8E060', '#BFD97A', '#8FC98A', '#5EB39A',
             '#3A9AA0', '#2A7A94', '#1F5A80']
TXT_F = {
 'es': dict(
    titulo='Variabilidad FINA del agua del dosel · %s · escena %s · 20 m nativos, SIN suavizar\n'
           'Más oscuro = más seco = cosechar primero · el satélite ORDENA, el humedímetro decide',
    chip=' %s · %.0f ha · NDMI p10 %+.2f · p50 %+.2f · p90 %+.2f ',
    cbar='NDMI (agua del dosel) · escalones de 0,02 = ruido de medición',
    caja=('MEDIDO A CAMPO dentro del rango marrón: 18 % y 24 % de humedad de grano.\n'
          'La banda de agua ve la PAJA, no el grano: en el extremo seco pierde sensibilidad.\n'
          'Usar el orden (oscuro → claro) para elegir por dónde entrar; medir humedad SIEMPRE.'),
    flecha='cosechar\nprimero'),
 'pt': dict(
    titulo='Variabilidade FINA da água do dossel · %s · cena %s · 20 m nativos, SEM suavizar\n'
           'Mais escuro = mais seco = colher primeiro · o satélite ORDENA, o medidor de umidade decide',
    chip=' %s · %.0f ha · NDMI p10 %+.2f · p50 %+.2f · p90 %+.2f ',
    cbar='NDMI (água do dossel) · degraus de 0,02 = ruído de medição',
    caja=('MEDIDO NO CAMPO dentro da faixa marrom: 18 % e 24 % de umidade do grão.\n'
          'A banda de água vê a PALHA, não o grão: no extremo seco perde sensibilidade.\n'
          'Usar a ordem (escuro → claro) para escolher por onde entrar; medir umidade SEMPRE.'),
    flecha='colher\nprimeiro'),
}


def render_fino(res, ndmi20, rgb_z, out, idioma='es'):
    """ndmi20: {lid: (array_20m, ext)} · rgb_z: dict {lid|rgb, lid|rgb_ext} (npz)."""
    from matplotlib.colors import ListedColormap, BoundaryNorm
    T = TXT_F[idioma]
    cmap = ListedColormap(COLS_FINO); norm = BoundaryNorm(BORDES_FINO, len(COLS_FINO))
    lotes = res['lotes']
    n = len(lotes); cols = 2; rows = (n + 1) // 2
    fig, axs = plt.subplots(rows, cols, figsize=(13.5, 5.7 * rows), facecolor='white')
    axs = np.atleast_1d(axs).ravel()
    for ax in axs[n:]:
        ax.axis('off')
    im = None
    for ax, r in zip(axs, lotes):
        lid = r['id']
        nd, ext = ndmi20[lid]
        rgb, extr = rgb_z[f'{lid}|rgb'], list(rgb_z[f'{lid}|rgb_ext'])
        lat = (ext[2] + ext[3]) / 2
        fin = np.isfinite(nd)
        p10, p50, p90 = np.percentile(nd[fin], [10, 50, 90])
        if rgb.ndim == 3 and rgb.shape[2] in (3, 4):
            ax.imshow(rgb, extent=extr, origin='upper', zorder=0)
        im = ax.imshow(np.ma.masked_invalid(nd), extent=ext, origin='upper',
                       cmap=cmap, norm=norm, interpolation='nearest', zorder=2, alpha=0.97)
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
        ax.set_title(T['chip'] % (lid, r['area'], p10, p50, p90),
                     fontsize=10.5, fontweight='bold', color='white', loc='left',
                     bbox=dict(boxstyle='square,pad=0.4', fc='#0D9488', ec='none'), pad=6)
    fig.subplots_adjust(left=0.02, right=0.85, top=0.90, bottom=0.13, wspace=0.05, hspace=0.14)
    cax = fig.add_axes([0.885, 0.20, 0.018, 0.62])
    cb = fig.colorbar(im, cax=cax, orientation='vertical')
    cb.set_ticks([-0.06, -0.02, 0.02, 0.068, 0.11, 0.16, 0.25, 0.35, 0.45])
    cb.set_ticklabels(['-0,06', '-0,02', '+0,02', 'ref.', '0,11', '0,16', '0,25', '0,35', '0,45'])
    cb.ax.tick_params(labelsize=8.5)
    cb.set_label(T['cbar'], fontsize=9)
    cb.ax.annotate(T['flecha'], xy=(0.5, -0.02), xycoords='axes fraction', xytext=(0.5, -0.11),
                   ha='center', va='top', fontsize=8.5, fontweight='bold',
                   arrowprops=dict(arrowstyle='->', lw=1.4))
    fig.text(0.5, 0.045, T['caja'], ha='center', va='center', fontsize=9.5,
             bbox=dict(boxstyle='round,pad=0.5', fc='#FFF6E5', ec='#B8860B', lw=1.2))
    fig.suptitle(T['titulo'] % (res['nombre'], res['fecha']), fontsize=12.5, fontweight='bold', y=0.985)
    plt.savefig(out, dpi=160, bbox_inches='tight', facecolor='white'); plt.close()


def cargar_ndmi20(res, salida_dir):
    d = {}
    for r in res['lotes']:
        lid = r['id']
        a = np.load(os.path.join(salida_dir, f"ndmi20m_{lid}_{res['fecha']}.npy"))
        ext = json.load(open(os.path.join(salida_dir, f"ndmi20m_{lid}_{res['fecha']}_ext.json")))
        d[lid] = (a, ext)
    return d
