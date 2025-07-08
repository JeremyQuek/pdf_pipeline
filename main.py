import os
import logging
import uuid

from flask import Flask, request
from dotenv import load_dotenv

from utils.pdf_to_images import *
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

    try:
        page_images = extract_images(file_buf = content)
        page_images_descriptions = asyncio.run(main_tasks_handler(job_id=job_id, image_uris=page_images))
        combined_page_text = combine_outputs(page_images_descriptions)
    except Exception as e:
        logging.error(f"Error processing file: {e}")
        return {'error': str(e)}, 500

    logging.info(f"File {filename} processing completed")
    return {"job_id": job_id, "message": f"File {filename} processing completed", "result": combined_page_text}, 200

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8087, debug=True)
