"""Build HD MDO AGRO logo — stacked layout (MDO on top, AGRO below) matching original."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import os

OUT = r"D:\PIXADVISOR_AGENT_WORKSPACE\mdo_logo_hd.png"

# Oversample for crisp result
SCALE = 3

# Final target dimensions (will be the layout canvas)
W, H = 1600, 1100
CW, CH = W * SCALE, H * SCALE

# Find a heavy bold/black font (stamp-like impact)
font_paths = [
    r"C:\Windows\Fonts\impact.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\Arial Black.ttf",
    r"C:\Windows\Fonts\ariblk.ttf",
    r"C:\Windows\Fonts\verdanab.ttf",
]
font_path = next((p for p in font_paths if os.path.exists(p)), None)
if not font_path:
    raise RuntimeError("No bold font found")
print(f"Using: {font_path}")

# Try to find Arial Black specifically (best match for the heavy look)
black_font = r"C:\Windows\Fonts\ariblk.ttf"
if os.path.exists(black_font):
    font_path = black_font

FONT_SIZE_TOP = 300 * SCALE   # MDO
FONT_SIZE_BOT = 300 * SCALE   # AGRO

font_top = ImageFont.truetype(font_path, FONT_SIZE_TOP)
font_bot = ImageFont.truetype(font_path, FONT_SIZE_BOT)

# Build a transparent canvas
img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

def measure(text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1], bbox

# Center horizontally, place MDO on top, AGRO below
mdo_w, mdo_h, mdo_bbox = measure("MDO", font_top)
agro_w, agro_h, agro_bbox = measure("AGRO", font_bot)

# Position
margin_y = 40 * SCALE
x_mdo = (CW - mdo_w) // 2 - mdo_bbox[0]
x_agro = (CW - agro_w) // 2 - agro_bbox[0]

# Vertical stack with tight spacing (lines almost touching, like original)
y_mdo = margin_y - mdo_bbox[1]
y_agro = y_mdo + mdo_bbox[1] + mdo_h - 60 * SCALE - agro_bbox[1]  # overlap a bit

# === Step 1: build text mask (combined for both lines) ===
mask = Image.new("L", (CW, CH), 0)
mdraw = ImageDraw.Draw(mask)
mdraw.text((x_mdo, y_mdo), "MDO", font=font_top, fill=255)
mdraw.text((x_agro, y_agro), "AGRO", font=font_bot, fill=255)

# Get bbox of all text
mask_bbox = mask.getbbox()
print(f"Text mask bbox: {mask_bbox}")

# === Step 2: build chrome/silver gradient ===
def chrome_gradient(width, height):
    """Vertical chrome — bright top/bottom, dark middle band, mirror polish."""
    grad = Image.new("RGB", (width, height))
    px = grad.load()
    # Stops matching the original logo's metallic look
    stops = [
        (0.00, (245, 248, 252)),  # bright white top
        (0.10, (220, 225, 232)),
        (0.28, (160, 168, 178)),
        (0.42, (95, 105, 118)),   # dark band (mirror line)
        (0.50, (75, 85, 100)),
        (0.58, (105, 115, 128)),
        (0.72, (180, 188, 198)),
        (0.88, (235, 240, 246)),
        (1.00, (210, 218, 228)),
    ]
    for yy in range(height):
        t = yy / max(1, height - 1)
        c0 = c1 = stops[0][1]
        for i in range(len(stops) - 1):
            t0, ca = stops[i]
            t1, cb = stops[i + 1]
            if t0 <= t <= t1:
                u = (t - t0) / (t1 - t0) if t1 > t0 else 0
                r = int(ca[0] + (cb[0] - ca[0]) * u)
                g = int(ca[1] + (cb[1] - ca[1]) * u)
                b = int(ca[2] + (cb[2] - ca[2]) * u)
                c0 = (r, g, b)
                break
        else:
            c0 = stops[-1][1]
        for xx in range(width):
            px[xx, yy] = c0
    return grad

# Build a gradient per line (so each line has its own chrome reflection)
def render_line_with_chrome(text, font, x, y, mask_canvas_w, mask_canvas_h, line_x_start, line_y_start, line_w, line_h):
    """Render one line with chrome gradient using its own bbox."""
    # Per-line mask
    lmask = Image.new("L", (mask_canvas_w, mask_canvas_h), 0)
    ldraw = ImageDraw.Draw(lmask)
    ldraw.text((x, y), text, font=font, fill=255)
    # Generate chrome of line height
    grad = chrome_gradient(mask_canvas_w, line_h)
    # Place gradient at line position
    line_canvas = Image.new("RGB", (mask_canvas_w, mask_canvas_h), (255, 255, 255))
    line_canvas.paste(grad, (0, line_y_start))
    line_canvas_rgba = line_canvas.convert("RGBA")
    # Mask
    return Image.composite(line_canvas_rgba, Image.new("RGBA", (mask_canvas_w, mask_canvas_h), (0, 0, 0, 0)), lmask)

# === Step 3: render each line with chrome gradient ===
# MDO line
mdo_line = render_line_with_chrome("MDO", font_top, x_mdo, y_mdo, CW, CH,
                                    0, y_mdo + mdo_bbox[1], mdo_w, mdo_h)
# AGRO line
agro_line = render_line_with_chrome("AGRO", font_bot, x_agro, y_agro, CW, CH,
                                     0, y_agro + agro_bbox[1], agro_w, agro_h)

# === Step 4: dark outer stroke for both lines ===
stroke_canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
sdraw = ImageDraw.Draw(stroke_canvas)
stroke_w = 6 * SCALE
sdraw.text((x_mdo, y_mdo), "MDO", font=font_top, fill=(8, 12, 16, 255),
           stroke_width=stroke_w, stroke_fill=(8, 12, 16, 255))
sdraw.text((x_agro, y_agro), "AGRO", font=font_bot, fill=(8, 12, 16, 255),
           stroke_width=stroke_w, stroke_fill=(8, 12, 16, 255))

# === Step 5: composite stroke + chrome lines ===
out = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
out = Image.alpha_composite(out, stroke_canvas)
out = Image.alpha_composite(out, mdo_line)
out = Image.alpha_composite(out, agro_line)

# === Step 6: bright horizontal highlight band across middle of each letter ===
# Create a thin bright band that runs through the middle of the text
def add_highlight_band(canvas, line_y, line_h, line_mask):
    band = Image.new("L", (CW, CH), 0)
    bdraw = ImageDraw.Draw(band)
    # Bright band at ~40% height of line
    band_y = line_y + int(line_h * 0.32)
    band_h = int(line_h * 0.10)
    for yy in range(band_y, band_y + band_h):
        # gaussian falloff
        d = abs(yy - (band_y + band_h / 2)) / (band_h / 2)
        alpha = int(220 * (1 - d * d))
        if alpha < 0:
            alpha = 0
        bdraw.line([(0, yy), (CW, yy)], fill=alpha)
    band = band.filter(ImageFilter.GaussianBlur(2 * SCALE))
    # Only keep band inside text mask
    band_inside = ImageChops.multiply(band, line_mask)
    bright = Image.new("RGBA", (CW, CH), (255, 255, 255, 0))
    bright.putalpha(band_inside)
    # Make it white
    white_layer = Image.new("RGBA", (CW, CH), (255, 255, 255, 255))
    bright = Image.composite(white_layer, Image.new("RGBA", (CW, CH), (0, 0, 0, 0)), band_inside)
    return Image.alpha_composite(canvas, bright)

# Build per-line masks
mdo_mask = Image.new("L", (CW, CH), 0)
ImageDraw.Draw(mdo_mask).text((x_mdo, y_mdo), "MDO", font=font_top, fill=255)
agro_mask = Image.new("L", (CW, CH), 0)
ImageDraw.Draw(agro_mask).text((x_agro, y_agro), "AGRO", font=font_bot, fill=255)

out = add_highlight_band(out, y_mdo + mdo_bbox[1], mdo_h, mdo_mask)
out = add_highlight_band(out, y_agro + agro_bbox[1], agro_h, agro_mask)

# === Step 7: add landscape circle replacing the "O" of MDO ===
# Compute O position
mdtext = "MD"
md_w_only, _, md_only_bbox = measure(mdtext, font_top)
o_w_only, _, o_only_bbox = measure("O", font_top)
o_left = x_mdo + md_only_bbox[0] + md_w_only
o_center_x = o_left + o_w_only // 2 + 5 * SCALE
# Vertical center of the O glyph
ascent, descent = font_top.getmetrics()
o_top = y_mdo + mdo_bbox[1]
o_center_y = o_top + (mdo_h // 2) + 5 * SCALE

radius = int(o_w_only * 0.34)

# Build landscape disc
disc = Image.new("RGBA", (radius * 2, radius * 2), (0, 0, 0, 0))
ddraw = ImageDraw.Draw(disc)

# Sky (top half) — blue/teal gradient
sky_h = int(radius * 1.05)
for yy in range(sky_h):
    t = yy / max(1, sky_h - 1)
    r = int(105 + (215 - 105) * t)
    g = int(195 + (240 - 195) * t)
    b = int(225 + (240 - 225) * t)
    ddraw.line([(0, yy), (radius * 2, yy)], fill=(r, g, b))

# Field (bottom half) — green gradient
for yy in range(sky_h, radius * 2):
    t = (yy - sky_h) / max(1, radius * 2 - sky_h)
    r = int(80 + (40 - 80) * t)
    g = int(170 + (105 - 170) * t)
    b = int(60 + (35 - 60) * t)
    ddraw.line([(0, yy), (radius * 2, yy)], fill=(r, g, b))

# Sun
sun_r = int(radius * 0.36)
sun_cx = int(radius * 1.08)
sun_cy = int(sky_h * 0.62)
# Sun glow halo
for k in range(10, 0, -1):
    rr = sun_r + k * 5
    alpha = int(110 * (1 - k / 10) * 0.35)
    ddraw.ellipse(
        [sun_cx - rr, sun_cy - rr, sun_cx + rr, sun_cy + rr],
        fill=(255, 220, 100, alpha),
    )
# Sun body (orange-yellow gradient)
sun_layer = Image.new("RGBA", (radius * 2, radius * 2), (0, 0, 0, 0))
sdraw2 = ImageDraw.Draw(sun_layer)
sdraw2.ellipse(
    [sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r],
    fill=(255, 175, 50),
)
# Lighter highlight on top
sdraw2.ellipse(
    [sun_cx - sun_r + 5, sun_cy - sun_r + 5, sun_cx + sun_r // 3, sun_cy - sun_r // 5],
    fill=(255, 230, 130),
)
disc = Image.alpha_composite(disc, sun_layer)

# Mask to circle
circle_mask = Image.new("L", (radius * 2, radius * 2), 0)
ImageDraw.Draw(circle_mask).ellipse([0, 0, radius * 2, radius * 2], fill=255)
disc.putalpha(circle_mask)

# Inner dark rim
rim = Image.new("RGBA", (radius * 2, radius * 2), (0, 0, 0, 0))
ImageDraw.Draw(rim).ellipse([2, 2, radius * 2 - 3, radius * 2 - 3], outline=(20, 30, 40, 230), width=4)
disc = Image.alpha_composite(disc, rim)

# Paste landscape over the O area
out.paste(disc, (o_center_x - radius, o_center_y - radius), disc)

# === Step 8: subtle drop shadow under whole logo ===
combined_mask = ImageChops.lighter(mdo_mask, agro_mask)
shadow_mask = combined_mask.filter(ImageFilter.GaussianBlur(8 * SCALE))
shadow = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
shadow_alpha = shadow_mask.point(lambda v: int(v * 0.4))
shadow.putalpha(shadow_alpha)
shadow_offset = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
shadow_offset.paste(shadow, (5 * SCALE, 10 * SCALE))
out_with_shadow = Image.alpha_composite(shadow_offset, out)

# === Step 9: trim transparent padding, then downscale to crisp HD ===
bbox_trim = out_with_shadow.getbbox()
trimmed = out_with_shadow.crop(bbox_trim)
pad = 30
final_w = trimmed.width + pad * 2
final_h = trimmed.height + pad * 2
final = Image.new("RGBA", (final_w, final_h), (0, 0, 0, 0))
final.paste(trimmed, (pad, pad), trimmed)

# Downscale to HD (target 1400 width)
target_w = 1400
ratio = target_w / final.width
target_h = int(final.height * ratio)
final_hd = final.resize((target_w, target_h), Image.LANCZOS)
final_hd.save(OUT, optimize=True)
print(f"Saved: {OUT} -> {final_hd.size}")
