"""
Update memory files: rewrite Desktop\... paths to point to the new umbrella folders.
SAFETY:
  - Only changes strings, never deletes files
  - Prints every replacement count
  - Skips PIXADVISOR_V8_VUELOS (not moved)
"""
import os

MEMORY_DIR = r"C:\Users\Usuario\.claude\projects\D--PIXADVISOR-AGENT-WORKSPACE\memory"

# Old path fragment -> new path fragment.
# Cover both `\` and `/` and bare `Desktop\X` (no drive prefix) forms.
REPLACEMENTS = [
    # PIXADVISOR_VUELOS_FINAL -> _VUELOS_DJI\PIXADVISOR_VUELOS_FINAL
    (r"Desktop\PIXADVISOR_VUELOS_FINAL", r"Desktop\_VUELOS_DJI\PIXADVISOR_VUELOS_FINAL"),
    ("Desktop/PIXADVISOR_VUELOS_FINAL", "Desktop/_VUELOS_DJI/PIXADVISOR_VUELOS_FINAL"),

    # HACIENDA-DEL-SENOR-PIX-MUESTREO -> _PROYECTOS_ACTIVOS\HACIENDA-...
    (r"Desktop\HACIENDA-DEL-SENOR-PIX-MUESTREO", r"Desktop\_PROYECTOS_ACTIVOS\HACIENDA-DEL-SENOR-PIX-MUESTREO"),
    ("Desktop/HACIENDA-DEL-SENOR-PIX-MUESTREO", "Desktop/_PROYECTOS_ACTIVOS/HACIENDA-DEL-SENOR-PIX-MUESTREO"),

    # PIXADVISOR_TRI_Cosecha_HDS_2026-05-20 -> _PROYECTOS_ACTIVOS\PIXADVISOR_TRI_...
    (r"Desktop\PIXADVISOR_TRI_Cosecha_HDS_2026-05-20", r"Desktop\_PROYECTOS_ACTIVOS\PIXADVISOR_TRI_Cosecha_HDS_2026-05-20"),
    ("Desktop/PIXADVISOR_TRI_Cosecha_HDS_2026-05-20", "Desktop/_PROYECTOS_ACTIVOS/PIXADVISOR_TRI_Cosecha_HDS_2026-05-20"),

    # PIXADVISOR_Hacienda_del_Senor_2026-05-15 -> _PROYECTOS_ACTIVOS\PIXADVISOR_Hacienda...
    (r"Desktop\PIXADVISOR_Hacienda_del_Senor_2026-05-15", r"Desktop\_PROYECTOS_ACTIVOS\PIXADVISOR_Hacienda_del_Senor_2026-05-15"),
    ("Desktop/PIXADVISOR_Hacienda_del_Senor_2026-05-15", "Desktop/_PROYECTOS_ACTIVOS/PIXADVISOR_Hacienda_del_Senor_2026-05-15"),
]

# Defensive guard: avoid double-substitution.
# If the new path already exists in the file content, skip that replacement.

def main():
    total_files_changed = 0
    total_replacements = 0

    for fname in sorted(os.listdir(MEMORY_DIR)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(MEMORY_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        original = content
        file_changes = 0

        for old, new in REPLACEMENTS:
            # If new path already present, the file was already updated — skip
            if new in content and old not in content:
                continue
            # Avoid double-prefixing: if new path is a superstring of old path,
            # skip occurrences that already contain `new`.
            if new in content:
                # Replace only the remaining occurrences of `old` that are NOT
                # already inside `new`. Easiest: temporarily mark new, do replace, unmark.
                sentinel = "\x00MARKER\x00"
                content = content.replace(new, sentinel)
                count = content.count(old)
                content = content.replace(old, new)
                content = content.replace(sentinel, new)
                file_changes += count
            else:
                count = content.count(old)
                if count:
                    content = content.replace(old, new)
                    file_changes += count

        if content != original:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  UPDATED  {fname}  ({file_changes} replacements)")
            total_files_changed += 1
            total_replacements += file_changes

    print()
    print(f"--- Summary ---")
    print(f"  Files changed:    {total_files_changed}")
    print(f"  Total rewrites:   {total_replacements}")


if __name__ == "__main__":
    main()
