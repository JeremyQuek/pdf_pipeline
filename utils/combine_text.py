import re
import logging

def process_images_results(image_results: list, pdf_structure: dict):
    pictures = pdf_structure.get("pictures", [])
    extracted_image_texts = ["" for _ in range(len(pictures))]
    try:
        texts = pdf_structure.get("texts", [])

        for row in image_results:
            image_id = row[0]
            status = row[1]
            extracted_text = row[2]

            if status == "success":
                match = re.search(r"\[IMAGE TEXT\](.*?)\[END TEXT\]", extracted_text, re.DOTALL)
                formatted_text = match.group(1).strip() if match else extracted_text.strip()
                extracted_image_texts[image_id] = formatted_text

            elif image_id < len(pictures):
                image_body = pictures[image_id]
                children = image_body.get("children")
                if not children:
                    continue

                text_elements = []
                for child in children:
                    ref = child.get("$ref", "")
                    match = re.search(r'#/texts/(\d+)', ref)
                    if match:
                        idx = int(match.group(1))
                        if 0 <= idx < len(texts):
                            text_elements.append(texts[idx].get("text", ""))
                        else:
                            logging.warning(f"text index {idx} out of bounds")
                if text_elements:
                    extracted_image_texts[image_id] = " ".join(text_elements)
        logging.info(f"Sucessfully processed image results from Openai tasks")
        return extracted_image_texts
    except Exception as e:
        logging.error(f"Error processing image results from Openai tasks: {e}")
        return extracted_image_texts


def interleave_text_and_images(markdown:str, extracted_image_texts:list[str]):
    markdown_components = markdown.split("<!-- image -->")
    joined_pdf_text = []
    for i, component in enumerate(markdown_components):
        joined_pdf_text.append(component)
        if i<len(extracted_image_texts) and extracted_image_texts[i]!="":
            joined_pdf_text.append("### Image Information\n\n"+ extracted_image_texts[i])
    return " ".join(joined_pdf_text)
