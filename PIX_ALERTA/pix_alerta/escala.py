# -*- coding: utf-8 -*-
"""Estimadores robustos de escala. La MAD no es el unico, y no es el mejor.

POR QUE ESTE MODULO EXISTE
--------------------------
Todo el motor estandariza residuos dividiendo por una escala robusta, y esa escala
es hoy la MAD en cinco lugares distintos. La MAD es robusta —punto de ruptura 50%—
pero es **ineficiente**: con datos gaussianos usa solo el 37% de la informacion de la
muestra. Con series de 6 a 14 observaciones limpias por pixel, tirar dos tercios de la
informacion no es gratis: la escala sale ruidosa, y una escala ruidosa mueve el z de
todos los pixeles.

    Rousseeuw, P.J. & Croux, C. (1993). "Alternatives to the Median Absolute
    Deviation". Journal of the American Statistical Association 88(424):1273-1283.
    DOI 10.1080/01621459.1993.10476408

    estimador   eficiencia gaussiana   punto de ruptura   costo
    MAD                 37%                  50%         O(n)
    Sn                  58%                  50%         O(n log n)
    Qn                  82%                  50%         O(n log n)

**Qn mas que duplica la eficiencia de la MAD sin perder nada de robustez.** No es un
compromiso: es estrictamente mejor en las dos dimensiones que importan, y el costo
extra es irrelevante con n de dos digitos.

LA CORRECCION DE MUESTRA FINITA NO ES OPCIONAL
----------------------------------------------
Los tres estimadores son consistentes solo ASINTOTICAMENTE. Con n chico estan
sesgados, y el sesgo es grande: para n=5, Qn sin corregir subestima la escala en mas
del 15%. Una escala subestimada infla el z y **dispara la tasa de falsa alarma**, que
es exactamente el modo de falla contra el que esta escrito todo este paquete.

    Akinshin, A. (2022). "Finite-sample Rousseeuw-Croux scale estimators".
    arXiv:2209.12268 — advierte ademas que "the actual Gaussian efficiency of Sn and
    Qn for small sample sizes is noticeably lower than in the asymptotic case".
    (Preprint sin revision por pares; los factores de abajo son los originales de
    Rousseeuw & Croux 1993, Tabla 2, que si esta revisado.)

⚠️ ESTO NO ESTA EN PRODUCCION. Se provee para poder MEDIRLO contra la MAD con los
arneses que ya existen. Cambiar el estimador de escala **invalida la calibracion**:
la tasa de falsa alarma del motor (mediana 0,00%, maximo 0,2-2,2%) se midio con MAD.
La regla de la casa no cambia por tener un buen argumento teorico.
"""
import numpy as np

# Constante de consistencia asintotica de la MAD para la normal.
C_MAD = 1.4826
# Idem Sn y Qn (Rousseeuw & Croux 1993).
C_SN = 1.1926
C_QN = 2.2219

# Factores de correccion de sesgo de muestra finita (R&C 1993, Tabla 2).
# Para n > 9 se usa la forma asintotica, distinta segun paridad.
_QN_FIN = {2: 0.399, 3: 0.994, 4: 0.512, 5: 0.844, 6: 0.611,
           7: 0.857, 8: 0.669, 9: 0.872}
_SN_FIN = {2: 0.743, 3: 1.851, 4: 0.954, 5: 1.351, 6: 0.993,
           7: 1.198, 8: 1.005, 9: 1.131}


def _factor_qn(n):
    """⚠️ LA PARIDAD VA AL REVES DE LO QUE PARECE, y el test lo caz0.

    Rousseeuw & Croux 1993 (y `robustbase::Qn` en R): para n > 9 el factor es
    **n/(n+1.4) si n es IMPAR** y **n/(n+3.8) si n es PAR**. Escribirlo al reves
    —que es el error natural— deja Qn(n=12) sesgado en **+18%**, medido por Monte
    Carlo en `tests/test_escala.py::test_la_correccion_deja_el_sesgo_acotado`.

    La razon de la asimetria: con n par, k = C(h,2) sobre h = n/2+1 cae mas lejos
    del cuartil asintotico que con n impar (para n=12, k/N = 0,318; para n=13,
    0,269; el limite es 0,25). El n par necesita una correccion MAS fuerte.
    """
    if n in _QN_FIN:
        return _QN_FIN[n]
    return n / (n + 1.4) if n % 2 == 1 else n / (n + 3.8)


def _factor_sn(n):
    if n in _SN_FIN:
        return _SN_FIN[n]
    return 1.0 if n % 2 == 0 else n / (n - 0.9)


def _limpio(v):
    v = np.asarray(v, dtype=float).ravel()
    return v[np.isfinite(v)]


def mad(v, corregir=True):
    """1,4826 x mediana(|x - mediana(x)|). El estimador actual del motor.

    `corregir` no hace nada aca y esta por simetria de interfaz: la MAD tambien
    tiene sesgo de muestra finita, pero el motor ya lo trata aparte en
    `ranking.SHRINK_MAD` para el caso concreto de residuos centrados por la mediana.
    """
    x = _limpio(v)
    if x.size == 0:
        return np.nan
    return float(C_MAD * np.median(np.abs(x - np.median(x))))


def sn(v, corregir=True):
    """1,1926 x mediana_i( mediana_j |x_i - x_j| ). Eficiencia gaussiana 58%.

    No necesita una estimacion previa de centro —a diferencia de la MAD, que resta
    la mediana— asi que no arrastra el error de ese centro.
    """
    x = _limpio(v)
    n = x.size
    if n < 2:
        return np.nan
    d = np.abs(x[:, None] - x[None, :])
    # mediana_j se toma sobre los n-1 valores distintos de j=i (se excluye el 0
    # propio, que no es una diferencia entre observaciones distintas).
    med_int = np.array([np.median(np.delete(d[i], i)) for i in range(n)])
    s = C_SN * float(np.median(med_int))
    return s * _factor_sn(n) if corregir else s


def qn(v, corregir=True):
    """2,2219 x el k-esimo orden de {|x_i - x_j| ; i < j}. Eficiencia gaussiana 82%.

    k = C(h,2) con h = floor(n/2) + 1, o sea aproximadamente el primer cuartil de
    las distancias entre pares. Es el estimador de escala robusto mas eficiente de
    los tres, y el que R&C recomiendan como reemplazo por defecto de la MAD.

    Implementacion directa O(n^2 log n). El algoritmo O(n log n) del paper no vale
    la pena con n de dos digitos, que es el regimen de este motor.
    """
    x = _limpio(v)
    n = x.size
    if n < 2:
        return np.nan
    pares = np.abs(x[:, None] - x[None, :])[np.triu_indices(n, k=1)]
    h = n // 2 + 1
    k = h * (h - 1) // 2
    k = min(max(k, 1), pares.size)
    q = C_QN * float(np.partition(pares, k - 1)[k - 1])
    return q * _factor_qn(n) if corregir else q


ESTIMADORES = {'mad': mad, 'sn': sn, 'qn': qn}


def estimar(v, metodo='mad', corregir=True):
    """Escala robusta por nombre. `metodo` en ESTIMADORES."""
    if metodo not in ESTIMADORES:
        raise ValueError('estimador desconocido: %r. Hay: %s'
                         % (metodo, tuple(ESTIMADORES)))
    return ESTIMADORES[metodo](v, corregir=corregir)
