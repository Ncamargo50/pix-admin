#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extrae texto de la propuesta Serro Alto v2 a un archivo de texto."""
import sys

SRC = r"C:\Users\Usuario\Desktop\Propuesta_Pastagem_SerroAlto_v2.pdf"
OUT = r"D:\PIXADVISOR_AGENT_WORKSPACE\_serroalto_text.txt"

text = ""
engine = ""
try:
    import pdfplumber
    engine = "pdfplumber"
    with pdfplumber.open(SRC) as pdf:
        for i, page in enumerate(pdf.pages):
            text += f"\n===== PAGE {i+1} =====\n"
            text += (page.extract_text() or "")
except Exception as e1:
    try:
        from pypdf import PdfReader
        engine = "pypdf"
        reader = PdfReader(SRC)
        for i, page in enumerate(reader.pages):
            text += f"\n===== PAGE {i+1} =====\n"
            text += (page.extract_text() or "")
    except Exception as e2:
        text = f"FAILED pdfplumber: {e1}\nFAILED pypdf: {e2}\n"

with open(OUT, "w", encoding="utf-8") as f:
    f.write(text)

print(f"engine={engine} chars={len(text)} -> {OUT}")
