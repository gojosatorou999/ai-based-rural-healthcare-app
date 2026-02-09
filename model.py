import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os

# Define the model path
MODEL_PATH = "models/eye_scan_model.h5"

# Initialize model variable
model = None

# Load the trained model safely
if os.path.exists(MODEL_PATH):
    try:
        print("🔄 Loading model...")
        model = tf.keras.models.load_model(MODEL_PATH)
        print("✅ Model loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
else:
    print(f"⚠️ Warning: Model file not found at {MODEL_PATH}. Ensure the model is trained and saved correctly.")

# Define class labels (modify as per your dataset)
CLASS_LABELS = ["Normal", "Diabetes", "Alzheimer", "Anemia"]

def predict_eye_disease(img_path):
    """Predicts eye disease based on the given image."""
    if model is None:
        return {"error": "Model not loaded. Check if the model file exists."}

    try:
        # Load and preprocess the image
        img = image.load_img(img_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array /= 255.0  # Normalize

        # Make prediction
        prediction = model.predict(img_array)
        class_index = np.argmax(prediction)
        confidence = np.max(prediction) * 100  # Get confidence percentage

        return {
            "prediction": CLASS_LABELS[class_index],
            "confidence": f"{confidence:.2f}%"
        }
    except Exception as e:
        return {"error": f"Error processing image: {str(e)}"}
