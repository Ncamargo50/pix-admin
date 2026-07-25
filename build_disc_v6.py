"""Disc v6 — exact match: silver ring, silver bg, yellow gear, cyan hub, big leaf in front."""
from PIL import Image, ImageDraw, ImageFilter
import math

OUT = r"D:\PIXADVISOR_AGENT_WORKSPACE\disc_correct.png"

SCALE = 4
R = 250
SR = R * SCALE
W = SR * 2 + 40 * SCALE
H = SR * 2 + 40 * SCALE
CX, CY = W // 2, H // 2

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# === 1) Silver chrome outer ring ===
ring_outer = SR
ring_inner = int(SR * 0.86)
for r_off in range(ring_outer, ring_inner, -1):
    t = (r_off - ring_inner) / (ring_outer - ring_inner)
    if t > 0.7:
        c = int(220 + 30 * (t - 0.7) / 0.3)
    elif t > 0.3:
        c = int(140 + 60 * (t - 0.3) / 0.4)
    else:
        c = int(95 + 45 * t / 0.3)
    draw.ellipse([CX - r_off, CY - r_off, CX + r_off, CY + r_off],
                 fill=(c, c, c + 5))

# Inner dark rim
draw.ellipse([CX - ring_inner, CY - ring_inner, CX + ring_inner, CY + ring_inner],
             outline=(60, 65, 75), width=4 * SCALE)

# === 2) Inside background — light metallic silver gradient ===
inner_r = ring_inner - 3 * SCALE
for yy in range(CY - inner_r, CY + inner_r):
    t = (yy - (CY - inner_r)) / (2 * inner_r)
    # silver gradient — bright top, slightly darker mid, bright bottom
    if t < 0.5:
        v = int(245 - 35 * (t / 0.5))   # 245 -> 210
    else:
        v = int(210 + 25 * ((t - 0.5) / 0.5))  # 210 -> 235
    dy = yy - CY
    dx = int(math.sqrt(max(0, inner_r * inner_r - dy * dy)))
    draw.line([(CX - dx, yy), (CX + dx, yy)], fill=(v, v + 2, v + 5))

# === 3) Yellow/gold gear (full gear, bottom will be covered by leaf) ===
def draw_gear_solid(canvas, cx, cy, outer_r, inner_r, num_teeth, body_color, edge_color):
    g = ImageDraw.Draw(canvas)
    points = []
    half = math.pi / num_teeth * 0.42
    for i in range(num_teeth):
        angle = (i / num_teeth) * 2 * math.pi - math.pi / 2
        # ramp into tooth
        points.append((cx + inner_r * math.cos(angle - half - 0.06),
                       cy + inner_r * math.sin(angle - half - 0.06)))
        points.append((cx + outer_r * math.cos(angle - half),
                       cy + outer_r * math.sin(angle - half)))
        points.append((cx + outer_r * math.cos(angle + half),
                       cy + outer_r * math.sin(angle + half)))
        points.append((cx + inner_r * math.cos(angle + half + 0.06),
                       cy + inner_r * math.sin(angle + half + 0.06)))
    g.polygon(points, fill=body_color, outline=edge_color)

gear_cx = CX
gear_cy = CY - int(inner_r * 0.05)
gear_outer = int(inner_r * 0.62)
gear_inner = int(inner_r * 0.50)

gear_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw_gear_solid(
    gear_layer,
    gear_cx, gear_cy,
    gear_outer, gear_inner,
    num_teeth=10,
    body_color=(245, 200, 35, 255),       # yellow/gold
    edge_color=(190, 145, 15, 255),
)

img = Image.alpha_composite(img, gear_layer)

# === 4) Cyan/teal blue hub in center of yellow gear ===
hub_cx = gear_cx
hub_cy = gear_cy
hub_r = int(inner_r * 0.30)

# Outer cyan circle
ImageDraw.Draw(img).ellipse(
    [hub_cx - hub_r, hub_cy - hub_r, hub_cx + hub_r, hub_cy + hub_r],
    fill=(95, 175, 195, 255),       # cyan/teal
    outline=(60, 130, 150, 255), width=3 * SCALE,
)

# Horizontal striped detail on the hub (like cog hub markings)
# Two horizontal bands lighter
for yy_off in [-int(hub_r * 0.35), 0, int(hub_r * 0.35)]:
    ImageDraw.Draw(img).line(
        [(hub_cx - int(hub_r * 0.7), hub_cy + yy_off),
         (hub_cx + int(hub_r * 0.7), hub_cy + yy_off)],
        fill=(170, 220, 230, 255), width=3 * SCALE,
    )

# Small darker dot in absolute center
center_dot = int(hub_r * 0.18)
ImageDraw.Draw(img).ellipse(
    [hub_cx - center_dot, hub_cy - center_dot, hub_cx + center_dot, hub_cy + center_dot],
    fill=(40, 90, 110, 255),
)

# === 5) Large leaf in front (covers bottom half of gear) ===
leaf_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ldraw = ImageDraw.Draw(leaf_layer)

# Leaf shape: large curved leaf, tip pointing up-right
# Dark green main body
leaf_dark = (35, 100, 55, 255)
leaf_light = (85, 165, 145, 255)   # teal-green for highlight curve
gold_vein = (220, 175, 30, 255)

# Leaf footprint:
# Bottom-left base, sweeping curve up to right tip
leaf_left = CX - int(inner_r * 1.05)
leaf_right = CX + int(inner_r * 0.98)
leaf_bot = CY + int(inner_r * 0.85)
leaf_top = CY - int(inner_r * 0.10)
tip_x = CX + int(inner_r * 0.92)
tip_y = CY - int(inner_r * 0.05)
base_x = CX - int(inner_r * 0.95)
base_y = CY + int(inner_r * 0.50)

# Build leaf polygon: top curve + bottom curve from base to tip
def bezier_curve(p0, p1, p2, n=60):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        pts.append((int(x), int(y)))
    return pts

# Top edge: arching curve
top_curve = bezier_curve(
    (base_x, base_y),
    (CX - int(inner_r * 0.10), CY - int(inner_r * 0.45)),  # control point lifts arc up
    (tip_x, tip_y),
)
# Bottom edge: gentler curve
bot_curve = bezier_curve(
    (base_x, base_y),
    (CX, CY + int(inner_r * 0.95)),  # control point dips down
    (tip_x, tip_y),
)

leaf_poly = top_curve + bot_curve[::-1]
ldraw.polygon(leaf_poly, fill=leaf_dark, outline=(20, 60, 35, 255))

# Lighter teal highlight on the upper edge of the leaf
# Build a thinner curve along the top edge
highlight_top = bezier_curve(
    (base_x + int(inner_r * 0.10), base_y - int(inner_r * 0.05)),
    (CX - int(inner_r * 0.10), CY - int(inner_r * 0.50)),
    (tip_x, tip_y),
)
highlight_inner = bezier_curve(
    (base_x + int(inner_r * 0.20), base_y - int(inner_r * 0.10)),
    (CX - int(inner_r * 0.05), CY - int(inner_r * 0.30)),
    (tip_x - int(inner_r * 0.05), tip_y + int(inner_r * 0.05)),
)
hi_poly = highlight_top + highlight_inner[::-1]
ldraw.polygon(hi_poly, fill=leaf_light)

# Gold vein running along the leaf
vein_curve = bezier_curve(
    (base_x + int(inner_r * 0.15), base_y - int(inner_r * 0.02)),
    (CX - int(inner_r * 0.05), CY - int(inner_r * 0.20)),
    (tip_x - int(inner_r * 0.02), tip_y + int(inner_r * 0.02)),
)
# Draw vein with thicker line
for k in range(len(vein_curve) - 1):
    ldraw.line([vein_curve[k], vein_curve[k + 1]], fill=gold_vein, width=4 * SCALE)

img = Image.alpha_composite(img, leaf_layer)

# === Clip everything to disc circle ===
disk_mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(disk_mask).ellipse([CX - SR, CY - SR, CX + SR, CY + SR], fill=255)

r, g, b, a = img.split()
new_a = Image.new("L", (W, H), 0)
a_data = a.load()
m_data = disk_mask.load()
nd = new_a.load()
for yy in range(H):
    for xx in range(W):
        nd[xx, yy] = min(a_data[xx, yy], m_data[xx, yy])
img.putalpha(new_a)

# Outer dark rim line
rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(rim).ellipse(
    [CX - SR + 1, CY - SR + 1, CX + SR - 1, CY + SR - 1],
    outline=(35, 40, 50, 230), width=4 * SCALE,
)
img = Image.alpha_composite(img, rim)

# Trim and downscale
bbox = img.getbbox()
trimmed = img.crop(bbox)
target = 500
ratio = target / trimmed.width
final = trimmed.resize((target, int(trimmed.height * ratio)), Image.LANCZOS)
final.save(OUT, optimize=True)
print(f"Saved: {OUT} -> {final.size}")
