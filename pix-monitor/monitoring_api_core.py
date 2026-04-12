"""
PIX Monitor — Crop Monitoring API Server
Satellite-based crop health monitoring with automatic anomaly detection.

Port: 9102
Auth: Service account via GEE token proxy (9101)
Credentials: Shared with user-api.py (9105)
Storage: monitoring.db.json (local JSON)

Endpoints:
  POST /api/clients              → Create client
  GET  /api/clients              → List clients
  POST /api/fields               → Register field with boundary
  GET  /api/fields               → List fields
  PUT  /api/fields/{id}          → Update field
  POST /api/fields/{id}/activate → Activate monitoring
  POST /api/fields/{id}/check    → Run anomaly check (GEE)
  GET  /api/alerts               → List all alerts
  GET  /api/timeseries/{id}      → Get time series for field
  POST /api/reports/{id}         → Generate PDF + KMZ
  GET  /api/health               → Health check
"""

import json
import os
import sys
import time
import random
import string
import hashlib
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PORT = 9102
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'monitoring.db.json')

# GEE Service Account Key
GEE_KEY_PATH = os.environ.get('GEE_KEY_PATH', r'C:\Users\Usuario\Desktop\PIXADVISOR\ee-gisagronomico-key.json')
GEE_PROJECT = os.environ.get('GEE_PROJECT', 'ee-gisagronomico')
GEE_SERVICE_ACCOUNT_KEY = os.environ.get('GEE_SERVICE_ACCOUNT_KEY', '')  # JSON string for cloud deploy

# ============================================================
# CROP PHENOLOGY CONFIGURATION
# ============================================================

CROP_PHENOLOGY = {
    "soja": {
        "name": "Soja",
        "cycle_days": 130,
        "stages": {
            "VE_V3": {
                "days": [
                    0,
                    25
                ],
                "primary": "MSAVI2",
                "reason": "R2=0.85 baja cobertura/suelo",
                "indices": [
                    "MSAVI2",
                    "OSAVI",
                    "BSI",
                    "NDVI",
                    "SAVI",
                    "SALINITY",
                    "CWSI",
                    "SIF_proxy",
                    "TCARI_OSAVI"
                ],
                "weed_indices": [
                    "NDVI",
                    "MSAVI2"
                ],
                "weed_risk": "alto",
                "desc": "Emergencia (VE-V3) — Suelo expuesto, malezas"
            },
            "V4_V8": {
                "days": [
                    25,
                    50
                ],
                "primary": "SIF_proxy",
                "reason": "Fluorescencia fotosintesis R2=0.72 Israel",
                "indices": [
                    "NDVI",
                    "NDRE",
                    "GNDVI",
                    "MTCI",
                    "CCCI",
                    "PRI_proxy",
                    "SIF_proxy",
                    "CWSI",
                    "TCARI_OSAVI",
                    "SALINITY"
                ],
                "weed_indices": [
                    "NDVI",
                    "GNDVI",
                    "PRI_proxy"
                ],
                "weed_risk": "medio",
                "desc": "Vegetativo (V4-V8)"
            },
            "R1_R2": {
                "days": [
                    50,
                    70
                ],
                "primary": "TCARI_OSAVI",
                "reason": "Volcani: clorofila R2=0.81 etapa critica",
                "indices": [
                    "NDRE",
                    "MTCI",
                    "kNDVI",
                    "EVI",
                    "NDMI",
                    "S2REP",
                    "IRECI",
                    "TCARI_OSAVI",
                    "SIF_proxy",
                    "CWSI",
                    "SALINITY"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Floracion (R1-R2) — Etapa critica"
            },
            "R3_R5": {
                "days": [
                    70,
                    100
                ],
                "primary": "kNDVI",
                "reason": "Anti-saturacion canopy denso Nature 2021",
                "indices": [
                    "NDRE",
                    "kNDVI",
                    "S2REP",
                    "CCCI",
                    "NDMI",
                    "IRECI",
                    "MTCI",
                    "TCARI_OSAVI",
                    "CWSI",
                    "SIF_proxy",
                    "SALINITY"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Llenado (R3-R5) — Maxima biomasa"
            },
            "R6_R8": {
                "days": [
                    100,
                    130
                ],
                "primary": "PSRI",
                "reason": "Mejor detector senescencia y madurez",
                "indices": [
                    "NDMI",
                    "PSRI",
                    "NBR2",
                    "NDRE",
                    "MSI",
                    "CWSI",
                    "SALINITY",
                    "TCARI_OSAVI",
                    "SIF_proxy"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Maduracion (R6-R8) — Senescencia"
            }
        },
        "critical_stages": [
            "R1_R2",
            "R3_R5"
        ],
        "weed_detection": {
            "method": "spatial_anomaly",
            "ndvi_weed_threshold": 0.2,
            "critical_window_days": [
                0,
                50
            ],
            "desc": "NDVI anomalo entresurco"
        }
    },
    "maiz": {
        "name": "Maiz",
        "cycle_days": 150,
        "stages": {
            "VE_V6": {
                "days": [
                    0,
                    30
                ],
                "primary": "MSAVI2",
                "reason": "R2=0.85 baja cobertura",
                "indices": [
                    "MSAVI2",
                    "OSAVI",
                    "BSI",
                    "NDVI",
                    "SAVI",
                    "SALINITY",
                    "CWSI",
                    "SIF_proxy",
                    "TCARI_OSAVI"
                ],
                "weed_indices": [
                    "NDVI",
                    "MSAVI2",
                    "BSI"
                ],
                "weed_risk": "alto",
                "desc": "Emergencia (VE-V6)"
            },
            "V8_V12": {
                "days": [
                    30,
                    55
                ],
                "primary": "NDRE",
                "reason": "Red-edge N foliar crecimiento",
                "indices": [
                    "NDVI",
                    "NDRE",
                    "GNDVI",
                    "MTCI",
                    "CCCI",
                    "PRI_proxy",
                    "SIF_proxy",
                    "CWSI",
                    "TCARI_OSAVI",
                    "SALINITY"
                ],
                "weed_indices": [
                    "NDVI",
                    "GNDVI",
                    "PRI_proxy"
                ],
                "weed_risk": "medio",
                "desc": "Crecimiento (V8-V12)"
            },
            "VT_R1": {
                "days": [
                    55,
                    75
                ],
                "primary": "TCARI_OSAVI",
                "reason": "Volcani: clorofila R2=0.81",
                "indices": [
                    "kNDVI",
                    "NDRE",
                    "MTCI",
                    "EVI",
                    "S2REP",
                    "IRECI",
                    "CCCI",
                    "TCARI_OSAVI",
                    "SIF_proxy",
                    "CWSI",
                    "SALINITY"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Floracion (VT-R1) — Critica"
            },
            "R2_R4": {
                "days": [
                    75,
                    105
                ],
                "primary": "kNDVI",
                "reason": "Anti-saturacion LAI>4",
                "indices": [
                    "kNDVI",
                    "NDRE",
                    "S2REP",
                    "CCCI",
                    "NDMI",
                    "MTCI",
                    "IRECI",
                    "TCARI_OSAVI",
                    "CWSI",
                    "SIF_proxy",
                    "SALINITY"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Llenado (R2-R4)"
            },
            "R5_R6": {
                "days": [
                    105,
                    150
                ],
                "primary": "NDMI",
                "reason": "Humedad foliar llenado grano",
                "indices": [
                    "NDMI",
                    "PSRI",
                    "NBR2",
                    "MSI",
                    "NDRE",
                    "CWSI",
                    "SALINITY",
                    "TCARI_OSAVI",
                    "SIF_proxy"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Maduracion (R5-R6)"
            }
        },
        "critical_stages": [
            "VT_R1",
            "R2_R4"
        ],
        "weed_detection": {
            "method": "spatial_anomaly",
            "ndvi_weed_threshold": 0.22,
            "critical_window_days": [
                0,
                55
            ],
            "desc": "Malezas entresurco"
        }
    },
    "cana": {
        "name": "Cana de Azucar",
        "cycle_days": 365,
        "stages": {
            "BROTACION": {
                "days": [
                    0,
                    90
                ],
                "primary": "MSAVI2",
                "reason": "Suelo + brotes",
                "indices": [
                    "MSAVI2",
                    "OSAVI",
                    "BSI",
                    "NDVI",
                    "SAVI",
                    "NDRE",
                    "EVI2",
                    "NBR2",
                    "SALINITY",
                    "CWSI",
                    "SIF_proxy",
                    "TCARI_OSAVI"
                ],
                "weed_indices": [
                    "NDVI",
                    "BSI",
                    "MSAVI2"
                ],
                "weed_risk": "alto",
                "desc": "Brotacion (0-3m)"
            },
            "MACOLLAJE": {
                "days": [
                    90,
                    150
                ],
                "primary": "NDRE",
                "reason": "Red-edge N macollaje",
                "indices": [
                    "NDRE",
                    "NDVI",
                    "RECI",
                    "CIre",
                    "MTCI",
                    "CCCI",
                    "GNDVI",
                    "PRI_proxy",
                    "SIF_proxy",
                    "CWSI",
                    "TCARI_OSAVI",
                    "SALINITY"
                ],
                "weed_indices": [
                    "NDVI",
                    "GNDVI"
                ],
                "weed_risk": "medio",
                "desc": "Macollaje (3-5m)"
            },
            "GRAN_CRECIMIENTO": {
                "days": [
                    150,
                    240
                ],
                "primary": "TCARI_OSAVI",
                "reason": "Volcani: clorofila canopy R2=0.81",
                "indices": [
                    "NDRE",
                    "RECI",
                    "CIre",
                    "IRECI",
                    "MTCI",
                    "S2REP",
                    "kNDVI",
                    "EVI",
                    "NDMI",
                    "TCARI_OSAVI",
                    "SIF_proxy",
                    "CWSI",
                    "SALINITY"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Gran crecimiento (5-8m)"
            },
            "ELONGACION": {
                "days": [
                    240,
                    330
                ],
                "primary": "kNDVI",
                "reason": "Anti-saturacion LAI>6",
                "indices": [
                    "NDRE",
                    "RECI",
                    "CIre",
                    "IRECI",
                    "MTCI",
                    "S2REP",
                    "kNDVI",
                    "CCCI",
                    "NDMI",
                    "MSI",
                    "TCARI_OSAVI",
                    "CWSI",
                    "SIF_proxy",
                    "SALINITY"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Elongacion (8-11m)"
            },
            "MADURACION": {
                "days": [
                    330,
                    365
                ],
                "primary": "NDMI",
                "reason": "Humedad cosecha",
                "indices": [
                    "NDMI",
                    "NDRE",
                    "RECI",
                    "PSRI",
                    "MSI",
                    "NBR2",
                    "S2REP",
                    "EVI2",
                    "CWSI",
                    "SALINITY",
                    "TCARI_OSAVI",
                    "SIF_proxy"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Maduracion (11-12m)"
            }
        },
        "critical_stages": [
            "GRAN_CRECIMIENTO",
            "ELONGACION"
        ],
        "weed_detection": {
            "method": "spatial_anomaly",
            "ndvi_weed_threshold": 0.25,
            "critical_window_days": [
                0,
                150
            ],
            "desc": "Malezas surcos 1.4m"
        }
    },
    "trigo": {
        "name": "Trigo",
        "cycle_days": 140,
        "stages": {
            "EMERGENCIA": {
                "days": [
                    0,
                    20
                ],
                "primary": "MSAVI2",
                "reason": "Baja cobertura",
                "indices": [
                    "MSAVI2",
                    "OSAVI",
                    "BSI",
                    "NDVI",
                    "SAVI",
                    "SALINITY",
                    "CWSI",
                    "SIF_proxy",
                    "TCARI_OSAVI"
                ],
                "weed_indices": [
                    "NDVI",
                    "BSI",
                    "MSAVI2"
                ],
                "weed_risk": "alto",
                "desc": "Emergencia"
            },
            "MACOLLAJE": {
                "days": [
                    20,
                    50
                ],
                "primary": "SIF_proxy",
                "reason": "Fluorescencia diferencia trigo/maleza",
                "indices": [
                    "NDVI",
                    "NDRE",
                    "GNDVI",
                    "MTCI",
                    "CCCI",
                    "PRI_proxy",
                    "SIF_proxy",
                    "CWSI",
                    "TCARI_OSAVI",
                    "SALINITY"
                ],
                "weed_indices": [
                    "NDVI",
                    "GNDVI",
                    "PRI_proxy"
                ],
                "weed_risk": "medio",
                "desc": "Macollaje"
            },
            "ENCANADO": {
                "days": [
                    50,
                    80
                ],
                "primary": "NDRE",
                "reason": "Red-edge N foliar",
                "indices": [
                    "NDRE",
                    "kNDVI",
                    "EVI",
                    "MTCI",
                    "S2REP",
                    "IRECI",
                    "TCARI_OSAVI",
                    "SIF_proxy",
                    "CWSI",
                    "SALINITY"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Encanado"
            },
            "ESPIGADO": {
                "days": [
                    80,
                    100
                ],
                "primary": "TCARI_OSAVI",
                "reason": "Volcani: maxima sensibilidad R2=0.81",
                "indices": [
                    "NDRE",
                    "kNDVI",
                    "S2REP",
                    "CCCI",
                    "NDMI",
                    "IRECI",
                    "MTCI",
                    "TCARI_OSAVI",
                    "CWSI",
                    "SIF_proxy",
                    "SALINITY"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Espigado — Critica"
            },
            "LLENADO": {
                "days": [
                    100,
                    130
                ],
                "primary": "NDMI",
                "reason": "Humedad foliar llenado",
                "indices": [
                    "NDMI",
                    "PSRI",
                    "NDRE",
                    "NBR2",
                    "MSI",
                    "CWSI",
                    "SALINITY",
                    "TCARI_OSAVI",
                    "SIF_proxy"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Llenado"
            },
            "MADURACION": {
                "days": [
                    130,
                    140
                ],
                "primary": "PSRI",
                "reason": "Senescencia + madurez",
                "indices": [
                    "NDMI",
                    "PSRI",
                    "NBR2",
                    "MSI",
                    "CWSI",
                    "SALINITY",
                    "TCARI_OSAVI",
                    "SIF_proxy"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Maduracion"
            }
        },
        "critical_stages": [
            "ESPIGADO",
            "LLENADO"
        ],
        "weed_detection": {
            "method": "spatial_anomaly",
            "ndvi_weed_threshold": 0.18,
            "critical_window_days": [
                0,
                50
            ],
            "desc": "Malezas hoja ancha"
        }
    },
    "arroz": {
        "name": "Arroz",
        "cycle_days": 140,
        "stages": {
            "EMERGENCIA": {
                "days": [
                    0,
                    25
                ],
                "primary": "MSAVI2",
                "reason": "Baja veg lamina agua",
                "indices": [
                    "MSAVI2",
                    "OSAVI",
                    "NDVI",
                    "SAVI",
                    "SALINITY",
                    "CWSI",
                    "SIF_proxy",
                    "TCARI_OSAVI"
                ],
                "weed_indices": [
                    "NDVI",
                    "MSAVI2"
                ],
                "weed_risk": "alto",
                "desc": "Emergencia"
            },
            "MACOLLAJE": {
                "days": [
                    25,
                    55
                ],
                "primary": "NDRE",
                "reason": "Red-edge N macollaje",
                "indices": [
                    "NDVI",
                    "NDRE",
                    "EVI",
                    "GNDVI",
                    "MTCI",
                    "PRI_proxy",
                    "SIF_proxy",
                    "CWSI",
                    "TCARI_OSAVI",
                    "SALINITY"
                ],
                "weed_indices": [
                    "NDVI",
                    "EVI"
                ],
                "weed_risk": "medio",
                "desc": "Macollaje"
            },
            "PANICULACION": {
                "days": [
                    55,
                    80
                ],
                "primary": "TCARI_OSAVI",
                "reason": "Volcani: clorofila R2=0.81",
                "indices": [
                    "NDRE",
                    "kNDVI",
                    "MTCI",
                    "EVI",
                    "NDMI",
                    "S2REP",
                    "TCARI_OSAVI",
                    "SIF_proxy",
                    "CWSI",
                    "SALINITY"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Paniculacion"
            },
            "FLORACION": {
                "days": [
                    80,
                    100
                ],
                "primary": "kNDVI",
                "reason": "Anti-saturacion LAI alto",
                "indices": [
                    "NDRE",
                    "kNDVI",
                    "S2REP",
                    "CCCI",
                    "NDMI",
                    "IRECI",
                    "TCARI_OSAVI",
                    "CWSI",
                    "SIF_proxy",
                    "SALINITY"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Floracion — Critica"
            },
            "LLENADO": {
                "days": [
                    100,
                    140
                ],
                "primary": "NDMI",
                "reason": "Humedad llenado grano",
                "indices": [
                    "NDMI",
                    "PSRI",
                    "NDRE",
                    "NBR2",
                    "MSI",
                    "CWSI",
                    "SALINITY",
                    "TCARI_OSAVI",
                    "SIF_proxy"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Llenado"
            }
        },
        "critical_stages": [
            "FLORACION",
            "LLENADO"
        ],
        "weed_detection": {
            "method": "spatial_anomaly",
            "ndvi_weed_threshold": 0.2,
            "critical_window_days": [
                0,
                55
            ],
            "desc": "Arroz rojo, capim"
        }
    },
    "girasol": {
        "name": "Girasol",
        "cycle_days": 120,
        "stages": {
            "EMERGENCIA": {
                "days": [
                    0,
                    20
                ],
                "primary": "MSAVI2",
                "reason": "Surcos abiertos",
                "indices": [
                    "MSAVI2",
                    "OSAVI",
                    "BSI",
                    "NDVI",
                    "SAVI",
                    "SALINITY",
                    "CWSI",
                    "SIF_proxy",
                    "TCARI_OSAVI"
                ],
                "weed_indices": [
                    "NDVI",
                    "BSI",
                    "MSAVI2"
                ],
                "weed_risk": "alto",
                "desc": "Emergencia"
            },
            "VEGETATIVO": {
                "days": [
                    20,
                    50
                ],
                "primary": "SIF_proxy",
                "reason": "Fluorescencia R2=0.72",
                "indices": [
                    "NDVI",
                    "NDRE",
                    "GNDVI",
                    "EVI",
                    "MTCI",
                    "PRI_proxy",
                    "SIF_proxy",
                    "CWSI",
                    "TCARI_OSAVI",
                    "SALINITY"
                ],
                "weed_indices": [
                    "NDVI",
                    "GNDVI"
                ],
                "weed_risk": "medio",
                "desc": "Vegetativo"
            },
            "FLORACION": {
                "days": [
                    50,
                    75
                ],
                "primary": "TCARI_OSAVI",
                "reason": "Volcani: clorofila R2=0.81",
                "indices": [
                    "NDRE",
                    "kNDVI",
                    "EVI2",
                    "NDMI",
                    "OSAVI",
                    "S2REP",
                    "IRECI",
                    "TCARI_OSAVI",
                    "SIF_proxy",
                    "CWSI",
                    "SALINITY"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Floracion"
            },
            "LLENADO": {
                "days": [
                    75,
                    100
                ],
                "primary": "CWSI",
                "reason": "Stress hidrico aquenios Israel",
                "indices": [
                    "NDRE",
                    "NDMI",
                    "NBR2",
                    "PSRI",
                    "MSI",
                    "CWSI",
                    "SALINITY",
                    "TCARI_OSAVI",
                    "SIF_proxy"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Llenado"
            },
            "MADURACION": {
                "days": [
                    100,
                    120
                ],
                "primary": "PSRI",
                "reason": "Senescencia capitulo",
                "indices": [
                    "NDMI",
                    "PSRI",
                    "NBR2",
                    "MSI",
                    "CWSI",
                    "SALINITY",
                    "TCARI_OSAVI",
                    "SIF_proxy"
                ],
                "weed_indices": [],
                "weed_risk": "bajo",
                "desc": "Maduracion"
            }
        },
        "critical_stages": [
            "FLORACION",
            "LLENADO"
        ],
        "weed_detection": {
            "method": "spatial_anomaly",
            "ndvi_weed_threshold": 0.2,
            "critical_window_days": [
                0,
                50
            ],
            "desc": "Malezas surcos"
        }
    },
    "pastura": {
        "name": "Pastura (Brachiaria/Panicum)",
        "cycle_days": 365,
        "is_perennial": True,
        "stages": {
            "REBROTE": {
                "days": [
                    0,
                    30
                ],
                "primary": "MSAVI2",
                "reason": "Post-pastoreo suelo expuesto",
                "indices": [
                    "MSAVI2",
                    "NDVI",
                    "SAVI",
                    "OSAVI",
                    "CWSI",
                    "SIF_proxy",
                    "TCARI_OSAVI",
                    "SALINITY"
                ],
                "desc": "Rebrote (0-30d)"
            },
            "CRECIMIENTO": {
                "days": [
                    30,
                    60
                ],
                "primary": "SIF_proxy",
                "reason": "Fluorescencia rebrote activo",
                "indices": [
                    "NDVI",
                    "NDRE",
                    "GNDVI",
                    "EVI",
                    "MTCI",
                    "SIF_proxy",
                    "CWSI",
                    "TCARI_OSAVI",
                    "SALINITY"
                ],
                "desc": "Crecimiento (30-60d)"
            },
            "OPTIMO_PASTOREO": {
                "days": [
                    60,
                    90
                ],
                "primary": "NDVI",
                "reason": "Calibrado biomasa R2=0.74 EMBRAPA",
                "indices": [
                    "NDVI",
                    "NDRE",
                    "EVI",
                    "NDMI",
                    "GNDVI",
                    "CWSI",
                    "SIF_proxy",
                    "TCARI_OSAVI",
                    "SALINITY"
                ],
                "desc": "Optimo pastoreo (60-90d)"
            },
            "MADURO": {
                "days": [
                    90,
                    120
                ],
                "primary": "PSRI",
                "reason": "Detecta lignificacion",
                "indices": [
                    "NDVI",
                    "NDMI",
                    "PSRI",
                    "NBR2",
                    "CWSI",
                    "SIF_proxy",
                    "TCARI_OSAVI",
                    "SALINITY"
                ],
                "desc": "Madura (>90d)"
            },
            "SOBREMADURO": {
                "days": [
                    120,
                    365
                ],
                "primary": "PSRI",
                "reason": "Lignificada PSRI max",
                "indices": [
                    "PSRI",
                    "NDMI",
                    "NBR2",
                    "MSI",
                    "CWSI",
                    "SIF_proxy",
                    "TCARI_OSAVI",
                    "SALINITY"
                ],
                "desc": "Sobremadura"
            }
        },
        "critical_stages": [
            "CRECIMIENTO",
            "OPTIMO_PASTOREO"
        ]
    }
}

# ============================================================
# DATABASE HELPERS — Local file + JSONBlob cloud sync
# ============================================================

JSONBLOB_ID = os.environ.get('JSONBLOB_ID', '')
JSONBLOB_URL = f'https://jsonblob.com/api/jsonBlob/{JSONBLOB_ID}' if JSONBLOB_ID else ''
import threading

def _cloud_load():
    """Load DB from JSONBlob (cloud persistence)."""
    if not JSONBLOB_URL:
        return None
    try:
        import urllib.request
        req = urllib.request.Request(JSONBLOB_URL, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if isinstance(data, dict) and 'clients' in data:
                return data
    except Exception as e:
        print(f'[DB] Cloud load error: {e}')
    return None

def _cloud_save(db):
    """Save DB to JSONBlob (cloud persistence)."""
    if not JSONBLOB_URL:
        return
    try:
        import urllib.request
        body = json.dumps(db, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(JSONBLOB_URL, data=body, method='PUT',
                                     headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f'[DB] Cloud save error: {e}')

def _new_empty_db():
    return {"clients": [], "fields": [], "alerts": [], "timeseries": {}, "version": 0}

def load_db():
    # Try local file first
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            data.setdefault('timeseries', {})
            return data
    # Fallback to cloud
    cloud_data = _cloud_load()
    if cloud_data:
        cloud_data.setdefault('timeseries', {})
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(cloud_data, f, indent=2, ensure_ascii=False)
        print(f'[DB] Loaded from cloud: {len(cloud_data.get("clients",[]))} clients, {len(cloud_data.get("fields",[]))} fields')
        return cloud_data
    return _new_empty_db()

def save_db(db):
    db['version'] = db.get('version', 0) + 1
    db['updatedAt'] = now_iso()
    # Save locally
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    # Save to cloud in background thread (non-blocking)
    import copy
    db_copy = copy.deepcopy(db)
    threading.Thread(target=_cloud_save, args=(db_copy,), daemon=True).start()

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def gen_id(prefix=''):
    ts = str(int(time.time() * 1000))
    rnd = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f'{prefix}{ts}-{rnd}'

def safe_getInfo(ee_obj, timeout=30):
    """Thread-safe getInfo() wrapper with timeout to prevent GEE server hangs.
    Returns None on timeout or error instead of blocking indefinitely."""
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(ee_obj.getInfo)
        try:
            return future.result(timeout=timeout)
        except FuturesTimeout:
            print(f'[GEE] getInfo() TIMEOUT after {timeout}s')
            return None
        except Exception as e:
            print(f'[GEE] getInfo() ERROR: {e}')
            return None

# ============================================================
# PHENOLOGY ENGINE
# ============================================================

def detect_stage(crop, planting_date_str):
    """Detect current phenological stage based on planting date."""
    if not planting_date_str or len(planting_date_str) < 8:
        planting = datetime.now(timezone.utc) - timedelta(days=30)
    else:
        try:
            planting = datetime.fromisoformat(planting_date_str.replace('Z', '+00:00'))
        except:
            try:
                planting = datetime.strptime(planting_date_str[:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except:
                planting = datetime.now(timezone.utc) - timedelta(days=30)

    # Ensure timezone-aware for subtraction
    if planting.tzinfo is None:
        planting = planting.replace(tzinfo=timezone.utc)

    days_since = (datetime.now(timezone.utc) - planting).days
    config = CROP_PHENOLOGY.get(crop)
    if not config:
        return None, None, None

    for stage_key, stage_cfg in config['stages'].items():
        d0, d1 = stage_cfg['days']
        if d0 <= days_since <= d1:
            return stage_key, stage_cfg, days_since

    # Beyond cycle — for perennial crops, wrap around
    if config.get('is_perennial'):
        days_mod = days_since % config['cycle_days']
        for stage_key, stage_cfg in config['stages'].items():
            d0, d1 = stage_cfg['days']
            if d0 <= days_mod <= d1:
                return stage_key, stage_cfg, days_since
    last_stage = list(config['stages'].keys())[-1]
    return last_stage, config['stages'][last_stage], days_since


def compute_pasture_metrics(ndvi_current, ndvi_previous, days_between, field_config):
    """
    Calculate pasture-specific metrics: biomass, growth rate, stocking rate.
    Based on calibrated NDVI-biomass regression for tropical Brachiaria/Panicum.
    Sources: Nature Sci Reports 2024, EMBRAPA Pecuaria, Springer 2024.
    """
    crop_cfg = CROP_PHENOLOGY.get('pastura', {})
    bm = crop_cfg.get('biomass_model', {})
    sr = crop_cfg.get('stocking_rate', {})
    thresholds = crop_cfg.get('management_thresholds', {})

    slope = bm.get('coefficients', {}).get('slope', 6842)
    intercept = bm.get('coefficients', {}).get('intercept', -988)

    # Biomass estimation (kg MS/ha)
    ndvi_clamped = max(bm.get('valid_range', {}).get('NDVI_min', 0.15),
                       min(ndvi_current, bm.get('valid_range', {}).get('NDVI_max', 0.85)))
    biomass_current = max(0, slope * ndvi_clamped + intercept)

    # Growth rate (kg MS/ha/dia)
    growth_rate = None
    if ndvi_previous is not None and days_between and days_between > 0:
        ndvi_prev_clamped = max(0.15, min(ndvi_previous, 0.85))
        biomass_previous = max(0, slope * ndvi_prev_clamped + intercept)
        growth_rate = round((biomass_current - biomass_previous) / days_between, 1)

    # Growth rate classification
    gr_class = 'unknown'
    gr_cfg = crop_cfg.get('growth_rate', {})
    if growth_rate is not None:
        if growth_rate >= gr_cfg.get('excellent', {}).get('min', 80):
            gr_class = 'excellent'
        elif growth_rate >= gr_cfg.get('good', {}).get('min', 50):
            gr_class = 'good'
        elif growth_rate >= gr_cfg.get('moderate', {}).get('min', 30):
            gr_class = 'moderate'
        elif growth_rate >= gr_cfg.get('low', {}).get('min', 10):
            gr_class = 'low'
        else:
            gr_class = 'dormant'

    # Stocking rate calculation (UA/ha)
    daily_intake = sr.get('daily_intake_kg', 11.25)
    residual_min = sr.get('min_residual_kg', 1500)
    eff_rotational = sr.get('grazing_efficiency_rotational', 0.55)
    eff_continuous = sr.get('grazing_efficiency_continuous', 0.35)

    available = max(0, biomass_current - residual_min)
    # Assuming 30-day grazing cycle for rotational
    stocking_rotational = round((available * eff_rotational) / (daily_intake * 30), 2) if daily_intake > 0 else 0
    stocking_continuous = round((available * eff_continuous) / (daily_intake * 30), 2) if daily_intake > 0 else 0

    # Management recommendation
    recommendation = ''
    ndvi_entry = thresholds.get('ndvi_entry', 0.65)
    ndvi_exit = thresholds.get('ndvi_exit', 0.40)
    if ndvi_current >= ndvi_entry:
        recommendation = 'ENTRADA: Pastura lista para pastoreo. Biomasa optima alcanzada.'
    elif ndvi_current <= ndvi_exit:
        recommendation = 'DESCANSO: Pastura necesita recuperacion. Retirar animales.'
    elif ndvi_current < 0.30:
        recommendation = 'ALERTA: Degradacion severa. Evaluar resiembra o fertilizacion.'
    else:
        days_to_entry = round((ndvi_entry - ndvi_current) / max(growth_rate / slope, 0.001)) if growth_rate and growth_rate > 0 else None
        recommendation = f'CRECIENDO: Faltan aprox. {days_to_entry} dias para punto optimo.' if days_to_entry else 'CRECIENDO: En recuperacion.'

    return {
        'biomass_kgDM_ha': round(biomass_current),
        'biomass_model_r2': bm.get('r2', 0.74),
        'growth_rate_kgDM_ha_day': growth_rate,
        'growth_rate_class': gr_class,
        'stocking_rate_rotational_UA_ha': stocking_rotational,
        'stocking_rate_continuous_UA_ha': stocking_continuous,
        'available_biomass_kg': round(available),
        'residual_minimum_kg': residual_min,
        'ndvi_current': round(ndvi_current, 4),
        'ndvi_entry_threshold': ndvi_entry,
        'ndvi_exit_threshold': ndvi_exit,
        'recommendation': recommendation,
        'confidence': 'R2=0.74, RMSE=487 kg/ha (Sentinel-2, Brachiaria tropical)',
        'sources': [
            'Nature Sci Reports 2024 — Sentinel-2 + ML tropical pasture',
            'EMBRAPA Gado de Corte — Sistemas de Produccion',
            'Springer Environmental Monitoring 2024 — Grassland biomass S2'
        ]
    }

# ============================================================
# GEE ENGINE (Python Earth Engine API)
# ============================================================

_ee_initialized = False

def init_gee():
    global _ee_initialized
    if _ee_initialized:
        return True
    try:
        import ee
        if os.path.exists(GEE_KEY_PATH):
            credentials = ee.ServiceAccountCredentials(None, GEE_KEY_PATH)
            ee.Initialize(credentials, project=GEE_PROJECT)
        elif GEE_SERVICE_ACCOUNT_KEY:
            import tempfile
            key_data = json.loads(GEE_SERVICE_ACCOUNT_KEY)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(key_data, f)
                tmp_key_path = f.name
            credentials = ee.ServiceAccountCredentials(None, tmp_key_path)
            ee.Initialize(credentials, project=GEE_PROJECT)
            os.unlink(tmp_key_path)
        else:
            ee.Authenticate()
            ee.Initialize(project=GEE_PROJECT)
        _ee_initialized = True
        print(f'[GEE] Initialized: project={GEE_PROJECT}')
        return True
    except Exception as e:
        print(f'[GEE] Init failed: {e}')
        return False

def compute_monitoring(field):
    """
    Run full monitoring check for a field using GEE.
    OPTIMIZED: Minimized getInfo() calls (max 4 instead of 12-15).
    Returns: { stage, indices, timeseries, anomalies, cloudFree }
    """
    import ee
    t0 = time.time()

    if not init_gee():
        return {"error": "GEE not available"}

    boundary = field['boundary']
    crop = field.get('crop', 'soja')
    planting_date = field.get('plantingDate') or ''

    # Detect current phenological stage
    stage_key, stage_cfg, days = detect_stage(crop, planting_date)
    if not stage_cfg:
        return {"error": f"Unknown crop: {crop}"}

    indices_needed = stage_cfg['indices']
    print(f'[GEE] Check: {field.get("name")} | {crop} | stage={stage_key} | day={days} | indices={len(indices_needed)}')

    # Build GEE geometry — handle Polygon, MultiPolygon, Feature, 3D coords
    geom = boundary
    if geom.get('type') == 'Feature':
        geom = geom['geometry']
    if geom.get('type') == 'MultiPolygon':
        ring = geom['coordinates'][0][0]  # first polygon, outer ring
    elif geom.get('type') == 'Polygon':
        ring = geom['coordinates'][0]  # outer ring
    else:
        return {"error": f"Unsupported geometry type: {geom.get('type')}"}
    # Strip Z coordinate if present (3D → 2D)
    ring_2d = [[p[0], p[1]] for p in ring]
    try:
        aoi = ee.Geometry({"type": "Polygon", "coordinates": [ring_2d]}, proj='EPSG:4326', evenOdd=False)
    except Exception as e:
        print(f'[GEE] Geometry error: {e}, points: {len(ring_2d)}, first: {ring_2d[0]}')
        return {"error": f"Invalid geometry: {str(e)[:100]}"}

    # Date range
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    now = ee.Date(now_str)

    # Cloud masking — keep only clear pixels
    def mask_clouds_scl(img):
        scl = img.select('SCL')
        mask = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7))
        return img.updateMask(mask)

    # Compute cloud % within field boundary
    def add_field_cloud_pct(img):
        scl = img.select('SCL')
        cloud = scl.eq(3).Or(scl.eq(8)).Or(scl.eq(9)).Or(scl.eq(10)).Or(scl.eq(11))
        pct = cloud.reduceRegion(reducer=ee.Reducer.mean(), geometry=aoi, scale=20, bestEffort=True).values().get(0)
        return img.set('cloud_pct_field', ee.Algorithms.If(pct, pct, 1))

    # ── STEP 1: INTELLIGENT IMAGE SEARCH ──
    # Expanding window search — memory-efficient: pre-filter + limit
    is_first_check = field.get('monitoring', {}).get('checkCount', 0) == 0
    search_windows = [30, 60, 90, 120] if is_first_check else [30, 60]

    s2_recent = None
    recent_count = 0
    search_days_used = 0

    for window_days in search_windows:
        search_start = now.advance(-window_days, 'day')
        # Pre-filter aggressively at scene level, then sort by date desc, limit to 10
        candidates = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(aoi)
            .filterDate(search_start, now)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .sort('system:time_start', False)
            .limit(5)
            .map(mask_clouds_scl))

        count = safe_getInfo(candidates.size(), timeout=20)
        if count and count > 0:
            s2_recent = candidates
            recent_count = count
            search_days_used = window_days
            print(f'[GEE] Found {count} images in {window_days}-day window ({time.time()-t0:.1f}s)')
            break
        print(f'[GEE] No images in {window_days}-day window, expanding...')

    if recent_count == 0:
        # Last resort: relax cloud filter, any image in 120 days
        fallback_start = now.advance(-120, 'day')
        s2_recent = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(aoi)
            .filterDate(fallback_start, now)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))
            .sort('system:time_start', False)
            .limit(5)
            .map(mask_clouds_scl))
        recent_count = safe_getInfo(s2_recent.size(), timeout=20) or 0
        search_days_used = 120
        if recent_count > 0:
            print(f'[GEE] Fallback: {recent_count} images in 120 days ({time.time()-t0:.1f}s)')

    cloud_blocked = recent_count == 0
    if cloud_blocked:
        print(f'[GEE] NO images for {field.get("name")} — cloud blocked')

    baseline_start = now.advance(-730, 'day')
    baseline_end = now.advance(-max(search_days_used, 45), 'day')

    # ── STEP 2: Compute all indices on latest image ──
    def compute_indices(img):
        b2 = img.select('B2').divide(10000)
        b3 = img.select('B3').divide(10000)
        b4 = img.select('B4').divide(10000)
        b5 = img.select('B5').divide(10000)
        b6 = img.select('B6').divide(10000)
        b7 = img.select('B7').divide(10000)
        b8 = img.select('B8').divide(10000)
        b8a = img.select('B8A').divide(10000)
        b11 = img.select('B11').divide(10000)
        b12 = img.select('B12').divide(10000)

        ndvi = b8.subtract(b4).divide(b8.add(b4)).rename('NDVI')
        ndre = b8a.subtract(b5).divide(b8a.add(b5)).rename('NDRE')
        evi = b8.subtract(b4).multiply(2.5).divide(b8.add(b4.multiply(6)).subtract(b2.multiply(7.5)).add(1)).rename('EVI')
        ndmi = b8a.subtract(b11).divide(b8a.add(b11)).rename('NDMI')
        mtci = b6.subtract(b5).divide(b5.subtract(b4).max(ee.Image(0.001))).rename('MTCI')
        gndvi = b8.subtract(b3).divide(b8.add(b3)).rename('GNDVI')
        savi = b8.subtract(b4).multiply(1.5).divide(b8.add(b4).add(0.5)).rename('SAVI')
        kndvi = ndvi.pow(2).tanh().rename('kNDVI')
        psri = b4.subtract(b3).divide(b6.max(ee.Image(0.001))).rename('PSRI')
        nbr2 = b11.subtract(b12).divide(b11.add(b12)).rename('NBR2')
        msi = b11.divide(b8a.max(ee.Image(0.001))).rename('MSI')
        osavi = b8.subtract(b4).multiply(1.16).divide(b8.add(b4).add(0.16)).rename('OSAVI')
        msavi2 = b8.multiply(2).add(1).subtract(
            b8.multiply(2).add(1).pow(2).subtract(b8.subtract(b4).multiply(8)).sqrt()
        ).divide(2).rename('MSAVI2')
        s2rep_denom = b6.subtract(b5).where(b6.subtract(b5).abs().lt(0.001), 0.001)
        s2rep = ee.Image(705).add(ee.Image(35).multiply(
            b4.add(b7).divide(2).subtract(b5).divide(s2rep_denom)
        )).rename('S2REP')
        ccci = ndre.divide(ndvi.max(ee.Image(0.001))).rename('CCCI')
        cire = b8a.divide(b6.max(ee.Image(0.001))).subtract(1).rename('CIre')
        reci = b8a.divide(b5.max(ee.Image(0.001))).subtract(1).rename('RECI')
        ireci = b7.subtract(b4).divide(b5.divide(b6.max(ee.Image(0.001)))).rename('IRECI')
        evi2 = b8.subtract(b4).multiply(2.5).divide(b8.add(b4.multiply(2.4)).add(1)).rename('EVI2')
        bsi = b11.add(b4).subtract(b8.add(b2)).divide(b11.add(b4).add(b8).add(b2).max(ee.Image(0.001))).rename('BSI')
        pri_denom = b3.add(b4).where(b3.add(b4).lt(0.001), 0.001)
        pri_proxy = b3.subtract(b4).divide(pri_denom).rename('PRI_proxy')
        # Israeli indices 2024-2025
        cwsi_proxy = b11.subtract(b8a).divide(b11.add(b8a).max(ee.Image(0.001))).rename('CWSI')
        sif_proxy = b5.subtract(b4).divide(b4.max(ee.Image(0.001))).rename('SIF_proxy')
        salinity = b4.multiply(b3).sqrt().rename('SALINITY')
        tcari = ee.Image(3).multiply(b5.subtract(b4).subtract(b5.subtract(b3).multiply(0.2).multiply(b5.divide(b4.max(ee.Image(0.001))))))
        tcari_osavi = tcari.divide(osavi.max(ee.Image(0.001))).rename('TCARI_OSAVI')

        # NEW: Israeli AgriTech indices (Volcani Center / Ben-Gurion / ARO methodology)
        ndvi705 = b6.subtract(b5).divide(b6.add(b5).max(ee.Image(0.001))).rename('NDVI705')
        mcari = b5.subtract(b4).subtract(b5.subtract(b3).multiply(0.2)).multiply(b5.divide(b4.max(ee.Image(0.001)))).rename('MCARI')
        rendvi = b7.subtract(b5).divide(b7.add(b5).max(ee.Image(0.001))).rename('RENDVI')
        nmdi = b8a.subtract(b11.subtract(b12)).divide(b8a.add(b11.subtract(b12)).max(ee.Image(0.001))).rename('NMDI')
        smi = b8a.subtract(b11).divide(b8a.add(b11).max(ee.Image(0.001))).rename('SMI')
        lswi = b8.subtract(b11).divide(b8.add(b11).max(ee.Image(0.001))).rename('LSWI')

        return img.addBands([ndvi, ndre, evi, ndmi, mtci, gndvi, savi, kndvi, psri,
                            nbr2, msi, osavi, msavi2, s2rep, ccci, cire, reci, ireci, evi2,
                            bsi, pri_proxy, cwsi_proxy, sif_proxy, salinity, tcari_osavi,
                            ndvi705, mcari, rendvi, nmdi, smi, lswi])

    current_values = {}
    weed_ndvi_std = None
    weed_ndvi_p90 = None
    weed_ndvi_p50 = None
    image_date = None

    if not cloud_blocked:
        latest = compute_indices(s2_recent.first())

        # Get image date
        try:
            image_date = safe_getInfo(ee.Date(s2_recent.first().get('system:time_start')).format('YYYY-MM-dd'), timeout=15)
        except:
            pass

        # getInfo #2: ALL current values in ONE call
        try:
            all_indices = list(set(indices_needed + ['NDVI']))
            reduce_result = safe_getInfo(latest.select(all_indices).reduceRegion(
                reducer=ee.Reducer.mean(), geometry=aoi, scale=20, bestEffort=True
            ), timeout=30)
            if reduce_result is None:
                raise Exception('Timeout computing indices')

            for idx in all_indices:
                v = reduce_result.get(idx)
                current_values[idx] = round(v, 4) if v is not None else None
            print(f'[GEE] Indices computed: {len(current_values)} values ({time.time()-t0:.1f}s)')

            # FALLBACK: If all values are None (cloud mask removed everything),
            # try the COMPOSITE median of all images WITHOUT cloud mask
            all_none = all(v is None for v in current_values.values())
            if all_none:
                print(f'[GEE] All values None — trying composite without cloud mask...')
                search_start = now.advance(-120, 'day')
                raw_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                    .filterBounds(aoi)
                    .filterDate(search_start, now)
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))
                    .limit(20))
                composite = compute_indices(raw_col.median())
                raw_result = safe_getInfo(composite.select(all_indices).reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=aoi, scale=20, bestEffort=True
                ), timeout=30) or {}
                for idx in all_indices:
                    v = raw_result.get(idx)
                    current_values[idx] = round(v, 4) if v is not None else None
                non_null = sum(1 for v in current_values.values() if v is not None)
                print(f'[GEE] Composite fallback: {non_null}/{len(all_indices)} indices ({time.time()-t0:.1f}s)')

        except Exception as e:
            print(f'[GEE] Index error: {e}')
            traceback.print_exc()
            for idx in indices_needed:
                current_values[idx] = None
            # Treat as cloud blocked to avoid saving None values
            cloud_blocked = True

        # getInfo #3: Weed detection stats (only if in weed window)
        weed_indices_for_stage = stage_cfg.get('weed_indices', [])
        crop_cfg = CROP_PHENOLOGY.get(crop, {})
        weed_cfg = crop_cfg.get('weed_detection', {})
        weed_window = weed_cfg.get('critical_window_days', [0, 0])

        if (weed_window[0] <= days <= weed_window[1] and weed_indices_for_stage
                and current_values.get('NDVI') is not None):
            try:
                ndvi_stats = safe_getInfo(latest.select('NDVI').reduceRegion(
                    reducer=ee.Reducer.stdDev().combine(ee.Reducer.percentile([90, 50]), sharedInputs=True),
                    geometry=aoi, scale=20, bestEffort=True
                ), timeout=20)
                if ndvi_stats is None:
                    raise Exception('Timeout computing weed stats')
                weed_ndvi_std = ndvi_stats.get('NDVI_stdDev', 0) or 0
                weed_ndvi_p90 = ndvi_stats.get('NDVI_p90', 0) or 0
                weed_ndvi_p50 = ndvi_stats.get('NDVI_p50', 0) or 0
                print(f'[GEE] Weed stats: stdDev={weed_ndvi_std:.3f}, P90={weed_ndvi_p90:.3f}, P50={weed_ndvi_p50:.3f} ({time.time()-t0:.1f}s)')
            except Exception as e:
                print(f'[GEE] Weed stats error: {e}')

    # ── STEP 3: Baseline (2-year historical) — NO compute_indices on collection ──
    # OPTIMIZATION: Only compute primary_idx on baseline, not all 24 indices
    # Auto-select primary index from phenological stage config
    primary_idx = stage_cfg.get('primary', indices_needed[0] if indices_needed else 'NDVI')
    primary_reason = stage_cfg.get('reason', '')
    baseline_mean_val = None
    baseline_std_val = None
    z_score = None
    anomalies = []

    if not cloud_blocked and current_values.get(primary_idx) is not None:
        try:
            def compute_primary_only(img):
                """Compute only the primary index for baseline — much faster than all 24."""
                b2 = img.select('B2').divide(10000)
                b3 = img.select('B3').divide(10000)
                b4 = img.select('B4').divide(10000)
                b5 = img.select('B5').divide(10000)
                b6 = img.select('B6').divide(10000)
                b7 = img.select('B7').divide(10000)
                b8 = img.select('B8').divide(10000)
                b8a = img.select('B8A').divide(10000)
                b11 = img.select('B11').divide(10000)
                b12 = img.select('B12').divide(10000)
                idx_map = {
                    'NDVI': b8.subtract(b4).divide(b8.add(b4)),
                    'NDRE': b8a.subtract(b5).divide(b8a.add(b5)),
                    'MSAVI2': b8.multiply(2).add(1).subtract(b8.multiply(2).add(1).pow(2).subtract(b8.subtract(b4).multiply(8)).sqrt()).divide(2),
                    'EVI': b8.subtract(b4).multiply(2.5).divide(b8.add(b4.multiply(6)).subtract(b2.multiply(7.5)).add(1)),
                    'NDMI': b8a.subtract(b11).divide(b8a.add(b11)),
                    'kNDVI': b8.subtract(b4).divide(b8.add(b4)).pow(2).tanh(),
                    'GNDVI': b8.subtract(b3).divide(b8.add(b3)),
                    'OSAVI': b8.subtract(b4).multiply(1.16).divide(b8.add(b4).add(0.16)),
                    'SIF_proxy': b5.subtract(b4).divide(b4.max(ee.Image(0.001))),
                    'MTCI': b6.subtract(b5).divide(b5.subtract(b4).max(ee.Image(0.001))),
                    'NDVI705': b6.subtract(b5).divide(b6.add(b5).max(ee.Image(0.001))),
                    'RENDVI': b7.subtract(b5).divide(b7.add(b5).max(ee.Image(0.001))),
                    'SMI': b8a.subtract(b11).divide(b8a.add(b11).max(ee.Image(0.001))),
                    'LSWI': b8.subtract(b11).divide(b8.add(b11).max(ee.Image(0.001))),
                }
                idx_img = idx_map.get(primary_idx, idx_map['NDVI'])
                return img.addBands(idx_img.rename(primary_idx))

            baseline_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(aoi)
                .filterDate(baseline_start, baseline_end)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 25))
                .limit(50)
                .map(mask_clouds_scl)
                .map(compute_primary_only))

            # Validate baseline has enough images (prevent meaningless Z-scores)
            baseline_count = safe_getInfo(baseline_col.size(), timeout=15) or 0
            if baseline_count < 5:
                print(f'[GEE] Baseline insufficient: only {baseline_count} images (need >=5)')
                result_extra = {'baseline_insufficient': True, 'baseline_count': baseline_count}
            else:
                result_extra = {'baseline_count': baseline_count}

                # getInfo #4: Baseline mean + stddev in ONE call
                baseline_stats = safe_getInfo(baseline_col.select(primary_idx).reduce(
                    ee.Reducer.mean().combine(ee.Reducer.stdDev().combine(ee.Reducer.count(), sharedInputs=True), sharedInputs=True)
                ).reduceRegion(
                    reducer=ee.Reducer.mean(), geometry=aoi, scale=20, bestEffort=True
                ), timeout=30)

                if baseline_stats:
                    baseline_mean_val = baseline_stats.get(f'{primary_idx}_mean')
                    baseline_std_val = baseline_stats.get(f'{primary_idx}_stdDev')
                    print(f'[GEE] Baseline: mean={baseline_mean_val}, std={baseline_std_val}, imgs={baseline_count} ({time.time()-t0:.1f}s)')

                    # Z-score anomaly detection — stddev floor 0.03 for sensitivity
                    if baseline_mean_val and baseline_std_val and baseline_std_val > 0.03:
                        z_score = round((current_values[primary_idx] - baseline_mean_val) / baseline_std_val, 2)
                        if abs(z_score) > 2.0:
                            severity = 'critical' if abs(z_score) > 3.0 else 'warning'
                            anomalies.append({
                                "id": gen_id('anomaly-'),
                                "fieldId": field['id'],
                                "date": now_iso(),
                                "type": "anomaly",
                                "severity": severity,
                                "zScore": z_score,
                                "index": primary_idx,
                                "currentValue": current_values[primary_idx],
                                "baselineMean": round(baseline_mean_val, 4),
                                "baselineStd": round(baseline_std_val, 4),
                                "baselineCount": baseline_count,
                                "description": f"{primary_idx} Z-score={z_score} ({'caida' if z_score < 0 else 'exceso'} vs baseline, n={baseline_count})",
                                "status": "active"
                            })
                else:
                    print(f'[GEE] Baseline stats timeout ({time.time()-t0:.1f}s)')
        except Exception as e:
            print(f'[GEE] Baseline error: {e}')

    # ── WEED DETECTION — Multi-criteria approach (reduces false positives) ──
    weed_alert = None
    if weed_ndvi_std is not None and current_values.get('NDVI') is not None:
        mean_ndvi = current_values.get('NDVI', 0)
        crop_cfg = CROP_PHENOLOGY.get(crop, {})

        # Multi-criteria weed scoring (must pass >= 2 of 3)
        weed_criteria_met = 0
        # Criterion 1: High spatial heterogeneity + active vegetation
        if weed_ndvi_std > 0.12 and mean_ndvi > 0.35:
            weed_criteria_met += 1
        # Criterion 2: P90-P50 gap > 0.20 (weed patches are outliers above canopy median)
        p90_p50_gap = (weed_ndvi_p90 - weed_ndvi_p50) if weed_ndvi_p50 else 0
        if p90_p50_gap > 0.20:
            weed_criteria_met += 1
        # Criterion 3: P90 significantly above mean (weed clusters above canopy)
        if weed_ndvi_p90 > (mean_ndvi + 0.18):
            weed_criteria_met += 1

        if weed_criteria_met >= 2:
            weed_severity = 'critical' if (weed_ndvi_std > 0.20 or weed_criteria_met == 3) else 'warning'
            weed_confidence = round(weed_criteria_met / 3.0 * 100)
            weed_alert = {
                'id': gen_id('weed-'),
                'fieldId': field['id'],
                'date': now_iso(),
                'type': 'weed_infestation',
                'severity': weed_severity,
                'confidence': weed_confidence,
                'criteria_met': weed_criteria_met,
                'description': (f'Posible infestacion de malezas (confianza {weed_confidence}%). '
                               f'Heterogeneidad NDVI={weed_ndvi_std:.3f}, P90={weed_ndvi_p90:.3f}, '
                               f'Gap P90-P50={p90_p50_gap:.3f}. '
                               f'Etapa: {stage_cfg.get("desc","")}. Revisar entresurcos.'),
                'ndvi_std': round(weed_ndvi_std, 4),
                'ndvi_p90': round(weed_ndvi_p90, 4),
                'ndvi_p50': round(weed_ndvi_p50 or 0, 4),
                'ndvi_mean': round(mean_ndvi, 4),
                'p90_p50_gap': round(p90_p50_gap, 4),
                'weed_risk': stage_cfg.get('weed_risk', 'medio'),
                'status': 'active'
            }
            anomalies.append(weed_alert)
            print(f'[Monitor] MALEZA: {field.get("name")} — criteria={weed_criteria_met}/3, stdNDVI={weed_ndvi_std:.3f}')

    # ── CLOUD / HARVEST DETECTION ──
    cloud_message = None
    if cloud_blocked:
        cloud_message = f'Sin imagen cloud-free en ultimos 30 dias. Reintentar en 7 dias.'
        print(f'[Monitor] NUBES: {field.get("name")}')

    harvest_detected = False
    harvest_message = None
    if not cloud_blocked and current_values.get('NDVI') is not None and crop != 'pastura':
        ndvi_now = current_values['NDVI']
        bsi_now = current_values.get('BSI', 0) or 0
        cycle_days = CROP_PHENOLOGY.get(crop, {}).get('cycle_days', 130)

        # Check previous NDVI from timeseries for drop rate
        prev_ndvi = None
        db_ts = load_db().get('timeseries', {}).get(field['id'], [])
        if db_ts:
            prev_entry = db_ts[-1]
            prev_ndvi = prev_entry.get('values', {}).get('NDVI')

        # Harvest detection: NDVI drop rate + BSI confirmation
        ndvi_drop_pct = ((prev_ndvi - ndvi_now) / prev_ndvi * 100) if prev_ndvi and prev_ndvi > 0.3 else 0
        harvest_criteria = 0
        if ndvi_now < 0.25:
            harvest_criteria += 1
        if ndvi_drop_pct > 50:
            harvest_criteria += 1
        if bsi_now > 0.3:
            harvest_criteria += 1
        if days > max(60, cycle_days - 30):
            harvest_criteria += 1

        if harvest_criteria >= 2:
            harvest_detected = True
            harvest_message = (f'Cosecha detectada: NDVI={ndvi_now:.3f}, BSI={bsi_now:.3f}, '
                              f'caida={ndvi_drop_pct:.0f}%. Monitoreo pausado.')
            print(f'[Monitor] COSECHA: {field.get("name")} NDVI={ndvi_now:.3f} BSI={bsi_now:.3f} drop={ndvi_drop_pct:.0f}%')

    # ── SAR FALLBACK (Sentinel-1) when cloud blocked ──
    sar_data = None
    if cloud_blocked:
        sar_data = compute_sar_fallback(aoi, now, search_days_used)
        if sar_data:
            print(f'[GEE] SAR fallback: RVI={sar_data.get("RVI","N/A")} ({time.time()-t0:.1f}s)')

    # ── AGRONOMIC INTERPRETATION ──
    agronomic = None
    if current_values and not cloud_blocked:
        agronomic = interpret_anomalies(current_values, crop, stage_key, anomalies)

    elapsed = round(time.time() - t0, 1)
    print(f'[GEE] DONE: {field.get("name")} in {elapsed}s | {recent_count} imgs | z={z_score}')

    result = {
        "stage": stage_key,
        "stageDesc": stage_cfg['desc'],
        "daysSincePlanting": days,
        "indicesUsed": indices_needed,
        "currentValues": current_values,
        "baseline": {
            "mean": round(baseline_mean_val, 4) if baseline_mean_val else None,
            "std": round(baseline_std_val, 4) if baseline_std_val else None,
        },
        "zScore": z_score,
        "anomalies": anomalies,
        "imagesFound": recent_count,
        "cloudFree": not cloud_blocked,
        "cloudBlocked": cloud_blocked,
        "cloudMessage": cloud_message,
        "harvestDetected": harvest_detected,
        "harvestMessage": harvest_message,
        "weedAlert": weed_alert,
        "weedRisk": stage_cfg.get('weed_risk', 'bajo') if stage_cfg else 'bajo',
        "checkedAt": now_iso(),
        "imageDate": image_date,
        "searchDaysUsed": search_days_used,
        "primaryIndex": primary_idx,
        "primaryReason": primary_reason,
        "elapsedSeconds": elapsed,
        "dataSource": "SAR_S1" if (cloud_blocked and sar_data) else "S2_SR",
        "sarData": sar_data,
        "agronomicInterpretation": agronomic
    }

    # ── PASTURA: Biomass + Growth Rate + Stocking Rate ──
    if crop == 'pastura' and current_values.get('NDVI') is not None:
        db = load_db()
        ts = db.get('timeseries', {}).get(field['id'], [])
        prev_ndvi = None
        days_between = None
        if ts:
            last_entry = ts[-1]
            prev_ndvi = last_entry.get('values', {}).get('NDVI')
            if prev_ndvi and last_entry.get('date'):
                try:
                    last_date = datetime.fromisoformat(last_entry['date'].replace('Z', '+00:00'))
                    days_between = max(1, (datetime.now(timezone.utc) - last_date).days)
                except:
                    days_between = 5
        pasture_metrics = compute_pasture_metrics(current_values['NDVI'], prev_ndvi, days_between, field)
        result['pastureMetrics'] = pasture_metrics

    return result

# ============================================================
# SAR FALLBACK (Sentinel-1 C-band when cloud blocked)
# ============================================================

def compute_sar_fallback(aoi, now_date, search_days):
    """Compute Sentinel-1 SAR indices when optical (S2) is cloud-blocked.
    Returns RVI, VV, VH means as cloud-independent vegetation proxy."""
    import ee
    try:
        sar_start = now_date.advance(-max(search_days, 30), 'day')
        s1 = (ee.ImageCollection('COPERNICUS/S1_GRD')
            .filterBounds(aoi)
            .filterDate(sar_start, now_date)
            .filter(ee.Filter.eq('instrumentMode', 'IW'))
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
            .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
            .select(['VV', 'VH']))

        count = safe_getInfo(s1.size(), timeout=15)
        if not count or count == 0:
            print(f'[SAR] No Sentinel-1 images found')
            return None

        composite = s1.mean().clip(aoi)
        # RVI = 4 * VH / (VV + VH) — Radar Vegetation Index
        vv = composite.select('VV')
        vh = composite.select('VH')
        # Convert from dB to linear for RVI
        vv_lin = ee.Image(10).pow(vv.divide(10))
        vh_lin = ee.Image(10).pow(vh.divide(10))
        rvi = vh_lin.multiply(4).divide(vv_lin.add(vh_lin)).rename('RVI')

        stats = safe_getInfo(composite.addBands(rvi).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi, scale=20, bestEffort=True
        ), timeout=20)

        if not stats:
            return None

        return {
            'RVI': round(stats.get('RVI', 0) or 0, 4),
            'VV': round(stats.get('VV', 0) or 0, 2),
            'VH': round(stats.get('VH', 0) or 0, 2),
            'images': count,
            'source': 'Sentinel-1 IW GRD'
        }
    except Exception as e:
        print(f'[SAR] Error: {e}')
        return None


# ============================================================
# AGRONOMIC INTERPRETATION ENGINE
# ============================================================

# Stress diagnosis matrix based on spectral signatures
STRESS_SIGNATURES = {
    'drought': {
        'indicators': [('NDMI', 'low'), ('MSI', 'high'), ('CWSI', 'high'), ('NMDI', 'low'), ('LSWI', 'low')],
        'recommendation': 'Estres hidrico detectado. Verificar riego o evaluar capacidad de retencion del suelo.',
        'urgency': 'alta'
    },
    'nitrogen': {
        'indicators': [('NDRE', 'low'), ('MTCI', 'low'), ('CCCI', 'low'), ('NDVI705', 'low'), ('RENDVI', 'low')],
        'recommendation': 'Deficiencia de nitrogeno. Aplicar fertilizacion nitrogenada segun dosis recomendada para el cultivo.',
        'urgency': 'media'
    },
    'disease': {
        'indicators': [('PRI_proxy', 'low'), ('PSRI', 'high'), ('SIF_proxy', 'low')],
        'recommendation': 'Posible enfermedad o senescencia prematura. Realizar scouting de campo y evaluar aplicacion de fungicida.',
        'urgency': 'alta'
    },
    'chlorophyll': {
        'indicators': [('MCARI', 'high'), ('TCARI_OSAVI', 'high'), ('GNDVI', 'low')],
        'recommendation': 'Bajo contenido de clorofila. Evaluar nutricion general del cultivo y posibles deficiencias de Mg o Fe.',
        'urgency': 'media'
    }
}

# Reference thresholds per index (approx normal ranges for active crops)
INDEX_THRESHOLDS = {
    'NDVI': (0.35, 0.85), 'NDRE': (0.15, 0.55), 'NDMI': (0.10, 0.50),
    'MSI': (0.40, 1.20), 'CWSI': (-0.30, 0.10), 'MTCI': (1.0, 4.5),
    'CCCI': (0.30, 0.90), 'PRI_proxy': (-0.05, 0.05), 'PSRI': (-0.10, 0.10),
    'SIF_proxy': (0.05, 0.40), 'GNDVI': (0.30, 0.70), 'MCARI': (0.01, 0.30),
    'TCARI_OSAVI': (0.05, 0.50), 'NDVI705': (0.10, 0.50), 'RENDVI': (0.10, 0.50),
    'NMDI': (0.30, 0.80), 'SMI': (0.10, 0.50), 'LSWI': (0.05, 0.40),
    'BSI': (-0.20, 0.15), 'EVI': (0.20, 0.80)
}

def interpret_anomalies(indices, crop, stage, anomalies):
    """Map vegetation index values to actionable agronomic recommendations.
    Uses spectral stress signatures to diagnose drought, nitrogen, disease, chlorophyll issues.
    Returns list of interpretations with type, severity, confidence, and recommendation."""
    interpretations = []

    for stress_type, sig in STRESS_SIGNATURES.items():
        matches = 0
        total = 0
        details = []
        for idx_name, direction in sig['indicators']:
            val = indices.get(idx_name)
            if val is None:
                continue
            total += 1
            thresholds = INDEX_THRESHOLDS.get(idx_name)
            if not thresholds:
                continue
            low, high = thresholds
            if direction == 'low' and val < low:
                matches += 1
                details.append(f'{idx_name}={val:.3f} (bajo)')
            elif direction == 'high' and val > high:
                matches += 1
                details.append(f'{idx_name}={val:.3f} (alto)')

        if total > 0 and matches >= 2:
            confidence = round(matches / total * 100)
            severity = 'critical' if confidence >= 80 else 'warning' if confidence >= 50 else 'info'
            interpretations.append({
                'type': stress_type,
                'severity': severity,
                'confidence': confidence,
                'indicators': details,
                'recommendation': sig['recommendation'],
                'urgency': sig['urgency'],
                'crop': crop,
                'stage': stage
            })

    # Sort by confidence descending
    interpretations.sort(key=lambda x: x['confidence'], reverse=True)
    return interpretations if interpretations else None


# ============================================================
# REPORT GENERATOR (PDF + KMZ)
# ============================================================

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')


def generate_health_map(field, stage_key):
    """Generate ISI health map as colored PNG directly from GEE.
    No matplotlib — uses GEE's built-in visualization for low memory usage.
    Returns: path to saved PNG file, or None if failed.
    """
    if not init_gee():
        return None
    import ee
    try:
        boundary = field['boundary']
        geom_type = boundary.get('type', 'Polygon')
        if geom_type == 'MultiPolygon':
            ring = boundary['coordinates'][0][0]
        else:
            ring = boundary['coordinates'][0]
        ring_2d = [[p[0], p[1]] for p in ring if len(p) >= 2]
        aoi = ee.Geometry({"type": "Polygon", "coordinates": [ring_2d]}, proj='EPSG:4326', evenOdd=False)

        now = ee.Date(datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        search_start = now.advance(-90, 'day')

        def mask_clouds(img):
            scl = img.select('SCL')
            return img.updateMask(scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7)))

        col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(aoi).filterDate(search_start, now)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
            .sort('system:time_start', False).limit(8).map(mask_clouds))

        if col.size().getInfo() == 0:
            return None

        img = col.median()
        b3 = img.select('B3').divide(10000)
        b4 = img.select('B4').divide(10000)
        b5 = img.select('B5').divide(10000)
        b8 = img.select('B8').divide(10000)
        b8a = img.select('B8A').divide(10000)
        b11 = img.select('B11').divide(10000)

        ndvi = b8.subtract(b4).divide(b8.add(b4))
        ndre = b8a.subtract(b5).divide(b8a.add(b5))
        ndmi = b8a.subtract(b11).divide(b8a.add(b11))
        osavi = b8.subtract(b4).multiply(1.16).divide(b8.add(b4).add(0.16))
        tcari = ee.Image(3).multiply(b5.subtract(b4).subtract(b5.subtract(b3).multiply(0.2).multiply(b5.divide(b4.max(ee.Image(0.001))))))
        tcari_osavi = tcari.divide(osavi.max(ee.Image(0.001)))
        cwsi = b11.subtract(b8a).divide(b11.add(b8a).max(ee.Image(0.001)))
        sif = b5.subtract(b4).divide(b4.max(ee.Image(0.001)))

        # ISI = weighted fusion
        isi = (ndvi.multiply(0.25).add(ndre.multiply(0.20))
               .add(sif.clamp(0, 2).divide(2).multiply(0.15))
               .add(ndmi.add(0.5).multiply(0.15))
               .subtract(cwsi.clamp(-0.5, 0.5).add(0.5).multiply(0.10))
               .subtract(tcari_osavi.clamp(0, 5).divide(5).multiply(0.15))
              ).clamp(0, 1).rename('ISI')

        # Gaussian smoothing for zone-like appearance
        isi_smooth = isi.focal_mean(radius=60, units='meters', kernelType='gaussian').clip(aoi)

        # Professional 15-color palette (red→yellow→green)
        palette = [
            '67000D', 'A50F15', 'CB181D', 'EF4444', 'F97316',
            'FB923C', 'FBBF24', 'FDE68A', 'D9F99D', '86EFAC',
            '4ADE80', '22C55E', '16A34A', '15803D', '14532D']

        region = aoi.bounds().buffer(50).getInfo()['coordinates']
        thumb_url = isi_smooth.getThumbURL({
            'region': region,
            'dimensions': '800x600',
            'format': 'png',
            'min': 0.05, 'max': 0.60,
            'palette': palette
        })

        import urllib.request
        os.makedirs(REPORTS_DIR, exist_ok=True)
        map_filename = f'ISI_map_{field.get("name","lote")}_{datetime.now().strftime("%Y%m%d")}.png'.replace(' ', '_')
        map_path = os.path.join(REPORTS_DIR, map_filename)
        urllib.request.urlretrieve(thumb_url, map_path)
        print(f'[Map] ISI map saved: {map_path} ({os.path.getsize(map_path)} bytes)')
        return map_path

    except Exception as e:
        print(f'[Map] ISI map error: {e}')
        traceback.print_exc()
        return None


def generate_report(field, client, alerts, timeseries):
    """Generate PDF geo-report with colored map, Israeli indices, anomaly navigation, and WhatsApp message."""
    import io, zipfile, urllib.parse
    os.makedirs(REPORTS_DIR, exist_ok=True)

    field_name = field.get('name', 'Lote')
    crop = field.get('crop', 'soja')
    date_str = datetime.now().strftime('%Y-%m-%d')
    stage = field.get('monitoring', {}).get('currentStage', '—')
    client_name = client.get('name', '—') if client else '—'
    client_phone = client.get('contact', '') if client else ''

    # Get boundary coords
    boundary = field.get('boundary', {})
    geom_type = boundary.get('type', 'Polygon')
    if geom_type == 'MultiPolygon':
        coords = boundary.get('coordinates', [[[]]])[0][0]
    else:
        coords = boundary.get('coordinates', [[]])[0]
    coords_2d = [[c[0], c[1]] for c in coords if len(c) >= 2]

    # Calculate centroid
    if coords_2d:
        center_lng = sum(c[0] for c in coords_2d) / len(coords_2d)
        center_lat = sum(c[1] for c in coords_2d) / len(coords_2d)
    else:
        center_lng, center_lat = -63.0, -17.5

    # Get last check values
    last_ts = timeseries[-1] if timeseries else {}
    current_values = last_ts.get('values', {})
    z_score = last_ts.get('zScore')
    image_date = last_ts.get('date', '')[:10] if last_ts.get('date') else '—'

    # Determine health status
    ndvi = current_values.get('NDVI')
    if ndvi is None:
        health = 'SIN DATOS'
        health_color = '#6B7280'
    elif ndvi > 0.65:
        health = 'EXCELENTE'
        health_color = '#22C55E'
    elif ndvi > 0.45:
        health = 'BUENO'
        health_color = '#7FD633'
    elif ndvi > 0.30:
        health = 'MODERADO'
        health_color = '#F5A623'
    elif ndvi > 0.15:
        health = 'BAJO'
        health_color = '#EF4444'
    else:
        health = 'CRITICO / POST-COSECHA'
        health_color = '#991B1B'

    # Stage config
    crop_cfg = CROP_PHENOLOGY.get(crop, {})
    stage_cfg_report = None
    for sk, sv in crop_cfg.get('stages', {}).items():
        if sk == stage:
            stage_cfg_report = sv
            break
    primary_idx = stage_cfg_report.get('primary', 'NDVI') if stage_cfg_report else 'NDVI'
    primary_reason = stage_cfg_report.get('reason', '') if stage_cfg_report else ''
    stage_desc = stage_cfg_report.get('desc', stage) if stage_cfg_report else stage

    # Google Maps link for navigation
    gmaps_link = f'https://www.google.com/maps?q={center_lat},{center_lng}&z=16'

    # ── KMZ (KML zipped) for Avenza Maps ──
    kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>PIX Monitor - {field_name} - {date_str}</name>
  <description>Reporte georreferenciado para navegacion a campo</description>
  <Style id="green"><LineStyle><color>ff33d67f</color><width>3</width></LineStyle><PolyStyle><color>4033d67f</color></PolyStyle></Style>
  <Style id="yellow"><LineStyle><color>ff00aaff</color><width>3</width></LineStyle><PolyStyle><color>4000aaff</color></PolyStyle></Style>
  <Style id="red"><LineStyle><color>ff0000ff</color><width>3</width></LineStyle><PolyStyle><color>400000ff</color></PolyStyle></Style>
  <Style id="alertPin"><IconStyle><color>ff0000ff</color><scale>1.3</scale><Icon><href>http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png</href></Icon></IconStyle></Style>

  <Folder><name>Lote {field_name}</name>
    <Placemark>
      <name>{field_name}</name>
      <description>Cultivo: {crop} | Area: {field.get("areaHa", 0)} ha | Estado: {health} | NDVI: {f'{ndvi:.3f}' if ndvi else '—'}</description>
      <styleUrl>#{'green' if health in ['EXCELENTE','BUENO'] else 'yellow' if health == 'MODERADO' else 'red'}</styleUrl>
      <Polygon><outerBoundaryIs><LinearRing><coordinates>
"""
    for c in coords_2d:
        kml_content += f'        {c[0]},{c[1]},0\n'
    kml_content += """      </coordinates></LinearRing></outerBoundaryIs></Polygon>
    </Placemark>
  </Folder>

  <Folder><name>Punto de Acceso</name>
    <Placemark>
      <name>Centro del Lote</name>
      <description>Navegar aqui para inspeccion de campo</description>
      <Point><coordinates>""" + f'{center_lng},{center_lat},0' + """</coordinates></Point>
    </Placemark>
  </Folder>
"""
    if alerts:
        kml_content += "  <Folder><name>Anomalias</name>\n"
        for i, a in enumerate(alerts):
            kml_content += f"""    <Placemark>
      <name>Anomalia-{i+1} (Z={a.get('zScore','?')})</name>
      <description>{a.get('description','')[:200]}</description>
      <styleUrl>#alertPin</styleUrl>
      <Point><coordinates>{center_lng},{center_lat},0</coordinates></Point>
    </Placemark>
"""
        kml_content += "  </Folder>\n"
    kml_content += "</Document>\n</kml>"

    kmz_filename = f'PIX_{field_name}_{date_str}.kmz'.replace(' ', '_')
    kmz_path = os.path.join(REPORTS_DIR, kmz_filename)
    with zipfile.ZipFile(kmz_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('doc.kml', kml_content)

    # ── PDF REPORT with map and indices ──
    pdf_filename = f'PIX_{field_name}_{date_str}.pdf'.replace(' ', '_')
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.colors import HexColor, white, black
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
        from reportlab.graphics.shapes import Drawing, Rect, String, Polygon as RLPolygon, Circle
        from reportlab.graphics import renderPDF

        W, H = A4
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=15*mm, bottomMargin=10*mm, leftMargin=12*mm, rightMargin=12*mm)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='T1', fontSize=16, spaceAfter=4, textColor=HexColor('#7FD633'), fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='Sub', fontSize=10, spaceAfter=8, textColor=HexColor('#94A3B8')))
        styles.add(ParagraphStyle(name='Body', fontSize=9, spaceAfter=4, leading=12))
        styles.add(ParagraphStyle(name='H2', fontSize=12, spaceAfter=6, textColor=HexColor('#00A4CC'), fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='H3', fontSize=10, spaceAfter=4, textColor=HexColor('#7FD633'), fontName='Helvetica-Bold'))
        styles.add(ParagraphStyle(name='Foot', fontSize=7, textColor=HexColor('#64748B')))

        story = []

        # ── HEADER ──
        story.append(Paragraph('PIX Monitor — Informe de Evaluacion Satelital', styles['T1']))
        story.append(Paragraph(f'Cliente: <b>{client_name}</b> | Lote: <b>{field_name}</b> | Cultivo: <b>{crop_cfg.get("name", crop)}</b> | {date_str}', styles['Sub']))

        # ── MAP: ISI (Integrated Health Index) from GEE ──
        story.append(Paragraph('1. Mapa de Salud del Cultivo (ISI)', styles['H2']))
        story.append(Paragraph('Indice de Salud Integrado: fusion TCARI/OSAVI + CWSI + SIF + NDVI + NDRE + NDMI', styles['Body']))

        # Generate ISI map — skip GEE map on Free tier (causes timeout)
        # Enable when on Starter plan ($7/mo) with more RAM/timeout
        isi_map_path = None  # generate_health_map(field, stage)
        if isi_map_path and os.path.exists(isi_map_path):
            story.append(Image(isi_map_path, width=170*mm, height=100*mm))
            story.append(Paragraph(
                f'<font color="#15803D">&#9632;</font> Sano &nbsp; '
                f'<font color="#7FD633">&#9632;</font> Bueno &nbsp; '
                f'<font color="#FCD34D">&#9632;</font> Moderado &nbsp; '
                f'<font color="#F5A623">&#9632;</font> Atencion &nbsp; '
                f'<font color="#EF4444">&#9632;</font> Critico &nbsp; '
                f'<font color="#991B1B">&#9632;</font> Severo',
                ParagraphStyle(name='Legend', fontSize=8, textColor=HexColor('#94A3B8'), spaceAfter=4)
            ))
        else:
            # Fallback: SVG polygon with health color
            map_w, map_h = 170*mm, 80*mm
            d = Drawing(map_w, map_h)
            d.add(Rect(0, 0, map_w, map_h, fillColor=HexColor('#0F1B2D'), strokeColor=HexColor('#334155')))
            if coords_2d:
                lngs = [c[0] for c in coords_2d]
                lats = [c[1] for c in coords_2d]
                min_lng, max_lng = min(lngs), max(lngs)
                min_lat, max_lat = min(lats), max(lats)
                pad = 15
                rng_lng = max(max_lng - min_lng, 0.001)
                rng_lat = max(max_lat - min_lat, 0.001)
                sc = min((map_w - 2*pad) / rng_lng, (map_h - 2*pad) / rng_lat)
                pts = []
                for c in coords_2d:
                    pts.extend([pad + (c[0] - min_lng) * sc, pad + (c[1] - min_lat) * sc])
                fill = HexColor('#22C55E') if health in ['EXCELENTE','BUENO'] else HexColor('#F5A623') if health == 'MODERADO' else HexColor('#EF4444')
                d.add(RLPolygon(pts, fillColor=fill, fillOpacity=0.4, strokeColor=HexColor('#7FD633'), strokeWidth=2))
                d.add(String(pad, map_h - 12, f'{field_name} — {health} (sin mapa satelital)', fontSize=9, fillColor=white, fontName='Helvetica-Bold'))
            story.append(d)

        story.append(Paragraph(f'Centro: {center_lat:.5f}, {center_lng:.5f} | Area: {field.get("areaHa",0)} ha | Imagen: {image_date}', ParagraphStyle(name='MapInfo', fontSize=8, textColor=HexColor('#94A3B8'), spaceAfter=4)))
        story.append(Spacer(1, 8))

        # ── ESTADO DEL CULTIVO ──
        story.append(Paragraph('2. Estado del Cultivo', styles['H2']))
        info = [
            ['Propiedad', 'Valor'],
            ['Estado general', f'{health}'],
            ['Etapa fenologica', stage_desc],
            ['Indice primario', f'{primary_idx} — {primary_reason}'],
            ['Imagen Sentinel-2', image_date],
            ['Area', f'{field.get("areaHa", 0)} ha'],
            ['Z-Score', f'{z_score}' if z_score else 'Sin baseline'],
        ]
        t = Table(info, colWidths=[45*mm, 125*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a2b3f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#334155')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#0F1B2D'), HexColor('#162236')]),
            ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 10))

        # ── INDICES ESPECTRALES (incluye israelies) ──
        story.append(Paragraph('3. Indices Espectrales', styles['H2']))

        israeli = ['TCARI_OSAVI', 'SIF_proxy', 'CWSI', 'SALINITY']
        classic = ['NDVI', 'NDRE', 'EVI', 'NDMI', 'GNDVI', 'kNDVI', 'SAVI']
        advanced = ['MTCI', 'S2REP', 'CCCI', 'IRECI', 'PSRI', 'NBR2', 'MSI', 'BSI', 'PRI_proxy', 'MSAVI2', 'OSAVI']

        idx_data = [['Indice', 'Valor', 'Origen', 'Uso']]
        for idx_name in israeli:
            v = current_values.get(idx_name)
            if v is not None:
                origins = {'TCARI_OSAVI': 'Volcani Israel', 'SIF_proxy': 'Israel/Guanter', 'CWSI': 'Volcani/ARO', 'SALINITY': 'Negev/Arava'}
                uses = {'TCARI_OSAVI': 'Clorofila R2=0.81', 'SIF_proxy': 'Fluorescencia R2=0.72', 'CWSI': 'Stress hidrico', 'SALINITY': 'Salinidad suelo'}
                idx_data.append([idx_name, f'{v:.4f}', origins.get(idx_name, 'Israel'), uses.get(idx_name, '')])
        for idx_name in classic + advanced:
            v = current_values.get(idx_name)
            if v is not None:
                idx_data.append([idx_name, f'{v:.4f}', 'Sentinel-2', ''])

        if len(idx_data) > 1:
            it = Table(idx_data, colWidths=[30*mm, 25*mm, 35*mm, 55*mm])
            it.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1E3A5F')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#334155')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#0F1B2D'), HexColor('#162236')]),
                ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#E2E8F0')),
                ('PADDING', (0, 0), (-1, -1), 3),
            ]))
            # Highlight Israeli indices rows in green
            for i in range(1, min(5, len(idx_data))):
                it.setStyle(TableStyle([('TEXTCOLOR', (0, i), (0, i), HexColor('#7FD633'))]))
            story.append(it)
        else:
            story.append(Paragraph('Sin datos de indices — zona nublada.', styles['Body']))
        story.append(Spacer(1, 10))

        # ── ANOMALIAS ──
        story.append(Paragraph('4. Anomalias y Alertas', styles['H2']))
        if alerts:
            for i, a in enumerate(alerts):
                sev = a.get('severity', 'warning').upper()
                color = '#EF4444' if sev == 'CRITICAL' else '#F5A623'
                story.append(Paragraph(f'<font color="{color}">&#9679;</font> Anomalia {i+1}: {a.get("description","")[:120]}', styles['Body']))
                story.append(Paragraph(f'&nbsp;&nbsp;Z-Score: {a.get("zScore","—")} | Severidad: {sev}', styles['Body']))
        else:
            story.append(Paragraph('<font color="#22C55E">&#10004;</font> Sin anomalias detectadas. Cultivo en estado normal.', styles['Body']))
        story.append(Spacer(1, 10))

        # ── NAVEGACION A CAMPO ──
        story.append(Paragraph('5. Navegacion a Campo', styles['H2']))
        story.append(Paragraph(f'<b>Centro del lote:</b> {center_lat:.6f}, {center_lng:.6f}', styles['Body']))
        story.append(Paragraph(f'<b>Google Maps:</b> <link href="{gmaps_link}">{gmaps_link}</link>', styles['Body']))
        story.append(Paragraph(f'<b>KMZ para Avenza Maps:</b> {kmz_filename}', styles['Body']))
        story.append(Spacer(1, 8))

        # ── FOOTER ──
        story.append(Spacer(1, 16))
        story.append(Paragraph(f'Generado por PIX Monitor — Pixadvisor Agricultura de Precision | www.pixadvisor.network | {date_str}', styles['Foot']))

        doc.build(story)
        print(f'[Report] PDF generated: {pdf_path}')

    except ImportError as e:
        print(f'[Report] reportlab not installed: {e}')
        with open(pdf_path.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
            f.write(f'PIX Monitor — Informe de Evaluacion Satelital\n')
            f.write(f'Cliente: {client_name} | Lote: {field_name} | Cultivo: {crop}\n')
            f.write(f'Estado: {health} | NDVI: {ndvi}\n')
            f.write(f'Indice primario: {primary_idx} — {primary_reason}\n')
            f.write(f'Google Maps: {gmaps_link}\n')
        pdf_filename = pdf_filename.replace('.pdf', '.txt')

    # ── WHATSAPP MESSAGE ──
    wa_msg = f"""*PIX Monitor — {field_name}*
_Informe de Evaluacion Satelital_

*Cliente:* {client_name}
*Lote:* {field_name} ({field.get('areaHa',0)} ha)
*Cultivo:* {crop_cfg.get('name', crop)}
*Etapa:* {stage_desc}
*Estado:* {health}

*Indices clave:*"""
    if current_values.get('NDVI') is not None:
        wa_msg += f"\n  NDVI: {current_values['NDVI']:.3f}"
    if current_values.get('TCARI_OSAVI') is not None:
        wa_msg += f"\n  TCARI/OSAVI (Israel): {current_values['TCARI_OSAVI']:.3f}"
    if current_values.get('CWSI') is not None:
        wa_msg += f"\n  CWSI (Stress hidrico): {current_values['CWSI']:.3f}"
    if current_values.get('SIF_proxy') is not None:
        wa_msg += f"\n  SIF (Fluorescencia): {current_values['SIF_proxy']:.3f}"

    if alerts:
        wa_msg += f"\n\n*{len(alerts)} Anomalias detectadas*"
        for a in alerts[:3]:
            wa_msg += f"\n  - {a.get('description','')[:60]}"

    wa_msg += f"\n\n*Navegacion:* {gmaps_link}"
    wa_msg += f"\n\n_Pixadvisor — Agricultura de Precision_"
    wa_msg += f"\n_www.pixadvisor.network_"

    # Generate WhatsApp URL
    wa_url = None
    if client_phone:
        phone_clean = client_phone.replace('+', '').replace(' ', '').replace('-', '')
        wa_url = f'https://wa.me/{phone_clean}?text={urllib.parse.quote(wa_msg)}'

    return {
        'pdf': pdf_filename,
        'kmz': kmz_filename,
        'pdfPath': pdf_path,
        'kmzPath': kmz_path,
        'alerts': len(alerts),
        'field': field_name,
        'date': date_str,
        'health': health,
        'healthColor': health_color,
        'primaryIndex': primary_idx,
        'googleMapsLink': gmaps_link,
        'whatsappMessage': wa_msg,
        'whatsappUrl': wa_url,
        'centerLat': center_lat,
        'centerLng': center_lng
    }

