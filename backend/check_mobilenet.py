import tensorflow as tf
import numpy as np

model = tf.keras.applications.MobileNetV2(weights='imagenet')
# Create a dummy green image just to see if it loads correctly
img_array = np.zeros((1, 224, 224, 3))
img_array[:, :, :, 1] = 255 # Green
img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)

preds = model.predict(img_array)
dec_preds = tf.keras.applications.mobilenet_v2.decode_predictions(preds, top=20)[0]
for p in dec_preds:
    print(p)
