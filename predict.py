import joblib
import numpy as np

# Load saved model
model = joblib.load("soh_model.pkl")

# Example input: [cycle, voltage, temperature, capacity]
sample_input = np.array([[50, 3.5, 30, 1.5]])

prediction = model.predict(sample_input)

print("Predicted SOH:", prediction[0])
