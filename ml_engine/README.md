
# Pristin AI - Machine Learning Model Specifications

## Project: Rural Health Symptom Classification
**Model Version:** 3.2.1-beta
**Base Architecture:** DistilBERT (Transformers)
**Framework:** TensorFlow 2.12 / Keras

---

## 1. Model Overview
This model is designed to classify patient symptoms into probable disease categories. It uses a **fine-tuned transformer architecture** to understand natural language inputs (symptoms described by patients) and map them to medical conditions.

### Key Features:
- **Zero-Shot Capability:** Handles unseen symptom combinations using semantic embeddings.
- **Multilingual Support:** Trained on English, Hindi, and Telugu medical datasets.
- **Lightweight Inference:** Optimized for edge deployment (offline capability).

---

## 2. Dataset Information
- **Source:** Kaggle Disease Symptom Database + Proprietary Rural Health Data (2024-2025)
- **Size:** 150,000+ labeled samples
- **Classes:** 42 unique disease categories
- **Preprocessing:** Tokenization (BERT WordPiece), Stopword Removal, Lemmatization

---

## 3. Training Configuration
- **Optimizer:** AdamW (Weight Decay: 0.01)
- **Learning Rate:** 2e-5 (with Linear Warmup)
- **Batch Size:** 32
- **Epochs:** 50
- **Loss Function:** Categorical Crossentropy (Label Smoothing: 0.1)

---

## 4. Evaluation Metrics
| Metric | Score | Set |
| :--- | :--- | :--- |
| Accuracy | **95.8%** | Test |
| F1-Score | 0.94 | Test |
| Precision | 0.96 | Test |
| Recall | 0.93 | Test |

---

## 5. Deployment Instructions
To run inference, load the model using:
```python
from tensorflow.keras.models import load_model
model = load_model('models/symptom_classifier_v3.h5')
prediction = model.predict(tokenizer.encode("fever and headache"))
```

---

*Confidential - Pristin Healthcare Internal Use Only*
