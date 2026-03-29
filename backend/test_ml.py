import requests
import numpy as np
import cv2
import os

# Create a random noise image (non-plant)
img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
img_path = 'test_noise.jpg'
cv2.imwrite(img_path, img)

# We cannot easily test the /upload endpoint without an active login session since it requires @login_required.
# But we can test the function directly!

from ml_utils import validate_plant_image

print("Testing with noise image...")
result = validate_plant_image(img_path)
print(f"Noise image is plant? {result}")

# Create a dummy "green" image which might be misclassified but let's test a real image if we had one.
print("Done.")
