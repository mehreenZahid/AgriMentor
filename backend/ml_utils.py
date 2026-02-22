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

