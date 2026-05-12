from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_guest = db.Column(db.Boolean, default=False)  # NEW: Track guest users
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    preferences = db.relationship('Preference', backref='user', lazy=True, cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='user', lazy=True, cascade='all, delete-orphan')
    uploaded_images = db.relationship('UploadedImage', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}{"[Guest]" if self.is_guest else ""}>'


class Preference(db.Model):
    __tablename__ = 'preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(50), nullable=False)
    question_id = db.Column(db.Integer, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Preference Q{self.question_id}: {self.answer[:20]}>'


class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(50), nullable=False)
    
    # Workflow tracking
    workflow_type = db.Column(db.String(50), default='generate_new')  # NEW: generate_new, modify, from_analysis
    parent_recommendation_id = db.Column(db.Integer, db.ForeignKey('recommendations.id'), nullable=True)  # NEW: For modifications
    
    # Content
    recommendation_text = db.Column(db.Text, nullable=False)
    image_paths = db.Column(db.Text)  # JSON string of image paths
    
    # Stable Diffusion prompt storage (for modifications)
    sd_prompt = db.Column(db.Text)  # NEW: Store original SD prompt
    sd_parameters = db.Column(db.Text)  # NEW: Store SD params as JSON
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_saved = db.Column(db.Boolean, default=False)
    
    # Relationships
    modifications = db.relationship('Recommendation', 
                                   backref=db.backref('parent', remote_side=[id]),
                                   lazy=True)
    
    def __repr__(self):
        return f'<Recommendation {self.id} ({self.workflow_type}) for User {self.user_id}>'


class UploadedImage(db.Model):
    """NEW: Store uploaded images for analysis workflow"""
    __tablename__ = 'uploaded_images'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(50), nullable=False)
    
    # Image data
    image_path = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255))
    
    # Analysis results
    analysis_text = db.Column(db.Text)  # Gemini analysis results
    detected_items = db.Column(db.Text)  # JSON: detected clothing items
    
    # Metadata
    upload_type = db.Column(db.String(20))  # 'file' or 'camera'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UploadedImage {self.id} by User {self.user_id}>'


class ConversationHistory(db.Model):
    """NEW: Store conversation history for follow-up questions"""
    __tablename__ = 'conversation_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(50), nullable=False)
    
    # Message data
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    message = db.Column(db.Text, nullable=False)
    
    # Context
    context_type = db.Column(db.String(50))  # 'question_answer', 'followup', 'analysis', etc.
    related_recommendation_id = db.Column(db.Integer, db.ForeignKey('recommendations.id'), nullable=True)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ConversationHistory {self.role}: {self.message[:30]}>'