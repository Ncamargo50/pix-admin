# -*- coding: utf-8 -*-
"""Empaqueta el banco (7 cultivos + clave) en app/js/data.js para uso 100% offline."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
DATADIR = os.path.join(HERE, '..', 'data')

CROPS = ['soya','trigo','maiz','sorgo','girasol','cana','pastura']
CROP_KEY = {'soya':'soya','trigo':'trigo','maiz':'maiz','sorgo':'sorgo','girasol':'girasol','cana':'cana_de_azucar','pastura':'pastura'}
CROP_LABEL = {'soya':'Soja','trigo':'Trigo','maiz':'Maíz','sorgo':'Sorgo','girasol':'Girasol','cana':'Caña de azúcar','pastura':'Pastura'}
FIELDS = ['id','categoria','nombre_comun','nombre_pt','nombre_cientifico','severidad_potencial',
          'signo','sintoma','confirmacion_campo','confusiones','dd_tags','manejo_ref','umbral_accion','fuente_umbral','fotos']

def trim(fi):
    o={}
    for k in FIELDS:
        v=fi.get(k)
        if k=='fotos': v=[p for p in (v or []) if isinstance(p,dict)]
        o[k]=v
    return o

cultivos={}; n_f=n_foto=n_umb=0
for c in CROPS:
    d=json.load(open(os.path.join(DATADIR,c+'.json'),encoding='utf-8'))
    fichas=[trim(f) for f in d['fichas']]
    for f in fichas:
        n_f+=1; n_foto+=len(f['fotos'])
        if f.get('fuente_umbral'): n_umb+=1
    cultivos[CROP_KEY[c]]={'label':CROP_LABEL[c],'fichas':fichas}

clave=json.load(open(os.path.join(DATADIR,'clave_dicotomica.json'),encoding='utf-8'))

# Focos de ejemplo (en producción se sincronizan del pipeline de anomalías en la nube).
PATRON_LABEL={'foco':'foco denso','difuso':'difuso homogéneo','borde':'bordes/franjas','relieve':'bajos del relieve'}
focos=[
 dict(id='F-2607-14',cultivo='trigo',lote='Talhão B14',hacienda='Serro Alto',sev='muy_alta',score=94,area_ha=6.2,patron='foco',estadio='Floración',punto='3/8',resumen='clúster rojo en floración, avanza rápido',lat=-24.9871,lon=-49.8123),
 dict(id='F-2607-07',cultivo='soya',lote='Bloque 2-L07',hacienda='Serro Alto',sev='alta',score=81,area_ha=11.4,patron='difuso',estadio='Vegetativo',punto='5/12',resumen='amarillamiento amplio en la loma seca',lat=-24.9910,lon=-49.8007),
 dict(id='F-2607-41',cultivo='cana',lote='Lote 41',hacienda='Hacienda del Señor',sev='alta',score=77,area_ha=8.9,patron='foco',estadio='Vegetativo',punto='2/10',resumen='manchones de secamiento y colmos débiles',lat=-17.8402,lon=-63.1789),
 dict(id='F-2607-P3',cultivo='maiz',lote='Pivot 3',hacienda='São Francisco',sev='media',score=63,area_ha=4.1,patron='borde',estadio='Vegetativo',punto='1/6',resumen='daño en cabeceras, plantas jóvenes dominadas',lat=-13.2554,lon=-46.8891),
 dict(id='F-2607-P9',cultivo='pastura',lote='Piquete 9',hacienda='Campo Verde',sev='media',score=58,area_ha=22.0,patron='relieve',estadio='Vegetativo',punto='4/8',resumen='amarilleo en el bajo tras las lluvias',lat=-14.9021,lon=-55.4402),
 dict(id='F-2607-12',cultivo='girasol',lote='Lote 12',hacienda='Santo Antonio',sev='baja',score=44,area_ha=3.3,patron='difuso',estadio='Floración',punto='6/9',resumen='defoliación leve dispersa en floración',lat=-22.4013,lon=-54.7120),
]
for f in focos:
    f['cultivoLabel']=CROP_LABEL[f['cultivo']]
    f['cultivo']=CROP_KEY[f['cultivo']]
    f['patronLabel']=PATRON_LABEL[f['patron']]

data={'version':'1.0.0','clave':clave,'cultivos':cultivos,'focos':focos,
      'stats':{'fichas':n_f,'umbrales':n_umb,'fotos':n_foto,'cultivos':len(cultivos)}}

js='/* AUTO-GENERADO por build_data.py — NO editar a mano. */\nwindow.PIXDATA = '+json.dumps(data,ensure_ascii=False)+';\n'
open(os.path.join(HERE,'js','data.js'),'w',encoding='utf-8').write(js)
print('OK -> js/data.js | fichas=%d umbrales=%d fotos=%d cultivos=%d focos=%d'%(n_f,n_umb,n_foto,len(cultivos),len(focos)))
