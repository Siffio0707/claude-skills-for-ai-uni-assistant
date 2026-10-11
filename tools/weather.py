#!/usr/bin/env python3
"""Today's weather from Open-Meteo (free, no key). Contacts only api.open-meteo.com.

Prints one line, for example:
  date=2026-10-05 high=22 low=11 rain_max=60 umbrella=yes rain_hours=14:00-17:00
Hours are your city time (the API is asked for YOUR_TIMEZONE). Rain is judged over 08:00-23:59;
an hour counts when its chance of rain is 40% or more, and umbrella=yes if any hour does.
On failure prints "weather: unavailable (<reason>)" and exits 1.
"""
import json
import subprocess
import sys
import urllib.parse

URL = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
    "latitude": "YOUR_LATITUDE",
    "longitude": "YOUR_LONGITUDE",
    "daily": "temperature_2m_max,temperature_2m_min",
    "hourly": "precipitation_probability",
    "timezone": "YOUR_TIMEZONE",
    "forecast_days": 1,
})
THRESHOLD = 40
FIRST_HOUR, LAST_HOUR = 8, 23


def main():
    try:
        # System curl: this Python build has no CA bundle, and certificate checks stay on.
        out = subprocess.run(["curl", "-fsS", "--max-time", "15", URL],
                             capture_output=True, text=True, check=True).stdout
        data = json.loads(out)
        day = data["daily"]["time"][0]
        high = round(data["daily"]["temperature_2m_max"][0])
        low = round(data["daily"]["temperature_2m_min"][0])
        hours = [(int(t[11:13]), p) for t, p in
                 zip(data["hourly"]["time"], data["hourly"]["precipitation_probability"])
                 if p is not None and FIRST_HOUR <= int(t[11:13]) <= LAST_HOUR]
    except Exception as exc:  # network, JSON or shape problems
        print(f"weather: unavailable ({type(exc).__name__})")
        return 1

    rain_max = max((p for _, p in hours), default=0)
    wet = [h for h, p in hours if p >= THRESHOLD]
    runs = []
    for h in wet:
        if runs and runs[-1][1] == h:
            runs[-1][1] = h + 1
        else:
            runs.append([h, h + 1])
    rain_hours = ",".join(f"{a:02d}:00-{b:02d}:00" for a, b in runs) or "none"
    print(f"date={day} high={high} low={low} rain_max={rain_max} "
          f"umbrella={'yes' if wet else 'no'} rain_hours={rain_hours}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
