package network.pixadvisor.muestreo;

import android.content.Context;
import android.location.GnssStatus;
import android.location.LocationManager;
import android.location.OnNmeaMessageListener;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.webkit.JavascriptInterface;

import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Native GNSS Bridge — exposes real satellite metadata to JavaScript WebView.
 *
 * Provides data NOT available through the standard Geolocation API:
 *   - Satellite count by constellation (GPS, GLONASS, Galileo, BeiDou, SBAS)
 *   - Real HDOP / PDOP / VDOP (parsed from NMEA GSA sentences)
 *   - C/N0 (carrier-to-noise) per satellite — better than estimated SNR
 *   - Dual-frequency detection (L1/L5)
 *   - Carrier phase availability
 *   - Fix type (No fix / 2D / 3D)
 *   - Per-satellite details (svid, constellation, elevation, azimuth, cn0, band)
 *
 * Registered in WebView as "AndroidGNSS".
 * JavaScript usage:
 *   if (window.AndroidGNSS && AndroidGNSS.isAvailable()) {
 *     const info = JSON.parse(AndroidGNSS.getSatelliteInfo());
 *     const dop  = JSON.parse(AndroidGNSS.getDOPValues());
 *   }
 *
 * Requires: ACCESS_FINE_LOCATION permission (already declared in manifest).
 * Min API: 24 (GnssStatus.Callback + OnNmeaMessageListener).
 */
public class GNSSBridge {
    private static final String TAG = "GNSSBridge";

    private final Context context;
    private LocationManager locationManager;
    private GnssStatus.Callback gnssCallback;
    private OnNmeaMessageListener nmeaListener;
    private boolean listening = false;

    // ── Satellite data (updated from GnssStatus callback) ──
    private volatile int totalSatellites = 0;
    private volatile int usedSatellites = 0;
    private volatile int gpsCount = 0;
    private volatile int glonassCount = 0;
    private volatile int galileoCount = 0;
    private volatile int beidouCount = 0;
    private volatile int sbasCount = 0;
    private volatile float bestCn0 = 0;
    private volatile float avgCn0 = 0;
    private volatile boolean hasDualFreq = false;
    private volatile int l1Count = 0;
    private volatile int l5Count = 0;
    private volatile boolean hasCarrierFreq = false;
    private volatile long lastSatUpdate = 0;

    // Per-satellite details JSON (rebuilt on each GnssStatus callback)
    private volatile String satelliteDetailsJson = "[]";

    // ── DOP values (parsed from NMEA GSA sentences) ──
    private volatile float hdop = 99f;
    private volatile float pdop = 99f;
    private volatile float vdop = 99f;
    private volatile int fixType = 0;  // 1=no fix, 2=2D, 3=3D
    private volatile long lastNmeaUpdate = 0;

    public GNSSBridge(Context ctx) {
        this.context = ctx;
        this.locationManager = (LocationManager) ctx.getSystemService(Context.LOCATION_SERVICE);
    }

    // ═══════════════════════════════════════════════
    //  JavaScript Interface Methods
    //  Called from WebView JS thread — must be thread-safe
    // ═══════════════════════════════════════════════

    /**
     * Returns true if native GNSS data is available (callbacks active and data received).
     */
    @JavascriptInterface
    public boolean isAvailable() {
        return listening && lastSatUpdate > 0;
    }

    /**
     * Returns satellite info as JSON string:
     * { totalSatellites, usedSatellites, gps, glonass, galileo, beidou, sbas,
     *   bestCn0, avgCn0, hasDualFreq, l1Count, l5Count, hasCarrierFreq, lastUpdate }
     */
    @JavascriptInterface
    public String getSatelliteInfo() {
        try {
            JSONObject info = new JSONObject();
            info.put("totalSatellites", totalSatellites);
            info.put("usedSatellites", usedSatellites);
            info.put("gps", gpsCount);
            info.put("glonass", glonassCount);
            info.put("galileo", galileoCount);
            info.put("beidou", beidouCount);
            info.put("sbas", sbasCount);
            info.put("bestCn0", round1(bestCn0));
            info.put("avgCn0", round1(avgCn0));
            info.put("hasDualFreq", hasDualFreq);
            info.put("l1Count", l1Count);
            info.put("l5Count", l5Count);
            info.put("hasCarrierFreq", hasCarrierFreq);
            info.put("lastUpdate", lastSatUpdate);
            return info.toString();
        } catch (Exception e) {
            Log.w(TAG, "getSatelliteInfo error: " + e.getMessage());
            return "{}";
        }
    }

    /**
     * Returns DOP (Dilution of Precision) values parsed from NMEA:
     * { hdop, pdop, vdop, fixType, fixLabel, lastUpdate }
     */
    @JavascriptInterface
    public String getDOPValues() {
        try {
            JSONObject dop = new JSONObject();
            dop.put("hdop", round1(hdop));
            dop.put("pdop", round1(pdop));
            dop.put("vdop", round1(vdop));
            dop.put("fixType", fixType);
            dop.put("fixLabel", fixType == 3 ? "3D" : fixType == 2 ? "2D" : "Sin fix");
            dop.put("lastUpdate", lastNmeaUpdate);
            return dop.toString();
        } catch (Exception e) {
            Log.w(TAG, "getDOPValues error: " + e.getMessage());
            return "{}";
        }
    }

    /**
     * Returns per-satellite details as JSON array:
     * [{ svid, constellation, cn0, elevation, azimuth, usedInFix, freqMHz?, band? }, ...]
     */
    @JavascriptInterface
    public String getSatelliteDetails() {
        return satelliteDetailsJson;
    }

    /**
     * Returns a combined GNSS summary as JSON:
     * { satellites: {...}, dop: {...}, quality, listening }
     */
    @JavascriptInterface
    public String getGNSSSummary() {
        try {
            JSONObject summary = new JSONObject();
            summary.put("satellites", new JSONObject(getSatelliteInfo()));
            summary.put("dop", new JSONObject(getDOPValues()));
            summary.put("quality", getQualityLabel());
            summary.put("listening", listening);
            return summary.toString();
        } catch (Exception e) {
            Log.w(TAG, "getGNSSSummary error: " + e.getMessage());
            return "{}";
        }
    }

    /**
     * Quality label based on real HDOP + satellite count.
     * Used by JS for display classification.
     */
    private String getQualityLabel() {
        if (usedSatellites == 0) return "sin_senal";
        if (hdop <= 1.0 && usedSatellites >= 8) return "rtk_grade";
        if (hdop <= 2.0 && usedSatellites >= 6) return "excelente";
        if (hdop <= 4.0 && usedSatellites >= 4) return "buena";
        if (hdop <= 8.0) return "aceptable";
        return "baja";
    }

    // ═══════════════════════════════════════════════
    //  Lifecycle — called from OfflineActivity
    // ═══════════════════════════════════════════════

    /**
     * Start listening for GNSS status updates and NMEA messages.
     * Call from Activity.onResume() after location permissions are granted.
     */
    public void startListening() {
        if (listening) return;
        try {
            // GnssStatus.Callback — satellite count, constellation, C/N0, carrier freq
            gnssCallback = new GnssStatus.Callback() {
                @Override
                public void onSatelliteStatusChanged(GnssStatus status) {
                    processSatelliteStatus(status);
                }

                @Override
                public void onStarted() {
                    Log.d(TAG, "GNSS engine started");
                }

                @Override
                public void onStopped() {
                    Log.d(TAG, "GNSS engine stopped");
                }
            };
            locationManager.registerGnssStatusCallback(
                gnssCallback, new Handler(Looper.getMainLooper()));

            // NMEA listener — parse GSA sentences for real HDOP/PDOP/VDOP
            nmeaListener = (message, timestamp) -> parseNmea(message);
            locationManager.addNmeaListener(
                nmeaListener, new Handler(Looper.getMainLooper()));

            listening = true;
            Log.i(TAG, "GNSS listeners registered (GnssStatus + NMEA)");
        } catch (SecurityException e) {
            listening = false;
            Log.e(TAG, "No location permission for GNSS: " + e.getMessage());
        } catch (Exception e) {
            listening = false;
            Log.e(TAG, "Failed to register GNSS listeners: " + e.getMessage());
        }
    }

    /**
     * Stop listening. Call from Activity.onPause().
     */
    public void stopListening() {
        if (!listening) return;
        try {
            if (gnssCallback != null) {
                locationManager.unregisterGnssStatusCallback(gnssCallback);
            }
            if (nmeaListener != null) {
                locationManager.removeNmeaListener(nmeaListener);
            }
        } catch (Exception e) {
            Log.w(TAG, "Error unregistering GNSS: " + e.getMessage());
        }
        listening = false;
        Log.i(TAG, "GNSS listeners unregistered");
    }

    // ═══════════════════════════════════════════════
    //  GnssStatus Processing
    // ═══════════════════════════════════════════════

    private void processSatelliteStatus(GnssStatus status) {
        int count = status.getSatelliteCount();
        int used = 0;
        int gps = 0, glo = 0, gal = 0, bei = 0, sba = 0;
        float best = 0, totalCn0 = 0;
        int cn0Count = 0;
        boolean dualFreq = false;
        int countL1 = 0, countL5 = 0;
        boolean carrierFreq = false;

        JSONArray details = new JSONArray();

        for (int i = 0; i < count; i++) {
            float cn0 = status.getCn0DbHz(i);
            boolean inFix = status.usedInFix(i);
            int constellation = status.getConstellationType(i);
            int svid = status.getSvid(i);
            float elevation = status.getElevationDegrees(i);
            float azimuth = status.getAzimuthDegrees(i);

            // Count satellites used in current fix, by constellation
            if (inFix) {
                used++;
                switch (constellation) {
                    case GnssStatus.CONSTELLATION_GPS:     gps++; break;
                    case GnssStatus.CONSTELLATION_GLONASS: glo++; break;
                    case GnssStatus.CONSTELLATION_GALILEO: gal++; break;
                    case GnssStatus.CONSTELLATION_BEIDOU:  bei++; break;
                    case GnssStatus.CONSTELLATION_SBAS:    sba++; break;
                }
            }

            // C/N0 statistics (only satellites with signal)
            if (cn0 > 0) {
                totalCn0 += cn0;
                cn0Count++;
                if (cn0 > best) best = cn0;
            }

            // Dual-frequency detection (API 26+ for hasCarrierFrequencyHz)
            if (Build.VERSION.SDK_INT >= 26 && status.hasCarrierFrequencyHz(i)) {
                float freq = status.getCarrierFrequencyHz(i);
                carrierFreq = true;
                float freqMHz = freq / 1e6f;
                // L1 band ≈ 1575.42 MHz (±20 MHz tolerance)
                if (freqMHz > 1555 && freqMHz < 1596) countL1++;
                // L5 band ≈ 1176.45 MHz (±20 MHz tolerance)
                if (freqMHz > 1156 && freqMHz < 1197) {
                    countL5++;
                    dualFreq = true;
                }
                // L2 band ≈ 1227.60 MHz (GLONASS/GPS military, some civilian)
                // Not counted but detected as dual-freq
                if (freqMHz > 1207 && freqMHz < 1248) dualFreq = true;
            }

            // Build per-satellite detail JSON (only satellites with signal)
            if (cn0 > 0) {
                try {
                    JSONObject sat = new JSONObject();
                    sat.put("svid", svid);
                    sat.put("constellation", constellationName(constellation));
                    sat.put("cn0", round1(cn0));
                    sat.put("elevation", Math.round(elevation));
                    sat.put("azimuth", Math.round(azimuth));
                    sat.put("usedInFix", inFix);
                    if (Build.VERSION.SDK_INT >= 26 && status.hasCarrierFrequencyHz(i)) {
                        float fq = status.getCarrierFrequencyHz(i);
                        float fqMHz = fq / 1e6f;
                        sat.put("freqMHz", round1(fqMHz));
                        String band = "Other";
                        if (fqMHz > 1555 && fqMHz < 1596) band = "L1";
                        else if (fqMHz > 1156 && fqMHz < 1197) band = "L5";
                        else if (fqMHz > 1207 && fqMHz < 1248) band = "L2";
                        sat.put("band", band);
                    }
                    details.put(sat);
                } catch (Exception ignored) {}
            }
        }

        // Atomic state update (all volatile fields)
        totalSatellites = count;
        usedSatellites = used;
        gpsCount = gps;
        glonassCount = glo;
        galileoCount = gal;
        beidouCount = bei;
        sbasCount = sba;
        bestCn0 = best;
        avgCn0 = cn0Count > 0 ? totalCn0 / cn0Count : 0;
        hasDualFreq = dualFreq;
        l1Count = countL1;
        l5Count = countL5;
        hasCarrierFreq = carrierFreq;
        lastSatUpdate = System.currentTimeMillis();
        satelliteDetailsJson = details.toString();
    }

    /**
     * Maps GnssStatus constellation type constant to human-readable name.
     */
    private String constellationName(int type) {
        switch (type) {
            case GnssStatus.CONSTELLATION_GPS:     return "GPS";
            case GnssStatus.CONSTELLATION_GLONASS: return "GLONASS";
            case GnssStatus.CONSTELLATION_GALILEO: return "Galileo";
            case GnssStatus.CONSTELLATION_BEIDOU:  return "BeiDou";
            case GnssStatus.CONSTELLATION_SBAS:    return "SBAS";
            case GnssStatus.CONSTELLATION_QZSS:    return "QZSS";
            case GnssStatus.CONSTELLATION_IRNSS:   return "IRNSS";
            default: return "Unknown";
        }
    }

    // ═══════════════════════════════════════════════
    //  NMEA Parsing for DOP Values
    //  Parses $GPGSA / $GNGSA / $GLGSA / $GAGSA
    // ═══════════════════════════════════════════════

    private void parseNmea(String sentence) {
        if (sentence == null) return;

        // GSA sentence format:
        // $GNGSA,A,3,sv,sv,...,sv,PDOP,HDOP,VDOP*checksum
        // Fields: [0]=talker, [1]=mode(A/M), [2]=fixType(1/2/3),
        //         [3-14]=PRN of sats, [15]=PDOP, [16]=HDOP, [17]=VDOP
        if (sentence.startsWith("$GPGSA") || sentence.startsWith("$GNGSA")
                || sentence.startsWith("$GLGSA") || sentence.startsWith("$GAGSA")) {
            try {
                // Strip checksum after '*'
                int starIdx = sentence.indexOf('*');
                String clean = starIdx > 0 ? sentence.substring(0, starIdx) : sentence;
                String[] parts = clean.split(",", -1);

                if (parts.length >= 17) {
                    int fix = safeParseInt(parts[2], 0);
                    float p = safeParseFloat(parts[15], 99f);
                    float h = safeParseFloat(parts[16], 99f);
                    float v = parts.length > 17 ? safeParseFloat(parts[17], 99f) : 99f;

                    // Only accept reasonable values (0.5 – 50.0)
                    if (h > 0 && h < 50) {
                        fixType = fix;
                        pdop = p;
                        hdop = h;
                        vdop = v;
                        lastNmeaUpdate = System.currentTimeMillis();
                    }
                }
            } catch (Exception e) {
                // NMEA parsing is best-effort — never crash
                Log.d(TAG, "NMEA GSA parse error: " + e.getMessage());
            }
        }
    }

    // ═══════════════════════════════════════════════
    //  Utility
    // ═══════════════════════════════════════════════

    private static int safeParseInt(String s, int def) {
        if (s == null || s.trim().isEmpty()) return def;
        try { return Integer.parseInt(s.trim()); } catch (Exception e) { return def; }
    }

    private static float safeParseFloat(String s, float def) {
        if (s == null || s.trim().isEmpty()) return def;
        try { return Float.parseFloat(s.trim()); } catch (Exception e) { return def; }
    }

    private static double round1(float v) {
        return Math.round(v * 10.0) / 10.0;
    }
}
