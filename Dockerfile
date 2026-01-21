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

# Install Wan2.2 dependencies (excluding flash_attn - will install separately)
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
    einops \
    librosa \
    safetensors \
    torchaudio \
    peft

# Install flash-attn from pre-built wheel (required for generation)
# Using wheel from https://github.com/Dao-AILab/flash-attention/releases
RUN pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.7.0.post2/flash_attn-2.7.0.post2+cu12torch2.4cxx11abiFALSE-cp311-cp311-linux_x86_64.whl || \
    pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.6.3/flash_attn-2.6.3+cu123torch2.4cxx11abiFALSE-cp311-cp311-linux_x86_64.whl || \
    echo "Warning: flash-attn wheel installation failed"

# Verify preprocessing imports work (fail fast if something is missing)
# Note: Can't verify generation imports (import wan) as it requires CUDA
RUN cd /workspace/Wan2.2/wan/modules/animate/preprocess && \
    python -c "from process_pipepline import ProcessPipeline; print('✅ Preprocessing imports OK')"

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
