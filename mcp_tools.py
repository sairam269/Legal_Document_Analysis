from fastapi import FastAPI
from pydantic import BaseModel
import os
import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel

app = FastAPI()
load_dotenv()

class ValidateRequest(BaseModel):
    session_id: str

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("Missing ANTHROPIC_API_KEY in .env")

client = anthropic.Anthropic(api_key=api_key)

# Store sessions in memory {session_id: {"document": str, "messages": list}}
SESSIONS = {}

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

def ask_claude(session_id: str, prompt: str, max_tokens: int = 1024):
    if session_id not in SESSIONS:
        raise ValueError(f"Session {session_id} not initialized with a document")

    # Conversation history
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

@app.post("/init_session")
def init_session(req: InitSessionRequest):
    """Initialize session with document (send doc once)."""
    SESSIONS[req.session_id] = {
        "document": req.document,
        "messages": [
            {"role": "user", "content": f"You are a legal assistant. Remember this document for future queries:\n{req.document}"}
        ]
    }
    return {"message": f"Session {req.session_id} initialized with document."}

@app.post("/qa")
def answer_question(req: QARequest):
    prompt = f"Answer the user's question based on the remembered document.\n\nQuestion: {req.question}"
    answer = ask_claude(req.session_id, prompt)
    return {"answer": answer}

@app.post("/simplify")
def simplify_document(req: SimplifyRequest):
    prompt = "Rewrite the remembered legal document in clear, plain language. Keep meaning but remove jargon."
    simplified = ask_claude(req.session_id, prompt)
    return {"simplified_document": simplified}

@app.post("/analyze_complications")
def analyze_complications(req: AnalyzeRequest):
    """
    Analyze a legal/contract document for multi-party complications, contradictions, ambiguities,
    misleading clauses, and legal risks.
    Return strict JSON with actionable negotiation suggestions for all involved parties.
    """
    if req.session_id not in SESSIONS:
        raise ValueError(f"Session {req.session_id} not initialized with a document")

    document = SESSIONS[req.session_id]["document"]

    prompt = f"""
You are a legal contract analyzer.
ONLY analyze the following original document. 
Do NOT hallucinate or provide generic advice.
Identify only clauses that could realistically cause legal disputes, lawsuits, or material risks to any party involved.

Document:
{document}

Task:
Return JSON with this schema:

{{
  "issues": [
    {{
      "line_number": int,              # approximate line or section
      "clause": str,                   # verbatim text of problematic clause
      "type": str,                     # one of ["contradiction","complication","ambiguity","misleading","risk"]
      "risk_percent": int,             # 0-100 probability this causes legal dispute or exposure
      "affected_parties": [str],       # parties potentially affected, e.g., ["signer","counterparty","both"]
      "reason": str,                   # concise explanation of the legal problem
      "suggestion": str                # practical counter-offer or mitigation strategy
    }}
  ],
  "overall_rating": int               # 0-100 overall contract clarity and safety
}}

Rules:
- Consider implications for all parties, not just one side.
- Only report clauses that are legally problematic.
- Quote clauses verbatim; do not paraphrase.
- Provide factual reasoning for risk_percent.
- Respond ONLY in valid JSON. No extra text.
"""

    response = client.messages.create(
        model="claude-3-7-sonnet-latest",
        max_tokens=2000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    return {"analysis": response.content[0].text.strip()}

@app.post("/validate_document")
def validate_document(req: ValidateRequest):
    """
    Validate whether the remembered document is a legal or contract document.
    Returns JSON:
    {
        "is_legal_document": bool,
        "reason": str  # if not legal, why
    }
    """
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
  "is_legal_document": bool,  # True if this is a legal/contract document, False otherwise
  "reason": str               # if False, explain why it is not a legal/contract document
}}
"""

    response_text = ask_claude(req.session_id, prompt)
    return {"validation": response_text}

class ExtractDatesRequest(BaseModel):
    session_id: str

@app.post("/extract_key_dates")
def extract_key_dates(req: ExtractDatesRequest):
    """
    Extract all important contractual dates (start, expiration, renewal, completion, recurring events).
    Return JSON with event name, recurrence, and date/day.
    """
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
- Recurring obligations (monthly, yearly, weekly)

Return JSON ONLY with this schema:
{{
  "key_dates": [
    {{
      "event_name": str,         # e.g., "Contract Start", "Renewal", "Payment Due"
      "recurrence": str|null,    # "monthly", "yearly", "weekly", or null if one-time
      "date_or_day": str         # exact date "YYYY-MM-DD" for one-time, or day name if weekly
    }}
  ]
}}

Rules:
- Include ALL important dates mentioned in the document.
- Do not hallucinate dates.
- Respond ONLY in valid JSON.
"""

    response_text = ask_claude(req.session_id, prompt, max_tokens=2000)
    return {"key_dates": response_text}

@app.post("/reset_session/{session_id}")
def reset_session(session_id: str):
    if session_id in SESSIONS:
        del SESSIONS[session_id]
        return {"message": f"Session {session_id} cleared."}
    return {"message": f"Session {session_id} not found."}