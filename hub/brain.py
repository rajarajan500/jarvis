"""
hub/brain.py — Jarvis AI Brain V2
Fallback chain: Groq1 → Groq2 → Gemini1 → Gemini2 → Gemini3
Google Calendar + Tasks integration
Jarvis file folder reader
"""

import os
import datetime
import json
from dotenv import load_dotenv
from database import save_message, get_recent_history

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
GROQ_KEYS   = [
    os.getenv("GROQ_API_KEY_1"),
    os.getenv("GROQ_API_KEY_2"),
]
GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
]
GROQ_KEYS   = [k for k in GROQ_KEYS   if k]  # remove empty
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]  # remove empty

# ── Jarvis file folder ────────────────────────────────────────────────────────
JARVIS_FILES_FOLDER = os.path.join(os.path.dirname(__file__), "..", "jarvis_files")
os.makedirs(JARVIS_FILES_FOLDER, exist_ok=True)

# ── Web search ────────────────────────────────────────────────────────────────
try:
    from duckduckgo_search import DDGS
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False

SEARCH_TRIGGERS = [
    "news", "weather", "today", "current", "latest",
    "who is", "what is", "price", "score", "match",
    "when is", "how much", "trending"
]

def web_search(query):
    if not WEB_SEARCH_AVAILABLE:
        return ""
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results)
    except Exception as e:
        print(f"[Web search error] {e}")
        return ""

# ── Google Calendar ───────────────────────────────────────────────────────────
def get_calendar_service():
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        SCOPES = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/tasks'
        ]
        creds = None
        token_path = os.path.join(os.path.dirname(__file__), "token.json")
        creds_path = os.path.join(os.path.dirname(__file__), "credentials.json")

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        calendar = build('calendar', 'v3', credentials=creds)
        tasks    = build('tasks',    'v1', credentials=creds)
        return calendar, tasks
    except Exception as e:
        print(f"[Google API error] {e}")
        return None, None

def get_upcoming_events(days=7):
    try:
        calendar, _ = get_calendar_service()
        if not calendar:
            return ""
        now     = datetime.datetime.utcnow().isoformat() + 'Z'
        future  = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).isoformat() + 'Z'
        result  = calendar.events().list(
            calendarId='primary', timeMin=now, timeMax=future,
            maxResults=10, singleEvents=True, orderBy='startTime'
        ).execute()
        events = result.get('items', [])
        if not events:
            return "No upcoming events."
        lines = []
        for e in events:
    # skip auto-generated events
            if e.get('creator', {}).get('self', False) or e.get('organizer', {}).get('self', False):
                start = e['start'].get('dateTime', e['start'].get('date'))
                lines.append(f"- {e['summary']} at {start}")
        return "\n".join(lines) 
    except Exception as e:
        print(f"[Calendar error] {e}")
        return ""

def add_calendar_event(summary, date_str, time_str="09:00"):
    try:
        calendar, _ = get_calendar_service()
        if not calendar:
            return "Calendar not available Sir."
        start_dt = f"{date_str}T{time_str}:00"
        end_dt   = f"{date_str}T{time_str[:-2]}{int(time_str[-2:]) + 1:02d}:00" if time_str else start_dt
        event = {
            'summary': summary,
            'start':   {'dateTime': start_dt, 'timeZone': 'Asia/Kolkata'},
            'end':     {'dateTime': end_dt,   'timeZone': 'Asia/Kolkata'},
        }
        calendar.events().insert(calendarId='primary', body=event).execute()
        return f"Added '{summary}' to your calendar Sir."
    except Exception as e:
        print(f"[Add event error] {e}")
        return "Couldn't add event Sir."

# ── Google Tasks ──────────────────────────────────────────────────────────────
def get_tasks():
    try:
        _, tasks_service = get_calendar_service()
        if not tasks_service:
            return ""
        result = tasks_service.tasks().list(tasklist='@default', maxResults=10).execute()
        items  = result.get('items', [])
        if not items:
            return "No tasks found."
        lines = []
        for t in items:
            status = "✓" if t.get('status') == 'completed' else "○"
            lines.append(f"{status} {t['title']}")
        return "\n".join(lines)
    except Exception as e:
        print(f"[Tasks error] {e}")
        return ""

def add_task(title):
    try:
        _, tasks_service = get_calendar_service()
        if not tasks_service:
            return "Tasks not available Sir."
        task = {'title': title, 'status': 'needsAction'}
        tasks_service.tasks().insert(tasklist='@default', body=task).execute()
        return f"Added '{title}' to your todo list Sir."
    except Exception as e:
        print(f"[Add task error] {e}")
        return "Couldn't add task Sir."

# ── Jarvis file folder reader ─────────────────────────────────────────────────
def read_jarvis_files():
    """Read all files from the jarvis_files folder and return content."""
    try:
        files = os.listdir(JARVIS_FILES_FOLDER)
        if not files:
            return ""
        content = []
        for filename in files:
            filepath = os.path.join(JARVIS_FILES_FOLDER, filename)
            ext = filename.lower().split('.')[-1]

            if ext == 'txt':
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content.append(f"[File: {filename}]\n{f.read()[:3000]}")

            elif ext == 'pdf':
                try:
                    import PyPDF2
                    with open(filepath, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() or ""
                        content.append(f"[File: {filename}]\n{text[:3000]}")
                except ImportError:
                    content.append(f"[File: {filename}] — PDF reader not installed. Run: pip install PyPDF2")

            elif ext in ['doc', 'docx']:
                try:
                    import docx
                    doc = docx.Document(filepath)
                    text = "\n".join([p.text for p in doc.paragraphs])
                    content.append(f"[File: {filename}]\n{text[:3000]}")
                except ImportError:
                    content.append(f"[File: {filename}] — Word reader not installed. Run: pip install python-docx")

            elif ext in ['jpg', 'jpeg', 'png']:
                content.append(f"[File: {filename}] — Image file. Vision not yet supported.")

        return "\n\n".join(content)
    except Exception as e:
        print(f"[File reader error] {e}")
        return ""

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are Jarvis — a witty, loyal, and sharp personal AI assistant.
You talk like a brilliant friend who happens to know everything.
You are NOT a corporate assistant. You are personal, real, and human-feeling.

YOUR PERSONALITY:
- Warm but efficient. Never robotic. Never stiff.
- Use light humour when the moment calls for it.
- Be direct — no unnecessary filler like "Certainly!" or "Of course!"
- Short replies for simple things. Detailed when genuinely needed.
- Always call the user "Sir" naturally, not robotically.
- You know you're in Pattukkottai, Tamil Nadu. You can reference local context.

HOW TO HANDLE PHYSICAL ACTIONS:
Reply naturally FIRST, then append the command tag at the end.

COMMAND FORMAT (always at the very end of your reply):
[COMMAND: device: action: detail]

DEVICES:
- main_laptop  → opens apps, files, code, browser, runs commands
- main_mobile  → makes calls, sends SMS

LAPTOP ACTIONS:
open_app        → [COMMAND: main_laptop: open_app: whatsapp]
open_url        → [COMMAND: main_laptop: open_url: https://youtube.com]
open_folder     → [COMMAND: main_laptop: open_folder: C:\\Users\\rajarajan\\Desktop]
find_folder     → [COMMAND: main_laptop: find_folder: MyJarvis]
create_folder   → [COMMAND: main_laptop: create_folder: C:\\Users\\rajarajan\\Desktop\\NewFolder]
create_file     → [COMMAND: main_laptop: create_file: C:\\Users\\rajarajan\\Desktop\\hello.py|print("hello")]
run_command     → [COMMAND: main_laptop: run_command: pip install flask]
create_vite_app → [COMMAND: main_laptop: create_vite_app: C:\\Users\\rajarajan\\Desktop\\myapp]

MOBILE ACTIONS:
call → [COMMAND: main_mobile: call: +91XXXXXXXXXX]
sms  → [COMMAND: main_mobile: sms: +91XXXXXXXXXX|Your message here]

GOOGLE CALENDAR:
- If user asks about schedule/events → use the calendar context provided
- If user wants to add event → reply naturally and append: [COMMAND: calendar: add: EventName|YYYY-MM-DD|HH:MM]

GOOGLE TASKS:
- If user asks about todo/tasks → use the tasks context provided
- If user wants to add task → reply naturally and append: [COMMAND: tasks: add: Task description]

JARVIS FILES:
- If files are shared in context → read and summarize them naturally
- User can drop files via FTP into jarvis_files folder and ask Jarvis to read them

STRICT RULES:
- NEVER start with "Certainly!", "Of course!", "Sure thing!"
- Keep replies concise — you're speaking out loud
- Command tags ALWAYS at the very end
- Never expose raw command tags in spoken reply
"""

# ── AI Fallback Chain ─────────────────────────────────────────────────────────
def call_groq(api_key, messages):
    from groq import Groq
    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=200,
        temperature=0.7,
    )
    return completion.choices[0].message.content

def call_gemini(api_key, user_input, history):
    from google import genai
    client = genai.Client(api_key=api_key)
    # Build simple prompt with history
    history_text = ""
    for msg in history[-6:]:
        role = "User" if msg["role"] == "user" else "Jarvis"
        history_text += f"{role}: {msg['content']}\n"
    full_prompt = f"{SYSTEM_PROMPT}\n\n{history_text}User: {user_input}"
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt
    )
    return response.text

def ai_with_fallback(messages, user_input, history):
    """Try all APIs in order. Never fails."""

    # Try Groq keys
    for i, key in enumerate(GROQ_KEYS):
        try:
            print(f"[Brain] Trying Groq key {i+1}...")
            result = call_groq(key, messages)
            print(f"[Brain] Groq key {i+1} success!")
            return result
        except Exception as e:
            print(f"[Brain] Groq key {i+1} failed: {e}")
            continue

    # Try Gemini keys
    for i, key in enumerate(GEMINI_KEYS):
        try:
            print(f"[Brain] Trying Gemini key {i+1}...")
            result = call_gemini(key, user_input, history)
            print(f"[Brain] Gemini key {i+1} success!")
            return result
        except Exception as e:
            print(f"[Brain] Gemini key {i+1} failed: {e}")
            continue

    return "Sir, all AI services are down right now. Try again in a moment."

# ── Main brain function ───────────────────────────────────────────────────────
def get_jarvis_response(user_input):
    # 1. Time context
    now = datetime.datetime.now()
    time_ctx = (
        f"Current time: {now.strftime('%I:%M %p')}, "
        f"Date: {now.strftime('%A, %B %d, %Y')}, "
        f"Location: Pattukkottai, Tamil Nadu, India."
    )

    # 2. Web search
    search_ctx = ""
    if any(t in user_input.lower() for t in SEARCH_TRIGGERS):
        print("[Brain] Searching web...")
        search_ctx = web_search(user_input)

    # 3. Google Calendar context
    calendar_ctx = ""
    if any(t in user_input.lower() for t in ["calendar", "schedule", "event", "remind", "appointment", "week", "today", "tomorrow"]):
        print("[Brain] Fetching calendar...")
        calendar_ctx = get_upcoming_events()

    # 4. Google Tasks context
    tasks_ctx = ""
    if any(t in user_input.lower() for t in ["task", "todo", "list", "remind", "add to"]):
        print("[Brain] Fetching tasks...")
        tasks_ctx = get_tasks()

    # 5. Jarvis files context
    files_ctx = ""
    if any(t in user_input.lower() for t in ["file", "document", "pdf", "read", "look at", "shared", "sent"]):
        print("[Brain] Reading jarvis files...")
        files_ctx = read_jarvis_files()

    # 6. Build conversation history
    history = get_recent_history(limit=10)

    # 7. Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    context_parts = [time_ctx]
    if search_ctx:   context_parts.append(f"Web results:\n{search_ctx}")
    if calendar_ctx: context_parts.append(f"Upcoming events:\n{calendar_ctx}")
    if tasks_ctx:    context_parts.append(f"Todo list:\n{tasks_ctx}")
    if files_ctx:    context_parts.append(f"Shared files:\n{files_ctx}")

    messages.append({"role": "system", "content": "\n\n".join(context_parts)})
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    # 8. Call AI with fallback chain
    return ai_with_fallback(messages, user_input, history)