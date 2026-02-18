# 🏥 Pristin Healthcare - AI-Based Rural Telemedicine Platform

> **Advanced AI-powered healthcare for rural communities.**
> *Bridging the gap between patients and medical professionals with offline-first technology.*

## 🌟 Overview

Pristin Healthcare is a comprehensive telemedicine application designed specifically for rural India. It addresses connectivity challenges with an **offline-first approach** and uses **Grade A Artificial Intelligence** to provide preliminary diagnostics, ensuring that even remote populations have access to quality healthcare guidance.

---

## 🚀 Key Features

### 1. 🔍 AI-Powered Diagnostics 
*   **Symptom Checker**: Chat with "Pristin AI" to analyze symptoms. It provides potential conditions (e.g., Malaria, Dengue) and severity levels.
*   **Facial Health Scan**: Uses your camera to scan for visible health indicators like **Anemia** (pallor), **Jaundice** (yellowness), and **Fever** (flush). *Now features a non-scary "Healthy Scan" mode!*
*   **Prescription OCR**: Upload a photo of a handwritten prescription, and our AI will digitize it into readable text and medicine reminders.

### 2. 📡 Offline-First Architecture
*   **Works Without Internet**: If the internet cuts out, you can still log symptoms, save vitals, and view past records.
*   **Auto-Sync**: Data saved offline automatically syncs with the server once connectivity is restored.
*   **PWA Support**: Installable on Android/iOS as a native-like app.

### 3. 👨‍⚕️ Doctor & Patient Dashboards
*   **Patient Dashboard**: Track vitals (BP, Sugar, Heart Rate), view reports, and manage family members.
*   **Doctor Dashboard**: Review patient cases, approve reports, and conduct video consultations.
*   **Video Consultations**: Integrated video calling for remote checkups.

### 4. 🚑 Emergency & Utility Tools
*   **Pharmacy Finder**: Locate nearby pharmacies on an interactive map.
*   **Visual Translations**: All icons and text translate to local languages (Hindi, Telugu, Tamil, Bengali, Marathi) for better accessibility.
*   **WhatsApp Integration**: Receive automated health alerts and reports on WhatsApp.

---

## 🛠️ Technical Stack

*   **Backend**: Python (Flask), SQLAlchemy (Database)
*   **Frontend**: HTML5, Vanilla CSS (Premium "MaxAlert" Dark UI), JavaScript (ES6+)
*   **AI/ML**: 
    *   Google Gemini 2.5 Flash (Symptom Analysis & Chatbot)
    *   OpenCV & TensorFlow (Image Processing & Facial Scan)
    *   Tesseract OCR (Prescription Digitization)
*   **Deployment**: Ngrok (Public Tunneling)

---

## 📲 How to Run Locally

### Prerequisites
*   Python 3.8+
*   Git
*   Tesseract OCR (installed and in PATH)

### Installation Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/gojosatorou999/ai-based-rural-healthcare-app.git
    cd ai-based-rural-healthcare-app
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Environment Variables**
    Create a `.env` file in the root directory and add your API keys:
    ```env
    FLASK_SECRET_KEY=your_secret_key
    GEMINI_API_KEY_1=your_gemini_key
    NGROK_AUTH_TOKEN=your_ngrok_token
    ```

4.  **Run the Application**
    ```bash
    python app.py
    ```

5.  **Access the App**
    *   **Local**: `http://localhost:5000`
    *   **Public (Mobile)**: Check the terminal for the `ngrok` URL (e.g., `https://xxxx.ngrok-free.app`). Use this link on your phone.

---

## 🧩 Troubleshooting

### 📉 App Stops Working / Goes Offline?
*   **Cause**: The server on your PC might have stopped, or the phone browser put the tab to sleep.
*   **Fix**: 
    1. Ensure your PC is **ON** and connected to the internet.
    2. Check the terminal window running `python app.py`. If it closed, restart it.
    3. Refresh the page on your mobile device.

### 🔗 Ngrok Connection Failure?
*   **Fix**: The app automatically tries to restart Ngrok. If it fails, close the terminal and run `python app.py` again. Ensure you aren't running VPNs that block tunneling.

### 📸 Camera/Microphone Issues?
*   **Permission**: Ensure you have allowed Camera permissions in your browser.
*   **Secure Context**: Camera ONLY works on `https://` (Ngrok) or `localhost`. It will NOT work on `http://192.168.x.x`.

---

## 🛡️ License
This project is for educational and healthcare development purposes.

---
**Made with ❤️ for Rural India**
