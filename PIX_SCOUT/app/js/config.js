/* PIX Scout — configuración de runtime.
   En producción, SUPABASE_URL/ANON_KEY se inyectan en el build o desde el panel admin.
   Dejar vacío = la app funciona 100% offline y encola las validaciones localmente. */
window.PIXCONFIG = {
  APP_NAME: 'PIX Scout',
  APP_VERSION: '1.0.9',
  // Focos de ejemplo (5 haciendas distintas). SOLO para capturas: si el GeoJSON real
  // falla, con esto en true el tecnico navega a otra finca sin enterarse.
  DEMO_FOCOS: false,
  // MODO CIEGO (protocolo de validacion). Oculta severidad, score y nivel ANTES de
  // que el tecnico registre: si sabe que va a un rojo, encuentra algo. El dato se
  // guarda igual en `estrato`. Encender durante la campaña de validacion.
  MODO_CIEGO: false,
  // Modo desarrollo: habilita atajos ?demo= (capturas). DEBE ir en false en producción.
  DEV_MODE: false,
  // PEGAR ACA las dos credenciales de Supabase (Project Settings -> API) para encender
  // el lazo de retorno. Pasos completos y esquema SQL en ../../backend/README.md.
  // Mientras esten vacias, la app funciona 100% offline y las validaciones se acumulan
  // en el telefono sin llegar nunca al servidor.
  // OJO: esta clave queda DENTRO del APK, o sea es publica. La tabla es append-only a
  // proposito (solo INSERT); leer se hace server-side con la service_role key.
  SUPABASE_URL: '',          // p.ej. 'https://xxxx.supabase.co'
  SUPABASE_ANON_KEY: '',
  VALIDACIONES_TABLE: 'scout_validaciones',
  // Endpoint del pipeline de anomalías (GeoJSON de focos). Vacío = usar focos empaquetados.
  // Acepta {campo} como marcador; si no lo lleva, se le agrega /<campo>.geojson al final.
  // Ej: 'https://raw.githubusercontent.com/Ncamargo50/pixadvisor-monitoreo-trigo/main/reports/ultimo'
  // Lo que baja queda cacheado: si no hay señal, el técnico sale con la última descarga.
  FOCOS_ENDPOINT: '',
  // GeoJSON de anomalías empaquetado a cargar al iniciar (data/<nombre>.geojson). Vacío = focos de ejemplo.
  DEFAULT_FOCOS: 'santo_antonio',
  // Base satelital (tiles XYZ). Esri World Imagery no requiere API key. Se cachea para uso offline.
  SAT_TILES: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Esri · Maxar · Earthstar Geographics',
    maxZoom: 19
  },
  SAT_DEFAULT: true,   // arrancar con la capa satelital encendida (si hay/estuvo señal)
  GPS: { enableHighAccuracy: true, maximumAge: 5000, timeout: 15000 },
  // Margen de precisión: dentro de este radio (m) se considera "en el foco".
  PROXIMITY_M: 15,
  // Autenticación
  AUTH: {
    REQUIRE: true,           // exigir login para usar la app
    PBKDF2_ITERS: 210000,    // costo del hash (offline, contra fuerza bruta)
    MIN_PASSWORD: 6,         // longitud mínima de contraseña
    OFFLINE_TTL_DAYS: 45,    // sesión válida sin reconectar (campo sin señal)
    USERS_TABLE: 'scout_users' // tabla Supabase para el modo multi-dispositivo (opcional)
  }
};
