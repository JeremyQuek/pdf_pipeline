import fitz
import base64
from io import BytesIO

def coordinate_conversion(page, bbox):
    page_height = page.rect.height
    l = bbox["l"]
    r = bbox["r"]
    t = page_height - bbox["t"]
    b = page_height - bbox["b"]
    y0 = min(t, b)
    y1 = max(t, b)
    x0 = min(l, r)
    x1 = max(l, r)
    return fitz.Rect(x0, y0, x1, y1)

def extract_tables(file_buf, pdf_structure):
    doc = fitz.open(stream=file_buf, filetype="pdf")
    table_uris = []
    for idx, table in enumerate(pdf_structure["tables"]):
        page_no = table["prov"][0]["page_no"]
        bbox = table["prov"][0]["bbox"]
        coord_origin = bbox["coord_origin"]

        page = doc.load_page(page_no)

        if coord_origin == "BOTTOMLEFT":
            rect = coordinate_conversion(page, bbox)
        else:
            rect = fitz.Rect(bbox["l"], bbox["t"], bbox["r"], bbox["b"])

        pix = page.get_pixmap(clip=rect)

        img_bytes = pix.tobytes(output="png")
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        pix.save(f"output/sliced_table_{idx}.png")  # saving to disk as well

        table_uris.append((idx, img_b64))
    return table_uris
