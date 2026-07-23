import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import random

# Training Data
TRAINING_DATA = [
    # 60+ samples across 12 categories
    ("need an oil change", "Oil Change"),
    ("engine oil is dark and dirty", "Oil Change"),
    ("car needs new oil and filter", "Oil Change"),
    ("routine oil service", "Oil Change"),
    ("oil level is very low", "Oil Change"),
    
    ("brakes are squeaking", "Brake Repair"),
    ("brake pedal goes to the floor", "Brake Repair"),
    ("grinding noise when I brake", "Brake Repair"),
    ("brakes feel spongy", "Brake Repair"),
    ("brake pads are worn out", "Brake Repair"),
    
    ("car won't start", "Battery Replacement"),
    ("battery is dead", "Battery Replacement"),
    ("need a new car battery", "Battery Replacement"),
    ("alternator is fine but battery drains", "Battery Replacement"),
    ("dim headlights and no start", "Battery Replacement"),
    
    ("ac blows hot air", "AC Repair"),
    ("air conditioning not working", "AC Repair"),
    ("ac smells bad", "AC Repair"),
    ("no cold air from vents", "AC Repair"),
    ("ac compressor makes noise", "AC Repair"),
    
    ("engine check light is on", "Engine Repair"),
    ("engine is overheating", "Engine Repair"),
    ("smoke coming from the engine", "Engine Repair"),
    ("engine misfire", "Engine Repair"),
    ("car stalling while driving", "Engine Repair"),
    
    ("clutch slipping", "Clutch Repair"),
    ("hard to shift gears", "Clutch Repair"),
    ("clutch pedal is stiff", "Clutch Repair"),
    ("smell of burning from clutch", "Clutch Repair"),
    ("gearbox grinding when shifting", "Clutch Repair"),
    
    ("car bounces too much", "Suspension Repair"),
    ("clunking noise over bumps", "Suspension Repair"),
    ("steering wheel vibrates", "Suspension Repair"),
    ("car pulls to one side", "Suspension Repair"),
    ("shocks and struts are leaking", "Suspension Repair"),
    
    ("headlights not working", "Electrical Repair"),
    ("power windows are stuck", "Electrical Repair"),
    ("blown fuse", "Electrical Repair"),
    ("dashboard lights flickering", "Electrical Repair"),
    ("horn doesn't work", "Electrical Repair"),
    
    ("flat tyre", "Tyre Replacement"),
    ("tires are bald", "Tyre Replacement"),
    ("need new tyres", "Tyre Replacement"),
    ("puncture repair", "Tyre Replacement"),
    ("tyre burst on highway", "Tyre Replacement"),
    
    ("dent on the bumper", "Body Repair"),
    ("scratches on the door", "Body Repair"),
    ("car was in an accident, front smashed", "Body Repair"),
    ("need paint touch up", "Body Repair"),
    ("windshield is cracked", "Body Repair"),
    
    ("transmission fluid leaking", "Transmission Repair"),
    ("automatic gears not shifting smoothly", "Transmission Repair"),
    ("transmission slipping", "Transmission Repair"),
    ("delay in gear engagement", "Transmission Repair"),
    ("whining noise from transmission", "Transmission Repair"),
    
    ("radiator is leaking coolant", "Radiator Repair"),
    ("engine overheating, coolant low", "Radiator Repair"),
    ("need radiator flush", "Radiator Repair"),
    ("broken radiator fan", "Radiator Repair"),
    ("steam from the hood", "Radiator Repair"),
    
    ("replace brake rotors", "Brake Repair"),
    ("synthetic oil change", "Oil Change"),
    ("battery terminal corroded", "Battery Replacement"),
    ("recharge ac gas", "AC Repair"),
    ("check engine light code p0300", "Engine Repair")
]

pipeline = None

def train_model():
    global pipeline
    try:
        X, y = zip(*TRAINING_DATA)
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(stop_words='english', ngram_range=(1, 2))),
            ('clf', MultinomialNB())
        ])
        pipeline.fit(X, y)
        print("AI Diagnosis model trained successfully.")
    except Exception as e:
        print(f"Error training AI model: {e}")

def diagnose(text):
    if pipeline is None:
        return {
            "predicted_service": "Unknown",
            "confidence": 0.0,
            "urgency": "Low",
            "keywords_matched": []
        }
        
    try:
        text_lower = text.lower()
        prediction = pipeline.predict([text_lower])[0]
        probabilities = pipeline.predict_proba([text_lower])[0]
        confidence = max(probabilities)
        
        # Urgency detection
        high_urgency_words = ['not starting', 'smoke', 'grinding', 'overheating', 'brake fail', 'leaking', 'stalling']
        medium_urgency_words = ['noise', 'vibration', 'slow', 'rough idle', 'warning light']
        
        urgency = "Low"
        matched = []
        
        for word in high_urgency_words:
            if word in text_lower:
                urgency = "High"
                matched.append(word)
                
        if urgency == "Low":
            for word in medium_urgency_words:
                if word in text_lower:
                    urgency = "Medium"
                    matched.append(word)
                    
        return {
            "predicted_service": prediction,
            "confidence": float(confidence),
            "urgency": urgency,
            "keywords_matched": matched
        }
    except Exception as e:
        print(f"Diagnosis error: {e}")
        return {
            "predicted_service": "Unknown",
            "confidence": 0.0,
            "urgency": "Low",
            "keywords_matched": []
        }
