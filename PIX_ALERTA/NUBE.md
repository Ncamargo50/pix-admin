# La máquina en la nube

Cómo queda funcionando solo, con tu PC apagada. Tu trabajo es **dar de alta el cliente**;
después la máquina busca las imágenes, procesa, emite el informe y te avisa.

---

## Lo que hace la máquina, sola

Todos los días a las 11:20 UTC (~07:20 hora local) GitHub Actions:

1. Recorre **todos los clientes activos**.
2. Para cada uno, busca escenas Sentinel-2 nuevas y calcula el ranking de lotes.
3. Emite **informe PDF**, **GeoJSON para la app** y CSV del ranking.
4. Los deja en `entregas/<CLIENTE>/<fecha>/` y copia la última a `entregas/<CLIENTE>/ultimo/`.
5. Te avisa por WhatsApp **sólo si hay algo que mirar**.

Si un cliente falla, los demás reciben su informe igual y el fallo se reporta. Si la
corrida entera falla, el job sale **rojo** — sin eso, un cliente dejaría de recibir su
informe y nadie se enteraría hasta que reclame.

---

## Tu trabajo: dar de alta un cliente

Un comando. Acepta KMZ, KML, SHP, GeoJSON o GPKG — lo que el cliente mande.

```bash
python -m pix_alerta.alta_cliente --clave CERRO --titulo "Cerro Alto" --lotes "C:/ruta/lotes.kmz" --campo-id lote --cultivo soya --epsg EPSG:31981 --campana 2026/2027 2026-10-01 2027-04-30 --K 10
```

Después:

```bash
git add clientes lotes && git commit -m "alta CERRO" && git push
```

Y listo. La próxima corrida lo toma solo.

### Qué valida el alta antes de aceptar

Rechaza el archivo si hay **ids de lote repetidos o vacíos** (sin id estable no se puede
rastrear lo que el técnico registra), geometrías nulas o inválidas, o falta de sistema de
coordenadas. Avisa si hay lotes de menos de 0,5 ha (suelen ser drenajes dibujados dentro
del mismo archivo) o de más de 2.000 ha (bloques sin dividir).

Eso se arregla en cinco minutos ahora. Descubrirlo en enero, dentro de una corrida
programada que nadie está mirando, cuesta una campaña.

---

## Puesta en marcha (una sola vez)

**1. Crear el repositorio.** Tiene que ser **privado**: lleva geometrías de campos de
clientes.

**2. Cargar los tres secretos** en Settings → Secrets → Actions:

| Secreto | Qué es |
|---|---|
| `GEE_SA_JSON` | El JSON completo de la cuenta de servicio de Earth Engine |
| `WHATSAPP_PHONE` | El número registrado en CallMeBot |
| `CALLMEBOT_APIKEY` | La clave que da CallMeBot |

Ya tenés los tres funcionando en el repo de monitoreo de trigo; son los mismos.

**3. Probar a mano** desde la pestaña Actions → *pixadvisor-monitor* → *Run workflow*,
poniendo un cliente y una fecha. Si sale verde y aparecen archivos en `entregas/`, está.

**4. Apuntar la app.** En `PIX_SCOUT/app/js/config.js`:

```js
FOCOS_ENDPOINT: 'https://raw.githubusercontent.com/<usuario>/<repo>/main/entregas/{campo}/ultimo'
```

El `{campo}` se reemplaza por la clave del cliente. Recompilar el APK una vez y no se
toca más: de ahí en adelante el teléfono baja los focos solo.

> ⚠️ Con el repo **privado**, `raw.githubusercontent.com` **no sirve sin token**. Dos
> caminos: publicar sólo la carpeta `entregas/` en un repo aparte público (no lleva
> geometría de lote, sólo los focos ya recortados), o servirla desde Supabase Storage.
> **Esto hay que decidirlo antes de la primera entrega real.**

---

## Por qué GitHub Actions y no un servidor

Porque ya lo tenés funcionando desde julio en el monitoreo de trigo y no te dio un
problema. Cuesta cero, corre con tu PC apagada, guarda el historial de cada entrega en el
propio repositorio, y si algo falla te llega un mail. Un servidor propio para uno a cinco
clientes es pagar y administrar algo que no hace falta todavía.

Cuando tengas suficientes clientes para que el panel valga la pena, la máquina no cambia:
el panel se apoya arriba de esto.

---

## Lo que todavía NO hace

- **La app manda las validaciones a un servidor.** El backend está escrito y probado pero
  las credenciales de Supabase no están pegadas: hoy lo que el técnico registra queda en
  el teléfono. Ver `PIX_SCOUT/backend/README.md`.
- **El cobro.** Alta y baja de clientes en Asaas es manual.
- **El panel web.** Hoy el alta es por comando y el estado se mira en la pestaña Actions.
- **La ruta pública para la APK.** Ver el aviso de arriba: hay que decidirla.
