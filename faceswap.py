#!/usr/bin/env python3
"""
Face Swap Script for Wan2.2-Animate-14B
Wrapper script to easily swap faces in videos using a reference photo.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Configuration
HOME = os.path.expanduser("~")
WORK_DIR = Path(HOME) / "faceswap"
WAN_DIR = WORK_DIR / "Wan2.2"
MODEL_DIR = WAN_DIR / "Wan2.2-Animate-14B"
INPUTS_VIDEO_DIR = WORK_DIR / "inputs" / "videos"
INPUTS_PHOTO_DIR = WORK_DIR / "inputs" / "photos"
OUTPUTS_DIR = WORK_DIR / "outputs"
PROCESSED_DIR = WORK_DIR / "processed"


def check_setup():
    """Verify the setup is complete."""
    if not WAN_DIR.exists():
        print("ERROR: Wan2.2 repository not found. Run setup_runpod.sh first.")
        sys.exit(1)
    if not MODEL_DIR.exists():
        print("ERROR: Model not downloaded. Run setup_runpod.sh first.")
        sys.exit(1)


def find_file(name: str, directory: Path) -> Path:
    """Find a file in a directory, with or without extension."""
    # Direct match
    direct = directory / name
    if direct.exists():
        return direct

    # Search for partial match
    matches = list(directory.glob(f"{name}*"))
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"Multiple matches found for '{name}':")
        for m in matches:
            print(f"  - {m.name}")
        print("Please specify the exact filename.")
        sys.exit(1)

    # List available files
    available = list(directory.glob("*"))
    if available:
        print(f"File '{name}' not found in {directory}")
        print("Available files:")
        for f in available:
            if f.is_file():
                print(f"  - {f.name}")
    else:
        print(f"No files found in {directory}")
        print(f"Please upload your files to: {directory}")
    sys.exit(1)


def run_preprocessing(video_path: Path, photo_path: Path, output_dir: Path, resolution: tuple):
    """Run the preprocessing step."""
    print("\n[Step 1/2] Preprocessing video and photo...")
    print(f"  Video: {video_path}")
    print(f"  Photo: {photo_path}")
    print(f"  Resolution: {resolution[0]}x{resolution[1]}")

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
        "--replace_flag"  # Use replacement mode for face swapping
    ]

    result = subprocess.run(cmd, cwd=WAN_DIR)
    if result.returncode != 0:
        print("ERROR: Preprocessing failed.")
        sys.exit(1)

    print("  Preprocessing complete!")


def run_generation(processed_dir: Path, output_path: Path, num_gpus: int):
    """Run the video generation step."""
    print("\n[Step 2/2] Generating face-swapped video...")

    if num_gpus > 1:
        # Multi-GPU inference
        cmd = [
            "python", "-m", "torch.distributed.run",
            "--nnodes", "1",
            "--nproc_per_node", str(num_gpus),
            "generate.py",
            "--task", "animate-14B",
            "--ckpt_dir", str(MODEL_DIR),
            "--src_root_path", str(processed_dir),
            "--refert_num", "1",
            "--replace_flag",
            "--use_relighting_lora",
            "--dit_fsdp",
            "--t5_fsdp",
            "--ulysses_size", str(num_gpus)
        ]
    else:
        # Single GPU inference
        cmd = [
            "python", "generate.py",
            "--task", "animate-14B",
            "--ckpt_dir", str(MODEL_DIR),
            "--src_root_path", str(processed_dir),
            "--refert_num", "1",
            "--replace_flag",
            "--use_relighting_lora"
        ]

    result = subprocess.run(cmd, cwd=WAN_DIR)
    if result.returncode != 0:
        print("ERROR: Generation failed.")
        sys.exit(1)

    # Find and move output
    output_files = list((WAN_DIR / "outputs").glob("*.mp4"))
    if output_files:
        latest = max(output_files, key=lambda p: p.stat().st_mtime)
        import shutil
        shutil.move(str(latest), str(output_path))
        print(f"  Output saved to: {output_path}")
    else:
        print("  Generation complete! Check Wan2.2/outputs/ for the result.")


def main():
    parser = argparse.ArgumentParser(
        description="Face swap using Wan2.2-Animate-14B model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python faceswap.py --video dance.mp4 --photo myface.jpg
  python faceswap.py --video interview.mp4 --photo portrait.png --resolution 1920 1080
  python faceswap.py --video clip.mp4 --photo face.jpg --gpus 4
        """
    )

    parser.add_argument("--video", "-v", required=True,
                        help="Input video filename (in inputs/videos/)")
    parser.add_argument("--photo", "-p", required=True,
                        help="Reference face photo filename (in inputs/photos/)")
    parser.add_argument("--resolution", "-r", nargs=2, type=int, default=[1280, 720],
                        metavar=("WIDTH", "HEIGHT"),
                        help="Output resolution (default: 1280 720)")
    parser.add_argument("--gpus", "-g", type=int, default=1,
                        help="Number of GPUs to use (default: 1)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output filename (default: auto-generated)")

    args = parser.parse_args()

    # Check setup
    check_setup()

    # Find input files
    video_path = find_file(args.video, INPUTS_VIDEO_DIR)
    photo_path = find_file(args.photo, INPUTS_PHOTO_DIR)

    # Create unique processing directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_name = f"{video_path.stem}_{photo_path.stem}_{timestamp}"
    process_dir = PROCESSED_DIR / job_name
    process_dir.mkdir(parents=True, exist_ok=True)

    # Output path
    if args.output:
        output_path = OUTPUTS_DIR / args.output
    else:
        output_path = OUTPUTS_DIR / f"{job_name}.mp4"

    print("=" * 50)
    print("Wan2.2-Animate-14B Face Swap")
    print("=" * 50)
    print(f"Video:      {video_path.name}")
    print(f"Photo:      {photo_path.name}")
    print(f"Resolution: {args.resolution[0]}x{args.resolution[1]}")
    print(f"GPUs:       {args.gpus}")
    print(f"Output:     {output_path.name}")
    print("=" * 50)

    # Run pipeline
    run_preprocessing(video_path, photo_path, process_dir, tuple(args.resolution))
    run_generation(process_dir, output_path, args.gpus)

    print("\n" + "=" * 50)
    print("FACE SWAP COMPLETE!")
    print("=" * 50)
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
