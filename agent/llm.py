import os, json, time
from typing import List, Literal
from pydantic import BaseModel
from google import genai
from google.genai import types

MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

class Verdict(BaseModel):
    risk: Literal["Safe", "Suspicious", "Dangerous"]
    confidence: int
    scam_type: str
    tactics: List[str]
    flags: List[str]
    explanation: str
    advice: List[str]
    learn_more: str

SYSTEM = """You are Scam Shield, an assistant that helps people in Pakistan check whether an SMS, WhatsApp message or link is a scam.

Rules:
- risk: "Safe" only for messages that are clearly legitimate (for example a genuine OTP message that warns not to share the code, or a normal transaction notice that asks the user to do nothing risky). "Suspicious" if you are unsure or some warning signs are present. "Dangerous" if it clearly tries to get money, PINs, OTPs or personal data.
- Do not flag a message just because it mentions a bank, wallet or courier. Look at what it asks the user to do.
- You also receive tool findings (URL analysis and pattern matches). Treat them as evidence, not as the final answer. Tools can be wrong, so weigh them.
- confidence is 0-100: how sure you are about your risk label. Never claim certainty.
- scam_type: one short English label such as "prize scam", "bank impersonation", "OTP theft", "courier fee scam", "job scam", "government payment scam", or "none".
- tactics: choose from "urgency", "fear", "too-good-to-be-true reward", "authority impersonation", "none".
- flags: short red flags that are really present. An empty list is fine for Safe messages.
- explanation: 2-4 simple sentences, no jargon.
- advice: 3-5 concrete steps (do not click, never share OTP or PIN, contact the bank on its official number, block and report). For Safe messages, still remind the user to verify through official channels if unsure.
- Never invent phone numbers, helplines, websites or app names. Say "the official number printed on the back of your card or on the official website" instead.
- learn_more: 1-2 sentences on how this type of scam works.
- Write explanation, flags, advice and learn_more in the requested language. If Urdu, use Urdu script and simple words. Keep scam_type and tactics in English."""

_client = None
def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client

def judge(text, evidence, language="English", retries=2):
    prompt = f'''Language for the answer: {language}

MESSAGE TO CHECK:
"""{text}"""

TOOL FINDINGS (may be empty):
{json.dumps(evidence, ensure_ascii=False, indent=2, default=str)}'''
    cfg = types.GenerateContentConfig(
        system_instruction=SYSTEM,
        temperature=0,
        response_mime_type="application/json",
        response_schema=Verdict,
    )
    for attempt in range(retries + 1):
        try:
            resp = _get_client().models.generate_content(model=MODEL, contents=prompt, config=cfg)
            if resp.parsed is None:
                raise ValueError("Model returned unparsable output")
            return resp.parsed
        except Exception as ex:
            msg = str(ex)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg or attempt == retries:
                raise
            time.sleep(2 * (attempt + 1))


EXTRACT_PROMPT = """Transcribe all the text visible in this screenshot of a message exactly as written, including links, phone numbers and the sender name. Output only the transcribed text. If there is no readable text, output exactly NO_TEXT."""

def extract_text(image_bytes, mime_type="image/png"):
    part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    cfg = types.GenerateContentConfig(temperature=0)
    resp = _get_client().models.generate_content(model=MODEL, contents=[part, EXTRACT_PROMPT], config=cfg)
    return (resp.text or "").strip()
