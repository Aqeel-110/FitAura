from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models.database import db, Preference, Recommendation, UploadedImage, ConversationHistory
from utils.gemini_handler import get_fitaura_ai
from utils.prompt_templates import PromptTemplates
from config.config import Config
import json
import uuid
import os
from datetime import datetime

chatbot_bp = Blueprint('chatbot', __name__)

# Load questions
QUESTIONS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'questions.json')

def load_questions():
    """Load questions from JSON"""
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            data = json.load(f)
            return data.get('questions', [])
    except:
        # Return default questions if file missing
        return [
            {"id": 1, "question": "What is your gender/style preference?", "type": "multiple_choice",
             "options": ["Male", "Female", "Unisex", "Prefer not to say"]},
            {"id": 2, "question": "What is the occasion?", "type": "multiple_choice",
             "options": ["Casual", "Formal", "Business", "Party", "Sports", "Beach", "Date"]},
            # ... (add rest of questions)
        ]

def is_guest_user():
    """Check if current session is guest"""
    return session.get('is_guest', False) and not current_user.is_authenticated

def get_user_id():
    """Get user ID (works for both registered and guest)"""
    if current_user.is_authenticated:
        return current_user.id
    return None

def save_if_registered(func):
    """Decorator to only save to DB if user is registered"""
    def wrapper(*args, **kwargs):
        if is_guest_user():
            print("⚠️ Guest user - skipping database save")
            return None
        return func(*args, **kwargs)
    return wrapper

@chatbot_bp.route('/chat')
def chat_interface():
    """Main chat interface (works for both guest and registered)"""
    # Create new session
    new_session_id = str(uuid.uuid4())
    session['chat_session_id'] = new_session_id
    
    # Check if guest
    is_guest = is_guest_user()
    
    print(f"🆕 Chat session: {new_session_id} ({'Guest' if is_guest else 'User'})")
    
    return render_template('chatbot.html', is_guest=is_guest)

# ========== WORKFLOW #1: GENERATE NEW OUTFIT (11 Questions) ==========

@chatbot_bp.route('/get-question/<int:question_id>', methods=['GET'])
def get_question(question_id):
    """Get specific question"""
    questions = load_questions()
    question = next((q for q in questions if q['id'] == question_id), None)
    
    if not question:
        return jsonify({'success': False, 'error': 'Question not found'}), 404
    
    return jsonify({'success': True, 'question': question})

@chatbot_bp.route('/process-answer', methods=['POST'])
def process_answer():
    """Process answer to structured question"""
    try:
        data = request.get_json()
        question_number = data.get('question_number')
        answer = data.get('answer', '').strip()
        
        if not answer:
            return jsonify({'success': False, 'error': 'Answer cannot be empty'}), 400
        
        session_id = session.get('chat_session_id', str(uuid.uuid4()))
        session['chat_session_id'] = session_id
        
        questions = load_questions()
        question = next((q for q in questions if q['id'] == question_number), None)
        
        if not question:
            return jsonify({'success': False, 'error': 'Invalid question'}), 400
        
        # Save to DB only if registered user
        if not is_guest_user() and current_user.is_authenticated:
            try:
                preference = Preference(
                    user_id=current_user.id,
                    session_id=session_id,
                    question_id=question_number,
                    question_text=question['question'],
                    answer=answer,
                    timestamp=datetime.utcnow()
                )
                db.session.add(preference)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error saving preference: {e}")
        
        # Check if completed
        if is_guest_user():
            # For guests, check session storage
            guest_answers = session.get('guest_answers', {})
            guest_answers[str(question_number)] = answer
            session['guest_answers'] = guest_answers
            answered_count = len(guest_answers)
        else:
            answered_count = Preference.query.filter_by(
                user_id=current_user.id,
                session_id=session_id
            ).count()
        
        total_questions = len(questions)
        
        if answered_count >= total_questions:
            return jsonify({
                'success': True,
                'completed': True,
                'message': 'All questions answered!'
            })
        else:
            next_question_id = question_number + 1
            next_question = next((q for q in questions if q['id'] == next_question_id), None)
            
            if next_question:
                return jsonify({
                    'success': True,
                    'completed': False,
                    'next_question': next_question
                })
            else:
                return jsonify({'success': True, 'completed': True})
    
    except Exception as e:
        print(f"Error processing answer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@chatbot_bp.route('/generate-recommendations', methods=['POST'])
def generate_recommendations():
    """Generate outfit using AI (Workflow #1)"""
    try:
        session_id = session.get('chat_session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'No active session'}), 400
        
        # Get preferences
        if is_guest_user():
            # Guest: get from session
            guest_answers = session.get('guest_answers', {})
            questions = load_questions()
            prefs_dict = {}
            for q_id, answer in guest_answers.items():
                q = next((q for q in questions if q['id'] == int(q_id)), None)
                if q:
                    prefs_dict[q['question']] = answer
        else:
            # Registered: get from DB
            preferences = Preference.query.filter_by(
                user_id=current_user.id,
                session_id=session_id
            ).order_by(Preference.question_id).all()
            
            prefs_dict = {pref.question_text: pref.answer for pref in preferences}
        
        # Initialize AI
        ai = get_fitaura_ai()
        
        # Generate outfit description
        print("Generating outfit description...")
        outfit_description = ai.generate_outfit_recommendation(prefs_dict)
        
        print(f"✅ Generated: {outfit_description[:100]}...")
        
        # Generate images
        image_paths = []
        sd_prompt = None
        try:
            print("Generating images...")
            gender = prefs_dict.get('What is your gender/style preference?', 'unisex')
            image_prompt = PromptTemplates.image_generation_prompt_from_description(
                outfit_description, gender
            )
            image_paths, sd_prompt = ai.generate_outfit_images(image_prompt, num_images=1)
            
            if image_paths:
                print(f"✅ Generated {len(image_paths)} images")
        except Exception as img_error:
            print(f"⚠️ Image generation failed: {img_error}")
        
        # Save to DB only if registered
        recommendation_id = None
        if not is_guest_user() and current_user.is_authenticated:
            try:
                recommendation = Recommendation(
                    user_id=current_user.id,
                    session_id=session_id,
                    workflow_type='generate_new',
                    recommendation_text=outfit_description,
                    image_paths=json.dumps(image_paths) if image_paths else None,
                    sd_prompt=sd_prompt,
                    is_saved=False
                )
                db.session.add(recommendation)
                db.session.commit()
                recommendation_id = recommendation.id
                print(f"💾 Saved to DB: Recommendation #{recommendation_id}")
            except Exception as db_error:
                db.session.rollback()
                print(f"⚠️ DB save failed: {db_error}")
        
        return jsonify({
            'success': True,
            'recommendations': outfit_description,
            'images': image_paths,
            'sd_prompt': sd_prompt,
            'recommendation_id': recommendation_id,
            'is_guest': is_guest_user()
        })
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== WORKFLOW #2: MODIFY OUTFIT ==========

@chatbot_bp.route('/modify-outfit', methods=['POST'])
def modify_outfit():
    """Modify existing outfit (change color, style, etc.)"""
    try:
        data = request.get_json()
        original_sd_prompt = data.get('original_sd_prompt')
        modification_request = data.get('modification')
        parent_rec_id = data.get('parent_recommendation_id')
        
        if not original_sd_prompt or not modification_request:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400
        
        ai = get_fitaura_ai()
        
        # Modify prompt
        print(f"Modifying prompt: {modification_request}")
        modified_prompt = ai.modify_sd_prompt(original_sd_prompt, modification_request)
        
        # Generate new images with modified prompt
        image_paths, _ = ai.generate_outfit_images(modified_prompt, num_images=1)
        
        # Generate text description of modification
        description = ai.generate_text_response(
            f"Briefly describe this outfit: {modified_prompt}",
            max_tokens=100
        )
        
        # Save to DB if registered
        recommendation_id = None
        if not is_guest_user() and current_user.is_authenticated:
            try:
                session_id = session.get('chat_session_id', str(uuid.uuid4()))
                recommendation = Recommendation(
                    user_id=current_user.id,
                    session_id=session_id,
                    workflow_type='modify',
                    parent_recommendation_id=parent_rec_id,
                    recommendation_text=description,
                    image_paths=json.dumps(image_paths) if image_paths else None,
                    sd_prompt=modified_prompt,
                    is_saved=False
                )
                db.session.add(recommendation)
                db.session.commit()
                recommendation_id = recommendation.id
            except Exception as e:
                db.session.rollback()
                print(f"DB save error: {e}")
        
        return jsonify({
            'success': True,
            'description': description,
            'images': image_paths,
            'sd_prompt': modified_prompt,
            'recommendation_id': recommendation_id
        })
    
    except Exception as e:
        print(f"Error modifying outfit: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== WORKFLOW #3: FOLLOW-UP QUESTIONS ==========

@chatbot_bp.route('/followup-question', methods=['POST'])
def followup_question():
    """Answer questions about generated outfit"""
    try:
        data = request.get_json()
        question = data.get('question')
        outfit_context = data.get('outfit_context')
        image_path = data.get('image_path')
        
        if not question or not outfit_context:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400
        
        ai = get_fitaura_ai()
        
        # Convert web path to filesystem path if needed
        full_image_path = None
        if image_path:
            full_image_path = image_path.replace('/static/', 'static/')
        
        answer = ai.answer_followup_question(question, outfit_context, full_image_path)
        
        return jsonify({
            'success': True,
            'answer': answer
        })
    
    except Exception as e:
        print(f"Error in followup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== WORKFLOW #4: IMAGE ANALYSIS ==========

@chatbot_bp.route('/upload-image', methods=['POST'])
def upload_image():
    """Upload image for analysis"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if file and Config.allowed_file(file.filename):
            # Save file
            filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # Save to DB if registered
            if not is_guest_user() and current_user.is_authenticated:
                try:
                    session_id = session.get('chat_session_id', str(uuid.uuid4()))
                    uploaded_image = UploadedImage(
                        user_id=current_user.id,
                        session_id=session_id,
                        image_path=filepath,
                        original_filename=file.filename,
                        upload_type='file'
                    )
                    db.session.add(uploaded_image)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"DB save error: {e}")
            
            relative_path = f"/static/uploads/{filename}"
            
            return jsonify({
                'success': True,
                'image_path': relative_path,
                'message': 'Image uploaded successfully'
            })
        
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@chatbot_bp.route('/analyze-image', methods=['POST'])
def analyze_image():
    """Analyze uploaded image"""
    try:
        data = request.get_json()
        image_path = data.get('image_path')
        analysis_type = data.get('analysis_type', 'general')
        
        if not image_path:
            return jsonify({'success': False, 'error': 'No image path'}), 400
        
        # Convert web path to filesystem
        full_path = image_path.replace('/static/', 'static/')
        
        ai = get_fitaura_ai()
        analysis = ai.analyze_uploaded_image(full_path, analysis_type)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    
    except Exception as e:
        print(f"Analysis error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== WORKFLOW #5: GENERATE FROM UPLOADED IMAGE ==========

@chatbot_bp.route('/generate-from-image', methods=['POST'])
def generate_from_image():
    """Generate outfit based on uploaded image"""
    try:
        data = request.get_json()
        image_path = data.get('image_path')
        
        if not image_path:
            return jsonify({'success': False, 'error': 'No image path'}), 400
        
        full_path = image_path.replace('/static/', 'static/')
        
        ai = get_fitaura_ai()
        
        # Extract features from image
        print("Extracting features from uploaded image...")
        outfit_description = ai.extract_outfit_features_from_image(full_path)
        
        # Generate similar outfit
        print("Generating similar outfit...")
        image_paths, sd_prompt = ai.generate_outfit_images(outfit_description, num_images=1)
        
        # Save to DB if registered
        recommendation_id = None
        if not is_guest_user() and current_user.is_authenticated:
            try:
                session_id = session.get('chat_session_id', str(uuid.uuid4()))
                recommendation = Recommendation(
                    user_id=current_user.id,
                    session_id=session_id,
                    workflow_type='from_analysis',
                    recommendation_text=outfit_description,
                    image_paths=json.dumps(image_paths) if image_paths else None,
                    sd_prompt=sd_prompt,
                    is_saved=False
                )
                db.session.add(recommendation)
                db.session.commit()
                recommendation_id = recommendation.id
            except Exception as e:
                db.session.rollback()
                print(f"DB save error: {e}")
        
        return jsonify({
            'success': True,
            'description': outfit_description,
            'images': image_paths,
            'sd_prompt': sd_prompt,
            'recommendation_id': recommendation_id
        })
    
    except Exception as e:
        print(f"Error generating from image: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== INTENT ROUTER ==========

@chatbot_bp.route('/chat-message', methods=['POST'])
def chat_message():
    """
    Smart chat endpoint - detects intent and routes to correct workflow
    """
    try:
        data = request.get_json()
        user_message = data.get('message')
        context = data.get('context', {})
        
        if not user_message:
            return jsonify({'success': False, 'error': 'No message'}), 400
        
        ai = get_fitaura_ai()
        
        # Detect intent
        intent_result = ai.detect_intent(user_message, json.dumps(context))
        intent = intent_result['intent']
        
        print(f"🎯 Detected intent: {intent}")
        
        # Route based on intent
        if intent == 'generate_new':
            return jsonify({
                'success': True,
                'action': 'start_questionnaire',
                'message': "Great! I'll ask you 11 quick questions to create your perfect outfit."
            })
        
        elif intent == 'modify_outfit':
            if not context.get('sd_prompt'):
                return jsonify({
                    'success': True,
                    'message': "I don't see an outfit to modify. Would you like to generate a new one?"
                })
            # Handle modification
            return modify_outfit()
        
        elif intent == 'followup_question':
            if not context.get('outfit_description'):
                return jsonify({
                    'success': True,
                    'message': "I don't have an outfit to discuss. Let's create one first!"
                })
            return followup_question()
        
        elif intent == 'analyze_image':
            return jsonify({
                'success': True,
                'action': 'request_image_upload',
                'message': "Please upload or capture an image to analyze."
            })
        
        elif intent == 'generate_from_image':
            if not context.get('uploaded_image'):
                return jsonify({
                    'success': True,
                    'action': 'request_image_upload',
                    'message': "Please upload the reference image first."
                })
            return generate_from_image()
        
        # Default: conversational response
        response = ai.generate_text_response(
            f"User: {user_message}\n\nAssistant (brief, helpful):",
            max_tokens=200
        )
        
        return jsonify({
            'success': True,
            'message': response,
            'intent': intent
        })
    
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@chatbot_bp.route('/restart-chat', methods=['POST'])
def restart_chat():
    """Restart chat session"""
    session.pop('chat_session_id', None)
    session.pop('guest_answers', None)
    session['chat_session_id'] = str(uuid.uuid4())
    
    return jsonify({'success': True, 'message': 'New chat started'})