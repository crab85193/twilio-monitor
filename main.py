
import os
import logging
import sentry_sdk
from src.twilio_monitor import TwilioMonitor
    
def main():    
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_URL'),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
    )
    
    twilio_monitor = TwilioMonitor()

    for row in twilio_monitor.get_non_end_id_and_sid():
        try:
            id = row["id"]
            sid = row["sid"]

            if sid:
                twilio_status = twilio_monitor.get_twilio_status(sid)
                result = twilio_monitor.set_status(id, twilio_status)

                if result[2] == twilio_monitor.FAILURE or result[2] == twilio_monitor.ERROR:
                    twilio_monitor.change_parent_status(id)

            else:
                twilio_monitor.change_parent_status(id, error=True)
                
        except Exception as e:
            logging.error(e)
            continue

if __name__ == "__main__":
    main()