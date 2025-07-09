import re
import logging

def combine_outputs(page_images_descriptions):
    combined_page_text = []
    with open("../output/openai_keppel.md", "w") as f:

        for page in page_images_descriptions:
            if page[1]=="failed":
                combined_page_text.append((f"---\n\nNo text was extracted for page {page[0]}\n\n---"))
                continue
            match = re.search(r"\[Page Text\](.*?)\[End Page\]", page[2], re.DOTALL | re.IGNORECASE)
            if match:
                page_text = match.group(1).strip()
            else:
                page_text  = page[2]
            combined_page_text.append(page_text)
            f.write(page_text)

    return "\n\n".join(combined_page_text)

    