# test_hf_images.py
from utils.gemini_handler import get_gemini_handler

def test_image_generation():
    gemini = get_gemini_handler()
    
    test_prompt = "A modern casual outfit: black jeans, white t-shirt, leather jacket, sneakers"
    
    print("Testing Hugging Face image generation...")
    image_paths = gemini.generate_outfit_images(test_prompt, num_images=1)
    
    if image_paths:
        print(f"✅ Success! Generated image: {image_paths[0]}")
    else:
        print("❌ Failed to generate image")

if __name__ == "__main__":
    test_image_generation()