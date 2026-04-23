import os
import json
import asyncio
import google.generativeai as genai
from typing import List, Dict, Any, AsyncGenerator
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted

def retry_logger(retry_state):
    print(f"DEBUG: Quota hit or API error. Retrying in {retry_state.next_action.sleep} seconds... (Attempt {retry_state.attempt_number})")

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
class QuizAgents:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        # Use gemini-3.1-flash-lite for faster analysis
        self.analyzer_model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")
        # Use gemini-3.1-pro for accurate extraction
        self.extractor_model = genai.GenerativeModel("gemini-3.1-pro-preview")

    @retry(
        retry=retry_if_exception_type(ResourceExhausted),
        wait=wait_exponential(multiplier=5, min=10, max=60),
        stop=stop_after_attempt(5),
        before_sleep=retry_logger
    )
    async def analyze_document(self, file_content: bytes, mime_type: str) -> AnalysisPlan:
        prompt = """
        أنت وكيل مُحلل (Analyzer Agent). هدفك قراءة المستند المرفق بالكامل وتحليله.
        1. هل يحتوي المستند على أسئلة اختيار من متعدد بإجاباتها؟
        2. ما هو إجمالي عدد الأسئلة المتوفرة تقريباً؟ (عدها بدقة).
        3. قم بوضع خطة لتقسيم هذه الأسئلة إلى أجزاء (Chunks) بحيث لا يتعدى كل جزء 50 سؤالاً.
        ملاحظة هامة: إذا كان عدد الأسئلة الإجمالي أكبر من 50، قم بتقسيمهم بشكل متوازن.
        أمثلة:
        - إذا كان هناك 80 سؤالاً: قسمهم إلى (40 و 40).
        - إذا كان هناك 90 سؤالاً: قسمهم إلى (50 و 40).
        - إذا كان هناك 120 سؤالاً: قسمهم إلى (40، 40، 40) أو (50، 50، 20).
        اجعل الأجزاء متساوية قدر الإمكان طالما أن الجزء الواحد لا يتخطى 50 سؤالاً.
        
        استجب بملف JSON مطابق للـ Schema المطلوبة فقط.
        {
            "hasAnswers": bool,
            "totalQuestions": int,
            "chunks": [{"start": int, "end": int}]
        }
        """
        
        response = self.analyzer_model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": file_content}
        ])
        
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        return AnalysisPlan.parse_raw(text)

    @retry(
        retry=retry_if_exception_type(ResourceExhausted),
        wait=wait_exponential(multiplier=10, min=20, max=300),
        stop=stop_after_attempt(10),
        before_sleep=retry_logger
    )
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
        
        print(f"DEBUG: Agent #{agent_id} calling Gemini API for range Q{start}-Q{end}...")
        response = self.extractor_model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": file_content}
        ])
        print(f"DEBUG: Agent #{agent_id} received response.")
        
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        try:
            questions_data = json.loads(text)
            return [Question(**q) for q in questions_data]
        except Exception as e:
            print(f"Error parsing Agent #{agent_id} response: {e}")
            return []
