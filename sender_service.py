import os
import random
import threading
import time

import requests
from flask import Flask

# ---- Where to send the data (your existing server's /data endpoint) ----
SERVER_URL = "https://pump-server-bridge.onrender.com/data"

SEND_INTERVAL_SECONDS = 2

# ---- Set the random range for each value here (min, max) ----
RANGES = {
    "Vr": (420, 435),
    "Ir": (7.5, 7.9),
    "Ir2": (7.5, 7.9),
    "Vy": (420, 435),
    "Iy": (7.5, 7.9),
    "Iy2": (7.5, 7.9),
    "Vb": (420, 435),
    "Ib": (7.5, 7.9),
    "Ib2": (7.5, 7.9),
    "L0": (0, 1),
    "L1": (0, 1),
    "L2": (0, 1),
    "L3": (0, 1),
    "ton": (0, 5),
    "tof": (0, 5),
    "RPS": (0, 20),
    "PV": (0, 1),
    "r1": (5.0, 15.0),
    "r2": (15.0, 25.0),
    "D": (20, 40),
    "P": (0, 1),
    "M": (100, 110),
}


def rand_val(key):
    lo, hi = RANGES[key]
    if isinstance(lo, int) and isinstance(hi, int):
        return random.randint(lo, hi)
    return round(random.uniform(lo, hi), 1)


def build_packet():
    v = {k: rand_val(k) for k in RANGES}
    line1 = (
        f"Vr={v['Vr']},Ir={v['Ir']},Ir2={v['Ir2']},"
        f"=Vy={v['Vy']},Iy={v['Iy']},Iy2={v['Iy2']},"
        f"Vb={v['Vb']},Ib={v['Ib']},Ib2={v['Ib2']},"
        f"L0={v['L0']},L1={v['L1']},L2={v['L2']},L3={v['L3']},"
        f"ton={v['ton']},tof={v['tof']},RPS={v['RPS']},PV={v['PV']}"
    )
    line2 = f"r1={v['r1']}r2={v['r2']}D={v['D']}P={v['P']}M={v['M']}"
    return line1 + "\n" + line2


last_status = "not started yet"


def send_loop():
    global last_status
    while True:
        packet = build_packet()
        try:
            r = requests.post(
                SERVER_URL,
                data=packet.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
                timeout=5,
            )
            last_status = f"OK ({r.status_code}) at {time.strftime('%H:%M:%S')}"
            print(f"Sent ({r.status_code}):\n{packet}\n")
        except requests.exceptions.RequestException as e:
            last_status = f"FAILED: {e}"
            print(f"Failed to send: {e}")
        time.sleep(SEND_INTERVAL_SECONDS)


# Start the background sending thread once, when the app module loads.
threading.Thread(target=send_loop, daemon=True).start()

# Tiny Flask app just so Render treats this as a valid free Web Service.
app = Flask(__name__)


@app.route("/")
def home():
    return f"Sender is running. Last send: {last_status}"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
