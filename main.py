import json
import logging
import smtplib
from email.mime.text import MIMEText
import os
import yaml
from scrape_speeds import get_speed_values

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global SMTP settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "je.vanderelst@gmail.com"
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'your_password')  # Use env var for security

def load_config():
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def send_notification(emails, spot, config):
    subject = f"Wind Alert for {spot}"
    body = f"Good winds detected at {spot}! Check the forecast."
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = ', '.join(emails)

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    server.sendmail(SMTP_USERNAME, emails, msg.as_string())
    server.quit()

def has_consecutive_high(speeds, threshold, min_consecutive):
    count = 0
    for speed in speeds:
        if int(speed) > threshold:
            count += 1
            if count >= min_consecutive:
                return True
        else:
            count = 0
    return False

def check_conditions(speeds, threshold, min_hours, start_hour, end_hour):
    # Assuming speeds is list of 72 values: 3 days * 24 hours
    days = 3
    hours_per_day = 24
    for day in range(days):
        start_idx = day * hours_per_day + start_hour
        end_idx = day * hours_per_day + end_hour
        day_speeds = speeds[start_idx:end_idx]
        if has_consecutive_high(day_speeds, threshold, min_hours):
            return True
    return False

def main():
    config = load_config()
    for spot, details in config['spots'].items():
        logging.info(f"Scraping speeds for {spot}")
        speeds = get_speed_values(details['url'])
        if len(speeds) != 72:
            logging.warning(f"Unexpected number of speeds for {spot}: {len(speeds)}")
            continue
        logging.info(f"Checking conditions for {spot}: threshold={details['threshold']}, min_hours={details['min_hours']}")
        if check_conditions(speeds, details['threshold'], details['min_hours'], details['start_hour'], details['end_hour']):
            logging.info(f"Sending notification for {spot} to {details['emails']}")
            send_notification(details['emails'], spot, config)
        else:
            logging.info(f"No notification needed for {spot}")

if __name__ == "__main__":
    main()
