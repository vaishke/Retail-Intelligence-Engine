# test_sales_graph.py

from dotenv import load_dotenv
import os
from bson import ObjectId

load_dotenv()

from sales_graph.graph import run_sales_graph

print("DB_NAME:", os.getenv("DB_NAME"))

if os.getenv("GROQ_API_KEY"):
    print("✅ Groq API key found - using LLM intent detection")
else:
    print("⚠️  No Groq API key - using rule-based intent detection")

print("\n🔥 Sales Graph CLI started (Press Ctrl+C to exit)\n")

# Keep session constant for conversation continuity
session_id = str(ObjectId())
user_id = "69c9f759145e288b29244cd9"
channel = "web"

try:
    while True:
        user_input = input("🧑 You: ").strip()

        if not user_input:
            continue  # ignore empty inputs

        result = run_sales_graph(
            user_id=user_id,
            session_id=session_id,
            channel=channel,
            message=user_input
        )

        print("\n🤖 Bot:")
        print("Intent detected:", result.get("current_intent"))
        print("Response:", result.get("response"))
        print("Agents called:", result.get("agent_call_history"))
        print("\n" + "="*50 + "\n")

except KeyboardInterrupt:
    print("\n👋 Exiting Sales Graph CLI. Bye!")