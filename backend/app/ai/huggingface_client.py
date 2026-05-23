import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import requests

from app.config import settings

logger = logging.getLogger("app.ai.huggingface_client")

HF_API_URL = "https://api-inference.huggingface.co/models"


def is_huggingface_enabled() -> bool:
    return bool(settings.HUGGINGFACE_API_TOKEN and settings.HUGGINGFACE_MODEL_ID)


def _extract_generated_text(payload: Any) -> str:
    if isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, dict):
            return str(first.get("generated_text") or first.get("summary_text") or "")
    if isinstance(payload, dict):
        return str(payload.get("generated_text") or payload.get("summary_text") or payload.get("text") or "")
    return ""


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def _post_generation(prompt: str, max_new_tokens: int = 700) -> str:
    if not is_huggingface_enabled():
        return ""

    headers = {
        "Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": 0.35,
            "return_full_text": False,
        },
        "options": {
            "wait_for_model": True,
        },
    }

    response = requests.post(
        f"{HF_API_URL}/{settings.HUGGINGFACE_MODEL_ID}",
        headers=headers,
        json=payload,
        timeout=45,
    )
    response.raise_for_status()
    return _extract_generated_text(response.json()).strip()


def _post_audio_transcription(audio_bytes: bytes, content_type: str) -> str:
    if not settings.HUGGINGFACE_API_TOKEN:
        return ""

    headers = {
        "Authorization": f"Bearer {settings.HUGGINGFACE_API_TOKEN}",
        "Content-Type": content_type or "audio/webm",
    }

    response = requests.post(
        f"{HF_API_URL}/{settings.HUGGINGFACE_ASR_MODEL_ID}",
        headers=headers,
        data=audio_bytes,
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        return str(payload.get("text") or payload.get("transcription") or "").strip()
    return ""


async def generate_questions_with_huggingface(role: str, count: int = 4) -> Optional[List[str]]:
    prompt = f"""
You are a senior campus placement interviewer.
Create {count} original, industry-level mock interview questions for a student preparing for a {role} role.
Cover technical depth, practical tradeoffs, and production thinking.
Return only JSON:
{{"questions":["question 1","question 2","question 3","question 4"]}}
"""
    try:
        text = await asyncio.to_thread(_post_generation, prompt, 650)
        data = _extract_json_object(text)
        questions = data.get("questions") if data else None
        if isinstance(questions, list):
            cleaned = [str(q).strip() for q in questions if str(q).strip()]
            if len(cleaned) >= count:
                return cleaned[:count]
    except Exception as exc:
        logger.warning("Hugging Face question generation failed: %s", exc)
    return None


async def evaluate_answer_with_huggingface(role: str, question: str, answer: str) -> Optional[Dict[str, Any]]:
    prompt = f"""
You are an expert technical interviewer evaluating a candidate for a {role} role.
Grade the answer strictly and constructively.

Question: {question}
Candidate answer: {answer}

Return only JSON:
{{
  "score": 0-100,
  "feedback": "specific feedback on correctness, clarity, depth, and communication",
  "improvement_tips": "specific missing concepts and how to improve"
}}
"""
    try:
        text = await asyncio.to_thread(_post_generation, prompt, 500)
        data = _extract_json_object(text)
        if not data:
            return None
        score = float(data.get("score", 0))
        return {
            "score": max(0.0, min(100.0, score)),
            "feedback": str(data.get("feedback", "")).strip(),
            "improvement_tips": str(data.get("improvement_tips", "")).strip(),
        }
    except Exception as exc:
        logger.warning("Hugging Face answer evaluation failed: %s", exc)
    return None


async def transcribe_audio_with_huggingface(audio_bytes: bytes, content_type: str) -> Optional[str]:
    try:
        transcript = await asyncio.to_thread(_post_audio_transcription, audio_bytes, content_type)
        return transcript or None
    except Exception as exc:
        logger.warning("Hugging Face audio transcription failed: %s", exc)
    return None
