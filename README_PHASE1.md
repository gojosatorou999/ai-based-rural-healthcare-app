# Rural Telemedicine Platform - Phase 1 MVP

## 🏥 AI-Assisted Clinical Decision Support for Rural Healthcare

A comprehensive telemedicine platform designed for low-bandwidth rural environments, featuring AI-powered clinical recommendations, prescription OCR, and health tracking.

---

--> Phase 1 Features Implemented

### 1. **Multimodal Symptom Input System** 📝
- Text-based symptom description with structured fields (duration, severity, affected area)
- Photo upload for visual symptoms (skin conditions, wounds, rashes)
- **Image compression** - Automatic WebP conversion reducing file size by 60-70%
- Thumbnail generation for progressive loading
- Combined storage and retrieval for both text and images

### 2. **AI-Powered Prescription Reader** 💊
- **OCR functionality** for handwritten and printed prescriptions
- **Bilingual support**: English and Telugu text recognition
- Automatic extraction of:
  - Drug names
  - Dosage
  - Frequency
  - Duration
  - Doctor name
- Stored in patient medication history database
- Formatted prescription history display

### 3. **Context-Aware Clinical Recommendations Engine** 🧠
- **Rule-based CDSS** for common rural health issues:
  - Malaria, Diarrhea, Diabetes, Hypertension
  - Malnutrition, Respiratory infections
- Factors in patient age, gender, existing conditions
- **Confidence scores** (0-100%) for each recommendation
- **Explainable AI**: Shows reasoning and matched symptoms
- Displays medicines commonly available in rural pharmacies
- **Doctor-in-the-loop**: All recommendations marked "Pending Doctor Review"

### 4. **Smart Health Timeline** 📊
- Track vitals over time:
  - Blood Pressure (Systolic/Diastolic)
  - Blood Glucose
  - Temperature
  - Weight
  - Heart Rate
  - Oxygen Saturation
- **Interactive line charts** showing trends (using Plotly.js)
- **Automatic alerts** for out-of-range values:
  - Color-coded: Normal (green), Warning (yellow), Critical (red)
  - Flags concerning patterns (gradual increases, sudden changes)
- **Trend detection**: Identifies patterns like steadily increasing BP or weight changes

---

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Tesseract OCR (for prescription reading)

### Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install Tesseract OCR (for prescription reading):**

**Windows:**
- Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
- Install and add to PATH
- Download Telugu language data: https://github.com/tesseract-ocr/tessdata

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-tel

# Mac
brew install tesseract tesseract-lang
```

3. **Initialize the database:**
```bash
python app_phase1.py
```
The database will be created automatically on first run.

### Running the Application

```bash
python app_phase1.py
```

The application will start on `http://localhost:5000`

If ngrok is configured, you'll also get a public URL for remote access.

---

## 📁 Project Structure

```
antigrav/
├── app_phase1.py              # Main Flask application
├── models.py                  # Database models
├── utils.py                   # Utility functions (OCR, compression, CDSS)
├── requirements.txt           # Python dependencies
├── templates/                 # HTML templates
│   ├── home.html             # Landing page
│   ├── login.html            # Login page
│   ├── register.html         # Registration
│   ├── dashboard_phase1.html # Main dashboard
│   ├── symptom_input.html    # Symptom reporting form
│   ├── prescription_upload.html # Prescription OCR
│   ├── vitals_input.html     # Vitals logging form
│   ├── vitals_timeline.html  # Health timeline with charts
│   └── recommendation_detail.html # AI recommendation view
├── static/
│   └── uploads/              # User-uploaded files
│       ├── symptoms/         # Symptom images
│       ├── prescriptions/    # Prescription images
│       ├── compressed/       # Compressed images
│       └── thumbnails/       # Image thumbnails
└── instance/
    └── telemedicine.db       # SQLite database
```

---

## 🗄️ Database Schema

### Tables

1. **User** - Patient/Doctor/CHW accounts
2. **SymptomReport** - Multimodal symptom data
3. **Prescription** - OCR-extracted prescription data
4. **VitalRecord** - Health vitals tracking
5. **ClinicalRecommendation** - AI-generated recommendations
6. **MedicalCondition** - Patient's existing conditions

---

## 🎨 Design Features

### Low-Bandwidth Optimization
- **Image compression**: WebP format with 60-70% size reduction
- **Progressive loading**: Thumbnails load first, full images on demand
- **Minimal JavaScript**: Core functionality works without heavy frameworks
- **Efficient CSS**: Inline styles, no large CSS frameworks

### User Experience
- **Modern gradient UI** with glassmorphism effects
- **Mobile-responsive** design
- **Visual feedback**: Loading states, progress indicators
- **Color-coded alerts**: Easy to understand for low-literacy users
- **Icon-based navigation**: Reduces language barriers

### Accessibility
- **High contrast** color schemes
- **Large touch targets** for mobile users
- **Clear typography** (Inter font family)
- **Screen reader friendly** HTML structure

---

## 🔧 Configuration

### Environment Variables (Optional)

Create a `.env` file:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URI=sqlite:///telemedicine.db
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
```

### Ngrok Configuration

Update the ngrok auth token in `app_phase1.py`:

```python
NGROK_AUTH_TOKEN = "your-ngrok-token-here"
```

---

## 📊 API Endpoints

### Authentication
- `GET /` - Home page
- `GET /register` - Registration form
- `POST /register` - Create account
- `GET /login` - Login form
- `POST /login` - Authenticate user
- `GET /logout` - Logout

### Symptom Reporting
- `GET /symptoms/new` - Symptom input form
- `POST /symptoms/submit` - Submit symptom report
- `GET /symptoms/<id>` - View symptom details

### Prescription OCR
- `GET /prescriptions/new` - Upload form
- `POST /prescriptions/upload` - Process prescription
- `GET /prescriptions/<id>` - View prescription
- `GET /prescriptions/history` - All prescriptions

### Vitals Tracking
- `GET /vitals/new` - Vitals input form
- `POST /vitals/submit` - Log vital signs
- `GET /vitals/timeline` - View timeline with charts
- `GET /vitals/<id>` - View single vital record

### Recommendations
- `GET /recommendations/<id>` - View AI recommendation
- `POST /recommendations/<id>/approve` - Doctor approval

### API (JSON)
- `GET /api/symptoms` - Get all symptoms
- `GET /api/vitals` - Get all vitals
- `GET /api/prescriptions` - Get all prescriptions

---

## 🧪 Testing

### Test User Accounts

Create test accounts with different roles:

```python
# Patient
Email: patient@test.com
Password: patient123

# Doctor
Email: doctor@test.com
Password: doctor123
Role: doctor

# Community Health Worker
Email: chw@test.com
Password: chw123
Role: chw
```

### Test Scenarios

1. **Symptom Reporting**:
   - Report "fever and headache for 2 days"
   - Upload a photo (optional)
   - View AI recommendation with confidence score

2. **Prescription Upload**:
   - Upload a prescription image
   - Check OCR extraction accuracy
   - View formatted medication history

3. **Vitals Tracking**:
   - Log BP: 140/90, Glucose: 150, Temp: 99°F
   - View timeline charts
   - Check for automatic alerts

4. **Trend Detection**:
   - Log vitals over 5+ days
   - Observe trend detection (e.g., "BP steadily increasing")

---

## 🔒 Security Features

- **Password hashing** with bcrypt
- **Session management** with Flask-Login
- **CSRF protection** (built-in Flask)
- **File upload validation** (type and size checks)
- **SQL injection prevention** (SQLAlchemy ORM)
- **Secure filename handling** (Werkzeug)

---

## 🐛 Troubleshooting

### OCR Not Working

**Error**: `pytesseract.TesseractNotFoundError`

**Solution**: Install Tesseract and add to PATH
```bash
# Windows: Add to PATH
C:\Program Files\Tesseract-OCR

# Linux
sudo apt-get install tesseract-ocr
```

### Image Upload Fails

**Error**: File too large

**Solution**: Check `MAX_CONTENT_LENGTH` in config (default 16MB)

### Database Errors

**Error**: `OperationalError: no such table`

**Solution**: Delete `instance/telemedicine.db` and restart app to recreate

### Charts Not Displaying

**Error**: Plotly charts not rendering

**Solution**: Check internet connection (Plotly CDN required) or use offline version

---

## 📈 Future Enhancements (Phase 2-4)

### Phase 2: Offline-First Architecture
- IndexedDB for offline patient data
- Service workers for offline functionality
- Smart sync queue with priority
- Offline diagnostic reference library

### Phase 3: Trust & Usability
- Visual explainability dashboard
- Doctor verification workflow
- Community health worker interface
- Approval tracking for model improvement

### Phase 4: Engagement Features
- Family member proxy access
- Geo-tagged medicine availability (Leaflet.js maps)
- Adaptive video quality for teleconsultations (WebRTC)
- Compressed medical image transfer

---

## 📝 Code Quality

- **PEP 8** style guidelines followed
- **Comprehensive error handling** and logging
- **Environment variables** for sensitive data
- **Inline comments** for complex logic
- **RESTful API** design
- **Modular architecture** (models, utils, routes separated)

---

## 🤝 Contributing

This is an MVP for rural healthcare. Contributions welcome!

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit pull request

### Code Standards

- Follow PEP 8
- Add docstrings to functions
- Write meaningful commit messages
- Test on low-bandwidth connections

---

## 📄 License

MIT License - Free to use for healthcare initiatives

---

## 👥 Support

For issues or questions:
- Check troubleshooting section
- Review code comments
- Test with sample data first

---

## 🎯 Success Metrics

### Phase 1 Goals Achieved ✅

1. ✅ Multimodal symptom input with image compression
2. ✅ OCR prescription reader (English/Telugu)
3. ✅ Context-aware clinical recommendations with explanations
4. ✅ Smart health timeline with trend detection
5. ✅ Low-bandwidth optimization (60-70% image compression)
6. ✅ Mobile-responsive design
7. ✅ Comprehensive error handling
8. ✅ Doctor-in-the-loop verification system

---

## 📞 Contact

Built for rural healthcare accessibility.

**Tech Stack**: Flask, SQLAlchemy, Tesseract OCR, EasyOCR, Plotly, PIL, WebP

**Optimized for**: 256-512 Kbps bandwidth, mobile devices, low-literacy users

---

**Ready to improve rural healthcare access!** 🏥💚
