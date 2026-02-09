"""
Database models for Rural Telemedicine Platform - Phase 1
Includes models for:
- Patient records
- Symptom reports (multimodal)
- Prescription history
- Vitals tracking
- Clinical recommendations
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# User model (existing)
class User(db.Model, UserMixin):
    """User authentication model"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='patient')  # patient, doctor, chw
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - use back_populates instead of backref to avoid conflicts
    symptom_reports = db.relationship('SymptomReport', back_populates='patient', lazy=True)
    prescriptions = db.relationship('Prescription', back_populates='patient', lazy=True)
    vitals = db.relationship('VitalRecord', back_populates='patient', lazy=True)
    recommendations = db.relationship('ClinicalRecommendation', back_populates='patient', lazy=True, foreign_keys='ClinicalRecommendation.user_id')




class SymptomReport(db.Model):
    """Multimodal symptom input - text + images"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship back to User
    patient = db.relationship('User', back_populates='symptom_reports')
    
    # Text-based symptom data
    symptom_description = db.Column(db.Text, nullable=False)
    affected_area = db.Column(db.String(100))
    severity = db.Column(db.String(20))  # mild, moderate, severe
    duration = db.Column(db.String(100))  # e.g., "2 days", "1 week"
    
    # Image data (for visual symptoms)
    image_path = db.Column(db.String(500))  # Path to compressed image
    image_compressed_path = db.Column(db.String(500))  # Thumbnail/compressed version
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')  # pending, reviewed, resolved
    
    def to_dict(self):
        return {
            'id': self.id,
            'symptom_description': self.symptom_description,
            'affected_area': self.affected_area,
            'severity': self.severity,
            'duration': self.duration,
            'image_path': self.image_path,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status
        }


class Prescription(db.Model):
    """Prescription history with OCR extraction"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship back to User
    patient = db.relationship('User', back_populates='prescriptions')
    
    # Original prescription image
    prescription_image_path = db.Column(db.String(500), nullable=False)
    
    # OCR extracted data
    raw_text = db.Column(db.Text)  # Raw OCR output
    drug_name = db.Column(db.String(200))
    dosage = db.Column(db.String(100))
    frequency = db.Column(db.String(100))
    duration = db.Column(db.String(100))
    
    # Additional metadata
    doctor_name = db.Column(db.String(200))
    prescription_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    
    # Processing status
    ocr_confidence = db.Column(db.Float)  # Confidence score
    manual_verification = db.Column(db.Boolean, default=False)
    verified_by_doctor = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'drug_name': self.drug_name,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'duration': self.duration,
            'doctor_name': self.doctor_name,
            'prescription_date': self.prescription_date.strftime('%Y-%m-%d') if self.prescription_date else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'verified': self.verified_by_doctor
        }


class VitalRecord(db.Model):
    """Track patient vitals over time"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship back to User
    patient = db.relationship('User', back_populates='vitals')
    
    # Vital measurements
    blood_pressure_systolic = db.Column(db.Integer)  # mmHg
    blood_pressure_diastolic = db.Column(db.Integer)  # mmHg
    glucose_level = db.Column(db.Float)  # mg/dL
    temperature = db.Column(db.Float)  # Celsius
    weight = db.Column(db.Float)  # kg
    heart_rate = db.Column(db.Integer)  # bpm
    oxygen_saturation = db.Column(db.Float)  # %
    
    # Metadata
    measured_at = db.Column(db.DateTime, default=datetime.utcnow)
    measured_by = db.Column(db.String(100))  # CHW name or self-reported
    notes = db.Column(db.Text)
    
    # Alert flags
    is_abnormal = db.Column(db.Boolean, default=False)
    alert_type = db.Column(db.String(50))  # critical, warning, normal
    
    def to_dict(self):
        return {
            'id': self.id,
            'blood_pressure': f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}" if self.blood_pressure_systolic else None,
            'glucose_level': self.glucose_level,
            'temperature': self.temperature,
            'weight': self.weight,
            'heart_rate': self.heart_rate,
            'oxygen_saturation': self.oxygen_saturation,
            'measured_at': self.measured_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_abnormal': self.is_abnormal,
            'alert_type': self.alert_type
        }


class ClinicalRecommendation(db.Model):
    """AI-generated clinical recommendations with explanations"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symptom_report_id = db.Column(db.Integer, db.ForeignKey('symptom_report.id'))
    
    # Relationship back to User (for the patient, not the reviewer)
    patient = db.relationship('User', back_populates='recommendations', foreign_keys=[user_id])
    
    # Recommendation details
    condition_identified = db.Column(db.String(200))
    confidence_score = db.Column(db.Float)  # 0-100
    
    # Treatment suggestions
    treatment_suggestion = db.Column(db.Text)
    medications = db.Column(db.Text)  # JSON string of medicine list
    lifestyle_advice = db.Column(db.Text)
    
    # Explainability
    reasoning = db.Column(db.Text)  # Why this recommendation was made
    symptoms_matched = db.Column(db.Text)  # Which symptoms triggered this
    similar_cases = db.Column(db.Text)  # References to similar cases
    
    # Doctor verification
    status = db.Column(db.String(50), default='pending_review')  # pending_review, approved, rejected, modified
    doctor_notes = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'condition_identified': self.condition_identified,
            'confidence_score': self.confidence_score,
            'treatment_suggestion': self.treatment_suggestion,
            'medications': self.medications,
            'reasoning': self.reasoning,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class MedicalCondition(db.Model):
    """Patient's existing medical conditions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    condition_name = db.Column(db.String(200), nullable=False)
    diagnosed_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
