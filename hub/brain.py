import os
import datetime
from groq import Groq
from dotenv import load_dotenv
from duckduckgo_search import DDGS # Make sure to pip install duckduckgo-search



load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are Jarvis, a supportive, grounded, and witty AI companion. 
Your tone is like a helpful peer—empathetic but direct. 
You can talk about anything: school, movies, life, or tech. 

RULES:
1. Be concise but friendly. Use humor if the user jokes.
2. If the user asks for a physical task (open app, call, sms), 
   append the command at the end of your friendly reply.
3. FORMAT: [Friendly Reply] [COMMAND: DEVICE: ACTION: DETAIL]

Example:
User: "Jarvis, I'm tired of studying. Open YouTube."
Jarvis: "I feel you, studying for Grade 12 can be a grind. Take a 15-minute break, you've earned it! Opening YouTube for you. [COMMAND: main_laptop: open: youtube]"
"""

def search_web(query):
    try:
        with DDGS() as ddgs:
            # Get the top 3 results to keep it fast and light
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results)
    except Exception:
        return "I couldn't reach the internet right now, Sir."

def get_jarvis_response(user_input):
    try:
        # 1. Get Real-Time Context (Time & Location)
        now = datetime.datetime.now()
        # Explicitly telling him he is in Pattukkottai makes him feel local
        time_context = f"Current Time: {now.strftime('%I:%M %p')}, Date: {now.strftime('%A, %B %d, %Y')}, Location: Pattukkottai, Tamil Nadu."
        
        # 2. Internet Search Logic
        keywords = ["news", "weather", "today", "current", "who is", "what is"]
        search_data = ""
        if any(word in user_input.lower() for word in keywords):
            print("Checking the web...")
            with DDGS() as ddgs:
                results = [r['body'] for r in ddgs.text(user_input, max_results=3)]
                search_data = "\n".join(results)
        
        # 3. Combine everything into the final prompt
        full_context = f"{time_context}\n\n"
        if search_data:
            full_context += f"Web Search Results:\n{search_data}\n\n"
            
        final_input = f"{full_context}User Message: {user_input}"

        # 4. The Groq Call
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": final_input}
            ],
            model="llama-3.3-70b-versatile",
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Sir, I encountered an error: {e}"