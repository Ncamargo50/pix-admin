#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PIXADVISOR — FICHAS DIGITALES rellenables en celular
20 PDFs interactivos con AcroForm (BS, BI, notas, decisión).
Adobe Acrobat Reader / Xodo PDF / Drive móvil.
CMI auto vía JavaScript embebido.
"""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas as pdfcanvas

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

SAMPL_ROOT = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\05-Muestreo-InSitu-Top20")
CSV_RANK   = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2"
                   r"\ranking_prioridad_v3_S2_S1_2026-05-15.csv")

N_TOP = 20
N_PUNTOS = 5
N_TALLOS = 10

VERDE       = HexColor("#1B5E20")
GRIS        = HexColor("#333333")
GRIS_CLARO  = HexColor("#F5F5F5")
GRIS_LINEA  = HexColor("#BDBDBD")
ROJO        = HexColor("#C62828")
AMARILLO    = HexColor("#FFF9C4")
VERDE_LIGHT = HexColor("#C8E6C9")

PAGE_W, PAGE_H = A4


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


# ════════════════════════════════════════════════════════════════════════════
# Helpers AcroForm — usan solo args mínimos seguros
# ════════════════════════════════════════════════════════════════════════════
def add_text(form, name, x, y, w, h, value=""):
    form.textfield(
        name=name, x=x, y=y, width=w, height=h,
        borderStyle="solid", borderWidth=0.5,
        borderColor=GRIS_LINEA, fillColor=white,
        textColor=GRIS, value=value, maxlen=200,
    )


def add_text_yellow(form, name, x, y, w, h):
    form.textfield(
        name=name, x=x, y=y, width=w, height=h,
        borderStyle="solid", borderWidth=0.5,
        borderColor=GRIS_LINEA, fillColor=AMARILLO,
        textColor=GRIS, value="", maxlen=20,
    )


def add_text_green(form, name, x, y, w, h):
    form.textfield(
        name=name, x=x, y=y, width=w, height=h,
        borderStyle="solid", borderWidth=0.5,
        borderColor=VERDE, fillColor=VERDE_LIGHT,
        textColor=GRIS, value="", maxlen=20,
    )


def add_choice(form, name, x, y, w, h, options, value=""):
    """Reemplazado con textfield simple — form.choice() tiene bug en ReportLab.
    El usuario escribe la opción a mano."""
    add_text(form, name, x, y, w, h, value=value)


# ════════════════════════════════════════════════════════════════════════════
# GENERAR FICHA DIGITAL POR LOTE
# ════════════════════════════════════════════════════════════════════════════
def generar_ficha_digital(meta: dict, pdf_out: Path):
    c = pdfcanvas.Canvas(str(pdf_out), pagesize=A4)
    c.setTitle(f"Ficha Digital Lote {meta['lote_id']}")
    c.setAuthor("Pixadvisor AP")

    form = c.acroForm
    lote_id = str(meta["lote_id"])
    rank = int(meta["Rank_v3"])

    margin = 12 * mm
    y = PAGE_H - margin

    # Header
    c.setFillColor(VERDE); c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y - 12, "PIXADVISOR")
    c.setFillColor(GRIS); c.setFont("Helvetica", 9)
    c.drawString(margin, y - 22, "Agricultura de Precisión")
    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W - margin, y - 12, "Ficha Digital de Muestreo")
    c.drawRightString(PAGE_W - margin, y - 22, "Hacienda del Señor")
    c.setStrokeColor(VERDE); c.setLineWidth(1.5)
    c.line(margin, y - 26, PAGE_W - margin, y - 26)
    y -= 36

    # Título
    c.setFillColor(VERDE); c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, f"Lote {lote_id} — Rank #{rank} prioridad")
    y -= 14
    c.setFillColor(GRIS); c.setFont("Helvetica", 9)
    c.drawString(margin, y,
        f"Área: {meta.get('area_ha',0):.2f} ha  ·  "
        f"Estado: {meta.get('Estado_fenologico_v3','—')}  ·  "
        f"S2A: {meta.get('fecha_imagen','—')}  ·  Score v3: {meta.get('Priority_score_v3',0):+.2f}")
    y -= 16

    # Cabecera con campos
    c.setFillColor(VERDE_LIGHT)
    c.rect(margin, y - 38, PAGE_W - 2*margin, 38, fill=1, stroke=0)
    c.setFillColor(GRIS); c.setFont("Helvetica-Bold", 8)

    c.drawString(margin + 4, y - 10, "Fecha:")
    add_text(form, "FECHA", margin + 38, y - 14, 65, 12)
    c.drawString(margin + 110, y - 10, "Hora ini:")
    add_text(form, "HORA_INI", margin + 150, y - 14, 40, 12)
    c.drawString(margin + 195, y - 10, "Hora fin:")
    add_text(form, "HORA_FIN", margin + 235, y - 14, 40, 12)
    c.drawString(margin + 285, y - 10, "Agrónomo:")
    add_text(form, "AGRONOMO", margin + 332, y - 14, 200, 12)

    c.drawString(margin + 4, y - 28, "Cultivar:")
    add_text(form, "CULTIVAR", margin + 38, y - 32, 65, 12)
    c.drawString(margin + 110, y - 28, "Edad (m):")
    add_text(form, "EDAD", margin + 152, y - 32, 30, 12)
    c.drawString(margin + 195, y - 28, "Riego 48h:")
    add_choice(form, "RIEGO", margin + 240, y - 32, 35, 12, ["No","Si"], "No")
    c.drawString(margin + 285, y - 28, "Lluvia 48h:")
    add_choice(form, "LLUVIA", margin + 332, y - 32, 35, 12, ["No","Si"], "No")

    y -= 50

    # Tabla mediciones
    table_w = PAGE_W - margin*2
    col_punto = margin
    col_tallo = margin + 30
    col_bs = margin + 60
    col_bi = margin + 115
    col_cmi = margin + 170
    col_notas = margin + 225

    c.setFillColor(VERDE)
    c.rect(margin, y - 14, table_w, 14, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 9)
    c.drawString(col_punto + 4, y - 10, "Punto")
    c.drawString(col_tallo + 4, y - 10, "Tallo")
    c.drawString(col_bs + 4, y - 10, "BS (°Brix)")
    c.drawString(col_bi + 4, y - 10, "BI (°Brix)")
    c.drawString(col_cmi + 4, y - 10, "CMI auto")
    c.drawString(col_notas + 4, y - 10, "Notas (opcional)")
    y -= 14

    row_h = 11

    for p in range(1, N_PUNTOS + 1):
        for t in range(1, N_TALLOS + 1):
            row_y = y - row_h
            if (t % 2) == 0:
                c.setFillColor(GRIS_CLARO)
                c.rect(margin, row_y, table_w, row_h, fill=1, stroke=0)
            if t == 1 and p > 1:
                c.setStrokeColor(VERDE); c.setLineWidth(1)
                c.line(margin, row_y + row_h, margin + table_w, row_y + row_h)
            c.setFillColor(GRIS)
            if t == 1:
                c.setFont("Helvetica-Bold", 8)
                c.drawString(col_punto + 4, row_y + 2, f"P{p}")
            c.setFont("Helvetica", 8)
            c.drawString(col_tallo + 4, row_y + 2, str(t))

            fp = f"P{p}_T{t}"
            add_text(form, f"{fp}_BS", col_bs + 2, row_y + 1, 50, row_h - 2)
            add_text(form, f"{fp}_BI", col_bi + 2, row_y + 1, 50, row_h - 2)
            add_text_yellow(form, f"{fp}_CMI", col_cmi + 2, row_y + 1,
                             50, row_h - 2)
            add_text(form, f"{fp}_NOTAS", col_notas + 2, row_y + 1,
                      table_w - (col_notas - margin) - 4, row_h - 2)
            y = row_y

        # Promedio del punto
        row_y = y - row_h
        c.setFillColor(VERDE_LIGHT)
        c.rect(margin, row_y, table_w, row_h, fill=1, stroke=0)
        c.setFillColor(GRIS); c.setFont("Helvetica-Bold", 8)
        c.drawString(col_punto + 4, row_y + 2, f"P{p}")
        c.drawString(col_tallo + 4, row_y + 2, "PROM")
        add_text_green(form, f"P{p}_PROM", col_cmi + 2, row_y + 1,
                        50, row_h - 2)
        c.drawString(col_notas + 4, row_y + 2,
                      f"← promedio CMI 10 tallos del punto P{p}")
        y = row_y

    # Promedio LOTE + decisión
    y -= 14
    c.setFillColor(VERDE)
    c.rect(margin, y - row_h, table_w, row_h, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 4, y - 8, "PROMEDIO LOTE (CMI)")
    add_text_yellow(form, "LOTE_PROM", col_cmi + 2, y - row_h + 1,
                     50, row_h - 2)
    c.drawString(col_notas + 4, y - 8, "Recomendación auto:")
    add_text_yellow(form, "RECOMENDACION_AUTO",
                     col_notas + 100, y - row_h + 1,
                     table_w - (col_notas - margin) - 102, row_h - 2)
    y -= row_h + 8

    # Decisión final
    c.setFillColor(VERDE); c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y - 10, "Decisión final del agrónomo:")
    y -= 16
    c.setFillColor(GRIS); c.setFont("Helvetica", 9)
    c.drawString(margin + 4, y - 10, "Acción:")
    add_choice(form, "DECISION", margin + 40, y - 14, 130, 12,
                ["Cosechar 7-14 d", "Esperar 2-3 sem",
                 "Re-evaluar 4 sem", "URGENTE cosechar"], "")
    c.drawString(margin + 180, y - 10, "Próx visita:")
    add_text(form, "PROX_VISITA", margin + 232, y - 14, 65, 12)
    c.drawString(margin + 305, y - 10, "Notas finales:")
    add_text(form, "NOTAS_FINALES", margin + 305, y - 36,
              table_w - (margin + 305 - margin) - 6, 22)

    y -= 50

    # Footer
    c.setFillColor(GRIS); c.setFont("Helvetica-Oblique", 7)
    c.drawString(margin, 18,
        "INSTRUCCIONES: Abrir en Adobe Acrobat Reader / Xodo PDF / Drive móvil. "
        "Escribir BS y BI con teclado del celular. CMI se calcula automáticamente. "
        "Compartir PDF lleno por email/WhatsApp.")
    c.setFont("Helvetica", 7)
    c.drawCentredString(PAGE_W/2, 8,
        f"Pixadvisor AP · Hacienda del Señor · Lote {lote_id} · "
        f"Ficha Digital · {datetime.now():%Y-%m-%d}")

    c.save()


# ════════════════════════════════════════════════════════════════════════════
# AGREGAR JAVASCRIPT a los campos BS/BI con pypdf
# ════════════════════════════════════════════════════════════════════════════
def agregar_javascript_cmi(pdf_path: Path):
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import (DictionaryObject, ArrayObject, NameObject,
                                TextStringObject, BooleanObject)
    import os

    reader = PdfReader(str(pdf_path))
    writer = PdfWriter(clone_from=reader)

    if "/AcroForm" not in writer._root_object: return
    acroform = writer._root_object["/AcroForm"]
    if "/Fields" not in acroform: return

    acroform[NameObject("/NeedAppearances")] = BooleanObject(True)

    fields = acroform["/Fields"]
    field_by_name = {}
    for fref in fields:
        f = fref.get_object() if hasattr(fref, 'get_object') else fref
        if "/T" in f:
            field_by_name[str(f["/T"])] = f

    for p in range(1, N_PUNTOS + 1):
        for t in range(1, N_TALLOS + 1):
            bs_n = f"P{p}_T{t}_BS"
            bi_n = f"P{p}_T{t}_BI"
            cmi_n = f"P{p}_T{t}_CMI"
            prom_n = f"P{p}_PROM"
            js = (
                f'var bs=parseFloat(this.getField("{bs_n}").value.replace(",","."));'
                f'var bi=parseFloat(this.getField("{bi_n}").value.replace(",","."));'
                f'if(!isNaN(bs)&&!isNaN(bi)&&bi>0)'
                f'{{this.getField("{cmi_n}").value=(bs/bi*100).toFixed(1);}}'
                f'else{{this.getField("{cmi_n}").value="";}}'
                f'var s=0,n=0;for(var ti=1;ti<=10;ti++){{var v=parseFloat(this.getField("P{p}_T"+ti+"_CMI").value);if(!isNaN(v)){{s+=v;n+=1;}}}}'
                f'this.getField("{prom_n}").value=(n>0)?(s/n).toFixed(1):"";'
                f'var s2=0,n2=0;for(var pi=1;pi<=5;pi++){{var v2=parseFloat(this.getField("P"+pi+"_PROM").value);if(!isNaN(v2)){{s2+=v2;n2+=1;}}}}'
                f'var avg=(n2>0)?s2/n2:NaN;'
                f'this.getField("LOTE_PROM").value=!isNaN(avg)?avg.toFixed(1):"";'
                f'var r=this.getField("RECOMENDACION_AUTO");'
                f'if(!isNaN(avg)){{if(avg>=95)r.value="URGENTE - cosechar inmediato";'
                f'else if(avg>=85)r.value="COSECHAR EN 7-14 DIAS";'
                f'else if(avg>=75)r.value="Esperar 2-3 semanas";'
                f'else r.value="ESPERAR - reevaluar 4 semanas";}}else{{r.value="";}}'
            )
            action = DictionaryObject({
                NameObject("/S"): NameObject("/JavaScript"),
                NameObject("/JS"): TextStringObject(js),
            })
            aa = DictionaryObject({NameObject("/Bl"): action})
            for fn in [bs_n, bi_n]:
                if fn in field_by_name:
                    field_by_name[fn][NameObject("/AA")] = aa

    tmp = pdf_path.with_suffix(".tmp.pdf")
    with open(tmp, "wb") as f: writer.write(f)
    os.replace(tmp, pdf_path)


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log("══ Pixadvisor — Fichas DIGITALES rellenables ══")
    if not CSV_RANK.exists():
        log(f"ERROR: falta {CSV_RANK}"); sys.exit(1)

    df = pd.read_csv(CSV_RANK)
    df["lote_id"] = df["lote_id"].astype(str)
    top20 = df.sort_values("Rank_v3").head(N_TOP).reset_index(drop=True)

    out_dir = SAMPL_ROOT / "FICHAS_DIGITALES"
    out_dir.mkdir(parents=True, exist_ok=True)

    ok = 0
    for i, (_, r) in enumerate(top20.iterrows(), 1):
        lote_id = str(r["lote_id"])
        rank = int(r["Rank_v3"])
        log(f"[{i}/{N_TOP}] {lote_id}")
        try:
            pdf_out = out_dir / f"FICHA_DIGITAL_{rank:02d}_{lote_id}.pdf"
            generar_ficha_digital(r.to_dict(), pdf_out)
            agregar_javascript_cmi(pdf_out)
            log(f"  ✓ {pdf_out.name}")
            ok += 1
        except Exception as e:
            log(f"  × {e}")
            import traceback; traceback.print_exc()
            break

    # ZIP
    if ok > 0:
        import zipfile
        zip_out = out_dir.parent / "Pixadvisor_FichasDigitales_Top20.zip"
        with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zf:
            for pdf in sorted(out_dir.glob("FICHA_DIGITAL_*.pdf")):
                zf.write(pdf, pdf.name)
        log(f"ZIP → {zip_out.name}")

    log(f"OK — {ok}/{N_TOP} fichas digitales en {out_dir}")


if __name__ == "__main__":
    main()
