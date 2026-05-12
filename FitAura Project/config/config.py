import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """FitAura Application Configuration"""
    
    # Application Info
    APP_NAME = 'FitAura'
    APP_TAGLINE = 'Your AI-Powered Style Companion'
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fitaura-secret-key-change-in-production-2025'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(basedir), 'data', 'fitaura.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Google Gemini API
    GEMINI_TEXT_API_KEY = os.environ.get('GEMINI_TEXT_API_KEY') or 'your-gemini-api-key-here'
    GEMINI_TEXT_MODEL = 'gemini-2.5-flash-lite'
    GEMINI_TEXT_MAX_TOKENS = int(os.getenv('GEMINI_TEXT_MAX_TOKENS', 2048))
    
    # Stable Diffusion (MohamedRashad/diffusion_fashion)
    SD_MODEL = 'MohamedRashad/diffusion_fashion'
    SD_NUM_INFERENCE_STEPS = 30
    SD_GUIDANCE_SCALE = 7.5
    SD_IMAGE_SIZE = 512
    
    # Image settings
    IMAGE_SAVE_PATH = os.path.join(os.path.dirname(basedir), 'static', 'generated_images')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(basedir), 'static', 'uploads')
    MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # Workflow settings
    MAX_IMAGES_PER_RECOMMENDATION = 1  # Generate 1 image per outfit
    MAX_QUESTIONS = 11
    MAX_RECOMMENDATIONS_PER_USER = 50
    
    # Validation settings
    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 50
    MIN_PASSWORD_LENGTH = 6
    
    # Guest user settings
    GUEST_SESSION_TIMEOUT = timedelta(hours=2)  # Guest data expires after 2 hours
    GUEST_MAX_GENERATIONS = 3  # Guests can generate max 3 outfits before signup prompt
    
    # AI Intent Detection
    INTENT_CONFIDENCE_THRESHOLD = 0.7
    
    @staticmethod
    def init_app(app):
        """Initialize application with config"""
        # Create necessary directories
        os.makedirs(Config.IMAGE_SAVE_PATH, exist_ok=True)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.join(os.path.dirname(basedir), 'data'), exist_ok=True)
        
    @staticmethod
    def allowed_file(filename):
        """Check if uploaded file has allowed extension"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS