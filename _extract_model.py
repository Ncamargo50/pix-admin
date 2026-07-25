import sys, json

path = r"C:\Users\Usuario\Desktop\Propuesta_Pixadvisor_HaciendaCerroAlto.pdf"

def via_pdfplumber():
    import pdfplumber
    out = []
    with pdfplumber.open(path) as pdf:
        out.append(f"PAGES: {len(pdf.pages)}")
        for i, pg in enumerate(pdf.pages, 1):
            txt = (pg.extract_text() or "").strip()
            nimg = len(pg.images)
            out.append(f"\n===== PAGE {i} | images={nimg} =====")
            out.append(txt if txt else "(no text)")
    return "\n".join(out)

def via_pypdf():
    try:
        from pypdf import PdfReader
    except Exception:
        from PyPDF2 import PdfReader
    r = PdfReader(path)
    out = [f"PAGES: {len(r.pages)}"]
    for i, pg in enumerate(r.pages, 1):
        txt = (pg.extract_text() or "").strip()
        out.append(f"\n===== PAGE {i} =====")
        out.append(txt if txt else "(no text)")
    return "\n".join(out)

for fn in (via_pdfplumber, via_pypdf):
    try:
        print(fn())
        break
    except Exception as e:
        sys.stderr.write(f"{fn.__name__} failed: {e}\n")
