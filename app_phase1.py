"""
Rural Telemedicine Platform - Phase 1 Implementation
Flask Backend with:
1. Multimodal symptom input (text + images)
2. AI-powered prescription reader (OCR)
3. Context-aware clinical recommendations
4. Smart health timeline (vitals tracking)
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import json
import logging

# Import models and utilities
from models import db, User, SymptomReport, Prescription, VitalRecord, ClinicalRecommendation, MedicalCondition
from utils import (
    compress_image, create_thumbnail, extract_prescription_text, parse_prescription,
    generate_clinical_recommendation, analyze_vitals, detect_vital_trends
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "ab5ea52cfbef6fcf789ce562369e183338e01c138e1b0cb3c1d63d7dc112f073"

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///telemedicine.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'symptoms'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'prescriptions'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'compressed'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails'), exist_ok=True)

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def home():
    """Home page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')


@app.route('/offline')
def offline():
    """Offline page for PWA"""
    return render_template('offline.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
            age = request.form.get('age', type=int)
            gender = request.form.get('gender')
            phone = request.form.get('phone')
            role = request.form.get('role', 'patient')

            # Check if user exists
            if User.query.filter_by(email=email).first():
                flash('Email already exists. Please log in.', 'warning')
                return redirect(url_for('login'))

            # Create new user
            new_user = User(
                username=username,
                email=email,
                password=password,
                age=age,
                gender=gender,
                phone=phone,
                role=role
            )
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# ==================== DASHBOARD ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    # Get recent data for dashboard
    recent_symptoms = SymptomReport.query.filter_by(user_id=current_user.id).order_by(SymptomReport.created_at.desc()).limit(5).all()
    recent_vitals = VitalRecord.query.filter_by(user_id=current_user.id).order_by(VitalRecord.measured_at.desc()).limit(5).all()
    pending_recommendations = ClinicalRecommendation.query.filter_by(user_id=current_user.id, status='pending_review').count()
    
    # Get vital trends
    all_vitals = VitalRecord.query.filter_by(user_id=current_user.id).order_by(VitalRecord.measured_at).all()
    trends = detect_vital_trends(all_vitals) if len(all_vitals) >= 3 else {'trends': [], 'warnings': []}
    
    return render_template('dashboard_phase1.html',
                         user=current_user,
                         recent_symptoms=recent_symptoms,
                         recent_vitals=recent_vitals,
                         pending_recommendations=pending_recommendations,
                         trends=trends)


# ==================== FEATURE 1: MULTIMODAL SYMPTOM INPUT ====================

@app.route('/symptoms/new', methods=['GET'])
@login_required
def new_symptom_report():
    """Show symptom input form"""
    return render_template('symptom_input.html')


@app.route('/symptoms/submit', methods=['POST'])
@login_required
def submit_symptom_report():
    """Submit symptom report with text and optional image"""
    try:
        # Get form data
        symptom_description = request.form.get('symptom_description', '').strip()
        affected_area = request.form.get('affected_area', '').strip()
        severity = request.form.get('severity', 'moderate')
        duration = request.form.get('duration', '').strip()
        
        if not symptom_description:
            return jsonify({'error': 'Symptom description is required'}), 400
        
        # Handle image upload (optional)
        image_path = None
        compressed_path = None
        
        if 'symptom_image' in request.files:
            file = request.files['symptom_image']
            if file and file.filename and allowed_file(file.filename):
                # Save original image
                filename = secure_filename(f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'symptoms', filename)
                file.save(image_path)
                
                # Compress image for low-bandwidth
                compressed_filename = f"compressed_{filename.rsplit('.', 1)[0]}.webp"
                compressed_path = os.path.join(app.config['UPLOAD_FOLDER'], 'compressed', compressed_filename)
                compress_image(image_path, compressed_path, quality=60, max_width=800)
                
                # Create thumbnail
                thumb_filename = f"thumb_{filename.rsplit('.', 1)[0]}.webp"
                thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', thumb_filename)
                create_thumbnail(image_path, thumb_path, size=(200, 200))
                
                logger.info(f"Image uploaded and compressed: {filename}")
        
        # Create symptom report
        symptom_report = SymptomReport(
            user_id=current_user.id,
            symptom_description=symptom_description,
            affected_area=affected_area,
            severity=severity,
            duration=duration,
            image_path=image_path,
            image_compressed_path=compressed_path
        )
        db.session.add(symptom_report)
        db.session.commit()
        
        # Generate clinical recommendation
        existing_conditions = [c.condition_name for c in MedicalCondition.query.filter_by(user_id=current_user.id, is_active=True).all()]
        recommendation_data = generate_clinical_recommendation(
            symptom_description,
            patient_age=current_user.age,
            patient_gender=current_user.gender,
            existing_conditions=existing_conditions
        )
        
        # Save recommendation
        recommendation = ClinicalRecommendation(
            user_id=current_user.id,
            symptom_report_id=symptom_report.id,
            **recommendation_data
        )
        db.session.add(recommendation)
        db.session.commit()
        
        flash('Symptom report submitted successfully!', 'success')
        return jsonify({
            'success': True,
            'symptom_id': symptom_report.id,
            'recommendation_id': recommendation.id,
            'redirect': url_for('view_recommendation', rec_id=recommendation.id)
        })
        
    except Exception as e:
        logger.error(f"Error submitting symptom report: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to submit symptom report'}), 500


@app.route('/symptoms/<int:symptom_id>')
@login_required
def view_symptom(symptom_id):
    """View symptom report details"""
    symptom = SymptomReport.query.get_or_404(symptom_id)
    
    # Ensure user owns this symptom report
    if symptom.user_id != current_user.id and current_user.role != 'doctor':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get associated recommendation
    recommendation = ClinicalRecommendation.query.filter_by(symptom_report_id=symptom_id).first()
    
    return render_template('symptom_detail.html', symptom=symptom, recommendation=recommendation)


# ==================== FEATURE 2: PRESCRIPTION READER (OCR) ====================

@app.route('/prescriptions/new', methods=['GET'])
@login_required
def new_prescription():
    """Show prescription upload form"""
    return render_template('prescription_upload.html')


@app.route('/prescriptions/upload', methods=['POST'])
@login_required
def upload_prescription():
    """Upload and process prescription image with OCR"""
    try:
        if 'prescription_image' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['prescription_image']
        if not file or not file.filename or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file'}), 400
        
        # Save prescription image
        filename = secure_filename(f"rx_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'prescriptions', filename)
        file.save(image_path)
        
        # Compress for storage
        compressed_filename = f"compressed_{filename.rsplit('.', 1)[0]}.webp"
        compressed_path = os.path.join(app.config['UPLOAD_FOLDER'], 'compressed', compressed_filename)
        compress_image(image_path, compressed_path)
        
        # Extract text using OCR
        language = request.form.get('language', 'eng')  # 'eng' or 'tel' for Telugu
        ocr_result = extract_prescription_text(image_path, language=language)
        
        # Parse prescription data
        parsed_data = parse_prescription(ocr_result['raw_text'])
        
        # Create prescription record
        prescription = Prescription(
            user_id=current_user.id,
            prescription_image_path=compressed_path,
            raw_text=ocr_result['raw_text'],
            drug_name=parsed_data['drug_name'],
            dosage=parsed_data['dosage'],
            frequency=parsed_data['frequency'],
            duration=parsed_data['duration'],
            doctor_name=parsed_data['doctor_name'],
            ocr_confidence=ocr_result['confidence']
        )
        db.session.add(prescription)
        db.session.commit()
        
        logger.info(f"Prescription uploaded and processed: {filename}")
        
        return jsonify({
            'success': True,
            'prescription_id': prescription.id,
            'ocr_data': {
                'raw_text': ocr_result['raw_text'],
                'drug_name': parsed_data['drug_name'],
                'dosage': parsed_data['dosage'],
                'frequency': parsed_data['frequency'],
                'duration': parsed_data['duration'],
                'confidence': ocr_result['confidence']
            },
            'redirect': url_for('view_prescription', prescription_id=prescription.id)
        })
        
    except Exception as e:
        logger.error(f"Error processing prescription: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to process prescription'}), 500


@app.route('/prescriptions/<int:prescription_id>')
@login_required
def view_prescription(prescription_id):
    """View prescription details"""
    prescription = Prescription.query.get_or_404(prescription_id)
    
    # Ensure user owns this prescription
    if prescription.user_id != current_user.id and current_user.role != 'doctor':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('prescription_detail.html', prescription=prescription)


@app.route('/prescriptions/history')
@login_required
def prescription_history():
    """View all prescriptions"""
    prescriptions = Prescription.query.filter_by(user_id=current_user.id).order_by(Prescription.created_at.desc()).all()
    return render_template('prescription_history.html', prescriptions=prescriptions)


# ==================== FEATURE 3: CLINICAL RECOMMENDATIONS ====================

@app.route('/recommendations/<int:rec_id>')
@login_required
def view_recommendation(rec_id):
    """View clinical recommendation with explanations"""
    recommendation = ClinicalRecommendation.query.get_or_404(rec_id)
    
    # Ensure user owns this recommendation
    if recommendation.user_id != current_user.id and current_user.role != 'doctor':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Parse JSON fields
    medications = json.loads(recommendation.medications) if recommendation.medications else []
    symptoms_matched = json.loads(recommendation.symptoms_matched) if recommendation.symptoms_matched else []
    
    return render_template('recommendation_detail.html',
                         recommendation=recommendation,
                         medications=medications,
                         symptoms_matched=symptoms_matched)


@app.route('/recommendations/<int:rec_id>/approve', methods=['POST'])
@login_required
def approve_recommendation(rec_id):
    """Doctor approves recommendation"""
    if current_user.role != 'doctor':
        return jsonify({'error': 'Only doctors can approve recommendations'}), 403
    
    try:
        recommendation = ClinicalRecommendation.query.get_or_404(rec_id)
        recommendation.status = 'approved'
        recommendation.reviewed_by = current_user.id
        recommendation.reviewed_at = datetime.utcnow()
        recommendation.doctor_notes = request.form.get('notes', '')
        
        db.session.commit()
        
        flash('Recommendation approved', 'success')
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error approving recommendation: {str(e)}")
        return jsonify({'error': 'Failed to approve recommendation'}), 500


# ==================== FEATURE 4: SMART HEALTH TIMELINE (VITALS) ====================

@app.route('/vitals/new', methods=['GET'])
@login_required
def new_vital_record():
    """Show vitals input form"""
    return render_template('vitals_input.html')


@app.route('/vitals/submit', methods=['POST'])
@login_required
def submit_vital_record():
    """Submit vital signs"""
    try:
        # Get form data
        bp_systolic = request.form.get('bp_systolic', type=int)
        bp_diastolic = request.form.get('bp_diastolic', type=int)
        glucose = request.form.get('glucose', type=float)
        temperature = request.form.get('temperature', type=float)
        weight = request.form.get('weight', type=float)
        heart_rate = request.form.get('heart_rate', type=int)
        oxygen_saturation = request.form.get('oxygen_saturation', type=float)
        notes = request.form.get('notes', '').strip()
        
        # Analyze vitals
        analysis = analyze_vitals(bp_systolic, bp_diastolic, glucose, temperature, weight, current_user.age)
        
        # Create vital record
        vital_record = VitalRecord(
            user_id=current_user.id,
            blood_pressure_systolic=bp_systolic,
            blood_pressure_diastolic=bp_diastolic,
            glucose_level=glucose,
            temperature=temperature,
            weight=weight,
            heart_rate=heart_rate,
            oxygen_saturation=oxygen_saturation,
            notes=notes,
            is_abnormal=analysis['is_abnormal'],
            alert_type=analysis['alert_type']
        )
        db.session.add(vital_record)
        db.session.commit()
        
        logger.info(f"Vital record submitted for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'vital_id': vital_record.id,
            'analysis': analysis,
            'redirect': url_for('vitals_timeline')
        })
        
    except Exception as e:
        logger.error(f"Error submitting vital record: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to submit vital record'}), 500


@app.route('/vitals/timeline')
@login_required
def vitals_timeline():
    """View vitals timeline with charts"""
    # Get all vitals for current user
    vitals = VitalRecord.query.filter_by(user_id=current_user.id).order_by(VitalRecord.measured_at).all()
    
    # Get trend analysis
    trends = detect_vital_trends(vitals) if len(vitals) >= 3 else {'trends': [], 'warnings': []}
    
    # Prepare data for charts
    chart_data = {
        'dates': [v.measured_at.strftime('%Y-%m-%d') for v in vitals],
        'bp_systolic': [v.blood_pressure_systolic for v in vitals],
        'bp_diastolic': [v.blood_pressure_diastolic for v in vitals],
        'glucose': [v.glucose_level for v in vitals],
        'temperature': [v.temperature for v in vitals],
        'weight': [v.weight for v in vitals]
    }
    
    return render_template('vitals_timeline.html',
                         vitals=vitals,
                         trends=trends,
                         chart_data=json.dumps(chart_data))


@app.route('/vitals/<int:vital_id>')
@login_required
def view_vital(vital_id):
    """View single vital record"""
    vital = VitalRecord.query.get_or_404(vital_id)
    
    # Ensure user owns this vital record
    if vital.user_id != current_user.id and current_user.role != 'doctor':
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('vital_detail.html', vital=vital)


# ==================== API ENDPOINTS ====================

@app.route('/api/symptoms', methods=['GET'])
@login_required
def api_get_symptoms():
    """API: Get all symptom reports for current user"""
    symptoms = SymptomReport.query.filter_by(user_id=current_user.id).order_by(SymptomReport.created_at.desc()).all()
    return jsonify([s.to_dict() for s in symptoms])


@app.route('/api/vitals', methods=['GET'])
@login_required
def api_get_vitals():
    """API: Get all vital records for current user"""
    vitals = VitalRecord.query.filter_by(user_id=current_user.id).order_by(VitalRecord.measured_at.desc()).all()
    return jsonify([v.to_dict() for v in vitals])


@app.route('/api/prescriptions', methods=['GET'])
@login_required
def api_get_prescriptions():
    """API: Get all prescriptions for current user"""
    prescriptions = Prescription.query.filter_by(user_id=current_user.id).order_by(Prescription.created_at.desc()).all()
    return jsonify([p.to_dict() for p in prescriptions])


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Page not found'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', error='Internal server error'), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.info("Database initialized")
    
    # Ngrok setup for public access
    try:
        from pyngrok import ngrok
        import logging as ngrok_logging
        
        # Set ngrok logging
        ngrok_logging.getLogger('pyngrok').setLevel(ngrok_logging.WARNING)
        
        # Set auth token
        NGROK_AUTH_TOKEN = "39MB34qkF3Vi1K64AHaXDYv6UkZ_41XgZDGYF5wJbTYVy7y2t"
        ngrok.set_auth_token(NGROK_AUTH_TOKEN)
        
        # Kill any existing ngrok processes
        ngrok.kill()
        
        # Start ngrok tunnel
        public_url = ngrok.connect(5000, bind_tls=True)
        
        print(f"\n{'='*70}")
        print(f"PUBLIC URL: {public_url}")
        print(f"LOCAL URL: http://localhost:5000")
        print(f"{'='*70}\n")
        print(f"Server is running and accessible online!")
        print(f"Share the public URL to access from anywhere")
        print(f"\n{'='*70}\n")
        
    except Exception as e:
        logger.warning(f"Ngrok setup failed: {str(e)}")
        print(f"\nNgrok not available: {str(e)}")
        print(f"Running locally only at: http://localhost:5000\n")
    
    # Run the Flask app
    print("Starting Flask server...")
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)


