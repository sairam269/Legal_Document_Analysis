import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(filename="mcp_server.log", level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

# FastAPI app
app = FastAPI(title="Legal MCP Server")

# Load Anthropic API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    logging.error("Missing ANTHROPIC_API_KEY in .env")
    raise ValueError("Missing ANTHROPIC_API_KEY in .env")

client = anthropic.Anthropic(api_key=api_key)

# In-memory session storage
SESSIONS = {}

# ------------------ Pydantic models ------------------

class InitSessionRequest(BaseModel):
    document: str
    session_id: str

class QARequest(BaseModel):
    question: str
    session_id: str

class SimplifyRequest(BaseModel):
    session_id: str

class AnalyzeRequest(BaseModel):
    session_id: str

class ValidateRequest(BaseModel):
    session_id: str

class ExtractDatesRequest(BaseModel):
    session_id: str

# ------------------ Helper function ------------------

def ask_claude(session_id: str, prompt: str, max_tokens: int = 1024):
    """
    Sends a prompt to Claude with the current conversation messages
    and appends the response to the session history.
    """
    try:
        if session_id not in SESSIONS:
            raise ValueError(f"Session {session_id} not initialized with a document")

        messages = SESSIONS[session_id]["messages"]
        messages.append({"role": "user", "content": prompt})

        response = client.messages.create(
            model="claude-3-7-sonnet-latest",
            messages=messages,
            max_tokens=max_tokens,
            temperature=0
        )

        text = response.content[0].text.strip()
        messages.append({"role": "assistant", "content": text})
        return text

    except Exception as e:
        logging.exception(f"Error in ask_claude for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ------------------ API endpoints ------------------

@app.post("/init_session")
def init_session(req: InitSessionRequest):
    """
    Initialize a session with a legal document.
    Stores the document and conversation history in memory.
    """
    try:
        SESSIONS[req.session_id] = {
            "document": req.document,
            "messages": [
                {"role": "user", "content": f"You are a legal assistant. Remember this document for future queries:\n{req.document}"}
            ]
        }
        logging.info(f"Session {req.session_id} initialized.")
        return {"message": f"Session {req.session_id} initialized with document."}
    except Exception as e:
        logging.exception(f"Error initializing session {req.session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/qa")
def answer_question(req: QARequest):
    """
    Answer a question about the remembered document.
    """
    try:
        prompt = f"Answer the user's question based on the remembered document.\n\nQuestion: {req.question}"
        answer = ask_claude(req.session_id, prompt)
        return {"answer": answer}
    except Exception as e:
        logging.exception(f"Error answering question for session {req.session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simplify")
def simplify_document(req: SimplifyRequest):
    """
    Rewrite the remembered legal document in clear, plain language.
    """
    try:
        prompt = "Rewrite the remembered legal document in clear, plain language. Keep meaning but remove jargon."
        simplified = ask_claude(req.session_id, prompt)
        return {"simplified_document": simplified}
    except Exception as e:
        logging.exception(f"Error simplifying document for session {req.session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_complications")
def analyze_complications(req: AnalyzeRequest):
    """
    Analyze document for multi-party complications, contradictions, ambiguities,
    misleading clauses, and legal risks. Returns strict JSON.
    """
    try:
        if req.session_id not in SESSIONS:
            raise ValueError(f"Session {req.session_id} not initialized with a document")

        document = SESSIONS[req.session_id]["document"]

        prompt = f"""
You are a legal contract analyzer.
ONLY analyze the following original document. 
Do NOT hallucinate or provide generic advice.
Identify only clauses that could realistically cause legal disputes, lawsuits, or material risks.

Document:
{document}

Task:
Return JSON with this schema:

{{
  "issues": [
    {{
      "line_number": int,
      "clause": str,
      "type": str,
      "risk_percent": int,
      "affected_parties": [str],
      "reason": str,
      "suggestion": str
    }}
  ],
  "overall_rating": int
}}

Rules:
- Consider all parties.
- Only report legally problematic clauses.
- Quote clauses verbatim.
- Respond ONLY in valid JSON.
"""
        response = client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=2000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        return {"analysis": response.content[0].text.strip()}
    except Exception as e:
        logging.exception(f"Error analyzing complications for session {req.session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate_document")
def validate_document(req: ValidateRequest):
    """
    Validate whether the remembered document is a legal or contract document.
    Returns JSON with 'is_legal_document' and reason.
    """
    try:
        if req.session_id not in SESSIONS:
            raise ValueError(f"Session {req.session_id} not initialized with a document")

        document = SESSIONS[req.session_id]["document"]

        prompt = f"""
You are a legal document classifier.
ONLY analyze the text below. Do NOT hallucinate.

Document:
{document}

Task:
Return JSON ONLY with these fields:
{{
  "is_legal_document": bool,
  "reason": str
}}
"""
        response_text = ask_claude(req.session_id, prompt)
        return {"validation": response_text}
    except Exception as e:
        logging.exception(f"Error validating document for session {req.session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract_key_dates")
def extract_key_dates(req: ExtractDatesRequest):
    """
    Extract all important contractual dates, milestones, and recurring obligations.
    Returns strict JSON.
    """
    try:
        if req.session_id not in SESSIONS:
            raise ValueError(f"Session {req.session_id} not initialized with a document")

        document = SESSIONS[req.session_id]["document"]

        prompt = f"""
You are a legal contract date extractor.
Analyze the following document and identify all important contractual dates:
- Contract start date
- Contract expiration
- Renewal dates
- Completion milestones
- Warning or notice periods
- Recurring obligations

Return JSON ONLY with this schema:
{{
  "key_dates": [
    {{
      "event_name": str,
      "recurrence": str|null,
      "date_or_day": str
    }}
  ]
}}

Rules:
- Include ALL important dates mentioned.
- Do not hallucinate.
- Respond ONLY in valid JSON.
"""
        response_text = ask_claude(req.session_id, prompt, max_tokens=2000)
        return {"key_dates": response_text}
    except Exception as e:
        logging.exception(f"Error extracting key dates for session {req.session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset_session/{session_id}")
def reset_session(session_id: str):
    """
    Clear the memory of a session.
    """
    try:
        if session_id in SESSIONS:
            del SESSIONS[session_id]
            logging.info(f"Session {session_id} cleared.")
            return {"message": f"Session {session_id} cleared."}
        return {"message": f"Session {session_id} not found."}
    except Exception as e:
        logging.exception(f"Error resetting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))