import json
import os

import requests


def send_flash_message(device_url, message):
    requests.put(
        os.path.join(
            device_url,
            'flash/'
        ),
        data=json.dumps(message)
    )
