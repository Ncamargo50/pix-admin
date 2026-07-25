"""Build HD MDO AGRO logo from scratch — metallic silver text + landscape in O."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

OUT = r"D:\PIXADVISOR_AGENT_WORKSPACE\mdo_logo_hd.png"

# HD canvas — 4x oversampled then downscaled for anti-aliasing
SCALE = 4
W = 1600 * SCALE // 2  # final 800w workable; oversample below
H = 320 * SCALE // 2

# Working canvas (oversample)
WW, HH = 1600 * 2, 320 * 2  # 3200 x 640 oversample

img = Image.new("RGBA", (WW, HH), (255, 255, 255, 0))

# Find a bold font
font_candidates = [
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\Arial Bold.ttf",
    r"C:\Windows\Fonts\impact.ttf",
    r"C:\Windows\Fonts\verdanab.ttf",
]
font_path = next((p for p in font_candidates if os.path.exists(p)), None)
if not font_path:
    raise RuntimeError("No bold font found")

# Big font size for HD
FONT_SIZE = 460
font = ImageFont.truetype(font_path, FONT_SIZE)

text = "MDO AGRO"

# Measure
draw = ImageDraw.Draw(img)
bbox = draw.textbbox((0, 0), text, font=font, stroke_width=12)
text_w = bbox[2] - bbox[0]
text_h = bbox[3] - bbox[1]
x = (WW - text_w) // 2 - bbox[0]
y = (HH - text_h) // 2 - bbox[1]

# Step 1: build a gradient mask for the text (vertical metallic silver gradient)
# Create solid white text on a separate image to use as mask
text_mask = Image.new("L", (WW, HH), 0)
mdraw = ImageDraw.Draw(text_mask)
mdraw.text((x, y), text, font=font, fill=255)

# Step 2: build metallic silver gradient
def metallic_gradient(width, height):
    """Vertical metallic silver gradient: light-dark-light bands."""
    grad = Image.new("RGB", (width, height))
    px = grad.load()
    # Stops (position 0..1, RGB)
    stops = [
        (0.00, (220, 222, 226)),
        (0.18, (245, 246, 248)),
        (0.38, (140, 145, 152)),
        (0.55, (95, 100, 108)),
        (0.72, (175, 180, 188)),
        (0.88, (240, 242, 246)),
        (1.00, (130, 135, 142)),
    ]
    for yy in range(height):
        t = yy / max(1, height - 1)
        # find segment
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                u = (t - t0) / (t1 - t0) if t1 > t0 else 0
                r = int(c0[0] + (c1[0] - c0[0]) * u)
                g = int(c0[1] + (c1[1] - c0[1]) * u)
                b = int(c0[2] + (c1[2] - c0[2]) * u)
                break
        else:
            r, g, b = stops[-1][1]
        for xx in range(width):
            px[xx, yy] = (r, g, b)
    return grad

grad = metallic_gradient(WW, HH)
grad_rgba = grad.convert("RGBA")

# Step 3: dark outer stroke + bright inner highlight
# Draw black stroke first (slightly larger), then gradient text on top
out = Image.new("RGBA", (WW, HH), (255, 255, 255, 0))
odraw = ImageDraw.Draw(out)

# Outer dark stroke
odraw.text((x, y), text, font=font, fill=(15, 18, 22, 255), stroke_width=14, stroke_fill=(15, 18, 22, 255))

# Apply metallic gradient inside the text shape
filled_text = Image.composite(grad_rgba, Image.new("RGBA", (WW, HH), (0, 0, 0, 0)), text_mask)

# Erode the text mask slightly so gradient sits inside the stroke
eroded = text_mask.filter(ImageFilter.MinFilter(7))
inner = Image.composite(grad_rgba, Image.new("RGBA", (WW, HH), (0, 0, 0, 0)), eroded)
out = Image.alpha_composite(out, inner)

# Step 4: subtle inner shadow / top highlight on letters
highlight_mask = eroded.filter(ImageFilter.MinFilter(15))
highlight = Image.new("RGBA", (WW, HH), (0, 0, 0, 0))
hdraw = ImageDraw.Draw(highlight)
# top half of each letter brighter
band = Image.new("L", (WW, HH), 0)
bdraw = ImageDraw.Draw(band)
# top brightness band
for yy in range(HH // 2):
    alpha = int(80 * (1 - yy / (HH / 2)))
    bdraw.line([(0, yy), (WW, yy)], fill=alpha)
bright_band = Image.new("RGBA", (WW, HH), (255, 255, 255, 0))
bright_band.putalpha(band)
# only inside text
bright_inside = Image.new("RGBA", (WW, HH), (0, 0, 0, 0))
bright_inside.paste(bright_band, (0, 0), eroded)
out = Image.alpha_composite(out, bright_inside)

# Step 5: replace the "O" of MDO with landscape circle
# Find the position of the "O" in MDO. We measure substring widths.
def measure(s):
    b = draw.textbbox((0, 0), s, font=font, stroke_width=12)
    return b[2] - b[0]

# "MD" before the O of MDO
md_w = measure("MD")
o1_w = measure("MDO") - md_w
# Center of "O" in MDO
o1_left = x + md_w
o1_center_x = o1_left + o1_w // 2
# Y center: middle of cap height
ascent, descent = font.getmetrics()
o1_center_y = y + ascent // 2 + 20

# Circle radius (slightly smaller than O inner)
radius = int(o1_w * 0.32)

# Build landscape disc
disc = Image.new("RGBA", (radius * 2, radius * 2), (0, 0, 0, 0))
ddraw = ImageDraw.Draw(disc)

# Sky gradient (top): blue/teal -> light
sky_h = int(radius * 1.1)
for yy in range(sky_h):
    t = yy / max(1, sky_h - 1)
    r = int(120 + (220 - 120) * t)
    g = int(190 + (235 - 190) * t)
    b = int(220 + (235 - 220) * t)
    ddraw.line([(0, yy), (radius * 2, yy)], fill=(r, g, b))

# Green field (bottom)
for yy in range(sky_h, radius * 2):
    t = (yy - sky_h) / max(1, radius * 2 - sky_h)
    r = int(85 + (45 - 85) * t)
    g = int(165 + (110 - 165) * t)
    b = int(70 + (40 - 70) * t)
    ddraw.line([(0, yy), (radius * 2, yy)], fill=(r, g, b))

# Sun
sun_r = int(radius * 0.32)
sun_cx = int(radius * 0.95)
sun_cy = int(sky_h * 0.65)
# Sun glow
for k in range(8, 0, -1):
    rr = sun_r + k * 4
    alpha = int(120 * (1 - k / 8) * 0.3)
    ddraw.ellipse(
        [sun_cx - rr, sun_cy - rr, sun_cx + rr, sun_cy + rr],
        fill=(255, 220, 100, alpha),
    )
# Sun body
ddraw.ellipse(
    [sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r],
    fill=(255, 195, 60),
)
# Sun highlight
ddraw.ellipse(
    [sun_cx - sun_r + 4, sun_cy - sun_r + 4, sun_cx - sun_r // 3, sun_cy - sun_r // 3],
    fill=(255, 235, 150),
)

# Mask disc to circle
circle_mask = Image.new("L", (radius * 2, radius * 2), 0)
ImageDraw.Draw(circle_mask).ellipse([0, 0, radius * 2, radius * 2], fill=255)
disc.putalpha(circle_mask)

# Slight dark rim
rim = Image.new("RGBA", (radius * 2, radius * 2), (0, 0, 0, 0))
ImageDraw.Draw(rim).ellipse([0, 0, radius * 2 - 1, radius * 2 - 1], outline=(40, 50, 60, 220), width=4)
disc = Image.alpha_composite(disc, rim)

# Paste landscape onto the O
out.paste(disc, (o1_center_x - radius, o1_center_y - radius), disc)

# Step 6: drop shadow under whole logo (subtle)
shadow_mask = text_mask.filter(ImageFilter.GaussianBlur(8))
shadow = Image.new("RGBA", (WW, HH), (0, 0, 0, 0))
shadow.putalpha(shadow_mask.point(lambda v: int(v * 0.35)))
shadow_offset = Image.new("RGBA", (WW, HH), (0, 0, 0, 0))
shadow_offset.paste(shadow, (4, 8))
out_with_shadow = Image.alpha_composite(shadow_offset, out)

# Step 7: trim transparent edges, then downscale with LANCZOS for crisp final
bbox_trim = out_with_shadow.getbbox()
trimmed = out_with_shadow.crop(bbox_trim)
# Add a small padding
pad = 30
final_w = trimmed.width + pad * 2
final_h = trimmed.height + pad * 2
final = Image.new("RGBA", (final_w, final_h), (0, 0, 0, 0))
final.paste(trimmed, (pad, pad), trimmed)

# Downscale to crisp HD (e.g., target 1600 width)
target_w = 1600
ratio = target_w / final.width
target_h = int(final.height * ratio)
final_hd = final.resize((target_w, target_h), Image.LANCZOS)
final_hd.save(OUT, optimize=True)
print(f"Saved: {OUT} -> {final_hd.size}")
