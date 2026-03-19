from flask import Flask, request, jsonify
import joblib
import numpy as np
from smart_optimizer import smart_optimize_v2

app = Flask(__name__)

# Load models
soc_model = joblib.load("soc_model.pkl")
soh_model = joblib.load("soh_model.pkl")
charging_model = joblib.load("charging_time_model.pkl")

@app.route('/')
def home():
    return "EV BMS AI Server Running"

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    cycle = data["cycle"]
    voltage = data["voltage"]
    temperature = data["temperature"]
    capacity = data["capacity"]

    soc = soc_model.predict([[cycle, voltage, temperature, capacity]])[0]
    soh = soh_model.predict([[cycle, voltage, temperature, capacity]])[0] * 100
    charging_time = charging_model.predict([[soc, temperature, voltage]])[0]

    hours = int(charging_time)
    minutes = int((charging_time - hours) * 60)

    current, severity, alerts = smart_optimize_v2(soc, soh, temperature)

    return jsonify({
        "soc": round(soc,2),
        "soh": round(soh,2),
        "charging_time": f"{hours} hr {minutes} min",
        "optimized_current": current,
        "severity": severity,
        "alerts": alerts
    })

app.run(host='0.0.0.0', port=3000)