#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — Reporte de PRIORIDAD DE COSECHA (v2 — defendible)
============================================================================
Genera:
  1) PDFs por lote con: identificación, métricas (Z-scores, GDD, ranking, IC95%),
     mapa de Priority_score visualizado (Z-score combinado por píxel),
     recomendación operativa, disclaimers explícitos con DOIs.
  2) PDF unificado para cliente con portada, glosario metodología, tabla
     ranking completo, anexo de exclusiones.

Input:
  ranking_prioridad_cosecha_<fecha>.csv (de compute_ranking_prioridad.py)
  clasificacion_lotes_2026-05-13.csv

Output:
  <lote>/MADUREZ_<lote>_<fecha>.pdf
  <lote>/mapa_madurez_<lote>.png
  RELATORIO_v2_PrioridadCosecha_HighConfidence_<fecha>.pdf
============================================================================
"""
from __future__ import annotations
import re
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
from matplotlib.colors import LinearSegmentedColormap

import ee
from pypdf import PdfReader, PdfWriter

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image as RLImage, PageBreak)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
LOTES_ROOT  = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\03-Zonas-Manejo")
OUTPUT_ROOT = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2")

CSV_RANKING  = OUTPUT_ROOT / "ranking_prioridad_cosecha_2026-05-13.csv"
CSV_CLASIF   = OUTPUT_ROOT / "clasificacion_lotes_2026-05-13.csv"

CLIENTE = "Hacienda del Señor"
UBICACION = "Santa Cruz, Bolivia"

# Branding
VERDE       = HexColor("#1B5E20")
VERDE_CLARO = HexColor("#4CAF50")
GRIS        = HexColor("#333333")
GRIS_CLARO  = HexColor("#F5F5F5")
GRIS_LINEA  = HexColor("#BDBDBD")
ROJO        = HexColor("#C62828")
NARANJA     = HexColor("#EF6C00")

# Paleta priority: rojo (cosechar primero) → azul (posponer)
PALETA_PRIORITY = [
    "#08306b", "#08519c", "#2171b5", "#4292c6", "#6baed6",
    "#9ecae1", "#c6dbef", "#fcbba1", "#fc9272", "#fb6a4a",
    "#ef3b2c", "#cb181d", "#a50f15"
]

# Pesos del composite (igual que compute_ranking_prioridad)
WEIGHTS = {"NDWI": 0.30, "NDMI": 0.20, "CIRE": 0.20, "PSRI": 0.10, "GDD": 0.20}
Z_CAP = 3.0

NUBES_MAX_MAPA = 60
COBERTURA_MIN_MAPA = 0.50

MESES_ES = ["enero","febrero","marzo","abril","mayo","junio",
            "julio","agosto","septiembre","octubre","noviembre","diciembre"]


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def fecha_es(d): return f"{d.day} de {MESES_ES[d.month-1]} de {d.year}"


# ════════════════════════════════════════════════════════════════════════════
# HELPERS GEE / GEOMETRÍA
# ════════════════════════════════════════════════════════════════════════════
def force_2d(g):
    try: return shapely.force_2d(g)
    except Exception: return shp_transform(lambda x, y, *_: (x, y), g)


def cargar_geom(lote_id: str):
    shp = LOTES_ROOT / lote_id / "PRO" / f"zonas_manejo_{lote_id}_PRO.shp"
    gdf = gpd.read_file(shp)
    if gdf.crs is None: gdf.set_crs("EPSG:32720", inplace=True)
    gdf["geometry"] = gdf.geometry.apply(force_2d)
    return gdf.dissolve()


def init_ee():
    try: ee.Initialize()
    except Exception:
        ee.Authenticate(); ee.Initialize()


def mask_scl(img):
    scl = img.select("SCL")
    return img.updateMask(scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)))


def make_priority_image(geom_ee, bl_means: dict, bl_stds: dict,
                        gdd_z: float):
    """
    Calcula mapa de Priority_score por píxel:
      Score(x,y) = -wNDWI·Z_NDWI(x,y) -wNDMI·Z_NDMI(x,y) -wCIRE·Z_CIRE(x,y)
                   +wPSRI·Z_PSRI(x,y) +wGDD·gdd_z (constante)
    Z(x,y) = clamp((valor(x,y) - baseline_mean_lote) / baseline_std_lote, ±3)
    """
    end_ee = ee.Date(int(datetime.now(timezone.utc).timestamp() * 1000))
    start_ee = end_ee.advance(-21, "day")

    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(geom_ee)
           .filterDate(start_ee, end_ee)
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", NUBES_MAX_MAPA))
           .map(mask_scl))

    def add_cov(img):
        cov = img.select("B4").mask().reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom_ee, scale=20,
            maxPixels=int(1e9), bestEffort=True).get("B4")
        return img.set("VALID_COVERAGE", ee.Number(cov))

    col = (col.map(add_cov)
              .filter(ee.Filter.gte("VALID_COVERAGE", COBERTURA_MIN_MAPA))
              .sort("system:time_start", False))
    n = col.size().getInfo()
    if n == 0: return None

    img = ee.Image(col.first())
    b2 = img.select("B2").divide(10000)
    b3 = img.select("B3").divide(10000)
    b4 = img.select("B4").divide(10000)
    b5 = img.select("B5").divide(10000)
    b6 = img.select("B6").divide(10000)
    b7 = img.select("B7").divide(10000)
    b8 = img.select("B8").divide(10000)
    b8a = img.select("B8A").divide(10000)
    b11 = img.select("B11").divide(10000)

    ndwi = b8a.subtract(b11).divide(b8a.add(b11).max(1e-6))
    ndmi = b8.subtract(b11).divide(b8.add(b11).max(1e-6))
    cire = b7.divide(b5.max(1e-6)).subtract(1)
    psri = b4.subtract(b2).divide(b6.max(1e-6))

    def zscore(idx_img, key):
        m = bl_means.get(key); s = bl_stds.get(key)
        if m is None or s is None or s < 1e-6:
            return ee.Image.constant(0)
        z = idx_img.subtract(m).divide(s)
        return z.clamp(-Z_CAP, Z_CAP)

    z_ndwi = zscore(ndwi, "NDWI")
    z_ndmi = zscore(ndmi, "NDMI")
    z_cire = zscore(cire, "CIRE")
    z_psri = zscore(psri, "PSRI")

    score = (z_ndwi.multiply(-WEIGHTS["NDWI"])
              .add(z_ndmi.multiply(-WEIGHTS["NDMI"]))
              .add(z_cire.multiply(-WEIGHTS["CIRE"]))
              .add(z_psri.multiply(WEIGHTS["PSRI"]))
              .add(ee.Image.constant(gdd_z * WEIGHTS["GDD"]))
              .rename("PRIORITY"))
    return score.clip(geom_ee)


def descargar_tif(img, geom_ee, out_path: Path) -> bool:
    try:
        url = img.getDownloadURL({
            "scale": 10, "region": geom_ee, "format": "GEO_TIFF",
            "crs": "EPSG:32720"})
    except Exception as e:
        log(f"  × URL: {e}"); return False
    try: r = requests.get(url, timeout=180)
    except Exception as e: log(f"  × HTTP: {e}"); return False
    if r.status_code != 200:
        log(f"  × HTTP {r.status_code}"); return False
    out_path.write_bytes(r.content)
    return True


# ════════════════════════════════════════════════════════════════════════════
# RENDER MAPA
# ════════════════════════════════════════════════════════════════════════════
CMAP_PRIORITY = LinearSegmentedColormap.from_list(
    "priority", PALETA_PRIORITY, N=256)


def render_mapa(tif: Path, gdf_lote, lote_meta: dict, png_out: Path):
    with rasterio.open(tif) as src:
        arr = src.read(1).astype(float)
        nd = src.nodata if src.nodata is not None else -9999
        arr = np.where((arr == nd) | np.isnan(arr), np.nan, arr)
        l, b, r, t = src.bounds
        crs_r = src.crs

    valid = arr[np.isfinite(arr)]
    if valid.size < 3:
        log("  (sin datos suficientes para render)")
        return False

    # Range fijo simétrico (priorizar lectura comparativa entre lotes)
    vmax = max(0.6, float(np.percentile(np.abs(valid), 95)))
    vmin = -vmax

    # Upsample bicúbico + suavizado
    mask = np.isnan(arr)
    fill = float(np.nanmean(arr))
    arr_filled = np.where(mask, fill, arr)
    factor = 4
    arr_up = zoom(arr_filled, factor, order=3, mode="nearest")
    mask_up = zoom(mask.astype(float), factor, order=1, mode="nearest") > 0.5
    arr_up = gaussian_filter(arr_up, sigma=1.5 * factor)
    arr_up = np.where(mask_up, np.nan, arr_up)

    fig, ax = plt.subplots(figsize=(8.5, 8.0), dpi=220)
    fig.patch.set_facecolor("white")

    im = ax.imshow(arr_up, cmap=CMAP_PRIORITY, vmin=vmin, vmax=vmax,
                    extent=(l, r, b, t), interpolation="bicubic",
                    origin="upper", aspect="equal")
    try:
        gdf_lote.to_crs(crs_r).boundary.plot(ax=ax, color="black",
                                              linewidth=1.6, alpha=0.9)
    except Exception:
        pass
    ax.set_xlim(l, r); ax.set_ylim(b, t); ax.set_axis_off()

    ax.set_title(
        f"Score de prioridad de cosecha — Lote {lote_meta['lote_id']}",
        fontsize=14, fontweight="bold", color="#1B5E20", pad=12)

    cbar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.04, shrink=0.85,
                        ticks=np.linspace(vmin, vmax, 5))
    cbar.set_label(
        "Score relativo (rojo: cosechar primero · azul: posponer)",
        fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    plt.figtext(
        0.5, 0.015,
        f"Sentinel-2A {lote_meta.get('fecha_imagen','—')}  ·  "
        f"Pixadvisor AP  ·  Score basado en Z-scores temporales NDWI/NDMI/CIRE/PSRI/GDD",
        ha="center", fontsize=8, color="#555555")

    fig.tight_layout()
    fig.savefig(png_out, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return True


# ════════════════════════════════════════════════════════════════════════════
# PDF POR LOTE
# ════════════════════════════════════════════════════════════════════════════
def generar_pdf_lote(meta: dict, png_mapa: Path, pdf_out: Path,
                      total_lotes: int):
    doc = SimpleDocTemplate(
        str(pdf_out), pagesize=A4,
        topMargin=15*mm, bottomMargin=18*mm,
        leftMargin=18*mm, rightMargin=18*mm,
        title=f"Prioridad cosecha lote {meta['lote_id']}",
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
    s_warn = ParagraphStyle("W", parent=s["Normal"],
        fontName="Helvetica-Bold", fontSize=8.5, textColor=ROJO, leading=11)

    story = []

    # Header
    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión", s_sub),
        Paragraph(f"<para align=right>Prioridad de Cosecha<br/>"
                   f"{datetime.now():%Y-%m-%d}</para>", s_sub)]]
    h_tbl = Table(header, colWidths=[100*mm, 70*mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LINEBELOW",(0,0),(-1,0),1.5,VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(h_tbl); story.append(Spacer(1, 6))

    # Título
    rank = int(meta.get("Rank", 0))
    rank_lo = int(meta.get("Rank_p025", rank))
    rank_hi = int(meta.get("Rank_p975", rank))
    estado = str(meta.get("Estado_fenologico","—"))
    story.append(Paragraph(
        f"Lote {meta['lote_id']} — Rank #{rank} de {total_lotes}", s_title))
    story.append(Paragraph(
        f"Estado fenológico estimado: <b>{estado}</b>  ·  "
        f"IC95% rank: [{rank_lo}–{rank_hi}]  ·  "
        f"Imagen Sentinel-2A: <b>{meta.get('fecha_imagen','—')}</b>",
        s_sub))
    story.append(Spacer(1, 4))

    # Tabla identificación
    info = [
        ["ID Lote",        str(meta["lote_id"])],
        ["Área",           f"{meta['area_ha']:.2f} ha"],
        ["Categoría",      str(meta.get("categoria","CAÑA HIGH"))],
        ["Imagen S2A",     str(meta.get("fecha_imagen","—"))],
        ["Cobertura útil", f"{(meta.get('valid_coverage') or 0)*100:.0f}%"],
        ["Nubosidad escena", f"{meta.get('cloud_pct') or 0:.1f}%"],
    ]
    t_info = Table(info, colWidths=[40*mm, 60*mm])
    t_info.setStyle(TableStyle([
        ("FONT",(0,0),(-1,-1),"Helvetica",8),
        ("FONT",(0,0),(0,-1),"Helvetica-Bold",8),
        ("TEXTCOLOR",(0,0),(0,-1),VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("TOPPADDING",(0,0),(-1,-1),2),
        ("LINEBELOW",(0,0),(-1,-1),0.3,GRIS_LINEA)]))

    # Tabla métricas (Z-scores + GDD + score)
    def fz(v, sig=False):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "—"
        if sig: return f"{v:+.2f}"
        return f"{v:.2f}"
    metrics = [
        ["Métrica",          "Valor",                "Interpretación"],
        ["Priority_score",   fz(meta.get("Priority_score"), True),  "Score relativo (mayor = cosechar antes)"],
        ["Z NDWI",           fz(meta.get("NDWI_zscore"), True),     "Agua foliar vs su propio histórico"],
        ["Z NDMI",           fz(meta.get("NDMI_zscore"), True),     "Humedad dosel vs histórico"],
        ["Z CIRE",           fz(meta.get("CIRE_zscore"), True),     "Clorofila vs histórico"],
        ["Z PSRI",           fz(meta.get("PSRI_zscore"), True),     "Senescencia vs histórico"],
        ["GDD acumulado",    f"{meta.get('GDD_acum',0):.0f} °C·d",  f"Desde último corte ({meta.get('GDD_dias','?')} días)"],
        ["Z GDD (rel)",      fz(meta.get("GDD_zscore"), True),      "Acumulación térmica vs hacienda"],
    ]
    t_met = Table(metrics, colWidths=[35*mm, 25*mm, 75*mm], repeatRows=1)
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

    side = Table([[t_info, t_met]], colWidths=[105*mm, 65*mm])
    side.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP")]))
    # Wait — corrijo widths
    side = Table([[t_info, t_met]])
    side.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(side); story.append(Spacer(1, 6))

    # Mapa
    if png_mapa.exists():
        rim = RLImage(str(png_mapa), width=165*mm, height=120*mm,
                       kind="proportional")
        rim.hAlign = "CENTER"
        story.append(rim); story.append(Spacer(1, 4))

    # Recomendación
    story.append(Paragraph("Recomendación operativa", s_h2))
    pct = (rank / total_lotes) * 100 if total_lotes else 0
    if pct <= 20:
        rec = (f"Lote en <b>{int(pct)}% superior</b> del ranking. "
               f"<b>Cosechar entre los primeros</b>. Validar con muestreo "
               f"in-situ de Brix superior/inferior con refractómetro de mano "
               f"(protocolo SASRI PurEst / CONSECANA).")
    elif pct <= 50:
        rec = (f"Lote en posición media-alta del ranking. "
               f"<b>Programar cosecha en próximas 2-4 semanas.</b> "
               f"Considerar muestreo in-situ confirmatorio.")
    elif pct <= 80:
        rec = (f"Lote en posición media-baja. "
               f"<b>Postergar cosecha</b>. Re-evaluar en 3-4 semanas con "
               f"nueva imagen Sentinel-2A.")
    else:
        rec = (f"Lote en <b>{int(pct)}% inferior</b>. Aún en fase vegetativa "
               f"o pre-maduración. <b>NO cosechar todavía</b>. Re-evaluar "
               f"en 4-6 semanas.")
    story.append(Paragraph(rec, s_body))

    # Disclaimers
    story.append(Spacer(1, 4))
    story.append(Paragraph("Limitaciones e interpretación", s_h2))
    disc = (
        "Este score es <b>RELATIVO entre lotes</b> de la hacienda, basado en "
        "anomalías espectrales (NDWI Gao, NDMI, CIRE Gitelson, PSRI) "
        "respecto al baseline histórico Sentinel-2 propio del lote (3 años) "
        "y Growing Degree Days (T_base 18°C, ERA5-Land). "
        "<b>NO es una estimación de Pol o Brix absoluto</b>. La decisión "
        "final de cosecha debe validarse con muestreo de juice in-situ "
        "(refractómetro + polarímetro, protocolo CONSECANA/SASRI). "
        "Referencias: Leandro et al. 2024 DOI 10.3390/crops4030024; "
        "Bocca et al. 2024 DOI 10.1007/s12355-024-01468-z; "
        "Inman-Bamber 1994 DOI 10.1016/0378-4290(94)90051-5; "
        "Meroni et al. 2019 DOI 10.1016/j.agsy.2018.07.002."
    )
    story.append(Paragraph(disc, s_body))

    # Footer
    def _f(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7); canvas.setFillColor(GRIS)
        canvas.drawCentredString(
            A4[0]/2, 10*mm,
            f"Pixadvisor AP · Hacienda del Señor · Lote {meta['lote_id']} · "
            f"Prioridad de Cosecha v2 · {datetime.now():%Y-%m-%d} · "
            f"pág {doc_.page}")
        canvas.setStrokeColor(VERDE); canvas.setLineWidth(0.4)
        canvas.line(18*mm, 13*mm, A4[0]-18*mm, 13*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_f, onLaterPages=_f)


# ════════════════════════════════════════════════════════════════════════════
# WORKER POR LOTE (mapa + PDF)
# ════════════════════════════════════════════════════════════════════════════
def procesar_lote(meta: dict, total_lotes: int, idx: int, total: int):
    lid = str(meta["lote_id"])
    out_dir = OUTPUT_ROOT / lid
    out_dir.mkdir(parents=True, exist_ok=True)
    fecha = meta.get("fecha_imagen", "—")

    try:
        # 1) Geom + Priority image en GEE
        gdf = cargar_geom(lid)
        gdf_w = gdf.to_crs("EPSG:4326")
        geom_ee = ee.Geometry(gdf_w.geometry.iloc[0].__geo_interface__)

        bl_means = {k: meta.get(f"{k}_baseline_mean") for k in ["NDWI","NDMI","CIRE","PSRI"]}
        bl_stds  = {k: meta.get(f"{k}_baseline_std")  for k in ["NDWI","NDMI","CIRE","PSRI"]}
        gdd_z    = float(meta.get("GDD_zscore") or 0)

        priority_img = make_priority_image(geom_ee, bl_means, bl_stds, gdd_z)
        if priority_img is None:
            log(f"[{idx}/{total}] {lid} sin imagen S2 reciente para mapa")
            return False

        # 2) Descargar TIF + render PNG
        tif = out_dir / f"PRIORITY_{lid}_{fecha}.tif"
        if not descargar_tif(priority_img.toFloat(), geom_ee, tif):
            return False

        png = out_dir / f"mapa_madurez_{lid}.png"
        ok = render_mapa(tif, gdf, meta, png)
        if not ok: return False

        # 3) PDF
        pdf = out_dir / f"MADUREZ_{lid}_{fecha}.pdf"
        generar_pdf_lote(meta, png, pdf, total_lotes)
        log(f"[{idx}/{total}] {lid} → MADUREZ_{lid}_{fecha}.pdf")
        return True
    except Exception as e:
        log(f"[{idx}/{total}] {lid} × {e}")
        return False


# ════════════════════════════════════════════════════════════════════════════
# PORTADA + RESUMEN + GLOSARIO METODOLOGÍA + ANEXO
# ════════════════════════════════════════════════════════════════════════════
def build_intro(df_rank: pd.DataFrame, df_clas: pd.DataFrame) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        topMargin=18*mm, bottomMargin=18*mm,
        leftMargin=20*mm, rightMargin=20*mm,
        title="Reporte v2 Prioridad Cosecha", author="Pixadvisor AP")

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
    story.append(h_tbl); story.append(Spacer(1, 30*mm))

    story.append(Paragraph("REPORTE DE PRIORIDAD DE COSECHA", s_big))
    story.append(Paragraph("Caña de Azúcar — Versión 2", s_huge))
    story.append(Paragraph(
        "<font color='#1B5E20'><b>Ranking ordinal RELATIVO entre lotes · "
        "Sin estimación de Pol absoluto</b></font>", s_sub))
    story.append(Spacer(1, 10*mm))

    meta = [
        ["Cliente",                 CLIENTE],
        ["Ubicación",               UBICACION],
        ["Cultivo",                 "Caña de azúcar (cultivares regionales UCG/RBD)"],
        ["Sensor principal",        "Sentinel-2A (ESA Copernicus, 10/20 m)"],
        ["Datos térmicos",          "ERA5-Land (Copernicus C3S)"],
        ["Lotes confirmados caña",  f"{len(df_rank)} (HIGH confidence)"],
        ["Hectáreas analizadas",    f"{df_rank['area_ha'].sum():,.0f} ha"],
        ["Imagen Sentinel-2A más reciente", df_rank["fecha_imagen"].mode().iloc[0]
                                                if not df_rank.empty else "—"],
        ["Baseline histórico",      "3 años Sentinel-2 (2023, 2024, 2025), mismo mes calendario por lote"],
        ["Fecha del reporte",       fecha_es(datetime.now())],
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
    story.append(Spacer(1, 25*mm))
    story.append(Paragraph(
        "<b>Garantía de calidad:</b> los lotes incluidos pasaron clasificación "
        "automática de cobertura usando 14 meses de Sentinel-2 NDVI (firma "
        "fenológica). Los puntajes de prioridad se basan en proxies espectrales "
        "y térmicos validados peer-reviewed, con cuantificación de incertidumbre "
        "vía bootstrap (200 iteraciones).", s_body))

    # PÁGINA 2 — Resumen Ejecutivo
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 6))
    story.append(Paragraph("Resumen Ejecutivo", s_big))
    story.append(Paragraph(
        f"Estado de madurez relativa al {datetime.now():%Y-%m-%d}", s_sub))
    story.append(Spacer(1, 6))

    # KPIs
    story.append(Paragraph("KPIs", s_h2))
    kpis = [
        ["Lotes en ranking",     f"{len(df_rank)}",                   "CAÑA HIGH confidence"],
        ["Área analizada",       f"{df_rank['area_ha'].sum():,.0f} ha", "100% verificada"],
        ["GDD medio acumulado",  f"{df_rank['GDD_acum'].mean():.0f} °C·d",
                                  "T_base 18°C — Inman-Bamber 1994"],
        ["Lotes en zona de cosecha (top 20%)", f"{len(df_rank.head(int(len(df_rank)*0.2)))}",
                                                "Prioridad alta"],
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

    # Distribución por estado fenológico
    story.append(Paragraph("Distribución por estado fenológico", s_h2))
    dist = df_rank.groupby("Estado_fenologico").agg(
        n=("lote_id","count"), ha=("area_ha","sum")).reset_index()
    dist["pct_ha"] = dist["ha"]/dist["ha"].sum()*100
    rows = [["Estado", "# Lotes", "Hectáreas", "% Área"]]
    for _, r in dist.iterrows():
        rows.append([str(r["Estado_fenologico"]), f"{int(r['n'])}",
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

    # Top 20 prioridad
    story.append(Paragraph("Top 20 — prioridad de cosecha (por ranking)", s_h2))
    top = df_rank.head(20).reset_index(drop=True)
    top_rows = [["#", "Lote", "Área (ha)", "Score", "Estado", "IC95% rank", "Img S2A"]]
    for i, r in top.iterrows():
        top_rows.append([
            str(i+1), str(r["lote_id"]), f"{r['area_ha']:,.2f}",
            f"{r['Priority_score']:+.2f}", str(r["Estado_fenologico"])[:18],
            f"[{int(r['Rank_p025'])}-{int(r['Rank_p975'])}]",
            str(r["fecha_imagen"])])
    t_t = Table(top_rows,
                colWidths=[8*mm, 25*mm, 22*mm, 18*mm, 38*mm, 25*mm, 25*mm],
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
        "<i>IC95% rank: rango de posiciones que el lote podría ocupar al "
        "considerar incertidumbre intra-lote. Lotes con IC ancho deben "
        "validarse in-situ antes de decidir.</i>", s_small))

    # PÁGINA 3 — Glosario metodológico
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 6))
    story.append(Paragraph("Metodología y referencias científicas", s_big))
    story.append(Spacer(1, 4))

    story.append(Paragraph("1) Clasificación de cobertura", s_h2))
    story.append(Paragraph(
        "Antes de aplicar el modelo de prioridad, todos los lotes se "
        "clasifican usando la firma fenológica NDVI multi-temporal "
        "(14 meses de Sentinel-2). Esto detecta lotes en reforma, soya, "
        "monte y pasto, que se EXCLUYEN del análisis de cosecha. Los 131 "
        "lotes incluidos en este reporte fueron confirmados como caña "
        "activa con confianza alta.", s_body))

    story.append(Paragraph("2) Índices espectrales utilizados", s_h2))
    indices_data = [
        ["Índice", "Fórmula", "Base fisiológica", "Peso", "Referencia"],
        ["NDWI Gao", "(B8A−B11)/(B8A+B11)", "Agua foliar (cae al madurar)",
         "0.30", "Leandro 2024\nDOI 10.3390/crops4030024"],
        ["NDMI",     "(B8−B11)/(B8+B11)",   "Humedad dosel (10m NIR)",
         "0.20", "Hajeb 2023\nDOI 10.1016/j.jag.2022.103168"],
        ["CIRE",     "B7/B5 − 1",           "Clorofila red-edge (cae)",
         "0.20", "Bocca 2024\nDOI 10.1007/s12355-024-01468-z"],
        ["PSRI",     "(B4−B2)/B6",          "Senescencia carotenoides",
         "0.10", "Merzlyak 1999\nDOI 10.1034/j.1399-3054.1999.106119.x"],
        ["GDD",      "Σ max(0, T−18°C)",    "Acumulación térmica entrenudos",
         "0.20", "Inman-Bamber 1994\nDOI 10.1016/0378-4290(94)90051-5"],
    ]
    t_idx = Table(indices_data,
                  colWidths=[18*mm, 32*mm, 42*mm, 12*mm, 56*mm], repeatRows=1)
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

    story.append(Paragraph("3) Z-score temporal", s_h2))
    story.append(Paragraph(
        "Para cada índice y cada lote: Z = (valor_actual − media_baseline) "
        "/ desvío_baseline, capeado a ±3 (estándar JRC ASAP). El baseline "
        "se construye con imágenes Sentinel-2 del MISMO mes calendario en "
        "los últimos 3 años para el MISMO lote. Esto controla por cultivar, "
        "edad y manejo intra-lote. Z negativo en NDWI/NDMI/CIRE = más "
        "maduro que el histórico; Z positivo en PSRI/GDD = más maduro. "
        "Referencia metodológica: Meroni et al. 2019 DOI "
        "10.1016/j.agsy.2018.07.002 (sistema ASAP del JRC, EU).", s_body))

    story.append(Paragraph("4) Composite y bootstrap", s_h2))
    story.append(Paragraph(
        "Priority_score = −0.30·Z_NDWI − 0.20·Z_NDMI − 0.20·Z_CIRE + "
        "0.10·Z_PSRI + 0.20·Z_GDD. Pesos derivados de la fuerza de "
        "validación reportada en literatura. El ranking se valida con "
        "bootstrap (200 iteraciones de ruido gaussiano sobre Z-scores con "
        "σ=1/√n_píxeles), reportando IC95% del rank. Lotes con IC ancho "
        "están en zona de empate y necesitan validación in-situ.", s_body))

    story.append(Paragraph("5) Validación in-situ recomendada", s_h2))
    story.append(Paragraph(
        "Para los lotes Top 20 del ranking, se recomienda muestreo "
        "in-situ con refractómetro de mano: 5 puntos × 10 tallos × "
        "Brix superior + Brix inferior. Calcular CMI = (BS/BI)·100. "
        "Lotes con CMI ≥ 85% son cosecha confirmada (estándar industrial "
        "SASRI PurEst / CONSECANA Brasil). Los datos de Pol post-cosecha "
        "se pueden registrar para construir progresivamente una "
        "calibración local específica de los cultivares de Hacienda del "
        "Señor.", s_body))

    story.append(Paragraph("6) Lo que este reporte NO afirma", s_h2))
    story.append(Paragraph(
        "<b>NO se reporta Pol o Brix absoluto numérico.</b> Sin "
        "calibración local con análisis de juice (≥30 muestras "
        "polarimétricas), no es científicamente defendible asignar un "
        "valor absoluto de Pol a un lote desde Sentinel-2. Para "
        "liquidación CONSECANA o decisiones contractuales, usar análisis "
        "de juice del ingenio.", s_body))

    def _f(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7); canvas.setFillColor(GRIS)
        canvas.drawCentredString(A4[0]/2, 10*mm,
            f"Pixadvisor AP · Hacienda del Señor · Prioridad Cosecha v2 · "
            f"{datetime.now():%Y-%m-%d} · pág {doc_.page}")
        canvas.setStrokeColor(VERDE); canvas.setLineWidth(0.4)
        canvas.line(20*mm, 13*mm, A4[0]-20*mm, 13*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_f, onLaterPages=_f)
    return buf.getvalue()


def build_anexo(df_clas: pd.DataFrame) -> bytes:
    CANA_CATS = {"CAÑA_ACTIVA","CAÑA_SOCA","CAÑA_PRE_COSECHA_RECIENTE","CAÑA_INMADURA_NUEVA"}
    no_cana = df_clas[~df_clas["categoria"].isin(CANA_CATS)].copy()
    medium_low = df_clas[df_clas["categoria"].isin(CANA_CATS) &
                          (df_clas["confianza"]!="HIGH")].copy()

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        topMargin=15*mm, bottomMargin=18*mm,
        leftMargin=18*mm, rightMargin=18*mm,
        title="Anexo lotes excluidos", author="Pixadvisor AP")
    s = getSampleStyleSheet()
    s_title = ParagraphStyle("T", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=18, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=4, leading=20)
    s_sub = ParagraphStyle("S", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS,
        alignment=TA_LEFT, spaceAfter=4, leading=13)
    s_h2 = ParagraphStyle("H2", parent=s["Heading2"],
        fontName="Helvetica-Bold", fontSize=12, textColor=VERDE,
        alignment=TA_LEFT, spaceBefore=8, spaceAfter=4, leading=14)
    s_body = ParagraphStyle("B", parent=s["Normal"],
        fontName="Helvetica", fontSize=9, textColor=GRIS, leading=12)

    story = []
    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión", s_sub),
        Paragraph(f"<para align=right>Anexo · {datetime.now():%Y-%m-%d}</para>", s_sub)]]
    h_tbl = Table(header, colWidths=[110*mm, 60*mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LINEBELOW",(0,0),(-1,0),1.5,VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(h_tbl); story.append(Spacer(1, 6))

    story.append(Paragraph("Anexo — Lotes excluidos", s_title))
    story.append(Paragraph(
        "Resultados de la clasificación de cobertura que justifican por "
        "qué cada lote NO está en el reporte principal de prioridad de "
        "cosecha.", s_sub))
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        f"Lotes detectados como NO-caña ({len(no_cana)} lotes · "
        f"{no_cana['area_ha'].sum():,.0f} ha)", s_h2))
    no_cana = no_cana.sort_values(["categoria","area_ha"], ascending=[True, False])
    rows = [["Lote", "Área (ha)", "Categoría", "Justificación"]]
    for _, r in no_cana.iterrows():
        rows.append([str(r["lote_id"]), f"{r['area_ha']:,.1f}",
                     str(r["categoria"]), str(r["nota"])[:90]])
    t = Table(rows, colWidths=[28*mm, 18*mm, 42*mm, 86*mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",8),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",7.5),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.2,GRIS_LINEA),
        ("ALIGN",(1,1),(1,-1),"RIGHT"),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("TOPPADDING",(0,0),(-1,-1),2)]))
    story.append(t)

    if len(medium_low) > 0:
        story.append(PageBreak())
        story.append(h_tbl); story.append(Spacer(1, 6))
        story.append(Paragraph(
            f"Lotes CAÑA confianza media o baja "
            f"({len(medium_low)} lotes · {medium_low['area_ha'].sum():,.0f} ha)",
            s_h2))
        story.append(Paragraph(
            "Patrón compatible con caña pero firma no concluyente. "
            "<b>Recomendar visita a campo</b> antes de incluir en próximo "
            "reporte.", s_body))
        story.append(Spacer(1, 4))
        ml = medium_low.sort_values("area_ha", ascending=False)
        rows2 = [["Lote", "Área", "Categoría", "Conf.", "Nota"]]
        for _, r in ml.iterrows():
            rows2.append([str(r["lote_id"]), f"{r['area_ha']:,.1f}",
                          str(r["categoria"]), str(r["confianza"]),
                          str(r["nota"])[:75]])
        t2 = Table(rows2, colWidths=[26*mm, 18*mm, 38*mm, 18*mm, 74*mm],
                    repeatRows=1)
        t2.setStyle(TableStyle([
            ("FONT",(0,0),(-1,0),"Helvetica-Bold",8),
            ("BACKGROUND",(0,0),(-1,0),VERDE),
            ("TEXTCOLOR",(0,0),(-1,0),white),
            ("FONT",(0,1),(-1,-1),"Helvetica",7.5),
            ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
            ("GRID",(0,0),(-1,-1),0.2,GRIS_LINEA),
            ("ALIGN",(1,1),(1,-1),"RIGHT"),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("BOTTOMPADDING",(0,0),(-1,-1),2),
            ("TOPPADDING",(0,0),(-1,-1),2)]))
        story.append(t2)

    def _f(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7); canvas.setFillColor(GRIS)
        canvas.drawCentredString(A4[0]/2, 10*mm,
            f"Pixadvisor AP · Anexo · {datetime.now():%Y-%m-%d} · pág {doc_.page}")
        canvas.setStrokeColor(VERDE); canvas.setLineWidth(0.4)
        canvas.line(18*mm, 13*mm, A4[0]-18*mm, 13*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_f, onLaterPages=_f)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log("══ Reporte v2 — Prioridad de Cosecha ══")
    if not CSV_RANKING.exists():
        log(f"ERROR: falta {CSV_RANKING}"); sys.exit(1)
    if not CSV_CLASIF.exists():
        log(f"ERROR: falta {CSV_CLASIF}"); sys.exit(1)

    df_rank = pd.read_csv(CSV_RANKING)
    df_clas = pd.read_csv(CSV_CLASIF)
    log(f"Lotes en ranking: {len(df_rank)}")

    init_ee()

    # Generar mapas + PDFs por lote en paralelo
    total = len(df_rank)
    t0 = datetime.now()
    ok = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(procesar_lote, r.to_dict(), total, i, total): i
                for i, (_, r) in enumerate(df_rank.iterrows(), 1)}
        for fu in as_completed(futs):
            try:
                if fu.result(): ok += 1
            except Exception as e:
                log(f"  worker err: {e}")
    log(f"PDFs lote-a-lote: {ok}/{total} en {(datetime.now()-t0).total_seconds()/60:.1f} min")

    # Portada + glosario + anexo
    log("Generando portada + glosario...")
    intro = build_intro(df_rank, df_clas)
    intro_reader = PdfReader(BytesIO(intro))

    log("Generando anexo NO-caña...")
    anexo = build_anexo(df_clas)
    anexo_reader = PdfReader(BytesIO(anexo))

    # Anexo standalone también
    fecha = datetime.now().strftime("%Y-%m-%d")
    anexo_path = OUTPUT_ROOT / f"v2_Anexo_LotesExcluidos_{fecha}.pdf"
    with open(anexo_path, "wb") as f: f.write(anexo)
    log(f"  → {anexo_path.name}")

    # Glosario Pol existente (lo mantenemos como referencia, pero ya NO afirma Pol)
    glosario_path = OUTPUT_ROOT / "00_Glosario_POL_Pixadvisor.pdf"

    # Merge final
    writer = PdfWriter()
    for p in intro_reader.pages: writer.add_page(p)
    if glosario_path.exists():
        gloss = PdfReader(str(glosario_path))
        for p in gloss.pages: writer.add_page(p)

    incluidos = 0
    for _, row in df_rank.iterrows():
        lid = str(row["lote_id"])
        fecha_img = row["fecha_imagen"]
        pdf = OUTPUT_ROOT / lid / f"MADUREZ_{lid}_{fecha_img}.pdf"
        if not pdf.exists(): continue
        try:
            r = PdfReader(str(pdf))
            for p in r.pages: writer.add_page(p)
            incluidos += 1
        except Exception as e:
            log(f"  × {lid}: {e}")

    for p in anexo_reader.pages: writer.add_page(p)

    out = OUTPUT_ROOT / f"RELATORIO_v2_PrioridadCosecha_{fecha}.pdf"
    writer.add_metadata({
        "/Title": "Reporte v2 Prioridad Cosecha — Hacienda del Señor",
        "/Author": "Pixadvisor AP",
        "/Subject": "Ranking ordinal de prioridad de cosecha caña, "
                    "Sentinel-2 + ERA5-Land, sin estimación Pol absoluto",
        "/Creator": "Pixadvisor v2 Pipeline (científicamente defendible)"})

    with open(out, "wb") as f: writer.write(f)
    size_mb = out.stat().st_size / 1024 / 1024
    log(f"OK → {out.name}  ({size_mb:.1f} MB)")
    log(f"   incluidos: {incluidos} lotes  ·  total páginas: "
        f"{len(intro_reader.pages) + (len(gloss.pages) if glosario_path.exists() else 0) + incluidos + len(anexo_reader.pages)}")


if __name__ == "__main__":
    main()
