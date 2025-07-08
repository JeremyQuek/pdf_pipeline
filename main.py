import os
import logging
import uuid
from io import BytesIO

from flask import Flask, request
from dotenv import load_dotenv
from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from utils.filter_images import *
from utils.openai_async import *
from utils.combine_text import *

load_dotenv()
PORT = int(os.getenv("PORT", 8087))

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/', methods=['POST'])
def documentprocessing():
    if 'file' not in request.files:
        logging.error("No file part in the request")
        return {'error': 'No file part in the request'}, 400

    file = request.files['file']
    filename = file.filename

    if filename == '':
        return {'error': 'No selected file'}, 400

    job_id = str(uuid.uuid4())


    logging.info(f"Processing file: {filename} with job ID: {job_id}")
    content = file.read()
    buf = BytesIO(content)
    source = DocumentStream(name=filename, stream=buf)

    pipeline_options = PdfPipelineOptions(
        do_ocr= False,
        do_table_structure=True,
        generate_picture_images=True,
    )

    logging.info(f"Utilizing {os.cpu_count()} cores for text extraction and analysis")
    try:
        converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options,
                    )
                }
            )

        result = converter.convert(source)
        pdf_structure = result.document.export_to_dict()
        markdown = result.document.export_to_markdown()

        image_uris = extract_and_filter_images(pdf_structure=pdf_structure)

        if image_uris == []:
            logging.info(f"File {filename} processing completed with job_id {job_id}")
            return {"job_id": job_id, "message": f"File {filename} processing completed", "final_result": markdown}, 200

        image_results = asyncio.run(main_tasks_handler(job_id=job_id, image_uris=image_uris))
        extracted_image_texts = process_images_results(image_results=image_results,pdf_structure=pdf_structure)
        final_result = interleave_text_and_images(markdown=markdown, extracted_image_texts= extracted_image_texts)

        with open("../output/docling.txt", "w") as f:
            f.write(final_result)
    except Exception as e:
        logging.error(f"Error processing file: {e}")
        return {'error': str(e)}, 500

    logging.info(f"File {filename} processing completed")
    return {"job_id": job_id, "message": f"File {filename} processing completed", "final_result": final_result}, 200

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Cloud Run. See entrypoint in Dockerfile.
    app.run(host="127.0.0.1", port=8087, debug=True)
