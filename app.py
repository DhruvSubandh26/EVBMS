from flask import Flask, request, jsonify, render_template
import joblib
import os
import psycopg2
from smart_optimizer import smart_optimize_v2

app = Flask(__name__)

# ==============================
# 🔥 DATABASE CONNECTION
# ==============================

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS battery_data (
        id SERIAL PRIMARY KEY,
        voltage FLOAT,
        current FLOAT,
        temperature FLOAT,
        soc FLOAT,
        soh FLOAT,
        prediction TEXT,
        optimized_current FLOAT,
        charging_time TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
else:
    conn = None
    cur = None
    print("⚠️ DATABASE NOT CONNECTED")

# ==============================
# 🔥 LOAD ML MODELS
# ==============================

soc_model = joblib.load("soc_model.pkl")
soh_model = joblib.load("soh_model.pkl")
charging_model = joblib.load("charging_time_model.pkl")

latest_data = {}

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/predict', methods=['POST'])
def predict():
    global latest_data

    data = request.get_json()
    print("Incoming Data:", data)

    voltage = data.get("voltage", 0)
    current = data.get("current", 0)
    temperature = data.get("temperature", 0)

    cycle = data.get("cycle", 100)
    capacity = data.get("capacity", 50)

    try:
        soc = soc_model.predict([[cycle, voltage, temperature, capacity]])[0]
        soh = soh_model.predict([[cycle, voltage, temperature, capacity]])[0] * 100
        charging_time = charging_model.predict([[soc, temperature, voltage]])[0]

        hours = int(charging_time)
        minutes = int((charging_time - hours) * 60)

        optimized_current, severity, alerts = smart_optimize_v2(soc, soh, temperature)

        prediction_text = severity

    except Exception as e:
        print("ML Error:", e)

        soc = (voltage / 12.6) * 100
        soh = 90
        optimized_current = current
        alerts = []
        prediction_text = "Fallback Mode"
        hours, minutes = 0, 0

    latest_data = {
        "voltage": voltage,
        "current": current,
        "temperature": temperature,
        "soc": round(soc, 2),
        "soh": round(soh, 2),
        "alerts": alerts,
        "prediction": prediction_text,
        "optimized_current": optimized_current,
        "charging_time": f"{hours} hr {minutes} min"
    }

    if conn:
        try:
            cur.execute(
                """
                INSERT INTO battery_data 
                (voltage, current, temperature, soc, soh, prediction, optimized_current, charging_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (voltage, current, temperature, soc, soh, prediction_text, optimized_current, f"{hours} hr {minutes} min")
            )
            conn.commit()
        except Exception as e:
            print("DB Insert Error:", e)

    return jsonify({"status": "received"})


@app.route('/data')
def get_data():
    try:
        if conn:
            cur.execute("""
                SELECT voltage, current, temperature, soc, soh, prediction, optimized_current, charging_time
                FROM battery_data
                ORDER BY id DESC LIMIT 1
            """)
            row = cur.fetchone()

            if row:
                return jsonify({
                    "voltage": row[0],
                    "current": row[1],
                    "temperature": row[2],
                    "soc": row[3],
                    "soh": row[4],
                    "prediction": row[5],
                    "optimized_current": row[6],
                    "charging_time": row[7],
                    "alerts": []
                })

        return jsonify(latest_data)

    except Exception as e:
        print("DB Fetch Error:", e)
        return jsonify(latest_data)


@app.route('/test')
def test():
    return jsonify({"status": "Server running"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
