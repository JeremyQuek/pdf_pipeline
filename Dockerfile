# Referenced from https://github.com/DS4SD/docling/blob/main/Dockerfile

FROM python:3.11-slim-bookworm

RUN apt-get update \
    && apt-get install -y libgl1 libglib2.0-0 curl wget git procps \
    && apt-get clean

# This will install torch with *only* cpu support
# Remove the --extra-index-url part if you want to install all the gpu requirements
# For more details in the different torch distribution visit https://pytorch.org/.
RUN pip install --no-cache-dir docling --extra-index-url https://download.pytorch.org/whl/cpu

ENV HF_HOME=/tmp/
ENV TORCH_HOME=/tmp/

RUN docling-tools models download --output-dir /models/
ENV DOCLING_ARTIFACTS_PATH=/models/

# On container environments, always set a thread budget to avoid undesired thread congestion.
ENV OMP_NUM_THREADS=4

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Run the web service on container startup.
# Use gunicorn webserver with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
