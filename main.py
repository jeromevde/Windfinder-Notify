import json
import logging
import smtplib
from email.mime.text import MIMEText
import os
import yaml
from scrape_speeds import get_wind_values

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global SMTP settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "je.vanderelst@gmail.com"
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'your_password')  # Use env var for security

def load_config():
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def send_notification(email, spots_and_details):
    spots_str = ', '.join([spot for spot, _, _, _ in spots_and_details])
    subject = f"Good conditions detected for {spots_str}"
    # Build HTML body with clickable links
    body = '<html><body>'
    for spot, url, windspeed_between, hours_between in spots_and_details:
        body += f'<p>{spot}: windspeed between {windspeed_between[0]} and {windspeed_between[1]} knots detected between {hours_between[0]}h and {hours_between[1]}h: <a href="{url}">{spot}</a></p>'
    body += '</body></html>'
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = email
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.sendmail(SMTP_USERNAME, [email], msg.as_string())
    server.quit()

def has_consecutive_high(wind_data, min_consecutive, temp_above=None, windspeed_between=None, hours=None):
    count = 0
    for idx, entry in enumerate(wind_data):
        speed = entry["speed"]
        temp = entry["temperature"]
        direction = entry["direction"]
        # Filter by temperature
        if temp_above is not None and (temp is None or temp < temp_above):
            count = 0
            continue
        # Filter by windspeed range
        if windspeed_between is not None:
            a, b = windspeed_between
            if speed is None or speed < a or speed > b:
                count = 0
                continue
        count += 1
        if count >= min_consecutive:
            return True
    return False

def check_conditions(wind_data, min_hours, hours_between, temp_above, windspeed_between):
    # wind_data: list of dicts for 72 hours
    days = 3
    hours_per_day = 24
    start_hour, end_hour = hours_between
    for day in range(days):
        start_idx = day * hours_per_day + start_hour
        end_idx = day * hours_per_day + end_hour
        day_data = wind_data[start_idx:end_idx]
        if has_consecutive_high(day_data, min_hours, temp_above, windspeed_between, (start_hour, end_hour)):
            return True
    return False

def main():
    config = load_config()
    notifications = {}
    for spot, details in config['spots'].items():
        wind_data = get_wind_values(details['url'])
        if len(wind_data) != 72:
            logging.warning(f"Unexpected number of wind data points for {spot}: {len(wind_data)}")
            continue
        logging.info(f"Checking conditions for {spot}: min_hours={details['min_hours']}, temp_above={details.get('temperature_above')}, windspeed_between={details.get('windspeed_between')}, hours_between={details.get('hours_between')}")
        if check_conditions(
            wind_data,
            details['min_hours'],
            details.get('hours_between', [details.get('start_hour', 8), details.get('end_hour', 20)]),
            details.get('temperature_above'),
            details.get('windspeed_between')
        ):
            logging.info(f"Sending notification for {spot} to {details['emails']}")
            for email in details['emails']:
                if email not in notifications:
                    notifications[email] = []
                notifications[email].append((spot, details['url'], details.get('windspeed_between'), details.get('hours_between', [details.get('start_hour', 8), details.get('end_hour', 20)])))
        else:
            logging.info(f"No notification needed for {spot}")
    for email, spots_and_details in notifications.items():
        logging.info(f"Sending aggregated notification to {email} for {len(spots_and_details)} spots")
        send_notification(email, spots_and_details)

main()