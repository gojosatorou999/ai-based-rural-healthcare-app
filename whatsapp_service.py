# Twilio WhatsApp Integration for Rural Healthcare App

"""
This module handles WhatsApp messaging via Twilio API for:
1. Sending alerts to family members
2. Patient-doctor communication
3. Automated health reminders
4. Report sharing
"""

from twilio.rest import Client
import os

# Twilio Configuration - REAL CREDENTIALS
# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'AC_YOUR_ACCOUNT_SID_HERE')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'YOUR_AUTH_TOKEN_HERE')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')

try:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    TWILIO_ENABLED = True
    print("[SUCCESS] Twilio WhatsApp client initialized successfully!")
except Exception as e:
    print(f"[ERROR] Twilio initialization failed: {e}")
    TWILIO_ENABLED = False
    client = None


def send_whatsapp_message(to_number, message_body):
    """
    Send a WhatsApp message to a phone number
    """
    # Robust formatting for Indian numbers as requested
    import re
    digits = re.sub(r'\D', '', str(to_number)) # Remove non-digits
    if len(digits) >= 10:
        clean_number = digits[-10:] # Take last 10
        to_number_formatted = f'whatsapp:+91{clean_number}'
    else:
        # Fallback for short numbers or weird input
        to_number_formatted = f'whatsapp:{to_number}'

    if not TWILIO_ENABLED or not client:
        print(f"[WARNING] Twilio not initialized. Using DIAGNOSTIC MOCK for {to_number_formatted}...")
        return mock_send_whatsapp(to_number_formatted, message_body)
    
    try:
        # Log attempting real send
        print(f"[INFO] Attempting REAL WhatsApp to: {to_number_formatted}")
        # Ensure 'from_' number has whatsapp: prefix
        from_number = TWILIO_WHATSAPP_NUMBER
        if not from_number.startswith('whatsapp:'):
            from_number = f'whatsapp:{from_number}'

        print(f"[DEBUG] Using From: {from_number}")
        
        message = client.messages.create(
            from_=from_number,
            body=message_body,
            to=to_number_formatted
        )
        
        print(f"[SUCCESS] REAL WhatsApp SID: {message.sid}, Status: {message.status}")
        return {
            'success': True,
            'message_sid': message.sid,
            'status': message.status,
            'mode': 'real'
        }
    except Exception as e:
        # Return ACTUAL error to user so they know it failed
        error_msg = str(e)
        print(f"[ERROR] Twilio REAL send failed to {to_number_formatted}: {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'mode': 'real_failed'
        }



def send_health_alert(patient_name, family_number, alert_type, details):
    """
    Send health alert to family member
    
    Args:
        patient_name (str): Name of the patient
        family_number (str): Family member's WhatsApp number
        alert_type (str): Type of alert (critical_vitals, symptom_report, etc.)
        details (str): Alert details
    """
    alert_messages = {
        'critical_vitals': f"🚨 *Health Alert*\n\n{patient_name} has critical vital signs:\n{details}\n\nPlease contact them immediately or consult a doctor.",
        'symptom_report': f"📋 *New Symptom Report*\n\n{patient_name} reported new symptoms:\n{details}\n\nMonitor their condition closely.",
        'medication_reminder': f"💊 *Medication Reminder*\n\n{patient_name} needs to take medication:\n{details}",
        'appointment_reminder': f"📅 *Appointment Reminder*\n\n{patient_name} has an upcoming appointment:\n{details}"
    }
    
    message = alert_messages.get(alert_type, f"Health update for {patient_name}:\n{details}")
    return send_whatsapp_message(family_number, message)


def send_doctor_notification(doctor_number, patient_name, notification_type, details):
    """
    Send notification to doctor
    
    Args:
        doctor_number (str): Doctor's WhatsApp number
        patient_name (str): Name of the patient
        notification_type (str): Type of notification
        details (str): Notification details
    """
    notification_messages = {
        'new_symptom': f"👨‍⚕️ *New Patient Report*\n\nPatient: {patient_name}\n{details}\n\nPlease review in the app.",
        'critical_case': f"🚨 *URGENT: Critical Case*\n\nPatient: {patient_name}\n{details}\n\nImmediate attention required!",
        'followup_needed': f"📋 *Follow-up Required*\n\nPatient: {patient_name}\n{details}"
    }
    
    message = notification_messages.get(notification_type, f"Update for patient {patient_name}:\n{details}")
    return send_whatsapp_message(doctor_number, message)


def send_patient_report(patient_number, report_data):
    """
    Send health report to patient via WhatsApp
    
    Args:
        patient_number (str): Patient's WhatsApp number
        report_data (dict): Report information
    """
    message = f"""📊 *Your Health Report*

Date: {report_data.get('date', 'N/A')}

*Symptoms:* {report_data.get('symptoms', 'None reported')}
*Diagnosis:* {report_data.get('diagnosis', 'Pending')}
*Recommendations:* {report_data.get('recommendations', 'Follow up with doctor')}

View full report in the Pristin Healthcare app.
"""
    return send_whatsapp_message(patient_number, message)


def send_medication_schedule(patient_number, medications):
    """
    Send medication schedule to patient
    
    Args:
        patient_number (str): Patient's WhatsApp number
        medications (list): List of medication dictionaries
    """
    med_list = "\n".join([
        f"• {med['name']} - {med.get('dosage', 'As prescribed')} - {med.get('frequency', 'Daily')}"
        for med in medications
    ])
    
    message = f"""💊 *Your Medication Schedule*

{med_list}

⏰ Set reminders to take your medicines on time!
"""
    return send_whatsapp_message(patient_number, message)


def send_video_call_link(patient_number, patient_name, doctor_name, call_link):
    """
    Send a video call link to a patient
    
    Args:
        patient_number (str): Patient's WhatsApp number
        patient_name (str): Patient's name
        doctor_name (str): Doctor's name
        call_link (str): The video call URL
    """
    message = f"""📹 *Video Consultation Request*
    
Hello {patient_name}, Dr. {doctor_name} would like to start a video consultation with you.

Click the link below to join the call:
{call_link}

Please ensure you have a stable internet connection and are in a quiet place.
"""
    return send_whatsapp_message(patient_number, message)


# Mock function for testing without Twilio
def mock_send_whatsapp(to_number, message):
    """Mock function for development/testing"""
    print(f"\n{'='*50}")
    print(f"MOCK WHATSAPP MESSAGE")
    print(f"To: {to_number}")
    print(f"Message:\n{message}")
    print(f"{'='*50}\n")
    return {'success': True, 'message_sid': 'MOCK_SID', 'status': 'sent'}
