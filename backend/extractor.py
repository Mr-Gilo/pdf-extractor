import ollama
import json
import re

def clean_json_response(raw: str) -> str:
    """
    Robustly extract JSON object from LLM response.
    Handles markdown fences, preamble text, and trailing content.
    """
    raw = raw.strip()

    # Remove markdown code fences
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'```\s*$', '', raw, flags=re.MULTILINE)
    raw = raw.strip()

    # Find the first { and last } to isolate the JSON object
    start = raw.find('{')
    end = raw.rfind('}')

    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in LLM response. Raw response: {repr(raw[:200])}")

    return raw[start:end + 1]


def extract_information(text: str, model: str = "llama3.2") -> dict:
    """
    Use local Ollama LLM to extract structured information from document text.
    """

    # Context window management
    max_chars = 4000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[Document truncated for processing]"

    prompt = f"""You are a precise document analysis assistant. Analyse the 
document text below and extract structured information.

You MUST return ONLY a valid JSON object. No explanation, no markdown, 
no code fences. Start your response with {{ and end with }}.

Required JSON structure:
{{
  "document_type": "string describing the type of document",
  "parties": [
    {{"text": "full name or organisation", "context": "their role"}}
  ],
  "dates": [
    {{"text": "the date", "context": "what this date refers to"}}
  ],
  "monetary_amounts": [
    {{"text": "amount with currency", "context": "what this refers to"}}
  ],
  "key_facts": ["fact 1", "fact 2", "fact 3"],
  "summary": "2-3 sentence summary of the document"
}}

If a field has no data use an empty list [] or empty string "".
Only extract what is explicitly stated.

Document text:
{text}"""

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        options={
            "temperature": 0.1,
            "num_predict": 1024
        }
    )

    raw = response['message']['content']

    if not raw or not raw.strip():
        raise ValueError("LLM returned an empty response. Try again.")

    cleaned = clean_json_response(raw)
    result = json.loads(cleaned)
    return result