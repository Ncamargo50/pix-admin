# -*- coding: utf-8 -*-
"""¿El criterio v2 tiene la tasa de falsa alarma que su alfa promete?

POR QUE ESTA MEDICION Y NO OTRA
-------------------------------
`calibrar_criterio.py` mide la tasa sobre fechas SIN evento de lotes reales. Eso es
lo que decide, pero no dice POR QUE da lo que da: mezcla el criterio con la
estructura del campo. Aca se simula la NULA EXACTA —pixeles que siguen su recta mas
ruido, sin ningun evento— para poder atribuir cada desvio a su causa.

Es un banco de pruebas SIN GEE: numpy solo. Corre en segundos y es reproducible.

    python -m medicion.nula_analitica_criterio

LO QUE SE PONE A PRUEBA
-----------------------
El criterio v2 estandariza el residuo de la fecha evaluada con la MAD TEMPORAL de
los residuos de la linea base contra su propia recta. Tres cosas pueden romper la
correspondencia entre `alfa` y la tasa real, y las tres se miden por separado:

1. GRADOS DE LIBERTAD. Los residuos de un ajuste de recta sobre N puntos tienen
   varianza sigma^2*(1-h_i), no sigma^2: la recta ya se acomodo a ellos. Su MAD
   SUBESTIMA sigma -> el z sale inflado -> mas falsas alarmas que las prometidas.

2. EXTRAPOLACION. La fecha evaluada esta FUERA de la ventana de ajuste. La varianza
   del residuo de prediccion es sigma^2*(1+h0) con
       h0 = 1/N + (t0 - t_medio)^2 / SUM (t_i - t_medio)^2
   que para un punto extrapolado puede ser >> 1/N. El docstring del modulo afirma
   `sigma^2*(1+1/N)`, que es la formula del punto MEDIO, no la de una prediccion.

3. DIRECCION. Se exige ademas que los dos ejes apunten al deterioro. Bajo la nula
   eso pasa con probabilidad P = 1/4 + arcsin(rho)/(2*pi), asi que la tasa REAL es
   alfa*P, bastante menor que alfa. El criterio es MAS DURO de lo que declara — que
   es el lado seguro para el productor, pero significa que la sensibilidad es menor
   que la que dice la etiqueta, y hoy la sensibilidad es justo lo que no esta medido.
"""
import math

import numpy as np

CHI2_2 = {0.01: 9.210, 0.02: 7.824, 0.025: 7.378, 0.05: 5.991, 0.10: 4.605}


def _chi2_2_umbral(p):
    """Cuantil 1-p de una chi2 con 2 gl. Tiene forma cerrada: -2*ln(p)."""
    return -2.0 * math.log(p)


def simular(n_base=6, n_pix=200000, alfa=0.01, rho=0.8, span=60.0,
            dt_eval=5.0, semilla=0, corregir=False):
    """Nula exacta: cada pixel sigue su recta + ruido. NO hay ningun evento.

    Devuelve la fraccion de pixeles marcados. Con el criterio bien calibrado tiene
    que dar `alfa * P(direccion)`; cualquier desvio es del estimador, no del campo.

    `corregir=True` aplica las dos correcciones (grados de libertad y varianza de
    prediccion) y el umbral ajustado por la puerta de direccion.
    """
    rng = np.random.default_rng(semilla)
    # Tiempos de la linea base: repartidos en `span` dias, como las escenas limpias.
    t = np.linspace(0.0, span, n_base)
    t0 = span + dt_eval                      # la fecha evaluada, FUERA del ajuste
    tm = t.mean()
    sxx = ((t - tm) ** 2).sum()
    h0 = 1.0 / n_base + (t0 - tm) ** 2 / sxx           # leverage de la prediccion
    h_medio = 2.0 / n_base                             # gl consumidos por la recta

    # Ruido correlacionado entre los dos ejes, con sigma=1 sin perdida de generalidad.
    L = np.linalg.cholesky(np.array([[1.0, rho], [rho, 1.0]]))

    def ruido(n):
        e = rng.standard_normal((2, n))
        return L @ e

    # Serie de la base: la senal es una recta, asi que el ajuste la recupera y lo
    # unico que queda es el ruido. Se simula directamente el ruido.
    res_base = np.empty((2, n_base, n_pix))
    for i in range(n_base):
        res_base[:, i, :] = ruido(n_pix)

    # Ajuste de la recta a ESE ruido, y residuos contra la recta ajustada.
    w = (t - tm) / sxx
    pend = np.tensordot(w, res_base, axes=([0], [1]))          # (2, n_pix)
    orden = res_base.mean(axis=1) - pend * tm
    ajuste = orden[:, None, :] + pend[:, None, :] * t[None, :, None]
    resid = res_base - ajuste

    mad = np.median(np.abs(resid), axis=1) * 1.4826            # (2, n_pix)

    # Residuo de la fecha evaluada contra la recta EXTRAPOLADA.
    r0 = ruido(n_pix) - (orden + pend * t0)

    sigma = mad.copy()
    if corregir:
        # 1. la MAD de residuos de un fit subestima sigma
        sigma = sigma / math.sqrt(1.0 - h_medio)
        # 2. el residuo de PREDICCION tiene varianza sigma^2*(1+h0)
        sigma = sigma * math.sqrt(1.0 + h0)
    sigma = np.maximum(sigma, 1e-9)
    z = r0 / sigma

    # Mahalanobis con la correlacion TEMPORAL verdadera (2x2 en forma cerrada).
    d2 = (z[0] ** 2 - 2 * rho * z[0] * z[1] + z[1] ** 2) / (1 - rho ** 2)

    # Puerta de direccion: los dos ejes en el sentido del deterioro.
    dir_mala = (z[0] < 0) & (z[1] < 0)
    p_dir = 0.25 + math.asin(rho) / (2 * math.pi)

    if corregir:
        # Para que la tasa FINAL sea alfa, el umbral tiene que compensar la puerta.
        umbral = _chi2_2_umbral(min(alfa / p_dir, 0.999))
    else:
        umbral = CHI2_2.get(round(alfa, 3), 9.210)

    marca = (d2 >= umbral) & dir_mala
    return {'tasa': float(marca.mean()), 'sd_z': float(z.std()),
            'h0': h0, 'p_dir': p_dir, 'umbral': umbral,
            'objetivo_sin_direccion': alfa,
            'objetivo_con_direccion': alfa * p_dir}


def main():
    print(__doc__.split('LO QUE SE PONE A PRUEBA')[0].strip()[:0] or '', end='')
    print('NULA EXACTA — no hay ningun evento. alfa nominal = 1%%\n')
    print('%-9s %-7s | %-8s %-9s | %-9s %-9s %-9s'
          % ('n_base', 'rho', 'SD(z)', 'leverage', 'objetivo', 'ACTUAL', 'CORREGIDO'))
    print('-' * 78)
    for n_base in (4, 5, 6, 8, 12):
        for rho in (0.0, 0.8):
            a = simular(n_base=n_base, rho=rho, corregir=False)
            b = simular(n_base=n_base, rho=rho, corregir=True)
            print('%-9d %-7.1f | %-8.2f %-9.2f | %-9.3f%% %-8.3f%% %-8.3f%%'
                  % (n_base, rho, a['sd_z'], a['h0'],
                     100 * a['objetivo_con_direccion'], 100 * a['tasa'],
                     100 * b['tasa']))
    print("""
COMO SE LEE
-----------
· `objetivo` es lo que el criterio DEBERIA marcar: alfa * P(direccion). Con rho=0,8
  la puerta de direccion deja pasar el 40%%, asi que 1%% nominal son 0,40%% reales.
· `ACTUAL` es lo que marca el criterio tal como esta hoy.
· `CORREGIDO` aplica grados de libertad + varianza de prediccion + umbral ajustado
  por la puerta, y tiene que dar el `alfa` PEDIDO (1%%), no el objetivo degradado.
· `SD(z)` distinto de 1 es la firma del problema: el z no esta bien escalado.""")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
