# -*- coding: utf-8 -*-
import ee, urllib.request, os
ee.Initialize()
mins=[233,329,217]; maxs=[1223,983,743]; GAMMA=1.10; SHARP=0.60; THR=35
PNG=os.path.join(os.path.expanduser('~'),'Desktop','AreaSerroAlto_FASTpreview.png')
coords=[[-59.09980870205587,-18.58884954766944],[-58.60695261617405,-18.66991438639186],
[-58.63656056535330,-18.23813443214794],[-59.15746155706938,-18.21358493934918],
[-59.09980870205587,-18.58884954766944]]
aoi=ee.Geometry.Polygon([coords])
s2sr=ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi).filterDate('2025-05-01','2026-06-25').filter(ee.Filter.calendarRange(5,9,'month'))
s2cl=ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(aoi).filterDate('2025-05-01','2026-06-25').filter(ee.Filter.calendarRange(5,9,'month'))
j=ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(primary=s2sr,secondary=s2cl,condition=ee.Filter.equals(leftField='system:index',rightField='system:index')))
def m(img):
    prb=ee.Image(img.get('s2cloudless')).select('probability'); scl=img.select('SCL')
    bad=prb.gt(THR).Or(scl.eq(3)).Or(scl.gte(8)).Or(scl.eq(1)).Or(scl.eq(0))
    return img.updateMask(bad.Not())
comp=j.map(m).select(['B4','B3','B2']).median().clip(aoi).toFloat()
minI=ee.Image.constant(mins).rename(['B4','B3','B2']); maxI=ee.Image.constant(maxs).rename(['B4','B3','B2'])
s=comp.subtract(minI).divide(maxI.subtract(minI)).clamp(0,1).pow(1.0/GAMMA)
b=s.convolve(ee.Kernel.gaussian(3,1.5,'pixels'))
final=s.add(s.subtract(b).multiply(SHARP)).clamp(0,1).multiply(255).toByte()
for dim in (1024,800,640):
    try:
        u=final.getThumbURL({'region':aoi,'dimensions':dim,'format':'png','min':0,'max':255})
        urllib.request.urlretrieve(u,PNG); print('PNG @%d ->'%dim,PNG,'%.0fKB'%(os.path.getsize(PNG)/1024)); break
    except Exception as e:
        print('  %d fallo %s'%(dim,repr(e)[:60]))
print('DONE')
