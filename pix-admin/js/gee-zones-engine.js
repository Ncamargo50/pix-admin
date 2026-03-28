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
  /**
   * Crop-specific vegetation indices for GEE computation.
   * These indices are used to compute a RANKING PERCENTIL per campaign.
   * The ranking is then fed into the Score Compuesto via PRODUCTION_SCORE_WEIGHTS.
   *
   * CAÑA indices match production v4.1 exactly (7 indices).
   */
  static CROP_INDEX_CONFIGS = {
    cana: {
      label: 'Caña de Azúcar',
      icon: '🌾',
      indices: { NDRE: 0.25, RECI: 0.15, CIre: 0.10, IRECI: 0.08, EVI: 0.07, NDMI: 0.05, MSI: 0.05 },
      fenologia: 'ELONGACION',
      ventana: { mesInicio: 5, mesFin: 9 },  // Mayo-Septiembre
      description: '7 indices produccion v4.1 — NDRE primario, etapa elongacion (mayo-sept)'
    },
    soja: {
      label: 'Soja',
      icon: '🌱',
      indices: { NDVI: 0.25, NDRE: 0.15, SAVI: 0.10, GNDVI: 0.05, NDWI: 0.05 },
      fenologia: 'R3_R6',
      ventana: { mesInicio: 1, mesFin: 4 },  // Enero-Abril (llenado)
      description: 'NDVI + NDRE — ciclo corto, ventana reproductiva'
    },
    maiz_sorgo: {
      label: 'Maíz / Sorgo',
      icon: '🌽',
      indices: { kNDVI: 0.20, NDRE: 0.15, EVI: 0.10, LSWI: 0.10, CIre: 0.05 },
      fenologia: 'VT_R1',
      ventana: { mesInicio: 1, mesFin: 4 },  // Enero-Abril (floración-llenado)
      description: 'kNDVI anti-saturación + EVI — dosel denso'
    },
    girasol: {
      label: 'Girasol / Chía',
      icon: '🌻',
      indices: { NDVI: 0.20, NDRE: 0.20, EVI: 0.10, NDMI: 0.10 },
      fenologia: 'R1_R4',
      ventana: { mesInicio: 2, mesFin: 5 },
      description: 'Balance NDVI/NDRE — estrés hídrico con NDMI'
    },
    horticolas: {
      label: 'Tomate / Papa / Pimentón',
      icon: '🍅',
      indices: { NDVI: 0.20, GNDVI: 0.15, NDRE: 0.15, NDMI: 0.10 },
      fenologia: 'FRUCTIFICACION',
      ventana: { mesInicio: 3, mesFin: 8 },
      description: 'GNDVI — parcelas pequeñas con suelo expuesto'
    },
    perennes: {
      label: 'Palta / Maracuyá / Frutales',
      icon: '🥑',
      indices: { NDVI: 0.20, GNDVI: 0.10, NDRE: 0.15, NDMI: 0.10, CIre: 0.05 },
      fenologia: 'VEGETATIVO',
      ventana: { mesInicio: 1, mesFin: 12 },  // Todo el año (perenne)
      description: 'Multi-índice — vigor perenne + estrés hídrico'
    }
  };

  /**
   * PRODUCTION SCORE WEIGHTS — Exact replication of v4.1 PESOS_SCORE.
   * These weights are applied to the Score Compuesto Ponderado, NOT to vegetation indices.
   * rank_medio/rank_std/rank_min come from multi-campaign ranking analysis.
   * Sum = 1.00
   */
  static PRODUCTION_SCORE_WEIGHTS = {
    ndvi_median:    0.40,  // rank_medio — stable productive potential (multi-year average)
    ndre_median:    0.20,  // rank_std — temporal stability (INVERTED: lower = more stable)
    ndvi_stability: 0.10,  // rank_min — worst-year security
    twi:            0.10,  // Topographic Wetness Index
    flow_inv:       0.06,  // Flow accumulation (INVERTED)
    slope_inv:      0.06,  // Slope (INVERTED)
    rel_elevation:  0.04,  // Relative elevation within field
    drain_distance: 0.04   // Distance to drainage lines
  };

  /** Production parameters */
  static CLOUD_MAX = 15;          // Primary cloud threshold (%)
  static CLOUD_FALLBACK_1 = 25;   // First fallback
  static CLOUD_FALLBACK_2 = 40;   // Second fallback
  static MIN_SCENES = 5;          // Minimum scenes per campaign
  static MIN_ZONE_AREA_HA = 1.5;  // Minimum zone area (ha)
  static ZONE_THRESHOLD_HA = 33;  // <=33ha→3 zones, >33ha→4 zones
  static MAX_ZONES = 4;           // Maximum absolute zone count

  /** GEE initialization state */
  static _eeReady = false;
  static _eeInitPromise = null;

  // ==================== GEE AUTHENTICATION ====================

  /** GEE JS client library CDN URL */
  static EE_CDN = 'https://cdn.earthengine.google.com/v0.1.384/earthengine-client.min.js';

  /**
   * Load the Earth Engine JS library dynamically (on demand).
   * Avoids loading ~500KB upfront for users who may only use demo mode.
   * @returns {Promise<boolean>} true if ee global is available
   */
  static async _loadEELibrary() {
    if (typeof ee !== 'undefined') return true;
    return new Promise((resolve) => {
      const script = document.createElement('script');
      script.src = this.EE_CDN;
      script.onload = () => {
        console.log('GEEZonesEngine: ee.js library loaded from CDN');
        resolve(typeof ee !== 'undefined');
      };
      script.onerror = () => {
        console.warn('GEEZonesEngine: Failed to load ee.js from CDN');
        resolve(false);
      };
      document.head.appendChild(script);
    });
  }

  /**
   * Initialize Google Earth Engine.
   * 1. Loads ee.js dynamically if not present
   * 2. Tries service-account token endpoint (production)
   * 3. Falls back to OAuth popup (development)
   * 4. Returns false gracefully if unavailable (demo mode will be used)
   *
   * @param {string} [tokenEndpoint] - URL to fetch short-lived GEE token
   * @param {string} [projectId] - GEE project ID (e.g. 'ee-gisagronomico')
   * @returns {Promise<boolean>} true if ready
   */
  static async initGEE(tokenEndpoint, projectId) {
    if (this._eeReady) return true;
    if (this._eeInitPromise) return this._eeInitPromise;

    this._eeInitPromise = (async () => {
      try {
        // Step 1: Load ee.js library
        const loaded = await this._loadEELibrary();
        if (!loaded) {
          console.warn('GEEZonesEngine: ee.js not available — will use demo mode');
          return false;
        }

        // Step 2: Service account token endpoint (recommended for production)
        if (tokenEndpoint) {
          try {
            const resp = await fetch(tokenEndpoint, { timeout: 10000 });
            if (resp.ok) {
              const data = await resp.json();
              const token = data.access_token || data.token;
              const project = data.project || projectId;
              if (token) {
                ee.data.setAuthToken('', 'Bearer', token, 3600, [], null, false);
                await new Promise((resolve, reject) => {
                  ee.initialize(project || null, null, resolve, reject);
                });
                this._eeReady = true;
                console.log('GEEZonesEngine: Initialized via service account token');
                return true;
              }
            }
          } catch (e) {
            console.warn('GEEZonesEngine: Token endpoint failed:', e.message);
          }
        }

        // Step 3: Direct project initialization (if user has credentials in browser)
        if (projectId) {
          try {
            await new Promise((resolve, reject) => {
              ee.initialize(projectId, null, resolve, reject);
            });
            this._eeReady = true;
            console.log('GEEZonesEngine: Initialized with project ID:', projectId);
            return true;
          } catch (e) {
            console.warn('GEEZonesEngine: Direct init failed, trying OAuth...', e.message);
          }
        }

        // Step 4: OAuth popup (development / interactive)
        try {
          await new Promise((resolve, reject) => {
            ee.data.authenticateViaPopup(() => {
              ee.initialize(projectId || null, null, resolve, reject);
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
   * @param {string} name - Index name from SUPPORTED_INDICES
   * @returns {ee.Image} Single-band image named after the index
   */
  static _computeIndex(img, name) {
    const formulas = {
      // --- Classic vegetation indices ---
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
      LSWI:  () => img.normalizedDifference(['B8', 'B11']).rename(name),
      RECI:  () => img.expression('NIR / RE1 - 1', { NIR: img.select('B8'), RE1: img.select('B5') }).rename(name),
      CIre:  () => img.expression('NIR / RE2 - 1', { NIR: img.select('B8'), RE2: img.select('B7') }).rename(name),

      // --- Advanced indices 2025+ (Skill v2.0) ---

      // kNDVI: Kernel NDVI — overcomes saturation at high LAI (>4)
      // Formula: tanh(NDVI²) — captures multiple scattering, SHAP-validated for yield prediction
      kNDVI: () => {
        const ndvi = img.normalizedDifference(['B8', 'B4']);
        return ndvi.pow(2).tanh().rename(name);
      },

      // IRECI: Inverted Red-Edge Chlorophyll Index — chlorophyll + biophysical retrieval
      // Formula: (B7 - B4) / (B5 / B6) — more robust than NDRE for high biomass
      IRECI: () => img.expression(
        '(RE3 - RED) / (RE1 / RE2)',
        { RE3: img.select('B7'), RED: img.select('B4'), RE1: img.select('B5'), RE2: img.select('B6') }
      ).rename(name),

      // S2REP: Sentinel-2 Red-Edge Position (nm) — chlorophyll via inflection point
      // Formula: 705 + 35 * ((B4+B7)/2 - B5) / (B6 - B5)
      S2REP: () => img.expression(
        '705 + 35 * (((RED + RE3) / 2) - RE1) / (RE2 - RE1 + 0.001)',
        { RED: img.select('B4'), RE1: img.select('B5'), RE2: img.select('B6'), RE3: img.select('B7') }
      ).rename(name),

      // MCARI: Modified Chlorophyll Absorption Ratio Index — R²=0.81 for chlorophyll
      // Formula: [(B5-B4) - 0.2*(B5-B3)] * (B5/B4)
      MCARI: () => img.expression(
        '((RE1 - RED) - 0.2 * (RE1 - GREEN)) * (RE1 / (RED + 0.001))',
        { RE1: img.select('B5'), RED: img.select('B4'), GREEN: img.select('B3') }
      ).rename(name),

      // PSRI: Plant Senescence Reflectance Index — carotenoid/chlorophyll ratio
      PSRI: () => img.expression(
        '(RED - BLUE) / (RE2 + 0.001)',
        { RED: img.select('B4'), BLUE: img.select('B2'), RE2: img.select('B6') }
      ).rename(name),

      // BSI: Bare Soil Index — for soil exposure detection and SOC mapping
      BSI: () => img.expression(
        '((SWIR + RED) - (NIR + BLUE)) / ((SWIR + RED) + (NIR + BLUE) + 0.001)',
        { SWIR: img.select('B11'), RED: img.select('B4'), NIR: img.select('B8'), BLUE: img.select('B2') }
      ).rename(name),

      // OSAVI: Optimized SAVI (L=0.16) — better for mixed veg/soil scenes
      OSAVI: () => img.expression(
        '((NIR - RED) / (NIR + RED + 0.16)) * 1.16',
        { NIR: img.select('B8'), RED: img.select('B4') }
      ).rename(name),

      // MSI: Moisture Stress Index — SWIR/NIR ratio (inverse of NDMI, higher=more stress)
      MSI: () => img.expression(
        'SWIR / NIR', { SWIR: img.select('B11'), NIR: img.select('B8A') }
      ).rename(name)
    };

    const fn = formulas[name];
    if (!fn) throw new Error(`Unknown index: ${name}`);
    return fn();
  }

  /**
   * Apply SCL cloud/shadow mask to a Sentinel-2 SR image.
   * Excludes: 0 (no data), 1 (saturated/defective), 3 (cloud shadow),
   *           8 (cloud med), 9 (cloud high), 10 (cirrus), 11 (snow/ice)
   * Keeps: 2 (dark area), 4 (vegetation), 5 (bare soil), 6 (water), 7 (cloud low/unclassified)
   */
  static _maskS2clouds(img) {
    const scl = img.select('SCL');
    const mask = scl.neq(0).and(scl.neq(1)).and(scl.neq(3))
      .and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11));
    return img.updateMask(mask);
  }

  // ==================== MAIN GEE PROCESSING PIPELINE ====================

  /**
   * Process a field polygon through the full GEE pipeline.
   * Follows production v4.1 methodology: multi-campaign ranking percentile.
   *
   * @param {Array<[number,number]>} fieldPolygon - [[lng,lat], ...] boundary
   * @param {string} cropKey - Key from CROP_INDEX_CONFIGS
   * @param {number} areaHa - Field area in hectares
   * @param {Function} [onProgress] - (step, totalSteps, message) callback
   * @param {number} [numCampaigns=5] - Number of campaigns/years to analyze
   * @returns {Promise<Object>} satelliteData object for ZonesEngine
   */
  static async processField(fieldPolygon, cropKey, areaHa, onProgress, numCampaigns = 5) {
    if (!this._eeReady) throw new Error('GEE not initialized. Call initGEE() first.');

    const cropConfig = this.CROP_INDEX_CONFIGS[cropKey];
    if (!cropConfig) throw new Error(`Unknown crop: ${cropKey}`);

    const indexNames = Object.keys(cropConfig.indices);
    const progress = onProgress || (() => {});
    const STEPS = 10;  // 10 steps: geometry, S2, indices, campaigns, DEM, SAR, download, campaigns-dl, format, done

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
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', this.CLOUD_MAX));

    // Apply cloud mask — use bound function reference (arrow + this doesn't work in GEE .map)
    const maskFn = this._maskS2clouds;
    s2 = s2.map(function(img) { return maskFn(img); });

    const count = await s2.size().getInfo();
    if (count < this.MIN_SCENES) {
      // Fallback 1: relax to 25%
      s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(geometry).filterDate(start, now)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', this.CLOUD_FALLBACK_1))
        .map(function(img) { return maskFn(img); });
      const count2 = await s2.size().getInfo();
      if (count2 < this.MIN_SCENES) {
        // Fallback 2: relax to 40%
        s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
          .filterBounds(geometry).filterDate(start, now)
          .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', this.CLOUD_FALLBACK_2))
          .map(function(img) { return maskFn(img); });
      }
    }

    // --- Step 3: Compute crop-specific indices ---
    progress(3, STEPS, `Calculando índices: ${indexNames.join(', ')}...`);

    // Build index computation function (GEE .map requires serializable functions)
    const computeIdx = this._computeIndex.bind(this);
    const idxList = indexNames;
    const withIndices = s2.map(function(img) {
      var result = img;
      for (var i = 0; i < idxList.length; i++) {
        result = result.addBands(computeIdx(img, idxList[i]));
      }
      return result;
    });

    // --- Step 4: Create campaign composites (phenological windows per year) ---
    // Production v4.1: each campaign = specific months (e.g., May-Sept for sugarcane elongation)
    progress(4, STEPS, `Generando composites ${numCampaigns} campañas (ventana fenológica)...`);

    const ventana = cropConfig.ventana || { mesInicio: 5, mesFin: 9 };
    const currentYear = new Date().getFullYear();
    const campaigns = [];
    for (let y = 0; y < numCampaigns; y++) {
      const year = currentYear - numCampaigns + y;
      const campStart = ee.Date.fromYMD(year, ventana.mesInicio, 1);
      const campEnd = ee.Date.fromYMD(year, ventana.mesFin, 30);
      const campCollection = withIndices.filterDate(campStart, campEnd);
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

    // TWI with real flow accumulation from MERIT Hydro when available
    const slopeRad = slope.multiply(Math.PI / 180);

    // MERIT/Hydro is a single ee.Image (not a collection) — check if 'upa' band has data
    // by sampling a point. If it fails or returns null, use slope proxy.
    let flowAccImg, twi;
    let usedMerit = false;
    try {
      const meritImg = ee.Image('MERIT/Hydro/v1_0_1');
      const meritFlow = meritImg.select('upa').clip(geometry);
      // Test if MERIT has data in this region (sample center point)
      const centerPt = geometry.centroid();
      const testVal = await meritFlow.sample({ region: centerPt, scale: 500, numPixels: 1 }).size().getInfo();

      if (testVal > 0) {
        // MERIT available — use real flow accumulation
        flowAccImg = meritFlow.rename('flow');
        // Real TWI = ln(contributing_area_m² / tan(slope_rad + eps))
        // upa is upstream area in km² → multiply by 1e6 for m²
        const contribArea = meritFlow.multiply(1e6);
        twi = contribArea.divide(slopeRad.add(0.001).tan()).log().rename('TWI');
        usedMerit = true;
      }
    } catch (e) {
      console.warn('GEEZonesEngine: MERIT Hydro unavailable:', e.message);
    }

    if (!usedMerit) {
      // Fallback: slope-based proxy for flow and TWI
      const slopeMin = ee.Number(slope.reduceRegion({ reducer: ee.Reducer.min(), geometry: geometry, scale: 30, bestEffort: true }).get('slope'));
      const slopeMax = ee.Number(slope.reduceRegion({ reducer: ee.Reducer.max(), geometry: geometry, scale: 30, bestEffort: true }).get('slope'));
      flowAccImg = slope.unitScale(slopeMin, slopeMax).multiply(-1).add(1).rename('flow');
      const pixelContribArea = scale * scale * 10;
      twi = ee.Image.constant(pixelContribArea).divide(slopeRad.add(0.001).tan()).log().rename('TWI');
    }

    // --- Step 6: Sentinel-1 SAR — RVI radar (cloud-independent) ---
    progress(6, STEPS, 'Integrando Sentinel-1 SAR (RVI radar)...');

    let sarRVI;
    try {
      const s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
        .filterBounds(geometry)
        .filterDate(start, now)
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
        .filter(ee.Filter.eq('instrumentMode', 'IW'))
        .select(['VV', 'VH']);

      const s1Count = await s1.size().getInfo();
      if (s1Count >= 3) {
        // RVI = 4 * VH / (VV + VH) — range 0 (bare) to 1 (dense veg)
        // S1 GRD values are in dB → convert to linear: linear = 10^(dB/10)
        const s1Median = s1.median().clip(geometry);
        const vv = ee.Image(10).pow(s1Median.select('VV').divide(10));
        const vh = ee.Image(10).pow(s1Median.select('VH').divide(10));
        sarRVI = vh.multiply(4).divide(vv.add(vh)).rename('SAR_RVI');
      }
    } catch (e) {
      console.warn('GEEZonesEngine: SAR processing skipped:', e.message);
    }

    // --- Step 7: OPTIMIZED single download (all layers in one call) ---
    progress(7, STEPS, 'Descargando todos los datos del servidor GEE...');

    // Stack ALL campaigns + median + terrain into ONE multi-band image
    let downloadStack = medianComposite
      .addBands(stdComposite)
      .addBands(dem.rename('DEM'))
      .addBands(slope.rename('slope'))
      .addBands(twi)
      .addBands(flowAccImg);

    // Add SAR RVI if available
    if (sarRVI) {
      downloadStack = downloadStack.addBands(sarRVI);
    }

    // Add individual campaign bands with renamed suffixes
    // (regexpRename doesn't exist in ee.js API — use rename() with explicit band list)
    for (let i = 0; i < campaigns.length; i++) {
      const campBands = campaigns[i].select(indexNames);
      const newNames = indexNames.map(idx => idx + '_c' + i);
      const renamed = campBands.rename(newNames);
      downloadStack = downloadStack.addBands(renamed);
    }

    // Auto-adjust scale to keep sampleRectangle within pixel limits (~262144 px)
    // Estimate pixel count: area_m² / scale² per band
    const areaSqM = areaHa * 10000;
    const estPixels = areaSqM / (scale * scale);
    if (estPixels > 200000) {
      // Increase scale to stay within limits
      scale = Math.ceil(Math.sqrt(areaSqM / 200000));
      console.log(`GEEZonesEngine: Auto-adjusted scale to ${scale}m to fit sampleRectangle limits`);
    }

    // SINGLE download — all data in one call (was 5 calls before!)
    const sampled = await downloadStack
      .reproject({ crs: 'EPSG:4326', scale })
      .sampleRectangle({ region: geometry, defaultValue: 0 })
      .getInfo();

    // --- Step 8: Extract campaign grids from unified download ---
    progress(8, STEPS, 'Procesando campañas temporales...');
    const props = sampled.properties;
    const campaignGrids = {};
    for (const idx of indexNames) {
      campaignGrids[idx] = [];
      for (let i = 0; i < campaigns.length; i++) {
        const band = props[`${idx}_c${i}`];
        if (band) campaignGrids[idx].push(band);
      }
      // Fallback: use median if no campaign data extracted
      if (campaignGrids[idx].length === 0 && props[idx]) {
        campaignGrids[idx] = [props[idx]];
      }
    }

    // --- Step 9: Validate image sufficiency ---
    if (count < 8) {
      console.warn(`GEEZonesEngine: Only ${count} images — below recommended minimum of 8 for statistical sufficiency`);
    }

    // --- Step 10: Format for ZonesEngine ---
    progress(10, STEPS, 'Formateando datos para motor de zonas...');

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

    // Use PRODUCTION score weights directly — v4.1 methodology
    // rank_medio(40%), rank_std(20%), rank_min(10%), TWI(10%), flow(6%), slope(6%), elev(4%), drain(4%)
    const compositeWeights = { ...this.PRODUCTION_SCORE_WEIGHTS };

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
      indexNames,
      hasSAR: !!sarRVI,
      sarRVI: sarRVI ? props['SAR_RVI'] : null,
      imageSufficiency: count >= 8 ? 'OK' : 'LOW'
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
  static processFieldDemo(bounds, boundary, areaHa, cropKey, numCampaigns = 5) {
    const cropConfig = this.CROP_INDEX_CONFIGS[cropKey];
    if (!cropConfig) throw new Error(`Unknown crop: ${cropKey}`);

    // Simulation grid resolution — higher = smoother organic zone boundaries
    // Production uses 2m interpolation; for demo, use high grid for equivalent quality
    const gridRes = areaHa > 200 ? 150 : areaHa > 100 ? 120 : areaHa > 30 ? 100 : 80;
    const satelliteData = ZonesEngine.simulateSatelliteData(bounds, boundary, areaHa, {
      years: numCampaigns,
      resolution: gridRes,
      cellSize: 10
    });

    // Use PRODUCTION score weights directly (same as real GEE pipeline)
    const compositeWeights = { ...this.PRODUCTION_SCORE_WEIGHTS };

    return {
      satelliteData,
      compositeWeights,
      cropKey,
      cropConfig,
      scale: satelliteData.cellSize || 10,
      imageCount: 0,
      campaignCount: numCampaigns,
      indexNames: Object.keys(cropConfig.indices),
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

    // Vegetation indices (used for ranking, shown as reference)
    for (const [name, weight] of Object.entries(cropConfig.indices)) {
      breakdown.push({ name, weight: Math.round(weight * 100), source: 'vegetation' });
    }

    // Score Compuesto weights (production v4.1)
    const sw = this.PRODUCTION_SCORE_WEIGHTS;
    breakdown.push({ name: 'Ranking medio (5 años)', weight: Math.round(sw.ndvi_median * 100), source: 'score' });
    breakdown.push({ name: 'Estabilidad temporal', weight: Math.round(sw.ndre_median * 100), source: 'score' });
    breakdown.push({ name: 'Seguridad (peor año)', weight: Math.round(sw.ndvi_stability * 100), source: 'score' });
    breakdown.push({ name: 'TWI (humedad)', weight: Math.round(sw.twi * 100), source: 'terrain' });
    breakdown.push({ name: 'Flujo agua', weight: Math.round(sw.flow_inv * 100), source: 'terrain' });
    breakdown.push({ name: 'Pendiente', weight: Math.round(sw.slope_inv * 100), source: 'terrain' });
    breakdown.push({ name: 'Elevación', weight: Math.round(sw.rel_elevation * 100), source: 'terrain' });
    breakdown.push({ name: 'Dist. drenaje', weight: Math.round(sw.drain_distance * 100), source: 'terrain' });

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
