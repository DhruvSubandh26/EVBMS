def smart_optimize_v2(soc, soh, temperature):

    base_current = 1.0  # 1A default charging
    charging_current = base_current

    alerts = []
    severity = "NORMAL"

    # ==============================
    # 1️⃣ Temperature Derating Curve
    # ==============================
    if 35 < temperature <= 40:
        charging_current *= 0.85
        alerts.append("Temperature rising. Mild current reduction.")
        severity = "INFO"

    elif 40 < temperature <= 45:
        charging_current *= 0.6
        alerts.append("High temperature detected. Strong reduction applied.")
        severity = "WARNING"

    elif temperature > 45:
        charging_current = 0.2
        alerts.append("CRITICAL TEMPERATURE! Emergency slow charge.")
        severity = "CRITICAL"

    # ==============================
    # 2️⃣ High SOC Charging Strategy
    # ==============================
    if 80 < soc <= 90:
        charging_current *= 0.7
        alerts.append("SOC above 80%. Activating slow charge mode.")

    elif 90 < soc <= 98:
        charging_current *= 0.5
        alerts.append("SOC above 90%. Trickle charging activated.")

    elif soc > 98:
        charging_current = 0.2
        alerts.append("Battery nearly full. Minimal charging applied.")

    # ==============================
    # 3️⃣ SOH-based Aging Protection
    # ==============================
    if 75 <= soh < 85:
        charging_current *= 0.8
        alerts.append("Battery aging detected. Stress reduction active.")

    elif 60 <= soh < 75:
        charging_current *= 0.6
        alerts.append("Low SOH. Significant stress control enabled.")
        severity = "WARNING"

    elif soh < 60:
        charging_current = 0.2
        alerts.append("CRITICAL SOH! Charging heavily restricted.")
        severity = "CRITICAL"

    # ==============================
    # 4️⃣ Adaptive Protection Rule
    # If both high temp AND low SOH
    # ==============================
    if temperature > 40 and soh < 75:
        charging_current *= 0.7
        alerts.append("Combined thermal + aging stress detected.")

    # ==============================
    # Minimum current safeguard
    # ==============================
    if charging_current < 0.2:
        charging_current = 0.2

    return round(charging_current, 2), severity, alerts



