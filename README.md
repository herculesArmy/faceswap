# Face Swap - RunPod Serverless

Face swap using Wan2.2-Animate-14B model on RunPod Serverless.

## Setup on RunPod

### Option 1: GitHub Integration (Recommended)

1. Push this repo to GitHub
2. In RunPod Console → Serverless → Create Endpoint
3. Select **"Build from GitHub"**
4. Connect your GitHub account and select `herculesArmy/faceswap`
5. Choose GPU: **A100 80GB** recommended
6. Set Max Workers based on your needs
7. Deploy

### Option 2: Docker Hub

1. Build and push the image:
```bash
docker build -t your-dockerhub/faceswap:latest .
docker push your-dockerhub/faceswap:latest
```

2. In RunPod, select "Docker Image" and enter your image URL

## API Usage

### Endpoint URL
After deployment, you'll get an endpoint URL like:
```
https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync
```

### Request Format

```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "video_url": "https://example.com/video.mp4",
      "photo_url": "https://example.com/face.jpg",
      "resolution": [1280, 720]
    }
  }'
```

### Input Options

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `video_url` | string | Yes* | URL to the reference video |
| `photo_url` | string | Yes* | URL to the face photo |
| `video_base64` | string | Yes* | Base64 encoded video (alternative to URL) |
| `photo_base64` | string | Yes* | Base64 encoded photo (alternative to URL) |
| `resolution` | [int, int] | No | Output resolution, default [1280, 720] |

*Either URL or base64 must be provided for both video and photo

### Response Format

```json
{
  "output": {
    "output_base64": "AAAAIGZ0eXBpc29t...",
    "status": "success"
  }
}
```

### Python Example

```python
import runpod
import base64

runpod.api_key = "YOUR_RUNPOD_API_KEY"
endpoint = runpod.Endpoint("YOUR_ENDPOINT_ID")

# Run face swap
result = endpoint.run_sync({
    "video_url": "https://example.com/dance.mp4",
    "photo_url": "https://example.com/myface.jpg",
    "resolution": [1280, 720]
})

# Save output
if result["status"] == "success":
    video_data = base64.b64decode(result["output_base64"])
    with open("output.mp4", "wb") as f:
        f.write(video_data)
    print("Saved to output.mp4")
else:
    print(f"Error: {result.get('error')}")
```

## Files

| File | Description |
|------|-------------|
| `handler.py` | Main serverless handler (model baked into image) |
| `handler_networkvolume.py` | Handler for network volume setup |
| `Dockerfile` | Main Dockerfile (~50GB image with model) |
| `Dockerfile.networkvolume` | Smaller image, model on network volume |

## Network Volume Setup (Optional)

If you want faster builds and smaller images:

1. Create a Network Volume in RunPod (100GB+)
2. Use `Dockerfile.networkvolume` instead
3. The model will auto-download to the volume on first run

## Cost Estimate

- Cold start: ~2-5 minutes (model loading)
- Processing: ~2-5 minutes per 10 second video
- Cost: ~$0.01-0.03 per second of GPU time

## Troubleshooting

**Cold starts are slow**: First request loads the 50GB model. Use "Active Workers" setting to keep workers warm.

**Out of memory**: Reduce resolution or use a larger GPU (H100).

**Video too long**: Split into shorter segments (<30 seconds).
# Trigger rebuild Sat Jan 17 16:44:27 +07 2026
