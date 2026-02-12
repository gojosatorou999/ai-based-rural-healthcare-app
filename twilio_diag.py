import os
import sys
from twilio.rest import Client

# Load from whatsapp_service if possible
try:
    sys.path.append(os.getcwd())
    from whatsapp_service import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER
    print(f"[INFO] Loaded credentials from whatsapp_service.py")
except Exception as e:
    print(f"[ERROR] Error loading whatsapp_service: {e}")
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'AC_YOUR_ACCOUNT_SID_HERE')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'YOUR_AUTH_TOKEN_HERE')
    TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')

print(f"SID: {TWILIO_ACCOUNT_SID[:5]}...{TWILIO_ACCOUNT_SID[-5:]}")
print(f"Token: {'*' * 10}{TWILIO_AUTH_TOKEN[-4:]}")
print(f"From: {TWILIO_WHATSAPP_NUMBER}")

try:
    print("Testing Twilio client initialization...")
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    print("Testing API connectivity (listing 1 message)...")
    # Just list some messages to verify connection
    messages = client.messages.list(limit=1)
    print("[SUCCESS] Connection Successful! The API responded correctly.")
except Exception as e:
    print(f"[FAILURE] Twilio error: {e}")
    if "Authenticate" in str(e):
        print("TIP: Your Twilio SID or Auth Token seems invalid.")
    elif "not found" in str(e).lower():
        print("TIP: The 'twilio' library might not be available to the current Python environment.")
