import os
import re
import json
import logging
from typing import List
from google import genai
from google.genai import types
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


def _retry_logger(retry_state):
    logger.warning(
        f"Quota hit. Retrying in {retry_state.next_action.sleep:.1f}s "
        f"(Attempt {retry_state.attempt_number})"
    )


def _strip_markdown_json(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    return text


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


class QuizAgents:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        self.client = genai.Client(api_key=api_key)

    def _make_contents(self, prompt: str, mime_type: str, file_content: bytes):
        return [
            types.Content(
                role="user",
                parts=[
                    types.Part(text=prompt),
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=file_content,
                        )
                    ),
                ],
            )
        ]

    @retry(
        retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
        wait=wait_exponential(multiplier=5, min=10, max=60),
        stop=stop_after_attempt(5),
        before_sleep=_retry_logger,
    )
    async def analyze_document(self, file_content: bytes, mime_type: str) -> AnalysisPlan:
        prompt = """
        أنت وكيل مُحلل (Analyzer Agent). هدفك قراءة المستند المرفق بالكامل وتحليله.
        1. هل يحتوي المستند على أسئلة اختيار من متعدد بإجاباتها؟
        2. ما هو إجمالي عدد الأسئلة المتوفرة تقريباً؟ (عدها بدقة، لا تتجاهل أي صفحة).
        3. قم بوضع خطة لتقسيم هذه الأسئلة إلى أجزاء (Chunks) بحيث لا يتعدى كل جزء 50 سؤالاً.
        ملاحظة هامة: إذا كان عدد الأسئلة الإجمالي أكبر من 50، قم بتقسيمهم بشكل متوازن.
        أمثلة:
        - 80 سؤالاً: (40 و 40)
        - 90 سؤالاً: (50 و 40)
        - 120 سؤالاً: (40، 40، 40)

        استجب بـ JSON فقط، لا تضف أي نص آخر:
        {
            "hasAnswers": bool,
            "totalQuestions": int,
            "chunks": [{"start": int, "end": int}]
        }
        """

        response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=self._make_contents(prompt, mime_type, file_content),
        )

        text = _strip_markdown_json(response.text)
        logger.info(f"Analyzer raw response: {text[:200]}")
        return AnalysisPlan.model_validate_json(text)

    @retry(
        retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable)),
        wait=wait_exponential(multiplier=5, min=10, max=60),
        stop=stop_after_attempt(8),
        before_sleep=_retry_logger,
    )
    async def extract_chunk(
        self, file_content: bytes, mime_type: str, start: int, end: int, agent_id: int
    ) -> List[Question]:
        prompt = f"""
        أنت وكيل استخراج دقيق (Extractor Agent #{agent_id}).
        مهمتك: استخراج الأسئلة من رقم {start} إلى رقم {end} فقط من المستند المرفق.

        شروط صارمة:
        1. استخرج الأسئلة الواقعة في هذا النطاق فقط ({start} إلى {end}). تجاهل أي سؤال آخر.
        2. الإجابات الصحيحة محددة بعلامة (•) أو بمفتاح الإجابة في نهاية الملف.
        3. عدد الخيارات مرن (4 أو 5). استخرج كل الخيارات.
        4. تجاهل الأسئلة المقالية.

        استجب بـ JSON فقط، مصفوفة أسئلة بهذا الشكل:
        [
          {{"q": "نص السؤال", "a": ["خيار1", "خيار2", "خيار3", "خيار4"], "c": 0}}
        ]
        حيث c = index الإجابة الصحيحة (0-based).
        """

        logger.info(f"Agent #{agent_id} → Gemini API (Q{start}–Q{end})")
        response = await self.client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=self._make_contents(prompt, mime_type, file_content),
        )
        logger.info(f"Agent #{agent_id} ← response received")

        text = _strip_markdown_json(response.text)
        try:
            questions_data = json.loads(text)
            return [Question(**q) for q in questions_data]
        except Exception as e:
            logger.error(f"Agent #{agent_id} parse error: {e}\nRaw: {text[:300]}")
            return []
