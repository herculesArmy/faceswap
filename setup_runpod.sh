#!/bin/bash
# RunPod Setup Script for Wan2.2-Animate-14B Face Swap Model
# Run this script on a fresh RunPod instance with an A100 GPU

set -e

echo "=========================================="
echo "Wan2.2-Animate-14B Setup Script for RunPod"
echo "=========================================="

# Check for NVIDIA GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: NVIDIA GPU not detected. Please use a GPU-enabled instance."
    exit 1
fi

echo "GPU detected:"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# Update system
echo ""
echo "[1/6] Updating system packages..."
apt-get update -qq
apt-get install -y -qq git git-lfs ffmpeg libsm6 libxext6 > /dev/null 2>&1

# Set up working directory
WORK_DIR="${HOME}/faceswap"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Clone Wan2.2 repository
echo ""
echo "[2/6] Cloning Wan2.2 repository..."
if [ ! -d "Wan2.2" ]; then
    git clone --depth 1 https://github.com/Wan-Video/Wan2.2.git
fi
cd Wan2.2

# Install Python dependencies
echo ""
echo "[3/6] Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -q -r requirements.txt
pip install -q huggingface_hub[cli]

# Download model
echo ""
echo "[4/6] Downloading Wan2.2-Animate-14B model (this may take a while)..."
if [ ! -d "Wan2.2-Animate-14B" ]; then
    huggingface-cli download Wan-AI/Wan2.2-Animate-14B --local-dir ./Wan2.2-Animate-14B --quiet
fi

# Create directories for inputs/outputs
echo ""
echo "[5/6] Creating input/output directories..."
mkdir -p "${WORK_DIR}/inputs/videos"
mkdir -p "${WORK_DIR}/inputs/photos"
mkdir -p "${WORK_DIR}/outputs"
mkdir -p "${WORK_DIR}/processed"

# Copy the face swap script
echo ""
echo "[6/6] Setup complete!"
echo ""
echo "=========================================="
echo "SETUP COMPLETE!"
echo "=========================================="
echo ""
echo "Directory structure:"
echo "  ${WORK_DIR}/inputs/videos/  - Place your reference videos here"
echo "  ${WORK_DIR}/inputs/photos/  - Place your face photos here"
echo "  ${WORK_DIR}/outputs/        - Generated videos will appear here"
echo ""
echo "Next steps:"
echo "  1. Upload your video to: ${WORK_DIR}/inputs/videos/"
echo "  2. Upload your face photo to: ${WORK_DIR}/inputs/photos/"
echo "  3. Run: python faceswap.py --video <video_name> --photo <photo_name>"
echo ""
