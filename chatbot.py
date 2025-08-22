import os
import uuid
import logging
import requests
import anthropic
from dotenv import load_dotenv

# ------------------ Setup ------------------
load_dotenv()

# Logging
logging.basicConfig(filename="mcp_client.log", level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

# Load config
api_key = os.getenv("ANTHROPIC_API_KEY")
doc_name = os.getenv("LEGAL_DOCUMENT_NAME")
if not api_key:
    logging.error("Missing ANTHROPIC_API_KEY in .env")
    raise ValueError("Missing ANTHROPIC_API_KEY in .env")
if not doc_name:
    logging.error("Missing LEGAL_DOCUMENT_NAME in .env")
    raise ValueError("Missing LEGAL_DOCUMENT_NAME in .env")

client = anthropic.Anthropic(api_key=api_key)
MCP_SERVER = "http://127.0.0.1:9000"

# Unique session ID
SESSION_ID = str(uuid.uuid4())

# Load document
with open(doc_name + ".txt", "r", encoding="utf-8") as f:
    DOCUMENT = f.read()

# ------------------ Helper functions ------------------

def call_mcp_tool(endpoint: str, payload: dict):
    """
    Sends a request to the MCP server endpoint with JSON payload.
    """
    try:
        response = requests.post(f"{MCP_SERVER}/{endpoint}", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.exception(f"Error calling MCP tool {endpoint}: {e}")
        raise RuntimeError(f"Error calling MCP tool {endpoint}: {e}")

def init_session():
    """
    Initialize MCP session by sending the document.
    """
    try:
        return call_mcp_tool("init_session", {"document": DOCUMENT, "session_id": SESSION_ID})
    except Exception as e:
        logging.exception(f"Error initializing session: {e}")
        raise

# ------------------ Tool selection ------------------

def classify_intent(question: str) -> str:
    """
    Simple fallback intent classifier based on keywords.
    """
    q = question.lower()
    if any(word in q for word in ["risk", "problem", "contradiction", "issue", "ambiguity"]):
        return "analyze_complications"
    elif any(word in q for word in ["plain english", "simplify", "explain"]):
        return "simplify"
    elif any(word in q for word in ["is this a contract", "legal document"]):
        return "validate_document"
    elif any(word in q for word in ["date", "deadline", "milestone", "expire", "renewal"]):
        return "extract_key_dates"
    else:
        return "qa"

def chat_with_bot(user_query: str):
    """
    Main function to interact with the MCP bot.
    Uses Claude to choose the best tool, with a fallback classifier.
    """
    try:
        # Detailed prompt for Claude with examples
        prompt = f"""
User question: "{user_query}"

You are a smart MCP assistant. Only choose **one tool** for this question.
Available tools with usage examples:

1. "qa": Answer specific questions about the document.
   Example: "Who is responsible for renewal notice?"
2. "simplify": Rewrite the document in plain language.
   Example: "Explain this contract in plain English"
3. "analyze_complications": Identify legal risks, ambiguities, contradictions.
   Example: "Find risky clauses in the contract"
4. "validate_document": Check if the document is a legal contract.
   Example: "Is this document a legal contract?"
5. "extract_key_dates": Extract all important dates and milestones.
   Example: "List all important contract dates"

Respond STRICTLY in JSON: {{"tool": "...", "reason": "..."}}
"""

        # Ask Claude
        response = client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
            tools=[{
                "name": "choose_tool",
                "description": "Select which MCP tool to call",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tool": {"type": "string", "enum": ["qa", "simplify", "analyze_complications", "validate_document", "extract_key_dates"]},
                        "reason": {"type": "string"}
                    },
                    "required": ["tool", "reason"]
                }
            }],
            tool_choice={"type": "auto"}
        )

        # Extract tool choice
        tool_use = None
        for msg in response.content:
            if msg.type == "tool_use":
                tool_use = msg.input
                break

        # Fallback to simple classifier
        if not tool_use or tool_use.get("tool") not in ["qa", "simplify", "analyze_complications", "validate_document", "extract_key_dates"]:
            fallback_tool = classify_intent(user_query)
            logging.warning(f"Falling back to intent classifier: {fallback_tool}")
            tool_use = {"tool": fallback_tool, "reason": "Fallback classifier used"}

        tool = tool_use.get("tool")

        # Call appropriate MCP endpoint
        if tool == "qa":
            return call_mcp_tool("qa", {"question": user_query, "session_id": SESSION_ID})["answer"]
        elif tool == "simplify":
            return call_mcp_tool("simplify", {"session_id": SESSION_ID})["simplified_document"]
        elif tool == "analyze_complications":
            return call_mcp_tool("analyze_complications", {"session_id": SESSION_ID})["analysis"]
        elif tool == "validate_document":
            return call_mcp_tool("validate_document", {"session_id": SESSION_ID})["validation"]
        elif tool == "extract_key_dates":
            return call_mcp_tool("extract_key_dates", {"session_id": SESSION_ID})["key_dates"]
        else:
            logging.error(f"Unrecognized tool: {tool}")
            return f"Unrecognized tool: {tool}"

    except Exception as e:
        logging.exception(f"Error in chat_with_bot: {e}")
        return f"Error in chat_with_bot: {e}"

# ------------------ Main loop ------------------

if __name__ == "__main__":
    print(f"Legal Chatbot started (session {SESSION_ID}) — type 'quit' to exit")
    print(init_session()["message"])
    while True:
        query = input("You: ")
        if query.lower() in ["quit", "exit"]:
            break
        response = chat_with_bot(query)
        print("Bot:", response)