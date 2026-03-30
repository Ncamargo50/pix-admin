# AUDITORIA TECNICA PROFESIONAL — PIX Monitor v1.0
## Plataforma de Monitoreo Satelital de Cultivos
### Fecha: 2026-03-30 | Auditor: Claude Opus 4.6 (1M context)
### Alcance: Backend (Python/GEE) + Frontend (HTML/JS) + Infraestructura

---

## RESUMEN EJECUTIVO

PIX Monitor es una plataforma de monitoreo satelital de cultivos que utiliza Sentinel-2 y Google Earth Engine para detectar anomalias en tiempo cuasi-real. La auditoria revela que el sistema tiene una **arquitectura solida** y un **motor GEE funcional**, pero presenta **issues criticos** que deben resolverse antes de ofrecerlo como servicio comercial a productores reales.

### Estado de Produccion: NO LISTO (requiere 13 fixes criticos/altos)

| Severidad | Backend | Frontend | Total |
|-----------|---------|----------|-------|
| CRITICO   | 2       | 4        | 6     |
| ALTO      | 5       | 5        | 10    |
| MEDIO     | 6       | 8        | 14    |
| Total     | 13      | 17       | 30    |

---

## PARTE 1: AUDITORIA DEL MOTOR GEE (Backend)

### CRITICOS

**C1. Indice BSI no computado en GEE**
- BSI esta declarado en 5 configuraciones de cultivo (brotacion, emergencia) pero NO se calcula en `compute_indices()`
- Impacto: Deteccion de malezas falla en etapas tempranas
- Fix: Agregar `bsi = (b11+b4-b8-b2)/(b11+b4+b8+b2)` al motor

**C2. Logica de mascara de nubes confusa**
- `mask_clouds()` y `is_cloud_free()` tienen logica conflictiva
- `mask_clouds` remueve nubes ANTES de que `is_cloud_free` las cuente
- Resultado: Imagenes nubladas pasan como "cloud-free"
- Fix: Unificar la logica — usar solo `is_cloud_free` para filtrar

### ALTOS

**A1. Filtro cloud_pct == 0 imposible**
- Comparacion exacta con float 0.0 casi nunca se cumple
- El filtro estricto es codigo muerto — siempre cae al fallback <5%
- Fix: Usar `lte(0.01)` en vez de `eq(0)`

**A2. Z-score con baseline stddev muy baja**
- Threshold de 0.01 muy debil — genera falsos positivos
- Fix: Subir a 0.05 minimo, o saltar anomalia si baseline demasiado estable

**A3. Baseline vacia para campos nuevos**
- Sin fallback cuando no hay 2 anos de historia
- GEE retorna NaN/None, Z-score falla silenciosamente
- Fix: Verificar `baseline_col.size() >= 10` antes de procesar

**A4. Umbrales de malezas no validados a 10m**
- stdDev > 0.10 puede disparar en bordes de campo (mixels)
- P90 > threshold puede confundir cultivo emergente con maleza
- Fix: Subir umbrales, agregar buffer de borde

**A5. Sin timeout en llamadas GEE getInfo()**
- Cada getInfo() puede colgar indefinidamente
- HTTP request timeout pero GEE sigue procesando
- Fix: Wrapper con ThreadPoolExecutor + timeout 30s

### MEDIOS

- M1: Growth rate pastura con minimo arbitrario 5 dias
- M2: Biomasa clampea NDVI, enmascara degradacion
- M3: PRI_proxy usa .max() incorrecto
- M4: JSON DB no es thread-safe (race conditions)
- M5: Harvest detection — threshold de dias deberia ser por cultivo
- M6: KMZ boundary extraction sin validacion de formato

---

## PARTE 2: AUDITORIA DEL FRONTEND

### CRITICOS

**C3. Sin upload de archivos GeoJSON/KML**
- El texto dice "subir archivo" pero NO existe input type=file
- Unica opcion: pegar texto JSON manualmente — no viable para productores
- Fix: Agregar file input + parser GeoJSON/KML

**C4. Sin loading spinner para chequeos GEE (30-60s)**
- UI parece congelada durante procesamiento
- Sin indicacion de progreso ni opcion de cancelar
- Fix: Overlay de carga con mensaje de progreso

**C5. Hash de clave maestra expuesto en source code**
- `MASTER_HASH = 'ac201...'` visible en View Source del navegador
- Cualquiera puede ver el hash e intentar romperlo
- Fix: Remover del frontend, usar auth server-side

**C6. Sin edicion ni eliminacion de campos/clientes**
- Una vez creado, no se puede corregir error
- No hay forma de eliminar datos de prueba
- Fix: Agregar botones edit/delete con confirmacion

### ALTOS

- A6: Sin menu hamburguesa en mobile (<900px sidebar desaparece)
- A7: apiGet/apiPost sin timeout ni manejo de errores HTTP
- A8: Sin reportes historicos (solo genera actual)
- A9: Sin enlaces de descarga de PDF/KMZ generados
- A10: Serie temporal solo tabla, sin grafico visual

### MEDIOS

- M7: Alertas sin interpretacion agronomica (solo Z-score numerico)
- M8: Metricas pastura solo en toast, no en panel permanente
- M9: Crop grid ilegible en celular (3 columnas en 375px)
- M10: user-scalable=no deshabilitado (mala accesibilidad)
- M11: Sin panel de configuracion (intervalos, umbrales)
- M12: Sesion infinita sin expiracion
- M13: Sin RBAC (todos los usuarios tienen mismo acceso)
- M14: Sin log de auditoria (quien hizo que)

---

## PARTE 3: MONITOREO REAL CADA 7 DIAS

### Estado actual: SOLO MANUAL

El sistema actual NO tiene scheduler automatico. El monitoreo cada 7 dias depende de que el administrador haga click manualmente en "Verificar" para cada lote.

### Que falta para monitoreo automatico real:

1. **Scheduler**: background thread con `schedule` o `APScheduler`
2. **Cola de procesamiento**: para manejar 50+ lotes sin bloquear
3. **Retry logic**: reintentar si GEE falla o hay nubes
4. **Notificaciones**: alertar al admin si el check fallo
5. **Dashboard de estado**: ver cuales lotes fueron chequeados y cuales no

### Viabilidad tecnica con GEE:

- Sentinel-2 tiene revisita de **5 dias** — compatible con ciclo de 7 dias
- GEE quota gratis: ~1000 computos/dia — suficiente para ~100 lotes
- Tiempo estimado por lote: 20-40 segundos (getInfo calls)
- Para 50 lotes: ~15-30 minutos de procesamiento total

**CONCLUSION: Es VIABLE monitorear cada 7 dias con GEE free tier para hasta 100 lotes.**

---

## PARTE 4: APLICABILIDAD REAL COMO SERVICIO

### Propuesta de valor para el productor

| Beneficio | Detalle | Valor |
|-----------|---------|-------|
| Deteccion temprana anomalias | Z-score vs baseline 2 anos | Prevenir perdidas 5-15% |
| Alerta de malezas | Heterogeneidad NDVI en emergencia | Herbicida oportuno |
| Monitoreo pastura | Biomasa + carga animal | Optimizar pastoreo |
| Cosecha automatica | NDVI < 0.15 pausa monitoreo | Ahorro operativo |
| Reporte PDF/KMZ | Waypoints para Avenza Maps | Navegacion a campo |
| WhatsApp | Informe semanal automatico | Comunicacion directa |

### Limitaciones honestas

1. **Resolucion 10m**: No detecta malezas individuales, solo parches >100m2
2. **Nubes**: En temporada lluviosa, puede pasar 2-3 semanas sin imagen
3. **Biomasa pastura**: R2=0.74, error ±487 kg/ha — orientativo, no exacto
4. **No reemplaza visita de campo**: Complementa, no sustituye al tecnico

### Diferenciadores vs competencia

| Feature | PIX Monitor | DataFarm | Taranis |
|---------|-------------|----------|---------|
| Costo | Bajo (GEE gratis) | Alto (suscripcion) | Muy alto |
| Indices | 21 (Israel 2025+) | 3-5 basicos | Propietarios |
| Pastura biomasa | Si (calibrado Brachiaria) | No | No |
| Malezas satelite | Si (heterogeneidad) | No | Si (avion 0.3mm) |
| PDF georeferenciado | Si (Avenza Maps) | Si | Si |
| WhatsApp | Si (automatico) | No | No |
| Auto-cosecha | Si | No | No |

---

## PARTE 5: PLAN DE CORRECCION

### Inmediato (antes de primer cliente)

| # | Fix | Esfuerzo |
|---|-----|----------|
| 1 | Agregar BSI al motor GEE | 10 min |
| 2 | Unificar logica cloud mask | 30 min |
| 3 | Cambiar cloud_pct eq(0) a lte(0.01) | 5 min |
| 4 | Agregar file upload GeoJSON/KML | 1 hora |
| 5 | Loading spinner para chequeos | 30 min |
| 6 | Edit/delete campos y clientes | 1 hora |
| 7 | Remover master hash del frontend | 15 min |
| 8 | Timeout en GEE getInfo() | 30 min |
| 9 | Baseline check minimo 10 imagenes | 15 min |
| 10 | Subir umbrales malezas (menos falsos positivos) | 15 min |

### Corto plazo (primera semana)

| # | Mejora | Esfuerzo |
|---|-------|----------|
| 11 | Scheduler automatico 7 dias | 2 horas |
| 12 | Menu hamburguesa mobile | 1 hora |
| 13 | Grafico serie temporal (Chart.js) | 1 hora |
| 14 | Interpretacion agronomica de alertas | 1 hora |
| 15 | Download links para PDF/KMZ | 30 min |

### Pre-lanzamiento (dos semanas)

| # | Feature | Esfuerzo |
|---|---------|----------|
| 16 | SQLite en vez de JSON DB | 3 horas |
| 17 | Historial de reportes | 1 hora |
| 18 | Panel de configuracion | 2 horas |
| 19 | Log de auditoria | 1 hora |
| 20 | Validacion ground-truth malezas | Trabajo de campo |

---

## PARTE 6: CONCLUSION

PIX Monitor tiene el **potencial de ser un servicio diferenciado** en el mercado de agricultura de precision boliviano/brasileño:

- **Motor GEE potente** con 21 indices especificos por cultivo y etapa
- **7 cultivos** incluyendo pastura con biomasa y carga animal
- **Deteccion automatica** de cosecha, nubes, malezas
- **Integracion WhatsApp** para comunicacion directa con el productor
- **PDF + KMZ** para navegacion con Avenza Maps

Sin embargo, requiere **13 fixes criticos/altos** antes de ser confiable para productores reales. La arquitectura es correcta pero la implementacion tiene gaps en cloud masking, error handling, y UX que generarian alertas falsas y frustracion del usuario.

**Recomendacion**: Invertir 2-3 dias de desarrollo enfocado en los 10 fixes inmediatos, luego hacer una prueba piloto con 2-3 productores antes del lanzamiento comercial.

---

*Auditoria realizada con: Claude Opus 4.6 (1M context) | Basado en revision de 3000+ lineas de codigo | Referencias: Nature 2024, EMBRAPA, Springer, MDPI, Volcani Center, Zhang et al. Agronomy 2024*
