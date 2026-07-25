# -*- coding: utf-8 -*-
"""Generador de planes de vuelo DJI Mavic 3M (mapping2d, DJI Pilot 2) para lotes
Cerro Alto. RGB GSD 2.5cm @95m, terrain follow real-time, RTK, sin corte.
Schema WPML verificado: drone 77/sub2, payload 68, ns wpmz/1.0.6."""
import os, sys, math, zipfile, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, numpy as np
from shapely.geometry import LineString, Point
from shapely.affinity import rotate, translate
from shapely.ops import unary_union
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import rasterio
import warnings; warnings.filterwarnings('ignore')

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUTDIR = os.path.join(DIRBASE, 'Vuelos_Mavic3M'); os.makedirs(OUTDIR, exist_ok=True)
RGB = os.path.join(DIRBASE, '_analisis_canadas', 's2_rgb_lotes.tif')
ARG = sys.argv[1] if len(sys.argv) > 1 else 'sample'

# --- parametros M3M (RGB GSD 2.5cm) ---
AGL = 95.0           # m AGL -> GSD 2.5cm RGB (GSD=H/37.9)
GSD_CM = 2.5
OVL_FRONT = 80       # orthoCameraOverlapH
OVL_SIDE = 70        # orthoCameraOverlapW
SPEED = 9.0          # m/s — optimizado: obturador mecanico M3M sin motion blur (a 19.8m/foto = 2.2s, ok)
MARGIN = 15.0        # m fuera del poligono
# footprint RGB a 95m: 5280x3956 px @ GSD 2.5cm
FOOT_W = GSD_CM/100 * 5280          # 132.0 m (across)
FOOT_H = GSD_CM/100 * 3956          # 98.9 m (along)
LINE_SP = FOOT_W * (1 - OVL_SIDE/100)    # 39.6 m
PHOTO_SP = FOOT_H * (1 - OVL_FRONT/100)  # 19.8 m
BAT_MIN = 32         # min utiles de mapeo por bateria (M3M con RTK, conservador)

lot = gpd.read_file(os.path.join(DIRBASE, 'Lotes_BASE_FINAL.geojson')).to_crs(31981)
lot['area_ha'] = lot.area / 1e4

def boustro(poly, spacing, direction_deg):
    """lineas paralelas en 'direction_deg' (azimuth eje mayor), recortadas al poligono+margen."""
    work = poly.buffer(MARGIN)
    cx, cy = work.centroid.x, work.centroid.y
    rot = rotate(work, -direction_deg, origin=(cx, cy))   # alinear eje mayor a horizontal
    minx, miny, maxx, maxy = rot.bounds
    lines = []
    y = miny + spacing/2
    while y <= maxy:
        seg = LineString([(minx-5, y), (maxx+5, y)]).intersection(rot)
        if not seg.is_empty:
            segs = [seg] if seg.geom_type == 'LineString' else list(seg.geoms)
            for s in segs:
                if s.length > 5: lines.append(s)
        y += spacing
    # rotar de vuelta + ordenar boustrophedon
    out = [rotate(s, direction_deg, origin=(cx, cy)) for s in lines]
    path = []
    for i, s in enumerate(out):
        pts = list(s.coords)
        if i % 2 == 1: pts = pts[::-1]
        path.append(pts)
    return path

def mbr_major_az(poly):
    mrr = poly.minimum_rotated_rectangle
    xs, ys = mrr.exterior.coords.xy
    edges = [(LineString([(xs[i], ys[i]), (xs[i+1], ys[i+1])])) for i in range(4)]
    e = max(edges, key=lambda l: l.length)
    (x0, y0), (x1, y1) = list(e.coords)
    dx, dy = x1-x0, y1-y0
    math_ang = math.degrees(math.atan2(dy, dx))         # angulo eje mayor desde X (rotacion shapely)
    az = math.degrees(math.atan2(dx, dy)) % 360         # azimuth compass del eje mayor (WPML direction)
    return math_ang, az, mrr

def plan_lote(row):
    poly = row.geometry
    survey = poly if poly.geom_type == 'Polygon' else poly.convex_hull
    math_ang, az, mrr = mbr_major_az(survey)
    path = boustro(survey, LINE_SP, math_ang)           # lineas a lo largo del eje mayor
    total_len = sum(LineString(p).length for p in path)
    # travel entre lineas (giros)
    travel = sum(Point(path[i][-1]).distance(Point(path[i+1][0])) for i in range(len(path)-1))
    n_lines = len(path)
    n_photos = int(total_len / PHOTO_SP) + n_lines
    dur_s = (total_len + travel) / SPEED + n_lines*4   # +4s por giro
    bats = max(1, math.ceil(dur_s/60 / BAT_MIN))
    return dict(az=az, path=path, n_lines=n_lines, total_len=total_len, travel=travel,
                n_photos=n_photos, dur_min=dur_s/60, bats=bats, survey=survey)

# WGS84 para el KMZ
lot4 = lot.to_crs(4326)

def to_wgs(path_utm, idx):
    g = gpd.GeoSeries([LineString(p) for p in path_utm], crs=31981).to_crs(4326)
    return [list(ls.coords) for ls in g]

def build_kmz(lote_id, row, pl, poly4):
    NS = 'http://www.dji.com/wpmz/1.0.6'
    coords_poly = ' '.join('%.8f,%.8f' % (x, y) for x, y in poly4.exterior.coords)
    miss = ('<wpml:missionConfig>'
            '<wpml:flyToWaylineMode>safely</wpml:flyToWaylineMode>'
            '<wpml:finishAction>goHome</wpml:finishAction>'
            '<wpml:exitOnRCLost>executeLostAction</wpml:exitOnRCLost>'
            '<wpml:executeRCLostAction>goBack</wpml:executeRCLostAction>'
            '<wpml:takeOffSecurityHeight>30</wpml:takeOffSecurityHeight>'
            '<wpml:globalTransitionalSpeed>8</wpml:globalTransitionalSpeed>'
            '<wpml:droneInfo><wpml:droneEnumValue>77</wpml:droneEnumValue>'
            '<wpml:droneSubEnumValue>2</wpml:droneSubEnumValue></wpml:droneInfo>'
            '<wpml:payloadInfo><wpml:payloadEnumValue>68</wpml:payloadEnumValue>'
            '<wpml:payloadPositionIndex>0</wpml:payloadPositionIndex></wpml:payloadInfo>'
            '</wpml:missionConfig>')
    template = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="{NS}">\n<Document>\n'
        f'<wpml:author>Pixadvisor-M3M</wpml:author>\n'
        f'<wpml:createTime>0</wpml:createTime><wpml:updateTime>0</wpml:updateTime>\n'
        f'{miss}\n'
        f'<Folder>\n'
        f'<wpml:templateType>mapping2d</wpml:templateType>\n<wpml:templateId>0</wpml:templateId>\n'
        f'<wpml:waylineCoordinateSysParam><wpml:coordinateMode>WGS84</wpml:coordinateMode>'
        f'<wpml:heightMode>realTimeFollowSurface</wpml:heightMode>'
        f'<wpml:positioningType>RTKBaseStation</wpml:positioningType></wpml:waylineCoordinateSysParam>\n'
        f'<wpml:autoFlightSpeed>{SPEED}</wpml:autoFlightSpeed>\n'
        f'<wpml:height>{AGL}</wpml:height><wpml:ellipsoidHeight>{AGL}</wpml:ellipsoidHeight>\n'
        f'<wpml:shootType>distance</wpml:shootType>\n'
        f'<wpml:direction>{pl["az"]:.1f}</wpml:direction>\n'
        f'<wpml:margin>{MARGIN:.0f}</wpml:margin>\n'
        f'<wpml:caliFlightEnable>0</wpml:caliFlightEnable>\n'
        f'<wpml:overlap><wpml:orthoCameraOverlapH>{OVL_FRONT}</wpml:orthoCameraOverlapH>'
        f'<wpml:orthoCameraOverlapW>{OVL_SIDE}</wpml:orthoCameraOverlapW></wpml:overlap>\n'
        f'<Placemark><Polygon><outerBoundaryIs><LinearRing>'
        f'<coordinates>{coords_poly}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>\n'
        f'</Folder>\n</Document>\n</kml>')
    # waylines: boustrophedon path como waypoints
    lines4 = gpd.GeoSeries([LineString(p) for p in pl['path']], crs=31981).to_crs(4326)
    wpts = []
    idx = 0
    for i, ls in enumerate(lines4):
        cc = list(ls.coords)
        if i % 2 == 1: cc = cc[::-1]
        for (x, y) in cc:
            wpts.append((idx, x, y)); idx += 1
    pm = []
    for (k, x, y) in wpts:
        pm.append(f'<Placemark><Point><coordinates>{x:.8f},{y:.8f}</coordinates></Point>'
                  f'<wpml:index>{k}</wpml:index><wpml:executeHeight>{AGL}</wpml:executeHeight>'
                  f'<wpml:waypointSpeed>{SPEED}</wpml:waypointSpeed>'
                  f'<wpml:waypointHeadingParam><wpml:waypointHeadingMode>followWayline</wpml:waypointHeadingMode></wpml:waypointHeadingParam>'
                  f'<wpml:waypointTurnParam><wpml:waypointTurnMode>toPointAndStopWithContinuityCurvature</wpml:waypointTurnMode>'
                  f'<wpml:waypointTurnDampingDist>0</wpml:waypointTurnDampingDist></wpml:waypointTurnParam></Placemark>')
    waylines = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:wpml="{NS}">\n<Document>\n{miss}\n'
        f'<Folder>\n<wpml:templateId>0</wpml:templateId><wpml:waylineId>0</wpml:waylineId>\n'
        f'<wpml:executeHeightMode>realTimeFollowSurface</wpml:executeHeightMode>\n'
        f'<wpml:autoFlightSpeed>{SPEED}</wpml:autoFlightSpeed>\n' + '\n'.join(pm) +
        f'\n</Folder>\n</Document>\n</kml>')
    kmz = os.path.join(OUTDIR, f'{lote_id}_M3M.kmz')
    with zipfile.ZipFile(kmz, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('wpmz/template.kml', template)
        z.writestr('wpmz/waylines.wpml', waylines)
    return kmz

def render(lote_id, row, pl):
    fig, ax = plt.subplots(figsize=(10, 8))
    poly4 = lot4[lot4.lote_id == lote_id].geometry.iloc[0]
    try:
        with rasterio.open(RGB) as r:
            b = poly4.bounds; mx = (b[2]-b[0])*0.1; my = (b[3]-b[1])*0.1
            win = rasterio.windows.from_bounds(b[0]-mx, b[1]-my, b[2]+mx, b[3]+my, r.transform)
            img = r.read(window=win); ext = rasterio.windows.bounds(win, r.transform)
            ax.imshow(np.transpose(img, (1, 2, 0)), extent=[ext[0], ext[2], ext[1], ext[3]])
    except Exception: pass
    path = pl['path']
    full = [pt for line in path for pt in line]                      # serpenteo continuo (lineas + giros)
    snake4 = gpd.GeoSeries([LineString(full)], crs=31981).to_crs(4326).iloc[0]
    xs, ys = snake4.xy
    ax.plot(xs, ys, color='yellow', linewidth=0.9, zorder=3)
    conns = [LineString([path[i][-1], path[i+1][0]]) for i in range(len(path)-1)]   # giros de entrada a la sig. linea
    gpd.GeoSeries(conns, crs=31981).to_crs(4326).plot(ax=ax, color='#FF1744', linewidth=1.6, zorder=4)
    s4 = gpd.GeoSeries([Point(full[0])], crs=31981).to_crs(4326).iloc[0]
    e4 = gpd.GeoSeries([Point(full[-1])], crs=31981).to_crs(4326).iloc[0]
    ax.scatter([s4.x], [s4.y], c='lime', s=70, edgecolor='k', zorder=6, label='Inicio')
    ax.scatter([e4.x], [e4.y], c='red', s=70, edgecolor='k', zorder=6, label='Fin')
    gpd.GeoSeries([poly4]).boundary.plot(ax=ax, color='cyan', linewidth=1.6)
    ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
    ax.set_title('%s — Plan de vuelo DJI Mavic 3M (RGB GSD 2.5cm @95m AGL)\n%d líneas · %.1f km · %d fotos · ~%.0f min · %d baterías · terrain follow + RTK'
                 % (lote_id, pl['n_lines'], (pl['total_len']+pl['travel'])/1000, pl['n_photos'], pl['dur_min'], pl['bats']), fontsize=10)
    ax.set_axis_off(); plt.tight_layout()
    png = os.path.join(OUTDIR, f'{lote_id}_M3M_plan.png'); plt.savefig(png, dpi=130, bbox_inches='tight'); plt.close()
    return png

# --- ejecutar ---
print('PARAMS M3M: AGL %.0fm | GSD %.1fcm RGB | line_sp %.1fm | photo_sp %.1fm | overlap %d/%d | %.1f m/s'
      % (AGL, GSD_CM, LINE_SP, PHOTO_SP, OVL_FRONT, OVL_SIDE, SPEED))
if ARG == 'sample':
    med = lot.sort_values('area_ha').iloc[len(lot)//2]; targets = [med['lote_id']]
    print('Lote de muestra (mediano):', targets[0], '%.1f ha' % med['area_ha'])
elif ARG == 'all':
    targets = sorted(lot['lote_id'])
else:
    targets = [ARG]

tot = dict(photos=0, min=0, bats=0); recs = []
for lid in targets:
    row = lot[lot.lote_id == lid].iloc[0]
    pl = plan_lote(row)
    survey4 = gpd.GeoSeries([pl['survey']], crs=31981).to_crs(4326).iloc[0]
    kmz = build_kmz(lid, row, pl, survey4)
    render(lid, row, pl)
    km = (pl['total_len']+pl['travel'])/1000
    tot['photos'] += pl['n_photos']; tot['min'] += pl['dur_min']; tot['bats'] += pl['bats']
    recs.append(dict(lote_id=lid, bloque=row['bloque'], area_ha=round(row['area_ha'], 1), dir_deg=round(pl['az'], 1),
                     n_lineas=pl['n_lines'], km=round(km, 1), fotos=pl['n_photos'], min=round(pl['dur_min']), baterias=pl['bats']))
    print('  %-16s %5.1f ha | dir %5.1f° | %3d líneas | %5.1f km | %4d fotos | ~%4.0f min | %d bat'
          % (lid, row['area_ha'], pl['az'], pl['n_lines'], km, pl['n_photos'], pl['dur_min'], pl['bats']))
if len(targets) > 1:
    import pandas as pd
    df = pd.DataFrame(recs).sort_values(['bloque', 'lote_id'])
    df.to_csv(os.path.join(OUTDIR, '_RESUMEN_vuelos_M3M.csv'), index=False, encoding='utf-8-sig')
    print('\nTOTAL CAMPAÑA: %d lotes | %d fotos | ~%.1f h vuelo | %d baterías | CSV guardado'
          % (len(targets), tot['photos'], tot['min']/60, tot['bats']))
    for b, g in df.groupby('bloque'):
        print('  Bloque %-3s: %2d lotes | %5d fotos | %3d baterías' % (b, len(g), g['fotos'].sum(), g['baterias'].sum()))
print('DONE')
