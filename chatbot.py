import os
import uuid
import requests
import anthropic
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("Missing ANTHROPIC_API_KEY in .env")

client = anthropic.Anthropic(api_key=api_key)
MCP_SERVER = "http://127.0.0.1:9000"

# Unique session ID per chatbot run
SESSION_ID = str(uuid.uuid4())

with open("sample_doc.txt", "r", encoding="utf-8") as f:
    DOCUMENT = f.read()

def call_mcp_tool(endpoint: str, payload: dict):
    return requests.post(f"{MCP_SERVER}/{endpoint}", json=payload).json()

def init_session():
    return call_mcp_tool("init_session", {
        "document": DOCUMENT,
        "session_id": SESSION_ID
    })

def chat_with_bot(user_query: str):
    # Ask Claude which tool to use
    prompt = f"""
User question: "{user_query}"

Choose the best tool:
- "qa" to answer a question about the remembered document
- "simplify" to rewrite the remembered document in plain language
- "analyze_complications" to analyze the original document for risks, contradictions, ambiguities, and misleading clauses

Respond in strict JSON: {{"tool": "...", "reason": "..."}}
"""

    response = client.messages.create(
        model="claude-3-7-sonnet-latest",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
        tools=[{
            "name": "choose_tool",
            "description": "Select which MCP tool to call (qa, simplify, analyze_complications)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "tool": {"type": "string", "enum": ["qa", "simplify", "analyze_complications"]},
                    "reason": {"type": "string"}
                },
                "required": ["tool", "reason"]
            }
        }],
        tool_choice={"type": "auto"}
    )

    tool_use = None
    for msg in response.content:
        if msg.type == "tool_use":
            tool_use = msg.input
            break

    if not tool_use:
        return f"Could not determine tool. Raw response: {response}"

    tool = tool_use.get("tool")

    if tool == "qa":
        return call_mcp_tool("qa", {
            "question": user_query,
            "session_id": SESSION_ID
        })["answer"]

    elif tool == "simplify":
        return call_mcp_tool("simplify", {
            "session_id": SESSION_ID
        })["simplified_document"]

    elif tool == "analyze_complications":
        return call_mcp_tool("analyze_complications", {
            "session_id": SESSION_ID
        })["analysis"]

    else:
        return f"Unrecognized tool: {tool}"

if __name__ == "__main__":
    print(f"Legal Chatbot started (session {SESSION_ID}) — type 'quit' to exit")
    print(init_session()["message"])  # send doc once at startup
    while True:
        query = input("You: ")
        if query.lower() in ["quit", "exit"]:
            break
        print("Bot:", chat_with_bot(query))