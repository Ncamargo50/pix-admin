/**
 * GEE Zones Engine — Google Earth Engine powered management zone generation.
 * Follows the gis-precision-agro SKILL methodology:
 *   - Multi-campaign temporal analysis (24 months)
 *   - Crop-specific vegetation indices
 *   - Terrain derivatives (DEM, TWI, flow, slope)
 *   - Weighted Composite Score → Percentile classification
 *
 * Produces the `satelliteData` object consumed by ZonesEngine.generateFromSatellite().
 *
 * @version 1.0.0
 */
class GEEZonesEngine {

  // ==================== CROP INDEX CONFIGURATIONS ====================

  /**
   * Crop-specific vegetation index weights.
   * Each category defines which Sentinel-2 indices to compute and their
   * contribution to the composite score. Terrain weights are shared.
   */
  static CROP_INDEX_CONFIGS = {
    cana: {
      label: 'Caña de Azúcar',
      icon: '🌾',
      indices: { NDRE: 0.25, RECI: 0.15, CIre: 0.10, EVI: 0.05, NDMI: 0.05 },
      description: 'NDRE dominante — sensible a clorofila y nitrógeno en red-edge'
    },
    soja: {
      label: 'Soja',
      icon: '🌱',
      indices: { NDVI: 0.25, NDRE: 0.20, SAVI: 0.10, GNDVI: 0.05, NDWI: 0.05 },
      description: 'NDVI + NDRE — ciclo corto con alta variación temporal'
    },
    maiz_sorgo: {
      label: 'Maíz / Sorgo',
      icon: '🌽',
      indices: { NDVI: 0.25, NDRE: 0.15, EVI: 0.10, LSWI: 0.05, CIre: 0.05 },
      description: 'NDVI + EVI — dosel denso, EVI corrige saturación'
    },
    girasol: {
      label: 'Girasol / Chía',
      icon: '🌻',
      indices: { NDVI: 0.20, NDRE: 0.20, EVI: 0.10, NDMI: 0.10 },
      description: 'Balance NDVI/NDRE — estrés hídrico con NDMI'
    },
    horticolas: {
      label: 'Tomate / Papa / Pimentón',
      icon: '🍅',
      indices: { NDVI: 0.20, GNDVI: 0.15, NDRE: 0.15, NDMI: 0.10 },
      description: 'GNDVI — parcelas pequeñas con suelo expuesto'
    },
    perennes: {
      label: 'Palta / Maracuyá / Frutales',
      icon: '🥑',
      indices: { NDVI: 0.20, GNDVI: 0.15, NDRE: 0.15, NDMI: 0.10, CIre: 0.05 },
      description: 'Multi-índice — vigor perenne + estrés hídrico'
    }
  };

  /**
   * Shared terrain-derived weights (sum = 0.40).
   * Applied identically regardless of crop type.
   */
  static TERRAIN_WEIGHTS = {
    stability:     0.15,
    twi_inv:       0.10,
    flow_inv:      0.05,
    slope_inv:     0.05,
    elevation_rel: 0.05,
    dist_drainage: 0.00  // absorbed into flow_inv for GEE pipeline
  };

  /** GEE initialization state */
  static _eeReady = false;
  static _eeInitPromise = null;

  // ==================== GEE AUTHENTICATION ====================

  /**
   * Initialize Google Earth Engine.
   * Tries service-account token endpoint first, falls back to OAuth popup.
   * @param {string} [tokenEndpoint] - URL to fetch short-lived GEE token
   * @returns {Promise<boolean>} true if ready
   */
  static async initGEE(tokenEndpoint) {
    if (this._eeReady) return true;
    if (this._eeInitPromise) return this._eeInitPromise;

    this._eeInitPromise = (async () => {
      try {
        // Check ee global is loaded
        if (typeof ee === 'undefined') {
          console.warn('GEEZonesEngine: ee.js not loaded, GEE unavailable');
          return false;
        }

        // Strategy 1: Service account token endpoint
        if (tokenEndpoint) {
          try {
            const resp = await fetch(tokenEndpoint);
            if (resp.ok) {
              const { access_token, project } = await resp.json();
              ee.data.setAuthToken('', 'Bearer', access_token, 3600, [], null, false);
              await new Promise((resolve, reject) => {
                ee.initialize(project || null, null, resolve, reject);
              });
              this._eeReady = true;
              console.log('GEEZonesEngine: Initialized via service account token');
              return true;
            }
          } catch (e) {
            console.warn('GEEZonesEngine: Token endpoint failed, trying OAuth...', e.message);
          }
        }

        // Strategy 2: OAuth popup (development)
        try {
          await new Promise((resolve, reject) => {
            ee.data.authenticateViaPopup(() => {
              ee.initialize(null, null, resolve, reject);
            }, reject);
          });
          this._eeReady = true;
          console.log('GEEZonesEngine: Initialized via OAuth popup');
          return true;
        } catch (e) {
          console.warn('GEEZonesEngine: OAuth failed:', e.message);
          return false;
        }
      } catch (e) {
        console.error('GEEZonesEngine: Init failed:', e);
        return false;
      }
    })();

    return this._eeInitPromise;
  }

  // ==================== INDEX COMPUTATION (GEE) ====================

  /**
   * Compute a vegetation index on a Sentinel-2 SR image.
   * @param {ee.Image} img - S2 SR image with bands B2-B12
   * @param {string} name - Index name (NDVI, NDRE, EVI, SAVI, GNDVI, NDMI, NDWI, LSWI, RECI, CIre)
   * @returns {ee.Image} Single-band image named after the index
   */
  static _computeIndex(img, name) {
    const formulas = {
      NDVI:  () => img.normalizedDifference(['B8', 'B4']).rename(name),
      NDRE:  () => img.normalizedDifference(['B8', 'B5']).rename(name),
      EVI:   () => img.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
        { NIR: img.select('B8'), RED: img.select('B4'), BLUE: img.select('B2') }
      ).rename(name),
      SAVI:  () => img.expression(
        '1.5 * ((NIR - RED) / (NIR + RED + 0.5))',
        { NIR: img.select('B8'), RED: img.select('B4') }
      ).rename(name),
      GNDVI: () => img.normalizedDifference(['B8', 'B3']).rename(name),
      NDMI:  () => img.normalizedDifference(['B8A', 'B11']).rename(name),
      NDWI:  () => img.normalizedDifference(['B3', 'B8']).rename(name),
      LSWI:  () => img.normalizedDifference(['B8A', 'B11']).rename(name),  // same formula as NDMI
      RECI:  () => img.expression('NIR / RE1 - 1', { NIR: img.select('B8'), RE1: img.select('B5') }).rename(name),
      CIre:  () => img.expression('NIR / RE2 - 1', { NIR: img.select('B8'), RE2: img.select('B7') }).rename(name)
    };

    const fn = formulas[name];
    if (!fn) throw new Error(`Unknown index: ${name}`);
    return fn();
  }

  /**
   * Apply SCL cloud/shadow mask to a Sentinel-2 SR image.
   * Excludes: 3 (cloud shadow), 8 (cloud med), 9 (cloud high), 10 (cirrus), 11 (snow)
   */
  static _maskS2clouds(img) {
    const scl = img.select('SCL');
    const mask = scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11));
    return img.updateMask(mask);
  }

  // ==================== MAIN GEE PROCESSING PIPELINE ====================

  /**
   * Process a field polygon through the full GEE pipeline.
   *
   * @param {Array<[number,number]>} fieldPolygon - [[lng,lat], ...] boundary
   * @param {string} cropKey - Key from CROP_INDEX_CONFIGS
   * @param {number} areaHa - Field area in hectares
   * @param {Function} [onProgress] - (step, totalSteps, message) callback
   * @returns {Promise<Object>} satelliteData object for ZonesEngine
   */
  static async processField(fieldPolygon, cropKey, areaHa, onProgress) {
    if (!this._eeReady) throw new Error('GEE not initialized. Call initGEE() first.');

    const cropConfig = this.CROP_INDEX_CONFIGS[cropKey];
    if (!cropConfig) throw new Error(`Unknown crop: ${cropKey}`);

    const indexNames = Object.keys(cropConfig.indices);
    const progress = onProgress || (() => {});
    const STEPS = 8;

    // --- Step 1: Build geometry ---
    progress(1, STEPS, 'Configurando geometría del lote...');
    const coords = fieldPolygon.map(c => [c[0], c[1]]);  // ensure [lng, lat]
    if (coords[0][0] !== coords[coords.length - 1][0] || coords[0][1] !== coords[coords.length - 1][1]) {
      coords.push(coords[0]);  // close ring
    }
    const geometry = ee.Geometry.Polygon([coords]);
    const buffered = geometry.buffer(500);  // 500m buffer for context

    // Auto-scale resolution
    let scale = 10;
    if (areaHa > 500) scale = 30;
    else if (areaHa > 100) scale = 20;

    // --- Step 2: Query Sentinel-2 ---
    progress(2, STEPS, 'Consultando imágenes Sentinel-2 (24 meses)...');
    const now = ee.Date(Date.now());
    const start = now.advance(-24, 'month');

    let s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(geometry)
      .filterDate(start, now)
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));

    // Apply cloud mask
    s2 = s2.map(img => this._maskS2clouds(img));

    const count = await s2.size().getInfo();
    if (count < 4) {
      // Relax cloud filter if insufficient images
      s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(geometry)
        .filterDate(start, now)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
        .map(img => this._maskS2clouds(img));
    }

    // --- Step 3: Compute crop-specific indices ---
    progress(3, STEPS, `Calculando índices: ${indexNames.join(', ')}...`);

    const withIndices = s2.map(img => {
      let result = img;
      for (const idx of indexNames) {
        result = result.addBands(this._computeIndex(img, idx));
      }
      return result;
    });

    // --- Step 4: Create campaign composites (4 x 6-month periods) ---
    progress(4, STEPS, 'Generando composites multi-campaña...');

    const campaigns = [];
    for (let i = 0; i < 4; i++) {
      const campStart = now.advance(-(24 - i * 6), 'month');
      const campEnd = now.advance(-(18 - i * 6), 'month');
      const campCollection = withIndices.filterDate(campStart, campEnd);

      // Median composite per campaign for each index
      const composite = campCollection.select(indexNames).median().clip(geometry);
      campaigns.push(composite);
    }

    // Multi-campaign stack: median and stdDev across campaigns
    const campaignStack = ee.ImageCollection(campaigns);
    const medianComposite = campaignStack.median();
    const stdComposite = campaignStack.reduce(ee.Reducer.stdDev());

    // Stability = 1 - normalized(stdDev)
    // We'll compute this after download

    // --- Step 5: DEM and terrain derivatives ---
    progress(5, STEPS, 'Procesando DEM y derivados del terreno...');

    const dem = ee.Image('COPERNICUS/DEM/GLO30').select('DEM').clip(geometry);
    const terrain = ee.Terrain.products(dem);
    const slope = terrain.select('slope');
    const aspect = terrain.select('aspect');

    // TWI approximation in GEE
    // Using slope-only approximation: TWI = ln(1000 / tan(slope_rad + 0.001))
    const slopeRad = slope.multiply(Math.PI / 180);
    const twi = slopeRad.add(0.001).tan().pow(-1).multiply(1000).log().rename('TWI');

    // Flow accumulation from MERIT Hydro (if available)
    let flowAcc;
    try {
      flowAcc = ee.Image('MERIT/Hydro/v1_0_1').select('upa').clip(geometry).rename('flow');
    } catch (e) {
      // Fallback: use inverted slope as proxy for flow tendency
      flowAcc = slope.multiply(-1).add(slope.reduceRegion({
        reducer: ee.Reducer.max(), geometry, scale: 30
      }).values().get(0)).rename('flow');
    }

    // --- Step 6: Stack all layers and download ---
    progress(6, STEPS, 'Descargando datos del servidor GEE...');

    // Build multi-band image for download
    const allBands = medianComposite
      .addBands(stdComposite)
      .addBands(dem.rename('DEM'))
      .addBands(slope.rename('slope'))
      .addBands(twi)
      .addBands(flowAcc);

    // Download as 2D arrays via sampleRectangle
    const sampled = await allBands
      .reproject({ crs: 'EPSG:4326', scale })
      .sampleRectangle({ region: geometry, defaultValue: 0 })
      .getInfo();

    // Also download each campaign separately for temporal analysis
    progress(7, STEPS, 'Procesando campañas temporales...');
    const campaignGrids = {};
    for (const idx of indexNames) {
      campaignGrids[idx] = [];
    }

    for (let i = 0; i < campaigns.length; i++) {
      const campSampled = await campaigns[i]
        .reproject({ crs: 'EPSG:4326', scale })
        .sampleRectangle({ region: geometry, defaultValue: 0 })
        .getInfo();

      for (const idx of indexNames) {
        const band = campSampled.properties[idx];
        if (band) {
          campaignGrids[idx].push(band);
        }
      }
    }

    // --- Step 7: Format for ZonesEngine ---
    progress(8, STEPS, 'Formateando datos para motor de zonas...');

    const props = sampled.properties;

    // Extract primary index campaigns (use first 3 indices as NDVI/NDRE/EVI slots)
    // ZonesEngine expects: ndviCampaigns, ndreCampaigns, eviCampaigns
    const primaryIdx = indexNames[0];  // Highest weight index
    const secondIdx = indexNames[1] || indexNames[0];
    const thirdIdx = indexNames[2] || indexNames[0];

    const satelliteData = {
      ndviCampaigns: campaignGrids[primaryIdx] || [props[primaryIdx]],
      ndreCampaigns: campaignGrids[secondIdx] || [props[secondIdx]],
      eviCampaigns:  campaignGrids[thirdIdx] || [props[thirdIdx]],
      dem:           props['DEM'],
      cellSize:      scale
    };

    // Build custom weights mapping the crop indices to the composite score formula
    // ZonesEngine.COMPOSITE_WEIGHTS maps: ndvi, ndre, ndvi_stability, twi, flow_inv, slope_inv, rel_elevation, drain_distance
    const compositeWeights = {
      ndvi:           cropConfig.indices[primaryIdx] || 0.25,
      ndre:           cropConfig.indices[secondIdx] || 0.15,
      ndvi_stability: this.TERRAIN_WEIGHTS.stability,
      twi:            this.TERRAIN_WEIGHTS.twi_inv,
      flow_inv:       this.TERRAIN_WEIGHTS.flow_inv,
      slope_inv:      this.TERRAIN_WEIGHTS.slope_inv,
      rel_elevation:  this.TERRAIN_WEIGHTS.elevation_rel,
      drain_distance: 0.10  // remaining weight to drain/flow
    };

    // Normalize weights to sum to 1.0
    const wSum = Object.values(compositeWeights).reduce((a, b) => a + b, 0);
    for (const k in compositeWeights) {
      compositeWeights[k] = compositeWeights[k] / wSum;
    }

    return {
      satelliteData,
      compositeWeights,
      cropKey,
      cropConfig,
      scale,
      imageCount: count,
      campaignCount: campaigns.length,
      indexNames
    };
  }

  // ==================== DEMO/FALLBACK MODE ====================

  /**
   * Generate demo satellite data when GEE is unavailable.
   * Uses existing ZonesEngine.simulateSatelliteData() for synthetic data.
   *
   * @param {Object} bounds - { minLat, maxLat, minLng, maxLng }
   * @param {Array<[number,number]>} boundary - polygon [[lat,lng],...]
   * @param {number} areaHa
   * @param {string} cropKey
   * @returns {Object} Same structure as processField() return
   */
  static processFieldDemo(bounds, boundary, areaHa, cropKey) {
    const cropConfig = this.CROP_INDEX_CONFIGS[cropKey];
    if (!cropConfig) throw new Error(`Unknown crop: ${cropKey}`);

    // Use existing simulation
    const satelliteData = ZonesEngine.simulateSatelliteData(bounds, boundary, areaHa, {
      numCampaigns: 4,
      resolution: areaHa > 100 ? 20 : 10
    });

    const indexNames = Object.keys(cropConfig.indices);
    const primaryIdx = indexNames[0];
    const secondIdx = indexNames[1] || indexNames[0];

    const compositeWeights = {
      ndvi:           cropConfig.indices[primaryIdx] || 0.25,
      ndre:           cropConfig.indices[secondIdx] || 0.15,
      ndvi_stability: this.TERRAIN_WEIGHTS.stability,
      twi:            this.TERRAIN_WEIGHTS.twi_inv,
      flow_inv:       this.TERRAIN_WEIGHTS.flow_inv,
      slope_inv:      this.TERRAIN_WEIGHTS.slope_inv,
      rel_elevation:  this.TERRAIN_WEIGHTS.elevation_rel,
      drain_distance: 0.10
    };

    const wSum = Object.values(compositeWeights).reduce((a, b) => a + b, 0);
    for (const k in compositeWeights) {
      compositeWeights[k] = compositeWeights[k] / wSum;
    }

    return {
      satelliteData,
      compositeWeights,
      cropKey,
      cropConfig,
      scale: satelliteData.cellSize || 10,
      imageCount: 0,
      campaignCount: 4,
      indexNames,
      isDemo: true
    };
  }

  // ==================== UTILITY ====================

  /**
   * Get the full weight breakdown for a crop, including terrain.
   * Useful for displaying in the UI.
   * @param {string} cropKey
   * @returns {Array<{name: string, weight: number, source: string}>}
   */
  static getWeightBreakdown(cropKey) {
    const cropConfig = this.CROP_INDEX_CONFIGS[cropKey];
    if (!cropConfig) return [];

    const breakdown = [];

    // Vegetation indices
    for (const [name, weight] of Object.entries(cropConfig.indices)) {
      breakdown.push({ name, weight: Math.round(weight * 100), source: 'vegetation' });
    }

    // Terrain
    breakdown.push({ name: 'Estabilidad temporal', weight: Math.round(this.TERRAIN_WEIGHTS.stability * 100), source: 'terrain' });
    breakdown.push({ name: 'TWI (humedad)', weight: Math.round(this.TERRAIN_WEIGHTS.twi_inv * 100), source: 'terrain' });
    breakdown.push({ name: 'Flujo agua', weight: Math.round(this.TERRAIN_WEIGHTS.flow_inv * 100), source: 'terrain' });
    breakdown.push({ name: 'Pendiente', weight: Math.round(this.TERRAIN_WEIGHTS.slope_inv * 100), source: 'terrain' });
    breakdown.push({ name: 'Elevación relativa', weight: Math.round(this.TERRAIN_WEIGHTS.elevation_rel * 100), source: 'terrain' });

    return breakdown;
  }

  /**
   * Compute bounds from polygon for ZonesEngine compatibility.
   * @param {Array<[number,number]>} polygon - [[lng,lat],...] or [[lat,lng],...]
   * @param {boolean} isLngLat - true if [lng,lat] format
   * @returns {{ minLat, maxLat, minLng, maxLng }}
   */
  static boundsFromPolygon(polygon, isLngLat = true) {
    let minLat = Infinity, maxLat = -Infinity;
    let minLng = Infinity, maxLng = -Infinity;

    for (const pt of polygon) {
      const lng = isLngLat ? pt[0] : pt[1];
      const lat = isLngLat ? pt[1] : pt[0];
      if (lat < minLat) minLat = lat;
      if (lat > maxLat) maxLat = lat;
      if (lng < minLng) minLng = lng;
      if (lng > maxLng) maxLng = lng;
    }

    return { minLat, maxLat, minLng, maxLng };
  }
}
