"""
Utility functions for Rural Telemedicine Platform - Phase 1
Includes:
- Image compression for low-bandwidth
- OCR for prescription reading
- Clinical decision support system
- Vitals analysis
"""

import os
import io
import json
from PIL import Image
import logging
from datetime import datetime, timedelta

# OCR imports
try:
    import pytesseract
    import easyocr
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    logging.warning("OCR libraries not available. Install pytesseract and easyocr.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== IMAGE COMPRESSION ====================

def compress_image(image_path, output_path=None, quality=60, max_width=800):
    """
    Compress image for low-bandwidth upload
    Converts to WebP format and reduces size by 60-70%
    
    Args:
        image_path: Path to original image
        output_path: Path to save compressed image (optional)
        quality: Compression quality (1-100, default 60)
        max_width: Maximum width in pixels (default 800)
    
    Returns:
        Path to compressed image
    """
    try:
        # Open image
        img = Image.open(image_path)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Resize if too large
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Generate output path if not provided
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_compressed.webp"
        
        # Save as WebP with compression
        img.save(output_path, 'WEBP', quality=quality, method=6)
        
        # Log compression results
        original_size = os.path.getsize(image_path)
        compressed_size = os.path.getsize(output_path)
        reduction = ((original_size - compressed_size) / original_size) * 100
        
        logger.info(f"Image compressed: {original_size/1024:.1f}KB → {compressed_size/1024:.1f}KB ({reduction:.1f}% reduction)")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error compressing image: {str(e)}")
        return image_path  # Return original if compression fails


def create_thumbnail(image_path, output_path=None, size=(200, 200)):
    """
    Create thumbnail for progressive loading
    
    Args:
        image_path: Path to original image
        output_path: Path to save thumbnail
        size: Thumbnail size (width, height)
    
    Returns:
        Path to thumbnail
    """
    try:
        img = Image.open(image_path)
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Create thumbnail
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Generate output path
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_thumb.webp"
        
        img.save(output_path, 'WEBP', quality=50)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating thumbnail: {str(e)}")
        return image_path


# ==================== OCR FOR PRESCRIPTIONS ====================

# Language mapping for OCR support
SUPPORTED_LANGUAGES = {
    'english': 'en',
    'hindi': 'hi',
    'tamil': 'ta',
    'telugu': 'te',
    'marathi': 'mr',
    'bengali': 'bn',
    'gujarati': 'gu',
    'kannada': 'kn',
    'malayalam': 'ml'
}

# Language display names for UI
LANGUAGE_DISPLAY_NAMES = {
    'english': 'English',
    'hindi': 'हिंदी (Hindi)',
    'tamil': 'தமிழ் (Tamil)',
    'telugu': 'తెలుగు (Telugu)',
    'marathi': 'मराठी (Marathi)',
    'bengali': 'বাংলা (Bengali)',
    'gujarati': 'ગુજરાતી (Gujarati)',
    'kannada': 'ಕನ್ನಡ (Kannada)',
    'malayalam': 'മലയാളം (Malayalam)'
}


def extract_prescription_text(image_path, language='english'):
    """
    Extract text from prescription image using OCR
    Supports English and Indian regional languages
    
    Args:
        image_path: Path to prescription image
        language: OCR language key from SUPPORTED_LANGUAGES
    
    Returns:
        Dictionary with extracted text and confidence
    """
    if not HAS_OCR:
        return {
            'raw_text': 'OCR not available. Please install pytesseract and easyocr.',
            'confidence': 0.0,
            'language_used': language
        }
    
    try:
        # Get language code
        lang_code = SUPPORTED_LANGUAGES.get(language.lower(), 'en')
        
        # Try pytesseract first for English (faster)
        if language.lower() == 'english':
            text = pytesseract.image_to_string(Image.open(image_path))
            confidence = 0.75  # Estimated confidence
        else:
            # Use EasyOCR for Indian languages
            # Always include English with regional language for mixed scripts
            lang_list = ['en', lang_code] if lang_code != 'en' else ['en']
            
            # Remove duplicates
            lang_list = list(dict.fromkeys(lang_list))
            
            logger.info(f"Using EasyOCR with languages: {lang_list}")
            reader = easyocr.Reader(lang_list, gpu=False)
            results = reader.readtext(image_path)
            
            text = ' '.join([result[1] for result in results])
            confidence = sum([result[2] for result in results]) / len(results) if results else 0.0
        
        return {
            'raw_text': text.strip(),
            'confidence': confidence,
            'language_used': language
        }
        
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        return {
            'raw_text': f'Error extracting text: {str(e)}',
            'confidence': 0.0,
            'language_used': language
        }


def detect_language_from_image(image_path):
    """
    Auto-detect language from prescription image
    Uses EasyOCR with multiple languages and returns best match
    
    Args:
        image_path: Path to prescription image
    
    Returns:
        Detected language key
    """
    if not HAS_OCR:
        return 'english'
    
    try:
        # Try with common Indian languages + English
        reader = easyocr.Reader(['en', 'hi', 'ta', 'te'], gpu=False)
        results = reader.readtext(image_path)
        
        # For now, return English as default
        # More sophisticated detection would analyze script patterns
        return 'english'
        
    except Exception as e:
        logger.error(f"Language detection error: {str(e)}")
        return 'english'


def parse_prescription(raw_text):
    """
    Parse prescription text to extract structured data
    
    Args:
        raw_text: Raw OCR text from prescription
    
    Returns:
        Dictionary with drug name, dosage, frequency, duration
    """
    # Simple rule-based parsing (can be enhanced with NLP)
    lines = raw_text.split('\n')
    
    prescription_data = {
        'drug_name': '',
        'dosage': '',
        'frequency': '',
        'duration': '',
        'doctor_name': ''
    }
    
    # Common patterns
    dosage_keywords = ['mg', 'ml', 'tablet', 'capsule', 'syrup']
    frequency_keywords = ['daily', 'twice', 'thrice', 'morning', 'evening', 'night', 'od', 'bd', 'td']
    duration_keywords = ['days', 'weeks', 'months', 'continue']
    
    for line in lines:
        line_lower = line.lower()
        
        # Extract drug name (usually first significant line)
        if not prescription_data['drug_name'] and len(line.strip()) > 3:
            if any(keyword in line_lower for keyword in dosage_keywords):
                prescription_data['drug_name'] = line.split()[0]
        
        # Extract dosage
        if any(keyword in line_lower for keyword in dosage_keywords):
            prescription_data['dosage'] = line.strip()
        
        # Extract frequency
        if any(keyword in line_lower for keyword in frequency_keywords):
            prescription_data['frequency'] = line.strip()
        
        # Extract duration
        if any(keyword in line_lower for keyword in duration_keywords):
            prescription_data['duration'] = line.strip()
        
        # Extract doctor name
        if 'dr.' in line_lower or 'doctor' in line_lower:
            prescription_data['doctor_name'] = line.strip()
    
    return prescription_data


# ==================== CLINICAL DECISION SUPPORT ====================

# Rural health conditions database
RURAL_CONDITIONS_DB = {
    'malaria': {
        'symptoms': ['fever', 'chills', 'sweating', 'headache', 'nausea', 'vomiting'],
        'severity_indicators': ['high fever', 'severe headache', 'confusion'],
        'treatment': 'Antimalarial medications (Chloroquine, Artemisinin-based combination therapy)',
        'medicines': ['Chloroquine 250mg', 'Artemether-Lumefantrine', 'Paracetamol for fever'],
        'advice': 'Use mosquito nets, seek immediate medical attention if symptoms worsen',
        'urgency': 'high'
    },
    'diarrhea': {
        'symptoms': ['loose stools', 'abdominal pain', 'cramping', 'dehydration', 'nausea'],
        'severity_indicators': ['blood in stool', 'severe dehydration', 'high fever'],
        'treatment': 'ORS (Oral Rehydration Solution), maintain hydration',
        'medicines': ['ORS packets', 'Zinc supplements', 'Loperamide (if needed)'],
        'advice': 'Drink plenty of fluids, avoid dairy products, maintain hygiene',
        'urgency': 'medium'
    },
    'diabetes': {
        'symptoms': ['increased thirst', 'frequent urination', 'weight loss', 'fatigue', 'blurred vision'],
        'severity_indicators': ['very high glucose', 'ketones in urine', 'confusion'],
        'treatment': 'Blood sugar management, lifestyle modifications',
        'medicines': ['Metformin 500mg', 'Glibenclamide', 'Insulin (if prescribed)'],
        'advice': 'Regular blood sugar monitoring, diet control, exercise, foot care',
        'urgency': 'medium'
    },
    'hypertension': {
        'symptoms': ['headache', 'dizziness', 'chest pain', 'shortness of breath', 'nosebleeds'],
        'severity_indicators': ['severe headache', 'chest pain', 'vision problems'],
        'treatment': 'Blood pressure control, lifestyle changes',
        'medicines': ['Amlodipine 5mg', 'Enalapril 5mg', 'Atenolol 50mg'],
        'advice': 'Reduce salt intake, regular exercise, stress management, regular BP monitoring',
        'urgency': 'medium'
    },
    'malnutrition': {
        'symptoms': ['weight loss', 'weakness', 'fatigue', 'poor growth', 'pale skin'],
        'severity_indicators': ['severe weight loss', 'edema', 'lethargy'],
        'treatment': 'Nutritional supplementation, balanced diet',
        'medicines': ['Multivitamin supplements', 'Iron supplements', 'Protein powder'],
        'advice': 'Balanced diet with proteins, fruits, vegetables. Regular meals.',
        'urgency': 'medium'
    },
    'respiratory_infection': {
        'symptoms': ['cough', 'fever', 'sore throat', 'runny nose', 'body aches'],
        'severity_indicators': ['difficulty breathing', 'high fever', 'chest pain'],
        'treatment': 'Rest, hydration, symptomatic relief',
        'medicines': ['Paracetamol 500mg', 'Cough syrup', 'Antibiotics (if bacterial)'],
        'advice': 'Rest, drink warm fluids, avoid cold exposure',
        'urgency': 'low'
    }
}


def generate_clinical_recommendation(symptoms, patient_age=None, patient_gender=None, existing_conditions=None):
    """
    Generate context-aware clinical recommendations
    
    Args:
        symptoms: Text description of symptoms
        patient_age: Patient age (optional)
        patient_gender: Patient gender (optional)
        existing_conditions: List of existing conditions (optional)
    
    Returns:
        Dictionary with recommendations, confidence, and reasoning
    """
    symptoms_lower = symptoms.lower()
    matched_conditions = []
    
    # Match symptoms to conditions
    for condition, data in RURAL_CONDITIONS_DB.items():
        symptom_matches = sum(1 for symptom in data['symptoms'] if symptom in symptoms_lower)
        severity_matches = sum(1 for indicator in data['severity_indicators'] if indicator in symptoms_lower)
        
        if symptom_matches > 0:
            confidence = (symptom_matches / len(data['symptoms'])) * 100
            
            # Boost confidence if severity indicators present
            if severity_matches > 0:
                confidence = min(confidence + 20, 95)
            
            matched_conditions.append({
                'condition': condition,
                'confidence': confidence,
                'symptom_matches': symptom_matches,
                'severity_matches': severity_matches,
                'data': data
            })
    
    # Sort by confidence
    matched_conditions.sort(key=lambda x: x['confidence'], reverse=True)
    
    if not matched_conditions:
        return {
            'condition_identified': 'Unknown condition',
            'confidence_score': 0,
            'treatment_suggestion': 'Please consult a doctor for proper diagnosis',
            'medications': json.dumps([]),
            'reasoning': 'No matching conditions found in database',
            'symptoms_matched': [],
            'urgency': 'medium'
        }
    
    # Get top match
    top_match = matched_conditions[0]
    condition_data = top_match['data']
    
    # Build reasoning
    matched_symptoms = [s for s in condition_data['symptoms'] if s in symptoms_lower]
    reasoning = f"Based on {top_match['symptom_matches']} matching symptoms: {', '.join(matched_symptoms)}. "
    
    # Add context based on patient data
    if patient_age:
        if patient_age < 5:
            reasoning += "Patient is a young child - extra caution advised. "
        elif patient_age > 60:
            reasoning += "Patient is elderly - monitor closely for complications. "
    
    if existing_conditions:
        reasoning += f"Patient has existing conditions: {', '.join(existing_conditions)}. "
    
    # Adjust urgency based on severity
    urgency = condition_data['urgency']
    if top_match['severity_matches'] > 0:
        urgency = 'high'
        reasoning += "URGENT: Severity indicators detected. Immediate medical attention recommended."
    
    return {
        'condition_identified': top_match['condition'].replace('_', ' ').title(),
        'confidence_score': round(top_match['confidence'], 1),
        'treatment_suggestion': condition_data['treatment'],
        'medications': json.dumps(condition_data['medicines']),
        'lifestyle_advice': condition_data['advice'],
        'reasoning': reasoning,
        'symptoms_matched': json.dumps(matched_symptoms),
        'urgency': urgency,
        'similar_cases': json.dumps([])  # Placeholder for future implementation
    }


# ==================== VITALS ANALYSIS ====================

def analyze_vitals(bp_systolic, bp_diastolic, glucose, temperature, weight=None, age=None):
    """
    Analyze vital signs and flag abnormalities
    
    Args:
        bp_systolic: Systolic blood pressure (mmHg)
        bp_diastolic: Diastolic blood pressure (mmHg)
        glucose: Blood glucose level (mg/dL)
        temperature: Body temperature (Celsius)
        weight: Weight in kg (optional)
        age: Patient age (optional)
    
    Returns:
        Dictionary with analysis results and alerts
    """
    alerts = []
    alert_type = 'normal'
    is_abnormal = False
    
    # Blood pressure analysis
    if bp_systolic and bp_diastolic:
        if bp_systolic >= 180 or bp_diastolic >= 120:
            alerts.append('CRITICAL: Hypertensive crisis - seek immediate medical attention')
            alert_type = 'critical'
            is_abnormal = True
        elif bp_systolic >= 140 or bp_diastolic >= 90:
            alerts.append('WARNING: High blood pressure detected')
            alert_type = 'warning' if alert_type != 'critical' else alert_type
            is_abnormal = True
        elif bp_systolic < 90 or bp_diastolic < 60:
            alerts.append('WARNING: Low blood pressure detected')
            alert_type = 'warning' if alert_type != 'critical' else alert_type
            is_abnormal = True
    
    # Glucose analysis
    if glucose:
        if glucose >= 200:
            alerts.append('CRITICAL: Very high blood sugar - immediate medical attention needed')
            alert_type = 'critical'
            is_abnormal = True
        elif glucose >= 126:
            alerts.append('WARNING: High blood sugar (possible diabetes)')
            alert_type = 'warning' if alert_type != 'critical' else alert_type
            is_abnormal = True
        elif glucose < 70:
            alerts.append('WARNING: Low blood sugar (hypoglycemia)')
            alert_type = 'warning' if alert_type != 'critical' else alert_type
            is_abnormal = True
    
    # Temperature analysis
    if temperature:
        if temperature >= 39.5:
            alerts.append('CRITICAL: Very high fever - seek medical attention')
            alert_type = 'critical'
            is_abnormal = True
        elif temperature >= 38:
            alerts.append('WARNING: Fever detected')
            alert_type = 'warning' if alert_type != 'critical' else alert_type
            is_abnormal = True
        elif temperature < 35:
            alerts.append('WARNING: Low body temperature (hypothermia)')
            alert_type = 'warning' if alert_type != 'critical' else alert_type
            is_abnormal = True
    
    return {
        'is_abnormal': is_abnormal,
        'alert_type': alert_type,
        'alerts': alerts,
        'recommendations': get_vital_recommendations(alerts)
    }


def get_vital_recommendations(alerts):
    """Generate recommendations based on vital alerts"""
    recommendations = []
    
    for alert in alerts:
        if 'blood pressure' in alert.lower():
            recommendations.append('Monitor BP regularly, reduce salt intake, consult doctor')
        if 'blood sugar' in alert.lower():
            recommendations.append('Check glucose levels regularly, follow diabetic diet, consult endocrinologist')
        if 'fever' in alert.lower():
            recommendations.append('Take paracetamol, stay hydrated, rest, monitor temperature')
    
    return recommendations if recommendations else ['Continue regular monitoring']


def detect_vital_trends(vital_records):
    """
    Detect concerning trends in vital signs
    
    Args:
        vital_records: List of VitalRecord objects (sorted by date)
    
    Returns:
        Dictionary with trend analysis
    """
    if len(vital_records) < 3:
        return {'trends': [], 'warnings': []}
    
    trends = []
    warnings = []
    
    # Analyze last 5 records
    recent_records = vital_records[-5:]
    
    # Blood pressure trend
    bp_systolic_values = [r.blood_pressure_systolic for r in recent_records if r.blood_pressure_systolic]
    if len(bp_systolic_values) >= 3:
        if all(bp_systolic_values[i] < bp_systolic_values[i+1] for i in range(len(bp_systolic_values)-1)):
            trends.append('Blood pressure steadily increasing')
            warnings.append('Increasing BP trend detected - consult doctor')
    
    # Glucose trend
    glucose_values = [r.glucose_level for r in recent_records if r.glucose_level]
    if len(glucose_values) >= 3:
        avg_glucose = sum(glucose_values) / len(glucose_values)
        if avg_glucose > 140:
            trends.append('Consistently high blood sugar')
            warnings.append('High average glucose - diabetes management needed')
    
    # Weight trend
    weight_values = [r.weight for r in recent_records if r.weight]
    if len(weight_values) >= 3:
        weight_change = weight_values[-1] - weight_values[0]
        if abs(weight_change) > 5:
            trends.append(f'Significant weight change: {weight_change:+.1f} kg')
            if weight_change < -5:
                warnings.append('Significant weight loss - check for underlying conditions')
    
    return {
        'trends': trends,
        'warnings': warnings
    }
