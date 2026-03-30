# test_sales_graph.py

from dotenv import load_dotenv
import os
load_dotenv()
print("DB_NAME:", os.getenv("DB_NAME"))

from sales_graph.graph import run_sales_graph
from bson import ObjectId

# Test 1: Discovery flow
print("Testing discovery flow...")
result = run_sales_graph(
    user_id="69c9f759145e288b29244cd9",
    session_id=str(ObjectId()),
    channel="web",
    message="I want to discover some footwear products"
)

print("Intent detected:", result.get("current_intent"))
print("Response:", result.get("response"))
print("Agents called:", result.get("agent_call_history"))
print("\n" + "="*50 + "\n")

# Test 2: Intent detection with Groq (if API key is set)
import os
if os.getenv("GROQ_API_KEY"):
    print("✅ Groq API key found - using LLM intent detection")
else:
    print("⚠️  No Groq API key - using rule-based intent detection")
