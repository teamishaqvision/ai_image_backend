import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import urllib.parse

app = FastAPI()

class ImageRequest(BaseModel):
    prompt: str

# 1. Segmind Image Generation Function (Primary)
def generate_with_segmind(prompt: str):
    api_key = os.environ.get("SG_54f518075b624090")
    if not api_key:
        raise Exception("SG_54f518075b624090")
    
    url = "https://api.segmind.com/v1/sdxl-1.0-base"
    payload = {
        "prompt": prompt,
        "samples": 1,
        "scheduler": "euler_a",
        "num_inference_steps": 25,
        "guidance_scale": 7.5,
        "img_width": 512,
        "img_height": 512,
        "base64": False
    }
    headers = {"x-api-key": api_key}
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Segmind failed with status {response.status_code}: {response.text}")

# 2. Runware Image Generation Function (Secondary)
def generate_with_runware(prompt: str):
    api_key = os.environ.get("fjcQYpZXfII1PcrQdcHTdGjwbrRhvewf")
    if not api_key:
        raise Exception("fjcQYpZXfII1PcrQdcHTdGjwbrRhvewf")
    
    url = "https://api.runware.ai/v1"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = [
        {
            "taskType": "imageInference",
            "taskUUID": "unique-task-id",
            "positivePrompt": prompt,
            "model": "runware:100@1",
            "width": 512,
            "height": 512,
            "numberResults": 1,
            "outputType": "URL"
        }
    ]
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        image_url = data['data'][0]['imageURL']
        return {"image_url": image_url}
    else:
        raise Exception(f"Runware failed with status {response.status_code}: {response.text}")

# 3. Pollinations.ai Image Generation Function (Third Fallback - Free & Open)
def generate_with_pollinations(prompt: str):
    # Prompt ko URL encode karna zaroori hai taaki spaces ya special characters mein error na aaye
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
    
    # Check karne ke liye ki URL active hai ya nahi
    response = requests.get(image_url)
    if response.status_code == 200:
        return {"image_url": image_url}
    else:
        raise Exception(f"Pollinations failed with status {response.status_code}")


# Main Multi-API Fallback Endpoint
@app.post("/generate-image")
def generate_image(data: ImageRequest):
    prompt = data.prompt
    
    # Try 1: Segmind
    try:
        print("Trying Segmind (Primary)...")
        result = generate_with_segmind(prompt)
        return {"provider": "segmind", "result": result}
    except Exception as e:
        print(f"Segmind error/exhausted: {e}")
        
    # Try 2: Runware
    try:
        print("Fallback to Runware (Secondary)...")
        result = generate_with_runware(prompt)
        return {"provider": "runware", "result": result}
    except Exception as e:
        print(f"Runware error: {e}")

    # Try 3: Pollinations.ai
    try:
        print("Fallback to Pollinations.ai (Third)...")
        result = generate_with_pollinations(prompt)
        return {"provider": "pollinations", "result": result}
    except Exception as e:
        print(f"Pollinations error: {e}")
        
    # Agar teeno fail ho jayein
    raise HTTPException(status_code=500, detail="All image generation providers are currently unavailable.")


@app.get("/")
def home():
    return {"message": "Welcome to ManifestAI Backend with 3-Layer Multi-API Fallback ✨"}