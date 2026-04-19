package network.pixadvisor.muestreo;

import android.app.Activity;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import com.google.android.gms.tasks.Task;
import com.google.android.play.core.integrity.IntegrityManager;
import com.google.android.play.core.integrity.IntegrityManagerFactory;
import com.google.android.play.core.integrity.IntegrityTokenRequest;
import com.google.android.play.core.integrity.IntegrityTokenResponse;

/**
 * Play Integrity API bridge.
 *
 * JS contract:
 *   window.PixIntegrity.requestToken(nonce)
 *       → resolves via window event 'pix:integrity' with { ok, token, error }.
 *
 * The `nonce` is a fresh random value from the server (Supabase Edge Function)
 * that must be echoed in the token and verified server-side against Google's
 * Play Integrity verdict endpoint. Without server-side verification this gate
 * is worthless — see docs/INTEGRITY.md for the backend flow.
 *
 * Cloud project number: Play Console → App Integrity → Cloud project number.
 * Stored in strings.xml as `integrity_cloud_project` so it can be swapped per
 * environment without recompiling. If it's the default zero value we skip the
 * request entirely (feature disabled in dev builds).
 */
public class IntegrityBridge {
    private static final String TAG = "PixIntegrity";
    private final Activity hostActivity;
    private final WebView webView;
    private final Handler mainHandler;

    public IntegrityBridge(Activity activity, WebView webView) {
        this.hostActivity = activity;
        this.webView = webView;
        this.mainHandler = new Handler(Looper.getMainLooper());
    }

    @JavascriptInterface
    public void requestToken(final String nonce) {
        if (nonce == null || nonce.length() < 16 || nonce.length() > 500) {
            pushResult(false, null, "invalid-nonce");
            return;
        }
        long cloudProject = 0L;
        try {
            int resId = hostActivity.getResources().getIdentifier(
                "integrity_cloud_project", "string", hostActivity.getPackageName());
            if (resId != 0) {
                String s = hostActivity.getResources().getString(resId);
                cloudProject = Long.parseLong(s);
            }
        } catch (Exception e) {
            // Missing / malformed resource → treat as disabled.
            cloudProject = 0L;
        }
        if (cloudProject == 0L) {
            // Feature disabled (no cloud project configured). Surface a
            // distinct "disabled" status so the server can decide whether
            // to hard-fail or soft-accept.
            pushResult(false, null, "disabled");
            return;
        }

        try {
            IntegrityManager manager = IntegrityManagerFactory.create(hostActivity);
            IntegrityTokenRequest.Builder b = IntegrityTokenRequest.builder()
                .setNonce(nonce)
                .setCloudProjectNumber(cloudProject);
            Task<IntegrityTokenResponse> task = manager.requestIntegrityToken(b.build());
            task.addOnSuccessListener(response -> {
                String token = response != null ? response.token() : null;
                pushResult(token != null, token, token == null ? "empty-token" : null);
            });
            task.addOnFailureListener(err -> {
                String msg = err != null ? err.getMessage() : "unknown";
                Log.w(TAG, "integrity request failed: " + msg);
                pushResult(false, null, "err: " + (msg != null ? msg.replace("'", "") : "unknown"));
            });
        } catch (Exception e) {
            Log.e(TAG, "requestToken threw", e);
            pushResult(false, null, "exception: " + e.getClass().getSimpleName());
        }
    }

    private void pushResult(final boolean ok, final String token, final String error) {
        if (webView == null) return;
        mainHandler.post(new Runnable() {
            @Override public void run() {
                String safeTok = token == null ? "null" : ("'" + token.replace("'", "\\'").replace("\\", "\\\\") + "'");
                String safeErr = error == null ? "null" : ("'" + error.replace("'", "\\'").replace("\\", "\\\\") + "'");
                String js = "window.dispatchEvent(new CustomEvent('pix:integrity',{detail:{ok:"
                    + (ok ? "true" : "false") + ",token:" + safeTok + ",error:" + safeErr + "}}));";
                try {
                    webView.evaluateJavascript(js, null);
                } catch (Exception e) {
                    Log.w(TAG, "evaluateJavascript failed", e);
                }
            }
        });
    }
}
