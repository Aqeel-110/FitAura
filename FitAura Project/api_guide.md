# 🔑 Separate API Keys Setup Guide

## Why Use Separate API Keys?

This project uses **TWO separate Google Gemini API keys** for optimal performance and cost management:

### 1. **Text API Key** (`GEMINI_TEXT_API_KEY`)
- **Model**: `gemini-2.5-flash-lite`
- **Purpose**: Fast, efficient text generation
- **Used For**:
  - Chatbot conversations
  - Outfit recommendations (text descriptions)
  - Question responses
  - General text generation
- **Benefits**:
  - Lower cost per token
  - Faster response times
  - Optimized for conversational AI

### 2. **Image API Key** (`GEMINI_IMAGE_API_KEY`)
- **Model**: `gemini-2.5-flash-image`  
- **Purpose**: High-quality image generation
- **Used For**:
  - Generating outfit visualization images
  - Creating fashion mockups
  - Visual representations of recommendations
- **Benefits**:
  - Better image quality
  - Specialized for image tasks
  - Separate rate limits

---

## Configuration

### Step 1: Get Your API Keys

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create **TWO separate API keys**:
   - One for text generation
   - One for image generation

### Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add BOTH API keys:

```env
# Flask Configuration
SECRET_KEY=your-random-secret-key-12345

# Google Gemini API - SEPARATE KEYS
GEMINI_TEXT_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXX  # Your text API key
GEMINI_IMAGE_API_KEY=AIzaSyYYYYYYYYYYYYYYYYYYYYYYYYYYY  # Your image API key

# Application Settings
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
```

---

## How It Works

### Text Generation Flow

```python
# In gemini_handler.py
self.text_client = genai.Client(api_key=text_api_key)  # Separate client

# When generating text recommendations:
response = self.text_client.models.generate_content(
    model="gemini-2.5-flash-lite",  # Text model
    contents=prompt
)
```

### Image Generation Flow

```python
# In gemini_handler.py
self.image_client = genai.Client(api_key=image_api_key)  # Separate client

# When generating outfit images:
response = self.image_client.models.generate_content(
    model="gemini-2.5-flash-image",  # Image model
    contents=[image_prompt]
)
```

---

## Code Implementation

### Config (config/config.py)

```python
class Config:
    # Separate API keys
    GEMINI_TEXT_API_KEY = os.environ.get('GEMINI_TEXT_API_KEY')
    GEMINI_IMAGE_API_KEY = os.environ.get('GEMINI_IMAGE_API_KEY')
    
    # Separate models
    GEMINI_TEXT_MODEL = 'gemini-2.5-flash-lite'
    GEMINI_IMAGE_MODEL = 'gemini-2.5-flash-image'
```

### Gemini Handler (utils/gemini_handler.py)

```python
class GeminiHandler:
    def __init__(self):
        # Initialize SEPARATE clients
        self.text_client = genai.Client(api_key=Config.GEMINI_TEXT_API_KEY)
        self.image_client = genai.Client(api_key=Config.GEMINI_IMAGE_API_KEY)
    
    def generate_text_response(self, prompt):
        # Use TEXT client
        return self.text_client.models.generate_content(
            model=self.text_model,
            contents=prompt
        )
    
    def generate_outfit_images(self, image_prompt):
        # Use IMAGE client
        return self.image_client.models.generate_content(
            model=self.image_model,
            contents=[image_prompt]
        )
```

---

## Benefits of This Approach

### ✅ **Cost Optimization**
- Text API charges less per token
- Image API charges only for images
- No wasted credits

### ✅ **Better Performance**
- Text model is faster for chat
- Image model produces better quality images
- Each optimized for its task

### ✅ **Separate Rate Limits**
- Text API won't block image generation
- Image API won't slow down chat
- Independent scaling

### ✅ **Better Monitoring**
- Track text usage separately
- Track image generation separately
- Easier to identify bottlenecks

---

## Testing Your Setup

Run this test to verify both API keys work:

```bash
python test_api_keys.py
```

Expected output:
```
✅ Gemini Handler initialized with SEPARATE API keys
   📝 Text Model: gemini-2.5-flash-lite (using text API key)
   🎨 Image Model: gemini-2.5-flash-image (using image API key)

Testing text generation...
✅ Text API works!

Testing image generation...
✅ Generated image 1/1: outfit_20250101_120000_1.png
✅ Image API works!
```

---

## Troubleshooting

### Error: "GEMINI_TEXT_API_KEY not configured"
- Check your `.env` file exists
- Verify `GEMINI_TEXT_API_KEY` is set
- Make sure there are no spaces around the `=` sign

### Error: "GEMINI_IMAGE_API_KEY not configured"
- Check your `.env` file exists
- Verify `GEMINI_IMAGE_API_KEY` is set
- Ensure you created a separate API key for images

### Images not generating
- Verify image API key has proper permissions
- Check `static/generated_images/` directory exists
- Ensure sufficient API quota

---

## API Key Security

⚠️ **IMPORTANT**: Never commit your `.env` file to git!

The `.gitignore` file already includes:
```
.env
*.env
```

Always use environment variables in production:
```bash
export GEMINI_TEXT_API_KEY="your-key-here"
export GEMINI_IMAGE_API_KEY="your-key-here"
```

---

## Summary

- **2 API Keys** = Better performance + Lower costs
- **Text Key** → Chat & recommendations
- **Image Key** → Outfit visualizations
- **Both required** for full functionality
- **Keep them separate** for optimal results