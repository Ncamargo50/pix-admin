# PIX Scout — conectar el backend (bloqueante 2 del plan)

Estado: **el código de la app ya está listo y probado**. Falta pegar dos credenciales.

Probado end-to-end el 2026-07-24 contra un servidor que imita a PostgREST con estas mismas
policies: 2 validaciones encoladas → sincronizadas → 0 en cola; reenvío del mismo id = no-op;
lectura con la clave anónima = HTTP 401; campo inexistente = rebota sin perder el dato.

---

## Los 3 pasos

### 1. Crear las tablas
En el proyecto Supabase → **SQL Editor** → pegar y ejecutar `001_scout_validaciones.sql`.

Crea `scout_validaciones` (32 columnas, exactamente las que manda la app), los índices, las
policies de RLS y la vista de análisis `scout_validaciones_geo`.

### 2. Copiar las credenciales
En Supabase → **Project Settings → API**, copiar:
- **Project URL** → va en `SUPABASE_URL`
- **anon / public key** → va en `SUPABASE_ANON_KEY`

Pegarlas en `PIX_SCOUT/app/js/config.js` (líneas 16-17).

### 3. Recompilar el APK
```bash
cd PIX_SCOUT/pix-scout-apk && ./gradlew :app:assembleRelease
```
Antes de compilar, copiar los assets y **subir la versión del service worker** en `app/sw.js`
(si no, el SW sirve la versión vieja y las credenciales nuevas no llegan nunca).

---

## Por qué el esquema es append-only (no es un detalle)

**La `anon key` viaja dentro del APK.** Cualquiera que instale la app la tiene: es pública por
construcción. Por eso las policies dan a `anon` **solo INSERT**:

| Operación | anon | Motivo |
|---|---|---|
| INSERT | ✅ | es el registro del técnico saliendo del campo |
| SELECT | ❌ | con la clave pública nadie puede volcarse la tabla entera |
| UPDATE | ❌ | una validación de campo es un dato observado: inmutable |
| DELETE | ❌ | — |

Para **leer** los datos (el pipeline, los informes, la campaña de validación) se usa la
`service_role key` desde el servidor, nunca desde la app.

Esto evita repetir el defecto ya detectado en pix-muestreo, donde `anon` podía leer
`password_hash` y las policies estaban con `using (true)`.

### Consecuencia en el cliente
`store.js` manda `Prefer: resolution=ignore-duplicates` (antes era `merge-duplicates`).
Con la tabla sin permiso de UPDATE, un `merge` daría **403 en todo reintento** y la cola no
drenaría nunca. Además `ignore-duplicates` es lo semánticamente correcto: reenviar una
validación tras un timeout debe ser no-op, no sobrescribir.

---

## Cómo saber si algo falla

`store.js` ahora distingue en consola los dos casos, que antes se veían iguales:

```
sync <id> HTTP 400 [PERMANENTE, no se arregla solo] {"code":"PGRST204", ...}
sync <id> HTTP 503 [reintentable] ...
```

- **PERMANENTE** (4xx salvo 429) = esquema o permisos. Reintentar no sirve; hay que arreglar
  la tabla o la policy. El dato **no se pierde**: queda en la cola local.
- **reintentable** = red o servidor caído. Drena solo cuando vuelve la señal.

El caso que más importa es `PGRST204`: significa que la app manda una clave que no existe como
columna, y PostgREST rechaza **el POST entero**. Si alguna vez se agrega un campo nuevo al
registro de validación, hay que agregar su columna acá o la cola se llena en silencio.

Verificación rápida de que app y esquema siguen calzando:
```bash
python -c "
import re
app=open('PIX_SCOUT/app/js/app.js',encoding='utf-8').read()
sql=open('PIX_SCOUT/backend/001_scout_validaciones.sql',encoding='utf-8').read()
cuerpo=sql[sql.index('create table'):sql.index(');')]
cols={ (m.group(1) or m.group(2)) for ln in cuerpo.splitlines()[1:] if (m:=re.match(r'\"([^\"]+)\"|^([a-z_][a-z0-9_]*)', ln.strip())) and not ln.strip().startswith('--') }
print('columnas:', len(cols))
"
```

---

## Lo que sigue faltando (no lo destraba este paso)

- **`supera_umbral` sigue siendo opinión del técnico**, no un cálculo: la columna `nde` guarda
  `under|at|over` apretado a mano. Los 26 umbrales MIP están como prosa. Es el bloqueante 4.
- **`FOCOS_ENDPOINT` sigue sin cablearse**: la app todavía carga el GeoJSON empaquetado, así que
  cambiar de campo exige recompilar. Es el bloqueante 7.
- La foto se guarda como base64 en una columna. Funciona, pero conviene mover a Supabase Storage
  pasadas unas ~2.000 validaciones.
