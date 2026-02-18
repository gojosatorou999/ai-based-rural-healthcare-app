
"""
Database of disease information for the AI Health App.
Used for fallback diagnosis when Gemini is offline or for rapid local lookup.
"""

DISEASE_INFO = {
    "Flu": {
        "disease": "Flu",
        "description": "Flu is a contagious respiratory illness caused by influenza viruses.",
        "causes": "It spreads through virus-infected droplets from coughing, sneezing, or touching contaminated surfaces.",
        "symptoms": "Fever, cough, sore throat, body aches, fatigue.",
        "treatment": "Rest, hydration, over-the-counter fever reducers like ibuprofen.",
        "doctor": "General physician"
    },
    "Malaria": {
        "disease": "Malaria",
        "description": "Malaria is a mosquito-borne disease caused by Plasmodium parasites.",
        "causes": "Transmitted through the bite of infected female Anopheles mosquitoes.",
        "symptoms": "Chills, fever, sweating, headache, nausea.",
        "treatment": "Antimalarial medication prescribed by a doctor, rest, hydration.",
        "doctor": "General Physician"
    },
    "Chronic Fatigue Syndrome": {
        "disease": "Chronic Fatigue Syndrome",
        "description": "A long-term illness characterized by extreme fatigue that doesn’t improve with rest.",
        "causes": "Unknown, but possibly linked to viral infections, immune system problems, or hormonal imbalances.",
        "symptoms": "Extreme tiredness, muscle pain, difficulty concentrating, sore throat.",
        "treatment": "Lifestyle changes, therapy, and symptom management.",
        "doctor": "General physician or neurologist"
    },
    "Anemia": {
        "disease": "Anemia",
        "description": "A condition where the body lacks enough healthy red blood cells to carry oxygen.",
        "causes": "Iron deficiency, vitamin deficiency, chronic diseases, or blood loss.",
        "symptoms": "Weakness, fatigue, pale skin, dizziness, shortness of breath.",
        "treatment": "Iron supplements, dietary changes, or treating underlying conditions.",
        "doctor": "Hematologist"
    },
    "Diabetes": {
        "disease": "Diabetes",
        "description": "A metabolic disorder that affects blood sugar regulation.",
        "causes": "Insufficient insulin production or insulin resistance.",
        "symptoms": "Unexplained weight loss, excessive thirst, frequent urination, fatigue.",
        "treatment": "Insulin therapy, medication, lifestyle changes.",
        "doctor": "Endocrinologist"
    },
    "Tuberculosis": {
        "disease": "Tuberculosis",
        "description": "A bacterial infection that mainly affects the lungs.",
        "causes": "Caused by Mycobacterium tuberculosis, spread through respiratory droplets.",
        "symptoms": "Night sweats, fever, cough, weight loss, fatigue.",
        "treatment": "Antibiotic regimen (e.g., isoniazid, rifampin, ethambutol).",
        "doctor": "Pulmonologist"
    },
    "Strep Throat": {
        "disease": "Strep Throat",
        "description": "A bacterial infection causing inflammation and pain in the throat.",
        "causes": "Caused by group A Streptococcus bacteria.",
        "symptoms": "Sore throat, swollen tonsils, fever, difficulty swallowing.",
        "treatment": "Antibiotics (penicillin or amoxicillin), pain relievers.",
        "doctor": "General physician or ENT specialist"
    },
    "Common Cold": {
        "disease": "Common Cold",
        "description": "A viral infection affecting the upper respiratory tract.",
        "causes": "Spread through respiratory droplets, commonly caused by rhinoviruses.",
        "symptoms": "Runny nose, sneezing, sore throat, mild cough.",
        "treatment": "Rest, fluids, over-the-counter cold medications.",
        "doctor": "General physician"
    },
    "Migraine": {
        "disease": "Migraine",
        "description": "A neurological condition that causes intense, throbbing headaches.",
        "causes": "Stress, hormonal changes, certain foods, lack of sleep.",
        "symptoms": "Headache, nausea, sensitivity to light and sound, visual disturbances.",
        "treatment": "Pain relievers, lifestyle changes, migraine-specific medications.",
        "doctor": "Neurologist"
    },
    "Allergy": {
        "disease": "Allergy",
        "description": "A hypersensitive response of the immune system to allergens.",
        "causes": "Food, medications, insect stings, pollen, pet dander.",
        "symptoms": "Itchy skin, hives, swelling, redness, sneezing.",
        "treatment": "Antihistamines, corticosteroids, avoiding allergens.",
        "doctor": "Allergist or Dermatologist"
    },
    "Arthritis": {
        "disease": "Arthritis",
        "description": "Inflammation of one or more joints, causing pain and stiffness.",
        "causes": "Age, wear and tear, autoimmune diseases, infections.",
        "symptoms": "Joint pain, stiffness, swelling, decreased range of motion.",
        "treatment": "Pain relievers, physical therapy, lifestyle changes, surgery in severe cases.",
        "doctor": "Rheumatologist"
    },
    "Depression": {
        "disease": "Depression",
        "description": "A mood disorder causing persistent sadness and loss of interest.",
        "causes": "Genetics, brain chemistry, trauma, stress, medical conditions.",
        "symptoms": "Persistent sadness, loss of interest, fatigue, changes in appetite or sleep.",
        "treatment": "Therapy, medications (antidepressants), lifestyle changes.",
        "doctor": "Psychiatrist"
    },
    "Anxiety": {
        "disease": "Anxiety",
        "description": "A mental health condition causing excessive fear, worry, or nervousness.",
        "causes": "Genetics, stress, trauma, medical conditions, substance abuse.",
        "symptoms": "Excessive worry, restlessness, rapid heartbeat, sweating, dizziness.",
        "treatment": "Therapy, medications (anti-anxiety drugs), relaxation techniques.",
        "doctor": "Psychiatrist"
    }
}
