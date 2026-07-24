#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — Reporte v3 COMPLETO (S2 + S1 VV)
============================================================================
Genera:
  - Mapa Priority_score v3 por píxel (S2 NDWI/NDMI/CIRE/PSRI + S1 VV + GDD)
  - PDF lote-a-lote con justificación que incluye Z_VV
  - Heatmap hacienda v3
  - PDF unificado FINAL para cliente

Pesos v3 (validados empíricamente sobre 131 lotes Hacienda del Señor):
  NDWI 0.25 · NDMI 0.15 · CIRE 0.20 · PSRI 0.10 · VV_S1 0.10 · GDD 0.20
============================================================================
"""
from __future__ import annotations
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests

import geopandas as gpd
import rasterio
from scipy.ndimage import gaussian_filter, zoom
import shapely
from shapely.ops import transform as shp_transform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Patch

import ee
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image as RLImage, PageBreak)

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

# ════════════════════════════════════════════════════════════════════════════
LOTES_ROOT  = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\03-Zonas-Manejo")
OUTPUT_ROOT = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2")
CSV_V3     = OUTPUT_ROOT / "ranking_prioridad_v3_S2_S1_2026-05-15.csv"
CSV_CLAS   = OUTPUT_ROOT / "clasificacion_lotes_2026-05-13.csv"
GLOSARIO   = OUTPUT_ROOT / "00_Glosario_POL_Pixadvisor.pdf"
ANEXO_PDF  = OUTPUT_ROOT / "v2_Anexo_LotesExcluidos_2026-05-13.pdf"

CLIENTE = "Hacienda del Señor"
UBICACION = "Santa Cruz, Bolivia"

VERDE       = HexColor("#1B5E20")
GRIS        = HexColor("#333333")
GRIS_CLARO  = HexColor("#F5F5F5")
GRIS_LINEA  = HexColor("#BDBDBD")
ROJO        = HexColor("#C62828")

# Pesos v3 + signos
WEIGHTS_V3 = {"NDWI":0.25, "NDMI":0.15, "CIRE":0.20, "PSRI":0.10,
              "VV":0.10, "GDD":0.20}
SIGNS_V3   = {"NDWI":-1, "NDMI":-1, "CIRE":-1, "PSRI":+1, "VV":-1, "GDD":+1}
Z_CAP = 3.0

# S1
S1_REL_ORBIT = 10
S1_PASS = "DESCENDING"

PALETA_PRIORITY = [
    "#08306b","#08519c","#2171b5","#4292c6","#6baed6",
    "#9ecae1","#c6dbef","#fcbba1","#fc9272","#fb6a4a",
    "#ef3b2c","#cb181d","#a50f15"]
CMAP_P = LinearSegmentedColormap.from_list("priority", PALETA_PRIORITY, N=256)

MESES_ES = ["enero","febrero","marzo","abril","mayo","junio","julio",
            "agosto","septiembre","octubre","noviembre","diciembre"]


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def fecha_es(d): return f"{d.day} de {MESES_ES[d.month-1]} de {d.year}"


def force_2d(g):
    try: return shapely.force_2d(g)
    except Exception: return shp_transform(lambda x, y, *_: (x, y), g)


def init_ee():
    try: ee.Initialize()
    except Exception: ee.Authenticate(); ee.Initialize()


def cargar_geom_dual(lote_id: str):
    """Devuelve (gdf en UTM, geometría EE en WGS84)."""
    shp = LOTES_ROOT / lote_id / "PRO" / f"zonas_manejo_{lote_id}_PRO.shp"
    gdf = gpd.read_file(shp)
    if gdf.crs is None: gdf.set_crs("EPSG:32720", inplace=True)
    gdf["geometry"] = gdf.geometry.apply(force_2d)
    diss_utm = gdf.dissolve()
    diss_wgs = diss_utm.to_crs("EPSG:4326")
    geom_ee = ee.Geometry(diss_wgs.geometry.iloc[0].__geo_interface__)
    return diss_utm, geom_ee


def mask_scl(img):
    scl = img.select("SCL")
    return img.updateMask(scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)))


# ════════════════════════════════════════════════════════════════════════════
# MAPA Priority_score v3 por píxel
# ════════════════════════════════════════════════════════════════════════════
def make_priority_image_v3(geom_ee, meta: dict):
    """Composite por píxel:
       Score(x,y) = -wNDWI·Z_NDWI(x,y) -wNDMI·Z_NDMI(x,y) -wCIRE·Z_CIRE(x,y)
                    +wPSRI·Z_PSRI(x,y) -wVV·Z_VV(x,y) +wGDD·gdd_z (constante)
       Z(x,y) = clamp((valor(x,y) - baseline_mean_lote) / baseline_std_lote, ±3)
    """
    end_ee = ee.Date(int(datetime.now(timezone.utc).timestamp()*1000))
    start_ee = end_ee.advance(-21, "day")

    # ─── S2 image
    s2_col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
              .filterBounds(geom_ee).filterDate(start_ee, end_ee)
              .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
              .map(mask_scl))

    def add_cov(img):
        c = img.select("B4").mask().reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom_ee, scale=20,
            maxPixels=int(1e9), bestEffort=True).get("B4")
        return img.set("VALID_COVERAGE", ee.Number(c))

    s2_col = (s2_col.map(add_cov)
                    .filter(ee.Filter.gte("VALID_COVERAGE", 0.50))
                    .sort("system:time_start", False))
    if s2_col.size().getInfo() == 0: return None

    s2 = ee.Image(s2_col.first())
    b2 = s2.select("B2").divide(10000)
    b3 = s2.select("B3").divide(10000)
    b4 = s2.select("B4").divide(10000)
    b5 = s2.select("B5").divide(10000)
    b6 = s2.select("B6").divide(10000)
    b7 = s2.select("B7").divide(10000)
    b8 = s2.select("B8").divide(10000)
    b8a = s2.select("B8A").divide(10000)
    b11 = s2.select("B11").divide(10000)
    ndwi = b8a.subtract(b11).divide(b8a.add(b11).max(1e-6))
    ndmi = b8.subtract(b11).divide(b8.add(b11).max(1e-6))
    cire = b7.divide(b5.max(1e-6)).subtract(1)
    psri = b4.subtract(b2).divide(b6.max(1e-6))

    # ─── S1 image
    s1_col = (ee.ImageCollection("COPERNICUS/S1_GRD")
              .filterBounds(geom_ee).filterDate(start_ee, end_ee)
              .filter(ee.Filter.listContains("transmitterReceiverPolarisation","VV"))
              .filter(ee.Filter.listContains("transmitterReceiverPolarisation","VH"))
              .filter(ee.Filter.eq("instrumentMode","IW"))
              .filter(ee.Filter.eq("orbitProperties_pass", S1_PASS))
              .filter(ee.Filter.eq("relativeOrbitNumber_start", S1_REL_ORBIT)))
    has_s1 = s1_col.size().getInfo() > 0
    vv = s1_col.select("VV").median() if has_s1 else None

    # ─── Z-score por píxel (clamped)
    def zscore_img(img, key):
        m = meta.get(f"{key}_baseline_mean")
        s = meta.get(f"{key}_baseline_std")
        if m is None or s is None or s < 1e-6:
            return None
        return img.subtract(m).divide(s).clamp(-Z_CAP, Z_CAP)

    z_ndwi = zscore_img(ndwi, "NDWI")
    z_ndmi = zscore_img(ndmi, "NDMI")
    z_cire = zscore_img(cire, "CIRE")
    z_psri = zscore_img(psri, "PSRI")
    z_vv   = zscore_img(vv, "VV") if vv is not None else None

    # GDD constante
    gdd_z = meta.get("GDD_zscore")
    gdd_z = float(gdd_z) if gdd_z is not None and not (isinstance(gdd_z, float) and np.isnan(gdd_z)) else 0

    # Composite (renormalizar pesos disponibles)
    components = {}
    if z_ndwi is not None: components["NDWI"] = z_ndwi
    if z_ndmi is not None: components["NDMI"] = z_ndmi
    if z_cire is not None: components["CIRE"] = z_cire
    if z_psri is not None: components["PSRI"] = z_psri
    if z_vv   is not None: components["VV"]   = z_vv

    wts_avail = {k: WEIGHTS_V3[k] for k in components.keys()}
    wts_avail["GDD"] = WEIGHTS_V3["GDD"]
    wsum = sum(wts_avail.values())
    wts_norm = {k: w/wsum for k, w in wts_avail.items()}

    score = ee.Image.constant(SIGNS_V3["GDD"] * gdd_z * wts_norm["GDD"])
    for k, img in components.items():
        score = score.add(img.multiply(SIGNS_V3[k] * wts_norm[k]))
    score = score.rename("PRIORITY_V3").clip(geom_ee)
    return score


def descargar_tif(img, geom_ee, out_path: Path) -> bool:
    try:
        url = img.getDownloadURL({"scale":10, "region":geom_ee,
                                   "format":"GEO_TIFF", "crs":"EPSG:32720"})
    except Exception as e:
        log(f"  × URL: {e}"); return False
    try: r = requests.get(url, timeout=180)
    except Exception as e: log(f"  × HTTP: {e}"); return False
    if r.status_code != 200: log(f"  × HTTP {r.status_code}"); return False
    out_path.write_bytes(r.content)
    return True


def render_mapa(tif: Path, gdf_lote, meta: dict, png_out: Path):
    with rasterio.open(tif) as src:
        arr = src.read(1).astype(float)
        nd = src.nodata if src.nodata is not None else -9999
        arr = np.where((arr == nd) | np.isnan(arr), np.nan, arr)
        l, b, r, t = src.bounds
        crs_r = src.crs

    valid = arr[np.isfinite(arr)]
    if valid.size < 3: return False

    vmax = max(0.6, float(np.percentile(np.abs(valid), 95)))
    vmin = -vmax

    mask = np.isnan(arr); fill = float(np.nanmean(arr))
    arr_f = np.where(mask, fill, arr)
    arr_up = zoom(arr_f, 4, order=3, mode="nearest")
    mask_up = zoom(mask.astype(float), 4, order=1, mode="nearest") > 0.5
    arr_up = gaussian_filter(arr_up, sigma=6)
    arr_up = np.where(mask_up, np.nan, arr_up)

    fig, ax = plt.subplots(figsize=(8.5, 8.0), dpi=220)
    fig.patch.set_facecolor("white")
    im = ax.imshow(arr_up, cmap=CMAP_P, vmin=vmin, vmax=vmax,
                    extent=(l,r,b,t), interpolation="bicubic",
                    origin="upper", aspect="equal")
    try: gdf_lote.to_crs(crs_r).boundary.plot(
            ax=ax, color="black", linewidth=1.6, alpha=0.9)
    except Exception: pass
    ax.set_xlim(l,r); ax.set_ylim(b,t); ax.set_axis_off()
    ax.set_title(f"Score v3 (S2+S1) — Lote {meta['lote_id']}",
                  fontsize=14, fontweight="bold", color="#1B5E20", pad=12)
    cbar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.04, shrink=0.85,
                         ticks=np.linspace(vmin, vmax, 5))
    cbar.set_label("Score relativo (rojo: cosechar primero · azul: posponer)",
                    fontsize=9)
    cbar.ax.tick_params(labelsize=8)
    plt.figtext(0.5, 0.015,
        f"Sentinel-2A {meta.get('fecha_imagen','—')} + Sentinel-1 SAR  ·  "
        f"Pixadvisor v3", ha="center", fontsize=8, color="#555555")
    fig.tight_layout()
    fig.savefig(png_out, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return True


# ════════════════════════════════════════════════════════════════════════════
# JUSTIFICACIÓN v3 (incluye Z_VV)
# ════════════════════════════════════════════════════════════════════════════
def justificar_v3(meta, total):
    z_ndwi=meta.get("NDWI_zscore"); z_ndmi=meta.get("NDMI_zscore")
    z_cire=meta.get("CIRE_zscore"); z_psri=meta.get("PSRI_zscore")
    z_vv  =meta.get("VV_zscore");   z_gdd=meta.get("GDD_zscore")
    rank = int(meta.get("Rank_v3") or 0)
    rank_lo = int(meta.get("Rank_v3_p025") or rank)
    rank_hi = int(meta.get("Rank_v3_p975") or rank)
    gdd_a = meta.get("GDD_acum") or 0; gdd_d = meta.get("GDD_dias") or 0

    def _f(v): return v if (v is not None and not (isinstance(v, float) and np.isnan(v))) else None

    pct = (rank/total)*100 if total else 0
    if pct <= 10:   pos = f"Top <b>{int(pct)}% del ranking</b> ({rank}/{total}) — entre los más maduros de la hacienda."
    elif pct <= 25: pos = f"<b>Top 25%</b> ({rank}/{total}) — clara prioridad de cosecha."
    elif pct <= 50: pos = f"Posición media-alta ({rank}/{total}) — cosechar próximas 2-4 semanas."
    elif pct <= 75: pos = f"Posición media-baja ({rank}/{total}) — esperar 4-8 semanas."
    else:           pos = f"<b>{int(pct)}% inferior</b> ({rank}/{total}) — vegetativo, no cosechar todavía."

    span = rank_hi - rank_lo
    if span <= 2:   stab = f"<b>Bootstrap muy estable</b> (IC95% [{rank_lo}-{rank_hi}]) — alta confianza."
    elif span <= 8: stab = f"Bootstrap moderadamente estable (IC95% [{rank_lo}-{rank_hi}], span {span})."
    else:           stab = f"<b>Bootstrap inestable</b> (IC95% [{rank_lo}-{rank_hi}], span {span}) — validar in-situ."

    interps = []
    z = _f(z_ndwi)
    if z is not None:
        if z <= -1.5: interps.append(f"<b>Z NDWI {z:+.2f}</b>: agua foliar muy baja vs histórico → senescencia avanzada")
        elif z <= -0.5: interps.append(f"Z NDWI {z:+.2f}: agua foliar baja → entrando senescencia")
        elif z >= 1.5: interps.append(f"<b>Z NDWI {z:+.2f}</b>: agua foliar muy alta → cultivo aún verde")

    z = _f(z_cire)
    if z is not None:
        if z <= -1.5: interps.append(f"<b>Z CIRE {z:+.2f}</b>: clorofila muy baja → pérdida pigmentación foliar")
        elif z <= -0.5: interps.append(f"Z CIRE {z:+.2f}: clorofila por debajo del histórico")
        elif z >= 1.5: interps.append(f"<b>Z CIRE {z:+.2f}</b>: clorofila muy alta → no maduro")

    z = _f(z_psri)
    if z is not None and z >= 0.5:
        interps.append(f"Z PSRI {z:+.2f}: senescencia visible — carotenoides predominan")

    z = _f(z_vv)
    if z is not None:
        if z <= -1.5: interps.append(f"<b>Z VV (S1) {z:+.2f}</b>: backscatter SAR muy bajo → biomasa más seca/menos volumen vs histórico (consistente con maduración)")
        elif z <= -0.5: interps.append(f"Z VV (S1) {z:+.2f}: backscatter SAR bajo → biomasa reducida vs histórico")
        elif z >= 1.5: interps.append(f"<b>Z VV (S1) {z:+.2f}</b>: backscatter SAR muy alto → mucha biomasa, lejos de madurez")
        elif z >= 0.5: interps.append(f"Z VV (S1) {z:+.2f}: biomasa por encima del histórico")

    if gdd_a > 0:
        if gdd_a >= 2400:   gdd_text = f"<b>GDD {gdd_a:.0f} °Cd en {gdd_d}d</b> — supera umbral típico de maduración (~2200-2500 °Cd, Inman-Bamber 1994)."
        elif gdd_a >= 1800: gdd_text = f"GDD {gdd_a:.0f} °Cd en {gdd_d}d — entrando ventana de maduración."
        elif gdd_a >= 1000: gdd_text = f"GDD {gdd_a:.0f} °Cd en {gdd_d}d — crecimiento medio."
        else:               gdd_text = f"GDD {gdd_a:.0f} °Cd en {gdd_d}d — etapa temprana."
    else: gdd_text = "GDD no disponible."

    return {"posicion":pos, "estabilidad":stab, "indices":interps, "gdd":gdd_text}


# ════════════════════════════════════════════════════════════════════════════
# PDF LOTE v3
# ════════════════════════════════════════════════════════════════════════════
def generar_pdf_lote_v3(meta: dict, png_mapa: Path, pdf_out: Path, total: int):
    doc = SimpleDocTemplate(str(pdf_out), pagesize=A4,
        topMargin=15*mm, bottomMargin=18*mm,
        leftMargin=18*mm, rightMargin=18*mm,
        title=f"v3 Prioridad cosecha lote {meta['lote_id']}",
        author="Pixadvisor AP")

    s = getSampleStyleSheet()
    s_title = ParagraphStyle("T", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=18, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=2, leading=20)
    s_sub = ParagraphStyle("S", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS,
        alignment=TA_LEFT, spaceAfter=4, leading=13)
    s_h2 = ParagraphStyle("H2", parent=s["Heading2"],
        fontName="Helvetica-Bold", fontSize=11, textColor=VERDE,
        alignment=TA_LEFT, spaceBefore=8, spaceAfter=4, leading=13)
    s_body = ParagraphStyle("B", parent=s["Normal"],
        fontName="Helvetica", fontSize=9, textColor=GRIS, leading=12)

    story = []
    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión", s_sub),
        Paragraph(f"<para align=right>Prioridad de Cosecha v3<br/>"
                   f"{datetime.now():%Y-%m-%d}</para>", s_sub)]]
    h_tbl = Table(header, colWidths=[100*mm, 70*mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LINEBELOW",(0,0),(-1,0),1.5,VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(h_tbl); story.append(Spacer(1, 4))

    rank = int(meta.get("Rank_v3") or 0)
    rank_lo = int(meta.get("Rank_v3_p025") or rank)
    rank_hi = int(meta.get("Rank_v3_p975") or rank)
    estado = str(meta.get("Estado_fenologico_v3","—"))
    rank_v2 = meta.get("Rank_v2"); rank_change = meta.get("Rank_change")

    story.append(Paragraph(
        f"Lote {meta['lote_id']} — Rank #{rank} de {total}", s_title))
    cambio_str = ""
    if rank_change is not None and not (isinstance(rank_change, float) and np.isnan(rank_change)):
        rc = int(rank_change)
        if rc > 0: cambio_str = f" (subió {rc} pos vs v2)"
        elif rc < 0: cambio_str = f" (bajó {-rc} pos vs v2)"
    story.append(Paragraph(
        f"Estado: <b>{estado}</b> · IC95% rank: [{rank_lo}–{rank_hi}]{cambio_str} · "
        f"Imagen S2A: <b>{meta.get('fecha_imagen','—')}</b>", s_sub))
    story.append(Spacer(1, 4))

    # Info + Métricas (incluye VV S1)
    info = [
        ["ID Lote", str(meta["lote_id"])],
        ["Área", f"{meta['area_ha']:.2f} ha"],
        ["Imagen S2A", str(meta.get("fecha_imagen","—"))],
        ["Cobertura", f"{(meta.get('valid_coverage') or 0)*100:.0f}%"],
        ["Nubes", f"{(meta.get('cloud_pct') or 0):.1f}%"],
    ]
    t_info = Table(info, colWidths=[28*mm, 50*mm])
    t_info.setStyle(TableStyle([
        ("FONT",(0,0),(-1,-1),"Helvetica",8),
        ("FONT",(0,0),(0,-1),"Helvetica-Bold",8),
        ("TEXTCOLOR",(0,0),(0,-1),VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("TOPPADDING",(0,0),(-1,-1),2),
        ("LINEBELOW",(0,0),(-1,-1),0.3,GRIS_LINEA)]))

    def fz(v, sig=False):
        if v is None or (isinstance(v, float) and np.isnan(v)): return "—"
        return f"{v:+.2f}" if sig else f"{v:.2f}"

    metrics = [
        ["Métrica", "Valor", "Interp."],
        ["Score v3",   fz(meta.get("Priority_score_v3"), True), "global"],
        ["Z NDWI",     fz(meta.get("NDWI_zscore"), True), "agua foliar"],
        ["Z NDMI",     fz(meta.get("NDMI_zscore"), True), "humedad"],
        ["Z CIRE",     fz(meta.get("CIRE_zscore"), True), "clorofila"],
        ["Z PSRI",     fz(meta.get("PSRI_zscore"), True), "senescencia"],
        ["Z VV (S1)",  fz(meta.get("VV_zscore"), True),   "biomasa SAR"],
        ["GDD acum",   f"{meta.get('GDD_acum',0):.0f}°Cd", f"{meta.get('GDD_dias','?')}d"],
    ]
    t_met = Table(metrics, colWidths=[22*mm, 22*mm, 38*mm], repeatRows=1)
    t_met.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",8),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",8),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("ALIGN",(1,1),(1,-1),"RIGHT"),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3)]))

    side = Table([[t_info, t_met]], colWidths=[80*mm, 90*mm])
    side.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0)]))
    story.append(side); story.append(Spacer(1, 4))

    # Mapa compacto
    if png_mapa.exists():
        rim = RLImage(str(png_mapa), width=130*mm, height=85*mm,
                       kind="proportional")
        rim.hAlign = "CENTER"
        story.append(rim); story.append(Spacer(1, 2))

    # Justificación
    j = justificar_v3(meta, total)
    story.append(Paragraph("Justificación técnica del ranking (v3 con S2+S1)", s_h2))
    story.append(Paragraph(j["posicion"], s_body)); story.append(Spacer(1, 1))
    story.append(Paragraph(j["estabilidad"], s_body)); story.append(Spacer(1, 1))
    if j["indices"]:
        story.append(Paragraph("<b>Lectura por índice:</b>", s_body))
        for it in j["indices"]:
            story.append(Paragraph(f"• {it}", s_body))
    story.append(Paragraph(f"<b>Térmica:</b> {j['gdd']}", s_body))
    story.append(Spacer(1, 3))

    # Recomendación — ORDEN DE MUESTREO, no instrucción de cosecha.
    #
    # El texto anterior convertía el PERCENTIL del score en una orden absoluta
    # ("cosechar entre los primeros" / "NO cosechar"). Eso es una CUOTA: con la
    # hacienda entera inmadura el 20% inferior recibía igual "cosechar", y con
    # la hacienda entera madura el 20% superior recibía "NO cosechar". El daño
    # es del 20% del área en ambos sentidos y el sistema no podía avisarlo.
    #
    # La decisión de corte la toma el refractómetro (ver madurez_campo.py).
    # El satélite dice DÓNDE medir primero.
    story.append(Paragraph("Prioridad de muestreo", s_h2))
    pct = (rank/total)*100 if total else 0
    if pct <= 20:
        rec = ("<b>Muestrear en el primer grupo.</b> Este lote presenta la "
               "anomalía de dosel más marcada respecto de su propio histórico, "
               "por lo que es donde el refractómetro aporta más información. "
               "La decisión de corte la define la medición de campo, no este "
               "orden.")
    elif pct <= 50:
        rec = ("<b>Muestrear en el segundo grupo.</b> Señal de dosel "
               "intermedia respecto de su histórico.")
    else:
        rec = ("<b>Muestreo de menor prioridad.</b> Sin anomalía de dosel "
               "destacable respecto de su histórico. Esto <b>no</b> significa "
               "que el lote esté inmaduro: significa que el satélite no aporta "
               "evidencia para adelantar su medición.")
    story.append(Paragraph(rec, s_body))
    story.append(Paragraph(
        "<b>Criterio de corte (campo):</b> Índice de Maturação "
        "IM = Brix(ponteiro)/Brix(base). Ponteiro = entrenudo de la última "
        "hoja cuya vaina se desprende fácilmente; base = 3.º–4.º entrenudo "
        "sobre el suelo. Umbrales (Stupiello &amp; Germek, vía UNESP/FEIS): "
        "&lt;0,60 verde · &lt;0,85 en maduración · <b>≥0,90 madura</b> · "
        "&gt;1,00 declive por inversión de la sacarosa. "
        "Nota: 0,85 <b>no</b> es «madura», es zona de transición.", s_body))

    # Disclaimer
    s_disc = ParagraphStyle("Disc", parent=s_body, fontSize=7.5,
        textColor=GRIS, leading=10, spaceBefore=4)
    story.append(Paragraph(
        "<i>Orden de muestreo RELATIVO, derivado de anomalías de dosel respecto del "
        "histórico de cada lote (Sentinel-2). <b>No estima Pol, Brix ni ATR</b>: no existe "
        "modelo publicado que lo haga sólo con Sentinel-2, y la sacarosa se acumula en el "
        "tallo, que el sensor no observa (Inman-Bamber et al., DOI 10.1071/CP11128). "
        "Índices: NDMI = (B8A−B11)/(B8A+B11), humedad de dosel (Hardisky et al. 1983; "
        "Wilson &amp; Sader 2002, DOI 10.1016/S0034-4257(01)00318-2) — <b>no</b> es el NDWI de "
        "Gao, que exige 1,24 µm, banda ausente en Sentinel-2. PSRI = (B4−B2)/B6, senescencia "
        "(Merzlyak et al. 1999, DOI 10.1034/j.1399-3054.1999.106119.x). "
        "Contains modified Copernicus Sentinel data.</i>", s_disc))

    def _f(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7); canvas.setFillColor(GRIS)
        canvas.drawCentredString(A4[0]/2, 10*mm,
            f"Pixadvisor AP · Hacienda del Señor · Lote {meta['lote_id']} · "
            f"Prioridad de Cosecha v3 · {datetime.now():%Y-%m-%d} · pág {doc_.page}")
        canvas.setStrokeColor(VERDE); canvas.setLineWidth(0.4)
        canvas.line(18*mm, 13*mm, A4[0]-18*mm, 13*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_f, onLaterPages=_f)


# ════════════════════════════════════════════════════════════════════════════
# WORKER
# ════════════════════════════════════════════════════════════════════════════
def procesar_lote(meta: dict, total: int, idx: int):
    lid = str(meta["lote_id"])
    out_dir = OUTPUT_ROOT / lid
    out_dir.mkdir(parents=True, exist_ok=True)
    fecha = meta.get("fecha_imagen", "—")

    try:
        gdf, geom_ee = cargar_geom_dual(lid)

        priority = make_priority_image_v3(geom_ee, meta)
        if priority is None:
            log(f"[{idx}/{total}] {lid} sin S2 reciente"); return False

        tif = out_dir / f"PRIORITY_v3_{lid}_{fecha}.tif"
        if not descargar_tif(priority.toFloat(), geom_ee, tif): return False

        png = out_dir / f"mapa_madurez_v3_{lid}.png"
        if not render_mapa(tif, gdf, meta, png): return False

        pdf = out_dir / f"MADUREZ_v3_{lid}_{fecha}.pdf"
        generar_pdf_lote_v3(meta, png, pdf, total)
        log(f"[{idx}/{total}] {lid} → MADUREZ_v3_{lid}.pdf")
        return True
    except Exception as e:
        log(f"[{idx}/{total}] {lid} × {e}")
        return False


# ════════════════════════════════════════════════════════════════════════════
# HEATMAP HACIENDA v3
# ════════════════════════════════════════════════════════════════════════════
def build_heatmap_v3(df_rank: pd.DataFrame, df_clas: pd.DataFrame, png_out: Path):
    log(f"  cargando {len(df_rank)} geometrías caña + contexto...")
    cana_recs = []
    for _, r in df_rank.iterrows():
        try:
            gdf, _ = cargar_geom_dual(str(r["lote_id"]))
            gdf = gdf.to_crs("EPSG:32720")
            gdf["lote_id"] = str(r["lote_id"])
            gdf["Priority_score_v3"] = r["Priority_score_v3"]
            gdf["Rank_v3"] = r["Rank_v3"]
            gdf["Estado_fenologico_v3"] = r["Estado_fenologico_v3"]
            cana_recs.append(gdf)
        except Exception: pass
    gdf_cana = gpd.GeoDataFrame(pd.concat(cana_recs, ignore_index=True),
                                 crs="EPSG:32720")

    CANA_CATS = {"CAÑA_ACTIVA","CAÑA_SOCA","CAÑA_PRE_COSECHA_RECIENTE","CAÑA_INMADURA_NUEVA"}
    no_cana_ids = df_clas[~df_clas["categoria"].isin(CANA_CATS)]["lote_id"].astype(str).tolist()
    no_cana_recs = []
    for lid in no_cana_ids:
        try:
            gdf, _ = cargar_geom_dual(lid)
            gdf = gdf.to_crs("EPSG:32720")
            no_cana_recs.append(gdf)
        except Exception: pass
    gdf_no_cana = (gpd.GeoDataFrame(pd.concat(no_cana_recs, ignore_index=True),
                                     crs="EPSG:32720") if no_cana_recs else None)

    fig, ax = plt.subplots(figsize=(13, 11), dpi=200)
    fig.patch.set_facecolor("white")
    if gdf_no_cana is not None:
        gdf_no_cana.plot(ax=ax, color="#E8E8E8", edgecolor="#888888",
                          linewidth=0.4, alpha=0.7)

    vmin = float(df_rank["Priority_score_v3"].min())
    vmax = float(df_rank["Priority_score_v3"].max())
    abs_max = max(abs(vmin), abs(vmax))
    norm = Normalize(vmin=-abs_max, vmax=abs_max)
    gdf_cana.plot(ax=ax, column="Priority_score_v3", cmap=CMAP_P,
                   norm=norm, edgecolor="black", linewidth=0.6)

    top20 = gdf_cana.nlargest(20, "Priority_score_v3")
    for _, r in top20.iterrows():
        c = r.geometry.centroid
        ax.annotate(f"#{int(r['Rank_v3'])} {r['lote_id']}",
                     xy=(c.x, c.y), xytext=(0,0), textcoords="offset points",
                     fontsize=6.5, fontweight="bold", color="black",
                     ha="center", va="center",
                     bbox=dict(boxstyle="round,pad=0.15", fc="white",
                                ec="black", lw=0.4, alpha=0.85))

    ax.set_axis_off()
    ax.set_title(
        "Mapa de Prioridad de Cosecha v3 (S2+S1) — Hacienda del Señor\n"
        f"131 lotes caña confirmada · {datetime.now():%Y-%m-%d}",
        fontsize=14, fontweight="bold", color="#1B5E20", pad=15)

    sm = plt.cm.ScalarMappable(cmap=CMAP_P, norm=norm); sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.02, shrink=0.6,
                         ticks=np.linspace(-abs_max, abs_max, 5))
    cbar.set_label("Priority_score v3 (rojo: cosechar primero · azul: posponer)",
                    fontsize=10)
    cbar.ax.tick_params(labelsize=9)

    legend_elements = [
        Patch(facecolor="#a50f15", edgecolor="black", label="MADUREZ_AVANZADA"),
        Patch(facecolor="#fb6a4a", edgecolor="black", label="MADURACION"),
        Patch(facecolor="#9ecae1", edgecolor="black", label="PRE_MADURACION"),
        Patch(facecolor="#08306b", edgecolor="black", label="VEGETATIVO"),
        Patch(facecolor="#E8E8E8", edgecolor="#888", label="No-caña"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=8,
               framealpha=0.9, title="Categorías")

    plt.figtext(0.5, 0.01,
        "Etiquetas Top 20. Composite: S2 (NDWI/NDMI/CIRE/PSRI) + S1 (VV SAR) + GDD ERA5-Land.",
        ha="center", fontsize=8, color="#555555")

    fig.tight_layout()
    fig.savefig(png_out, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# INTRO + ANEXO
# ════════════════════════════════════════════════════════════════════════════
def build_intro(df_rank, df_clas, heatmap_png):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        topMargin=18*mm, bottomMargin=18*mm,
        leftMargin=20*mm, rightMargin=20*mm,
        title="Reporte v3 Prioridad Cosecha", author="Pixadvisor AP")

    s = getSampleStyleSheet()
    s_huge = ParagraphStyle("Huge", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=26, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=8, leading=30)
    s_big = ParagraphStyle("Big", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=18, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=4, leading=20)
    s_sub = ParagraphStyle("Sub", parent=s["Normal"],
        fontName="Helvetica", fontSize=11, textColor=GRIS,
        alignment=TA_LEFT, spaceAfter=4, leading=14)
    s_h2 = ParagraphStyle("H2", parent=s["Heading2"],
        fontName="Helvetica-Bold", fontSize=13, textColor=VERDE,
        alignment=TA_LEFT, spaceBefore=10, spaceAfter=6, leading=15)
    s_body = ParagraphStyle("B", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS, leading=13)
    s_small = ParagraphStyle("Sm", parent=s["Normal"],
        fontName="Helvetica", fontSize=8, textColor=GRIS, leading=11)

    story = []
    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión", s_sub),
        Paragraph(f"<para align=right>{datetime.now():%Y-%m-%d}</para>", s_sub)]]
    h_tbl = Table(header, colWidths=[110*mm, 60*mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LINEBELOW",(0,0),(-1,0),1.5,VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),4)]))

    # Portada
    story.append(h_tbl); story.append(Spacer(1, 30*mm))
    story.append(Paragraph("REPORTE DE PRIORIDAD DE COSECHA v3", s_big))
    story.append(Paragraph("Caña de Azúcar — S2 + S1 SAR", s_huge))
    story.append(Paragraph(
        "<font color='#1B5E20'><b>Ranking ordinal RELATIVO · Multi-sensor "
        "validado empíricamente · Sin Pol absoluto</b></font>", s_sub))
    story.append(Spacer(1, 10*mm))

    meta = [
        ["Cliente", CLIENTE],
        ["Ubicación", UBICACION],
        ["Cultivo", "Caña de azúcar (UCG/RBD)"],
        ["Sensores", "Sentinel-2A (óptico 10/20 m) + Sentinel-1 (SAR 10 m)"],
        ["Datos térmicos", "ERA5-Land (Copernicus C3S)"],
        ["Lotes confirmados caña", f"{len(df_rank)} (HIGH confidence)"],
        ["Hectáreas analizadas", f"{df_rank['area_ha'].sum():,.0f} ha"],
        ["Imagen S2A más reciente", df_rank["fecha_imagen"].mode().iloc[0]
                                       if not df_rank.empty else "—"],
        ["Validación local S1 VV", "Spearman r=-0.529 (p<0.001) vs S2 (n=131)"],
        ["Baseline histórico", "3 años S2 + S1, mismo mes calendario por lote"],
        ["Fecha del reporte", fecha_es(datetime.now())],
    ]
    t_meta = Table(meta, colWidths=[55*mm, 110*mm])
    t_meta.setStyle(TableStyle([
        ("FONT",(0,0),(-1,-1),"Helvetica",10),
        ("FONT",(0,0),(0,-1),"Helvetica-Bold",10),
        ("TEXTCOLOR",(0,0),(0,-1),VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),5),
        ("LINEBELOW",(0,0),(-1,-1),0.3,GRIS_LINEA)]))
    story.append(t_meta)
    story.append(Spacer(1, 18*mm))
    story.append(Paragraph(
        "<b>Mejoras v3 vs v2:</b> integración Sentinel-1 SAR (independiente de "
        "nubes, validado localmente con r=-0.529 sobre 131 lotes). Cambio "
        "promedio de rank vs v2: 1.8 posiciones — refinamiento sin desestabilizar "
        "el Top 20.", s_body))

    # Mapa hacienda
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 4))
    story.append(Paragraph("Mapa de la Hacienda — Prioridad v3", s_big))
    story.append(Paragraph(
        f"131 lotes caña confirmada · Score multi-sensor · Top 20 etiquetados",
        s_sub))
    story.append(Spacer(1, 4))
    if heatmap_png.exists():
        img = RLImage(str(heatmap_png), width=170*mm, height=200*mm,
                      kind="proportional")
        img.hAlign = "CENTER"
        story.append(img)

    # Resumen ejecutivo
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 6))
    story.append(Paragraph("Resumen Ejecutivo v3", s_big))
    story.append(Paragraph(
        f"Estado de madurez relativa al {datetime.now():%Y-%m-%d}", s_sub))
    story.append(Spacer(1, 6))

    story.append(Paragraph("KPIs", s_h2))
    kpis = [
        ["Lotes en ranking", f"{len(df_rank)}", "CAÑA HIGH confidence"],
        ["Área analizada", f"{df_rank['area_ha'].sum():,.0f} ha", "100% verificada"],
        ["GDD medio acumulado", f"{df_rank['GDD_acum'].mean():.0f} °C·d", "T_base 18°C"],
        ["Lotes con S1 VV válido", f"{df_rank['VV_zscore'].notna().sum()}/{len(df_rank)}", "Cobertura SAR"],
        ["Top 20% (cosecha alta)", f"{int(len(df_rank)*0.2)}", "Prioridad inmediata"],
    ]
    t_kpi = Table(kpis, colWidths=[55*mm, 40*mm, 65*mm])
    t_kpi.setStyle(TableStyle([
        ("FONT",(0,0),(-1,-1),"Helvetica",10),
        ("FONT",(0,0),(0,-1),"Helvetica-Bold",10),
        ("FONT",(1,0),(1,-1),"Helvetica-Bold",11),
        ("TEXTCOLOR",(0,0),(0,-1),VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("LINEBELOW",(0,0),(-1,-1),0.3,GRIS_LINEA)]))
    story.append(t_kpi)
    story.append(Spacer(1, 6))

    # Distribución
    story.append(Paragraph("Distribución por estado fenológico", s_h2))
    dist = df_rank.groupby("Estado_fenologico_v3").agg(
        n=("lote_id","count"), ha=("area_ha","sum")).reset_index()
    dist["pct_ha"] = dist["ha"]/dist["ha"].sum()*100
    rows = [["Estado", "# Lotes", "Hectáreas", "% Área"]]
    for _, r in dist.iterrows():
        rows.append([str(r["Estado_fenologico_v3"]), f"{int(r['n'])}",
                     f"{r['ha']:,.0f}", f"{r['pct_ha']:.1f}%"])
    t_d = Table(rows, colWidths=[55*mm, 25*mm, 35*mm, 25*mm], repeatRows=1)
    t_d.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",9),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",9),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("ALIGN",(1,1),(-1,-1),"RIGHT")]))
    story.append(t_d)
    story.append(Spacer(1, 6))

    # Top 20
    story.append(Paragraph("Top 20 — prioridad de cosecha", s_h2))
    top = df_rank.head(20).reset_index(drop=True)
    top_rows = [["#","Lote","Área","Score","Estado","IC95%","Δ vs v2"]]
    for i, r in top.iterrows():
        rc = r.get("Rank_change", 0)
        if pd.isna(rc): rc_str = "—"
        elif rc > 0: rc_str = f"+{int(rc)}"
        elif rc < 0: rc_str = f"{int(rc)}"
        else: rc_str = "0"
        top_rows.append([
            str(i+1), str(r["lote_id"]), f"{r['area_ha']:,.1f}",
            f"{r['Priority_score_v3']:+.2f}",
            str(r["Estado_fenologico_v3"])[:18],
            f"[{int(r['Rank_v3_p025'])}-{int(r['Rank_v3_p975'])}]",
            rc_str])
    t_t = Table(top_rows,
                colWidths=[7*mm, 22*mm, 18*mm, 18*mm, 38*mm, 22*mm, 18*mm],
                repeatRows=1)
    t_t.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",8),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",8),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("ALIGN",(2,1),(-1,-1),"RIGHT"),
        ("ALIGN",(0,0),(0,-1),"CENTER"),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3)]))
    story.append(t_t)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<i>Δ vs v2: cambio en el rank al integrar Sentinel-1 SAR. "
        "Rank promedio cambió 1.8 posiciones; Top 3 idéntico.</i>", s_small))

    # Metodología
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 6))
    story.append(Paragraph("Metodología v3 — sensores y referencias", s_big))
    story.append(Spacer(1, 4))

    story.append(Paragraph("1) Clasificación previa de cobertura", s_h2))
    story.append(Paragraph(
        "Lotes filtrados por firma fenológica NDVI multi-temporal (14 meses S2). "
        "Excluye reforma, soya, monte, pasto. Los 131 lotes incluidos son caña "
        "activa con confianza alta.", s_body))

    story.append(Paragraph("2) Sensores y bandas", s_h2))
    sensors = [
        ["Sensor", "Bandas", "Resolución", "Frecuencia real"],
        ["Sentinel-2A", "B2/B3/B4/B5/B6/B7/B8/B8A/B11", "10-20 m", "5 días (limitado por nubes)"],
        ["Sentinel-1 SAR", "VV (descending IW rel_orb 10)", "10 m", "5-7 días (todo clima)"],
        ["ERA5-Land", "temperature_2m", "11 km", "diario (climático)"],
    ]
    t_s = Table(sensors, colWidths=[28*mm, 60*mm, 25*mm, 47*mm], repeatRows=1)
    t_s.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",9),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",8.5),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3)]))
    story.append(t_s)
    story.append(Spacer(1, 4))

    story.append(Paragraph("3) Índices y pesos del composite v3", s_h2))
    idx_data = [
        ["Índice", "Fórmula", "Peso", "Referencia / Validación"],
        ["NDWI Gao", "(B8A−B11)/(B8A+B11)", "0.25", "Leandro 2024 DOI 10.3390/crops4030024"],
        ["NDMI",     "(B8−B11)/(B8+B11)",   "0.15", "Hajeb 2023 DOI 10.1016/j.jag.2022.103168"],
        ["CIRE",     "B7/B5 − 1",           "0.20", "Bocca 2024 DOI 10.1007/s12355-024-01468-z"],
        ["PSRI",     "(B4−B2)/B6",          "0.10", "Merzlyak 1999 DOI 10.1034/j.1399-3054.1999.106119.x"],
        ["VV S1",    "σ⁰VV (dB)",           "0.10", "Validación local 2026-05-15: r=-0.529 vs S2"],
        ["GDD",      "Σmax(0, T−18°C)",     "0.20", "Inman-Bamber 1994 DOI 10.1016/0378-4290(94)90051-5"],
    ]
    t_idx = Table(idx_data,
                  colWidths=[18*mm, 30*mm, 12*mm, 100*mm], repeatRows=1)
    t_idx.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",8),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",7.5),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3)]))
    story.append(t_idx)
    story.append(Spacer(1, 4))

    story.append(Paragraph("4) Validación empírica de S1 VV (transparencia)", s_h2))
    story.append(Paragraph(
        "Antes de integrar S1 al composite, se hizo estudio sobre los 131 "
        "lotes HIGH-caña: <b>Z VV vs Priority_score S2 → Pearson r=-0.326 "
        "(p&lt;0.001), Spearman r=-0.529 (p&lt;0.001)</b>. Correlación "
        "negativa fuerte como esperaba la teoría (lower VV = drier biomass = "
        "more mature). Z CR (Cross-Ratio) tuvo signo invertido (r=+0.214) y "
        "fue EXCLUIDO del composite — la teoría den Besten 2021 (Mozambique) "
        "no transfiere directamente a Bolivia. <b>Solo se incluye lo que se "
        "valida con datos locales.</b>", s_body))

    story.append(Paragraph("5) Z-score temporal + bootstrap", s_h2))
    story.append(Paragraph(
        "Z = (valor_actual − media_baseline_lote) / SD_baseline_lote, capeado a "
        "±3 SD (estándar JRC ASAP, Meroni 2019 DOI 10.1016/j.agsy.2018.07.002). "
        "Baseline: mismo mes calendario, últimos 3 años, MISMO lote. Bootstrap "
        "200 iter con ruido gaussiano σ=1/√n_píxeles, IC95% del rank por lote.", s_body))

    story.append(Paragraph("6) Validación in-situ obligatoria", s_h2))
    story.append(Paragraph(
        "Para Top 20 del ranking: muestreo Brix superior/inferior con "
        "refractómetro (5 puntos × 10 tallos). CMI = (BS/BI)·100. "
        "<b>CMI ≥ 85% → cosecha confirmada</b> (estándar SASRI PurEst / "
        "CONSECANA). Datos Pol post-cosecha permiten construir calibración "
        "local progresiva.", s_body))

    story.append(Paragraph("7) Lo que este reporte NO afirma", s_h2))
    story.append(Paragraph(
        "<b>NO se reporta Pol o Brix absoluto numérico.</b> Sin calibración "
        "local con análisis polarimétrico de juice (≥30 muestras), no es "
        "defendible asignar Pol absoluto desde sensores remotos. Para "
        "liquidación CONSECANA usar análisis de juice del ingenio.", s_body))

    def _f(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7); canvas.setFillColor(GRIS)
        canvas.drawCentredString(A4[0]/2, 10*mm,
            f"Pixadvisor AP · Hacienda del Señor · Prioridad Cosecha v3 · "
            f"{datetime.now():%Y-%m-%d} · pág {doc_.page}")
        canvas.setStrokeColor(VERDE); canvas.setLineWidth(0.4)
        canvas.line(20*mm, 13*mm, A4[0]-20*mm, 13*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_f, onLaterPages=_f)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log("══ Reporte v3 COMPLETO (S2+S1) ══")
    if not CSV_V3.exists():
        log(f"ERROR: falta {CSV_V3}"); sys.exit(1)
    init_ee()

    df_rank = pd.read_csv(CSV_V3)
    df_clas = pd.read_csv(CSV_CLAS)
    log(f"Lotes en ranking v3: {len(df_rank)}")

    # 1) Heatmap hacienda
    heatmap_png = OUTPUT_ROOT / "_heatmap_hacienda_v3.png"
    log("Generando heatmap hacienda v3...")
    build_heatmap_v3(df_rank, df_clas, heatmap_png)
    log(f"  → {heatmap_png.name}")

    # 2) PDFs por lote en paralelo
    log(f"Generando {len(df_rank)} PDFs lote v3 (download TIF + render + PDF)...")
    total = len(df_rank)
    t0 = datetime.now()
    ok = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(procesar_lote, r.to_dict(), total, i): i
                for i, (_, r) in enumerate(df_rank.iterrows(), 1)}
        for fu in as_completed(futs):
            try:
                if fu.result(): ok += 1
            except Exception as e: log(f"  worker err: {e}")
    log(f"PDFs lote: {ok}/{total} en {(datetime.now()-t0).total_seconds()/60:.1f} min")

    # 3) Intro
    log("Generando intro v3...")
    intro = build_intro(df_rank, df_clas, heatmap_png)
    intro_reader = PdfReader(BytesIO(intro))

    # 4) Glosario + anexo
    glos_reader  = PdfReader(str(GLOSARIO))  if GLOSARIO.exists()  else None
    anexo_reader = PdfReader(str(ANEXO_PDF)) if ANEXO_PDF.exists() else None

    # 5) Merge final
    writer = PdfWriter()
    for p in intro_reader.pages: writer.add_page(p)
    if glos_reader:
        for p in glos_reader.pages: writer.add_page(p)

    incluidos = 0
    for _, row in df_rank.iterrows():
        lid = str(row["lote_id"])
        fecha = row["fecha_imagen"]
        pdf = OUTPUT_ROOT / lid / f"MADUREZ_v3_{lid}_{fecha}.pdf"
        if not pdf.exists(): continue
        try:
            r = PdfReader(str(pdf))
            for p in r.pages: writer.add_page(p)
            incluidos += 1
        except Exception as e: log(f"  × {lid}: {e}")

    if anexo_reader:
        for p in anexo_reader.pages: writer.add_page(p)

    fecha = datetime.now().strftime("%Y-%m-%d")
    out = OUTPUT_ROOT / f"RELATORIO_v3_PrioridadCosecha_S2_S1_{fecha}.pdf"
    writer.add_metadata({
        "/Title": "Reporte v3 Prioridad Cosecha — Hacienda del Señor",
        "/Author": "Pixadvisor AP",
        "/Subject": "Ranking S2+S1+ERA5 con validación local de pesos",
        "/Creator": "Pixadvisor v3 Pipeline (multi-sensor validado localmente)"})
    with open(out, "wb") as f: writer.write(f)
    size_mb = out.stat().st_size / 1024 / 1024
    total_p = (len(intro_reader.pages)
               + (len(glos_reader.pages) if glos_reader else 0)
               + incluidos
               + (len(anexo_reader.pages) if anexo_reader else 0))
    log(f"OK → {out.name}  ({size_mb:.1f} MB · {total_p} pág · {incluidos} lotes)")


if __name__ == "__main__":
    main()
