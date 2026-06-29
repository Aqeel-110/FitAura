# 🔑 API Setup Guide

## How FitAura Handles AI

FitAura uses **two separate AI systems** for text and image generation:

| Task | Technology | Requires API Key? |
|---|---|---|
| Chat, recommendations, intent detection | Google Gemini 2.5 Flash Lite | ✅ Yes |
| Outfit image generation | Stable Diffusion (local) | ❌ No |

---

## Text Generation - Google Gemini

### What it's used for
- Chatbot conversations
- Outfit recommendation descriptions
- Intent detection (routing user messages to the correct workflow)
- Follow-up question answers
- Outfit modification descriptions

### Model
`gemini-2.5-flash-lite`

### Setup

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in and create an API key
3. Add it to your `.env` file:

```env
SECRET_KEY=your-random-secret-key-12345
GEMINI_TEXT_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXX

FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5000
FLASK_HOST=0.0.0.0
```

### How it works in code

```python
# config/config.py
GEMINI_TEXT_API_KEY = os.environ.get('GEMINI_TEXT_API_KEY')
GEMINI_TEXT_MODEL = 'gemini-2.5-flash-lite'

# utils/gemini_handler.py
self.text_client = genai.Client(api_key=Config.GEMINI_TEXT_API_KEY)

response = self.text_client.models.generate_content(
    model=self.text_model,
    contents=prompt
)
```

---

## Image Generation - Stable Diffusion

### What it's used for
- Generating outfit visualization images
- Creating fashion mockups from text descriptions
- Producing visual output for the modify outfit workflow

### Model
`MohamedRashad/diffusion_fashion` (runs locally via HuggingFace `diffusers`)

### No API key needed
Stable Diffusion runs locally on your machine. The model is downloaded automatically on first run via HuggingFace. No account or API key required.

### Requirements
- A GPU with CUDA is strongly recommended for reasonable speed
- The model loads into memory on startup - this may take a minute the first time

### How it works in code

```python
# config/config.py
SD_MODEL = 'MohamedRashad/diffusion_fashion'
SD_NUM_INFERENCE_STEPS = 30
SD_GUIDANCE_SCALE = 7.5
SD_IMAGE_SIZE = 512
MAX_IMAGES_PER_RECOMMENDATION = 1

# utils/gemini_handler.py
from diffusers import StableDiffusionPipeline
import torch

self.pipeline = StableDiffusionPipeline.from_pretrained(
    Config.SD_MODEL,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
)
self.pipeline.to("cuda" if torch.cuda.is_available() else "cpu")
```

Generated images are saved locally to `static/generated_images/` and served by Flask.

---

## Troubleshooting

### "GEMINI_TEXT_API_KEY not configured"
- Check your `.env` file exists in the project root
- Make sure there are no spaces around the `=` sign
- Verify the key is valid in Google AI Studio

### Images not generating
- Check that `static/generated_images/` directory exists (created automatically on startup)
- If on CPU, generation will be slow - this is expected
- Check console output for Stable Diffusion loading errors on startup

### Stable Diffusion loading error
- Run `pip install diffusers torch transformers accelerate` to ensure dependencies are installed
- On first run, the model downloads from HuggingFace - make sure you have internet access and enough disk space (~2-4 GB)

---

## Security

⚠️ **Never commit your `.env` file to git.**

The `.gitignore` should already include:
```
.env
*.env
```

In production, set environment variables directly:
```bash
export GEMINI_TEXT_API_KEY="your-key-here"
```
