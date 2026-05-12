import re
import json
from config.config import Config

class ResponseValidator:
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self):
        """Load validation rules from JSON file"""
        try:
            with open(Config.VALIDATION_RULES_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default validation rules if file not found
            return {
                "multiple_choice": {
                    "min_length": 1,
                    "max_length": 50
                },
                "text": {
                    "min_length": 2,
                    "max_length": 200
                },
                "number": {
                    "min_value": 0,
                    "max_value": 100000
                }
            }
    
    def validate_response(self, question_type, response, options=None):
        """
        Validate user response based on question type
        
        Args:
            question_type: Type of question (multiple_choice, text, number)
            response: User's response
            options: Valid options for multiple choice questions
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not response or response.strip() == '':
            return False, "Response cannot be empty"
        
        response = response.strip()
        
        if question_type == 'multiple_choice':
            return self._validate_multiple_choice(response, options)
        elif question_type == 'text':
            return self._validate_text(response)
        elif question_type == 'number':
            return self._validate_number(response)
        else:
            return True, None
    
    def _validate_multiple_choice(self, response, options):
        """Validate multiple choice response"""
        if not options:
            return True, None
        
        # Convert to lowercase for case-insensitive comparison
        response_lower = response.lower()
        options_lower = [opt.lower() for opt in options]
        
        if response_lower in options_lower:
            return True, None
        else:
            return False, f"Please choose from: {', '.join(options)}"
    
    def _validate_text(self, response):
        """Validate text response"""
        rules = self.validation_rules.get('text', {})
        min_length = rules.get('min_length', 2)
        max_length = rules.get('max_length', 200)
        
        if len(response) < min_length:
            return False, f"Response must be at least {min_length} characters"
        
        if len(response) > max_length:
            return False, f"Response must not exceed {max_length} characters"
        
        # Check for meaningful content (not just spaces or special characters)
        if not re.search(r'[a-zA-Z0-9]', response):
            return False, "Please provide a meaningful response"
        
        return True, None
    
    def _validate_number(self, response):
        """Validate numeric response"""
        rules = self.validation_rules.get('number', {})
        min_value = rules.get('min_value', 0)
        max_value = rules.get('max_value', 100000)
        
        try:
            number = float(response)
            
            if number < min_value:
                return False, f"Value must be at least {min_value}"
            
            if number > max_value:
                return False, f"Value must not exceed {max_value}"
            
            return True, None
        
        except ValueError:
            return False, "Please enter a valid number"
    
    def validate_all_responses(self, responses_dict, questions_list):
        """
        Validate all user responses against questions
        
        Args:
            responses_dict: Dictionary of question_id: response
            questions_list: List of question objects
            
        Returns:
            tuple: (is_valid, errors_dict)
        """
        errors = {}
        
        for question in questions_list:
            question_id = question['id']
            response = responses_dict.get(question_id, '')
            
            is_valid, error_msg = self.validate_response(
                question['type'],
                response,
                question.get('options')
            )
            
            if not is_valid:
                errors[question_id] = error_msg
        
        return len(errors) == 0, errors
    
    def sanitize_input(self, text):
        """
        Sanitize user input to prevent injection attacks
        
        Args:
            text: User input text
            
        Returns:
            Sanitized text
        """
        if not text:
            return ''
        
        # Remove potentially harmful characters
        text = re.sub(r'[<>{}]', '', text)
        
        # Limit length
        max_length = 500
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()