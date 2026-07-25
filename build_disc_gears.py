"""Disc design: silver ring + cream bg + orange gear (with blue gear inside) + green leaf."""
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

# === 1) Silver metallic outer ring ===
ring_outer = SR
ring_inner = int(SR * 0.86)

for r_off in range(ring_outer, ring_inner, -1):
    t = (r_off - ring_inner) / (ring_outer - ring_inner)
    if t > 0.7:
        c = int(220 + 30 * (t - 0.7) / 0.3)
    elif t > 0.3:
        c = int(140 + 60 * (t - 0.3) / 0.4)
    else:
        c = int(100 + 40 * t / 0.3)
    draw.ellipse([CX - r_off, CY - r_off, CX + r_off, CY + r_off],
                 fill=(c, c, c + 5))

# Inner dark rim
draw.ellipse([CX - ring_inner, CY - ring_inner, CX + ring_inner, CY + ring_inner],
             outline=(60, 65, 75), width=4 * SCALE)

# === 2) Cream/pale yellow background ===
inner_r = ring_inner - 3 * SCALE
for yy in range(CY - inner_r, CY + inner_r):
    t = (yy - (CY - inner_r)) / (2 * inner_r)
    r = int(255 - 5 * t)
    g = int(248 - 8 * t)
    b = int(215 - 15 * t)
    dy = yy - CY
    dx = int(math.sqrt(max(0, inner_r * inner_r - dy * dy)))
    draw.line([(CX - dx, yy), (CX + dx, yy)], fill=(r, g, b))


def draw_gear(canvas, cx, cy, outer_r, inner_r, hole_r, num_teeth, body_color, edge_color):
    """Draw a gear: spoked teeth + inner body + center hole."""
    g = ImageDraw.Draw(canvas)

    # Build gear silhouette as polygon
    # alternating outer (tip) and inner (between teeth) points
    points = []
    tooth_half = math.pi / num_teeth * 0.45  # half-angle of a tooth
    for i in range(num_teeth):
        angle = (i / num_teeth) * 2 * math.pi - math.pi / 2
        # leading flank (rises to tip)
        points.append((cx + inner_r * math.cos(angle - tooth_half - 0.05),
                       cy + inner_r * math.sin(angle - tooth_half - 0.05)))
        points.append((cx + outer_r * math.cos(angle - tooth_half),
                       cy + outer_r * math.sin(angle - tooth_half)))
        # tooth flat top
        points.append((cx + outer_r * math.cos(angle + tooth_half),
                       cy + outer_r * math.sin(angle + tooth_half)))
        # trailing flank
        points.append((cx + inner_r * math.cos(angle + tooth_half + 0.05),
                       cy + inner_r * math.sin(angle + tooth_half + 0.05)))

    g.polygon(points, fill=body_color, outline=edge_color)

    # Center hub circle
    g.ellipse([cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r],
              fill=None, outline=edge_color, width=3 * SCALE)


# === 3) Orange gear (large, upper-center) ===
orange_cx = CX
orange_cy = CY - int(inner_r * 0.18)
orange_outer = int(inner_r * 0.55)
orange_inner = int(inner_r * 0.42)
orange_hole = int(inner_r * 0.18)

orange_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw_gear(
    orange_layer,
    orange_cx, orange_cy,
    orange_outer, orange_inner, orange_hole,
    num_teeth=12,
    body_color=(245, 130, 35, 255),       # vibrant orange
    edge_color=(180, 80, 15, 255),
)

img = Image.alpha_composite(img, orange_layer)

# === 4) Blue gear (smaller, inside the orange one) ===
blue_cx = orange_cx
blue_cy = orange_cy
blue_outer = int(inner_r * 0.20)
blue_inner = int(inner_r * 0.14)
blue_hole = int(inner_r * 0.04)

blue_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw_gear(
    blue_layer,
    blue_cx, blue_cy,
    blue_outer, blue_inner, blue_hole,
    num_teeth=10,
    body_color=(40, 120, 200, 255),       # bright blue
    edge_color=(20, 70, 150, 255),
)

img = Image.alpha_composite(img, blue_layer)

# Add a tiny center dot in blue gear
ImageDraw.Draw(img).ellipse(
    [blue_cx - blue_hole, blue_cy - blue_hole, blue_cx + blue_hole, blue_cy + blue_hole],
    fill=(20, 70, 150, 255),
)

# === 5) Green leaf at the bottom ===
leaf_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ldraw = ImageDraw.Draw(leaf_layer)

leaf_color_main = (60, 145, 60)
leaf_color_dark = (35, 95, 40)

leaf_cx = CX
leaf_cy = CY + int(inner_r * 0.45)
leaf_w = int(inner_r * 1.20)
leaf_h = int(inner_r * 0.50)

# Build leaf as two arcs meeting at left tip and right tip
leaf_points_top = []
leaf_points_bot = []
N = 50
for i in range(N + 1):
    t = i / N
    x = leaf_cx - leaf_w // 2 + int(leaf_w * t)
    y_top = leaf_cy - int(leaf_h * 0.5 * math.sin(math.pi * t) * 0.95)
    y_bot = leaf_cy + int(leaf_h * 0.5 * math.sin(math.pi * t))
    leaf_points_top.append((x, y_top))
    leaf_points_bot.append((x, y_bot))

leaf_poly = leaf_points_top + leaf_points_bot[::-1]
ldraw.polygon(leaf_poly, fill=leaf_color_main, outline=leaf_color_dark)

# Central vein
ldraw.line(
    [(leaf_cx - leaf_w // 2, leaf_cy), (leaf_cx + leaf_w // 2, leaf_cy)],
    fill=leaf_color_dark, width=3 * SCALE,
)

# Side veins
for k in range(1, 6):
    t = k / 6
    x = leaf_cx - leaf_w // 2 + int(leaf_w * t)
    y_top = leaf_cy - int(leaf_h * 0.4 * math.sin(math.pi * t) * 0.7)
    y_bot = leaf_cy + int(leaf_h * 0.4 * math.sin(math.pi * t) * 0.85)
    # angle veins outward from center
    sgn = -1 if t < 0.5 else 1
    ldraw.line([(x, leaf_cy), (x + sgn * 5 * SCALE, y_top)], fill=leaf_color_dark, width=2 * SCALE)
    ldraw.line([(x, leaf_cy), (x + sgn * 5 * SCALE, y_bot)], fill=leaf_color_dark, width=2 * SCALE)

img = Image.alpha_composite(img, leaf_layer)

# === Clip everything to the disc circle ===
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

# Outer subtle dark rim
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
