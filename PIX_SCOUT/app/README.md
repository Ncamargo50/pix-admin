# PIX Scout — App (PWA instalable → APK Android)

App de campo de Pixadvisor para **validar anomalías satelitales**: navegación GPS a los focos que
detecta el pipeline de anomalías, **diagnóstico diferencial defendible** (enfermedad / plaga /
carencia / abiótico) con confianza honesta y umbral MIP, y **captura offline-first** con foto
georreferenciada + cola de sincronización.

Misma arquitectura que **PIX Muestreo** (PWA en WebView), lista para envolver en Android.

## Estructura
```
app/
  index.html               shell de la app (tabs Focos / Banco / Historial)
  manifest.webmanifest      PWA instalable (standalone, portrait)
  sw.js                     service worker — offline-first (cache-first del shell + datos)
  css/app.css               diseño de campo (tokens, modo Sol/alto contraste, targets grandes)
  js/
    config.js               config runtime (Supabase URL/key, endpoint de focos, GPS)
    data.js                 AUTO-GENERADO: banco 7 cultivos + clave (offline). No editar a mano.
    geo.js                  GPS real: watchPosition, accuracy, haversine (distancia), bearing (rumbo), brújula
    store.js                IndexedDB: validaciones + cola de sync no destructiva (anti-pérdida)
    diagnosis.js            motor de la clave (biótico/abiótico/nutricional + confianza + 7 causas abióticas)
    app.js                  router + vistas + navegación GPS + cámara + guardado
  icons/                    icono de marca (SVG normal + maskable)
  build_data.py             regenera js/data.js desde ../data/*.json
```

## Regenerar el banco (tras editar las fichas)
```
cd app && python build_data.py
```
Lee `../data/{soya,trigo,maiz,sorgo,girasol,cana,pastura}.json` + `clave_dicotomica.json`
y reescribe `js/data.js`. **Al cambiar cualquier asset, subir `CACHE` en `sw.js`** (p.ej. `pixscout-v2`)
para forzar la actualización en los dispositivos.

## Correr local
```
python -m http.server 9301 --directory app
```
Abrir `http://localhost:9301`. GPS y cámara requieren **contexto seguro** (https o localhost) y permisos.

## Qué funciona (verificado)
- **Offline-first**: service worker cachea el shell + datos → abre sin señal. IndexedDB guarda las
  validaciones localmente; el sync es diferido y **no destructivo** (solo marca `synced` tras confirmación).
- **GPS real**: brújula que apunta al foco (rumbo relativo a la orientación del teléfono), distancia
  en vivo (haversine), precisión visible, margen de proximidad configurable (`PROXIMITY_M`).
- **Motor de diagnóstico**: paso Contexto (estadio + rango de hospederos + temporalidad) → patrón →
  signo → rama; distingue biótico/abiótico; devuelve **hipótesis presuntiva** con confianza y escala
  a laboratorio ante duda. Nunca fuerza un único resultado.
- **Validación**: para plagas compara el conteo contra el **umbral MIP** (nivel de acción, color-coded,
  MIP-primero); severidad, % incidencia, coincidencia con satélite, **foto georreferenciada obligatoria**
  (cámara nativa con fallback a selector de archivo).
- **Historial** con estado pendiente/sincronizado + botón de sync manual.
- **Modo Sol** (alto contraste), targets ≥48–56 px, acción primaria al alcance del pulgar, tema claro/oscuro.

## Conectar el backend (opcional)
En `js/config.js`:
- `SUPABASE_URL` + `SUPABASE_ANON_KEY` + `VALIDACIONES_TABLE` → habilita el POST REST de validaciones
  (tabla sugerida `scout_validaciones`). Sin esto, todo queda en cola local segura.
- `FOCOS_ENDPOINT` → GeoJSON de focos del pipeline de anomalías en la nube (repo
  `pixadvisor-monitoreo-trigo`). Sin esto, usa los focos de ejemplo bundleados.

## Empaquetar como APK Android (patrón PIX Muestreo)
La PWA va como assets de un WebView, igual que `pix-muestreo-apk`:
1. Copiar el contenido de `app/` a `app/src/main/assets/` del proyecto Android.
2. `MainActivity` carga `file:///android_asset/index.html` en un `WebView` con
   `javaScriptEnabled=true`, `domStorageEnabled=true`, `databaseEnabled=true` (IndexedDB),
   `geolocationEnabled=true` y `setGeolocationDatabasePath(...)`.
3. Permisos en `AndroidManifest.xml`: `INTERNET`, `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`,
   `CAMERA`. Manejar `onGeolocationPermissionsShowPrompt` y `onPermissionRequest` (cámara) en el `WebChromeClient`.
4. Ícono de launcher: exportar `icons/icon-maskable.svg` a los mipmaps PNG de Android.
5. La cámara usa `getUserMedia`; asegurar `WebChromeClient.onPermissionRequest` que conceda
   `RESOURCE_VIDEO_CAPTURE`. Alternativa universal: el `<input type=file capture=environment>` (ya incluido como fallback).

> Alternativa sin código nativo: PWABuilder / Bubblewrap (TWA) empaqueta la PWA hospedada en gh-pages
> directamente a APK/AAB, reutilizando el manifest y el service worker de este mismo directorio.
