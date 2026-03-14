import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "potato_transfer_model.h5")
model = tf.keras.models.load_model(MODEL_PATH)




# IMPORTANT: Paste your exact class list here
CLASS_NAMES = [
    'Apple__Black_rot',
    'Apple__healthy',
    'Blueberry__healthy',
    'Corn_(maize)__Common_rust',
    'Corn_(maize)__Northern_Leaf_Blight',
    'Corn_(maize)__healthy',
    'Grape__Black_rot',
    'Potato__Early_blight',
    'Potato__Late_blight',
    'Potato__healthy',
    'Soybean__healthy',
    'Strawberry__healthy',
    'Tomato__Early_blight',
    'Tomato__Late_blight',
    'Tomato__Leaf_Mold',
    'Tomato__healthy'
]

IMG_SIZE = (224, 224)

def predict_image(img_path):
    img = image.load_img(img_path, target_size=IMG_SIZE)
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array)

    print("\n===== DEBUG START =====")
    print("Raw prediction vector:", predictions)
    predicted_index = np.argmax(predictions)
    print("Predicted index:", predicted_index)
    print("CLASS_NAMES:", CLASS_NAMES)
    print("Mapped class:", CLASS_NAMES[predicted_index])
    print("===== DEBUG END =====\n")

    predicted_class = CLASS_NAMES[predicted_index]
    confidence = float(np.max(predictions))

    return predicted_class, round(confidence * 100, 2)

from PIL import Image

def detect_soil_type_from_image(img_path):
    try:
        # Open image and resize to a 50x50 block to average out colors easily
        img = Image.open(img_path).convert('RGB')
        img = img.resize((50, 50))
        
        # Calculate the average color
        np_img = np.array(img)
        avg_color = np.mean(np_img, axis=(0, 1))
        r, g, b = avg_color

        # Simple heuristic to determine soil type based on RGB
        if r > 150 and g > 130 and b < 120:
            return "Sandy"
        elif r > 100 and g < 100 and b < 100:
            return "Clay"
        elif r < 100 and g < 100 and b < 100:
            return "Loamy"
        else:
            return "Silt"
            
    except Exception as e:
        print(f"Error processing soil image: {e}")
        return "Loamy" # Default fallback

def get_crop_recommendations(soil_type, season, water_availability):
    mapping = {
        "Sandy": ["Groundnut", "Watermelon", "Millets"],
        "Clay": ["Rice", "Taro"],
        "Loamy": ["Wheat", "Sugarcane", "Cotton"],
        "Silt": ["Tomato", "Lettuce"]
    }
    
    crops = mapping.get(soil_type, ["Wheat", "Maize", "Tomato"])
    
    explanation = f"These crops grow well in {soil_type.lower()} soil "
    conditions = []
    if water_availability:
        conditions.append(f"with {water_availability.lower()} water availability")
    if season:
        conditions.append(f"during the {season.lower()} season")
        
    if conditions:
        explanation += " and ".join(conditions) + "."
    else:
        explanation += "."
        
    return crops, explanation
