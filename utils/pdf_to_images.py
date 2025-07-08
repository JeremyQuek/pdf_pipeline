import fitz
import base64
import logging

def extract_images(file_buf):
    try:
        doc = fitz.open(stream=file_buf, filetype="pdf")
        page_images = []
        for page_no, page in enumerate(doc):  
            pix = page.get_pixmap()
            img_bytes = pix.tobytes(output="png")
            img_b64 = "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")

            page_images.append((page_no, img_b64))
            pix.save(f"output/page_{page_no}.png")
        return page_images
    except Exception as e:
        logging.info(f"Error encountered while attempting to open PDF: {e}")
        raise 