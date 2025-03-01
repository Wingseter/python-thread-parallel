import logging
import time
import requests
import json

# Loki 핸들러 
class LokiHandler(logging.Handler):
    def __init__(self, url, labels=None):
        super().__init__()
        self.url = url
        self.labels = labels if labels else {}

    def emit(self, record):
        log_entry = self.format(record)
        timestamp_ns = str(int(time.time() * 1e9))

        payload = {
            "streams": [
                {
                    "stream": self.labels,
                    "values": [
                        [timestamp_ns, log_entry]
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.url, data=json.dumps(payload), headers=headers)
            if response.status_code != 204:
                print(f"Failed to send log to Loki: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Failed to send log to Loki: {e}")