
"""
Prisitn AI - Medical Symptom Classifier (Scikit-Learn Version)
==============================================================
Description:
    This script trains a Random Forest classifier on the medical symptom dataset.
    It uses TF-IDF for feature extraction and is optimized for speed and compatibility.
    
    Model Architecture:
    - Feature Extraction: TfidfVectorizer (ngram_range=(1,2))
    - Classifier: RandomForestClassifier (n_estimators=100)

Usage:
    python train_model.py

Author: Rishab (Pristin Healthcare AI Team)
Date: Feb 2026
"""

import os
import time
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

# --- Configuration ---
DATA_PATH = "data/symptom_dataset_processed.csv"
MODEL_SAVE_PATH = "models/symptom_classifier_sklearn.joblib"
LABEL_ENCODER_PATH = "models/symptom_label_encoder.joblib"

print("----------------------------------------------------------------")
print("   PRISTIN AI - MEDICAL MODEL TRAINING PIPELINE (SKLEARN v1)")
print("----------------------------------------------------------------")

# --- 1. Data Loading ---
print("\n[STEP 1/4] Loading Medical Knowledge Graph Data...")

def load_data(data_path):
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}")
    
    df = pd.read_csv(data_path)
    print(f"[INFO] Loaded {len(df)} records. Columns: {df.columns.tolist()}")
    return df

try:
    df = load_data(DATA_PATH)
    texts = df['text'].astype(str).tolist()
    labels = df['label'].tolist()
    
    print(f"[INFO] Sample Text: {texts[0]}")
    print(f"[INFO] Sample Label: {labels[0]}")

except Exception as e:
    print(f"[ERROR] Failed to load data: {e}")
    exit(1)

# --- 2. Model Pipeline ---
print("\n[STEP 2/4] Initializing Scikit-Learn Pipeline...")

# Define Pipeline
model_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=5000)),
    ('clf', RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1))
])

# --- 3. Training Loop ---
print("\n[STEP 3/4] Starting Training...")

# Split Data
# Use stratification to ensure class representation, handle small data gracefully
try:
    X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42, stratify=labels)
except ValueError:
    print("[WARN] Dataset too small for stratified split. Using random split.")
    X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)

# Train
start_time = time.time()
model_pipeline.fit(X_train, y_train)
train_time = time.time() - start_time
print(f"[INFO] Training completed in {train_time:.2f} seconds.")

# --- 4. Evaluation & Saving ---
print("\n[STEP 4/4] Evaluating...")

# Training Performance (Sanity Check)
train_preds = model_pipeline.predict(X_train)
train_acc = accuracy_score(y_train, train_preds)
print(f"Training Accuracy: {train_acc*100:.2f}%")

# Test Performance
preds = model_pipeline.predict(X_test)
acc = accuracy_score(y_test, preds)
print(f"Test Accuracy: {acc*100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test, preds))

print("\n[STEP 5/5] Saving Model Artifacts...")
os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)

# Save Pipeline
joblib.dump(model_pipeline, MODEL_SAVE_PATH)
print(f"[SUCCESS] Model saved to {MODEL_SAVE_PATH}")

print("[INFO] Training Complete. Ready for Deployment.")

