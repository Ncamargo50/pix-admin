"""Parse KMLs y genera GeoJSON + script GEE con coordenadas embebidas."""
import re, json, os, pathlib

HERE = pathlib.Path(__file__).parent
DESKTOP = pathlib.Path.home() / "Desktop"

def parse_kml_coords(kml_path):
    with open(kml_path, "r", encoding="utf-8") as f:
        xml = f.read()
    m = re.search(r"<coordinates>\s*(.*?)\s*</coordinates>", xml, re.DOTALL)
    if not m:
        raise ValueError(f"No <coordinates> found in {kml_path}")
    raw = m.group(1).strip()
    pts = []
    for tok in raw.split():
        parts = tok.split(",")
        if len(parts) >= 2:
            lon, lat = float(parts[0]), float(parts[1])
            pts.append([lon, lat])
    # cerrar anillo si no lo está
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts

def write_geojson(name, coords, out_path, props=None):
    geo = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": props or {"name": name},
            "geometry": {"type": "Polygon", "coordinates": [coords]}
        }]
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(geo, f, ensure_ascii=False, indent=2)

# 1) Parse ambos KMLs
santo_coords = parse_kml_coords(DESKTOP / "Faz. Santo Antonio.kml")
sa2_coords = parse_kml_coords(DESKTOP / "S.A-2.kml")

# 2) Escribir GeoJSON
out_dir = HERE / "boundaries"
write_geojson("Faz. Santo Antonio", santo_coords,
              out_dir / "santo_antonio.geojson",
              {"name": "Faz. Santo Antonio", "uso": "campo_a_clasificar"})
write_geojson("S.A-2 (Soya ref)", sa2_coords,
              out_dir / "sa2_soya_ref.geojson",
              {"name": "S.A-2", "uso": "firma_pura_soya", "cultivo": "soya"})

# 3) Formatear coordenadas para JavaScript (una lista larga)
def js_coords(pts):
    # formato: [[lon,lat],[lon,lat],...]
    inner = ",\n    ".join([f"[{lon:.7f},{lat:.7f}]" for lon, lat in pts])
    return "[\n    " + inner + "\n  ]"

santo_js = js_coords(santo_coords)
sa2_js = js_coords(sa2_coords)

print(f"Santo Antonio: {len(santo_coords)} vértices")
print(f"S.A-2:         {len(sa2_coords)} vértices")

# 4) Generar el script GEE
script = f"""// =============================================================================
// CLASIFICACIÓN MAÍZ vs SOYA — Faz. Santo Antonio (parceria)
// Periodo: 2026-01-01 → 2026-02-25
// Metodología: K-means (k=2) + asignación por firma de referencia de S.A-2
// Autor: Pixadvisor AP | Engine: Google Earth Engine
// =============================================================================

// --- 1. BOUNDARIES (embebidos desde KML) ------------------------------------
var santoAntonio = ee.Geometry.Polygon({santo_js});

var sa2Soya = ee.Geometry.Polygon({sa2_js});

// Buffer interno -15 m en AOI para evitar píxeles de borde (efecto de mezcla)
var aoi       = santoAntonio.buffer(-15);
var soyaPure  = sa2Soya.buffer(-15);

Map.centerObject(aoi, 15);
Map.addLayer(santoAntonio, {{color: 'yellow'}}, '1. Santo Antonio (AOI)');
Map.addLayer(sa2Soya,      {{color: 'cyan'}},   '2. S.A-2 (Ref. Soya pura)');

// --- 2. PARÁMETROS TEMPORALES -----------------------------------------------
var startDate = '2026-01-01';
var endDate   = '2026-02-26';   // end exclusive → incluye 25/02
var CLOUD_MAX = 30;              // % nubes máximo por escena

// --- 3. SENTINEL-2 SR + MÁSCARA SCL -----------------------------------------
function maskS2(img) {{
  var scl = img.select('SCL');
  //  3=cloud shadow, 8=cloud med, 9=cloud high, 10=cirrus, 11=snow
  var mask = scl.neq(3).and(scl.neq(8)).and(scl.neq(9))
                .and(scl.neq(10)).and(scl.neq(11));
  return img.updateMask(mask).divide(10000)
    .copyProperties(img, ['system:time_start']);
}}

var col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(santoAntonio.buffer(500))
  .filterDate(startDate, endDate)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CLOUD_MAX))
  .map(maskS2);

print('📡 Imágenes S-2 disponibles:', col.size());
print('📅 Fechas capturadas:',
      col.aggregate_array('system:time_start')
         .map(function(t){{ return ee.Date(t).format('YYYY-MM-dd'); }}));

// --- 4. ÍNDICES DE VEGETACIÓN ------------------------------------------------
function addIndices(img) {{
  var ndvi = img.normalizedDifference(['B8','B4']).rename('NDVI');
  var ndre = img.normalizedDifference(['B8','B5']).rename('NDRE');
  var ndmi = img.normalizedDifference(['B8A','B11']).rename('NDMI');
  var gndvi = img.normalizedDifference(['B8','B3']).rename('GNDVI');
  var evi = img.expression(
    '2.5*((NIR-RED)/(NIR+6*RED-7.5*BLUE+1))',
    {{NIR: img.select('B8'), RED: img.select('B4'), BLUE: img.select('B2')}}
  ).rename('EVI');
  var gcvi = img.expression('(NIR/GREEN)-1',
    {{NIR: img.select('B8'), GREEN: img.select('B3')}}
  ).rename('GCVI');
  return img.addBands([ndvi, ndre, ndmi, gndvi, evi, gcvi]);
}}

// --- 5. COMPUESTO MEDIANA (periodo completo) --------------------------------
var composite = col.map(addIndices).median();

// Bandas usadas en la clasificación (espectrales + índices)
var BANDS = ['B2','B3','B4','B5','B6','B7','B8','B8A','B11','B12',
             'NDVI','NDRE','NDMI','GNDVI','EVI','GCVI'];

var stack = composite.select(BANDS).clip(santoAntonio);

// --- 6. VISUALIZACIONES BASE -------------------------------------------------
Map.addLayer(stack, {{bands:['B4','B3','B2'], min:0.02, max:0.25}},
             '3. RGB Color Natural', false);
Map.addLayer(stack, {{bands:['B8','B4','B3'], min:0.02, max:0.45}},
             '4. Falso Color IR (veg roja)', false);
Map.addLayer(stack.select('NDVI'),
             {{min:0.3, max:0.9, palette:['#a50026','#fdae61','#66bd63','#006837']}},
             '5. NDVI mediana');
Map.addLayer(stack.select('NDRE'),
             {{min:0.1, max:0.5, palette:['#2c7bb6','#abd9e9','#ffffbf','#fdae61','#d7191c']}},
             '6. NDRE mediana', false);

// --- 7. FIRMA ESPECTRAL DE SOYA (desde S.A-2) -------------------------------
var soyaSignature = stack.reduceRegion({{
  reducer: ee.Reducer.mean(),
  geometry: soyaPure,
  scale: 10,
  maxPixels: 1e9
}});
print('🌱 Firma espectral SOYA (referencia S.A-2):', soyaSignature);

// --- 8. K-MEANS k=2 SOBRE SANTO ANTONIO -------------------------------------
var training = stack.sample({{
  region: aoi,
  scale: 10,
  numPixels: 5000,
  seed: 42,
  geometries: false
}});

var clusterer = ee.Clusterer.wekaKMeans({{
  nClusters: 2,
  init: 1,         // k-means++
  maxIterations: 30,
  seed: 42
}}).train(training);

var classified = stack.cluster(clusterer).rename('cluster');

// Firma media de cada cluster dentro del AOI
var sig0 = stack.updateMask(classified.eq(0)).reduceRegion({{
  reducer: ee.Reducer.mean(), geometry: aoi, scale: 10, maxPixels: 1e9
}});
var sig1 = stack.updateMask(classified.eq(1)).reduceRegion({{
  reducer: ee.Reducer.mean(), geometry: aoi, scale: 10, maxPixels: 1e9
}});

print('📊 Firma Cluster 0:', sig0);
print('📊 Firma Cluster 1:', sig1);

// --- 9. ASIGNACIÓN CLUSTER → CULTIVO (distancia a firma pura de soya) -------
// Uso evaluate() del lado cliente para decisión condicional y export final
soyaSignature.evaluate(function(soya) {{
  sig0.evaluate(function(c0) {{
    sig1.evaluate(function(c1) {{

      var dist0 = 0, dist1 = 0;
      BANDS.forEach(function(b) {{
        var s  = soya[b] || 0;
        var v0 = c0[b]   || 0;
        var v1 = c1[b]   || 0;
        dist0 += Math.pow(v0 - s, 2);
        dist1 += Math.pow(v1 - s, 2);
      }});
      dist0 = Math.sqrt(dist0);
      dist1 = Math.sqrt(dist1);

      var soyaC = dist0 < dist1 ? 0 : 1;   // cluster más parecido a soya
      var maizC = 1 - soyaC;

      print('📐 Distancia Cluster 0 → Soya:', dist0.toFixed(4));
      print('📐 Distancia Cluster 1 → Soya:', dist1.toFixed(4));
      print('✅ SOYA = Cluster ' + soyaC + '  |  🌽 MAÍZ = Cluster ' + maizC);

      // Remapear: 1=Soya, 2=Maíz
      var cropMap = classified.remap([soyaC, maizC], [1, 2]).rename('cultivo');

      // ---- VISUALIZACIÓN FINAL --------------------------------------------
      var cropViz = {{min:1, max:2, palette:['#2E7D32', '#FFB300']}};
      //                                      verde soya    ámbar maíz
      Map.addLayer(cropMap.clip(aoi), cropViz,
                   '🎯 CLASIFICACIÓN: Verde=Soya | Ámbar=Maíz');

      // ---- CÁLCULO DE ÁREAS (hectáreas) -----------------------------------
      var pixelArea = ee.Image.pixelArea().divide(10000);   // ha por pixel
      var areaImg   = pixelArea.addBands(cropMap);

      var stats = areaImg.reduceRegion({{
        reducer: ee.Reducer.sum().group({{groupField: 1, groupName: 'cultivo'}}),
        geometry: aoi,
        scale: 10,
        maxPixels: 1e10
      }});

      var totalHa = aoi.area(1).divide(10000);

      stats.evaluate(function(s) {{
        totalHa.evaluate(function(tot) {{
          var groups = s.groups || [];
          var soyaHa = 0, maizHa = 0;
          groups.forEach(function(g) {{
            if (g.cultivo === 1) soyaHa = g.sum;
            if (g.cultivo === 2) maizHa = g.sum;
          }});
          var sumHa = soyaHa + maizHa;
          print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
          print('🏞️  ÁREA TOTAL AOI:  ' + tot.toFixed(2)   + ' ha');
          print('🌱  SOYA:            ' + soyaHa.toFixed(2)+ ' ha  (' +
                (soyaHa/sumHa*100).toFixed(1) + '%)');
          print('🌽  MAÍZ:            ' + maizHa.toFixed(2)+ ' ha  (' +
                (maizHa/sumHa*100).toFixed(1) + '%)');
          print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        }});
      }});

      // ---- EXPORTS (Drive) ------------------------------------------------
      // 1) Raster GeoTIFF clasificado (EPSG:32722 UTM 22S)
      Export.image.toDrive({{
        image: cropMap.clip(aoi).toInt8(),
        description: 'SantoAntonio_Clasif_MaizSoya_raster',
        folder: 'GEE_Pixadvisor',
        fileNamePrefix: 'santo_antonio_clasificacion',
        region: aoi,
        scale: 10,
        crs: 'EPSG:32722',
        maxPixels: 1e10
      }});

      // 2) Polígonos vectoriales por cultivo (Shapefile)
      var vectors = cropMap.clip(aoi)
        .reduceToVectors({{
          geometry: aoi,
          scale: 10,
          maxPixels: 1e10,
          geometryType: 'polygon',
          eightConnected: false,
          labelProperty: 'cultivo',
          reducer: ee.Reducer.countEvery()
        }})
        // agregar área en ha como atributo
        .map(function(f) {{
          var ha = f.geometry().area(1).divide(10000);
          var tag = ee.Algorithms.If(ee.Number(f.get('cultivo')).eq(1),
                                     'Soya', 'Maiz');
          return f.set('area_ha', ha).set('cultivo_n', tag);
        }});

      Export.table.toDrive({{
        collection: vectors,
        description: 'SantoAntonio_Clasif_MaizSoya_vector',
        folder: 'GEE_Pixadvisor',
        fileNamePrefix: 'santo_antonio_poligonos',
        fileFormat: 'SHP'
      }});

      // 3) RGB del compuesto para reporte
      Export.image.toDrive({{
        image: stack.select(['B4','B3','B2']).clip(santoAntonio)
                    .multiply(10000).toInt16(),
        description: 'SantoAntonio_RGB_S2_compuesto',
        folder: 'GEE_Pixadvisor',
        fileNamePrefix: 'santo_antonio_rgb',
        region: santoAntonio,
        scale: 10,
        crs: 'EPSG:32722',
        maxPixels: 1e10
      }});

      print('💾 Exports listos en pestaña "Tasks" → click RUN para descargar a Drive.');
    }});
  }});
}});

// --- 10. LEYENDA EN MAPA -----------------------------------------------------
var legend = ui.Panel({{
  style: {{position:'bottom-right', padding:'8px 12px',
          backgroundColor:'rgba(255,255,255,0.92)'}}
}});
legend.add(ui.Label({{value:'Clasificación de Cultivos',
                    style:{{fontWeight:'bold', fontSize:'14px', margin:'0 0 6px 0'}}}}));
function row(color, text) {{
  return ui.Panel([
    ui.Label({{style:{{backgroundColor:color,padding:'8px',margin:'0 6px 0 0'}}}}),
    ui.Label({{value:text, style:{{margin:'2px 0'}}}})
  ], ui.Panel.Layout.Flow('horizontal'));
}}
legend.add(row('#2E7D32','Soya'));
legend.add(row('#FFB300','Maíz'));
Map.add(legend);
"""

script_path = HERE / "clasificacion_gee.js"
with open(script_path, "w", encoding="utf-8") as f:
    f.write(script)

print(f"\n✅ GeoJSONs -> {out_dir}")
print(f"✅ Script GEE -> {script_path}")
print(f"   Tamaño script: {len(script):,} chars")
