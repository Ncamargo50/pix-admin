# -*- coding: utf-8 -*-
"""
Optimizacion de ruta de muestreo — Pixadvisor.

Motivacion (auditoria 2026-07-24): el recorrido de campo se hacia en el orden
del ranking satelital, que es un orden agronomico y geograficamente aleatorio.
Medido sobre los 20 lotes reales de Hacienda del Senor:

    inter-lote, orden por rank ....  81,6 km
    inter-lote, NN + 2-opt ........  19,9 km   (-76%)
    intra-lote, orden P1..P5 ......  26,3 km
    intra-lote, optimo ............  12,1 km   (-54%)

A velocidad de camino de hacienda y de caminata dentro de cana en pie, eso es
del orden de una jornada de campo completa de las 20.

Sin dependencias nuevas: solo numpy. Trabaja en coordenadas proyectadas
(UTM, metros) — no pasar lat/lon sin proyectar o las distancias no son metros.
"""
from __future__ import annotations

import numpy as np

__all__ = [
    "matriz_distancias",
    "longitud_ruta",
    "vecino_mas_cercano",
    "dos_opt",
    "resolver_ruta",
    "ordenar_puntos",
]


def matriz_distancias(coords: np.ndarray) -> np.ndarray:
    """Matriz euclidiana NxN a partir de un array Nx2 de coordenadas UTM."""
    coords = np.asarray(coords, dtype=float)
    d = coords[:, None, :] - coords[None, :, :]
    return np.sqrt((d ** 2).sum(axis=-1))


def longitud_ruta(orden: list[int], D: np.ndarray, cerrada: bool = False) -> float:
    """Longitud total en metros de un recorrido dado como lista de indices."""
    if len(orden) < 2:
        return 0.0
    total = float(sum(D[orden[i], orden[i + 1]] for i in range(len(orden) - 1)))
    if cerrada:
        total += float(D[orden[-1], orden[0]])
    return total


def vecino_mas_cercano(D: np.ndarray, inicio: int = 0) -> list[int]:
    """Construccion golosa: desde `inicio`, saltar siempre al mas cercano."""
    n = len(D)
    pendientes = set(range(n))
    pendientes.discard(inicio)
    orden = [inicio]
    actual = inicio
    while pendientes:
        siguiente = min(pendientes, key=lambda j: D[actual, j])
        orden.append(siguiente)
        pendientes.discard(siguiente)
        actual = siguiente
    return orden


def dos_opt(orden: list[int], D: np.ndarray, cerrada: bool = False,
            max_pasadas: int = 50) -> list[int]:
    """Refina un recorrido invirtiendo tramos mientras haya mejora.

    Mantiene fijo el primer nodo: el punto de partida (porton de entrada o
    punto de acceso al lote) no se elige, viene dado.
    """
    orden = list(orden)
    n = len(orden)
    if n < 4:
        return orden
    mejor = longitud_ruta(orden, D, cerrada)
    for _ in range(max_pasadas):
        mejoro = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                candidato = orden[:i] + orden[i:j + 1][::-1] + orden[j + 1:]
                largo = longitud_ruta(candidato, D, cerrada)
                if largo < mejor - 1e-9:
                    orden, mejor, mejoro = candidato, largo, True
        if not mejoro:
            break
    return orden


def _fuerza_bruta(D: np.ndarray, inicio: int) -> list[int]:
    """Optimo exacto por permutaciones. Solo para n pequeno (<= 8)."""
    from itertools import permutations
    resto = [i for i in range(len(D)) if i != inicio]
    mejor_orden, mejor_largo = None, float("inf")
    for perm in permutations(resto):
        cand = [inicio] + list(perm)
        largo = longitud_ruta(cand, D)
        if largo < mejor_largo:
            mejor_orden, mejor_largo = cand, largo
    return mejor_orden if mejor_orden else [inicio]


def resolver_ruta(coords: np.ndarray, inicio: int = 0,
                  cerrada: bool = False, exacto_hasta: int = 8) -> list[int]:
    """Devuelve el orden de visita optimizado como lista de indices.

    Con pocos puntos (<= `exacto_hasta`, tipico dentro de un lote) resuelve por
    fuerza bruta y el resultado es el optimo exacto. Con mas, usa vecino mas
    cercano refinado con 2-opt.
    """
    coords = np.asarray(coords, dtype=float)
    n = len(coords)
    if n <= 1:
        return list(range(n))
    D = matriz_distancias(coords)
    if n <= exacto_hasta and not cerrada:
        return _fuerza_bruta(D, inicio)
    return dos_opt(vecino_mas_cercano(D, inicio), D, cerrada)


def ordenar_puntos(coords: np.ndarray, acceso: tuple[float, float] | None = None,
                   cerrada: bool = False) -> tuple[list[int], float, float]:
    """Ordena puntos de muestreo por recorrido y reporta el ahorro.

    `acceso` es el punto por el que se entra (porton de la hacienda o borde del
    lote); si se da, el recorrido arranca por el punto mas cercano a el. Eso
    importa: el mejor recorrido depende de por donde se entra.

    Devuelve (orden, metros_originales, metros_optimizados) — el par de
    distancias permite registrar el ahorro real en el log y en el plan.
    """
    coords = np.asarray(coords, dtype=float)
    n = len(coords)
    if n <= 1:
        return list(range(n)), 0.0, 0.0

    D = matriz_distancias(coords)
    original = longitud_ruta(list(range(n)), D, cerrada)

    inicio = 0
    if acceso is not None:
        d_acceso = np.sqrt(((coords - np.asarray(acceso, dtype=float)) ** 2).sum(axis=1))
        inicio = int(np.argmin(d_acceso))

    orden = resolver_ruta(coords, inicio=inicio, cerrada=cerrada)
    return orden, original, longitud_ruta(orden, D, cerrada)
