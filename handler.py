"""
RunPod Serverless Handler for Wan2.2-Animate-14B Face Swap
"""

import os
import runpod
import subprocess
import tempfile
import base64
import requests
from pathlib import Path

# Paths - Model stored on network volume for persistence
# Check both possible mount points (pods use /workspace, serverless uses /runpod-volume)
def get_model_dir():
    if os.environ.get("MODEL_DIR"):
        return Path(os.environ.get("MODEL_DIR"))
    # Check /runpod-volume first (serverless), then /workspace (pods)
    for path in ["/runpod-volume/Wan2.2-Animate-14B", "/workspace/Wan2.2-Animate-14B"]:
        if Path(path).exists():
            return Path(path)
    return Path("/runpod-volume/Wan2.2-Animate-14B")  # default for download

MODEL_DIR = get_model_dir()
WAN_DIR = Path("/workspace/Wan2.2")

def ensure_model_downloaded():
    """Download model to network volume if not present."""
    marker_file = MODEL_DIR / ".download_complete"

    if marker_file.exists():
        print("Model already downloaded.")
        return

    print("Model not found. Downloading to network volume...")
    print("This will take 15-30 minutes on first run, but only happens once.")

    # Create directory
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Download using huggingface-cli
    result = subprocess.run([
        "huggingface-cli", "download",
        "Wan-AI/Wan2.2-Animate-14B",
        "--local-dir", str(MODEL_DIR)
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Model download failed: {result.stderr}")

    # Create marker file to indicate successful download
    marker_file.touch()
    print("Model download complete!")

def download_file(url: str, dest: Path) -> Path:
    """Download a file from URL to destination."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return dest

def save_base64_file(data: str, dest: Path) -> Path:
    """Save base64 encoded data to file."""
    file_data = base64.b64decode(data)
    with open(dest, 'wb') as f:
        f.write(file_data)
    return dest

def run_preprocessing(video_path: Path, photo_path: Path, output_dir: Path, resolution: tuple):
    """Run the preprocessing step."""
    cmd = [
        "python", str(WAN_DIR / "wan" / "modules" / "animate" / "preprocess" / "preprocess_data.py"),
        "--ckpt_path", str(MODEL_DIR / "process_checkpoint"),
        "--video_path", str(video_path),
        "--refer_path", str(photo_path),
        "--save_path", str(output_dir),
        "--resolution_area", str(resolution[0]), str(resolution[1]),
        "--iterations", "3",
        "--k", "7",
        "--w_len", "1",
        "--h_len", "1",
        "--replace_flag"
    ]

    result = subprocess.run(cmd, cwd=WAN_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Preprocessing failed: {result.stderr}")
    return output_dir

def run_generation(processed_dir: Path, output_path: Path):
    """Run the video generation step."""
    cmd = [
        "python", "generate.py",
        "--task", "animate-14B",
        "--ckpt_dir", str(MODEL_DIR),
        "--src_root_path", str(processed_dir),
        "--refert_num", "1",
        "--replace_flag",
        "--use_relighting_lora"
    ]

    result = subprocess.run(cmd, cwd=WAN_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Generation failed: {result.stderr}")

    # Find output file
    output_files = list((WAN_DIR / "outputs").glob("*.mp4"))
    if output_files:
        latest = max(output_files, key=lambda p: p.stat().st_mtime)
        import shutil
        shutil.move(str(latest), str(output_path))
        return output_path
    else:
        raise RuntimeError("No output file generated")

def handler(job):
    """
    RunPod serverless handler.

    Input format:
    {
        "input": {
            "video_url": "https://...",      # URL to video file
            "photo_url": "https://...",      # URL to face photo
            # OR use base64:
            "video_base64": "...",           # Base64 encoded video
            "photo_base64": "...",           # Base64 encoded photo

            "resolution": [1280, 720],       # Optional, default 1280x720
            "output_format": "url"           # "url" or "base64", default "url"
        }
    }

    Output format:
    {
        "output_url": "https://...",         # If output_format is "url"
        # OR
        "output_base64": "...",              # If output_format is "base64"
        "status": "success"
    }
    """
    job_input = job["input"]

    # Ensure model is downloaded (first run only)
    ensure_model_downloaded()

    # Create temp directory for this job
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        process_dir = temp_path / "processed"
        process_dir.mkdir()

        # Get video
        video_path = temp_path / "input_video.mp4"
        if "video_url" in job_input:
            download_file(job_input["video_url"], video_path)
        elif "video_base64" in job_input:
            save_base64_file(job_input["video_base64"], video_path)
        else:
            return {"error": "No video provided. Use video_url or video_base64"}

        # Get photo
        photo_path = temp_path / "input_photo.jpg"
        if "photo_url" in job_input:
            download_file(job_input["photo_url"], photo_path)
        elif "photo_base64" in job_input:
            save_base64_file(job_input["photo_base64"], photo_path)
        else:
            return {"error": "No photo provided. Use photo_url or photo_base64"}

        # Get resolution
        resolution = tuple(job_input.get("resolution", [1280, 720]))

        # Output path
        output_path = temp_path / "output.mp4"

        try:
            # Run preprocessing
            run_preprocessing(video_path, photo_path, process_dir, resolution)

            # Run generation
            run_generation(process_dir, output_path)

            # Return output
            output_format = job_input.get("output_format", "base64")

            if output_format == "base64":
                with open(output_path, "rb") as f:
                    output_base64 = base64.b64encode(f.read()).decode("utf-8")
                return {
                    "output_base64": output_base64,
                    "status": "success"
                }
            else:
                # For URL output, you'd need to upload to cloud storage
                # This is a placeholder - implement based on your storage choice
                with open(output_path, "rb") as f:
                    output_base64 = base64.b64encode(f.read()).decode("utf-8")
                return {
                    "output_base64": output_base64,
                    "status": "success",
                    "note": "URL output requires cloud storage configuration"
                }

        except Exception as e:
            return {"error": str(e), "status": "failed"}

# Start the serverless worker
runpod.serverless.start({"handler": handler})
