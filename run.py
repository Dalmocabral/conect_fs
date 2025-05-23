from SimConnect import *

sm = SimConnect()
aq = AircraftRequests(sm, _time=2000)

while True:
    altitude = aq.get("PLANE_ALTITUDE")
    speed = aq.get("AIRSPEED_INDICATED")
    print(f"Altitude: {altitude:.0f} ft | Speed: {speed:.0f} knots")
