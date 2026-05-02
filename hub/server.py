from fastapi import FastAPI
from brain import get_jarvis_response
from database import init_db, save_message, get_recent_history
import uvicorn

init_db()

app = FastAPI()
queues = {"main_laptop": [], "main_mobile": []}

@app.get("/ask")
def ask(text: str):
    # Get Jarvis's friendly response
    full_response = get_jarvis_response(text)
    
    # Logic to route the command
    if "[COMMAND:" in full_response:
        cmd_part = full_response.split("[COMMAND:")[1].split("]")[0].strip()
        parts = cmd_part.split(": ")
        
        if len(parts) == 3:
            device, action, detail = parts[0], parts[1], parts[2]
            # Route to the correct queue (main_laptop or mobile)
            if device in queues:
                queues[device].append({"action": action, "detail": detail})
                print(f"Sent {action} to {device}")

    # Return only the text for the Tablet to speak
    clean_reply = full_response.split("[COMMAND:")[0].strip()
    return {"reply": clean_reply}

@app.get("/fetch/{device_id}")
def fetch(device_id: str):
    if device_id in queues and queues[device_id]:
        return queues[device_id].pop(0)
    return {"action": None}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)