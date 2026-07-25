"""
FastAPI - Pixadvisor Field Delineation API.

Endpoints basicos (POC):
    GET  /health, /info
    POST /delineate          (single-period, sin refinamiento)

Endpoints de produccion (cadastrable):
    POST /delineate/pro      (multi-temporal + consensus + smoothing + QA)
    GET  /clients            list clientes (con totales)
    POST /clients            crear cliente (o get si existe)
    GET  /farms              list fincas
    POST /farms              crear finca (o get)
    GET  /lots               list lotes (filtrar por farm_id)
    POST /lots               guardar lote (con audit trail)
    GET  /farms/{id}/export  exportar GeoJSON consolidado
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException, Header, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from shapely.geometry import mapping

from inference import load_model, run_inference, WEIGHTS
from s2_fetch import fetch_sentinel2_rgb, fetch_sentinel2_ndvi
from refinement import refine_polygons, compute_useful_area, quality_score
from consensus import split_periods, consensus_polygons, merge_adjacent
from boundary_refinement import refine_boundary
from productive_detection import detect_productive_perimeters
from planting_v2_inference import predict_planting_v2
from highres_inference import detect_lots_highres
from lots_via_borders import detect_lots_via_borders
from sam_detector import detect_lots_with_sam
from ftw_prue_detector import detect_lots_with_ftw
import lots_db

API_KEY = os.environ.get("PIXADVISOR_API_KEY")
ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "output" / "s2_cache"

app = FastAPI(title="Pixadvisor Field Delineation API", version="2.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS", "PATCH", "DELETE"],
    allow_headers=["*"],
)


def check_api_key(x_api_key):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(401, "Invalid X-API-Key")


# ---------------- Models ---------------- #
class DelineateRequest(BaseModel):
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    start: str = "2026-01-01"
    end: str = "2026-02-25"
    cloud_pct: int = 30
    model: str = "small"
    conf: float = 0.05
    min_area_ha: float = 0.3


class DelineateProRequest(BaseModel):
    bbox: list[float] = Field(..., min_length=4, max_length=4,
                               description="[W, S, E, N] WGS84")
    start: str = "2026-01-01"
    end: str = "2026-04-30"
    cloud_pct: int = 30
    model: str = "small"
    conf: float = 0.10
    min_area_ha: float = Field(1.0, description="ignora < N ha (1 ha tipico)")
    n_periods: int = Field(3, ge=1, le=6, description="ventanas multi-temporal")
    min_periods_match: int = Field(2, ge=1, description=">= N periodos para aceptar")
    iou_match: float = Field(0.30, ge=0.05, le=0.99)
    smooth_iters: int = Field(2, ge=0, le=5)
    simplify_m: float = Field(5.0, ge=0.5, le=30)
    merge_gap_m: float = Field(8.0, ge=0, le=30,
                                description="fusiona poligonos a < N metros")
    ndvi_threshold: float = Field(0.30, ge=0, le=0.95,
                                   description="umbral para area util")


class ClientCreate(BaseModel):
    name: str
    notes: str = ""


class FarmCreate(BaseModel):
    client_id: int
    name: str
    country: str = None
    state: str = None
    city: str = None


class LotCreate(BaseModel):
    farm_id: int
    name: str
    geometry: dict  # FeatureCollection / Feature / Polygon
    area_ha: float
    crop: str = None
    useful_area_ha: float = None
    useful_pct: float = None
    mean_ndvi: float = None
    std_ndvi: float = None
    quality_score: float = None
    quality_tag: str = None
    temporal_stability: float = None
    n_periods_detected: int = None
    source: str = "AI_DELINEATE"
    s2_period_start: str = None
    s2_period_end: str = None
    actor: str = None


# ---------------- Static ---------------- #
@app.get("/")
def root():
    pro = Path(__file__).parent / "client_pro.html"
    if pro.exists():
        return FileResponse(pro)
    demo = Path(__file__).parent / "client_demo.html"
    return FileResponse(demo) if demo.exists() else {"see": "/docs"}


@app.get("/demo")
def demo():
    p = Path(__file__).parent / "client_demo.html"
    return FileResponse(p) if p.exists() else {"see": "/docs"}


@app.get("/widget")
def widget():
    """Widget light-theme embebible para integrar en pix-admin via iframe."""
    p = ROOT / "integration" / "pix_admin_widget.html"
    return FileResponse(p) if p.exists() else {"error": "widget not found"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "weights_available": {k: v.exists() for k, v in WEIGHTS.items()},
        "version": "2.0.0",
    }


@app.get("/info")
def info():
    return {
        "service": "pixadvisor-field-delineation",
        "version": "2.0.0",
        "models": {k: {"size_mb": round(v.stat().st_size/1024/1024, 1) if v.exists() else None}
                   for k, v in WEIGHTS.items()},
        "endpoints": {
            "/delineate": "single-period basic",
            "/delineate/pro": "multi-temporal + consensus + QA (RECOMMENDED)",
            "/clients, /farms, /lots": "cadastro persistente",
        },
    }


# ---------------- Basic /delineate (legacy POC) ---------------- #
@app.post("/delineate")
def delineate(req: DelineateRequest, x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    if not WEIGHTS.get(req.model, Path()).exists():
        raise HTTPException(503, f"weights {req.model} no disponibles")
    try:
        rgb, transform, crs, meta = fetch_sentinel2_rgb(
            bbox=req.bbox, start=req.start, end=req.end,
            cloud_pct=req.cloud_pct, cache_dir=CACHE,
        )
    except Exception as e:
        raise HTTPException(502, f"S2 fetch: {e}")
    polys = run_inference(rgb, transform, crs, size=req.model,
                          conf=req.conf, min_area_ha=req.min_area_ha)
    feats = [{"type": "Feature",
              "properties": {"area_ha": round(p["area_ha"], 3), "id": i},
              "geometry": mapping(p["geometry"])}
             for i, p in enumerate(polys)]
    return JSONResponse({
        "type": "FeatureCollection",
        "features": feats,
        "metadata": {"n_polygons": len(feats), "imagery": meta,
                      "model": req.model, "bbox": req.bbox,
                      "period": [req.start, req.end]}
    })


# ---------------- /delineate/pro (production) ---------------- #
@app.post("/delineate/pro")
def delineate_pro(req: DelineateProRequest, x_api_key: str = Header(None)):
    """Pipeline cadastrable: multi-temporal + consenso + smoothing + area util + QA."""
    check_api_key(x_api_key)
    if not WEIGHTS.get(req.model, Path()).exists():
        raise HTTPException(503, f"weights {req.model} no disponibles")

    timings = {}
    t_total = time.time()

    # 1) Dividir el periodo en N ventanas
    periods = split_periods(req.start, req.end, req.n_periods)

    # 2) Inferencia por periodo
    detections_per_period = []
    s2_meta = {"periods": [], "n_scenes_per_period": []}
    t0 = time.time()
    for ps, pe in periods:
        try:
            rgb, transform, crs, meta = fetch_sentinel2_rgb(
                bbox=req.bbox, start=ps, end=pe,
                cloud_pct=req.cloud_pct, cache_dir=CACHE,
            )
        except RuntimeError as e:
            # periodo sin escenas - skip
            s2_meta["periods"].append({"start": ps, "end": pe, "skipped": str(e)})
            detections_per_period.append([])
            continue
        s2_meta["periods"].append({"start": ps, "end": pe, "n_scenes": meta["n_scenes"]})
        s2_meta["n_scenes_per_period"].append(meta["n_scenes"])
        polys = run_inference(rgb, transform, crs, size=req.model,
                              conf=req.conf, min_area_ha=req.min_area_ha)
        detections_per_period.append(polys)
    timings["multi_temporal_inference"] = round(time.time() - t0, 2)
    timings["periods_used"] = sum(1 for d in detections_per_period if d)

    if not any(detections_per_period):
        raise HTTPException(404, "No se detectaron poligonos en ningun periodo")

    # 3) Consenso temporal: solo polys que aparecen en >= min_periods_match
    t0 = time.time()
    stable = consensus_polygons(detections_per_period,
                                min_periods=req.min_periods_match,
                                iou_match=req.iou_match)
    # 4) Merge de poligonos adyacentes (mismo lote partido)
    if req.merge_gap_m > 0 and stable:
        stable = merge_adjacent(stable, gap_m=req.merge_gap_m)
    timings["consensus_and_merge"] = round(time.time() - t0, 2)
    timings["polygons_after_consensus"] = len(stable)

    if not stable:
        return JSONResponse({
            "type": "FeatureCollection", "features": [],
            "metadata": {"reason": "Ningun poligono cumplio min_periods_match",
                         "timings": timings, "imagery": s2_meta},
        })

    # 5) Refinamiento: smoothing + simplify + topology
    t0 = time.time()
    refined = refine_polygons(
        [p["geometry"] for p in stable],
        simplify_m=req.simplify_m, smooth_iters=req.smooth_iters,
    )
    # Devolver metadata de stable a refined matcheando por area mas cercana
    for r, s in zip(refined, stable):
        r["temporal_stability"] = s.get("temporal_stability")
        r["n_periods_detected"] = s.get("n_periods_detected")
    timings["refinement"] = round(time.time() - t0, 2)

    # 6) NDVI compuesto del periodo total + useful_area por poligono
    t0 = time.time()
    try:
        ndvi_arr, ndvi_transform, _, _ = fetch_sentinel2_ndvi(
            bbox=req.bbox, start=req.start, end=req.end,
            cloud_pct=req.cloud_pct, cache_dir=CACHE,
        )
        refined = compute_useful_area(refined, ndvi_arr, ndvi_transform,
                                       ndvi_threshold=req.ndvi_threshold)
    except Exception as e:
        s2_meta["ndvi_error"] = str(e)
    timings["ndvi_useful_area"] = round(time.time() - t0, 2)

    # 7) Quality score por poligono
    t0 = time.time()
    scored = [quality_score(p, temporal_stability=p.get("temporal_stability"))
              for p in refined]
    timings["quality_scoring"] = round(time.time() - t0, 2)

    # 8) FeatureCollection
    feats = []
    for i, p in enumerate(scored):
        feats.append({
            "type": "Feature",
            "properties": {
                "id": i,
                "area_ha": round(p["area_ha"], 3),
                "perimeter_m": round(p.get("perimeter_m", 0), 1),
                "useful_area_ha": p.get("useful_area_ha"),
                "useful_pct": p.get("useful_pct"),
                "mean_ndvi": p.get("mean_ndvi"),
                "std_ndvi": p.get("std_ndvi"),
                "temporal_stability": p.get("temporal_stability"),
                "n_periods_detected": p.get("n_periods_detected"),
                "quality_score": p["quality_score"],
                "quality_tag": p["quality_tag"],
                "quality_components": p["quality_components"],
            },
            "geometry": mapping(p["geometry"]),
        })

    timings["total"] = round(time.time() - t_total, 2)

    summary = {
        "n_polygons": len(feats),
        "total_area_ha": round(sum(p["area_ha"] for p in scored), 2),
        "total_useful_ha": round(sum((p.get("useful_area_ha") or 0) for p in scored), 2),
        "by_quality": {
            t: sum(1 for p in scored if p["quality_tag"] == t)
            for t in ["EXCELENTE","BUENO","REVISAR","RECHAZAR"]
        },
    }
    return JSONResponse({
        "type": "FeatureCollection", "features": feats,
        "metadata": {"summary": summary, "timings": timings,
                     "imagery": s2_meta, "request": req.model_dump()},
    })


# ---------------- Persistencia: clients / farms / lots ---------------- #
@app.get("/clients")
def get_clients(x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    return lots_db.list_clients()


@app.post("/clients")
def post_client(req: ClientCreate, x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    cid = lots_db.get_or_create_client(req.name, req.notes)
    return {"id": cid, "name": req.name}


@app.get("/farms")
def get_farms(client_id: int = None, x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    return lots_db.list_farms(client_id=client_id)


@app.post("/farms")
def post_farm(req: FarmCreate, x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    fid = lots_db.get_or_create_farm(req.client_id, req.name,
                                      country=req.country, state=req.state, city=req.city)
    return {"id": fid, "client_id": req.client_id, "name": req.name}


@app.get("/lots")
def get_lots(farm_id: int = None, x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    return lots_db.list_lots(farm_id=farm_id)


@app.post("/lots")
def post_lot(req: LotCreate, x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    lid = lots_db.save_lot(
        farm_id=req.farm_id, name=req.name, geometry_geojson=req.geometry,
        area_ha=req.area_ha, crop=req.crop,
        useful_area_ha=req.useful_area_ha, useful_pct=req.useful_pct,
        mean_ndvi=req.mean_ndvi, std_ndvi=req.std_ndvi,
        quality_score=req.quality_score, quality_tag=req.quality_tag,
        temporal_stability=req.temporal_stability,
        n_periods_detected=req.n_periods_detected,
        source=req.source,
        s2_period_start=req.s2_period_start, s2_period_end=req.s2_period_end,
        actor=req.actor,
    )
    return {"id": lid}


class RefineBoundaryRequest(BaseModel):
    perimeter: dict = Field(..., description="GeoJSON Feature/FeatureCollection/geometry")
    start: str = "2026-01-01"
    end: str = "2026-04-15"
    cloud_pct: int = 30
    n_periods: int = 3
    min_periods_match: int = 2
    iou_match: float = 0.30
    snap_m: float = 12.0
    densify_m: float = 5.0
    smooth_iters: int = 2
    ndvi_threshold: float = 0.30
    min_inside_pct: float = 0.85
    detect_sub_talhoes: bool = True
    bbox_buffer_m: float = 100.0


@app.post("/refine_boundary")
def refine_boundary_endpoint(req: RefineBoundaryRequest, x_api_key: str = Header(None)):
    """Refina un perimetro EXTERNO (operador-aportado) con S2 + Canny + NDVI + sub-talhoes."""
    check_api_key(x_api_key)
    import json as _j
    import time
    from shapely.geometry import shape, mapping

    t_total = time.time()
    timings = {}

    # 1) Validar perimetro y calcular bbox con buffer
    raw = req.perimeter
    if raw.get("type") == "FeatureCollection":
        geom = shape(raw["features"][0]["geometry"])
    elif raw.get("type") == "Feature":
        geom = shape(raw["geometry"])
    else:
        geom = shape(raw)

    minx, miny, maxx, maxy = geom.bounds
    # convertir buffer m -> grados aproximado
    buf = req.bbox_buffer_m / 111000
    bbox = [minx - buf, miny - buf, maxx + buf, maxy + buf]

    # 2) Bajar Sentinel-2 RGB compuesto (mediana de todo el periodo) - para Canny edges
    t0 = time.time()
    try:
        rgb, transform_rgb, crs_rgb, meta_rgb = fetch_sentinel2_rgb(
            bbox=bbox, start=req.start, end=req.end,
            cloud_pct=req.cloud_pct, cache_dir=CACHE,
        )
    except Exception as e:
        raise HTTPException(502, f"S2 RGB: {e}")
    timings["s2_rgb"] = round(time.time() - t0, 2)

    # 3) NDVI compuesto del periodo total
    t0 = time.time()
    try:
        ndvi_arr, ndvi_transform, _, _ = fetch_sentinel2_ndvi(
            bbox=bbox, start=req.start, end=req.end,
            cloud_pct=req.cloud_pct, cache_dir=CACHE,
        )
    except Exception as e:
        ndvi_arr, ndvi_transform = None, None
    timings["ndvi"] = round(time.time() - t0, 2)

    # 4) Detectar sub-talhoes con Delineate Anything multi-temporal (opcional)
    sub_polys = []
    if req.detect_sub_talhoes:
        t0 = time.time()
        periods = split_periods(req.start, req.end, req.n_periods)
        detections = []
        for ps, pe in periods:
            try:
                rgb_p, tr_p, crs_p, _ = fetch_sentinel2_rgb(
                    bbox=bbox, start=ps, end=pe,
                    cloud_pct=req.cloud_pct, cache_dir=CACHE,
                )
            except Exception:
                detections.append([])
                continue
            polys_p = run_inference(rgb_p, tr_p, crs_p, size="small",
                                    conf=0.10, min_area_ha=0.5)
            detections.append(polys_p)
        stable = consensus_polygons(detections,
                                    min_periods=req.min_periods_match,
                                    iou_match=req.iou_match)
        sub_polys = stable
        timings["sub_talhoes_detection"] = round(time.time() - t0, 2)

    # 5) Refinamiento del perimetro
    t0 = time.time()
    if ndvi_arr is None:
        # Crear NDVI vacio para que la funcion no falle
        ndvi_arr = np.zeros((rgb.shape[0], rgb.shape[1]))
        ndvi_transform = transform_rgb
    result = refine_boundary(
        perimeter_geojson=raw,
        rgb=rgb, rgb_transform=transform_rgb, rgb_crs=crs_rgb,
        ndvi=ndvi_arr, ndvi_transform=ndvi_transform,
        sub_polys_wgs=sub_polys,
        snap_m=req.snap_m, densify_m=req.densify_m,
        smooth_iters=req.smooth_iters,
        ndvi_threshold=req.ndvi_threshold,
        min_inside_pct=req.min_inside_pct,
    )
    timings["boundary_refinement"] = round(time.time() - t0, 2)
    timings["total"] = round(time.time() - t_total, 2)

    return JSONResponse({
        "type": "RefinedBoundary",
        "perimeter_input": result["perimeter_input_wgs"],
        "perimeter_refined": result["perimeter_refined_wgs"],
        "productive_area": result.get("productive_polygon_wgs"),
        "nonproductive_area": result.get("nonproductive_polygon_wgs"),
        "sub_talhoes": {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": st["geometry"],
                "properties": {
                    "id": st["id"], "area_ha": st["area_ha"],
                    "inside_pct": st["inside_pct"], "clipped": st["clipped"],
                },
            } for st in result["sub_talhoes"]],
        },
        "summary": {
            "perimeter_input_ha": result["perimeter_input_ha"],
            "perimeter_refined_ha": result["perimeter_refined_ha"],
            "useful_area_ha": result["useful_area_ha"],
            "useful_pct": result["useful_pct"],
            "mean_ndvi": result["mean_ndvi"],
            "std_ndvi": result["std_ndvi"],
            "n_sub_talhoes": result["n_sub_talhoes"],
        },
        "timings": timings,
        "imagery": meta_rgb,
    })


class DetectProductiveRequest(BaseModel):
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    start: str = "2026-01-01"
    end: str = "2026-04-15"
    cloud_pct: int = 30
    ndvi_threshold: float = 0.30
    min_area_ha: float = 5.0
    max_area_ha: float = 5000.0
    smooth_iters: int = 3
    simplify_m: float = 8.0
    closing_iters: int = 3
    opening_iters: int = 1


@app.post("/detect_productive_perimeters")
def detect_productive_endpoint(req: DetectProductiveRequest, x_api_key: str = Header(None)):
    """
    Sin perimetro previo: detecta poligonos de areas productivas (NDVI>umbral)
    en una bbox y devuelve candidatos para que el operador elija cual es su lote.
    """
    check_api_key(x_api_key)
    import time
    from shapely.geometry import mapping
    t_total = time.time()
    timings = {}

    t0 = time.time()
    try:
        ndvi, ndvi_transform, ndvi_crs, meta = fetch_sentinel2_ndvi(
            bbox=req.bbox, start=req.start, end=req.end,
            cloud_pct=req.cloud_pct, cache_dir=CACHE,
        )
    except Exception as e:
        raise HTTPException(502, f"S2 NDVI fetch: {e}")
    timings["ndvi_fetch"] = round(time.time() - t0, 2)

    t0 = time.time()
    candidates = detect_productive_perimeters(
        ndvi=ndvi, ndvi_transform=ndvi_transform,
        threshold=req.ndvi_threshold,
        min_area_ha=req.min_area_ha, max_area_ha=req.max_area_ha,
        smooth_iters=req.smooth_iters, simplify_m=req.simplify_m,
        closing_iters=req.closing_iters, opening_iters=req.opening_iters,
    )
    timings["component_detection"] = round(time.time() - t0, 2)
    timings["total"] = round(time.time() - t_total, 2)

    feats = [{
        "type": "Feature",
        "geometry": mapping(c["geometry"]),
        "properties": {
            "id": c["id"], "area_ha": c["area_ha"],
            "mean_ndvi": c["mean_ndvi"], "std_ndvi": c["std_ndvi"],
            "bbox": c["bbox"], "pixel_count": c["pixel_count"],
        }
    } for c in candidates]

    return JSONResponse({
        "type": "FeatureCollection",
        "features": feats,
        "metadata": {
            "n_candidates": len(feats),
            "total_productive_ha": round(sum(c["area_ha"] for c in candidates), 2),
            "timings": timings,
            "imagery": meta,
            "request": req.model_dump(),
        },
    })


class PlantingV2Request(BaseModel):
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    year: int = 2025
    threshold: float = Field(0.5, ge=0.1, le=0.95)
    min_area_ha: float = Field(1.0, ge=0.1)
    erode_pixels: int = Field(2, ge=0, le=8,
                               description="Erosion para separar lotes adjacentes")
    smooth_iters: int = Field(2, ge=0, le=5,
                               description="Iter Chaikin smoothing (1-3)")
    simplify_m: float = Field(12.0, ge=0, le=50,
                               description="Tolerancia simplify Douglas-Peucker en m")
    instance_separation: bool = True
    use_delineate_anything: bool = Field(False,
                                          description="Si True, sub-divide blobs V3 con Delineate Anything (lote por lote)")


class HighresLotsRequest(BaseModel):
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    zoom: int = Field(17, ge=15, le=19,
                       description="Zoom 15(~5m), 16(~2.5m), 17(~1.2m), 18(~0.6m), 19(~0.3m)")
    source: str = Field("esri", description="'esri' (sin auth) o 'google'")
    conf: float = Field(0.05, ge=0.01, le=0.95)
    min_area_ha: float = Field(1.0, ge=0.1)
    smooth_iters: int = Field(2, ge=0, le=5)
    simplify_m: float = Field(5.0, ge=0, le=30)
    model_size: str = Field("small", description="'small' (16.8MB) o 'large' (125MB)")


class BordersLotsRequest(BaseModel):
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    zoom: int = Field(17, ge=15, le=19)
    source: str = "esri"
    border_block_size: int = 51
    border_C: int = 3
    border_dilate: int = 2
    field_erode: int = 4
    min_area_ha: float = 2.0
    approx_epsilon_pct: float = 0.008
    smooth_iters: int = 1


class S2ImageRequest(BaseModel):
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    start: str = "2026-01-01"
    end: str = "2026-04-15"
    cloud_pct: int = Field(30, ge=0, le=100)
    scale_m: int = Field(10, ge=10, le=60)
    enhancement: str = Field("natural", description="'natural', 'agro', 'urban', 'true_color'")
    format: str = Field("tif", description="'tif' (GeoTIFF), 'png', 'jpg'")


@app.post("/download_sentinel2_image")
def download_sentinel2_image_endpoint(req: S2ImageRequest, x_api_key: str = Header(None)):
    """Descarga imagen Sentinel-2 SR Harmonized color natural mejorada del bbox."""
    check_api_key(x_api_key)
    from s2_fetch import fetch_sentinel2_rgb_enhanced
    import tempfile
    import rasterio
    from fastapi.responses import FileResponse
    from PIL import Image

    try:
        rgb, transform, crs, meta = fetch_sentinel2_rgb_enhanced(
            bbox=req.bbox, start=req.start, end=req.end,
            cloud_pct=req.cloud_pct, scale_m=req.scale_m,
            enhancement=req.enhancement,
            cache_dir=ROOT / "output" / "s2_cache",
        )
    except Exception as e:
        raise HTTPException(502, f"Sentinel-2 fetch: {e}")

    fmt = req.format.lower()
    suffix = "." + fmt
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.close()

    try:
        if fmt == "tif":
            profile = {
                "driver": "GTiff", "dtype": "uint8", "count": 3,
                "height": rgb.shape[0], "width": rgb.shape[1],
                "transform": transform, "crs": crs, "compress": "deflate",
                "tiled": True, "blockxsize": 256, "blockysize": 256,
            }
            with rasterio.open(tmp.name, "w", **profile) as dst:
                dst.write(rgb[:, :, 0], 1)
                dst.write(rgb[:, :, 1], 2)
                dst.write(rgb[:, :, 2], 3)
                dst.set_band_description(1, "Red B4")
                dst.set_band_description(2, "Green B3")
                dst.set_band_description(3, "Blue B2")
        elif fmt in ("png", "jpg", "jpeg"):
            Image.fromarray(rgb).save(tmp.name, quality=92 if fmt != "png" else None)
        else:
            raise HTTPException(400, "format debe ser tif, png o jpg")
    except Exception as e:
        raise HTTPException(500, f"Save image: {e}")

    fname = (f"sentinel2_{req.enhancement}_{req.scale_m}m_"
             f"{req.start}_{req.end}_"
             f"{req.bbox[0]:.4f}_{req.bbox[1]:.4f}_{req.bbox[2]:.4f}_{req.bbox[3]:.4f}.{fmt}")
    headers = {
        "X-S2-Scenes": str(meta.get("n_scenes", "?")),
        "X-S2-Enhancement": meta.get("enhancement", "natural"),
    }
    return FileResponse(tmp.name, filename=fname,
                         media_type=f"image/{fmt if fmt != 'tif' else 'tiff'}",
                         headers=headers)


class HighresImageRequest(BaseModel):
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    zoom: int = Field(17, ge=10, le=19)
    source: str = "esri"
    format: str = Field("tif", description="'tif' (GeoTIFF), 'png' o 'jpg'")


@app.post("/download_highres_image")
def download_highres_image_endpoint(req: HighresImageRequest, x_api_key: str = Header(None)):
    """Descarga la imagen satelite color natural del bbox como GeoTIFF/PNG/JPG."""
    check_api_key(x_api_key)
    from highres_tiles import download_highres_bbox, crop_to_exact_bbox
    import tempfile
    import rasterio
    from fastapi.responses import FileResponse
    from PIL import Image

    try:
        rgb, transform, crs = download_highres_bbox(
            req.bbox, zoom=req.zoom, source=req.source,
            cache_dir=ROOT / "output" / "highres_cache",
        )
        rgb, transform = crop_to_exact_bbox(rgb, transform, req.bbox)
    except Exception as e:
        raise HTTPException(502, f"Tile download: {e}")

    fmt = req.format.lower()
    suffix = "." + fmt
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.close()

    try:
        if fmt == "tif":
            profile = {
                "driver": "GTiff", "dtype": "uint8", "count": 3,
                "height": rgb.shape[0], "width": rgb.shape[1],
                "transform": transform, "crs": crs, "compress": "deflate",
                "tiled": True, "blockxsize": 256, "blockysize": 256,
            }
            with rasterio.open(tmp.name, "w", **profile) as dst:
                dst.write(rgb[:, :, 0], 1)
                dst.write(rgb[:, :, 1], 2)
                dst.write(rgb[:, :, 2], 3)
                dst.set_band_description(1, "Red")
                dst.set_band_description(2, "Green")
                dst.set_band_description(3, "Blue")
        elif fmt in ("png", "jpg", "jpeg"):
            Image.fromarray(rgb).save(tmp.name, quality=92 if fmt != "png" else None)
        else:
            raise HTTPException(400, "format debe ser tif, png o jpg")
    except Exception as e:
        raise HTTPException(500, f"Save image: {e}")

    fname = f"satellite_z{req.zoom}_{req.source}_{req.bbox[0]:.4f}_{req.bbox[1]:.4f}_{req.bbox[2]:.4f}_{req.bbox[3]:.4f}.{fmt}"
    return FileResponse(tmp.name, filename=fname, media_type=f"image/{fmt if fmt != 'tif' else 'tiff'}")


class SamLotsRequest(BaseModel):
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    zoom: int = Field(17, ge=15, le=19)
    source: str = "esri"
    model_type: str = Field("vit_b", description="vit_b (375MB), vit_l (1.2GB), vit_h (2.5GB)")
    min_area_ha: float = 1.0
    max_area_ha: float = 500.0
    points_per_side: int = Field(32, ge=8, le=64)
    pred_iou_thresh: float = 0.86
    stability_score_thresh: float = 0.90
    simplify_m: float = 4.0
    smooth_iters: int = 1
    subtract_borders: bool = Field(True,
        description="Restar lineas de arboles/caminos detectadas para separar lotes que SAM unio")
    border_min_split_area_ha: float = 2.0


class FtwLotsRequest(BaseModel):
    bbox: list[float] = Field(..., min_length=4, max_length=4)
    year: int = 2025
    win_a_start: str = "2025-01-01"
    win_a_end: str = "2025-03-31"
    win_b_start: str = "2025-07-01"
    win_b_end: str = "2025-09-30"
    scale_m: int = 10
    cloud_pct: int = 30
    extent_thresh: float = 0.3
    boundary_thresh: float = 0.4
    marker_min_area_px: int = 50
    marker_erode_iters: int = 1
    min_area_ha: float = 0.5
    max_area_ha: float = 500.0
    simplify_m: float = 3.0
    smooth_iters: int = 2
    tile_size: int = 256
    overlap: int = 64
    use_tta: bool = False


@app.post("/detect_lots_ftw")
def detect_lots_ftw_endpoint(req: FtwLotsRequest, x_api_key: str = Header(None)):
    """FTW PRUE EfficientNet-B5 con watershed segmentation. Modelo SOTA para field boundaries."""
    check_api_key(x_api_key)
    try:
        result = detect_lots_with_ftw(
            bbox=req.bbox,
            win_a_start=req.win_a_start, win_a_end=req.win_a_end,
            win_b_start=req.win_b_start, win_b_end=req.win_b_end,
            scale_m=req.scale_m, cloud_pct=req.cloud_pct,
            extent_thresh=req.extent_thresh, boundary_thresh=req.boundary_thresh,
            marker_min_area_px=req.marker_min_area_px,
            marker_erode_iters=req.marker_erode_iters,
            min_area_ha=req.min_area_ha, max_area_ha=req.max_area_ha,
            simplify_m=req.simplify_m, smooth_iters=req.smooth_iters,
            tile_size=req.tile_size, overlap=req.overlap,
            use_tta=req.use_tta,
        )
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        import traceback
        raise HTTPException(502, f"FTW detection: {e}\n{traceback.format_exc()[:400]}")
    return JSONResponse(result)


@app.post("/detect_lots_sam")
def detect_lots_sam_endpoint(req: SamLotsRequest, x_api_key: str = Header(None)):
    """
    Detector con SAM (Segment Anything Model de Meta).
    Foundation model de vision: ve la imagen como un humano y segmenta lotes.
    Sin entrenamiento, funciona out-of-the-box en cualquier region.
    """
    check_api_key(x_api_key)
    try:
        result = detect_lots_with_sam(
            bbox=req.bbox, zoom=req.zoom, source=req.source,
            model_type=req.model_type,
            min_area_ha=req.min_area_ha, max_area_ha=req.max_area_ha,
            points_per_side=req.points_per_side,
            pred_iou_thresh=req.pred_iou_thresh,
            stability_score_thresh=req.stability_score_thresh,
            simplify_m=req.simplify_m, smooth_iters=req.smooth_iters,
            subtract_borders=req.subtract_borders,
            border_min_split_area_ha=req.border_min_split_area_ha,
        )
    except FileNotFoundError as e:
        raise HTTPException(503, f"SAM model: {e}")
    except Exception as e:
        import traceback
        raise HTTPException(502, f"SAM detection: {e}\n{traceback.format_exc()[:300]}")
    return JSONResponse(result)


@app.post("/detect_lots_via_borders")
def detect_lots_via_borders_endpoint(req: BordersLotsRequest, x_api_key: str = Header(None)):
    """
    Detector basado en BORDES VISIBLES (lineas de arboles/caminos como separadores).
    No usa AI/ML — pura morfologia OpenCV. Lotes = espacios encerrados por bordes oscuros.
    Resultado: poligonos siguiendo los limites visibles, lote por lote individual.
    """
    check_api_key(x_api_key)
    try:
        result = detect_lots_via_borders(
            bbox=req.bbox, zoom=req.zoom, source=req.source,
            border_block_size=req.border_block_size, border_C=req.border_C,
            border_dilate=req.border_dilate, field_erode=req.field_erode,
            min_area_ha=req.min_area_ha,
            approx_epsilon_pct=req.approx_epsilon_pct,
            smooth_iters=req.smooth_iters,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        import traceback
        raise HTTPException(502, f"Borders detection: {e}\n{traceback.format_exc()[:300]}")
    return JSONResponse(result)


@app.post("/detect_lots_highres")
def detect_lots_highres_endpoint(req: HighresLotsRequest, x_api_key: str = Header(None)):
    """
    Detector de lotes a alta resolucion (~1m/pixel).
    Descarga Esri World Imagery + Delineate Anything sobre el mosaic.
    """
    check_api_key(x_api_key)
    try:
        result = detect_lots_highres(
            bbox=req.bbox, zoom=req.zoom, source=req.source,
            conf=req.conf, min_area_ha=req.min_area_ha,
            smooth_iters=req.smooth_iters, simplify_m=req.simplify_m,
            model_size=req.model_size,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        import traceback
        raise HTTPException(502, f"Highres detection: {e}\n{traceback.format_exc()[:300]}")
    return JSONResponse(result)


@app.post("/detect_planting_v2")
def detect_planting_v2_endpoint(req: PlantingV2Request, x_api_key: str = Header(None)):
    """
    Modelo V2 (LightGBM 28 features) entrenado con 400 lotes HDS Bolivia. IoU 0.90 in-distribution.
    Pipeline: predict proba -> threshold -> erode-CCL-dilate (separa lotes) -> Chaikin -> simplify -> filter.
    """
    check_api_key(x_api_key)
    import time
    t0 = time.time()
    try:
        result = predict_planting_v2(
            bbox=req.bbox, year=req.year,
            threshold=req.threshold, min_area_ha=req.min_area_ha,
            erode_pixels=req.erode_pixels,
            smooth_iters=req.smooth_iters,
            simplify_m=req.simplify_m,
            instance_separation=req.instance_separation,
            use_delineate_anything=req.use_delineate_anything,
        )
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        import traceback
        raise HTTPException(502, f"V2 inference: {e}\n{traceback.format_exc()}")
    result["metadata"]["elapsed_seconds"] = round(time.time() - t0, 2)
    return JSONResponse(result)


@app.post("/upload_perimeter")
async def upload_perimeter(file: UploadFile = File(...), x_api_key: str = Header(None)):
    """Acepta GeoJSON / KML / KMZ / SHP-zip y devuelve un FeatureCollection en WGS84."""
    check_api_key(x_api_key)
    import tempfile, zipfile, json as _j
    from pathlib import Path as _P
    import os as _os

    name = (file.filename or "").lower()
    content = await file.read()

    with tempfile.TemporaryDirectory() as td:
        td = _P(td)
        if name.endswith(".geojson") or name.endswith(".json"):
            try:
                fc = _j.loads(content.decode("utf-8"))
                # Validar minimum
                if fc.get("type") not in ("FeatureCollection", "Feature"):
                    raise ValueError("GeoJSON debe ser Feature o FeatureCollection")
                if fc["type"] == "Feature":
                    fc = {"type": "FeatureCollection", "features": [fc]}
                return JSONResponse(fc)
            except Exception as e:
                raise HTTPException(400, f"GeoJSON invalido: {e}")

        if name.endswith(".kml") or name.endswith(".kmz"):
            import geopandas as gpd
            p = td / name
            p.write_bytes(content)
            if name.endswith(".kmz"):
                with zipfile.ZipFile(p) as z:
                    kmls = [n for n in z.namelist() if n.lower().endswith(".kml")]
                    if not kmls: raise HTTPException(400, "KMZ sin .kml")
                    z.extract(kmls[0], td)
                    p = td / kmls[0]
            try:
                gdf = gpd.read_file(p, driver="KML")
            except Exception:
                # Algunas versiones requieren engine fiona y forzar driver
                import fiona
                fiona.drvsupport.supported_drivers["KML"] = "rw"
                gdf = gpd.read_file(p, driver="KML")
            gdf = gdf.to_crs("EPSG:4326")
            return JSONResponse(_j.loads(gdf.to_json()))

        if name.endswith(".zip") or name.endswith(".shp"):
            p = td / "in.zip"
            p.write_bytes(content)
            try:
                with zipfile.ZipFile(p) as z:
                    z.extractall(td)
            except zipfile.BadZipFile:
                raise HTTPException(400, "ZIP corrupto. Usar archivo .zip con .shp/.shx/.dbf/.prj")
            shp = list(td.rglob("*.shp"))
            if not shp:
                raise HTTPException(400, "ZIP sin archivo .shp")
            import os as _os2
            _os2.environ["SHAPE_RESTORE_SHX"] = "YES"
            import geopandas as gpd
            try:
                gdf = gpd.read_file(shp[0])
                if gdf.crs is None:
                    gdf = gdf.set_crs("EPSG:4326")
                gdf = gdf.to_crs("EPSG:4326")
                return JSONResponse(_j.loads(gdf.to_json()))
            except Exception as e:
                raise HTTPException(400, f"SHP no se pudo leer: {e}")

        raise HTTPException(400, "Formato no soportado. Use .geojson, .kml, .kmz, .zip(shp)")


@app.get("/truth/santo_antonio.geojson")
def truth_santo_antonio():
    """Verdad de campo: shapefile real Faz. Santo Antonio (137.05 ha)."""
    import json
    p = ROOT / "output" / "santo_antonio_truth_wgs84.geojson"
    if not p.exists():
        raise HTTPException(404, "Truth no disponible. Correr 01_prepare_aoi.py primero.")
    return JSONResponse(json.loads(p.read_text(encoding="utf-8")))


@app.get("/farms/{farm_id}/export.geojson")
def export_farm(farm_id: int, x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    fc = lots_db.export_farm_geojson(farm_id)
    return JSONResponse(fc, headers={
        "Content-Disposition": f'attachment; filename="finca_{farm_id}_lotes.geojson"'
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=False)
