from flask import Flask, request, jsonify, render_template
import joblib
import numpy as np
from smart_optimizer import smart_optimize_v2

app = Flask(__name__)

# 🔥 LOAD MODELS
soc_model = joblib.load("soc_model.pkl")
soh_model = joblib.load("soh_model.pkl")
charging_model = joblib.load("charging_time_model.pkl")

# 🔥 STORE LATEST DATA FOR UI
latest_data = {
    "voltage": 0,
    "current": 0,
    "temperature": 0,
    "soc": 0,
    "soh": 0,
    "alerts": [],
    "prediction": "Waiting..."
}

# 🔥 FRONTEND ROUTE
@app.route('/')
def home():
    return render_template("index.html")

# 🔥 ESP32 DATA COMES HERE
@app.route('/predict', methods=['POST'])
def predict():
    global latest_data

    data = request.get_json()

    # ESP32 sends only these
    voltage = data.get("voltage", 0)
    current = data.get("current", 0)
    temperature = data.get("temperature", 0)

    # 🔥 DUMMY VALUES (since ESP32 doesn't send these)
    cycle = data.get("cycle", 100)
    capacity = data.get("capacity", 50)

    try:
        # 🔥 ML PREDICTIONS
        soc = soc_model.predict([[cycle, voltage, temperature, capacity]])[0]
        soh = soh_model.predict([[cycle, voltage, temperature, capacity]])[0] * 100
        charging_time = charging_model.predict([[soc, temperature, voltage]])[0]

        hours = int(charging_time)
        minutes = int((charging_time - hours) * 60)

        # 🔥 OPTIMIZATION + ALERTS
        optimized_current, severity, alerts = smart_optimize_v2(soc, soh, temperature)

        prediction_text = f"{severity}"

    except Exception as e:
        print("ML Error:", e)

        # 🔥 FALLBACK
        soc = (voltage / 12.6) * 100
        soh = 90
        optimized_current = current
        alerts = []
        prediction_text = "Fallback Mode"

    # 🔥 STORE FOR UI
    latest_data = {
        "voltage": voltage,
        "current": current,
        "temperature": temperature,
        "soc": round(soc, 2),
        "soh": round(soh, 2),
        "alerts": alerts,
        "prediction": prediction_text,
        "optimized_current": optimized_current
    }

    return jsonify({"status": "received"})


# 🔥 UI FETCHES FROM HERE
@app.route('/data')
def get_data():
    return jsonify(latest_data)


# 🔥 OPTIONAL TEST ROUTE
@app.route('/test')
def test():
    return jsonify({"status": "Server running"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
