"""
Hiltown Hotel Sylhet — IoT Room & Energy Control System
=======================================================
Flask backend for the control dashboard.

PROTOTYPE STAGE (now):
    - Serves the full final-system dashboard UI.
    - Room 101 AC is driven by real hardware through ESP32 + Blynk.
    - All other controls run as a front-end simulation so the owner can
      preview the complete experience before every device is wired up.

FINAL STAGE (after the deal is confirmed):
    - Flip USE_REAL_HARDWARE / USE_MQTT / USE_FIREBASE to True and fill in
      the stubbed functions below. The dashboard UI does NOT change — only
      these server functions start talking to real services.

Run:
    pip install -r requirements.txt
    python app.py
    # open http://127.0.0.1:5000
"""

from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Integration switches — all OFF for the prototype demo.
# Turn these on one at a time as each layer is integrated.
# ---------------------------------------------------------------------------
USE_REAL_HARDWARE = False   # Room 101 AC via Blynk (prototype target)
USE_MQTT          = False   # Live command/status channel (final system)
USE_FIREBASE      = False   # Cloud data store (final system)
USE_BOOKING_SYNC  = False   # Link to the hotel's check-in/check-out website

# Booking system link (the hotel's existing booking/reservation site).
# Occupancy is owned by that site, not set in this dashboard. It tells us a
# room's state either by calling the webhook below, or we poll its API.
BOOKING_WEBHOOK_SECRET = "SET_A_SHARED_SECRET"   # verify incoming webhook calls
BOOKING_API_URL        = "https://booking.hiltownhotel.example/api"  # if polling instead

# Blynk config for the prototype (fill in when ESP32 is handed over)
BLYNK_AUTH_TOKEN  = "YOUR_BLYNK_TOKEN_HERE"
BLYNK_BASE_URL    = "https://blynk.cloud/external/api"
# Virtual pins agreed with the hardware team:
BLYNK_PIN_AC_POWER = "V0"   # 0 / 1
BLYNK_PIN_AC_TEMP  = "V1"   # 16..30

# MQTT topic template for the final system
MQTT_TOPIC = "hotel/room/{room}/{appliance}/command"


# ===========================================================================
# PAGE
# ===========================================================================
@app.route("/")
def index():
    return render_template("index.html")


# ===========================================================================
# CONTROL API
# The dashboard can POST here later. Right now these are safe stubs that just
# acknowledge the command and show exactly where real integration slots in.
# ===========================================================================
@app.route("/api/room/<room_id>/<appliance>/command", methods=["POST"])
def appliance_command(room_id, appliance):
    """Turn an appliance ON/OFF.  Body: {"state": true|false}"""
    state = bool(request.json.get("state", False)) if request.is_json else False

    # --- PROTOTYPE: Room 101 AC via Blynk ---------------------------------
    if USE_REAL_HARDWARE and room_id == "101" and appliance == "ac":
        return _blynk_set_ac_power(state)

    # --- FINAL SYSTEM: publish over MQTT ----------------------------------
    if USE_MQTT:
        return _mqtt_publish(room_id, appliance, {"state": state})

    # --- SIMULATION (default) ---------------------------------------------
    return jsonify(ok=True, mode="simulation", room=room_id,
                   appliance=appliance, state=state,
                   note="Command accepted (not sent to hardware yet).")


@app.route("/api/room/<room_id>/ac/temp", methods=["POST"])
def ac_set_temp(room_id):
    """Set AC temperature. Body: {"temp": 16..30}"""
    temp = int(request.json.get("temp", 24)) if request.is_json else 24
    temp = max(16, min(30, temp))

    if USE_REAL_HARDWARE and room_id == "101":
        return _blynk_set_ac_temp(temp)
    if USE_MQTT:
        return _mqtt_publish(room_id, "ac", {"temp": temp})

    return jsonify(ok=True, mode="simulation", room=room_id, temp=temp)


@app.route("/api/room/<room_id>/offline", methods=["POST"])
def mark_offline(room_id):
    """Apply the automatic Offline-room rule: OFF for all four appliances."""
    results = {}
    for appliance in ("ac", "fan", "light", "heater"):
        if USE_MQTT:
            _mqtt_publish(room_id, appliance, {"state": False})
        results[appliance] = "off"
    # In the final system this event is written to Firebase (roomEvents).
    if USE_FIREBASE:
        _firebase_log_event(room_id, "auto_offline_shutdown", results)
    return jsonify(ok=True, room=room_id, rule="offline_shutdown",
                   appliances=results, mode=_mode())


@app.route("/api/booking/webhook", methods=["POST"])
def booking_webhook():
    """Receive check-in / check-out events from the hotel's booking website.

    The booking site POSTs here whenever a room's reservation changes, e.g.:
        {"room": "101", "event": "check_in"}    -> dashboard shows Occupied
        {"room": "101", "event": "check_out"}   -> dashboard shows Vacant
    Occupancy is therefore driven by the booking system, matched by room
    number — staff never set it by hand here.
    """
    data = request.json or {}
    room = str(data.get("room", ""))
    event = data.get("event")            # "check_in" | "check_out"
    # Production: verify the request against BOOKING_WEBHOOK_SECRET first, then
    # update the room's occupancy/booking state (Firebase) and the board.
    if event == "check_out":
        # vacancy rule — turn every appliance off for the freed room
        for appliance in ("ac", "fan", "light", "heater"):
            if USE_MQTT:
                _mqtt_publish(room, appliance, {"state": False})
        if USE_FIREBASE:
            _firebase_log_event(room, "checkout_auto_shutdown", {})

    return jsonify(ok=True, room=room, event=event, mode=_mode(),
                   occupancy=("Occupied" if event == "check_in" else "Vacant"),
                   note="Booking event accepted (stub — wire to booking site).")


@app.route("/api/energy/monthly")
def energy_monthly():
    """Monthly energy summary (served from Firebase in the final system)."""
    if USE_FIREBASE:
        return jsonify(_firebase_monthly_energy())
    # Prototype placeholder data:
    return jsonify(ok=True, mode="simulation", yearMonth="2026-10",
                   note="Real totals come from validated meter readings.")


# ===========================================================================
# INTEGRATION STUBS  — implement these in the final phase
# ===========================================================================
def _mode():
    if USE_MQTT:
        return "mqtt"
    if USE_REAL_HARDWARE:
        return "blynk"
    return "simulation"


def _blynk_set_ac_power(state):
    """PROTOTYPE: set Room 101 AC power through Blynk Cloud HTTP API."""
    # import requests
    # value = 1 if state else 0
    # url = f"{BLYNK_BASE_URL}/update?token={BLYNK_AUTH_TOKEN}&{BLYNK_PIN_AC_POWER}={value}"
    # requests.get(url, timeout=5)
    return jsonify(ok=True, mode="blynk", room="101", appliance="ac",
                   state=state, note="Stub — wire Blynk HTTP API here.")


def _blynk_set_ac_temp(temp):
    """PROTOTYPE: set Room 101 AC temperature through Blynk Cloud."""
    # import requests
    # url = f"{BLYNK_BASE_URL}/update?token={BLYNK_AUTH_TOKEN}&{BLYNK_PIN_AC_TEMP}={temp}"
    # requests.get(url, timeout=5)
    return jsonify(ok=True, mode="blynk", room="101", temp=temp,
                   note="Stub — wire Blynk HTTP API here.")


def _mqtt_publish(room_id, appliance, payload):
    """FINAL: publish a command to the room/appliance MQTT topic."""
    topic = MQTT_TOPIC.format(room=room_id, appliance=appliance)
    # import paho.mqtt.publish as publish, json
    # publish.single(topic, json.dumps(payload), hostname=MQTT_HOST, ...)
    return jsonify(ok=True, mode="mqtt", topic=topic, payload=payload,
                   note="Stub — connect your MQTT broker here.")


def _firebase_log_event(room_id, event, data):
    """FINAL: append an event to Firebase (roomEvents collection)."""
    pass  # firestore.collection("roomEvents").add({...})


def _firebase_monthly_energy():
    """FINAL: read monthly totals from Firebase (monthlyEnergy collection)."""
    return {"ok": True, "mode": "firebase", "note": "Stub."}


if __name__ == "__main__":
    print("  Hiltown Hotel Sylhet — IoT Control System")
    print("  Mode:", _mode().upper(), "| open http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
