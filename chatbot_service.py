import os
from dotenv import load_dotenv
import google.generativeai as genai
from functools import lru_cache
import json

# Load environment variables
load_dotenv()

# Use the dedicated Analysis key for health scans and chatbot
GEMINI_KEY = os.getenv("GEMINI_ANALYSIS_KEY")

if not GEMINI_KEY:
    # Fallback to the one provided in the prompt if not in env
    GEMINI_KEY = "AIzaSyAUFPRiJSNOxrGYrorPVwNzw9luYPaNSrY"

def get_model():
    """Get configured Gemini model with the dedicated analysis key"""
    try:
        if not GEMINI_KEY:
            print("CRITICAL: GEMINI_ANALYSIS_KEY is missing.")
            return None
        genai.configure(api_key=GEMINI_KEY)
        # Using gemini-2.5-flash as it is the stable production-ready model
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
        print(f"Chatbot API Error: {e}")
        return "I'm having trouble connecting right now. Please try again later."

def get_medical_analysis(symptoms, age=None, gender=None, conditions=None, severity=5, affected_area=None, language='english'):
    """
    Get a structured medical analysis from Gemini.
    """
    
    prompt = f"""
    You are a medical diagnostic assistant. Analyze these symptoms for a {age} year old {gender} 
    with existing conditions: {conditions}.
    
    SYMPTOMS: {symptoms}
    AFFECTED AREA: {affected_area if affected_area else 'Not specified'}
    SEVERITY: {severity}/10
    
    Return a JSON object with the following fields IN {language.upper()}:
    - disease: (String) Likely condition name
    - description: (String) Short description
    - causes: (String) What causes it
    - symptoms: (String) Common symptoms
    - treatment: (String) General non-prescription treatment/advice
    - urgency: (String) Low, Medium, or High
    - doctor: (String) Which specialist to visit
    
    IMPORTANT: Provide personalized insights based on the patient's age and conditions. 
    If symptoms are severe ({severity}>=7), prioritize urgent care advice.
    Return ONLY the JSON object. All values must be in {language}.
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

def get_facial_analysis(image_path=None, language='english'):
    """
    Generate health analysis from facial scan using Gemini.
    """
    prompt = f"""
    Analyze the health indicators visible in a facial scan for a rural patient.
    Language: {language}
    
    Look for:
    - Sclera color (whites of eyes) - Indicators of Jaundice
    - Under-eye color - Indicators of Anemia/Iron deficiency
    - Skin tone uniformity - Dehydration or circulation issues
    
    Return a JSON object with:
    - status: (String) "Normal", "Warning", or "Action Required"
    - conditions: (List of Objects) Each with:
        - name: (String) e.g., "Healthy Appearance", "Slight Anemia Indicator"
        - confidence: (Float) 0-100
        - indicator: (String) High-level observation
        - action: (String) Recommended next step
    - analysis: (String) 1-2 sentence detailed summary.
    
    IMPORTANT: Be professional and medical in tone. Avoid diagnostics, use "indicates" or "suggests".
    Return ONLY the JSON.
    """
    
    try:
        model = get_model()
        if not model: return None
        
        # In a real app, we'd pass the image to Gemini Vision
        # For this demo, we can either pass the image if supported or use a prompt
        # genai supports multimodal, so if image_path exists:
        if image_path and os.path.exists(image_path):
             from PIL import Image
             img = Image.open(image_path)
             response = model.generate_content([prompt, img])
        else:
             response = model.generate_content(prompt)
             
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception as e:
        print(f"Facial Analysis Error: {e}")
        return None

def get_ai_summary(report_text, language='english'):
    """Generate a 1-sentence summary of a symptom report"""
    prompt = f"Summarize this symptom report in one short, clear sentence in {language}: {report_text}"
    try:
        model = get_model()
        if not model: return report_text[:50] + "..."
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return report_text[:50] + "..."

def get_meal_analysis(image_path, age=None, weight=None, height=None, language='english'):
    """
    Generate nutritional analysis from a meal photo using Gemini Vision.
    """
    prompt = f"""
    Analyze this meal photo for a patient in a rural setting.
    Patient Info: Age: {age}, Weight: {weight}kg, Height: {height}cm.
    Language: {language}
    
    Tasks:
    1. Identify the food items.
    2. Estimate total calories.
    3. Estimate Macronutrients (Protein, Carbs, Fats) in grams.
    4. Provide 2-3 specific nutritional advices based on the patient's info (if provided).
    
    Return a JSON object with:
    - calories: (Integer) Total estimated calories
    - nutrients: (Object) {{ "Protein": int, "Carbs": int, "Fats": int }}
    - advice: (String) Unified nutritional advice string.
    
    IMPORTANT: Be helpful and encouraging.
    Return ONLY the JSON.
    """
    
    try:
        model = get_model()
        if not model: return None
        
        if image_path and os.path.exists(image_path):
             from PIL import Image
             img = Image.open(image_path)
             response = model.generate_content([prompt, img])
             
             text = response.text.strip()
             if "```json" in text:
                 text = text.split("```json")[1].split("```")[0].strip()
             elif "```" in text:
                 text = text.split("```")[1].split("```")[0].strip()
                 
             return json.loads(text)
        return None
    except Exception as e:
        print(f"Meal Analysis Error: {e}")
        return None
