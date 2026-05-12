class PromptTemplates:
    """
    FitAura Prompt Templates
    Optimized for CLIP's 77 token limit
    """
    
    @staticmethod
    def outfit_recommendation_prompt(preferences):
        """Generate SHORT outfit description (2-3 lines)"""
        template = """You are a FitAura fashion stylist. Create ONE complete outfit description (2-3 sentences max).

CLIENT PREFERENCES:
"""
        for key, value in preferences.items():
            template += f"• {key}: {value}\n"
        
        template += """
YOUR RESPONSE (2-3 sentences only):
Describe ONE outfit with specific items, exact colors, and one accessory. Keep it concise.

Example: "A navy blue blazer with white dress shirt, charcoal grey trousers, and black oxford shoes. Add a silver watch for sophistication."
"""
        return template
    
    @staticmethod
    def image_generation_prompt_from_description(outfit_description, gender="unisex"):
        """
        Convert outfit description to SD prompt
        (Will be further optimized by _optimize_prompt_for_clip)
        """
        return outfit_description  # Handler will optimize
    
    @staticmethod
    def modification_prompt(original_prompt, modification):
        """Generate prompt for outfit modification"""
        return f"""Original outfit: {original_prompt}
        
Modification requested: {modification}

Generate modified version (under 50 words, comma-separated keywords)."""
    
    @staticmethod
    def followup_prompt(outfit_description, user_question):
        """Handle followup questions"""
        return f"""Outfit: {outfit_description}

Question: {user_question}

Provide specific, helpful answer."""
    
    @staticmethod
    def image_analysis_prompt(analysis_type='general'):
        """Prompts for image analysis"""
        prompts = {
            'general': "Analyze this outfit and describe the style, colors, and items visible.",
            'feedback': "As a fashion expert, provide constructive feedback on this outfit.",
            'extract': "Extract specific clothing items, colors, and style keywords from this image."
        }
        return prompts.get(analysis_type, prompts['general'])