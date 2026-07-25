"""Re-extract stamp at high DPI and enhance contrast/sharpness."""
import fitz
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

src = r"D:\PIXADVISOR_AGENT_WORKSPACE\MDO_Autorizacion_Original.pdf"
out_raw = r"D:\PIXADVISOR_AGENT_WORKSPACE\stamp_hires_raw.png"
out_clean = r"D:\PIXADVISOR_AGENT_WORKSPACE\stamp_hd.png"

doc = fitz.open(src)
page = doc[0]

# Render at 600 DPI for high resolution
DPI = 600
pix = page.get_pixmap(dpi=DPI)
W, H = pix.width, pix.height

# Crop bottom-right stamp area
left = int(W * 0.48)
top = int(H * 0.91)
right = int(W * 0.97)
bottom = int(H * 0.985)

clip_pdf = fitz.Rect(
    left * 72 / DPI,
    top * 72 / DPI,
    right * 72 / DPI,
    bottom * 72 / DPI,
)
stamp_pix = page.get_pixmap(dpi=DPI, clip=clip_pdf)
stamp_pix.save(out_raw)
print(f"Raw extract: {stamp_pix.width}x{stamp_pix.height}")

# Load with PIL for enhancement
img = Image.open(out_raw).convert("RGB")
print(f"Loaded: {img.size}")

# Step 1: convert to grayscale to work with the ink
gray = img.convert("L")

# Step 2: increase contrast hard — push light pixels to white, dark to black
# autocontrast with cutoff to remove background noise
gray_ac = ImageOps.autocontrast(gray, cutoff=(2, 0))

# Step 3: threshold-like curve — make ink pure black, paper pure white
# Use a soft threshold that preserves anti-aliased edges
def punch_curve(v):
    # Below 90 -> very dark; above 200 -> white
    if v < 80:
        return 0
    if v > 210:
        return 255
    # smooth ramp
    t = (v - 80) / (210 - 80)
    # Strong S-curve
    if t < 0.5:
        t2 = 2 * t * t
    else:
        t2 = 1 - (-2 * t + 2) ** 2 / 2
    return int(t2 * 255)

cleaned = gray_ac.point(punch_curve)

# Step 4: slight sharpen to crisp the strokes
cleaned = cleaned.filter(ImageFilter.UnsharpMask(radius=1.5, percent=140, threshold=2))

# Step 5: convert to RGB and tint slightly toward navy/dark blue (rubber stamp ink)
rgb = Image.new("RGB", cleaned.size, (255, 255, 255))
ink_color = (28, 38, 90)  # dark navy blue ink
ink_layer = Image.new("RGB", cleaned.size, ink_color)
# Use cleaned as inverse alpha — black text becomes ink color
inverse = ImageOps.invert(cleaned)
rgb.paste(ink_layer, (0, 0), inverse)

# Step 6: optional — slight transparency for non-ink areas (so it sits on white)
final = rgb.convert("RGBA")
# make near-white pixels fully transparent
data = final.load()
w, h = final.size
for y in range(h):
    for x in range(w):
        r, g, b, a = data[x, y]
        # measure how "white" (background) the pixel is
        whiteness = min(r, g, b)
        if whiteness > 235:
            data[x, y] = (r, g, b, 0)
        elif whiteness > 200:
            # partial fade
            alpha = int(255 * (235 - whiteness) / (235 - 200))
            data[x, y] = (r, g, b, alpha)

final.save(out_clean, optimize=True)
print(f"Saved HD stamp: {out_clean} -> {final.size}")

doc.close()
