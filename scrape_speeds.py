#%%
import requests
from bs4 import BeautifulSoup

URL = "https://nl.windfinder.com/weatherforecast/brouwersdam"

def get_wind_values(url):
    """Returns a list of dicts with speed, temperature, direction for 72 hours"""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Wind speeds
    speed_divs = soup.find_all("div", class_="speed")
    speeds = []
    for div in speed_divs:
        span = div.find("span", class_="units-ws")
        if span:
            try:
                speeds.append(float(span.contents[0]))
            except Exception:
                speeds.append(None)

    # Wind directions
    direction_divs = soup.find_all("div", class_="data-windbar--mobile")
    directions = []
    for div in direction_divs:
        # windfinder uses classes like ws15, ws20, etc. for direction
        for cls in div.get("class", []):
            if cls.startswith("ws") and cls[2:].isdigit():
                deg = int(cls[2:]) * 10
                # Windfinder: South = 0, so correct by +180 and modulo 360
                deg = (deg + 180) % 360
                directions.append(deg)
                break
        else:
            directions.append(None)

    # Temperatures
    temp_divs = soup.find_all("div", class_="data-temp")
    temperatures = []
    for div in temp_divs:
        span = div.find("span", class_="units-at")
        if span and span.get("data-value"):
            try:
                temperatures.append(float(span["data-value"]))
            except Exception:
                temperatures.append(None)
        else:
            temperatures.append(None)

    # Combine all values
    wind_data = []
    for i in range(min(len(speeds), len(directions), len(temperatures))):
        wind_data.append({
            "speed": speeds[i],
            "direction": directions[i],
            "temperature": temperatures[i]
        })
    return wind_data

if __name__ == "__main__":
    wind_data = get_wind_values(URL)
    print(wind_data)

