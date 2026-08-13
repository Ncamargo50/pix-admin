"""
Separabilidad sano/enfermo, convolucionada a las bandas REALES de Sentinel-2.

Que hace
--------
Toma espectros hiperespectrales medidos con espectrorradiometro (400-2500 nm, 5 nm),
los convoluciona con las funciones de respuesta espectral OFICIALES de Sentinel-2 (ESA),
calcula los indices que usa el motor de PIX_ALERTA, y mide cuanto separan los dos grupos.

Es el puente laboratorio -> satelite: responde "si mi sensor fuera S2, ¿este indice
veria la diferencia?" ANTES de ir a buscarla en una escena.

Caso de origen
--------------
Herrmann et al. 2016, "Leaf and canopy level detection of Fusarium virguliforme
(sudden death syndrome) in soybean", UW EnSpec / Univ. of Wisconsin.
EcoSIS id 2a9d952a-5a28-47b3-9f85-8aa6e6808991, 5.851 espectros.
Etiqueta = `Inoculation` (1 inoculado / 0 control).

Lo que este arnes NO dice — leer antes de usar el numero
--------------------------------------------------------
1. `Inoculation` es el TRATAMIENTO, no el sintoma. Una planta inoculada puede no haber
   expresado la enfermedad. La separabilidad medida es un PISO, no el techo.
2. Son espectros de pinza foliar y de canopia proximal. **No hay suelo, ni atmosfera,
   ni pixel mixto, ni BRDF.** Un pixel de S2 de 100 m2 es otra cosa. Este numero acota
   por arriba lo que se puede esperar del satelite: si aca no separa, en orbita menos.
3. Hay ~250 plantas y 5.851 espectros: las repeticiones por planta NO son observaciones
   independientes. Por eso se reporta tambien el agregado POR PLANTA, que es el n real.

Datos
-----
Se descargan a `_cache_espectros/` (no versionado: son 17 MB + 0,9 MB).
  - EcoSIS  : https://ecosis.org/api/package/<id>/export?format=csv&metadata=true
  - SRF ESA : S2-SRF_COPE-GSEG-EOPG-TN-15-0007_3.1.xlsx

Uso
---
    python separabilidad_fusarium_s2.py
    python separabilidad_fusarium_s2.py --satelite B
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(__file__).parent / "_cache_espectros"

ID_ECOSIS = "2a9d952a-5a28-47b3-9f85-8aa6e6808991"
URL_ECOSIS = (
    f"https://ecosis.org/api/package/{ID_ECOSIS}/export?format=csv&metadata=true"
)
URL_SRF = (
    "https://sentinels.copernicus.eu/documents/247904/685211/"
    "S2-SRF_COPE-GSEG-EOPG-TN-15-0007_3.1.xlsx"
)

COLS_META = ["Date", "Inoculation", "Plant", "SampleNumber", "Site"]

# Piso fisico de escala del motor. Por debajo de esto una diferencia no se puede
# atribuir al cultivo con S2. Ver feedback_piso_de_escala_focos.
#
# OJO: 0,010 esta definido en unidades de una DIFERENCIA NORMALIZADA, acotada en
# [-1,1]. Compararlo contra el delta de un cociente sin acotar (CIre) o de un indice
# en nanometros (REIP) o de escala arbitraria (REDSI) no significa nada. Por eso el
# cociente solo se imprime para los indices acotados.
SIGMA_MINIMA = 0.010
ACOTADOS = {"NDVI", "NDMI", "NDRE", "PSRI", "SMI"}


# --------------------------------------------------------------------------- datos


def _bajar(url: str, destino: Path) -> Path:
    """Descarga perezosa: si el archivo ya esta, no lo vuelve a pedir."""
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    import urllib.request

    CACHE.mkdir(parents=True, exist_ok=True)
    print(f"  bajando {destino.name} ...", flush=True)
    with urllib.request.urlopen(url, timeout=300) as r, open(destino, "wb") as f:
        f.write(r.read())
    return destino


def cargar_espectros() -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Devuelve (longitudes de onda, matriz n x nbandas, metadatos)."""
    csv = _bajar(URL_ECOSIS, CACHE / "fusarium_soja_ecosis.csv")
    d = pd.read_csv(csv, encoding="utf-8-sig", low_memory=False)

    cols_wl = [c for c in d.columns if str(c).replace(".", "", 1).isdigit()]
    wl = np.array([float(c) for c in cols_wl])
    refl = d[cols_wl].to_numpy(dtype=float)
    meta = d[[c for c in COLS_META if c in d.columns]].copy()

    # El metadato del dataset declara unidades "%", pero el dato viene en fraccion.
    # Se verifica en vez de suponerlo: un NIR foliar sano vive en 0,35-0,60.
    nir = refl[:, np.argmin(np.abs(wl - 800))]
    if np.nanmedian(nir) > 1.5:
        print("  AVISO: reflectancia parece estar en %, se divide por 100")
        refl = refl / 100.0

    return wl, refl, meta


def cargar_srf(satelite: str = "A") -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Funciones de respuesta espectral oficiales de ESA, a 1 nm."""
    xlsx = _bajar(URL_SRF, CACHE / "S2-SRF.xlsx")
    hoja = f"Spectral Responses (S2{satelite.upper()})"
    d = pd.read_excel(xlsx, sheet_name=hoja)

    wl = d["SR_WL"].to_numpy(dtype=float)
    pref = f"S2{satelite.upper()}_SR_AV_"
    srf = {
        c.replace(pref, ""): d[c].to_numpy(dtype=float)
        for c in d.columns
        if c.startswith(pref)
    }
    return wl, srf


# ---------------------------------------------------------------------- convolucion


def convolucionar(
    wl_dato: np.ndarray,
    refl: np.ndarray,
    wl_srf: np.ndarray,
    srf: dict[str, np.ndarray],
    cobertura_minima: float = 0.99,
) -> pd.DataFrame:
    """
    B_i = integral(R(l) * S_i(l) dl) / integral(S_i(l) dl)

    Se interpola el espectro a la grilla de 1 nm de la SRF (no al reves: remuestrear
    la SRF a 5 nm perderia la forma de las bandas angostas como B5 y B8A).

    Dos reglas que no son opcionales:

    1. **La cobertura se evalua POR FILA, no para la matriz entera.** En este dataset
       conviven dos instrumentos: la hoja llega a 2500 nm y la canopia se corta en
       1630 nm. Con un solo rango global, `np.interp` devuelve NaN para la canopia y
       el conteo cae de 5.851 a 4.844 SIN AVISAR. Es el mismo modo de falla que
       [[feedback_verify_layer_ranges]]: el resultado sale, y esta mal.
    2. **Se descarta la banda cuya respuesta no esta cubierta**, en vez de integrarla
       a medias y seguir llamandola "la banda".
    """
    finito = np.isfinite(refl)
    n_val = finito.sum(axis=1)

    idx = np.arange(refl.shape[1])
    primero = np.where(n_val > 0, np.argmax(finito, axis=1), -1)
    ultimo = np.where(n_val > 0, refl.shape[1] - 1 - np.argmax(finito[:, ::-1], axis=1), -1)
    contiguo = (ultimo - primero + 1) == n_val
    if not contiguo[n_val > 0].all():
        print(f"  AVISO: {int((~contiguo).sum())} filas con huecos internos, se anulan")

    salida = pd.DataFrame(
        {b: np.full(refl.shape[0], np.nan) for b in srf}, index=range(refl.shape[0])
    )

    grupos = pd.DataFrame({"p": primero, "u": ultimo, "ok": contiguo & (n_val > 0)})
    for (p, u), sub in grupos[grupos.ok].groupby(["p", "u"]):
        filas = sub.index.to_numpy()
        lo, hi = wl_dato[p], wl_dato[u]
        dentro = (wl_srf >= lo) & (wl_srf <= hi)
        wl_i = wl_srf[dentro]
        cols = idx[p : u + 1]

        refl_i = np.vstack(
            [np.interp(wl_i, wl_dato[cols], refl[f, cols]) for f in filas]
        )

        descartadas = []
        for banda, resp in srf.items():
            total = np.trapezoid(resp, wl_srf)
            if total <= 0:
                continue
            r = resp[dentro]
            parcial = np.trapezoid(r, wl_i)
            if parcial / total < cobertura_minima:
                descartadas.append(f"{banda}({parcial / total:.0%})")
                continue
            salida.loc[filas, banda] = (
                np.trapezoid(refl_i * r, wl_i, axis=1) / parcial
            )
        print(
            f"  grupo {lo:.0f}-{hi:.0f} nm: {len(filas)} espectros"
            + (f" | bandas SIN cobertura: {', '.join(descartadas)}" if descartadas else "")
        )

    return salida


# -------------------------------------------------------------------------- indices


def _div(a: np.ndarray, b: np.ndarray, piso: float = 1e-3) -> np.ndarray:
    """Division con guarda: el denominador nunca baja de `piso`."""
    return a / np.where(np.abs(b) < piso, np.sign(b + 1e-12) * piso, b)


def indices(b: pd.DataFrame) -> pd.DataFrame:
    """
    Los indices del motor, con las bandas ya auditadas contra el paper original.
    NDMI con B8A (no B8), PSRI con B2 (no B3), REIP con 705+35 (no 700+40).

    Un indice cuya banda no tiene cobertura NO se calcula: queda NaN. Preferimos la
    columna vacia antes que un numero construido sobre una banda a medias.
    """
    recetas = {
        "NDVI": (("B8", "B4"), lambda d: _div(d["B8"] - d["B4"], d["B8"] + d["B4"])),
        "NDMI": (("B8A", "B11"), lambda d: _div(d["B8A"] - d["B11"], d["B8A"] + d["B11"])),
        "NDRE": (("B8A", "B5"), lambda d: _div(d["B8A"] - d["B5"], d["B8A"] + d["B5"])),
        "CIre": (("B7", "B5"), lambda d: _div(d["B7"], d["B5"]) - 1.0),
        "PSRI": (("B4", "B2", "B6"), lambda d: _div(d["B4"] - d["B2"], d["B6"])),
        "REIP": (
            ("B4", "B7", "B5", "B6"),
            lambda d: 705.0
            + 35.0 * _div((d["B4"] + d["B7"]) / 2.0 - d["B5"], d["B6"] - d["B5"]),
        ),
        "REDSI": (
            ("B7", "B4", "B5"),
            lambda d: _div(
                (705 - 665) * (d["B7"] - d["B4"]) - (783 - 665) * (d["B5"] - d["B4"]),
                2.0 * d["B4"],
            ),
        ),
        "SMI": (("B8A", "B12"), lambda d: _div(d["B8A"] - d["B12"], d["B8A"] + d["B12"])),
    }
    i = pd.DataFrame(index=b.index)
    for nombre, (necesita, f) in recetas.items():
        faltan = [x for x in necesita if x not in b.columns or b[x].isna().all()]
        if faltan:
            print(f"  {nombre}: NO calculable, faltan {', '.join(faltan)}")
            i[nombre] = np.nan
            continue
        i[nombre] = f(b)
    return i


# --------------------------------------------------------------------- separabilidad


def jm_1d(a: np.ndarray, b: np.ndarray) -> float:
    """
    Jeffries-Matusita univariada, rango [0, 2].
    Convencion de practica (ENVI/ERDAS, NO resultado teorico): >1,9 bien separables,
    <1,0 probablemente la misma clase. Supone normalidad en cada grupo.
    """
    m1, m2 = float(np.mean(a)), float(np.mean(b))
    v1, v2 = float(np.var(a, ddof=1)), float(np.var(b, ddof=1))
    vm = (v1 + v2) / 2.0
    if vm <= 0 or v1 <= 0 or v2 <= 0:
        return float("nan")
    bh = 0.125 * (m1 - m2) ** 2 / vm + 0.5 * math.log(vm / math.sqrt(v1 * v2))
    return 2.0 * (1.0 - math.exp(-bh))


def cohen_d(a: np.ndarray, b: np.ndarray) -> float:
    n1, n2 = len(a), len(b)
    v1, v2 = np.var(a, ddof=1), np.var(b, ddof=1)
    sp = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    return float((np.mean(a) - np.mean(b)) / sp) if sp > 0 else float("nan")


def tabla(ind: pd.DataFrame, etiqueta: pd.Series, titulo: str) -> pd.DataFrame:
    sano = etiqueta == 0
    enfe = etiqueta == 1
    filas = []
    for col in ind.columns:
        a = ind.loc[sano, col].to_numpy()
        b = ind.loc[enfe, col].to_numpy()
        a, b = a[np.isfinite(a)], b[np.isfinite(b)]
        if len(a) < 3 or len(b) < 3:
            continue
        delta = float(np.mean(b) - np.mean(a))
        filas.append(
            {
                "indice": col,
                "control": round(float(np.mean(a)), 4),
                "inoculado": round(float(np.mean(b)), 4),
                "delta": round(delta, 4),
                "d_Cohen": round(cohen_d(b, a), 3),
                "JM": round(jm_1d(a, b), 3),
                "|delta|/sigma_min": (
                    round(abs(delta) / SIGMA_MINIMA, 2) if col in ACOTADOS else "n/a"
                ),
            }
        )
    print(f"\n--- {titulo}  (n control={int(sano.sum())}, inoculado={int(enfe.sum())})")
    if not filas:
        print("  SIN DATO EVALUABLE: ningun indice tiene >=3 observaciones por grupo.")
        return pd.DataFrame()
    t = pd.DataFrame(filas).sort_values("JM", ascending=False)
    print(t.to_string(index=False))
    return t


def rangos(df: pd.DataFrame, titulo: str) -> None:
    """Imprimir min/max/prom de cada capa ANTES de usarla. Regla de la casa."""
    print(f"\n--- rangos: {titulo}")
    for c in df.columns:
        v = df[c].to_numpy()
        v = v[np.isfinite(v)]
        marca = ""
        if len(v) and (v.max() - v.min()) < 0.01 * max(abs(v.mean()), 1e-9):
            marca = "  <-- DEGENERADA"
        print(
            f"  {c:>6}: n={len(v):5d} min={v.min():8.4f} max={v.max():8.4f} "
            f"prom={v.mean():8.4f}{marca}"
        )


# ------------------------------------------------------------------------------ main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--satelite", default="A", choices=["A", "B", "a", "b"])
    args = ap.parse_args()

    print("== 1. datos ==")
    wl, refl, meta = cargar_espectros()
    print(f"  espectros: {refl.shape[0]}  |  {wl.min():.0f}-{wl.max():.0f} nm, "
          f"paso {np.median(np.diff(wl)):.0f} nm")

    wl_srf, srf = cargar_srf(args.satelite)
    print(f"  SRF Sentinel-2{args.satelite.upper()}: {len(srf)} bandas, "
          f"{wl_srf.min():.0f}-{wl_srf.max():.0f} nm")

    print("\n== 2. convolucion a bandas S2 ==")
    bandas = convolucionar(wl, refl, wl_srf, srf)
    rangos(bandas, "bandas convolucionadas (reflectancia)")

    print("\n== 3. indices ==")
    ind = indices(bandas)
    rangos(ind, "indices")

    et = pd.to_numeric(meta["Inoculation"], errors="coerce")
    sitio = meta["Site"].astype(str).str.strip()
    planta = meta["Plant"]

    print("\n== 4. separabilidad control vs inoculado ==")
    hoja = sitio.ne("") & sitio.ne("nan")
    tabla(ind[hoja], et[hoja], "NIVEL HOJA (pinza foliar, a campo)")
    tabla(ind[~hoja], et[~hoja], "NIVEL CANOPIA (proximal)")

    for s in sorted(sitio[hoja].unique()):
        m = hoja & sitio.eq(s)
        tabla(ind[m], et[m], f"hoja, sitio = {s}")

    print("\n== 5. el n que vale: agregado POR PLANTA ==")
    print("  5.851 espectros sobre ~250 plantas no son 5.851 observaciones "
          "independientes.")
    g = pd.concat([ind[hoja], planta[hoja].rename("planta"), et[hoja].rename("et")],
                  axis=1).dropna(subset=["planta"])
    if len(g):
        agg = g.groupby(["planta", "et"], as_index=False).mean(numeric_only=True)
        tabla(agg[ind.columns], agg["et"], "hoja, una observacion por planta")

    print(
        "\n== recordatorio ==\n"
        "  `Inoculation` es el tratamiento, NO el sintoma: la separabilidad medida es\n"
        "  un PISO. Y son espectros foliares/proximales: sin suelo, sin atmosfera y sin\n"
        "  pixel mixto. Lo que no separa aca, en orbita separa menos."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
