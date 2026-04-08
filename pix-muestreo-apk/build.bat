@echo off
set ANDROID_HOME=C:\Users\Usuario\Downloads\PIX-MUESTREO\android-sdk
set ANDROID_SDK_ROOT=C:\Users\Usuario\Downloads\PIX-MUESTREO\android-sdk
set JAVA_HOME=C:\Program Files\Microsoft\jdk-21.0.10.7-hotspot
set BUILD_TOOLS=%ANDROID_HOME%\build-tools\35.0.0
set KS_PATH=C:\Users\Usuario\Downloads\PIX-MUESTREO\pixadvisor.keystore
set KS_ALIAS=pixadvisor
set KS_PASS=pixadvisor123
set OUTPUT_DIR=D:\PIXADVISOR_AGENT_WORKSPACE\pix-muestreo-apk\app\build\outputs\apk\release
set FINAL_APK=C:\Users\Usuario\Downloads\PIX-Muestreo-v3.4.1-audit-fix.apk

echo JAVA_HOME=%JAVA_HOME%
echo ANDROID_HOME=%ANDROID_HOME%

cd /d D:\PIXADVISOR_AGENT_WORKSPACE\pix-muestreo-apk

echo === Building unsigned APK ===
call gradlew.bat assembleRelease --no-daemon
echo BUILD EXIT CODE: %ERRORLEVEL%
if %ERRORLEVEL% neq 0 (
    echo BUILD FAILED
    exit /b 1
)

echo === Zipaligning APK ===
"%BUILD_TOOLS%\zipalign.exe" -f 4 "%OUTPUT_DIR%\app-release-unsigned.apk" "%OUTPUT_DIR%\app-release-aligned.apk"
if not exist "%OUTPUT_DIR%\app-release-aligned.apk" (
    echo Trying with app-release.apk...
    "%BUILD_TOOLS%\zipalign.exe" -f 4 "%OUTPUT_DIR%\app-release.apk" "%OUTPUT_DIR%\app-release-aligned.apk"
)

echo === Signing APK with apksigner (v1+v2+v3) ===
"%JAVA_HOME%\bin\java.exe" -jar "%BUILD_TOOLS%\lib\apksigner.jar" sign ^
  --ks "%KS_PATH%" ^
  --ks-key-alias "%KS_ALIAS%" ^
  --ks-pass "pass:%KS_PASS%" ^
  --key-pass "pass:%KS_PASS%" ^
  --v1-signing-enabled true ^
  --v2-signing-enabled true ^
  --v3-signing-enabled true ^
  --out "%FINAL_APK%" ^
  "%OUTPUT_DIR%\app-release-aligned.apk"
echo SIGN EXIT CODE: %ERRORLEVEL%

echo === Verifying signature ===
"%JAVA_HOME%\bin\java.exe" -jar "%BUILD_TOOLS%\lib\apksigner.jar" verify --verbose "%FINAL_APK%"

echo === Done ===
echo Output: %FINAL_APK%
del "%OUTPUT_DIR%\app-release-aligned.apk" 2>nul
