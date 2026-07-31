# -*- coding: utf-8 -*-
"""
Protocolo de aplicacion MAX PIROL — potencializador de herbicidas
Desecacion pre-siembra soya 26/27 — Hacienda Cerro Alto (cliente Joao Geraldo).
Estilo ejecutivo Pixadvisor (pix_branding.Brand).
"""
import os, sys
from reportlab.lib.units import cm
from reportlab.platypus import Spacer, PageBreak, CondPageBreak

SKILL = r"C:\Users\Usuario\.claude\skills\pixadvisor-propuesta-ejecutiva"
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from pix_branding import Brand, TEAL, AZUL, LIMA, AMBAR, GRIS_CLR  # noqa: E402

LOGO = os.path.join(SKILL, "assets", "logo_pix_azulnegro_trim.png")
OUTDIR = r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS\Joao-Geraldo\04-Informes"
OUT = os.path.join(OUTDIR, "Protocolo_MAXPIROL_Desecacion_CerroAlto_Soya_26-27.pdf")

FECHA = "26 de julio de 2026"
AREA_UTIL = 1782.8

B = Brand(logo=LOGO, content_w=17.0 * cm,
          footer_center="Protocolo de aplicación · MAX PIROL · Cerro Alto")
W = B.CONTENT_W
P = B.P


def bul(t):
    return B.P("• " + t, "Bull")


def nota(t):
    return B.P(t, "Note")


story = []
story += B.cover_filler()

# ---------------------------------------------------------------- Ficha
story += [P("Ficha del documento", "H1"), B.hr()]
story += [B.meta_table([
    ("Hacienda", "Cerro Alto — Santa Cruz, Bolivia"),
    ("Cliente", "João Geraldo"),
    ("Responsable agrícola", "Ing. Agr. Marcelo — encargado del área agrícola"),
    ("Cultivo y campaña", "Soya, campaña 26/27"),
    ("Operación", "Desecación pre-siembra (barbecho químico previo a la siembra)"),
    ("Superficie de referencia", "1.782,8 ha útiles (bruta 1.871,5 ha · 66 divisiones-lote · bloques 2, 3 y 14)"),
    ("Producto", "MAX PIROL — extracto piroleñoso"),
    ("Fabricante", "MDO Agro Indústria Ltda. — Nova Esperança, Paraná, Brasil"),
    ("Importa y distribuye", "Pixadvisor S.R.L. — NIT 527663028"),
    ("Función en este protocolo", "Potencializador del herbicida y acondicionador del caldo. Permite reducir la dosis comercial del herbicida."),
    ("Elaborado por", "Pixadvisor Agricultura de Precisión"),
    ("Fecha de emisión", FECHA),
])]
story += [Spacer(1, 0.5 * cm)]
story += [B.kpi_strip([
    ("1,0 %", "del caudal<br/>maleza en estadio temprano"),
    ("1,5 %", "del caudal<br/>maleza en estadio avanzado"),
    ("- 30 %", "dosis comercial<br/>de glifosato"),
    ("- 20 %", "dosis comercial<br/>de otros herbicidas"),
])]
story += [Spacer(1, 0.5 * cm)]
story += [B.callout("EN UNA LÍNEA",
                    "MAX PIROL se carga en el agua limpia, antes de cualquier herbicida, a razón de "
                    "<b>1,0 % del caudal</b> si la maleza está en estadio temprano y <b>1,5 %</b> si está "
                    "en estadio avanzado. Con el caldo así acondicionado se reduce la dosis comercial del "
                    "herbicida: <b>30 % menos en glifosato</b> y <b>20 % menos en los demás herbicidas</b>.")]

story += [Spacer(1, 0.3 * cm), P("Contenido", "H1"), B.hr(), B.toc(), PageBreak()]

# ---------------------------------------------------------------- 1
story += [B.sec(1, "Qué hace MAX PIROL en la desecación")]
story += [P("MAX PIROL es un extracto piroleñoso: la condensación de los gases de la pirólisis de madera. "
            "Químicamente es una solución acuosa de ácidos orgánicos (acético, propiónico, fórmico) y "
            "compuestos fenólicos (guayacoles, siringoles), de reacción fuertemente ácida. En el tanque de "
            "pulverización cumple tres funciones concretas:")]
story += [bul("<b>Baja el pH del caldo.</b> Los herbicidas de reacción ácida débil —el glifosato entre ellos— "
              "trabajan mejor en caldos de pH ácido. El agua alcalina degrada la molécula por hidrólisis antes "
              "de que llegue a la hoja.")]
story += [bul("<b>Secuestra los cationes del agua dura.</b> El calcio, el magnesio y el hierro del agua se unen "
              "al glifosato y forman sales que la planta prácticamente no absorbe. El extracto actúa como "
              "quelante y libera la molécula activa.")]
story += [bul("<b>Estabiliza y uniformiza el caldo.</b> Mejora la homogeneidad de la mezcla y la uniformidad "
              "del secado, sobre todo en mezclas de varios productos.")]
story += [Spacer(1, 0.25 * cm)]
story += [P("El resultado práctico de esas tres funciones es que el herbicida trabaja en mejores condiciones "
            "y rinde más por litro. Sobre esa base se ajusta la dosis del herbicida, según el apartado 4.")]

# ---------------------------------------------------------------- 2
story += [B.sec(2, "Dosis de MAX PIROL: cómo decidir entre 1,0 % y 1,5 %")]
story += [P("La dosis se define por el <b>estadio y el porte de la maleza</b> al momento de la aplicación, "
            "no por el lote ni por el herbicida elegido. Recorrer el lote antes de cargar el tanque y "
            "clasificar según esta tabla:")]
story += [B.tbl([
    [P("Estadio", "CellB"), P("Cómo se reconoce en el campo", "CellB"), P("MAX PIROL", "CellB")],
    [P("<b>Temprano</b>", "Cell"),
     P("Maleza en crecimiento activo. Latifoliadas hasta 4 hojas verdaderas o de 10 a 15 cm de altura; "
       "gramíneas hasta inicio de macollaje. Sin floración, hoja tierna, sin estrés hídrico.", "Cell"),
     P("<b>1,0 %</b><br/>del caudal", "Cell")],
    [P("<b>Avanzado</b>", "Cell"),
     P("Maleza de más de 15 a 20 cm, ramificada o macollada, en floración o pasada de floración, cutícula "
       "engrosada; rebrote de barbecho largo; o presencia de especies de control difícil "
       "(<i>Conyza</i> spp., <i>Digitaria insularis</i>, <i>Euphorbia heterophylla</i>, "
       "<i>Amaranthus</i> spp., <i>Ipomoea</i> spp., <i>Chloris</i> spp.).", "Cell"),
     P("<b>1,5 %</b><br/>del caudal", "Cell")],
], [2.6 * cm, W - 6.2 * cm, 3.6 * cm])]
story += [Spacer(1, 0.2 * cm)]
story += [nota("Si dentro del mismo lote conviven los dos estadios, se aplica el criterio del estadio más "
               "avanzado: <b>1,5 %</b>. Nunca se mezclan dos dosis en el mismo tanque.")]

story += [P("2.1 · Del porcentaje a los litros por hectárea", "H2")]
story += [P("El porcentaje es sobre el <b>caudal de aplicación</b> (volumen de caldo por hectárea). "
            "Cambiar el caudal cambia los litros de producto por hectárea:")]
story += [B.tbl([
    [P("Caudal de aplicación", "CellB"), P("MAX PIROL a 1,0 %", "CellB"), P("MAX PIROL a 1,5 %", "CellB")],
    [P("80 L/ha", "Cell"), P("0,80 L/ha", "Cell"), P("1,20 L/ha", "Cell")],
    [P("<b>100 L/ha</b>", "Cell"), P("<b>1,00 L/ha</b>", "Cell"), P("<b>1,50 L/ha</b>", "Cell")],
    [P("<b>120 L/ha</b>", "Cell"), P("<b>1,20 L/ha</b>", "Cell"), P("<b>1,80 L/ha</b>", "Cell")],
    [P("<b>150 L/ha</b>", "Cell"), P("<b>1,50 L/ha</b>", "Cell"), P("<b>2,25 L/ha</b>", "Cell")],
    [P("200 L/ha", "Cell"), P("2,00 L/ha", "Cell"), P("3,00 L/ha", "Cell")],
], [W - 10.0 * cm, 5.0 * cm, 5.0 * cm], aligns={1: "CENTER", 2: "CENTER"})]
story += [Spacer(1, 0.2 * cm)]
story += [nota("Las filas en negrita son la ventana de trabajo recomendada para desecación terrestre en "
               "Cerro Alto (100 a 150 L/ha). Ahí el porcentaje y la dosis por hectárea quedan alineados con el "
               "rango de uso del fabricante para manejo herbicida.")]
story += [Spacer(1, 0.2 * cm)]
story += [B.callout("APLICACIÓN AÉREA",
                    "Con caudales aéreos (30 a 40 L/ha) la regla del porcentaje deja el producto por debajo de "
                    "su rango útil por hectárea. En aplicación aérea <b>no usar el porcentaje</b>: fijar la "
                    "dosis en <b>1,0 L/ha</b> (maleza temprana) o <b>1,5 L/ha</b> (maleza avanzada). "
                    "Criterio operativo Pixadvisor.")]

story += [P("2.2 · Carga por tanque", "H2")]
story += [P("Regla práctica para el operador: <b>10 litros de MAX PIROL por cada 1.000 litros de caldo</b> "
            "a 1,0 %, y <b>15 litros por cada 1.000</b> a 1,5 %.")]
story += [B.tbl([
    [P("Capacidad del tanque", "CellB"), P("A 1,0 %", "CellB"), P("A 1,5 %", "CellB"),
     P("Cubre a 100 L/ha", "CellB"), P("Cubre a 150 L/ha", "CellB")],
    [P("2.000 L", "Cell"), P("20 L", "Cell"), P("30 L", "Cell"), P("20,0 ha", "Cell"), P("13,3 ha", "Cell")],
    [P("2.500 L", "Cell"), P("25 L", "Cell"), P("37,5 L", "Cell"), P("25,0 ha", "Cell"), P("16,7 ha", "Cell")],
    [P("3.000 L", "Cell"), P("30 L", "Cell"), P("45 L", "Cell"), P("30,0 ha", "Cell"), P("20,0 ha", "Cell")],
    [P("4.000 L", "Cell"), P("40 L", "Cell"), P("60 L", "Cell"), P("40,0 ha", "Cell"), P("26,7 ha", "Cell")],
], [W - 12.8 * cm, 3.0 * cm, 3.0 * cm, 3.4 * cm, 3.4 * cm],
    aligns={1: "CENTER", 2: "CENTER", 3: "CENTER", 4: "CENTER"})]
story += [Spacer(1, 0.2 * cm)]
story += [nota("La dosis se calcula siempre sobre el <b>volumen final del tanque</b>, no sobre el agua que hay "
               "cargada en el momento de agregarlo.")]

# ---------------------------------------------------------------- 3 (nueva)
story += [B.sec(3, "Reducción de la dosis del herbicida")]
story += [P("Con el caldo acondicionado con MAX PIROL el herbicida rinde más, y la dosis se ajusta hacia "
            "abajo. La reducción se calcula sobre la <b>dosis comercial que la hacienda viene usando</b> "
            "para esa maleza y ese estadio.")]
story += [B.tbl([
    [P("Herbicida", "CellB"), P("Reducción", "CellB"), P("Cómo se calcula", "CellB")],
    [P("<b>Glifosato</b>", "Cell"), P("<b>- 30 %</b>", "Cell"),
     P("Dosis comercial × 0,70. Ejemplo: 3,0 L/ha pasan a 2,1 L/ha.", "Cell")],
    [P("<b>Los demás herbicidas</b> de la mezcla", "Cell"), P("<b>- 20 %</b>", "Cell"),
     P("Dosis comercial × 0,80. Ejemplo: 1,0 L/ha pasan a 0,8 L/ha.", "Cell")],
], [W - 10.0 * cm, 3.0 * cm, 7.0 * cm], aligns={1: "CENTER"})]
story += [Spacer(1, 0.25 * cm)]
story += [P("3.1 · Tabla rápida para glifosato", "H2")]
story += [B.tbl([
    [P("Dosis comercial habitual", "CellB"), P("Con MAX PIROL (- 30 %)", "CellB"),
     P("Ahorro por hectárea", "CellB")],
    [P("2,0 L/ha", "Cell"), P("<b>1,40 L/ha</b>", "Cell"), P("0,60 L/ha", "Cell")],
    [P("2,5 L/ha", "Cell"), P("<b>1,75 L/ha</b>", "Cell"), P("0,75 L/ha", "Cell")],
    [P("3,0 L/ha", "Cell"), P("<b>2,10 L/ha</b>", "Cell"), P("0,90 L/ha", "Cell")],
    [P("3,5 L/ha", "Cell"), P("<b>2,45 L/ha</b>", "Cell"), P("1,05 L/ha", "Cell")],
    [P("4,0 L/ha", "Cell"), P("<b>2,80 L/ha</b>", "Cell"), P("1,20 L/ha", "Cell")],
], [W - 11.0 * cm, 5.5 * cm, 5.5 * cm], aligns={1: "CENTER", 2: "CENTER"})]
story += [Spacer(1, 0.25 * cm)]
story += [B.callout("VAN JUNTOS",
                    "La reducción del herbicida y la carga de MAX PIROL son una sola decisión. Si por "
                    "cualquier motivo un tanque sale <b>sin</b> MAX PIROL, ese tanque va con la "
                    "<b>dosis comercial plena</b> del herbicida.")]
story += [Spacer(1, 0.2 * cm)]
story += [nota("Respaldo: ensayo de campo propio de Pixadvisor con MAX PIROL, en el que la reducción del "
               "30 % de la dosis de glifosato mantuvo la eficiencia de control de malezas.")]

# ---------------------------------------------------------------- 4
story += [B.sec(4, "Orden de mezcla — el punto crítico")]
story += [P("Este es el apartado que decide si el protocolo funciona o falla. MAX PIROL <b>acondiciona el "
            "agua</b>: corrige el pH y secuestra los cationes <i>antes</i> de que el herbicida entre en "
            "contacto con ellos. Si se agrega después del herbicida, el daño ya está hecho y además sube el "
            "riesgo de precipitado.")]
story += [B.tbl([
    [P("Paso", "CellB"), P("Qué entra al tanque", "CellB"), P("Detalle operativo", "CellB")],
    [P("<b>1</b>", "Cell"), P("Agua limpia hasta 1/2 – 2/3 del tanque", "Cell"),
     P("Agitación <b>en marcha</b> antes de cargar cualquier producto. Agua filtrada y decantada.", "Cell")],
    [P("<b>2</b>", "Cell"), P("<b>MAX PIROL</b>", "Cell"),
     P("Dosis calculada sobre el volumen <b>final</b> del caldo. Agitar 3 a 5 minutos.", "Cell")],
    [P("<b>3</b>", "Cell"), P("Medición de pH", "Cell"),
     P("Objetivo <b>4,5 a 5,5</b>. Nunca por debajo de 4,0. Anotar en la planilla de registro.", "Cell")],
    [P("<b>4</b>", "Cell"), P("Sólidos: WG · WDG · SG · WP", "Cell"),
     P("Pre-diluir en balde con agua y volcar al tanque con la agitación en marcha.", "Cell")],
    [P("<b>5</b>", "Cell"), P("Suspensiones: SC · CS · SE", "Cell"),
     P("Agitar el envase antes de dosificar. Esperar homogeneización.", "Cell")],
    [P("<b>6</b>", "Cell"), P("Solubles SL: <b>primero glifosato, después 2,4-D</b>", "Cell"),
     P("Nunca al revés: invertir el orden es la causa habitual del precipitado tipo cuajada que tapa "
       "picos y filtros.", "Cell")],
    [P("<b>7</b>", "Cell"), P("Oleosos: EC · OD, aceites y surfactantes", "Cell"),
     P("Siempre últimos, ya con la mayor parte del agua en el tanque.", "Cell")],
    [P("<b>8</b>", "Cell"), P("Completar el volumen con agua", "Cell"),
     P("Agitación continua hasta terminar la aplicación.", "Cell")],
], [1.5 * cm, 6.0 * cm, W - 7.5 * cm])]
story += [Spacer(1, 0.25 * cm)]
story += [B.callout("REGLA FIJA",
                    "MAX PIROL entra <b>siempre en el agua y siempre antes de todo herbicida</b>. Nunca se "
                    "vierte sobre un producto concentrado ni se mezcla con otro concentrado fuera del tanque.")]

# ---------------------------------------------------------------- 4
story += [B.sec(5, "Preparación del tanque — paso a paso")]
for i, t in enumerate([
    "Verificar que el tanque, los filtros y los picos estén limpios y sin restos de la aplicación anterior.",
    "Cargar agua limpia y filtrada hasta la mitad o dos tercios del volumen. Encender la agitación.",
    "Calcular la dosis de MAX PIROL sobre el volumen final (10 L/1.000 L a 1,0 % · 15 L/1.000 L a 1,5 %).",
    "Cargar MAX PIROL y agitar de 3 a 5 minutos.",
    "Medir el pH con cinta o pHmetro. Objetivo 4,5 a 5,5. Si baja de 4,0, agregar agua y volver a medir.",
    "Cargar los herbicidas en el orden de la tabla del apartado 4, uno por vez, esperando homogeneización.",
    "Completar con agua hasta el volumen final.",
    "Mantener la agitación durante todo el traslado y toda la aplicación.",
    "Aplicar el caldo el mismo día. No dejar caldo preparado de un día para el otro.",
], 1):
    story += [B.P("<b>%d.</b>  %s" % (i, t), "Bull")]

# ---------------------------------------------------------------- 5
story += [B.sec(6, "Prueba de jarra — obligatoria antes del primer tanque")]
story += [P("Se hace una sola vez por cada combinación distinta de productos y por cada fuente de agua. "
            "Toma quince minutos y evita perder un tanque entero en el lote.")]
for i, t in enumerate([
    "Tomar 1 litro de la misma agua que se va a usar en el tanque, en un frasco de vidrio transparente.",
    "Dividir cada dosis del tanque por el volumen del tanque en litros. Ejemplo: tanque de 3.000 L con 30 L "
    "de MAX PIROL da 10 mL en la jarra.",
    "Agregar los productos en el mismo orden del apartado 4, agitando 30 segundos entre uno y otro.",
    "Dejar reposar 30 minutos sin agitar.",
    "Observar: grumos, natas en la superficie, separación de fases, sedimento en el fondo o aumento de "
    "viscosidad.",
], 1):
    story += [B.P("<b>%d.</b>  %s" % (i, t), "Bull")]
story += [Spacer(1, 0.2 * cm)]
story += [B.tbl([
    [P("Resultado", "CellB"), P("Decisión", "CellB")],
    [P("Caldo homogéneo, sin sedimento ni natas", "Cell"),
     P("Mezcla aprobada. Preparar el tanque con el mismo orden.", "Cell")],
    [P("Sedimento leve que se redispersa al agitar", "Cell"),
     P("Aceptable solo con agitación continua garantizada. Reducir MAX PIROL a 0,5 % y repetir la prueba.", "Cell")],
    [P("Grumos, natas, fases separadas o cuajada", "Cell"),
     P("<b>No aplicar esa mezcla.</b> Separar la aplicación en dos pasadas o consultar a Pixadvisor antes "
       "de cargar el tanque.", "Cell")],
], [W - 9.5 * cm, 9.5 * cm])]

# ---------------------------------------------------------------- 6
story += [B.sec(7, "Incompatibilidades y precauciones")]
story += [B.tbl([
    [P("Situación", "CellB"), P("Qué hacer", "CellB")],
    [P("<b>Dicamba en la mezcla</b>", "Cell"),
     P("<b>NO usar MAX PIROL en ese tanque.</b> Bajar el pH aumenta la proporción de dicamba en forma ácida "
       "y con ello su volatilización, con riesgo de deriva sobre soya no tolerante y cultivos vecinos.", "Cell")],
    [P("<b>2,4-D sal amina</b>", "Cell"),
     P("Combinación de riesgo conocido de precipitación. Prueba de jarra obligatoria. Orden: primero "
       "MAX PIROL, después "
       "glifosato y por último 2,4-D. No dejar el pH por debajo de 4,0.", "Cell")],
    [P("Productos alcalinos (cobre, caldo bordelés, fosfitos alcalinos, cal)", "Cell"),
     P("No mezclar. Se neutralizan con el extracto y pueden precipitar.", "Cell")],
    [P("pH del caldo por debajo de 4,0", "Cell"),
     P("Corregir agregando agua. Por debajo de 3,5 hay riesgo de precipitación de las sales del herbicida y "
       "de mayor fitotoxicidad.", "Cell")],
    [P("Agua turbia o con arcilla en suspensión", "Cell"),
     P("Decantar o filtrar antes de cargar. La arcilla adsorbe el glifosato y ningún adyuvante corrige eso.", "Cell")],
    [P("Caldo preparado y no aplicado", "Cell"),
     P("No guardarlo de un día para el otro. Descargar en área segura y lavar el equipo.", "Cell")],
    [P("Tanque cargado sin MAX PIROL", "Cell"),
     P("Ese tanque va con la dosis comercial plena del herbicida. La reducción del apartado 3 solo aplica "
       "cuando el caldo lleva MAX PIROL.", "Cell")],
], [W - 11.5 * cm, 11.5 * cm])]


# ---------------------------------------------------------------- 7
story += [B.sec(8, "Condiciones de aplicación")]
story += [B.tbl([
    [P("Parámetro", "CellB"), P("Rango operativo", "CellB")],
    [P("Momento", "Cell"), P("Según la etiqueta del herbicida y el plan de siembra. Maleza en crecimiento "
                             "activo, sin estrés hídrico.", "Cell")],
    [P("Temperatura", "Cell"), P("Por debajo de 30 °C", "Cell")],
    [P("Humedad relativa", "Cell"), P("Por encima de 55 a 60 %", "Cell")],
    [P("Viento", "Cell"), P("3 a 10 km/h. No aplicar en calma total (inversión térmica) ni por encima de "
                            "12 km/h.", "Cell")],
    [P("Ventana horaria", "Cell"), P("Primeras horas de la mañana o última tarde. Evitar 11:00 a 16:00.", "Cell")],
    [P("Caudal", "Cell"), P("100 a 150 L/ha terrestre. Usar 150 L/ha con alta densidad o porte de maleza.", "Cell")],
    [P("Tamaño de gota", "Cell"), P("Media, 200 a 300 µm. Evitar gota muy fina (deriva) y muy gruesa "
                                    "(falla de cobertura).", "Cell")],
    [P("Agua", "Cell"), P("Limpia, filtrada y decantada. Registrar la fuente en la planilla.", "Cell")],
    [P("Lluvia", "Cell"), P("Respetar el período libre de lluvia indicado en la etiqueta del herbicida.", "Cell")],
], [W - 12.5 * cm, 12.5 * cm])]

# ---------------------------------------------------------------- 8
story += [B.sec(9, "Franja testigo y validación en Cerro Alto")]
story += [P("Para que la campaña 26/27 deje el dato demostrado sobre el propio campo de Cerro Alto, se deja "
            "una franja testigo por bloque. Es la forma de que el Ing. Marcelo vea la reducción de dosis "
            "funcionando en su suelo y con su maleza:")]
story += [B.tbl([
    [P("Franja", "CellB"), P("Tratamiento", "CellB"), P("Para qué sirve", "CellB")],
    [P("<b>A</b>", "Cell"), P("Herbicida solo, dosis comercial plena", "Cell"),
     P("Línea base. Es contra esta franja que se mide todo lo demás.", "Cell")],
    [P("<b>B</b>", "Cell"), P("Herbicida reducido (apartado 3) + MAX PIROL 1,0 %", "Cell"),
     P("Demuestra la reducción de dosis con maleza en estadio temprano.", "Cell")],
    [P("<b>C</b>", "Cell"), P("Herbicida reducido (apartado 3) + MAX PIROL 1,5 %", "Cell"),
     P("Demuestra la reducción con maleza avanzada y verifica si la dosis alta se justifica.", "Cell")],
], [1.7 * cm, 6.6 * cm, W - 8.3 * cm])]
story += [Spacer(1, 0.25 * cm)]
story += [P("9.1 · Cómo se ejecuta", "H2")]
story += [bul("Una franja por bloque (2, 3 y 14), del ancho completo de la barra y al menos 200 m de largo, "
              "sobre maleza homogénea.")]
story += [bul("Mismo día, mismo operador, mismo equipo y mismo herbicida. Lo único que cambia entre franjas "
              "es MAX PIROL y la dosis del herbicida.")]
story += [bul("Georreferenciar los extremos de cada franja con el APK PIX Muestreo y dejar registro "
              "fotográfico con GPS.")]
story += [bul("Evaluación visual de porcentaje de control a los <b>3, 7, 14 y 21 días</b> después de la "
              "aplicación, en 5 puntos de 0,25 m² por franja.")]
story += [bul("Seguimiento satelital Pixadvisor con Sentinel-2: se toma la <b>escena limpia anterior a la "
              "aplicación</b> como referencia y se compara la caída de NDVI y NDMI franja por franja. La "
              "referencia es la escena previa, no el promedio de la temporada.")]
story += [Spacer(1, 0.2 * cm)]
story += [B.callout("CRITERIO DE LECTURA",
                    "La reducción de dosis queda demostrada en Cerro Alto cuando <b>B y C igualan a A</b> a "
                    "los 14 días. Entre B y C: se adopta el 1,5 % para maleza avanzada solo si supera al "
                    "1,0 % por al menos <b>10 puntos porcentuales</b> de control; si la diferencia es menor, "
                    "el 1,0 % alcanza.")]

# ---------------------------------------------------------------- 9
story += [B.sec(10, "Planilla de registro por aplicación")]
story += [P("Una fila por tanque. Sin este registro la franja testigo del apartado 9 no se puede interpretar.")]
_h = ["Fecha", "Bloque / lote", "Sup. (ha)", "Tanque Nº", "Caudal (L/ha)", "pH", "MAX PIROL (L)", "Operador"]
_rows = [[P(h, "CellB") for h in _h]] + [[P("", "Cell") for _ in _h] for _ in range(9)]
story += [B.tbl(_rows, [2.2 * cm, 2.6 * cm, 1.7 * cm, 1.6 * cm, 2.1 * cm, 1.2 * cm, 2.3 * cm,
                        W - 13.7 * cm])]
story += [Spacer(1, 0.2 * cm)]
story += [nota("Campos adicionales a anotar al dorso: hora de inicio y fin, fuente del agua, pH del agua "
               "antes de MAX PIROL, herbicida y dosis, temperatura, humedad relativa, viento y observaciones "
               "sobre el estadio de la maleza.")]

# ---------------------------------------------------------------- 10
story += [B.sec(11, "Cálculo de producto para la campaña")]
story += [P("Sobre la superficie útil de siembra de Cerro Alto, <b>1.782,8 ha</b>, para una pasada de "
            "desecación:")]


def _fmt(x):
    return ("{:,.0f}".format(x)).replace(",", ".")


rows = [[P("Escenario de aplicación", "CellB"), P("MAX PIROL", "CellB"),
         P("Total 1.782,8 ha", "CellB"), P("Bidones de 20 L", "CellB")]]
for caudal, pct in [(100, 1.0), (100, 1.5), (120, 1.0), (120, 1.5), (150, 1.0), (150, 1.5)]:
    lha = caudal * pct / 100.0
    tot = lha * AREA_UTIL
    rows.append([
        P("Caudal %d L/ha · %s %%" % (caudal, ("%0.1f" % pct).replace(".", ",")), "Cell"),
        P(("%0.2f" % lha).replace(".", ",") + " L/ha", "Cell"),
        P(_fmt(tot) + " L", "Cell"),
        P(str(int(-(-tot // 20))), "Cell"),
    ])
story += [B.tbl(rows, [W - 12.0 * cm, 4.0 * cm, 4.0 * cm, 4.0 * cm],
                aligns={1: "CENTER", 2: "CENTER", 3: "CENTER"})]
story += [Spacer(1, 0.2 * cm)]
story += [nota("Si se aplica sobre la superficie bruta (1.871,5 ha) en lugar de la útil, multiplicar los "
               "totales por 1,05. Si el plan de manejo contempla una segunda desecación de repaso, duplicar. "
               "Prever un 5 % adicional para lavados de tanque y pérdidas de manipuleo.")]

# ---------------------------------------------------------------- 11
story += [B.sec(12, "Seguridad, manipuleo y almacenaje")]
story += [bul("Producto de reacción fuertemente ácida (pH aproximado 2,5 a 3 en el concentrado): usar "
              "guantes, antiparras y ropa de trabajo cerrada al dosificar.")]
story += [bul("En caso de contacto con piel u ojos, lavar con agua abundante durante 15 minutos.")]
story += [bul("Almacenar en el envase original cerrado, a la sombra, lejos de fuentes de calor y separado de "
              "productos alcalinos y de fertilizantes.")]
story += [bul("No reenvasar en recipientes de alimentos ni de bebidas.")]
story += [bul("Respetar íntegramente las medidas de seguridad, los equipos de protección personal y los "
              "plazos indicados en la etiqueta del <b>herbicida</b>, que es el producto que gobierna el "
              "riesgo de la aplicación.")]


# ---------------------------------------------------------------- Anexo A
story += [B.sec(13, "Anexo A · Base técnica")]
story += [P("Lo que respalda cada decisión de este protocolo, con la fuente correspondiente.")]
story += [B.tbl([
    [P("Tema", "CellB"), P("Evidencia", "CellB")],
    [P("Efecto adyuvante del extracto piroleñoso", "Cell"),
     P("Zeferino, I.; Lima, E. A.; Vieira, E. S. N. <i>Uso do extrato pirolenhoso como adjuvante de "
       "herbicida.</i> Embrapa Florestas, Comunicado Técnico 429, Colombo (PR), dic. 2018. El extracto a "
       "2 L/ha con media dosis de oxifluorfen inhibió por completo la germinación de <i>Brachiaria "
       "decumbens</i>, <i>Bidens pilosa</i> y <i>Amaranthus viridis</i>, superando a la dosis comercial "
       "plena. <b>Ensayo de laboratorio sobre germinación de semillas, no de desecación foliar a campo.</b>", "Cell")],
    [P("Reducción de dosis en desecación", "Cell"),
     P("<i>Redução da dose de glifosato na dessecação de cana-de-açúcar com extrato pirolenhoso.</i> "
       "Revista de Gestão e Secretariado. Glifosato 3,0 L/ha + 0,5 L/ha de extracto piroleñoso + aceite "
       "mineral dio control equivalente a la dosis comercial de 3,5 L/ha, con menor rebrote y menor "
       "acumulación de biomasa.", "Cell")],
    [P("Media dosis con extracto en post-emergencia", "Cell"),
     P("Rico et al. (2007), Acenas et al. (2013) y Seo et al. (2015), Corea del Sur: extracto piroleñoso a "
       "1:500 y 1:1000 con media dosis de herbicida igualó el desempeño de la dosis plena en el control de "
       "<i>Echinochloa crus-galli</i> y otras malezas de arroz.", "Cell")],
    [P("Acción propia sobre la hoja", "Cell"),
     P("Aguirre et al. (2020), <i>Energies</i> y <i>Food and Energy Security</i>: a concentraciones altas "
       "(por encima de 25 % v/v) el extracto actúa como herbicida de contacto; la microscopía electrónica "
       "muestra cierre estomático y colapso celular a las 24 horas.", "Cell")],
    [P("Composición y pH", "Cell"),
     P("Solución acuosa de ácidos carboxílicos (acético, propiónico, fórmico) y compuestos fenólicos "
       "(guayacoles, siringoles), obtenida por condensación de los gases de pirólisis de madera a unos "
       "350 a 400 °C. pH del concentrado próximo a 2,5. Ficha de línea agrícola de MDO Agro Indústria.", "Cell")],
    [P("pH del caldo", "Cell"),
     P("Los herbicidas de ácido débil trabajan mejor entre pH 4 y 6; el glifosato en el rango 3,5 a 5,0. "
       "Por debajo de pH 3,5 aparece riesgo de disociación iónica y precipitación del producto.", "Cell")],
    [P("Agua dura", "Cell"),
     P("Los cationes Ca<super>2+</super>, Mg<super>2+</super> y Fe del agua forman con el glifosato sales "
       "complejas poco absorbidas por "
       "la planta y reducen su eficacia. Es el fundamento del acondicionamiento previo del agua.", "Cell")],
    [P("Dicamba y pH bajo", "Cell"),
     P("Caldos con pH por debajo de 5,0 aumentan la fracción de dicamba en forma ácida y su volatilización. "
       "Las propias etiquetas advierten no usar adyuvantes que acidifiquen el caldo. De ahí la exclusión del "
       "apartado 7.", "Cell")],
    [P("Orden de mezcla", "Cell"),
     P("Secuencia estándar de tecnología de aplicación: acondicionadores de agua primero, luego sólidos "
       "(WG/SG), suspensiones (SC/CS), solubles (SL) y por último oleosos (EC/OD). Con agua dura o "
       "glifosato, el reductor de pH va antes que los fitosanitarios. Glifosato antes que 2,4-D para evitar "
       "precipitación.", "Cell")],
], [W - 13.0 * cm, 13.0 * cm])]

story += [PageBreak()]

# ---------------------------------------------------------------- Anexo B
story += [B.sec(14, "Anexo B · Respaldo de la reducción de dosis")]
story += [P("La reducción del apartado 3 no es una extrapolación de literatura: es el resultado propio de "
            "Pixadvisor, alineado además con lo que reporta la investigación publicada.")]
story += [bul("<b>Ensayo de campo propio de Pixadvisor con MAX PIROL.</b> La dosis de glifosato se bajó un "
              "<b>30 %</b> respecto de la dosis comercial y se mantuvo la eficiencia en el control de "
              "malezas. Es el respaldo directo de la recomendación de este protocolo.")]
story += [bul("<b>Caña de azúcar.</b> Glifosato 3,0 L/ha + 0,5 L/ha de extracto piroleñoso + aceite mineral "
              "dio control equivalente a la dosis comercial de 3,5 L/ha, con menor rebrote y menor "
              "acumulación de biomasa.")]
story += [bul("<b>Post-emergentes en arroz (Corea del Sur).</b> Extracto piroleñoso a 1:500 y 1:1000 con "
              "media dosis de herbicida igualó el desempeño de la dosis plena.")]
story += [bul("<b>Pre-emergencia (Embrapa).</b> Extracto a 2 L/ha con media dosis de oxifluorfen inhibió por "
              "completo la germinación de las tres malezas evaluadas, superando a la dosis comercial plena.")]
story += [Spacer(1, 0.2 * cm)]
story += [P("La franja testigo del apartado 9 no está para poner en duda la reducción, sino para dejarla "
            "<b>documentada sobre el propio campo de Cerro Alto</b>, con fotos georreferenciadas y "
            "seguimiento satelital, y para afinar entre 1,0 % y 1,5 % según la maleza de la hacienda.")]
story += [Spacer(1, 0.4 * cm)]
story += [B.callout("CONSULTAS",
                    "Pixadvisor Agricultura de Precisión — soporte técnico de campo para la campaña 26/27 de "
                    "Cerro Alto. Ante cualquier resultado inesperado en la prueba de jarra o en la franja "
                    "testigo, consultar antes de generalizar la aplicación.")]

# Ningun encabezado de seccion debe quedar huerfano al pie de una pagina.
_flow = []
for _f in story:
    if getattr(_f, "_toc", None):
        _flow.append(CondPageBreak(4.2 * cm))
    _flow.append(_f)
story = _flow

B.build(OUT, story,
        cover_title="PROTOCOLO DE APLICACIÓN — MAX PIROL",
        cover_subtitle="Desecación pre-siembra · Soya 26/27 · Hacienda Cerro Alto")
print("OK ->", OUT, os.path.getsize(OUT), "bytes")
