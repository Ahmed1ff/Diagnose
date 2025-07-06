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
def detect_language(text: str) -> str:
    arabic_chars = [c for c in text if '\u0600' <= c <= '\u06FF']
    return "ar" if len(arabic_chars) > 5 else "en"
def call_azure_gpt(symptoms: str):
    language = detect_language(symptoms)

    if language == "ar":
       if language == "ar":
         system_prompt = (
        "أنت طبيب بشري محترف. عندما يكتب المستخدم أعراضًا صحية، قم بإرجاع الرد بهذا الشكل بالضبط:\n\n"
        "التشخيص المبدئي: [اكتب كل التشخيصات المحتملة في سطر واحد فقط، مفصولة بفواصل (،) بدون أي رموز أو قوائم أو سطور جديدة. لا تبدأ بـ 'قد يكون']\n"
        "التخصص المقترح: [اكتب التخصص الطبي الأكثر دقة حسب الأعراض مثل 'أنف وأذن وحنجرة' أو 'أعصاب' أو 'أمراض جلدية'. لا تذكر تخصصات عامة مثل 'طب الأسرة']\n"
        "نصيحة: [اكتب جملة واحدة فقط في نفس السطر، مباشرة وواضحة بدون 'يُفضل' أو 'قد'. لا تبدأ سطر جديد ولا تستخدم رموز أو تنقيط.]\n\n"
        "❗ إذا كتب المستخدم شيئًا لا علاقة له بالأعراض الصحية، أجب بهذه الجملة فقط:\n"
        "'من فضلك أدخل أعراضًا صحية فقط للحصول على التشخيص.'\n\n"
        "مهم جدًا:\n"
        "- كل جزء يجب أن يكون في **سطر واحد فقط**.\n"
        "- لا تستخدم رموز مثل (-) أو (•).\n"
        "- لا تستخدم نقاط أو قوائم أو أي مقدمة تفسيرية.\n"
        "- الرد كله يجب أن يكون باللغة العربية فقط.\n"
    )


    else:
        system_prompt = (
        "You are a professional medical doctor. When the user provides symptoms, respond in this exact strict format:\n\n"
        "Preliminary Diagnosis: [List all possible diagnoses in a **single line**, separated by commas (,) with no bullets, no symbols, and no line breaks. Do not start with 'Possible' or 'May be']\n"
        "Suggested Specialty: [State the most accurate and specific medical specialty like 'ENT', 'Neurology', or 'Dermatology'. Do not say 'Family Medicine']\n"
        "Advice: [Write **one direct sentence** in the same line, no 'consider' or 'might'. No line breaks, symbols, or bullet points.]\n\n"
        "❗ If the user enters non-medical input, respond only with:\n"
        "'Please enter only medical symptoms to get a diagnosis.'\n\n"
        "Strict formatting rules:\n"
        "- Each section must be on one line only.\n"
        "- No symbols like (-), (•), or numbering.\n"
        "- No vague or general specialties.\n"
        "- The entire response must be written in English only.\n"
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

# 👇 دالة تفصل الرد إلى حقول منفصلة
def parse_gpt_response(response_text: str):
    lines = response_text.strip().split("\n")
    result = {"diagnosis": "", "specialty": "", "advice": ""}

    for line in lines:
        if "التشخيص المبدئي" in line:
            result["diagnosis"] = line.split(":", 1)[1].strip()
        elif "التخصص المقترح" in line:
            result["specialty"] = line.split(":", 1)[1].strip()
        elif "نصيحة" in line:
            result["advice"] = line.split(":", 1)[1].strip()
        elif "Preliminary Diagnosis" in line:
            result["diagnosis"] = line.split(":", 1)[1].strip()
        elif "Suggested Specialty" in line:
            result["specialty"] = line.split(":", 1)[1].strip()
        elif "Advice" in line:
            result["advice"] = line.split(":", 1)[1].strip()

    return result

@app.post("/diagnose")
async def diagnose(req: DiagnosisRequest):
    try:
        reply = call_azure_gpt(req.symptoms)

        # لو المستخدم كتب حاجة غير أعراض، هنرجع الرد زي ما هو
        if "من فضلك أدخل أعراضًا صحية فقط" in reply or "Please enter only medical symptoms" in reply:
            return {"message": reply}

        parsed = parse_gpt_response(reply)
        return parsed

    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def home():
    return {"message": "🤖 Medical Diagnosis Chatbot is running"}
