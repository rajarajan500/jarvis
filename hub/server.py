"""
hub/server.py — Jarvis Central Hub V2
Handles: laptop, mobile, calendar, tasks commands
"""

from fastapi import FastAPI
from brain import get_jarvis_response, add_calendar_event, add_task
from database import init_db, save_message, get_recent_history
import uvicorn
import re

init_db()
app = FastAPI()

queues = {
    "main_laptop": [],
    "main_mobile": [],
    "tablet":      [],
}

@app.get("/ping")
def ping():
    return {"status": "alive", "message": "Jarvis hub is running Sir."}

@app.get("/ask")
def ask(text: str):
    save_message("user", text)
    full_response = get_jarvis_response(text)
    save_message("assistant", full_response)

    # Parse all commands
    command_pattern = r'\[COMMAND:\s*([^:]+):\s*([^:]+):\s*([^\]]+)\]'
    matches = re.findall(command_pattern, full_response)

    for device, action, detail in matches:
        device = device.strip().lower()
        action = action.strip().lower()
        detail = detail.strip()

        # ── Google Calendar ──────────────────────────
        if device == "calendar" and action == "add":
            parts = detail.split("|")
            if len(parts) >= 2:
                summary  = parts[0].strip()
                date_str = parts[1].strip()
                time_str = parts[2].strip() if len(parts) > 2 else "09:00"
                result   = add_calendar_event(summary, date_str, time_str)
                print(f"[Calendar] {result}")
            continue

        # ── Google Tasks ─────────────────────────────
        if device == "tasks" and action == "add":
            result = add_task(detail)
            print(f"[Tasks] {result}")
            continue

        # ── Device queues ────────────────────────────
        if device in queues:
            queues[device].append({"action": action, "detail": detail})
            print(f"[Router] → {device} | {action} | {detail}")
        else:
            print(f"[Router] Unknown device: {device}")

    clean_reply = re.sub(r'\[COMMAND:[^\]]+\]', '', full_response).strip()
    return {"reply": clean_reply}

@app.get("/fetch/{device_id}")
def fetch(device_id: str):
    if device_id in queues and queues[device_id]:
        cmd = queues[device_id].pop(0)
        print(f"[Fetch] {device_id} picked up: {cmd}")
        return cmd
    return {"action": None}

@app.get("/history")
def history(limit: int = 10):
    return {"history": get_recent_history(limit)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=False, timeout_keep_alive=60)