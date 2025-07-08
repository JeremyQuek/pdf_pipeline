import re
import base64
import logging
from io import BytesIO

def extract_and_filter_images(pdf_structure: dict, tolerance: float = 0.1) -> list[tuple[int,str]]:
    filtered_uris=[] 
    for pic in pdf_structure['pictures']:
        if pic["children"]==[]:
            continue
        dpi = pic["image"]["dpi"]
        width_pt = pic["image"]["size"]["width"]
        height_pt = pic["image"]["size"]["height"]
        width_px = width_pt * (dpi / 72)
        height_px = height_pt * (dpi / 72)

        if width_px<100 or height_px<100:
            continue

        image_id = pic["self_ref"]
        match = re.search(r'\d+', image_id)
        if match:
            image_id = match.group(0)
        filtered_uris.append((int(image_id), pic["image"]["uri"]))
    logging.info(f"There are {len(pdf_structure['pictures'])} images")
    logging.info(f"There are {len(filtered_uris)} images filtered through")
    return filtered_uris
