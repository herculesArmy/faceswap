# RunPod Serverless Dockerfile for Wan2.2-Animate-14B Face Swap
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    git-lfs \
    ffmpeg \
    libsm6 \
    libxext6 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    runpod \
    requests \
    huggingface_hub[cli]

# Clone Wan2.2 repository
RUN git clone --depth 1 https://github.com/Wan-Video/Wan2.2.git

# Install Wan2.2 dependencies
WORKDIR /workspace/Wan2.2
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler
WORKDIR /workspace
COPY handler.py /workspace/handler.py

# Model will be downloaded at runtime to network volume
# This keeps build fast and under the 30-minute limit

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/workspace/hf_cache
ENV MODEL_DIR=/workspace/Wan2.2-Animate-14B

# Start the handler
CMD ["python", "-u", "/workspace/handler.py"]
