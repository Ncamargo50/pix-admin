"""Build the correct landscape disc: silver ring, sun with rays, green hills + leaf."""
from PIL import Image, ImageDraw, ImageFilter
import math

OUT = r"D:\PIXADVISOR_AGENT_WORKSPACE\disc_correct.png"

SCALE = 4
R = 250  # base radius
SR = R * SCALE
W = SR * 2 + 40 * SCALE
H = SR * 2 + 40 * SCALE
CX, CY = W // 2, H // 2

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# === 1) Silver metallic outer ring ===
# Outer disk silver gradient
ring_outer = SR
ring_inner = int(SR * 0.85)

# Build gradient ring using radial bands
for r_off in range(ring_outer, ring_inner, -1):
    t = (r_off - ring_inner) / (ring_outer - ring_inner)
    # silver gradient: bright at edge, darker mid, light again
    if t > 0.7:
        # bright outer edge
        c = int(220 + 30 * (t - 0.7) / 0.3)
    elif t > 0.3:
        c = int(140 + 60 * (t - 0.3) / 0.4)
    else:
        c = int(100 + 40 * t / 0.3)
    draw.ellipse([CX - r_off, CY - r_off, CX + r_off, CY + r_off],
                 fill=(c, c, c + 5))

# Dark inner ring border
draw.ellipse([CX - ring_inner, CY - ring_inner, CX + ring_inner, CY + ring_inner],
             outline=(60, 65, 75), width=4 * SCALE)

# === 2) Cream/yellow inner disc background ===
inner_r = ring_inner - 2 * SCALE
# Gradient: lighter top, slightly warmer bottom
for yy in range(CY - inner_r, CY + inner_r):
    t = (yy - (CY - inner_r)) / (2 * inner_r)
    # light cream from top, slightly more yellow toward bottom
    r = int(255 - 5 * t)
    g = int(245 - 8 * t)
    b = int(210 - 15 * t)
    # constrain horizontally to circle
    dy = yy - CY
    dx = int(math.sqrt(max(0, inner_r * inner_r - dy * dy)))
    draw.line([(CX - dx, yy), (CX + dx, yy)], fill=(r, g, b))

# === 3) Sun with rays (center-upper) ===
sun_cx = CX
sun_cy = CY - int(inner_r * 0.18)
sun_body_r = int(inner_r * 0.30)
ray_inner_r = sun_body_r + int(inner_r * 0.04)
ray_outer_r = int(inner_r * 0.62)
ray_color = (245, 200, 30)
sun_color = (250, 210, 40)

# Draw 12 triangular rays
import math as _m
NUM_RAYS = 12
for i in range(NUM_RAYS):
    angle = (i / NUM_RAYS) * 2 * _m.pi - _m.pi / 2
    # ray width as angular spread
    half = _m.radians(360 / NUM_RAYS / 2 * 0.55)
    a1 = angle - half
    a2 = angle + half
    # tip
    tip = (sun_cx + ray_outer_r * _m.cos(angle),
           sun_cy + ray_outer_r * _m.sin(angle))
    # base (two points on inner ring)
    b1 = (sun_cx + ray_inner_r * _m.cos(a1),
          sun_cy + ray_inner_r * _m.sin(a1))
    b2 = (sun_cx + ray_inner_r * _m.cos(a2),
          sun_cy + ray_inner_r * _m.sin(a2))
    draw.polygon([tip, b1, b2], fill=ray_color)

# Sun body
draw.ellipse([sun_cx - sun_body_r, sun_cy - sun_body_r,
              sun_cx + sun_body_r, sun_cy + sun_body_r],
             fill=sun_color, outline=(220, 175, 20), width=2 * SCALE)

# Inner sun highlight
ddraw = ImageDraw.Draw(img)
inner_highlight_r = int(sun_body_r * 0.55)
ddraw.ellipse([sun_cx - inner_highlight_r + sun_body_r // 5,
               sun_cy - inner_highlight_r - sun_body_r // 5,
               sun_cx + inner_highlight_r + sun_body_r // 5,
               sun_cy + inner_highlight_r - sun_body_r // 5],
              fill=(255, 235, 130))

# === 4) Two green hills at bottom ===
hill_color_dark = (40, 110, 55)
hill_color_light = (75, 155, 70)

# Build hill shapes — overlapping mounds
# Bottom hill (darker, behind)
hill1_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
h1draw = ImageDraw.Draw(hill1_layer)
# Left hill: ellipse
h1_w = int(inner_r * 1.2)
h1_h = int(inner_r * 0.5)
h1_cx = CX - int(inner_r * 0.25)
h1_cy = CY + int(inner_r * 0.45)
h1draw.ellipse([h1_cx - h1_w // 2, h1_cy - h1_h // 2,
                h1_cx + h1_w // 2, h1_cy + h1_h // 2],
               fill=hill_color_dark)

# Right hill (lighter, in front)
hill2_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
h2draw = ImageDraw.Draw(hill2_layer)
h2_w = int(inner_r * 1.0)
h2_h = int(inner_r * 0.45)
h2_cx = CX + int(inner_r * 0.30)
h2_cy = CY + int(inner_r * 0.55)
h2draw.ellipse([h2_cx - h2_w // 2, h2_cy - h2_h // 2,
                h2_cx + h2_w // 2, h2_cy + h2_h // 2],
               fill=hill_color_light)

# === 5) Green leaf at bottom-center ===
leaf_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ldraw = ImageDraw.Draw(leaf_layer)

# Leaf shape: pointed oval
leaf_color = (60, 145, 60)
leaf_dark = (35, 95, 40)

# Define leaf as polygon (curved leaf shape)
leaf_cx = CX - int(inner_r * 0.10)
leaf_cy = CY + int(inner_r * 0.35)
leaf_w = int(inner_r * 0.95)
leaf_h = int(inner_r * 0.40)

# Leaf as two curves meeting at points
leaf_points_top = []
leaf_points_bot = []
N = 30
for i in range(N + 1):
    t = i / N
    x = leaf_cx - leaf_w // 2 + int(leaf_w * t)
    # top curve (gentle arc)
    y_top = leaf_cy - int(leaf_h * 0.5 * _m.sin(_m.pi * t) * 0.85)
    # bottom curve (deeper arc)
    y_bot = leaf_cy + int(leaf_h * 0.5 * _m.sin(_m.pi * t))
    leaf_points_top.append((x, y_top))
    leaf_points_bot.append((x, y_bot))

leaf_poly = leaf_points_top + leaf_points_bot[::-1]
ldraw.polygon(leaf_poly, fill=leaf_color, outline=leaf_dark)

# Leaf central vein
vein_start = (leaf_cx - leaf_w // 2, leaf_cy)
vein_end = (leaf_cx + leaf_w // 2, leaf_cy)
ldraw.line([vein_start, vein_end], fill=leaf_dark, width=3 * SCALE)

# Side veins
for k in range(1, 5):
    t = k / 5
    x = leaf_cx - leaf_w // 2 + int(leaf_w * t)
    y_top = leaf_cy - int(leaf_h * 0.4 * _m.sin(_m.pi * t) * 0.7)
    y_bot = leaf_cy + int(leaf_h * 0.4 * _m.sin(_m.pi * t) * 0.85)
    ldraw.line([(x, leaf_cy), (x - 8 * SCALE, y_top)], fill=leaf_dark, width=2 * SCALE)
    ldraw.line([(x, leaf_cy), (x - 8 * SCALE, y_bot)], fill=leaf_dark, width=2 * SCALE)

# === Composite hills first (behind), then leaf on top ===
img = Image.alpha_composite(img, hill1_layer)
img = Image.alpha_composite(img, hill2_layer)
img = Image.alpha_composite(img, leaf_layer)

# === Mask everything to inner circle (clip outside) ===
clip_mask = Image.new("L", (W, H), 0)
cdraw = ImageDraw.Draw(clip_mask)
cdraw.ellipse([CX - inner_r, CY - inner_r, CX + inner_r, CY + inner_r], fill=255)

# Apply: take inner content, apply circle mask
# But preserve the silver ring outside
ring_mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(ring_mask).ellipse([CX - SR, CY - SR, CX + SR, CY + SR], fill=255)
ImageDraw.Draw(ring_mask).ellipse([CX - inner_r, CY - inner_r, CX + inner_r, CY + inner_r], fill=0)

# Combine: ring + inner content (already drawn above is fine — they're separate areas)
# But we need to clip the hills/leaf inside circle
# Solution: mask the entire alpha by full disk
disk_mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(disk_mask).ellipse([CX - SR, CY - SR, CX + SR, CY + SR], fill=255)

# apply disk mask
r, g, b, a = img.split()
new_a = Image.new("L", (W, H), 0)
a_data = a.load()
m_data = disk_mask.load()
nd = new_a.load()
for yy in range(H):
    for xx in range(W):
        nd[xx, yy] = min(a_data[xx, yy], m_data[xx, yy])
img.putalpha(new_a)

# === Subtle dark outer rim ===
rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(rim).ellipse([CX - SR + 1, CY - SR + 1, CX + SR - 1, CY + SR - 1],
                              outline=(35, 40, 50, 230), width=4 * SCALE)
img = Image.alpha_composite(img, rim)

# Trim and downscale
bbox = img.getbbox()
trimmed = img.crop(bbox)
target = 400
ratio = target / trimmed.width
final = trimmed.resize((target, int(trimmed.height * ratio)), Image.LANCZOS)
final.save(OUT, optimize=True)
print(f"Saved: {OUT} -> {final.size}")
