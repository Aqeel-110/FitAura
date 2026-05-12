from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from models.database import db, User
from config.config import Config
import re
import uuid

auth_bp = Blueprint('auth', __name__)

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_username(username):
    """Validate username"""
    if len(username) < Config.MIN_USERNAME_LENGTH or len(username) > Config.MAX_USERNAME_LENGTH:
        return False
    return re.match(r'^[a-zA-Z0-9_]+$', username) is not None

def is_valid_password(password):
    """Validate password"""
    return len(password) >= Config.MIN_PASSWORD_LENGTH

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user signup"""
    if request.method == 'GET':
        return render_template('signup.html')
    
    data = request.get_json() if request.is_json else request.form
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    
    # Validation
    errors = []
    
    if not username:
        errors.append('Username is required')
    elif not is_valid_username(username):
        errors.append(f'Username must be {Config.MIN_USERNAME_LENGTH}-{Config.MAX_USERNAME_LENGTH} characters')
    
    if not email:
        errors.append('Email is required')
    elif not is_valid_email(email):
        errors.append('Invalid email format')
    
    if not password:
        errors.append('Password is required')
    elif not is_valid_password(password):
        errors.append(f'Password must be at least {Config.MIN_PASSWORD_LENGTH} characters')
    
    if password != confirm_password:
        errors.append('Passwords do not match')
    
    if errors:
        if request.is_json:
            return jsonify({'success': False, 'errors': errors}), 400
        for error in errors:
            flash(error, 'error')
        return render_template('signup.html')
    
    # Check if user exists
    if User.query.filter_by(email=email).first():
        error = 'Email already registered'
        if request.is_json:
            return jsonify({'success': False, 'errors': [error]}), 400
        flash(error, 'error')
        return render_template('signup.html')
    
    if User.query.filter_by(username=username).first():
        error = 'Username already taken'
        if request.is_json:
            return jsonify({'success': False, 'errors': [error]}), 400
        flash(error, 'error')
        return render_template('signup.html')
    
    # Create user
    try:
        new_user = User(username=username, email=email, is_guest=False)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user, remember=True)
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Account created successfully',
                'redirect': url_for('chatbot.chat_interface')
            })
        
        flash('Welcome to FitAura! 🎨', 'success')
        return redirect(url_for('chatbot.chat_interface'))
    
    except Exception as e:
        db.session.rollback()
        print(f"Error creating user: {e}")
        error = 'An error occurred during signup'
        if request.is_json:
            return jsonify({'success': False, 'errors': [error]}), 500
        flash(error, 'error')
        return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json() if request.is_json else request.form
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        error = 'Email and password are required'
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'error')
        return render_template('login.html')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        login_user(user, remember=True)
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'redirect': url_for('chatbot.chat_interface')
            })
        
        flash(f'Welcome back, {user.username}! 👋', 'success')
        return redirect(url_for('chatbot.chat_interface'))
    else:
        error = 'Invalid email or password'
        if request.is_json:
            return jsonify({'success': False, 'error': error}), 401
        flash(error, 'error')
        return render_template('login.html')

@auth_bp.route('/guest-login', methods=['POST'])
def guest_login():
    """
    Create temporary guest session (NO database entry)
    Guest data stored in browser only
    """
    try:
        # Create guest session ID
        guest_session_id = f"guest_{uuid.uuid4().hex[:12]}"
        session['guest_id'] = guest_session_id
        session['is_guest'] = True
        session.permanent = False  # Session expires on browser close
        
        print(f"✅ Guest session created: {guest_session_id}")
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Guest session created',
                'guest_id': guest_session_id,
                'redirect': url_for('chatbot.chat_interface')
            })
        
        flash('👋 Browsing as guest. Sign up to save your recommendations!', 'info')
        return redirect(url_for('chatbot.chat_interface'))
        
    except Exception as e:
        print(f"Error creating guest session: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': 'Failed to create guest session'}), 500
        flash('Error creating guest session', 'error')
        return redirect(url_for('index'))

@auth_bp.route('/logout')
def logout():
    """Handle logout (works for both regular and guest users)"""
    is_guest = session.get('is_guest', False)
    
    if current_user.is_authenticated:
        logout_user()
    
    # Clear guest session
    session.pop('guest_id', None)
    session.pop('is_guest', None)
    
    flash('You have been logged out' if not is_guest else 'Guest session ended', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/check-auth')
def check_auth():
    """Check authentication status (for AJAX)"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'is_guest': False,
            'user_id': current_user.id,
            'username': current_user.username
        })
    elif session.get('is_guest'):
        return jsonify({
            'authenticated': True,
            'is_guest': True,
            'guest_id': session.get('guest_id'),
            'username': 'Guest'
        })
    
    return jsonify({'authenticated': False}), 401 