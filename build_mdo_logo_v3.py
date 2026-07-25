"""HD MDO AGRO logo v3 — exact match to original (Arial Black, tight stack, dramatic chrome)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import os

OUT = r"D:\PIXADVISOR_AGENT_WORKSPACE\mdo_logo_hd.png"

SCALE = 3
W, H = 1700, 1100
CW, CH = W * SCALE, H * SCALE

# Use Arial Black (matches original aesthetic — heavier, rounder than Impact)
font_path = r"C:\Windows\Fonts\ariblk.ttf"
if not os.path.exists(font_path):
    # fallback
    font_path = r"C:\Windows\Fonts\arialbd.ttf"
print(f"Using: {font_path}")

# Same font size for both lines (both lines visually equal weight)
FONT_SIZE = 360 * SCALE

font = ImageFont.truetype(font_path, FONT_SIZE)

img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

def measure(text, f):
    bbox = draw.textbbox((0, 0), text, font=f)
    return bbox[2] - bbox[0], bbox[3] - bbox[1], bbox

# Measure both lines
mdo_w, mdo_h, mdo_bbox = measure("MDO", font)
agro_w, agro_h, agro_bbox = measure("AGRO", font)

# Position both lines centered, very tight spacing (lines almost touching)
# Use vertical metrics to align cap-tops and bottoms cleanly
ascent, descent = font.getmetrics()
cap_h = ascent  # approximate

# Place MDO (top)
y_mdo = 60 * SCALE - mdo_bbox[1]
x_mdo = (CW - mdo_w) // 2 - mdo_bbox[0]

# Place AGRO immediately below MDO (tight)
# Use the bottom of MDO's bbox as start for AGRO's top
mdo_bottom = y_mdo + mdo_bbox[3]
y_agro = mdo_bottom - 30 * SCALE - agro_bbox[1]
x_agro = (CW - agro_w) // 2 - agro_bbox[0]

# === Build per-line masks ===
mdo_mask = Image.new("L", (CW, CH), 0)
ImageDraw.Draw(mdo_mask).text((x_mdo, y_mdo), "MDO", font=font, fill=255)

agro_mask = Image.new("L", (CW, CH), 0)
ImageDraw.Draw(agro_mask).text((x_agro, y_agro), "AGRO", font=font, fill=255)

# === Chrome gradient — sharp horizontal mirror band ===
def chrome_gradient(width, height):
    """Match original: bright top, sharp dark band ~50%, bright bottom."""
    grad = Image.new("RGB", (width, height))
    px = grad.load()
    stops = [
        (0.00, (255, 255, 255)),  # pure white at top
        (0.06, (250, 252, 254)),
        (0.20, (215, 220, 228)),
        (0.36, (160, 168, 180)),
        (0.46, (90, 100, 115)),   # start of dark band
        (0.50, (60, 72, 88)),     # darkest point (mirror line)
        (0.54, (95, 108, 122)),
        (0.64, (180, 190, 202)),
        (0.80, (240, 244, 250)),
        (0.94, (255, 255, 255)),  # bright bottom
        (1.00, (220, 226, 234)),
    ]
    for yy in range(height):
        t = yy / max(1, height - 1)
        c = stops[0][1]
        for i in range(len(stops) - 1):
            t0, ca = stops[i]
            t1, cb = stops[i + 1]
            if t0 <= t <= t1:
                u = (t - t0) / (t1 - t0) if t1 > t0 else 0
                r = int(ca[0] + (cb[0] - ca[0]) * u)
                g = int(ca[1] + (cb[1] - ca[1]) * u)
                b = int(ca[2] + (cb[2] - ca[2]) * u)
                c = (r, g, b)
                break
        for xx in range(width):
            px[xx, yy] = c
    return grad

# Apply gradient per line (each line gets its own chrome reflection)
def apply_chrome_to_line(line_mask, line_y_top, line_height):
    grad = chrome_gradient(CW, line_height)
    full = Image.new("RGB", (CW, CH), (255, 255, 255))
    full.paste(grad, (0, line_y_top))
    rgba = full.convert("RGBA")
    return Image.composite(rgba, Image.new("RGBA", (CW, CH), (0, 0, 0, 0)), line_mask)

mdo_chrome = apply_chrome_to_line(mdo_mask, y_mdo + mdo_bbox[1], mdo_h)
agro_chrome = apply_chrome_to_line(agro_mask, y_agro + agro_bbox[1], agro_h)

# === Black outline (stroke) ===
stroke_w = 5 * SCALE
stroke = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
sdraw = ImageDraw.Draw(stroke)
sdraw.text((x_mdo, y_mdo), "MDO", font=font, fill=(0, 0, 0, 255),
           stroke_width=stroke_w, stroke_fill=(0, 0, 0, 255))
sdraw.text((x_agro, y_agro), "AGRO", font=font, fill=(0, 0, 0, 255),
           stroke_width=stroke_w, stroke_fill=(0, 0, 0, 255))

# === Composite stroke + chrome ===
out = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
out = Image.alpha_composite(out, stroke)
out = Image.alpha_composite(out, mdo_chrome)
out = Image.alpha_composite(out, agro_chrome)

# === Landscape disc inside the "O" of MDO ===
md_w, _, md_bbox = measure("MD", font)
o_only_w, _, o_bbox = measure("O", font)
o_left = x_mdo + md_bbox[0] + md_w
o_center_x = o_left + o_only_w // 2 + 8 * SCALE
o_top = y_mdo + mdo_bbox[1]
o_center_y = o_top + (mdo_h // 2) + 4 * SCALE

# Load pre-built correct disc (silver ring, sun rays, hills, leaf)
disc_src = Image.open(r"D:\PIXADVISOR_AGENT_WORKSPACE\disc_correct.png").convert("RGBA")
# Resize disc to fit inside the O of MDO
target_disc_size = int(o_only_w * 0.78)
disc = disc_src.resize((target_disc_size, target_disc_size), Image.LANCZOS)

# Paste centered on the O
disc_x = o_center_x - target_disc_size // 2
disc_y = o_center_y - target_disc_size // 2
out.paste(disc, (disc_x, disc_y), disc)

# === Drop shadow under whole logo ===
combined_mask = ImageChops.lighter(mdo_mask, agro_mask)
shadow_mask = combined_mask.filter(ImageFilter.GaussianBlur(7 * SCALE))
shadow_alpha = shadow_mask.point(lambda v: int(v * 0.5))
shadow = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
shadow.putalpha(shadow_alpha)
shadow_offset = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
shadow_offset.paste(shadow, (4 * SCALE, 12 * SCALE))
out_with_shadow = Image.alpha_composite(shadow_offset, out)

# === Trim and downscale ===
bbox_trim = out_with_shadow.getbbox()
trimmed = out_with_shadow.crop(bbox_trim)
pad = 30
final_w = trimmed.width + pad * 2
final_h = trimmed.height + pad * 2
final = Image.new("RGBA", (final_w, final_h), (0, 0, 0, 0))
final.paste(trimmed, (pad, pad), trimmed)

target_w = 1500
ratio = target_w / final.width
target_h = int(final.height * ratio)
final_hd = final.resize((target_w, target_h), Image.LANCZOS)
final_hd.save(OUT, optimize=True)
print(f"Saved: {OUT} -> {final_hd.size}")
