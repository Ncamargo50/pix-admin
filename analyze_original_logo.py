"""Upscale the official MDO logo for inspection of its exact look."""
from PIL import Image, ImageFilter

src = r"D:\PIXADVISOR_AGENT_WORKSPACE\mdo_logo_color.png"
img = Image.open(src).convert("RGBA")
print(f"Original: {img.size} mode={img.mode}")

# Upscale 8x with LANCZOS for inspection
big = img.resize((img.width * 8, img.height * 8), Image.LANCZOS)
big.save(r"D:\PIXADVISOR_AGENT_WORKSPACE\mdo_logo_8x_inspection.png")
print(f"Upscaled to: {big.size}")

# Also extract dominant colors from the "O" landscape area
# Approximate landscape region in original 197x31
# "O" of MDO is at roughly x=49..65 in the 197 width
crop = img.crop((49, 6, 65, 25))
crop_big = crop.resize((400, 480), Image.LANCZOS)
crop_big.save(r"D:\PIXADVISOR_AGENT_WORKSPACE\mdo_O_landscape_8x.png")

# Sample a few colors
print("\nLandscape pixel samples:")
sample_points = [(53, 10), (55, 15), (57, 20), (60, 12), (62, 22)]
for x, y in sample_points:
    if 0 <= x < img.width and 0 <= y < img.height:
        px = img.getpixel((x, y))
        print(f"  ({x},{y}): {px}")
