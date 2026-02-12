import os
from dotenv import load_dotenv
import google.generativeai as genai
from functools import lru_cache
import json

# Load environment variables
load_dotenv()

# Reuse API keys from environment or fallback
API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2")
]
API_KEYS = [k for k in API_KEYS if k]

if not API_KEYS:
    API_KEYS = ["AIzaSyC9QuwKKF4TmXnwOxL3GvNR9fBvI36979A"]

CURRENT_KEY_INDEX = 0

def get_model():
    """Get configured Gemini model with current key"""
    global CURRENT_KEY_INDEX
    try:
        genai.configure(api_key=API_KEYS[CURRENT_KEY_INDEX])
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        return None

def get_ai_response(user_message, language='english', history=None):
    """
    Get response from Gemini AI acting as a medical assistant.
    Args:
        user_message (str): The user's input message.
        language (str): The language to respond in (e.g., 'english', 'hindi').
        history (list): List of previous messages (optional).
    Returns:
        str: AI response.
    """
    global CURRENT_KEY_INDEX
    
    # System prompt to define behavior
    system_prompt = f"""
    You are Pristin AI, a helpful virtual health assistant for rural patients in India.
    
    GUIDELINES:
    1. Language: Reply in {language}. If the user speaks a different language, adapt but prefer {language}.
    2. Role: You assist with understanding symptoms, finding pharmacies, and general health advice.
    3. SAFETY: You are NOT a doctor. Do NOT diagnose serious conditions. ALWAYS recommend visiting a doctor for serious issues.
    4. Tone: Empathetic, simple, and clear. Avoid complex medical jargon.
    5. Context: The user is using the 'Pristin Healthcare' app which has features like Symptom Check, Vitals Log, Prescription OCR, and Video Consult.
    
    If asked about the app features:
    - "Symptoms": Tell them they can [Report Symptoms](/symptom_input) to get AI insights.
    - "Vitals": They can [Log Vitals](/vitals_input) to track BP, sugar, etc.
    - "Doctors": They can [Start Video Consultation](/video_start) or view [Prescriptions](/prescription_history).
    - "Pharmacy": They can [Find Pharmacy](/pharmacy_map).
    
    Use Markdown for links. Example: [Link Text](URL).
    
    Now, answer the user's question.
    """

    # Construct full prompt
    full_prompt = f"{system_prompt}\n\nUser: {user_message}\nAssistant:"

    try:
        model = get_model()
        if not model:
            return "Service temporarily unavailable. Please try again."

        response = model.generate_content(full_prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Chatbot API Error (Key {CURRENT_KEY_INDEX}): {e}")
        
        # Rotate key
        CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(API_KEYS)
        print(f"Switching Chatbot API Key to Index: {CURRENT_KEY_INDEX}")
        
        try:
            model = get_model()
            response = model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e2:
            print(f"Chatbot API Error (Retry failed): {e2}")
            return "I'm having trouble connecting right now. Please try again later."

def get_medical_analysis(symptoms, age=None, gender=None, conditions=None, severity=5, affected_area=None):
    """
    Get a structured medical analysis from Gemini.
    """
    global CURRENT_KEY_INDEX
    
    prompt = f"""
    You are a medical diagnostic assistant. Analyze these symptoms for a {age} year old {gender} 
    with existing conditions: {conditions}.
    
    SYMPTOMS: {symptoms}
    AFFECTED AREA: {affected_area if affected_area else 'Not specified'}
    SEVERITY: {severity}/10
    
    Return a JSON object with the following fields:
    - disease: (String) Likely condition name
    - description: (String) Short description
    - causes: (String) What causes it
    - symptoms: (String) Common symptoms
    - treatment: (String) General non-prescription treatment/advice
    - urgency: (String) Low, Medium, or High
    - doctor: (String) Which specialist to visit
    
    IMPORTANT: Provide personalized insights based on the patient's age and conditions. 
    If symptoms are severe ({severity}>=7), prioritize urgent care advice.
    Return ONLY the JSON object.
    """

    try:
        model = get_model()
        if not model: return None
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up JSON if AI adds markdown blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception as e:
        print(f"Medical Analysis Error: {e}")
        return None
