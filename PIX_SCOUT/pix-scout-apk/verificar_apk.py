# -*- coding: utf-8 -*-
"""Verificacion del APK compilado: se abre el paquete y se mira lo que hay adentro."""
import zipfile, re, json, sys

import os
APK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app/build/outputs/apk/release/app-release.apk')
z = zipfile.ZipFile(APK)
rd = lambda p: z.read(p).decode('utf-8')

cfg = rd('assets/js/config.js')
app = rd('assets/js/app.js')
gjs = rd('assets/js/geojson.js')
sw = rd('assets/sw.js')
html = rd('assets/index.html')
umb = rd('assets/js/umbral.js')
sto = rd('assets/js/store.js')

ok = []
def chk(nombre, cond, detalle=''):
    ok.append(bool(cond))
    print('  %-46s %s %s' % (nombre, 'OK' if cond else '<<< FALLA', detalle))

ver = re.search(r"APP_VERSION: '([^']+)'", cfg).group(1)
swv = re.search(r"CACHE = '([^']+)'", sw).group(1)
print('=== IDENTIDAD ===')
print('  APP_VERSION %s | service worker %s' % (ver, swv))
chk('cache-busters coherentes con la version', set(re.findall(r'\?v=([\d.]+)', html)) == {ver})

print()
print('=== SEGURIDAD DE CAMPO (los P0) ===')
chk('no cae a focos demo de otras haciendas', 'CFG.DEMO_FOCOS' in app and re.search(r'DEMO_FOCOS: false', cfg))
chk('geojson en el precache del SW', 'santo_antonio.geojson' in sw)
chk('el Banco resetea el wizard', app.count('wiz=null;') >= 2)
chk('severidad NO se inventa por posicion', 'SEVS[idx%SEVS.length]' not in gjs)
chk('score no colapsa con SI>1', '(1.2-si)/0.9' in gjs)
chk('cultivo sale del GeoJSON, no fijo a trigo', "cultivo:'trigo'" not in app and 'cultKey' in app)

print()
print('=== LAZO DE RETORNO ===')
chk('registro negativo "no encontre nada"', 'registrarSinHallazgo' in app)
chk('conteo con unidad', "id=\"cntu\"" in app or 'cntu' in app)
chk('acepta coma decimal', "replace(',','.')" in app)
chk('observacion', 'obsv' in app)
chk('guarda el estrato sin mostrarlo', 'estrato:' in app)
chk('marca el muestreo dirigido', app.count('dirigido_satelital') >= 2)

print()
print('=== UMBRAL MIP COMO CALCULO ===')
chk('modulo umbral.js presente', 'window.Umbral' in umb)
chk('declara comparable_con_mip', 'comparable_con_mip' in umb)
chk('el motor de umbral se usa en el guardado', 'Umbral' in app)

print()
print('=== MODO CIEGO (protocolo de validacion) ===')
chk('flag MODO_CIEGO en config', 'MODO_CIEGO' in cfg)
chk('oculta severidad en la app', 'const CIEGO' in app)
chk('oculta nivel/SI en el resumen', 'MODO_CIEGO' in gjs)

print()
print('=== OFFLINE ===')
chk('IndexedDB + cola de sync', 'indexedDB' in sto and 'syncNow' in sto)
mods = sorted(n.split('/')[-1] for n in z.namelist() if n.startswith('assets/js/') and n.endswith('.js'))
chk('todos los modulos js empaquetados (%d)' % len(mods), len(mods) >= 10, str(mods))
# build_data.py empaqueta las fichas DENTRO de data.js (no como json sueltos):
# es lo correcto para offline, un solo archivo en el precache.
dat = rd('assets/js/data.js')
fichas = dat.count('nombre_cientifico')
cultivos = len(re.findall(r'"(soya|trigo|maiz|sorgo|girasol|cana_de_azucar|pastura)"\s*:\s*\{', dat))
chk('banco de fichas empaquetado en data.js', fichas >= 120 and cultivos == 7,
    '%d fichas / %d cultivos' % (fichas, cultivos))
chk('tabla de umbrales empaquetada', 'umbrales' in dat)
gj = json.loads(rd('assets/data/santo_antonio.geojson'))
con_id = sum(1 for f in gj['features'] if f['properties'].get('id'))
per = sum(1 for f in gj['features'] if f['properties'].get('tipo') == 'perimetro')
chk('geojson con ids estables y perimetro', con_id == len(gj['features']) and per == 1,
    '%d/%d con id, %d perimetro' % (con_id, len(gj['features']), per))

print()
print('RESULTADO: %d/%d' % (sum(ok), len(ok)))
sys.exit(0 if all(ok) else 1)
