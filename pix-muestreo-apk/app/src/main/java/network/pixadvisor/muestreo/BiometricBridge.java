package network.pixadvisor.muestreo;

import android.app.Activity;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import androidx.biometric.BiometricManager;
import androidx.biometric.BiometricPrompt;
import androidx.core.content.ContextCompat;
import androidx.fragment.app.FragmentActivity;

/**
 * JS-interface for biometric auth. Called from JS as:
 *
 *   window.PixBiometric.isAvailable()
 *       → "yes" | "no-hardware" | "no-enrolled"
 *
 *   window.PixBiometric.prompt(tag, title, subtitle)
 *       → fires Android BiometricPrompt; result pushed back to JS via
 *         window.dispatchEvent('pix:biometric', { detail:{ tag, ok, error }}).
 *
 * SECURITY: we gate prompts to STRONG biometric only (Class 3) to exclude
 * face-unlock implementations that don't meet the NIST bar. DEVICE_CREDENTIAL
 * (PIN/pattern) is allowed as a fallback so users without fingerprint can
 * still use the gate — the goal is "authenticated user at the phone", not
 * "specific biometric modality".
 *
 * We require FragmentActivity for BiometricPrompt. OfflineActivity extends
 * plain Activity, so this bridge holds its own FragmentActivity reference
 * and is only wired in when the host activity qualifies. If not, isAvailable
 * returns "no-hardware" and prompts no-op-fail gracefully.
 */
public class BiometricBridge {
    private static final String TAG = "PixBiometric";
    private final Activity hostActivity;
    private final WebView webView;
    private final Handler mainHandler;

    // Acceptable authenticators: STRONG biometric (Class 3) + device credential
    // fallback (PIN / pattern / password). This matches the Play recommendation
    // for "soft gate" prompts that protect in-app sensitive ops.
    private static final int AUTHENTICATORS =
        BiometricManager.Authenticators.BIOMETRIC_STRONG
            | BiometricManager.Authenticators.DEVICE_CREDENTIAL;

    public BiometricBridge(Activity activity, WebView webView) {
        this.hostActivity = activity;
        this.webView = webView;
        this.mainHandler = new Handler(Looper.getMainLooper());
    }

    @JavascriptInterface
    public String isAvailable() {
        try {
            BiometricManager bm = BiometricManager.from(hostActivity);
            int code = bm.canAuthenticate(AUTHENTICATORS);
            switch (code) {
                case BiometricManager.BIOMETRIC_SUCCESS:
                    return "yes";
                case BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE:
                case BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE:
                case BiometricManager.BIOMETRIC_ERROR_UNSUPPORTED:
                    return "no-hardware";
                case BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED:
                    return "no-enrolled";
                default:
                    return "no-hardware";
            }
        } catch (Exception e) {
            Log.w(TAG, "isAvailable failed", e);
            return "no-hardware";
        }
    }

    @JavascriptInterface
    public void prompt(final String tag, final String title, final String subtitle) {
        // Sanity: reject empty / absurd tags (JS→Java bridge is untrusted).
        if (tag == null || tag.isEmpty() || tag.length() > 64) {
            pushResult("invalid", false, "invalid-tag");
            return;
        }
        final String safeTitle = (title != null && title.length() <= 120) ? title : "Confirmá tu identidad";
        final String safeSub = (subtitle != null && subtitle.length() <= 200) ? subtitle : "";

        // BiometricPrompt MUST be constructed on the main thread and, per the
        // current androidx.biometric contract, bound to a FragmentActivity.
        // OfflineActivity doesn't extend FragmentActivity, so we use the
        // activity's support executor and bail gracefully if the cast fails.
        if (!(hostActivity instanceof FragmentActivity)) {
            pushResult(tag, false, "host-not-fragment-activity");
            return;
        }
        final FragmentActivity fa = (FragmentActivity) hostActivity;

        mainHandler.post(new Runnable() {
            @Override public void run() {
                try {
                    BiometricPrompt.PromptInfo.Builder b = new BiometricPrompt.PromptInfo.Builder()
                        .setTitle(safeTitle)
                        .setSubtitle(safeSub)
                        .setAllowedAuthenticators(AUTHENTICATORS);
                    // Negative button is REQUIRED unless DEVICE_CREDENTIAL is in
                    // the authenticators — we include it, so no negative button.
                    BiometricPrompt.PromptInfo info = b.build();

                    BiometricPrompt bp = new BiometricPrompt(
                        fa,
                        ContextCompat.getMainExecutor(hostActivity),
                        new BiometricPrompt.AuthenticationCallback() {
                            @Override
                            public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult result) {
                                pushResult(tag, true, null);
                            }
                            @Override
                            public void onAuthenticationError(int errorCode, CharSequence errString) {
                                pushResult(tag, false, "err-" + errorCode);
                            }
                            @Override
                            public void onAuthenticationFailed() {
                                // One failed attempt — OS keeps prompt open.
                                // We only surface terminal errors to JS.
                            }
                        }
                    );
                    bp.authenticate(info);
                } catch (Exception e) {
                    Log.e(TAG, "prompt failed", e);
                    pushResult(tag, false, "exception: " + e.getClass().getSimpleName());
                }
            }
        });
    }

    private void pushResult(final String tag, final boolean ok, final String error) {
        if (webView == null) return;
        mainHandler.post(new Runnable() {
            @Override public void run() {
                // Sanitize inputs for JS string interpolation.
                String safeTag = tag == null ? "" : tag.replace("'", "\\'").replace("\\", "\\\\");
                String safeErr = error == null ? "null" : ("'" + error.replace("'", "\\'").replace("\\", "\\\\") + "'");
                String js = "window.dispatchEvent(new CustomEvent('pix:biometric',{detail:{tag:'"
                    + safeTag + "',ok:" + (ok ? "true" : "false") + ",error:" + safeErr + "}}));";
                try {
                    webView.evaluateJavascript(js, null);
                } catch (Exception e) {
                    Log.w(TAG, "evaluateJavascript failed", e);
                }
            }
        });
    }
}
