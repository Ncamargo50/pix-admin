// =============================================================================
// POC Field Boundary - Tool A: SNIC + Canny en Google Earth Engine
// AOI: Faz. Santo Antonio (Parana, Brasil) - 137.05 ha truth
// Periodo: 2026-01-01 a 2026-02-25 (mismo que clasificacion existente)
// =============================================================================
// Pegar este script completo en https://code.earthengine.google.com/
// Pre-requisito: estar logueado con cuenta GEE de Pixadvisor.
// =============================================================================

// --- 1. AOI con buffer 165m (output/santo_antonio_bbox.txt FORMATO 2) -----
var aoiBbox = ee.Geometry.Rectangle([-50.663396, -23.501477, -50.653555, -23.472671]);
// Truth Santo Antonio embebido (simplificado, tolerance 5m, vertices de 01_prepare_aoi.py)
var aoi_part_1 = ee.Geometry.Polygon([[[-50.65678700425402,-23.49610697269555],[-50.6567744023073,-23.496201537869222],[-50.65602683562762,-23.496070656241006],[-50.655920538050424,-23.496136084160774],[-50.65590744075277,-23.49649408158203],[-50.656547184081035,-23.496702959482327],[-50.65660083219876,-23.496814789795383],[-50.65650426803925,-23.49683332871347],[-50.65644753781723,-23.49696169222971],[-50.65589479169222,-23.496778492853252],[-50.65583663094045,-23.49811501917952],[-50.6608903956098,-23.49994950576059],[-50.660979505651596,-23.495887032414775],[-50.659958781565294,-23.496216497369634],[-50.6594238242019,-23.496098577337328],[-50.65915292134764,-23.49614039382674],[-50.65865393414714,-23.495976056834273],[-50.65723714295704,-23.495742373600695],[-50.65594941746928,-23.495150246778632],[-50.65596988549244,-23.495753011517113],[-50.65664374379797,-23.49595504434588],[-50.65678700425402,-23.49610697269555]]]);
var aoi_part_2 = ee.Geometry.Polygon([[[-50.65505464675906,-23.480869113559972],[-50.65656225863661,-23.48125993196528],[-50.65602821571603,-23.494703500583263],[-50.65663569720366,-23.494555048067355],[-50.657440359144616,-23.494594406215892],[-50.657941932916394,-23.494911726274818],[-50.658393864552316,-23.49497652801831],[-50.658782220531876,-23.49532156051083],[-50.65926732899524,-23.495524344366988],[-50.66005781372803,-23.495666250828936],[-50.660591975656104,-23.495534073360925],[-50.66091797927519,-23.49537910608215],[-50.661069413595285,-23.494633774985495],[-50.66165718813816,-23.480698105550694],[-50.66189603893997,-23.47677330416047],[-50.66165101013743,-23.476728993490635],[-50.661538357155415,-23.47653955988519],[-50.661404246358615,-23.47654694025398],[-50.66069614359693,-23.477083259320825],[-50.660358679027226,-23.477587093894858],[-50.660065618540244,-23.478644645097145],[-50.66007118871581,-23.47947857589669],[-50.65996745107739,-23.48006788707796],[-50.66057847924624,-23.480533066922238],[-50.66053580624596,-23.481033861795687],[-50.660408110969954,-23.48144386716918],[-50.66005745843128,-23.48199618560982],[-50.660118760253646,-23.482255825743536],[-50.660006738073136,-23.482334788957026],[-50.65969302725698,-23.482285668202504],[-50.659170849258246,-23.48234265088909],[-50.65847124892549,-23.48268473205356],[-50.658398740332885,-23.482772898066667],[-50.658416349343284,-23.48313193457205],[-50.65807905040498,-23.483365398487514],[-50.657605721530686,-23.483403678365818],[-50.65738668156017,-23.483275047738932],[-50.65725257119519,-23.482999520475953],[-50.65733572016948,-23.48278795501017],[-50.65788602725114,-23.48227316546221],[-50.657745544066024,-23.481889356118707],[-50.65773731822333,-23.48124656075008],[-50.657878330902506,-23.481185327765257],[-50.65812016035034,-23.480855100942055],[-50.658608683451725,-23.48055868035885],[-50.65972389686992,-23.47950063148636],[-50.660045072560315,-23.47777973968991],[-50.660368878023874,-23.477180996963234],[-50.661117169353915,-23.476529883208965],[-50.66172350802497,-23.476304505331345],[-50.661820232644594,-23.47616567453452],[-50.66177142224019,-23.47592623644612],[-50.66131071848864,-23.475304196207524],[-50.660846695628685,-23.47492040404446],[-50.660511419478645,-23.47492286390812],[-50.659865339364444,-23.474664917374028],[-50.65946321833268,-23.474392073001443],[-50.6588815222634,-23.47423558934805],[-50.65867691207236,-23.47422255682789],[-50.658394592912764,-23.47436456600127],[-50.658056761109684,-23.47487141128019],[-50.657656580149265,-23.474866338255662],[-50.65726706052412,-23.474811862225685],[-50.65704314359634,-23.47461267853385],[-50.65689602627125,-23.47466971163],[-50.65621241968106,-23.47452742118951],[-50.65542762221696,-23.474171119968865],[-50.65505464675906,-23.480869113559972]]]);
var aoiTruth = ee.FeatureCollection([
  ee.Feature(aoi_part_1, {part:1}),
  ee.Feature(aoi_part_2, {part:2})
]);

Map.centerObject(aoiBbox, 15);

// --- 2. Sentinel-2 SR composite (perido contrato) --------------------------
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(aoiBbox)
  .filterDate('2026-01-01', '2026-02-25')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
  .map(function(img) {
    var scl = img.select('SCL');
    // 4=veg, 5=bare, 6=water, 11=snow ; 3=shadow, 8/9/10=clouds, 1=defective
    var clearMask = scl.eq(4).or(scl.eq(5)).or(scl.eq(6)).or(scl.eq(11));
    return img.updateMask(clearMask).divide(10000)
      .copyProperties(img, ['system:time_start']);
  });
print('S2 scenes count', s2.size());

var composite = s2.median().clip(aoiBbox);
var rgb = composite.select(['B4','B3','B2']);

Map.addLayer(rgb, {min:0.02, max:0.25, gamma:1.2}, 'S2 RGB median 2026-01/02');
Map.addLayer(aoiTruth, {color:'yellow'}, 'Truth (Santo Antonio shp)');

// --- 3. Calcular indices auxiliares para edges ------------------------------
var ndvi = composite.normalizedDifference(['B8','B4']).rename('NDVI');
var ndwi = composite.normalizedDifference(['B3','B8']).rename('NDWI');
// Brilho como referencia textural
var brightness = composite.select(['B4','B3','B2','B8']).reduce(ee.Reducer.mean());
var stack = composite.select(['B2','B3','B4','B8','B11']).addBands([ndvi, brightness.rename('BR')]);

// --- 4. SNIC super-pixels ---------------------------------------------------
// SNIC agrupa pixels similares; size=12 -> super-pixels ~120m de lado en S2 10m
var snic = ee.Algorithms.Image.Segmentation.SNIC({
  image: stack,
  size: 12,
  compactness: 0.5,
  connectivity: 8,
  neighborhoodSize: 256,
  seeds: null
});
var clusters = snic.select('clusters');
var snicMean = snic.select(['B2_mean','B3_mean','B4_mean','B8_mean','NDVI_mean','BR_mean']);

Map.addLayer(clusters.randomVisualizer(), {}, 'SNIC clusters', false);

// --- 5. Canny Edge Detection sobre cada banda ------------------------------
function cannyOn(band) {
  var b = snicMean.select(band);
  var edges = ee.Algorithms.CannyEdgeDetector({
    image: b, threshold: 0.04, sigma: 1.0
  });
  return edges.gt(0).rename(band + '_edge');
}
var edges = ee.Image.cat([
  cannyOn('B4_mean'),
  cannyOn('B3_mean'),
  cannyOn('B2_mean'),
  cannyOn('B8_mean'),
  cannyOn('NDVI_mean')
]);
// Edge consensus: pixel es borde si lo es en >= 2 bandas
var edgeCount = edges.reduce(ee.Reducer.sum());
var edgeMask = edgeCount.gte(2).selfMask();

Map.addLayer(edgeMask, {palette:'red'}, 'Canny edges (>=2 bandas)');

// --- 6. Vectorizar regiones (no edges) -> poligonos de campo ---------------
// Mascara de "interior de campo": NOT edge AND NDVI razonable de cultivo
var inField = edgeCount.lt(2).and(ndvi.gt(0.25));
var fieldVec = inField.selfMask().reduceToVectors({
  geometry: aoiBbox,
  scale: 10,
  geometryType: 'polygon',
  eightConnected: true,
  labelProperty: 'field_id',
  reducer: ee.Reducer.mean(),
  maxPixels: 1e10
});

// Filtro por area: descarta poligonos < 0.5 ha (5000 m2)
fieldVec = fieldVec.map(function(f){
  return f.set('area_ha', f.geometry().area(1).divide(10000));
}).filter(ee.Filter.gte('area_ha', 0.5));

print('Campos detectados', fieldVec.size());
print('Suma area detectada (ha)', fieldVec.aggregate_sum('area_ha'));

Map.addLayer(fieldVec, {color:'cyan'}, 'Lotes detectados (SNIC+Canny)');

// --- 7. Comparacion IoU (bounding-box level) -------------------------------
var truthGeom = aoiTruth.geometry();
var detectedGeom = fieldVec.geometry();
var inter = truthGeom.intersection(detectedGeom, 1).area(1);
var union = truthGeom.union(detectedGeom, 1).area(1);
var iou = inter.divide(union);
print('IoU truth vs detection', iou);

// --- 8. EXPORT a Drive (descomentar y correr en tab "Tasks") ---------------
// Export.table.toDrive({
//   collection: fieldVec,
//   description: 'POC_SantoAntonio_SNIC_Canny',
//   fileFormat: 'GeoJSON',
//   folder: 'PIXADVISOR_POC'
// });
// Export.image.toDrive({
//   image: rgb.multiply(255).uint8(),
//   description: 'POC_SantoAntonio_S2_RGB',
//   region: aoiBbox,
//   scale: 10,
//   maxPixels: 1e9
// });

// =============================================================================
// Como usar:
// 1. Pegar este script completo en code.earthengine.google.com
// 2. Click "Run" - aparece RGB Sentinel-2 + edges + lotes detectados
// 3. Verificar visualmente vs poligono amarillo (truth)
// 4. Descomentar bloque export para descargar GeoJSON a Drive
// 5. Bajar GeoJSON, correr: python 04_compare_iou.py output/<archivo>.geojson
// =============================================================================
