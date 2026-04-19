const {TwaManifest, TwaGenerator, JdkHelper, AndroidSdkTools, GradleWrapper, ConsoleLog, Config} = require('@bubblewrap/core');
const path = require('path');
const fs = require('fs');

const JAVA_HOME = 'C:\Program Files\Microsoft\jdk-21.0.10.7-hotspot';
const ANDROID_HOME = 'C:\Users\Usuario\Downloads\PIX-MUESTREO\android-sdk';
const KS_PATH = 'C:\Users\Usuario\Downloads\PIX-MUESTREO\pixadvisor.keystore';
const KS_PASS = 'pixadvisor123';
const KS_ALIAS = 'pixadvisor';
const OUTPUT_DIR = path.resolve('.');

async function build() {
  const log = new ConsoleLog('build');
  
  // Create TwaManifest  
  const manifest = new TwaManifest({
    packageId: 'network.pixadvisor.muestreo',
    host: 'pixadvisor.network',
    name: 'PIX Muestreo',
    launcherName: 'PIX Muestreo',
    display: 'standalone',
    themeColor: '#0F1B2D',
    themeColorDark: '#0F1B2D',
    navigationColor: '#0F1B2D',
    navigationColorDark: '#0F1B2D',
    navigationDividerColor: '#0F1B2D',
    navigationDividerColorDark: '#0F1B2D',
    backgroundColor: '#0F1B2D',
    startUrl: '/pix-muestreo/',
    iconUrl: 'https://pixadvisor.network/pix-muestreo/icons/icon-512.png',
    maskableIconUrl: 'https://pixadvisor.network/pix-muestreo/icons/icon-512.png',
    monochromeIconUrl: 'https://pixadvisor.network/pix-muestreo/icons/icon-512.png',
    shortcuts: [],
    signingKey: { path: KS_PATH, alias: KS_ALIAS },
    appVersionCode: 3,
    appVersionName: '3.0.0',
    webManifestUrl: 'https://pixadvisor.network/pix-muestreo/manifest.json',
    generatorApp: 'bubblewrap-cli',
    fallbackType: 'webview',
    enableSiteSettingsShortcut: true,
    fullScopeUrl: 'https://pixadvisor.network/pix-muestreo/',
    minSdkVersion: 24,
    orientation: 'portrait',
    fingerprints: [{
      name: 'pixadvisor',
      value: '95:15:E0:97:5D:6C:89:A1:F1:43:54:1E:F5:D2:F0:36:8B:FF:48:E9:70:86:47:DB:3F:3F:86:3E:26:C3:2F:1C'
    }]
  });

  console.log('Manifest created:', manifest.packageId);

  // Setup JDK and Android SDK
  const jdkHelper = new JdkHelper(process, JAVA_HOME);
  const androidSdk = new AndroidSdkTools(process, jdkHelper, ANDROID_HOME, log);

  console.log('JDK:', JAVA_HOME);
  console.log('SDK:', ANDROID_HOME);

  // Generate project
  const twaGenerator = new TwaGenerator(log);
  await twaGenerator.createTwaProject(OUTPUT_DIR, manifest);
  console.log('Project generated');

  // Build with Gradle
  const gradle = new GradleWrapper(process, jdkHelper, OUTPUT_DIR);
  console.log('Building APK...');
  await gradle.assembleRelease();
  console.log('APK built!');

  // Sign
  const apkPath = path.join(OUTPUT_DIR, 'app', 'build', 'outputs', 'apk', 'release', 'app-release-unsigned.apk');
  if (fs.existsSync(apkPath)) {
    console.log('APK found:', apkPath);
    // Copy to downloads
    const dest = 'C:\Users\Usuario\Downloads\PIX-Muestreo-OFFLINE-FULL.apk';
    fs.copyFileSync(apkPath, dest);
    console.log('Copied to:', dest);
  } else {
    console.log('APK not at expected path, searching...');
    const {execSync} = require('child_process');
    const found = execSync('find . -name "*.apk" 2>/dev/null || dir /s /b *.apk 2>nul').toString();
    console.log('Found APKs:', found);
  }
}

build().catch(e => console.error('BUILD ERROR:', e.message || e));
