#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — Fix layout PDFs lote + agregar HEATMAP de hacienda
============================================================================
- Regenera PDFs por lote con tablas correctamente dimensionadas (no overlap)
- Agrega mapa GLOBAL de la hacienda con los 131 lotes coloreados por
  Priority_score, para que el cliente vea de un solo vistazo qué cosechar
- Reusa PNGs y TIFs ya generados (no llama a GEE)
- Re-arma PDF unificado v2 con: portada + resumen + heatmap + glosario +
  131 reportes lote-a-lote + anexo
============================================================================
"""
from __future__ import annotations
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from shapely.ops import transform as shp_transform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Patch

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image as RLImage, PageBreak)

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

# ════════════════════════════════════════════════════════════════════════════
LOTES_ROOT  = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\03-Zonas-Manejo")
OUTPUT_ROOT = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2")
CSV_RANK   = OUTPUT_ROOT / "ranking_prioridad_cosecha_2026-05-13.csv"
CSV_CLAS   = OUTPUT_ROOT / "clasificacion_lotes_2026-05-13.csv"
GLOSARIO   = OUTPUT_ROOT / "00_Glosario_POL_Pixadvisor.pdf"
ANEXO_PDF  = OUTPUT_ROOT / "v2_Anexo_LotesExcluidos_2026-05-13.pdf"

CLIENTE = "Hacienda del Señor"
UBICACION = "Santa Cruz, Bolivia"

VERDE       = HexColor("#1B5E20")
GRIS        = HexColor("#333333")
GRIS_CLARO  = HexColor("#F5F5F5")
GRIS_LINEA  = HexColor("#BDBDBD")

PALETA_PRIORITY = [
    "#08306b", "#08519c", "#2171b5", "#4292c6", "#6baed6",
    "#9ecae1", "#c6dbef", "#fcbba1", "#fc9272", "#fb6a4a",
    "#ef3b2c", "#cb181d", "#a50f15"
]
CMAP_P = LinearSegmentedColormap.from_list("priority", PALETA_PRIORITY, N=256)

MESES_ES = ["enero","febrero","marzo","abril","mayo","junio","julio",
            "agosto","septiembre","octubre","noviembre","diciembre"]


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def fecha_es(d): return f"{d.day} de {MESES_ES[d.month-1]} de {d.year}"


def force_2d(g):
    try: return shapely.force_2d(g)
    except Exception: return shp_transform(lambda x, y, *_: (x, y), g)


# ════════════════════════════════════════════════════════════════════════════
# 1) HEATMAP GLOBAL DE LA HACIENDA
# ════════════════════════════════════════════════════════════════════════════
def cargar_geom(lote_id: str):
    shp = LOTES_ROOT / lote_id / "PRO" / f"zonas_manejo_{lote_id}_PRO.shp"
    if not shp.exists(): return None
    gdf = gpd.read_file(shp)
    if gdf.crs is None: gdf.set_crs("EPSG:32720", inplace=True)
    gdf["geometry"] = gdf.geometry.apply(force_2d)
    return gdf.dissolve()


def build_heatmap_hacienda(df_rank: pd.DataFrame, df_clas: pd.DataFrame,
                            png_out: Path) -> bool:
    """Mapa de toda la hacienda con polígonos coloreados por Priority_score.
    Lotes no-caña se muestran en gris claro para contexto."""
    log(f"  cargando geometrías de {len(df_rank)} lotes caña + contexto no-caña...")

    # Caña HIGH con score
    cana_records = []
    for _, r in df_rank.iterrows():
        g = cargar_geom(str(r["lote_id"]))
        if g is None: continue
        g = g.to_crs("EPSG:32720")
        g["lote_id"] = str(r["lote_id"])
        g["Priority_score"] = r["Priority_score"]
        g["Rank"] = r["Rank"]
        g["Estado_fenologico"] = r["Estado_fenologico"]
        cana_records.append(g)
    if not cana_records:
        log("  ! sin geometrías"); return False
    gdf_cana = pd.concat(cana_records, ignore_index=True)
    gdf_cana = gpd.GeoDataFrame(gdf_cana, crs="EPSG:32720")

    # No-caña (contexto, gris)
    CANA_CATS = {"CAÑA_ACTIVA","CAÑA_SOCA","CAÑA_PRE_COSECHA_RECIENTE",
                  "CAÑA_INMADURA_NUEVA"}
    no_cana_ids = df_clas[~df_clas["categoria"].isin(CANA_CATS)]["lote_id"].astype(str).tolist()
    no_cana_records = []
    for lid in no_cana_ids:
        g = cargar_geom(lid)
        if g is None: continue
        g = g.to_crs("EPSG:32720")
        g["lote_id"] = lid
        no_cana_records.append(g)
    gdf_no_cana = (gpd.GeoDataFrame(pd.concat(no_cana_records, ignore_index=True),
                                     crs="EPSG:32720")
                    if no_cana_records else None)

    # Plot
    fig, ax = plt.subplots(figsize=(13, 11), dpi=200)
    fig.patch.set_facecolor("white")

    # No-caña en gris claro
    if gdf_no_cana is not None:
        gdf_no_cana.plot(ax=ax, color="#E8E8E8", edgecolor="#888888",
                          linewidth=0.4, alpha=0.7)

    # Caña coloreada por score
    vmin = float(df_rank["Priority_score"].min())
    vmax = float(df_rank["Priority_score"].max())
    abs_max = max(abs(vmin), abs(vmax))
    norm = Normalize(vmin=-abs_max, vmax=abs_max)

    gdf_cana.plot(ax=ax, column="Priority_score", cmap=CMAP_P,
                   norm=norm, edgecolor="black", linewidth=0.6)

    # Etiquetas para el TOP 20 (prioridad alta)
    top20 = gdf_cana.nlargest(20, "Priority_score")
    for _, r in top20.iterrows():
        c = r.geometry.centroid
        ax.annotate(f"#{int(r['Rank'])} {r['lote_id']}",
                     xy=(c.x, c.y), xytext=(0, 0), textcoords="offset points",
                     fontsize=6.5, fontweight="bold", color="black",
                     ha="center", va="center",
                     bbox=dict(boxstyle="round,pad=0.15",
                                fc="white", ec="black", lw=0.4, alpha=0.85))

    ax.set_axis_off()
    ax.set_title(
        "Mapa de Prioridad de Cosecha — Hacienda del Señor\n"
        f"131 lotes caña confirmada · Sentinel-2A · "
        f"{datetime.now():%Y-%m-%d}",
        fontsize=14, fontweight="bold", color="#1B5E20", pad=15)

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=CMAP_P, norm=norm); sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.02, shrink=0.6,
                        ticks=np.linspace(-abs_max, abs_max, 5))
    cbar.set_label(
        "Priority_score (rojo: cosechar primero · azul: posponer)",
        fontsize=10)
    cbar.ax.tick_params(labelsize=9)

    # Leyenda
    legend_elements = [
        Patch(facecolor="#a50f15", edgecolor="black", label="MADUREZ_AVANZADA (cosechar)"),
        Patch(facecolor="#fb6a4a", edgecolor="black", label="MADURACION"),
        Patch(facecolor="#9ecae1", edgecolor="black", label="PRE_MADURACION"),
        Patch(facecolor="#08306b", edgecolor="black", label="VEGETATIVO (esperar)"),
        Patch(facecolor="#E8E8E8", edgecolor="#888", label="No-caña (contexto)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=8,
               framealpha=0.9, title="Categorías")

    plt.figtext(0.5, 0.01,
        "Etiquetas muestran Top 20 lotes por prioridad. "
        "Score basado en Z-scores temporales NDWI/NDMI/CIRE/PSRI/GDD vs baseline 3 años.",
        ha="center", fontsize=8, color="#555555")

    fig.tight_layout()
    fig.savefig(png_out, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    log(f"  → heatmap: {png_out.name}")
    return True


# ════════════════════════════════════════════════════════════════════════════
# 2) JUSTIFICACIÓN TÉCNICA específica al lote (driven por sus datos)
# ════════════════════════════════════════════════════════════════════════════
def justificar_lote(meta: dict, total_lotes: int) -> dict:
    """Construye texto de justificación específica al lote a partir de
    sus Z-scores, GDD, rank y bootstrap. Cada frase es atribuible a una
    métrica numérica concreta — el cliente puede ratrear cada afirmación."""
    z_ndwi = meta.get("NDWI_zscore")
    z_ndmi = meta.get("NDMI_zscore")
    z_cire = meta.get("CIRE_zscore")
    z_psri = meta.get("PSRI_zscore")
    z_gdd  = meta.get("GDD_zscore")
    score  = meta.get("Priority_score")
    rank   = int(meta.get("Rank") or 0)
    rank_lo = int(meta.get("Rank_p025") or rank)
    rank_hi = int(meta.get("Rank_p975") or rank)
    gdd_a   = meta.get("GDD_acum") or 0
    gdd_d   = meta.get("GDD_dias") or 0
    estado  = str(meta.get("Estado_fenologico","—"))

    def _f(v): return v if (v is not None and not (isinstance(v, float) and np.isnan(v))) else None

    pct = (rank / total_lotes) * 100 if total_lotes else 0

    # 1) Posición en ranking — frase natural
    if pct <= 10:
        pos = (f"Este lote está en el <b>{int(pct)}% superior</b> del ranking "
               f"({rank}/{total_lotes}) — entre los lotes con mayor evidencia "
               f"espectral de madurez de toda la hacienda.")
    elif pct <= 25:
        pos = (f"Este lote está en el <b>top 25%</b> ({rank}/{total_lotes}) — "
               f"clara prioridad de cosecha.")
    elif pct <= 50:
        pos = (f"Este lote está en posición <b>media-alta</b> ({rank}/{total_lotes}) — "
               f"candidato a cosecha en próximas 2-4 semanas.")
    elif pct <= 75:
        pos = (f"Este lote está en posición <b>media-baja</b> ({rank}/{total_lotes}) — "
               f"aún no maduro, esperar 4-8 semanas.")
    else:
        pos = (f"Este lote está en el <b>{int(pct)}% inferior</b> "
               f"({rank}/{total_lotes}) — fase vegetativa o pre-maduración, "
               f"no cosechar todavía.")

    # 2) Estabilidad del rank
    span = rank_hi - rank_lo
    if span <= 2:
        stab = (f"El <b>bootstrap es muy estable</b> (IC95% rank [{rank_lo}-{rank_hi}]) — "
                f"posición de alta confianza.")
    elif span <= 8:
        stab = (f"El bootstrap es moderadamente estable (IC95% [{rank_lo}-{rank_hi}], "
                f"span {span}) — posición probable, pero puede oscilar con "
                f"nueva imagen.")
    else:
        stab = (f"<b>Bootstrap inestable</b> (IC95% [{rank_lo}-{rank_hi}], "
                f"span {span}) — alta incertidumbre, validación in-situ "
                f"crítica antes de decidir.")

    # 3) Interpretación de cada Z-score (atribuible a métrica)
    interps = []
    z = _f(z_ndwi)
    if z is not None:
        if z <= -1.5:
            interps.append(f"<b>Z NDWI {z:+.2f}</b>: agua foliar muy por debajo del histórico del lote → senescencia avanzada (proxy fuerte de madurez)")
        elif z <= -0.5:
            interps.append(f"Z NDWI {z:+.2f}: agua foliar por debajo del histórico → entrando senescencia")
        elif z >= 1.5:
            interps.append(f"<b>Z NDWI {z:+.2f}</b>: agua foliar muy por encima del histórico → cultivo en crecimiento vigoroso, lejos de madurez")
        elif z >= 0.5:
            interps.append(f"Z NDWI {z:+.2f}: agua foliar por encima del histórico")
        else:
            interps.append(f"Z NDWI {z:+.2f}: agua foliar normal para esta época del año")

    z = _f(z_cire)
    if z is not None:
        if z <= -1.5:
            interps.append(f"<b>Z CIRE {z:+.2f}</b>: clorofila red-edge muy baja vs histórico → pérdida de pigmentación foliar (signo de madurez)")
        elif z <= -0.5:
            interps.append(f"Z CIRE {z:+.2f}: clorofila red-edge por debajo del histórico")
        elif z >= 1.5:
            interps.append(f"<b>Z CIRE {z:+.2f}</b>: clorofila muy alta → dosel verde y activo, cultivo no maduro")
        elif z >= 0.5:
            interps.append(f"Z CIRE {z:+.2f}: clorofila por encima del histórico (cultivo aún verde)")

    z = _f(z_psri)
    if z is not None:
        if z >= 1.5:
            interps.append(f"<b>Z PSRI {z:+.2f}</b>: índice de senescencia muy alto → carotenoides predominan sobre clorofila (cultivo amarilleando)")
        elif z >= 0.5:
            interps.append(f"Z PSRI {z:+.2f}: senescencia visible respecto al histórico")
        elif z <= -0.5:
            interps.append(f"Z PSRI {z:+.2f}: cultivo más verde que su histórico (lejos de senescencia)")

    z = _f(z_ndmi)
    if z is not None and abs(z) > 1.0:
        if z < 0:
            interps.append(f"Z NDMI {z:+.2f}: humedad de dosel reducida (consistente con NDWI)")
        else:
            interps.append(f"Z NDMI {z:+.2f}: humedad de dosel elevada")

    # 4) GDD — interpretación según valor absoluto
    if gdd_a > 0:
        if gdd_a >= 2400:
            gdd_text = (f"<b>GDD acumulado {gdd_a:.0f} °C·d en {gdd_d} días</b> "
                        f"desde último corte detectado — supera el umbral típico "
                        f"de maduración de caña (~2200-2500 °C·d con T_base 18°C, "
                        f"Inman-Bamber 1994).")
        elif gdd_a >= 1800:
            gdd_text = (f"GDD acumulado {gdd_a:.0f} °C·d en {gdd_d} días — "
                        f"entrando ventana de maduración fisiológica.")
        elif gdd_a >= 1000:
            gdd_text = (f"GDD acumulado {gdd_a:.0f} °C·d en {gdd_d} días — "
                        f"crecimiento vegetativo medio, lejos de madurez térmica.")
        else:
            gdd_text = (f"GDD acumulado {gdd_a:.0f} °C·d en {gdd_d} días — "
                        f"etapa temprana del ciclo, recién después del corte.")
    else:
        gdd_text = ("GDD acumulado no disponible (revisar datos ERA5-Land).")

    return {
        "posicion": pos,
        "estabilidad": stab,
        "indices": interps,
        "gdd": gdd_text,
        "estado": estado,
        "score": score,
    }


# ════════════════════════════════════════════════════════════════════════════
# 3) PDF POR LOTE (layout corregido + justificación técnica)
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

    story = []

    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión", s_sub),
        Paragraph(f"<para align=right>Prioridad de Cosecha<br/>"
                   f"{datetime.now():%Y-%m-%d}</para>", s_sub)]]
    h_tbl = Table(header, colWidths=[100*mm, 70*mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LINEBELOW",(0,0),(-1,0),1.5,VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(h_tbl); story.append(Spacer(1, 4))

    rank = int(meta.get("Rank", 0))
    rank_lo = int(meta.get("Rank_p025", rank))
    rank_hi = int(meta.get("Rank_p975", rank))
    estado = str(meta.get("Estado_fenologico","—"))
    story.append(Paragraph(
        f"Lote {meta['lote_id']} — Rank #{rank} de {total_lotes}", s_title))
    story.append(Paragraph(
        f"Estado: <b>{estado}</b> · IC95% rank: [{rank_lo}–{rank_hi}] · "
        f"Imagen S2A: <b>{meta.get('fecha_imagen','—')}</b>", s_sub))
    story.append(Spacer(1, 4))

    # ─── INFO + MÉTRICAS lado a lado, anchos calculados para NO desbordar
    # Página A4 ancho útil = 210 - 18*2 = 174 mm
    # info: 35 + 50 = 85 mm; metricas: 25 + 18 + 42 = 85 mm; total = 170 mm OK

    info = [
        ["ID Lote",        str(meta["lote_id"])],
        ["Área",           f"{meta['area_ha']:.2f} ha"],
        ["Imagen S2A",     str(meta.get("fecha_imagen","—"))],
        ["Cobertura útil", f"{(meta.get('valid_coverage') or 0)*100:.0f}%"],
        ["Nubes escena",   f"{(meta.get('cloud_pct') or 0):.1f}%"],
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
        ["Métrica",       "Valor",                                       "Interp."],
        ["Score",         fz(meta.get("Priority_score"), True),          "global"],
        ["Z NDWI",        fz(meta.get("NDWI_zscore"), True),             "agua foliar"],
        ["Z NDMI",        fz(meta.get("NDMI_zscore"), True),             "humedad"],
        ["Z CIRE",        fz(meta.get("CIRE_zscore"), True),             "clorofila"],
        ["Z PSRI",        fz(meta.get("PSRI_zscore"), True),             "senescencia"],
        ["GDD acum.",     f"{meta.get('GDD_acum',0):.0f}°Cd",            f"{meta.get('GDD_dias','?')}d"],
        ["Z GDD rel.",    fz(meta.get("GDD_zscore"), True),              "térmica"],
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

    # Tabla side-by-side con anchos EXPLÍCITOS que suman 170mm
    side = Table([[t_info, t_met]], colWidths=[80*mm, 90*mm])
    side.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),0),
        ("BOTTOMPADDING",(0,0),(-1,-1),0),
    ]))
    story.append(side)
    story.append(Spacer(1, 6))

    # Mapa (compactado para que todo el lote quepa en 1 página)
    if png_mapa.exists():
        rim = RLImage(str(png_mapa), width=130*mm, height=85*mm,
                       kind="proportional")
        rim.hAlign = "CENTER"
        story.append(rim); story.append(Spacer(1, 2))

    # ─── JUSTIFICACIÓN TÉCNICA específica al lote
    j = justificar_lote(meta, total_lotes)
    pct = (rank / total_lotes) * 100 if total_lotes else 0

    story.append(Paragraph("Justificación técnica del ranking", s_h2))
    story.append(Paragraph(j["posicion"], s_body))
    story.append(Spacer(1, 2))
    story.append(Paragraph(j["estabilidad"], s_body))
    story.append(Spacer(1, 2))

    # Lectura por índice (cada bullet = un dato medido)
    if j["indices"]:
        story.append(Paragraph("<b>Lectura por índice espectral:</b>", s_body))
        for it in j["indices"]:
            story.append(Paragraph(f"• {it}", s_body))
        story.append(Spacer(1, 2))

    story.append(Paragraph(f"<b>Acumulación térmica:</b> {j['gdd']}", s_body))
    story.append(Spacer(1, 4))

    # Recomendación derivada
    story.append(Paragraph("Recomendación operativa", s_h2))
    if pct <= 20:
        rec = (f"<b>Cosechar entre los primeros.</b> Validar con muestreo "
               f"in-situ Brix superior/inferior con refractómetro de mano "
               f"(protocolo SASRI PurEst / CONSECANA). "
               f"<b>CMI = (BS/BI)·100 ≥ 85% confirma madurez industrial</b>; "
               f"si se confirma, programar cosecha en los próximos 7-14 días.")
    elif pct <= 50:
        rec = (f"<b>Programar cosecha en próximas 2-4 semanas.</b> "
               f"Considerar muestreo in-situ confirmatorio antes de "
               f"movilizar maquinaria. Re-evaluar con nueva imagen "
               f"Sentinel-2A en 10-15 días.")
    elif pct <= 80:
        rec = (f"<b>Postergar cosecha.</b> Re-evaluar en 3-4 semanas con "
               f"nueva imagen Sentinel-2A. No requiere muestreo in-situ "
               f"todavía.")
    else:
        rec = (f"<b>NO cosechar todavía.</b> Cultivo aún en fase "
               f"vegetativa o pre-maduración. Re-evaluar en 4-6 semanas.")
    story.append(Paragraph(rec, s_body))

    # Limitaciones (compactado a 2 líneas para fit en 1 pág)
    s_disc = ParagraphStyle("Disc", parent=s_body, fontSize=7.5,
        textColor=GRIS, leading=10, spaceBefore=4)
    disc = (
        "<i>Score RELATIVO entre lotes (NO Pol/Brix absoluto). Decisión "
        "final requiere muestreo de juice in-situ (CONSECANA/SASRI). "
        "Metodología completa y referencias DOI en la sección "
        "Metodología del reporte unificado.</i>"
    )
    story.append(Paragraph(disc, s_disc))

    def _f(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7); canvas.setFillColor(GRIS)
        canvas.drawCentredString(A4[0]/2, 10*mm,
            f"Pixadvisor AP · Hacienda del Señor · Lote {meta['lote_id']} · "
            f"Prioridad de Cosecha v2 · {datetime.now():%Y-%m-%d} · "
            f"pág {doc_.page}")
        canvas.setStrokeColor(VERDE); canvas.setLineWidth(0.4)
        canvas.line(18*mm, 13*mm, A4[0]-18*mm, 13*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_f, onLaterPages=_f)


# ════════════════════════════════════════════════════════════════════════════
# 3) INTRO con HEATMAP HACIENDA
# ════════════════════════════════════════════════════════════════════════════
def build_intro(df_rank: pd.DataFrame, df_clas: pd.DataFrame,
                 heatmap_png: Path) -> bytes:
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

    # ═══ PORTADA
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
        ["Imagen S2A más reciente", df_rank["fecha_imagen"].mode().iloc[0]
                                                if not df_rank.empty else "—"],
        ["Baseline histórico",      "3 años Sentinel-2, mismo mes calendario por lote"],
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
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph(
        "<b>Garantía de calidad:</b> los lotes incluidos pasaron clasificación "
        "automática de cobertura por firma fenológica NDVI (14 meses S2). "
        "Los puntajes de prioridad se basan en proxies espectrales y "
        "térmicos validados peer-reviewed con incertidumbre cuantificada "
        "vía bootstrap (200 iter).", s_body))

    # ═══ PÁGINA 2 — MAPA HACIENDA (lo que pidió el cliente)
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 4))
    story.append(Paragraph("Mapa de la Hacienda — Prioridad de Cosecha", s_big))
    story.append(Paragraph(
        f"131 lotes caña confirmada coloreados por Priority_score · "
        f"Rojo intenso = cosechar primero · Etiquetas: Top 20", s_sub))
    story.append(Spacer(1, 4))
    if heatmap_png.exists():
        # Mapa grande (casi página completa)
        img = RLImage(str(heatmap_png), width=170*mm, height=200*mm,
                      kind="proportional")
        img.hAlign = "CENTER"
        story.append(img)
    else:
        story.append(Paragraph("[Mapa no disponible]", s_body))

    # ═══ PÁGINA 3 — RESUMEN EJECUTIVO
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 6))
    story.append(Paragraph("Resumen Ejecutivo", s_big))
    story.append(Paragraph(
        f"Estado de madurez relativa al {datetime.now():%Y-%m-%d}", s_sub))
    story.append(Spacer(1, 6))

    story.append(Paragraph("KPIs", s_h2))
    kpis = [
        ["Lotes en ranking",     f"{len(df_rank)}",                          "CAÑA HIGH confidence"],
        ["Área analizada",       f"{df_rank['area_ha'].sum():,.0f} ha",      "100% verificada"],
        ["GDD medio acumulado",  f"{df_rank['GDD_acum'].mean():.0f} °C·d",   "T_base 18°C"],
        ["Lotes top 20% (cosecha alta)", f"{len(df_rank.head(int(len(df_rank)*0.2)))}",
                                  "Prioridad inmediata"],
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

    # Top 20
    story.append(Paragraph("Top 20 — prioridad de cosecha", s_h2))
    top = df_rank.head(20).reset_index(drop=True)
    top_rows = [["#","Lote","Área (ha)","Score","Estado","IC95%","Img S2A"]]
    for i, r in top.iterrows():
        top_rows.append([
            str(i+1), str(r["lote_id"]), f"{r['area_ha']:,.2f}",
            f"{r['Priority_score']:+.2f}", str(r["Estado_fenologico"])[:18],
            f"[{int(r['Rank_p025'])}-{int(r['Rank_p975'])}]",
            str(r["fecha_imagen"])])
    t_t = Table(top_rows,
                colWidths=[8*mm, 22*mm, 22*mm, 18*mm, 38*mm, 22*mm, 28*mm],
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
        "<i>IC95% rank: rango de posiciones del lote considerando "
        "incertidumbre intra-lote (bootstrap 200 iter). IC ancho → "
        "validar in-situ.</i>", s_small))

    # ═══ PÁGINA 4 — METODOLOGÍA
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 6))
    story.append(Paragraph("Metodología y referencias científicas", s_big))
    story.append(Spacer(1, 4))

    story.append(Paragraph("1) Clasificación previa de cobertura", s_h2))
    story.append(Paragraph(
        "Antes del modelo de prioridad, los lotes se clasifican usando la "
        "firma fenológica NDVI multi-temporal (14 meses Sentinel-2). "
        "Detecta lotes en reforma, soya, monte y pasto, que se EXCLUYEN. "
        "Los 131 lotes incluidos son caña activa con confianza alta.", s_body))

    story.append(Paragraph("2) Índices espectrales y pesos", s_h2))
    indices_data = [
        ["Índice", "Fórmula", "Base fisiológica", "Peso", "Referencia"],
        ["NDWI Gao", "(B8A−B11)/(B8A+B11)", "Agua foliar (cae al madurar)",
         "0.30", "Leandro 2024 DOI 10.3390/crops4030024"],
        ["NDMI",     "(B8−B11)/(B8+B11)",   "Humedad dosel",
         "0.20", "Hajeb 2023 DOI 10.1016/j.jag.2022.103168"],
        ["CIRE",     "B7/B5 − 1",           "Clorofila red-edge",
         "0.20", "Bocca 2024 DOI 10.1007/s12355-024-01468-z"],
        ["PSRI",     "(B4−B2)/B6",          "Senescencia carotenoides",
         "0.10", "Merzlyak 1999 DOI 10.1034/j.1399-3054.1999.106119.x"],
        ["GDD",      "Σmax(0,T−18°C)",      "Acumulación térmica",
         "0.20", "Inman-Bamber 1994 DOI 10.1016/0378-4290(94)90051-5"],
    ]
    t_idx = Table(indices_data,
                  colWidths=[16*mm, 30*mm, 38*mm, 12*mm, 64*mm], repeatRows=1)
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

    story.append(Paragraph("3) Z-score temporal (sistema JRC ASAP)", s_h2))
    story.append(Paragraph(
        "Z = (valor_actual − media_baseline) / desvío_baseline, capeado a "
        "±3 SD. Baseline = Sentinel-2 mismo mes calendario, últimos 3 años, "
        "MISMO lote. Controla por cultivar, edad y manejo. Z negativo en "
        "NDWI/NDMI/CIRE = más maduro; Z positivo en PSRI/GDD = más maduro. "
        "Ref: Meroni et al. 2019 DOI 10.1016/j.agsy.2018.07.002.", s_body))

    story.append(Paragraph("4) Composite y bootstrap del ranking", s_h2))
    story.append(Paragraph(
        "Score = −0.30·Z_NDWI − 0.20·Z_NDMI − 0.20·Z_CIRE + 0.10·Z_PSRI + "
        "0.20·Z_GDD. Bootstrap 200 iter con ruido gaussiano σ=1/√n_píxeles, "
        "reportando IC95% del rank por lote. IC ancho → empate → validar in-situ.",
        s_body))

    story.append(Paragraph("5) Validación in-situ recomendada", s_h2))
    story.append(Paragraph(
        "Para Top 20 del ranking: muestreo Brix con refractómetro de mano "
        "(5 puntos × 10 tallos × superior+inferior). CMI = (BS/BI)·100. "
        "CMI ≥ 85% → cosecha confirmada (estándar SASRI PurEst / "
        "CONSECANA Brasil). Datos Pol post-cosecha permiten construir "
        "calibración local progresiva.", s_body))

    story.append(Paragraph("6) Lo que este reporte NO afirma", s_h2))
    story.append(Paragraph(
        "<b>NO se reporta Pol o Brix absoluto numérico.</b> Sin "
        "calibración local con análisis polarimétrico de juice (≥30 muestras), "
        "no es defendible asignar Pol absoluto desde Sentinel-2. Para "
        "liquidación CONSECANA / decisiones contractuales, usar análisis "
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


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log("══ Fix layout + heatmap hacienda ══")
    df_rank = pd.read_csv(CSV_RANK)
    df_clas = pd.read_csv(CSV_CLAS)
    log(f"Lotes en ranking: {len(df_rank)}")

    # 1) Heatmap hacienda
    heatmap_png = OUTPUT_ROOT / "_heatmap_hacienda.png"
    log("Generando heatmap hacienda...")
    build_heatmap_hacienda(df_rank, df_clas, heatmap_png)

    # 2) Regenerar PDFs por lote (layout fix), reusando PNGs existentes
    log("Regenerando PDFs por lote con layout fix...")
    total = len(df_rank)
    ok = 0
    for i, (_, r) in enumerate(df_rank.iterrows(), 1):
        meta = r.to_dict()
        lid = str(meta["lote_id"])
        png = OUTPUT_ROOT / lid / f"mapa_madurez_{lid}.png"
        pdf = OUTPUT_ROOT / lid / f"MADUREZ_{lid}_{meta['fecha_imagen']}.pdf"
        if not png.exists():
            log(f"[{i}/{total}] {lid} sin PNG, skip"); continue
        try:
            generar_pdf_lote(meta, png, pdf, total)
            ok += 1
        except Exception as e:
            log(f"[{i}/{total}] {lid} × {e}")
    log(f"PDFs lote regenerados: {ok}/{total}")

    # 3) Intro con heatmap
    log("Generando intro con mapa hacienda...")
    intro_bytes = build_intro(df_rank, df_clas, heatmap_png)
    intro_reader = PdfReader(BytesIO(intro_bytes))
    log(f"  intro: {len(intro_reader.pages)} pág")

    # 4) Glosario + anexo (ya existen)
    glosario_reader = PdfReader(str(GLOSARIO)) if GLOSARIO.exists() else None
    anexo_reader = PdfReader(str(ANEXO_PDF)) if ANEXO_PDF.exists() else None

    # 5) Merge
    writer = PdfWriter()
    for p in intro_reader.pages: writer.add_page(p)
    if glosario_reader:
        for p in glosario_reader.pages: writer.add_page(p)

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

    if anexo_reader:
        for p in anexo_reader.pages: writer.add_page(p)

    fecha = datetime.now().strftime("%Y-%m-%d")
    out = OUTPUT_ROOT / f"RELATORIO_v2_PrioridadCosecha_FIX_{fecha}.pdf"
    writer.add_metadata({
        "/Title": "Reporte v2 Prioridad Cosecha — Hacienda del Señor",
        "/Author": "Pixadvisor AP",
        "/Subject": "Ranking de prioridad cosecha caña con mapa hacienda",
        "/Creator": "Pixadvisor v2 Pipeline FIX layout"})

    with open(out, "wb") as f: writer.write(f)
    size_mb = out.stat().st_size / 1024 / 1024
    total_p = (len(intro_reader.pages)
               + (len(glosario_reader.pages) if glosario_reader else 0)
               + incluidos
               + (len(anexo_reader.pages) if anexo_reader else 0))
    log(f"OK → {out.name}  ({size_mb:.1f} MB · {total_p} pág · "
        f"{incluidos} lotes)")


if __name__ == "__main__":
    main()
