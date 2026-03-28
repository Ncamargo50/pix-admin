# PIX Admin v3.0 PRO MAX — Plan de Reestructuración Total

## Objetivo
Ventanas dedicadas full-screen por tipo de trabajo, agentes especializados por módulo, motor de zonas de manejo por cultivo con índices temporales (mínimo 3 campañas), planialtimetría y flujo de agua.

## Arquitectura de Motores v3

### 1. `zones-engine.js` (~1000 líneas) — Motor de Zonas de Manejo PRO v3
- **K-Means++ clustering** (Lloyd's algorithm iterativo) — metodología DataFarm
- **Multi-variable**: combinar capas (suelo + índices vegetación + altimetría + temporal)
- **Z-score normalization** para multi-variable con pesos configurables
- **Perfiles por cultivo** con índices recomendados por etapa fenológica:
  - Caña: NDVI vegetativo, NDRE maduración, EVI macollaje
  - Soja: NDVI R5-R6, NDRE R3, SAVI emergencia
  - Maíz: NDVI V8-VT, NDRE V6, EVI V12
  - Sorgo, girasol, tomate, papa, etc.
- **Estabilidad temporal**: coeficiente de estabilidad multi-campaña (mín 3 años)
  - Media, desvío, CV por píxel a través de campañas
  - Clasificación: estable (<15%), moderado (15-30%), inestable (>30%)
- **Topographic Wetness Index (TWI)**: flujo de agua desde planialtimetría
  - Horn method para slope, D8 flow direction & accumulation
  - Clasificación: cresta, ladera, planicie, bajo/acumulación
  - Líneas de flujo de agua renderizadas en mapa
- **Clasificación de ambientes**: Alto/Medio/Bajo potencial productivo
- **Estadísticas por zona**: área, media, CV, percentiles, potencial
- **Exportación**: GeoJSON, CSV, SHP, PDF

### 2. `sampling-engine.js` (~500 líneas) — Motor de Puntos de Muestreo
- **Grid regular** dentro de perímetro con buffer de borde
- **Muestreo estratificado** por zona de manejo
- **Centroide de zona** (representativo)
- **Random dentro de zona** con PRNG reproducible
- **Submuestreo compuesto**: zigzag, cruz, diamante, circular
- **Densidad configurable** (puntos/ha)
- **Validación cobertura**: distancia mínima/media, score 0-100
- **Exportar**: GPX, KML, GeoJSON, CSV
- **Visualización** en mapa con labels por zona y colores

### 3. Reestructuración HTML — Vistas Full-Screen Dedicadas

Cada vista GIS con layout: **mapa pantalla completa + panel lateral de controles**

| Vista | Layout | Contenido Panel |
|---|---|---|
| `management-zones` | `view-fullmap` | Wizard 5 pasos: Capas → Cultivo → Temporal → DEM → Generar |
| `sampling-points` | `view-fullmap` | Método + Config + Compuesto + Exportar |
| `nutrient-maps` | `view` (existente) | Nutriente/método/resolución |
| `relation-maps` | `view` (existente) | Relación Ca/Mg/K |
| `prescription` | `view` (existente) | Prescripción VRT |
| `engine-*` | `view` (existente) | IDW/Kriging/Variograma/Validación |

### 4. Layout Full-Screen CSS
```css
.view-fullmap { grid-template-columns: 1fr 400px; height: calc(100vh - 56px); }
.fullmap-map { height: 100%; }
.fullmap-panel { overflow-y: auto; background: var(--dark-2); }
```

### 5. Sidebar — Nuevas entradas
- Bajo "Mapas GIS": "Puntos de Muestreo" agregado
- "Zonas de Manejo" marcado con badge v3

### 6. admin-app.js — Controladores nuevos
- Wizard multi-paso para management-zones (5 pasos)
- Vista sampling-points con generación y exportación
- Integración de capas multi-variable con pesos
- Toggle de capas en mapa (zonas, labels, estabilidad, TWI, puntos)
- Generación fallback si ZonesEngine no disponible

## Estado de Implementación
- [x] `zones-engine.js` creado
- [x] `sampling-engine.js` creado
- [x] CSS actualizado con layout fullmap y componentes v3
- [x] HTML reestructurado con vistas full-screen y wizard
- [x] Sidebar actualizado con nueva entrada
- [x] admin-app.js actualizado con controladores v3
- [x] Script tags agregados al HTML
