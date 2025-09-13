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

def send_notification(email, spots_and_details):
    spots_str = ', '.join([spot for spot, _, _, _, _ in spots_and_details])
    subject = f"Good conditions detected for {spots_str}"
    
    # Build HTML body with clickable links
    body = '<html><body>'
    for spot, url, threshold, start_hour, end_hour in spots_and_details:
        body += f'<p>{spot}: winds above {threshold} knots detected between {start_hour} and {end_hour} hours</p>'
        body += f'<p><a href="{url}">{spot}</a></p>'
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

def has_consecutive_high(speeds, threshold, min_consecutive):
    count = 0
    for speed in speeds:
        if int(speed) >= threshold:
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
    notifications = {}
    for spot, details in config['spots'].items():
        speeds = get_speed_values(details['url'])
        if len(speeds) != 72:
            logging.warning(f"Unexpected number of speeds for {spot}: {len(speeds)}")
            continue
        logging.info(f"Checking conditions for {spot}: threshold={details['threshold']}, min_hours={details['min_hours']}")
        if check_conditions(speeds, details['threshold'], details['min_hours'], details['start_hour'], details['end_hour']):
            logging.info(f"Sending notification for {spot} to {details['emails']}")
            for email in details['emails']:
                if email not in notifications:
                    notifications[email] = []
                notifications[email].append((spot, details['url'], details['threshold'], details['start_hour'], details['end_hour']))
        else:
            logging.info(f"No notification needed for {spot}")
    
    for email, spots_and_details in notifications.items():
        logging.info(f"Sending aggregated notification to {email} for {len(spots_and_details)} spots")
        send_notification(email, spots_and_details)

main()