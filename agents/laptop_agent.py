import requests
import time
import pyautogui
import subprocess
from config import HUB_URL, MAIN_LAPTOP
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

def execute(cmd):
    action, detail = cmd["action"], cmd["detail"]

    # --- App & File Control ---
    if action == "open":
        pyautogui.press('win')
        pyautogui.write(detail)
        pyautogui.press('enter')

    # --- Media Control (Music/Video/YouTube) ---
    elif action == "media":
        if detail == "pause" or detail == "play":
            pyautogui.press('playpause')
        elif detail == "next":
            pyautogui.press('nexttrack')
        elif detail == "prev":
            pyautogui.press('prevtrack')

    # --- Volume Control ---
    elif action == "volume":
        # detail would be a number like "50" or "up"/"down"
        if detail == "up": pyautogui.press("volumeup", presses=5)
        elif detail == "down": pyautogui.press("volumedown", presses=5)
        elif detail.isdigit():
            # Set specific volume 0-100 logic here
            pass

    # --- Brightness Control ---
    elif action == "brightness":
        current = sbc.get_brightness()[0]
        if detail == "up": sbc.set_brightness(min(current + 20, 100))
        elif detail == "down": sbc.set_brightness(max(current - 20, 0))

# Simple retry logic for your agent
while True:
    try:
        r = requests.get(f"{HUB_URL}/fetch/{MAIN_LAPTOP}")
        # ... your logic ...
    except Exception as e:
        print("Hub not found, retrying in 10 seconds...")
        time.sleep(10)