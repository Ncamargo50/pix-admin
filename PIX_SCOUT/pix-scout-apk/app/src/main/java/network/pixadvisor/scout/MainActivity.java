package network.pixadvisor.scout;

import android.Manifest;
import android.annotation.SuppressLint;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.view.ViewGroup;
import android.webkit.GeolocationPermissions;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;

import androidx.activity.OnBackPressedCallback;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.webkit.ServiceWorkerClientCompat;
import androidx.webkit.ServiceWorkerControllerCompat;
import androidx.webkit.WebViewAssetLoader;
import androidx.webkit.WebViewClientCompat;
import androidx.webkit.WebViewFeature;

import java.util.ArrayList;
import java.util.List;

/**
 * PIX Scout — contenedor WebView offline-first.
 * Sirve la PWA desde los assets bajo un ORIGEN SEGURO (https://appassets.androidplatform.net/assets/)
 * con WebViewAssetLoader → IndexedDB, getUserMedia (cámara) y geolocalización funcionan 100% offline.
 */
public class MainActivity extends AppCompatActivity {

    private static final String HOST = "appassets.androidplatform.net";
    private static final String BASE = "https://" + HOST + "/assets/index.html";
    private static final int REQ_PERMS = 101;

    private WebView web;
    private ValueCallback<Uri[]> fileCallback;

    // Selector de archivos (fallback <input type=file>) — API moderna, no deprecada.
    private final ActivityResultLauncher<Intent> fileChooser =
        registerForActivityResult(new ActivityResultContracts.StartActivityForResult(), result -> {
            Uri[] out = null;
            if (result.getResultCode() == RESULT_OK && result.getData() != null
                    && result.getData().getData() != null) {
                out = new Uri[]{ result.getData().getData() };
            }
            if (fileCallback != null) { fileCallback.onReceiveValue(out); fileCallback = null; }
        });

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        requestRuntimePermissions();   // ubicación (GPS) + cámara

        final WebViewAssetLoader assetLoader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();

        // Rutea también las peticiones del service worker por el asset loader (offline confiable).
        if (WebViewFeature.isFeatureSupported(WebViewFeature.SERVICE_WORKER_BASIC_USAGE)) {
            ServiceWorkerControllerCompat swController = ServiceWorkerControllerCompat.getInstance();
            swController.setServiceWorkerClient(new ServiceWorkerClientCompat() {
                @Nullable @Override
                public WebResourceResponse shouldInterceptRequest(@NonNull WebResourceRequest request) {
                    return assetLoader.shouldInterceptRequest(request.getUrl());
                }
            });
        }

        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);          // localStorage / IndexedDB
        s.setGeolocationEnabled(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setSupportZoom(false);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);

        web.setWebViewClient(new WebViewClientCompat() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                return assetLoader.shouldInterceptRequest(request.getUrl());
            }
            // Allow-list: solo el origen interno navega dentro del WebView; el resto abre en el navegador.
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri u = request.getUrl();
                String host = u.getHost();
                if (host != null && host.equals(HOST)) return false;   // interno → cargar aquí
                try { startActivity(new Intent(Intent.ACTION_VIEW, u)); } catch (Exception ignored) {}
                return true;                                           // externo → navegador del sistema
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            // Geolocalización: SOLO al origen interno de la app.
            @Override
            public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback cb) {
                boolean ok = origin != null && origin.startsWith("https://" + HOST);
                cb.invoke(origin, ok, false);
            }
            // Cámara (getUserMedia): conceder SOLO captura de video; denegar el resto (mic, etc.).
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                runOnUiThread(() -> {
                    List<String> allow = new ArrayList<>();
                    for (String r : request.getResources()) {
                        if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(r)) allow.add(r);
                    }
                    if (!allow.isEmpty()) request.grant(allow.toArray(new String[0]));
                    else request.deny();
                });
            }
            // Fallback <input type=file> con API moderna (ActivityResultLauncher).
            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, FileChooserParams params) {
                fileCallback = filePathCallback;
                try { fileChooser.launch(params.createIntent()); }
                catch (Exception e) { fileCallback = null; return false; }
                return true;
            }
        });

        setContentView(web);

        // Back moderno (OnBackPressedDispatcher) — no usa onBackPressed() deprecado.
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override public void handleOnBackPressed() {
                if (web != null && web.canGoBack()) { web.goBack(); }
                else { setEnabled(false); getOnBackPressedDispatcher().onBackPressed(); }
            }
        });

        if (savedInstanceState != null) web.restoreState(savedInstanceState);
        else web.loadUrl(BASE);
    }

    private void requestRuntimePermissions() {
        String[] perms = { Manifest.permission.ACCESS_FINE_LOCATION,
                           Manifest.permission.ACCESS_COARSE_LOCATION,
                           Manifest.permission.CAMERA };
        boolean need = false;
        for (String p : perms)
            if (ContextCompat.checkSelfPermission(this, p) != PackageManager.PERMISSION_GRANTED) { need = true; break; }
        if (need) ActivityCompat.requestPermissions(this, perms, REQ_PERMS);
    }

    @Override protected void onPause() {
        if (web != null) { web.onPause(); web.pauseTimers(); }   // pausa timers/GPS/cámara en background
        super.onPause();
    }
    @Override protected void onResume() {
        super.onResume();
        if (web != null) { web.onResume(); web.resumeTimers(); }
    }
    @Override protected void onDestroy() {
        if (web != null) {
            ViewGroup p = (ViewGroup) web.getParent();
            if (p != null) p.removeView(web);
            web.destroy(); web = null;
        }
        super.onDestroy();
    }

    @Override public void onSaveInstanceState(@NonNull Bundle out) {
        super.onSaveInstanceState(out);
        if (web != null) web.saveState(out);
    }
}
