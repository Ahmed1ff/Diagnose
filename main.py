from fastapi import FastAPI
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
import os
load_dotenv()
app = FastAPI()

AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")

class DiagnosisRequest(BaseModel):
    symptoms: str  

def call_azure_gpt(symptoms: str):
    system_prompt = (
    "أنت مساعد طبي ذكي. إذا كتب المستخدم أعراضًا صحية، قدّم له تشخيصًا مبدئيًا ونصيحة بسيطة.\n"
    "أما إذا كتب المستخدم كلامًا لا علاقة له بالأعراض (مثل النكت أو الكورة)، فقم بالرد بالرسالة التالية فقط:\n"
    "' من فضلك أدخل أعراضًا صحية فقط للحصول على تشخيص.'\n"
    "انتبه: يجب أن ترد دائمًا بلغة المستخدم. إذا كتب المستخدم بالعربية، رد بالعربية. إذا كتب بالإنجليزية، رد بالإنجليزية."
)


    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_API_KEY
    }

    body = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": symptoms}
        ],
        "temperature": 0.5,
        "max_tokens": 400
    }

    response = requests.post(AZURE_OPENAI_ENDPOINT, headers=headers, json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


@app.post("/diagnose")
async def diagnose(req: DiagnosisRequest):
    try:
        reply = call_azure_gpt(req.symptoms)
        return {"diagnosis_and_advice": reply}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def home():
    return {"message": "🤖 Medical Diagnosis Chatbot is running"}
