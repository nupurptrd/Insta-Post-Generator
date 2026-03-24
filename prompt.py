import os
import re
import base64
from io import BytesIO
import sys

from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

# Load .env (expects a file with a line like: api_key=sk-...)
load_dotenv()

# Try both common env var names
API_KEY = os.getenv("api_key") 
#print(API_KEY)

if not API_KEY:
    print("❌ API key not found. Add 'api_key=YOUR_KEY' to a .env file or set API_KEY in your environment.")
    sys.exit(1)

print(f"🔐 Key loaded: {API_KEY[:5]}****")

# Initialize the genai client
client = genai.Client(api_key=API_KEY)


def sanitize_filename(s: str) -> str:
    """Sanitize string to be safe for filenames."""
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)

# # Insert the specific Brand Logo image here
# # 1. Load the logo from your PC
# logo_path = "Given Logos\Sunbots.jpg"
# try:
#     logo_image = Image.open(logo_path)
#     print("Image Uploaded")
# except FileNotFoundError:
#     print(f"Error: {logo_path} not found!")
#     exit()

def build_prompt(config: dict) -> str:
    return (
        f"Act as a Lead Social Media Strategist,Create a professional Instagram post for {config['brand_name']} "
        f"styled like the official @{config['brand_name']} Instagram feed "
        f"Brand Logo: Use the Given logo jpg file OR the logo watermark of the {config['brand_name']}. "
        f"Visual Strategy: Dominant {config['theme_1']}, {config['theme_2']}. "
        f"Theme: MAtch the theme with the majority posts present at the official instagram page of the {config['brand_name']} "
        f"Color Palette: {config['colors']}. Lighting: {config['lighting']}. "
        f"Background Style: {config['bg_style']}. "
        f"Hero Subject: Center {config['product_name']}, photorealistic, ultra-detailed, {config['placement']}, "
        f"integrated into a {config['occasion']} context. "
        f"Visual Details: No clutter, no text overlapping, subtle sparkles, "
        f"dynamic composition with negative space. High-end e-commerce photography, "
        f"1:1 square aspect ratio, 8K resolution, Professional studio quality like {config['example_brand']}. "
        f"Include centered text overlay related to {config['occasion']}: 'Let's Celebrate this {config['occasion'].capitalize()} with {config['brand_name']}'."
    )


def save_generated_image(generated_image, save_path: str):
    """
    Tries multiple ways to obtain an image from the SDK response object:
    - If SDK returns a PIL Image object at generated_image.image, use it.
    - Otherwise look for base64 fields and decode.
    """
    # 1) Direct PIL Image object (some SDKs yield this)
    if hasattr(generated_image, "image") and isinstance(generated_image.image, Image.Image):
        img = generated_image.image
        img.save(save_path)
        return save_path

    # 2) Common base64 fields (try a few common names)
    b64_candidates = [
        getattr(generated_image, "b64_json", None),
        getattr(generated_image, "image_base64", None),
        getattr(generated_image, "base64", None),
        getattr(generated_image, "data", None),
    ]
    for b64 in b64_candidates:
        if b64:
            try:
                img_bytes = base64.b64decode(b64)
                img = Image.open(BytesIO(img_bytes))
                img.save(save_path)
                return save_path
            except Exception:
                pass

    # 3) If the SDK returned raw bytes on an attribute
    raw_candidates = [
        getattr(generated_image, "image_bytes", None),
        getattr(generated_image, "bytes", None),
    ]
    for raw in raw_candidates:
        if raw:
            try:
                img = Image.open(BytesIO(raw))
                img.save(save_path)
                return save_path
            except Exception:
                pass

    raise ValueError("Could not extract image from the model response object.")


def main():
    print("--- 📱 Instagram Post Generator ---")

    config = {
        "brand_name": "BoAt",
        "product_name": "Earbuds",
        "occasion": "Holi",
        "brand_logo": " watermark of logo of the brand_name given OR Given LOGO Image",
        "theme_1": "minimalist luxury",
        "theme_2": "vibrant lifestyle aesthetic",
        "colors": "brand_name signature colours taken from majority of the Brands official Instagram Page",
        "lighting": "cinematic studio lighting with high contrast",
        "bg_style": "Match with most of the posts of the Brand's Instagram Posts",
        "placement": "floating elegantly in mid-air",
        "example_brand": "Apple's clean product shots",
    }
    
    prompt_text = build_prompt(config)
    print(f"\n🚀 Generating image for {config['brand_name']}...")

    try:
        print(f"🚀 Generating image with gemini-2.5-flash-image...")
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt_text],    # Use 'prompt' as a string, not a list in 'contents'
            # contents=[prompt_text, logo_image],  #Use this line when you have logo to upload from your side
            config=types.GenerateContentConfig(
                # This is the critical part: telling the model to output an image
                response_modalities=["IMAGE"], 
                image_config=types.ImageConfig(
                    aspect_ratio="1:1"
                )
            )
        )
        # Process the image from the response parts
        image_found = False
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                # part.as_image() is a helper in the SDK that returns a PIL Image
                img = part.as_image() 
                safe_name = sanitize_filename(f"post_{config['brand_name']}.png")
                img.save(safe_name)
                print(f"✅ Success! Post saved as: {safe_name}")
                image_found = True
                break
            
        if not image_found:
            print("❌ Model responded but no image data was found in the parts.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()

