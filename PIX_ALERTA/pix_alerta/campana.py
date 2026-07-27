"""Acumulacion de la campaña de validacion, ronda por ronda.

    python -m pix_alerta.campana --agregar salida/muestra_HDS_2026-10-15.csv
    python -m pix_alerta.campana --evaluar

POR QUE HACE FALTA
------------------
Medido sobre HDS: a una fecha hay ~6 lotes alertados, y con 6 el intervalo de confianza
de la precision es de **+-44 puntos**. No distingue "funciona" de "no funciona". Para
que el numero signifique algo hacen falta 40-60 alertados, y eso solo se junta
ACUMULANDO a lo largo de la campaña:

    n alertados |  6   20   40   60
    IC de la precision | +-44  +-22  +-16  +-13  puntos

Por eso la muestra se sortea en CADA ronda y los resultados se van sumando. Sortear una
sola vez en octubre daria una campaña entera para producir un numero inservible.

LA UNIDAD ES EL (LOTE, RONDA), NO EL LOTE
-----------------------------------------
Un lote puede salir ATENCION en la ronda 3 y SIN SEÑAL en la 7: son dos observaciones
distintas del sistema, y las dos cuentan. La pregunta que se contesta es **"de las
semanas-lote que el sistema alerto, cuantas tenian un problema real"**, que es
exactamente la pregunta operativa.

Consecuencia: un lote visitado dos veces pesa doble. Es correcto —el sistema lo alerto
dos veces— pero hay que decirlo, porque invita a leer los totales como si fueran lotes.
"""
import argparse
import json
import os
import sys

import pandas as pd

from . import validacion as vl

COLS = ('ronda', 'lote_id', 'estrato', 'N_estrato', 'n_estrato',
        'prob_inclusion', 'peso_diseño')


def _ruta(base, sitio):
    return os.path.join(base, 'campana_%s.csv' % sitio)


# Representaciones de "hubo problema" que sobreviven a un round-trip por CSV.
# Un CSV escrito desde una columna booleana CON algun NA sale como 1.0/0.0 (pandas
# promueve a float64), y una lista blanca de strings sobre eso convierte TODOS los
# positivos en negativos sin fallar ni avisar. Medido: [1.0, 0.0, 1.0, nan] daba
# cero positivos. Se castea numerico primero y se cae a texto solo si no es numero.
_VERDAD = ('true', 't', '1', 'si', 'sí', 'x', 'yes', 'y', 'verdadero')
_FALSO = ('false', 'f', '0', 'no', 'n', 'falso')


def _a_booleano(s):
    """Serie -> booleana con NA. Acepta bool, 1/0, 1.0/0.0 y texto.

    NO VISITADO NO ES 'SIN PROBLEMA'. Un vacio, un NaN o un texto irreconocible
    quedan en NA, nunca en False: convertirlos en False seria contar como revisado
    y limpio un lote al que nadie fue, y eso infla la precision del sistema. Es el
    mismo principio que el SIN DATO del criterio de lote.
    """
    vacio = s.isna() | s.astype(str).str.strip().str.lower().isin(
        ('', 'nan', 'none', 'na', '<na>', 'null'))
    num = pd.to_numeric(s.where(~vacio), errors='coerce')
    txt = s.astype(str).str.strip().str.lower()
    out = pd.Series(pd.NA, index=s.index, dtype='boolean')
    m = num.notna()                       # numerico: distinto de cero es verdadero
    out[m] = (num[m] != 0)
    out[~m & ~vacio & txt.isin(_VERDAD)] = True
    out[~m & ~vacio & txt.isin(_FALSO)] = False
    return out                            # lo no reconocido queda NA, no False


def agregar(base, sitio, muestra, ronda=None, validaciones=None):
    """Suma una ronda al acumulado. Idempotente por (ronda, lote_id).

    `validaciones` es opcional: se puede agregar la muestra al sortearla y completar
    los hallazgos despues, cuando el tecnico vuelve.
    """
    d = muestra.copy()
    if ronda is None:
        # La etiqueta de ronda NO puede salir de 'sin-fecha': con esa etiqueta todas
        # las rondas se llaman igual y cada `agregar` destruye el acumulado anterior.
        # Medido: dos rondas -> 26 filas y 1 ronda, cuando debian ser 52 y 2.
        if 'fecha_dato' not in d.columns or d['fecha_dato'].isna().all():
            raise ValueError(
                'no se puede deducir la ronda: la muestra no trae "fecha_dato". '
                'Pasala explicitamente con ronda="YYYY-MM-DD" (o --ronda en el CLI). '
                'Sin etiqueta distinta, la ronda nueva pisa a la anterior.')
        ronda = str(d['fecha_dato'].max())[:10]
    d['ronda'] = ronda
    if 'hubo_problema' not in d.columns:
        d['hubo_problema'] = pd.NA          # todavia no se visito
    else:
        d['hubo_problema'] = _a_booleano(d['hubo_problema'])
    if validaciones is not None and len(validaciones):
        v = _a_booleano(validaciones.set_index('lote_id')['hubo_problema'])
        traidos = d['lote_id'].map(v)
        # Un lote_id del archivo de validaciones que NO esta en esta ronda se
        # descartaba en silencio: un archivo entero podia evaporarse y el informe
        # solo decia "Pendientes: N".
        ajenos = sorted(set(v.index.astype(str)) - set(d['lote_id'].astype(str)))
        if ajenos:
            print('   [aviso] %d validacion(es) no corresponden a la ronda %s y se '
                  'descartan: %s' % (len(ajenos), ronda, ', '.join(ajenos[:8])))
        d['hubo_problema'] = traidos.astype('boolean')

    ruta = _ruta(base, sitio)
    if os.path.exists(ruta):
        viejo = pd.read_csv(ruta)
        # NO se pierde lo ya registrado de esta ronda. Antes se reemplazaba la ronda
        # entera, asi que si el tecnico volvia en dos tandas la segunda BORRABA los
        # hallazgos de la primera. Medido: tanda 1 (L00,L01) + tanda 2 (L02,L03)
        # dejaba L00 y L01 en NaN. Ahora lo nuevo pisa donde tiene dato y lo viejo
        # sobrevive donde lo nuevo no lo trae.
        prev = viejo[viejo['ronda'].astype(str) == str(ronda)]
        if len(prev) and 'hubo_problema' in prev.columns:
            ya = _a_booleano(prev.set_index('lote_id')['hubo_problema'])
            ya = ya[~ya.index.duplicated(keep='last')]
            nuevo = d.set_index('lote_id')['hubo_problema']
            nuevo = nuevo[~nuevo.index.duplicated(keep='last')]
            comb = nuevo.combine_first(ya)
            d['hubo_problema'] = d['lote_id'].map(comb).astype('boolean')
        viejo = viejo[viejo['ronda'].astype(str) != str(ronda)]
        # Las columnas todas-NA se excluyen del concat en pandas viejo y eso cambia el
        # dtype del resultado; se alinean antes para que el acumulado sea estable.
        for c in set(viejo.columns) | set(d.columns):
            if c not in viejo:
                viejo[c] = pd.NA
            if c not in d:
                d[c] = pd.NA
        partes = [x for x in (viejo, d) if len(x)]
        d = pd.concat(partes, ignore_index=True) if partes else d
    os.makedirs(base, exist_ok=True)
    d.to_csv(ruta, index=False)
    return ruta, len(d)


def cargar(base, sitio):
    ruta = _ruta(base, sitio)
    if not os.path.exists(ruta):
        return pd.DataFrame()
    return pd.read_csv(ruta)


def agrupar(acum):
    """Junta las rondas en el formato que espera `validacion.evaluar`.

    Cada ronda es una muestra estratificada independiente. Al agrupar, el tamaño de
    cada estrato es la SUMA de sus tamaños por ronda: son unidades (lote, ronda)
    distintas, no el mismo lote contado de nuevo.
    """
    if acum.empty:
        return pd.DataFrame(), {}
    acum = acum.copy()
    # Se normaliza ANTES de filtrar: leido de CSV, `hubo_problema` puede venir como
    # 1.0/0.0 y la lista blanca de strings lo convertia todo en False sin avisar.
    acum['hubo_problema'] = _a_booleano(acum['hubo_problema'])
    d = acum[acum['hubo_problema'].notna()].copy()
    if d.empty:
        return pd.DataFrame(), {'rondas': acum['ronda'].nunique(), 'visitados': 0,
                                'pendientes': len(acum)}
    d['hubo_problema'] = d['hubo_problema'].astype(bool)
    # N por estrato = suma de los N de cada ronda (una fila por lote-ronda sorteado)
    porronda = (acum.groupby(['ronda', 'estrato'])['N_estrato'].first()
                .groupby('estrato').sum())
    d['N_estrato'] = d['estrato'].map(porronda)
    meta = {'rondas': int(acum['ronda'].nunique()),
            'visitados': int(len(d)),
            'pendientes': int(acum['hubo_problema'].isna().sum()),
            'lotes_distintos': int(acum['lote_id'].nunique())}
    return d, meta


def informe(base, sitio):
    acum = cargar(base, sitio)
    if acum.empty:
        return 'Sin rondas acumuladas para %s.' % sitio
    d, meta = agrupar(acum)
    L = ['=' * 72, 'CAMPAÑA DE VALIDACION — %s' % sitio, '=' * 72, '',
         'Rondas acumuladas : %d' % meta.get('rondas', 0),
         'Visitas con dato  : %d' % meta.get('visitados', 0),
         'Pendientes        : %d (sorteados, el tecnico todavia no fue)'
         % meta.get('pendientes', 0), '']
    if d.empty:
        L.append('Todavia no volvio ninguna validacion: no hay nada que evaluar.')
        return '\n'.join(L)

    alert = d[d['estrato'].isin(('ATENCION', 'VIGILANCIA'))]
    L.append('Alertados visitados: %d  ->  %s' % (len(alert), _lectura_ic(len(alert))))
    L.append('')
    L.append(vl.informe(vl.evaluar(d), 'Acumulado de %d ronda(s)' % meta['rondas']))
    L.append('')
    L.append('OJO: la unidad es el (lote, ronda). Un lote alertado en dos rondas cuenta')
    L.append('dos veces — el sistema lo alerto dos veces. Lotes distintos: %d.'
             % meta.get('lotes_distintos', 0))
    return '\n'.join(L)


def _lectura_ic(n):
    """Cuanto vale el numero con ese n. Sin esto se leen 12 visitas como si fueran 60."""
    if n < 10:
        return 'IC ~±%d pp: NO alcanza para concluir nada' % (98 // max(n, 1) * 4 // 10 + 30)
    if n < 25:
        return 'IC ~±22 pp: sirve para descartar extremos, no para afirmar una cifra'
    if n < 45:
        return 'IC ~±16 pp: empieza a significar algo'
    return 'IC ~±13 pp o mejor: el numero es utilizable'


def main(argv=None):
    p = argparse.ArgumentParser(description='PIX ALERTA — campaña de validacion')
    p.add_argument('--sitio', default='HDS')
    p.add_argument('--base', default='salida')
    p.add_argument('--agregar', default=None, help='CSV de muestra de una ronda')
    p.add_argument('--validaciones', default=None, help='CSV con lote_id,hubo_problema')
    p.add_argument('--ronda', default=None, help='etiqueta de la ronda (def: fecha)')
    p.add_argument('--evaluar', action='store_true')
    a = p.parse_args(argv)

    if a.agregar:
        m = pd.read_csv(a.agregar)
        v = pd.read_csv(a.validaciones) if a.validaciones else None
        ruta, n = agregar(a.base, a.sitio, m, a.ronda, v)
        print('Ronda agregada. %d filas acumuladas -> %s' % (n, ruta))
    if a.evaluar or not a.agregar:
        print(informe(a.base, a.sitio))
    return 0


if __name__ == '__main__':
    sys.exit(main())
