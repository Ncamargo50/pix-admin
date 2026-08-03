# -*- coding: utf-8 -*-
"""¿La TEXTURA es el segundo eje independiente que ningun indice espectral logro ser?

DE DONDE SALE LA PREGUNTA
-------------------------
De un callejon sin salida MEDIDO, no de una idea nueva. `medicion/banda_compartida.py`
dejo esta tabla de correlacion de residuos temporales contra NDMI:

    NDMI + NDRE (produccion)   rho = 0,969   -> 6,1% de varianza independiente
    NDMI + PSRI                rho = 0,927
    NDMI + CIRE                rho = 0,830   -> 31,1%, el mejor de los tres

y la conclusion de `config.py` fue no cambiar, porque las tres evidencias no
coincidian. Pero hay algo que las tres alternativas comparten y que explica el techo:
**son indices espectrales, y todos siguen la biomasa**. Ya estaba medido que los cinco
indices del motor correlacionan 0,97-0,998 espacialmente entre si. Buscar el segundo
eje entre indices era buscarlo donde no esta.

La textura no es reflectancia: es la ORGANIZACION ESPACIAL de la reflectancia. Es
ortogonal por fisica, no por estadistica.

QUE MIDE ESTE ARNES
-------------------
Las DOS cosas que hacen falta antes de siquiera considerar el cambio, y en este orden:

  1. **EL SIGNO** (`--signo`). Sin esto no se puede usar el eje **en ninguna forma**.
     `ranking.SIGNO` declara si la alarma es el valor alto o el bajo, y un signo
     invertido hace que el motor marque los lotes SANOS sin fallar ni avisar. Para
     TEXNIR el signo esta razonado pero no medido; para NDTX no esta ni razonado.

  2. **LA INDEPENDENCIA** (`--rho`, por defecto). |rho| de los residuos temporales
     contra NDMI, con el MISMO estimador que uso `banda_compartida.py`, para que los
     numeros sean comparables contra la tabla de arriba sin asteriscos.

    python -m medicion.textura_como_eje --hasta 2026-08-20 --signo
    python -m medicion.textura_como_eje --hasta 2026-08-20

LO QUE ESTE ARNES **NO** DECIDE
------------------------------
No alcanza para tocar `config.EJES`. Faltan las otras dos patas que la casa exige:

    medicion/calibrar_criterio.py --ejes NDMI,TEXNIR   (tasa sobre fechas sin evento)
    medicion/comparar_ejes.py                          (lift contra la nula sintetica)

Y sigue vigente la regla: **cambiar un parametro de produccion necesita una razon
POSITIVA.** Si empata, no se cambia.

LA TRAMPA ESPECIFICA DE ESTA MEDICION
-------------------------------------
La textura sube en el borde de nube y en el borde de lote (`series._textura`, limites 1
y 2). Los dos artefactos se parecen a lo que se busca. Si TEXNIR sale espectacularmente
independiente de NDMI, la primera hipotesis a descartar NO es que sea un gran eje: es
que este midiendo geometria de mascara. Por eso el arnes imprime tambien la cobertura
de cada lote-fecha: si la independencia se concentra en las fechas de baja cobertura,
es artefacto.
"""
import argparse
import json
import sys

# Candidatos a medir contra el primer eje. El primer eje se toma de cfg.EJES[0] para
# que este arnes siga a produccion si algun dia cambia.
CANDIDATOS = ('TEXNIR', 'NDTX', 'NDRE', 'CIRE')
# Que comparte cada candidato con NDMI, para que la tabla se explique sola.
FAMILIA = {'TEXNIR': 'textura', 'NDTX': 'textura',
           'NDRE': 'espectral', 'CIRE': 'espectral'}


def _cobertura_media(sitio, feat, hasta):
    """Cobertura media de las escenas de la base. Para separar señal de artefacto."""
    import ee
    import pandas as pd

    from pix_alerta import criterio as cri
    from pix_alerta import focos as fo
    geom = fo._geom_lote(sitio, feat)
    ventana = cri.ventana_de(sitio)
    desde = str(pd.Timestamp(hasta) - pd.Timedelta(days=ventana))[:10]
    fin = str(pd.Timestamp(hasta) - pd.Timedelta(days=1))[:10]
    base = cri._coleccion_limpia(geom, desde, fin)
    cobs = base.aggregate_array('cob').getInfo() or []
    return (sum(cobs) / len(cobs)) if cobs else float('nan')


def medir(cliente, hasta, con_signo=False):
    """Devuelve filas (lote, candidato, rho, n_base, cobertura)."""
    from pix_alerta import config as cfg
    from medicion.banda_compartida import rho_residuos

    eje1 = cfg.EJES[0]
    filas = []
    for s in cliente.sitios:
        with open(s.lotes_geojson, encoding='utf-8') as fh:
            gj = json.load(fh)
        for f in gj['features']:
            lid = str(f['properties'].get(s.campo_id))
            try:
                cob = _cobertura_media(s, f, hasta)
            except Exception:                             # noqa: BLE001
                cob = float('nan')
            for cand in CANDIDATOS:
                try:
                    r = rho_residuos(s, f, hasta, (eje1, cand))
                except Exception as exc:                  # noqa: BLE001
                    print('%-20s %-8s AVERIA %s: %s'
                          % (lid, cand, type(exc).__name__, str(exc)[:50]))
                    continue
                if r is None:
                    print('%-20s %-8s sin datos suficientes' % (lid, cand))
                    continue
                filas.append({'lote': lid, 'candidato': cand, 'rho': r['rho'],
                              'n_base': r['n_base'], 'cobertura': cob})
                if con_signo:
                    print('%-20s %-8s %-10s rho=%+.3f  n=%d  cob=%.2f'
                          % (lid, cand, FAMILIA[cand], r['rho'], r['n_base'], cob))
                else:
                    print('%-20s %-8s %-10s %+8.3f %6d %8.2f'
                          % (lid, cand, FAMILIA[cand], r['rho'], r['n_base'], cob))
    return filas


def signo_implicado(rho):
    """Signo de alarma que IMPLICA una correlacion contra el primer eje.

    El primer eje es NDMI, cuya alarma es el valor BAJO (`ranking.SIGNO['NDMI'] = -1`).
    Entonces, sobre los residuos:

        rho < 0  -> cuando NDMI baja (deterioro), el candidato SUBE  -> alarma alta -> +1
        rho > 0  -> cuando NDMI baja, el candidato tambien BAJA      -> alarma baja -> -1

    Devuelve (signo, |rho|). Con |rho| chico el signo NO esta determinado por esta
    medicion: dos variables casi independientes no se implican el sentido entre si, y
    ahi hace falta un evento conocido para fijarlo.
    """
    return (-1 if rho > 0 else +1), abs(rho)


# Debajo de este |rho| la implicacion de signo no es concluyente: la correlacion es
# demasiado debil para que el sentido de una diga algo del sentido de la otra.
RHO_MINIMO_PARA_SIGNO = 0.30


def resumen(filas, con_signo=False):
    import statistics as st

    from pix_alerta import ranking as rk
    if not filas:
        print('\nsin filas: no se pudo medir nada')
        return
    print('\n' + '=' * 74)
    por = {}
    for r in filas:
        por.setdefault(r['candidato'], []).append(r['rho'])

    if con_signo:
        print('SIGNO IMPLICADO POR LA CORRELACION CON %s\n'
              % __import__('pix_alerta.config', fromlist=['x']).EJES[0])
        print('%-8s %-10s %8s %8s %10s %10s %s'
              % ('cand', 'familia', 'rho_med', '|rho|', 'implicado',
                 'declarado', 'veredicto'))
        print('-' * 74)
        for cand, v in por.items():
            m = st.fmean(v)
            imp, mag = signo_implicado(m)
            dec = rk.SIGNO.get(cand)
            if mag < RHO_MINIMO_PARA_SIGNO:
                vered = 'NO CONCLUYENTE (|rho| < %.2f)' % RHO_MINIMO_PARA_SIGNO
            elif dec is None:
                vered = 'FALTA DECLARAR en ranking.SIGNO'
            elif imp == dec:
                vered = 'coincide'
            else:
                vered = '*** CONTRADICE lo declarado ***'
            print('%-8s %-10s %+8.3f %8.3f %+10d %+10s %s'
                  % (cand, FAMILIA[cand], m, mag, imp,
                     ('%+d' % dec) if dec is not None else 'n/d', vered))
        print("""
COMO SE LEE
-----------
"CONTRADICE" es un hallazgo, no un error del arnes: significa que el eje, tal como esta
declarado hoy en `ranking.SIGNO`, marcaria los lotes SANOS. Hay que corregir el signo
ANTES de cualquier otra medicion, porque la tasa de falsa alarma se mide sobre el
sentido de alarma y saldria al reves.

"NO CONCLUYENTE" no es malo: para un eje que se busca INDEPENDIENTE, un |rho| bajo es
justamente lo deseable. Solo dice que el signo hay que fijarlo con un evento conocido
—un lote con daño confirmado a campo— y no con esta correlacion.""")
        return

    print('INDEPENDENCIA CONTRA %s (residuos temporales)\n'
          % __import__('pix_alerta.config', fromlist=['x']).EJES[0])
    print('%-8s %-10s %8s %8s %8s %10s'
          % ('cand', 'familia', '|rho|med', '|rho|min', '|rho|max', 'var_indep'))
    print('-' * 60)
    orden = sorted(por.items(), key=lambda x: st.fmean([abs(v) for v in x[1]]))
    for cand, v in orden:
        a = [abs(x) for x in v]
        m = st.fmean(a)
        print('%-8s %-10s %8.3f %8.3f %8.3f %9.1f%%'
              % (cand, FAMILIA[cand], m, min(a), max(a), (1 - m ** 2) * 100))
    print("""
COMO SE LEE
-----------
`var_indep` = 1 - rho^2, la fraccion de varianza del candidato que NO esta explicada
por el primer eje. Es la evidencia que el segundo eje agrega de verdad. Referencia
MEDIDA sobre trigo (`medicion/banda_compartida.py`): NDRE en produccion aporta 6,1%,
CIre aporta 31,1%.

⚠️ ANTES DE FESTEJAR UN NUMERO ALTO, mirar la columna `cobertura` de la tabla de
arriba: la textura sube en el borde de nube y en el borde de lote. Si la independencia
se concentra en los lotes-fechas de baja cobertura, no es un eje nuevo — es geometria
de mascara con otro nombre.

Y esto sigue sin alcanzar para mover `config.EJES`. Faltan la tasa empirica sobre
fechas sin evento y el lift contra la nula sintetica.""")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--hasta', required=True)
    ap.add_argument('--cliente', default='TRIGO')
    ap.add_argument('--signo', action='store_true',
                    help='medir el SIGNO de alarma implicado, no la independencia')
    a = ap.parse_args(argv)

    from pix_alerta.ee_init import inicializar
    print('[GEE] %s' % inicializar())
    from pix_alerta import clientes as cl
    clientes = cl.cargar_todos()
    cl.registrar_sitios(clientes)
    cliente = next((c for c in clientes if c.clave == a.cliente), None)
    if cliente is None:
        print('no existe el cliente %s' % a.cliente)
        return 1

    if not a.signo:
        print('\n%-20s %-8s %-10s %8s %6s %8s'
              % ('lote', 'cand', 'familia', 'rho', 'n_base', 'cobert'))
        print('-' * 66)
    filas = medir(cliente, a.hasta, con_signo=a.signo)
    resumen(filas, con_signo=a.signo)
    return 0


if __name__ == '__main__':
    sys.exit(main())
