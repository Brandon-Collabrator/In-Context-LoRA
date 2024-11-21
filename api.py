import os
import time
import requests
import json
from PIL import Image
from io import BytesIO
import base64

# API Key
api_key = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJsaXUgamlueGl1IiwiVXNlck5hbWUiOiJsaXUgamlueGl1IiwiQWNjb3VudCI6IiIsIlN1YmplY3RJRCI6IjE4NTczMzUzNDg3MDc3MjU0MjUiLCJQaG9uZSI6IiIsIkdyb3VwSUQiOiIxODU3MzM1MzQ4Njk5MzM2ODE3IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiamlueGl1bGl1MDYyOEBnbWFpbC5jb20iLCJDcmVhdGVUaW1lIjoiMjAyNC0xMS0yMSAwNzozMjo0MyIsIlRva2VuVHlwZSI6MSwiaXNzIjoibWluaW1heCJ9.GRChm_7L0OzidgtrDkMrbQUwJ979BsL4uGDykhfZCD11V2hlzHYs2gGVL01ofI5Axeiw0IViynVoMlIO-RI0Wyhh7bfFZN0OSHwNK6KIWUzNX7pAsyOedkvifUlICWG3Y-A4kouvOBnd4MifbqRFw3knFfpM_fxNxoCs8ymVC5e8f-qO2IfbZd-fAAXSPfpgAFqDgWTxQzwzQAQtzO5shVb5nDuXllbseHvniNFsldv_34xBD2ifm4_BTRZOdP8w68dSNCmLSeVhuKqF_Y-4a4oO4CS2if8shQs7JQGGFTNMlfhmnfGH5Y94JEm7q3N5SDfixCgQo6cyPPGIZR0rbA"

# Parameters
# prompt = "A young African male (dark-skinned, wearing casual clothes) walks through a lively marketplace in Africa, surrounded by colorful stalls and bustling street activity. He takes out his smartphone to make a payment."
prompt = ""
model = "video-01"
input_image_path = "/ssd1/jinxiu/PhysVideoGen/In-Context-LoRA/flux-dev.png"  # Local path of the image
input_image_path = "https://github.com/black-forest-labs/flux/raw/main/assets/grid.jpg"
input_image_path = "https://github.com/Brandon-Collabrator/temp_input_image/blob/main/Palmpay.png?raw=true"
input_image_path = "https://github.com/Brandon-Collabrator/temp_input_image/blob/main/palmpay.jpg"
input_image_path = "https://github.com/Brandon-Collabrator/temp_input_image/blob/main/palmpay.jpg?raw=true"
output_file_name = "output.mp4"  # Path to save the generated video

# Function to fetch the image from the URL or local file and resize it
def resize_image(image_path: str, min_size=300, aspect_ratio_range=(2/5, 5/2)):
    # Open image
    if image_path.startswith("http"):
        response = requests.get(image_path)
        image = Image.open(BytesIO(response.content))
    else:
        image = Image.open(image_path)
    
    width, height = image.size
    
    # Check aspect ratio
    aspect_ratio = width / height
    if aspect_ratio < aspect_ratio_range[0] or aspect_ratio > aspect_ratio_range[1]:
        raise ValueError(f"Image aspect ratio {aspect_ratio} is out of range {aspect_ratio_range}")

    # Resize the image if the shorter side is less than min_size (300px)
    if width < height:
        if width < min_size:
            new_width = min_size
            new_height = int(min_size * height / width)
            image = image.resize((new_width, new_height))
    else:
        if height < min_size:
            new_height = min_size
            new_width = int(min_size * width / height)
            image = image.resize((new_width, new_height))

    # Save the resized image to a temporary location
    temp_path = "/tmp/resized_image.jpg"
    image.save(temp_path)
    return temp_path

# Function to encode an image to base64 (for API request)
def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Submit the video generation task
def invoke_video_generation() -> str:
    print("------ Submitting Video Generation Task ------")

    # Resize the input image to meet the size requirement
    resized_image_path = resize_image(input_image_path, min_size=300)
    first_frame_image = encode_image_to_base64(resized_image_path)

    # Prepare the payload for the API request
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "prompt_optimizer": True,
        "first_frame_image": input_image_path
    })

    headers = {
        'authorization': f'Bearer {api_key}',
        'content-type': 'application/json',
    }

    # Make the API request
    url = "https://api.minimaxi.chat/v1/video_generation"
    response = requests.post(url, headers=headers, data=payload)
    response_data = response.json()

    if response_data.get("base_resp", {}).get("status_code") == 0:
        task_id = response_data["task_id"]
        print(f"Task submitted successfully. Task ID: {task_id}")
        return task_id
    else:
        raise Exception(f"Failed to submit task: {response_data}")

# Query the video generation task status
def query_video_generation(task_id: str):
    url = f"https://api.minimaxi.chat/v1/query/video_generation?task_id={task_id}"
    headers = {'authorization': f'Bearer {api_key}'}
    
    response = requests.get(url, headers=headers)
    response_data = response.json()
    status = response_data.get("status", "Unknown")

    if status == 'Queueing':
        print("...In the queue...")
        return "", 'Queueing'
    elif status == 'Processing':
        print("...Generating...")
        return "", 'Processing'
    elif status == 'Success':
        return response_data['file_id'], "Finished"
    elif status == 'Fail':
        return "", "Fail"
    else:
        return "", "Unknown"

# Download the generated video
def fetch_video_result(file_id: str):
    print("------ Downloading Generated Video ------")
    url = f"https://api.minimaxi.chat/v1/files/retrieve?file_id={file_id}"
    headers = {'authorization': f'Bearer {api_key}'}
    
    response = requests.get(url, headers=headers)
    response_data = response.json()
    
    download_url = response_data['file']['download_url']
    print(f"Download URL: {download_url}")
    
    # Save video locally
    video_data = requests.get(download_url).content
    with open(output_file_name, 'wb') as f:
        f.write(video_data)
    print(f"Video saved at: {os.path.abspath(output_file_name)}")

# Main execution
if __name__ == '__main__':
    try:
        task_id = invoke_video_generation()
        print("------ Video Generation Task Submitted ------")
        
        # Polling to check task status
        while True:
            time.sleep(10)  # Adjust polling interval as needed
            file_id, status = query_video_generation(task_id)
            
            if file_id:
                fetch_video_result(file_id)
                print("------ Video Generation Successful ------")
                break
            elif status in ["Fail", "Unknown"]:
                print("------ Video Generation Failed ------")
                break
    except Exception as e:
        print(f"Error: {e}")
