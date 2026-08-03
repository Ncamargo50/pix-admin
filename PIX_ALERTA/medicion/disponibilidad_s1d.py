# -*- coding: utf-8 -*-
"""¿Sentinel-1D cambio la disponibilidad de observacion? La palanca de ~5x, re-medida.

POR QUE ESTA MEDICION VA ANTES QUE CUALQUIER MEJORA DEL CRITERIO
----------------------------------------------------------------
Es la conclusion mas fuerte que produjo este motor, y esta escrita en `config.py`:

    El lift sigue a la COBERTURA, no al indice. La campaña con 16,0% de observaciones
    plenas dio 36x; la de 11,8% dio 6,7x, con el mismo eje. **Cambiar de eje compra
    ~2x; mejorar la disponibilidad de imagen compra ~5x.**

Y `radar.py` dejo medido el techo que teniamos:

    Medido sobre HDS (oct-2025 a ene-2026): S1 aporta **9 pasadas en 4 meses, de UNA
    sola orbita relativa, solo descendente**, con hueco mediano de 12 dias. Los 6 dias
    nominales NO existen ahi.

QUE CAMBIO EN EL MUNDO (y por eso hay que volver a medir)
---------------------------------------------------------
**Sentinel-1D quedo plenamente operativo el 1 de mayo de 2026.** Con S1C ya en orbita
desde 2024, la constelacion recupero la revisita nominal de 6 dias: S1D vuela la misma
traza que S1C y repite sus adquisiciones un dia despues.

Toda la caracterizacion de radar de este repositorio es de oct-2025 a ene-2026, o sea
**anterior a eso**. El "9 pasadas en 4 meses, una sola orbita" puede seguir siendo
cierto —el plan de adquisicion de ESA sobre Sudamerica no es simetrico y una sola
orbita puede seguir cubriendo el punto— o puede haber cambiado. **No se sabe, y se
esta planificando una campaña sobre el numero viejo.**

    python -m medicion.disponibilidad_s1d --cliente TRIGO
    python -m medicion.disponibilidad_s1d --cliente HDS --desde 2025-10-01 --hasta 2026-08-01

QUE IMPRIME
-----------
Por sitio, y partiendo la serie en el 1-may-2026 (S1D operativo):

  · pasadas por orbita relativa y por sentido (ascendente / descendente)
  · hueco mediano y hueco maximo entre pasadas de la orbita dominante
  · dekadas con al menos una observacion S2 UTIL, con S1, y con la union de las dos

LO QUE ESTA MEDICION **NO** DICE
--------------------------------
No dice que el radar mejore la deteccion. `radar.py` es explicito: **S1 no detecta
enfermedad**, mide estructura y agua. Lo que compra es convertir un "SIN DATO" en un
"el radar no vio cambio estructural", y eso vale por la continuidad, no por la
sensibilidad. Si las pasadas subieron, lo que sube es la fraccion de lote-fecha con
ALGUNA observacion; cuanto de eso se traduce en lift hay que medirlo aparte, con
`medicion/comparar_ejes.py` sobre una campaña completa.
"""
import argparse
import sys

import pandas as pd

# Fecha en que Sentinel-1D quedo plenamente operativo tras el comisionamiento.
S1D_OPERATIVO = '2026-05-01'
# Cobertura minima para llamar UTIL a una escena optica sobre el sitio. Se toma la
# misma que usa el criterio para aceptar una escena a evaluar (criterio.COB_MINIMA_ACTUAL),
# no un numero nuevo elegido a conveniencia.
COB_UTIL = 0.70
DEKADA_DIAS = 10


def _pasadas_s1(aoi, desde, hasta):
    """DataFrame (fecha, orbita, pass) de las escenas S1 IW dual-pol sobre el AOI."""
    import ee

    from pix_alerta import radar as rd
    col = rd._coleccion(aoi, desde, hasta)
    n = int(col.size().getInfo() or 0)
    if not n:
        return pd.DataFrame(columns=['fecha', 'orbita', 'pass'])
    ts = col.aggregate_array('system:time_start').getInfo() or []
    orb = col.aggregate_array('relativeOrbitNumber_start').getInfo() or []
    pas = col.aggregate_array('orbitProperties_pass').getInfo() or []
    d = pd.DataFrame({'fecha': pd.to_datetime(ts, unit='ms').normalize(),
                      'orbita': orb, 'pass': pas})
    return d.drop_duplicates().sort_values('fecha').reset_index(drop=True)


def _fechas_s2_utiles(sitio, desde, hasta):
    """Fechas con al menos una escena S2 de cobertura >= COB_UTIL sobre el sitio.

    Pasa por `criterio._coleccion_limpia`, o sea por el MISMO camino de mascara que
    usa produccion (SCL dilatada + CloudScore+). Contar escenas del catalogo en vez de
    escenas limpias es lo que hace que todo el mundo publique disponibilidades que no
    se parecen a las que despues tiene el motor.
    """
    from pix_alerta import criterio as cri
    from pix_alerta import focos as fo
    geom = fo._geom_sitio(sitio) if hasattr(fo, '_geom_sitio') else None
    if geom is None:
        from pix_alerta import series as sr
        geom = sr._lotes_ee(sitio).geometry()
    base = cri._coleccion_limpia(geom, desde, hasta, cob_minima=COB_UTIL)
    f = base.aggregate_array('fecha').getInfo() or []
    return sorted(set(pd.to_datetime(f).normalize()))


def _huecos(fechas):
    """(mediano, maximo) en dias entre observaciones consecutivas. (nan, nan) si <2."""
    f = sorted(pd.to_datetime(list(fechas)))
    if len(f) < 2:
        return float('nan'), float('nan')
    d = [(f[i + 1] - f[i]).days for i in range(len(f) - 1)]
    return float(pd.Series(d).median()), float(max(d))


def _dekadas(desde, hasta):
    ini, fin = pd.Timestamp(desde), pd.Timestamp(hasta)
    out, d = [], ini
    while d < fin:
        out.append((d, min(d + pd.Timedelta(days=DEKADA_DIAS), fin)))
        d += pd.Timedelta(days=DEKADA_DIAS)
    return out


def _cubre(fechas, a, b):
    return any(a <= pd.Timestamp(f) < b for f in fechas)


def analizar_sitio(sitio, desde, hasta):
    from pix_alerta import series as sr
    aoi = sr._lotes_ee(sitio).geometry()

    print('\n' + '=' * 72)
    print('SITIO %s   %s .. %s' % (sitio.clave, desde, hasta))
    print('=' * 72)

    s1 = _pasadas_s1(aoi, desde, hasta)
    if s1.empty:
        print('  sin escenas S1 en el periodo')
    else:
        corte = pd.Timestamp(S1D_OPERATIVO)
        for etiqueta, sub in (('ANTES de S1D operativo', s1[s1.fecha < corte]),
                              ('DESPUES de S1D operativo', s1[s1.fecha >= corte])):
            print('\n  %s  (corte %s)' % (etiqueta, S1D_OPERATIVO))
            if sub.empty:
                print('    sin pasadas en este tramo')
                continue
            dias = max((sub.fecha.max() - sub.fecha.min()).days, 1)
            print('    %d pasadas en %d dias  (1 cada %.1f dias en promedio)'
                  % (len(sub), dias, dias / max(len(sub), 1)))
            g = sub.groupby(['orbita', 'pass']).size().sort_values(ascending=False)
            for (o, p), n in g.items():
                med, mx = _huecos(sub[(sub.orbita == o) & (sub['pass'] == p)].fecha)
                print('      orbita %-5s %-12s %3d pasadas | hueco mediano %s d, '
                      'maximo %s d'
                      % (o, p, n,
                         ('%.0f' % med) if med == med else 'n/d',
                         ('%.0f' % mx) if mx == mx else 'n/d'))
            if len(g) > 1:
                print('      (%d orbitas distintas: el motor usa SOLO la dominante, '
                      'mezclarlas cambia la geometria de vista)' % len(g))

    try:
        f_s2 = _fechas_s2_utiles(sitio, desde, hasta)
    except Exception as exc:                                   # noqa: BLE001
        print('\n  AVERIA leyendo S2: %s: %s' % (type(exc).__name__, str(exc)[:60]))
        return
    f_s1 = list(s1.fecha) if not s1.empty else []

    deks = _dekadas(desde, hasta)
    c2 = sum(1 for a, b in deks if _cubre(f_s2, a, b))
    c1 = sum(1 for a, b in deks if _cubre(f_s1, a, b))
    cu = sum(1 for a, b in deks if _cubre(f_s2, a, b) or _cubre(f_s1, a, b))
    n = max(len(deks), 1)
    print('\n  DEKADAS CON OBSERVACION  (%d dekadas de %d dias)' % (n, DEKADA_DIAS))
    print('    S2 util (cob >= %.2f) : %3d  (%5.1f%%)' % (COB_UTIL, c2, 100 * c2 / n))
    print('    S1 cualquiera         : %3d  (%5.1f%%)' % (c1, 100 * c1 / n))
    print('    S2 union S1           : %3d  (%5.1f%%)  <- lo que ve el motor'
          % (cu, 100 * cu / n))
    print('    aporte del radar      : %+5.1f puntos' % (100 * (cu - c2) / n))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cliente', default='TRIGO')
    ap.add_argument('--desde', default='2025-10-01')
    ap.add_argument('--hasta', default=None,
                    help='por defecto, hoy')
    a = ap.parse_args(argv)
    hasta = a.hasta or str(pd.Timestamp.today().date())

    from pix_alerta.ee_init import inicializar
    print('[GEE] %s' % inicializar())
    from pix_alerta import clientes as cl
    clientes = cl.cargar_todos()
    cl.registrar_sitios(clientes)
    cliente = next((c for c in clientes if c.clave == a.cliente), None)
    if cliente is None:
        print('no existe el cliente %s' % a.cliente)
        return 1

    print("""
REFERENCIA MEDIDA ANTES DE S1D (radar.py, HDS oct-2025 a ene-2026):
    9 pasadas en 4 meses | UNA sola orbita relativa, solo descendente | hueco mediano 12 d
Si el tramo "DESPUES" de abajo se parece a eso, S1D no cambio nada sobre este sitio y
hay que seguir planificando con 12 dias.""")

    for s in cliente.sitios:
        analizar_sitio(s, a.desde, hasta)

    print("""

COMO SE LEE
-----------
· Si aparecen DOS orbitas con conteos parecidos despues del corte, la constelacion
  ahora cubre el sitio por dos geometrias. Eso NO significa que el motor pueda usar las
  dos: `radar.py` trabaja con una sola y declara cual, porque mezclar geometrias de
  vista fabrica variabilidad temporal que no ocurrio en el campo. Lo que si se puede es
  elegir la mejor, o correr las dos por separado.
· Si el hueco mediano de la orbita dominante bajo de 12 a ~6 dias, la continuidad
  mejoro de verdad y hay que actualizar el numero que va al CONTRATO
  (`PLAN_A_PRODUCCION.md` puerta 5.1, hueco maximo declarado).
· El "aporte del radar" en puntos es la unica cifra que se puede prometer sin medir
  lift: dice cuantas dekadas mas tienen ALGUNA observacion, no cuantas anomalias mas
  se detectan.""")
    return 0


if __name__ == '__main__':
    sys.exit(main())
