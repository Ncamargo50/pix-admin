"""
Second-pass organize: sub-folders inside intact Desktop folders.
SAFETY:
  - Creates subfolders only if missing
  - Skips moves when source missing OR destination exists
  - Never deletes / never overwrites
"""
import os
import shutil

DESKTOP = r"C:\Users\Usuario\Desktop"


def safe_move(src, dst, stats):
    if not os.path.exists(src):
        stats["src_missing"] += 1
        return f"  SKIP src-missing  {os.path.relpath(src, DESKTOP)}"
    if os.path.exists(dst):
        stats["dst_conflict"] += 1
        return f"  SKIP dst-exists   {os.path.relpath(src, DESKTOP)} -> {os.path.relpath(dst, DESKTOP)}"
    try:
        shutil.move(src, dst)
        stats["moved"] += 1
        return f"  MOVED             {os.path.relpath(src, DESKTOP)} -> {os.path.relpath(dst, DESKTOP)}"
    except Exception as e:
        stats["error"] += 1
        return f"  ERROR             {os.path.relpath(src, DESKTOP)}: {e}"


def ensure_subdir(parent, name):
    p = os.path.join(parent, name)
    if os.path.isdir(p):
        return f"  EXISTS    {os.path.relpath(p, DESKTOP)}", p
    os.makedirs(p, exist_ok=False)
    return f"  CREATED   {os.path.relpath(p, DESKTOP)}", p


def organize_section(label, parent_rel, subdirs_plan, file_assignments, stats):
    """
    label: section header.
    parent_rel: parent folder relative to DESKTOP.
    subdirs_plan: list of subfolder names to ensure.
    file_assignments: dict {filename_in_parent: subfolder_name}.
    """
    parent = os.path.join(DESKTOP, parent_rel)
    print()
    print(f"=== {label} === ({parent_rel})")
    if not os.path.isdir(parent):
        print(f"  PARENT MISSING -- abort section")
        stats["error"] += 1
        return

    print(f"  -- ensure subfolders --")
    sub_paths = {}
    for s in subdirs_plan:
        msg, p = ensure_subdir(parent, s)
        print(msg)
        sub_paths[s] = p

    print(f"  -- move files --")
    for fname, sub in file_assignments.items():
        src = os.path.join(parent, fname)
        dst = os.path.join(sub_paths[sub], fname)
        print(safe_move(src, dst, stats))


stats = {"moved": 0, "src_missing": 0, "dst_conflict": 0, "error": 0}


# ============ 1. Notas-Varios ============
organize_section(
    label="Notas-Varios",
    parent_rel="Notas-Varios",
    subdirs_plan=["Prompts-IA", "Tracking", "Credenciales"],
    file_assignments={
        # The "#" filename has a special char (em dash). Use the raw name from inspect.
        "# Pixadvisor PRO — Identity  Eres m.txt": "Prompts-IA",
        "Pront-IA.txt": "Prompts-IA",
        "Lotes que estan faltando.txt": "Tracking",
        "BMAGRO ----.txt": "Tracking",
        "LLamar a Cloude CODEcd DPIXADVISOR_.txt": "Tracking",
        "Client ID drive 1012775070766-ai7lg.txt": "Credenciales",
    },
    stats=stats,
)


# ============ 2. GIS-Mapas ============
organize_section(
    label="GIS-Mapas",
    parent_rel="GIS-Mapas",
    subdirs_plan=["Vectorial", "Mapas-Ref", "Reportes"],
    file_assignments={
        # Vectorial: 8 geojson + 2 kml + 1 qmd sidecar
        "4A.geojson": "Vectorial",
        "4A.qmd": "Vectorial",
        "Area-Prueba-3Zonas-Muestreo.geojson": "Vectorial",
        "LT1-Cancha-Norte.geojson": "Vectorial",
        "LT2-Cancha-Sur.geojson": "Vectorial",
        "Prueba-Cancha-Muestreo.geojson": "Vectorial",
        "Prueba-Cancha.geojson": "Vectorial",
        "Prueba-Cancha_2zonas_2pts_2sub.geojson": "Vectorial",
        "Area de Prueba-Aplicativo-Pix-Muestreo.kml": "Vectorial",
        "Prueba-Cancha.kml": "Vectorial",

        # Mapas-Ref: PNG references
        "ref_map_page1.png": "Mapas-Ref",
        "ref_map_page4.png": "Mapas-Ref",
        "ref_map_page5.png": "Mapas-Ref",
        "ref_map_page6.png": "Mapas-Ref",
        "ref_map_page7.png": "Mapas-Ref",
        "ref_map_page8.png": "Mapas-Ref",

        # Reportes: PDF + xlsx
        "Resultado-Analisis.pdf": "Reportes",
        "FICHA IBRA-DONIZETE FERNANDES.xlsx": "Reportes",
    },
    stats=stats,
)


# ============ 3. DJI-FLIP-06-05-2026 ============
# JPG_DJI_2026-02-08: 72 uppercase DJI_20260208*.JPG
dji_main = {}
for i in range(1, 73):
    pass
# Build the exact filenames from the inspect output
DJI_MAIN_TIMESTAMPS = [
    "20260208155641_0001", "20260208155649_0002", "20260208155655_0003", "20260208155700_0004",
    "20260208155716_0005", "20260208155720_0006", "20260208155723_0007", "20260208155727_0008",
    "20260208155813_0009", "20260208155820_0010", "20260208155825_0011", "20260208155829_0012",
    "20260208155832_0013", "20260208155836_0014", "20260208155840_0015", "20260208155926_0016",
    "20260208155935_0017", "20260208155945_0018", "20260208155951_0019", "20260208155953_0020",
    "20260208160005_0021", "20260208160020_0022", "20260208160025_0023", "20260208160039_0024",
    "20260208160044_0025", "20260208160046_0026", "20260208160113_0027", "20260208160116_0028",
    "20260208160124_0029", "20260208160129_0030", "20260208160132_0031", "20260208160136_0032",
    "20260208160255_0033", "20260208160300_0034", "20260208160339_0035", "20260208160343_0036",
    "20260208160346_0037", "20260208160419_0038", "20260208160422_0039", "20260208160427_0040",
    "20260208160432_0041", "20260208160435_0042", "20260208160438_0043", "20260208160510_0044",
    "20260208160530_0045", "20260208160533_0046", "20260208160535_0047", "20260208160538_0048",
    "20260208160541_0049", "20260208160543_0050", "20260208173220_0051", "20260208173225_0052",
    "20260208173228_0053", "20260208173231_0054", "20260208173233_0055", "20260208173240_0056",
    "20260208173244_0057", "20260208173252_0058", "20260208173259_0059", "20260208173338_0060",
    "20260208173353_0061", "20260208173356_0062", "20260208173401_0063", "20260208173406_0064",
    "20260208173411_0065", "20260208173414_0066", "20260208173427_0067", "20260208173457_0068",
    "20260208173511_0069", "20260208173514_0070", "20260208173517_0071", "20260208173520_0072",
]
dji_assign = {f"DJI_{ts}_D.JPG": "JPG_DJI_2026-02-08" for ts in DJI_MAIN_TIMESTAMPS}

# JPG_Fly_2026-03: dji_fly photos (March 2026 + one March 4)
DJI_FLY_PHOTOS = [
    "dji_fly_20260304_155407_0_1772650447698_photo_low_quality.jpg",
    "dji_fly_20260316_155820_0155_1773688755544_photo.jpg",
    "dji_fly_20260316_155844_0156_1773688752932_photo.jpg",
    "dji_fly_20260316_155848_0157_1773688750435_photo.jpg",
    "dji_fly_20260316_155850_0158_1773688747907_photo.jpg",
    "dji_fly_20260316_160204_0160_1773688745417_photo.jpg",
    "dji_fly_20260316_160206_0161_1773688742916_photo.jpg",
    "dji_fly_20260316_161006_0165_1773688740383_photo.jpg",
    "dji_fly_20260316_161012_0166_1773688737853_photo.jpg",
    "dji_fly_20260316_161022_0167_1773688735243_photo.jpg",
]
for n in DJI_FLY_PHOTOS:
    dji_assign[n] = "JPG_Fly_2026-03"

# JPG_Numeradas: lowercase number.jpg
NUMERADAS = [
    "44.jpg", "45.jpg",
    "175.jpg", "177.jpg", "181.jpg", "183.jpg", "184.jpg",
    "216.jpg",
    "223.jpg", "225.jpg", "226.jpg", "227.jpg", "228.jpg", "230.jpg",
    "232.jpg", "233.jpg", "234.jpg", "235.jpg", "236.jpg",
    "346.jpg", "347.jpg", "348.jpg", "349.jpg", "350.jpg",
    "351.jpg", "352.jpg", "353.jpg", "354.jpg", "355.jpg",
    "356.jpg", "357.jpg", "358.jpg", "359.jpg", "360.jpg",
    "362.jpg", "363.jpg", "364.jpg", "366.jpg", "367.jpg",
    "368.jpg", "369.jpg", "370.jpg",
    "373.jpg", "375.jpg", "377.jpg", "379.jpg", "380.jpg",
    "381.jpg", "382.jpg", "383.jpg",
    "545.jpg", "548.jpg", "551.jpg", "552.jpg", "553.jpg",
    "554.jpg", "555.jpg", "556.jpg", "559.jpg", "568.jpg", "569.jpg",
]
for n in NUMERADAS:
    dji_assign[n] = "JPG_Numeradas"

# Videos_MP4: all .mp4
VIDEOS = [
    "dji_fly_20250613_134331_0_1749833011775_video_low_quality.mp4",
    "dji_fly_20250813_095703_0_1755089823369_video_low_quality.mp4",
    "dji_fly_20250831_092112_0_1756642872462_video_low_quality.mp4",
    "dji_fly_20260304_155221_0_1772650341847_video_low_quality.mp4",
    "screen-20250509-141707.mp4",
    "screen-20250523-131743.mp4",
    "screen-20260506-095049.mp4",
    "screen-20260506-123432.mp4",
]
for n in VIDEOS:
    dji_assign[n] = "Videos_MP4"


organize_section(
    label="DJI-FLIP-06-05-2026",
    parent_rel=r"_VUELOS_DJI\DJI-FLIP-06-05-2026",
    subdirs_plan=["JPG_DJI_2026-02-08", "JPG_Fly_2026-03", "JPG_Numeradas", "Videos_MP4"],
    file_assignments=dji_assign,
    stats=stats,
)


# ============ Summary ============
print()
print("==========================")
print("       FINAL SUMMARY      ")
print("==========================")
print(f"  Moved:               {stats['moved']}")
print(f"  Source missing:      {stats['src_missing']}")
print(f"  Destination exists:  {stats['dst_conflict']}")
print(f"  Errors:              {stats['error']}")
