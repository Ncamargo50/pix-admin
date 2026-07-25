"""Extract all embedded images from the original PDF at native resolution."""
import fitz
import os

src = r"D:\PIXADVISOR_AGENT_WORKSPACE\MDO_Autorizacion_Original.pdf"
out_dir = r"D:\PIXADVISOR_AGENT_WORKSPACE\pdf_images"
os.makedirs(out_dir, exist_ok=True)

doc = fitz.open(src)
for pnum in range(len(doc)):
    page = doc[pnum]
    images = page.get_images(full=True)
    print(f"Page {pnum + 1}: {len(images)} images")
    for idx, img in enumerate(images):
        xref = img[0]
        base = doc.extract_image(xref)
        ext = base["ext"]
        w = base["width"]
        h = base["height"]
        path = os.path.join(out_dir, f"p{pnum+1}_img{idx+1}_{w}x{h}.{ext}")
        with open(path, "wb") as f:
            f.write(base["image"])
        print(f"  img{idx+1}: {w}x{h} {ext} -> {path}")

doc.close()
