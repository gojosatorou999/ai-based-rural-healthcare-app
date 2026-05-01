# 🏥 Pristin Healthcare: AI-Powered Rural Telemedicine Platform
<div align="center">

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite%20%2F%20PostgreSQL-Ready-003B57?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Twilio](https://img.shields.io/badge/Twilio-WhatsApp_API-F22F46?style=for-the-badge&logo=twilio&logoColor=white)](https://twilio.com)
[![PWA](https://img.shields.io/badge/PWA-Installable-5A0FC8?style=for-the-badge&logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)


[![AI-Powered](https://img.shields.io/badge/AI-Gemini%20Flash-blue)](https://deepmind.google/technologies/gemini/flash/)
[![Offline First](https://img.shields.io/badge/Offline-First-orange)](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)

> **Empowering rural communities with Grade-A Medical AI and Offline-First technology.**
> *Pristin Healthcare bridges the gap between remote patients and medical professionals, ensuring quality care regardless of connectivity.*
</div>
-------------------------------------------------------------------------------------------------------------------------------------------------

####  Executive Summary

Pristin Healthcare is an advanced, multilingual telemedicine ecosystem designed specifically for the challenges of rural healthcare in India. It combines modern web technologies (PWA) with cutting-edge AI (Google Gemini) to provide a seamless experience that works both online and offline.

-> Key Features

### 1. 🔍 Advanced AI-Powered Diagnostics
*   **Multimodal Symptom Checker**: Analyze symptoms using text or voice. Powered by **Gemini 1.5 Flash** for deep medical reasoning and multilingual support.
*   **AI Eye Scan (Ophthalmology)**: Upload or take a photo of the eyes to scan for indicators of **Jaundice** or **Anemia**.
*   **AI Facial Health Scan**: Non-invasive scan for visible health indicators (Pallor, Flush, Skin Tone) with a reassuring "Healthy Scan" UI.
*   **AI Meal Analysis**: Snap a photo of your meal to get instant nutritional insights (Calories, Macros) and personalized dietary advice.
*   **AI Prescription Reader (OCR)**: Automatically digitize handwritten or printed prescriptions into structured medicine logs and reminders.

### 2. 📶 Offline-First Resilience
*   **Zero-Internet Functionality**: Log vitals, submit symptom reports, and view past records even with no network connection.
*   **Intelligent Background Sync**: Data saved offline (using **IndexedDB**) automatically syncs to the server the moment connectivity is restored.
*   **Local AI Fallback**: Uses a local **Scikit-Learn** model for basic symptom classification when cloud AI is unreachable.

### 3. 👩‍⚕️ Professional Healthcare Tiered Access
*   **Doctor Dashboard**: Professional interface for physicians to review AI-generated reports, modify diagnoses, and approve treatment plans.
*   **CHW (Community Health Worker) Suite**: Simplified tools for frontline workers to register patients, perform quick screenings, and manage community health files.
*   **Integrated Video Consultations**: Direct video link between patients and doctors with camera/mic optimization.

### 4. 📊 Personal Health Management
*   **Smart Health Timeline**: Visual tracking of Blood Pressure, Glucose, SpO2, and Temperature with automated trend alerts.
*   **Family Proxy Access**: A "Universal Health Account" approach where one family member can manage records for children or elderly relatives.
*   **Rural Pharmacy Locator**: Interactive map (Leaflet.js) to find nearby medicine supplies with mock inventory status.

### 5. 🌍 Accessibility & Engagement
*   **Multilingual Interface**: Full support for **Hindi, Telugu, Tamil, Bengali, Marathi, and Kannada**.
*   **WhatsApp Integration**: Automated WhatsApp alerts for critical health changes and doctor-approved reports using Twilio.
*   **Bandwidth Optimization**: Automatic client-side image compression for fast uploads on 2G/3G networks.

----------------------------------------

## 🛠️ Technical Architecture

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.14+, Flask, SQLAlchemy, Bcrypt |
| **Frontend** | HTML5, Vanilla CSS3 (Pristin Premium Design System), JS (ES6+) |
| **AI / ML** | Google Gemini (Pro/Vision), Scikit-Learn (Local), OpenCV, EasyOCR |
| **Offline/PWA** | Service Workers, Cache API, IndexedDB, Web App Manifest |
| **Infrastructure** | SQLite (Instance Database), Twilio (Messaging), Leaflet (Mapping) |

---

## 📂 Project Structure

```text
├── app.py                  # Core Flask application (Routing & Logic)
├── chatbot_service.py      # Gemini AI Integration (Chat, Scans, Nutrition)
├── translation_service.py  # High-performance localization engine
├── models.py               # Database Schema (Users, Reports, Vitals)
├── static/
│   ├── js/                 # PWA Logic (sw.js), Offline DB, UI logic
│   ├── css/                # Pristin Premium "Liquid Glass" design system
│   └── uploads/            # Secure storage for clinical images
├── templates/              # 35+ Responsive UI templates
└── venv/                   # Python Virtual Environment
```

---

## 📲 Installation & Setup

### Prerequisites
- Python 3.8 or higher.
- Tesseract OCR (Optional, for Prescription OCR).
- Git.

### Quick Start
1.  **Clone the Repo**:
    ```bash
    git clone https://github.com/gojosatorou999/ai-based-rural-healthcare-app.git
    cd ai-based-rural-healthcare-app
    ```
2.  **Initialize Environment**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    pip install -r requirements.txt
    ```
3.  **Configure `.env`**:
    Create a `.env` file and add:
    ```env
    FLASK_SECRET_KEY=your_secured_key
    GEMINI_ANALYSIS_KEY=your_google_gemini_key
    TWILIO_ACCOUNT_SID=your_sid (Optional)
    TWILIO_AUTH_TOKEN=your_token (Optional)
    ```
4.  **Run the Portal**:
    ```bash
    python app.py
    ```
    *The app will automatically initialize the database on first run.*

---

## 👤 Test Personas

- **Patient**: Register a new account to access the personal health dashboard.
- **Doctor**: Register/Login as a doctor to access `/doctor/dashboard` for report reviews.
- **CHW**: Register/Login as a Community Health Worker for the screening interface.

---

## 🛡️ Security & Privacy
- **AES Password Hashing**: All user passwords encrypted with Bcrypt.
- **Data Isolation**: Strict role-based access control (RBAC) ensures patient privacy.
- **Secure Sessions**: Flask-Login sessions with secure cookie handling.

---

**Made with ❤️ for Rural India | [Project Roadmap](PHASE1_SUMMARY.md)**
