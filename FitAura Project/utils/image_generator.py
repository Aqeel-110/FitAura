from google import genai
from config.config import Config
from PIL import Image
import os
from datetime import datetime

class GeminiImageGenerator:
    def __init__(self):
        # Set API key from config
        api_key = Config.GEMINI_API_KEY
        if api_key == 'your-gemini-api-key-here':
            raise ValueError("Please set GEMINI_API_KEY in environment variables or config.py")
        
        os.environ['GEMINI_API_KEY'] = api_key
        self.client = genai.Client(api_key=api_key)
        self.model = Config.IMAGE_MODEL
        self.output_folder = Config.UPLOAD_FOLDER
        
        # Create output folder if it doesn't exist
        os.makedirs(self.output_folder, exist_ok=True)
    
    def generate_outfit_images(self, preferences_dict, num_images=3):
        """
        Generate outfit images based on user preferences
        
        Args:
            preferences_dict: Dictionary with question-answer pairs
            num_images: Number of outfit images to generate
            
        Returns:
            List of image file paths
        """
        image_paths = []
        
        try:
            # Generate multiple outfit variations
            for i in range(num_images):
                prompt = self._build_image_prompt(preferences_dict, variation=i+1)
                image_path = self._generate_single_image(prompt, index=i+1)
                
                if image_path:
                    image_paths.append(image_path)
            
            return image_paths
        
        except Exception as e:
            print(f"Error generating outfit images: {str(e)}")
            return []
    
    def _build_image_prompt(self, preferences_dict, variation=1):
        """
        Build detailed image generation prompt
        
        Args:
            preferences_dict: Dictionary with question-answer pairs
            variation: Which variation to generate (1, 2, or 3)
            
        Returns:
            Formatted prompt string for image generation
        """
        # Extract key preferences
        occasion = preferences_dict.get('What is the occasion for your outfit?', 'casual')
        style = preferences_dict.get('What is your preferred style?', 'modern')
        colors = preferences_dict.get('What are your color preferences?', 'neutral colors')
        weather = preferences_dict.get('What is the weather condition?', 'moderate')
        
        variation_styles = {
            1: "main outfit",
            2: "alternative stylish outfit",
            3: "trendy variation outfit"
        }
        
        variation_text = variation_styles.get(variation, "outfit")
        
        prompt = f"""Create a professional fashion photograph of a complete {variation_text} for {occasion}.

Style: {style}
Colors: {colors}
Weather: {weather}

Requirements:
- Show a full outfit layout on a clean white background
- Include all clothing items clearly visible
- Professional fashion photography quality
- Modern, stylish presentation
- Well-coordinated colors and pieces
- Flat lay or mannequin display style

Make it look like a premium fashion catalog image."""
        
        return prompt
    
    def _generate_single_image(self, prompt, index=1):
        """
        Generate a single image using Gemini API
        
        Args:
            prompt: Image generation prompt
            index: Image index for filename
            
        Returns:
            Path to saved image or None
        """
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt]
            )
            
            # Save generated image
            for part in response.parts:
                if part.inline_data is not None:
                    image = part.as_image()
                    
                    # Generate unique filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"outfit_{timestamp}_{index}.png"
                    filepath = os.path.join(self.output_folder, filename)
                    
                    # Save image
                    image.save(filepath)
                    
                    # Return relative path for web access
                    return f"generated_images/{filename}"
            
            return None
        
        except Exception as e:
            print(f"Error generating single image: {str(e)}")
            return None
    
    def generate_custom_outfit_image(self, custom_prompt):
        """
        Generate image based on custom user prompt
        
        Args:
            custom_prompt: User's custom image generation request
            
        Returns:
            Path to saved image or None
        """
        try:
            enhanced_prompt = f"""Create a professional fashion photograph: {custom_prompt}

Requirements:
- High quality fashion photography
- Clean, professional presentation
- Well-lit and clearly visible
- Fashion catalog style"""
            
            return self._generate_single_image(enhanced_prompt, index=1)
        
        except Exception as e:
            print(f"Error generating custom image: {str(e)}")
            return None