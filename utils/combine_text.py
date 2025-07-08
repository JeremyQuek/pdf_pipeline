import re
import logging

def combine_outputs(page_images_descriptions):
    combined_page_text = []
    with open("output/result2xs.txt","w")as f:
        for page in page_images_descriptions:
            f.write(page[2])

    for page in page_images_descriptions:
        if page[1]=="failed":
            combined_page_text.append((f"---\n\nNo text was extracted for page {page[0]}\n\n---"))
            continue
        match = re.search(r"\[Page text\](.*?)\[End Page\]", page[2], re.DOTALL)
        if match:
            page_text = match.group(1).strip()
        else:
            page_text  = page[1]
    combined_page_text.append(page_text)

    return "".join(combined_page_text)

    