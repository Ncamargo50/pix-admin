# -*- coding: utf-8 -*-
"""
Prioridad de MUESTREO por senal de dosel — Pixadvisor. Rediseno 2026-07-24.

QUE PRODUCE ESTE MODULO
=======================
Un ORDEN DE MUESTREO: en que lotes conviene poner el refractometro primero.
NO produce un estado fenologico, NO estima Pol/Brix, y NO dice que cosechar.

Ese cambio de alcance no es cosmetico. El motor anterior clasificaba el estado
fenologico por CUARTILES del propio score, lo que es una CUOTA: con toda la
hacienda inmadura salian igual 33 lotes rotulados MADUREZ_AVANZADA, y el
informe los convertia en "cosechar entre los primeros" (26 lotes) y "NO
cosechar" (27 lotes). Simulado sobre los datos reales con la hacienda entera
+3 SD mas humeda y nadie madurando, salian los mismos 33 lotes. Una etiqueta
que no puede decir "ninguno esta maduro" no es un diagnostico.

La decision de corte la toma el refractometro: ver madurez_campo.py
(Indice de Maturacao con los umbrales de Stupiello & Germek). Es lo que hacen
SASRI (ranking relativo con refractometro + PurEst) y ESALQ/Copersucar (curvas
de maduracion por variedad; el modelo Predpol usa horas-frio y balance hidrico,
no indices espectrales). Ninguna institucion que se pudo verificar decide el
orden de corte con satelite.

POR QUE EL SATELITE IGUAL SIRVE
===============================
Medido sobre los 131 lotes de Hacienda del Senor (2026-05-15):

    Spearman(orden por EDAD desde el corte, orden SATELITAL) = -0.137 (p=0.12)
    R2 de edad -> Priority_score                              =  0.004
    Top20 satelital vs Top20 por edad: coinciden               =  5 / 20

El satelite NO es una forma cara de recalcular la edad: dice algo distinto.
Pero "distinto" no es "correcto" — sin Pol o CMI de campo no se puede saber si
esa diferencia es informacion nueva o ruido nuevo. Por eso el producto es una
HIPOTESIS DE DONDE MIRAR, no una conclusion. Una campana de refractometro
cargada en la KB resuelve la pregunta (ver agente/pixadvisor_agente.py).

Todo el modulo opera sobre el CSV de features ya extraido, no sobre Earth
Engine: se puede testear y auditar sin credenciales.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "PISO_SD", "Z_CAP", "EJES",
    "zscore_con_piso", "eje_dosel", "diagnostico_capas",
    "bootstrap_honesto", "orden_muestreo", "anclaje_absoluto",
]

# Ejes conservados. NDWI se elimina por ser el MISMO indice que NDMI (r=0.998
# sobre los datos reales; difieren solo en B8 vs B8A). CIRE se elimina por
# correlacionar 0.90 con NDMI, no tener validacion publicada contra calidad de
# jugo en cana, y no haberse podido verificar su cita.
# PCA sobre los 4 originales: PC1 = 92.5%, indices efectivos = 1.17 de 4.
EJES = ("NDMI", "PSRI")

# Signo: mas seco (NDMI bajo) y mas senescente (PSRI alto) = mas prioritario
# para ir a medir. Es la direccion que la fisiologia respalda como DISPARADOR
# de la maduracion (deficit hidrico + baja temperatura; SASRI IS 4.7 y 12.1,
# Beauclair ESALQ 2004), no como medida de sacarosa.
SIGNOS = {"NDMI": -1.0, "PSRI": +1.0}

# PISO de desviacion estandar, no gate. El motor anterior usaba un gate con
# umbral 1e-6: casi nunca disparaba y cuando no disparaba dividia por una SD
# minuscula. Medido: 49 de 131 lotes tenian SD de PSRI < 0.03, con minimo
# 0.0016 -> ruido dividido por ~0.002, pegado al cap. Consecuencia perversa:
# los lotes MAS homogeneos eran los que mas se desplazaban en el ranking.
PISO_SD = {"NDMI": 0.03, "PSRI": 0.03}

Z_CAP = 3.0

# Numero minimo de anos de baseline para que el Z sea interpretable. Con n=3
# la SD tiene 2 grados de libertad y ~50% de error relativo: se midio que el
# Top20 tenia SD 5.8x menor que el resto pero solo 14% mas de sequedad, es
# decir, el denominador estaba eligiendo el ranking. Sentinel-2 opera desde
# 2015: hay 8-9 anos disponibles sin costo adicional.
N_ANOS_MINIMO = 5
N_ANOS_RECOMENDADO = 8


def zscore_con_piso(actual, base_mean, base_std, piso, cap=Z_CAP):
    """Z-score con PISO en la desviacion estandar (nunca saltar el lote).

    Devuelve np.nan solo si falta el valor actual o la media del baseline.
    Una SD baja NO invalida el lote: se le aplica el piso.
    """
    a = np.asarray(actual, dtype=float)
    m = np.asarray(base_mean, dtype=float)
    s = np.asarray(base_std, dtype=float)
    s = np.where(np.isfinite(s), s, 0.0)
    s_eff = np.maximum(s, piso)
    z = (a - m) / s_eff
    z = np.clip(z, -cap, cap)
    return np.where(np.isfinite(a) & np.isfinite(m), z, np.nan)


def eje_dosel(df: pd.DataFrame, ejes=EJES) -> pd.Series:
    """Combina los ejes de dosel en un unico indicador estandarizado.

    Se promedian los Z con su signo fisiologico, en vez de ponderarlos. Los
    pesos del motor anterior (0.30/0.20/0.20/0.10) daban impresion de composite
    multi-evidencia, pero como los indices correlacionaban 0.86-0.998 el
    resultado era un solo factor: el analisis de sensibilidad mostro que mover
    cualquier peso +-50% conservaba 19-20 de los 20 primeros. Promediar dos
    ejes reales es mas honesto y da el mismo orden.
    """
    cols, signos = [], []
    for k in ejes:
        c = f"{k}_z"
        if c in df.columns:
            cols.append(c); signos.append(SIGNOS[k])
    if not cols:
        raise ValueError("No hay columnas de Z-score; correr calcular_z primero")
    Z = df[cols].to_numpy(dtype=float)
    S = np.asarray(signos, dtype=float)
    with np.errstate(invalid="ignore"):
        num = np.nansum(Z * S, axis=1)
        den = np.sum(np.isfinite(Z), axis=1)
    return pd.Series(np.where(den > 0, num / np.maximum(den, 1), np.nan),
                      index=df.index, name="eje_dosel")


def diagnostico_capas(df: pd.DataFrame, ejes=EJES) -> str:
    """Imprime min/max/promedio y colinealidad ANTES de normalizar.

    Regla del proyecto que no estaba implementada. Este bloque habria
    detectado en la primera corrida que NDWI y NDMI eran el mismo indice
    (r=0.998) y que GDD tenia 8 valores unicos en 131 lotes.
    """
    lineas = ["-- diagnostico de capas --"]
    for k in ejes:
        for suf in ("_actual", "_baseline_std", "_z"):
            c = f"{k}{suf}"
            if c not in df.columns:
                continue
            v = pd.to_numeric(df[c], errors="coerce").dropna()
            if v.empty:
                lineas.append(f"  {c}: VACIA ({df[c].isna().sum()} nulos)  <-- REVISAR")
                continue
            rango = v.max() - v.min()
            alerta = ""
            if rango < 0.01 * max(abs(v.mean()), 1e-9):
                alerta += "  <-- DEGENERADA"
            if v.nunique() < max(len(v) / 5, 2):
                alerta += f"  <-- solo {v.nunique()} valores unicos"
            lineas.append(f"  {c}: min={v.min():.4f} max={v.max():.4f} "
                          f"prom={v.mean():.4f} n={len(v)}{alerta}")
    zc = [f"{k}_z" for k in ejes if f"{k}_z" in df.columns]
    if len(zc) > 1:
        lineas.append("-- colinealidad entre ejes --")
        lineas.append(df[zc].corr().round(3).to_string())
    return "\n".join(lineas)


def bootstrap_honesto(df: pd.DataFrame, ejes=EJES, n_iter=500,
                      n_anos=3, seed=42) -> pd.DataFrame:
    """Bootstrap que propaga TAMBIEN la incertidumbre del denominador.

    El bootstrap anterior solo perturbaba con sigma = 1/sqrt(n_pixeles), lo que
    daba un IC95 de ~4 posiciones sobre 131 lotes y se reportaba al cliente
    como "alta confianza". Propagando la incertidumbre de una SD estimada con
    n=3 anos, el IC real medido fue de ~34 posiciones: unas 8 veces mas ancho.

    Se propagan dos fuentes:
      1. Error espacial real: {eje}_actual_std / sqrt(n_pixeles), usando la SD
         espacial que YA esta en el CSV (el motor anterior la calculaba y no
         la usaba).
      2. Error del denominador: una SD estimada con (n_anos - 1) grados de
         libertad se remuestrea con el factor chi-cuadrado correspondiente.
    """
    rng = np.random.default_rng(seed)
    n = len(df)
    gl = max(n_anos - 1, 1)
    ranks = np.empty((n_iter, n), dtype=float)

    base = {}
    for k in ejes:
        z = pd.to_numeric(df.get(f"{k}_z"), errors="coerce").to_numpy(dtype=float)
        sd_esp = pd.to_numeric(df.get(f"{k}_actual_std"), errors="coerce").to_numpy(dtype=float)
        npx = pd.to_numeric(df.get(f"{k}_actual_n"), errors="coerce").to_numpy(dtype=float)
        sd_base = pd.to_numeric(df.get(f"{k}_baseline_std"), errors="coerce").to_numpy(dtype=float)
        sd_base = np.where(np.isfinite(sd_base) & (sd_base > 0), sd_base, PISO_SD[k])
        sd_base = np.maximum(sd_base, PISO_SD[k])
        npx = np.where(np.isfinite(npx) & (npx > 0), npx, 100.0)
        sem = np.where(np.isfinite(sd_esp), sd_esp, 0.0) / np.sqrt(npx)
        base[k] = (z, sem / sd_base)   # SEM expresada en unidades de Z

    for it in range(n_iter):
        acc = np.zeros(n); cnt = np.zeros(n)
        for k in ejes:
            z, sem_z = base[k]
            # 1) ruido espacial
            zi = z + rng.normal(0.0, np.where(np.isfinite(sem_z), sem_z, 0.0))
            # 2) incertidumbre del denominador: sd_hat/sd_real ~ sqrt(chi2_gl/gl)
            factor = np.sqrt(rng.chisquare(gl, size=n) / gl)
            zi = np.clip(zi / np.maximum(factor, 1e-6), -Z_CAP, Z_CAP)
            ok = np.isfinite(zi)
            acc = acc + np.where(ok, zi * SIGNOS[k], 0.0)
            cnt = cnt + ok.astype(float)
        score = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)
        ranks[it] = pd.Series(-score).rank(method="average").to_numpy()

    return pd.DataFrame({
        "rank_p025": np.nanpercentile(ranks, 2.5, axis=0),
        "rank_p975": np.nanpercentile(ranks, 97.5, axis=0),
        "rank_ancho_IC95": np.nanpercentile(ranks, 97.5, axis=0)
                            - np.nanpercentile(ranks, 2.5, axis=0),
    }, index=df.index)


def anclaje_absoluto(score: pd.Series, umbral=0.5) -> pd.Series:
    """Etiqueta por valor ABSOLUTO del score, no por cuantil.

    A diferencia de los cuartiles, esto PUEDE devolver "sin diferenciacion"
    para todos los lotes — que es la respuesta correcta cuando la hacienda es
    homogenea, y la que el motor anterior era incapaz de dar.

    El score es un promedio de Z capeados a +-3, asi que tiene interpretacion
    absoluta: |score| >= 0.5 significa medio desvio estandar de anomalia
    respecto del propio historico del lote. No es una medida de madurez.
    """
    s = pd.to_numeric(score, errors="coerce")
    out = pd.Series("sin_diferenciacion", index=s.index, dtype=object)
    out[s >= umbral] = "anomalia_seca_senescente"
    out[s <= -umbral] = "anomalia_humeda_vigorosa"
    out[~np.isfinite(s)] = "sin_dato"
    return out


def orden_muestreo(df: pd.DataFrame, ejes=EJES, n_anos=3,
                   col_variedad=None, verbose=True) -> pd.DataFrame:
    """Construye el orden de muestreo a partir del CSV de features.

    Espera por eje las columnas {eje}_actual, {eje}_baseline_mean,
    {eje}_baseline_std y, para el bootstrap, {eje}_actual_std y {eje}_actual_n.

    Si se pasa `col_variedad`, el orden se estratifica POR VARIEDAD: se
    recorren las variedades intercaladas, de modo que la primera jornada de
    muestreo cubra todas y no solo la mas precoz. La variedad es determinante
    de primer orden — la fecha optima de corte varia hasta ~6 semanas solo por
    cultivar (Rahimi Jamnani et al. 2019) — y la hacienda ya tiene el dato.
    """
    out = df.copy()

    for k in ejes:
        out[f"{k}_z"] = zscore_con_piso(
            out.get(f"{k}_actual"), out.get(f"{k}_baseline_mean"),
            out.get(f"{k}_baseline_std"), PISO_SD[k])

    if verbose:
        print(diagnostico_capas(out, ejes))
        if n_anos < N_ANOS_MINIMO:
            print(f"\n  AVISO: baseline de {n_anos} anos. Con menos de "
                  f"{N_ANOS_MINIMO} la SD tiene demasiado error y el "
                  f"denominador termina eligiendo el ranking. "
                  f"Recomendado: {N_ANOS_RECOMENDADO} anos.")

    out["score_dosel"] = eje_dosel(out, ejes)
    out["senal"] = anclaje_absoluto(out["score_dosel"])

    ic = bootstrap_honesto(out, ejes, n_anos=n_anos)
    out = pd.concat([out, ic], axis=1)

    out["orden_muestreo"] = (-out["score_dosel"]).rank(method="first").astype("Int64")

    if col_variedad and col_variedad in out.columns:
        out = out.sort_values("orden_muestreo")
        out["_k"] = out.groupby(col_variedad).cumcount()
        out = out.sort_values(["_k", "orden_muestreo"]).drop(columns="_k")
        out["orden_muestreo"] = range(1, len(out) + 1)
        if verbose:
            print(f"\n  Orden estratificado por '{col_variedad}': "
                  f"{out[col_variedad].nunique()} variedades intercaladas.")
    else:
        out = out.sort_values("orden_muestreo")
        if verbose:
            print("\n  AVISO: sin columna de variedad. La variedad y la fecha "
                  "del corte anterior son determinantes de primer orden y la "
                  "hacienda ya los tiene — pedirlos mejora esto mas que "
                  "cualquier indice espectral.")

    return out.reset_index(drop=True)
