# Windfinder-Notify

Scrape wind speed forecasts from Windfinder and send email notifications for kitesurfing spots when for example wind speeds superior to 20 knots are detected for 3 consecutive hours

Runs daily at 8 AM UTC

![alt text](windfinder.png)

## Configuration
Edit `config.yaml`:
```yaml
spots:
  brouwersdam:
    url: https://nl.windfinder.com/weatherforecast/brouwersdam
    emails: [user@example.com] # emails to be notified
    threshold: 20 # windspeed threshold
    min_hours: 3 # number of consecutive hours
    start_hour: 8 # start of daily timespan of interest
    end_hour: 20 # end of daily timespan of interest
```

