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

# Install Wan2.2 dependencies (excluding flash_attn which has compatibility issues)
WORKDIR /workspace/Wan2.2
RUN grep -v "flash_attn" requirements.txt > requirements_no_flash.txt && \
    pip install --no-cache-dir -r requirements_no_flash.txt && \
    pip install --no-cache-dir \
    loguru \
    onnxruntime-gpu \
    moviepy \
    decord \
    hydra-core \
    omegaconf \
    sam2 \
    matplotlib \
    einops

# Verify all imports work (fail fast if something is missing)
RUN cd /workspace/Wan2.2/wan/modules/animate/preprocess && \
    python -c "from process_pipepline import ProcessPipeline; print('✅ Preprocessing imports OK')"
RUN cd /workspace/Wan2.2 && \
    python -c "import wan; print('✅ Generation imports OK')"

# Copy handler
WORKDIR /workspace
COPY handler.py /workspace/handler.py

# Model will be downloaded at runtime to network volume
# This keeps build fast and under the 30-minute limit

# Set environment variables
ENV PYTHONUNBUFFERED=1
# Don't hardcode MODEL_DIR - let handler auto-detect /runpod-volume (serverless) or /workspace (pods)

# Start the handler
CMD ["python", "-u", "/workspace/handler.py"]
