import os
import json
import asyncio
import google.generativeai as genai
from typing import List, Dict, Any, AsyncGenerator
from pydantic import BaseModel

class Chunk(BaseModel):
    start: int
    end: int

class AnalysisPlan(BaseModel):
    hasAnswers: bool
    totalQuestions: int
    chunks: List[Chunk]

class Question(BaseModel):
    q: str
    a: List[str]
    c: int

# Initialize Gemini
load_dotenv_status = False # We'll assume main.py handles this
def get_model(model_name="gemini-1.5-flash"):
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

class QuizAgents:
    def __init__(self):
        self.model = get_model()

    async def analyze_document(self, file_content: bytes, mime_type: str) -> AnalysisPlan:
        prompt = """
        أنت وكيل مُحلل (Analyzer Agent). هدفك قراءة المستند المرفق بالكامل وتحليله.
        1. هل يحتوي المستند على أسئلة اختيار من متعدد بإجاباتها؟
        2. ما هو إجمالي عدد الأسئلة المتوفرة تقريباً؟ (عدها بدقة).
        3. قم بوضع خطة لتقسيم هذه الأسئلة إلى أجزاء (Chunks) بحيث لا يتعدى كل جزء 50 سؤالاً.
        
        استجب بملف JSON مطابق للـ Schema المطلوبة فقط.
        {
            "hasAnswers": bool,
            "totalQuestions": int,
            "chunks": [{"start": int, "end": int}]
        }
        """
        
        response = self.model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": file_content}
        ])
        
        # Clean response text if it has markdown backticks
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        return AnalysisPlan.parse_raw(text)

    async def extract_chunk(self, file_content: bytes, mime_type: str, start: int, end: int, agent_id: int) -> List[Question]:
        prompt = f"""
        أنت وكيل استخراج دقيق (Extractor Agent #{agent_id}).
        مهمتك: استخراج الأسئلة من رقم {start} إلى رقم {end} فقط من المستند المرفق.
        
        شروط صارمة:
        1. استخرج الأسئلة الواقعة في هذا النطاق فقط ({start} إلى {end}). تجاهل أي سؤال آخر.
        2. الإجابات الصحيحة في هذا الملف محددة بعلامة (•) بجانب الحرف أو ابحث عن مفتاح الإجابة.
        3. عدد الخيارات مرن (قد يكون 4 أو 5). استخرج كل الخيارات لكل سؤال.
        4. تجاهل أي أسئلة مقالية شاذة.
        
        استجب بملف JSON يحتوي على مصفوفة من الأسئلة فقط:
        [
          {{"q": "نص السؤال", "a": ["الخيارات"], "c": index_of_correct_answer}}
        ]
        """
        
        response = self.model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": file_content}
        ])
        
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        questions_data = json.loads(text)
        return [Question(**q) for q in questions_data]
