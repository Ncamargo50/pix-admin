"""Build a real-looking rubber stamp: bold text + drop shadow + slight ink-bleed."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import os
import random

OUT = r"D:\PIXADVISOR_AGENT_WORKSPACE\stamp_digital_hd.png"

LINES = [
    ("M. D. O. AGRO INDUSTRIA LTDA.", 1.0),
    ("AV MERCOSUL, 1.474 - NOVA ESPERANÇA-PR", 0.86),
    ("CNPJ 44.631.321/0001-60 - I.E. 90932499-81", 0.86),
    ("TEL (44) 97400-9877 - (44) 99134-3408 - (44) 3090-8038", 0.82),
]

INK = (15, 25, 85)        # deep navy ink
SHADOW = (0, 0, 0, 90)    # soft shadow

# Heavy bold font for stamp authenticity
font_paths_bold = [
    r"C:\Windows\Fonts\ariblk.ttf",   # Arial Black
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\verdanab.ttf",
    r"C:\Windows\Fonts\impact.ttf",
]
font_path = next((p for p in font_paths_bold if os.path.exists(p)), None)
if not font_path:
    raise RuntimeError("No bold font found")

SCALE = 4
W = 2000
H = 600
CW, CH = W * SCALE, H * SCALE

img_text = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
draw = ImageDraw.Draw(img_text)

FS_BASE = 78 * SCALE
PAD_X = 40 * SCALE
PAD_Y = 40 * SCALE
LINE_GAP = 10 * SCALE

# Pre-render each line
rendered = []
for text, scale_factor in LINES:
    fs = int(FS_BASE * scale_factor)
    f = ImageFont.truetype(font_path, fs)
    bbox = draw.textbbox((0, 0), text, font=f)
    rendered.append({
        "text": text,
        "font": f,
        "bbox": bbox,
        "w": bbox[2] - bbox[0],
        "h": bbox[3] - bbox[1],
    })

total_h = sum(r["h"] for r in rendered) + LINE_GAP * (len(rendered) - 1)
max_w = max(r["w"] for r in rendered)

# Center on canvas
y = (CH - total_h) // 2

# Render each line centered
for r in rendered:
    f = r["font"]
    text = r["text"]
    bbox = r["bbox"]
    tw = r["w"]
    th = r["h"]
    x = (CW - tw) // 2 - bbox[0]
    ty = y - bbox[1]
    draw.text((x, ty), text, font=f, fill=(*INK, 255))
    y += th + LINE_GAP

# Slight ink-bleed via tiny noise mask multiplied into alpha
random.seed(7)
noise = Image.new("L", (CW // 6, CH // 6), 255)
ndraw = ImageDraw.Draw(noise)
for _ in range(1500):
    nx = random.randint(0, noise.width - 1)
    ny = random.randint(0, noise.height - 1)
    nr = random.randint(1, 4)
    nv = random.randint(200, 255)
    ndraw.ellipse([nx - nr, ny - nr, nx + nr, ny + nr], fill=nv)
noise = noise.resize((CW, CH), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1))

r, g, b, a = img_text.split()
a_data = a.load()
n_data = noise.load()
for yy in range(CH):
    for xx in range(CW):
        v = a_data[xx, yy]
        if v > 0:
            mod = n_data[xx, yy]
            a_data[xx, yy] = v * mod // 255
img_text.putalpha(a)

# Slight gaussian softness for ink feel
img_text = img_text.filter(ImageFilter.GaussianBlur(0.4 * SCALE))

# === Build drop shadow ===
shadow_offset_x = 4 * SCALE
shadow_offset_y = 6 * SCALE
shadow_blur = 5 * SCALE

# shadow alpha = text alpha, blurred
text_alpha = img_text.split()[3]
shadow_alpha = text_alpha.filter(ImageFilter.GaussianBlur(shadow_blur))
# reduce intensity
shadow_alpha = shadow_alpha.point(lambda v: int(v * 0.55))

shadow_layer = Image.new("RGBA", (CW, CH), SHADOW[:3] + (0,))
shadow_layer.putalpha(shadow_alpha)
# offset
shadow_offset = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
shadow_offset.paste(shadow_layer, (shadow_offset_x, shadow_offset_y))

# Composite shadow under text
final_canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
final_canvas = Image.alpha_composite(final_canvas, shadow_offset)
final_canvas = Image.alpha_composite(final_canvas, img_text)

# Trim and pad
bbox_trim = final_canvas.getbbox()
trimmed = final_canvas.crop(bbox_trim)
pad = 50
final_w = trimmed.width + pad * 2
final_h = trimmed.height + pad * 2
final = Image.new("RGBA", (final_w, final_h), (0, 0, 0, 0))
final.paste(trimmed, (pad, pad), trimmed)

# Downscale to crisp final
target_w = 2000
ratio = target_w / final.width
target_h = int(final.height * ratio)
final = final.resize((target_w, target_h), Image.LANCZOS)

final.save(OUT, optimize=True)
print(f"Saved: {OUT} -> {final.size}")
