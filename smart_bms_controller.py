import joblib
import numpy as np
from smart_optimizer import smart_optimize_v2

# ==============================
# Load Trained Models
# ==============================
soc_model = joblib.load("soc_model.pkl")
soh_model = joblib.load("soh_model.pkl")
charging_model = joblib.load("charging_time_model.pkl")

# ==============================
# Example Real-Time Sensor Input
# (Replace later with ESP32 data)
# ==============================
cycle = 120
voltage = 3.65
temperature = 41
capacity = 1.4

# ==============================
# Prepare Inputs
# ==============================

# SOC Prediction Input
soc_input = np.array([[cycle, voltage, temperature, capacity]])
soc = soc_model.predict(soc_input)[0]

# SOH Prediction Input
soh_input = np.array([[cycle, voltage, temperature, capacity]])
soh = soh_model.predict(soh_input)[0]

# Charging Time Prediction Input
charging_input = np.array([[soc, temperature, voltage]])
charging_time_hours = charging_model.predict(charging_input)[0]

# Convert time to hr + min
hours = int(charging_time_hours)
minutes = int((charging_time_hours - hours) * 60)

# ==============================
# Optimization Logic
# ==============================
optimized_current, severity, alerts = smart_optimize_v2(soc, soh, temperature)

# ==============================
# FINAL OUTPUT
# ==============================
print("\n========== SMART EV BMS ==========\n")

print(f"SOC: {round(soc,2)} %")
print(f"SOH: {round(soh*100 if soh<=1 else soh,2)} %")
print(f"Estimated Charging Time: {hours} hr {minutes} min")
print(f"Optimized Charging Current: {optimized_current} A")
print(f"Severity Level: {severity}")

print("\nNotifications:")
for alert in alerts:
    print("-", alert)

print("\n==================================")
