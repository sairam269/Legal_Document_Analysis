---

# Legal Document Analysis Tool

## Description

The **Legal Document Analysis Tool** is designed to process legal documents and automatically extract key clauses, terms, and conditions. It provides high-level summaries and can answer questions based on the content of the documents, helping legal teams or businesses quickly understand and analyze contracts.

### Key Features

* **Clause Extraction:** Automatically extract specific clauses, such as payment terms, confidentiality, or termination clauses.
* **Summarization:** Simplify complex legal language into easy-to-understand summaries.
* **Question Answering:** Answer questions like:

  * “What are the terms for cancellation?”
  * “What is the length of the contract?”

### Realistic Problems Addressed

1. **Compare Clauses Across Multiple Contracts** – Analyze multiple documents to find differences or inconsistencies in key clauses.
2. **Automatic Risk Flagging** – Identify potential risks using AI and keyword detection.
3. **Obligation Extraction & Tracking** – Extract structured obligations and track deadlines or reminders automatically.

### Tech Stack

* **Server:** MCP server using Cequence AI Gateway
* **Clients:** Custom MCP client implemented in Python using Claude
* **Language:** Python
* **Framework:** Flask

---

## Prerequisites

Before running the tool, ensure the following are installed:

* **Python 3.x**
* **pip** (Python package installer)

---

## Installation & Running

### Linux

1. Open a terminal in the project directory.
2. Make the startup script executable:

   ```bash
   chmod +x start.sh
   ```
3. Run the script:

   ```bash
   ./start.sh
   ```

This will:

* Check for Python and pip.
* Install dependencies from `requirements.txt`.
* Start `chatbot.py`.
* Start the FastAPI app on port 9000.

---

### Windows

1. Open Command Prompt in the project directory.
2. Run the batch file:

   ```bat
   start.bat
   ```

This will:

* Check for Python and pip.
* Install dependencies from `requirements.txt`.
* Start `chatbot.py` and the FastAPI app on port 9000 in separate windows.

---

## Usage

* **Chatbot:** Interact with the legal document analysis chatbot via the console.
* **API Server:** Access the FastAPI endpoints on `http://localhost:9000` to query documents or get clause summaries.

---

## Notes

* Ensure all legal documents to be analyzed are placed in the designated folder or provided via the API.
* The application is designed to scale and handle multiple document analyses concurrently.

---