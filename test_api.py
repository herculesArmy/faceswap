#!/usr/bin/env python3
"""
Test script for Face Swap RunPod Serverless API
"""

import requests
import base64
import json
import sys
import time
import os

# Load .env file if present
from dotenv import load_dotenv
load_dotenv()

RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY")
ENDPOINT_ID = os.environ.get("RUNPOD_ENDPOINT_ID")

# Test files - set via env vars or use defaults
VIDEO_URL = os.environ.get("VIDEO_URL", "")
PHOTO_URL = os.environ.get("PHOTO_URL", "")

def run_faceswap(video_url: str, photo_url: str, resolution: list = [1280, 720]):
    """Run face swap via RunPod API."""

    endpoint_url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"

    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "input": {
            "video_url": video_url,
            "photo_url": photo_url,
            "resolution": resolution
        }
    }

    print(f"Submitting job to RunPod...")
    print(f"  Video: {video_url}")
    print(f"  Photo: {photo_url}")
    print(f"  Resolution: {resolution}")

    # Submit job
    response = requests.post(endpoint_url, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()

    job_id = result.get("id")
    print(f"\nJob submitted! ID: {job_id}")

    # Poll for status
    status_url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}"

    print("Waiting for completion...")
    while True:
        status_response = requests.get(status_url, headers=headers)
        status_data = status_response.json()

        status = status_data.get("status")
        print(f"  Status: {status}")

        if status == "COMPLETED":
            return status_data.get("output")
        elif status == "FAILED":
            print(f"Error: {status_data.get('error')}")
            return None
        elif status in ["IN_QUEUE", "IN_PROGRESS"]:
            time.sleep(10)  # Poll every 10 seconds
        else:
            print(f"Unknown status: {status}")
            time.sleep(5)

def save_output(output_data: dict, output_path: str = "output.mp4"):
    """Save the output video."""
    if "output_base64" in output_data:
        video_bytes = base64.b64decode(output_data["output_base64"])
        with open(output_path, "wb") as f:
            f.write(video_bytes)
        print(f"\nSaved to: {output_path}")
        return True
    else:
        print("No output_base64 in response")
        return False

def main():
    if not RUNPOD_API_KEY:
        print("ERROR: RUNPOD_API_KEY environment variable not set")
        print("Run: export RUNPOD_API_KEY='your-key-here'")
        print("Get it from: https://www.runpod.io/console/user/settings")
        sys.exit(1)

    if not ENDPOINT_ID:
        print("ERROR: RUNPOD_ENDPOINT_ID environment variable not set")
        print("Run: export RUNPOD_ENDPOINT_ID='your-endpoint-id'")
        print("Get it from your deployed serverless endpoint")
        sys.exit(1)

    if not VIDEO_URL or not PHOTO_URL:
        print("ERROR: VIDEO_URL and PHOTO_URL environment variables required")
        print("Run: export VIDEO_URL='https://...' && export PHOTO_URL='https://...'")
        sys.exit(1)

    # Run face swap
    output = run_faceswap(VIDEO_URL, PHOTO_URL)

    if output and output.get("status") == "success":
        save_output(output, "faceswap_result.mp4")
        print("\nFace swap completed successfully!")
    else:
        print(f"\nFace swap failed: {output}")

if __name__ == "__main__":
    main()
