# -*- coding: utf-8 -*-
"""Genera el Tutorial de uso de la APK PIX Scout — PDF ejecutivo de marca Pixadvisor."""
import sys, os
SKILL = r"C:\Users\Usuario\.claude\skills\pixadvisor-propuesta-ejecutiva"
sys.path.insert(0, os.path.join(SKILL, "scripts"))
import struct
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import HexColor
from pix_branding import Brand

LOGO = os.path.join(SKILL, "assets", "logo_pix_azulnegro_trim.png")
B = Brand(logo=LOGO, footer_center="PIX Scout · Manual del técnico de campo · 2026")
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
B.ss.add(ParagraphStyle("Cap", parent=B.ss["Note"], alignment=TA_CENTER,
                        textColor=HexColor("#0D9488"), fontName="Helvetica-Bold", fontSize=8.5))

def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])   # (w, h) en px

def shot(name, cap="", w=4.9*cm, maxH=16.0*cm):
    """Captura de pantalla enmarcada y centrada, con leyenda."""
    path = os.path.join(SHOTS, name + ".png")
    pw, ph = png_size(path)
    W = w; H = W * ph / pw
    if H > maxH:
        H = maxH; W = H * pw / ph
    img = Image(path, width=W, height=H)
    frame = Table([[img]], colWidths=[W]); frame.hAlign = "CENTER"
    frame.setStyle(TableStyle([("BOX", (0,0), (-1,-1), 0.75, HexColor("#C7D2DC")),
        ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    out = [Spacer(1, 5), frame]
    if cap:
        out += [Spacer(1, 3), B.P("Captura · " + cap, "Cap")]
    out += [Spacer(1, 8)]
    return out

def bl(items):  # lista de viñetas
    return [B.P("• " + t, "Bull") for t in items]

def TBL(data, widths, **kw):  # tabla de marca con celdas que hacen wrap (párrafos)
    header = kw.get("header", True)
    rows = []
    for r, row in enumerate(data):
        st = "CellB" if (r == 0 and header) else "Cell"
        rows.append([B.P(str(c), st) for c in row])
    return B.tbl(rows, widths, **kw)

story = []

# ---------- Portada (contenido bajo el hero) ----------
story += B.cover_filler()
story += [B.P("Ficha del producto", "H1"), B.hr()]
story += [B.meta_table([
    ("Aplicación", "PIX Scout — validación de anomalías a campo"),
    ("Versión", "1.0.0  ·  Android 8.0 o superior"),
    ("Modo", "Offline-first (funciona sin señal en el campo)"),
    ("Para quién", "Técnico de campo y administrador"),
    ("Fecha de emisión", "Julio 2026"),
])]
story += [B.callout("En una línea",
    "El satélite marca dónde hay una anomalía; PIX Scout te lleva por GPS hasta el punto, "
    "te guía a decidir si es enfermedad, plaga o carencia, y registra la validación firmada — todo sin conexión.")]
story += [PageBreak()]

# ---------- Índice ----------
story += [B.P("Contenido", "H1"), B.hr(), B.toc(), PageBreak()]

# ---------- Resumen ----------
story += [B.P("De un vistazo", "H1"), B.hr()]
story += [B.P(
    "PIX Scout es la app de campo de Pixadvisor para <b>validar en el terreno las anomalías que detecta "
    "el satélite</b>. Cierra el lazo satélite ↔ campo: cada validación que registrás vuelve como verdad de "
    "campo y mejora el próximo mapa. Está diseñada para trabajar <b>a pleno sol, con guantes y sin señal</b>.", "Body")]
story += [B.kpi_strip([("7", "cultivos"), ("123", "fichas de campo"), ("26", "umbrales MIP citados"), ("100%", "offline")])]
story += [B.P(
    "Cultivos cubiertos: soja, trigo, maíz, sorgo, girasol, caña de azúcar y pastura. La app no reemplaza "
    "el criterio del técnico: entrega una <b>hipótesis presuntiva</b> con nivel de confianza y, ante la duda, "
    "recomienda colectar muestra a laboratorio.", "Body")]
story += [PageBreak()]

# ---------- 1. Qué es y para qué sirve ----------
story += [B.sec(1, "Qué es y para qué sirve")]
story += [B.P(
    "El motor satelital de Pixadvisor analiza los lotes y genera <b>focos</b> de anomalía, ordenados por "
    "severidad. PIX Scout toma esos focos y te ayuda a resolver la pregunta que el satélite no puede: "
    "<b>¿qué es lo que está pasando en ese punto?</b>", "Body")]
story += bl([
    "Navega por GPS hasta cada foco (brújula + distancia en vivo).",
    "Te guía con una clave de diagnóstico diferencial paso a paso.",
    "Distingue causa <b>biótica</b> (enfermedad/plaga) de <b>abiótica</b> (deriva, agua, clima, suelo) y de <b>carencia nutricional</b>.",
    "Compara la plaga contra el <b>umbral de acción (MIP)</b> para decidir si tratar.",
    "Registra la validación con foto georreferenciada, firmada con tu nombre, y la guarda aunque no haya señal.",
])
story += [B.callout("Importante",
    "El diagnóstico visual es una <b>hipótesis</b>, no una verdad definitiva. Ante enfermedades confundibles, "
    "virus, nematodos o una decisión de alto costo, confirmá siempre por laboratorio (IBRA).")]

# ---------- 2. Instalación ----------
story += [B.sec(2, "Instalación en el celular")]
story += [TBL([
    ["Paso", "Acción"],
    ["1", "Pasá el archivo pix-scout-v1.0.0.apk al celular (WhatsApp, Drive o cable)."],
    ["2", "Abrí el archivo. Android va a pedir permitir “instalar apps de esta fuente”: aceptá."],
    ["3", "Se instala “PIX Scout”. Abrila desde el menú de aplicaciones."],
    ["4", "En el primer uso, concedé los permisos de Ubicación y Cámara."],
], [1.8*cm, 13.2*cm])]
story += [B.callout("Permisos que pide y por qué",
    "Ubicación (GPS): para navegar al foco y georreferenciar cada validación. "
    "Cámara: para adjuntar la foto de la anomalía. Sin estos permisos la app funciona, pero pierde precisión y la foto.")]

# ---------- 3. Primer acceso / login ----------
story += [B.sec(3, "Primer acceso e ingreso")]
story += [B.P(
    "PIX Scout pide <b>usuario y contraseña</b> para trabajar. Las credenciales se guardan cifradas en el "
    "dispositivo (nunca en texto plano) y la verificación funciona <b>sin conexión</b>.", "Body")]
story += [B.P("Primer arranque (una sola vez):", "H2")]
story += bl([
    "La app te pide <b>crear el administrador</b>. Ese sos vos (o el responsable). Elegí usuario, nombre y contraseña.",
    "Guardá bien esa contraseña: con ella vas a dar de alta a los técnicos.",
])
story += [B.P("Ingreso del técnico:", "H2")]
story += bl([
    "El técnico entra con el usuario y contraseña que le dio el administrador.",
    "La sesión queda válida <b>45 días sin reconectar</b> — pensada para campañas en zonas sin señal.",
    "Si el administrador desactiva a un usuario, ese técnico ya no puede ingresar.",
])
story += [B.callout("Gestión de usuarios",
    "El alta de técnicos la hace el administrador desde el ícono de Cuenta → “Gestionar usuarios” "
    "(ver sección 11). Así vos habilitás o bloqueás quién puede trabajar a campo.")]
story += shot("01_login", "primer arranque — crear la cuenta de administrador.")

# ---------- 4. Focos ----------
story += [B.sec(4, "Pantalla principal: Focos activos")]
story += [B.P(
    "Al ingresar ves la lista de <b>focos para validar</b>, ordenados por severidad (los más graves primero). "
    "Cada tarjeta muestra:", "Body")]
story += [TBL([
    ["Dato", "Qué significa"],
    ["Cultivo + severidad", "Cultivo del lote y qué tan grave es el foco (Muy alta → Baja)."],
    ["Hacienda · Lote", "Ubicación del foco."],
    ["Área", "Superficie afectada estimada (ha)."],
    ["Punto X/Y", "Progreso de muestreo del lote (p. ej. 3/8 puntos recorridos)."],
    ["Patrón satelital", "Cómo se ve el foco desde el satélite (foco denso, difuso, bordes, bajos)."],
], [3.6*cm, 11.4*cm])]
story += bl([
    "Tocá una tarjeta para <b>navegar</b> hasta ese foco.",
    "Las tres pestañas de abajo son: <b>Focos</b>, <b>Banco</b> (referencia) e <b>Historial</b> (tus validaciones).",
])
story += shot("02_focos", "focos activos ordenados por severidad.")

# ---------- 5. Navegación GPS ----------
story += [B.sec(5, "Navegación GPS hasta el foco")]
story += [B.P(
    "Al elegir un foco, la app abre la <b>brújula de aproximación</b>:", "Body")]
story += bl([
    "La <b>flecha</b> apunta hacia el foco (se orienta con la brújula del teléfono).",
    "El número grande es la <b>distancia</b> en metros o kilómetros, actualizada en vivo.",
    "Abajo ves tus <b>coordenadas y la precisión</b> del GPS (± metros).",
    "Cuando llegás a menos de 15 m, aparece <b>“estás en el foco”</b>.",
    "Tocá <b>“Diagnosticar aquí”</b> para arrancar la clave de diagnóstico.",
])
story += [B.callout("Sin señal, igual funciona",
    "Si el GPS todavía no fija posición, la app no te bloquea: podés diagnosticar igual. "
    "La precisión se muestra siempre para que sepas cuán confiable es la ubicación.")]
story += shot("03_nav", "brújula de aproximación con distancia y precisión en vivo.")

# ---------- 6. Diagnóstico ----------
story += [B.sec(6, "Diagnóstico diferencial en 4 pasos")]
story += [B.P(
    "La clave sigue el mismo razonamiento que un fitopatólogo a campo: primero el contexto, después la planta. "
    "Respondé tocando la opción que corresponde.", "Body")]
story += [TBL([
    ["Paso", "Pregunta", "Para qué sirve"],
    ["1 · Contexto", "Estadio del cultivo · ¿otros cultivos/vecinos afectados? · ¿súbito o gradual?",
        "Si afecta a varios cultivos o fue de golpe, apunta a causa abiótica."],
    ["2 · Patrón", "¿Cómo se distribuye el daño?",
        "Foco irregular → biótico. Parejo, en bordes o siguiendo el relieve → sospechar abiótico."],
    ["3 · Signo", "¿Hay signo del organismo (pústula, insecto, larva) o solo cambio de color?",
        "El signo confirma la causa biótica. Sin signo → carencia o abiótico."],
    ["4 · Rama", "Según el caso: avance de la enfermedad, tipo de daño de la plaga, o gradiente de hoja.",
        "Acota los candidatos al grupo correcto."],
], [2.4*cm, 6.3*cm, 6.3*cm])]
story += shot("04_contexto", "paso 1 — contexto del lote (estadio, hospederos, temporalidad).")
story += shot("05_signo", "paso 3 — ¿hay signo del organismo?")
story += [B.P("El resultado:", "H2")]
story += bl([
    "Una <b>hipótesis presuntiva</b> (enfermedad / plaga / carencia / causa abiótica) con un <b>% de confianza</b>.",
    "Una lista corta de <b>candidatos</b> ordenados; tocá cualquiera para ver su ficha.",
    "Si la confianza es baja o las señales son mixtas, la app avisa <b>“diagnóstico no concluyente”</b> y "
    "recomienda buscar el signo con lupa o <b>colectar muestra a laboratorio</b>.",
])
story += [B.callout("Regla de oro",
    "PIX Scout nunca fuerza un único resultado. Te da opciones con su confianza y vos, con la ficha delante, "
    "confirmás. La honestidad del diagnóstico es la que protege la decisión de campo.")]
story += shot("06_results", "hipótesis presuntiva con % de confianza y candidatos ordenados.")

# ---------- 7. Fichas / banco ----------
story += [B.sec(7, "Fichas y banco de conocimiento")]
story += [B.P(
    "Cada candidato abre una <b>ficha</b> pensada para comparar contra lo que tenés en la mano. También podés "
    "navegar el <b>Banco</b> completo por cultivo (pestaña Banco).", "Body")]
story += [TBL([
    ["Sección de la ficha", "Qué te dice"],
    ["Signo", "La presencia física del organismo (pústula, micelio, insecto). Es lo que confirma."],
    ["Síntoma", "La reacción de la planta (clorosis, necrosis, marchitez)."],
    ["Confirmación a campo", "La maniobra concreta para confirmar en el punto."],
    ["Diagnóstico diferencial", "Con qué se confunde y cómo diferenciarlo."],
    ["Umbral de acción (MIP)", "El nivel a partir del cual se justifica tratar, con su fuente citada."],
    ["Fotos de referencia", "Imágenes con licencia abierta para comparar con tu foto."],
    ["Manejo", "Orientación de manejo (integrado, MIP primero)."],
], [4.6*cm, 10.4*cm])]
story += shot("07_ficha", "ficha con signo, síntoma, confirmación y umbral MIP con fuente.")

# ---------- 8. Validación ----------
story += [B.sec(8, "Registrar la validación")]
story += [B.P(
    "Cuando confirmás el hallazgo, tocá <b>“Confirmar y registrar validación”</b>. Se abre la ficha de captura:", "Body")]
story += bl([
    "<b>Severidad in situ</b> y <b>% de incidencia</b> (plantas afectadas).",
    "<b>¿Coincide con el aviso del satélite?</b> (Sí / Parcial / No).",
    "Para <b>plagas</b>: comparás el conteo contra el <b>nivel de acción MIP</b>. La app te devuelve el veredicto:",
])
story += [TBL([
    ["Veredicto MIP", "Qué hacer"],
    ["Por debajo del umbral", "No tratar; seguir monitoreando."],
    ["En el umbral", "Re-monitorear en 2–3 días."],
    ["Lo supera", "Intervención justificada — con criterio MIP primero (biológico/cultural antes que químico)."],
], [5.0*cm, 10.0*cm])]
story += bl([
    "<b>Foto georreferenciada obligatoria</b>: se toma con la cámara (o se elige de la galería) y queda con las coordenadas.",
    "La validación se guarda <b>firmada con tu usuario</b> y con el punto GPS.",
])
story += [B.callout("Por qué la foto es obligatoria",
    "La foto + el punto GPS son la prueba que respalda el diagnóstico y alimentan la verdad de campo. "
    "Sin foto, el registro no se puede guardar.")]
story += shot("08_validacion", "captura: conteo vs nivel de acción MIP, severidad, foto obligatoria.")

# ---------- 9. Historial / sync ----------
story += [B.sec(9, "Historial y sincronización")]
story += [B.P(
    "La pestaña <b>Historial</b> lista todas tus validaciones, con su estado:", "Body")]
story += bl([
    "<b>pend</b> = guardada en el celular, pendiente de sincronizar.",
    "<b>sync</b> = ya enviada al sistema.",
    "El botón <b>“Sincronizar”</b> sube las pendientes cuando hay conexión.",
])
story += [B.callout("A prueba de pérdida de datos",
    "Todo se guarda primero en el dispositivo (offline-first). El envío es diferido y no destructivo: "
    "una validación solo se marca como sincronizada cuando el servidor la confirma. Nunca se pierde trabajo por falta de señal.")]
story += shot("09_historial", "historial con estado pendiente / sincronizado por validación.")

# ---------- 10. Herramientas de campo ----------
story += [B.sec(10, "Herramientas de campo")]
story += [TBL([
    ["Herramienta", "Para qué"],
    ["Modo Sol ☀", "Alto contraste para leer la pantalla a pleno sol. Un toque en el ícono del sol."],
    ["Tema claro/oscuro", "Cambia el aspecto general (desde Cuenta o el ícono de tema)."],
    ["Cuenta 👤", "Ver tu usuario, cambiar tema, cerrar sesión y —si sos admin— gestionar usuarios."],
    ["Indicador GPS", "Arriba a la izquierda muestra la precisión del GPS en todo momento."],
], [3.8*cm, 11.2*cm])]

# ---------- 11. Administración ----------
story += [B.sec(11, "Administración: dar de alta técnicos")]
story += [B.P(
    "Esta sección es para el <b>administrador</b>. Desde el ícono de <b>Cuenta → “Gestionar usuarios”</b>:", "Body")]
story += bl([
    "Ves la lista de usuarios con su rol (admin/técnico) y si están activos.",
    "<b>Crear usuario</b>: usuario, nombre del técnico, cliente/finca, rol y contraseña.",
    "<b>Activar / desactivar</b> con un toque: así habilitás o bloqueás a un técnico para trabajar a campo.",
])
story += [B.callout("Provisión por dispositivo",
    "En esta versión los usuarios se cargan en cada dispositivo. Para gestión central multi-dispositivo "
    "(un panel único para todos los celulares) se conecta el backend en la nube — es el siguiente paso del proyecto.")]
story += shot("10_users", "panel de administración: alta y activación de técnicos.")

# ---------- 12. Buenas prácticas / FAQ ----------
story += [B.sec(12, "Buenas prácticas y preguntas frecuentes")]
story += bl([
    "<b>Cargá la app con señal antes de salir</b> para tener los focos del día; después trabaja sin problema offline.",
    "<b>Sacá la foto lo más nítida posible</b> y de cerca: mejora la comparación y la confianza del diagnóstico.",
    "<b>Ante duda, colectá muestra</b>: el botón de laboratorio está siempre a mano.",
    "<b>Sincronizá al volver</b> a zona con señal para respaldar tus validaciones.",
    "<b>Modo Sol</b> si no ves bien la pantalla en el lote.",
])
story += [B.P("Preguntas frecuentes", "H2")]
story += [TBL([
    ["Pregunta", "Respuesta"],
    ["¿Funciona sin internet?", "Sí. Todo el diagnóstico, el banco y el guardado son offline. Solo el envío final necesita señal."],
    ["Olvidé mi contraseña", "El administrador puede reasignártela desde Gestionar usuarios."],
    ["¿Se pierden datos sin señal?", "No. Quedan en el celular como “pend” y se sincronizan después."],
    ["¿El diagnóstico es definitivo?", "No: es una hipótesis. Confirmá con la ficha y, si hay duda, con laboratorio."],
], [4.8*cm, 10.2*cm])]

story += [B.callout("Soporte",
    "Dudas o mejoras: Pixadvisor Agricultura de Precisión. Este manual corresponde a PIX Scout v1.0.0.")]

# ---------- Build ----------
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "release", "PIX-Scout-Tutorial-v1.0.0.pdf")
OUT = os.path.abspath(OUT)
B.build(OUT, story,
        cover_title="PIX Scout — Guía de uso",
        cover_subtitle="Manual del técnico de campo · App de validación de anomalías · v1.0.0")
print("OK ->", OUT)
