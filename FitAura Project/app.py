from flask import Flask, render_template, session
from flask_login import LoginManager
from config.config import Config
from models.database import db, User
from routes.auth import auth_bp
from routes.chatbot import chatbot_bp
from routes.recommendations import recommendations_bp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(chatbot_bp, url_prefix='/chatbot')
app.register_blueprint(recommendations_bp, url_prefix='/recommendations')

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

# Context processor for global template variables
@app.context_processor
def inject_globals():
    """Inject global variables into all templates"""
    from flask_login import current_user
    
    is_guest = session.get('is_guest', False) and not current_user.is_authenticated
    
    return {
        'app_name': Config.APP_NAME,
        'app_tagline': Config.APP_TAGLINE,
        'is_guest': is_guest,
        'guest_id': session.get('guest_id') if is_guest else None
    }

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    return render_template('403.html'), 403

# Session configuration
@app.before_request
def make_session_permanent():
    """Make sessions permanent for better UX"""
    session.permanent = True

# Create database tables and initialize
with app.app_context():
    # Initialize config
    Config.init_app(app)
    
    # Create all database tables
    db.create_all()
    print("✅ Database tables created successfully!")
    
    # Print directory structure
    print(f"\n📁 Directory structure:")
    print(f"   - Database: {Config.SQLALCHEMY_DATABASE_URI}")
    print(f"   - Images: {Config.IMAGE_SAVE_PATH}")
    print(f"   - Uploads: {Config.UPLOAD_FOLDER}")

if __name__ == '__main__':
    # Get configuration from environment
    debug_mode = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.environ.get('FLASK_PORT', 5000))
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    
    print(f"\n{'='*70}")
    print(f"  ✨ {Config.APP_NAME} - {Config.APP_TAGLINE}")
    print(f"{'='*70}")
    print(f"  🌐 Server: http://{host}:{port}")
    print(f"  🔧 Debug: {debug_mode}")
    print(f"  💾 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"  🎨 AI Models:")
    print(f"     - Text: {Config.GEMINI_TEXT_MODEL} (Gemini)")
    print(f"     - Images: {Config.SD_MODEL} (Stable Diffusion)")
    print(f"  👥 User Modes:")
    print(f"     - Registered users: Full features + save")
    print(f"     - Guest users: All features (browser storage only)")
    print(f"{'='*70}\n")
    
    print("🚀 Starting FitAura server...\n")
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode
    )