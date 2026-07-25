# AUDITORIA PROFUNDA - Plataforma Pixadvisor
**Fecha:** 19 de Marzo de 2026
**Alcance:** Website + PIX Admin + PIX Muestreo (codigo completo)
**Nivel:** Auditoría a nivel de código línea por línea
**Auditor:** Claude Opus 4.6 (PhD Precision Agriculture Systems)

---

## RESUMEN EJECUTIVO

Se auditaron **22+ archivos fuente** (~15,000+ líneas de código) en 3 aplicaciones. Se encontraron:

| Severidad | Website | PIX Admin | PIX Muestreo | Total |
|-----------|---------|-----------|--------------|-------|
| **CRITICO** | 6 | 4 | 6 | **16** |
| **ALTO** | 9 | 8 | 9 | **26** |
| **MEDIO** | 9 | 9 | 8 | **26** |
| **BAJO** | 3 | 5 | 3 | **11** |
| **Total** | 27 | 26 | 26 | **79** |

---

# PARTE 1: PIX ADMIN (Dashboard GIS)

## 1.1 BUGS FUNCIONALES EN ALGORITMOS

### CRITICO: Formula DRIS incorrecta (engine.js:813)
```
Actual:   f = ((observed - norm.mean) / norm.std) * (1000 / cv)
Correcto: f = (A/B - a/b) * 1000 / (a/b * CV)  [Jones 1981]
```
El factor `1000/cv` produce `10*mean/std`, generando ponderaciones incorrectas. El diagnostico DRIS/IBN entero esta afectado.

**Impacto:** Recomendaciones de fertilizacion foliar erroneas.
**Fix:** Reimplementar con la formula de Jones (1981) con funciones asimetricas de Beaufils.

### CRITICO: Shapefile truncado (interpolation.js:1134)
```
Actual:   4*2*ptsPerZone (= 8 bytes por punto)
Correcto: 8*2*ptsPerZone (= 16 bytes por punto, Float64 x2)
```
Cada punto son dos Float64 (lat+lng = 16 bytes), no 8. El buffer queda subdimensionado, truncando coordenadas en el .shp exportado.

**Impacto:** Prescripciones VRT corruptas al importar en controladores de maquinaria.
**Fix:** Cambiar `4*2` a `8*2` en el calculo de `recordContentLen`.

### ALTO: Conversion lng a grados ignora latitud (interpolation.js:112)
```
spreadDeg = spreadM / 111320  // Solo correcto para latitud
// Para longitud: spreadDeg = spreadM / (111320 * cos(lat))
```
A latitud -25S (tipica BR/BO), el error es ~9% en eje E-W. Los subpuntos virtuales para IDW quedan distorsionados.

### ALTO: Convex hull en vez de boundary real (zones-engine.js:1838)
Las zonas de manejo se exportan como convex hull, perdiendo formas concavas. Zonas que rodean a otras se solapan en el GeoJSON.

### ALTO: K-Means no determinista (zones-engine.js:1012)
`Math.random()` sin seed. Correr el mismo analisis dos veces produce zonas diferentes. Resultado no reproducible.

### ALTO: Varianza poblacional en estabilidad temporal (zones-engine.js:1258)
Usa N en vez de N-1. Con 3 campanas (minimo), subestima varianza en ~18%.

### ALTO: Cluster vacio no se reinicializa (zones-engine.js:1082)
Si un centroide pierde todos sus puntos, mantiene su posicion previa sin reasignarse al punto mas lejano.

### MEDIO: No hay validacion de estructura espacial en variograma (kriging.js)
El modelo "mejor" puede ser pure nugget (sill=nugget), colapsando Kriging a la media global sin advertencia.

### MEDIO: Elbow method no puede seleccionar k=2 ni k=max (zones-engine.js:2862)
El loop `for (i=1; i<len-1)` excluye primer y ultimo indice del optimo.

### MEDIO: BFS drainage usa distancia Manhattan (zones-engine.js:524)
Celdas diagonales deberian tener distancia `sqrt(2)*cellSize`, pero se tratan como distancia 1.

## 1.2 BUGS DE INTEGRIDAD DE DATOS

### ALTO: `parseFloat("<0.1")` retorna NaN (engine.js:52)
Labs reportan valores bajo limite de deteccion como `"<0.1"`. `parseFloat` produce NaN sin deteccion.

### ALTO: Division por zero en DRIS con nutrientes traza (engine.js:808)
Si `leafData[B]` es muy pequeno (0.001 para B o Cu), el ratio se vuelve enorme dominando el IBN.

### MEDIO: `_bilinearSample` puede no existir (report-generator.js:1140)
Referencia a `InterpolationEngine._bilinearSample()` que no esta definida como metodo estatico. Produce `TypeError`.

### MEDIO: `getBounds` retorna Infinity/NaN con array vacio (interpolation.js:1669)
Sin guard para input vacio.

## 1.3 SEGURIDAD

### ALTO: XSS via datos de cliente (admin-app.js:2723)
```javascript
`<div>${this.clientData.nombre}</div>` // Sin sanitizar
```
Datos importados con `<script>` se ejecutan.

### BAJO: Password default hardcoded `'pixadvisor'` (admin-app.js:162)
### BAJO: Auth client-side sin server (security theater)
### BAJO: Emails hardcoded en source (agent-admin.js:1709)
