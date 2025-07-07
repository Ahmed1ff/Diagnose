from fastapi import FastAPI
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI()

AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

# Request schema
class DiagnosisRequest(BaseModel):
    symptoms: str

# Language detection
def detect_language(text: str) -> str:
    arabic_count = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    english_count = sum(1 for c in text if c.isascii() and c.isalpha())

    print("🔍 Detected Arabic count:", arabic_count)
    print("🔍 Detected English count:", english_count)

    if arabic_count > 0 and english_count > 0:
        return "ar"  # Mixed input → force Arabic
    elif arabic_count > english_count:
        return "ar"
    elif english_count > arabic_count:
        return "en"
    return "ar"  # Default


# GPT call
def call_azure_gpt(symptoms: str):
    language = detect_language(symptoms)

    system_prompt = f"""
You are a professional medical doctor who understands both Arabic and English.
When the user provides symptoms, respond in ONLY one language — the dominant language used in the symptoms.
Dominant language: {language}

If responding in Arabic:
 التشخيص المبدئي: [اكتب كل التشخيصات المحتملة في سطر واحد فقط، مفصولة بفواصل (،)، بدون 'قد يكون']
 التخصص المقترح: [اكتب تخصصًا طبيًا دقيقًا مثل 'أمراض باطنية' أو 'أعصاب']

If responding in English:
 Preliminary Diagnosis: [List all possible diagnoses in one line, separated by commas. Do not use 'possible']
 Suggested Specialty: [Provide a specific specialty like 'Neurology' or 'Cardiology']

❗ If the input is unrelated to medical symptoms, reply ONLY with:
- ' أدخل أعراضًا صحية فقط للحصول على التشخيص.' IF Arabic
- ' enter only medical symptoms to get a diagnosis.' IF English

Strict rules:
- Use ONLY the dominant language in reply
- Use EXACTLY two lines — no more, no less
- NO symbols, NO names, NO mixing of Arabic and English
"""


    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_API_KEY
    }

    body = {
  "messages": [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": symptoms.strip()}
  ],
  "temperature": 0,
  "max_tokens": 400
}

    response = requests.post(AZURE_OPENAI_ENDPOINT, headers=headers, json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

@app.post("/diagnose")
async def diagnose(req: DiagnosisRequest):
    try:
        reply = call_azure_gpt(req.symptoms)

        if any(x in reply for x in [
            "من فضلك أدخل أعراضًا صحية فقط",
            "Please enter only medical symptoms"
        ]):
            return {"message": reply}

        banned_words = ["جيفارا", "مارادونا", "ترامب", "Messi", "Hitler"]
        if any(word.lower() in reply.lower() for word in banned_words):
            return {"error": "رد غير منطقي. يرجى إعادة كتابة الأعراض بشكل أوضح."}

        return {"result": reply}

    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def home():
    return {"message": "🤖 Medical Diagnosis Chatbot is running"}
