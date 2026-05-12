"""
FitAura AI Handler - Gemini for Text + Stable Diffusion for Images
Includes: Intent Router, Image Analysis, Prompt Modification
"""

from google import genai
from diffusers import StableDiffusionPipeline
import torch
import os
import json
import base64
from config.config import Config
from datetime import datetime
from PIL import Image
import io

class FitAuraAI:
    """Main AI handler for FitAura with intent routing"""
    
    def __init__(self):
        """Initialize Gemini and Stable Diffusion"""
        # Initialize Gemini for text
        text_api_key = Config.GEMINI_TEXT_API_KEY
        
        if not text_api_key or text_api_key == 'your-gemini-api-key-here':
            raise ValueError("GEMINI_TEXT_API_KEY not configured")
        
        self.text_client = genai.Client(api_key=text_api_key)
        self.text_model = Config.GEMINI_TEXT_MODEL
        
        # Initialize Stable Diffusion
        print("🔄 Loading Stable Diffusion model...")
        try:
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                Config.SD_MODEL,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.pipeline.to(device)
            
            if torch.cuda.is_available():
                self.pipeline.enable_attention_slicing()
            
            print(f"✅ Stable Diffusion loaded on {device}")
        except Exception as e:
            print(f"❌ Error loading Stable Diffusion: {e}")
            self.pipeline = None
        
        self._ensure_directories()
        print(f"✅ FitAura AI initialized")
    
    def _ensure_directories(self):
        """Create necessary directories"""
        for path in [Config.IMAGE_SAVE_PATH, Config.UPLOAD_FOLDER]:
            os.makedirs(path, exist_ok=True)
    
    # ========== INTENT ROUTER ==========
    
    def detect_intent(self, user_message, conversation_context=None):
        """
        Detect user intent to route to correct workflow
        Returns: dict with 'intent' and 'confidence'
        
        Intents:
        - generate_new: User wants new outfit (needs 11 questions)
        - modify_outfit: User wants to modify existing outfit
        - followup_question: User asking questions about generated outfit
        - analyze_image: User wants to analyze uploaded image
        - generate_from_image: User wants outfit based on uploaded image
        """
        try:
            context_str = f"\n\nConversation context:\n{conversation_context}" if conversation_context else ""
            
            prompt = f"""You are an intent classifier for a fashion AI assistant called FitAura.

Analyze this user message and classify their intent into ONE of these categories:

1. **generate_new**: User wants to create a brand NEW outfit from scratch
   Examples: "I need an outfit", "create outfit for me", "what should I wear", "I want new clothes recommendation"

2. **modify_outfit**: User wants to CHANGE/MODIFY an existing outfit
   Examples: "change the color to blue", "make it more casual", "different shoes", "try red instead"

3. **followup_question**: User asking QUESTIONS about an outfit they already have
   Examples: "what hairstyle matches", "can I wear this to wedding", "what occasion is this for"

4. **analyze_image**: User wants to ANALYZE an image they uploaded
   Examples: "analyze this outfit", "what do you think of this", "give feedback on my clothes"

5. **generate_from_image**: User wants to CREATE a NEW outfit BASED ON their uploaded image
   Examples: "create similar outfit", "make outfit like this", "generate based on this image"

User message: "{user_message}"{context_str}

Respond with ONLY a JSON object:
{{
    "intent": "intent_name",
    "confidence": 0.95,
    "reasoning": "brief explanation"
}}"""
            
            response = self.text_client.models.generate_content(
                model=self.text_model,
                contents=prompt
            )
            
            if response and response.text:
                # Parse JSON response
                result_text = response.text.strip()
                # Remove markdown code blocks if present
                if result_text.startswith('```'):
                    result_text = result_text.split('```')[1]
                    if result_text.startswith('json'):
                        result_text = result_text[4:]
                    result_text = result_text.strip()
                
                result = json.loads(result_text)
                print(f"🎯 Intent detected: {result['intent']} (confidence: {result['confidence']})")
                return result
            
            return {'intent': 'generate_new', 'confidence': 0.5, 'reasoning': 'Default fallback'}
            
        except Exception as e:
            print(f"❌ Error in intent detection: {e}")
            return {'intent': 'generate_new', 'confidence': 0.5, 'reasoning': 'Error fallback'}
    
    # ========== TEXT GENERATION ==========
    
    def generate_text_response(self, prompt, max_tokens=None):
        """Generate text response using Gemini"""
        try:
            if max_tokens is None:
                max_tokens = Config.GEMINI_TEXT_MAX_TOKENS
            
            response = self.text_client.models.generate_content(
                model=self.text_model,
                contents=prompt
            )
            
            if response and response.text:
                return response.text.strip()
            return "I apologize, but I couldn't generate a response. Please try again."
        except Exception as e:
            print(f"❌ Error in text generation: {e}")
            return f"Error: {str(e)}"
    
    # ========== IMAGE GENERATION (STABLE DIFFUSION) ==========
    
    def _optimize_prompt_for_clip(self, prompt, max_words=50):
        """Optimize prompt to stay under CLIP's 77 token limit"""
        fashion_keywords = {
            'colors': ['navy', 'blue', 'white', 'black', 'grey', 'charcoal', 'red', 'green', 
                      'yellow', 'pink', 'purple', 'brown', 'beige', 'cream'],
            'clothing': ['blazer', 'shirt', 'trousers', 'dress', 'skirt', 'jacket', 'jeans', 
                        'shorts', 'sweater', 'coat', 'top', 'blouse', 'shoes', 'boots'],
            'styles': ['casual', 'formal', 'professional', 'elegant', 'modern', 'vintage', 
                      'sporty', 'minimalist', 'classic']
        }
        
        prompt_lower = prompt.lower()
        parts = []
        
        # Extract style
        for style in fashion_keywords['styles']:
            if style in prompt_lower:
                parts.append(style)
                break
        
        # Extract clothing (max 4)
        for item in fashion_keywords['clothing']:
            if item in prompt_lower and len(parts) < 8:
                parts.append(item)
        
        # Extract colors (max 3)
        for color in fashion_keywords['colors']:
            if color in prompt_lower and len(parts) < 12:
                parts.append(color)
        
        # Add essential keywords
        parts.extend(['white background', 'professional fashion photography'])
        
        optimized = ', '.join(parts) if parts else 'professional fashion outfit, white background'
        
        print(f"✂️ Optimized prompt: {optimized}")
        return optimized
    
    def generate_outfit_images(self, image_prompt, num_images=1):
        """Generate outfit images using Stable Diffusion"""
        try:
            if self.pipeline is None:
                print("❌ Stable Diffusion not available")
                return [], None
            
            num_images = min(num_images, Config.MAX_IMAGES_PER_RECOMMENDATION)
            image_paths = []
            
            print(f"🔄 Generating {num_images} images...")
            
            # Optimize prompt for CLIP
            optimized_prompt = self._optimize_prompt_for_clip(image_prompt)
            
            for i in range(num_images):
                try:
                    with torch.no_grad():
                        result = self.pipeline(
                            optimized_prompt,
                            num_inference_steps=Config.SD_NUM_INFERENCE_STEPS,
                            guidance_scale=Config.SD_GUIDANCE_SCALE,
                            height=Config.SD_IMAGE_SIZE,
                            width=Config.SD_IMAGE_SIZE
                        )
                        image = result.images[0]
                    
                    # Save image
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    filename = f"outfit_{timestamp}_{i+1}.png"
                    filepath = os.path.join(Config.IMAGE_SAVE_PATH, filename)
                    image.save(filepath, format='PNG', optimize=True)
                    
                    relative_path = f"/static/generated_images/{filename}"
                    image_paths.append(relative_path)
                    
                    print(f"✅ Generated image {i+1}/{num_images}: {filename}")
                    
                except Exception as img_error:
                    print(f"❌ Error generating image {i+1}: {img_error}")
                    continue
            
            return image_paths, optimized_prompt
            
        except Exception as e:
            print(f"❌ Error in image generation: {e}")
            return [], None
    
    # ========== IMAGE ANALYSIS ==========
    
    def analyze_uploaded_image(self, image_path_or_data, analysis_type='general'):
        """
        Analyze uploaded image using Gemini Vision
        analysis_type: 'general', 'outfit_feedback', 'style_detection'
        """
        try:
            # Load image
            if isinstance(image_path_or_data, str):
                with open(image_path_or_data, 'rb') as f:
                    image_data = f.read()
            else:
                image_data = image_path_or_data
            
            # Convert to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create analysis prompt based on type
            prompts = {
                'general': """Analyze this outfit image and provide:
1. Clothing items visible
2. Colors and patterns
3. Style category (casual, formal, sporty, etc.)
4. Occasion suitability
5. Overall impression""",
                
                'outfit_feedback': """As a fashion expert, analyze this outfit and provide:
1. What works well
2. What could be improved
3. Styling suggestions
4. Complementary accessories
5. Overall rating (1-10)""",
                
                'style_detection': """Detect and list:
1. All clothing items (be specific)
2. Exact colors
3. Patterns/prints
4. Fabric types (if visible)
5. Style keywords for replication"""
            }
            
            prompt = prompts.get(analysis_type, prompts['general'])
            
            # Call Gemini with image
            response = self.text_client.models.generate_content(
                model='gemini-2.5-flash',  # Vision model
                contents=[
                    {
                        'parts': [
                            {'text': prompt},
                            {
                                'inline_data': {
                                    'mime_type': 'image/png',
                                    'data': image_base64
                                }
                            }
                        ]
                    }
                ]
            )
            
            if response and response.text:
                return response.text.strip()
            return "Could not analyze image."
            
        except Exception as e:
            print(f"❌ Error analyzing image: {e}")
            return f"Error analyzing image: {str(e)}"
    
    def extract_outfit_features_from_image(self, image_path_or_data):
        """Extract features to create similar outfit"""
        analysis = self.analyze_uploaded_image(image_path_or_data, 'style_detection')
        
        prompt = f"""Based on this outfit analysis, create a SHORT description for image generation:

{analysis}

Generate a concise description (under 50 words) suitable for creating a similar outfit.
Include: main clothing items, colors, style.
Format: "style, item1, item2, item3, color1, color2"

Example: "casual summer outfit, white t-shirt, blue jeans, sneakers, denim blue, white, red"
"""
        
        description = self.generate_text_response(prompt, max_tokens=100)
        return description
    
    # ========== PROMPT MODIFICATION ==========
    
    def modify_sd_prompt(self, original_prompt, modification_request):
        """Modify existing Stable Diffusion prompt based on user request"""
        try:
            prompt = f"""You are modifying a Stable Diffusion prompt for fashion outfit generation.

Original prompt: "{original_prompt}"

User wants to change: "{modification_request}"

Generate a NEW short prompt (under 50 words) with the modification applied.
Keep the same format: comma-separated keywords.

Examples:
- If user says "change to blue", replace color words with "blue"
- If user says "make it formal", replace "casual" with "formal"
- If user says "different shoes", change shoe-related words

Respond with ONLY the new prompt, nothing else."""
            
            modified = self.generate_text_response(prompt, max_tokens=100)
            return modified.strip()
            
        except Exception as e:
            print(f"❌ Error modifying prompt: {e}")
            return original_prompt
    
    # ========== OUTFIT RECOMMENDATION ==========
    
    def generate_outfit_recommendation(self, preferences_dict):
        """Generate outfit description from user preferences"""
        template = """You are a fashion stylist. Based on preferences, create ONE outfit description (2-3 sentences).

PREFERENCES:
"""
        for key, value in preferences_dict.items():
            template += f"• {key}: {value}\n"
        
        template += """
Describe ONE complete outfit with:
- Specific items (top, bottom, shoes)
- Exact colors
- One accessory
- Why it works

Keep it SHORT - exactly 2-3 sentences."""
        
        return self.generate_text_response(template, max_tokens=150)
    
    # ========== FOLLOWUP CHAT ==========
    
    def answer_followup_question(self, question, outfit_context, image_path=None):
        """Answer questions about generated outfit"""
        context = f"The outfit is: {outfit_context}"
        
        if image_path:
            # Include image analysis if available
            context += f"\n\nImage analysis: {self.analyze_uploaded_image(image_path, 'general')}"
        
        prompt = f"""{context}

User question: "{question}"

Provide a helpful, specific answer about this outfit."""
        
        return self.generate_text_response(prompt, max_tokens=500)


# Singleton instance
_fitaura_ai = None

def get_fitaura_ai():
    """Get or create FitAuraAI singleton"""
    global _fitaura_ai
    if _fitaura_ai is None:
        _fitaura_ai = FitAuraAI()
    return _fitaura_ai