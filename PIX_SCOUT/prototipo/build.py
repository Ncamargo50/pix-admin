# -*- coding: utf-8 -*-
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATADIR = os.path.join(HERE, '..', 'data')

CROPS = ['soya','trigo','maiz','sorgo','girasol','cana','pastura']
CROP_KEY = {'soya':'soya','trigo':'trigo','maiz':'maiz','sorgo':'sorgo',
            'girasol':'girasol','cana':'cana_de_azucar','pastura':'pastura'}
CROP_LABEL = {'soya':'Soja','trigo':'Trigo','maiz':'Maíz','sorgo':'Sorgo',
              'girasol':'Girasol','cana':'Caña de azúcar','pastura':'Pastura'}

FIELDS = ['id','categoria','nombre_comun','nombre_pt','nombre_cientifico',
          'severidad_potencial','signo','sintoma','confirmacion_campo',
          'confusiones','dd_tags','manejo_ref','umbral_accion','fuente_umbral','fotos']

def trim(fi):
    o={}
    for k in FIELDS:
        v=fi.get(k)
        if k=='fotos':
            v=[p for p in (v or []) if isinstance(p,dict)]  # only licensed photo objects
        o[k]=v
    return o

cultivos={}
n_f=n_foto=n_umb=0
for c in CROPS:
    d=json.load(open(os.path.join(DATADIR,c+'.json'),encoding='utf-8'))
    fichas=[trim(f) for f in d['fichas']]
    for f in fichas:
        n_f+=1; n_foto+=len(f['fotos'])
        if f.get('fuente_umbral'): n_umb+=1
    cultivos[CROP_KEY[c]]={'label':CROP_LABEL[c],'fichas':fichas}

# ---- example foci (fabricated, referencing real crops + Pixadvisor haciendas) ----
PATRON_LABEL={'foco':'foco denso','difuso':'difuso homogéneo','borde':'bordes/franjas','relieve':'bajos del relieve'}
focos=[
 dict(cultivo='trigo',lote='Talhão B14', hacienda='Serro Alto',      sev='muy_alta',score=94,area_ha=6.2, dist_m=180, patron='foco', estadio='Floración', punto='3/8',
      resumen='clúster rojo en floración, avanza rápido', mx=228,my=54, coord='-24.9871, -49.8123'),
 dict(cultivo='soya', lote='Bloque 2-L07',hacienda='Serro Alto',      sev='alta',   score=81,area_ha=11.4,dist_m=430, patron='difuso', estadio='Vegetativo', punto='5/12',
      resumen='amarillamiento amplio en la loma seca', mx=96,my=88, coord='-24.9910, -49.8007'),
 dict(cultivo='cana', lote='Lote 41',     hacienda='Hacienda del Señor',sev='alta',  score=77,area_ha=8.9, dist_m=1240,patron='foco', estadio='Vegetativo', punto='2/10',
      resumen='manchones de secamiento y colmos débiles', mx=176,my=104, coord='-17.8402, -63.1789'),
 dict(cultivo='maiz', lote='Pivot 3',     hacienda='São Francisco',    sev='media',  score=63,area_ha=4.1, dist_m=610, patron='borde', estadio='Vegetativo', punto='1/6',
      resumen='daño en cabeceras, plantas jóvenes dominadas', mx=272,my=118, coord='-13.2554, -46.8891'),
 dict(cultivo='pastura',lote='Piquete 9', hacienda='Campo Verde',      sev='media',  score=58,area_ha=22.0,dist_m=2050,patron='relieve', estadio='Vegetativo', punto='4/8',
      resumen='amarilleo en el bajo tras las lluvias', mx=48,my=118, coord='-14.9021, -55.4402'),
 dict(cultivo='girasol',lote='Lote 12',   hacienda='Santo Antonio',    sev='baja',   score=44,area_ha=3.3, dist_m=880, patron='difuso', estadio='Floración', punto='6/9',
      resumen='defoliación leve dispersa en floración', mx=132,my=40, coord='-22.4013, -54.7120'),
]
for f in focos:
    f['cultivoLabel']=CROP_LABEL[f['cultivo']]
    f['cultivo']=CROP_KEY[f['cultivo']]
    f['patronLabel']=PATRON_LABEL[f['patron']]

clave=json.load(open(os.path.join(DATADIR,'clave_dicotomica.json'),encoding='utf-8'))

data={'clave':clave,'cultivos':cultivos,'focos':focos,
      'stats':{'fichas':n_f,'umbrales':n_umb,'fotos':n_foto}}

tpl=open(os.path.join(HERE,'pix_scout_template.html'),encoding='utf-8').read()
out=tpl.replace('__DATA__', json.dumps(data,ensure_ascii=False))
open(os.path.join(HERE,'pix_scout.html'),'w',encoding='utf-8').write(out)
print('OK -> pix_scout.html  |  fichas=%d  umbrales=%d  fotos=%d  focos=%d'%(n_f,n_umb,n_foto,len(focos)))
