# -*- coding: utf-8 -*-
"""Parchea _propuesta_joao.py (copia del template oficial) con datos reales
Serro Alto / Joao Geraldo, $15/ha, y condiciones de pago 50/50 VRT."""
import re, io
F = r'D:\PIXADVISOR_AGENT_WORKSPACE\_propuesta_joao.py'
c = io.open(F, encoding='utf-8').read()

# 1) metodologia
c = c.replace('Paragraph("Densidad de grilla", TD), Paragraph("[1 muestra cada ___ ha] (típico 2,5–5 ha/muestra)", TD)',
              'Paragraph("Estrategia", TD), Paragraph("Dirigido por ambientes de manejo · 3 ambientes por lote · 146 muestras compuestas", TD)')
c = c.replace('Paragraph("Submuestras por punto", TD), Paragraph("12–20 piques compuestos, dispersos por ambiente", TD)',
              'Paragraph("Submuestras por punto", TD), Paragraph("5–10 piques distribuidos por todo el ambiente · buffer ≥ 20 m del borde", TD)')
c = c.replace('Paragraph("Tipo de muestreo", TD), Paragraph("Grilla georreferenciada / por ambientes (dirigido)", TD)',
              'Paragraph("Tipo de muestreo", TD), Paragraph("Dirigido por ambientes productivos (zonas de manejo)", TD)')

# 2) intro inversion
c = c.replace('Paragraph("Valores de referencia. La inversión final depende de la superficie, la densidad de grilla "\n   "y el paquete de parámetros. <i>Completar precios antes de enviar.</i>", BODY)',
              'Paragraph("Servicio integral de análisis de suelo y mapeo de fertilidad, con tarifa única por hectárea de área útil (todo incluido).", BODY)')

# 3) tabla de inversion (reemplazo del bloque completo via regex)
NEW_INV = '''inv = [[Paragraph("Concepto", TH), Paragraph("Unidad", TH), Paragraph("Cant.", TH), Paragraph("P. unit. (USD)", TH), Paragraph("Subtotal (USD)", TH)],
 [Paragraph("Servicio integral de análisis de suelo y mapeo de fertilidad — incluye muestreo georreferenciado, análisis de laboratorio, procesamiento GIS, delimitación de zonas de manejo, reporte de diagnóstico, recomendación de fertilización y mapas de prescripción de tasa variable (VRT)", TD), Paragraph("por ha útil", TD), Paragraph("1.782,8", TD), Paragraph("15,00", TD), Paragraph("26.742", TD)],
 [Paragraph("TOTAL (USD)", TH), Paragraph("", TD), Paragraph("", TD), Paragraph("", TD), Paragraph("USD 26.742", TH)]]'''
c = re.sub(r'inv = \[\[Paragraph\("Concepto".*?Paragraph\("\[\$________\]", TH\)\]\]', NEW_INV, c, flags=re.S)

# nota de tarifa antes de condiciones
c = c.replace('S += [ti, Spacer(1,10), Paragraph("8. Condiciones comerciales", H2)]',
              'S += [ti, Spacer(1,8), Paragraph("<b>Tarifa: USD 15 por hectárea de área útil — todo incluido.</b> Total del servicio: <b>USD 26.742</b> sobre 1.782,8 ha útiles (cañadas y drenajes ya descontados; el lote bruto es 1.871,5 ha).", BODY), Spacer(1,4), Paragraph("8. Condiciones comerciales", H2)]')

# 4) condiciones de pago
c = c.replace('"<b>Forma de pago:</b> [50% al inicio / 50% contra entrega] — a definir.",',
              '"<b>Forma de pago:</b> 50% a la firma del contrato y 50% contra la entrega de los mapas de prescripción de tasa variable (VRT) y las recomendaciones de fertilización.",')

# 5) alcance: mencionar area util
c = c.replace('"reporte de diagnóstico y los mapas. <b>No incluye</b> el costo de los fertilizantes ni la "',
              '"reporte de diagnóstico, los mapas y la prescripción de tasa variable. El servicio se aplica sobre el <b>área útil</b> de cada lote (cañadas y drenajes ya descontados). <b>No incluye</b> el costo de los fertilizantes ni la "')

io.open(F, 'w', encoding='utf-8').write(c)
# verificacion de que se aplicaron
ok = all(s in c for s in ['26.742', '15,00', 'a la firma del contrato', '3 ambientes por lote'])
print('parche aplicado OK' if ok else 'REVISAR: algun reemplazo no matcheo')
