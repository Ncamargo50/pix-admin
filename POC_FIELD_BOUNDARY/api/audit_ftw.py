"""
Auditoria tecnica del pipeline FTW PRUE.

Genera visualizaciones de cada etapa para identificar dónde rompe la delimitación:
  1. Sentinel-2 RGB (input)
  2. Probabilidad EXTENT (clase 1) - heatmap
  3. Probabilidad BOUNDARY (clase 2) - heatmap
  4. Markers usados por watershed
  5. Labels watershed (cada lote color distinto)
  6. Boundary FILTRADO (solo lineas largas) - propuesta de fix

Output: PNGs en output/audit/ y diagnóstico imprimido.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "audit"
OUT.mkdir(parents=True, exist_ok=True)


def main(bbox=None):
    bbox = bbox or [-58.808, -18.470, -58.778, -18.448]
    print(f">>> Auditando bbox {bbox}")

    from ftw_prue_detector import (
        _fetch_s2_window_bgrn, _normalize_for_prue,
        _tile_inference, _load_prue_model
    )
    import torch

    # 1. Bajar 2 windows S2
    print("    Bajando S2 Win A (Q1) + Win B (Q3)...")
    win_a, transform, crs, n_a = _fetch_s2_window_bgrn(
        bbox, "2025-01-01", "2025-03-31", scale=10)
    win_b, _, _, n_b = _fetch_s2_window_bgrn(
        bbox, "2025-07-01", "2025-09-30", scale=10)
    H, W = win_a.shape[:2]
    print(f"    Shape: {H}x{W}, escenas A={n_a}, B={n_b}")

    # 2. Generar RGB para visualizacion (de Win A solamente)
    rgb_vis = win_a[:, :, [2, 1, 0]]  # B4, B3, B2
    rgb_vis = np.clip(rgb_vis.astype(np.float32) * 0.8 / 30, 0, 255).astype(np.uint8)

    # 3. Stack 8 channels y inference
    def reorder(arr):
        return np.stack([arr[:, :, 2], arr[:, :, 1], arr[:, :, 0], arr[:, :, 3]], axis=-1)
    stack_8ch = np.concatenate([reorder(win_a), reorder(win_b)], axis=-1)
    stack_norm = _normalize_for_prue(stack_8ch)

    print("    Inferiendo PRUE...")
    model, device = _load_prue_model()
    logits = _tile_inference(model, device, stack_norm, tile_size=256, overlap=64)
    probs = torch.softmax(torch.from_numpy(logits), dim=0).numpy()
    background_prob = probs[0]
    extent_prob = probs[1]
    boundary_prob = probs[2]

    # 4. Stats del modelo
    print("\n=== STATS DE PROBABILIDADES (auditoria) ===")
    for name, p in [("background", background_prob), ("extent", extent_prob), ("boundary", boundary_prob)]:
        print(f"  {name}: min={p.min():.3f} max={p.max():.3f} mean={p.mean():.3f} median={np.median(p):.3f}")
        print(f"    {name} > 0.30: {(p > 0.30).sum()/p.size*100:.1f}% pixels")
        print(f"    {name} > 0.50: {(p > 0.50).sum()/p.size*100:.1f}% pixels")
        print(f"    {name} > 0.70: {(p > 0.70).sum()/p.size*100:.1f}% pixels")

    # 5. Diagnostico de boundary
    boundary_strong = boundary_prob > 0.50
    boundary_weak = (boundary_prob > 0.30) & (boundary_prob <= 0.50)
    print(f"\n  Boundary strong (>0.50): {boundary_strong.sum()/boundary_prob.size*100:.1f}% pixels")
    print(f"  Boundary weak (0.30-0.50): {boundary_weak.sum()/boundary_prob.size*100:.1f}% pixels")

    # Componentes de boundary - detectar boundaries cortas (intra-lote, ruido) vs largas (inter-lote)
    bnd_dilated = ndi.binary_dilation(boundary_strong, iterations=2)
    n_bnd, lbl_bnd = ndi.label(bnd_dilated)
    if int(n_bnd) > 0:
        sizes = ndi.sum(bnd_dilated, lbl_bnd, range(1, int(n_bnd) + 1))
        print(f"\n  Componentes de boundary: {n_bnd}")
        print(f"    < 30 px (probable intra-lote): {(sizes < 30).sum()}")
        print(f"    30-100 px (medio): {((sizes >= 30) & (sizes < 100)).sum()}")
        print(f"    >= 100 px (probable inter-lote real): {(sizes >= 100).sum()}")

    # 6. Boundary FILTRADO: solo componentes >= 50 px
    boundary_clean = np.zeros_like(boundary_strong)
    if int(n_bnd) > 0:
        for i in range(1, int(n_bnd) + 1):
            if sizes[i-1] >= 50:
                boundary_clean[lbl_bnd == i] = True
    print(f"\n  Boundary CLEAN (solo lineas largas): {boundary_clean.sum()/boundary_clean.size*100:.1f}% pixels")

    # 7. Generar visualizaciones
    print("\n>>> Guardando visualizaciones en output/audit/")
    fig, axes = plt.subplots(2, 3, figsize=(20, 13))

    axes[0,0].imshow(rgb_vis)
    axes[0,0].set_title("1. Sentinel-2 RGB Win A (Q1)")
    axes[0,0].axis("off")

    im = axes[0,1].imshow(extent_prob, cmap="RdYlGn", vmin=0, vmax=1)
    axes[0,1].set_title(f"2. EXTENT prob (>0.30={(extent_prob>0.30).sum()/extent_prob.size*100:.0f}%)")
    plt.colorbar(im, ax=axes[0,1], fraction=0.046)
    axes[0,1].axis("off")

    im = axes[0,2].imshow(boundary_prob, cmap="hot", vmin=0, vmax=1)
    axes[0,2].set_title(f"3. BOUNDARY prob (>0.50={boundary_strong.sum()/boundary_prob.size*100:.1f}%)")
    plt.colorbar(im, ax=axes[0,2], fraction=0.046)
    axes[0,2].axis("off")

    axes[1,0].imshow(rgb_vis)
    axes[1,0].imshow(np.where(extent_prob > 0.30, extent_prob, np.nan),
                     cmap="Greens", alpha=0.55, vmin=0, vmax=1)
    axes[1,0].imshow(np.where(boundary_prob > 0.50, 1, np.nan), cmap="Reds", alpha=0.85)
    axes[1,0].set_title("4. RGB + extent (verde) + boundary (rojo)")
    axes[1,0].axis("off")

    axes[1,1].imshow(rgb_vis)
    axes[1,1].imshow(np.where(boundary_strong, 1, np.nan), cmap="autumn", alpha=0.9)
    axes[1,1].set_title(f"5. Boundary RAW: {n_bnd} componentes")
    axes[1,1].axis("off")

    axes[1,2].imshow(rgb_vis)
    axes[1,2].imshow(np.where(boundary_clean, 1, np.nan), cmap="autumn", alpha=0.9)
    axes[1,2].set_title(f"6. Boundary FILTRADO (>=50 px): solo lineas largas")
    axes[1,2].axis("off")

    plt.tight_layout()
    out_png = OUT / "ftw_audit.png"
    plt.savefig(out_png, dpi=110, bbox_inches="tight")
    plt.close()
    print(f"<<< {out_png}")

    # 8. Probar watershed con boundary FILTRADO vs RAW
    from skimage.segmentation import watershed
    from skimage.feature import peak_local_max

    def run_watershed(bnd_mask, label_str):
        field = extent_prob > 0.30
        field = ndi.binary_closing(field, iterations=2)
        field = ndi.binary_fill_holes(field)
        seed = (extent_prob > 0.55) & (~bnd_mask)
        seed = ndi.binary_erosion(seed, iterations=2)
        markers, n = ndi.label(seed)
        if n > 0:
            sizes = ndi.sum(seed, markers, range(1, n + 1))
            for i in np.where(sizes < 5)[0]:
                markers[markers == i + 1] = 0
        n_markers = int(markers.max())
        if n_markers == 0:
            print(f"    {label_str}: 0 markers -> 0 lotes")
            return None
        elevation = (boundary_prob - extent_prob * 0.5).astype(np.float32)
        labels = watershed(elevation, markers=markers, mask=field, watershed_line=False)
        n_lots = int(labels.max())
        print(f"    {label_str}: {n_markers} markers -> {n_lots} lotes")
        return labels

    print("\n=== COMPARACION watershed: boundary RAW vs FILTRADO ===")
    labels_raw = run_watershed(boundary_strong, "RAW (boundary > 0.50)")
    labels_clean = run_watershed(boundary_clean, "FILTRADO (lineas >=50 px)")

    # 9. Visualizar comparacion lotes
    fig2, axes2 = plt.subplots(1, 2, figsize=(20, 9))
    for ax, labels, label in [(axes2[0], labels_raw, "RAW"), (axes2[1], labels_clean, "FILTRADO")]:
        ax.imshow(rgb_vis)
        if labels is not None:
            from matplotlib.colors import ListedColormap
            n = int(labels.max()) if labels is not None else 0
            colors = plt.get_cmap("tab20")(np.arange(n) % 20)
            colors = np.vstack([[0, 0, 0, 0], colors])  # 0 = transparent
            cmap = ListedColormap(colors)
            ax.imshow(labels, cmap=cmap, alpha=0.55)
            ax.set_title(f"Watershed {label}: {n} lotes detectados")
        else:
            ax.set_title(f"Watershed {label}: SIN MARKERS")
        ax.axis("off")
    plt.tight_layout()
    out_png2 = OUT / "ftw_audit_watershed.png"
    plt.savefig(out_png2, dpi=110, bbox_inches="tight")
    plt.close()
    print(f"<<< {out_png2}")

    print("\n=== DIAGNOSTICO FINAL ===")
    print("Mira 'output/audit/ftw_audit.png' panel 5 vs 6:")
    print("  - Si en panel 5 hay MUCHAS rayas cortas dentro de un lote = boundary intra-lote (problema)")
    print("  - Si en panel 6 (filtrado) las rayas largas estan SOLO en separaciones reales = fix correcto")
    print("\nMira 'output/audit/ftw_audit_watershed.png':")
    print("  - Si RAW tiene 1 lote real = N pedazos, FILTRADO debe tener menos pedazos")
    print("  - Si FILTRADO sigue dividiendo dentro = el problema esta en extent_prob (no boundary)")


if __name__ == "__main__":
    main()
