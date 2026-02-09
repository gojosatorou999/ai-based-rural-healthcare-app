from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import json
import os
import cv2
import base64
import io
from PIL import Image
import random
import numpy as np
import logging
try:
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing import image
    import tensorflow as tf
    from keras.models import load_model
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    print("Warning: TensorFlow not found. AI image features will be disabled.")

from werkzeug.utils import secure_filename
from transformers import pipeline
from pyngrok import ngrok
#---------------------------------------

#-------------load_model()---------------------
app = Flask(__name__)
app.secret_key = "ab5ea52cfbef6fcf789ce562369e183338e01c138e1b0cb3c1d63d7dc112f073"


# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS







# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Initialize Flask app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load AI Model
symptom_checker_model = None
try:
    symptom_checker_model = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")
    logging.info("✅ Symptom checker AI model loaded successfully!")
except Exception as e:
    logging.error(f"⚠️ Error loading AI model: {e}")

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    existing_conditions = db.Column(db.Text, nullable=True)  # Comma-separated conditions
    role = db.Column(db.String(20), default='patient')  # patient, doctor, chw (community health worker)
    
    # Relationships
    symptom_reports = db.relationship('SymptomReport', backref='user', lazy=True, foreign_keys='SymptomReport.user_id')
    prescriptions = db.relationship('Prescription', backref='user', lazy=True)
    vital_records = db.relationship('VitalRecord', backref='user', lazy=True)

# Symptom Report with image support
class SymptomReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symptoms_text = db.Column(db.Text, nullable=False)
    affected_area = db.Column(db.String(100), nullable=True)  # e.g., "head", "chest", "stomach"
    severity = db.Column(db.Integer, nullable=True)  # 1-10 scale
    duration = db.Column(db.String(50), nullable=True)  # e.g., "2 days", "1 week"
    image_path = db.Column(db.String(255), nullable=True)
    ai_prediction = db.Column(db.Text, nullable=True)  # JSON with disease, confidence, etc.
    confidence_score = db.Column(db.Float, nullable=True)
    doctor_approved = db.Column(db.Boolean, default=False)
    doctor_notes = db.Column(db.Text, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Doctor who approved
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Prescription from OCR
class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    raw_text = db.Column(db.Text, nullable=True)  # OCR extracted text
    language = db.Column(db.String(20), default='eng')
    confidence = db.Column(db.Float, nullable=True)
    doctor_name = db.Column(db.String(150), nullable=True)
    prescription_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to medicines
    medicines = db.relationship('Medicine', backref='prescription', lazy=True, cascade='all, delete-orphan')

# Medicine extracted from prescription
class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescription.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    dosage = db.Column(db.String(50), nullable=True)  # e.g., "500mg"
    frequency = db.Column(db.String(100), nullable=True)  # e.g., "twice daily"
    duration = db.Column(db.String(50), nullable=True)  # e.g., "7 days"
    instructions = db.Column(db.Text, nullable=True)  # e.g., "after meals"

# Family Member Proxy Access
class FamilyMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # The patient
    family_member_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # The proxy (must be a registered user)
    relationship = db.Column(db.String(50), nullable=False)  # e.g., Parent, Child, Spouse
    access_granted = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate links
    __table_args__ = (db.UniqueConstraint('user_id', 'family_member_id', name='unique_family_link'),)

# Vital Records for health timeline
class VitalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bp_systolic = db.Column(db.Integer, nullable=True)
    bp_diastolic = db.Column(db.Integer, nullable=True)
    blood_glucose = db.Column(db.Float, nullable=True)  # mg/dL
    temperature = db.Column(db.Float, nullable=True)  # Fahrenheit
    heart_rate = db.Column(db.Integer, nullable=True)
    oxygen_saturation = db.Column(db.Integer, nullable=True)  # SpO2 %
    weight = db.Column(db.Float, nullable=True)  # kg
    notes = db.Column(db.Text, nullable=True)
    alert_level = db.Column(db.String(20), default='normal')  # normal, warning, critical
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/welcome')
def welcome():
    return "Welcome to the AI Healthcare App!"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        
        # Optional fields
        age = request.form.get('age')
        gender = request.form.get('gender')
        role = request.form.get('role', 'patient')

        if User.query.filter_by(email=email).first():
            flash('Email already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        # Create user with all fields
        new_user = User(
            username=username, 
            email=email, 
            password=password,
            age=int(age) if age else None,
            gender=gender,
            role=role
        )
        
        db.session.add(new_user)
        db.session.commit()
        flash(f'Registration successful! Welcome {role}.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            
            # Redirect based on role
            if user.role == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            elif user.role == 'chw':
                return redirect(url_for('chw_dashboard'))
            else:
                return redirect(url_for('dashboard'))
                
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Role-based redirect
    if current_user.role == 'doctor':
        return redirect(url_for('doctor_dashboard'))
    elif current_user.role == 'chw':
        return redirect(url_for('chw_dashboard'))
        
    return render_template('dashboard.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))




@app.route('/check_symptoms', methods=['POST'])
def check_symptoms():
    try:
        # Ensure request has JSON data
        if not request.is_json:
            return jsonify({"error": "Invalid request format. Please send JSON data."}), 400

        data = request.get_json()
        symptoms = data.get("symptoms", "").strip()

        # Check if symptoms were provided
        if not symptoms:
            return jsonify({"error": "No symptoms provided. Please enter your symptoms."}), 400

        # AI model prediction (Replace with actual AI function)
        ai_response = predict_disease(symptoms)

        # Check if the model returned valid data
        if not ai_response or "error" in ai_response:
            return jsonify({"error": "Could not analyze symptoms. Try again."}), 500

        # Return the AI-generated response
        return jsonify({
            "description": ai_response.get("description", "N/A"),
            "causes": ai_response.get("causes", "N/A"),
            "symptoms": ai_response.get("symptoms", "N/A"),
            "treatment": ai_response.get("treatment", "N/A"),
            "doctor": ai_response.get("doctor", "N/A")
        })

    except Exception as e:
        print("Error:", str(e))  # Log error for debugging
        return jsonify({"error": "An unexpected error occurred. Please try again."}), 500



@app.route('/symptom_checker')
def symptom_checker():
    return render_template('symptom_checker.html')



def predict_disease(symptoms):
    symptoms = symptoms.lower()
    # Mock AI prediction logic (replace with real AI model)
    if "fever" in symptoms:
        return {
            "disease": "Flu",
            "description": "Flu is a contagious respiratory illness caused by influenza viruses.",
            "causes": "It spreads through virus-infected droplets from coughing, sneezing, or touching contaminated surfaces.",
            "symptoms": "Fever, cough, sore throat, body aches, fatigue.",
            "treatment": "Rest, hydration, over-the-counter fever reducers like ibuprofen.",
            "doctor": "General physician"
        }
    elif "chills" in symptoms:
        return {
            "disease": "Malaria",
            "description": "Malaria is a mosquito-borne disease caused by Plasmodium parasites.",
            "causes": "Transmitted through the bite of infected female Anopheles mosquitoes.",
            "symptoms": "Chills, fever, sweating, headache, nausea.",
            "treatment": "Antimalarial medications like chloroquine or artemisinin-based combination therapy.",
            "doctor": "Infectious disease specialist"
        }
    elif "fatigue" in symptoms:
        return {
            "disease": "Chronic Fatigue Syndrome",
            "description": "A long-term illness characterized by extreme fatigue that doesn’t improve with rest.",
            "causes": "Unknown, but possibly linked to viral infections, immune system problems, or hormonal imbalances.",
            "symptoms": "Extreme tiredness, muscle pain, difficulty concentrating, sore throat.",
            "treatment": "Lifestyle changes, therapy, and symptom management.",
            "doctor": "General physician or neurologist"
        }
    elif "weakness" in symptoms:
        return {
            "disease": "Anemia",
            "description": "A condition where the body lacks enough healthy red blood cells to carry oxygen.",
            "causes": "Iron deficiency, vitamin deficiency, chronic diseases, or blood loss.",
            "symptoms": "Weakness, fatigue, pale skin, dizziness, shortness of breath.",
            "treatment": "Iron supplements, dietary changes, or treating underlying conditions.",
            "doctor": "Hematologist"
        }
    elif "sweating" in symptoms:
        return {
            "disease": "Hyperthyroidism",
            "description": "A condition where the thyroid gland produces too much thyroid hormone.",
            "causes": "Graves' disease, thyroid nodules, or excessive iodine intake.",
            "symptoms": "Excessive sweating, weight loss, rapid heartbeat, irritability.",
            "treatment": "Antithyroid medications, radioactive iodine, or surgery.",
            "doctor": "Endocrinologist"
        }
    elif "weight loss" in symptoms:
        return {
            "disease": "Diabetes",
            "description": "A metabolic disorder that affects blood sugar regulation.",
            "causes": "Insufficient insulin production or insulin resistance.",
            "symptoms": "Unexplained weight loss, excessive thirst, frequent urination, fatigue.",
            "treatment": "Insulin therapy, medication, lifestyle changes.",
            "doctor": "Endocrinologist"
        }
    elif "weight gain" in symptoms:
        return {
            "disease": "Hypothyroidism",
            "description": "A condition where the thyroid gland does not produce enough thyroid hormone.",
            "causes": "Autoimmune disease, iodine deficiency, or certain medications.",
            "symptoms": "Weight gain, fatigue, cold intolerance, dry skin.",
            "treatment": "Thyroid hormone replacement therapy.",
            "doctor": "Endocrinologist"
        }
    elif "loss of appetite" in symptoms:
        return {
            "disease": "Gastritis",
            "description": "Inflammation of the stomach lining causing digestive discomfort.",
            "causes": "Infections, prolonged NSAID use, excessive alcohol intake.",
            "symptoms": "Loss of appetite, nausea, stomach pain, bloating.",
            "treatment": "Antacids, antibiotics (if bacterial infection present), dietary changes.",
            "doctor": "Gastroenterologist"
        }
    elif "excessive thirst" in symptoms:
        return {
            "disease": "Diabetes Mellitus",
            "description": "A chronic condition characterized by high blood sugar levels.",
            "causes": "Insufficient insulin production or resistance to insulin.",
            "symptoms": "Excessive thirst, frequent urination, weight loss, fatigue.",
            "treatment": "Lifestyle modifications, medication, insulin therapy.",
            "doctor": "Endocrinologist"
        }
    elif "night sweats" in symptoms:
        return {
            "disease": "Tuberculosis",
            "description": "A bacterial infection that mainly affects the lungs.",
            "causes": "Caused by Mycobacterium tuberculosis, spread through respiratory droplets.",
            "symptoms": "Night sweats, fever, cough, weight loss, fatigue.",
            "treatment": "Antibiotic regimen (e.g., isoniazid, rifampin, ethambutol).",
            "doctor": "Pulmonologist"
        }
    elif "cough" in symptoms:
        return {
            "disease": "Bronchitis",
            "description": "Bronchitis is an inflammation of the bronchial tubes in the lungs.",
            "causes": "Usually caused by viral infections but can also be bacterial.",
            "symptoms": "Cough (dry or wet), chest discomfort, mild fever, fatigue.",
            "treatment": "Rest, fluids, cough suppressants, inhalers if needed.",
            "doctor": "Pulmonologist"
        }
    elif "shortness of breath" in symptoms:
        return {
            "disease": "Asthma",
            "description": "A chronic condition that causes inflammation and narrowing of the airways.",
            "causes": "Allergies, pollution, respiratory infections, genetic factors.",
            "symptoms": "Shortness of breath, wheezing, coughing, chest tightness.",
            "treatment": "Inhalers, bronchodilators, lifestyle adjustments.",
            "doctor": "Pulmonologist"
        }
    elif "wheezing" in symptoms:
        return {
            "disease": "COPD (Chronic Obstructive Pulmonary Disease)",
            "description": "A group of lung diseases that block airflow and make breathing difficult.",
            "causes": "Smoking, long-term exposure to irritants, genetic conditions.",
            "symptoms": "Wheezing, chronic cough, shortness of breath, fatigue.",
            "treatment": "Bronchodilators, oxygen therapy, pulmonary rehabilitation.",
            "doctor": "Pulmonologist"
        }
    elif "chest pain" in symptoms:
        return {
            "disease": "Pneumonia",
            "description": "An infection that inflames the air sacs in one or both lungs.",
            "causes": "Bacteria, viruses, or fungi infecting the lungs.",
            "symptoms": "Chest pain, fever, cough with phlegm, difficulty breathing.",
            "treatment": "Antibiotics (if bacterial), antivirals (if viral), oxygen therapy if needed.",
            "doctor": "Pulmonologist"
        }
    elif "sore throat" in symptoms:
        return {
            "disease": "Strep Throat",
            "description": "A bacterial infection causing inflammation and pain in the throat.",
            "causes": "Caused by group A Streptococcus bacteria.",
            "symptoms": "Sore throat, swollen tonsils, fever, difficulty swallowing.",
            "treatment": "Antibiotics (penicillin or amoxicillin), pain relievers.",
            "doctor": "General physician or ENT specialist"
        }
    elif "runny nose" in symptoms:
        return {
            "disease": "Common Cold",
            "description": "A viral infection affecting the upper respiratory tract.",
            "causes": "Spread through respiratory droplets, commonly caused by rhinoviruses.",
            "symptoms": "Runny nose, sneezing, sore throat, mild cough.",
            "treatment": "Rest, fluids, over-the-counter cold medications.",
            "doctor": "General physician"
        }
    elif "nasal congestion" in symptoms:
        return {
            "disease": "Sinusitis",
            "description": "Inflammation or swelling of the sinuses due to infection or allergies.",
            "causes": "Bacterial, viral infections, allergies, or nasal polyps.",
            "symptoms": "Nasal congestion, headache, facial pain, postnasal drip.",
            "treatment": "Decongestants, nasal sprays, antibiotics (if bacterial).",
            "doctor": "ENT specialist"
        }
    elif "sneezing" in symptoms:
        return {
            "disease": "Allergic Rhinitis",
            "description": "An allergic reaction causing nasal inflammation.",
            "causes": "Dust, pollen, pet dander, mold, strong odors.",
            "symptoms": "Sneezing, runny nose, itchy eyes, nasal congestion.",
            "treatment": "Antihistamines, nasal corticosteroids, allergen avoidance.",
            "doctor": "Allergist"
        }
    elif "hoarseness" in symptoms:
        return {
            "disease": "Laryngitis",
            "description": "Inflammation of the voice box (larynx), leading to hoarseness.",
            "causes": "Viral infections, overuse of voice, smoking, acid reflux.",
            "symptoms": "Hoarseness, sore throat, dry cough, throat irritation.",
            "treatment": "Voice rest, hydration, steam inhalation, lozenges.",
            "doctor": "ENT specialist"
        }
    elif "coughing up blood" in symptoms:
        return {
            "disease": "Tuberculosis",
            "description": "A serious infectious disease that mainly affects the lungs.",
            "causes": "Caused by Mycobacterium tuberculosis, spread through airborne droplets.",
            "symptoms": "Coughing up blood, night sweats, weight loss, fever.",
            "treatment": "Long-term antibiotics (isoniazid, rifampin, ethambutol, pyrazinamide).",
            "doctor": "Pulmonologist"
        }
    elif "palpitations" in symptoms:
        return {
            "disease": "Arrhythmia",
            "description": "Irregular heartbeat that may be too fast, too slow, or irregular.",
            "causes": "Heart disease, stress, caffeine, alcohol, certain medications.",
            "symptoms": "Palpitations, dizziness, shortness of breath, chest discomfort.",
            "treatment": "Lifestyle changes, medications, pacemaker (if needed).",
            "doctor": "Cardiologist"
        }
    elif "high blood pressure" in symptoms:
        return {
            "disease": "Hypertension",
            "description": "A condition where the force of the blood against artery walls is too high.",
            "causes": "Obesity, high salt intake, stress, genetics, lack of exercise.",
            "symptoms": "Often no symptoms, but severe cases may cause headaches, dizziness, nosebleeds.",
            "treatment": "Lifestyle changes, antihypertensive medications.",
            "doctor": "General physician or Cardiologist"
        }
    elif "low blood pressure" in symptoms:
        return {
            "disease": "Hypotension",
            "description": "A condition where blood pressure is lower than normal, causing dizziness and fainting.",
            "causes": "Dehydration, heart problems, endocrine disorders, medications.",
            "symptoms": "Dizziness, fainting, blurry vision, nausea.",
            "treatment": "Increase salt intake, stay hydrated, wear compression stockings.",
            "doctor": "General physician"
        }
    elif "dizziness" in symptoms:
        return {
            "disease": "Vertigo",
            "description": "A sensation of spinning or loss of balance.",
            "causes": "Inner ear problems, low blood pressure, migraines, neurological conditions.",
            "symptoms": "Dizziness, nausea, loss of balance, blurred vision.",
            "treatment": "Vestibular rehabilitation, medications, lifestyle changes.",
            "doctor": "Neurologist or ENT specialist"
        }
    elif "fainting" in symptoms:
        return {
            "disease": "Syncope",
            "description": "A temporary loss of consciousness due to lack of blood flow to the brain.",
            "causes": "Low blood pressure, dehydration, heart problems, extreme stress.",
            "symptoms": "Sudden collapse, dizziness, weakness, blurred vision.",
            "treatment": "Stay hydrated, avoid prolonged standing, treat underlying cause.",
            "doctor": "Cardiologist or Neurologist"
        }
    elif "swelling in legs or feet" in symptoms:
        return {
            "disease": "Congestive Heart Failure",
            "description": "A chronic condition where the heart doesn't pump blood efficiently.",
            "causes": "High blood pressure, coronary artery disease, heart valve disease.",
            "symptoms": "Swelling in legs or feet, shortness of breath, fatigue, rapid heartbeat.",
            "treatment": "Medications, lifestyle changes, possible surgery.",
            "doctor": "Cardiologist"
        }
    elif "cold hands and feet" in symptoms:
        return {
            "disease": "Peripheral Artery Disease (PAD)",
            "description": "A condition where narrowed arteries reduce blood flow to the limbs.",
            "causes": "Smoking, diabetes, high cholesterol, high blood pressure.",
            "symptoms": "Cold hands and feet, leg pain while walking, numbness in extremities.",
            "treatment": "Medications, lifestyle changes, angioplasty (if severe).",
            "doctor": "Vascular specialist"
        }
    # 🧠 Neurological Symptoms
    elif "headache" in symptoms:
        return {
            "disease": "Migraine",
            "description": "A neurological condition that causes intense, throbbing headaches.",
            "causes": "Stress, hormonal changes, certain foods, lack of sleep.",
            "symptoms": "Headache, nausea, sensitivity to light and sound, visual disturbances.",
            "treatment": "Pain relievers, lifestyle changes, migraine-specific medications.",
            "doctor": "Neurologist"
        }
    elif "dizziness" in symptoms:
        return {
            "disease": "Vertigo",
            "description": "A sensation of spinning or loss of balance.",
            "causes": "Inner ear problems, low blood pressure, migraines, neurological conditions.",
            "symptoms": "Dizziness, nausea, loss of balance, blurred vision.",
            "treatment": "Vestibular rehabilitation, medications, lifestyle changes.",
            "doctor": "Neurologist or ENT specialist"
        }
    elif "confusion" in symptoms:
        return {
            "disease": "Dementia",
            "description": "A decline in cognitive function affecting memory, thinking, and reasoning.",
            "causes": "Alzheimer’s disease, stroke, brain injuries, infections.",
            "symptoms": "Confusion, memory loss, difficulty speaking, personality changes.",
            "treatment": "Medications, cognitive therapy, lifestyle modifications.",
            "doctor": "Neurologist"
        }
    elif "memory loss" in symptoms:
        return {
            "disease": "Alzheimer’s Disease",
            "description": "A progressive brain disorder causing memory decline and cognitive impairment.",
            "causes": "A buildup of amyloid plaques and tau tangles in the brain.",
            "symptoms": "Memory loss, confusion, difficulty recognizing people, mood changes.",
            "treatment": "Medications to slow progression, cognitive therapy, supportive care.",
            "doctor": "Neurologist"
        }
    elif "seizures" in symptoms:
        return {
            "disease": "Epilepsy",
            "description": "A neurological disorder causing recurrent seizures.",
            "causes": "Genetics, brain injuries, infections, stroke.",
            "symptoms": "Seizures, loss of consciousness, muscle stiffness, confusion after episodes.",
            "treatment": "Antiepileptic medications, surgery (if needed), lifestyle management.",
            "doctor": "Neurologist"
        }
    elif "numbness or tingling" in symptoms:
        return {
            "disease": "Peripheral Neuropathy",
            "description": "Damage to peripheral nerves, leading to numbness and weakness.",
            "causes": "Diabetes, infections, autoimmune diseases, vitamin deficiencies.",
            "symptoms": "Numbness, tingling, burning pain, muscle weakness.",
            "treatment": "Managing underlying condition, medications, physical therapy.",
            "doctor": "Neurologist"
        }
    elif "weakness in limbs" in symptoms:
        return {
            "disease": "Multiple Sclerosis (MS)",
            "description": "An autoimmune disease affecting the brain and spinal cord.",
            "causes": "Immune system attacks myelin sheath covering nerve fibers.",
            "symptoms": "Weakness in limbs, vision problems, balance issues, fatigue.",
            "treatment": "Immunosuppressive drugs, physical therapy, lifestyle adjustments.",
            "doctor": "Neurologist"
        }
    elif "difficulty walking" in symptoms:
        return {
            "disease": "Parkinson’s Disease",
            "description": "A progressive nervous system disorder affecting movement.",
            "causes": "Loss of dopamine-producing neurons in the brain.",
            "symptoms": "Tremors, stiffness, difficulty walking, slow movements.",
            "treatment": "Medications to boost dopamine levels, physical therapy, surgery in severe cases.",
            "doctor": "Neurologist"
        }
    elif "slurred speech" in symptoms:
        return {
            "disease": "Stroke",
            "description": "A medical emergency where blood supply to the brain is interrupted.",
            "causes": "Blood clot (ischemic stroke) or burst blood vessel (hemorrhagic stroke).",
            "symptoms": "Slurred speech, facial drooping, weakness on one side, confusion.",
            "treatment": "Emergency care, clot-busting drugs, rehabilitation therapy.",
            "doctor": "Neurologist"
        }
    elif "tremors" in symptoms:
        return {
            "disease": "Essential Tremor",
            "description": "A nervous system disorder causing involuntary shaking movements.",
            "causes": "Genetics, age-related nerve degeneration, unknown factors.",
            "symptoms": "Tremors in hands, head, voice, or legs.",
            "treatment": "Beta-blockers, anti-seizure medications, deep brain stimulation (if needed).",
            "doctor": "Neurologist"
        }
     # 👂 Ear Symptoms
    elif "ear pain" in symptoms:
        return {
            "disease": "Ear Infection (Otitis Media)",
            "description": "An infection in the middle ear, often caused by bacteria or viruses.",
            "causes": "Cold, flu, allergies, sinus infections, or fluid buildup in the ear.",
            "symptoms": "Ear pain, fever, difficulty hearing, fluid drainage.",
            "treatment": "Pain relievers, antibiotics (if bacterial), warm compresses.",
            "doctor": "ENT specialist"
        }
    elif "hearing loss" in symptoms:
        return {
            "disease": "Sensorineural Hearing Loss",
            "description": "Hearing loss due to damage to the inner ear or auditory nerve.",
            "causes": "Aging, loud noise exposure, infections, genetics.",
            "symptoms": "Gradual or sudden hearing loss, difficulty understanding speech.",
            "treatment": "Hearing aids, cochlear implants, auditory therapy.",
            "doctor": "Audiologist or ENT specialist"
        }
    elif "ringing in the ears" in symptoms:
        return {
            "disease": "Tinnitus",
            "description": "A ringing, buzzing, or hissing sound in the ears without an external source.",
            "causes": "Hearing loss, ear infections, exposure to loud noise, earwax buildup.",
            "symptoms": "Persistent ringing or buzzing in the ears, sensitivity to sound.",
            "treatment": "Hearing aids, sound therapy, cognitive behavioral therapy.",
            "doctor": "Audiologist or ENT specialist"
        }
    elif "ear drainage" in symptoms:
        return {
            "disease": "Swimmer’s Ear (Otitis Externa)",
            "description": "An outer ear infection due to trapped water, bacteria, or fungi.",
            "causes": "Prolonged moisture in the ear, injury, allergies.",
            "symptoms": "Ear pain, itching, fluid drainage, redness, swelling.",
            "treatment": "Antibiotic or antifungal ear drops, pain relief, keeping the ear dry.",
            "doctor": "ENT specialist"
        }
     # 🦷 Dental Symptoms
    elif "toothache" in symptoms:
        return {
            "disease": "Dental Cavity (Tooth Decay)",
            "description": "Damage to the tooth's surface due to bacteria and acid buildup.",
            "causes": "Poor oral hygiene, sugary foods, plaque buildup.",
            "symptoms": "Tooth pain, sensitivity to hot/cold, visible holes or dark spots.",
            "treatment": "Fillings, fluoride treatments, root canal if severe.",
            "doctor": "Dentist"
        }
    elif "swollen gums" in symptoms:
        return {
            "disease": "Gingivitis",
            "description": "Inflammation of the gums caused by plaque buildup.",
            "causes": "Poor oral hygiene, smoking, diabetes, certain medications.",
            "symptoms": "Red, swollen gums, bleeding when brushing, bad breath.",
            "treatment": "Regular brushing/flossing, professional dental cleaning.",
            "doctor": "Dentist"
        }
    elif "bleeding gums" in symptoms:
        return {
            "disease": "Periodontitis (Gum Disease)",
            "description": "A severe gum infection that damages the soft tissue and bone supporting teeth.",
            "causes": "Untreated gingivitis, poor oral hygiene, smoking, diabetes.",
            "symptoms": "Bleeding gums, receding gums, loose teeth, bad breath.",
            "treatment": "Deep cleaning, antibiotics, surgery in severe cases.",
            "doctor": "Dentist or Periodontist"
        }
    elif "bad breath" in symptoms:
        return {
            "disease": "Halitosis (Chronic Bad Breath)",
            "description": "Persistent bad breath caused by bacteria, food, or health conditions.",
            "causes": "Poor oral hygiene, gum disease, dry mouth, infections.",
            "symptoms": "Unpleasant breath odor that doesn’t go away with brushing.",
            "treatment": "Good oral hygiene, mouthwash, treating underlying conditions.",
            "doctor": "Dentist"
        }
    elif "sensitivity to hot or cold" in symptoms:
        return {
            "disease": "Tooth Sensitivity",
            "description": "Discomfort or pain when consuming hot, cold, or sweet foods.",
            "causes": "Worn enamel, receding gums, cavities, cracked teeth.",
            "symptoms": "Sharp pain when eating/drinking hot, cold, or sugary items.",
            "treatment": "Desensitizing toothpaste, fluoride treatment, dental sealants.",
            "doctor": "Dentist"
        }
    # 🦴 Musculoskeletal Symptoms
    elif "joint pain" in symptoms:
        return {
            "disease": "Arthritis",
            "description": "Inflammation of one or more joints, causing pain and stiffness.",
            "causes": "Age, wear and tear, autoimmune diseases, infections.",
            "symptoms": "Joint pain, stiffness, swelling, decreased range of motion.",
            "treatment": "Pain relievers, physical therapy, lifestyle changes, surgery in severe cases.",
            "doctor": "Rheumatologist or Orthopedic Specialist"
        }
    elif "swelling in joints" in symptoms:
        return {
            "disease": "Rheumatoid Arthritis",
            "description": "An autoimmune disorder where the immune system attacks the joints.",
            "causes": "Immune system dysfunction, genetic factors, environmental triggers.",
            "symptoms": "Swollen, tender joints, morning stiffness, fatigue.",
            "treatment": "Anti-inflammatory medications, physical therapy, immunosuppressants.",
            "doctor": "Rheumatologist"
        }
    elif "muscle weakness" in symptoms:
        return {
            "disease": "Myasthenia Gravis",
            "description": "A chronic autoimmune disorder causing muscle weakness.",
            "causes": "Immune system attacking nerve-muscle communication.",
            "symptoms": "Weakness in arms, legs, difficulty swallowing or breathing.",
            "treatment": "Medications, physical therapy, in severe cases surgery.",
            "doctor": "Neurologist"
        }
    elif "back pain" in symptoms:
        return {
            "disease": "Herniated Disc",
            "description": "A condition where a spinal disc slips out of place, pressing on nerves.",
            "causes": "Age, injury, improper lifting, repetitive strain.",
            "symptoms": "Back pain, leg pain (sciatica), numbness, tingling.",
            "treatment": "Physical therapy, pain relievers, surgery in severe cases.",
            "doctor": "Orthopedic Specialist or Neurosurgeon"
        }
    elif "stiffness" in symptoms:
        return {
            "disease": "Ankylosing Spondylitis",
            "description": "A type of arthritis affecting the spine, causing stiffness and pain.",
            "causes": "Genetic factors, immune system malfunction.",
            "symptoms": "Lower back stiffness, pain, limited spinal mobility.",
            "treatment": "Anti-inflammatory medications, exercise, physical therapy.",
            "doctor": "Rheumatologist"
        }
    elif "muscle cramps" in symptoms:
        return {
            "disease": "Electrolyte Imbalance",
            "description": "An imbalance of minerals affecting muscle function.",
            "causes": "Dehydration, kidney disease, excessive sweating, medications.",
            "symptoms": "Painful muscle cramps, weakness, irregular heartbeat.",
            "treatment": "Hydration, electrolyte supplements, treating underlying conditions.",
            "doctor": "General Physician"
        }
    # 🔬 Skin Symptoms
    elif "rash" in symptoms:
        return {
            "disease": "Eczema",
            "description": "A condition that makes the skin red, itchy, and inflamed.",
            "causes": "Genetics, allergens, irritants, immune system dysfunction.",
            "symptoms": "Itchy, dry, red, inflamed skin, sometimes with blisters.",
            "treatment": "Moisturizers, anti-inflammatory creams, avoiding triggers.",
            "doctor": "Dermatologist"
        }
    elif "itching" in symptoms:
        return {
            "disease": "Allergic Reaction",
            "description": "A hypersensitive response of the immune system to allergens.",
            "causes": "Food, medications, insect stings, pollen, pet dander.",
            "symptoms": "Itchy skin, hives, swelling, redness.",
            "treatment": "Antihistamines, corticosteroids, avoiding allergens.",
            "doctor": "Allergist or Dermatologist"
        }
    elif "dry skin" in symptoms:
        return {
            "disease": "Xerosis (Dry Skin)",
            "description": "A condition where the skin becomes excessively dry and scaly.",
            "causes": "Cold weather, dehydration, harsh soaps, aging.",
            "symptoms": "Rough, flaky, or cracked skin, sometimes itchy.",
            "treatment": "Moisturizers, hydration, avoiding harsh soaps.",
            "doctor": "Dermatologist"
        }
    elif "peeling skin" in symptoms:
        return {
            "disease": "Sunburn",
            "description": "Skin damage due to excessive exposure to ultraviolet (UV) rays.",
            "causes": "Prolonged sun exposure without protection.",
            "symptoms": "Red, painful, peeling skin, sometimes with blisters.",
            "treatment": "Aloe vera, cool compress, pain relievers, hydration.",
            "doctor": "Dermatologist"
        }
    elif "hives" in symptoms:
        return {
            "disease": "Urticaria (Hives)",
            "description": "A skin reaction that causes itchy, red welts.",
            "causes": "Allergens, stress, infections, medications.",
            "symptoms": "Raised, itchy, red or skin-colored welts.",
            "treatment": "Antihistamines, avoiding triggers, corticosteroids in severe cases.",
            "doctor": "Allergist or Dermatologist"
        }
    elif "bruising easily" in symptoms:
        return {
            "disease": "Vitamin Deficiency (Vitamin C or K Deficiency)",
            "description": "A condition where the body lacks essential vitamins affecting blood clotting and skin health.",
            "causes": "Poor diet, medical conditions affecting absorption.",
            "symptoms": "Easy bruising, bleeding gums, slow wound healing.",
            "treatment": "Vitamin supplements, a balanced diet rich in fruits and vegetables.",
            "doctor": "General Physician"
        }
    elif "skin discoloration" in symptoms:
        return {
            "disease": "Vitiligo",
            "description": "A condition where the skin loses pigment, leading to white patches.",
            "causes": "Autoimmune response attacking pigment-producing cells.",
            "symptoms": "White patches on the skin, often on hands, face, and joints.",
            "treatment": "Topical corticosteroids, light therapy, cosmetic camouflage.",
            "doctor": "Dermatologist"
        }
    elif "swelling" in symptoms:
        return {
            "disease": "Angioedema",
            "description": "A condition causing deep swelling under the skin, often around the eyes, lips, or throat.",
            "causes": "Allergic reactions, genetic factors, medications.",
            "symptoms": "Sudden swelling of skin and mucous membranes, sometimes painful.",
            "treatment": "Antihistamines, epinephrine in severe cases, avoiding triggers.",
            "doctor": "Allergist or Dermatologist"
        }
    # 🧴 Endocrine Symptoms
    elif "unexplained weight gain" in symptoms or "weight gain" in symptoms:
        return {
            "disease": "Hypothyroidism",
            "description": "A condition where the thyroid gland doesn't produce enough hormones.",
            "causes": "Autoimmune diseases, iodine deficiency, certain medications.",
            "symptoms": "Fatigue, weight gain, cold intolerance, slow metabolism.",
            "treatment": "Thyroid hormone replacement therapy.",
            "doctor": "Endocrinologist"
        }
    elif "unexplained weight loss" in symptoms or "weight loss" in symptoms:
        return {
            "disease": "Hyperthyroidism",
            "description": "A condition where the thyroid gland produces excessive hormones.",
            "causes": "Graves' disease, thyroid nodules, excessive iodine intake.",
            "symptoms": "Unintentional weight loss, rapid heartbeat, excessive sweating, tremors.",
            "treatment": "Anti-thyroid medications, radioactive iodine, surgery in severe cases.",
            "doctor": "Endocrinologist"
        }
    elif "increased thirst" in symptoms or "excessive thirst" in symptoms:
        return {
            "disease": "Diabetes Mellitus",
            "description": "A metabolic disorder where blood sugar levels are too high due to insulin problems.",
            "causes": "Genetics, lifestyle factors, autoimmune response.",
            "symptoms": "Increased thirst, frequent urination, fatigue, blurred vision.",
            "treatment": "Insulin therapy, oral medications, lifestyle changes.",
            "doctor": "Endocrinologist"
        }
    elif "increased urination" in symptoms:
        return {
            "disease": "Diabetes Insipidus",
            "description": "A condition causing excessive urination due to problems with the kidney's ability to retain water.",
            "causes": "Hormonal imbalance, kidney disease, genetic disorders.",
            "symptoms": "Extreme thirst, frequent urination, dehydration.",
            "treatment": "Desmopressin (hormone therapy), hydration management.",
            "doctor": "Endocrinologist"
        }
    elif "hair loss" in symptoms:
        return {
            "disease": "Alopecia",
            "description": "An autoimmune condition that causes hair loss on the scalp and other parts of the body.",
            "causes": "Autoimmune disorder, genetics, stress, thyroid imbalance.",
            "symptoms": "Hair thinning, bald patches, excessive hair shedding.",
            "treatment": "Topical steroids, minoxidil, lifestyle modifications.",
            "doctor": "Dermatologist or Endocrinologist"
        }
    elif "increased body hair growth" in symptoms:
        return {
            "disease": "Hirsutism",
            "description": "Excessive hair growth in women in areas where men typically grow hair.",
            "causes": "Polycystic ovary syndrome (PCOS), hormonal imbalance, genetics.",
            "symptoms": "Coarse, dark hair growth on face, chest, back.",
            "treatment": "Hormonal therapy, laser hair removal, lifestyle changes.",
            "doctor": "Endocrinologist or Gynecologist"
        }
    elif "cold intolerance" in symptoms:
        return {
            "disease": "Hypothyroidism",
            "description": "A condition where the thyroid gland doesn't produce enough hormones.",
            "causes": "Autoimmune diseases, iodine deficiency, certain medications.",
            "symptoms": "Cold intolerance, weight gain, fatigue, slow metabolism.",
            "treatment": "Thyroid hormone replacement therapy.",
            "doctor": "Endocrinologist"
        }
    elif "heat intolerance" in symptoms:
        return {
            "disease": "Hyperthyroidism",
            "description": "A condition where the thyroid gland produces excessive hormones.",
            "causes": "Graves' disease, thyroid nodules, excessive iodine intake.",
            "symptoms": "Heat intolerance, sweating, weight loss, rapid heartbeat.",
            "treatment": "Anti-thyroid medications, radioactive iodine, surgery in severe cases.",
            "doctor": "Endocrinologist"
        }
    # 🚺 Female-Specific Symptoms
    elif "irregular periods" in symptoms:
        return {
            "disease": "Polycystic Ovary Syndrome (PCOS)",
            "description": "A hormonal disorder causing enlarged ovaries with small cysts.",
            "causes": "Hormonal imbalance, insulin resistance, genetics.",
            "symptoms": "Irregular periods, weight gain, acne, excessive hair growth.",
            "treatment": "Birth control pills, lifestyle changes, hormonal therapy.",
            "doctor": "Gynecologist"
        }
    elif "heavy bleeding" in symptoms:
        return {
            "disease": "Menorrhagia",
            "description": "Excessive menstrual bleeding that lasts longer than usual.",
            "causes": "Hormonal imbalances, uterine fibroids, polyps, blood disorders.",
            "symptoms": "Heavy or prolonged periods, fatigue, anemia.",
            "treatment": "Hormonal therapy, iron supplements, surgery in severe cases.",
            "doctor": "Gynecologist"
        }
    elif "pelvic pain" in symptoms:
        return {
            "disease": "Endometriosis",
            "description": "A condition where tissue similar to the uterine lining grows outside the uterus.",
            "causes": "Unknown, but linked to genetics, immune system disorders, and retrograde menstruation.",
            "symptoms": "Pelvic pain, painful periods, infertility, painful intercourse.",
            "treatment": "Pain relievers, hormone therapy, surgery in severe cases.",
            "doctor": "Gynecologist"
        }
    elif "breast lumps" in symptoms:
        return {
            "disease": "Fibrocystic Breast Changes",
            "description": "Noncancerous changes in breast tissue that may cause lumps or discomfort.",
            "causes": "Hormonal fluctuations during the menstrual cycle.",
            "symptoms": "Breast lumps, tenderness, swelling before periods.",
            "treatment": "Pain management, lifestyle changes, supportive bras.",
            "doctor": "Gynecologist or Breast Specialist"
        }
    elif "pain during intercourse" in symptoms:
        return {
            "disease": "Dyspareunia",
            "description": "Painful sexual intercourse due to medical or psychological causes.",
            "causes": "Infections, hormonal changes, pelvic disorders, psychological factors.",
            "symptoms": "Pain during intercourse, vaginal dryness, discomfort.",
            "treatment": "Lubricants, pelvic floor therapy, hormonal treatments.",
            "doctor": "Gynecologist"
        }
     # 🚺 Female-Specific Symptoms
    elif "period cramps" in symptoms or "menstrual cramps" in symptoms:
        return {
            "disease": "Dysmenorrhea (Menstrual Cramps)",
            "description": "Painful cramps during menstruation caused by uterine contractions.",
            "causes": "Hormonal changes, uterine contractions, conditions like endometriosis or fibroids.",
            "symptoms": "Lower abdominal pain, lower back pain, nausea, fatigue, headaches.",
            "treatment": "Pain relievers (ibuprofen), heat therapy, exercise, hormonal birth control.",
            "doctor": "Gynecologist"
        }
     # 🚹 Male-Specific Symptoms
    elif "erectile dysfunction" in symptoms:
        return {
            "disease": "Erectile Dysfunction (ED)",
            "description": "The inability to achieve or maintain an erection for satisfactory sexual activity.",
            "causes": "Poor blood flow, nerve damage, stress, diabetes, high blood pressure.",
            "symptoms": "Difficulty getting or maintaining an erection, reduced sexual desire.",
            "treatment": "Lifestyle changes, medications like sildenafil (Viagra), therapy.",
            "doctor": "Urologist"
        }
    elif "testicular pain" in symptoms:
        return {
            "disease": "Testicular Torsion",
            "description": "A medical emergency where the spermatic cord twists, cutting off blood supply to the testicle.",
            "causes": "Congenital testicular abnormalities, trauma, or spontaneous twisting.",
            "symptoms": "Sudden severe testicular pain, swelling, nausea, vomiting.",
            "treatment": "Emergency surgery to untwist the cord.",
            "doctor": "Urologist or Emergency Care"
        }
    elif "enlarged prostate" in symptoms:
        return {
            "disease": "Benign Prostatic Hyperplasia (BPH)",
            "description": "A noncancerous enlargement of the prostate gland that can affect urination.",
            "causes": "Aging, hormonal changes, genetic factors.",
            "symptoms": "Frequent urination, weak urine stream, difficulty starting urination.",
            "treatment": "Medications, lifestyle changes, surgery in severe cases.",
            "doctor": "Urologist"
        }
    elif "breast swelling" in symptoms:
        return {
            "disease": "Gynecomastia",
            "description": "The enlargement of male breast tissue due to hormonal imbalance.",
            "causes": "Hormonal changes, obesity, certain medications, liver disease.",
            "symptoms": "Swelling of breast tissue, tenderness, nipple sensitivity.",
            "treatment": "Lifestyle changes, medication, surgery in severe cases.",
            "doctor": "Endocrinologist or General Physician"
        }
    # 🛑 Mental Health Symptoms
    elif "depression" in symptoms:
        return {
            "disease": "Depression",
            "description": "A mood disorder causing persistent sadness and loss of interest.",
            "causes": "Genetics, brain chemistry, trauma, stress, medical conditions.",
            "symptoms": "Persistent sadness, loss of interest, fatigue, changes in appetite or sleep.",
            "treatment": "Therapy, medications (antidepressants), lifestyle changes.",
            "doctor": "Psychiatrist or Psychologist"
        }
    elif "anxiety" in symptoms:
        return {
            "disease": "Anxiety Disorder",
            "description": "A mental health condition causing excessive fear, worry, or nervousness.",
            "causes": "Genetics, stress, trauma, medical conditions, substance abuse.",
            "symptoms": "Excessive worry, restlessness, rapid heartbeat, sweating, dizziness.",
            "treatment": "Therapy, medications (anti-anxiety drugs), relaxation techniques.",
            "doctor": "Psychiatrist or Psychologist"
        }
    elif "mood swings" in symptoms:
        return {
            "disease": "Bipolar Disorder",
            "description": "A mental illness characterized by extreme mood swings between mania and depression.",
            "causes": "Genetic factors, brain chemistry, stress, traumatic events.",
            "symptoms": "Periods of mania (high energy, impulsivity) and depression (low energy, sadness).",
            "treatment": "Mood stabilizers, therapy, lifestyle adjustments.",
            "doctor": "Psychiatrist"
        }
    elif "hallucinations" in symptoms:
        return {
            "disease": "Schizophrenia",
            "description": "A severe mental disorder affecting thinking, emotions, and behavior.",
            "causes": "Genetics, brain chemistry, environment, substance abuse.",
            "symptoms": "Hallucinations, delusions, disorganized speech, social withdrawal.",
            "treatment": "Antipsychotic medications, therapy, social support.",
            "doctor": "Psychiatrist"
        }
    elif "suicidal thoughts" in symptoms:
        return {
            "disease": "Suicidal Ideation",
            "description": "Persistent thoughts of wanting to end one’s life, often due to mental illness.",
            "causes": "Depression, trauma, stress, social isolation, substance abuse.",
            "symptoms": "Thinking about or planning suicide, feeling hopeless, withdrawal from others.",
            "treatment": "Immediate crisis intervention, therapy, medications.",
            "doctor": "Psychiatrist, Crisis Hotline, Emergency Care"
        }
    elif "panic attacks" in symptoms:
        return {
            "disease": "Panic Disorder",
            "description": "An anxiety disorder that causes sudden, intense episodes of fear.",
            "causes": "Genetic predisposition, trauma, high stress, certain medical conditions.",
            "symptoms": "Sudden fear, rapid heartbeat, chest pain, dizziness, shortness of breath.",
            "treatment": "Therapy, anti-anxiety medications, relaxation techniques.",
            "doctor": "Psychiatrist or Psychologist"
        }
    else:
        # Default analysis when no specific condition matches
        return {
            "disease": "General Health Concern",
            "description": "Based on your symptoms, we couldn't identify a specific condition. This could be due to various factors including stress, minor infections, or lifestyle factors.",
            "causes": "Symptoms can arise from many sources including stress, lack of sleep, dehydration, minor viral infections, or dietary issues.",
            "symptoms": symptoms.title() if symptoms else "Various symptoms reported",
            "treatment": "Rest well, stay hydrated, eat nutritious food, and monitor your symptoms. If symptoms persist for more than a few days or worsen, please consult a healthcare professional.",
            "doctor": "General Physician or Family Doctor"
        }


def predict_disease_with_context(symptoms, age=None, gender=None, existing_conditions=None, affected_area=None, severity=5):
    """
    Enhanced disease prediction that considers patient context.
    Returns prediction with reasoning and rural medicine suggestions.
    """
    # Get base prediction
    base_prediction = predict_disease(symptoms)
    
    # Add context-based adjustments and reasoning
    reasoning = []
    rural_medicines = []
    warnings = []
    
    # Age-based considerations
    if age:
        if age < 5:
            reasoning.append(f"Patient is a young child (age {age}), pediatric considerations apply")
            warnings.append("Consult a pediatrician for children under 5")
        elif age > 60:
            reasoning.append(f"Patient is elderly (age {age}), may need adjusted dosages")
            warnings.append("Monitor for drug interactions with any existing medications")
    
    # Gender-based considerations
    if gender:
        reasoning.append(f"Patient gender: {gender}")
    
    # Existing conditions considerations
    if existing_conditions:
        conditions = existing_conditions.split(',') if isinstance(existing_conditions, str) else []
        if conditions:
            reasoning.append(f"Patient has existing conditions: {', '.join(conditions)}")
            if 'diabetes' in existing_conditions.lower():
                warnings.append("Diabetic patient - monitor blood sugar levels during treatment")
            if 'hypertension' in existing_conditions.lower():
                warnings.append("Hypertensive patient - avoid medications that raise blood pressure")
    
    # Severity-based urgency
    urgency = "Low"
    if severity >= 7:
        urgency = "High"
        warnings.append("High severity symptoms - seek medical attention promptly")
    elif severity >= 4:
        urgency = "Medium"
    
    # Rural pharmacy medicine suggestions (commonly available)
    disease = base_prediction.get('disease', '').lower()
    if 'flu' in disease or 'fever' in disease:
        rural_medicines = [
            {"name": "Paracetamol 500mg", "usage": "For fever, 1 tablet every 6 hours", "price": "₹10-15"},
            {"name": "ORS Packets", "usage": "Prevent dehydration, 1 packet in 1L water", "price": "₹10-20"},
            {"name": "Cetirizine 10mg", "usage": "For cold symptoms, 1 tablet at night", "price": "₹5-10"}
        ]
    elif 'diabetes' in disease:
        rural_medicines = [
            {"name": "Metformin 500mg", "usage": "As prescribed by doctor", "price": "₹20-40"},
            {"name": "Blood Glucose Test Strips", "usage": "Monitor sugar levels daily", "price": "₹400-600"}
        ]
    elif 'hypertension' in disease or 'blood pressure' in disease:
        rural_medicines = [
            {"name": "Amlodipine 5mg", "usage": "As prescribed by doctor", "price": "₹30-50"},
            {"name": "BP Monitor (digital)", "usage": "Check BP twice daily", "price": "₹800-1500"}
        ]
    elif 'gastritis' in disease or 'stomach' in disease:
        rural_medicines = [
            {"name": "Pantoprazole 40mg", "usage": "1 tablet before breakfast", "price": "₹30-50"},
            {"name": "Antacid Gel", "usage": "10ml after meals", "price": "₹50-80"},
            {"name": "ORS Packets", "usage": "For hydration", "price": "₹10-20"}
        ]
    else:
        rural_medicines = [
            {"name": "Paracetamol 500mg", "usage": "For pain/fever relief", "price": "₹10-15"},
            {"name": "Multivitamin tablets", "usage": "1 tablet daily for general health", "price": "₹50-100"}
        ]
    
    # Combine everything into enhanced prediction
    enhanced_prediction = {
        **base_prediction,
        "reasoning": reasoning,
        "warnings": warnings,
        "urgency": urgency,
        "rural_medicines": rural_medicines,
        "affected_area": affected_area,
        "severity_level": severity,
        "context_aware": True
    }
    
    return enhanced_prediction



@app.route('/image_diagnosis', methods=['POST'])
@login_required
def image_diagnosis():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        # Secure filename
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Placeholder for image analysis model (Replace with actual model logic)
        prediction = "Possible skin condition detected. Consult a doctor."

        return jsonify({"prediction": prediction, "image_path": url_for('static', filename=f'uploads/{filename}', _external=True)}), 200

    except Exception as e:
        logging.error(f"Error processing image: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to process the image. Please try again later."}), 500


@app.route('/upload_eye_image', methods=['POST'])
def upload_eye_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file found'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    return jsonify({'message': 'Image uploaded successfully', 'file_path': filepath}), 200
#-------------------------------
def predict_eye_disease(image_path):
    diseases = ["Normal"]
    return random.choice(diseases)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    file = request.files['image']

    if file.filename == 'blob':  # If it's a captured camera image
        image = Image.open(io.BytesIO(file.read()))
        filename = f"captured_{random.randint(1000, 9999)}.png"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)
    else:  # If it's an uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

    # Predict disease
    result = predict_eye_disease(filepath)

    return jsonify({'result': result, 'image_url': url_for('static', filename=f'uploads/{filename}')})

#--------------------------------------------
# Helper function to save base64 camera images
def save_camera_image(base64_data, prefix='camera'):
    """Save base64 image data to file and return filepath"""
    import re
    
    # Extract base64 data (remove data:image/jpeg;base64, prefix if present)
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]
    
    # Decode and save
    image_data = base64.b64decode(base64_data)
    filename = f"{prefix}_{random.randint(1000, 9999)}.jpg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    with open(filepath, 'wb') as f:
        f.write(image_data)
    
    return filepath, filename

#--------------------------------------------
# Prescription Upload and OCR
#--------------------------------------------
@app.route('/prescription_upload')
@login_required
def prescription_upload():
    return render_template('prescription_upload.html')

@app.route('/new_prescription', methods=['POST'])
@login_required
def new_prescription():
    """Process prescription image with OCR and save to database"""
    from utils import extract_prescription_text, parse_prescription
    
    filepath = None
    filename = None
    
    # Handle camera image (base64)
    camera_image = request.form.get('camera_image')
    if camera_image and camera_image.strip():
        try:
            filepath, filename = save_camera_image(camera_image, 'prescription')
        except Exception as e:
            flash(f'Error processing camera image: {str(e)}', 'danger')
            return redirect(url_for('prescription_upload'))
    
    # Handle file upload
    elif 'prescription_image' in request.files:
        file = request.files['prescription_image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
    
    if not filepath:
        flash('Please upload an image or capture a photo.', 'danger')
        return redirect(url_for('prescription_upload'))
    
    # Get selected language
    language = request.form.get('language', 'english')
    
    # Extract text using OCR
    ocr_result = extract_prescription_text(filepath, language=language)
    
    # Parse the prescription
    parsed = parse_prescription(ocr_result.get('raw_text', ''))
    
    # Save prescription to database
    prescription = Prescription(
        user_id=current_user.id,
        image_path=f'uploads/{filename}',
        raw_text=ocr_result.get('raw_text', ''),
        language=language,
        confidence=ocr_result.get('confidence', 0),
        doctor_name=parsed.get('doctor_name')
    )
    db.session.add(prescription)
    db.session.flush()  # Get the ID before committing
    
    # Save parsed medicines
    for med in parsed.get('medications', []):
        medicine = Medicine(
            prescription_id=prescription.id,
            name=med.get('name', 'Unknown'),
            dosage=med.get('dosage'),
            frequency=med.get('frequency'),
            duration=med.get('duration'),
            instructions=med.get('instructions')
        )
        db.session.add(medicine)
    
    db.session.commit()
    
    # Prepare result for display
    result = {
        'image_url': url_for('static', filename=f'uploads/{filename}'),
        'raw_text': ocr_result.get('raw_text', ''),
        'confidence': ocr_result.get('confidence', 0),
        'language': language,
        'parsed': parsed,
        'prescription_id': prescription.id
    }
    
    return render_template('prescription_result.html', result=result)

@app.route('/prescription_history')
@login_required
def prescription_history():
    """View prescription history from database"""
    prescriptions = Prescription.query.filter_by(user_id=current_user.id)\
        .order_by(Prescription.created_at.desc())\
        .all()
    return render_template('prescription_history.html', prescriptions=prescriptions)

#--------------------------------------------
# Symptom Report with image support
#--------------------------------------------
@app.route('/symptom_input')
@login_required
def symptom_input():
    return render_template('symptom_input.html')

@app.route('/new_symptom_report', methods=['POST'])
@login_required
def new_symptom_report():
    """Process symptom report with optional image and save to database"""
    symptoms = request.form.get('symptoms', '')
    affected_area = request.form.get('affected_area', '')
    severity = request.form.get('severity', '5')
    duration = request.form.get('duration', '')
    
    # Handle camera image
    image_path = None
    camera_image = request.form.get('camera_image')
    if camera_image and camera_image.strip():
        try:
            filepath, filename = save_camera_image(camera_image, 'symptom')
            image_path = f'uploads/{filename}'
        except Exception as e:
            logging.error(f"Error saving symptom image: {e}")
    
    # Handle file upload
    elif 'symptom_image' in request.files:
        file = request.files['symptom_image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_path = f'uploads/{filename}'
    
    # Get AI prediction with context
    prediction = predict_disease_with_context(
        symptoms=symptoms,
        age=current_user.age,
        gender=current_user.gender,
        existing_conditions=current_user.existing_conditions,
        affected_area=affected_area,
        severity=int(severity) if severity else 5
    )
    
    # Calculate confidence score (0.6-0.95 range based on symptom specificity)
    confidence_score = min(0.95, 0.6 + (len(symptoms.split()) * 0.02) + (0.1 if affected_area else 0))
    
    # Save to database
    symptom_report = SymptomReport(
        user_id=current_user.id,
        symptoms_text=symptoms,
        affected_area=affected_area,
        severity=int(severity) if severity else 5,
        duration=duration,
        image_path=image_path,
        ai_prediction=json.dumps(prediction),
        confidence_score=confidence_score,
        doctor_approved=False
    )
    db.session.add(symptom_report)
    db.session.commit()
    
    # Flash success and redirect
    flash('Symptom report submitted successfully!', 'success')
    
    return render_template('symptom_result.html', 
                         symptoms=symptoms,
                         affected_area=affected_area,
                         severity=severity,
                         duration=duration,
                         image_path=url_for('static', filename=image_path) if image_path else None,
                         prediction=prediction,
                         confidence_score=round(confidence_score * 100),
                         report_id=symptom_report.id)


# Vitals input
#--------------------------------------------
@app.route('/vitals_input')
@login_required
def vitals_input():
    return render_template('vitals_input.html')

@app.route('/new_vital_record', methods=['POST'])
@login_required
def new_vital_record():
    """Save vital signs to database with alert detection"""
    
    # Parse form data with safe type conversion
    def safe_int(val):
        try:
            return int(val) if val else None
        except:
            return None
    
    def safe_float(val):
        try:
            return float(val) if val else None
        except:
            return None
    
    bp_sys = safe_int(request.form.get('bp_systolic'))
    bp_dia = safe_int(request.form.get('bp_diastolic'))
    glucose = safe_float(request.form.get('glucose'))
    temperature = safe_float(request.form.get('temperature'))
    heart_rate = safe_int(request.form.get('heart_rate'))
    oxygen = safe_int(request.form.get('oxygen'))
    weight = safe_float(request.form.get('weight'))
    notes = request.form.get('notes', '')
    
    # Determine alert level based on values
    alert_level = 'normal'
    alerts = []
    
    if bp_sys:
        if bp_sys >= 180 or (bp_dia and bp_dia >= 120):
            alert_level = 'critical'
            alerts.append('Blood pressure critically high')
        elif bp_sys >= 140 or (bp_dia and bp_dia >= 90):
            alert_level = 'warning' if alert_level != 'critical' else alert_level
            alerts.append('Blood pressure elevated')
    
    if glucose:
        if glucose > 250 or glucose < 70:
            alert_level = 'critical'
            alerts.append('Blood glucose critical')
        elif glucose > 180 or glucose < 100:
            alert_level = 'warning' if alert_level != 'critical' else alert_level
            alerts.append('Blood glucose abnormal')
    
    if temperature:
        if temperature >= 103:
            alert_level = 'critical'
            alerts.append('High fever detected')
        elif temperature >= 100.4:
            alert_level = 'warning' if alert_level != 'critical' else alert_level
            alerts.append('Fever detected')
    
    if oxygen and oxygen < 90:
        alert_level = 'critical'
        alerts.append('Low oxygen saturation')
    elif oxygen and oxygen < 95:
        alert_level = 'warning' if alert_level != 'critical' else alert_level
        alerts.append('Oxygen saturation below normal')
    
    # Create vital record
    vital_record = VitalRecord(
        user_id=current_user.id,
        bp_systolic=bp_sys,
        bp_diastolic=bp_dia,
        blood_glucose=glucose,
        temperature=temperature,
        heart_rate=heart_rate,
        oxygen_saturation=oxygen,
        weight=weight,
        notes=notes,
        alert_level=alert_level
    )
    db.session.add(vital_record)
    db.session.commit()
    
    # Prepare analysis for template
    vitals = {
        'blood_pressure_systolic': bp_sys,
        'blood_pressure_diastolic': bp_dia,
        'blood_glucose': glucose,
        'temperature': temperature,
        'heart_rate': heart_rate,
        'oxygen_saturation': oxygen,
        'weight': weight,
        'notes': notes
    }
    
    analysis = {
        'alert_level': alert_level,
        'alerts': alerts,
        'recommendations': get_vital_recommendations(vitals, alert_level),
        'status': 'Critical - Seek immediate medical attention' if alert_level == 'critical' 
                  else 'Warning - Monitor closely' if alert_level == 'warning'
                  else 'All vitals within normal range'
    }
    
    flash('Vital signs recorded successfully!', 'success')
    return render_template('vitals_result.html', vitals=vitals, analysis=analysis)

def get_vital_recommendations(vitals, alert_level):
    """Generate recommendations based on vital signs"""
    recommendations = []
    
    if vitals.get('blood_pressure_systolic') and vitals['blood_pressure_systolic'] >= 140:
        recommendations.append('Reduce salt intake and avoid stress')
        recommendations.append('Monitor BP twice daily')
    
    if vitals.get('blood_glucose') and vitals['blood_glucose'] > 180:
        recommendations.append('Check for diabetes, avoid sugary foods')
        recommendations.append('Consult endocrinologist')
    
    if vitals.get('temperature') and vitals['temperature'] >= 100.4:
        recommendations.append('Take paracetamol for fever')
        recommendations.append('Stay hydrated with ORS')
    
    if vitals.get('oxygen_saturation') and vitals['oxygen_saturation'] < 95:
        recommendations.append('Practice deep breathing exercises')
        recommendations.append('Sit upright, avoid lying flat')
    
    if not recommendations:
        recommendations.append('Continue maintaining healthy lifestyle')
        recommendations.append('Regular exercise and balanced diet recommended')
    
    return recommendations

@app.route('/vitals_timeline')
@login_required
def vitals_timeline():
    """View vitals history timeline with chart data"""
    # Get last 30 vital records for the user
    records = VitalRecord.query.filter_by(user_id=current_user.id)\
        .order_by(VitalRecord.created_at.desc())\
        .limit(30).all()
    
    # Prepare chart data
    chart_data = {
        'dates': [r.created_at.strftime('%b %d') for r in reversed(records)],
        'systolic': [r.bp_systolic for r in reversed(records) if r.bp_systolic],
        'diastolic': [r.bp_diastolic for r in reversed(records) if r.bp_diastolic],
        'glucose': [r.blood_glucose for r in reversed(records) if r.blood_glucose],
        'temperature': [r.temperature for r in reversed(records) if r.temperature],
        'heart_rate': [r.heart_rate for r in reversed(records) if r.heart_rate],
        'oxygen': [r.oxygen_saturation for r in reversed(records) if r.oxygen_saturation]
    }
    
    return render_template('vitals_timeline.html', records=records, chart_data=chart_data)


#--------------------------------------------
# Meal Analysis (fixed to support camera + mock analysis)
#--------------------------------------------

@app.route('/meal_analysis')
@login_required
def meal_analysis():
    return render_template('meal_analysis.html')

@app.route('/upload_meal', methods=['POST'])
@login_required
def upload_meal():
    filepath = None
    filename = None
    
    # Handle camera image (base64)
    camera_image = request.form.get('camera_image')
    if camera_image and camera_image.strip():
        try:
            filepath, filename = save_camera_image(camera_image, 'meal')
        except Exception as e:
            return jsonify({'error': f'Error processing camera image: {str(e)}'}), 400
    
    # Handle file upload (check both 'meal_image' and 'image' for compatibility)
    if not filepath:
        file = request.files.get('meal_image') or request.files.get('image')
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
    
    if not filepath:
        return jsonify({'error': 'No image provided'}), 400
    
    # Get user info
    age = request.form.get('age')
    weight = request.form.get('weight')
    height = request.form.get('height')
    
    # Analyze meal using mock analysis
    result = analyze_meal_mock(filepath, age, weight, height)
    
    return jsonify({
        'calories': result['calories'],
        'nutrients': result['nutrients'],
        'advice': result['advice'],
        'image_url': url_for('static', filename=f'uploads/{filename}')
    })


def analyze_meal_mock(image_path, age=None, weight=None, height=None):
    """
    Mock meal analysis that provides realistic-looking results
    In production, this would use an actual ML model
    """
    import random
    
    # Generate realistic mock values
    calories = random.randint(250, 850)
    protein = random.randint(10, 45)
    carbs = random.randint(20, 80)
    fats = random.randint(8, 35)
    
    nutrients = {
        "Protein": protein,
        "Carbs": carbs,
        "Fats": fats
    }
    
    # Generate contextual advice
    advices = []
    
    if calories > 700:
        advices.append("This meal appears high in calories. Consider a lighter portion.")
    elif calories < 300:
        advices.append("This seems like a light meal. Consider adding more nutrients.")
    
    if protein < 15:
        advices.append("Consider adding a protein source like dal, eggs, or paneer.")
    
    if carbs > 60:
        advices.append("High carbohydrate content. Balance with vegetables and protein.")
    
    if fats > 30:
        advices.append("Consider reducing oil or fried components.")
    
    if not advices:
        advices.append("This meal looks well-balanced! Good choice for your health.")
    
    # Add personalized advice if user info provided
    if weight and height:
        try:
            bmi = float(weight) / ((float(height) / 100) ** 2)
            if bmi > 25:
                advices.append("Consider portion control to maintain a healthy weight.")
            elif bmi < 18.5:
                advices.append("Ensure you're getting enough calories for your needs.")
        except:
            pass
    
    return {
        'calories': calories,
        'nutrients': nutrients,
        'advice': ' '.join(advices)
    }

# ========== DOCTOR VERIFICATION WORKFLOW ==========

def doctor_required(f):
    """Decorator for routes that require doctor or CHW role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['doctor', 'chw']:
            flash('Access denied. Doctor or CHW role required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/doctor/dashboard')
@login_required
@doctor_required
def doctor_dashboard():
    """Dashboard for doctors showing pending and recent verifications"""
    pending_reports = SymptomReport.query.filter_by(doctor_approved=False).order_by(SymptomReport.created_at.desc()).limit(20).all()
    recent_approved = SymptomReport.query.filter_by(doctor_approved=True, approved_by=current_user.id).order_by(SymptomReport.approved_at.desc()).limit(10).all()
    
    # Stats
    stats = {
        'pending_count': SymptomReport.query.filter_by(doctor_approved=False).count(),
        'approved_today': SymptomReport.query.filter(
            SymptomReport.approved_by == current_user.id,
            SymptomReport.approved_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).count(),
        'total_approved': SymptomReport.query.filter_by(approved_by=current_user.id).count()
    }
    
    return render_template('doctor_dashboard.html', 
                         pending=pending_reports, 
                         recent=recent_approved,
                         stats=stats)

@app.route('/doctor/review/<int:report_id>')
@login_required
@doctor_required
def doctor_review(report_id):
    """View detailed report for doctor review"""
    report = SymptomReport.query.get_or_404(report_id)
    patient = User.query.get(report.user_id)
    
    # Parse AI prediction if exists
    ai_analysis = None
    if report.ai_prediction:
        try:
            ai_analysis = json.loads(report.ai_prediction)
        except:
            ai_analysis = {'disease': 'Error parsing prediction'}
    
    return render_template('doctor_review.html', 
                         report=report, 
                         patient=patient,
                         ai_analysis=ai_analysis)

@app.route('/doctor/approve/<int:report_id>', methods=['POST'])
@login_required
@doctor_required
def doctor_approve(report_id):
    """Approve a symptom report with optional doctor notes"""
    report = SymptomReport.query.get_or_404(report_id)
    
    doctor_notes = request.form.get('doctor_notes', '')
    action = request.form.get('action', 'approve')  # approve, reject, modify
    
    if action == 'approve':
        report.doctor_approved = True
        report.doctor_notes = doctor_notes
        report.approved_by = current_user.id
        report.approved_at = datetime.utcnow()
        db.session.commit()
        flash('Report approved successfully!', 'success')
    elif action == 'reject':
        report.doctor_notes = f"REJECTED: {doctor_notes}"
        report.approved_by = current_user.id
        report.approved_at = datetime.utcnow()
        db.session.commit()
        flash('Report marked as rejected with notes.', 'warning')
    elif action == 'modify':
        # Doctor modifies the AI prediction
        modified_diagnosis = request.form.get('modified_diagnosis', '')
        if modified_diagnosis:
            try:
                current_prediction = json.loads(report.ai_prediction) if report.ai_prediction else {}
                current_prediction['doctor_diagnosis'] = modified_diagnosis
                current_prediction['original_ai_disease'] = current_prediction.get('disease', '')
                current_prediction['disease'] = modified_diagnosis
                report.ai_prediction = json.dumps(current_prediction)
            except:
                pass
        report.doctor_approved = True
        report.doctor_notes = doctor_notes
        report.approved_by = current_user.id
        report.approved_at = datetime.utcnow()
        db.session.commit()
        flash('Report approved with modifications.', 'success')
    
    return redirect(url_for('doctor_dashboard'))

# ========== CHW (Community Health Worker) INTERFACE ==========

@app.route('/chw/dashboard')
@login_required
@doctor_required
def chw_dashboard():
    """Simplified dashboard for Community Health Workers"""
    # Quick screening tools
    screening_tools = [
        {'name': 'Symptom Check', 'icon': 'stethoscope', 'url': 'symptom_input'},
        {'name': 'Record Vitals', 'icon': 'heartbeat', 'url': 'vitals_input'},
        {'name': 'Scan Prescription', 'icon': 'file-medical', 'url': 'prescription'},
        {'name': 'View Pending', 'icon': 'clipboard-list', 'url': 'doctor_dashboard'}
    ]
    
    # Recent patient entries by this CHW
    recent_reports = SymptomReport.query.join(User).filter(
        User.role == 'patient'
    ).order_by(SymptomReport.created_at.desc()).limit(10).all()
    
    return render_template('chw_dashboard.html', 
                         tools=screening_tools,
                         recent_reports=recent_reports)

@app.route('/chw/screening-checklist')
@login_required
@doctor_required
def screening_checklist():
    """Interactive screening checklist for CHWs"""
    checklists = {
        'maternal': [
            'Has the patient experienced bleeding?',
            'Are there signs of pre-eclampsia (headache, swelling)?',
            'Is fetal movement present?',
            'Last prenatal checkup date?'
        ],
        'child': [
            'Is the child experiencing fever?',
            'Signs of dehydration (sunken eyes, dry mouth)?',
            'Vaccine schedule up to date?',
            'Weight and height within normal range?'
        ],
        'general': [
            'Any chronic conditions (diabetes, hypertension)?',
            'Currently on any medications?',
            'Recent hospitalizations?',
            'Known allergies?'
        ]
    }
    return render_template('screening_checklist.html', checklists=checklists)

# ========== FAMILY PROXY ACCESS ==========

@app.route('/family')
@login_required
def family_manage():
    """Manage family members and proxy access"""
    # Members where I am the proxy (I can view them)
    my_family = FamilyMember.query.filter_by(family_member_id=current_user.id).all()
    
    # Members who are my proxy (They can view me)
    my_proxies = FamilyMember.query.filter_by(user_id=current_user.id).all()
    
    family_details = []
    for rel in my_family:
        user = User.query.get(rel.user_id)
        if user:
            family_details.append({
                'user': user,
                'relationship': rel.relationship,
                'access_granted': rel.access_granted,
                'link_id': rel.id
            })
            
    proxy_details = []
    for rel in my_proxies:
        user = User.query.get(rel.family_member_id)
        if user:
            proxy_details.append({
                'user': user,
                'relationship': rel.relationship,
                'access_granted': rel.access_granted,
                'link_id': rel.id
            })
            
    return render_template('family_manage.html', 
                         family=family_details, 
                         proxies=proxy_details)

@app.route('/family/add', methods=['POST'])
@login_required
def family_add():
    """Add a family member by email"""
    email = request.form.get('email')
    relationship = request.form.get('relationship')
    action = request.form.get('action') # 'add_member' (I manage them) or 'add_proxy' (They manage me)
    
    target_user = User.query.filter_by(email=email).first()
    
    if not target_user:
        flash('User with this email not found.', 'error')
        return redirect(url_for('family_manage'))
        
    if target_user.id == current_user.id:
        flash('You cannot add yourself.', 'warning')
        return redirect(url_for('family_manage'))
    
    existing_link = None
    if action == 'add_member':
        # I want to manage THEM. They are the user_id, I am the family_member_id (proxy)
        # In a real app, this would require THEIR approval. For MVP, we'll assume consent if email is known.
        existing_link = FamilyMember.query.filter_by(user_id=target_user.id, family_member_id=current_user.id).first()
        if not existing_link:
            link = FamilyMember(user_id=target_user.id, family_member_id=current_user.id, relationship=relationship)
            db.session.add(link)
            flash(f'Added {target_user.username} to your family list.', 'success')
    else:
        # I want THEM to manage ME. I am user_id, They are family_member_id
        existing_link = FamilyMember.query.filter_by(user_id=current_user.id, family_member_id=target_user.id).first()
        if not existing_link:
            link = FamilyMember(user_id=current_user.id, family_member_id=target_user.id, relationship=relationship)
            db.session.add(link)
            flash(f'Granted access to {target_user.username}.', 'success')
            
    if existing_link:
        flash('This link already exists.', 'info')
    else:
        db.session.commit()
        
    return redirect(url_for('family_manage'))

@app.route('/family/view/<int:user_id>')
@login_required
def family_view(user_id):
    """View a family member's dashboard"""
    # Check permission
    permission = FamilyMember.query.filter_by(
        user_id=user_id, 
        family_member_id=current_user.id,
        access_granted=True
    ).first()
    
    if not permission:
        flash('You do not have permission to view this profile.', 'error')
        return redirect(url_for('family_manage'))
        
    target_user = User.query.get_or_404(user_id)
    
    # Render dashboard with target user data but passing a flag that it's a proxy view
    return render_template('dashboard.html', 
                         user=target_user, 
                         is_proxy_view=True,
                         proxy_for=target_user.username)

# ========== PHARMACY MAP ==========

@app.route('/pharmacy')
def pharmacy_map():
    """View nearby pharmacies on a map"""
    # Mock data for rural pharmacies
    # In a real app, this would come from a database or Google Maps API
    pharmacies = [
        {
            "id": 1,
            "name": "Jeevan Raksha Pharmacy",
            "lat_offset": 0.002, 
            "lng_offset": 0.003,
            "address": "Main Road, Near Bus Stand",
            "phone": "+91 98765 11111",
            "stock": ["Paracetamol", "Amoxicillin", "ORS"]
        },
        {
            "id": 2,
            "name": "Gramin Health Chemist",
            "lat_offset": -0.004, 
            "lng_offset": 0.001,
            "address": "Village Square, Opposite School",
            "phone": "+91 98765 22222",
            "stock": ["Ibuprofen", "Bandages", "Insulin"]
        },
        {
            "id": 3,
            "name": "City Medicos",
            "lat_offset": 0.001, 
            "lng_offset": -0.005,
            "address": "Station Road, Market Complex",
            "phone": "+91 98765 33333",
            "stock": ["All Medicines Available"]
        }
    ]
    return render_template('pharmacy_map.html', pharmacies=pharmacies)

# ========== VIDEO CONSULTATION ==========

@app.route('/video/start')
@login_required
def video_start():
    """Start a new video consultation (generates room ID)"""
    import uuid
    room_id = str(uuid.uuid4())[:8]
    return redirect(url_for('video_room', room_id=room_id))

@app.route('/video/room/<room_id>')
@login_required
def video_room(room_id):
    """Video consultation room"""
    return render_template('video_consult.html', room_id=room_id)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # --- Ngrok Setup ---
    from pyngrok import conf
    import os
    conf.get_default().ngrok_path = os.path.join(os.getcwd(), "ngrok.exe")
    
    NGROK_AUTH_TOKEN = "39MB34qkF3Vi1K64AHaXDYv6UkZ_41XgZDGYF5wJbTYVy7y2t"
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    public_url = ngrok.connect(5000).public_url
    print(f" * Public URL: {public_url}")
    # -------------------

    app.run(debug=True, use_reloader=False)
