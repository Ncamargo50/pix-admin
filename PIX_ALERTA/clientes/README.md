# Alta de cliente

Un cliente es **un archivo JSON en esta carpeta**. No se toca ningún `.py`.

Ese era el bloqueante 8 del plan: hasta ahora, dar de alta el segundo cliente significaba
forkear el repositorio, que es lo que pasa con el pipeline de rásteres (haciendas
hardcodeadas en 6 archivos + binarios traídos a mano).

---

## El archivo mínimo

Para una hacienda nueva, definiéndola completa:

```json
{
  "clave": "CERRO",
  "titulo": "Cerro Alto Agropecuaria",
  "activo": true,
  "K": 5,
  "sitios": [
    {
      "clave": "CERRO_B2",
      "titulo": "Cerro Alto Bloque 2",
      "lotes_geojson": "../lotes/cerro_alto.geojson",
      "campo_id": "lote",
      "epsg_metrico": "EPSG:31981",
      "campanas": {"2026/2027": ["2026-10-01", "2027-04-30"]}
    }
  ],
  "entrega": {"cadencia_dias": 10},
  "marca": {"nombre": "Cerro Alto", "color": "#1E40AF"}
}
```

Para reutilizar un sitio ya definido en `config.py`, `"sitios_ref": ["HDS"]`.

Las **rutas relativas se resuelven contra este archivo**, para que un cliente sea una
carpeta portable y no un conjunto de rutas absolutas del Escritorio de alguien.

### Campos

| Campo | Obligatorio | Qué es |
|---|---|---|
| `clave` | sí | Identificador. **Da nombre a su carpeta de salida** |
| `titulo` | sí | Nombre para el informe |
| `sitios` / `sitios_ref` | uno de los dos | Haciendas del cliente |
| `K` | no | **Su** capacidad de scouting: cuántos lotes puede caminar. Entero ≥ 1 |
| `activo` | no (def. `true`) | `false` lo saca de la corrida sin borrarlo |
| `entrega` | no | `cadencia_dias`, `hueco_maximo_declarado_dias` |
| `marca` | no | Nombre y color para el informe |
| `nota` | no | Texto libre |

Del sitio, obligatorios: `clave`, `titulo`, `lotes_geojson`, `campo_id`.
Opcionales: `campo_area`, `epsg_metrico`, `buffer_negativo_m`, `campanas`, `unidades_csv`,
`unidades_col_id`, `unidades_col_cat`, `categorias_excluidas`.

---

## Correr

```bash
python -m pix_alerta.correr_todos --hasta 2026-04-30
```

```bash
python -m pix_alerta.correr_todos --cliente CERRO --hasta 2026-04-30
```

Códigos de salida (los que lee el cron): `0` nadie tenía novedad · `10` alguien entregó ·
`1` alguien falló o se violó el aislamiento.

---

## Las dos reglas que el código hace cumplir

**1. Aislamiento.** Cada cliente escribe sólo en `<salida>/<clave>/`, y al terminar la
corrida se **verifica leyendo las carpetas**, sin confiar en que cada módulo se haya
portado bien. Un entregable de un cliente en la carpeta de otro no es un problema de
formato: es mandarle a un productor los lotes de su vecino.

**2. Un cliente que falla no frena a los demás.** Si a uno se le rompe el GeoJSON, los
otros reciben su informe igual. El fallo se reporta en el resumen y tiñe el código de
salida, pero no aborta la corrida.

---

## Lo que se rechaza a propósito

El alta falla ruidosamente, antes de correr nada, si:

- **Hay un campo con typo** (`epsg` en vez de `epsg_metrico`). Se aceptaría en silencio y
  el sitio saldría proyectado en la zona equivocada.
- **Dos clientes comparten `clave`.** Compartirían carpeta y un informe pisaría al otro.
- **Un archivo de cliente es ilegible.** No se saltea: o se corre sabiéndolo, o no se
  corre. Saltearlo callado deja a un cliente sin informe y nadie se entera hasta que
  reclama.
- **`K` no es un entero ≥ 1.** K es la capacidad real de scouting; con un K malo el corte
  del ranking no significa nada.
- **Un sitio pisa a otro ya definido.** Se falla en vez de resolver por orden de lectura
  del directorio.

---

## Notas de operación

- Un cliente **fuera de su ventana de campaña no cuesta nada**: el motor corta antes de
  tocar Earth Engine (en madurez el NDMI baja y el PSRI sube, que es la misma firma que
  busca el criterio — no se puede distinguir cosecha de deterioro).
- `--serie` sólo se puede usar junto con `--cliente`: una serie ya extraída pertenece a un
  sitio, y reutilizarla para todos escribiría el ranking de un cliente con datos de otro.
- **La extracción de Earth Engine es lenta** (HDS: 207 lotes × 150 días tardó más de dos
  minutos). Con varios clientes conviene medir la corrida completa antes de fijar el
  horario del cron.
- `K` de `HDS.json` está en 10 de forma **provisoria**: el cliente todavía no lo declaró
  por escrito, que es la Puerta 0.2 del plan.
