package network.pixadvisor.muestreo;

import android.app.Activity;
import android.os.Bundle;
import android.os.Build;
import android.webkit.WebView;
import android.webkit.WebSettings;
import android.webkit.WebViewClient;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.GeolocationPermissions;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.content.Intent;
import android.content.ContentResolver;
import android.content.pm.ActivityInfo;
import android.database.Cursor;
import android.net.Uri;
import android.provider.OpenableColumns;
import android.util.Base64;
import android.util.Log;
import android.view.View;
import android.view.WindowManager;
import android.Manifest;
import android.content.pm.PackageManager;
import android.webkit.JavascriptInterface;
import android.widget.Toast;
import androidx.browser.customtabs.CustomTabsIntent;
import androidx.webkit.WebViewAssetLoader;
import java.io.InputStream;
import java.io.BufferedReader;
import java.io.InputStreamReader;

/**
 * Motor interno offline para PIX Muestreo.
 * Usa WebViewAssetLoader para servir assets desde HTTPS local.
 * GPS, Cámara, IndexedDB funcionan 100% offline.
 */
public class OfflineActivity extends Activity {
    private static final String TAG = "PixMuestreo";
    private static final String APPASSETS_ORIGIN = "https://appassets.androidplatform.net";
    private static final int PERMISSION_REQUEST_CODE = 100;
    private WebView webView;
    private ValueCallback<Uri[]> fileCallback;
    private WebViewAssetLoader assetLoader;
    private String pendingFileJson = null;
    private String pendingFileName = null;
    private boolean webViewReady = false;

    /**
     * JavaScript bridge for native Android features (OAuth, etc.)
     * Accessible from JS as: AndroidBridge.startGoogleAuth(clientId)
     */
    private class WebAppInterface {
        @JavascriptInterface
        public void startGoogleAuth(String clientId) {
            String authUrl = "https://accounts.google.com/o/oauth2/v2/auth"
                + "?client_id=" + Uri.encode(clientId)
                + "&redirect_uri=" + Uri.encode("https://pixadvisor.network/pix-muestreo/oauth-callback.html")
                + "&response_type=token"
                + "&scope=" + Uri.encode("https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/drive.readonly")
                + "&prompt=consent"
                + "&include_granted_scopes=true";

            try {
                CustomTabsIntent customTabsIntent = new CustomTabsIntent.Builder().build();
                customTabsIntent.launchUrl(OfflineActivity.this, Uri.parse(authUrl));
            } catch (Exception e) {
                // Fallback to system browser
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(authUrl)));
                } catch (Exception ex) { /* ignore */ }
            }
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Fullscreen + keep screen on
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        if (Build.VERSION.SDK_INT > Build.VERSION_CODES.O) {
            setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_USER_PORTRAIT);
        }

        // Request runtime permissions (GPS + Camera)
        if (Build.VERSION.SDK_INT >= 23) {
            requestPermissions(new String[]{
                Manifest.permission.ACCESS_FINE_LOCATION,
                Manifest.permission.ACCESS_COARSE_LOCATION,
                Manifest.permission.CAMERA
            }, PERMISSION_REQUEST_CODE);
        }

        // WebViewAssetLoader: motor interno HTTPS local
        // Sirve assets desde https://appassets.androidplatform.net/assets/
        assetLoader = new WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
            .build();

        // Setup WebView
        webView = new WebView(this);
        setContentView(webView);

        WebSettings ws = webView.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(true);
        ws.setDatabaseEnabled(true);
        ws.setAllowFileAccess(false);   // Not needed — WebViewAssetLoader serves via HTTPS
        ws.setAllowContentAccess(false); // Content URIs handled by Java, not WebView
        ws.setGeolocationEnabled(true);
        ws.setMediaPlaybackRequiresUserGesture(false);
        ws.setUseWideViewPort(true);
        ws.setLoadWithOverviewMode(true);
        ws.setBuiltInZoomControls(false);
        ws.setDisplayZoomControls(false);
        if (Build.VERSION.SDK_INT >= 21) {
            ws.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        }
        ws.setDatabasePath(getApplicationContext().getDir("database", MODE_PRIVATE).getPath());

        // WebViewClient: intercepts requests and serves from local assets
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                if (Build.VERSION.SDK_INT >= 21) {
                    return assetLoader.shouldInterceptRequest(request.getUrl());
                }
                return null;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                webViewReady = true;
                // Inject pending file from intent (cold start — WebView wasn't ready yet)
                if (pendingFileJson != null) {
                    view.postDelayed(() -> injectFileToWebView(), 1500);
                }
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (url.startsWith("https://appassets.androidplatform.net/")) return false;
                // External links open in browser
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                } catch (Exception e) { /* ignore */ }
                return true;
            }
        });

        // WebChromeClient: GPS permissions + camera + file chooser
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(String origin,
                    GeolocationPermissions.Callback callback) {
                // Only grant geolocation to our local assets origin
                if (origin != null && origin.startsWith(APPASSETS_ORIGIN)) {
                    callback.invoke(origin, true, false);
                } else {
                    callback.invoke(origin, false, false);
                }
            }

            @Override
            public void onPermissionRequest(PermissionRequest request) {
                if (Build.VERSION.SDK_INT >= 21) {
                    // Only grant permissions (camera, etc.) to our local assets origin
                    Uri origin = request.getOrigin();
                    if (origin != null && origin.toString().startsWith(APPASSETS_ORIGIN)) {
                        request.grant(request.getResources());
                    } else {
                        request.deny();
                    }
                }
            }

            @Override
            public boolean onShowFileChooser(WebView wv, ValueCallback<Uri[]> cb,
                    FileChooserParams params) {
                fileCallback = cb;
                try {
                    startActivityForResult(params.createIntent(), 1001);
                } catch (Exception e) {
                    fileCallback = null;
                    return false;
                }
                return true;
            }
        });

        // Register JavaScript bridge for native auth
        webView.addJavascriptInterface(new WebAppInterface(), "AndroidBridge");

        // Load from HTTPS local origin (motor interno)
        webView.loadUrl("https://appassets.androidplatform.net/assets/index.html");

        // Check if launched with a file intent (WhatsApp, file manager, etc.)
        // The data is stored and injected in onPageFinished once WebView is ready
        handleFileIntent(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (intent == null) return;

        // 1. Handle OAuth callback from pixmuestreo://oauth-callback?token=...
        Uri data = intent.getData();
        if (data != null && "pixmuestreo".equals(data.getScheme())
                && "oauth-callback".equals(data.getHost())) {
            String token = data.getQueryParameter("token");
            String expiresIn = data.getQueryParameter("expires_in");
            if (token != null && webView != null) {
                int expSeconds = 3600;
                try { expSeconds = Integer.parseInt(expiresIn); } catch (Exception e) {}
                String js = "driveSync.setTokenFromNative('" + token.replace("'", "\\'") + "', " + expSeconds + ")";
                webView.evaluateJavascript(js, null);
            }
            return;
        }

        // 2. Handle file intent (warm start — WebView already loaded)
        handleFileIntent(intent);
        if (webViewReady) {
            injectFileToWebView();
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == 1001 && fileCallback != null) {
            Uri[] result = null;
            if (resultCode == RESULT_OK && data != null && data.getDataString() != null) {
                result = new Uri[]{Uri.parse(data.getDataString())};
            }
            fileCallback.onReceiveValue(result);
            fileCallback = null;
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    // ===== LIFECYCLE MANAGEMENT =====

    @Override
    protected void onPause() {
        super.onPause();
        if (webView != null) {
            webView.onPause();
            webView.pauseTimers();
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (webView != null) {
            webView.onResume();
            webView.resumeTimers();
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        if (webView != null) {
            webView.saveState(outState);
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.stopLoading();
            webView.setWebViewClient(null);
            webView.setWebChromeClient(null);
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != PERMISSION_REQUEST_CODE) return;

        boolean locationGranted = false;
        for (int i = 0; i < permissions.length; i++) {
            if (Manifest.permission.ACCESS_FINE_LOCATION.equals(permissions[i])) {
                locationGranted = (grantResults[i] == PackageManager.PERMISSION_GRANTED);
            }
        }
        if (!locationGranted) {
            Toast.makeText(this,
                "GPS es necesario para georreferenciar muestras. Active el permiso en Configuración.",
                Toast.LENGTH_LONG).show();
        }
    }

    // ===== FILE INTENT HANDLING (WhatsApp, file managers, etc.) =====

    /**
     * Reads a JSON/GeoJSON file from a content:// or file:// URI.
     * Stores content in pendingFileJson for injection into WebView.
     * Works with ACTION_VIEW (open with) and ACTION_SEND (share to).
     */
    private void handleFileIntent(Intent intent) {
        if (intent == null) return;

        String action = intent.getAction();
        Uri fileUri = null;

        if (Intent.ACTION_VIEW.equals(action)) {
            fileUri = intent.getData();
        } else if (Intent.ACTION_SEND.equals(action)) {
            // WhatsApp and most apps use EXTRA_STREAM for shared files
            fileUri = intent.getParcelableExtra(Intent.EXTRA_STREAM);
        }

        if (fileUri == null) return;

        try {
            // Get the display name of the file
            String filename = getFileDisplayName(fileUri);
            if (filename == null) filename = "mapa.json";

            // Accept JSON, GeoJSON, KML, and CSV files
            String lowerName = filename.toLowerCase();
            boolean isSupported = lowerName.endsWith(".json") || lowerName.endsWith(".geojson")
                || lowerName.endsWith(".kml") || lowerName.endsWith(".csv");
            if (!isSupported) {
                // If extension is unknown, still try to read — WhatsApp may strip extensions
                Log.d(TAG, "Unknown extension for: " + filename + ", will try to detect format");
            }

            // Read content from URI
            ContentResolver cr = getContentResolver();
            InputStream is = cr.openInputStream(fileUri);
            if (is == null) {
                Log.e(TAG, "Could not open input stream for: " + fileUri);
                return;
            }

            BufferedReader reader = new BufferedReader(new InputStreamReader(is, "UTF-8"));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append('\n');
            }
            reader.close();
            is.close();

            String fileContent = sb.toString().trim();
            if (fileContent.isEmpty()) return;

            // Auto-detect format by content if extension is unknown
            char first = fileContent.charAt(0);
            if (!isSupported) {
                if (first == '{' || first == '[') {
                    // Looks like JSON — add .json extension for JS-side detection
                    if (!lowerName.endsWith(".json")) filename = filename + ".json";
                } else if (first == '<' && fileContent.contains("<kml")) {
                    // Looks like KML
                    if (!lowerName.endsWith(".kml")) filename = filename + ".kml";
                } else if (fileContent.contains(",") || fileContent.contains(";") || fileContent.contains("\t")) {
                    // Could be CSV
                    if (!lowerName.endsWith(".csv")) filename = filename + ".csv";
                } else {
                    Log.w(TAG, "Unrecognized file format for: " + filename);
                    return;
                }
            }

            pendingFileJson = fileContent;
            pendingFileName = filename;
            Log.i(TAG, "File ready for injection: " + filename + " (" + fileContent.length() + " bytes)");

        } catch (Exception e) {
            Log.e(TAG, "Error reading file intent: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * Gets the display name of a file from its URI using ContentResolver.
     */
    private String getFileDisplayName(Uri uri) {
        String result = null;
        if ("content".equals(uri.getScheme())) {
            try {
                Cursor cursor = getContentResolver().query(uri, null, null, null, null);
                if (cursor != null && cursor.moveToFirst()) {
                    int nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                    if (nameIndex >= 0) {
                        result = cursor.getString(nameIndex);
                    }
                }
                if (cursor != null) cursor.close();
            } catch (Exception e) {
                Log.w(TAG, "Could not query file name: " + e.getMessage());
            }
        }
        if (result == null) {
            result = uri.getLastPathSegment();
        }
        return result;
    }

    /**
     * Injects the pending file content into the WebView via JavaScript.
     * Uses Base64 encoding to avoid JSON escaping issues.
     */
    private void injectFileToWebView() {
        if (pendingFileJson == null || webView == null) return;

        try {
            // Base64-encode to avoid any escaping issues with quotes, newlines, etc.
            String b64 = Base64.encodeToString(
                pendingFileJson.getBytes("UTF-8"), Base64.NO_WRAP);
            String safeName = pendingFileName
                .replace("\\", "\\\\")
                .replace("'", "\\'");

            // Call app.receiveFileFromIntent(filename, contentBase64)
            // The JS side will atob() decode it
            String js = "if(typeof app!=='undefined' && app.receiveFileFromIntent){" +
                        "app.receiveFileFromIntent('" + safeName + "',atob('" + b64 + "'));" +
                        "} else { console.warn('[Native] app.receiveFileFromIntent not available'); }";

            Log.i(TAG, "Injecting file into WebView: " + pendingFileName);
            webView.evaluateJavascript(js, null);

        } catch (Exception e) {
            Log.e(TAG, "Error injecting file: " + e.getMessage());
        }

        pendingFileJson = null;
        pendingFileName = null;
    }
}
