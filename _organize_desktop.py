"""
Organize C:\\Users\\Usuario\\Desktop into 5 umbrella folders.
SAFETY:
  - Creates umbrella folders only if missing
  - Moves only if source exists
  - Skips (does NOT overwrite) if destination already exists
  - Never deletes source
  - Logs every action to stdout
"""
import os
import shutil
import sys

DESKTOP = r"C:\Users\Usuario\Desktop"

# Umbrella folders to create
UMBRELLAS = [
    "_PROYECTOS_ACTIVOS",
    "_VUELOS_DJI",
    "_APK_RELEASES_ACTAS",
    "_NOTAS_SUELTAS",
    "_SECRETOS_NO_COMPARTIR",
]

# Map: source name (relative to Desktop) -> umbrella folder
MOVES = {
    # _PROYECTOS_ACTIVOS
    "PIXADVISOR_Hacienda_del_Senor_2026-05-15": "_PROYECTOS_ACTIVOS",
    "HACIENDA-DEL-SENOR-PIX-MUESTREO": "_PROYECTOS_ACTIVOS",
    "PIXADVISOR_TRI_Cosecha_HDS_2026-05-20": "_PROYECTOS_ACTIVOS",
    "HACIENDA-DEL-SENOR-PIX-MUESTREO.zip": "_PROYECTOS_ACTIVOS",
    "PIXADVISOR_FichasDigitales_CelularTop20.zip": "_PROYECTOS_ACTIVOS",
    "PIXADVISOR_GeoPDF_Avenza_Top20.zip": "_PROYECTOS_ACTIVOS",
    "PIXADVISOR_APKPixMuestreo_Top20.zip": "_PROYECTOS_ACTIVOS",
    "PIXADVISOR_MuestreoTop20_Datos.xlsx": "_PROYECTOS_ACTIVOS",

    # _VUELOS_DJI
    "DJI-FLIP-06-05-2026": "_VUELOS_DJI",
    "PIXADVISOR_VUELOS_FINAL": "_VUELOS_DJI",
    "PV2DST_misiones_divididas (1).zip": "_VUELOS_DJI",
    "Mision-S-F.zip": "_VUELOS_DJI",
    "PV2DST_misiones_PIXADVISOR.zip": "_VUELOS_DJI",
    "SF_V7_PIXADVISOR_BLOQUES.zip": "_VUELOS_DJI",
    "SA_V7_PIXADVISOR_BLOQUES.zip": "_VUELOS_DJI",

    # _APK_RELEASES_ACTAS
    "pix-muestreo-v3.16.0-RELEASE-INFO.txt": "_APK_RELEASES_ACTAS",
    "pix-muestreo-v3.17.0-RELEASE-INFO.txt": "_APK_RELEASES_ACTAS",
    "pix-muestreo-v3.17.1-RELEASE-INFO.txt": "_APK_RELEASES_ACTAS",
    "ACTA-CERTIFICACION-PIX-MUESTREO-v3.17.1.txt": "_APK_RELEASES_ACTAS",
    "ACTA-CERTIFICACION-FINAL-PIX-MUESTREO-v3.17.1.txt": "_APK_RELEASES_ACTAS",
    "COMPATIBILIDAD-APK-PLATAFORMA-v3.17.1.txt": "_APK_RELEASES_ACTAS",
    "ACTA-DASHBOARD-v1.1-SCORE-9.5.txt": "_APK_RELEASES_ACTAS",
    "EJECUTAR-ESTO-EN-SUPABASE.txt": "_APK_RELEASES_ACTAS",
    "proyecto-prueba-3zonas-1sub.json": "_APK_RELEASES_ACTAS",

    # _NOTAS_SUELTAS
    "Generá zonas de manejo para el Lote.txt": "_NOTAS_SUELTAS",
    "Respaldar informe ibra automático c.txt": "_NOTAS_SUELTAS",

    # _SECRETOS_NO_COMPARTIR
    "Login-pixadmin.txt": "_SECRETOS_NO_COMPARTIR",
    "anthropi_key.txt": "_SECRETOS_NO_COMPARTIR",
    "Client ID drive 1012775070766-ai7lg.txt": "_SECRETOS_NO_COMPARTIR",
}


def main():
    if not os.path.isdir(DESKTOP):
        print(f"[FATAL] Desktop not found: {DESKTOP}")
        sys.exit(1)

    print(f"=== ORGANIZE DESKTOP ===")
    print(f"Target: {DESKTOP}")
    print()

    # Step 1: create umbrella folders
    print("--- Step 1: ensure umbrella folders ---")
    for u in UMBRELLAS:
        p = os.path.join(DESKTOP, u)
        if os.path.isdir(p):
            print(f"  EXISTS    {u}")
        elif os.path.exists(p):
            print(f"  CONFLICT  {u} exists but is not a directory — SKIP")
        else:
            os.makedirs(p, exist_ok=False)
            print(f"  CREATED   {u}")

    # Step 2: move items
    print()
    print("--- Step 2: move items ---")
    stats = {"moved": 0, "src_missing": 0, "dst_conflict": 0}
    for src_name, umbrella in MOVES.items():
        src = os.path.join(DESKTOP, src_name)
        dst_dir = os.path.join(DESKTOP, umbrella)
        dst = os.path.join(dst_dir, src_name)

        if not os.path.exists(src):
            print(f"  SKIP src-missing  {src_name}")
            stats["src_missing"] += 1
            continue

        if os.path.exists(dst):
            print(f"  SKIP dst-exists   {src_name}  -> {umbrella}\\")
            stats["dst_conflict"] += 1
            continue

        try:
            shutil.move(src, dst)
            print(f"  MOVED             {src_name}  -> {umbrella}\\")
            stats["moved"] += 1
        except Exception as e:
            print(f"  ERROR             {src_name}: {e}")

    print()
    print("--- Summary ---")
    print(f"  Moved:               {stats['moved']}")
    print(f"  Source missing:      {stats['src_missing']}")
    print(f"  Destination exists:  {stats['dst_conflict']}")
    print(f"  Total planned:       {len(MOVES)}")


if __name__ == "__main__":
    main()
