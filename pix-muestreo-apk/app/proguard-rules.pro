# ==========================================================================
# PIX Muestreo — ProGuard / R8 rules for release build
# ==========================================================================
# With minifyEnabled=true, R8 will strip "unused" code. Our Java classes are
# invoked by the TWA runtime and via @JavascriptInterface from WebView, both
# of which use reflection and are invisible to static analysis. Without these
# keep rules, the release build will silently break GPS bridge + file sharing
# at runtime.
# ==========================================================================

# --- Trusted Web Activity runtime ----------------------------------------
# androidbrowserhelper uses reflection for CustomTabs/TWA callbacks. Keep the
# whole library to avoid surprise NPEs on launch.
-keep class com.google.androidbrowserhelper.** { *; }
-keep class androidx.browser.** { *; }
-keep class androidx.browser.trusted.** { *; }
-dontwarn com.google.androidbrowserhelper.**

# --- Biometric (androidx.biometric.BiometricPrompt lifecycle) -----------
# BiometricPrompt binds via FragmentManager using reflection on internal
# fragment classes. Without these rules R8 renames them to 1–2 letter names
# and the prompt fires ClassNotFoundException / IllegalStateException on
# first invocation.
-keep class androidx.biometric.** { *; }
-keep class androidx.fragment.app.FragmentActivity { *; }
-keep class androidx.fragment.app.** { *; }
-dontwarn androidx.biometric.**

# --- Play Integrity + Play Services Tasks --------------------------------
# IntegrityManagerFactory.create() → IntegrityManager.requestIntegrityToken()
# returns a Task<IntegrityTokenResponse>. The whole chain uses runtime
# proxies + AIDL-style interfaces. Any class renaming = guaranteed crash
# the first time we request a token on a real device.
-keep class com.google.android.play.core.integrity.** { *; }
-keep class com.google.android.play.integrity.** { *; }
-keep interface com.google.android.play.core.integrity.** { *; }
-keep class com.google.android.gms.tasks.** { *; }
-keep class com.google.android.gms.common.** { *; }
-dontwarn com.google.android.play.**
-dontwarn com.google.android.gms.**

# --- WebView JavaScript bridges -----------------------------------------
# Anything tagged with @JavascriptInterface MUST keep its method names intact
# or window.AndroidGNSS.* / window.AndroidBridge.* calls from JS break.
-keepattributes JavascriptInterface
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# Our custom TWA/WebView classes (LauncherActivity, DelegationService, GNSSBridge, etc.)
-keep class network.pixadvisor.muestreo.** { *; }

# --- Android framework boilerplate that R8 already knows about, but ---
# --- repeating them is cheap insurance ---
-keep public class * extends android.app.Activity
-keep public class * extends android.app.Application
-keep public class * extends android.app.Service
-keep public class * extends android.content.BroadcastReceiver
-keep public class * extends android.content.ContentProvider

# --- Parcelable / Serializable --------------------------------------------
-keepclassmembers class * implements android.os.Parcelable {
    public static final android.os.Parcelable$Creator CREATOR;
}
-keepnames class * implements java.io.Serializable
-keepclassmembers class * implements java.io.Serializable {
    static final long serialVersionUID;
    private static final java.io.ObjectStreamField[] serialPersistentFields;
    private void writeObject(java.io.ObjectOutputStream);
    private void readObject(java.io.ObjectInputStream);
    java.lang.Object writeReplace();
    java.lang.Object readResolve();
}

# --- Keep line numbers for crash reports --------------------------------
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile

# --- Strip all Log.v / Log.d calls in release (reduces APK + leaks) ---
# Uncomment if you want verbose/debug logs dropped entirely:
# -assumenosideeffects class android.util.Log {
#     public static *** v(...);
#     public static *** d(...);
# }

# --- Quiet noisy warnings that don't affect behavior ---------------------
-dontwarn org.conscrypt.**
-dontwarn org.bouncycastle.**
-dontwarn org.openjsse.**
-dontwarn javax.annotation.**
