"""Inspect target folders, dump exact filenames as JSON for review."""
import json
import os

DESKTOP = r"C:\Users\Usuario\Desktop"
TARGETS = [
    "Notas-Varios",
    "Scripts-Codigo",
    "GIS-Mapas",
    "Accesos-Directos",
    r"_VUELOS_DJI\DJI-FLIP-06-05-2026",
]

result = {}
for t in TARGETS:
    p = os.path.join(DESKTOP, t)
    if not os.path.isdir(p):
        result[t] = {"_error": "not a directory"}
        continue
    items = []
    for name in sorted(os.listdir(p)):
        full = os.path.join(p, name)
        kind = "dir" if os.path.isdir(full) else "file"
        items.append({"name": name, "kind": kind})
    result[t] = items

print(json.dumps(result, indent=2, ensure_ascii=False))
