import requests
from bs4 import BeautifulSoup

URL = "https://nl.windfinder.com/weatherforecast/brouwersdam"

def get_speed_values(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    speed_divs = soup.find_all("div", class_="speed")
    speeds = []
    for div in speed_divs:
        span = div.find("span", class_="units-ws")
        if span:
            speeds.append(span.contents[0])


if __name__ == "__main__":
    speeds = get_speed_values(URL)

    