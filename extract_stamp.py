"""Render original PDF page and extract bottom stamp area as PNG."""
import fitz

src = r"D:\PIXADVISOR_AGENT_WORKSPACE\MDO_Autorizacion_Original.pdf"
doc = fitz.open(src)
page = doc[0]

# Render full page at high DPI
pix = page.get_pixmap(dpi=300)
full_path = r"D:\PIXADVISOR_AGENT_WORKSPACE\original_page_full.png"
pix.save(full_path)
print(f"Full page: {pix.width}x{pix.height}")

# Crop bottom-right stamp region (approximate based on layout)
# Page is approximately 2480x3508 at 300dpi (A4)
# Stamp is in bottom-right corner
w, h = pix.width, pix.height
stamp_left = int(w * 0.48)
stamp_top = int(h * 0.91)
stamp_right = int(w * 0.97)
stamp_bottom = int(h * 0.985)

clip = fitz.Rect(
    stamp_left * 72 / 300,
    stamp_top * 72 / 300,
    stamp_right * 72 / 300,
    stamp_bottom * 72 / 300,
)
stamp_pix = page.get_pixmap(dpi=300, clip=clip)
stamp_path = r"D:\PIXADVISOR_AGENT_WORKSPACE\stamp_extracted.png"
stamp_pix.save(stamp_path)
print(f"Stamp: {stamp_pix.width}x{stamp_pix.height} -> {stamp_path}")

doc.close()
