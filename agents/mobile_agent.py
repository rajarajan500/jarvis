import requests
import time
import os
from shared import HUB_URL, MAIN_MOBILE

def handle_mobile_action(data):
    action = data.get("action")
    detail = data.get("detail")
    
    if action == "call":
        print(f"Calling: {detail}")
        # Termux command to trigger a call
        os.system(f"termux-telephony-call {detail}")
        
    elif action == "sms":
        # Format detail could be "number|message"
        number, msg = detail.split("|")
        os.system(f'termux-sms-send -n {number} "{msg}"')

while True:
    try:
        r = requests.get(f"{HUB_URL}/fetch/{MAIN_MOBILE}")
        cmd = r.json()
        if cmd.get("action"):
            handle_mobile_action(cmd)
    except:
        pass
    time.sleep(2)