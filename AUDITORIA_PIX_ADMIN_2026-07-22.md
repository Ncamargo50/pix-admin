# Auditoría Profesional — PIX Admin

**Fecha:** 2026-07-22
**Alcance:** Panel `pix-admin` (SPA vanilla JS + PWA) + 3 backends Python, código local y desplegado.
**Metodología:** 3 auditorías paralelas (seguridad, online-readiness, calidad/bugs) + verificación en vivo del sitio desplegado.
**Deployed:** https://pixadvisor.network/pix-admin/ (v3.3.0) — GitHub Pages del repo `Ncamargo50/pixadvisor-website`.
**Repo fuente:** `Ncamargo50/pix-admin` (rama `serro-alto-ambientes-v2`, con cambios sin commitear).

---

## Veredicto general

El frontend **ya está online y responde**. Pero NO está "al 100%": hay **3 problemas de bloqueo** que hay que resolver antes de poder promocionar la URL, y el sistema depende de la PC del dueño encendida para 3 de sus módulos.

| Área | Estado | Nota |
|---|---|---|
| Frontend online | 🟡 Vivo pero con scripts rotos | v3.3.0 sirve, pero 3 JS dan 404 |
| Sincronía fuente↔deploy | 🔴 Bifurcado | Local (v2.0) y deployed (v3.3.0) son código distinto |
| Seguridad | 🔴 Crítico | Login trivial + 3 backends sin auth |
| Backends | 🔴 Solo local | 4 servicios en localhost hardcodeado |
| PWA/offline | 🟡 Funciona con bugs | SW cachea APIs, íconos falsos |
| Calidad/bugs | 🟡 15 hallazgos | 3 de alto impacto (pérdida de datos) |

---

## 🔴 HALLAZGO ESTRUCTURAL #1 — El código está bifurcado (lo más urgente)

El deployed y el local **no son versiones de lo mismo**; son ramas de features distintas que nunca se reconciliaron:

- **Deployed v3.3.0** tiene: sincronización con Supabase Cloud (`pullCloudData`, `adminCloud`), reporte de cliente, pipeline completo. PERO su `index.html` referencia 3 scripts que **dan 404 en producción ahora mismo**:
  - `js/cloud-sync.js` → **404**
  - `js/client-report.js` → **404**
  - `js/gee-zones-engine.js` → **404**
- **Local (base v2.0)** tiene features que el deployed NO tiene: gestión de colaboradores, Cadastro AI (iframe field-delineation), zonas GEE vía localhost. Y le faltan las funciones cloud del deployed.

**Consecuencia:** en producción, la sincronía con la nube y el reporte de cliente **fallan en runtime** (los `<script>` no cargan → `adminCloud` no existe). No hay un único "código verdadero"; el copiado manual entre repos rompió la trazabilidad.

**Acción #1 (bloqueante):** decidir cuál base es la buena, reunificar en el repo `pix-admin`, y montar un GitHub Action que copie `pix-admin/` → `pixadvisor-website` en cada push (elimina el copiado manual y la bifurcación futura).

---

## 🔴 SEGURIDAD (crítico — bloquea "online full")

Si estos backends salen a internet tal cual, es un incidente de seguridad. Priorizado:

| # | Severidad | Hallazgo | Archivo | Fix |
|---|---|---|---|---|
| C-1 | CRÍTICO | `user-api.py` (:9105) sin auth: `GET /api/users` devuelve **passwordHash de todos**; CORS `*`; bind `0.0.0.0` | user-api.py:107-233,253 | Auth por token en cada endpoint, nunca serializar hash, bind 127.0.0.1, CORS restringido |
| C-2 | CRÍTICO | `gee-token-proxy.py` (:9101) acuña tokens de la **service account GEE** a cualquier origen (CORS `*`) | gee-token-proxy.py:54-67 | Secret compartido + CORS a origen del panel; no exponer token crudo |
| C-3 | CRÍTICO | Credenciales admin triviales hardcodeadas: usuario `pix` / clave `admin` (hashes de diccionario) + backdoor `pixmaster2026` | index.html:1625-1628; admin-app.js:172-179; user-api.py:38-39 | Eliminar defaults, forzar cambio en 1er arranque, borrar master_hash |
| A-1 | ALTO | Auth 100% client-side (`sessionStorage`), evadible con una línea en DevTools | index.html:1635-1707 | Auth real server-side con token firmado |
| A-2 | ALTO | Hashing SHA-256 (rápido, sin salt en backend) | user-api.py; admin-app.js:182 | PBKDF2/Argon2/bcrypt con salt |
| A-3 | ALTO | Sin Content-Security-Policy | index.html `<head>` | Añadir CSP restrictiva |
| A-4 | ALTO | `postMessage` listener sin validar `e.origin` | admin-app.js:2932 | Validar origin + registrar una sola vez |
| M-1/M-2 | MEDIO | XSS por `innerHTML` sin escapar en chat del agente y reporte de cliente | agent-admin.js:223; report-generator.js:517 | `escapeHtml()` antes de interpolar |
| M-4 | MEDIO | Path traversal vía `loteName` sin sanitizar | gee-backend.py:32,147 | Whitelist / regex `[A-Za-z0-9_-]+` |

---

## 🟡 ONLINE-READINESS (para que no dependa de tu PC)

### Dependencias localhost (mueren si la PC está apagada)

| URL | Módulo que rompe | Backend |
|---|---|---|
| `localhost:9105` | Gestión de colaboradores + sync credenciales con APK | user-api.py |
| `localhost:8765` | Cadastro AI / Field Delineation (iframe) | POC_FIELD_BOUNDARY (FastAPI) |
| `localhost:9104` | Zonas de Manejo "GEE REAL" | gee-backend.py |
| `localhost:9101` | Token GEE para cliente Earth Engine | gee-token-proxy.py |

### PWA / Service Worker
- **BUG:** el SW cachea las llamadas API (`localhost:*`) en modo cache-first → lista de colaboradores y estado de backends quedan **congelados** hasta el próximo bump de `BUILD_TS`.
- `cache.addAll` incluye CDNs cross-origin → si un CDN falla, **toda la instalación del SW falla**.
- Fallback a `index.html` para cualquier request same-origin fallido → sirve HTML con MIME incorrecto a `.js`/`.json`.
- `gee-zones-engine.js` y el worker no están en el precache.

### Rendimiento
- Peso real ~8.5 MB, de los cuales **7.8 MB son 4 copias del mismo PNG** (logo 1536×1024, 1.95 MB c/u). Los "íconos" 192/512 del manifest son ese mismo PNG gigante → fallan Lighthouse y el prompt de instalación.
- Sin minificación/bundling; 12 scripts secuenciales.
- Primera carga estimada: 3-6 s banda ancha, 15-30 s en 4G rural.
- **Quick win:** logo→WebP (~80 KB) + íconos reales (~20 KB) baja la primera carga de ~4.2 MB a ~1.5 MB.

### CDNs sin SRI
Leaflet, markercluster, SheetJS, Earth Engine — ninguno con `integrity=`. Vendorizar + SRI o al menos SRI.

### Backends — deployabilidad
- `user-api.py`: el más fácil de mover (Render/Fly), pero **NO debe salir sin auth**. Alternativa mejor: portar a Supabase (ya lo usás en pix-muestreo, free tier + keepalive ya montado).
- `gee-backend.py`: solo sirve GeoJSON pre-generados desde ruta local → publicarlos como archivos estáticos, no necesita servidor.
- `gee-token-proxy.py`: solo online con secret + CORS restringido.
- Field API (8765): la más pesada (YOLO/rasterio/GPU), pero la mejor preparada (ya tiene Dockerfile + variante Supabase). Cloud Run/Fly con 2-4 GB.

### Supabase
- pix-admin **no usa Supabase** en el código local; el deployed sí (via `cloud-sync.js`, que hoy da 404).
- Workflow `supabase-keepalive.yml` está **deshabilitado por inactividad** y sus últimas 3 corridas **fallaron** (aunque el endpoint responde 200 ahora — probable bug del workflow o proyecto que estuvo pausado). Revisar y reactivar.

---

## 🟡 CALIDAD / BUGS (los de mayor impacto)

| # | Severidad | Bug | Archivo | Fix |
|---|---|---|---|---|
| 1 | ALTO | Órdenes de servicio borradas **resucitan** tras refrescar (`saveState` hace put, nunca `_dbDelete`) | admin-app.js:4227,130 | `await _dbDelete('serviceOrders', id)` al borrar |
| 2 | ALTO | `fetch({timeout:N})` no existe → se ignora → **spinner infinito** si el API cuelga | admin-app.js:2958,3105; gee-zones-engine.js:164 | Usar `AbortSignal.timeout(N)` |
| 3 | ALTO | `localStorage.setItem` de OS sin try/catch → `QuotaExceededError` **aborta el guardado** en IndexedDB | admin-app.js:4036 | try/catch o eliminar el espejo |
| 4 | MEDIO | `shareServiceOrder` crashea si OS sin cliente (`order.client.nombre`) | admin-app.js:4248 | `order.client?.nombre` |
| 5 | MEDIO | `notify()` llama a `_showToast` inexistente → avisos tragados | admin-app.js:2944 | Delegar en `this.toast` |
| 6 | MEDIO | `_initFieldDelineation` puede registrar listener duplicado (carrera) | admin-app.js:301,2932 | Flag antes del await / handler idempotente |
| 7 | MEDIO | `_normalizeGrid` no verifica min/max (regla del proyecto) → capa degenerada/NaN silenciosa | zones-engine.js:408 | Loggear min/max + nº NaN, avisar si range≈0 |

**Lo que está BIEN (no tocar):** `kriging.js` (pivoteo parcial, fallback IDW, guardas NaN), mapas Leaflet (guarda contra reinicialización), k-means (reinicia clusters vacíos), SW con `skipWaiting`+`clients.claim`.

---

## PLAN DE MEJORAS — "al 100% y online full"

### FASE 0 — Desbloqueo inmediato (1 día)
1. **Reunificar la base de código** (Hallazgo #1): elegir la buena, resolver los 404 de `cloud-sync.js`/`client-report.js`/`gee-zones-engine.js` en producción.
2. **Fix de los 3 bugs ALTO** (OS resucitan, spinner infinito, quota). Son de bajo esfuerzo y alto impacto.
3. **Rotar credenciales:** eliminar `pix/admin` y el backdoor `pixmaster2026`.

### FASE 1 — Seguridad para exponer a internet (2-3 días)
4. Auth real server-side (token firmado) + PBKDF2/Argon2.
5. Los 3 backends: auth por token + CORS restringido a `pixadvisor.network` + bind correcto + leer `$PORT`.
6. CSP + escape XSS (M-1, M-2) + validar `postMessage`.

### FASE 2 — Independencia de la PC local (3-5 días)
7. Config por entorno (`window.PIX_CONFIG`) en vez de `localhost` hardcodeado.
8. Portar `user-api` → Supabase (tabla users + RLS), coherente con pix-muestreo.
9. `gee-backend` → publicar GeoJSON como estáticos.
10. Field API → Cloud Run/Fly (2-4 GB) con service account GEE.

### FASE 3 — Pulido PWA + performance (1-2 días)
11. Fix SW: excluir APIs del cache, `Promise.allSettled` para CDNs, fallback index.html solo en navegaciones, precachear worker.
12. Íconos PWA reales + logo WebP + `defer` en xlsx + SRI en CDNs.
13. GitHub Action de deploy automático `pix-admin` → website (evita bifurcación futura).
14. Reactivar y arreglar `supabase-keepalive.yml`.

### FASE 4 — Datos en la nube (opcional, escala)
15. Migrar clientes/análisis/colaboradores de IndexedDB → Supabase para multi-dispositivo + backup.
