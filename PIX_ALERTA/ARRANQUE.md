# Arranque — lo que sólo podés hacer vos

Todo lo demás está hecho y probado. Lo que queda son **credenciales y una decisión**, y
no las toco por diseño: si me equivoco moviendo una clave, el error no se deshace.

Verificá en cualquier momento en qué estás parado:

```bash
python scripts/verificar_setup.py
```

Te dice, eslabón por eslabón, si el cron entregaría si corriera ahora.

---

## 1. Los tres secretos del repositorio · 5 minutos

Son **los mismos** que ya tenés funcionando en `pixadvisor-monitoreo-trigo`. Desde la
carpeta del repo nuevo:

```bash
gh secret set GEE_SA_JSON < "C:/ruta/a/tu/cuenta-de-servicio.json"
```

```bash
gh secret set WHATSAPP_PHONE --body "554399819554"
```

```bash
gh secret set CALLMEBOT_APIKEY --body "TU_CLAVE"
```

> El número de WhatsApp que funciona en CallMeBot tiene **un 9 menos** que el que usás
> normalmente. Está así en el repo de trigo y ahí anda.

También podés cargarlos desde la web: Settings → Secrets and variables → Actions.

---

## 2. Supabase, para que vuelva lo que registra el técnico · 15 minutos

Sin esto la app funciona igual, pero las validaciones se acumulan en el teléfono y no
llegan a ningún lado — o sea, no hay con qué medir el sistema.

1. Crear el proyecto en supabase.com (o usar el que ya tenés del panel).
2. SQL Editor → pegar y ejecutar `PIX_SCOUT/backend/001_scout_validaciones.sql`.
3. Settings → API Keys → copiar **Project URL** y **Publishable key**
   (`sb_publishable_...`; en proyectos viejos se llamaba **anon key** y
   empezaba con `eyJ`). Los dos formatos funcionan.
4. Pegarlas en `PIX_SCOUT/app/js/config.js` (líneas 22-23).
5. Recompilar el APK: `cd PIX_SCOUT/pix-scout-apk && ./gradlew :app:assembleRelease`

El esquema es **append-only**: la clave anónima puede insertar y nada más, porque viaja
dentro del APK y es pública. Está explicado en `PIX_SCOUT/backend/README.md`.

---

## 3. Cómo llega el mapa al técnico — RESUELTO

El canal es **WhatsApp**, y con eso no hace falta ninguna URL pública ni exponer
coordenadas de campos de clientes en internet.

1. Bajás el GeoJSON de la corrida desde el repo: `entregas/<CLIENTE>/ultimo/`
2. Se lo mandás al cliente por WhatsApp.
3. El técnico abre la app → **Focos → “Abrir mapa”** → elige el archivo.

La app le muestra qué trae antes de reemplazar nada (campo, fecha de escena, cuántos
lotes) y **le avisa si el mapa es más viejo** que el que ya tiene cargado. El mapa
importado queda guardado: sobrevive a cerrar la app y funciona sin señal.

Necesita el **APK v1.0.10** o posterior.

> `FOCOS_ENDPOINT` sigue existiendo por si algún día conviene la descarga automática,
> pero **no hace falta para operar**. El chequeo lo marca como pendiente; con el flujo de
> WhatsApp podés ignorarlo.

---

## 4. Probar · 2 minutos

```bash
gh workflow run pixadvisor-monitor -f cliente=HDS -f hasta=2026-04-30
```

```bash
gh run watch
```

Si sale verde y aparecen archivos en `entregas/HDS/`, la máquina está andando.

> ⚠️ Usá una fecha **dentro de la campaña declarada**. Fuera de campaña el motor hace
> no-op a propósito: en madurez el dosel se seca y senesce, que es la misma firma que
> busca el criterio, y no puede distinguir cosecha de deterioro.

---

## Lo que no arregla ninguna de estas cuatro cosas

- **La planilla de siembra.** Mientras no exista, la cohorte se estima por fenología y
  el entregable lo declara como estimada. Es el bloqueante más largo del plan.
- **Un técnico caminando un lote.** Media jornada con el trigo que queda alcanza para
  saber qué se rompe en la mano, y es lo más barato que podés hacer para bajar el riesgo.

Esas dos deciden si el producto **sirve**. Las cuatro de arriba sólo deciden si
**funciona**.
