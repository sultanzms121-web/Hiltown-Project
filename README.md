# Hiltown Hotel Sylhet — IoT Room & Energy Control System

A premium control dashboard for monitoring rooms and controlling AC, fan,
light and heater — plus monthly energy reporting. Built with **Python
(Flask)** serving a custom animated web dashboard (blue & white theme).

> **This is the full final-system interface.** Every control is interactive so
> the hotel owner can preview the complete product. In the current prototype,
> **Room 101's AC** is wired to real hardware via **ESP32 + Blynk**; everything
> else runs in simulation until each device is integrated.

---

## Run it

```bash
cd hiltown_dashboard
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** and click **Sign In** on the login screen.

> No ESP32 needed to demo. The dashboard is fully interactive on its own.

---

## What the dashboard shows

| Area | What it does |
|------|--------------|
| **Dashboard** | Live stat cards (rooms, online, appliances, energy), 6-month energy chart, alerts, room status, activity feed |
| **Rooms** | Every room as a card — AC (power + temperature dial + mode), fan, light, heater toggles, per-room energy, online/offline switch, full-control modal |
| **Offline rule** | Flip a room **Offline** and watch AC, fan, light & heater auto shut down (the core automation from the spec). "Shut down empty rooms" applies it to all unoccupied rooms |
| **Energy** | Monthly trend, per-room table with **meter coverage flags** (Full / Partial / No data — never counted as zero) |
| **Activity** | Full command & event audit trail (goes to Firebase in the final system) |
| **Architecture** | Live integration status for Dashboard / Blynk / MQTT / Firebase / Security |

Extras: login with role selection, live clock, global search, light/dark theme,
toast feedback, smooth animations & transitions throughout.

---

## Demo tips for the owner meeting

1. Sign in → land on **Dashboard** (numbers count up, chart animates).
2. Go to **Rooms** → toggle the AC on Room 101 (badged **⚡ Live** — the real prototype).
3. Flip Room **104** to **Offline** → all its appliances shut down automatically.
4. Click **Shut down empty rooms** → the offline rule cascades across empty rooms.
5. Open **Energy** → show per-room usage and the flagged incomplete meters.
6. Open **Architecture** → explain what's live now vs. what goes live after the deal.

---

## Going from prototype → final system

The UI stays the same. Only `app.py` server functions change. Open `app.py`
and flip these switches as each layer is integrated:

```python
USE_REAL_HARDWARE = False   # Room 101 AC via Blynk
USE_MQTT          = False   # Live command/status for all rooms
USE_FIREBASE      = False   # Cloud storage for rooms, energy, logs
```

The integration points are already stubbed and commented:

- **Blynk** — `_blynk_set_ac_power()`, `_blynk_set_ac_temp()` (prototype, Room 101)
- **MQTT** — `_mqtt_publish()`, topics like `hotel/room/101/ac/command`
- **Firebase** — `_firebase_log_event()`, `_firebase_monthly_energy()`

### API routes (ready for the dashboard to call)
| Route | Purpose |
|-------|---------|
| `POST /api/room/<id>/<appliance>/command` | Turn an appliance on/off |
| `POST /api/room/<id>/ac/temp` | Set AC temperature |
| `POST /api/room/<id>/offline` | Apply the offline-shutdown rule |
| `POST /api/booking/webhook` | Check-in/out events from the hotel's booking site |
| `GET  /api/energy/monthly` | Monthly energy summary |

### Occupancy = booking system (not set by hand)
Occupancy is **owned by the hotel's existing check-in/check-out website**, matched
by room number. When a room is booked/checked-in there, it shows here as
**Occupied**; on checkout it flips to **Vacant** and the shutdown rule fires.
The site sends events to `POST /api/booking/webhook` (or we poll its API — set
`USE_BOOKING_SYNC`, `BOOKING_WEBHOOK_SECRET`, `BOOKING_API_URL` in `app.py`).
In the demo, the **"Simulate check-in/out"** button on the Room Board plays this
feed so you can show the owner the link working.

---

## Project structure

```
hiltown_dashboard/
├── app.py              # Flask server + stubbed Blynk/MQTT/Firebase integration
├── requirements.txt
├── README.md
└── templates/
    └── index.html      # The full premium dashboard (self-contained)
```

---

## Notes carried over from the project spec

- An **OFF command is not the same as a verified OFF state** — the final build
  shows device status only when firmware confirms it.
- **Monthly energy** requires validated meter readings; missing data is
  **flagged**, never treated as zero consumption.
- Meter coverage (per room / per appliance / hotel-wide) is a decision to
  confirm with the hardware team.

---

*Prototype for Hiltown Hotel Sylhet. All figures are demo placeholders.*
